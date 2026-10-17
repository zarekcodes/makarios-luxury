"""The migrations must build exactly the schema the models describe.

Every other test builds its database straight from the models, so a model
change whose migration was never generated passes them all, then fails on the
real database. These tests run the migrations themselves and compare.
"""

from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import inspect

from app.db import create_db_engine
from app.models import Base

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


def alembic_config(url: str) -> Config:
    config = Config(ALEMBIC_INI)
    config.set_main_option("sqlalchemy.url", url)
    return config


def test_migrations_build_the_schema_the_models_describe(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'migrated.db'}"
    command.upgrade(alembic_config(url), "head")

    engine = create_db_engine(url)
    with engine.connect() as connection:
        differences = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    engine.dispose()

    assert differences == [], "the models changed without a migration: run alembic revision"


def test_migrations_downgrade_to_an_empty_database(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'migrated.db'}"
    config = alembic_config(url)
    command.upgrade(config, "head")
    command.downgrade(config, "base")

    engine = create_db_engine(url)
    tables = set(inspect(engine).get_table_names())
    engine.dispose()

    assert tables == {"alembic_version"}
