"""Tests for loading inventory: the featured query, the seed, and the CLI that runs it."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import cli
from app.config import Settings
from app.main import app
from app.models import BoxPapers, Condition, Photo, Watch
from app.seed import placeholder_watches, seed
from app.services.featured import FEATURED_LIMIT, get_featured_watches

client = TestClient(app)


def listed(slug: str, day: int, featured: bool = True) -> Watch:
    return Watch(
        slug=slug,
        brand="Testbrand",
        model=slug.title(),
        reference=f"TB-{day}",
        year=2020,
        condition=Condition.EXCELLENT,
        price=5000,
        box_papers=BoxPapers.BOX_AND_PAPERS,
        featured=featured,
        listed_at=datetime(2026, 11, day, tzinfo=UTC),
        photos=[Photo(image="placeholder/watch-01", alt="A test watch.")],
    )


def test_only_featured_watches_are_featured(session: Session) -> None:
    session.add(listed("not-chosen", day=20, featured=False))
    session.commit()

    slugs = [watch.slug for watch in get_featured_watches(session)]

    assert "not-chosen" not in slugs


def test_featured_watches_are_newest_first_and_capped(session: Session) -> None:
    session.add_all([listed("older", day=10), listed("newest", day=12), listed("newer", day=11)])
    session.commit()

    featured = get_featured_watches(session)

    assert [watch.slug for watch in featured] == ["newest", "newer", "older"]
    assert len(featured) == FEATURED_LIMIT


def test_landing_page_shows_a_watch_added_to_the_database(session: Session) -> None:
    """The end-to-end proof: a row added in the database appears as a card."""
    session.add(listed("fresh-arrival", day=20))
    session.commit()

    response = client.get("/")

    assert "Fresh-Arrival" in response.text
    assert "TB-20" in response.text


def test_a_featured_watch_without_photos_still_renders(session: Session) -> None:
    watch = listed("unphotographed", day=20)
    watch.photos = []
    session.add(watch)
    session.commit()

    response = client.get("/")

    assert response.status_code == 200
    assert "Unphotographed" in response.text


def test_seed_loads_the_placeholders_once(session: Session) -> None:
    """The fixture already seeded, so seeding again must add nothing."""
    count = session.scalar(select(func.count(Watch.id)))

    assert count == len(placeholder_watches())
    assert seed(session) == 0
    assert session.scalar(select(func.count(Watch.id))) == count


def test_every_placeholder_has_a_photo_that_exists() -> None:
    for watch in placeholder_watches():
        assert watch.primary_photo is not None, f"{watch.slug} has no photo"
        assert client.get(f"/static/img/{watch.primary_photo.image}-400.webp").status_code == 200


def test_cli_seed_reports_what_it_added(
    session: Session, capsys: pytest.CaptureFixture[str]
) -> None:
    session.execute(Watch.__table__.delete())
    session.commit()

    exit_code = cli.main(["seed"], session_factory=lambda: session)

    assert exit_code == 0
    assert f"Added {len(placeholder_watches())}" in capsys.readouterr().out


def test_cli_seed_refuses_in_production(
    session: Session, capsys: pytest.CaptureFixture[str]
) -> None:
    """The placeholders are invented watches, so they must never reach real buyers."""
    session.execute(Watch.__table__.delete())
    session.commit()
    production = Settings(_env_file=None, environment="production")

    exit_code = cli.main(["seed"], session_factory=lambda: session, settings=production)

    assert exit_code == 1
    assert "production" in capsys.readouterr().err
    assert session.scalar(select(func.count()).select_from(Watch)) == 0
