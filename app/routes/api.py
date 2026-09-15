"""JSON routes, mounted under /api. For health checks and any non-browser clients."""

from fastapi import APIRouter

router = APIRouter(tags=["api"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
