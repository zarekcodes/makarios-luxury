"""A watch's photos: adding, ordering and removing them.

The first photo, position 0, is the one the cards show. Positions are kept
0, 1, 2... with no gaps after every change, so "first" is never ambiguous.
"""

from sqlalchemy.orm import Session

from app.models import Photo, Watch
from app.services.images import PhotoRejected, process_photo
from app.services.media import MediaStore

# Photo.alt's column width.
MAX_ALT_LENGTH = 300


class PhotoNotFound(LookupError):
    """The watch has no photo with that id."""


def add_photo(session: Session, store: MediaStore, watch: Watch, data: bytes, alt: str) -> Photo:
    """Process an uploaded photo, store its files, and add it after the watch's others.

    Raises PhotoRejected, with a message for the owner, for missing alt text
    or a file the image pipeline refuses. Nothing is stored in either case.
    """
    alt = " ".join(alt.split())
    if not alt:
        raise PhotoRejected(
            "Describe the photo before adding it, e.g. “Dial close-up in daylight”. "
            "Screen readers read it out, and it shows if the photo fails to load."
        )
    if len(alt) > MAX_ALT_LENGTH:
        raise PhotoRejected(f"Keep the description under {MAX_ALT_LENGTH} characters.")

    name = store.save(process_photo(data))
    photo = Photo(image=name, alt=alt, position=len(watch.photos))
    watch.photos.append(photo)
    try:
        session.commit()
    except Exception:
        # The files are written before the row, so a failed save takes them
        # back out rather than leave files no photo points to.
        session.rollback()
        store.delete(name)
        raise
    return photo


def move_photo(session: Session, watch: Watch, photo_id: int, step: int) -> None:
    """Move a photo one place earlier (step -1) or later (step 1). The ends stay put."""
    photos = list(watch.photos)
    index = _index_of(photos, photo_id)
    target = index + step
    if 0 <= target < len(photos):
        photos[index], photos[target] = photos[target], photos[index]
        _renumber(photos)
        session.commit()
        _reload_order(session, watch)


def delete_photo(session: Session, store: MediaStore, watch: Watch, photo_id: int) -> None:
    """Remove a photo and its files. The ones after it move up a place."""
    photos = list(watch.photos)
    photo = photos.pop(_index_of(photos, photo_id))
    watch.photos.remove(photo)
    _renumber(photos)
    session.commit()
    _reload_order(session, watch)
    # After the commit, so a failed delete never leaves a row without files.
    # A placeholder's files belong to the repository, not to the store.
    if photo.is_upload:
        store.delete(photo.image)


def _index_of(photos: list[Photo], photo_id: int) -> int:
    for index, photo in enumerate(photos):
        if photo.id == photo_id:
            return index
    raise PhotoNotFound(photo_id)


def _renumber(photos: list[Photo]) -> None:
    for position, photo in enumerate(photos):
        photo.position = position


def _reload_order(session: Session, watch: Watch) -> None:
    """Forget watch.photos, so the next read loads it again in its new position order.

    The list in memory keeps the order it was loaded in; changing positions
    doesn't re-sort it.
    """
    session.expire(watch, ["photos"])
