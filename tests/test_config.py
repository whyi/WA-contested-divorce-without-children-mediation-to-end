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

if __name__ == "__main__":
    unittest.main()
