"""Vercel entry point for the FastAPI application."""

from pathlib import Path
import sys

_BACKEND_ROOT = Path(__file__).resolve().parents[1] / "workspace-gpt" / "backend"
sys.path.insert(0, str(_BACKEND_ROOT))

from main import app

__all__ = ["app"]