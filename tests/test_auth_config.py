from pathlib import Path

import pytest

from spotify_mcp.config import load_settings


@pytest.fixture(autouse=True)
def clean_auth_env(monkeypatch):
    for key in (
        "SPOTIPY_CLIENT_SECRET",
        "SPOTIPY_REDIRECT_URI",
        "SPOTIPY_CACHE_PATH",
        "SPOTIFY_AUTH_MODE",
        "SPOTIFY_SCOPE",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("SPOTIPY_CLIENT_ID", "test-client")


@pytest.mark.parametrize("mode", [None, "  ", "pkce"])
def test_pkce_configuration_needs_only_client_id(monkeypatch, mode):
    if mode is not None:
        monkeypatch.setenv("SPOTIFY_AUTH_MODE", mode)

    settings = load_settings()

    assert settings.auth_mode == "pkce"
    assert settings.client_secret is None
    assert settings.redirect_uri == "http://127.0.0.1:8888/callback"
    assert settings.cache_path == str(
        Path.home() / ".cache" / "spotify-mcp" / "token-pkce.json"
    )


@pytest.mark.parametrize("cache_path", [None, "/app/.cache/token"])
def test_legacy_configuration_preserves_cache_path(monkeypatch, cache_path):
    monkeypatch.setenv("SPOTIPY_CLIENT_SECRET", "existing-secret")
    monkeypatch.setenv("SPOTIPY_REDIRECT_URI", "https://example.org/callback")
    if cache_path is not None:
        monkeypatch.setenv("SPOTIPY_CACHE_PATH", cache_path)

    settings = load_settings()

    assert settings.auth_mode == "legacy"
    assert settings.client_secret == "existing-secret"
    assert settings.cache_path == cache_path
    assert settings.redirect_uri == "https://example.org/callback"


def test_explicit_auth_mode_overrides_secret_detection(monkeypatch):
    monkeypatch.setenv("SPOTIFY_AUTH_MODE", "pkce")
    monkeypatch.setenv("SPOTIPY_CLIENT_SECRET", "unused-secret")
    monkeypatch.setenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:9090/auth")
    monkeypatch.setenv("SPOTIPY_CACHE_PATH", "/tmp/user/token.json")
    monkeypatch.setenv("SPOTIFY_SCOPE", "user-read-playback-state")

    settings = load_settings()

    assert settings.auth_mode == "pkce"
    assert settings.client_secret is None
    assert settings.redirect_uri == "http://127.0.0.1:9090/auth"
    assert settings.cache_path == "/tmp/user/token.json"
    assert settings.scope == "user-read-playback-state"


def test_explicit_legacy_requires_secret_and_redirect(monkeypatch):
    monkeypatch.setenv("SPOTIFY_AUTH_MODE", "legacy")

    with pytest.raises(
        RuntimeError, match="SPOTIPY_CLIENT_SECRET.*SPOTIPY_REDIRECT_URI"
    ):
        load_settings()


def test_unknown_auth_mode_fails(monkeypatch):
    monkeypatch.setenv("SPOTIFY_AUTH_MODE", "unsupported")
    monkeypatch.setenv("SPOTIPY_CLIENT_SECRET", "otherwise-valid")
    monkeypatch.setenv(
        "SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback"
    )

    with pytest.raises(RuntimeError, match="SPOTIFY_AUTH_MODE"):
        load_settings()
