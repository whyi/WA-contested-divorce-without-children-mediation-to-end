import smtplib
import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import HTTPException, Response
from starlette.requests import Request

from app.auth_routes import (
    LoginRequest,
    TotpCodeRequest,
    _create_session,
    _finish_login,
    _rate_limit,
    _require_csrf,
    _require_email_config,
    _require_secret_config,
    _send_security_email,
    _verify_second_factor,
    clear_auth_cookies,
    confirm_totp,
    disable_totp,
    enroll_totp,
    login,
    logout,
    refresh,
)
from app.config import Settings
from app.models import AuthSession, RecoveryCode, User


class AuthenticationRouteCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="auth-route-coverage-test-secret-is-long-enough",
            auth_encryption_key="auth-route-encryption-test-secret-is-long-enough",
            smtp_host="smtp.example.test",
            auth_email_from="casework@example.com",
            smtp_username="mailer",
            smtp_password="mailer-password",
        )

    @staticmethod
    def request(
        method: str = "POST",
        path: str = "/api/auth/test",
        headers: list[tuple[bytes, bytes]] | None = None,
        client: tuple[str, int] | None = ("127.0.0.1", 12345),
    ) -> Request:
        return Request(
            {
                "type": "http",
                "method": method,
                "path": path,
                "raw_path": path.encode(),
                "query_string": b"",
                "headers": headers or [],
                "server": ("testserver", 443),
                "client": client,
                "scheme": "https",
            }
        )

    def test_authentication_and_email_configuration_guards(self) -> None:
        for settings in (
            Settings(auth_enabled=False),
            SimpleNamespace(auth_enabled=True, auth_jwt_secret="short"),
            SimpleNamespace(auth_enabled=True, auth_jwt_secret=None),
        ):
            with self.subTest(settings=settings), patch(
                "app.auth_routes.get_settings", return_value=settings
            ):
                with self.assertRaisesRegex(HTTPException, "Authentication is not configured"):
                    _require_secret_config()

        with patch("app.auth_routes.get_settings", return_value=self.settings):
            _require_secret_config()
            _require_email_config()

        for settings in (
            self.settings.model_copy(update={"smtp_host": None}),
            self.settings.model_copy(update={"auth_email_from": None}),
        ):
            with self.subTest(settings=settings), patch(
                "app.auth_routes.get_settings", return_value=settings
            ):
                with self.assertRaisesRegex(HTTPException, "Email delivery is not configured"):
                    _require_email_config()

    def test_csrf_guard_requires_matching_cookie_and_header(self) -> None:
        matching = self.request(
            headers=[
                (b"cookie", b"auth_csrf=csrf-token"),
                (b"x-csrf-token", b"csrf-token"),
            ]
        )
        _require_csrf(matching)

        for headers in (
            [],
            [(b"cookie", b"auth_csrf=csrf-token")],
            [
                (b"cookie", b"auth_csrf=csrf-token"),
                (b"x-csrf-token", b"different-token"),
            ],
        ):
            with self.subTest(headers=headers), self.assertRaises(HTTPException) as raised:
                _require_csrf(self.request(headers=headers))
            self.assertEqual(raised.exception.status_code, 403)

    def test_rate_limit_commits_attempts_then_rejects_over_limit(self) -> None:
        db = Mock()
        db.execute.return_value.scalar_one.return_value = self.settings.auth_rate_limit_attempts
        with patch("app.auth_routes.get_settings", return_value=self.settings):
            _rate_limit(db, self.request(client=None), "login", "USER@example.com")
        db.commit.assert_called_once_with()

        db.reset_mock()
        db.execute.return_value.scalar_one.return_value = self.settings.auth_rate_limit_attempts + 1
        with (
            patch("app.auth_routes.get_settings", return_value=self.settings),
            self.assertRaises(HTTPException) as raised,
        ):
            _rate_limit(db, self.request(client=None), "login", "USER@example.com")
        self.assertEqual(raised.exception.status_code, 429)
        db.commit.assert_called_once_with()

    def test_security_email_transport_failure_becomes_service_unavailable(self) -> None:
        with (
            patch("app.auth_routes._send_email", side_effect=smtplib.SMTPException("offline")),
            self.assertLogs("app.auth_routes", level="ERROR"),
            self.assertRaises(HTTPException) as raised,
        ):
            _send_security_email("user@example.com", "Verify", "token")
        self.assertEqual(raised.exception.status_code, 503)

    def test_login_rejects_missing_inactive_and_invalid_users(self) -> None:
        scenarios = (
            (None, False),
            (
                SimpleNamespace(id=uuid4(), status="disabled", password_hash="hash", email="u@example.com"),
                False,
            ),
            (
                SimpleNamespace(id=uuid4(), status="active", password_hash=None, email="u@example.com"),
                False,
            ),
            (
                SimpleNamespace(id=uuid4(), status="active", password_hash="hash", email="u@example.com"),
                False,
            ),
        )
        for user, valid_password in scenarios:
            with self.subTest(user=user, valid_password=valid_password):
                db = Mock()
                db.scalar.return_value = user
                with (
                    patch("app.auth_routes.get_settings", return_value=self.settings),
                    patch("app.auth_routes._rate_limit"),
                    patch("app.auth_routes.verify_password", return_value=valid_password),
                    self.assertRaises(HTTPException) as raised,
                ):
                    login(
                        LoginRequest(email="u@example.com", password="bad"),
                        self.request(path="/api/auth/login"),
                        Response(),
                        db,
                    )
                self.assertEqual(raised.exception.status_code, 401)
                db.commit.assert_called_once_with()

    def test_password_login_returns_an_mfa_challenge_for_enabled_accounts(self) -> None:
        user = SimpleNamespace(
            id=uuid4(),
            email="u@example.com",
            status="active",
            password_hash="hash",
            mfa_enabled=True,
        )
        db = Mock()
        db.scalar.return_value = user
        with (
            patch("app.auth_routes.get_settings", return_value=self.settings),
            patch("app.auth_routes._rate_limit"),
            patch("app.auth_routes._owner_beta_allows", return_value=True),
            patch("app.auth_routes.verify_password", return_value=True),
            patch("app.auth_routes.random_token", side_effect=["challenge-token"]),
        ):
            result = login(
                LoginRequest(email="u@example.com", password="correct"),
                self.request(path="/api/auth/login"),
                Response(),
                db,
            )
        self.assertTrue(result["mfa_required"])
        self.assertEqual(result["challenge"], "challenge-token")
        db.commit.assert_called_once_with()
        self.assertEqual(db.add.call_args.args[0].purpose, "mfa_login")

    def test_password_login_finishes_non_mfa_account(self) -> None:
        user = SimpleNamespace(
            id=uuid4(),
            email="u@example.com",
            status="active",
            password_hash="hash",
            mfa_enabled=False,
        )
        db = Mock()
        db.scalar.return_value = user
        expected = {"session_id": "session-id"}
        response = Response()
        with (
            patch("app.auth_routes.get_settings", return_value=self.settings),
            patch("app.auth_routes._rate_limit"),
            patch("app.auth_routes._owner_beta_allows", return_value=True),
            patch("app.auth_routes.verify_password", return_value=True),
            patch("app.auth_routes._finish_login", return_value=expected) as finish,
        ):
            result = login(
                LoginRequest(email="u@example.com", password="correct"),
                self.request(path="/api/auth/login"),
                response,
                db,
            )
        self.assertEqual(result, expected)
        finish.assert_called_once_with(db, user, response)

    def test_create_session_revokes_oldest_sessions_and_limits_refresh_lifetime(self) -> None:
        user_id = uuid4()
        oldest = SimpleNamespace(revoked_at=None, revoke_reason=None)
        newest = SimpleNamespace(revoked_at=None, revoke_reason=None)
        db = Mock()
        db.scalars.return_value = [newest, oldest]

        def assign_session_id() -> None:
            db.add.call_args.args[0].id = uuid4()

        db.flush.side_effect = assign_session_id
        settings = self.settings.model_copy(
            update={
                "auth_max_active_sessions": 2,
                "auth_absolute_session_days": 1,
                "auth_refresh_token_days": 30,
            }
        )
        user = SimpleNamespace(id=user_id)
        with (
            patch("app.auth_routes.get_settings", return_value=settings),
            patch(
                "app.auth_routes.create_refresh_token",
                return_value=("refresh-token", "refresh-id", datetime.now(UTC) + timedelta(days=5)),
            ) as create_refresh,
            patch("app.auth_routes.create_access_token", return_value=("access-token", "jti", datetime.now(UTC))),
            patch("app.auth_routes.hash_token", return_value="refresh-hash"),
            patch("app.auth_routes.random_token", return_value="csrf-token"),
        ):
            session, access, refresh_token, csrf = _create_session(db, user)

        self.assertIsNone(newest.revoked_at)
        self.assertEqual(oldest.revoke_reason, "session_limit")
        self.assertIsNotNone(oldest.revoked_at)
        self.assertEqual(session.user_id, user_id)
        self.assertEqual((access, refresh_token, csrf), ("access-token", "refresh-token", "csrf-token"))
        self.assertLessEqual(
            create_refresh.call_args.kwargs["lifetime"],
            timedelta(days=1),
        )
        refresh_record = db.add.call_args.args[0]
        self.assertEqual(refresh_record.session_id, session.id)

    def test_finish_login_commits_and_sets_auth_cookies(self) -> None:
        user = SimpleNamespace(id=uuid4())
        session = SimpleNamespace(id=uuid4())
        db = Mock()
        response = Response()
        with (
            patch("app.auth_routes._create_session", return_value=(session, "access", "refresh", "csrf")),
            patch("app.auth_routes._audit") as audit,
            patch("app.auth_routes.get_settings", return_value=self.settings),
            patch("app.auth_routes._set_auth_cookies") as set_cookies,
        ):
            result = _finish_login(db, user, response)
        self.assertEqual(result["session_id"], str(session.id))
        self.assertEqual(result["expires_in"], self.settings.auth_access_token_minutes * 60)
        audit.assert_called_once_with(db, "login", "success", user.id)
        db.commit.assert_called_once_with()
        set_cookies.assert_called_once_with(response, "access", "refresh", "csrf")

    def test_refresh_without_token_clears_cookies_after_csrf_validation(self) -> None:
        request = self.request(
            path="/api/auth/refresh",
            headers=[
                (b"cookie", b"auth_csrf=csrf-token"),
                (b"x-csrf-token", b"csrf-token"),
            ],
        )
        with (
            patch("app.auth_routes.get_settings", return_value=self.settings),
            patch("app.auth_routes._rate_limit"),
            self.assertRaises(HTTPException) as raised,
        ):
            refresh(request, Response(), Mock())
        self.assertEqual(raised.exception.status_code, 401)

    def test_refresh_rotates_tokens_and_commits_new_session_activity(self) -> None:
        now = datetime.now(UTC)
        session_id, user_id = uuid4(), uuid4()
        stored = SimpleNamespace(used_at=None, revoked_at=None, expires_at=now + timedelta(days=1))
        session = SimpleNamespace(
            id=session_id,
            family_id=uuid4(),
            revoked_at=None,
            idle_expires_at=now + timedelta(days=1),
            absolute_expires_at=now + timedelta(days=2),
            last_used_at=None,
        )
        user = SimpleNamespace(id=user_id, status="active", email="u@example.com")
        db = Mock()
        db.scalar.return_value = stored
        db.get.side_effect = [session, user]
        request = self.request(
            path="/api/auth/refresh",
            headers=[
                (b"cookie", b"auth_csrf=csrf-token; auth_refresh=refresh-token"),
                (b"x-csrf-token", b"csrf-token"),
            ],
        )
        response = Response()
        with (
            patch("app.auth_routes.get_settings", return_value=self.settings),
            patch("app.auth_routes._rate_limit"),
            patch(
                "app.auth_routes.verify_token",
                return_value={"sid": str(session_id), "sub": str(user_id), "jti": "old-jti"},
            ),
            patch(
                "app.auth_routes.create_refresh_token",
                return_value=("new-refresh", "new-jti", now + timedelta(days=1)),
            ),
            patch("app.auth_routes.create_access_token", return_value=("new-access", "access-jti", now)),
            patch("app.auth_routes.hash_token", return_value="hashed-jti"),
            patch("app.auth_routes.random_token", return_value="new-csrf"),
            patch("app.auth_routes._audit"),
            patch("app.auth_routes._set_auth_cookies") as set_cookies,
        ):
            result = refresh(request, response, db)
        self.assertEqual(result["access_token"], "new-access")
        self.assertEqual(session.last_used_at, stored.used_at)
        self.assertIsNotNone(session.idle_expires_at)
        self.assertEqual(set_cookies.call_args.args[1:], ("new-access", "new-refresh", "new-csrf"))
        db.commit.assert_called_once_with()

    def test_refresh_reuse_revokes_the_token_family(self) -> None:
        now = datetime.now(UTC)
        session_id, user_id = uuid4(), uuid4()
        session = SimpleNamespace(
            id=session_id,
            family_id=uuid4(),
            revoked_at=None,
            idle_expires_at=now + timedelta(days=1),
            absolute_expires_at=now + timedelta(days=2),
        )
        stored = SimpleNamespace(used_at=now, revoked_at=None, expires_at=now + timedelta(days=1))
        user = SimpleNamespace(id=user_id, email="u@example.com")
        db = Mock()
        db.scalar.return_value = stored
        db.get.side_effect = [session, user]
        request = self.request(
            path="/api/auth/refresh",
            headers=[
                (b"cookie", b"auth_csrf=csrf-token; auth_refresh=refresh-token"),
                (b"x-csrf-token", b"csrf-token"),
            ],
        )
        response = Response()
        with (
            patch("app.auth_routes.get_settings", return_value=self.settings),
            patch("app.auth_routes._rate_limit"),
            patch("app.auth_routes.verify_token", return_value={"sid": str(session_id), "sub": str(user_id), "jti": "jti"}),
            patch("app.auth_routes._audit"),
            self.assertRaises(HTTPException) as raised,
        ):
            refresh(request, response, db)
        self.assertIn("reuse detected", raised.exception.detail)
        db.execute.assert_called_once()
        db.commit.assert_called_once_with()

    def test_refresh_invalid_token_rolls_back_authentication_without_leaking_state(self) -> None:
        request = self.request(
            path="/api/auth/refresh",
            headers=[
                (b"cookie", b"auth_csrf=csrf-token; auth_refresh=bad-token"),
                (b"x-csrf-token", b"csrf-token"),
            ],
        )
        response = Response()
        with (
            patch("app.auth_routes.get_settings", return_value=self.settings),
            patch("app.auth_routes._rate_limit"),
            patch("app.auth_routes.verify_token", side_effect=ValueError("invalid")),
            self.assertRaises(HTTPException) as raised,
        ):
            refresh(request, response, Mock())
        self.assertEqual(raised.exception.status_code, 401)
        self.assertTrue(
            any("auth_refresh=" in cookie for cookie in response.headers.getlist("set-cookie"))
        )

    def test_logout_revokes_valid_session_and_always_clears_cookies(self) -> None:
        session = SimpleNamespace(user_id=uuid4(), revoked_at=None, revoke_reason=None)
        db = Mock()
        db.get.return_value = session
        request = self.request(
            path="/api/auth/logout",
            headers=[
                (b"cookie", b"auth_csrf=csrf-token; auth_refresh=refresh-token"),
                (b"x-csrf-token", b"csrf-token"),
            ],
        )
        response = Response()
        with (
            patch("app.auth_routes.get_settings", return_value=self.settings),
            patch("app.auth_routes.verify_token", return_value={"sid": str(uuid4())}),
            patch("app.auth_routes._audit") as audit,
        ):
            result = logout(request, response, db)
        self.assertIsNone(result)
        self.assertEqual(session.revoke_reason, "logout")
        audit.assert_called_once()
        db.commit.assert_called_once_with()
        cookies = response.headers.getlist("set-cookie")
        self.assertEqual(len(cookies), 3)

    def test_logout_malformed_refresh_token_rolls_back_and_clears_cookies(self) -> None:
        db = Mock()
        request = self.request(
            path="/api/auth/logout",
            headers=[
                (b"cookie", b"auth_csrf=csrf-token; auth_refresh=bad-token"),
                (b"x-csrf-token", b"csrf-token"),
            ],
        )
        response = Response()
        with (
            patch("app.auth_routes.get_settings", return_value=self.settings),
            patch("app.auth_routes.verify_token", side_effect=ValueError("bad token")),
        ):
            logout(request, response, db)
        db.rollback.assert_called_once_with()
        self.assertEqual(len(response.headers.getlist("set-cookie")), 3)

    def test_clear_auth_cookies_uses_configured_security_attributes(self) -> None:
        response = Response()
        settings = self.settings.model_copy(
            update={"auth_cookie_secure": False, "auth_cookie_samesite": "strict"}
        )
        with patch("app.auth_routes.get_settings", return_value=settings):
            clear_auth_cookies(response)
        cookies = response.headers.getlist("set-cookie")
        self.assertEqual(len(cookies), 3)
        self.assertTrue(all("SameSite=strict" in cookie for cookie in cookies))

    def test_totp_second_factor_accepts_unused_recovery_code_once(self) -> None:
        user = SimpleNamespace(id=uuid4())
        recovery = SimpleNamespace(used_at=None)
        db = Mock()
        db.scalar.return_value = recovery
        credential = SimpleNamespace(encrypted_secret=b"encrypted")
        with (
            patch("app.auth_routes._decrypt_totp", return_value="secret"),
            patch("app.auth_routes._verify_totp", return_value=None),
            patch("app.auth_routes.hash_token", return_value="recovery-hash"),
            patch("app.auth_routes._audit") as audit,
        ):
            self.assertTrue(_verify_second_factor(db, user, credential, "recovery-code"))
        self.assertIsNotNone(recovery.used_at)
        audit.assert_called_once_with(db, "recovery_code_used", "success", user.id)

    def test_totp_second_factor_rejects_replayed_step_and_missing_recovery_code(self) -> None:
        user = SimpleNamespace(id=uuid4())
        credential = SimpleNamespace(encrypted_secret=b"encrypted", last_used_step=10)
        db = Mock()
        with (
            patch("app.auth_routes._decrypt_totp", return_value="secret"),
            patch("app.auth_routes._verify_totp", return_value=10),
        ):
            self.assertFalse(_verify_second_factor(db, user, credential, "123456"))
        db.scalar.assert_not_called()

        with (
            patch("app.auth_routes._decrypt_totp", return_value="secret"),
            patch("app.auth_routes._verify_totp", return_value=None),
        ):
            db.scalar.return_value = None
            self.assertFalse(_verify_second_factor(db, user, credential, "no-recovery"))

    def test_totp_enrollment_creates_or_resets_pending_credential(self) -> None:
        user = SimpleNamespace(id=uuid4(), email="u@example.com")
        request = self.request(path="/api/auth/mfa/totp/enroll")
        for existing in (None, SimpleNamespace(
            encrypted_secret=b"old",
            pending=False,
            last_used_step=123,
            confirmed_at=datetime.now(UTC),
            revoked_at=datetime.now(UTC),
        )):
            db = Mock()
            db.scalar.return_value = existing
            with (
                self.subTest(existing=existing),
                patch("app.auth_routes._rate_limit"),
                patch("app.auth_routes._encrypt_totp", return_value=b"encrypted"),
                patch("app.auth_routes.get_settings", return_value=self.settings),
            ):
                result = enroll_totp(request, user, db)
            self.assertTrue(result["secret"])
            self.assertIn("otpauth://totp/", result["provisioning_uri"])
            if existing is None:
                self.assertTrue(db.add.call_args.args[0].pending)
            else:
                self.assertTrue(existing.pending)
                self.assertIsNone(existing.last_used_step)
                self.assertIsNone(existing.confirmed_at)
                self.assertIsNone(existing.revoked_at)
            db.commit.assert_called_once_with()

    def test_confirm_totp_rejects_missing_or_invalid_pending_enrollment(self) -> None:
        user = SimpleNamespace(id=uuid4(), mfa_enabled=False)
        request = self.request(path="/api/auth/mfa/totp/confirm")
        for credential, verified_step in ((None, None), (SimpleNamespace(encrypted_secret=b"secret"), None)):
            db = Mock()
            db.scalar.return_value = credential
            patches = [
                patch("app.auth_routes._rate_limit"),
                patch("app.auth_routes._decrypt_totp", return_value="secret"),
                patch("app.auth_routes._verify_totp", return_value=verified_step),
            ]
            with self.subTest(credential=credential), patches[0], patches[1], patches[2]:
                with self.assertRaises(HTTPException) as raised:
                    confirm_totp(TotpCodeRequest(code="123456"), request, user, db)
            self.assertEqual(raised.exception.status_code, 409 if credential is None else 401)
            db.commit.assert_not_called()

    def test_confirm_totp_activates_mfa_and_issues_recovery_codes(self) -> None:
        user = SimpleNamespace(id=uuid4(), email="u@example.com", mfa_enabled=False)
        credential = SimpleNamespace(
            encrypted_secret=b"encrypted",
            pending=True,
            last_used_step=None,
            confirmed_at=None,
        )
        db = Mock()
        db.scalar.return_value = credential
        with (
            patch("app.auth_routes._rate_limit"),
            patch("app.auth_routes._decrypt_totp", return_value="secret"),
            patch("app.auth_routes._verify_totp", return_value=123),
            patch("app.auth_routes.secrets.token_urlsafe", return_value="recovery-code"),
            patch("app.auth_routes._audit") as audit,
        ):
            result = confirm_totp(
                TotpCodeRequest(code="123456"),
                self.request(path="/api/auth/mfa/totp/confirm"),
                user,
                db,
            )
        self.assertEqual(len(result["recovery_codes"]), 10)
        self.assertTrue(user.mfa_enabled)
        self.assertFalse(credential.pending)
        self.assertEqual(credential.last_used_step, 123)
        self.assertEqual(len(list(db.add_all.call_args.args[0])), 10)
        audit.assert_called_once()
        db.commit.assert_called_once_with()

    def test_disable_totp_requires_credential_and_valid_second_factor(self) -> None:
        user = SimpleNamespace(id=uuid4(), mfa_enabled=True)
        request = self.request(path="/api/auth/mfa/totp/disable")
        for credential, valid in ((None, False), (SimpleNamespace(revoked_at=None), False)):
            db = Mock()
            db.scalar.return_value = credential
            with (
                self.subTest(credential=credential),
                patch("app.auth_routes._rate_limit"),
                patch("app.auth_routes._verify_second_factor", return_value=valid),
            ):
                with self.assertRaises(HTTPException) as raised:
                    disable_totp(TotpCodeRequest(code="123456"), request, user, db)
            self.assertEqual(raised.exception.status_code, 409 if credential is None else 401)
            db.commit.assert_not_called()

    def test_disable_totp_revokes_factor_and_active_sessions(self) -> None:
        user = SimpleNamespace(id=uuid4(), mfa_enabled=True)
        credential = SimpleNamespace(revoked_at=None)
        db = Mock()
        db.scalar.return_value = credential
        with (
            patch("app.auth_routes._rate_limit"),
            patch("app.auth_routes._verify_second_factor", return_value=True),
            patch("app.auth_routes._audit") as audit,
        ):
            result = disable_totp(
                TotpCodeRequest(code="123456"),
                self.request(path="/api/auth/mfa/totp/disable"),
                user,
                db,
            )
        self.assertFalse(user.mfa_enabled)
        self.assertIsNotNone(credential.revoked_at)
        self.assertEqual(result["message"], "TOTP has been disabled. Sign in again.")
        audit.assert_called_once()
        db.execute.assert_called_once()
        db.commit.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
