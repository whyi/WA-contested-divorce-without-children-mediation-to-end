import io
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4
from zipfile import ZipFile

from fastapi import HTTPException, Response
from pydantic import ValidationError

from app.models import Document, DocumentExtraction, SettlementOfferResponseAttachment
from app.offer_response import (
    OfferOutcomeUpdate,
    _authorized_selection,
    continue_offer_response,
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
            patch("app.offer_response._response_record", return_value=record),
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

    async def test_accepted_offer_attachment_is_stored_without_extraction(self) -> None:
        case_id = uuid4()
        selection = SimpleNamespace(id=uuid4(), case_id=case_id)
        user = SimpleNamespace(id=uuid4())
        record = SimpleNamespace(id=uuid4(), outcome="accepted")
        upload = AsyncUpload("accepted-agreement.pdf", b"%PDF-1.7\naccepted agreement")
        db = Mock()
        expected = SimpleNamespace(attachments=[])

        with (
            patch("app.offer_response._require_secure_case_storage"),
            patch("app.offer_response._authorized_selection", return_value=(None, selection)),
            patch("app.offer_response._response_record", return_value=record),
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

    def test_counteroffer_continue_requires_an_attachment(self) -> None:
        selection = SimpleNamespace(id=uuid4(), case_id=uuid4())
        user = SimpleNamespace(id=uuid4())
        current = SimpleNamespace(
            sent_documents_complete=True,
            outcome="counteroffer",
            counteroffer_attachment_present=False,
        )
        with (
            patch("app.offer_response._authorized_selection", return_value=(None, selection)),
            patch("app.offer_response._response_record", return_value=object()),
            patch("app.offer_response._read_response", return_value=current),
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
            ("counteroffer", "future_placeholder"),
        ):
            current = SimpleNamespace(
                sent_documents_complete=True,
                outcome=outcome,
                counteroffer_attachment_present=True,
            )
            with (
                patch("app.offer_response._authorized_selection", return_value=(None, selection)),
                patch("app.offer_response._response_record", return_value=object()),
                patch("app.offer_response._read_response", return_value=current),
            ):
                result = continue_offer_response(
                    selection.case_id,
                    selection.id,
                    Response(),
                    user,
                    Mock(),
                )
            self.assertEqual(result["next_step"], expected)

    def test_history_returns_case_scoped_selection_and_attachment_metadata(self) -> None:
        case_id = uuid4()
        selection_id = uuid4()
        response_id = uuid4()
        user = SimpleNamespace(id=uuid4())
        offer_response = SimpleNamespace(id=response_id, outcome="accepted")
        selection = SimpleNamespace(id=selection_id, scenario_id="scenario-1")
        attachment = SimpleNamespace(
            response_id=response_id,
            kind="sent_docx",
            filename="final.docx",
        )
        query_result = Mock()
        query_result.all.return_value = [(offer_response, selection)]
        attachment_query = Mock()
        attachment_query.all.return_value = [attachment]
        db = Mock()
        db.execute.return_value = query_result
        db.scalars.return_value = attachment_query
        response = SimpleNamespace(headers={})

        result = list_settlement_offer_responses(case_id, response, user, db)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].selection_id, selection_id)
        self.assertEqual(result[0].outcome, "accepted")
        self.assertEqual(
            [item.model_dump() for item in result[0].attachments],
            [{"kind": "sent_docx", "filename": "final.docx"}],
        )
        self.assertEqual(response.headers["Cache-Control"], "no-store")

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


if __name__ == "__main__":
    unittest.main()
