"""ASGI entry point for Render and local root-directory commands."""

from pathlib import Path
import sys

_BACKEND_ROOT = Path(__file__).resolve().parent / "workspace-gpt" / "backend"
sys.path.insert(0, str(_BACKEND_ROOT))

from app.main import app

__all__ = ["app"]