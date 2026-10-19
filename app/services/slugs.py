"""Slugs: the part of a URL that names a watch, e.g. "aurelian-meridian-chronograph"."""

import re


def slugify(text: str) -> str:
    """Return text as a slug: lowercase letters and digits, with one hyphen between words."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower())
