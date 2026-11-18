"""new_slug(): the slug a watch gets when an owner adds it, checked against the database."""

from sqlalchemy.orm import Session

from app.models import BoxPapers, Condition, Watch
from app.services.inventory import SLUG_BASE_MAX, new_slug
from app.services.slugs import slugify

# The longest model the database stores. Postgres refuses anything longer
# (SQLite doesn't check), and the admin form caps the field at this too.
MODEL_MAX = Watch.__table__.c.model.type.length


def test_a_new_watch_gets_its_brand_and_model(session: Session) -> None:
    assert new_slug(session, "Halden", "Fjord Diver") == "halden-fjord-diver"


def test_a_slug_already_stored_is_numbered(session: Session) -> None:
    """The placeholder Aurelian Meridian Chronograph holds the plain slug."""
    assert new_slug(session, "Aurelian", "Meridian Chronograph") == (
        "aurelian-meridian-chronograph-2"
    )


def test_a_slug_that_only_starts_the_same_does_not_count(session: Session) -> None:
    """A slug isn't taken just because a longer one begins with it."""
    assert new_slug(session, "Aurelian", "Meridian") == "aurelian-meridian"


def test_a_long_name_leaves_room_for_a_number(session: Session) -> None:
    # As long as the model column allows, which still makes a slug longer than
    # SLUG_BASE_MAX, so the truncation is what's under test.
    long_model = ("Grande Complication " * 10)[:MODEL_MAX].rstrip()
    assert len(slugify(f"Halden {long_model}")) > SLUG_BASE_MAX

    slug = new_slug(session, "Halden", long_model)
    session.add(
        Watch(
            slug=slug,
            brand="Halden",
            model=long_model,
            reference="X",
            condition=Condition.EXCELLENT,
            box_papers=BoxPapers.WATCH_ONLY,
        )
    )
    session.commit()

    second = new_slug(session, "Halden", long_model)

    assert len(slug) <= SLUG_BASE_MAX
    assert not slug.endswith("-")
    assert second == f"{slug}-2"
    assert len(second) <= 120


def test_a_name_with_no_letters_slugify_keeps_still_gets_a_slug(session: Session) -> None:
    assert new_slug(session, "セイコー", "グランド") == "watch"


def test_accents_are_dropped(session: Session) -> None:
    assert new_slug(session, "Söhne", "Montréal") == "sohne-montreal"
