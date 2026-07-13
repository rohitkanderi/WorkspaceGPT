"""Pydantic schemas for notes."""

from __future__ import annotations

from datetime import datetime

from app.schemas.base import SchemaBase


class NoteBase(SchemaBase):
    """Common note fields."""

    title: str
    body: str
    workspace_id: int | None = None


class NoteCreate(NoteBase):
    """Schema for creating a note."""


class NoteUpdate(SchemaBase):
    """Schema for updating a note."""

    title: str | None = None
    body: str | None = None
    workspace_id: int | None = None


class NoteRead(NoteBase):
    """Schema returned for a note."""

    id: int
    created_at: datetime
    updated_at: datetime
