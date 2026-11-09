import smtplib
import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import HTTPException
from starlette.requests import Request

from app.auth import hash_token, verify_password
from app.auth_routes import (
    EmailRequest,
    EmailTokenRequest,
    PasswordResetRequest,
    forgot_password,
    reset_password,
    verify_password_reset,
)
from app.config import Settings
from app.models import User


class PasswordRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="recovery-test-signing-secret-that-is-long-enough",
            smtp_host="smtp.example.test",
            auth_email_from="casework@example.com",
        )
        self.request = Request({
            "type": "http", "method": "POST", "path": "/api/auth/password/verify",
            "headers": [], "client": ("127.0.0.1", 12345),
        })
        self.user = SimpleNamespace(
            id=uuid4(), email="recovery@example.com", status="active", password_hash="old-hash"
        )
        self.code = "test-recovery-code-with-high-entropy"
        self.token = SimpleNamespace(
            id=uuid4(),
            user_id=self.user.id,
            created_at=datetime.now(UTC) - timedelta(minutes=6),
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
            used_at=None,
        )
        self.db = Mock()
        self.db.get.return_value = self.user
        self.settings_patch = patch("app.auth_routes.get_settings", return_value=self.settings)
        self.settings_patch.start()
        self.addCleanup(self.settings_patch.stop)
        self.limit_patch = patch("app.auth_routes._rate_limit")
        self.rate_limit = self.limit_patch.start()
        self.addCleanup(self.limit_patch.stop)

    def test_sending_code_hashes_it_and_revokes_previous_codes(self) -> None:
        self.db.scalar.side_effect = [self.user, None]
        with patch("app.auth_routes._send_security_email") as send:
            result = forgot_password(EmailRequest(email=self.user.email), self.request, self.db)
        token = self.db.add.call_args.args[0]
        body = send.call_args.args[2]
        code = body.split("\n\n")[1]
        self.assertEqual(token.token_hash, hash_token(code))
        self.assertNotEqual(token.token_hash, code)
        self.assertEqual(token.purpose, "password_reset")
        self.assertAlmostEqual(
            (token.expires_at - datetime.now(UTC)).total_seconds(), 1800, delta=5
        )
        self.assertIn("If the account exists", result["message"])
        self.assertIn("revoked_at", str(self.db.execute.call_args.args[0]))
        self.db.commit.assert_called_once()

    def test_resend_is_suppressed_for_five_minutes(self) -> None:
        for age, expected in ((299, False), (300, True), (301, True)):
            with self.subTest(age=age):
                self.db.reset_mock()
                self.token.created_at = datetime.now(UTC) - timedelta(seconds=age)
                self.db.scalar.side_effect = [self.user, self.token]
                with patch("app.auth_routes._send_security_email") as send:
                    forgot_password(EmailRequest(email=self.user.email), self.request, self.db)
                self.assertEqual(send.called, expected)

    def test_unknown_account_returns_same_generic_message_without_email(self) -> None:
        self.db.scalar.return_value = None
        with patch("app.auth_routes._send_security_email") as send:
            result = forgot_password(EmailRequest(email=self.user.email), self.request, self.db)
        self.assertEqual(
            result["message"], "If the account exists, password reset instructions will be sent."
        )
        send.assert_not_called()

    def test_email_failure_is_explicit_and_does_not_commit_code_or_cooldown(self) -> None:
        self.db.scalar.side_effect = [self.user, None]
        with patch("app.auth_routes._send_email", side_effect=smtplib.SMTPException("offline")):
            with self.assertRaises(HTTPException) as raised:
                forgot_password(EmailRequest(email=self.user.email), self.request, self.db)
        self.assertEqual(raised.exception.status_code, 503)
        self.db.commit.assert_not_called()

    def test_verification_does_not_consume_code_or_change_password(self) -> None:
        self.db.scalar.return_value = self.token
        result = verify_password_reset(EmailTokenRequest(token=self.code), self.request, self.db)
        self.assertIn("Code verified", result["message"])
        self.assertIsNone(self.token.used_at)
        self.assertEqual(self.user.password_hash, "old-hash")
        self.rate_limit.assert_called_once_with(self.db, self.request, "password-verify")

    def test_invalid_expired_and_ineligible_codes_are_rejected(self) -> None:
        for kind in ("missing", "expired", "inactive"):
            with self.subTest(kind=kind):
                self.db.scalar.return_value = None if kind == "missing" else self.token
                self.token.expires_at = datetime.now(UTC) + timedelta(
                    minutes=-1 if kind == "expired" else 10
                )
                self.user.status = "disabled" if kind == "inactive" else "active"
                with self.assertRaises(HTTPException) as raised:
                    verify_password_reset(EmailTokenRequest(token=self.code), self.request, self.db)
                self.assertEqual(raised.exception.status_code, 400)
                self.assertIn("try again", raised.exception.detail)
                self.db.commit.assert_not_called()

    def test_reset_hashes_password_consumes_code_and_revokes_sessions(self) -> None:
        self.db.scalar.return_value = self.token
        password = "A fresh password for recovery 2026!"
        reset_password(
            PasswordResetRequest(token=self.code, password=password), self.request, self.db
        )
        self.assertTrue(verify_password(self.user.password_hash, password))
        self.assertIsNotNone(self.token.used_at)
        self.db.get.assert_any_call(User, self.user.id, with_for_update=True)
        statements = [str(call.args[0]) for call in self.db.execute.call_args_list]
        self.assertTrue(any("auth_sessions" in statement for statement in statements))
        self.assertTrue(any("auth_tokens" in statement for statement in statements))
        self.db.commit.assert_called_once()
        self.db.reset_mock()
        self.db.scalar.return_value = None
        with self.assertRaises(HTTPException):
            reset_password(
                PasswordResetRequest(token=self.code, password=password), self.request, self.db
            )
        self.db.commit.assert_not_called()

    def test_code_revoked_while_waiting_for_account_lock_cannot_be_used(self) -> None:
        self.db.scalar.side_effect = [self.token, None]
        with self.assertRaises(HTTPException):
            reset_password(
                PasswordResetRequest(token=self.code, password="A fresh recovery password!"),
                self.request,
                self.db,
            )
        self.assertEqual(self.user.password_hash, "old-hash")
        self.db.commit.assert_not_called()
