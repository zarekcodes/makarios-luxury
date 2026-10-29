import logging
from collections.abc import Callable

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.middleware.gzip import GZipMiddleware

from app.admin import mount_admin
from app.config import get_settings
from app.db import SessionLocal
from app.paths import STATIC_DIR
from app.routes import api, pages

# The app's own log lines (admin logins and changes) at INFO. The server only
# sets up its own loggers, so without this they'd be dropped as below WARNING.
logging.basicConfig(format="%(levelname)s:     %(name)s %(message)s")
logging.getLogger("makarios").setLevel(logging.INFO)


def create_app(session_maker: Callable[[], Session] = SessionLocal) -> FastAPI:
    """Build the app. Tests pass a session_maker bound to their own database."""
    settings = get_settings()
    # The interactive API docs describe only /api/health, and in production
    # they'd be one more public page with nothing for a buyer on it.
    docs = not settings.is_production
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
    )

    # Railway's proxy passes responses through uncompressed, so the app
    # compresses them itself. HTML, CSS and htmx shrink to about a quarter of
    # their size, which a phone on a slow connection feels directly. Responses
    # under 1 KB aren't worth the CPU.
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.include_router(pages.router)
    app.include_router(api.router, prefix="/api")
    mount_admin(app, settings, session_maker)

    return app


app = create_app()
