"""Functional and non-functional tests for one feature: the featured watches on the home page.

The functional test checks what the page does: a featured watch in the
database shows up on GET / with its name, reference and price. The
non-functional test checks how well it does it: how fast the server builds
the page.
"""

import statistics
import time
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import BoxPapers, Condition, Photo, Watch

client = TestClient(app)

REQUESTS = 50
P95_BUDGET_MS = 100


def test_a_featured_watch_appears_on_the_home_page(session: Session) -> None:
    """Valid input: a featured, available watch, listed newest, so it makes the grid."""
    session.add(
        Watch(
            slug="omega-speedmaster-professional",
            brand="Omega",
            model="Speedmaster Professional",
            reference="310.30.42.50.01.001",
            year=2023,
            condition=Condition.EXCELLENT,
            price=18750,
            box_papers=BoxPapers.BOX_AND_PAPERS,
            featured=True,
            listed_at=datetime(2026, 11, 20, tzinfo=UTC),
            photos=[Photo(image="placeholder/watch-01", alt="An Omega Speedmaster.")],
        )
    )
    session.commit()

    response = client.get("/")

    assert response.status_code == 200
    assert "Omega Speedmaster Professional" in response.text
    assert "310.30.42.50.01.001" in response.text
    assert "$18,750" in response.text


# NFR (performance): across 50 sequential GET / requests, the 95th-percentile
# response time must be under 100 ms.
def test_home_page_p95_response_time_is_under_budget() -> None:
    """Times the server building the page: in-process TestClient, in-memory SQLite.

    Network, TLS and the browser's own rendering are outside this number, so
    it guards against server-side regressions (an extra query per watch, a slow
    template), not the latency a buyer on a phone actually feels. Measured
    locally at about 12 ms p95; the budget leaves room for slower CI machines.
    """
    # The first request pays one-time costs (compiling templates, warming
    # SQLAlchemy's caches) that no later buyer pays, so it isn't counted.
    client.get("/")

    timings_ms = []
    for _ in range(REQUESTS):
        start = time.perf_counter()
        response = client.get("/")
        timings_ms.append((time.perf_counter() - start) * 1000)
        assert response.status_code == 200

    # quantiles(n=100) returns the 99 cut points between percentiles; the 95th is index 94.
    p95_ms = statistics.quantiles(timings_ms, n=100)[94]

    assert p95_ms < P95_BUDGET_MS, f"p95 was {p95_ms:.1f} ms, budget is {P95_BUDGET_MS} ms"
