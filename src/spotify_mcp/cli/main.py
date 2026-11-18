"""Entry points for Spotify login and the MCP server."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    """Keep the original login module as an alias of the shared command."""
    from spotify_mcp.cli.auth_init import main as login

    return login(argv)


def auth_init() -> None:
    """Installed spotify-mcp-auth entry point."""
    sys.exit(main())


def main_cli() -> None:
    """Installed spotify-mcp server entry point."""
    from spotify_mcp.server import main as server_main

    server_main()


if __name__ == "__main__":
    sys.exit(main())
