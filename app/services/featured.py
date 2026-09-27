"""The watches highlighted on the landing page.

The data is hardcoded for now. It lives here rather than in the template for
two reasons: routes and templates stay free of business logic, and when the
catalog database arrives in Sprint 3 only the body of get_featured_watches()
changes — the route and the template stay exactly as they are.

The pieces below are invented. They are deliberately plausible rather than
real references, and they use the same condition grades the trust section
publishes, so the page reads as internally consistent.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FeaturedWatch:
    """One watch as the landing page needs it."""

    slug: str
    brand: str
    model: str
    reference: str
    year: int
    condition: str
    # Whole US dollars. None means the price is given on request, not listed.
    price: int | None
    alt: str

    @property
    def name(self) -> str:
        return f"{self.brand} {self.model}"

    @property
    def price_label(self) -> str:
        if self.price is None:
            return "Price on request"
        return f"${self.price:,}"


_FEATURED = (
    FeaturedWatch(
        slug="watch-01",
        brand="Aurelian",
        model="Meridian Chronograph",
        reference="AM-3120-SS",
        year=2019,
        condition="Excellent",
        price=8400,
        alt="Steel chronograph with a pale dial on a navy leather strap.",
    ),
    FeaturedWatch(
        slug="watch-02",
        brand="Calloway",
        model="Regent Ultra-Thin",
        reference="CR-880-YG",
        year=2016,
        condition="Very Good",
        price=12950,
        alt="Yellow gold dress watch with a cream dial on a brown leather strap.",
    ),
    FeaturedWatch(
        slug="watch-03",
        brand="Norvell",
        model="Deepline 300",
        reference="ND-300-TI",
        year=2021,
        condition="Unworn",
        price=None,
        alt="Titanium diver with a royal blue dial on a dark rubber strap.",
    ),
)


def get_featured_watches() -> list[FeaturedWatch]:
    """Return the watches to highlight on the landing page."""
    return list(_FEATURED)
