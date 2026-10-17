"""The watches highlighted on the landing page."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Watch

# The grid is three across on a laptop, so a fourth watch would start a
# lonely second row.
FEATURED_LIMIT = 3


def get_featured_watches(session: Session, limit: int = FEATURED_LIMIT) -> list[Watch]:
    """Return the watches the owner chose to feature, newest listing first."""
    query = (
        select(Watch)
        .where(Watch.featured)
        .order_by(Watch.listed_at.desc(), Watch.id.desc())
        .limit(limit)
        # Load every card's photos in one extra query, rather than one query
        # per card as the template reads them (the "N+1" problem).
        .options(selectinload(Watch.photos))
    )
    return list(session.scalars(query))
