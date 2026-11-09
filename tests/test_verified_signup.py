import importlib.util
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, inspect, select, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth import hash_token, verify_password
from app.auth_routes import CONSENT_VERSION
from app.config import Settings
from app.database import Base, get_db
from app.main import app
from app.models import AuthChallenge, AuthSession, ExternalIdentity, User
from tests import test_attachment_limits as sqlite_support
from deploy.local.seed_test_account import ESSENTIAL_TEST_EMAIL, ensure_essential_test_account


class VerifiedSignupTests(unittest.TestCase):
    def setUp(self):
        self.defaults = []
        for table in Base.metadata.tables.values():
            for column in table.columns:
                default = column.server_default
                if default is not None and "::" in str(getattr(default, "arg", "")):
                    self.defaults.append((column, default))
                    column.server_default = None
        self.engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine, expire_on_commit=False)
        self.settings = Settings(
            _env_file=None, auth_enabled=True, auth_cookie_secure=True,
            auth_jwt_secret="fictional-verified-signup-secret-long-enough",
            smtp_host="smtp.example.test", auth_email_from="casework@example.com",
            google_client_id="fictional-client", google_client_secret="fictional-secret",
        )
        self.original_overrides = app.dependency_overrides.copy()
        app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(app, base_url="https://testserver")
        for target, options in (
            ("app.auth_routes.get_settings", {"return_value": self.settings}),
            ("app.auth_routes._rate_limit", {}),
            ("app.auth_routes._send_security_email", {}),
        ):
            item = patch(target, **options)
            mock = item.start()
            self.addCleanup(item.stop)
            if target.endswith("_send_security_email"):
                self.send_email = mock

    def tearDown(self):
        app.dependency_overrides.clear()
        app.dependency_overrides.update(self.original_overrides)
        self.db.close()
        self.engine.dispose()
        for column, default in self.defaults:
            column.server_default = default

    def start_email(self):
        response = self.client.post("/api/auth/signup/email/start", json={"email": "new@example.com"})
        self.assertEqual(response.status_code, 202, response.text)
        from uuid import UUID
        self.record = self.db.get(AuthChallenge, UUID(response.json()["challenge_id"]))
        self.record.expires_at = self.record.expires_at.replace(tzinfo=UTC)
        self.db.flush()
        self.token = self.send_email.call_args.args[2].split("token is: ", 1)[1].split("\n", 1)[0]
        self.assertEqual(self.record.challenge, hash_token(self.token))
        return response.json()["challenge_id"]

    def verify_email(self):
        challenge_id = self.start_email()
        result = self.client.post("/api/auth/signup/email/verify", json={
            "email": "new@example.com", "challenge_id": challenge_id, "token": self.token,
        })
        self.assertEqual(result.status_code, 200, result.text)
        return {
            "email": "new@example.com", "password": "fictional-signup-password-not-a-secret",
            "first_name": " Test ", "last_name": " User ",
            "challenge_id": challenge_id, "verification_token": result.json()["verification_token"],
            "terms_accepted": True,
        }

    def test_account_created_only_after_verified_consent_and_full_signup(self):
        payload = self.verify_email()
        self.assertEqual(self.db.scalar(select(func.count(User.id))), 0)
        self.assertLessEqual((self.record.expires_at - datetime.now(UTC)).total_seconds(), 300)
        self.assertEqual(self.record.context["verification_hash"], hash_token(payload["verification_token"]))
        result = self.client.post("/api/auth/signup", json=payload)
        self.assertEqual(result.status_code, 200, result.text)
        user = self.db.scalar(select(User))
        self.assertEqual((user.first_name, user.last_name, user.status), ("Test", "User", "active"))
        self.assertEqual(user.terms_version, CONSENT_VERSION)
        self.assertIsNotNone(user.terms_accepted_at)
        self.assertIsNotNone(user.email_verified_at)
        self.assertTrue(verify_password(user.password_hash, payload["password"]))
        self.assertIsNotNone(self.record.consumed_at)
        self.assertEqual(self.db.scalar(select(func.count(AuthSession.id))), 1)
        self.assertIn("auth_access", self.client.cookies)
        self.assertIn("auth_refresh", self.client.cookies)
        self.assertEqual(self.client.post("/api/auth/signup", json=payload).status_code, 400)
        self.assertEqual(self.db.scalar(select(func.count(User.id))), 1)
        csrf = self.client.cookies["auth_csrf"]
        response = self.client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf})
        self.assertEqual(response.status_code, 204, response.text)
        self.assertIsNotNone(self.db.scalar(select(AuthSession)).revoked_at)
        self.assertNotIn("auth_access", self.client.cookies)
        self.assertNotIn("auth_refresh", self.client.cookies)
        self.assertNotIn("auth_csrf", self.client.cookies)

    def test_incorrect_expired_replayed_and_other_email_tokens_rejected(self):
        challenge_id = self.start_email()
        payload = {"email": "new@example.com", "challenge_id": challenge_id, "token": self.token}
        for changes in ({"token": "wrong-token-at-least-twenty-characters"}, {"email": "other@example.com"}):
            with self.subTest(changes=changes):
                result = self.client.post("/api/auth/signup/email/verify", json={**payload, **changes})
                self.assertEqual(result.status_code, 400)
        self.record.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        self.db.commit()
        self.assertEqual(self.client.post("/api/auth/signup/email/verify", json=payload).status_code, 400)
        self.record.expires_at = datetime.now(UTC) + timedelta(minutes=5)
        self.db.commit()
        self.assertEqual(self.client.post("/api/auth/signup/email/verify", json=payload).status_code, 200)
        self.assertEqual(self.client.post("/api/auth/signup/email/verify", json=payload).status_code, 400)
        self.assertEqual(self.db.scalar(select(func.count(User.id))), 0)

    def test_signup_cannot_bypass_verification_names_or_consent(self):
        payload = self.verify_email()
        for changes, expected in (
            ({"verification_token": "unverified-proof-at-least-twenty"}, 400),
            ({"email": "other@example.com"}, 400),
            ({"terms_accepted": False}, 422),
            ({"first_name": "   "}, 422),
            ({"password": "short"}, 422),
        ):
            with self.subTest(changes=changes):
                self.assertEqual(self.client.post("/api/auth/signup", json={**payload, **changes}).status_code, expected)
        old_shape = {"email": payload["email"], "password": payload["password"]}
        self.assertEqual(self.client.post("/api/auth/signup", json=old_shape).status_code, 422)
        self.record.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        self.db.commit()
        self.assertEqual(self.client.post("/api/auth/signup", json=payload).status_code, 400)
        self.assertEqual(self.db.scalar(select(func.count(User.id))), 0)

    def test_delivery_failure_rolls_back_without_creating_account(self):
        from fastapi import HTTPException
        self.send_email.side_effect = HTTPException(status_code=503, detail="Email delivery failed.")
        with self.assertLogs("app.auth_routes", level="ERROR"):
            result = self.client.post("/api/auth/signup/email/start", json={"email": "new@example.com"})
        self.assertEqual(result.status_code, 503)
        self.assertEqual(self.db.scalar(select(func.count(User.id))), 0)
        self.assertEqual(self.db.scalar(select(func.count(AuthChallenge.id))), 0)

    def test_existing_email_is_not_disclosed_before_verification(self):
        self.db.add(User(email="new@example.com", status="active"))
        self.db.commit()
        challenge_id = self.start_email()
        result = self.client.post("/api/auth/signup/email/verify", json={
            "email": "new@example.com", "challenge_id": challenge_id, "token": self.token,
        })
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["next"], "login")
        self.assertEqual(self.db.scalar(select(func.count(User.id))), 1)

    def test_google_does_not_start_without_explicit_consent(self):
        with patch("app.auth_routes.httpx.post") as provider:
            result = self.client.get("/api/auth/oidc/google/start", follow_redirects=False)
            self.assertEqual(result.headers["location"], "/?auth=login")
            for body in ({}, {"terms_accepted": False}):
                self.assertEqual(self.client.post("/api/auth/oidc/google/start", json=body).status_code, 422)
            provider.assert_not_called()
        self.assertEqual(self.db.scalar(select(func.count(AuthChallenge.id))), 0)
        self.assertEqual(self.db.scalar(select(func.count(User.id))), 0)
        self.assertEqual(self.db.scalar(select(func.count(ExternalIdentity.id))), 0)

    def google_start(self):
        response = self.client.post("/api/auth/oidc/google/start", json={"terms_accepted": True})
        self.assertEqual(response.status_code, 200, response.text)
        query = parse_qs(urlparse(response.json()["authorization_url"]).query)
        self.record = self.db.scalar(select(AuthChallenge))
        self.record.expires_at = self.record.expires_at.replace(tzinfo=UTC)
        self.db.flush()
        self.assertEqual(self.record.context["consent_version"], CONSENT_VERSION)
        return query["state"][0]

    def test_google_denial_clears_pending_cookie_without_account_or_provider_exchange(self):
        state = self.google_start()
        with patch("app.auth_routes.httpx.post") as provider:
            response = self.client.get("/api/auth/oidc/google/callback", params={"state": state, "error": "access_denied"}, follow_redirects=False)
            provider.assert_not_called()
        self.assertEqual(response.status_code, 303)
        self.assertNotIn("auth_google_consent", self.client.cookies)
        self.assertIsNotNone(self.record.consumed_at)
        self.assertEqual(self.db.scalar(select(func.count(User.id))), 0)
        self.assertEqual(self.db.scalar(select(func.count(ExternalIdentity.id))), 0)

    def test_google_signup_persists_consent_and_redirects_to_account_without_storing_provider_tokens(self):
        state = self.google_start()
        token_response = Mock()
        token_response.json.return_value = {"id_token": "fictional-id-token", "access_token": "not-stored"}
        certificate_response = Mock()
        certificate_response.json.return_value = {"keys": []}
        with (
            patch("app.auth_routes.httpx.post", return_value=token_response),
            patch("app.auth_routes.httpx.get", return_value=certificate_response),
            patch("app.auth_routes.jwt.PyJWKSet.from_dict", return_value=Mock(keys=[Mock(key_id="fictional-key", key=object())])),
            patch("app.auth_routes.jwt.get_unverified_header", return_value={"kid": "fictional-key"}),
            patch("app.auth_routes.jwt.decode", return_value={
                "nonce": self.record.context["nonce"], "email_verified": True,
                "email": "google-user@example.com", "sub": "fictional-subject",
            }),
        ):
            result = self.client.get("/api/auth/oidc/google/callback", params={"state": state, "code": "fictional-code"}, follow_redirects=False)
        self.assertEqual(result.status_code, 303, result.text)
        self.assertEqual(result.headers["location"], "/?view=account")
        user = self.db.scalar(select(User))
        self.assertEqual(user.terms_version, CONSENT_VERSION)
        self.assertIsNotNone(user.terms_accepted_at)
        self.assertEqual(self.db.scalar(select(ExternalIdentity)).user_id, user.id)
        self.assertNotIn("not-stored", str(self.record.context))
        self.assertNotIn("auth_google_consent", self.client.cookies)
        self.assertIn("auth_access", self.client.cookies)

    def test_google_callback_requires_same_browser_and_cannot_replay(self):
        state = self.google_start()
        binding = self.client.cookies.get("auth_google_consent")
        self.client.cookies.clear()
        with patch("app.auth_routes.httpx.post") as provider:
            response = self.client.get("/api/auth/oidc/google/callback", params={"state": state, "code": "fictional-code"})
            provider.assert_not_called()
        self.assertEqual(response.status_code, 401)
        self.client.cookies.set("auth_google_consent", binding)
        self.record.consumed_at = datetime.now(UTC)
        self.db.commit()
        response = self.client.get("/api/auth/oidc/google/callback", params={"state": state, "code": "fictional-code"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.db.scalar(select(func.count(User.id))), 0)

    def test_essential_account_is_paid_without_changing_free_accounts_or_regranting(self):
        from app.attachment_limits import attachment_limit
        from app.billing_routes import read_account_entitlement
        from app.models import Case, DocumentCreditLedgerEntry
        free = User(email="free@example.com", status="active")
        self.db.add(free)
        self.db.commit()
        password = "fictional-test-account-password-not-a-secret"
        ensure_essential_test_account(self.db, password)
        self.db.commit()
        user = self.db.scalar(select(User).where(User.email == ESSENTIAL_TEST_EMAIL))
        case = self.db.scalar(select(Case))
        self.assertTrue(verify_password(user.password_hash, password))
        self.assertEqual(read_account_entitlement(user, self.db).status, "paid")
        self.assertEqual(read_account_entitlement(free, self.db).status, "free")
        self.assertEqual(attachment_limit(self.db, case.id), 100)
        self.assertEqual(case.attempt_credit_balance, 5)
        case.attempt_credit_balance = 2
        case.metadata_json = {"preserve": "existing work"}
        self.db.commit()
        ensure_essential_test_account(self.db, password)
        self.db.commit()
        self.assertEqual(case.attempt_credit_balance, 2)
        self.assertEqual(case.metadata_json, {"preserve": "existing work"})
        self.assertEqual(self.db.scalar(select(func.count(DocumentCreditLedgerEntry.id))), 1)
        with self.assertRaisesRegex(ValueError, "not modified"):
            ensure_essential_test_account(self.db, "different-fictional-password")
        self.assertEqual(self.db.scalar(select(func.count(User.id))), 2)

    def test_migration_preserves_existing_accounts_and_round_trips(self):
        path = Path(__file__).parents[1] / "migrations/versions/0029_signup_consent.py"
        spec = importlib.util.spec_from_file_location("signup_migration", path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        engine = create_engine("sqlite://")
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE users (id TEXT PRIMARY KEY, email TEXT)"))
            connection.execute(text("INSERT INTO users VALUES ('existing', 'existing@example.com')"))
            with patch.object(migration, "op", Operations(MigrationContext.configure(connection))):
                migration.upgrade()
                self.assertIsNone(connection.execute(text("SELECT terms_accepted_at FROM users")).scalar())
                self.assertIn("first_name", {col["name"] for col in inspect(connection).get_columns("users")})
                migration.downgrade()
                self.assertEqual(connection.execute(text("SELECT id FROM users")).scalar(), "existing")
        engine.dispose()
