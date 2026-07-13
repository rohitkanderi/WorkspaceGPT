"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.core.config import settings
from app.database.base import Base, import_models
from app.database.engine import engine

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_PROJECT_ROOT = _BACKEND_ROOT.parent
_FRONTEND_ROOT = _PROJECT_ROOT / "frontend"
_FRONTEND_SRC = _FRONTEND_ROOT / "src"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize lightweight local resources for development."""
    import_models()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    if _FRONTEND_SRC.is_dir():
        app.mount("/assets", StaticFiles(directory=_FRONTEND_SRC), name="assets")

    @app.get("/", include_in_schema=False, response_model=None)
    async def frontend() -> FileResponse | dict[str, str]:
        index_path = _FRONTEND_ROOT / "index.html"
        if index_path.is_file():
            return FileResponse(index_path)
        return {"message": "WorkspaceGPT API is running"}

    return app


app = create_app()
