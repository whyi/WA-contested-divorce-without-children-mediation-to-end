import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.config import Settings
from app.main import app
from app.models import AuthSession, User


class WorkingPageAuthTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(
            auth_enabled=True, case_data_enabled=True, demo_mode_enabled=False,
            auth_jwt_secret="synthetic-session-secret-with-at-least-32-characters",
            s3_kms_key_id="alias/synthetic-test",
        )
        self.user = SimpleNamespace(id=uuid4(), status="active", email="synthetic@example.invalid")
        now = datetime.now(UTC)
        self.session = SimpleNamespace(
            user_id=self.user.id, revoked_at=None, idle_expires_at=now + timedelta(days=1),
            absolute_expires_at=now + timedelta(days=2),
        )
        self.db = MagicMock()
        self.db.get.side_effect = lambda model, key: self.session if model is AuthSession else self.user if model is User else None
        self.db.scalar.return_value = None
        self.session_factory = MagicMock()
        self.session_factory.return_value.__enter__.return_value = self.db
        self.client = TestClient(app)
        for context in (
            patch("app.main.SessionLocal", self.session_factory),
            patch("app.auth_routes.get_settings", return_value=self.settings),
            patch("app.auth_routes._owner_beta_allows", return_value=True),
        ):
            context.start()
            self.addCleanup(context.stop)

    def request(self, path, token=True):
        return self.client.get(path, headers={"Authorization": "Bearer synthetic"} if token else {}, follow_redirects=False)

    def test_anonymous_working_routes_redirect_to_bare_home_without_html_or_query(self):
        for path in (
            "/settlement-completion?case_id=private&asset_attempt=1",
            "/rejection-completion?case_id=private", "/onboarding/upload?case_id=private",
            "/onboarding/wizard", "/case/assets", "/case/files", "/case/assets/",
            "/onboarding/unknown", "/case/unknown",
        ):
            with self.subTest(path=path):
                response = self.request(path, token=False)
                self.assertEqual(response.status_code, 303)
                self.assertEqual(response.headers["Location"], "/")
                self.assertEqual(response.headers["Cache-Control"], "no-store")
                self.assertNotIn("Congratulations", response.text)
                self.assertNotIn("Asset Overview", response.text)

    def test_valid_active_session_can_open_every_real_working_page(self):
        with patch("app.auth_routes.verify_token", return_value={"sub": str(self.user.id), "sid": str(uuid4())}):
            for path in ("/settlement-completion", "/rejection-completion", "/case/assets", "/case/files", "/onboarding/upload", "/onboarding/wizard"):
                response = self.request(path)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.headers["Cache-Control"], "no-store")
                self.assertIn("Casework", response.text)

    def test_invalid_token_and_expired_revoked_inactive_or_deleted_sessions_redirect(self):
        with patch("app.auth_routes.verify_token", side_effect=ValueError("Invalid token")):
            self.assertEqual(self.request("/case/assets").status_code, 303)
        claims = {"sub": str(self.user.id), "sid": str(uuid4())}
        for field, value in (
            ("revoked_at", datetime.now(UTC)),
            ("idle_expires_at", datetime.now(UTC) - timedelta(seconds=1)),
            ("absolute_expires_at", datetime.now(UTC) - timedelta(seconds=1)),
        ):
            original = getattr(self.session, field)
            setattr(self.session, field, value)
            with patch("app.auth_routes.verify_token", return_value=claims):
                self.assertEqual(self.request("/settlement-completion").status_code, 303)
            setattr(self.session, field, original)
        self.user.status = "inactive"
        with patch("app.auth_routes.verify_token", return_value=claims):
            self.assertEqual(self.request("/case/files").status_code, 303)
        self.user.status = "active"
        self.db.scalar.return_value = SimpleNamespace(status="completed")
        with patch("app.auth_routes.verify_token", return_value=claims):
            self.assertEqual(self.request("/onboarding/wizard").status_code, 303)

    def test_session_database_failure_is_logged_and_fails_closed(self):
        self.db.get.side_effect = SQLAlchemyError("Synthetic unavailable database")
        with patch("app.auth_routes.verify_token", return_value={"sub": str(self.user.id), "sid": str(uuid4())}), patch("app.main.log_failure_event") as log:
            response = self.request("/settlement-completion")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("Congratulations", response.text)
        log.assert_called_once()

    def test_home_and_demo_stay_public(self):
        for path in ("/", "/?auth=login", "/demo/start?source=demo1", "/demo/start?source=demo2", "/demo/wizard", "/demo/settlement-completion"):
            response = self.request(path, token=False)
            self.assertEqual(response.status_code, 200)
        self.db.get.assert_not_called()
