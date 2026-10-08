from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="KDH Marketing Dashboard")
    app_env: Literal["development", "test", "production"] = "development"
    debug: bool = False
    database_url: str = "postgresql://postgres:postgres@localhost:5432/kdh_report"
        # =====================================================
    # KDH REPORT ADMIN - INTERNAL REPORT API
    # =====================================================

    report_admin_base_url: str = (
        "http://127.0.0.1:8090"
    )

    report_service_token: SecretStr = SecretStr("")

    report_request_timeout_seconds: float = Field(
        default=5.0,
        gt=0,
        le=30,
    )
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
