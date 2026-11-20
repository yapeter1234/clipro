"""Environment-backed Clipro API settings."""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    clipro_api_token_secret: str | None = None
    clipro_api_token_issuer: str = "clipro-web"
    clipro_api_token_audience: str = "clipro-api"
    database_url: str | None = None
    database_ssl: bool = True

    r2_account_id: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_bucket_name: str | None = None

    clipro_web_origins: str = "http://localhost:3000"
    clipro_modal_app_name: str = "clipro-workers"
    clipro_modal_probe_function: str = "probe_asset"
    clipro_modal_analysis_function: str = "analyze_asset"
    clipro_modal_dispatch_enabled: bool = False

    upload_max_file_size_bytes: int = Field(default=20 * 1024**3, ge=1, le=5 * 1024**4)
    upload_part_url_ttl_seconds: int = Field(default=900, ge=60, le=3600)
    upload_session_ttl_hours: int = Field(default=24, ge=1, le=168)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
