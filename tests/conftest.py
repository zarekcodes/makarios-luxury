"""Shared fixtures: every test gets its own database.

In test-double terms the database is a fake: a real, working SQLite engine,
but in memory, private to one test, and gone when the test ends, standing in
for the Postgres the app really uses in production. It is built straight from
the models, loaded with the placeholder watches, and swapped in for the app's
get_session dependency, so pages run real queries without touching
makarios.db.

Set MAKARIOS_TEST_DATABASE_URL to a Postgres URL to run the same suite against
Postgres instead (see docs/DEPLOY.md). Each test then drops and recreates the
tables, so tests still can't see each other's rows. Nothing else in the
database is safe either: point it at a throwaway database only.
"""

import os
from collections.abc import Iterator

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.db import create_db_engine, get_session
from app.main import app
from app.models import Base
from app.seed import seed

# None runs the suite on in-memory SQLite.
TEST_DATABASE_URL = os.environ.get("MAKARIOS_TEST_DATABASE_URL")


def production_settings(**overrides: object) -> Settings:
    """Settings that pass the production checks, ignoring the developer's .env file."""
    values: dict[str, object] = {"environment": "production", "secret_key": "s" * 32}
    return Settings(_env_file=None, **(values | overrides))


@pytest.fixture
def engine() -> Iterator[Engine]:
    if TEST_DATABASE_URL:
        engine = create_db_engine(TEST_DATABASE_URL)
        Base.metadata.drop_all(engine)
    else:
        # An in-memory SQLite database lives only as long as its connection,
        # so StaticPool hands every checkout the same one. A second connection
        # would find an empty database.
        engine = create_db_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)

    yield engine

    engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    with Session(engine, expire_on_commit=False) as session:
        seed(session)
        yield session


@pytest.fixture(autouse=True)
def database(session: Session) -> Iterator[None]:
    """Point every request at the test's database, including the module-level clients."""
    app.dependency_overrides[get_session] = lambda: session
    yield
    app.dependency_overrides.clear()
