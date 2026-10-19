"""Slugs: the part of a URL that names a watch, e.g. "aurelian-meridian-chronograph"."""


def slugify(text: str) -> str:
    """Return text as a slug: lowercase, with hyphens between its words."""
    return text.lower().replace(" ", "-")
