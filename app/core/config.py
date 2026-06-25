from functools import lru_cache

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    The code reads from this object instead of calling `os.getenv` throughout
    the project. That keeps configuration discoverable, typed, and testable.
    """

    app_name: str = "Merxio"
    app_env: str = "local"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str = Field(
        default="postgresql+asyncpg://merxio:merxio@localhost:5432/merxio",
        repr=False,
    )
    database_echo: bool = False

    redis_url: str = "redis://localhost:6379/0"
    rabbitmq_url: str = Field(default="amqp://guest:guest@localhost:5672/", repr=False)

    jwt_secret_key: str = Field(default="change-me-in-production-use-at-least-32-bytes", repr=False)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    log_level: str = "INFO"
    cors_allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @computed_field
    @property
    def is_production(self) -> bool:
        """Convenience flag for production-only behavior."""
        return self.app_env.lower() == "production"

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_cors_allowed_origins(cls, value: str | list[str]) -> list[str]:
        """Allow `.env` files to use a simple comma-separated CORS list."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings object.

    Settings are immutable for the life of a running process in most backend
    services, so caching avoids reparsing `.env` on every import.
    """
    return Settings()


settings = get_settings()
