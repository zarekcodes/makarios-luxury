"""Changes the owner makes to inventory."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Watch, WatchStatus
from app.services.slugs import slugify, unique_slug

# Watch.slug holds 120 characters. A slug made from a long model name is cut
# short enough to leave room for a "-<number>" ending that tells two of the
# same watch apart.
SLUG_BASE_MAX = 110

# For a brand and model with no letters or digits slugify can keep, such as
# one written only in Japanese. Every watch needs some address.
FALLBACK_SLUG = "watch"


class WatchNotFound(LookupError):
    """No watch has the given slug."""


def new_slug(session: Session, brand: str, model: str) -> str:
    """The slug for a watch being added: its brand and model, made unique.

    A second watch of the same brand and model gets "-2", a third "-3", and so
    on. The slug is a watch's address on the site, so it's set once, here, and
    never typed or edited by hand: changing it would break every link to it.
    """
    base = slugify(f"{brand} {model}")[:SLUG_BASE_MAX].rstrip("-") or FALLBACK_SLUG
    # Only slugs that start with base can collide with it, so there's no need
    # to load every slug in the catalog.
    taken = set(session.scalars(select(Watch.slug).where(Watch.slug.startswith(base))))
    return unique_slug(base, taken)


def set_status(session: Session, slug: str, status: WatchStatus) -> Watch:
    """Mark a watch available, on hold, or sold, and save the change."""
    watch = session.scalars(select(Watch).where(Watch.slug == slug)).one_or_none()
    if watch is None:
        raise WatchNotFound(slug)

    watch.status = status
    session.commit()
    return watch
