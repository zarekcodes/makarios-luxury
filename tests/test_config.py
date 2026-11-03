"""Settings: the database URL the host provides, and the production safety checks."""

import base64
import secrets

import pytest
from pydantic import ValidationError

from app.config import DEVELOPMENT_SECRET_KEY, Settings
from tests.conftest import production_settings


def settings(**values: object) -> Settings:
    """Settings from these values alone, ignoring the developer's .env file."""
    return Settings(_env_file=None, **values)


@pytest.mark.parametrize(
    "given",
    [
        "postgresql://user:secret@db.internal:5432/makarios",
        "postgres://user:secret@db.internal:5432/makarios",
        "postgresql+psycopg://user:secret@db.internal:5432/makarios",
    ],
)
def test_a_postgres_url_uses_the_psycopg_driver(given: str) -> None:
    assert settings(database_url=given).database_url == (
        "postgresql+psycopg://user:secret@db.internal:5432/makarios"
    )


def test_a_sqlite_url_is_left_alone() -> None:
    assert settings(database_url="sqlite:///makarios.db").database_url == "sqlite:///makarios.db"


def test_production_refuses_debug_mode() -> None:
    with pytest.raises(ValidationError, match="MAKARIOS_DEBUG"):
        production_settings(debug=True)


@pytest.mark.parametrize(
    "key",
    [
        DEVELOPMENT_SECRET_KEY,
        "too-short-to-be-random",
        # The command itself, pasted in place of what it prints. Long enough
        # to pass the length check, and printed in the docs for anyone to read.
        'python3 -c "import secrets; print(secrets.token_urlsafe(32))"',
        '<python3 -c "import secrets; print(secrets.token_urlsafe(32))">',
    ],
)
def test_production_refuses_a_guessable_secret_key(key: str) -> None:
    """The key signs admin sessions, so a known or short one lets anyone sign themselves in."""
    with pytest.raises(ValidationError, match="MAKARIOS_SECRET_KEY"):
        production_settings(secret_key=key)


def test_production_accepts_its_own_secret_key() -> None:
    assert production_settings().is_production


@pytest.mark.parametrize(
    "key",
    [
        secrets.token_urlsafe(32),  # what docs/DEPLOY.md generates
        base64.b64encode(secrets.token_bytes(32)).decode(),  # base64, as other hosts generate
    ],
)
def test_production_accepts_generated_keys(key: str) -> None:
    assert production_settings(secret_key=key).secret_key == key


def test_a_settings_error_does_not_print_the_secret_key() -> None:
    """The error lands in the host's logs, so it must not echo the values it was given."""
    key = secrets.token_urlsafe(32)

    with pytest.raises(ValidationError) as error:
        production_settings(secret_key=key, debug=True)

    assert key[-12:] not in str(error.value)


def test_development_allows_debug_mode() -> None:
    assert settings(environment="development", debug=True).debug is True
