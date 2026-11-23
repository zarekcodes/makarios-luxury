"""Render the storefront into static files, the build output the S3 deploy uploads.

    uv run python scripts/build_static_site.py --color blue --out dist

The site is server-rendered by FastAPI, which S3 can't run, so this renders
the pages S3 can serve as plain files: the landing page and the catalog, with
the placeholder watches, and everything under app/static. Each page is
fetched through the real app (the same templates, routes and services a
buyer gets), against a throwaway in-memory database, then rewritten so it
works from wherever it's uploaded:

- Links become relative. S3 serves the build under a prefix such as
  <your folder>/blue/, so "/static/css/app.css" or "/watches" would point at
  the bucket's root. Every root-relative link must name a page in PAGES or a
  file under /static, or the build fails, rather than upload a broken link.
- A ribbon at the foot of each page names the slot and commit, so a
  screenshot shows which build is live.
- noindex, so a copy of the site in a class bucket never competes with the
  real one in search results.

The watch detail page isn't rendered. Whether it's visible is a release
decision, made at request time by the flags file (app/services/flags.py);
baking it into a deploy would tie the release back to the deploy.

version.json, at the root of the build, records the slot, commit and time.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db import create_db_engine, get_session  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402
from app.paths import STATIC_DIR  # noqa: E402
from app.seed import seed  # noqa: E402

COLORS = ("blue", "green")

# The path each page is served at by the app, and the file it becomes.
PAGES = {
    "/": "index.html",
    "/watches": "watches/index.html",
}

# url_for() builds absolute URLs from the request's host, so pages are fetched
# from a host that appears nowhere else, then stripped back to paths.
BUILD_HOST = "http://static.build"

# Tailwind's source, not served.
NOT_SHIPPED = shutil.ignore_patterns("input.css")

# A root-relative URL in an attribute or a CSS url(): "/watches", "/#contact".
ROOT_RELATIVE = re.compile(r'(?P<lead>(?:href|src|action)="|url\()(?P<url>/[^"\s)]*)')
SRCSET = re.compile(r'srcset="(?P<value>[^"]*)"')


class BrokenLinkError(Exception):
    """A page links to a root-relative path the static build doesn't contain."""


def build(out: Path, color: str, commit: str) -> dict[str, str]:
    """Write the static site for one slot into out, replacing what was there."""
    if color not in COLORS:
        raise ValueError(f"color must be one of {COLORS}, not {color!r}")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    pages = render_pages()
    for path, filename in PAGES.items():
        target = out / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        html = relative_links(pages[path], depth=filename.count("/"))
        target.write_text(stamp(html, color, commit))

    shutil.copytree(STATIC_DIR, out / "static", ignore=NOT_SHIPPED)
    # The stylesheet's font url() is root-relative too, and lives two levels down.
    css = out / "static" / "css" / "app.css"
    css.write_text(relative_links(css.read_text(), depth=2))

    version = {
        "color": color,
        "commit": commit,
        "built_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    (out / "version.json").write_text(json.dumps(version, indent=2) + "\n")
    return version


def render_pages() -> dict[str, str]:
    """Every page in PAGES, fetched through the app against the placeholder watches."""
    engine = create_db_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        seed(session)
        app.dependency_overrides[get_session] = lambda: session
        try:
            client = TestClient(app, base_url=BUILD_HOST)
            pages = {}
            for path in PAGES:
                response = client.get(path)
                response.raise_for_status()
                pages[path] = response.text.replace(BUILD_HOST, "")
        finally:
            app.dependency_overrides.pop(get_session, None)
    engine.dispose()
    return pages


def relative_links(text: str, depth: int) -> str:
    """Rewrite every root-relative URL so it works from a file depth folders down."""
    up = "../" * depth

    def rewrite(url: str) -> str:
        path, hash_mark, fragment = url.partition("#")
        if path.startswith("/static/"):
            target = path.removeprefix("/")
        elif path in PAGES:
            target = PAGES[path]
        else:
            raise BrokenLinkError(f"{url!r} isn't in the static build; add it to PAGES")
        return up + target + hash_mark + fragment

    text = ROOT_RELATIVE.sub(lambda m: m["lead"] + rewrite(m["url"]), text)
    return SRCSET.sub(
        lambda m: (
            'srcset="'
            + ", ".join(
                rewrite(candidate) if candidate.startswith("/") else candidate
                for candidate in (part.strip() for part in m["value"].split(","))
            )
            + '"'
        ),
        text,
    )


def stamp(html: str, color: str, commit: str) -> str:
    """Mark the page as this slot's build, and keep it out of search results."""
    ribbon = (
        f'<p data-build="{color}" style="margin:0;padding:.5rem;text-align:center;'
        f"font:600 .8rem/1.4 system-ui,sans-serif;color:#fff;"
        f'background:{"#1d4ed8" if color == "blue" else "#15803d"}">'
        f"Build: {color} · {commit[:7]}</p>"
    )
    html = html.replace("<head>", '<head>\n  <meta name="robots" content="noindex">', 1)
    return html.replace("</body>", f"{ribbon}\n</body>", 1)


def current_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--color", choices=COLORS, required=True, help="the slot to build for")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "dist")
    parser.add_argument("--commit", help="the commit to stamp (default: the checkout's HEAD)")
    args = parser.parse_args(argv)
    version = build(args.out, args.color, args.commit or current_commit())
    print(f"Built {version['color']} ({version['commit'][:7]}) into {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
