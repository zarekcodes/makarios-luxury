from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# A later migration can only drop or change a constraint it can name. Left
# alone, SQLite and Postgres would each invent their own names, so these
# templates make every name predictable and the same on both.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """The base class of every model. Its metadata is the schema Alembic migrates."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
