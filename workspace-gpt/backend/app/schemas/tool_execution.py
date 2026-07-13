"""Pydantic schemas for MCP tool execution history."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.base import SchemaBase


class ToolExecutionCreate(SchemaBase):
    """Schema for recording an MCP tool call."""

    server_name: str
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    conversation_id: int | None = None


class ToolExecutionRead(ToolExecutionCreate):
    """Schema returned for an MCP tool execution."""

    id: int
    result: dict[str, Any] | None = None
    is_error: bool = False
    error_message: str | None = None
    created_at: datetime
