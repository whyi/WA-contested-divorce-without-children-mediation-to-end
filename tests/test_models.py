import unittest

from app.models import (
    AuthAuditEvent,
    AuthChallenge,
    AuthRateLimit,
    AuthSession,
    AuthToken,
    CaseMembership,
    ExternalIdentity,
    MaterialImportBatch,
    MaterialImportItem,
    PasskeyCredential,
    RecoveryCode,
    RefreshToken,
    TotpCredential,
    User,
)


class AuthenticationModelTests(unittest.TestCase):
    def test_authentication_tables_are_registered(self) -> None:
        expected = {
            "users",
            "external_identities",
            "auth_sessions",
            "refresh_tokens",
            "auth_tokens",
            "totp_credentials",
            "passkey_credentials",
            "auth_challenges",
            "recovery_codes",
            "auth_rate_limits",
            "auth_audit_events",
            "case_memberships",
            "material_import_batches",
            "material_import_items",
        }
        actual = {
            model.__tablename__
            for model in (
                User,
                ExternalIdentity,
                AuthSession,
                RefreshToken,
                AuthToken,
                TotpCredential,
                PasskeyCredential,
                AuthChallenge,
                RecoveryCode,
                AuthAuditEvent,
                AuthRateLimit,
                CaseMembership,
                MaterialImportBatch,
                MaterialImportItem,
            )
        }

        self.assertEqual(actual, expected)

    def test_provider_and_case_access_constraints_are_explicit(self) -> None:
        self.assertIn(
            "uq_external_identity_provider_subject",
            {constraint.name for constraint in ExternalIdentity.__table__.constraints},
        )
        self.assertIn(
            "uq_case_membership_user_case",
            {constraint.name for constraint in CaseMembership.__table__.constraints},
        )
        self.assertIn("public_key", PasskeyCredential.__table__.columns)
        self.assertNotIn("private_key", PasskeyCredential.__table__.columns)


if __name__ == "__main__":
    unittest.main()
