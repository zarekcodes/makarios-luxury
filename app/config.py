from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, read from environment variables prefixed with MAKARIOS_ (or .env)."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="MAKARIOS_")

    app_name: str = "Makarios Luxury"
    environment: str = "development"
    debug: bool = False

    # How buyers reach the business. Kept here rather than in the templates
    # because the email appears in several places: the footer, the contact
    # band, and every watch card's inquiry link.
    contact_email: str = "makarioslux@gmail.com"
    instagram_handle: str = "makariosluxury"

    @property
    def instagram_url(self) -> str:
        return f"https://www.instagram.com/{self.instagram_handle}"

    @property
    def instagram_dm_url(self) -> str:
        """Opens a direct message thread in the Instagram app, or on the web."""
        return f"https://ig.me/m/{self.instagram_handle}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
