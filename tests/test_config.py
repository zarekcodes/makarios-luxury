"""Settings: the database URL Railway provides, and the production safety checks."""

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
        "postgresql://user:secret@db.railway.internal:5432/railway",
        "postgres://user:secret@db.railway.internal:5432/railway",
        "postgresql+psycopg://user:secret@db.railway.internal:5432/railway",
    ],
)
def test_a_postgres_url_uses_the_psycopg_driver(given: str) -> None:
    assert settings(database_url=given).database_url == (
        "postgresql+psycopg://user:secret@db.railway.internal:5432/railway"
    )


def test_a_sqlite_url_is_left_alone() -> None:
    assert settings(database_url="sqlite:///makarios.db").database_url == "sqlite:///makarios.db"


def test_production_refuses_debug_mode() -> None:
    with pytest.raises(ValidationError, match="MAKARIOS_DEBUG"):
        production_settings(debug=True)


@pytest.mark.parametrize("key", [DEVELOPMENT_SECRET_KEY, "too-short-to-be-random"])
def test_production_refuses_a_guessable_secret_key(key: str) -> None:
    """The key signs admin sessions, so a known or short one lets anyone sign themselves in."""
    with pytest.raises(ValidationError, match="MAKARIOS_SECRET_KEY"):
        production_settings(secret_key=key)


def test_production_accepts_its_own_secret_key() -> None:
    assert production_settings().is_production


def test_development_allows_debug_mode() -> None:
    assert settings(environment="development", debug=True).debug is True
