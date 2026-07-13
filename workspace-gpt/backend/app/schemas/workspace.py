"""Pydantic schemas for workspaces."""

from __future__ import annotations

from datetime import datetime

from app.schemas.base import SchemaBase


class WorkspaceBase(SchemaBase):
    """Common workspace fields."""

    name: str
    root_path: str
    description: str | None = None


class WorkspaceCreate(WorkspaceBase):
    """Schema for creating a workspace."""


class WorkspaceUpdate(SchemaBase):
    """Schema for updating a workspace."""

    name: str | None = None
    root_path: str | None = None
    description: str | None = None


class WorkspaceRead(WorkspaceBase):
    """Schema returned for a workspace."""

    id: int
    created_at: datetime
    updated_at: datetime
