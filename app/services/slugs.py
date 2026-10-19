"""Slugs: the part of a URL that names a watch, e.g. "aurelian-meridian-chronograph"."""

import re
import unicodedata
from collections.abc import Container

# What sits between the words of a slug: any run of characters that aren't a
# lowercase letter or a digit, such as spaces, "/", ", " or " & ".
_SEPARATOR = re.compile(r"[^a-z0-9]+")


def _to_ascii(text: str) -> str:
    """Drop accents, so "Söhne" becomes "Sohne".

    NFKD normalization splits an accented letter into its base letter plus a
    separate accent mark ("ö" into "o" and a combining diaeresis). The accent
    marks aren't ASCII, so encoding to ASCII and ignoring errors drops them.
    """
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def slugify(text: str) -> str:
    """Return text as a slug: lowercase letters and digits, with one hyphen between words."""
    return _SEPARATOR.sub("-", _to_ascii(text).lower())


def unique_slug(slug: str, taken: Container[str]) -> str:
    """Return slug, or if it's taken, slug with the lowest free number from 2 up."""
    if slug not in taken:
        return slug
    number = 2
    while f"{slug}-{number}" in taken:
        number += 1
    return f"{slug}-{number}"
