"""Service wrapper around the MCP client."""

from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.mcp.client import MCPClient, MCPServerInfo, MCPToolInfo


class MCPService:
    """Coordinate MCP server connections for API routes."""

    def __init__(self) -> None:
        config_source = settings.resolved_mcp_server_config or None
        self._client = MCPClient(config_source=config_source)

    async def connect(self, server_name: str | None = None) -> None:
        """Connect to one configured server or all configured servers."""
        await self._client.connect(server_name)

    async def disconnect(self, server_name: str | None = None) -> None:
        """Disconnect one configured server or all configured servers."""
        await self._client.disconnect(server_name)

    async def discover_tools(self, server_name: str | None = None) -> list[MCPToolInfo]:
        """Refresh and return tool metadata."""
        return await self._client.discover_tools(server_name)

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        *,
        server_name: str | None = None,
    ) -> dict[str, Any]:
        """Invoke a tool through the managed MCP client."""
        return await self._client.call_tool(
            tool_name,
            arguments=arguments,
            server_name=server_name,
        )

    def list_servers(self) -> list[MCPServerInfo]:
        """Return current server status."""
        return self._client.list_servers()

    def list_tools(self, server_name: str | None = None) -> list[MCPToolInfo]:
        """Return cached tool metadata."""
        return self._client.list_tools(server_name)


_mcp_service: MCPService | None = None


def get_mcp_service() -> MCPService:
    """Return the process-wide MCP service."""
    global _mcp_service
    if _mcp_service is None:
        _mcp_service = MCPService()
    return _mcp_service
