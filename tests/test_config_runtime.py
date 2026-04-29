"""Tests for MCP runtime transport settings."""

import pytest

from spotify_mcp.config import load_runtime_settings


def test_defaults_to_stdio(monkeypatch):
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    monkeypatch.delenv("MCP_HOST", raising=False)
    monkeypatch.delenv("MCP_PORT", raising=False)
    monkeypatch.delenv("MCP_SSE_PATH", raising=False)

    s = load_runtime_settings()

    assert s.transport == "stdio"
    assert s.host == "0.0.0.0"
    assert s.port == 8000
    assert s.sse_path == "/sse"


def test_sse_transport_with_custom_values(monkeypatch):
    monkeypatch.setenv("MCP_TRANSPORT", "sse")
    monkeypatch.setenv("MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_PORT", "9000")
    monkeypatch.setenv("MCP_SSE_PATH", "custom-sse")

    s = load_runtime_settings()

    assert s.transport == "sse"
    assert s.host == "127.0.0.1"
    assert s.port == 9000
    assert s.sse_path == "/custom-sse"


def test_http_alias_maps_to_sse(monkeypatch):
    monkeypatch.setenv("MCP_TRANSPORT", "http")
    s = load_runtime_settings()
    assert s.transport == "sse"


def test_invalid_transport_raises(monkeypatch):
    monkeypatch.setenv("MCP_TRANSPORT", "banana")
    with pytest.raises(ValueError, match="MCP_TRANSPORT"):
        load_runtime_settings()


def test_invalid_port_raises(monkeypatch):
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    monkeypatch.setenv("MCP_PORT", "not-a-number")
    with pytest.raises(ValueError, match="MCP_PORT must be an integer"):
        load_runtime_settings()


def test_out_of_range_port_raises(monkeypatch):
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    monkeypatch.setenv("MCP_PORT", "99999")
    with pytest.raises(ValueError, match="MCP_PORT must be between"):
        load_runtime_settings()


def test_sse_path_gets_leading_slash(monkeypatch):
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    monkeypatch.setenv("MCP_SSE_PATH", "events")
    s = load_runtime_settings()
    assert s.sse_path == "/events"
