import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException, Response
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.main import app, read_case_workspace, record_workspace_entry
from app.config import Settings
from app.models import Case


class CaseWorkspaceTests(unittest.TestCase):
    def test_workspace_entry_is_persisted_idempotently_without_changing_case_data(self) -> None:
        case = Case(id=uuid4(), status="draft", metadata_json={"workflow_mode": "upload", "case_title": "Synthetic"})
        db = MagicMock(spec=Session)
        db.scalar.return_value = case
        response = Response()
        with patch("app.main.resolve_case_access", return_value=SimpleNamespace(role="owner")):
            for _ in range(2):
                result = record_workspace_entry(case.id, response, SimpleNamespace(id=uuid4()), db)
                self.assertTrue(result.workspace_started)
        self.assertEqual(case.metadata_json, {
            "workflow_mode": "upload", "case_title": "Synthetic", "workspace_started": True,
        })
        self.assertEqual(db.commit.call_count, 2)
        self.assertIn("FOR UPDATE", str(db.scalar.call_args.args[0]))
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_workspace_entry_rejects_non_owner_missing_and_closed_cases(self) -> None:
        for role, case, code in [
            (None, None, 404),
            ("owner", None, 404),
            ("other", Case(id=uuid4(), status="draft"), 403),
            ("owner", Case(id=uuid4(), status="draft", closed_at=datetime.now(UTC)), 409),
            ("owner", Case(id=uuid4(), status="finalized"), 409),
        ]:
            with self.subTest(code=code, role=role):
                db = MagicMock(spec=Session)
                db.scalar.return_value = case
                membership = SimpleNamespace(role=role) if role else None
                with patch("app.main.resolve_case_access", return_value=membership):
                    with self.assertRaises(HTTPException) as caught:
                        record_workspace_entry(uuid4(), Response(), SimpleNamespace(id=uuid4()), db)
                self.assertEqual(caught.exception.status_code, code)
                db.commit.assert_not_called()

    def test_workspace_entry_storage_failure_is_logged_and_rolled_back(self) -> None:
        db = MagicMock(spec=Session)
        db.scalar.return_value = Case(id=uuid4(), status="draft", metadata_json={})
        db.commit.side_effect = SQLAlchemyError("synthetic")
        with patch("app.main.resolve_case_access", return_value=SimpleNamespace(role="owner")), patch("app.main.log_failure_event") as log:
            with self.assertRaises(HTTPException) as caught:
                record_workspace_entry(uuid4(), Response(), SimpleNamespace(id=uuid4()), db)
        self.assertEqual(caught.exception.status_code, 503)
        db.rollback.assert_called_once()
        log.assert_called_once()

    def test_workspace_entry_requires_authentication(self) -> None:
        settings = Settings(
            auth_enabled=True, case_data_enabled=True,
            auth_jwt_secret="synthetic-signing-secret-that-is-long-enough",
            s3_endpoint_url="http://127.0.0.1:5000",
        )
        with patch("app.main.settings", settings):
            response = TestClient(app).post(f"/cases/{uuid4()}/workspace-entry")
        self.assertEqual(response.status_code, 401)

    def test_saved_case_intake_files_and_frozen_attempt_profiles_are_returned(self) -> None:
        case_id = uuid4()
        document_id = uuid4()
        case = Case(
            id=case_id, status="draft", metadata_json={"case_title": "Synthetic"},
            property_assets=[], relationship_milestones={}, asset_liability_inventory={},
            wizard_intake_json={"finances": [{"id": "saved", "amount": "1234.56"}]},
        )
        attempt = SimpleNamespace(
            attempt_ordinal=1, frozen_at=datetime.now(UTC), finalized_at=None,
            selection_id=uuid4(), sent_confirmed_at=None,
            finalized_snapshot_json=None,
            frozen_snapshot_json={"case_profile": {"property_assets": [{"name": "Frozen property"}]}},
            snapshot_json={"case_profile": {"property_assets": [{"name": "Wrong live property"}]}},
        )
        document = SimpleNamespace(
            id=document_id, extension="pdf", size_bytes=1024, created_at=datetime.now(UTC),
            original_filename="Original evidence.pdf",
        )
        db = MagicMock(spec=Session)
        db.scalars.return_value.all.side_effect = [[attempt], [document]]
        response = Response()
        with patch("app.main._require_case", return_value=case):
            result = read_case_workspace(case_id, response, db)
        self.assertEqual(result.case.id, case_id)
        self.assertEqual(str(result.intake.finances[0].amount), "1234.56")
        self.assertEqual(result.documents[0].id, document_id)
        self.assertIsNone(result.accepted_offer_url)
        self.assertTrue(result.attempts[0].frozen)
        self.assertEqual(result.attempts[0].profile["property_assets"][0]["name"], "Frozen property")
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        query = str(db.scalars.call_args_list[1].args[0])
        self.assertIn("deletion_tombstones", query)
        self.assertIn("documents.case_id", query)

    def test_workspace_identifies_only_the_latest_confirmed_accepted_offer(self) -> None:
        for backend in ["asset", "selection"]:
            for outcome, sent in [("accepted", True), ("accepted", False), ("rejected", True), ("counteroffer", True), (None, True)]:
                with self.subTest(backend=backend, outcome=outcome, sent=sent):
                    case_id = uuid4()
                    selection_id = uuid4()
                    case = Case(
                        id=case_id, status="finalized", closed_at=datetime.now(UTC),
                        closed_reason="accepted", metadata_json={"asset_mediation": {
                            "1": {"sent": True, "outcome": "accepted"},
                            "2": {"sent": sent, "outcome": outcome},
                        } if backend == "asset" else {}},
                        property_assets=[], relationship_milestones={},
                        asset_liability_inventory={}, wizard_intake_json={},
                    )
                    attempt = SimpleNamespace(
                        attempt_ordinal=2, selection_id=selection_id,
                        sent_confirmed_at=datetime.now(UTC) if sent else None,
                        frozen_at=datetime.now(UTC), finalized_at=None,
                        finalized_snapshot_json=None, frozen_snapshot_json=None,
                        snapshot_json={},
                    )
                    db = MagicMock(spec=Session)
                    db.scalars.return_value.all.side_effect = [[attempt], []]
                    db.scalar.return_value = outcome
                    with patch("app.main._require_case", return_value=case):
                        result = read_case_workspace(case_id, Response(), db)
                    expected = None
                    if outcome == "accepted" and sent:
                        target = f"asset_attempt=2" if backend == "asset" else f"selection_id={selection_id}"
                        expected = f"/settlement-completion?case_id={case_id}&{target}"
                    self.assertEqual(result.accepted_offer_url, expected)
                    db.commit.assert_not_called()
                    db.add.assert_not_called()

    def test_stopped_workflows_do_not_get_an_accepted_offer_shortcut(self) -> None:
        for reason, stopped in [("stopped", False), (None, True)]:
            with self.subTest(reason=reason, stopped=stopped):
                case = Case(
                    id=uuid4(), status="finalized", closed_reason=reason,
                    metadata_json={"asset_mediation": {"1": {
                        "sent": True, "outcome": "accepted", "stopped": stopped,
                    }}},
                    property_assets=[], relationship_milestones={},
                    asset_liability_inventory={}, wizard_intake_json={},
                )
                db = MagicMock(spec=Session)
                db.scalars.return_value.all.side_effect = [[], []]
                with patch("app.main._require_case", return_value=case):
                    result = read_case_workspace(case.id, Response(), db)
                self.assertIsNone(result.accepted_offer_url)
                db.commit.assert_not_called()

    def test_acceptance_lookup_failure_is_logged_instead_of_hiding_the_step(self) -> None:
        case = Case(id=uuid4(), status="draft", metadata_json={})
        attempt = SimpleNamespace(
            attempt_ordinal=1, selection_id=uuid4(), sent_confirmed_at=datetime.now(UTC),
        )
        db = MagicMock(spec=Session)
        db.scalars.return_value.all.return_value = [attempt]
        db.scalar.side_effect = SQLAlchemyError("synthetic")
        with patch("app.main._require_case", return_value=case), patch("app.main.log_failure_event") as log:
            with self.assertRaises(HTTPException) as caught:
                read_case_workspace(case.id, Response(), db)
        self.assertEqual(caught.exception.status_code, 503)
        log.assert_called_once()

    def test_missing_or_unauthorized_case_cannot_be_read(self) -> None:
        db = MagicMock(spec=Session)
        with patch("app.main._require_case", side_effect=HTTPException(status_code=404)):
            with self.assertRaises(HTTPException) as caught:
                read_case_workspace(uuid4(), Response(), db)
        self.assertEqual(caught.exception.status_code, 404)
        db.scalars.assert_not_called()

    def test_database_failure_is_logged_and_retryable(self) -> None:
        db = MagicMock(spec=Session)
        with patch("app.main._require_case", side_effect=SQLAlchemyError("synthetic")), patch("app.main.log_failure_event") as log:
            with self.assertRaises(HTTPException) as caught:
                read_case_workspace(uuid4(), Response(), db)
        self.assertEqual(caught.exception.status_code, 503)
        log.assert_called_once()

    def test_real_workspace_html_routes_are_registered(self) -> None:
        paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
        self.assertIn("/case/assets", paths)
        self.assertIn("/case/files", paths)
        self.assertIn("/cases/{case_id}/workspace", paths)

    def test_workspace_endpoint_requires_authentication_in_real_case_mode(self) -> None:
        settings = Settings(
            auth_enabled=True, case_data_enabled=True,
            auth_jwt_secret="synthetic-signing-secret-that-is-long-enough",
            s3_endpoint_url="http://127.0.0.1:5000",
        )
        with patch("app.main.settings", settings):
            response = TestClient(app).get(f"/cases/{uuid4()}/workspace")
        self.assertEqual(response.status_code, 401)
