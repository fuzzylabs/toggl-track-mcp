"""Toggl Track MCP Server - Expose time tracking data as AI tools."""

from .server import app, mcp

__version__ = "0.1.0"
__all__ = ["app", "mcp"]