import json
import os
import stat

import pytest

from spotify_mcp.auth_cache import TokenCache, TokenCacheError
from spotify_mcp.config import Settings

TOKEN = {"access_token": "fixture-access", "refresh_token": "fixture-refresh"}


def cache(path, mode="pkce", client_id="test-client"):
    return TokenCache(
        Settings(
            client_id=client_id,
            client_secret="legacy-secret" if mode == "legacy" else None,
            redirect_uri="http://127.0.0.1:8888/callback",
            cache_path=str(path) if path is not None else None,
            auth_mode=mode,
        )
    )


def test_reads_existing_legacy_cache_without_rewriting(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SPOTIPY_CLIENT_USERNAME", "old-user")
    path = tmp_path / ".cache-old-user"
    raw = json.dumps(TOKEN, indent=2).encode()
    path.write_bytes(raw)

    assert cache(None, "legacy").read() == TOKEN
    assert path.read_bytes() == raw


def test_pkce_cache_round_trip_uses_private_permissions(tmp_path):
    path = tmp_path / "auth" / "token.json"
    token_cache = cache(path)
    assert token_cache.read() is None

    token_cache.write(TOKEN)

    raw = json.loads(path.read_text())
    assert raw["_spotify_mcp"] == {"version": 1, "client_id": "test-client"}
    assert token_cache.read() == TOKEN
    if os.name == "posix":
        assert stat.S_IMODE(path.stat().st_mode) == 0o600


@pytest.mark.parametrize(
    ("mode", "contents"),
    [
        ("pkce", json.dumps(TOKEN)),
        (
            "legacy",
            json.dumps(
                {
                    **TOKEN,
                    "_spotify_mcp": {"version": 1, "client_id": "test-client"},
                }
            ),
        ),
        (
            "pkce",
            json.dumps(
                {
                    **TOKEN,
                    "_spotify_mcp": {
                        "version": 1,
                        "client_id": "other-client",
                    },
                }
            ),
        ),
        (
            "pkce",
            json.dumps(
                {
                    **TOKEN,
                    "_spotify_mcp": {"version": 2, "client_id": "test-client"},
                }
            ),
        ),
        ("pkce", 'bad json "fixture-access"'),
    ],
)
def test_does_not_read_or_replace_incompatible_cache(tmp_path, mode, contents):
    path = tmp_path / "token.json"
    path.write_text(contents)
    token_cache = cache(path, mode)

    with pytest.raises(TokenCacheError) as read_error:
        token_cache.read()
    with pytest.raises(TokenCacheError) as write_error:
        token_cache.write(TOKEN)

    assert str(path) in str(read_error.value)
    assert "fixture-access" not in str(read_error.value)
    assert "fixture-refresh" not in str(write_error.value)
    assert path.read_text() == contents


def test_failed_atomic_replace_preserves_previous_token(tmp_path, monkeypatch):
    path = tmp_path / "token.json"
    token_cache = cache(path, "legacy")
    token_cache.write(TOKEN)

    def deny_replace(source, destination):
        raise PermissionError("write failed")

    monkeypatch.setattr(os, "replace", deny_replace)
    with pytest.raises(TokenCacheError, match="write"):
        token_cache.write({**TOKEN, "access_token": "replacement"})

    assert json.loads(path.read_text()) == TOKEN
    assert {entry.name for entry in tmp_path.iterdir()} <= {
        path.name,
        f"{path.name}.lock",
    }
