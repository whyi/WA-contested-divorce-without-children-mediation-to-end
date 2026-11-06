import unittest

from app.config import Settings


class SettingsTests(unittest.TestCase):
    def test_bedrock_configuration_is_optional(self) -> None:
        settings = Settings()

        self.assertIsNone(settings.bedrock_model_id)
        self.assertIsNone(settings.bedrock_region)

    def test_bedrock_model_and_region_can_be_configured(self) -> None:
        settings = Settings(
            bedrock_model_id="us.amazon.nova-lite-v1:0",
            bedrock_region="us-west-2",
        )

        self.assertEqual(settings.bedrock_model_id, "us.amazon.nova-lite-v1:0")
        self.assertEqual(settings.bedrock_region, "us-west-2")

    def test_support_contact_must_be_https_without_embedded_data(self) -> None:
        settings = Settings(support_contact_url="https://support.example.test/help")
        self.assertEqual(settings.support_contact_url, "https://support.example.test/help")

        for invalid_url in (
            "http://support.example.test/help",
            "https://user:password@support.example.test/help",
            "https://support.example.test/help?token=secret",
            "https://support.example.test/help#case",
        ):
            with self.subTest(invalid_url=invalid_url):
                with self.assertRaisesRegex(ValueError, "SUPPORT_CONTACT_URL"):
                    Settings(support_contact_url=invalid_url)

    def test_authentication_is_disabled_without_explicit_secrets(self) -> None:
        settings = Settings(
            auth_enabled=False,
            case_data_enabled=False,
            demo_mode_enabled=False,
            auth_jwt_secret=None,
        )

        self.assertIsNone(settings.auth_jwt_secret)
        self.assertFalse(settings.auth_enabled)
        self.assertFalse(settings.case_data_enabled)
        self.assertIsNone(settings.auth_encryption_key)
        self.assertIsNone(settings.google_client_id)
        self.assertIsNone(settings.smtp_host)

    def test_authentication_configuration_rejects_mismatched_provider_secrets(self) -> None:
        with self.assertRaisesRegex(ValueError, "configured together"):
            Settings(google_client_id="client-id")
        with self.assertRaisesRegex(ValueError, "configured together"):
            Settings(dropbox_app_key="app-key")

    def test_authentication_configuration_rejects_invalid_session_lifetimes(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot exceed"):
            Settings(auth_idle_session_days=31)

    def test_samesite_none_requires_secure_cookies(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be enabled"):
            Settings(auth_cookie_samesite="none", auth_cookie_secure=False)

    def test_auth_cannot_be_enabled_without_a_strong_secret(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 32 bytes"):
            Settings(auth_enabled=True, auth_jwt_secret=None, demo_mode_enabled=False)

    def test_non_local_auth_origins_require_https(self) -> None:
        with self.assertRaisesRegex(ValueError, "must use HTTPS"):
            Settings(
                auth_enabled=True,
                auth_jwt_secret="a-secure-test-signing-secret-that-is-long-enough",
                auth_public_base_url="http://app.example.test",
            )

    def test_case_data_cannot_be_enabled_without_authentication(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires AUTH_ENABLED"):
            Settings(
                auth_enabled=False,
                case_data_enabled=True,
                demo_mode_enabled=False,
            )

    def test_demo_mode_is_local_only_and_cannot_enable_case_data(self) -> None:
        auth_options = {
            "auth_enabled": True,
            "auth_jwt_secret": "local-demo-signing-key-that-is-long-enough",
            "demo_mode_enabled": True,
        }
        self.assertTrue(Settings(**auth_options).demo_mode_enabled)

        with self.assertRaisesRegex(ValueError, "restricted to localhost"):
            Settings(**auth_options, auth_public_base_url="https://app.example.test")
        with self.assertRaisesRegex(ValueError, "cannot enable case-data"):
            Settings(**auth_options, case_data_enabled=True)

    def test_remote_http_s3_endpoint_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "must use HTTPS"):
            Settings(s3_endpoint_url="http://objects.example.test")

    def test_s3_endpoint_cannot_embed_credentials(self) -> None:
        with self.assertRaisesRegex(ValueError, "without embedded credentials"):
            Settings(s3_endpoint_url="https://user:password@objects.example.test")

    def test_case_materials_require_auth_and_case_data(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires AUTH_ENABLED and CASE_DATA_ENABLED"):
            Settings(case_materials_enabled=True)

    def test_production_case_materials_require_a_kms_key(self) -> None:
        with self.assertRaisesRegex(ValueError, "S3_KMS_KEY_ID"):
            Settings(
                auth_enabled=True,
                auth_jwt_secret="secure-test-signing-secret-that-is-long-enough",
                case_data_enabled=True,
                case_materials_enabled=True,
                demo_mode_enabled=False,
            )

    def test_local_loopback_storage_can_be_explicitly_enabled_without_kms(self) -> None:
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="secure-test-signing-secret-that-is-long-enough",
            case_data_enabled=True,
            case_materials_enabled=True,
            demo_mode_enabled=False,
            s3_endpoint_url="http://localhost:5000",
        )

        self.assertTrue(settings.case_materials_enabled)

    def test_production_case_data_requires_kms_even_before_materials_toggle(self) -> None:
        with self.assertRaisesRegex(ValueError, "before production case-data access"):
            Settings(
                auth_enabled=True,
                auth_jwt_secret="secure-test-signing-secret-that-is-long-enough",
                case_data_enabled=True,
                demo_mode_enabled=False,
            )

    def test_production_readiness_is_opt_in_and_reports_only_safe_check_codes(self) -> None:
        self.assertEqual(Settings().production_readiness_errors(), ())

        errors = Settings(production_readiness_required=True).production_readiness_errors()

        self.assertIn("authentication_disabled", errors)
        self.assertIn("case_data_disabled", errors)
        self.assertIn("case_material_storage_disabled", errors)
        self.assertIn("live_payment_configuration_incomplete", errors)
        self.assertIn("qualified_counsel_review_evidence_missing", errors)
        self.assertIn("backup_restore_tombstone_reconciliation_unverified", errors)
        self.assertIn("production_alert_delivery_unverified", errors)
        self.assertNotIn("AUTH_JWT_SECRET", " ".join(errors))

    def test_production_readiness_requires_tls_and_live_payment_configuration(self) -> None:
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="secure-test-signing-secret-that-is-long-enough",
            auth_encryption_key="secure-encryption-secret-that-is-long-enough",
            auth_issuer="https://auth.example.test",
            auth_public_base_url="https://app.example.test",
            webauthn_origin="https://app.example.test",
            case_data_enabled=True,
            case_materials_enabled=True,
            demo_mode_enabled=False,
            production_readiness_required=True,
            s3_kms_key_id="arn:aws:kms:us-west-2:123:key/test",
            database_url="postgresql+psycopg://user:password@db.example.test/mediation",
            support_contact_url="https://support.example.test/help",
            stripe_secret_key="sk_test_example",
            stripe_webhook_secret="whsec_example",
            stripe_price_id_attempt_credits_5="price_five",
            stripe_price_id_attempt_credits_10="price_ten",
        )

        errors = settings.production_readiness_errors()

        self.assertNotIn("auth_signing_secret_missing_or_weak", errors)
        self.assertNotIn("case_data_disabled", errors)
        self.assertNotIn("case_material_storage_disabled", errors)
        self.assertIn("database_tls_not_required", errors)
        self.assertIn("live_payment_configuration_incomplete", errors)
        self.assertIn("backup_restore_tombstone_reconciliation_unverified", errors)

    def test_production_readiness_requires_separate_counsel_and_provider_evidence_for_ai(self) -> None:
        settings = Settings(
            production_readiness_required=True,
            ai_analysis_enabled=True,
        )

        errors = settings.production_readiness_errors()
        self.assertIn("qualified_counsel_review_evidence_missing", errors)
        self.assertIn("ai_qualified_counsel_review_evidence_missing", errors)
        self.assertIn("ai_provider_review_evidence_missing", errors)

        provider_only = Settings(
            production_readiness_required=True,
            ai_analysis_enabled=True,
            ai_provider_review_evidence_verified=True,
        )
        self.assertIn(
            "qualified_counsel_review_evidence_missing",
            provider_only.production_readiness_errors(),
        )
        self.assertIn(
            "ai_qualified_counsel_review_evidence_missing",
            provider_only.production_readiness_errors(),
        )
        self.assertNotIn(
            "ai_provider_review_evidence_missing",
            provider_only.production_readiness_errors(),
        )

        counsel_only = Settings(
            production_readiness_required=True,
            ai_analysis_enabled=True,
            counsel_review_evidence_verified=True,
        )
        self.assertNotIn(
            "qualified_counsel_review_evidence_missing",
            counsel_only.production_readiness_errors(),
        )
        self.assertNotIn(
            "ai_qualified_counsel_review_evidence_missing",
            counsel_only.production_readiness_errors(),
        )
        self.assertIn(
            "ai_provider_review_evidence_missing",
            counsel_only.production_readiness_errors(),
        )

    def test_complete_configuration_does_not_clear_unverified_operational_evidence(self) -> None:
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="secure-test-signing-secret-that-is-long-enough",
            auth_encryption_key="secure-encryption-secret-that-is-long-enough",
            auth_issuer="https://auth.example.test",
            auth_public_base_url="https://app.example.test",
            webauthn_origin="https://app.example.test",
            case_data_enabled=True,
            case_materials_enabled=True,
            demo_mode_enabled=False,
            production_readiness_required=True,
            s3_kms_key_id="arn:aws:kms:us-west-2:123:key/test",
            database_url=(
                "postgresql+psycopg://user:password@db.example.test/mediation"
                "?sslmode=verify-full"
            ),
            support_contact_url="https://support.example.test/help",
            stripe_secret_key="sk_live_example",
            stripe_webhook_secret="whsec_example",
            stripe_price_id_attempt_credits_5="price_five",
            stripe_price_id_attempt_credits_10="price_ten",
            counsel_review_evidence_verified=True,
        )

        errors = settings.production_readiness_errors()

        self.assertEqual(
            set(errors),
            {
                "backup_restore_tombstone_reconciliation_unverified",
                "production_alert_delivery_unverified",
                "payment_provider_test_evidence_unverified",
            },
        )

    def test_counsel_review_evidence_flag_defaults_closed_and_clears_only_its_gate(self) -> None:
        settings = Settings(production_readiness_required=True)
        self.assertFalse(settings.counsel_review_evidence_verified)
        self.assertIn(
            "qualified_counsel_review_evidence_missing",
            settings.production_readiness_errors(),
        )
        reviewed = Settings(
            production_readiness_required=True,
            counsel_review_evidence_verified=True,
        )
        self.assertNotIn(
            "qualified_counsel_review_evidence_missing",
            reviewed.production_readiness_errors(),
        )

    def test_ai_provider_evidence_flag_defaults_closed_and_clears_only_provider_gate(self) -> None:
        settings = Settings(
            production_readiness_required=True,
            ai_analysis_enabled=True,
        )
        self.assertFalse(settings.ai_provider_review_evidence_verified)
        self.assertIn("ai_provider_review_evidence_missing", settings.production_readiness_errors())

        provider_reviewed = Settings(
            production_readiness_required=True,
            ai_analysis_enabled=True,
            ai_provider_review_evidence_verified=True,
        )
        errors = provider_reviewed.production_readiness_errors()
        self.assertNotIn("ai_provider_review_evidence_missing", errors)
        self.assertIn("qualified_counsel_review_evidence_missing", errors)


if __name__ == "__main__":
    unittest.main()
