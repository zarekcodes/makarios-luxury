"""Where owners' photos are kept: files in a folder, served at /media.

In production the folder is on a Railway volume, a disk that outlives each
deploy (docs/DEPLOY.md). MediaStore is the only code that touches it, so
moving photos to object storage later means replacing this class and the
/media mount, and nothing else.
"""

import os
import re
import secrets
from pathlib import Path
from typing import Any

from starlette.applications import Starlette
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

from app.models.watch import UPLOADS_PREFIX
from app.services.images import WIDTHS, ProcessedPhoto, file_name

# What MediaStore names a photo: "uploads/" and 16 hex digits. Anything else
# is refused by delete(), so a bad value in the database can never point it at
# another file, such as "uploads/../../app/main.py".
_UPLOAD_NAME = re.compile(rf"^{re.escape(UPLOADS_PREFIX)}[0-9a-f]{{16}}$")

# A year. Safe because a name is never reused: a replaced photo gets a new
# random name, so a browser never holds a stale copy under an old one.
CACHE_FOREVER = "public, max-age=31536000, immutable"


class MediaStore:
    """Saves and deletes a photo's WebP files under one folder."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def save(self, photo: ProcessedPhoto) -> str:
        """Write every width of the photo, and return its name for Photo.image."""
        name = UPLOADS_PREFIX + secrets.token_hex(8)
        for width, data in photo.files.items():
            path = self.root / file_name(name, width)
            path.parent.mkdir(parents=True, exist_ok=True)
            # Written beside the final name, then renamed over it in one step,
            # so a crash part-way through never leaves a half-written file
            # that a browser could be served.
            partial = path.with_name(path.name + ".partial")
            partial.write_bytes(data)
            os.replace(partial, path)
        return name

    def delete(self, name: str) -> None:
        """Remove every width of a photo saved here. Files already gone are fine."""
        if not _UPLOAD_NAME.match(name):
            raise ValueError(f"not an uploaded photo's name: {name!r}")
        for width in WIDTHS:
            (self.root / file_name(name, width)).unlink(missing_ok=True)

    def writable(self) -> bool:
        """Whether photos can be saved here: the folder exists, or can be made, and takes writes.

        A Railway volume is mounted owned by root, so an app running as a
        non-root user can't write to it unless set up for it (docs/DEPLOY.md).
        Checking first lets the admin say so, rather than fail mid-upload.
        """
        try:
            self.root.mkdir(parents=True, exist_ok=True)
        except OSError:
            return False
        return os.access(self.root, os.W_OK)

    def exists(self, name: str) -> bool:
        return all((self.root / file_name(name, width)).is_file() for width in WIDTHS)


def mount_media(app: Starlette, root: Path) -> None:
    """Serve the media folder at /media, as the "media" mount that templates' url_for names."""
    app.mount("/media", MediaFiles(root), name="media")


class MediaFiles(StaticFiles):
    """Serves the media folder, telling browsers to keep each file for a year."""

    def __init__(self, root: Path) -> None:
        # check_dir=False: the folder appears with the first upload, and an
        # empty site shouldn't fail to start for want of it.
        super().__init__(directory=root, check_dir=False)

    def file_response(self, *args: Any, **kwargs: Any) -> Response:
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = CACHE_FOREVER
        return response

    async def check_config(self) -> None:
        # StaticFiles refuses every request while its folder is missing, which
        # it is on a fresh volume until the first upload. Missing, each file is
        # just not found: a 404, not a 500.
        if self.directory is not None and Path(self.directory).is_dir():
            await super().check_config()

    async def get_response(self, path: str, scope: Scope) -> Response:
        # Only finished WebP files: never a ".partial" one mid-write.
        if not path.endswith(".webp"):
            return Response(status_code=404)
        return await super().get_response(path, scope)
