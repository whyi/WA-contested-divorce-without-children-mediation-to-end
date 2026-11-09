import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import HTTPException, Response
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.existing_offer import (
    AssetTermsUpdate,
    ExistingOfferCreate,
    ExistingOfferUpdate,
    offer_origin,
    read_existing_offer,
    update_asset_terms,
    update_existing_offer,
)
from app.main import CaseCreate, create_case


DOC_ID = str(uuid4())


class ExistingOfferValidationTests(unittest.TestCase):
    def test_yes_requires_a_document_or_non_empty_notes(self) -> None:
        with self.assertRaises(ValidationError):
            ExistingOfferCreate(exists=True)
        with self.assertRaises(ValidationError):
            ExistingOfferCreate(exists=True, notes="  \n\t ")
        with self.assertRaises(ValidationError):
            ExistingOfferUpdate(exists=True, notes="   ", document_ids=[])

    def test_notes_only_document_only_and_both_are_accepted(self) -> None:
        document_id = uuid4()
        notes = ExistingOfferCreate(exists=True, notes="  house -> me, 401k split 60/40 ")
        self.assertEqual(notes.notes, "house -> me, 401k split 60/40")
        only_doc = ExistingOfferUpdate(exists=True, document_ids=[document_id])
        self.assertIsNone(only_doc.notes)
        both = ExistingOfferUpdate(
            exists=True, notes="see attached", document_ids=[document_id, document_id]
        )
        self.assertEqual(both.document_ids, [document_id])

    def test_no_forbids_orphan_sources(self) -> None:
        self.assertFalse(ExistingOfferCreate(exists=False).exists)
        with self.assertRaises(ValidationError):
            ExistingOfferCreate(exists=False, notes="orphan")
        with self.assertRaises(ValidationError):
            ExistingOfferUpdate(exists=False, document_ids=[uuid4()])

    def test_notes_are_length_limited(self) -> None:
        with self.assertRaises(ValidationError):
            ExistingOfferCreate(exists=True, notes="x" * 20_001)

    def test_case_create_rejects_reserved_metadata_bypass(self) -> None:
        with self.assertRaises(ValidationError):
            CaseCreate(metadata={"existing_offer": {"exists": True}})

    def test_create_case_persists_validated_intake(self) -> None:
        db = Mock()
        db.get.return_value = SimpleNamespace(
        )
        db.scalar.return_value = 0
        request = SimpleNamespace(state=SimpleNamespace(user_id=uuid4()))
        case = create_case(
            CaseCreate(
                workflow_mode="wizard",
                existing_offer=ExistingOfferCreate(exists=True, notes="They offered the car."),
            ),
            request,
            db,
        )
        stored = case.metadata_json["existing_offer"]
        self.assertTrue(stored["exists"])
        self.assertEqual(stored["notes"], "They offered the car.")
        self.assertEqual(stored["origin"], "initial_incoming_offer")
        self.assertEqual(stored["document_ids"], [])

    def test_create_case_without_answer_stores_no_offer_record(self) -> None:
        db = Mock()
        db.get.return_value = SimpleNamespace(
        )
        db.scalar.return_value = 0
        request = SimpleNamespace(state=SimpleNamespace(user_id=uuid4()))
        case = create_case(CaseCreate(workflow_mode="upload"), request, db)
        self.assertNotIn("existing_offer", case.metadata_json)


class ExistingOfferRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case_id = uuid4()
        self.user = SimpleNamespace(id=uuid4())
        self.case = SimpleNamespace(
            id=self.case_id,
            metadata_json={},
            property_assets=[],
            status="draft",
        )
        self.db = Mock()
        self.db.scalar.return_value = None
        self.db.scalars.return_value.all.return_value = []
        patcher_auth = patch("app.existing_offer._authorize_case", return_value=self.case)
        patcher_lock = patch("app.existing_offer._lock_case", return_value=self.case)
        self.auth = patcher_auth.start()
        self.lock = patcher_lock.start()
        self.addCleanup(patcher_auth.stop)
        self.addCleanup(patcher_lock.stop)

    def _put(self, payload: ExistingOfferUpdate):
        return update_existing_offer(self.case_id, payload, self.user, self.db)

    def test_put_saves_notes_only_and_checks_write_authorization(self) -> None:
        result = self._put(ExistingOfferUpdate(exists=True, notes="car for house"))
        self.auth.assert_called_once_with(self.db, self.user, self.case_id, write=True)
        self.lock.assert_called_once()
        self.db.commit.assert_called_once()
        self.assertEqual(self.case.metadata_json["existing_offer"]["notes"], "car for house")
        self.assertTrue(result.exists)

    def test_put_saves_document_only_after_verifying_case_ownership(self) -> None:
        document_id = uuid4()
        self.db.scalars.return_value.all.side_effect = [[document_id], []]
        self._put(ExistingOfferUpdate(exists=True, document_ids=[document_id]))
        stored = self.case.metadata_json["existing_offer"]
        self.assertEqual(stored["document_ids"], [str(document_id)])
        self.assertIsNone(stored["notes"])

    def test_put_rejects_documents_from_another_case(self) -> None:
        self.db.scalars.return_value.all.return_value = []
        with self.assertRaises(HTTPException) as caught:
            self._put(ExistingOfferUpdate(exists=True, document_ids=[uuid4()]))
        self.assertEqual(caught.exception.status_code, 422)
        self.db.commit.assert_not_called()
        self.assertNotIn("existing_offer", self.case.metadata_json)

    def test_put_cannot_change_answer_after_attempt_exists(self) -> None:
        self.case.metadata_json = {"existing_offer": {"exists": True, "notes": "n", "document_ids": []}}
        self.db.scalar.return_value = uuid4()
        with self.assertRaises(HTTPException) as caught:
            self._put(ExistingOfferUpdate(exists=False))
        self.assertEqual(caught.exception.status_code, 409)
        self.db.commit.assert_not_called()

    def test_put_rejects_autosaves_from_the_discarded_mode_and_during_reset(self) -> None:
        for metadata in [
            {"workflow_mode": "wizard"},
            {"workflow_mode": "upload", "onboarding_reset": "wizard"},
        ]:
            with self.subTest(metadata=metadata):
                self.case.metadata_json = metadata
                with self.assertRaises(HTTPException) as caught:
                    self._put(ExistingOfferUpdate(exists=True, notes="Stale draft", expected_workflow_mode="upload"))
                self.assertEqual(caught.exception.status_code, 409)
                self.db.commit.assert_not_called()
                self.assertNotIn("existing_offer", self.case.metadata_json)

    def test_put_database_failure_is_retryable_and_rolls_back(self) -> None:
        self.db.commit.side_effect = SQLAlchemyError("boom")
        with self.assertRaises(HTTPException) as caught:
            self._put(ExistingOfferUpdate(exists=True, notes="x"))
        self.assertEqual(caught.exception.status_code, 503)
        self.db.rollback.assert_called_once()

    def test_put_preserves_existing_asset_terms(self) -> None:
        terms = [{"asset_index": 0, "asset_name": "House", "term": "mine"}]
        self.case.metadata_json = {
            "existing_offer": {"exists": True, "notes": "a", "document_ids": [], "asset_terms": terms}
        }
        self._put(ExistingOfferUpdate(exists=True, notes="a, updated"))
        self.assertEqual(self.case.metadata_json["existing_offer"]["asset_terms"], terms)

    def test_get_reports_unanswered_and_hides_nothing_without_cache(self) -> None:
        response = Response()
        result = read_existing_offer(self.case_id, response, self.user, self.db)
        self.auth.assert_called_once_with(self.db, self.user, self.case_id, write=False)
        self.assertIsNone(result.exists)
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_get_lists_assets_and_case_documents(self) -> None:
        self.case.property_assets = [{"name": "House"}, {"name": "Boat"}]
        self.case.metadata_json = {
            "existing_offer": {"exists": True, "notes": "n", "document_ids": [], "asset_terms": []}
        }
        document = SimpleNamespace(
            id=uuid4(),
            extension="pdf",
            size_bytes=10,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        self.db.scalars.return_value.all.return_value = [document]
        result = read_existing_offer(self.case_id, Response(), self.user, self.db)
        self.assertEqual([asset.name for asset in result.assets], ["House", "Boat"])
        self.assertEqual(result.documents[0].extension, "pdf")


class AssetTermsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case_id = uuid4()
        self.user = SimpleNamespace(id=uuid4())
        self.record = {
            "exists": True,
            "origin": "initial_incoming_offer",
            "notes": "raw shorthand: house=me",
            "document_ids": [DOC_ID],
            "asset_terms": [],
        }
        self.case = SimpleNamespace(
            id=self.case_id,
            metadata_json={"case_title": "T", "existing_offer": self.record},
            property_assets=[{"name": "House"}, {"name": "Boat"}],
        )
        self.db = Mock()
        self.db.scalars.return_value.all.return_value = []
        for target in ("_authorize_case", "_lock_case"):
            patcher = patch(f"app.existing_offer.{target}", return_value=self.case)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _update(self, terms):
        return update_asset_terms(self.case_id, AssetTermsUpdate(terms=terms), self.user, self.db)

    def test_maps_terms_without_changing_raw_notes_or_documents(self) -> None:
        self._update([{"asset_index": 1, "asset_name": "Boat", "term": "to spouse"}])
        stored = self.case.metadata_json["existing_offer"]
        self.assertEqual(stored["notes"], "raw shorthand: house=me")
        self.assertEqual(stored["document_ids"], [DOC_ID])
        self.assertEqual(stored["asset_terms"][0]["term"], "to spouse")
        self.assertEqual(self.case.metadata_json["case_title"], "T")
        self.db.commit.assert_called_once()

    def test_rejects_without_offer_or_inventory_or_with_stale_reference(self) -> None:
        for mutate, expected in (
            (lambda: self.case.metadata_json.pop("existing_offer"), 409),
            (lambda: setattr(self.case, "property_assets", []), 409),
        ):
            mutate()
            with self.assertRaises(HTTPException) as caught:
                self._update([{"asset_index": 0, "asset_name": "House", "term": "x"}])
            self.assertEqual(caught.exception.status_code, expected)
            self.case.metadata_json["existing_offer"] = self.record
            self.case.property_assets = [{"name": "House"}, {"name": "Boat"}]
        with self.assertRaises(HTTPException) as caught:
            self._update([{"asset_index": 0, "asset_name": "Boat", "term": "x"}])
        self.assertEqual(caught.exception.status_code, 409)
        with self.assertRaises(HTTPException) as caught:
            self._update([{"asset_index": 5, "asset_name": "Boat", "term": "x"}])
        self.assertEqual(caught.exception.status_code, 409)

    def test_rejects_duplicate_assets_and_blank_terms(self) -> None:
        with self.assertRaises(ValidationError):
            AssetTermsUpdate(terms=[
                {"asset_index": 0, "asset_name": "House", "term": "a"},
                {"asset_index": 0, "asset_name": "House", "term": "b"},
            ])
        with self.assertRaises(ValidationError):
            AssetTermsUpdate(terms=[{"asset_index": 0, "asset_name": "House", "term": "  "}])


class OfferOriginTests(unittest.TestCase):
    def test_origin_distinguishes_incoming_offer_proposal_and_counteroffer(self) -> None:
        incoming = {"case_profile": {"metadata": {"existing_offer": {"exists": True}}}}
        plain = {"case_profile": {"metadata": {}}}
        self.assertEqual(offer_origin(1, incoming), "initial_incoming_offer")
        self.assertEqual(offer_origin(1, plain), "initial_user_proposal")
        self.assertEqual(offer_origin(2, incoming), "counteroffer_response")
        self.assertEqual(offer_origin(2, plain), "counteroffer_response")
        self.assertEqual(offer_origin(1, {}), "initial_user_proposal")
        declined = {"case_profile": {"metadata": {"existing_offer": {"exists": False}}}}
        self.assertEqual(offer_origin(1, declined), "initial_user_proposal")

    def test_offer_response_read_model_exposes_origin(self) -> None:
        from app.offer_response import OfferResponseRead

        self.assertIn("offer_origin", OfferResponseRead.model_fields)


class ExistingOfferUiTests(unittest.TestCase):
    page = open("src/app/static/index.html", encoding="utf-8").read()

    def test_both_selected_start_paths_create_without_an_offer_question(self) -> None:
        chooser = self.page.split('id="case-create-choice"', 1)[1].split("</section>", 1)[0]
        self.assertNotIn("case-offer-question", chooser)
        self.assertNotIn('id="case-create-offer-intake"', self.page)
        self.assertIn('data-start-mode="upload"', chooser)
        self.assertIn('data-start-mode="wizard"', chooser)
        self.assertIn(
            "createCaseFromDashboard(button.dataset.startMode, button)",
            self.page,
        )

    def test_preparation_page_keeps_accessible_offer_editing(self) -> None:
        for marker in (
            'id="existing-offer-panel"',
            'id="existing-offer-status"',
            'id="existing-offer-asset-terms"',
        ):
            self.assertIn(marker, self.page)
        status = self.page.split('id="existing-offer-status"', 1)[1][:120]
        self.assertIn('aria-live="polite"', status)

    def test_case_creation_does_not_upload_offer_files(self) -> None:
        create = self.page.split("async function createCaseFromDashboard", 1)[1].split(
            "async function openActiveCase", 1
        )[0]
        self.assertNotIn("offerFile", create)
        self.assertNotIn('id="case-offer-file-recovery"', self.page)

    def test_client_validates_offer_source_and_uses_server_endpoint(self) -> None:
        self.assertIn("/existing-offer", self.page)
        self.assertNotIn('id="settlement-planner"', self.page)

    def test_case_creation_only_submits_the_selected_workflow(self) -> None:
        create = self.page.split("async function createCaseFromDashboard", 1)[1].split(
            "async function openActiveCase", 1
        )[0]
        self.assertNotIn("offer=pending", self.page)
        self.assertIn("JSON.stringify({ workflow_mode: mode })", create)
        self.assertNotIn("existing_offer", create)
        self.assertIn("caseCreateProgress = { caseId, mode }", create)

    def test_wizard_opens_without_an_offer_but_offer_sources_are_still_validated(self) -> None:
        self.assertNotIn("function applyExistingOfferGate", self.page)
        self.assertIn("wizardDemoPage.hidden = false", self.page)
        self.assertNotIn('id="materials-workflow"', self.page)
        self.assertIn("preparationView.append(wizardDemoPage)", self.page)
        self.assertIn('.querySelector(".demo-flow-panel > .demo-flow-actions").before(existingOfferPanel)', self.page)
        panel_save = self.page.split("async function saveExistingOffer(", 1)[1].split(
            "async function saveExistingOfferTerms", 1
        )[0]
        self.assertIn("!notes && documentIds.length === 0 && !offerFile", panel_save)
        self.assertIn('id="existing-offer-file"', self.page)


if __name__ == "__main__":
    unittest.main()
