"""Async SQLAlchemy engine configuration."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import settings

_engine: AsyncEngine | None = None


def _normalize_database_url(url: str) -> str:
    """Ensure the database URL uses an async-compatible driver."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


def get_engine() -> AsyncEngine:
    """Return the shared async database engine, creating it on first use."""
    global _engine
    if _engine is None:
        database_url = _normalize_database_url(settings.database_url)
        _engine = create_async_engine(database_url, echo=False)
    return _engine


engine = get_engine()
