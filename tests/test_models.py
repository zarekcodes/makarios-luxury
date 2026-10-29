"""Tests for the watch data model: what the database accepts, and what it keeps.

Several of these write through raw SQL on purpose. The ORM would reject a bad
value before the database saw it, and the point is that the database rejects
it too, so data entered any other way (an admin tool, a script, a manual fix)
stays consistent as well.
"""

import pytest
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import BoxPapers, Condition, Photo, Watch, WatchStatus


def new_watch(slug: str = "test-watch", **fields: object) -> Watch:
    defaults: dict[str, object] = {
        "brand": "Testbrand",
        "model": "Model",
        "reference": "TB-1",
        "year": 2020,
        "condition": Condition.EXCELLENT,
        "price": 5000,
        "box_papers": BoxPapers.BOX_AND_PAPERS,
    }
    return Watch(slug=slug, **(defaults | fields))


def insert_sql(**overrides: str) -> str:
    """An INSERT for one watch, with any column replaced by a raw SQL literal."""
    values = {
        "slug": "'raw-watch'",
        "brand": "'Testbrand'",
        "model": "'Model'",
        "reference": "'TB-1'",
        "condition": "'EXCELLENT'",
        "box_papers": "'WATCH_ONLY'",
        "status": "'AVAILABLE'",
        "featured": "FALSE",  # Postgres refuses 0 for a boolean; SQLite takes either
    } | overrides
    return f"INSERT INTO watches ({', '.join(values)}) VALUES ({', '.join(values.values())})"


def test_a_watch_keeps_every_listing_field(session: Session) -> None:
    session.add(
        new_watch(
            year=1968,
            condition=Condition.GOOD,
            price=None,
            box_papers=BoxPapers.WATCH_ONLY,
            photos=[Photo(image="placeholder/watch-01", alt="A watch.")],
        )
    )
    session.commit()
    session.expire_all()

    stored = session.scalars(select(Watch).where(Watch.slug == "test-watch")).one()

    assert (stored.brand, stored.model, stored.reference) == ("Testbrand", "Model", "TB-1")
    assert stored.year == 1968
    assert stored.condition is Condition.GOOD
    assert stored.price is None
    assert stored.box_papers is BoxPapers.WATCH_ONLY
    assert stored.status is WatchStatus.AVAILABLE
    assert [photo.image for photo in stored.photos] == ["placeholder/watch-01"]


def test_a_new_watch_is_not_featured(session: Session) -> None:
    """Featuring is the owner's choice, never the default."""
    watch = new_watch()
    session.add(watch)
    session.flush()

    assert watch.featured is False


def test_two_watches_cannot_share_a_slug(session: Session) -> None:
    """The slug will be the watch's URL, so two watches can't share one."""
    session.add_all([new_watch("same-slug"), new_watch("same-slug")])

    with pytest.raises(IntegrityError):
        session.flush()


@pytest.mark.parametrize(
    "column, value",
    [("condition", "'MINT'"), ("box_papers", "'WARRANTY_ONLY'"), ("status", "'RESERVED'")],
)
def test_the_database_rejects_values_off_the_published_lists(
    session: Session, column: str, value: str
) -> None:
    with pytest.raises(IntegrityError):
        session.execute(text(insert_sql(**{column: value})))


def test_the_database_accepts_a_valid_raw_insert(session: Session) -> None:
    """The control for the test above: the same INSERT with valid values succeeds."""
    session.execute(text(insert_sql()))

    assert session.scalars(select(Watch).where(Watch.slug == "raw-watch")).one()


def test_photos_come_back_in_position_order(session: Session) -> None:
    watch = new_watch(
        photos=[
            Photo(image="placeholder/c", alt="Third.", position=2),
            Photo(image="placeholder/a", alt="First.", position=0),
            Photo(image="placeholder/b", alt="Second.", position=1),
        ]
    )
    session.add(watch)
    session.commit()
    session.expire_all()

    assert [photo.image for photo in watch.photos] == [
        "placeholder/a",
        "placeholder/b",
        "placeholder/c",
    ]
    assert watch.primary_photo is not None
    assert watch.primary_photo.image == "placeholder/a"


def test_a_watch_without_photos_has_no_primary_photo() -> None:
    assert new_watch().primary_photo is None


def test_deleting_a_watch_deletes_its_photos(session: Session) -> None:
    """Deleted with a bulk SQL DELETE, which bypasses the ORM's own cascade.

    Only the database's ON DELETE CASCADE can remove the photos here, and in
    SQLite that only works when foreign keys are switched on.
    """
    session.add(new_watch(photos=[Photo(image="placeholder/a", alt="A watch.")]))
    session.commit()
    photos_before = session.scalar(select(func.count(Photo.id)))

    session.execute(delete(Watch).where(Watch.slug == "test-watch"))

    assert session.scalar(select(func.count(Photo.id))) == photos_before - 1


def test_a_photo_needs_a_watch(session: Session) -> None:
    with pytest.raises(IntegrityError):
        session.execute(
            text("INSERT INTO photos (watch_id, image, alt, position) VALUES (9999, 'x', 'x', 0)")
        )


def test_price_label_formats_dollars_or_says_on_request() -> None:
    assert new_watch(price=12950).price_label == "$12,950"
    assert new_watch(price=None).price_label == "Price on request"


def test_enum_labels_are_what_the_page_prints() -> None:
    """Stored as names, shown as values: VERY_GOOD in the database, "Very Good" on the page."""
    assert str(Condition.VERY_GOOD) == "Very Good"
    assert str(BoxPapers.PAPERS_ONLY) == "Papers only"
