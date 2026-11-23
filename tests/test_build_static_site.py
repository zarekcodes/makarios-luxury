"""scripts/build_static_site.py: the storefront as static files, for the S3 deploy."""

import importlib.util
import json
import re
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "build_static_site.py"
spec = importlib.util.spec_from_file_location("build_static_site", SCRIPT)
assert spec is not None and spec.loader is not None
site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site)

COMMIT = "0123456789abcdef0123456789abcdef01234567"


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    site.build(out, "blue", COMMIT)
    return out


def test_each_page_and_the_static_files_are_written(built: Path) -> None:
    assert (built / "index.html").is_file()
    assert (built / "watches" / "index.html").is_file()
    assert (built / "static" / "css" / "app.css").is_file()
    assert (built / "static" / "js" / "htmx.min.js").is_file()


def test_tailwinds_source_is_not_shipped(built: Path) -> None:
    assert not (built / "static" / "css" / "input.css").exists()


def test_the_pages_hold_the_placeholder_watches(built: Path) -> None:
    assert "Aurelian Meridian Chronograph" in (built / "watches" / "index.html").read_text()


@pytest.mark.parametrize("page", ["index.html", "watches/index.html", "static/css/app.css"])
def test_no_link_points_at_the_bucket_root_or_the_build_host(built: Path, page: str) -> None:
    """Under <folder>/blue/, "/static/..." would resolve to the bucket's root."""
    text = (built / page).read_text()

    assert not re.search(r'(?:href|src|action)="/|url\(/', text)
    assert site.BUILD_HOST not in text


def test_every_relative_link_resolves_to_a_file_in_the_build(built: Path) -> None:
    for page in ("index.html", "watches/index.html"):
        html = (built / page).read_text()
        urls = re.findall(r'(?:href|src)="([^"]*)"', html)
        urls += [
            candidate.split()[0]
            for value in re.findall(r'srcset="([^"]*)"', html)
            for candidate in value.split(",")
        ]
        # Only links within the build: not mailto:, https: or an anchor on the same page.
        for url in (u.partition("#")[0] for u in urls if ":" not in u):
            if url:
                assert ((built / page).parent / url).resolve().is_file(), f"{page}: {url}"


def test_the_stylesheets_font_resolves_from_the_css_folder(built: Path) -> None:
    css = built / "static" / "css" / "app.css"
    (font,) = re.findall(r"url\(([^)]+)\)", css.read_text())

    assert (css.parent / font).resolve().is_file()


def test_each_page_names_its_slot_and_commit(built: Path) -> None:
    html = (built / "index.html").read_text()

    assert 'data-build="blue"' in html
    assert "Build: blue · 0123456" in html


def test_the_copy_is_kept_out_of_search_results(built: Path) -> None:
    assert '<meta name="robots" content="noindex">' in (built / "index.html").read_text()


def test_version_json_records_the_slot_and_commit(built: Path) -> None:
    version = json.loads((built / "version.json").read_text())

    assert version["color"] == "blue"
    assert version["commit"] == COMMIT
    assert version["built_at"]


def test_the_detail_page_is_left_to_the_flag_not_baked_in(built: Path) -> None:
    assert not (built / "watches" / "aurelian-meridian-chronograph").exists()


def test_a_rebuild_replaces_the_previous_one(tmp_path: Path) -> None:
    stale = tmp_path / "left-over.html"
    stale.write_text("old")

    site.build(tmp_path, "green", COMMIT)

    assert not stale.exists()
    assert json.loads((tmp_path / "version.json").read_text())["color"] == "green"


def test_an_unknown_slot_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="color"):
        site.build(tmp_path / "dist", "purple", COMMIT)


def test_a_link_to_a_page_outside_the_build_fails_it() -> None:
    with pytest.raises(site.BrokenLinkError, match="/about"):
        site.relative_links('<a href="/about">About</a>', depth=0)


@pytest.mark.parametrize(
    ("html", "depth", "expected"),
    [
        ('<a href="/">', 0, '<a href="index.html">'),
        ('<a href="/#contact">', 1, '<a href="../index.html#contact">'),
        ('<a href="/watches">', 1, '<a href="../watches/index.html">'),
        ('<img src="/static/a.webp">', 1, '<img src="../static/a.webp">'),
        (
            'srcset="/static/a-400.webp 400w, /static/a-800.webp 800w"',
            0,
            'srcset="static/a-400.webp 400w, static/a-800.webp 800w"',
        ),
        ('<a href="mailto:a@b.c">', 1, '<a href="mailto:a@b.c">'),
        ('<a href="#main">', 1, '<a href="#main">'),
    ],
)
def test_root_relative_links_become_relative(html: str, depth: int, expected: str) -> None:
    assert site.relative_links(html, depth) == expected
