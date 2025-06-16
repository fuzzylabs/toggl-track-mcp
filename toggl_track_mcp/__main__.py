"""Entry point for running Toggl Track MCP server in stdio mode."""

import asyncio

from .server import mcp


def main():
    """Run the MCP server in stdio mode."""
    asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    main()
