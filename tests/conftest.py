"""Shared fixtures: every test gets its own in-memory database.

In test-double terms the database is a fake: a real, working SQLite engine,
but in memory, private to one test, and gone when the test ends, standing in
for the file (and later Postgres) the app really uses. It is built straight
from the models, loaded with the placeholder watches, and swapped in for the
app's get_session dependency, so pages run real queries without touching
makarios.db.
"""

from collections.abc import Iterator

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import create_db_engine, get_session
from app.main import app
from app.models import Base
from app.seed import seed


@pytest.fixture
def session() -> Iterator[Session]:
    # An in-memory SQLite database lives only as long as its connection, so
    # StaticPool hands every checkout the same one. A second connection would
    # find an empty database.
    engine = create_db_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)

    with Session(engine, expire_on_commit=False) as session:
        seed(session)
        yield session

    engine.dispose()


@pytest.fixture(autouse=True)
def database(session: Session) -> Iterator[None]:
    """Point every request at the test's database, including the module-level clients."""
    app.dependency_overrides[get_session] = lambda: session
    yield
    app.dependency_overrides.clear()
