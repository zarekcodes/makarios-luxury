"""Slugs: the part of a URL that names a watch, e.g. "aurelian-meridian-chronograph"."""

import re
import unicodedata

# What sits between the words of a slug: any run of characters that aren't a
# lowercase letter or a digit, such as spaces, "/", ", " or " & ".
_SEPARATOR = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    """Return text as a slug: lowercase letters and digits, with one hyphen between words."""
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return _SEPARATOR.sub("-", ascii_text.lower())
