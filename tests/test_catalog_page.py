"""The catalog listing (#25): /watches lists every watch that isn't sold, newest first."""

import re
import statistics
import time
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import BoxPapers, Condition, Watch, WatchStatus
from app.services.catalog import get_catalog_watches
from tests.test_landing import collect, hrefs, mailto_subjects, remove_every_watch

client = TestClient(app)


def listed(
    slug: str, day: int, status: WatchStatus = WatchStatus.AVAILABLE, featured: bool = False
) -> Watch:
    return Watch(
        slug=slug,
        brand="Halden",
        model=slug.replace("-", " ").title(),
        reference=f"HL-{day}",
        condition=Condition.EXCELLENT,
        box_papers=BoxPapers.WATCH_ONLY,
        price=4000 + day,
        status=status,
        featured=featured,
        listed_at=datetime(2026, 11, day, tzinfo=UTC),
    )


def names_in_order(html: str) -> list[str]:
    """The watch names on the page, top to bottom, from the cards' headings."""
    return re.findall(r'<h2 class="text-display-3 text-white">([^<]+)</h2>', html)


@pytest.fixture
def stock(session: Session) -> None:
    """Only these four: two in stock, one on hold, one sold."""
    remove_every_watch(session)
    session.add_all(
        [
            listed("older-piece", day=2),
            listed("newest-piece", day=9),
            listed("held-piece", day=5, status=WatchStatus.ON_HOLD),
            listed("sold-piece", day=7, status=WatchStatus.SOLD),
        ]
    )
    session.commit()


@pytest.mark.usefixtures("stock")
def test_every_watch_in_stock_is_listed_newest_first() -> None:
    """Featured or not: featuring only chooses the landing page's three."""
    response = client.get("/watches")

    assert response.status_code == 200
    assert names_in_order(response.text) == [
        "Halden Newest Piece",
        "Halden Held Piece",
        "Halden Older Piece",
    ]


@pytest.mark.usefixtures("stock")
def test_a_sold_watch_is_left_out() -> None:
    assert "Sold Piece" not in client.get("/watches").text


@pytest.mark.usefixtures("stock")
def test_a_watch_on_hold_says_so() -> None:
    html = client.get("/watches").text
    card = html[html.index("Halden Held Piece") :]

    assert "On hold" in card[: card.index("</article>")]


@pytest.mark.usefixtures("stock")
def test_the_count_matches_the_cards() -> None:
    html = client.get("/watches").text

    assert "3 pieces, newest first." in html
    assert html.count("<article") == 3


def test_the_service_orders_and_filters(session: Session) -> None:
    remove_every_watch(session)
    session.add_all(
        [listed("a", day=1), listed("b", day=3), listed("c", day=2, status=WatchStatus.SOLD)]
    )
    session.commit()

    assert [watch.slug for watch in get_catalog_watches(session)] == ["b", "a"]


def test_with_nothing_in_stock_the_page_offers_sourcing(session: Session) -> None:
    remove_every_watch(session)
    session.add(listed("sold-piece", day=7, status=WatchStatus.SOLD))
    session.commit()

    response = client.get("/watches")

    assert response.status_code == 200
    assert "<article" not in response.text
    assert "New pieces arriving." in response.text
    assert "Every watch in stock." not in response.text
    assert "Sourcing request" in mailto_subjects(response.text)


def test_the_page_has_one_h1_and_skips_no_heading_level() -> None:
    """The cards' names are <h2> here, under the page's <h1>; on the landing page, <h3>."""
    html = client.get("/watches").text

    assert html.count("<h1") == 1
    assert "<h3" not in html
    assert names_in_order(html)


def test_the_page_is_open_to_search_engines() -> None:
    """The flag's noindex went with the flag, now the page is finished."""
    assert 'name="robots"' not in client.get("/watches").text


def test_the_navigation_and_the_landing_page_lead_to_the_catalog() -> None:
    home = client.get("/").text
    catalog = client.get("/watches").text

    assert 'href="/watches"' in home
    assert "Shop the collection" in home
    assert "See every watch in stock" in home
    # Only the catalog marks its own nav link as the current page.
    assert 'aria-current="page"' in catalog
    assert 'aria-current="page"' not in home


def test_the_section_links_work_from_the_catalog() -> None:
    """On /watches, "#trust" would point nowhere; "/#trust" goes to the landing page's section."""
    catalog = client.get("/watches").text
    home = client.get("/").text

    for href in ("/#trust", "/#contact"):
        assert f'href="{href}"' in catalog
        assert f'id="{href[2:]}"' in home


def test_internal_links_and_images_resolve() -> None:
    html = client.get("/watches").text

    for href in hrefs(html):
        if href.startswith("/"):
            assert client.get(href).status_code < 400, f"broken link: {href}"
    for image in collect(html, "img"):
        candidates = [image.get("src") or ""]
        candidates += re.findall(r"(\S+)\s+\d+w", image.get("srcset") or "")
        for url in filter(None, candidates):
            assert client.get(url).status_code == 200, f"missing image: {url}"


def test_watch_photos_load_lazily() -> None:
    """A buyer on a phone downloads only the photos they scroll to.

    The cards' photos, that is: the header's logo loads at once, on every page.
    """
    html = client.get("/watches").text
    cards = "".join(re.findall(r"<article.*?</article>", html, re.S))
    photos = collect(cards, "img")

    assert photos
    for image in photos:
        assert image.get("loading") == "lazy"
        assert image.get("width") and image.get("height")


# NFR (performance), as for the landing page: the 95th-percentile server time
# for /watches stays under 100 ms across 50 requests (in-process, in-memory).
def test_catalog_p95_response_time_is_under_budget() -> None:
    client.get("/watches")  # Warm up: the first render compiles the templates.
    timings = []
    for _ in range(50):
        start = time.perf_counter()
        client.get("/watches")
        timings.append((time.perf_counter() - start) * 1000)

    p95 = statistics.quantiles(timings, n=20)[-1]
    assert p95 < 100, f"p95 {p95:.1f} ms"
