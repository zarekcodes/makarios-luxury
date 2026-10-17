"""Placeholder inventory, so the site has watches to show before real listings exist.

Load it with `uv run python -m app.cli seed`. Running it again is safe: a
watch whose slug is already stored is left alone.

The pieces are invented. They are deliberately plausible rather than real
references, and they use the same condition grades the trust section
publishes, so the page reads as internally consistent. Their listing dates
set the order the landing page shows them in, newest first.
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import BoxPapers, Condition, Photo, Watch


def placeholder_watches() -> list[Watch]:
    """New, unsaved copies of the placeholder watches.

    A function rather than a constant, because a model object belongs to the
    one session that saved it and can't be added to a second.
    """
    return [
        Watch(
            slug="aurelian-meridian-chronograph",
            brand="Aurelian",
            model="Meridian Chronograph",
            reference="AM-3120-SS",
            year=2019,
            condition=Condition.EXCELLENT,
            price=8400,
            box_papers=BoxPapers.BOX_AND_PAPERS,
            featured=True,
            listed_at=datetime(2026, 10, 3, tzinfo=UTC),
            photos=[
                Photo(
                    image="placeholder/watch-01",
                    alt="Steel chronograph with a pale dial on a navy leather strap.",
                )
            ],
        ),
        Watch(
            slug="calloway-regent-ultra-thin",
            brand="Calloway",
            model="Regent Ultra-Thin",
            reference="CR-880-YG",
            year=2016,
            condition=Condition.VERY_GOOD,
            price=12950,
            box_papers=BoxPapers.PAPERS_ONLY,
            featured=True,
            listed_at=datetime(2026, 10, 2, tzinfo=UTC),
            photos=[
                Photo(
                    image="placeholder/watch-02",
                    alt="Yellow gold dress watch with a cream dial on a brown leather strap.",
                )
            ],
        ),
        Watch(
            slug="norvell-deepline-300",
            brand="Norvell",
            model="Deepline 300",
            reference="ND-300-TI",
            year=2021,
            condition=Condition.UNWORN,
            price=None,
            box_papers=BoxPapers.BOX_AND_PAPERS,
            featured=True,
            listed_at=datetime(2026, 10, 1, tzinfo=UTC),
            photos=[
                Photo(
                    image="placeholder/watch-03",
                    alt="Titanium diver with a royal blue dial on a dark rubber strap.",
                )
            ],
        ),
    ]


def seed(session: Session) -> int:
    """Store every placeholder watch not already in the database. Returns how many were added."""
    stored = set(session.scalars(select(Watch.slug)))
    new = [watch for watch in placeholder_watches() if watch.slug not in stored]

    session.add_all(new)
    session.commit()
    return len(new)
