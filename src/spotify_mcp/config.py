"""
Configuration for Spotify MCP server.

Centralizes reading and validation of environment variables so that both the
MCP server entrypoint and the Spotify tool implementations share one source of
truth. Supports optional overrides for OAuth scope and token cache path while
keeping backward compatibility with existing Docker/MCP configurations that
provide the standard Spotipy environment variables.

SPOTIPY_CLIENT_ID is required. SPOTIFY_AUTH_MODE selects pkce or legacy.
Legacy requires SPOTIPY_CLIENT_SECRET and SPOTIPY_REDIRECT_URI. PKCE uses
a loopback redirect by default. SPOTIFY_SCOPE and SPOTIPY_CACHE_PATH can
override the scope and token cache location.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, cast

AuthMode = Literal["pkce", "legacy"]
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8888/callback"

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
    client_secret: str | None = field(repr=False)
    redirect_uri: str
    scope: str = DEFAULT_SCOPE
    cache_path: str | None = None
    auth_mode: AuthMode = "legacy"


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
    if client_secret is not None and not client_secret.strip():
        client_secret = None

    mode = os.getenv("SPOTIFY_AUTH_MODE", "").strip().lower()
    mode = mode or ("legacy" if client_secret else "pkce")
    if mode not in {"legacy", "pkce"}:
        raise RuntimeError("SPOTIFY_AUTH_MODE must be pkce or legacy.")
    auth_mode = cast(AuthMode, mode)

    missing = []
    if not client_id:
        missing.append("SPOTIPY_CLIENT_ID")
    if auth_mode == "legacy":
        if not client_secret:
            missing.append("SPOTIPY_CLIENT_SECRET")
        if not redirect_uri:
            missing.append("SPOTIPY_REDIRECT_URI")
    else:
        client_secret = None
        redirect_uri = redirect_uri or DEFAULT_REDIRECT_URI

    if not client_id or not redirect_uri or missing:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Provide them via your MCP client configuration or a .env file."
        )

    scope = os.getenv("SPOTIFY_SCOPE", DEFAULT_SCOPE)
    cache_path = os.getenv("SPOTIPY_CACHE_PATH") or None
    if auth_mode == "pkce" and cache_path is None:
        cache_path = str(Path.home() / ".cache/spotify-mcp/token-pkce.json")

    return Settings(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        cache_path=cache_path,
        auth_mode=auth_mode,
    )


_DEFAULT_HOST = (
    "0.0.0.0"  # nosec B104 — intentional bind-all for Docker SSE mode
)


@dataclass(frozen=True)
class RuntimeSettings:
    """Transport and binding settings for the MCP server."""

    transport: str = "stdio"
    host: str = _DEFAULT_HOST
    port: int = 8000
    sse_path: str = "/sse"


def load_runtime_settings() -> RuntimeSettings:
    """Load MCP transport settings from environment variables.

    Raises:
        ValueError: If env vars contain invalid values.
    """
    transport = os.getenv("MCP_TRANSPORT", "stdio").strip().lower()
    if transport == "http":
        transport = "sse"

    if transport not in {"stdio", "sse"}:
        raise ValueError("MCP_TRANSPORT must be one of: stdio, sse")

    port_raw = os.getenv("MCP_PORT", "8000").strip()
    try:
        port = int(port_raw)
    except ValueError as exc:
        raise ValueError("MCP_PORT must be an integer") from exc

    if not 1 <= port <= 65535:
        raise ValueError("MCP_PORT must be between 1 and 65535")

    sse_path = os.getenv("MCP_SSE_PATH", "/sse").strip() or "/sse"
    if not sse_path.startswith("/"):
        sse_path = f"/{sse_path}"

    return RuntimeSettings(
        transport=transport,
        host=os.getenv("MCP_HOST", _DEFAULT_HOST).strip() or _DEFAULT_HOST,
        port=port,
        sse_path=sse_path,
    )
