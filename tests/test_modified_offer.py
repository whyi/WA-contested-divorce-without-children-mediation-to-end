import io
import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from docx import Document as WordDocument
from fastapi import HTTPException, Response
from openpyxl import Workbook

from app.models import SettlementOfferResponse, SettlementScenarioSelection
from app.offer_response import (
    OfferSentConfirmation,
    _read_response,
    confirm_offer_sent,
    download_offer_response_attachment,
    parse_uploaded_modified_offer,
)
from app.modified_offer import ModifiedOfferParseError, parse_modified_offer


def modified_docx(
    *,
    offer_from: str = "Alex Example",
    offer_to: str = "Jordan Example",
    cause_number: str = "25-2-12345-1",
) -> bytes:
    document = WordDocument()
    document.add_paragraph("IN THE SUPERIOR COURT OF THE STATE OF WASHINGTON")
    document.add_paragraph("FOR KING COUNTY")
    caption = document.add_table(rows=1, cols=2)
    caption.cell(0, 0).text = f"In re:\nProposing party: {offer_from}\nOther party: {offer_to}"
    caption.cell(0, 1).text = f"NO. {cause_number}\nCR 2A AGREEMENT"
    document.add_paragraph("Proposed effective date: 2026-03-01")
    document.add_paragraph("Proposed response deadline: 2026-03-15")
    document.add_paragraph("4.5 Proposed terms and additional settlement provisions:")
    document.add_paragraph("Transfer the vehicle by June 1.", style="List Bullet")
    document.add_paragraph("V. ALLOCATION OF DEBTS")
    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


def modified_xlsx(
    *,
    offer_from: str = "Alex Example",
    offer_to: str = "Jordan Example",
    proposed_to_user: object = 12_345.67,
    proposed_to_other: object = 8_000,
) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Property Division"
    sheet["A3"] = f"Proposing party: {offer_from}    Other party: {offer_to}"
    for column, heading in enumerate(
        (
            "Property or debt",
            "Type",
            "User separate",
            "Other party separate",
            "Community",
            "Unresolved",
            "Total",
            "Proposed to user",
            "Proposed to other party",
        ),
        1,
    ):
        sheet.cell(5, column, heading)
    sheet.cell(6, 1, "House")
    sheet.cell(6, 2, "Asset")
    sheet.cell(6, 8, proposed_to_user)
    sheet.cell(6, 9, proposed_to_other)
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


class ModifiedOfferParsingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.asset_id = uuid4()
        self.known_assets = [
            {"asset_id": str(self.asset_id), "asset_name": "House"},
        ]

    def test_imports_supported_docx_fields_and_known_user_allocation(self) -> None:
        result = parse_modified_offer(
            modified_docx(),
            modified_xlsx(),
            self.known_assets,
        )

        fields = result["editable_state"]
        self.assertEqual(fields["offer_from"], "Alex Example")
        self.assertEqual(fields["offer_to"], "Jordan Example")
        self.assertEqual(fields["county"], "KING")
        self.assertEqual(fields["cause_number"], "25-2-12345-1")
        self.assertEqual(fields["proposed_effective_date"], "2026-03-01")
        self.assertEqual(fields["proposed_response_date"], "2026-03-15")
        self.assertEqual(fields["proposal_terms"], ["Transfer the vehicle by June 1."])
        self.assertEqual(
            fields["proposed_values"],
            [{"asset_id": str(self.asset_id), "proposed_amount_cents": 1_234_567}],
        )
        self.assertTrue(any("other party" in warning for warning in result["warnings"]))

    def test_does_not_evaluate_workbook_formulas(self) -> None:
        result = parse_modified_offer(
            modified_docx(),
            modified_xlsx(proposed_to_user="=SUM(C6:F6)"),
            self.known_assets,
        )

        self.assertEqual(result["editable_state"]["proposed_values"], [])
        self.assertTrue(any("formulas" in warning for warning in result["warnings"]))

    def test_rejects_party_mismatch_between_documents(self) -> None:
        with self.assertRaisesRegex(ModifiedOfferParseError, "disagree about offer from"):
            parse_modified_offer(
                modified_docx(),
                modified_xlsx(offer_from="Different Party"),
                self.known_assets,
            )

    def test_reports_unknown_xlsx_asset_without_importing_it(self) -> None:
        result = parse_modified_offer(
            modified_docx(),
            modified_xlsx(),
            [],
        )

        self.assertEqual(result["editable_state"]["proposed_values"], [])
        self.assertTrue(any("did not match a known asset" in warning for warning in result["warnings"]))

    def test_rejects_unreadable_documents(self) -> None:
        with self.assertRaises(ModifiedOfferParseError):
            parse_modified_offer(b"not a docx", modified_xlsx(), self.known_assets)
        with self.assertRaises(ModifiedOfferParseError):
            parse_modified_offer(modified_docx(), b"not an xlsx", self.known_assets)

    def test_parse_endpoint_returns_fields_from_authorized_attempt_documents(self) -> None:
        case_id = uuid4()
        selection = SimpleNamespace(id=uuid4(), case_id=case_id)
        attempt = SimpleNamespace(snapshot_json={"settlement_ledger": self.known_assets})
        db = Mock()
        with (
            patch("app.offer_response._require_secure_case_storage"),
            patch("app.offer_response._authorized_selection", return_value=(None, selection)),
            patch("app.offer_response._attempt_for_selection", return_value=attempt),
            patch("app.offer_response._response_record", return_value=object()),
            patch(
                "app.offer_response._modified_offer_documents",
                return_value={
                    "modified_docx": modified_docx(),
                    "modified_xlsx": modified_xlsx(),
                },
            ),
        ):
            result = parse_uploaded_modified_offer(
                case_id,
                selection.id,
                Response(),
                SimpleNamespace(id=uuid4()),
                db,
            )

        self.assertEqual(result.editable_state["offer_from"], "Alex Example")
        self.assertEqual(
            result.editable_state["proposed_values"],
            [{"asset_id": str(self.asset_id), "proposed_amount_cents": 1_234_567}],
        )

    def test_parse_endpoint_checks_case_authorization_before_reading_documents(self) -> None:
        case_id = uuid4()
        denied = HTTPException(status_code=403, detail="Case is read-only.")
        with (
            patch("app.offer_response._require_secure_case_storage"),
            patch("app.offer_response._authorized_selection", side_effect=denied),
            patch("app.offer_response._modified_offer_documents") as load_documents,
        ):
            with self.assertRaises(HTTPException) as raised:
                parse_uploaded_modified_offer(
                    case_id,
                    uuid4(),
                    Response(),
                    SimpleNamespace(id=uuid4()),
                    Mock(),
                )

        self.assertEqual(raised.exception.status_code, 403)
        load_documents.assert_not_called()

    def test_modified_confirmation_requires_explicit_review(self) -> None:
        case_id = uuid4()
        selection = SimpleNamespace(id=uuid4(), case_id=case_id)
        attempt = SimpleNamespace(
            revision=0,
            frozen_at=None,
            sent_confirmed_at=None,
            editable_state_json={
                "sent_offer_mode": "modified",
                "modified_offer_reviewed": False,
            },
            snapshot_json={},
            frozen_snapshot_json=None,
        )
        current = SimpleNamespace(
            sent_documents_complete=True,
            sent_documents_current=True,
            proposal_downloaded_formats=["docx", "xlsx"],
            sent_confirmed=False,
        )
        db = Mock()
        with (
            patch("app.offer_response._require_secure_case_storage"),
            patch("app.offer_response._authorized_selection", return_value=(None, selection)),
            patch("app.offer_response._lock_case", return_value=SimpleNamespace()),
            patch("app.offer_response._selection", return_value=selection),
            patch("app.offer_response._response_record", return_value=SimpleNamespace(outcome=None)),
            patch("app.offer_response._attempt_for_selection", return_value=attempt),
            patch("app.offer_response._read_response", return_value=current),
            patch("app.offer_response._require_current_attempt_revisions"),
            patch("app.offer_response._parse_current_modified_offer") as parse_offer,
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
        parse_offer.assert_not_called()
        db.commit.assert_not_called()

    def test_modified_document_pair_is_the_complete_sent_document_set(self) -> None:
        case_id = uuid4()
        selection = SettlementScenarioSelection(
            id=uuid4(),
            case_id=case_id,
            user_id_snapshot=uuid4(),
            idempotency_key=uuid4(),
            request_sha256="test",
            run_id=uuid4(),
            scenario_id="scenario-1",
            scenario_result_json={"scenario": {}},
            profile_revision=0,
            settlement_revision=0,
        )
        attempt = SimpleNamespace(
            id=uuid4(),
            editable_state_json={"sent_offer_mode": "modified"},
            sent_confirmed_at=None,
            attempt_ordinal=1,
            frozen_at=None,
            revision=2,
            frozen_snapshot_json=None,
            snapshot_json={},
        )
        rows = [
            (
                SimpleNamespace(id=uuid4(), kind=kind, filename=f"{kind}.{extension}"),
                SimpleNamespace(extension=extension, size_bytes=20),
            )
            for kind, extension in (("modified_docx", "docx"), ("modified_xlsx", "xlsx"))
        ]
        db = Mock()
        db.execute.return_value.all.return_value = rows
        db.scalar.side_effect = [attempt, None, None]

        response_record = SettlementOfferResponse(
            id=uuid4(),
            case_id=case_id,
            selection_id=selection.id,
            user_id_snapshot=uuid4(),
            outcome=None,
        )
        result = _read_response(db, selection, response_record, 1)

        self.assertTrue(result.sent_documents_complete)
        self.assertEqual(
            {item.kind for item in result.attachments},
            {"modified_docx", "modified_xlsx"},
        )

    def test_sent_documents_are_stale_when_uploaded_before_current_draft(self) -> None:
        case_id = uuid4()
        selection = SimpleNamespace(id=uuid4(), case_id=case_id, scenario_result_json={})
        updated_at = datetime.now(UTC)
        attempt = SimpleNamespace(
            id=uuid4(),
            proposal_version_ordinal=1,
            proposal_issued_at=updated_at,
            proposal_terms_json={},
            proposal_scenario_result_json={},
            proposal_draft_unlocked=False,
            frozen_at=None,
            sent_confirmed_at=None,
            attempt_ordinal=1,
            revision=2,
            editable_state_json={"sent_offer_mode": "unchanged"},
            snapshot_json={},
            frozen_snapshot_json=None,
        )
        version = SimpleNamespace(
            updated_at=updated_at,
            downloaded_formats=["docx", "xlsx"],
        )
        old_upload_time = updated_at - timedelta(seconds=1)
        rows = [
            (
                SimpleNamespace(
                    id=uuid4(),
                    kind=kind,
                    filename=f"final.{extension}",
                    created_at=old_upload_time,
                ),
                SimpleNamespace(extension=extension, size_bytes=20),
            )
            for kind, extension in (("sent_docx", "docx"), ("sent_xlsx", "xlsx"))
        ]
        db = Mock()
        db.execute.return_value.all.return_value = rows
        db.scalar.side_effect = [attempt, version, None]

        result = _read_response(
            db,
            selection,
            SimpleNamespace(id=uuid4(), outcome=None),
            1,
        )

        self.assertTrue(result.sent_documents_complete)
        self.assertFalse(result.sent_documents_current)
        self.assertEqual(result.proposal_downloaded_formats, ["docx", "xlsx"])

    def test_attachment_download_cannot_cross_selection_boundary(self) -> None:
        case_id = uuid4()
        selection = SimpleNamespace(id=uuid4(), case_id=case_id)
        db = Mock()
        db.execute.return_value.first.return_value = None
        with (
            patch("app.offer_response._require_secure_case_storage"),
            patch("app.offer_response._authorized_selection", return_value=(None, selection)),
            patch("app.offer_response._response_record", return_value=SimpleNamespace(id=uuid4())),
            patch("app.offer_response.storage.get") as storage_get,
        ):
            with self.assertRaises(HTTPException) as raised:
                download_offer_response_attachment(
                    case_id,
                    selection.id,
                    uuid4(),
                    SimpleNamespace(id=uuid4()),
                    db,
                )

        self.assertEqual(raised.exception.status_code, 404)
        storage_get.assert_not_called()

    def test_attachment_download_returns_authorized_file_with_safe_filename(self) -> None:
        case_id = uuid4()
        selection = SimpleNamespace(id=uuid4(), case_id=case_id)
        document_id = uuid4()
        attachment = SimpleNamespace(filename="modified offer.docx")
        document = SimpleNamespace(
            object_key=f"{case_id}/offer-responses/{document_id}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        db = Mock()
        db.execute.return_value.first.return_value = (attachment, document)
        content = b"private modified offer"
        with (
            patch("app.offer_response._require_secure_case_storage"),
            patch("app.offer_response._authorized_selection", return_value=(None, selection)),
            patch("app.offer_response._response_record", return_value=SimpleNamespace(id=uuid4())),
            patch("app.offer_response.storage.get", return_value=content),
        ):
            result = download_offer_response_attachment(
                case_id,
                selection.id,
                document_id,
                SimpleNamespace(id=uuid4()),
                db,
            )

        self.assertEqual(result.body, content)
        self.assertEqual(
            result.headers["content-disposition"],
            "attachment; filename*=UTF-8''modified%20offer.docx",
        )


if __name__ == "__main__":
    unittest.main()
