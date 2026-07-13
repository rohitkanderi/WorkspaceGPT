"""SQLite MCP server for local SQL exploration."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("sqlite")


def _db_path() -> Path:
    return Path(os.environ.get("SQLITE_DB_PATH", "workspacegpt.db")).resolve()


def _connect() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


@mcp.tool()
def list_tables() -> list[str]:
    """List SQLite tables."""
    with _connect() as connection:
        rows = connection.execute(
            "select name from sqlite_master where type = 'table' order by name"
        ).fetchall()
    return [row["name"] for row in rows]


@mcp.tool()
def describe_table(table_name: str) -> list[dict[str, Any]]:
    """Return SQLite column metadata for a table."""
    with _connect() as connection:
        rows = connection.execute(f"pragma table_info({_quote_identifier(table_name)})").fetchall()
    return [dict(row) for row in rows]


@mcp.tool()
def run_select(query: str, limit: int = 100) -> list[dict[str, Any]]:
    """Run a read-only SELECT query."""
    if not query.lstrip().lower().startswith("select"):
        raise ValueError("Only SELECT queries are allowed")
    with _connect() as connection:
        rows = connection.execute(query).fetchmany(limit)
    return [dict(row) for row in rows]


@mcp.tool()
def execute_statement(statement: str) -> dict[str, int]:
    """Execute a non-SELECT SQL statement."""
    with _connect() as connection:
        cursor = connection.execute(statement)
        connection.commit()
    return {"rowcount": cursor.rowcount}


if __name__ == "__main__":
    mcp.run()
