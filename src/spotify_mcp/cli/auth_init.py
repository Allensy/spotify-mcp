#!/usr/bin/env python3
"""
Auth initialization script for Spotify MCP.

This script performs the initial OAuth flow to create and cache a Spotify token.
Run this once to authenticate, then the MCP server can reuse the cached token.

Usage:
    python -m spotify_mcp.cli.auth_init
"""

from __future__ import annotations

import sys

from spotify_mcp.config import load_settings
from spotipy.oauth2 import SpotifyOAuth


def main() -> None:
    """Initialize Spotify OAuth and cache the token."""
    print("=== Spotify MCP Authentication Initializer ===\n")

    try:
        settings = load_settings()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Client ID: {settings.client_id}")
    print(f"Redirect URI: {settings.redirect_uri}")
    print(f"Scope: {settings.scope}")
    if settings.cache_path:
        print(f"Cache path: {settings.cache_path}")
    print()

    auth_manager_kwargs = {
        "client_id": settings.client_id,
        "client_secret": settings.client_secret,
        "redirect_uri": settings.redirect_uri,
        "scope": settings.scope,
    }
    if settings.cache_path:
        auth_manager_kwargs["cache_path"] = settings.cache_path

    auth_manager = SpotifyOAuth(**auth_manager_kwargs)

    # Get the authorization URL
    auth_url = auth_manager.get_authorize_url()
    print("Please visit this URL to authorize the application:")
    print(f"\n{auth_url}\n")

    # For interactive use, try to get the response
    print("After authorizing, you will be redirected to a URL.")
    print("Please paste the full redirect URL here:")
    redirect_response = input().strip()

    if not redirect_response:
        print("Error: No redirect URL provided", file=sys.stderr)
        sys.exit(1)

    # Extract the code and get the token
    code = auth_manager.parse_response_code(redirect_response)
    token_info = auth_manager.get_access_token(code, as_dict=True)

    if token_info:
        cache_location = settings.cache_path or ".cache"
        print(f"\n✓ Success! Token cached at: {cache_location}")
        print("You can now use the Spotify MCP server.")
    else:
        print("\n✗ Failed to obtain token", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

