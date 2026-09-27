"""Unit tests for the catalog price filter.

The cases come from Equivalence Partitioning (one representative per class of
input: inside the range, outside it, no numeric price at all) and Boundary
Value Analysis (the exact edge of the range and one step past it).
"""

from dataclasses import replace

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


def test_price_on_request_is_excluded() -> None:
    """EP, special partition: a watch with no numeric price can't match a range."""
    assert filter_by_price([watch(None)], min_price=0, max_price=10000) == []
