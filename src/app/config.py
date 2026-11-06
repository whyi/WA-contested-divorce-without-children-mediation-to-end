from functools import lru_cache
from urllib.parse import parse_qs, urlparse

from pydantic import EmailStr, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROVIDER_HANDLING_LIMITATION = (
    "Provider-managed retention, human access or review, product improvement, generalized "
    "model training, subprocessors, and deletion behavior are not independently verified by "
    "this application. Consult the deployment-specific notice for reviewed provider details."
)


def provider_data_handling_notice(configured_notice: str | None) -> str | None:
    if not configured_notice or not configured_notice.strip():
        return None
    return f"{configured_notice.strip()}\n\n{PROVIDER_HANDLING_LIMITATION}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://mediation:mediation-dev-only@localhost:5432/mediation"
    s3_bucket: str = "mediation-documents"
    deletion_ledger_bucket: str = "mediation-deletion-ledger"
    s3_region: str = "us-west-2"
    s3_endpoint_url: str | None = None
    s3_kms_key_id: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    bedrock_model_id: str | None = None
    bedrock_region: str | None = None
    ai_analysis_enabled: bool = False
    ai_provider_review_evidence_verified: bool = False
    ai_analysis_notice_version: str | None = None
    ai_analysis_data_handling_notice: str | None = None
    settlement_planning_data_handling_notice: str | None = None
    support_contact_url: str | None = None
    auth_enabled: bool = False
    case_data_enabled: bool = False
    case_materials_enabled: bool = False
    demo_mode_enabled: bool = False
    owner_beta_enabled: bool = False
    owner_beta_email: EmailStr | None = None
    production_readiness_required: bool = False
    counsel_review_evidence_verified: bool = False
    auth_jwt_secret: str | None = None
    auth_issuer: str = "http://localhost:8000"
    auth_audience: str = "casework"
    auth_access_token_minutes: int = Field(default=10, gt=0)
    auth_refresh_token_days: int = Field(default=30, gt=0)
    auth_idle_session_days: int = Field(default=7, gt=0)
    auth_absolute_session_days: int = Field(default=30, gt=0)
    auth_max_active_sessions: int = Field(default=5, gt=0)
    auth_cookie_secure: bool = True
    auth_cookie_samesite: str = "lax"
    auth_encryption_key: str | None = None
    auth_public_base_url: str = "http://localhost:8000"
    auth_email_from: str | None = None
    smtp_host: str | None = None
    smtp_port: int = Field(default=587, gt=0, le=65535)
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_starttls: bool = True
    google_client_id: str | None = None
    google_client_secret: str | None = None
    dropbox_app_key: str | None = None
    dropbox_app_secret: str | None = None
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_price_id_attempt_credits_5: str | None = None
    stripe_price_id_attempt_credits_10: str | None = None
    webauthn_rp_id: str = "localhost"
    webauthn_rp_name: str = "Casework"
    webauthn_origin: str = "http://localhost:8000"
    auth_rate_limit_window_seconds: int = Field(default=60, gt=0)
    auth_rate_limit_attempts: int = Field(default=10, gt=0)
    max_upload_bytes: int = Field(default=2 * 1024 * 1024, gt=0)
    max_pdf_pages: int = Field(default=200, gt=0)
    conversion_timeout_seconds: int = Field(default=90, gt=0)

    @model_validator(mode="after")
    def validate_s3_credentials(self) -> "Settings":
        if self.deletion_ledger_bucket == self.s3_bucket:
            raise ValueError("DELETION_LEDGER_BUCKET must differ from S3_BUCKET.")
        if bool(self.s3_access_key_id) != bool(self.s3_secret_access_key):
            raise ValueError("S3 access key and secret key must be configured together.")
        if self.s3_endpoint_url:
            parsed = urlparse(self.s3_endpoint_url)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or parsed.username
                or parsed.password
            ):
                raise ValueError("S3_ENDPOINT_URL must be an HTTP(S) URL without embedded credentials.")
            is_local = parsed.hostname.lower() in {"localhost", "127.0.0.1", "::1"}
            is_compose_mock = self.demo_mode_enabled and parsed.hostname.lower() == "s3mock"
            if parsed.scheme != "https" and not (is_local or is_compose_mock):
                raise ValueError("S3_ENDPOINT_URL must use HTTPS outside loopback development.")
        return self

    @model_validator(mode="after")
    def validate_support_contact_url(self) -> "Settings":
        if self.support_contact_url:
            parsed = urlparse(self.support_contact_url)
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError(
                    "SUPPORT_CONTACT_URL must be an HTTPS URL without credentials, query, or fragment."
                )
        return self

    @model_validator(mode="after")
    def validate_auth_settings(self) -> "Settings":
        if self.auth_cookie_samesite not in {"lax", "strict", "none"}:
            raise ValueError("AUTH_COOKIE_SAMESITE must be lax, strict, or none.")
        if self.auth_cookie_samesite == "none" and not self.auth_cookie_secure:
            raise ValueError("AUTH_COOKIE_SECURE must be enabled when SameSite is none.")
        if bool(self.google_client_id) != bool(self.google_client_secret):
            raise ValueError("Google OIDC client ID and secret must be configured together.")
        if bool(self.dropbox_app_key) != bool(self.dropbox_app_secret):
            raise ValueError("Dropbox app key and secret must be configured together.")
        if bool(self.smtp_username) != bool(self.smtp_password):
            raise ValueError("SMTP username and password must be configured together.")
        if self.auth_idle_session_days > self.auth_absolute_session_days:
            raise ValueError("Idle session lifetime cannot exceed absolute lifetime.")
        if self.auth_enabled:
            if not self.auth_jwt_secret or len(self.auth_jwt_secret.encode()) < 32:
                raise ValueError("AUTH_JWT_SECRET must contain at least 32 bytes when auth is enabled.")
            if not self.auth_cookie_secure:
                raise ValueError("AUTH_COOKIE_SECURE must be enabled when auth is enabled.")
            for name, value in (
                ("AUTH_ISSUER", self.auth_issuer),
                ("AUTH_PUBLIC_BASE_URL", self.auth_public_base_url),
                ("WEBAUTHN_ORIGIN", self.webauthn_origin),
            ):
                parsed = urlparse(value)
                is_local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
                if parsed.scheme != "https" and not (
                    is_local and parsed.scheme == "http"
                ):
                    raise ValueError(f"{name} must use HTTPS outside localhost.")
        if self.case_data_enabled and not self.auth_enabled:
            raise ValueError("CASE_DATA_ENABLED requires AUTH_ENABLED.")
        if (
            self.case_data_enabled
            and not self.demo_mode_enabled
            and not self._uses_local_s3_endpoint()
            and not (self.s3_kms_key_id or "").strip()
        ):
            raise ValueError(
                "S3_KMS_KEY_ID must be configured before production case-data access is enabled."
            )
        if self.case_materials_enabled:
            if not self.auth_enabled or not self.case_data_enabled:
                raise ValueError(
                    "CASE_MATERIALS_ENABLED requires AUTH_ENABLED and CASE_DATA_ENABLED."
                )
            if self.demo_mode_enabled:
                raise ValueError("Case-material storage cannot be enabled in demo mode.")
            if not self._uses_local_s3_endpoint() and not (self.s3_kms_key_id or "").strip():
                raise ValueError(
                    "S3_KMS_KEY_ID must be configured before case-material storage is enabled."
                )
        if self.demo_mode_enabled:
            if not self.auth_enabled:
                raise ValueError("DEMO_MODE_ENABLED requires AUTH_ENABLED.")
            if urlparse(self.auth_public_base_url).hostname not in {
                "localhost",
                "127.0.0.1",
                "::1",
            }:
                raise ValueError("DEMO_MODE_ENABLED is restricted to localhost.")
            if self.case_data_enabled:
                raise ValueError("Demo mode cannot enable case-data APIs.")
        if self.owner_beta_enabled:
            if not self.auth_enabled:
                raise ValueError("OWNER_BETA_ENABLED requires AUTH_ENABLED.")
            if self.demo_mode_enabled:
                raise ValueError("OWNER_BETA_ENABLED cannot be used with DEMO_MODE_ENABLED.")
            if self.owner_beta_email is None:
                raise ValueError("OWNER_BETA_EMAIL is required when OWNER_BETA_ENABLED is true.")
        return self

    def _uses_local_s3_endpoint(self) -> bool:
        if not self.s3_endpoint_url:
            return False
        endpoint = urlparse(self.s3_endpoint_url)
        return (
            endpoint.scheme == "http"
            and endpoint.hostname is not None
            and (
                endpoint.hostname.lower() in {"localhost", "127.0.0.1", "::1"}
                or (self.demo_mode_enabled and endpoint.hostname.lower() == "s3mock")
            )
        )

    def production_readiness_errors(self) -> tuple[str, ...]:
        if not self.production_readiness_required:
            return ()

        errors: list[str] = []
        if self.demo_mode_enabled:
            errors.append("demo_mode_enabled")
        if not self.auth_enabled:
            errors.append("authentication_disabled")
        if not self.auth_jwt_secret or len(self.auth_jwt_secret.encode()) < 32:
            errors.append("auth_signing_secret_missing_or_weak")
        if not self.auth_cookie_secure:
            errors.append("secure_auth_cookies_disabled")
        if not self.auth_encryption_key or len(self.auth_encryption_key.encode()) < 32:
            errors.append("auth_encryption_key_missing_or_weak")
        if not self.case_data_enabled:
            errors.append("case_data_disabled")
        if not self.case_materials_enabled:
            errors.append("case_material_storage_disabled")
        if not (self.s3_kms_key_id or "").strip():
            errors.append("s3_kms_key_missing")
        if self._uses_local_s3_endpoint():
            errors.append("local_object_storage_endpoint_configured")
        if not self.support_contact_url:
            errors.append("support_contact_url_missing")
        if not self.counsel_review_evidence_verified:
            errors.append("qualified_counsel_review_evidence_missing")

        parsed_database_url = urlparse(self.database_url)
        if parsed_database_url.scheme not in {"postgresql", "postgresql+psycopg"}:
            errors.append("postgresql_database_required")
        database_sslmode = parse_qs(parsed_database_url.query).get("sslmode", [""])[0]
        if database_sslmode not in {"require", "verify-ca", "verify-full"}:
            errors.append("database_tls_not_required")

        if not (
            (self.stripe_secret_key or "").startswith("sk_live_")
            and (self.stripe_webhook_secret or "").startswith("whsec_")
            and (self.stripe_price_id_attempt_credits_5 or "").startswith("price_")
            and (self.stripe_price_id_attempt_credits_10 or "").startswith("price_")
        ):
            errors.append("live_payment_configuration_incomplete")
        if self.ai_analysis_enabled:
            if not self.counsel_review_evidence_verified:
                errors.append("ai_qualified_counsel_review_evidence_missing")
            if not self.ai_provider_review_evidence_verified:
                errors.append("ai_provider_review_evidence_missing")

        # Restore reconciliation exists, but production ledger controls and a real
        # restore exercise require operator evidence not represented by settings.
        errors.append("backup_restore_tombstone_reconciliation_unverified")
        # No monitoring provider, alert route, or alert-delivery test is configured here.
        errors.append("production_alert_delivery_unverified")
        # Stripe credentials/configuration do not prove the required provider test scenarios.
        errors.append("payment_provider_test_evidence_unverified")

        return tuple(errors)

    def production_ai_readiness_passed(self) -> bool:
        return (
            not self.production_readiness_required
            or not self.production_readiness_errors()
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
