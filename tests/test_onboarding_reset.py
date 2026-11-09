import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.main import OnboardingResetRequest, read_onboarding_state, reset_onboarding
from app.models import Case


class OnboardingResetTests(unittest.TestCase):
    def setUp(self):
        self.case = Case(
            id=uuid4(), status="draft", metadata_json={
                "workflow_mode": "upload", "case_title": "Synthetic",
                "existing_offer": {"exists": True, "notes": "Synthetic offer"},
                "asset_overview": {"revision": 1},
            },
            wizard_intake_json={"filed": "yes"}, wizard_intake_revision=3,
            property_assets=[{"name": "Synthetic asset"}],
            relationship_milestones={"marriage": "2020-01-01"},
            asset_liability_inventory={"cash": 100},
        )
        self.user = SimpleNamespace(id=uuid4())
        self.db = MagicMock(spec=Session)
        self.db.scalar.side_effect = [self.case, None, self.case]
        self.documents = [uuid4(), uuid4()]
        self.db.scalars.return_value = self.documents
        self.payload = OnboardingResetRequest(workflow_mode="wizard", confirmation="DISCARD ONBOARDING")

    def reset(self):
        with patch("app.main.resolve_case_access", return_value=SimpleNamespace(role="owner")):
            return reset_onboarding(self.case.id, self.payload, Response(), self.user, self.db)

    def test_confirmed_reset_purges_every_document_and_all_onboarding_inputs(self):
        with patch("app.main.delete_document_scope") as purge:
            result = self.reset()
        self.assertEqual(result.workflow_mode, "wizard")
        self.assertFalse(result.has_work)
        self.assertFalse(result.reset_pending)
        self.assertEqual([call.args[3] for call in purge.call_args_list], self.documents)
        self.assertEqual(self.case.wizard_intake_revision, 4)
        self.assertIsNone(self.case.wizard_intake_json["filed"])
        self.assertEqual(self.case.property_assets, [])
        self.assertEqual(self.case.relationship_milestones, {})
        self.assertEqual(self.case.asset_liability_inventory, {})
        self.assertEqual(self.case.metadata_json, {"case_title": "Synthetic", "workflow_mode": "wizard"})
        self.assertEqual(self.db.commit.call_count, 2)

    def test_deletion_failure_keeps_intent_and_requires_retry_toward_same_mode(self):
        with patch("app.main.delete_document_scope", side_effect=HTTPException(status_code=503, detail="Deletion incomplete.")):
            with self.assertRaises(HTTPException) as caught:
                self.reset()
        self.assertEqual(caught.exception.status_code, 503)
        self.assertEqual(self.case.metadata_json["onboarding_reset"], "wizard")
        self.assertEqual(self.case.wizard_intake_revision, 3)
        self.assertEqual(self.case.metadata_json["workflow_mode"], "upload")
        self.db.scalar.side_effect = [self.case, None]
        self.payload = OnboardingResetRequest(workflow_mode="upload", confirmation="DISCARD ONBOARDING")
        with self.assertRaises(HTTPException) as caught:
            self.reset()
        self.assertEqual(caught.exception.status_code, 409)

    def test_rejects_nonowner_missing_closed_and_started_workspace(self):
        for case, role, attempt, code in [
            (None, "owner", None, 404),
            (self.case, "other", None, 403),
            (Case(id=uuid4(), status="finalized"), "owner", None, 409),
            (Case(id=uuid4(), status="draft", metadata_json={"workspace_started": True}), "owner", None, 409),
            (self.case, "owner", uuid4(), 409),
        ]:
            with self.subTest(code=code, role=role):
                self.db.reset_mock()
                self.db.scalar.side_effect = [case, attempt]
                with patch("app.main.resolve_case_access", return_value=SimpleNamespace(role=role)), patch("app.main.delete_document_scope") as purge:
                    with self.assertRaises(HTTPException) as caught:
                        reset_onboarding(self.case.id, self.payload, Response(), self.user, self.db)
                self.assertEqual(caught.exception.status_code, code)
                self.db.commit.assert_not_called()
                purge.assert_not_called()

    def test_database_failure_is_logged_and_retryable(self):
        self.db.commit.side_effect = SQLAlchemyError("Synthetic")
        with patch("app.main.log_failure_event") as log:
            with self.assertRaises(HTTPException) as caught:
                self.reset()
        self.assertEqual(caught.exception.status_code, 503)
        self.db.rollback.assert_called_once()
        log.assert_called_once()

    def test_working_mode_state_detects_saved_intake_files_and_pending_reset(self):
        for metadata, intake, document, expected in [
            ({"workflow_mode": "upload"}, {}, None, False),
            ({"workflow_mode": "wizard"}, {"filed": "yes"}, None, True),
            ({"workflow_mode": "upload"}, {}, uuid4(), True),
            ({"workflow_mode": "upload", "existing_offer": {"exists": False}}, {}, None, False),
            ({"workflow_mode": "upload", "existing_offer": {"exists": True, "notes": "Offer"}}, {}, None, True),
            ({"workflow_mode": "upload", "onboarding_reset": "wizard"}, {}, None, False),
        ]:
            with self.subTest(metadata=metadata):
                case = Case(id=uuid4(), status="draft", metadata_json=metadata, wizard_intake_json=intake)
                self.db.scalar.side_effect = [document]
                response = Response()
                with patch("app.main._require_case", return_value=case):
                    result = read_onboarding_state(case.id, response, self.db)
                self.assertEqual(result.workflow_mode, metadata["workflow_mode"])
                self.assertEqual(result.has_work, expected)
                self.assertEqual(result.reset_pending, "onboarding_reset" in metadata)
                self.assertEqual(response.headers["Cache-Control"], "no-store")
