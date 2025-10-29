"""
Command-line interface for Spotify MCP.

Provides commands for authentication and running the MCP server.

Interactive OAuth initializer for Spotify MCP (Docker-friendly).

Usage (Docker, zero local installs):

  docker run --rm -it \
    -v ${HOME}/.cache/spotify-mcp:/app/.cache \
    -e SPOTIPY_CLIENT_ID=... \
    -e SPOTIPY_CLIENT_SECRET=... \
    -e SPOTIPY_REDIRECT_URI=http://localhost:8765/callback \
    -e SPOTIPY_CACHE_PATH=/app/.cache/token \
    spotify-mcp:latest python -u auth_init.py

This script prints an authorize URL, prompts you to paste the redirected URL
after login, exchanges it for tokens, and writes them to the configured cache
path so subsequent runs of the server can reuse the token.
"""

from __future__ import annotations

import os
import sys
from urllib.parse import urlparse, parse_qs

from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

from spotify_mcp.config import load_settings


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


def main() -> int:
    # Load env from .env when running locally; ignored in Docker unless present
    load_dotenv()

    settings = load_settings()

    auth_kwargs = {
        "client_id": settings.client_id,
        "client_secret": settings.client_secret,
        "redirect_uri": settings.redirect_uri,
        "scope": settings.scope,
        # cache_path is optional; Spotipy will default to .cache in CWD
        # but we prefer an explicit location when provided
    }
    cache_path = os.getenv("SPOTIPY_CACHE_PATH")
    if cache_path:
        _ensure_parent_dir(cache_path)
        auth_kwargs["cache_path"] = cache_path

    oauth = SpotifyOAuth(**auth_kwargs)

    authorize_url = oauth.get_authorize_url()
    print("\nSpotify authorization required.")
    print("1) Open this URL in your browser:")
    print(authorize_url)
    print("\n2) After login, copy the FULL redirected URL from the browser")
    print("   address bar and paste it below.\n")

    try:
        redirected = input("Paste redirected URL here: ").strip()
    except KeyboardInterrupt:
        print("\nAborted.")
        return 1

    if not redirected:
        print("No URL provided; aborting.")
        return 1

    parsed = urlparse(redirected)
    query = parse_qs(parsed.query)
    code_values = query.get("code")
    if not code_values:
        print(
            "Could not find 'code' in the provided URL. "
            "Ensure you pasted the redirected URL."
        )
        return 1

    code = code_values[0]

    try:
        token_info = oauth.get_access_token(code)
    except Exception as e:  # noqa: BLE001
        print("Error exchanging code for token: " f"{e}")
        return 1

    # Spotipy caches automatically when using SpotifyOAuth with cache_path
    # or its default cache file.
    access_token = token_info.get("access_token")
    cache_hint = cache_path or os.path.join(os.getcwd(), ".cache")
    if access_token:
        print("\nSuccess! Token acquired and cached.")
        print(f"Cache location: {cache_hint}")
        return 0
    else:
        print("Token acquisition failed unexpectedly.")
        return 1


def auth_init() -> None:
    """Entry point for spotify-mcp-auth command."""
    sys.exit(main())


def main_cli() -> None:
    """Entry point for spotify-mcp command to run the server."""
    from spotify_mcp.server import main as server_main

    server_main()


if __name__ == "__main__":
    sys.exit(main())
