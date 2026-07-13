"""Top-level API router."""

from fastapi import APIRouter

from app.api.routes import health, mcp

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(mcp.router)
