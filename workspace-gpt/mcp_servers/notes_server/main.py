"""Local notes MCP server backed by a JSON file."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("notes")


def _notes_path() -> Path:
    default = Path.cwd() / "workspace_notes.json"
    return Path(os.environ.get("NOTES_DB_PATH", default)).resolve()


def _load_notes() -> list[dict[str, str]]:
    path = _notes_path()
    if not path.is_file():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _save_notes(notes: list[dict[str, str]]) -> None:
    path = _notes_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(notes, indent=2), encoding="utf-8")


@mcp.tool()
def list_notes() -> list[dict[str, str]]:
    """List saved notes."""
    return _load_notes()


@mcp.tool()
def create_note(title: str, body: str) -> dict[str, str]:
    """Create a note."""
    notes = _load_notes()
    now = datetime.now(timezone.utc).isoformat()
    note = {
        "id": str(uuid4()),
        "title": title,
        "body": body,
        "created_at": now,
        "updated_at": now,
    }
    notes.append(note)
    _save_notes(notes)
    return note


@mcp.tool()
def search_notes(query: str) -> list[dict[str, str]]:
    """Search notes by title or body."""
    needle = query.lower()
    return [
        note
        for note in _load_notes()
        if needle in note["title"].lower() or needle in note["body"].lower()
    ]


@mcp.tool()
def delete_note(note_id: str) -> dict[str, str | bool]:
    """Delete a note by id."""
    notes = _load_notes()
    remaining = [note for note in notes if note["id"] != note_id]
    _save_notes(remaining)
    return {"id": note_id, "deleted": len(remaining) != len(notes)}


if __name__ == "__main__":
    mcp.run()
