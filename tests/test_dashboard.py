import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.auth_routes import require_current_user
from app.config import Settings
from app.database import get_db
from app.main import app


class DashboardStatusTests(unittest.TestCase):
    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_status_requires_an_authenticated_user(self) -> None:
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="dashboard-test-signing-secret-long-enough",
        )
        with patch("app.auth_routes.get_settings", return_value=settings):
            response = TestClient(app).get("/api/v1/dashboard/status")

        self.assertEqual(response.status_code, 401)
        self.assertNotIn("case_count", response.text)

    def test_status_returns_only_the_current_users_case_summaries(self) -> None:
        user_id = uuid4()
        case_id = uuid4()
        db = Mock()
        db.execute.return_value.all.return_value = [
            (case_id, "draft", {"case_title": "XYZ vs ABC", "workflow_mode": "upload"}, 2, "owner", True, 2)
        ]
        app.dependency_overrides[require_current_user] = lambda: SimpleNamespace(id=user_id)

        def override_db():
            yield db

        app.dependency_overrides[get_db] = override_db
        response = TestClient(app).get("/api/v1/dashboard/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "data": {
                    "has_cases": True,
                    "case_count": 1,
                    "active_case_count": 1,
                    "cases": [{
                        "id": str(case_id),
                        "status": "draft",
                        "title": "XYZ vs ABC",
                        "workflow_mode": "upload",
                        "attempt_ordinal": 2,
                        "workspace_started": True,
                    }],
                },
            },
        )
        statement = str(db.execute.call_args.args[0])
        self.assertIn("case_memberships.user_id", statement)
        self.assertIn("case_memberships.revoked_at IS NULL", statement)
        self.assertIn("settlement_negotiation_attempts.attempt_ordinal", statement)
        self.assertIn("documents.case_id", statement)
        self.assertIn("deletion_tombstones.scope_type", statement)

    def test_status_returns_empty_case_list_for_new_account(self) -> None:
        db = Mock()
        db.execute.return_value.all.return_value = []
        app.dependency_overrides[require_current_user] = lambda: SimpleNamespace(id=uuid4())

        def override_db():
            yield db

        app.dependency_overrides[get_db] = override_db
        response = TestClient(app).get("/api/v1/dashboard/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["data"],
            {
                "has_cases": False,
                "case_count": 0,
                "active_case_count": 0,
                "cases": [],
            },
        )

    def test_saved_progress_documents_attempts_and_snapshots_resume_the_workspace(self) -> None:
        case_id = uuid4()
        db = Mock()
        app.dependency_overrides[require_current_user] = lambda: SimpleNamespace(id=uuid4())

        def override_db():
            yield db

        app.dependency_overrides[get_db] = override_db
        for metadata, documents, attempts, expected in [
            ({"workflow_mode": "upload"}, False, 0, False),
            ({"workspace_started": True}, False, 0, True),
            ({"workflow_mode": "upload"}, True, 0, True),
            ({}, False, 1, True),
            ({"asset_overview": {"overview": {"snapshots": [{"date": "2025-01-01"}]}}}, False, 0, True),
        ]:
            with self.subTest(metadata=metadata, documents=documents, attempts=attempts):
                db.execute.return_value.all.return_value = [
                    (case_id, "draft", metadata, 1, "owner", documents, attempts)
                ]
                response = TestClient(app).get("/api/v1/dashboard/status")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["data"]["cases"][0]["workspace_started"], expected)

    def test_status_reports_database_failure_as_retryable_service_error(self) -> None:
        db = Mock()
        db.execute.side_effect = SQLAlchemyError("database unavailable")
        app.dependency_overrides[require_current_user] = lambda: SimpleNamespace(id=uuid4())

        def override_db():
            yield db

        app.dependency_overrides[get_db] = override_db
        response = TestClient(app).get("/api/v1/dashboard/status")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()["detail"],
            "Dashboard status is unavailable. Please try again.",
        )

    def test_status_does_not_expose_account_types_or_delegation(self) -> None:
        case_id = uuid4()
        db = Mock()
        db.execute.return_value.all.return_value = [
            (case_id, "settlement", {"case_title": "Mine"}, 1, "owner", False, 0)
        ]
        app.dependency_overrides[require_current_user] = lambda: SimpleNamespace(
            id=uuid4(), account_type="professional"
        )

        def override_db():
            yield db

        app.dependency_overrides[get_db] = override_db
        response = TestClient(app).get("/api/v1/dashboard/status")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("account_type", response.json()["data"])
        self.assertNotIn("delegated_to", response.json()["data"]["cases"][0])
        self.assertEqual(db.execute.call_count, 1)
        self.assertNotIn("suspended_at", str(db.execute.call_args.args[0]))


if __name__ == "__main__":
    unittest.main()
