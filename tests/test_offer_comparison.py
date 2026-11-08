from copy import deepcopy
from datetime import UTC, datetime
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from app.offer_comparison import build_offer_comparison
from app.offer_response import _read_response


ASSET = str(uuid4())
DEBT = str(uuid4())


def snapshot():
    return {
        "case_profile": {
            "metadata": {
                "existing_offer": {
                    "exists": True,
                    "notes": "House to me; retirement split discussed",
                    "asset_terms": [{"asset_index": 0, "asset_name": "House", "term": "To you"}],
                }
            }
        },
        "scenario": {
            "scenario_id": "scenario-1",
            "result": {
                "scenario": {"community_share_bps": 6000},
                "ledgers": [
                    {
                        "asset_id": ASSET,
                        "name": "House",
                        "kind": "asset",
                        "balances": {
                            "user_separate_cents": 1000,
                            "other_separate_cents": 2000,
                            "community_cents": 3000,
                            "unresolved_cents": 0,
                        },
                    },
                    {
                        "asset_id": DEBT,
                        "name": "Mortgage",
                        "kind": "debt",
                        "balances": {
                            "user_separate_cents": 0,
                            "other_separate_cents": 0,
                            "community_cents": 5000,
                            "unresolved_cents": 1000,
                        },
                    },
                ],
            },
        },
        "settlement_ledger": [
            {"asset_id": ASSET, "asset_name": "House", "asset_kind": "asset"},
            {"asset_id": DEBT, "asset_name": "Mortgage", "asset_kind": "debt"},
        ],
    }


def values_by_asset(series):
    return {item["asset_id"]: item for item in series["values"]}


class OfferComparisonTests(unittest.TestCase):
    def test_initial_incoming_offer_does_not_invent_prior_user_proposal(self):
        result = build_offer_comparison(
            attempt_ordinal=1,
            proposal_version_ordinal=0,
            finalized=False,
            offer_origin="initial_incoming_offer",
            snapshot=snapshot(),
            scenario_result=snapshot()["scenario"]["result"],
            editable_state={"proposed_values": []},
            prior_attempt=None,
            current_counteroffer=None,
        )

        series = {item["id"]: item for item in result["series"]}
        self.assertEqual(result["offer_origin"], "initial_incoming_offer")
        self.assertEqual(result["initial_incoming_offer"]["notes"], "House to me; retirement split discussed")
        self.assertFalse(series["prior_proposal"]["available"])
        self.assertFalse(series["party_baseline"]["available"])
        self.assertFalse(series["opposing_baseline"]["available"])
        self.assertTrue(series["party_value"]["available"])
        self.assertEqual(values_by_asset(series["party_value"])[ASSET]["amount_cents"], 2800)
        self.assertEqual(values_by_asset(series["opposing_value"])[ASSET]["amount_cents"], 3200)
        self.assertEqual(values_by_asset(series["party_value"])[DEBT]["status"], "partial_unresolved")
        self.assertEqual(values_by_asset(series["party_value"])[DEBT]["unresolved_cents"], 1000)
        self.assertEqual(result["totals"]["party_value"]["known_subtotal_cents"], -200)
        self.assertEqual(result["totals"]["party_value"]["status"], "partial")
        self.assertIsNone(result["totals"]["party_value"]["amount_cents"])
        difference = next(
            item for item in result["differences"] if item["id"] == "party_vs_opposing_value"
        )
        self.assertEqual(values_by_asset(difference)[ASSET]["amount_cents"], -400)
        self.assertEqual(difference["known_subtotal_cents"], -400)

    def test_later_attempt_keeps_current_prior_and_counteroffer_series_distinct(self):
        prior = {
            "attempt_ordinal": 1,
            "proposal_version_ordinal": 2,
            "user_proposed_values": [
                {"asset_id": ASSET, "proposed_amount_cents": 2500},
            ],
            "counteroffer": {
                "source": "mediator_reported",
                "recorded_at": "2026-01-02T03:04:05+00:00",
                "verified_by_app": False,
                "values": [{"asset_id": ASSET, "amount_cents": 1800}],
            },
        }
        result = build_offer_comparison(
            attempt_ordinal=2,
            proposal_version_ordinal=1,
            finalized=False,
            offer_origin="counteroffer_response",
            snapshot=snapshot(),
            scenario_result=snapshot()["scenario"]["result"],
            editable_state={
                "proposed_values": [{"asset_id": ASSET, "proposed_amount_cents": 2200}],
            },
            prior_attempt=prior,
            current_counteroffer=None,
        )

        series = {item["id"]: item for item in result["series"]}
        self.assertEqual(series["current_proposal"]["attempt_ordinal"], 2)
        self.assertEqual(series["current_proposal"]["proposal_version_ordinal"], 1)
        self.assertEqual(values_by_asset(series["current_proposal"])[ASSET]["amount_cents"], 2200)
        self.assertEqual(series["prior_proposal"]["attempt_ordinal"], 1)
        self.assertEqual(series["prior_proposal"]["proposal_version_ordinal"], 2)
        self.assertEqual(values_by_asset(series["prior_proposal"])[ASSET]["amount_cents"], 2500)
        self.assertEqual(series["counteroffer"]["source"], "mediator_reported")
        self.assertEqual(values_by_asset(series["counteroffer"])[ASSET]["amount_cents"], 1800)
        self.assertFalse(series["current_response_counteroffer"]["available"])
        self.assertEqual(
            values_by_asset(series["projected_if_accepted"])[ASSET]["amount_cents"],
            1800,
        )
        self.assertFalse(series["projected_if_accepted"]["verified_by_app"])
        self.assertEqual(series["counteroffer"]["recorded_at"], "2026-01-02T03:04:05+00:00")
        difference = next(
            item for item in result["differences"] if item["id"] == "current_vs_prior_proposal"
        )
        self.assertEqual(values_by_asset(difference)[ASSET]["amount_cents"], -300)

    def test_new_response_counteroffer_does_not_replace_predecessor_counteroffer(self):
        prior = {
            "attempt_ordinal": 1,
            "proposal_version_ordinal": 1,
            "user_proposed_values": [{"asset_id": ASSET, "proposed_amount_cents": 2000}],
            "counteroffer": {
                "source": "mediator_reported",
                "recorded_at": "2026-01-02T03:04:05+00:00",
                "note": "The earlier reported amount",
                "values": [{"asset_id": ASSET, "amount_cents": 1800}],
            },
        }
        current_counteroffer = {
            "source": "document_reviewed",
            "recorded_at": "2026-02-02T03:04:05+00:00",
            "note": "A later response",
            "values": [{"asset_id": ASSET, "amount_cents": 1200}],
        }
        result = build_offer_comparison(
            attempt_ordinal=2,
            proposal_version_ordinal=1,
            finalized=False,
            offer_origin="counteroffer_response",
            snapshot=snapshot(),
            scenario_result=snapshot()["scenario"]["result"],
            editable_state={"proposed_values": [{"asset_id": ASSET, "proposed_amount_cents": 2200}]},
            prior_attempt=prior,
            current_counteroffer=current_counteroffer,
        )

        series = {item["id"]: item for item in result["series"]}
        self.assertEqual(values_by_asset(series["counteroffer"])[ASSET]["amount_cents"], 1800)
        self.assertEqual(
            values_by_asset(series["current_response_counteroffer"])[ASSET]["amount_cents"],
            1200,
        )
        self.assertEqual(
            values_by_asset(series["projected_if_accepted"])[ASSET]["amount_cents"],
            1800,
        )
        self.assertEqual(result["counteroffer_context"]["note"], "The earlier reported amount")
        self.assertEqual(
            result["current_response_counteroffer_context"]["note"],
            "A later response",
        )

    def test_first_attempt_counteroffer_is_compared_without_a_fake_predecessor(self):
        response = {
            "source": "mediator_reported",
            "recorded_at": "2026-03-01T00:00:00+00:00",
            "values": [{"asset_id": ASSET, "amount_cents": 1500}],
        }
        result = build_offer_comparison(
            attempt_ordinal=1,
            proposal_version_ordinal=1,
            finalized=False,
            offer_origin="initial_user_proposal",
            snapshot=snapshot(),
            scenario_result=snapshot()["scenario"]["result"],
            editable_state={"proposed_values": [{"asset_id": ASSET, "proposed_amount_cents": 1800}]},
            prior_attempt=None,
            current_counteroffer=response,
        )

        series = {item["id"]: item for item in result["series"]}
        self.assertFalse(series["prior_proposal"]["available"])
        self.assertEqual(values_by_asset(series["counteroffer"])[ASSET]["amount_cents"], 1500)
        self.assertEqual(
            values_by_asset(series["projected_if_accepted"])[ASSET]["amount_cents"],
            1500,
        )
        self.assertFalse(series["current_response_counteroffer"]["available"])

    def test_missing_values_stay_unavailable_and_build_does_not_mutate_history(self):
        prior = {
            "attempt_ordinal": 1,
            "proposal_version_ordinal": 1,
            "user_proposed_values": [],
            "counteroffer": None,
        }
        current_snapshot = snapshot()
        historical_before = deepcopy(prior)
        result = build_offer_comparison(
            attempt_ordinal=2,
            proposal_version_ordinal=1,
            finalized=True,
            offer_origin="counteroffer_response",
            snapshot=current_snapshot,
            scenario_result={},
            editable_state={"proposed_values": []},
            prior_attempt=prior,
            current_counteroffer=None,
        )

        series = {item["id"]: item for item in result["series"]}
        self.assertFalse(series["party_value"]["available"])
        self.assertFalse(series["opposing_value"]["available"])
        self.assertFalse(series["prior_proposal"]["available"])
        self.assertFalse(series["counteroffer"]["available"])
        self.assertFalse(series["projected_if_accepted"]["available"])
        self.assertEqual(prior, historical_before)
        self.assertEqual(result["attempt"]["finalized"], True)

    def test_finalized_comparison_reads_the_immutable_finalization_snapshot(self):
        finalized_state = {"proposed_values": [{"asset_id": ASSET, "proposed_amount_cents": 250}]}
        finalized_scenario = snapshot()["scenario"]["result"]
        attempt = SimpleNamespace(
            id=uuid4(),
            case_id=uuid4(),
            selection_id=uuid4(),
            attempt_ordinal=1,
            predecessor_id=None,
            sent_confirmed_at=None,
            frozen_at=None,
            finalized_at=datetime.now(UTC),
            finalized_version_ordinal=1,
            proposal_issued_at=None,
            proposal_terms_json=None,
            proposal_scenario_result_json=None,
            proposal_draft_unlocked=False,
            proposal_version_ordinal=2,
            revision=3,
            editable_state_json={
                "proposed_values": [{"asset_id": ASSET, "proposed_amount_cents": 999}],
            },
            snapshot_json=snapshot(),
            frozen_snapshot_json=None,
            finalized_snapshot_json={
                **snapshot(),
                "negotiation": finalized_state,
                "proposal_version": {"ordinal": 1},
                "scenario": {"result": finalized_scenario},
            },
        )
        selection = SimpleNamespace(
            id=attempt.selection_id,
            case_id=attempt.case_id,
            scenario_result_json={},
        )
        db = Mock()
        db.execute.return_value.all.return_value = []
        db.scalar.return_value = None
        with patch("app.offer_response._attempt_for_selection", return_value=attempt):
            finalized_snapshot_before = deepcopy(attempt.finalized_snapshot_json)
            result = _read_response(db, selection, None)

        series = {item["id"]: item for item in result.comparison["series"]}
        self.assertEqual(series["current_proposal"]["proposal_version_ordinal"], 1)
        self.assertEqual(values_by_asset(series["current_proposal"])[ASSET]["amount_cents"], 250)
        self.assertEqual(attempt.finalized_snapshot_json, finalized_snapshot_before)
