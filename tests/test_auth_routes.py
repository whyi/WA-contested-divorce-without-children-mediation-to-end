import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import Mock, patch

from fastapi import HTTPException, Response
from fastapi.testclient import TestClient
import pyotp
from starlette.requests import Request

from app.database import get_db
from app.auth_routes import (
    LoginRequest,
    _current_user,
    _decrypt_totp,
    _encrypt_totp,
    _set_auth_cookies,
    _verify_totp,
    login,
    router,
)
from app.config import Settings
from app.main import app


class AuthenticationRouteTests(unittest.TestCase):
    def test_authentication_contract_routes_are_registered(self) -> None:
        paths = {route.path for route in router.routes}
        required = {
            "/api/auth/signup",
            "/api/auth/providers",
            "/api/auth/verify-email",
            "/api/auth/verify-email/resend",
            "/api/auth/login",
            "/api/auth/refresh",
            "/api/auth/logout",
            "/api/auth/password/forgot",
            "/api/auth/password/reset",
            "/api/auth/oidc/google/start",
            "/api/auth/oidc/google/callback",
            "/api/auth/oidc/google/link/start",
            "/api/auth/mfa/totp/enroll",
            "/api/auth/mfa/totp/confirm",
            "/api/auth/mfa/totp/verify",
            "/api/auth/mfa/totp/disable",
            "/api/auth/passkeys/register/options",
            "/api/auth/passkeys/register/verify",
            "/api/auth/passkeys/authenticate/options",
            "/api/auth/passkeys/authenticate/verify",
            "/api/auth/passkeys",
            "/api/auth/passkeys/{credential_id}",
            "/api/auth/sessions",
            "/api/auth/sessions/{session_id}",
        }

        self.assertTrue(required.issubset(paths), sorted(required - paths))

    def test_pending_account_deletion_blocks_stale_sessions_except_retry_endpoint(self) -> None:
        user_id, session_id = uuid4(), uuid4()
        now = datetime.now(UTC)
        user = SimpleNamespace(id=user_id, status="disabled")
        session = SimpleNamespace(
            user_id=user_id,
            revoked_at=None,
            idle_expires_at=now + timedelta(days=1),
            absolute_expires_at=now + timedelta(days=2),
        )
        tombstone = SimpleNamespace(status="pending")
        db = Mock()
        db.get.side_effect = lambda model, key: session if model.__name__ == "AuthSession" else user
        db.scalar.return_value = tombstone
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="secure-test-signing-secret-that-is-long-enough",
        )

        def make_request(path: str) -> Request:
            return Request(
                {
                    "type": "http",
                    "method": "DELETE",
                    "path": path,
                    "raw_path": path.encode(),
                    "query_string": b"",
                    "headers": [(b"authorization", b"Bearer access-token")],
                    "server": ("testserver", 80),
                    "client": ("testclient", 12345),
                    "scheme": "http",
                }
            )

        with (
            patch("app.auth_routes.get_settings", return_value=settings),
            patch(
                "app.auth_routes.verify_token",
                return_value={"sub": str(user_id), "sid": str(session_id)},
            ),
        ):
            self.assertIs(
                _current_user(make_request("/api/v1/account/permanent-deletion"), db),
                user,
            )
            with self.assertRaises(HTTPException) as raised:
                _current_user(make_request("/api/auth/sessions"), db)

        self.assertEqual(raised.exception.status_code, 401)

    def test_passkey_verification_handlers_are_not_duplicated(self) -> None:
        handlers = [
            route.endpoint.__name__
            for route in router.routes
            if route.path.endswith("/passkeys/register/verify")
        ]

        self.assertEqual(handlers, ["verify_passkey_registration"])

    def test_totp_secrets_are_encrypted_and_codes_are_time_bounded(self) -> None:
        settings = Settings(
            auth_encryption_key="totp-encryption-secret-long-enough-for-tests",
        )
        secret = pyotp.random_base32()
        with patch("app.auth_routes.get_settings", return_value=settings):
            encrypted = _encrypt_totp(secret)

            self.assertNotIn(secret.encode(), encrypted)
            self.assertEqual(_decrypt_totp(encrypted), secret)

        code = pyotp.TOTP(secret).now()
        self.assertIsNotNone(_verify_totp(secret, code))
        self.assertIsNone(_verify_totp(secret, "abcdef"))

    def test_browser_auth_cookies_are_http_only_and_csrf_cookie_is_accessible(self) -> None:
        settings = Settings()
        response = Response()
        with patch("app.auth_routes.get_settings", return_value=settings):
            _set_auth_cookies(response, "access", "refresh", "csrf")

        headers = response.headers.getlist("set-cookie")
        self.assertTrue(any("auth_access=access" in header and "HttpOnly" in header for header in headers))
        self.assertTrue(any("auth_refresh=refresh" in header and "HttpOnly" in header for header in headers))
        self.assertTrue(any("auth_csrf=csrf" in header and "HttpOnly" not in header for header in headers))

    def test_authentication_routes_fail_closed_when_disabled(self) -> None:
        disabled = Settings(
            auth_enabled=False,
            demo_mode_enabled=False,
            auth_jwt_secret=None,
        )
        with patch("app.auth_routes.get_settings", return_value=disabled):
            response = TestClient(app).post(
                "/api/auth/passkeys/authenticate/options",
                json={},
            )

        self.assertEqual(response.status_code, 503)

    def test_google_provider_is_reported_unavailable_when_auth_is_disabled(self) -> None:
        disabled = Settings(
            auth_enabled=False,
            demo_mode_enabled=False,
            auth_jwt_secret=None,
        )
        with patch("app.auth_routes.get_settings", return_value=disabled):
            response = TestClient(app).get("/api/auth/providers")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"google": False, "demo": False})

    def test_google_provider_is_reported_available_when_fully_configured(self) -> None:
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="a-secure-test-signing-secret-that-is-long-enough",
            google_client_id="google-client-id",
            google_client_secret="google-client-secret",
        )
        with patch("app.auth_routes.get_settings", return_value=settings):
            response = TestClient(app).get("/api/auth/providers")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"google": True, "demo": False})

    def test_google_callback_redirects_without_returning_auth_tokens(self) -> None:
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="a-secure-test-signing-secret-that-is-long-enough",
            google_client_id="google-client-id",
            google_client_secret="google-client-secret",
        )
        challenge = SimpleNamespace(
            purpose="google_oidc",
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
            context={"verifier": "test-verifier", "nonce": "test-nonce"},
            consumed_at=None,
            user_id=None,
        )
        user = Mock(id=uuid4(), status="active", mfa_enabled=False)
        db = Mock()
        identity = SimpleNamespace(user_id=user.id)
        db.scalar.side_effect = [challenge, identity]
        db.get.return_value = user
        token_response = Mock()
        token_response.json.return_value = {"id_token": "google-id-token"}
        certs_response = Mock()
        certs_response.json.return_value = {"keys": []}
        session = Mock(id=uuid4())
        original_db_override = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = lambda: db

        try:
            with (
                patch("app.auth_routes.get_settings", return_value=settings),
                patch("app.auth_routes._rate_limit"),
                patch("app.auth_routes.httpx.post", return_value=token_response),
                patch("app.auth_routes.httpx.get", return_value=certs_response),
                patch(
                    "app.auth_routes.jwt.PyJWKSet.from_dict",
                    return_value=Mock(
                        keys=[Mock(key_id="google-key", key=object())]
                    ),
                ),
                patch(
                    "app.auth_routes.jwt.get_unverified_header",
                    return_value={"kid": "google-key"},
                ),
                patch(
                    "app.auth_routes.jwt.decode",
                    return_value={
                        "nonce": "test-nonce",
                        "email_verified": True,
                        "email": "user@example.com",
                        "sub": "google-subject",
                    },
                ),
                patch(
                    "app.auth_routes._create_session",
                    return_value=(
                        session,
                        "access-token-secret",
                        "refresh-token-secret",
                        "csrf-token",
                    ),
                ),
                patch("app.auth_routes._audit"),
            ):
                response = TestClient(app).get(
                    "/api/auth/oidc/google/callback",
                    params={"state": "test-state", "code": "authorization-code"},
                    follow_redirects=False,
                )
        finally:
            if original_db_override is None:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = original_db_override

        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "/")
        self.assertEqual(response.content, b"")
        self.assertNotIn("access-token-secret", response.text)
        self.assertNotIn("refresh-token-secret", response.text)
        self.assertIn("auth_access=", response.headers["set-cookie"])
        self.assertIn("auth_refresh=", response.headers["set-cookie"])
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.headers["referrer-policy"], "no-referrer")

    def test_demo_provider_is_reported_available_only_in_demo_mode(self) -> None:
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="local-demo-signing-key-that-is-long-enough",
            demo_mode_enabled=True,
        )
        with patch("app.auth_routes.get_settings", return_value=settings):
            response = TestClient(app).get("/api/auth/providers")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"google": False, "demo": True})

    def test_demo_login_accepts_demo_credentials_only_when_demo_mode_is_enabled(self) -> None:
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="local-demo-signing-key-that-is-long-enough",
            demo_mode_enabled=True,
        )
        user = Mock(status="active", password_hash="hashed-demo", mfa_enabled=False)
        db = Mock()
        db.scalar.return_value = user
        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/api/auth/login",
                "headers": [],
                "client": ("127.0.0.1", 12345),
            }
        )
        response = Response()

        with (
            patch("app.auth_routes.get_settings", return_value=settings),
            patch("app.auth_routes._rate_limit"),
            patch("app.auth_routes.verify_demo_password", return_value=True) as verify_demo,
            patch("app.auth_routes.verify_password") as verify_password,
            patch("app.auth_routes._finish_login", return_value={"session_id": "demo-session"}),
        ):
            result = login(
                LoginRequest(email="demo", password="demo"),
                request,
                response,
                db,
            )

        self.assertEqual(result, {"session_id": "demo-session"})
        verify_demo.assert_called_once_with("demo", "hashed-demo")
        verify_password.assert_not_called()

    def test_demo_login_rejects_an_incorrect_password(self) -> None:
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="local-demo-signing-key-that-is-long-enough",
            demo_mode_enabled=True,
        )
        user = Mock(status="active", password_hash="hashed-demo", mfa_enabled=False)
        db = Mock()
        db.scalar.return_value = user
        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/api/auth/login",
                "headers": [],
                "client": ("127.0.0.1", 12345),
            }
        )

        with (
            patch("app.auth_routes.get_settings", return_value=settings),
            patch("app.auth_routes._rate_limit"),
            patch("app.auth_routes.verify_demo_password", return_value=False),
            self.assertRaises(HTTPException) as raised,
        ):
            login(
                LoginRequest(email="demo", password="wrong"),
                request,
                Response(),
                db,
            )

        self.assertEqual(raised.exception.status_code, 401)
        self.assertEqual(raised.exception.detail, "Invalid email or password.")

    def test_mfa_challenge_is_sent_in_the_request_body_not_the_url(self) -> None:
        operation = app.openapi()["paths"]["/api/auth/mfa/totp/verify"]["post"]

        self.assertIn("requestBody", operation)
        self.assertNotIn("parameters", operation)


if __name__ == "__main__":
    unittest.main()
