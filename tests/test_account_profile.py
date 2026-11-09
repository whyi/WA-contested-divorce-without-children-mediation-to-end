import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth_routes import require_current_user
from app.config import Settings
from app.main import app


class AccountProfileTests(unittest.TestCase):
    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_profile_requires_authentication(self) -> None:
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="account-profile-test-signing-secret-long-enough",
        )
        with patch("app.auth_routes.get_settings", return_value=settings):
            response = TestClient(app).get("/api/auth/account")

        self.assertEqual(response.status_code, 401)

    def test_profile_returns_only_current_user_email_and_names_without_caching(self) -> None:
        app.dependency_overrides[require_current_user] = lambda: SimpleNamespace(
            id=uuid4(),
            email="essential-test@localhost.invalid",
            first_name="Synthetic",
            last_name="User",
            password_hash="must-not-be-returned",
        )

        response = TestClient(app).get("/api/auth/account")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "email": "essential-test@localhost.invalid",
                "first_name": "Synthetic",
                "last_name": "User",
            },
        )
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertNotIn("must-not-be-returned", response.text)


if __name__ == "__main__":
    unittest.main()
