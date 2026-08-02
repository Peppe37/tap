"""Application configuration, loaded from environment variables / .env."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = Field(default="development", alias="TAP_ENVIRONMENT")

    database_url: str = Field(
        default="postgresql+asyncpg://tap:tap@localhost:5432/tap",
        alias="TAP_DATABASE_URL",
    )

    redis_url: str = Field(default="redis://localhost:6379/0", alias="TAP_REDIS_URL")

    # Secret used to sign JWT access/refresh tokens. Must be overridden in production.
    jwt_secret_key: str = Field(alias="TAP_JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="TAP_JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="TAP_ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=30, alias="TAP_REFRESH_TOKEN_EXPIRE_DAYS")

    # Fernet key (32 url-safe base64 bytes) used to encrypt stored provider credentials.
    credential_encryption_key: str = Field(alias="TAP_CREDENTIAL_ENCRYPTION_KEY")

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"], alias="TAP_CORS_ORIGINS"
    )

    # Provider-specific defaults, overridable per-deployment via env.
    aggregator_base_url: str = Field(
        default="https://api.17track.net/track/v2.4", alias="TAP_AGGREGATOR_BASE_URL"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
