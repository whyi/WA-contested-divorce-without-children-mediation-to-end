import unittest
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt

from app.auth import (
    AuthConfigurationError,
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    normalize_email,
    validate_password,
    verify_password,
    verify_token,
)
from app.config import Settings


class AuthenticationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Settings(
            auth_jwt_secret="test-only-secret-that-is-long-enough-123456",
            auth_issuer="https://auth.example.test",
            auth_audience="casework-test",
        )

    def test_normalizes_email_without_provider_specific_rewriting(self) -> None:
        self.assertEqual(normalize_email("  Person+case@gmail.com "), "person+case@gmail.com")
        self.assertNotEqual(
            normalize_email("person.name@gmail.com"),
            normalize_email("personname@gmail.com"),
        )

    def test_rejects_short_and_common_passwords(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least"):
            validate_password("short")
        with self.assertRaisesRegex(ValueError, "common"):
            validate_password("Password123!")

    def test_password_size_limit_counts_utf8_bytes(self) -> None:
        with self.assertRaisesRegex(ValueError, "1024"):
            validate_password("éabc123456789xyz" * 70)

    def test_password_hash_verifies_without_storing_plaintext(self) -> None:
        password = "correct horse battery staple 92!"
        password_hash = hash_password(password)

        self.assertNotEqual(password_hash, password)
        self.assertTrue(password_hash.startswith("$argon2id$"))
        self.assertTrue(verify_password(password_hash, password))
        self.assertFalse(verify_password(password_hash, "incorrect password"))

    def test_access_token_has_required_claims_and_validates_audience(self) -> None:
        user_id = uuid4()
        token, token_id, expires_at = create_access_token(user_id, self.settings)
        claims = verify_token(token, self.settings, "access")

        self.assertEqual(claims["sub"], str(user_id))
        self.assertEqual(claims["jti"], token_id)
        self.assertEqual(claims["iss"], self.settings.auth_issuer)
        self.assertEqual(claims["aud"], self.settings.auth_audience)
        self.assertGreater(expires_at, datetime.now(UTC))

    def test_rejects_wrong_token_type_and_invalid_signature(self) -> None:
        token, _, _ = create_access_token(uuid4(), self.settings)
        with self.assertRaises(ValueError):
            verify_token(token, self.settings, "refresh")

        forged = jwt.encode(
            {
                "sub": str(uuid4()),
                "jti": str(uuid4()),
                "iss": self.settings.auth_issuer,
                "aud": self.settings.auth_audience,
                "iat": datetime.now(UTC),
                "exp": datetime.now(UTC) + timedelta(minutes=1),
                "token_type": "access",
            },
            "attacker-controlled-secret-that-is-long-enough",
            algorithm="HS256",
        )
        with self.assertRaises(ValueError):
            verify_token(forged, self.settings, "access")

    def test_authentication_fails_closed_without_a_signing_secret(self) -> None:
        with self.assertRaises(AuthConfigurationError):
            create_access_token(
                uuid4(),
                Settings(
                    auth_enabled=False,
                    demo_mode_enabled=False,
                    auth_jwt_secret=None,
                ),
            )

    def test_token_hash_is_stable_and_one_way(self) -> None:
        token = "random-single-use-verification-token"

        self.assertEqual(hash_token(token), hash_token(token))
        self.assertNotEqual(hash_token(token), token)

    def test_refresh_token_has_a_distinct_token_type_and_session_claim(self) -> None:
        user_id = uuid4()
        session_id = uuid4()
        token, _, _ = create_refresh_token(user_id, session_id, self.settings)

        claims = verify_token(token, self.settings, "refresh")

        self.assertEqual(claims["sub"], str(user_id))
        self.assertEqual(claims["sid"], str(session_id))
        with self.assertRaises(ValueError):
            verify_token(token, self.settings, "access")


if __name__ == "__main__":
    unittest.main()
