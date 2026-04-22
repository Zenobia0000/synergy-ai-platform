"""Uvicorn entrypoint. Run: `uv run uvicorn main:app --reload`."""

from app.api.main import app

__all__ = ["app"]
