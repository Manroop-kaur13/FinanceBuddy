"""Environment-backed application settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings loaded from environment variables or the local .env file."""

    database_url: str | None = None
    jwt_secret_key: str | None = None
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = 30
    cors_origins: str = "http://localhost:3000,https://finance-buddyai.vercel.app"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Create settings once so API requests share the same configuration."""
    return Settings()
