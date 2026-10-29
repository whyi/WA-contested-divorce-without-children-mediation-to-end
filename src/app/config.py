from functools import lru_cache
from urllib.parse import urlparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://mediation:mediation-dev-only@localhost:5432/mediation"
    s3_bucket: str = "mediation-documents"
    s3_region: str = "us-west-2"
    s3_endpoint_url: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    bedrock_model_id: str | None = None
    bedrock_region: str | None = None
    auth_enabled: bool = False
    case_data_enabled: bool = False
    demo_mode_enabled: bool = False
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
    webauthn_rp_id: str = "localhost"
    webauthn_rp_name: str = "Casework"
    webauthn_origin: str = "http://localhost:8000"
    auth_rate_limit_window_seconds: int = Field(default=60, gt=0)
    auth_rate_limit_attempts: int = Field(default=10, gt=0)
    max_upload_bytes: int = Field(default=20 * 1024 * 1024, gt=0)
    max_pdf_pages: int = Field(default=200, gt=0)
    conversion_timeout_seconds: int = Field(default=90, gt=0)

    @model_validator(mode="after")
    def validate_s3_credentials(self) -> "Settings":
        if bool(self.s3_access_key_id) != bool(self.s3_secret_access_key):
            raise ValueError("S3 access key and secret key must be configured together.")
        return self

    @model_validator(mode="after")
    def validate_auth_settings(self) -> "Settings":
        if self.auth_cookie_samesite not in {"lax", "strict", "none"}:
            raise ValueError("AUTH_COOKIE_SAMESITE must be lax, strict, or none.")
        if self.auth_cookie_samesite == "none" and not self.auth_cookie_secure:
            raise ValueError("AUTH_COOKIE_SECURE must be enabled when SameSite is none.")
        if bool(self.google_client_id) != bool(self.google_client_secret):
            raise ValueError("Google OIDC client ID and secret must be configured together.")
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
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
