"""Pydantic schemas for conversations."""

from __future__ import annotations

from datetime import datetime

from app.schemas.base import SchemaBase


class ConversationBase(SchemaBase):
    """Common conversation fields."""

    title: str
    workspace_id: int | None = None
    summary: str | None = None


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation."""


class ConversationUpdate(SchemaBase):
    """Schema for updating a conversation."""

    title: str | None = None
    summary: str | None = None


class ConversationRead(ConversationBase):
    """Schema returned for a conversation."""

    id: int
    created_at: datetime
    updated_at: datetime
