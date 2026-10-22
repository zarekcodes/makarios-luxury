"""Unit tests for slugify(), which turns a watch's name into the slug in its URL.

Written test-first: each test came before the code that makes it pass.
"""

from app.services.slugs import slugify, unique_slug


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


def test_no_hyphen_at_either_end() -> None:
    """Punctuation at the start or end of a name leaves no stray hyphen behind."""
    assert slugify("Rolex Daytona (Paul Newman)") == "rolex-daytona-paul-newman"
    assert slugify('"Snowflake" Grand Seiko') == "snowflake-grand-seiko"


def test_a_taken_slug_gets_the_next_free_number() -> None:
    """Two watches of the same model need different URLs, so a repeat is numbered from 2."""
    assert unique_slug("rolex-submariner", taken=set()) == "rolex-submariner"
    assert unique_slug("rolex-submariner", taken={"rolex-submariner"}) == "rolex-submariner-2"
    taken = {"rolex-submariner", "rolex-submariner-2"}
    assert unique_slug("rolex-submariner", taken=taken) == "rolex-submariner-3"
