from copy import deepcopy
import io
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4
from zipfile import ZipFile

from fastapi import HTTPException, Response
from pydantic import ValidationError

from app.models import (
    Document,
    DocumentExtraction,
    SettlementNegotiationAttempt,
    SettlementOfferResponseAttachment,
    SettlementScenarioSelection,
)
from app.offer_response import (
    OfferOutcomeUpdate,
    OfferAttemptStateUpdate,
    OfferSentConfirmation,
    _authorized_selection,
    _create_initial_attempt,
    confirm_offer_sent,
    continue_offer_response,
    update_offer_attempt_state,
    update_offer_response,
    upload_offer_response_attachment,
)
from app.settlement_routes import list_settlement_offer_responses


def make_docx() -> bytes:
    output = io.BytesIO()
    with ZipFile(output, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")
    return output.getvalue()


def make_xlsx() -> bytes:
    output = io.BytesIO()
    with ZipFile(output, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("xl/workbook.xml", "<workbook/>")
    return output.getvalue()


class AsyncUpload:
    def __init__(self, filename: str, content: bytes) -> None:
        self.filename = filename
        self.content = content
        self.closed = False

    async def read(self, size: int) -> bytes:
        return self.content[:size]

    async def close(self) -> None:
        self.closed = True


class OfferResponseAuthorizationTests(unittest.TestCase):
    def test_case_write_authorization_precedes_selection_lookup(self) -> None:
        user = SimpleNamespace(id=uuid4())
        db = Mock()
        denied = HTTPException(status_code=403, detail="Case is read-only.")

        with (
            patch("app.offer_response._authorize_case", side_effect=denied),
            patch("app.offer_response._selection") as selection_lookup,
        ):
            with self.assertRaises(HTTPException) as raised:
                _authorized_selection(uuid4(), uuid4(), user, db, write=True)

        self.assertEqual(raised.exception.status_code, 403)
        selection_lookup.assert_not_called()


class OfferResponseUploadTests(unittest.IsolatedAsyncioTestCase):
    async def test_uploaded_final_file_is_stored_without_extraction_or_delivery(self) -> None:
        case_id = uuid4()
        selection = SimpleNamespace(id=uuid4(), case_id=case_id)
        user = SimpleNamespace(id=uuid4())
        record = SimpleNamespace(id=uuid4(), outcome=None)
        upload = AsyncUpload("final-property-schedule.xlsx", make_xlsx())
        db = Mock()
        existing_rows = Mock()
        existing_rows.all.return_value = []
        db.scalars.return_value = existing_rows
        expected = SimpleNamespace(sent_documents_complete=True)

        with (
            patch("app.offer_response._require_secure_case_storage"),
            patch("app.offer_response._authorized_selection", return_value=(None, selection)),
            patch("app.offer_response._lock_case", return_value=SimpleNamespace(id=case_id)),
            patch("app.offer_response._response_record", return_value=record),
            patch("app.offer_response._attempt_for_selection", return_value=None),
            patch("app.offer_response._read_response", return_value=expected),
            patch("app.offer_response.storage.put") as store,
            patch("app.offer_response.storage.delete") as delete,
            patch("app.settlement_routes.rank_settlement_scenarios") as rank,
            patch("app.settlement_routes.deliver_export_files") as deliver,
        ):
            result = await upload_offer_response_attachment(
                case_id,
                selection.id,
                "sent_xlsx",
                Response(),
                upload,
                user,
                db,
            )

        self.assertIs(result, expected)
        self.assertTrue(upload.closed)
        key, content, media_type = store.call_args.args
        self.assertTrue(key.startswith(f"{case_id}/offer-responses/"))
        self.assertEqual(content, upload.content)
        self.assertEqual(
            media_type,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        stored_models = [call.args[0] for call in db.add.call_args_list]
        self.assertTrue(any(isinstance(item, Document) for item in stored_models))
        self.assertTrue(any(isinstance(item, SettlementOfferResponseAttachment) for item in stored_models))
        self.assertFalse(any(isinstance(item, DocumentExtraction) for item in stored_models))
        delete.assert_not_called()
        rank.assert_not_called()
        deliver.assert_not_called()

    async def test_confirmed_attempt_rejects_replacing_sent_files(self) -> None:
        case_id = uuid4()
        selection = SimpleNamespace(id=uuid4(), case_id=case_id)
        user = SimpleNamespace(id=uuid4())
        attempt = SimpleNamespace(frozen_at=object())
        with (
            patch("app.offer_response._require_secure_case_storage"),
            patch("app.offer_response._authorized_selection", return_value=(None, selection)),
            patch("app.offer_response._lock_case", return_value=SimpleNamespace(id=case_id)),
            patch(
                "app.offer_response._response_record",
                return_value=SimpleNamespace(outcome=None),
            ),
            patch("app.offer_response._attempt_for_selection", return_value=attempt),
            patch("app.offer_response.storage.put") as store,
        ):
            with self.assertRaises(HTTPException) as raised:
                await upload_offer_response_attachment(
                    case_id,
                    selection.id,
                    "sent_docx",
                    Response(),
                    AsyncUpload("replacement.docx", make_docx()),
                    user,
                    Mock(),
                )
        self.assertEqual(raised.exception.status_code, 409)
        store.assert_not_called()

    async def test_accepted_offer_attachment_is_stored_without_extraction(self) -> None:
        case_id = uuid4()
        selection = SimpleNamespace(id=uuid4(), case_id=case_id)
        user = SimpleNamespace(id=uuid4())
        record = SimpleNamespace(id=uuid4(), outcome="accepted")
        upload = AsyncUpload("accepted-agreement.pdf", b"%PDF-1.7\naccepted agreement")
        db = Mock()
        db.scalar.return_value = None
        expected = SimpleNamespace(attachments=[])

        with (
            patch("app.offer_response._require_secure_case_storage"),
            patch("app.offer_response._authorized_selection", return_value=(None, selection)),
            patch("app.offer_response._lock_case", return_value=SimpleNamespace(id=case_id)),
            patch("app.offer_response._response_record", return_value=record),
            patch("app.offer_response._attempt_for_selection", return_value=None),
            patch("app.offer_response._read_response", return_value=expected),
            patch("app.offer_response.storage.put") as store,
        ):
            result = await upload_offer_response_attachment(
                case_id,
                selection.id,
                "accepted_offer",
                Response(),
                upload,
                user,
                db,
            )

        self.assertIs(result, expected)
        self.assertTrue(upload.closed)
        stored_models = [call.args[0] for call in db.add.call_args_list]
        self.assertTrue(any(isinstance(item, Document) for item in stored_models))
        accepted = [
            item
            for item in stored_models
            if isinstance(item, SettlementOfferResponseAttachment)
        ]
        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0].kind, "accepted_offer")
        store.assert_called_once()

    async def test_rejects_wrong_final_file_type_before_storage(self) -> None:
        case_id = uuid4()
        selection = SimpleNamespace(id=uuid4(), case_id=case_id)
        user = SimpleNamespace(id=uuid4())
        upload = AsyncUpload("not-a-workbook.docx", make_docx())

        with (
            patch("app.offer_response._require_secure_case_storage"),
            patch("app.offer_response._authorized_selection", return_value=(None, selection)),
            patch("app.offer_response.storage.put") as store,
        ):
            with self.assertRaises(HTTPException) as raised:
                await upload_offer_response_attachment(
                    case_id,
                    selection.id,
                    "sent_xlsx",
                    Response(),
                    upload,
                    user,
                    Mock(),
                )

        self.assertEqual(raised.exception.status_code, 415)
        self.assertTrue(upload.closed)
        store.assert_not_called()

    async def test_unauthorized_upload_never_reaches_storage(self) -> None:
        denied = HTTPException(status_code=404, detail="Case not found.")
        with (
            patch("app.offer_response._require_secure_case_storage"),
            patch("app.offer_response._authorized_selection", side_effect=denied),
            patch("app.offer_response.storage.put") as store,
        ):
            with self.assertRaises(HTTPException):
                await upload_offer_response_attachment(
                    uuid4(),
                    uuid4(),
                    "counteroffer",
                    Response(),
                    AsyncUpload("response.pdf", b"%PDF-1.7\n"),
                    SimpleNamespace(id=uuid4()),
                    Mock(),
                )
        store.assert_not_called()


class OfferResponseTransitionTests(unittest.TestCase):
    def test_only_the_three_requested_outcomes_are_accepted(self) -> None:
        for outcome in ("counteroffer", "rejected", "accepted"):
            self.assertEqual(OfferOutcomeUpdate(outcome=outcome).outcome, outcome)
        with self.assertRaises(ValidationError):
            OfferOutcomeUpdate(outcome="withdrawn")

    def test_initial_attempt_uses_server_built_snapshot_and_first_ordinal(self) -> None:
        case = SimpleNamespace(id=uuid4())
        selection = SimpleNamespace(id=uuid4())
        user = SimpleNamespace(id=uuid4())
        snapshot = {
            "scenario": {
                "result": {
                    "scenario": {
                        "relationship_window": {"id": "window-1"},
                        "tracing_method": "explicit",
                        "community_share_bps": 5_000,
                    }
                }
            }
        }
        db = Mock()
        db.scalar.return_value = None
        with patch("app.offer_response._attempt_snapshot", return_value=snapshot):
            attempt = _create_initial_attempt(db, case, selection, user)
        self.assertEqual(attempt.attempt_ordinal, 1)
        self.assertEqual(attempt.snapshot_json, snapshot)
        self.assertEqual(
            attempt.editable_state_json["scenario_assumptions"],
            {
                "relationship_windows": [{"id": "window-1"}],
                "tracing_methods": ["explicit"],
                "community_share_bps": [5_000],
            },
        )
        self.assertEqual(db.add.call_count, 2)

    def test_counteroffer_continue_requires_an_attachment(self) -> None:
        selection = SimpleNamespace(id=uuid4(), case_id=uuid4())
        user = SimpleNamespace(id=uuid4())
        current = SimpleNamespace(
            sent_documents_complete=True,
            sent_confirmed=True,
            outcome="counteroffer",
            counteroffer_attachment_present=False,
        )
        with (
            patch("app.offer_response._authorized_selection", return_value=(None, selection)),
            patch("app.offer_response._response_record", return_value=object()),
            patch("app.offer_response._read_response", return_value=current),
            patch("app.offer_response._attempt_for_selection", return_value=SimpleNamespace(
                id=uuid4(), frozen_at=object()
            )),
            patch("app.offer_response._lock_case"),
        ):
            with self.assertRaises(HTTPException) as raised:
                continue_offer_response(selection.case_id, selection.id, Response(), user, Mock())
        self.assertEqual(raised.exception.status_code, 409)

    def test_acceptance_leads_only_to_checklist_and_rejection_to_placeholder(self) -> None:
        selection = SimpleNamespace(id=uuid4(), case_id=uuid4())
        user = SimpleNamespace(id=uuid4())
        for outcome, expected in (
            ("accepted", "final_checklist"),
            ("rejected", "future_placeholder"),
        ):
            current = SimpleNamespace(
                sent_documents_complete=True,
                sent_confirmed=True,
                outcome=outcome,
                counteroffer_attachment_present=True,
            )
            attempt = SimpleNamespace(id=uuid4(), frozen_at=object())
            with (
                patch("app.offer_response._authorized_selection", return_value=(None, selection)),
                patch("app.offer_response._response_record", return_value=object()),
                patch("app.offer_response._read_response", return_value=current),
                patch("app.offer_response._attempt_for_selection", return_value=attempt),
                patch("app.offer_response._lock_case"),
            ):
                result = continue_offer_response(
                    selection.case_id,
                    selection.id,
                    Response(),
                    user,
                    Mock(),
                )
            self.assertEqual(result["next_step"], expected)

    def test_counteroffers_create_unbounded_independent_attempt_copies(self) -> None:
        case_id = uuid4()
        user = SimpleNamespace(id=uuid4())
        case = SimpleNamespace(id=case_id, profile_revision=2, settlement_revision=5)
        current = SimpleNamespace(
            sent_documents_complete=True,
            sent_confirmed=True,
            outcome="counteroffer",
            counteroffer_attachment_present=True,
        )
        attempt = SimpleNamespace(
            id=uuid4(),
            frozen_at=object(),
            attempt_ordinal=1,
            selection_id=uuid4(),
            snapshot_json={
                "revisions": {"profile": 2, "settlement": 5},
                "scenario": {"result": {"scenario": {"id": "saved"}}},
            },
            frozen_snapshot_json={
                "frozen": {"baseline": "unchanged"},
                "revisions": {"profile": 2, "settlement": 5},
                "scenario": {"result": {"scenario": {"id": "saved"}}},
            },
            editable_state_json={"proposal_terms": ["Initial term"]},
        )
        attempts = [attempt]
        for expected_ordinal in (2, 3, 4):
            selection = SimpleNamespace(
                id=attempt.selection_id,
                case_id=case_id,
                run_id=uuid4(),
                scenario_id="saved-scenario",
            )
            db = Mock()
            db.scalar.return_value = None
            with (
                patch("app.offer_response._authorized_selection", return_value=(case, selection)),
                patch("app.offer_response._lock_case", return_value=case),
                patch("app.offer_response._selection", return_value=selection),
                patch("app.offer_response._response_record", return_value=object()),
                patch("app.offer_response._read_response", return_value=current),
                patch("app.offer_response._attempt_for_selection", return_value=attempt),
            ):
                result = continue_offer_response(
                    case_id,
                    selection.id,
                    Response(),
                    user,
                    db,
                )
            self.assertEqual(result["next_step"], "next_attempt")
            self.assertEqual(result["attempt_ordinal"], expected_ordinal)
            created = [call.args[0] for call in db.add.call_args_list]
            next_selection = next(
                item for item in created if isinstance(item, SettlementScenarioSelection)
            )
            next_attempt = next(
                item for item in created if isinstance(item, SettlementNegotiationAttempt)
            )
            self.assertEqual(next_attempt.predecessor_id, attempt.id)
            self.assertEqual(next_attempt.snapshot_json, attempt.frozen_snapshot_json)
            self.assertIsNot(next_attempt.snapshot_json, attempt.frozen_snapshot_json)
            self.assertEqual(next_attempt.editable_state_json, attempt.editable_state_json)
            self.assertIsNot(next_attempt.editable_state_json, attempt.editable_state_json)
            self.assertEqual(next_selection.scenario_result_json, attempt.snapshot_json["scenario"]["result"])
            parent_editable_state = deepcopy(attempt.editable_state_json)
            next_attempt.editable_state_json["proposal_terms"].append(
                f"Edit on attempt {expected_ordinal}"
            )
            self.assertEqual(attempt.editable_state_json, parent_editable_state)
            attempt = next_attempt
            attempt.frozen_at = object()
            attempt.sent_confirmed_at = object()
            attempt.frozen_snapshot_json = deepcopy(attempt.snapshot_json)
            attempts.append(attempt)

        self.assertEqual([item.attempt_ordinal for item in attempts], [1, 2, 3, 4])

    def test_counteroffer_outcome_requires_prior_sent_confirmation(self) -> None:
        case_id = uuid4()
        selection = SimpleNamespace(
            id=uuid4(),
            case_id=case_id,
            run_id=uuid4(),
            scenario_id="saved-scenario",
            scenario_result_json={"scenario": {"id": "saved-scenario"}},
        )
        case = SimpleNamespace(profile_revision=3, settlement_revision=8)
        response_record = SimpleNamespace(outcome=None)
        attempt = SimpleNamespace(
            id=uuid4(),
            frozen_at=None,
            sent_confirmed_at=None,
            revision=2,
            snapshot_json={
                "revisions": {"profile": 3, "settlement": 8},
                "scenario": {"objective": "Keep property assumptions explicit"},
            },
            editable_state_json={"proposal_terms": ["One year to refinance"]},
            frozen_snapshot_json=None,
        )
        current = SimpleNamespace(
            sent_documents_complete=True,
            attachments=[
                SimpleNamespace(kind="sent_docx", model_dump=lambda **_: {"kind": "sent_docx"}),
                SimpleNamespace(kind="sent_xlsx", model_dump=lambda **_: {"kind": "sent_xlsx"}),
            ],
        )
        expected = SimpleNamespace()
        db = Mock()
        with (
            patch("app.offer_response._authorized_selection", return_value=(case, selection)),
            patch("app.offer_response._lock_case", return_value=case),
            patch("app.offer_response._response_record", return_value=response_record),
            patch("app.offer_response._read_response", return_value=current),
            patch("app.offer_response._attempt_for_selection", return_value=attempt),
        ):
            with self.assertRaises(HTTPException) as raised:
                update_offer_response(
                    case_id,
                    selection.id,
                    OfferOutcomeUpdate(outcome="counteroffer", expected_attempt_revision=2),
                    Response(),
                    SimpleNamespace(id=uuid4()),
                    db,
                )
        self.assertEqual(raised.exception.status_code, 409)
        self.assertIsNone(response_record.outcome)
        self.assertIsNone(attempt.frozen_at)
        db.commit.assert_not_called()

    def test_explicit_sent_confirmation_freezes_attempt_snapshot(self) -> None:
        case_id = uuid4()
        user = SimpleNamespace(id=uuid4())
        selection = SimpleNamespace(
            id=uuid4(),
            case_id=case_id,
            run_id=uuid4(),
            scenario_id="saved-scenario",
            scenario_result_json={"scenario": {"id": "saved-scenario"}},
        )
        case = SimpleNamespace(profile_revision=3, settlement_revision=8)
        attempt = SimpleNamespace(
            attempt_ordinal=1,
            frozen_at=None,
            sent_confirmed_at=None,
            revision=2,
            snapshot_json={
                "revisions": {"profile": 3, "settlement": 8},
                "scenario": {"objective": "Keep property assumptions explicit"},
            },
            editable_state_json={"proposal_terms": ["One year to refinance"]},
            frozen_snapshot_json=None,
        )
        current = SimpleNamespace(
            sent_documents_complete=True,
            outcome=None,
            attachments=[
                SimpleNamespace(kind="sent_docx", model_dump=lambda **_: {"kind": "sent_docx"}),
                SimpleNamespace(kind="sent_xlsx", model_dump=lambda **_: {"kind": "sent_xlsx"}),
            ],
        )
        expected = SimpleNamespace(sent_confirmed=True, frozen=True)
        db = Mock()
        with (
            patch("app.offer_response._authorized_selection", return_value=(case, selection)),
            patch("app.offer_response._lock_case", return_value=case),
            patch("app.offer_response._response_record", return_value=SimpleNamespace(outcome=None)),
            patch("app.offer_response._read_response", side_effect=[current, expected]),
            patch("app.offer_response._attempt_for_selection", return_value=attempt),
        ):
            result = confirm_offer_sent(
                case_id,
                selection.id,
                OfferSentConfirmation(expected_attempt_revision=2),
                Response(),
                user,
                db,
            )
        self.assertIs(result, expected)
        self.assertIsNotNone(attempt.sent_confirmed_at)
        self.assertIsNotNone(attempt.frozen_at)
        self.assertEqual(
            attempt.frozen_snapshot_json["negotiation"],
            {"proposal_terms": ["One year to refinance"]},
        )
        self.assertEqual(
            attempt.frozen_snapshot_json["sent_confirmation"]["user_id_snapshot"],
            str(user.id),
        )
        self.assertEqual(
            attempt.frozen_snapshot_json["sent_attachments"],
            [{"kind": "sent_docx"}, {"kind": "sent_xlsx"}],
        )
        self.assertNotIn("outcome", attempt.frozen_snapshot_json)
        self.assertEqual(attempt.revision, 3)
        db.commit.assert_called_once()

    def test_sent_confirmation_requires_both_final_attachments(self) -> None:
        case_id = uuid4()
        selection = SimpleNamespace(id=uuid4(), case_id=case_id)
        current = SimpleNamespace(sent_documents_complete=False)
        db = Mock()
        with (
            patch("app.offer_response._authorized_selection", return_value=(None, selection)),
            patch("app.offer_response._lock_case"),
            patch("app.offer_response._selection", return_value=selection),
            patch("app.offer_response._response_record", return_value=object()),
            patch("app.offer_response._attempt_for_selection", return_value=object()),
            patch("app.offer_response._read_response", return_value=current),
        ):
            with self.assertRaises(HTTPException) as raised:
                confirm_offer_sent(
                    case_id,
                    selection.id,
                    OfferSentConfirmation(expected_attempt_revision=0),
                    Response(),
                    SimpleNamespace(id=uuid4()),
                    db,
                )
        self.assertEqual(raised.exception.status_code, 409)
        db.commit.assert_not_called()

    def test_attempt_inputs_remain_editable_after_final_documents_are_uploaded(self) -> None:
        case_id = uuid4()
        selection = SimpleNamespace(
            id=uuid4(),
            case_id=case_id,
            scenario_result_json={"scenario": {"id": "scenario-1"}},
        )
        case = SimpleNamespace(profile_revision=3, settlement_revision=8)
        attempt = SimpleNamespace(
            attempt_ordinal=1,
            frozen_at=None,
            sent_confirmed_at=None,
            revision=2,
            snapshot_json={"revisions": {"profile": 3, "settlement": 8}},
            editable_state_json={},
        )
        with (
            patch("app.offer_response._authorized_selection", return_value=(case, selection)),
            patch("app.offer_response._lock_case", return_value=case),
            patch("app.offer_response._selection", return_value=selection),
            patch("app.offer_response._attempt_for_selection", return_value=attempt),
            patch("app.offer_response._response_record", return_value=object()),
            patch("app.offer_response._read_response", return_value=SimpleNamespace(
                sent_documents_complete=True
            )),
        ):
            update_offer_attempt_state(
                case_id,
                selection.id,
                OfferAttemptStateUpdate(expected_revision=2, offer_to="Other party"),
                Response(),
                SimpleNamespace(id=uuid4()),
                db := Mock(),
            )
        self.assertEqual(attempt.editable_state_json["offer_to"], "Other party")
        self.assertEqual(attempt.revision, 3)
        db.commit.assert_called_once()

    def test_frozen_attempt_rejects_outcome_correction(self) -> None:
        case_id = uuid4()
        selection = SimpleNamespace(id=uuid4(), case_id=case_id)
        response_record = SimpleNamespace(outcome="counteroffer")
        attempt = SimpleNamespace(frozen_at=object())
        current = SimpleNamespace(sent_documents_complete=True)
        with (
            patch("app.offer_response._authorized_selection", return_value=(None, selection)),
            patch("app.offer_response._lock_case"),
            patch("app.offer_response._response_record", return_value=response_record),
            patch("app.offer_response._read_response", return_value=current),
            patch("app.offer_response._attempt_for_selection", return_value=attempt),
        ):
            with self.assertRaises(HTTPException) as raised:
                update_offer_response(
                    case_id,
                    selection.id,
                    OfferOutcomeUpdate(outcome="accepted"),
                    Response(),
                    SimpleNamespace(id=uuid4()),
                    Mock(),
                )
        self.assertEqual(raised.exception.status_code, 409)

    def test_outcome_cannot_be_recorded_until_sent_confirmation(self) -> None:
        case_id = uuid4()
        selection = SimpleNamespace(id=uuid4(), case_id=case_id)
        current = SimpleNamespace(
            sent_documents_complete=True,
            sent_confirmed=False,
        )
        attempt = SimpleNamespace(
            frozen_at=None,
            sent_confirmed_at=None,
            revision=1,
        )
        with (
            patch("app.offer_response._authorized_selection", return_value=(None, selection)),
            patch("app.offer_response._lock_case"),
            patch("app.offer_response._response_record", return_value=SimpleNamespace(outcome=None)),
            patch("app.offer_response._read_response", return_value=current),
            patch("app.offer_response._attempt_for_selection", return_value=attempt),
        ):
            with self.assertRaises(HTTPException) as raised:
                update_offer_response(
                    case_id,
                    selection.id,
                    OfferOutcomeUpdate(outcome="rejected", expected_attempt_revision=1),
                    Response(),
                    SimpleNamespace(id=uuid4()),
                    Mock(),
                )
        self.assertEqual(raised.exception.status_code, 409)

    def test_history_returns_case_scoped_selection_and_attachment_metadata(self) -> None:
        case_id = uuid4()
        selection_id = uuid4()
        response_id = uuid4()
        user = SimpleNamespace(id=uuid4())
        offer_response = SimpleNamespace(id=response_id, outcome="accepted")
        selection = SimpleNamespace(id=selection_id, scenario_id="scenario-1")
        attempt = SimpleNamespace(attempt_ordinal=1, frozen_at=object())
        attachment = SimpleNamespace(
            response_id=response_id,
            kind="sent_docx",
            filename="final.docx",
        )
        query_result = Mock()
        query_result.all.return_value = [(offer_response, selection, attempt)]
        attachment_query = Mock()
        attachment_query.all.return_value = [attachment]
        db = Mock()
        db.execute.return_value = query_result
        db.scalars.return_value = attachment_query
        response = SimpleNamespace(headers={})

        result = list_settlement_offer_responses(case_id, response, user, db)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].selection_id, selection_id)
        self.assertEqual(result[0].attempt_ordinal, 1)
        self.assertTrue(result[0].frozen)
        self.assertEqual(result[0].outcome, "accepted")
        self.assertEqual(
            [item.model_dump() for item in result[0].attachments],
            [{"kind": "sent_docx", "filename": "final.docx"}],
        )
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_attempt_state_schema_forbids_untrusted_fields(self) -> None:
        with self.assertRaises(ValidationError):
            OfferAttemptStateUpdate(
                expected_revision=0,
                arbitrary_snapshot={"scenario_result": "client supplied"},
            )

    def test_stale_attempt_revision_is_rejected(self) -> None:
        case_id = uuid4()
        selection = SimpleNamespace(id=uuid4(), case_id=case_id)
        attempt = SimpleNamespace(
            id=uuid4(),
            frozen_at=None,
            revision=3,
            snapshot_json={"revisions": {"profile": 1, "settlement": 2}},
            editable_state_json={},
        )
        with (
            patch("app.offer_response._authorized_selection", return_value=(None, selection)),
            patch(
                "app.offer_response._lock_case",
                return_value=SimpleNamespace(profile_revision=1, settlement_revision=2),
            ),
            patch("app.offer_response._selection", return_value=selection),
            patch("app.offer_response._attempt_for_selection", return_value=attempt),
            patch("app.offer_response._response_record", return_value=None),
            patch("app.offer_response._read_response", return_value=SimpleNamespace(
                sent_documents_complete=False
            )),
        ):
            with self.assertRaises(HTTPException) as raised:
                update_offer_attempt_state(
                    case_id,
                    selection.id,
                    OfferAttemptStateUpdate(expected_revision=2),
                    Response(),
                    SimpleNamespace(id=uuid4()),
                    Mock(),
                )
        self.assertEqual(raised.exception.status_code, 409)

    def test_response_history_requires_case_membership(self) -> None:
        denied = HTTPException(status_code=404, detail="Case not found.")
        db = Mock()
        with patch("app.settlement_routes._authorize_case", side_effect=denied):
            with self.assertRaises(HTTPException):
                list_settlement_offer_responses(
                    uuid4(),
                    SimpleNamespace(headers={}),
                    SimpleNamespace(id=uuid4()),
                    db,
                )
        db.execute.assert_not_called()

    def test_checklist_uses_verified_official_links_and_caveats(self) -> None:
        html = (Path(__file__).resolve().parents[1] / "src/app/static/index.html").read_text(
            encoding="utf-8"
        )
        for source in (
            "https://www.courts.wa.gov/forms/?fa=forms.contribute&amp;formID=13",
            "https://www.courts.wa.gov/forms/documents/FL%20Divorce%20231%20Findings-Conclusions-Marriage_2023%2007%2001.pdf",
            "https://kingcounty.gov/en/court/superior-court/courts-jails-legal-system/court-programs-children-families/divorce-custody-adoption/how-to-resources-family-law",
            "https://app.leg.wa.gov/RCW/default.aspx?cite=4.64.080",
        ):
            self.assertIn(source, html)
        self.assertIn("No statewide Superior Court family-law form titled", html)
        self.assertIn("for garnishment, not a generic divorce judgment", html)
        self.assertIn("signed, filed, or sufficient", html)
        self.assertIn('id="settlement-response-accepted-file"', html)
        self.assertIn('uploadSettlementResponseFile("accepted_offer", file)', html)
        self.assertIn("First Attempt — active and editable", html)
        self.assertIn('id="settlement-demo-attempt-status"', html)
        self.assertIn("First Attempt — demo preview only", html)
        self.assertIn('body[data-demo-page="settlement"] .settlement-attempt-banner', html)
        self.assertIn("position: fixed", html)
        self.assertIn("min-height: 86px", html)
        self.assertIn('document.body.dataset.demoPage = "settlement"', html)
        self.assertIn("settlementDemoAttemptOrdinal += 1", html)
        self.assertIn("settlementAttemptOrdinalLabel(settlementDemoAttemptOrdinal)", html)
        self.assertIn("counterofferNeedsFile", html)
        self.assertIn('id="settlement-response-confirm-sent"', html)
        self.assertIn("offer-response/confirm-sent", html)
        self.assertIn("I reviewed and sent these final documents", html)
        self.assertIn("current?.sent_confirmed", html)
        attempt_save = html.split("async function saveSettlementAttemptState()", 1)[1].split(
            "async function loadSettlementOfferResponse", 1
        )[0]
        self.assertLess(
            attempt_save.index("if (!settlementAttemptStateDirty) return true;"),
            attempt_save.index("settlementOfferResponseState?.sent_documents_complete"),
        )
        self.assertIn("An editable copy was opened as the next attempt", html)
        self.assertIn("Google Drive Picker is unavailable", html)


if __name__ == "__main__":
    unittest.main()
