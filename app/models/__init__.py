"""Database models.

Importing this package registers every table on Base.metadata, which is the
schema Alembic compares the database against when it generates a migration.
"""

from app.models.admin_user import AdminUser
from app.models.base import Base
from app.models.watch import BoxPapers, Condition, Photo, Watch, WatchStatus

__all__ = ["AdminUser", "Base", "BoxPapers", "Condition", "Photo", "Watch", "WatchStatus"]
