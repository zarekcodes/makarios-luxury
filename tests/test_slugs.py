"""Unit tests for slugify(), which turns a watch's name into the slug in its URL.

Written test-first: each test came before the code that makes it pass.
"""

from app.services.slugs import slugify


def test_slug_is_lowercase_words_joined_by_hyphens() -> None:
    """The simplest name: plain words with a single space between them."""
    assert slugify("Aurelian Meridian Chronograph") == "aurelian-meridian-chronograph"
