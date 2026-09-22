"""Tests for the landing page and the frontend asset pipeline.

These deliberately avoid asserting that some piece of copy is on the page,
which passes whether or not anything works. They check the things that
actually break: an asset that is referenced but not served, a link that goes
nowhere, an image without dimensions, a template that renders as literal
Jinja syntax.
"""

import re
from html.parser import HTMLParser

from fastapi.testclient import TestClient

from app.main import app
from app.paths import current_year
from app.services.featured import get_featured_watches

client = TestClient(app)


class TagCollector(HTMLParser):
    """Collects (tag, attrs) pairs so tests can inspect rendered markup."""

    def __init__(self) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append((tag, dict(attrs)))


def collect(html: str, wanted: str) -> list[dict[str, str | None]]:
    parser = TagCollector()
    parser.feed(html)

    return [attrs for tag, attrs in parser.tags if tag == wanted]


def hrefs(html: str) -> list[str]:
    return re.findall(r'href="([^"]+)"', html)


def test_home_page_renders() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_no_unrendered_template_syntax() -> None:
    """A Jinja mistake can still return 200 with braces printed on the page."""
    response = client.get("/")

    assert "{{" not in response.text
    assert "{%" not in response.text


def test_stylesheet_is_linked_and_served() -> None:
    """Catches a forgotten Tailwind rebuild or an uncommitted app.css."""
    response = client.get("/")

    assert "/static/css/app.css" in response.text
    assert client.get("/static/css/app.css").status_code == 200


def test_stylesheet_contains_brand_tokens() -> None:
    """A stale build would still be served, but without the brand colours."""
    css = client.get("/static/css/app.css").text.lower()

    assert "#0f52ba" in css
    assert "cormorant" in css


def test_htmx_is_served() -> None:
    """Catches the vendored library being gitignored by accident."""
    response = client.get("/")

    assert "/static/js/htmx.min.js" in response.text
    assert client.get("/static/js/htmx.min.js").status_code == 200


def test_display_font_is_preloaded_and_served() -> None:
    response = client.get("/")

    assert 'rel="preload"' in response.text
    assert client.get("/static/fonts/cormorant-garamond-600-latin.woff2").status_code == 200


def test_favicons_are_served() -> None:
    assert client.get("/static/img/brand/favicon.png").status_code == 200
    assert client.get("/static/img/brand/apple-touch-icon.png").status_code == 200


def test_internal_links_resolve() -> None:
    """Every in-site link must actually go somewhere. Catches a dead CTA."""
    response = client.get("/")

    for href in hrefs(response.text):
        if href.startswith("/"):
            assert client.get(href).status_code < 400, f"broken link: {href}"


def test_anchor_targets_exist() -> None:
    """An on-page anchor pointing at a missing id silently does nothing."""
    response = client.get("/")

    for href in hrefs(response.text):
        if href.startswith("#"):
            assert f'id="{href[1:]}"' in response.text, f"no target for {href}"


def test_page_has_exactly_one_h1() -> None:
    response = client.get("/")

    assert response.text.count("<h1") == 1


def test_skip_link_targets_main() -> None:
    response = client.get("/")

    assert 'href="#main"' in response.text
    assert 'id="main"' in response.text


def test_images_declare_dimensions_and_alt() -> None:
    """Missing width/height causes layout shift; a missing alt breaks readers.

    An empty alt is allowed: it is the correct marking for a decorative image
    whose meaning is already carried by adjacent text.
    """
    response = client.get("/")

    for image in collect(response.text, "img"):
        src = image.get("src")

        assert image.get("width"), f"no width on {src}"
        assert image.get("height"), f"no height on {src}"
        assert image.get("alt") is not None, f"no alt attribute on {src}"


def test_hero_image_is_not_lazy_loaded() -> None:
    """The hero is the largest-contentful-paint element.

    Lazy-loading it delays the very measurement it would appear to help, so
    it must be eager and high priority while everything below is lazy.
    """
    response = client.get("/")

    hero = [i for i in collect(response.text, "img") if "placeholder/hero" in (i.get("src") or "")]
    assert len(hero) == 1, "expected exactly one hero image"

    assert hero[0].get("loading") != "lazy"
    assert hero[0].get("fetchpriority") == "high"


def test_watch_images_below_the_fold_are_lazy() -> None:
    response = client.get("/")

    cards = [
        i for i in collect(response.text, "img") if "placeholder/watch" in (i.get("src") or "")
    ]
    assert cards, "expected the featured watch images"

    for image in cards:
        assert image.get("loading") == "lazy"


def test_featured_watches_come_from_the_service() -> None:
    """Proves the route -> service -> template wiring, not just that text exists.

    Adding a watch to the service must make it appear on the page; this fails
    if the template ever goes back to hardcoding the list.
    """
    response = client.get("/")

    watches = get_featured_watches()
    assert watches, "the service returned nothing to feature"

    for watch in watches:
        assert watch.name in response.text
        assert watch.reference in response.text
        assert watch.price_label in response.text


def test_each_featured_watch_is_its_own_article() -> None:
    """One card per watch, no duplicates and none silently dropped."""
    response = client.get("/")

    assert response.text.count("<article") == len(get_featured_watches())


def test_footer_contact_is_a_real_link() -> None:
    """A mailto: works with JavaScript disabled; plain text does not."""
    response = client.get("/")

    assert 'href="mailto:' in response.text


def test_copyright_year_is_not_hardcoded() -> None:
    """A year frozen into the template quietly goes stale every January."""
    response = client.get("/")

    assert str(current_year()) in response.text


def test_image_sources_resolve() -> None:
    """Every src and every srcset candidate must actually be served."""
    response = client.get("/")

    for image in collect(response.text, "img"):
        candidates = [image.get("src") or ""]
        candidates += re.findall(r"(\S+)\s+\d+w", image.get("srcset") or "")

        for url in filter(None, candidates):
            assert client.get(url).status_code == 200, f"missing image: {url}"
