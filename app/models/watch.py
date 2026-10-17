"""A watch for sale, and its photos."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Condition(enum.StrEnum):
    """The grading scale the landing page publishes, best first."""

    UNWORN = "Unworn"
    EXCELLENT = "Excellent"
    VERY_GOOD = "Very Good"
    GOOD = "Good"


class BoxPapers(enum.StrEnum):
    """What comes with the watch. Buyers weigh this almost as heavily as condition."""

    BOX_AND_PAPERS = "Box and papers"
    PAPERS_ONLY = "Papers only"
    BOX_ONLY = "Box only"
    WATCH_ONLY = "Watch only"


class WatchStatus(enum.StrEnum):
    """Whether a watch can still be bought."""

    AVAILABLE = "Available"
    ON_HOLD = "On hold"
    SOLD = "Sold"


def choice(enum_class: type[enum.Enum]) -> Enum:
    """A column type that accepts only the members of enum_class.

    The database stores each member's name (VERY_GOOD), while templates print
    its value (Very Good), so a label can be reworded without touching the
    data. native_enum=False makes it a plain string column with a CHECK
    constraint on every database, rather than a Postgres ENUM type, which is
    awkward to change in a migration.
    """
    return Enum(enum_class, native_enum=False, create_constraint=True)


class Watch(Base):
    __tablename__ = "watches"

    id: Mapped[int] = mapped_column(primary_key=True)
    # The watch's name in a URL, e.g. "aurelian-meridian-chronograph".
    slug: Mapped[str] = mapped_column(String(120), unique=True)
    brand: Mapped[str] = mapped_column(String(60))
    model: Mapped[str] = mapped_column(String(120))
    reference: Mapped[str] = mapped_column(String(40))
    # None when the year isn't documented, which is common for vintage pieces.
    year: Mapped[int | None]
    condition: Mapped[Condition] = mapped_column(choice(Condition))
    box_papers: Mapped[BoxPapers] = mapped_column(choice(BoxPapers))
    # Whole US dollars. None means the price is given on request, not listed.
    price: Mapped[int | None]
    status: Mapped[WatchStatus] = mapped_column(choice(WatchStatus), default=WatchStatus.AVAILABLE)
    # Chosen by the owner to appear on the landing page.
    featured: Mapped[bool] = mapped_column(default=False)
    listed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # In display order. Deleting a watch deletes its photos.
    photos: Mapped[list["Photo"]] = relationship(
        back_populates="watch", order_by="Photo.position", cascade="all, delete-orphan"
    )

    @property
    def name(self) -> str:
        return f"{self.brand} {self.model}"

    @property
    def price_label(self) -> str:
        if self.price is None:
            return "Price on request"
        return f"${self.price:,}"

    @property
    def inquiry_subject(self) -> str:
        """The subject line of an email about this watch.

        It carries the reference, so the owner knows exactly which piece a
        buyer means without having to ask.
        """
        return f"Inquiry: {self.name}, ref. {self.reference}"

    @property
    def primary_photo(self) -> "Photo | None":
        """The photo cards show: the first one, or None for a watch not yet photographed."""
        return self.photos[0] if self.photos else None


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    watch_id: Mapped[int] = mapped_column(ForeignKey("watches.id", ondelete="CASCADE"), index=True)
    # The image's path under /static/img, without the "-<width>.webp" suffix,
    # e.g. "placeholder/watch-01". Owner uploads will need media storage
    # instead (#28), which may change what this holds.
    image: Mapped[str] = mapped_column(String(200))
    # Describes the photo for screen readers and for when it fails to load.
    alt: Mapped[str] = mapped_column(String(300))
    # 0 comes first. The first photo is the one cards show.
    position: Mapped[int] = mapped_column(default=0)

    watch: Mapped[Watch] = relationship(back_populates="photos")
