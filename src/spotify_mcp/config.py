"""
Configuration for Spotify MCP server.

Centralizes reading and validation of environment variables so that both the
MCP server entrypoint and the Spotify tool implementations share one source of
truth. Supports optional overrides for OAuth scope and token cache path while
keeping backward compatibility with existing Docker/MCP configurations that
provide the standard Spotipy environment variables.

Required environment variables:
- SPOTIPY_CLIENT_ID
- SPOTIPY_CLIENT_SECRET
- SPOTIPY_REDIRECT_URI

Optional environment variables:
- SPOTIFY_SCOPE: Overrides the default OAuth scope string
- SPOTIPY_CACHE_PATH: Sets a specific token cache file path (inside the
  container or host if bind-mounted)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

DEFAULT_SCOPE: str = (
    "user-read-playback-state "
    "user-modify-playback-state "
    "user-read-currently-playing "
    "playlist-read-private "
    "playlist-modify-public "
    "playlist-modify-private "
    "user-library-read "
    "user-library-modify "
    "user-top-read "
    "user-read-recently-played "
    "user-follow-read "
    "user-follow-modify"
)


@dataclass(frozen=True)
class Settings:
    """Strongly-typed configuration values for the server."""

    client_id: str
    client_secret: str
    redirect_uri: str
    scope: str = DEFAULT_SCOPE
    cache_path: Optional[str] = None


def load_settings() -> Settings:
    """Load and validate environment-based settings.

    Returns:
        Settings: Populated settings object.

    Raises:
        RuntimeError: If any required environment variables are missing.
    """

    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")

    missing = [
        name
        for name, value in (
            ("SPOTIPY_CLIENT_ID", client_id),
            ("SPOTIPY_CLIENT_SECRET", client_secret),
            ("SPOTIPY_REDIRECT_URI", redirect_uri),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Provide them via your MCP client configuration or a .env file."
        )

    scope = os.getenv("SPOTIFY_SCOPE", DEFAULT_SCOPE)
    cache_path = os.getenv("SPOTIPY_CACHE_PATH") or None

    return Settings(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        cache_path=cache_path,
    )
