"""Tests for server main() transport selection."""

from unittest.mock import patch

from spotify_mcp import server


def test_main_runs_stdio_by_default(monkeypatch):
    monkeypatch.setenv("SPOTIPY_CLIENT_ID", "x")
    monkeypatch.setenv("SPOTIPY_CLIENT_SECRET", "y")
    monkeypatch.setenv(
        "SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback"
    )
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)

    with patch.object(server.mcp, "run") as run:
        server.main()

    run.assert_called_once_with("stdio")


def test_main_runs_sse_when_configured(monkeypatch):
    monkeypatch.setenv("SPOTIPY_CLIENT_ID", "x")
    monkeypatch.setenv("SPOTIPY_CLIENT_SECRET", "y")
    monkeypatch.setenv(
        "SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback"
    )
    monkeypatch.setenv("MCP_TRANSPORT", "sse")
    monkeypatch.setenv("MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("MCP_PORT", "8000")
    monkeypatch.setenv("MCP_SSE_PATH", "/sse")

    with patch.object(server.mcp, "run") as run:
        server.main()

    run.assert_called_once_with("sse")
    assert server.mcp.settings.host == "0.0.0.0"
    assert server.mcp.settings.port == 8000
    assert server.mcp.settings.sse_path == "/sse"
