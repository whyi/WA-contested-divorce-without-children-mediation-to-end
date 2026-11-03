import unittest
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import Mock

from fastapi import HTTPException, Response
from unittest.mock import patch

from app.settlement_routes import (
    create_settlement_scenarios,
)
from app.settlement_planning import ScenarioAxes


class SettlementRouteGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case_id = uuid4()
        self.user = SimpleNamespace(id=uuid4())

    def test_local_scenario_calculation_is_available_without_ai_consent(self) -> None:
        asset_id = uuid4()
        event_id = uuid4()
        case = SimpleNamespace(
            id=self.case_id,
            profile_revision=0,
            settlement_revision=1,
        )
        membership = SimpleNamespace(role="owner")
        ledger_row = SimpleNamespace(
            asset_id=asset_id,
            asset_name="Savings",
            asset_kind="asset",
            event_json={
                "id": str(event_id),
                "effective_date": "2023-01-01",
                "sequence_number": 0,
                "event_type": "acquisition",
                "amount_cents": 1000,
                "source_allocations": {
                    "user_separate": 1000,
                    "other_separate": 0,
                    "community": 0,
                    "unresolved": 0,
                },
                "provenance": "user_reported",
                "source_fact_ids": [],
                "note": "",
            },
        )
        db = Mock()
        db.scalar.side_effect = [membership, None]
        db.get.return_value = case
        empty_result = Mock()
        empty_result.all.return_value = []
        ledger_result = Mock()
        ledger_result.all.return_value = [ledger_row]
        db.scalars.side_effect = [empty_result, ledger_result]
        payload = SimpleNamespace(
            expected_profile_revision=0,
            expected_settlement_revision=1,
            objective="Preserve traceable property.",
            axes=ScenarioAxes.model_validate(
                {
                    "relationship_windows": [{
                        "id": "marriage",
                        "label": "Marriage only",
                        "relationship_type": "marriage_only",
                        "start_date": "2020-01-01",
                        "separation_date": "2024-01-01",
                    }],
                    "tracing_methods": ["explicit"],
                    "community_share_bps": [5000],
                }
            ),
        )

        with patch("app.settlement_routes.rank_settlement_scenarios") as rank:
            result = create_settlement_scenarios(
                self.case_id,
                payload,
                Response(),
                self.user,
                db,
            )

        self.assertEqual(len(result.scenarios), 1)
        self.assertIsNone(result.ranking)
        self.assertIn("consent", result.ranking_error)
        rank.assert_not_called()

    def test_viewers_cannot_save_settlement_consent(self) -> None:
        db = Mock()
        db.scalar.return_value = SimpleNamespace(role="viewer")
        from app.settlement_routes import ConsentCreate, grant_settlement_planning_consent

        with self.assertRaises(HTTPException) as raised:
            grant_settlement_planning_consent(
                self.case_id,
                ConsentCreate(confirm=True, notice_version="settlement-planning-v1"),
                Response(),
                self.user,
                db,
            )

        self.assertEqual(raised.exception.status_code, 403)
        db.add.assert_not_called()
        db.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
