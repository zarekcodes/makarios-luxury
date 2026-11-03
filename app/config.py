from functools import lru_cache
from typing import Self

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_SECRET_KEY = "development-only-not-secret"

# 32 random bytes, the size `secrets.token_urlsafe(32)` makes, is far beyond
# guessing. Anything shorter is likely a placeholder typed by hand.
MIN_SECRET_KEY_LENGTH = 32

# A generated key is letters, digits and a few symbols, never spaces, quotes or
# brackets. Those mean something else was pasted in: a placeholder from the
# docs, or the command that generates a key instead of the key it prints.
NOT_IN_A_GENERATED_KEY = frozenset(" \t\n\"'<>()")


class Settings(BaseSettings):
    """App configuration, read from environment variables prefixed with MAKARIOS_ (or .env)."""

    # hide_input_in_errors: a settings error would otherwise print the values
    # it was given, the secret key among them, into the host's logs.
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="MAKARIOS_", hide_input_in_errors=True
    )

    app_name: str = "Makarios Luxury"
    environment: str = "development"
    debug: bool = False

    # SQLite in a file at the project root for development. Production sets a
    # Postgres URL here through MAKARIOS_DATABASE_URL.
    database_url: str = "sqlite:///makarios.db"

    @field_validator("database_url")
    @classmethod
    def use_the_psycopg_driver(cls, url: str) -> str:
        """Point a plain Postgres URL at psycopg 3.

        Hosts hand out `postgresql://...` URLs. SQLAlchemy reads that scheme
        as "Postgres through psycopg2", a driver this project doesn't install,
        so the scheme is rewritten to name psycopg 3 explicitly. Heroku-style
        `postgres://` gets the same treatment. Anything else passes unchanged.
        """
        scheme, separator, rest = url.partition("://")
        if separator and scheme in ("postgres", "postgresql"):
            return f"postgresql+psycopg://{rest}"
        return url

    # Signs the admin's session cookie, so it can't be forged or edited.
    # Production must set its own (see docs/DEPLOY.md); anyone who knows this
    # one could sign themselves in.
    secret_key: str = DEVELOPMENT_SECRET_KEY

    # How many proxies in front of the app add to X-Forwarded-For. It decides
    # which entry of that header is the visitor's address for the login throttle
    # (see client_address in app/admin.py).
    proxy_hops: int = Field(default=1, ge=1)

    # How buyers reach the business. Kept here rather than in the templates
    # because the email appears in several places: the footer, the contact
    # band, and every watch card's inquiry link.
    contact_email: str = "makarioslux@gmail.com"
    instagram_handle: str = "makariosluxury"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @model_validator(mode="after")
    def refuse_unsafe_production_settings(self) -> Self:
        """Fail at startup, rather than serve production with a development setting.

        Debug mode shows tracebacks, with code and local values, to whoever
        triggers an error. The development secret key is in this file, so
        anyone could sign an admin session with it.
        """
        if not self.is_production:
            return self
        if self.debug:
            raise ValueError("MAKARIOS_DEBUG must be off when MAKARIOS_ENVIRONMENT=production")
        key = self.secret_key
        if key == DEVELOPMENT_SECRET_KEY or len(key) < MIN_SECRET_KEY_LENGTH:
            raise ValueError(
                f"production needs its own MAKARIOS_SECRET_KEY of at least "
                f"{MIN_SECRET_KEY_LENGTH} characters"
            )
        if NOT_IN_A_GENERATED_KEY & set(key):
            raise ValueError(
                "MAKARIOS_SECRET_KEY looks like a command or placeholder, not a generated "
                "key: set it to what the command in docs/DEPLOY.md prints"
            )
        return self

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
