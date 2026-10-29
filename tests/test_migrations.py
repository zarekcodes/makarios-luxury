"""The migrations must build exactly the schema the models describe.

Every other test builds its database straight from the models, so a model
change whose migration was never generated passes them all, then fails on the
real database. These tests run the migrations themselves and compare.

They run on a fresh SQLite file, and on Postgres too when
MAKARIOS_TEST_DATABASE_URL is set, since production migrates Postgres and the
two databases disagree on details such as defaults and constraint types.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import MetaData, inspect

from app.db import create_db_engine
from app.models import Base
from tests.conftest import TEST_DATABASE_URL

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"

DATABASES = ["sqlite"] + (["postgres"] if TEST_DATABASE_URL else [])


def alembic_config(url: str) -> Config:
    config = Config(ALEMBIC_INI)
    config.set_main_option("sqlalchemy.url", url)
    return config


def drop_everything(url: str) -> None:
    """Empty the database, including alembic_version, which the models don't know about."""
    engine = create_db_engine(url)
    metadata = MetaData()
    metadata.reflect(engine)
    metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(params=DATABASES)
def empty_database_url(request: pytest.FixtureRequest, tmp_path: Path) -> Iterator[str]:
    """The URL of an empty database, for the migrations to build from nothing."""
    if request.param == "sqlite":
        yield f"sqlite:///{tmp_path / 'migrated.db'}"
        return

    assert TEST_DATABASE_URL
    drop_everything(TEST_DATABASE_URL)
    yield TEST_DATABASE_URL
    drop_everything(TEST_DATABASE_URL)


def test_migrations_build_the_schema_the_models_describe(empty_database_url: str) -> None:
    command.upgrade(alembic_config(empty_database_url), "head")

    engine = create_db_engine(empty_database_url)
    with engine.connect() as connection:
        differences = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    engine.dispose()

    assert differences == [], "the models changed without a migration: run alembic revision"


def test_migrations_downgrade_to_an_empty_database(empty_database_url: str) -> None:
    config = alembic_config(empty_database_url)
    command.upgrade(config, "head")
    command.downgrade(config, "base")

    engine = create_db_engine(empty_database_url)
    tables = set(inspect(engine).get_table_names())
    engine.dispose()

    assert tables == {"alembic_version"}
