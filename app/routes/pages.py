"""HTML page routes. These render Jinja templates; HTMX requests return partials."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.config import Settings, get_settings
from app.db import SessionDep
from app.paths import templates
from app.services.featured import get_featured_watches

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
def catalog(request: Request, settings: SettingsDep) -> HTMLResponse:
    """The catalog listing (#25), built behind a feature flag until it ships.

    With MAKARIOS_CATALOG_PAGE_ENABLED off, which is the default and what
    production runs, the page answers exactly like a URL that doesn't exist.
    """
    if not settings.catalog_page_enabled:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(request, "pages/catalog.html")
