from functools import lru_cache

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
    max_upload_bytes: int = Field(default=20 * 1024 * 1024, gt=0)
    max_pdf_pages: int = Field(default=200, gt=0)
    conversion_timeout_seconds: int = Field(default=90, gt=0)

    @model_validator(mode="after")
    def validate_s3_credentials(self) -> "Settings":
        if bool(self.s3_access_key_id) != bool(self.s3_secret_access_key):
            raise ValueError("S3 access key and secret key must be configured together.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
