from io import BytesIO
from datetime import UTC, datetime
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4
from zipfile import ZipFile

from fastapi import HTTPException, Response
from docx import Document
from openpyxl import load_workbook
from pydantic import ValidationError

from app.offer_documents import MediationOfferTerms
from app.models import DocumentCreditLedgerEntry, SettlementProposalVersion
from app.offer_response import OfferAttemptStateUpdate, _update_attempt_proposal_documents
from app.offer_documents import render_mediation_offer_docx, render_property_schedule_xlsx
from app.settlement_planning import (
    AssetLedger,
    LedgerEvent,
    RelationshipWindow,
    ScenarioAxes,
    calculate_scenario,
    generate_scenarios,
)
from app.settlement_routes import (
    DemoExportRequest,
    OfferCreate,
    OfferDelivery,
    _delivery_request_digest,
    _destination_digest,
    create_demo_settlement_offer,
    create_demo_settlement_property_schedule,
    create_settlement_offer,
    create_settlement_property_schedule,
    deliver_settlement_offer,
)


class SettlementExportRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        window = RelationshipWindow(
            id="marriage",
            label="Marriage-only dates",
            relationship_type="marriage_only",
            start_date="2020-01-01",
            separation_date="2024-01-01",
        )
        scenario = generate_scenarios(
            ScenarioAxes(
                relationship_windows=[window],
                tracing_methods=["explicit"],
                community_share_bps=[6_000],
            )
        )[0]
        self.result = calculate_scenario(
            scenario,
            [
                AssetLedger(
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
                        )
                    ],
                )
            ],
        )
        self.terms = MediationOfferTerms(
            offer_from="Party A",
            offer_to="Party B",
            terms=["Each party retains the property listed in their column."],
        )
        self.user = SimpleNamespace(id=uuid4())
        self.case_id = uuid4()
        self.selection_id = uuid4()
        self.case = SimpleNamespace(
            profile_revision=3,
            settlement_revision=5,
            first_finalization_used=False,
            attempt_credit_balance=1,
        )
        self.selection = SimpleNamespace(
            id=self.selection_id,
            case_id=self.case_id,
            profile_revision=3,
            settlement_revision=5,
            scenario_result_json=self.result.model_dump(mode="json"),
        )
        self.attempt = SimpleNamespace(
            id=uuid4(),
            attempt_ordinal=1,
            proposal_issued_at=None,
            proposal_terms_json=None,
            proposal_scenario_result_json=None,
            proposal_version_ordinal=0,
            proposal_draft_unlocked=False,
        )
        self.settings = SimpleNamespace(
            auth_enabled=True,
            case_data_enabled=True,
            demo_mode_enabled=False,
            max_upload_bytes=2_000_000,
            auth_jwt_secret="settlement-export-test-secret-at-least-32-bytes",
            smtp_host="smtp.example.test",
            auth_email_from="casework@example.test",
        )
        self.membership = SimpleNamespace(role="owner")
        self.db = Mock()
        self.db.scalar.side_effect = [
            self.membership,
            self.case,
            self.selection,
            self.attempt,
            None,
        ]
        self.db.get.return_value = self.case

    def test_docx_and_workbook_downloads_validate_authorization_and_revisions(self) -> None:
        with (
            patch("app.settlement_routes.get_settings", return_value=self.settings),
            patch("app.settlement_routes.render_mediation_offer_docx", return_value=b"docx"),
            patch("app.settlement_routes.render_property_schedule_xlsx", return_value=b"xlsx"),
        ):
            docx = create_settlement_offer(
                self.case_id,
                self.selection_id,
                OfferCreate(terms=self.terms, confirm_credit_use=True),
                self.user,
                self.db,
            )
            version = next(
                call.args[0]
                for call in self.db.add.call_args_list
                if isinstance(call.args[0], SettlementProposalVersion)
            )
            self.db.scalar.side_effect = [
                self.membership,
                self.case,
                self.selection,
                self.attempt,
                version,
            ]
            workbook = create_settlement_property_schedule(
                self.case_id,
                self.selection_id,
                OfferCreate(terms=self.terms),
                self.user,
                self.db,
            )

        self.assertEqual(docx.body, b"docx")
        self.assertIn("no-store", docx.headers["Cache-Control"])
        self.assertEqual(workbook.body, b"xlsx")
        self.assertIn("no-store", workbook.headers["Cache-Control"])
        self.assertEqual(self.case.attempt_credit_balance, 1)
        self.assertEqual(
            sum(isinstance(call.args[0], DocumentCreditLedgerEntry)
                for call in self.db.add.call_args_list if call.args),
            0,
        )

    def test_stale_selection_is_rejected_before_render_or_delivery(self) -> None:
        self.case.profile_revision = 4
        with (
            patch("app.settlement_routes.get_settings", return_value=self.settings),
            patch("app.settlement_routes.render_mediation_offer_docx") as render_docx,
            self.assertRaises(HTTPException) as raised,
        ):
            create_settlement_offer(
                self.case_id,
                self.selection_id,
                OfferCreate(terms=self.terms, confirm_credit_use=True),
                self.user,
                self.db,
            )

        self.assertEqual(raised.exception.status_code, 409)
        render_docx.assert_not_called()

    def test_export_rejects_terms_that_do_not_match_saved_attempt_edits(self) -> None:
        self.attempt.editable_state_json = {
            "offer_from": "Party A",
            "offer_to": "Party B",
            "county": "",
            "cause_number": "",
            "proposed_effective_date": None,
            "proposed_response_date": None,
            "milestones": [],
            "proposed_values": [],
            "proposal_terms": ["Previously saved terms."],
        }
        with (
            patch("app.settlement_routes.get_settings", return_value=self.settings),
            patch("app.settlement_routes.render_mediation_offer_docx") as render_docx,
            self.assertRaises(HTTPException) as raised,
        ):
            create_settlement_offer(
                self.case_id,
                self.selection_id,
                OfferCreate(terms=self.terms, confirm_credit_use=True),
                self.user,
                self.db,
            )

        self.assertEqual(raised.exception.status_code, 409)
        render_docx.assert_not_called()

    def test_issued_terms_remain_editable_until_sent_confirmation(self) -> None:
        with (
            patch("app.settlement_routes.get_settings", return_value=self.settings),
            patch(
                "app.settlement_routes.render_mediation_offer_docx",
                return_value=b"docx",
            ) as render_docx,
            patch(
                "app.settlement_routes.render_property_schedule_xlsx",
                return_value=b"xlsx",
            ) as render_xlsx,
        ):
            docx = create_settlement_offer(
                self.case_id,
                self.selection_id,
                OfferCreate(terms=self.terms, confirm_credit_use=True),
                self.user,
                self.db,
            )
            self.assertEqual(docx.body, b"docx")
            self.assertIsNotNone(self.attempt.proposal_issued_at)
            self.attempt.attempt_ordinal = 2
            self.case.profile_revision += 1
            version = next(
                call.args[0]
                for call in self.db.add.call_args_list
                if isinstance(call.args[0], SettlementProposalVersion)
            )
            self.db.scalar.side_effect = [
                self.membership,
                self.case,
                self.selection,
                self.attempt,
                version,
            ]
            workbook = create_settlement_property_schedule(
                self.case_id,
                self.selection_id,
                OfferCreate(terms=self.terms),
                self.user,
                self.db,
            )
            self.assertEqual(workbook.body, b"xlsx")

            changed_terms = self.terms.model_copy(update={"offer_to": "Different party"})
            self.attempt.editable_state_json = {
                "offer_from": changed_terms.offer_from,
                "offer_to": changed_terms.offer_to,
                "county": changed_terms.county or "",
                "cause_number": changed_terms.court_case_number or "",
                "proposed_effective_date": changed_terms.effective_date,
                "proposed_response_date": changed_terms.response_by_date,
                "milestones": [],
                "proposed_values": [],
                "proposal_terms": changed_terms.terms,
            }
            version.terms_json = changed_terms.model_dump(mode="json")
            version.downloaded_formats = []
            self.db.scalar.side_effect = [
                self.membership,
                self.case,
                self.selection,
                self.attempt,
                version,
            ]
            updated_docx = create_settlement_offer(
                self.case_id,
                self.selection_id,
                OfferCreate(terms=changed_terms),
                self.user,
                self.db,
            )

        self.assertEqual(updated_docx.body, b"docx")
        self.assertEqual(version.terms_json, changed_terms.model_dump(mode="json"))
        self.assertEqual(version.downloaded_formats, ["docx"])
        self.assertEqual(version.credit_cost, 0)
        self.assertEqual(render_docx.call_count, 1)
        self.assertEqual(render_xlsx.call_count, 1)

    def test_export_has_no_plan_attempt_limit(self) -> None:
        self.attempt.attempt_ordinal = 2
        with (
            patch("app.settlement_routes.get_settings", return_value=self.settings),
            patch("app.settlement_routes.render_mediation_offer_docx", return_value=b"docx"),
            patch("app.settlement_routes.render_property_schedule_xlsx", return_value=b"xlsx"),
        ):
            response = create_settlement_offer(
                self.case_id,
                self.selection_id,
                OfferCreate(terms=self.terms),
                self.user,
                self.db,
            )

        self.assertEqual(response.body, b"docx")

    def test_generating_new_version_is_free_without_credit_consent(self) -> None:
        self.db.scalar.side_effect = [
            self.membership,
            self.case,
            self.selection,
            self.attempt,
            None,
        ]
        with (
            patch("app.settlement_routes.get_settings", return_value=self.settings),
            patch("app.settlement_routes.render_mediation_offer_docx", return_value=b"docx"),
            patch("app.settlement_routes.render_property_schedule_xlsx", return_value=b"xlsx"),
        ):
            response = create_settlement_offer(
                self.case_id,
                self.selection_id,
                OfferCreate(terms=self.terms),
                self.user,
                self.db,
            )
        self.assertEqual(response.body, b"docx")
        self.assertEqual(self.case.attempt_credit_balance, 1)
        self.assertEqual(
            sum(isinstance(call.args[0], DocumentCreditLedgerEntry)
                for call in self.db.add.call_args_list if call.args),
            0,
        )

    def test_failed_pair_generation_does_not_consume_credit(self) -> None:
        self.db.scalar.side_effect = [
            self.membership,
            self.case,
            self.selection,
            self.attempt,
            None,
            self.user,
        ]
        with (
            patch("app.settlement_routes.get_settings", return_value=self.settings),
            patch("app.settlement_routes.render_mediation_offer_docx", return_value=b"docx"),
            patch(
                "app.settlement_routes.render_property_schedule_xlsx",
                side_effect=ValueError("render failed"),
            ),
            self.assertRaises(HTTPException) as raised,
        ):
            create_settlement_offer(
                self.case_id,
                self.selection_id,
                OfferCreate(terms=self.terms, confirm_credit_use=True),
                self.user,
                self.db,
            )
        self.assertEqual(raised.exception.status_code, 422)
        self.assertEqual(self.case.attempt_credit_balance, 1)
        self.db.add.assert_not_called()

    def test_revised_version_is_free_without_overwriting_previous_version(self) -> None:
        self.db.scalar.side_effect = [
            self.membership,
            self.case,
            self.selection,
            self.attempt,
            None,
            self.user,
        ]
        with (
            patch("app.settlement_routes.get_settings", return_value=self.settings),
            patch("app.settlement_routes.render_mediation_offer_docx", return_value=b"docx"),
            patch("app.settlement_routes.render_property_schedule_xlsx", return_value=b"xlsx"),
        ):
            create_settlement_offer(
                self.case_id,
                self.selection_id,
                OfferCreate(terms=self.terms, confirm_credit_use=True),
                self.user,
                self.db,
            )
            previous_version = next(
                call.args[0]
                for call in self.db.add.call_args_list
                if isinstance(call.args[0], SettlementProposalVersion)
            )
            self.attempt.proposal_draft_unlocked = True
            self.attempt.proposal_version_ordinal = 2
            revised_terms = self.terms.model_copy(update={"offer_to": "Revised Party"})
            self.db.scalar.side_effect = [
                self.membership,
                self.case,
                self.selection,
                self.attempt,
                None,
            ]
            response = create_settlement_property_schedule(
                self.case_id,
                self.selection_id,
                OfferCreate(terms=revised_terms, confirm_credit_use=True),
                self.user,
                self.db,
            )
        versions = [
            call.args[0]
            for call in self.db.add.call_args_list
            if isinstance(call.args[0], SettlementProposalVersion)
        ]
        self.assertEqual(response.body, b"xlsx")
        self.assertEqual(len(versions), 2)
        self.assertEqual(previous_version.terms_json, self.terms.model_dump(mode="json"))
        self.assertEqual(versions[1].terms_json, revised_terms.model_dump(mode="json"))
        self.assertEqual(versions[1].credit_cost, 0)
        self.assertEqual(self.case.attempt_credit_balance, 1)

    def test_existing_issued_proposal_is_backfilled_without_retroactive_charge(self) -> None:
        self.attempt.proposal_issued_at = datetime.now(UTC)
        self.attempt.proposal_terms_json = self.terms.model_dump(mode="json")
        self.attempt.proposal_scenario_result_json = self.result.model_dump(mode="json")
        self.db.scalar.side_effect = [
            self.membership,
            self.case,
            self.selection,
            self.attempt,
            None,
        ]
        with (
            patch("app.settlement_routes.get_settings", return_value=self.settings),
            patch("app.settlement_routes.render_mediation_offer_docx", return_value=b"legacy-docx"),
            patch("app.settlement_routes.render_property_schedule_xlsx", return_value=b"legacy-xlsx"),
        ):
            response = create_settlement_offer(
                self.case_id,
                self.selection_id,
                OfferCreate(terms=self.terms),
                self.user,
                self.db,
            )
        version = next(
            call.args[0]
            for call in self.db.add.call_args_list
            if isinstance(call.args[0], SettlementProposalVersion)
        )
        self.assertEqual(response.body, b"legacy-docx")
        self.assertEqual(version.credit_cost, 0)
        self.assertEqual(self.case.attempt_credit_balance, 1)
        self.assertEqual(
            sum(
                isinstance(call.args[0], DocumentCreditLedgerEntry)
                for call in self.db.add.call_args_list
                if call.args
            ),
            0,
        )

    def test_demo_or_disabled_case_data_cannot_generate_documents(self) -> None:
        self.settings.demo_mode_enabled = True
        with (
            patch("app.settlement_routes.get_settings", return_value=self.settings),
            patch("app.settlement_routes.render_mediation_offer_docx") as render_docx,
            self.assertRaises(HTTPException) as raised,
        ):
            create_settlement_offer(
                self.case_id,
                self.selection_id,
                OfferCreate(terms=self.terms, confirm_credit_use=True),
                self.user,
                self.db,
            )

        self.assertEqual(raised.exception.status_code, 503)
        render_docx.assert_not_called()
        self.db.scalar.assert_not_called()

    def test_demo_documents_download_from_fictional_data_without_case_access(self) -> None:
        payload = DemoExportRequest(
            start_date="2021-06-15",
            end_date="2025-01-01",
            community_share_bps=5500,
        )
        settings = SimpleNamespace(max_upload_bytes=2_000_000)
        with patch("app.settlement_routes.get_settings", return_value=settings):
            docx = create_demo_settlement_offer(payload)
            workbook = create_demo_settlement_property_schedule(payload)

        self.assertEqual(docx.media_type, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        self.assertIn("fictional-demo-cr2a-proposal.docx", docx.headers["Content-Disposition"])
        demo_document = Document(BytesIO(docx.body))
        self.assertIn("Sam Taylor (fictional)", demo_document.tables[0].cell(0, 0).text)
        self.assertIn("Alex Taylor (fictional)", demo_document.tables[0].cell(0, 0).text)
        self.assertEqual(workbook.media_type, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.assertIn("fictional-demo-property-schedule.xlsx", workbook.headers["Content-Disposition"])
        for response, required_member in (
            (docx, "word/document.xml"),
            (workbook, "xl/workbook.xml"),
        ):
            with ZipFile(BytesIO(response.body)) as archive:
                self.assertIn(required_member, archive.namelist())
                if required_member == "word/document.xml":
                    self.assertIn("Sam Taylor (fictional)", archive.read(required_member).decode())
                    self.assertIn("Fictional home equity", archive.read(required_member).decode())

    def test_demo_export_rejects_out_of_range_dates_and_shares(self) -> None:
        with self.assertRaises(ValidationError):
            DemoExportRequest(
                start_date="2025-01-02",
                end_date="2025-01-01",
                community_share_bps=5000,
            )
        with self.assertRaises(ValidationError):
            DemoExportRequest(
                start_date="2021-01-01",
                end_date="2025-01-01",
                community_share_bps=6000,
            )

    def test_attempt_details_are_included_in_both_generated_documents(self) -> None:
        asset_id = self.result.ledgers[0].asset_id
        terms = MediationOfferTerms.model_validate({
            **self.terms.model_dump(),
            "milestones": [{"name": "Refinance deadline", "date": "2027-01-15"}],
            "proposed_values": [{"asset_id": asset_id, "proposed_amount_cents": 7500}],
        })
        docx = render_mediation_offer_docx(terms, self.result)
        workbook = render_property_schedule_xlsx(terms, self.result)

        document_text = "\n".join(
            paragraph.text for paragraph in Document(BytesIO(docx)).paragraphs
        )
        self.assertIn("Refinance deadline: 2027-01-15", document_text)
        self.assertIn("$75.00 proposed to Party A", document_text)
        schedule = load_workbook(BytesIO(workbook), data_only=False)
        row_number = 6
        self.assertEqual(schedule["Property Division"].cell(row_number, 8).value, 75)
        self.assertEqual(schedule["Property Division"].cell(row_number, 9).value, f"=G{row_number}-H{row_number}")
        self.assertEqual(schedule["Attempt Milestones"]["A2"].value, "Refinance deadline")

    def test_attempt_edits_refresh_saved_documents_and_clear_download_marks(self) -> None:
        asset_id = self.result.ledgers[0].asset_id
        previous_timestamp = datetime(2026, 1, 1, tzinfo=UTC)
        version = SimpleNamespace(
            terms_json=self.terms.model_dump(mode="json"),
            scenario_result_json=self.result.model_dump(mode="json"),
            docx_content=b"old docx",
            xlsx_content=b"old xlsx",
            downloaded_formats=["docx", "xlsx"],
            credit_cost=1,
            updated_at=previous_timestamp,
        )
        attempt = SimpleNamespace(
            id=uuid4(),
            proposal_version_ordinal=1,
            snapshot_json={"settlement_ledger": [{"asset_id": str(asset_id)}]},
            proposal_terms_json=self.terms.model_dump(mode="json"),
            proposal_scenario_result_json=self.result.model_dump(mode="json"),
        )
        payload = OfferAttemptStateUpdate(
            expected_revision=3,
            offer_from="Party A",
            offer_to="Party B",
            proposal_terms=["Updated proposal term"],
            milestones=[{"name": "Refinance deadline", "date": "2027-01-15"}],
            proposed_values=[{"asset_id": asset_id, "proposed_amount_cents": 7500}],
        )
        db = Mock()
        db.scalar.return_value = version
        with (
            patch("app.offer_response.render_mediation_offer_docx", return_value=b"new docx") as render_docx,
            patch("app.offer_response.render_property_schedule_xlsx", return_value=b"new xlsx") as render_xlsx,
            patch(
                "app.offer_response.get_settings",
                return_value=SimpleNamespace(max_upload_bytes=2_000_000),
            ),
        ):
            updated = _update_attempt_proposal_documents(
                db,
                self.user,
                self.case_id,
                self.selection,
                attempt,
                payload,
                self.result.model_dump(mode="json"),
            )

        self.assertTrue(updated)
        self.assertEqual(version.docx_content, b"new docx")
        self.assertEqual(version.xlsx_content, b"new xlsx")
        self.assertEqual(version.downloaded_formats, [])
        self.assertGreater(version.updated_at, previous_timestamp)
        self.assertEqual(version.terms_json["terms"], ["Updated proposal term"])
        rendered_terms = render_docx.call_args.args[0]
        self.assertEqual(rendered_terms.milestones[0].name, "Refinance deadline")
        self.assertEqual(rendered_terms.proposed_values[0].proposed_amount_cents, 7500)
        render_xlsx.assert_called_once()

    def test_idempotent_success_returns_existing_result_without_resending(self) -> None:
        payload = OfferDelivery(
            channel="email",
            confirm=True,
            idempotency_key=uuid4(),
            recipient="recipient@example.com",
            terms=self.terms,
        )
        version = SettlementProposalVersion(
            id=uuid4(),
            case_id=self.case_id,
            attempt_id=self.attempt.id,
            user_id_snapshot=self.user.id,
            version_ordinal=1,
            request_sha256="0" * 64,
            terms_json=self.terms.model_dump(mode="json"),
            scenario_result_json=self.result.model_dump(mode="json"),
            docx_content=b"docx",
            xlsx_content=b"xlsx",
            credit_cost=1,
        )
        prior = SimpleNamespace(
            request_sha256="",
            selection_id=self.selection_id,
            case_id=self.case_id,
            channel="email",
            destination_digest="",
            outcome="success",
            file_count=2,
        )
        with patch("app.settlement_routes.get_settings", return_value=self.settings):
            prior.request_sha256 = _delivery_request_digest(payload)
            prior.destination_digest = _destination_digest("email:recipient@example.com")
            self.attempt.proposal_issued_at = datetime.now(UTC)
            self.attempt.proposal_terms_json = self.terms.model_dump(mode="json")
            self.attempt.proposal_scenario_result_json = self.result.model_dump(mode="json")
            self.attempt.proposal_version_ordinal = 1
            self.db.scalar.side_effect = [
                self.membership,
                self.case,
                self.selection,
                self.attempt,
                version,
                prior,
            ]
            response = Response()
            with patch("app.settlement_routes.deliver_export_files") as send:
                result = deliver_settlement_offer(
                    self.case_id,
                    self.selection_id,
                    payload,
                    response,
                    self.user,
                    self.db,
                )

        self.assertEqual(result, {"outcome": "success", "file_count": 2})
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        send.assert_not_called()
        self.db.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
