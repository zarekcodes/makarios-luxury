"""The watch detail page (#27), built behind MAKARIOS_WATCH_DETAIL_PAGE_ENABLED until it ships.

The route reads settings through a dependency, so each test hands it settings
with the flag set the way that test needs, the same override that swaps in
the test database.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.main import app
from app.models import BoxPapers, Condition, Watch, WatchStatus

client = TestClient(app)

# One of the placeholder watches the test database is seeded with.
SEEDED_SLUG = "aurelian-meridian-chronograph"


def set_detail_flag(monkeypatch: pytest.MonkeyPatch, *, enabled: bool) -> None:
    """Serve the app with the flag set; monkeypatch removes the override afterwards."""
    flagged = Settings(_env_file=None, watch_detail_page_enabled=enabled)
    monkeypatch.setitem(app.dependency_overrides, get_settings, lambda: flagged)


@pytest.fixture
def flag_on(monkeypatch: pytest.MonkeyPatch) -> None:
    set_detail_flag(monkeypatch, enabled=True)


def add_watch(
    session: Session,
    slug: str,
    *,
    status: WatchStatus = WatchStatus.AVAILABLE,
    price: int | None = 8450,
    year: int | None = 2019,
) -> None:
    session.add(
        Watch(
            slug=slug,
            brand="Halden",
            model="Tidewater GMT",
            reference="HL-4021",
            year=year,
            condition=Condition.VERY_GOOD,
            box_papers=BoxPapers.BOX_AND_PAPERS,
            price=price,
            status=status,
        )
    )
    session.commit()


def test_with_the_flag_off_the_detail_page_does_not_exist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Off is what production runs: a buyer finds a plain 404, like any unknown URL."""
    set_detail_flag(monkeypatch, enabled=False)

    response = client.get(f"/watches/{SEEDED_SLUG}")

    assert response.status_code == 404
    assert response.json() == client.get("/no-such-page").json()


def test_with_the_flag_on_the_detail_page_renders(monkeypatch: pytest.MonkeyPatch) -> None:
    set_detail_flag(monkeypatch, enabled=True)

    response = client.get(f"/watches/{SEEDED_SLUG}")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_the_unfinished_detail_page_is_kept_out_of_search_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_detail_flag(monkeypatch, enabled=True)

    response = client.get(f"/watches/{SEEDED_SLUG}")

    assert '<meta name="robots" content="noindex">' in response.text


def test_the_catalog_still_answers_with_the_flag_off(monkeypatch: pytest.MonkeyPatch) -> None:
    """The flag gates /watches/<slug> only; the shipped listing at /watches stays up."""
    set_detail_flag(monkeypatch, enabled=False)

    assert client.get("/watches").status_code == 200


@pytest.mark.usefixtures("flag_on")
def test_the_page_shows_the_watch_it_is_for(session: Session) -> None:
    add_watch(session, "halden-tidewater-gmt")

    html = client.get("/watches/halden-tidewater-gmt").text

    assert "<h1" in html and "Halden Tidewater GMT</h1>" in html
    for detail in ("HL-4021", "2019", "Very Good", "Box and papers", "Available", "$8,450"):
        assert detail in html


@pytest.mark.usefixtures("flag_on")
def test_the_page_title_and_description_name_the_watch(session: Session) -> None:
    add_watch(session, "halden-tidewater-gmt")

    html = client.get("/watches/halden-tidewater-gmt").text

    assert "<title>Halden Tidewater GMT · Makarios Luxury</title>" in html
    assert '<meta name="description" content="Halden Tidewater GMT, ref. HL-4021' in html


@pytest.mark.usefixtures("flag_on")
def test_a_watch_priced_on_request_says_so(session: Session) -> None:
    add_watch(session, "halden-tidewater-gmt", price=None)

    assert "Price on request" in client.get("/watches/halden-tidewater-gmt").text


@pytest.mark.usefixtures("flag_on")
def test_an_undocumented_year_is_not_printed_as_none(session: Session) -> None:
    add_watch(session, "halden-tidewater-gmt", year=None)

    html = client.get("/watches/halden-tidewater-gmt").text

    assert "Not documented" in html
    assert ">None<" not in html


@pytest.mark.usefixtures("flag_on")
def test_a_watch_on_hold_says_so(session: Session) -> None:
    add_watch(session, "halden-tidewater-gmt", status=WatchStatus.ON_HOLD)

    assert "On hold" in client.get("/watches/halden-tidewater-gmt").text


@pytest.mark.usefixtures("flag_on")
def test_a_sold_watch_keeps_its_page(session: Session) -> None:
    """Links to it have been shared, so they must not break once it sells."""
    add_watch(session, "halden-tidewater-gmt", status=WatchStatus.SOLD)

    response = client.get("/watches/halden-tidewater-gmt")

    assert response.status_code == 200
    assert "Sold" in response.text


@pytest.mark.usefixtures("flag_on")
def test_an_unknown_slug_is_a_404() -> None:
    response = client.get("/watches/no-such-watch")

    assert response.status_code == 404
    assert response.json() == client.get("/no-such-page").json()
