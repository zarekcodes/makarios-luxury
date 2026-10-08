"""Tests for the landing page and the frontend asset pipeline.

These deliberately avoid asserting that some piece of copy is on the page,
which passes whether or not anything works. They check the things that
actually break: an asset that is referenced but not served, a link that goes
nowhere, an image without dimensions, a template that renders as literal
Jinja syntax.
"""

import re
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.paths import STATIC_DIR, current_year
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


def test_picture_sources_declare_dimensions() -> None:
    """An art-directed <source> has its own shape, so it needs its own size.

    Without width/height on the <source>, the browser reserves space using the
    <img>'s portrait shape and then jumps when the landscape crop arrives.
    """
    response = client.get("/")

    for source in collect(response.text, "source"):
        assert source.get("width"), f"no width on <source media={source.get('media')}>"
        assert source.get("height"), f"no height on <source media={source.get('media')}>"


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


def test_hero_is_art_directed() -> None:
    """Landscape screens get a wide crop; everything else falls back to portrait.

    The fallback matters: a browser that matches no <source> still shows the
    <img>, so the portrait crop must be the one on the <img> itself.
    """
    response = client.get("/")

    sources = [
        s for s in collect(response.text, "source") if "hero-wide" in (s.get("srcset") or "")
    ]
    assert len(sources) == 1, "expected one landscape <source> for the hero"
    assert "landscape" in (sources[0].get("media") or "")

    hero = [i for i in collect(response.text, "img") if "hero-portrait" in (i.get("src") or "")]
    assert len(hero) == 1, "the hero <img> should carry the portrait crop"


def test_hero_images_fit_the_performance_budget() -> None:
    """The hero is the largest-contentful-paint image, so its weight is the page's speed.

    The ceiling is generous for today's stand-ins (about 50 KB at most) and is
    there to catch the day a real photo is dropped in unoptimised: a phone
    straight off a camera easily produces several megabytes.
    """
    budget = 150_000
    variants = sorted((STATIC_DIR / "img" / "placeholder").glob("hero-*.webp"))
    assert variants, "no hero images found"

    for path in variants:
        size = path.stat().st_size
        assert size <= budget, f"{path.name} is {size:,} bytes, over the {budget:,} budget"


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
        assert watch.box_papers in response.text


def test_every_featured_watch_has_an_inquiry_link() -> None:
    """Each card's Inquire link must name its own watch.

    Decoded rather than string-matched, so this checks what a mail app will
    actually show in the subject line, not how the URL happens to be escaped.
    """
    response = client.get("/")

    subjects = []
    for href in hrefs(response.text):
        if href.startswith(f"mailto:{get_settings().contact_email}?"):
            subjects += parse_qs(urlsplit(href).query).get("subject", [])

    for watch in get_featured_watches():
        assert any(watch.reference in subject for subject in subjects), (
            f"no inquiry link for {watch.name} ({watch.reference})"
        )


def test_each_featured_watch_is_its_own_article() -> None:
    """One card per watch, no duplicates and none silently dropped."""
    response = client.get("/")

    assert response.text.count("<article") == len(get_featured_watches())


def test_navigation_works_without_javascript() -> None:
    """The mobile menu must be a native disclosure, not a scripted one.

    The links have to be in the HTML the server sent, not injected later,
    and the toggle has to be the <details> element that browsers open on
    their own.
    """
    response = client.get("/")

    assert "<details" in response.text
    assert "<summary" in response.text

    for href in ("#featured", "#trust", "#contact"):
        assert f'href="{href}"' in response.text


def test_summary_has_no_hand_written_aria_expanded() -> None:
    """A static aria-expanded can never be updated, so it would always lie.

    Browsers report a disclosure's state natively; writing the attribute by
    hand is the usual way this pattern gets broken.
    """
    response = client.get("/")

    summary_markup = response.text.split("<summary", 1)[1].split(">", 1)[0]

    assert "aria-expanded" not in summary_markup


def test_footer_contact_is_a_real_link() -> None:
    """A mailto: works with JavaScript disabled; plain text does not."""
    response = client.get("/")

    assert 'href="mailto:makarioslux@gmail.com"' in response.text


def test_instagram_profile_is_linked() -> None:
    """The link is asserted, not fetched: tests must not depend on network."""
    response = client.get("/")

    assert 'href="https://www.instagram.com/makariosluxury"' in response.text


def test_instagram_direct_message_is_linked() -> None:
    """The contact band's second call to action opens a DM, not the profile."""
    response = client.get("/")

    assert 'href="https://ig.me/m/makariosluxury"' in response.text


def test_no_placeholder_links() -> None:
    """href="#" is a link that goes nowhere, and it is easy to leave behind."""
    response = client.get("/")

    assert 'href="#"' not in response.text


def test_copyright_year_is_not_hardcoded() -> None:
    """A year frozen into the template quietly goes stale every January."""
    response = client.get("/")

    assert str(current_year()) in response.text


def test_image_sources_resolve() -> None:
    """Every src and every srcset candidate must actually be served.

    That includes the <source> elements inside a <picture>, which only one
    screen shape ever requests, so a missing file there is easy to miss.
    """
    response = client.get("/")

    for image in collect(response.text, "img") + collect(response.text, "source"):
        candidates = [image.get("src") or ""]
        candidates += re.findall(r"(\S+)\s+\d+w", image.get("srcset") or "")

        for url in filter(None, candidates):
            assert client.get(url).status_code == 200, f"missing image: {url}"
