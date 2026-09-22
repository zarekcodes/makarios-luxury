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


def test_image_sources_resolve() -> None:
    """Every src and every srcset candidate must actually be served."""
    response = client.get("/")

    for image in collect(response.text, "img"):
        candidates = [image.get("src") or ""]
        candidates += re.findall(r"(\S+)\s+\d+w", image.get("srcset") or "")

        for url in filter(None, candidates):
            assert client.get(url).status_code == 200, f"missing image: {url}"
