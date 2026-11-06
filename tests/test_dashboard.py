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
            (case_id, "draft", {"case_title": "XYZ vs ABC", "workflow_mode": "upload"}, 2, "owner", None)
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
                    "account_type": "party",
                    "cases": [{
                        "id": str(case_id),
                        "status": "draft",
                        "title": "XYZ vs ABC",
                        "workflow_mode": "upload",
                        "attempt_ordinal": 2,
                        "delegated_to": None,
                    }],
                },
            },
        )
        statement = str(db.execute.call_args.args[0])
        self.assertIn("case_memberships.user_id", statement)
        self.assertIn("case_memberships.revoked_at IS NULL", statement)
        self.assertIn("settlement_negotiation_attempts.attempt_ordinal", statement)

    def test_status_returns_empty_case_list_for_new_account(self) -> None:
        db = Mock()
        db.execute.return_value.all.return_value = []
        app.dependency_overrides[require_current_user] = lambda: SimpleNamespace(
            id=uuid4(), account_type="party"
        )

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
                "account_type": "party",
                "cases": [],
            },
        )

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

    def test_delegated_case_is_listed_for_the_party_with_the_delegate(self) -> None:
        case_id = uuid4()
        db = Mock()
        db.execute.side_effect = [
            Mock(all=lambda: [(case_id, "settlement", {"case_title": "Mine"}, 1, "owner", object())]),
            Mock(all=lambda: [(case_id, "lawyer@example.com")]),
        ]
        app.dependency_overrides[require_current_user] = lambda: SimpleNamespace(id=uuid4())

        def override_db():
            yield db

        app.dependency_overrides[get_db] = override_db
        response = TestClient(app).get("/api/v1/dashboard/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["cases"][0]["delegated_to"], "lawyer@example.com")
        statement = str(db.execute.call_args_list[0].args[0])
        self.assertIn("case_memberships.suspended_at IS NOT NULL", statement)

    def test_professional_account_type_is_reported(self) -> None:
        db = Mock()
        db.execute.return_value.all.return_value = []
        app.dependency_overrides[require_current_user] = lambda: SimpleNamespace(
            id=uuid4(), account_type="professional"
        )

        def override_db():
            yield db

        app.dependency_overrides[get_db] = override_db
        response = TestClient(app).get("/api/v1/dashboard/status")

        self.assertEqual(response.json()["data"]["account_type"], "professional")


if __name__ == "__main__":
    unittest.main()
