"""Catalog queries: narrowing the list of watches a buyer sees.

The catalog filters story needs a price range, and it is business logic, so it
lives here rather than in a route. It works on anything the featured service
returns today and will keep working once the watches come from the database.
"""

from collections.abc import Iterable

from app.services.featured import FeaturedWatch


def filter_by_price(
    watches: Iterable[FeaturedWatch],
    min_price: int | None = None,
    max_price: int | None = None,
) -> list[FeaturedWatch]:
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
