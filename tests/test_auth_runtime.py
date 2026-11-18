import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from threading import Event
from time import time

import pytest
import requests
from mcp.shared.memory import create_connected_server_and_client_session

from spotify_mcp import server, tools
from spotify_mcp.auth import get_access_token
from spotify_mcp.auth_cache import TokenCache
from spotify_mcp.config import load_settings

SCOPE = "user-read-playback-state"


@pytest.fixture
def spotify_env(monkeypatch, tmp_path):
    monkeypatch.setenv("SPOTIPY_CLIENT_ID", "fixture-client")
    monkeypatch.delenv("SPOTIPY_CLIENT_SECRET", raising=False)
    monkeypatch.setenv(
        "SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback"
    )
    monkeypatch.setenv("SPOTIPY_CACHE_PATH", str(tmp_path / "token.json"))
    monkeypatch.setenv("SPOTIFY_AUTH_MODE", "pkce")
    monkeypatch.setenv("SPOTIFY_SCOPE", SCOPE)
    monkeypatch.setattr(tools, "_settings", None)

    def forbidden(*args, **kwargs):
        pytest.fail("MCP attempted an interactive sign-in")

    monkeypatch.setattr("builtins.input", forbidden)
    monkeypatch.setattr("webbrowser.open", forbidden)
    monkeypatch.setattr(requests.Session, "request", forbidden)


def token(*, expires_in=3600, scope=SCOPE):
    return {
        "access_token": "fixture-access",
        "refresh_token": "fixture-refresh",
        "scope": scope,
        "expires_at": int(time()) + expires_in,
    }


def response(url, content, status=200):
    reply = requests.Response()
    reply.status_code = status
    reply.url = url
    reply._content = json.dumps(content).encode()
    return reply


def message(result):
    return " ".join(
        part.text for part in result.content if part.type == "text"
    )


async def search(session):
    return await session.call_tool("search", {"query": "fixture"})


def test_in_flight_refresh_cannot_overwrite_new_login(
    spotify_env, monkeypatch
):
    settings = load_settings()
    cache = TokenCache(settings)
    cache.write(token(expires_in=-1))
    refreshing, release_refresh, writing = Event(), Event(), Event()

    def request(_session, method, url, **kwargs):
        refreshing.set()
        assert release_refresh.wait(timeout=3)
        return response(
            url, {"access_token": "old-account-renewed", "expires_in": 3600}
        )

    def sign_in():
        writing.set()
        TokenCache(settings).write({**token(), "access_token": "new-account"})

    monkeypatch.setattr(requests.Session, "request", request)
    with ThreadPoolExecutor(max_workers=2) as workers:
        refresh = workers.submit(get_access_token, settings)
        assert refreshing.wait(timeout=3)
        login = workers.submit(sign_in)
        try:
            assert writing.wait(timeout=3)
            with pytest.raises(TimeoutError):
                login.result(timeout=0.2)
        finally:
            release_refresh.set()
        assert refresh.result(timeout=3) == "old-account-renewed"
        login.result(timeout=3)

    assert cache.read()["access_token"] == "new-account"


@pytest.mark.parametrize("mode", ["pkce", "legacy"])
async def test_runtime_refreshes_in_both_modes(spotify_env, monkeypatch, mode):
    monkeypatch.setenv("SPOTIFY_AUTH_MODE", mode)
    if mode == "legacy":
        monkeypatch.setenv("SPOTIPY_CLIENT_SECRET", "fixture-secret")
    cache = TokenCache(load_settings())
    cache.write(token(expires_in=-1))
    calls = []

    def request(_session, method, url, **kwargs):
        calls.append(method.upper())
        if method.upper() == "POST":
            assert kwargs["data"]["refresh_token"] == "fixture-refresh"
            if mode == "pkce":
                assert kwargs["data"]["client_id"] == "fixture-client"
                assert "Authorization" not in kwargs["headers"]
            else:
                assert kwargs["headers"]["Authorization"].startswith("Basic ")
            return response(
                url, {"access_token": "renewed", "expires_in": 3600}
            )
        assert kwargs["headers"]["Authorization"] == "Bearer renewed"
        return response(url, {"tracks": {"items": []}})

    monkeypatch.setattr(requests.Session, "request", request)
    async with create_connected_server_and_client_session(
        server.mcp
    ) as client:
        assert not (await search(client)).isError

    saved = cache.read()
    assert saved["access_token"] == "renewed"
    assert saved["refresh_token"] == "fixture-refresh"
    assert saved["scope"] == SCOPE
    assert calls == ["POST", "GET"]


async def test_runtime_reconnects_after_cache_appears(
    spotify_env, monkeypatch
):
    async with create_connected_server_and_client_session(
        server.mcp
    ) as client:
        assert len((await client.list_tools()).tools) == 25
        signed_out = await search(client)
        assert signed_out.isError
        assert "spotify-mcp-auth" in message(signed_out)

        TokenCache(load_settings()).write(token())

        def request(_session, method, url, **kwargs):
            assert (
                kwargs["headers"]["Authorization"] == "Bearer fixture-access"
            )
            return response(url, {"tracks": {"items": []}})

        monkeypatch.setattr(requests.Session, "request", request)
        assert not (await search(client)).isError


@pytest.mark.parametrize(
    "problem", ["signed-out", "invalid_grant", "scope", "bad-cache"]
)
async def test_signed_out_and_invalid_grant_are_mcp_errors(
    spotify_env, monkeypatch, problem
):
    cache = TokenCache(load_settings())
    if problem == "invalid_grant":
        cache.write(token(expires_in=-1))
        monkeypatch.setattr(
            requests.Session,
            "request",
            lambda _, method, url, **kw: response(
                url,
                {
                    "error": "invalid_grant",
                    "error_description": "fixture-refresh",
                },
                400,
            ),
        )
    elif problem == "scope":
        cache.write(token(scope="user-top-read"))
    elif problem == "bad-cache":
        cache.path.write_text("not valid JSON")

    async with create_connected_server_and_client_session(
        server.mcp
    ) as client:
        result = await search(client)

    assert result.isError
    assert "spotify-mcp-auth" in message(result)
    assert "fixture-refresh" not in message(result)


async def test_transient_refresh_failure_keeps_cache(spotify_env, monkeypatch):
    cache = TokenCache(load_settings())
    cache.write(token(expires_in=-1))
    before = cache.path.read_bytes()

    def timeout(*args, **kwargs):
        raise requests.Timeout("fixture-refresh")

    monkeypatch.setattr(requests.Session, "request", timeout)
    async with create_connected_server_and_client_session(
        server.mcp
    ) as client:
        result = await search(client)

    assert result.isError
    assert "try again" in message(result).lower()
    assert "fixture-refresh" not in message(result)
    assert cache.path.read_bytes() == before


@pytest.mark.parametrize(
    ("tool_name", "arguments", "method"),
    [("search", {"query": "fixture"}, "GET"), ("pause", {}, "PUT")],
)
async def test_spotify_401_is_an_mcp_error_without_replay(
    spotify_env, monkeypatch, tool_name, arguments, method
):
    cache = TokenCache(load_settings())
    cache.write(token())
    before = cache.path.read_bytes()
    calls = []

    def request(_session, actual_method, url, **kwargs):
        calls.append(actual_method.upper())
        return response(url, {"error": {"message": "token rejected"}}, 401)

    monkeypatch.setattr(requests.Session, "request", request)
    async with create_connected_server_and_client_session(
        server.mcp
    ) as client:
        result = await client.call_tool(tool_name, arguments)

    assert result.isError
    assert "spotify-mcp-auth" in message(result)
    assert calls == [method]
    assert cache.path.read_bytes() == before
