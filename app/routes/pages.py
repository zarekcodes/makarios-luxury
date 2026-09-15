"""HTML page routes. These render Jinja templates; HTMX requests return partials."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.paths import templates

router = APIRouter(include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "pages/home.html")
