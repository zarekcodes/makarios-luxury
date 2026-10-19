"""Unit tests for slugify(), which turns a watch's name into the slug in its URL.

Written test-first: each test came before the code that makes it pass.
"""

from app.services.slugs import slugify


def test_slug_is_lowercase_words_joined_by_hyphens() -> None:
    """The simplest name: plain words with a single space between them."""
    assert slugify("Aurelian Meridian Chronograph") == "aurelian-meridian-chronograph"


def test_punctuation_between_words_becomes_one_hyphen() -> None:
    """A lone mark, or a run of marks and spaces, turns into a single hyphen."""
    assert slugify("Patek Philippe Nautilus 5711/1A") == "patek-philippe-nautilus-5711-1a"
    assert slugify("Cartier Tank Louis, Large Model") == "cartier-tank-louis-large-model"


def test_accented_letters_keep_their_base_letter() -> None:
    """An accent falls away ("ö" to "o", "é" to "e") instead of splitting the word."""
    assert slugify("A. Lange & Söhne Datograph") == "a-lange-sohne-datograph"
    assert slugify("Montblanc Héritage Chronométrie") == "montblanc-heritage-chronometrie"
