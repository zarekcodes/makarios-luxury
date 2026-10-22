"""Changes the owner makes to inventory."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Watch, WatchStatus


class WatchNotFound(LookupError):
    """No watch has the given slug."""


def set_status(session: Session, slug: str, status: WatchStatus) -> Watch:
    """Mark a watch available, on hold, or sold, and save the change."""
    watch = session.scalars(select(Watch).where(Watch.slug == slug)).one_or_none()
    if watch is None:
        raise WatchNotFound(slug)

    watch.status = status
    session.commit()
    return watch
