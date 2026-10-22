"""HTML page routes. These render Jinja templates; HTMX requests return partials."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.db import SessionDep
from app.paths import templates
from app.services.featured import get_featured_watches

router = APIRouter(include_in_schema=False)


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
