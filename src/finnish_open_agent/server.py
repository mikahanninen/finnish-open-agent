"""Entry point for the Finnish Open Agent MCP server.

Run locally over stdio (default) for Claude Desktop / Claude Code:

    finnish-open-agent
    # or
    python -m finnish_open_agent.server

Run as a remote streamable-HTTP server:

    FOA_TRANSPORT=http FOA_PORT=8000 finnish-open-agent
"""

from __future__ import annotations

import os

from .app import mcp
from .tools import load_all


def main() -> None:
    """Register all tool modules and start the server on the configured transport."""
    load_all()  # ensures every @mcp.tool has been imported/registered
    transport = os.environ.get("FOA_TRANSPORT", "stdio").lower()
    if transport in ("http", "streamable_http", "streamable-http"):
        # Host/port are read by FastMCP from its settings/env; default 127.0.0.1.
        mcp.settings.host = os.environ.get("FOA_HOST", "127.0.0.1")
        mcp.settings.port = int(os.environ.get("FOA_PORT", "8000"))
        mcp.run(transport="streamable-http")
    else:
        mcp.run()  # stdio


if __name__ == "__main__":
    main()
