import unittest
from datetime import date
from uuid import uuid4

from pydantic import ValidationError

from app.settlement_planning import (
    AssetLedger,
    LedgerEvent,
    RelationshipWindow,
    ScenarioAxes,
    calculate_scenario,
    generate_scenarios,
    trace_ledgers,
)


def event(
    event_type: str,
    amount: int,
    **kwargs: object,
) -> LedgerEvent:
    return LedgerEvent(
        event_type=event_type,
        effective_date=kwargs.pop("effective_date", "2022-01-01"),
        amount_cents=amount,
        provenance=kwargs.pop("provenance", "user_reported"),
        **kwargs,
    )


class PropertyLedgerTests(unittest.TestCase):
    def test_pro_rata_withdrawal_and_valuation_are_deterministic(self) -> None:
        asset_id = uuid4()
        ledger = AssetLedger(
            asset_id=asset_id,
            name="Investment account",
            kind="asset",
            events=[
                event(
                    "contribution",
                    10_000,
                    effective_date="2022-01-01",
                    source_allocations={"user_separate": 10_000},
                    provenance="user_reported",
                ),
                event(
                    "contribution",
                    10_000,
                    effective_date="2022-01-02",
                    source_allocations={"community": 10_000},
                    provenance="source_supported",
                    source_fact_ids=[uuid4()],
                ),
                event("withdrawal", 5_000, effective_date="2022-01-03"),
                event("valuation", 30_000, effective_date="2022-01-04"),
            ],
        )

        result = trace_ledgers([ledger], "pro_rata")[0]

        self.assertEqual(result.balances.user_separate_cents, 15_000)
        self.assertEqual(result.balances.community_cents, 15_000)
        self.assertEqual(result.balances.total_cents, 30_000)
        self.assertEqual(len(result.steps), 4)

    def test_income_source_is_reclassified_by_explicit_relationship_window(self) -> None:
        ledger = AssetLedger(
            asset_id=uuid4(),
            name="Paycheck deposits",
            kind="asset",
            events=[
                event(
                    "income",
                    20_000,
                    effective_date="2022-05-01",
                    earned_by="user",
                    provenance="user_reported",
                )
            ],
        )
        inside_window = RelationshipWindow(
            id="cir",
            label="Assumed CIR window",
            relationship_type="cir_assumed",
            start_date="2022-01-01",
            separation_date="2023-01-01",
        )
        outside_window = RelationshipWindow(
            id="marriage",
            label="Marriage-only window",
            relationship_type="marriage_only",
            start_date="2022-06-01",
            separation_date="2023-01-01",
        )

        community_result = trace_ledgers(
            [ledger],
            "pro_rata",
            inside_window,
        )[0]
        separate_result = trace_ledgers(
            [ledger],
            "pro_rata",
            outside_window,
        )[0]

        self.assertEqual(community_result.balances.community_cents, 20_000)
        self.assertEqual(separate_result.balances.user_separate_cents, 20_000)

    def test_unknown_funds_remain_unresolved(self) -> None:
        ledger = AssetLedger(
            asset_id=uuid4(),
            name="Unverified deposit",
            kind="asset",
            events=[
                event(
                    "contribution",
                    12_345,
                    provenance="unresolved",
                )
            ],
        )

        result = trace_ledgers([ledger], "pro_rata")[0]

        self.assertEqual(result.balances.unresolved_cents, 12_345)
        self.assertEqual(result.balances.community_cents, 0)

    def test_withdrawal_cannot_overdraw_a_source_bucket(self) -> None:
        ledger = AssetLedger(
            asset_id=uuid4(),
            name="Cash account",
            kind="asset",
            events=[
                event(
                    "contribution",
                    5_000,
                    source_allocations={"community": 5_000},
                    provenance="user_reported",
                ),
                event(
                    "withdrawal",
                    6_000,
                    effective_date="2022-01-02",
                    source_allocations={"community": 6_000},
                    provenance="user_reported",
                ),
            ],
        )

        with self.assertRaisesRegex(ValueError, "exceeds the available"):
            trace_ledgers([ledger], "explicit")

    def test_transfer_requires_matching_outflow_and_inflow(self) -> None:
        source_id = uuid4()
        destination_id = uuid4()
        transfer_id = uuid4()
        outflow = AssetLedger(
            asset_id=source_id,
            name="Checking",
            kind="asset",
            events=[
                event(
                    "contribution",
                    10_000,
                    source_allocations={"user_separate": 10_000},
                    provenance="user_reported",
                ),
                event(
                    "transfer_out",
                    4_000,
                    effective_date="2022-02-01",
                    source_allocations={"user_separate": 4_000},
                    transfer_id=transfer_id,
                    provenance="user_reported",
                ),
            ],
        )
        inflow = AssetLedger(
            asset_id=destination_id,
            name="Savings",
            kind="asset",
            events=[
                event(
                    "transfer_in",
                    4_000,
                    effective_date="2022-02-01",
                    source_allocations={"user_separate": 4_000},
                    transfer_id=transfer_id,
                    provenance="user_reported",
                )
            ],
        )

        results = trace_ledgers([outflow, inflow], "explicit")

        self.assertEqual(
            sum(result.balances.total_cents for result in results),
            10_000,
        )
        with self.assertRaisesRegex(ValueError, "matching"):
            trace_ledgers([outflow], "explicit")

    def test_scenario_calculation_uses_explicit_user_share_and_liability_sign(self) -> None:
        window = RelationshipWindow(
            id="marriage",
            label="Marriage-only",
            relationship_type="marriage_only",
            start_date="2021-01-01",
            separation_date="2024-01-01",
        )
        assets = [
            AssetLedger(
                asset_id=uuid4(),
                name="Home",
                kind="asset",
                events=[
                    event(
                        "contribution",
                        100_000,
                        source_allocations={"user_separate": 20_000, "community": 80_000},
                        provenance="user_reported",
                    )
                ],
            ),
            AssetLedger(
                asset_id=uuid4(),
                name="Debt",
                kind="debt",
                events=[
                    event(
                        "contribution",
                        20_000,
                        source_allocations={"community": 20_000},
                        provenance="user_reported",
                    )
                ],
            ),
        ]
        axes = ScenarioAxes(
            relationship_windows=[window],
            tracing_methods=["explicit"],
            community_share_bps=[7_500],
        )
        scenario = generate_scenarios(axes)[0]

        result = calculate_scenario(scenario, assets)

        self.assertEqual(result.user_net_cents, 65_000)
        self.assertEqual(result.other_net_cents, 15_000)
        self.assertEqual(result.unresolved_cents, 0)

    def test_scenario_generation_is_bounded_and_requires_explicit_shares(self) -> None:
        windows = [
            RelationshipWindow(
                id=f"window-{index}",
                label=f"Window {index}",
                relationship_type="alternate",
                start_date=f"202{index}-01-01",
                separation_date="2025-01-01",
            )
            for index in range(1, 4)
        ]
        axes = ScenarioAxes(
            relationship_windows=windows,
            tracing_methods=["explicit", "pro_rata", "community_first"],
            community_share_bps=[4_000, 5_000, 6_000],
        )

        scenarios = generate_scenarios(axes)

        self.assertLessEqual(len(scenarios), 12)
        self.assertGreater(len({scenario.id for scenario in scenarios}), 1)
        with self.assertRaises(ValidationError):
            ScenarioAxes(
                relationship_windows=[windows[0]],
                tracing_methods=["explicit"],
                community_share_bps=[],
            )

    def test_scenario_result_does_not_mutate_source_ledger(self) -> None:
        original_date = date(2022, 1, 1)
        ledger = AssetLedger(
            asset_id=uuid4(),
            name="Account",
            kind="asset",
            events=[
                event(
                    "contribution",
                    1_000,
                    effective_date=original_date.isoformat(),
                    source_allocations={"community": 1_000},
                    provenance="user_reported",
                )
            ],
        )
        scenario = generate_scenarios(
            ScenarioAxes(
                relationship_windows=[
                    RelationshipWindow(
                        id="window",
                        label="Window",
                        relationship_type="alternate",
                        start_date="2021-01-01",
                        separation_date="2023-01-01",
                    )
                ],
                tracing_methods=["explicit"],
                community_share_bps=[5_000],
            )
        )[0]

        calculate_scenario(scenario, [ledger])

        self.assertEqual(ledger.events[0].effective_date, original_date)


if __name__ == "__main__":
    unittest.main()
