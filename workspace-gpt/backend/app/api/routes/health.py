"""Health check routes."""

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return basic process health."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
    }
