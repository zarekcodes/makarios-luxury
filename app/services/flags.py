"""Feature flags read at request time, so turning one on or off is a config edit, not a deploy.

A flag in app/config.py is an environment variable, read once when the app
starts. Changing it means restarting the app, and on Railway changing a
variable restarts the service: a redeploy. A flags file separates the two.
The deploy puts the code out, flag and all, and the file decides whether
buyers see what the flag gates (the release), whenever its owner edits it.

The file is a JSON object of flag names and booleans:

    {"watch_detail_page": true}

MAKARIOS_FLAGS_SOURCE names it: a path on disk, or an http(s) URL, such as a
presigned URL for an S3 object (docs/DEPLOY.md). Unset, which is what
production runs, every flag falls back to its setting in app/config.py.

The file is read again once its last read is MAKARIOS_FLAGS_TTL_SECONDS old,
so an edit takes effect within that many seconds, without a restart. If a
read fails (the file is missing, unreachable, or not valid JSON), the last
values that read cleanly stay in force, and before any read succeeds each
flag keeps its default. A broken flags file never takes the site down.
"""

import json
import logging
import time
import urllib.request
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends

from app.config import get_settings

logger = logging.getLogger("makarios.flags")

# How long a URL read may take. A request waits on it, so a slow host must not
# hold a buyer's page for long; past this the last good values are used.
FETCH_TIMEOUT_SECONDS = 2.0


class FlagFile:
    """The flags in one JSON file, re-read once the last read is ttl_seconds old."""

    def __init__(
        self,
        source: str | None,
        ttl_seconds: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.source = source
        self.ttl_seconds = ttl_seconds
        self._clock = clock
        self._values: dict[str, bool] = {}
        self._read_at: float | None = None

    def is_enabled(self, name: str, *, default: bool) -> bool:
        """The flag's value in the file, or default if the file doesn't set it."""
        if self.source is None:
            return default
        self._refresh_if_stale()
        return self._values.get(name, default)

    def _refresh_if_stale(self) -> None:
        now = self._clock()
        if self._read_at is not None and now - self._read_at < self.ttl_seconds:
            return
        # Set before reading, so a failing source is retried once per ttl, not
        # on every request.
        self._read_at = now
        try:
            self._values = _parse(self._read())
        except (OSError, ValueError) as error:
            logger.warning("Keeping the last flag values: can't read %s (%s)", self.source, error)

    def _read(self) -> str:
        assert self.source is not None
        if self.source.startswith(("http://", "https://")):
            with urllib.request.urlopen(self.source, timeout=FETCH_TIMEOUT_SECONDS) as response:
                return response.read().decode()
        return Path(self.source).read_text()


def _parse(text: str) -> dict[str, bool]:
    """Every boolean in the file. Anything else is logged and left out, so it falls back."""
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("the flags file must be a JSON object")
    flags = {}
    for name, value in data.items():
        if isinstance(value, bool):
            flags[name] = value
        else:
            logger.warning("Ignoring flag %r: %r is not true or false", name, value)
    return flags


@lru_cache
def get_flags() -> FlagFile:
    """The app's one flags file, so its cached values are shared by every request."""
    settings = get_settings()
    return FlagFile(settings.flags_source, settings.flags_ttl_seconds)


# Routes declare `flags: FlagsDep`; tests override get_flags with their own file.
FlagsDep = Annotated[FlagFile, Depends(get_flags)]
