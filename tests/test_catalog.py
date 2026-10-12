"""Unit tests for the catalog price filter.

The cases come from Equivalence Partitioning (one representative per class of
input: inside the range, outside it, no numeric price at all, no range at all,
an impossible range) and Boundary Value Analysis (each edge of the range, one
step past it, and the narrowest range there is). Each test's docstring names
the technique it comes from.

No test double is needed here. filter_by_price() receives its watches as an
argument instead of fetching them, and it touches no database, file, network
or clock, so every test already controls every input by building watches in
memory. Those watches are test data, not doubles: they are the real
FeaturedWatch type, passed in as values. A double becomes necessary one layer
up, once the catalog route loads watches from the database in Sprint 4. That
route is where a stub or fake will stand in for the query.
"""

from dataclasses import replace

import pytest

from app.services.catalog import filter_by_price
from app.services.featured import FeaturedWatch

BASE = FeaturedWatch(
    slug="test",
    brand="Testbrand",
    model="Model",
    reference="TB-1",
    year=2020,
    condition="Excellent",
    price=5000,
    box_papers="Box and papers",
    alt="A test watch.",
)


def watch(price: int | None) -> FeaturedWatch:
    return replace(BASE, slug=f"watch-{price}", price=price)


def test_price_inside_range_is_included() -> None:
    """EP, valid partition: a price comfortably between the bounds."""
    inside = watch(5000)

    assert filter_by_price([inside], min_price=1000, max_price=10000) == [inside]


def test_price_above_range_is_excluded() -> None:
    """EP, invalid partition: a price well over the maximum."""
    assert filter_by_price([watch(25000)], min_price=1000, max_price=10000) == []


def test_price_exactly_at_max_is_included() -> None:
    """BVA: the upper bound is inclusive, so max itself stays in."""
    at_max = watch(10000)

    assert filter_by_price([at_max], min_price=1000, max_price=10000) == [at_max]


def test_price_one_above_max_is_excluded() -> None:
    """BVA: the smallest step past the upper bound is dropped."""
    assert filter_by_price([watch(10001)], min_price=1000, max_price=10000) == []


def test_price_exactly_at_min_is_included() -> None:
    """BVA: the lower bound is inclusive too, so min itself stays in."""
    at_min = watch(1000)

    assert filter_by_price([at_min], min_price=1000, max_price=10000) == [at_min]


def test_price_one_below_min_is_excluded() -> None:
    """BVA: the smallest step under the lower bound is dropped."""
    assert filter_by_price([watch(999)], min_price=1000, max_price=10000) == []


def test_equal_bounds_match_only_that_price() -> None:
    """BVA: min equal to max is the narrowest valid range, one exact price."""
    exact = watch(5000)

    assert filter_by_price([watch(4999), exact, watch(5001)], min_price=5000, max_price=5000) == [
        exact
    ]


def test_price_on_request_is_excluded() -> None:
    """EP, special partition: a watch with no numeric price can't match a range."""
    assert filter_by_price([watch(None)], min_price=0, max_price=10000) == []


def test_open_range_keeps_every_watch() -> None:
    """EP, no-bounds partition: with no range set, nothing is filtered out.

    That includes a watch priced on request, which only drops out once a
    bound gives it something to be compared against.
    """
    watches = [watch(None), watch(5000)]

    assert filter_by_price(watches) == watches


def test_min_above_max_is_rejected() -> None:
    """EP, invalid partition: a range whose minimum is over its maximum is an error."""
    with pytest.raises(ValueError, match="greater than"):
        filter_by_price([watch(5000)], min_price=10000, max_price=9999)
