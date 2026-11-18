"""Catalog queries: which watches a buyer sees on /watches, and narrowing them.

get_catalog_watches() is the listing itself (#25), and get_watch_by_slug()
finds the one watch a detail page shows (#27). filter_by_price() is for the
catalog filters (#26); it filters watches already loaded, so it needs no
database of its own.
"""

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Watch, WatchStatus


def get_catalog_watches(session: Session) -> list[Watch]:
    """Every watch that isn't sold, newest listing first.

    Featured or not makes no difference here: featuring only chooses the
    landing page's three. A watch on hold stays, and its card says so. No
    pagination: at the business's inventory size one page loads fast
    (revisit past about 60 watches).
    """
    query = (
        select(Watch)
        .where(Watch.status != WatchStatus.SOLD)
        .order_by(Watch.listed_at.desc(), Watch.id.desc())
        # Every card's photos in one extra query, not one query per card.
        .options(selectinload(Watch.photos))
    )
    return list(session.scalars(query))


def get_watch_by_slug(session: Session, slug: str) -> Watch | None:
    """The watch with this slug, or None if there isn't one.

    A sold watch is still returned, unlike the listing: links to it have been
    shared, so its page stays up and says it's sold.
    """
    query = select(Watch).where(Watch.slug == slug).options(selectinload(Watch.photos))
    return session.scalars(query).one_or_none()


def filter_by_price(
    watches: Iterable[Watch],
    min_price: int | None = None,
    max_price: int | None = None,
) -> list[Watch]:
    """Return the watches priced within [min_price, max_price], both ends inclusive.

    Either bound may be None, meaning no limit on that side. A watch priced on
    request has no number to compare, so it is left out whenever a bound is
    set, and kept only when the range is fully open.
    """
    if min_price is not None and max_price is not None and min_price > max_price:
        raise ValueError(f"min_price ({min_price}) is greater than max_price ({max_price})")

    if min_price is None and max_price is None:
        return list(watches)

    return [
        watch
        for watch in watches
        if watch.price is not None
        and (min_price is None or watch.price >= min_price)
        and (max_price is None or watch.price <= max_price)
    ]
