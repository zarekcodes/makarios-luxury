"""Alembic's entry point: connects to the database and runs the migrations.

The URL comes from the app's settings unless the caller set one on the Config
object (the migration tests do, to point at a throwaway database).
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool

from app.config import get_settings
from app.db import create_db_engine
from app.models import Base

config = context.config

if config.config_file_name is not None:
    # Keep loggers that already exist, such as pytest's, working when the
    # migration tests run Alembic in-process.
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# Autogenerate compares the database against this: every model, because
# importing app.models registers each table on Base.metadata.
target_metadata = Base.metadata

url = config.get_main_option("sqlalchemy.url") or get_settings().database_url

# SQLite can't alter most things about an existing table. Batch mode works
# around that by copying the table, so the same migration runs on SQLite in
# development and on Postgres in production.
render_as_batch = url.startswith("sqlite")


def run_migrations_offline() -> None:
    """Write the migration SQL to stdout instead of running it (`alembic upgrade --sql`)."""
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=render_as_batch,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect to the database and run the migrations against it."""
    engine = create_db_engine(url, poolclass=pool.NullPool)

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=render_as_batch,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
