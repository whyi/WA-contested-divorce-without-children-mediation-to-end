import unittest
import asyncio
from io import BytesIO
from copy import deepcopy
from uuid import uuid4
from unittest.mock import patch

from fastapi import HTTPException, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from openpyxl import Workbook

from app.asset_mediation import (
    get_mediation_state, record_download, update_mediation_state, MediationUpdate,
    upload_counteroffer,
)
from app.asset_overview import OverviewScenarioExport
from app.models import Case, Document, SettlementNegotiationAttempt
import test_attachment_limits as quota_fixtures


class AssetMediationTests(unittest.TestCase):
    def setUp(self) -> None:
        quota_fixtures.AttachmentLimitTests.setUp(self)
        for target in ("app.asset_mediation.storage", "app.main.storage"):
            item = patch(target, self.storage)
            item.start()
            self.addCleanup(item.stop)
        for target in ("app.asset_mediation._require_real_case_exports", "app.main._require_real_case_exports"):
            item = patch(target)
            item.start()
            self.addCleanup(item.stop)
        self.case.metadata_json = {"asset_overview": {
            "revision": 1, "overview": {"snapshots": [
                {"date": date, "balances": [
                    {"category": category, "you_cents": value if index == 0 else 0, "other_cents": value if index == 0 else 0}
                    for index, category in enumerate(("Home equity", "Retirement accounts", "Cash and savings", "Vehicles", "Debt"))
                ]}
                for date, value in (("2020-01-01", 10000), ("2023-01-01", 50000))
            ]},
        }}
        self.db.commit()
        self.selection = OverviewScenarioExport.model_validate({
            "expected_revision": 1, "attempt_ordinal": 1, "start_date": "2020-01-01",
            "end_date": "2023-01-01", "community_share_bps": 5000,
        })

    def tearDown(self) -> None:
        quota_fixtures.AttachmentLimitTests.tearDown(self)

    def state(self, ordinal=1):
        return get_mediation_state(self.case.id, ordinal, Response(), self.user, self.db)

    def update(self, action, ordinal=1, **extra):
        return update_mediation_state(
            self.case.id, MediationUpdate(
                expected_revision=self.state(ordinal).revision, attempt_ordinal=ordinal,
                action=action, **extra,
            ), Response(), self.user, self.db,
        )

    def send(self):
        for format in ("docx", "xlsx"):
            record_download(self.db, self.case, self.selection, format)
        return self.update("sent", selection=self.selection, confirm=True)

    def upload(self, document_id, name, content, overwrite=None):
        return asyncio.run(upload_counteroffer(
            self.case.id, 1, document_id, UploadFile(filename=name, file=BytesIO(content)),
            self.user, self.db, overwrite,
        ))

    def test_delivery_requires_both_current_downloads_and_freezes_real_snapshot_idempotently(self):
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as error:
            self.update("sent", selection=self.selection, confirm=True)
        self.assertEqual(error.exception.status_code, 409)
        record_download(self.db, self.case, self.selection, "docx")
        with self.assertRaises(HTTPException):
            self.update("sent", selection=self.selection, confirm=True)
        record_download(self.db, self.case, self.selection, "xlsx")
        self.assertTrue(self.update("sent", selection=self.selection, confirm=True).sent)
        self.assertTrue(self.update("sent", selection=self.selection, confirm=True).sent)
        attempts = self.db.scalars(select(SettlementNegotiationAttempt)).all()
        self.assertEqual(len(attempts), 1)
        self.assertIsNotNone(attempts[0].sent_confirmed_at)
        self.assertIsNotNone(attempts[0].frozen_at)
        self.assertEqual(attempts[0].frozen_snapshot_json["case_profile"]["metadata"]["asset_overview"]["revision"], 1)
        self.assertFalse(attempts[0].frozen_snapshot_json["externally_sent"])

    def test_changed_selection_resets_download_receipts_and_stale_values_cannot_be_sent(self):
        from fastapi import HTTPException
        record_download(self.db, self.case, self.selection, "docx")
        changed = self.selection.model_copy(update={"community_share_bps": 5500})
        record_download(self.db, self.case, changed, "xlsx")
        self.assertEqual(self.state().downloaded_formats, ["xlsx"])
        with self.assertRaises(HTTPException):
            self.update("sent", selection=changed, confirm=True)
        record_download(self.db, self.case, changed, "docx")
        metadata = deepcopy(self.case.metadata_json)
        metadata["asset_overview"]["revision"] = 2
        self.case.metadata_json = metadata
        self.db.commit()
        with self.assertRaises(HTTPException) as error:
            self.update("sent", selection=changed, confirm=True)
        self.assertEqual(error.exception.status_code, 409)
        self.assertFalse(self.state().sent)

    def test_free_response_persists_notes_but_cannot_create_second_attempt(self):
        from fastapi import HTTPException
        self.send()
        saved = self.update("response", outcome="counteroffer", notes="Saved counteroffer notes")
        self.assertEqual(saved.notes, "Saved counteroffer notes")
        self.assertEqual(self.state().outcome, "counteroffer")
        with self.assertRaises(HTTPException) as error:
            self.update("continue")
        self.assertEqual(error.exception.status_code, 402)
        self.assertEqual(len(self.db.scalars(select(SettlementNegotiationAttempt)).all()), 1)

    def test_paid_continuation_creates_one_next_attempt_and_preserves_prior_response(self):
        self.send()
        self.update("response", outcome="counteroffer", notes="Received proposal")
        with patch("app.asset_mediation.attachment_limit", return_value=100):
            next_state = self.update("continue")
            self.assertEqual(next_state.attempt_ordinal, 2)
            self.assertEqual(next_state.notes, "Received proposal")
            retry = self.update("continue")
            self.assertEqual(retry.attempt_ordinal, 2)
        attempts = self.db.scalars(select(SettlementNegotiationAttempt).order_by(SettlementNegotiationAttempt.attempt_ordinal)).all()
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[1].predecessor_id, attempts[0].id)
        self.assertIsNone(attempts[1].frozen_at)
        self.assertEqual(self.state(1).outcome, "counteroffer")

    def test_accepted_completion_and_rejection_stop_preserve_data_and_close_case(self):
        self.send()
        self.update("response", outcome="accepted")
        self.assertTrue(self.update("complete", confirm=True).completed)
        self.assertTrue(self.update("complete", confirm=True).completed)
        self.assertEqual(self.case.status, "finalized")
        self.assertEqual(self.case.closed_reason, "accepted")
        self.assertIsNotNone(self.case.attempts_locked_at)
        self.assertIn("asset_overview", self.case.metadata_json)

    def test_rejection_stop_uses_existing_reversible_closure(self):
        self.send()
        self.update("response", outcome="rejected")
        self.assertTrue(self.update("stop", confirm=True).stopped)
        self.assertTrue(self.update("stop", confirm=True).stopped)
        self.assertEqual(self.case.closed_reason, "stopped")
        self.assertIsNotNone(self.case.closed_at)
        self.assertIn("asset_overview", self.case.metadata_json)

    def test_reopened_accepted_case_can_close_again_without_unlocking_attempts(self):
        from app.case_lifecycle import reopen_case

        self.send()
        self.update("response", outcome="accepted")
        self.update("complete", confirm=True)
        locked_at = self.case.attempts_locked_at
        attempt = self.db.scalar(select(SettlementNegotiationAttempt))
        snapshot = deepcopy(attempt.frozen_snapshot_json)
        reopen_case(self.case.id, self.user, self.db)
        self.assertIsNone(self.case.closed_at)
        with self.assertRaises(HTTPException):
            self.update("complete", confirm=False)
        result = self.update("complete", confirm=True)
        self.assertTrue(result.completed)
        self.assertIsNotNone(self.case.closed_at)
        self.assertEqual(self.case.status, "finalized")
        self.assertEqual(self.case.closed_reason, "accepted")
        self.assertEqual(self.case.attempts_locked_at, locked_at)
        self.assertEqual(attempt.frozen_snapshot_json, snapshot)
        with self.assertRaises(HTTPException):
            self.update("response", outcome="accepted")

    def test_accepted_closure_keeps_all_attempts_read_only_after_reopen(self):
        from app.case_lifecycle import reopen_case

        self.send()
        self.update("response", outcome="accepted")
        completed = self.update("complete", confirm=True)
        self.assertTrue(completed.attempts_locked)
        self.assertIsNotNone(self.case.attempts_locked_at)

        reopen_case(self.case.id, self.user, self.db)
        self.assertTrue(self.state().attempts_locked)
        with self.assertRaises(HTTPException) as error:
            self.update("response", outcome="accepted")
        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(len(self.db.scalars(select(SettlementNegotiationAttempt)).all()), 1)

    def test_counteroffer_upload_preserves_filename_and_links_file_with_retry_identity(self):
        self.send()
        self.update("response", outcome="counteroffer")
        document_id = uuid4()
        name = "Received \uc81c\uc548.pdf"
        for _ in range(2):
            response = self.upload(document_id, name, quota_fixtures.PDF)
            self.assertEqual(response["state"]["document_ids"], [str(document_id)])
        self.assertEqual(self.db.get(Document, document_id).original_filename, name)
        self.assertEqual(len(self.stored), 1)
        self.assertEqual(self.state().document_ids, [document_id])

    def test_counteroffer_upload_rejects_other_case_documents_and_unsupported_files(self):
        self.send()
        self.update("response", outcome="counteroffer")
        with self.assertRaises(HTTPException) as error:
            self.upload(uuid4(), "bad.txt", b"text")
        self.assertEqual(error.exception.status_code, 415)
        other = Case(status="draft", metadata_json={})
        self.db.add(other)
        self.db.flush()
        document = Document(
            id=uuid4(), case_id=other.id, object_key="other.pdf", extension="pdf",
            media_type="application/pdf", sha256="f" * 64, size_bytes=1, original_filename="Other.pdf",
        )
        self.db.add(document)
        self.db.commit()
        with self.assertRaises(HTTPException) as error:
            self.upload(document.id, "Other.pdf", quota_fixtures.PDF)
        self.assertEqual(error.exception.status_code, 404)
        self.assertEqual(len(self.stored), 0)

    def test_xlsx_is_validated_stored_and_linked_to_accepted_response(self):
        self.send()
        self.update("response", outcome="accepted")
        output = BytesIO()
        Workbook().save(output)
        document_id = uuid4()
        result = self.upload(document_id, "Accepted offer.xlsx", output.getvalue())
        self.assertEqual(result["state"]["accepted_document_ids"], [str(document_id)])
        self.assertEqual(self.db.get(Document, document_id).extension, "xlsx")
        self.assertEqual(self.state().document_ids, [])

    def test_full_quota_overwrite_requires_confirmation_and_retargets_response_file(self):
        self.send()
        self.update("response", outcome="counteroffer")
        first_id = uuid4()
        self.upload(first_id, "Received.pdf", quota_fixtures.PDF)
        for _ in range(4):
            self.assertEqual(quota_fixtures.AttachmentLimitTests.upload(self).status_code, 201)
        second_id = uuid4()
        with self.assertRaises(HTTPException) as error:
            self.upload(second_id, "Received.pdf", quota_fixtures.PDF + b"new")
        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(error.exception.detail["code"], "filename_conflict")
        result = self.upload(second_id, "Received.pdf", quota_fixtures.PDF + b"new", first_id)
        self.assertEqual(result["state"]["document_ids"], [str(second_id)])
        self.assertIsNone(self.db.get(Document, first_id))
        self.assertEqual(len(self.db.scalars(select(Document)).all()), 5)

    def test_storage_failure_preserves_counteroffer_state_and_retry_identity(self):
        self.send()
        self.update("response", outcome="counteroffer", notes="Keep these notes")
        document_id = uuid4()
        original_put = self.storage.put.side_effect
        self.storage.put.side_effect = RuntimeError("Synthetic upload failure")
        with self.assertRaises(HTTPException) as error:
            self.upload(document_id, "Retry.pdf", quota_fixtures.PDF)
        self.assertEqual(error.exception.status_code, 503)
        self.assertEqual(self.state().notes, "Keep these notes")
        self.assertEqual(self.state().document_ids, [])
        self.storage.put.side_effect = original_put
        self.upload(document_id, "Retry.pdf", quota_fixtures.PDF)
        self.assertEqual(self.state().document_ids, [document_id])

    def test_stale_response_revision_and_database_failure_preserve_saved_state(self):
        self.send()
        before = self.state()
        with self.assertRaises(HTTPException) as error:
            update_mediation_state(
                self.case.id, MediationUpdate(
                    expected_revision=before.revision - 1, attempt_ordinal=1, action="response", outcome="rejected",
                ), Response(), self.user, self.db,
            )
        self.assertEqual(error.exception.status_code, 409)
        self.assertIsNone(self.state().outcome)
        with patch.object(self.db, "commit", side_effect=SQLAlchemyError("Synthetic")):
            with self.assertRaises(HTTPException) as error:
                self.update("response", outcome="accepted")
        self.assertEqual(error.exception.status_code, 503)
        self.assertIsNone(self.state().outcome)

    def test_non_members_and_non_owners_cannot_read_or_write_mediation(self):
        from types import SimpleNamespace
        for role, status in [(None, 404), ("viewer", 403)]:
            with patch("app.asset_mediation.resolve_case_access", return_value=None if role is None else SimpleNamespace(role=role)):
                with self.assertRaises(HTTPException) as error:
                    self.state()
                self.assertEqual(error.exception.status_code, status)
