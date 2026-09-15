from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, read from environment variables prefixed with MAKARIOS_ (or .env)."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="MAKARIOS_")

    app_name: str = "Makarios Luxury"
    environment: str = "development"
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
