"""Pydantic v2 schemas for MCP-related application models."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import Field

from app.schemas.base import SchemaBase

TransportType = Literal["stdio", "sse", "streamable-http"]
ServerStatusValue = Literal["connected", "connecting", "disconnected", "error"]


class MCPServerConfigBase(SchemaBase):
    """Shared fields for configuring an MCP server."""

    name: str
    transport: TransportType
    enabled: bool = True


class MCPServerConfigCreate(MCPServerConfigBase):
    """Schema for registering or loading an MCP server config."""

    command: Optional[str] = None
    args: List[str] = Field(default_factory=list)
    env: Optional[Dict[str, str]] = None
    url: Optional[str] = None


class MCPServerConfigRead(MCPServerConfigCreate):
    """Schema returned for an MCP server config."""


class MCPToolRead(SchemaBase):
    """Schema returned for a discovered MCP tool."""

    name: str
    server_name: str
    description: Optional[str] = None
    input_schema: Dict[str, Any] = Field(default_factory=dict)


class MCPServerRead(SchemaBase):
    """Schema returned for a managed MCP server."""

    name: str
    transport: str
    status: ServerStatusValue
    tool_count: int
    last_error: Optional[str] = None


class MCPToolCallRequest(SchemaBase):
    """Schema for invoking an MCP tool."""

    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    server_name: Optional[str] = None


class MCPToolCallResponse(SchemaBase):
    """Schema returned after invoking an MCP tool."""

    tool_name: str
    server_name: Optional[str] = None
    result: Any
