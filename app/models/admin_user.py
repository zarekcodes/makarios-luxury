"""An owner who can sign in to the admin."""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # What the owner types on the login form.
    username: Mapped[str] = mapped_column(String(60), unique=True)
    # An Argon2 hash, never the password itself. It records its own salt and
    # cost settings, so it's the only column a password check needs.
    password_hash: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
