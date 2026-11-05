import importlib.util
import unittest
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import HTTPException, Response
from pydantic import ValidationError

from app.counteroffer import (
    suggest_counteroffer_values,
    CounterofferValuesUpdate,
    DELIVERY_BOUNDARY,
    build_counteroffer_record,
    prior_attempt_context,
)
from app.offer_response import (
    _read_response,
    continue_offer_response,
    record_counteroffer_values,
    suggest_counteroffer_values_route,
)

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1] / "migrations" / "versions" / "0021_counteroffer_values.py"
)


def load_migration():
    spec = importlib.util.spec_from_file_location("counteroffer_migration", MIGRATION_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ASSET = str(uuid4())
NOW = datetime(2026, 11, 5, tzinfo=UTC)


class CounterofferRecordTests(unittest.TestCase):
    def test_verbal_values_need_no_document_and_are_labelled_unverified(self) -> None:
        payload = CounterofferValuesUpdate(
            expected_attempt_revision=3,
            source="mediator_reported",
            values=[{"asset_id": ASSET, "amount_cents": 125_000}],
            note="Relayed verbally",
        )
        record = build_counteroffer_record(payload, {ASSET}, NOW)
        self.assertEqual(record["source"], "mediator_reported")
        self.assertEqual(record["values"], [{"asset_id": ASSET, "amount_cents": 125_000}])
        self.assertFalse(record["verified_by_app"])

    def test_document_source_requires_explicit_review(self) -> None:
        with self.assertRaises(ValidationError):
            CounterofferValuesUpdate(
                expected_attempt_revision=0,
                source="document_reviewed",
                values=[{"asset_id": ASSET, "amount_cents": 1}],
                reviewed=False,
            )

    def test_rejects_unknown_asset_duplicates_and_extra_fields(self) -> None:
        payload = CounterofferValuesUpdate(
            expected_attempt_revision=0,
            source="mediator_reported",
            values=[{"asset_id": str(uuid4()), "amount_cents": 1}],
        )
        with self.assertRaises(HTTPException) as raised:
            build_counteroffer_record(payload, {ASSET}, NOW)
        self.assertEqual(raised.exception.status_code, 422)
        with self.assertRaises(ValidationError):
            CounterofferValuesUpdate(
                expected_attempt_revision=0,
                source="mediator_reported",
                values=[
                    {"asset_id": ASSET, "amount_cents": 1},
                    {"asset_id": ASSET, "amount_cents": 2},
                ],
            )
        with self.assertRaises(ValidationError):
            CounterofferValuesUpdate(
                expected_attempt_revision=0, source="ai", values=[], extra_field=1
            )

    def test_delivery_boundary_never_claims_verification_or_opposing_party_send(self) -> None:
        self.assertEqual(DELIVERY_BOUNDARY["recipient"], "mediator")
        self.assertFalse(DELIVERY_BOUNDARY["sent_to_opposing_party"])
        self.assertFalse(DELIVERY_BOUNDARY["delivery_verified_by_app"])
        self.assertFalse(DELIVERY_BOUNDARY["response_verified_by_app"])

    def test_prior_attempt_context_keeps_sides_distinct(self) -> None:
        predecessor = SimpleNamespace(
            attempt_ordinal=1,
            editable_state_json={"proposed_values": [{"asset_id": ASSET, "proposed_amount_cents": 5}]},
        )
        record = {"source": "mediator_reported", "values": [{"asset_id": ASSET, "amount_cents": 9}]}
        context = prior_attempt_context(predecessor, "counteroffer", record)
        self.assertEqual(context["attempt_ordinal"], 1)
        self.assertEqual(context["user_proposed_values"][0]["proposed_amount_cents"], 5)
        self.assertEqual(context["counteroffer"]["values"][0]["amount_cents"], 9)
        self.assertEqual(context["outcome"], "counteroffer")


class RecordRouteTests(unittest.TestCase):
    def _run(self, *, outcome="counteroffer", revision=4, next_exists=False, expected=4):
        case_id = uuid4()
        selection = SimpleNamespace(id=uuid4(), case_id=case_id)
        response_record = SimpleNamespace(counteroffer_json=None)
        attempt = SimpleNamespace(
            id=uuid4(),
            revision=revision,
            snapshot_json={"settlement_ledger": [{"asset_id": ASSET}]},
        )
        current = SimpleNamespace(outcome=outcome, has_next_attempt=next_exists)
        db = Mock()
        payload = CounterofferValuesUpdate(
            expected_attempt_revision=expected,
            source="mediator_reported",
            values=[{"asset_id": ASSET, "amount_cents": 7}],
        )
        with (
            patch("app.offer_response._authorized_selection", return_value=(SimpleNamespace(id=case_id), selection)),
            patch("app.offer_response._lock_case"),
            patch("app.offer_response._selection", return_value=selection),
            patch("app.offer_response._response_record", return_value=response_record),
            patch("app.offer_response._attempt_for_selection", return_value=attempt),
            patch("app.offer_response._read_response", return_value=current),
        ):
            result = record_counteroffer_values(
                case_id, selection.id, payload, Response(), SimpleNamespace(id=uuid4()), db
            )
        return result, response_record, db

    def test_records_values_on_response_without_changing_attempt_revision(self) -> None:
        _, response_record, db = self._run()
        self.assertEqual(response_record.counteroffer_json["values"][0]["amount_cents"], 7)
        db.commit.assert_called_once()

    def test_requires_counteroffer_outcome(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            self._run(outcome="rejected")
        self.assertEqual(raised.exception.status_code, 409)

    def test_stale_revision_conflicts(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            self._run(expected=1)
        self.assertEqual(raised.exception.status_code, 409)

    def test_locked_once_next_attempt_exists(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            self._run(next_exists=True)
        self.assertEqual(raised.exception.status_code, 409)


class ContinueWithManualCounterofferTests(unittest.TestCase):
    def test_manual_values_satisfy_counteroffer_continue_without_attachment(self) -> None:
        case_id = uuid4()
        selection = SimpleNamespace(id=uuid4(), case_id=case_id)
        case = SimpleNamespace(id=case_id)
        attempt = SimpleNamespace(id=uuid4(), frozen_at=object())
        next_attempt = SimpleNamespace(selection_id=uuid4(), attempt_ordinal=2)
        current = SimpleNamespace(
            sent_documents_complete=True,
            sent_confirmed=True,
            outcome="counteroffer",
            counteroffer_attachment_present=False,
            counteroffer={"source": "mediator_reported", "values": []},
        )
        db = Mock()
        db.scalar.return_value = next_attempt
        with (
            patch("app.offer_response._authorized_selection", return_value=(case, selection)),
            patch("app.offer_response._selection", return_value=selection),
            patch("app.offer_response._response_record", return_value=object()),
            patch("app.offer_response._read_response", return_value=current),
            patch("app.offer_response._attempt_for_selection", return_value=attempt),
            patch("app.offer_response._lock_case", return_value=case),
            patch("app.offer_response._require_current_attempt_revisions"),
        ):
            result = continue_offer_response(
                case_id, selection.id, Response(), SimpleNamespace(id=uuid4()), db
            )
        self.assertEqual(result["next_step"], "next_attempt")

    def test_counteroffer_without_document_or_values_is_still_blocked(self) -> None:
        case_id = uuid4()
        selection = SimpleNamespace(id=uuid4(), case_id=case_id)
        current = SimpleNamespace(
            sent_documents_complete=True,
            sent_confirmed=True,
            outcome="counteroffer",
            counteroffer_attachment_present=False,
            counteroffer=None,
        )
        with (
            patch("app.offer_response._authorized_selection", return_value=(SimpleNamespace(id=case_id), selection)),
            patch("app.offer_response._selection", return_value=selection),
            patch("app.offer_response._response_record", return_value=object()),
            patch("app.offer_response._read_response", return_value=current),
            patch("app.offer_response._lock_case"),
        ):
            with self.assertRaises(HTTPException) as raised:
                continue_offer_response(
                    case_id, selection.id, Response(), SimpleNamespace(id=uuid4()), Mock()
                )
        self.assertEqual(raised.exception.status_code, 409)


class ReadResponseTests(unittest.TestCase):
    def test_read_exposes_boundary_counteroffer_and_rejection_choices(self) -> None:
        selection = SimpleNamespace(id=uuid4(), case_id=uuid4(), scenario_result_json={})
        record = SimpleNamespace(
            id=uuid4(), outcome="rejected", counteroffer_json=None
        )
        attempt = SimpleNamespace(
            attempt_ordinal=1, id=uuid4(), predecessor_id=None, sent_confirmed_at=NOW,
            frozen_at=NOW, finalized_at=None, finalized_version_ordinal=None,
            proposal_issued_at=None, proposal_terms_json=None,
            proposal_scenario_result_json=None, proposal_draft_unlocked=False,
            proposal_version_ordinal=0, revision=2,
            editable_state_json={}, snapshot_json={}, frozen_snapshot_json=None,
        )
        db = Mock()
        db.execute.return_value.all.return_value = []
        db.scalar.return_value = None
        with patch("app.offer_response._attempt_for_selection", return_value=attempt):
            result = _read_response(db, selection, record)
        self.assertEqual(result.delivery["recipient"], "mediator")
        self.assertFalse(result.delivery["delivery_verified_by_app"])
        self.assertIsNone(result.counteroffer)
        self.assertIsNone(result.prior_attempt)
        self.assertEqual(result.outcome_choices, ["next_attempt", "stop_case"])


class SuggestionTests(unittest.TestCase):
    def test_xlsx_suggestions_are_unadopted_and_unmatched_rows_are_reported(self) -> None:
        from test_modified_offer import modified_xlsx

        result = suggest_counteroffer_values(
            "xlsx", modified_xlsx(), [{"asset_id": ASSET, "asset_name": "House"}]
        )
        self.assertEqual(result["suggestions"], [{"asset_id": ASSET, "amount_cents": 1_234_567}])
        self.assertFalse(result["adopted"])
        self.assertEqual(result["source"], "document_analysis")
        none = suggest_counteroffer_values("xlsx", modified_xlsx(), [])
        self.assertEqual(none["suggestions"], [])
        self.assertTrue(none["warnings"])

    def test_unsupported_formats_direct_user_to_manual_entry(self) -> None:
        result = suggest_counteroffer_values("pdf", b"%PDF", [])
        self.assertEqual(result["suggestions"], [])
        self.assertIn("manually", " ".join(result["warnings"]))


class SuggestionRouteTests(unittest.TestCase):
    def _call(self, rows, outcome="counteroffer"):
        case_id = uuid4()
        selection = SimpleNamespace(id=uuid4(), case_id=case_id)
        attempt = SimpleNamespace(snapshot_json={"settlement_ledger": [{"asset_id": ASSET, "asset_name": "House"}]})
        db = Mock()
        db.execute.return_value.all.return_value = rows
        with (
            patch("app.offer_response._authorized_selection", return_value=(SimpleNamespace(id=case_id), selection)),
            patch("app.offer_response._selection", return_value=selection),
            patch("app.offer_response._response_record", return_value=SimpleNamespace(id=uuid4(), outcome=outcome)),
            patch("app.offer_response._attempt_for_selection", return_value=attempt),
            patch("app.offer_response.storage") as storage,
        ):
            storage.get.return_value = b"%PDF"
            result = suggest_counteroffer_values_route(
                case_id, selection.id, Response(), SimpleNamespace(id=uuid4()), db
            )
        return result, db

    def test_requires_uploaded_counteroffer_and_never_writes(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            self._call([])
        self.assertEqual(raised.exception.status_code, 409)

    def test_returns_unadopted_suggestions_without_commit(self) -> None:
        attachment = SimpleNamespace(filename="c.pdf")
        document = SimpleNamespace(extension="pdf", object_key="k")
        with patch("app.offer_response.validate_upload"):
            result, db = self._call([(attachment, document)])
        self.assertFalse(result["adopted"])
        db.commit.assert_not_called()


class MigrationTests(unittest.TestCase):
    def test_adds_and_drops_counteroffer_column(self) -> None:
        migration = load_migration()
        self.assertEqual(migration.down_revision, "0020_attempt_credit_packages")
        self.assertLessEqual(len(migration.revision), 32)
        operations = Mock()
        with patch.object(migration, "op", operations):
            migration.upgrade()
            migration.downgrade()
        self.assertEqual(operations.add_column.call_args.args[0], "settlement_offer_responses")
        operations.drop_column.assert_called_once_with("settlement_offer_responses", "counteroffer_json")


if __name__ == "__main__":
    unittest.main()


class CounterofferUiTests(unittest.TestCase):
    def test_page_has_manual_entry_review_gate_and_mediator_only_notice(self) -> None:
        html = (Path(__file__).resolve().parents[1] / "src/app/static/index.html").read_text()
        for marker in (
            "settlement-counteroffer-rows",
            "settlement-counteroffer-reviewed",
            "counteroffer-values/suggestions",
            "settlement-response-stop-choice",
            "never sends anything to the other party",
        ):
            self.assertIn(marker, html)
