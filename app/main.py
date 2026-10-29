from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware

from app.config import get_settings
from app.paths import STATIC_DIR
from app.routes import api, pages


def create_app() -> FastAPI:
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

    return app


app = create_app()
