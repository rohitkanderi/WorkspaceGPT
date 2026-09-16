"""MCP client for connecting to multiple servers and invoking tools."""

from __future__ import annotations

import json
import logging
import os
import sys
import asyncio
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

TransportType = Literal["stdio", "sse", "streamable-http"]


class MCPClientError(Exception):
    """Base error for MCP client operations."""


class MCPConnectionError(MCPClientError):
    """Raised when connecting to or reconnecting with an MCP server fails."""


class MCPServerNotFoundError(MCPClientError):
    """Raised when a requested MCP server is not configured or known."""


class MCPToolNotFoundError(MCPClientError):
    """Raised when a requested tool cannot be found on any connected server."""


class MCPToolCallError(MCPClientError):
    """Raised when invoking a tool fails after retries."""


class ServerStatus(StrEnum):
    """Connection state for an MCP server."""

    CONNECTED = "connected"
    CONNECTING = "connecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server."""

    name: str
    transport: TransportType
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] | None = None
    url: str | None = None
    enabled: bool = True


@dataclass(frozen=True)
class MCPToolInfo:
    """Cached metadata for a discovered MCP tool."""

    name: str
    server_name: str
    description: str | None
    input_schema: dict[str, Any]


@dataclass(frozen=True)
class MCPServerInfo:
    """Summary information about a managed MCP server."""

    name: str
    transport: str
    status: ServerStatus
    tool_count: int
    last_error: str | None


@dataclass
class _ServerConnection:
    """Internal connection state for one MCP server."""

    config: MCPServerConfig
    status: ServerStatus = ServerStatus.DISCONNECTED
    last_error: str | None = None
    exit_stack: AsyncExitStack | None = None
    session: ClientSession | None = None
    tools: dict[str, types.Tool] = field(default_factory=dict)


def load_server_configs(config_source: str | None = None) -> list[MCPServerConfig]:
    """Load MCP server definitions from a JSON file path or JSON string.

    The source may be a file path, a JSON array of server objects, or an object
    with a top-level ``servers`` array. When omitted, ``MCP_SERVER_CONFIG`` is used.
    """
    raw = (config_source or os.environ.get("MCP_SERVER_CONFIG", "")).strip()
    if not raw:
        return []

    data = _load_json_config(raw)
    servers = data.get("servers", data) if isinstance(data, dict) else data
    if not isinstance(servers, list):
        raise MCPClientError("MCP server config must be a list or contain a 'servers' array")

    configs: list[MCPServerConfig] = []
    for entry in servers:
        try:
            configs.append(MCPServerConfig.model_validate(entry))
        except ValidationError as exc:
            raise MCPClientError(f"Invalid MCP server config entry: {exc}") from exc
    return [config for config in configs if config.enabled]


def _load_json_config(raw: str) -> Any:
    """Parse MCP config from a file path or inline JSON."""
    path = Path(raw)
    if path.is_file():
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MCPClientError(
            "MCP_SERVER_CONFIG must be a valid JSON string or path to a JSON file"
        ) from exc


class MCPClient:
    """Connect to multiple MCP servers, discover tools, and invoke them."""

    def __init__(
        self,
        config_source: str | list[MCPServerConfig] | None = None,
        *,
        max_retries: int = 2,
    ) -> None:
        """Create a client from a config source or explicit server definitions."""
        if isinstance(config_source, list):
            self._configs = {config.name: config for config in config_source if config.enabled}
        else:
            self._configs = {
                config.name: config for config in load_server_configs(config_source)
            }
        self._connections: dict[str, _ServerConnection] = {
            name: _ServerConnection(config=config)
            for name, config in self._configs.items()
        }
        self._max_retries = max_retries

    async def connect(self, server_name: str | None = None) -> None:
        """Connect to one server or all configured servers."""
        targets = self._resolve_server_names(server_name)
        errors: list[str] = []

        for name in targets:
            try:
                await self._connect_server(name)
            except MCPConnectionError as exc:
                errors.append(str(exc))
                logger.warning("Failed to connect to MCP server '%s': %s", name, exc)

        if errors and (server_name is not None or len(errors) == len(targets)):
            raise MCPConnectionError("; ".join(errors))

    async def add_server(self, config: MCPServerConfig) -> None:
        """Register or replace a server definition for this process."""
        if config.name in self._connections:
            await self._disconnect_server(config.name)
        self._configs[config.name] = config
        self._connections[config.name] = _ServerConnection(config=config)

    async def disconnect(self, server_name: str | None = None) -> None:
        """Disconnect from one server or all connected servers."""
        targets = list(self._resolve_server_names(server_name))
        for name in targets:
            await self._disconnect_server(name)

    async def discover_tools(self, server_name: str | None = None) -> list[MCPToolInfo]:
        """Discover tools from connected servers and refresh the local cache."""
        targets = self._resolve_server_names(server_name)
        discovered: list[MCPToolInfo] = []

        for name in targets:
            connection = self._get_connection(name)
            if connection.status != ServerStatus.CONNECTED:
                await self._connect_server(name)
            discovered.extend(await self._discover_tools_for_server(connection))

        return discovered

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        *,
        server_name: str | None = None,
    ) -> dict[str, Any]:
        """Invoke a tool, optionally scoped to a specific server."""
        resolved_server, connection = self._resolve_tool(tool_name, server_name)
        payload = arguments or {}
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                await self._ensure_connected(resolved_server, connection)
                assert connection.session is not None
                result = await connection.session.call_tool(tool_name, arguments=payload)
                return _format_tool_result(result)
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Tool call failed for '%s' on '%s' (attempt %s): %s",
                    tool_name,
                    resolved_server,
                    attempt + 1,
                    exc,
                )
                connection.status = ServerStatus.ERROR
                connection.last_error = str(exc)
                if attempt < self._max_retries:
                    await self._reconnect_server(resolved_server)

        raise MCPToolCallError(
            f"Tool '{tool_name}' failed on server '{resolved_server}'"
        ) from last_error

    def list_servers(self) -> list[MCPServerInfo]:
        """Return status summaries for all configured servers."""
        servers: list[MCPServerInfo] = []
        for name, connection in self._connections.items():
            servers.append(
                MCPServerInfo(
                    name=name,
                    transport=connection.config.transport,
                    status=connection.status,
                    tool_count=len(connection.tools),
                    last_error=connection.last_error,
                )
            )
        return servers

    def list_tools(self, server_name: str | None = None) -> list[MCPToolInfo]:
        """Return cached tools for one server or all servers."""
        if server_name is not None:
            connection = self._get_connection(server_name)
            return [_tool_info(connection.config.name, tool) for tool in connection.tools.values()]

        tools: list[MCPToolInfo] = []
        for connection in self._connections.values():
            tools.extend(
                _tool_info(connection.config.name, tool) for tool in connection.tools.values()
            )
        return tools

    def _resolve_server_names(self, server_name: str | None) -> list[str]:
        """Return target server names for an optional filter."""
        if server_name is not None:
            if server_name not in self._connections:
                raise MCPServerNotFoundError(f"Unknown MCP server '{server_name}'")
            return [server_name]
        return list(self._connections.keys())

    def _get_connection(self, server_name: str) -> _ServerConnection:
        """Return connection state for a configured server."""
        if server_name not in self._connections:
            raise MCPServerNotFoundError(f"Unknown MCP server '{server_name}'")
        return self._connections[server_name]

    async def _connect_server(self, server_name: str) -> None:
        """Establish a transport session for a single server."""
        connection = self._get_connection(server_name)
        await self._disconnect_server(server_name)
        connection.status = ServerStatus.CONNECTING
        connection.last_error = None

        exit_stack = AsyncExitStack()
        try:
            session = await self._open_session(connection.config, exit_stack)
            await session.initialize()
            connection.exit_stack = exit_stack
            connection.session = session
            connection.status = ServerStatus.CONNECTED
            await self._discover_tools_for_server(connection)
        except Exception as exc:
            await exit_stack.aclose()
            connection.status = ServerStatus.ERROR
            connection.last_error = str(exc)
            raise MCPConnectionError(
                f"Could not connect to MCP server '{server_name}': {exc}"
            ) from exc

    async def _disconnect_server(self, server_name: str) -> None:
        """Tear down a server connection and clear cached tools."""
        connection = self._get_connection(server_name)
        if connection.exit_stack is not None:
            try:
                await connection.exit_stack.aclose()
            except (Exception, asyncio.CancelledError) as exc:
                logger.debug(
                    "Ignoring MCP stdio cleanup error for server '%s': %s",
                    server_name,
                    exc,
                )
        connection.exit_stack = None
        connection.session = None
        connection.tools.clear()
        connection.status = ServerStatus.DISCONNECTED

    async def _reconnect_server(self, server_name: str) -> None:
        """Reconnect a server after a failed tool call or health check."""
        await self._connect_server(server_name)

    async def _ensure_connected(
        self, server_name: str, connection: _ServerConnection
    ) -> None:
        """Ensure a server is connected before making a request."""
        if connection.status == ServerStatus.CONNECTED and connection.session is not None:
            return
        await self._connect_server(server_name)

    async def _discover_tools_for_server(
        self, connection: _ServerConnection
    ) -> list[MCPToolInfo]:
        """Fetch tools from a connected server and update the cache."""
        if connection.session is None:
            raise MCPConnectionError(
                f"Server '{connection.config.name}' is not connected"
            )

        response = await connection.session.list_tools()
        connection.tools = {tool.name: tool for tool in response.tools}
        return [_tool_info(connection.config.name, tool) for tool in response.tools]

    def _resolve_tool(
        self, tool_name: str, server_name: str | None
    ) -> tuple[str, _ServerConnection]:
        """Resolve a tool name to a server connection."""
        if server_name is not None:
            connection = self._get_connection(server_name)
            if tool_name not in connection.tools:
                raise MCPToolNotFoundError(
                    f"Tool '{tool_name}' not found on server '{server_name}'"
                )
            return server_name, connection

        matches = [
            (name, connection)
            for name, connection in self._connections.items()
            if tool_name in connection.tools
        ]
        if not matches:
            raise MCPToolNotFoundError(f"Tool '{tool_name}' not found on any server")
        if len(matches) > 1:
            server_names = ", ".join(name for name, _ in matches)
            raise MCPToolNotFoundError(
                f"Tool '{tool_name}' exists on multiple servers: {server_names}. "
                "Pass server_name to disambiguate."
            )
        return matches[0]

    async def _open_session(
        self, config: MCPServerConfig, exit_stack: AsyncExitStack
    ) -> ClientSession:
        """Open an MCP session using the configured transport."""
        if config.transport == "stdio":
            return await self._open_stdio_session(config, exit_stack)
        if config.transport == "sse":
            return await self._open_sse_session(config, exit_stack)
        if config.transport == "streamable-http":
            return await self._open_streamable_http_session(config, exit_stack)
        raise MCPClientError(f"Unsupported transport '{config.transport}'")

    async def _open_stdio_session(
        self, config: MCPServerConfig, exit_stack: AsyncExitStack
    ) -> ClientSession:
        """Connect to a stdio-based MCP server subprocess."""
        if not config.command:
            raise MCPClientError(
                f"Server '{config.name}' requires 'command' for stdio transport"
            )

        params = StdioServerParameters(
            command=_stdio_command(config.command),
            args=config.args,
            env=_stdio_env(config.env),
        )
        read_stream, write_stream = await exit_stack.enter_async_context(
            stdio_client(params)
        )
        return await exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

    async def _open_sse_session(
        self, config: MCPServerConfig, exit_stack: AsyncExitStack
    ) -> ClientSession:
        """Connect to an SSE-based MCP server."""
        if not config.url:
            raise MCPClientError(f"Server '{config.name}' requires 'url' for sse transport")

        read_stream, write_stream = await exit_stack.enter_async_context(
            sse_client(config.url)
        )
        return await exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

    async def _open_streamable_http_session(
        self, config: MCPServerConfig, exit_stack: AsyncExitStack
    ) -> ClientSession:
        """Connect to a streamable HTTP MCP server."""
        if not config.url:
            raise MCPClientError(
                f"Server '{config.name}' requires 'url' for streamable-http transport"
            )

        read_stream, write_stream, _ = await exit_stack.enter_async_context(
            streamable_http_client(config.url)
        )
        return await exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )


def _tool_info(server_name: str, tool: types.Tool) -> MCPToolInfo:
    """Convert an MCP tool definition into cached metadata."""
    schema = tool.inputSchema if isinstance(tool.inputSchema, dict) else {}
    return MCPToolInfo(
        name=tool.name,
        server_name=server_name,
        description=tool.description,
        input_schema=schema,
    )


def _stdio_env(config_env: dict[str, str] | None) -> dict[str, str] | None:
    """Merge configured stdio env vars with the parent process environment."""
    if config_env is None:
        return None
    env = dict(os.environ)
    for key, value in config_env.items():
        env[key] = os.environ.get(key, value) if value == "" else value
    return env


def _stdio_command(command: str) -> str:
    """Use the running Python interpreter for Python-based stdio servers."""
    if command.lower() in {"python", "python.exe"}:
        return sys.executable
    return command


def _format_tool_result(result: types.CallToolResult) -> dict[str, Any]:
    """Serialize an MCP tool result for service and API layers."""
    content: list[dict[str, Any]] = []
    for block in result.content:
        if isinstance(block, types.TextContent):
            content.append({"type": "text", "text": block.text})
        elif isinstance(block, types.ImageContent):
            content.append(
                {
                    "type": "image",
                    "mime_type": block.mimeType,
                    "data": block.data,
                }
            )
        elif isinstance(block, types.EmbeddedResource):
            resource = block.resource
            if isinstance(resource, types.TextResourceContents):
                content.append(
                    {
                        "type": "resource",
                        "uri": str(resource.uri),
                        "mime_type": resource.mimeType,
                        "text": resource.text,
                    }
                )
            elif isinstance(resource, types.BlobResourceContents):
                content.append(
                    {
                        "type": "resource",
                        "uri": str(resource.uri),
                        "mime_type": resource.mimeType,
                        "blob": resource.blob,
                    }
                )

    return {
        "is_error": bool(result.isError),
        "content": content,
        "structured_content": result.structuredContent,
    }
