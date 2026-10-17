"""The database engine, and the session each request gets."""

from collections.abc import Iterator
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


def create_db_engine(url: str, **kwargs: Any) -> Engine:
    """Create an engine, with the two settings SQLite needs to behave here.

    - check_same_thread=False: FastAPI runs a plain `def` route and its
      dependencies on a thread pool, so a connection opened on one thread can
      be used on another. A session still serves one request at a time, so
      this is safe.
    - PRAGMA foreign_keys=ON: SQLite ignores foreign keys, and with them
      ON DELETE CASCADE, unless each connection switches them on. Postgres
      always enforces them.
    """
    if make_url(url).get_backend_name() != "sqlite":
        return create_engine(url, **kwargs)

    engine = create_engine(url, connect_args={"check_same_thread": False}, **kwargs)
    event.listen(engine, "connect", _enable_foreign_keys)
    return engine


def _enable_foreign_keys(dbapi_connection: Any, _connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


engine = create_db_engine(get_settings().database_url)

# expire_on_commit=False keeps a watch's attributes readable after a commit,
# instead of reloading each one from the database the next time it's read.
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """One session per request, closed once the request is handled."""
    with SessionLocal() as session:
        yield session


# Routes declare `session: SessionDep` to receive the request's session.
SessionDep = Annotated[Session, Depends(get_session)]
