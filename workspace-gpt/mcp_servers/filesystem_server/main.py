"""Filesystem MCP server scoped to WORKSPACE_ROOT."""

from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("filesystem")


def _root() -> Path:
    return Path(os.environ.get("WORKSPACE_ROOT", ".")).resolve()


def _safe_path(path: str = ".") -> Path:
    root = _root()
    target = (root / path).resolve()
    if target != root and root not in target.parents:
        raise ValueError("Path is outside WORKSPACE_ROOT")
    return target


@mcp.tool()
def list_directory(path: str = ".") -> list[dict[str, str | int | bool]]:
    """List files and directories under WORKSPACE_ROOT."""
    target = _safe_path(path)
    if not target.is_dir():
        raise ValueError(f"Not a directory: {path}")
    entries = []
    for child in sorted(target.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())):
        stat = child.stat()
        entries.append(
            {
                "name": child.name,
                "path": str(child.relative_to(_root())),
                "is_dir": child.is_dir(),
                "size": stat.st_size,
            }
        )
    return entries


@mcp.tool()
def read_file(path: str, max_bytes: int = 100_000) -> str:
    """Read a UTF-8 text file from WORKSPACE_ROOT."""
    target = _safe_path(path)
    if not target.is_file():
        raise ValueError(f"Not a file: {path}")
    data = target.read_bytes()[:max_bytes]
    return data.decode("utf-8", errors="replace")


@mcp.tool()
def write_file(path: str, content: str) -> dict[str, str | int]:
    """Write a UTF-8 text file under WORKSPACE_ROOT."""
    target = _safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"path": str(target.relative_to(_root())), "bytes": len(content.encode("utf-8"))}


@mcp.tool()
def search_text(query: str, path: str = ".") -> list[dict[str, str | int]]:
    """Search text files under WORKSPACE_ROOT for a query string."""
    target = _safe_path(path)
    roots = [target] if target.is_file() else target.rglob("*")
    matches = []
    for file_path in roots:
        if not file_path.is_file():
            continue
        try:
            lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line_number, line in enumerate(lines, start=1):
            if query.lower() in line.lower():
                matches.append(
                    {
                        "path": str(file_path.relative_to(_root())),
                        "line": line_number,
                        "text": line,
                    }
                )
    return matches[:100]


if __name__ == "__main__":
    mcp.run()
