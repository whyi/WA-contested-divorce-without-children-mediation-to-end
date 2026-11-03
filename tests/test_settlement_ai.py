import json
import unittest
from uuid import uuid4

from app.config import Settings
from app.settlement_ai import rank_settlement_scenarios
from app.settlement_planning import (
    AssetLedger,
    LedgerEvent,
    RelationshipWindow,
    ScenarioAxes,
    calculate_scenario,
    generate_scenarios,
)


def response_json(value: object) -> dict:
    return {
        "output": {
            "message": {
                "content": [{"text": json.dumps(value)}],
            }
        }
    }


class FakeBedrockClient:
    def __init__(self, value: object) -> None:
        self.value = value
        self.request: dict | None = None

    def converse(self, **request: object) -> dict:
        self.request = request
        return response_json(self.value)


def scenario_results():
    window = RelationshipWindow(
        id="marriage",
        label="Marriage-only dates",
        relationship_type="marriage_only",
        start_date="2020-01-01",
        separation_date="2024-01-01",
    )
    axes = ScenarioAxes(
        relationship_windows=[window],
        tracing_methods=["explicit"],
        community_share_bps=[5_000],
    )
    scenario = generate_scenarios(axes)[0]
    ledger = AssetLedger(
        asset_id=uuid4(),
        name="Savings",
        kind="asset",
        events=[
            LedgerEvent(
                effective_date="2022-01-01",
                event_type="contribution",
                amount_cents=10_000,
                source_allocations={"community": 10_000},
                provenance="user_reported",
                note="Do not send this internal source note.",
            )
        ],
    )
    return [calculate_scenario(scenario, [ledger])]


class SettlementRankingTests(unittest.TestCase):
    def test_ranks_only_supplied_scenarios_and_authorities(self) -> None:
        scenarios = scenario_results()
        fact_id = uuid4()
        client = FakeBedrockClient(
            {
                "ranked": [
                    {
                        "scenario_id": scenarios[0].scenario.id,
                        "reason": "The calculation follows the stated objective.",
                        "supporting_fact_ids": [str(fact_id)],
                        "countervailing_fact_ids": [],
                        "authority_ids": ["rcw_26_09_080"],
                        "uncertainty": "The valuation remains user-reported.",
                    }
                ]
            }
        )

        result = rank_settlement_scenarios(
            scenarios,
            "Preserve my separate property while reaching a workable agreement.",
            [{"id": fact_id, "field_key": "asset_value", "value": "100"}],
            Settings(bedrock_model_id="test-model", bedrock_region="us-west-2"),
            client,
        )

        self.assertEqual(result.ranked[0].scenario_id, scenarios[0].scenario.id)
        self.assertIn("rcw_26_09_080", result.authorities)
        self.assertEqual(client.request["inferenceConfig"], {"temperature": 0.0})
        self.assertNotIn("toolConfig", client.request)
        provider_input = client.request["messages"][0]["content"][0]["text"]
        self.assertIn("Preserve my separate property", provider_input)
        self.assertNotIn("Do not send this internal source note.", provider_input)

    def test_rejects_references_to_unprovided_scenario_facts_and_law(self) -> None:
        scenarios = scenario_results()
        fact_id = uuid4()
        invalid_responses = [
            {
                "scenario_id": "made-up",
                "supporting_fact_ids": [],
                "authority_ids": ["rcw_26_09_080"],
            },
            {
                "scenario_id": scenarios[0].scenario.id,
                "supporting_fact_ids": [str(uuid4())],
                "authority_ids": ["rcw_26_09_080"],
            },
            {
                "scenario_id": scenarios[0].scenario.id,
                "supporting_fact_ids": [str(fact_id)],
                "authority_ids": ["made-up-law"],
            },
        ]
        for invalid in invalid_responses:
            response = {
                "ranked": [
                    {
                        **invalid,
                        "reason": "This answer cannot be verified.",
                        "countervailing_fact_ids": [],
                        "uncertainty": "Review is required.",
                    }
                ]
            }
            with self.subTest(response=response):
                with self.assertRaises(ValueError):
                    rank_settlement_scenarios(
                        scenarios,
                        "Preserve assets.",
                        [{"id": fact_id, "field_key": "asset_value", "value": "100"}],
                        Settings(bedrock_model_id="test-model"),
                        FakeBedrockClient(response),
                    )

    def test_invalid_ai_json_is_an_explicit_failure(self) -> None:
        client = FakeBedrockClient("invalid")
        with self.assertRaisesRegex(ValueError, "required schema"):
            rank_settlement_scenarios(
                scenario_results(),
                "Preserve assets.",
                [{"id": uuid4(), "field_key": "asset_value", "value": "100"}],
                Settings(bedrock_model_id="test-model"),
                client,
            )

    def test_empty_ranking_must_explain_insufficient_evidence(self) -> None:
        scenarios = scenario_results()
        fact_id = uuid4()
        client = FakeBedrockClient(
            {
                "ranked": [],
                "unranked_reason": "The disputed dates do not support a reliable relative ranking.",
            }
        )
        result = rank_settlement_scenarios(
            scenarios,
            "Preserve assets.",
            [{"id": fact_id, "field_key": "asset_value", "value": "100"}],
            Settings(bedrock_model_id="test-model"),
            client,
        )
        self.assertEqual(result.ranked, [])
        self.assertIn("disputed dates", result.unranked_reason)

        with self.assertRaisesRegex(ValueError, "required schema"):
            rank_settlement_scenarios(
                scenarios,
                "Preserve assets.",
                [{"id": fact_id, "field_key": "asset_value", "value": "100"}],
                Settings(bedrock_model_id="test-model"),
                FakeBedrockClient({"ranked": []}),
            )

    def test_provider_is_not_called_without_objective_or_reviewed_facts(self) -> None:
        client = FakeBedrockClient({"ranked": []})
        with self.assertRaisesRegex(ValueError, "objective"):
            rank_settlement_scenarios(
                scenario_results(),
                " ",
                [{"id": uuid4()}],
                Settings(bedrock_model_id="test-model"),
                client,
            )
        self.assertIsNone(client.request)

    def test_provider_is_not_called_when_reviewed_facts_lack_unique_ids(self) -> None:
        client = FakeBedrockClient({"ranked": []})
        with self.assertRaisesRegex(ValueError, "valid UUID identifiers"):
            rank_settlement_scenarios(
                scenario_results(),
                "Preserve assets.",
                [{"field_key": "asset_value", "value": "100"}],
                Settings(bedrock_model_id="test-model"),
                client,
            )
        self.assertIsNone(client.request)


if __name__ == "__main__":
    unittest.main()
