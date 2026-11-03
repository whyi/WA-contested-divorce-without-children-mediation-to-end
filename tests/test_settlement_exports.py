from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import HTTPException, Response

from app.offer_documents import MediationOfferTerms
from app.settlement_planning import (
    AssetLedger,
    LedgerEvent,
    RelationshipWindow,
    ScenarioAxes,
    calculate_scenario,
    generate_scenarios,
)
from app.settlement_routes import (
    OfferCreate,
    OfferDelivery,
    _delivery_request_digest,
    _destination_digest,
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
        self.case = SimpleNamespace(profile_revision=3, settlement_revision=5)
        self.selection = SimpleNamespace(
            id=self.selection_id,
            case_id=self.case_id,
            profile_revision=3,
            settlement_revision=5,
            scenario_result_json=self.result.model_dump(mode="json"),
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
        self.db.scalar.side_effect = [self.membership, self.selection]
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
                OfferCreate(terms=self.terms),
                self.user,
                self.db,
            )
            self.db.scalar.side_effect = [self.membership, self.selection]
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
                OfferCreate(terms=self.terms),
                self.user,
                self.db,
            )

        self.assertEqual(raised.exception.status_code, 409)
        render_docx.assert_not_called()

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
                OfferCreate(terms=self.terms),
                self.user,
                self.db,
            )

        self.assertEqual(raised.exception.status_code, 503)
        render_docx.assert_not_called()
        self.db.scalar.assert_not_called()

    def test_idempotent_success_returns_existing_result_without_resending(self) -> None:
        payload = OfferDelivery(
            channel="email",
            confirm=True,
            idempotency_key=uuid4(),
            recipient="recipient@example.com",
            terms=self.terms,
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
            self.db.scalar.side_effect = [self.membership, self.selection, prior]
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
