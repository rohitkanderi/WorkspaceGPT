"""SQLAlchemy declarative base for ORM models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


def import_models() -> None:
    """Import ORM models so metadata is populated before table creation."""
    import app.models  # noqa: F401
