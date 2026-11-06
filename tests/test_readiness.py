import unittest
from unittest.mock import MagicMock, Mock, patch

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app


class ProductionReadinessTests(unittest.TestCase):
    def test_readyz_fails_closed_when_production_requirements_are_unmet(self) -> None:
        settings = Settings(
            production_readiness_required=True,
            auth_jwt_secret="secret-value-that-must-not-be-returned",
        )

        with (
            patch("app.main.settings", settings),
            patch("app.main.SessionLocal") as session_factory,
            patch("app.main.storage") as storage,
        ):
            response = TestClient(app).get("/readyz")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"detail": "Production readiness requirements are unmet."},
        )
        self.assertNotIn("secret-value", response.text)
        session_factory.assert_not_called()
        storage.check_ready.assert_not_called()

    def test_case_data_routes_fail_closed_before_auth_when_readiness_is_unmet(self) -> None:
        settings = Settings(production_readiness_required=True)

        with patch("app.main.settings", settings):
            response = TestClient(app).get("/cases")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"detail": "Production readiness requirements are unmet."},
        )

    def test_local_readyz_checks_database_and_object_storage(self) -> None:
        session = Mock()
        session_context = MagicMock()
        session_context.__enter__.return_value = session
        session_context.__exit__.return_value = False

        with (
            patch("app.main.settings", Settings()),
            patch("app.main.SessionLocal", return_value=session_context),
            patch("app.main.storage") as storage,
        ):
            response = TestClient(app).get("/readyz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready"})
        session.execute.assert_called_once()
        storage.check_ready.assert_called_once()


if __name__ == "__main__":
    unittest.main()
