"""MCP management routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.mcp.client import MCPClientError
from app.schemas import (
    MCPServerConfigCreate,
    MCPServerRead,
    MCPToolCallRequest,
    MCPToolCallResponse,
    MCPToolRead,
)
from app.services import MCPService, get_mcp_service

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.post("/servers", response_model=MCPServerRead, status_code=status.HTTP_201_CREATED)
async def add_server(
    request: MCPServerConfigCreate,
    service: MCPService = Depends(get_mcp_service),
) -> MCPServerRead:
    """Register, connect, and discover tools from a new MCP server."""
    from app.mcp.client import MCPServerConfig

    try:
        await service.add_server(MCPServerConfig(**request.model_dump()))
        await service.connect(request.name)
        await service.discover_tools(request.name)
    except MCPClientError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    server = next(server for server in service.list_servers() if server.name == request.name)
    return MCPServerRead.model_validate(server)


@router.get("/servers", response_model=list[MCPServerRead])
def list_servers(service: MCPService = Depends(get_mcp_service)) -> list[MCPServerRead]:
    """Return configured MCP servers and their current status."""
    return [MCPServerRead.model_validate(server) for server in service.list_servers()]


@router.post("/servers/connect", status_code=status.HTTP_204_NO_CONTENT)
async def connect_servers(
    server_name: str | None = Query(default=None),
    service: MCPService = Depends(get_mcp_service),
) -> None:
    """Connect one MCP server, or all configured servers when omitted."""
    try:
        await service.connect(server_name)
    except MCPClientError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/servers/disconnect", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_servers(
    server_name: str | None = Query(default=None),
    service: MCPService = Depends(get_mcp_service),
) -> None:
    """Disconnect one MCP server, or all configured servers when omitted."""
    try:
        await service.disconnect(server_name)
    except MCPClientError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/tools/discover", response_model=list[MCPToolRead])
async def discover_tools(
    server_name: str | None = Query(default=None),
    service: MCPService = Depends(get_mcp_service),
) -> list[MCPToolRead]:
    """Connect as needed and refresh MCP tool metadata."""
    try:
        tools = await service.discover_tools(server_name)
    except MCPClientError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [MCPToolRead.model_validate(tool) for tool in tools]


@router.get("/tools", response_model=list[MCPToolRead])
def list_tools(
    server_name: str | None = Query(default=None),
    service: MCPService = Depends(get_mcp_service),
) -> list[MCPToolRead]:
    """Return cached MCP tool metadata."""
    try:
        tools = service.list_tools(server_name)
    except MCPClientError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [MCPToolRead.model_validate(tool) for tool in tools]


@router.post("/tools/call", response_model=MCPToolCallResponse)
async def call_tool(
    request: MCPToolCallRequest,
    service: MCPService = Depends(get_mcp_service),
) -> MCPToolCallResponse:
    """Invoke an MCP tool and return its serialized result."""
    try:
        result = await service.call_tool(
            request.tool_name,
            request.arguments,
            server_name=request.server_name,
        )
    except MCPClientError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return MCPToolCallResponse(
        tool_name=request.tool_name,
        server_name=request.server_name,
        result=result,
    )
