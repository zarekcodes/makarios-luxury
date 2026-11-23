"""HTML page routes. These render Jinja templates.

No route returns an htmx partial yet. When the first one does (the catalog filters, #26), it
answers a request carrying the HX-Request header with the fragment from templates/partials/.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.config import Settings, get_settings
from app.db import SessionDep
from app.paths import templates
from app.services.catalog import get_catalog_watches, get_watch_by_slug
from app.services.featured import get_featured_watches
from app.services.flags import FlagsDep

router = APIRouter(include_in_schema=False)

# Settings as a dependency rather than a call to get_settings() inside the
# route, so a test can hand a route its own settings (a feature flag on or off)
# through app.dependency_overrides, the way tests already swap the database.
SettingsDep = Annotated[Settings, Depends(get_settings)]


# A plain `def`, not `async def`: the database calls block while they wait,
# and FastAPI runs a plain `def` on a thread pool so other requests carry on
# meanwhile. Inside an `async def` they would stall the whole server.
@router.get("/", response_class=HTMLResponse)
def home(request: Request, session: SessionDep) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "pages/home.html",
        {"watches": get_featured_watches(session)},
    )


@router.get("/watches", response_class=HTMLResponse)
def catalog(request: Request, session: SessionDep) -> HTMLResponse:
    """The catalog listing (#25): every watch that isn't sold."""
    return templates.TemplateResponse(
        request,
        "pages/catalog.html",
        {"watches": get_catalog_watches(session)},
    )


@router.get("/watches/{slug}", response_class=HTMLResponse)
def watch_detail(
    request: Request, slug: str, session: SessionDep, settings: SettingsDep, flags: FlagsDep
) -> HTMLResponse:
    """The watch detail page (#27), built behind a feature flag until it ships.

    With the flag off, which is the default and what production runs, the
    page answers exactly like a URL that doesn't exist. With it on, an unknown
    slug is a 404 too. "watch_detail_page" in the flags file, when there is
    one, overrides MAKARIOS_WATCH_DETAIL_PAGE_ENABLED and flips without a restart.
    """
    if not flags.is_enabled("watch_detail_page", default=settings.watch_detail_page_enabled):
        raise HTTPException(status_code=404)
    watch = get_watch_by_slug(session, slug)
    if watch is None:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(request, "pages/watch_detail.html", {"watch": watch})
