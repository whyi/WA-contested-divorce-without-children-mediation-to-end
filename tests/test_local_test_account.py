import unittest
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.auth import hash_password, verify_password
from app.config import Settings
from app.models import User
from deploy.local.seed_test_account import (
    TEST_EMAIL,
    ensure_test_account,
    validate_local_environment,
)


class LocalTestAccountTests(unittest.TestCase):
    def local_settings(self) -> Settings:
        return Settings(
            _env_file=None,
            database_url="postgresql+psycopg://postgres:postgres@local-test-db:5432/mediation",
            s3_endpoint_url="http://127.0.0.1:5000",
            s3_bucket="local-test-documents",
            deletion_ledger_bucket="local-test-deletion-ledger",
            auth_public_base_url="https://192.168.1.17:8444",
            auth_enabled=True,
            auth_jwt_secret="fictional-test-signing-secret-long-enough",
            case_data_enabled=True,
            case_materials_enabled=True,
        )

    def test_seeding_is_restricted_to_isolated_local_configuration(self) -> None:
        settings = self.local_settings()
        validate_local_environment(settings)
        for override in (
            {"database_url": "postgresql+psycopg://postgres:postgres@db:5432/mediation"},
            {"s3_bucket": "existing-documents"},
            {"auth_public_base_url": "https://deployed.example.com"},
            {"demo_mode_enabled": True},
            {"ai_analysis_enabled": True},
            {"smtp_host": "smtp.example.com"},
        ):
            with self.subTest(override=override):
                with self.assertRaisesRegex(ValueError, "isolated local-test"):
                    validate_local_environment(settings.model_copy(update=override))

    def test_new_account_is_verified_and_password_is_hashed(self) -> None:
        db = MagicMock(spec=Session)
        db.scalar.return_value = None
        password = "fictional-test-password-not-a-real-secret"
        ensure_test_account(db, password)
        user = db.add.call_args.args[0]
        self.assertEqual(user.email, TEST_EMAIL)
        self.assertEqual(user.status, "active")
        self.assertIsNotNone(user.email_verified_at)
        self.assertNotEqual(user.password_hash, password)
        self.assertTrue(verify_password(user.password_hash, password))
        db.flush.assert_called_once()

    def test_existing_account_is_preserved_and_mismatched_password_is_rejected(self) -> None:
        password = "fictional-test-password-not-a-real-secret"
        db = MagicMock(spec=Session)
        user = User(email=TEST_EMAIL, status="active", password_hash=hash_password(password))
        db.scalar.return_value = user
        ensure_test_account(db, password)
        db.add.assert_not_called()
        with self.assertRaisesRegex(ValueError, "not modified"):
            ensure_test_account(db, "another-fictional-test-password")
        self.assertTrue(verify_password(user.password_hash, password))
