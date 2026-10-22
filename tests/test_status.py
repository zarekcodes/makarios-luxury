"""Tests for marking a watch available, on hold, or sold, and what buyers then see."""

from html.parser import HTMLParser

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import cli
from app.main import app
from app.models import BoxPapers, Condition, Watch, WatchStatus
from app.services.featured import get_featured_watches
from app.services.inventory import WatchNotFound, set_status

client = TestClient(app)

# Two of the seeded placeholder watches.
CHRONOGRAPH = "aurelian-meridian-chronograph"
DIVER = "norvell-deepline-300"


class ArticleText(HTMLParser):
    """Collects the text of each <article>, so a test can check one card at a time."""

    def __init__(self) -> None:
        super().__init__()
        self.articles: list[str] = []
        self.depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "article":
            self.articles.append("")
            self.depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "article":
            self.depth -= 1

    def handle_data(self, data: str) -> None:
        if self.depth:
            self.articles[-1] += data


def stored_status(session: Session, slug: str) -> WatchStatus:
    """The status as the database has it, not as the session remembers it."""
    session.expire_all()
    return session.scalars(select(Watch.status).where(Watch.slug == slug)).one()


def card_for(name: str) -> str | None:
    """The text of the landing page card for the watch called `name`, or None."""
    parser = ArticleText()
    parser.feed(client.get("/").text)
    return next((text for text in parser.articles if name in text), None)


def test_a_new_watch_starts_available(session: Session) -> None:
    watch = Watch(
        slug="new-arrival",
        brand="Testbrand",
        model="Model",
        reference="TB-1",
        condition=Condition.EXCELLENT,
        box_papers=BoxPapers.WATCH_ONLY,
    )
    session.add(watch)
    session.flush()

    assert watch.status is WatchStatus.AVAILABLE


def test_set_status_saves_the_change(session: Session) -> None:
    set_status(session, CHRONOGRAPH, WatchStatus.ON_HOLD)

    assert stored_status(session, CHRONOGRAPH) is WatchStatus.ON_HOLD


def test_set_status_on_an_unknown_watch_is_an_error(session: Session) -> None:
    with pytest.raises(WatchNotFound):
        set_status(session, "no-such-watch", WatchStatus.SOLD)


def test_a_sold_watch_leaves_the_landing_page(session: Session) -> None:
    set_status(session, DIVER, WatchStatus.SOLD)

    assert DIVER not in [watch.slug for watch in get_featured_watches(session)]
    assert card_for("Norvell Deepline 300") is None


def test_a_watch_on_hold_stays_on_the_page_labelled(session: Session) -> None:
    set_status(session, CHRONOGRAPH, WatchStatus.ON_HOLD)

    card = card_for("Aurelian Meridian Chronograph")

    assert card is not None, "a watch on hold must stay on the page"
    assert "On hold" in card


def test_an_available_watch_has_no_status_label() -> None:
    """The control for the test above: the label appears only when it means something."""
    card = card_for("Aurelian Meridian Chronograph")

    assert card is not None
    assert "On hold" not in card
    assert "Sold" not in card


def test_a_watch_can_go_back_on_sale(session: Session) -> None:
    """A buyer's hold can fall through; the watch then returns to the page unlabelled."""
    set_status(session, CHRONOGRAPH, WatchStatus.ON_HOLD)
    set_status(session, CHRONOGRAPH, WatchStatus.AVAILABLE)

    card = card_for("Aurelian Meridian Chronograph")

    assert card is not None
    assert "On hold" not in card


@pytest.mark.parametrize(
    "argument, status",
    [
        ("available", WatchStatus.AVAILABLE),
        ("on-hold", WatchStatus.ON_HOLD),
        ("sold", WatchStatus.SOLD),
    ],
)
def test_cli_status_marks_the_watch(
    session: Session, capsys: pytest.CaptureFixture[str], argument: str, status: WatchStatus
) -> None:
    exit_code = cli.main(["status", CHRONOGRAPH, argument], session_factory=lambda: session)

    assert exit_code == 0
    assert stored_status(session, CHRONOGRAPH) is status
    assert f"is now {status.lower()}" in capsys.readouterr().out


def test_cli_status_reports_an_unknown_watch(
    session: Session, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = cli.main(["status", "no-such-watch", "sold"], session_factory=lambda: session)

    assert exit_code == 1
    assert "no-such-watch" in capsys.readouterr().err


def test_cli_status_rejects_an_unknown_status(session: Session) -> None:
    """argparse refuses it before any watch is touched, and exits with usage error 2."""
    with pytest.raises(SystemExit) as error:
        cli.main(["status", CHRONOGRAPH, "reserved"], session_factory=lambda: session)

    assert error.value.code == 2
