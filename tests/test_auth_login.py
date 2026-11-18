import base64
import hashlib
import json
import socket
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import urlopen

import pytest
import requests

from spotify_mcp.auth_cache import TokenCache
from spotify_mcp.cli.auth_init import main as auth_main
from spotify_mcp.cli.main import main as legacy_main
from spotify_mcp.config import load_settings

SCOPE = "user-read-playback-state"


@pytest.fixture
def login_env(monkeypatch, tmp_path):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    uri = f"http://127.0.0.1:{port}/callback"
    monkeypatch.setenv("SPOTIFY_AUTH_MODE", "pkce")
    monkeypatch.setenv("SPOTIPY_CLIENT_ID", "fixture-client")
    monkeypatch.delenv("SPOTIPY_CLIENT_SECRET", raising=False)
    monkeypatch.setenv("SPOTIPY_REDIRECT_URI", uri)
    monkeypatch.setenv("SPOTIPY_CACHE_PATH", str(tmp_path / "token.json"))
    monkeypatch.setenv("SPOTIFY_SCOPE", SCOPE)
    return uri


@pytest.fixture
def exchanges(monkeypatch):
    requests_seen = []

    def request(_session, method, url, **kwargs):
        assert method.upper() == "POST"
        assert url == "https://accounts.spotify.com/api/token"
        requests_seen.append(kwargs)
        result = requests.Response()
        result.status_code = 200
        result.url = url
        result._content = json.dumps(
            {
                "access_token": "fixture-access",
                "refresh_token": "fixture-refresh",
                "expires_in": 3600,
                "scope": SCOPE,
            }
        ).encode()
        return result

    monkeypatch.setattr(requests.Session, "request", request)
    return requests_seen


def authorize_query(url):
    assert url.startswith("https://accounts.spotify.com/authorize?")
    return {
        key: values[0] for key, values in parse_qs(urlsplit(url).query).items()
    }


def make_callback(uri, state, **params):
    return f"{uri}?{urlencode({'state': state, **params})}"


def assert_pkce_exchange(query, exchange):
    payload = exchange["data"]
    verifier = payload["code_verifier"]
    digest = hashlib.sha256(verifier.encode()).digest()
    assert query["code_challenge_method"] == "S256"
    assert query["code_challenge"] == base64.urlsafe_b64encode(
        digest
    ).decode().rstrip("=")
    assert payload["client_id"] == "fixture-client"
    assert payload["code"] == "fixture-code"
    assert "client_secret" not in payload
    assert "Authorization" not in exchange["headers"]


@pytest.mark.parametrize("unrelated", [False, True])
def test_browser_login_saves_pkce_token(
    login_env, exchanges, monkeypatch, capsys, unrelated
):
    with ThreadPoolExecutor() as worker:
        tasks = []
        query = {}

        def click_browser(url):
            query.update(authorize_query(url))

            def send_callback():
                if unrelated:
                    bad_urls = [
                        make_callback(
                            login_env + "-unrelated",
                            query["state"],
                            code="fixture-code",
                        ),
                        make_callback(
                            login_env, "wrong-state", code="fixture-code"
                        ),
                        make_callback(login_env, query["state"]),
                    ]
                    for bad_url in bad_urls:
                        with pytest.raises(HTTPError) as rejected:
                            urlopen(bad_url, timeout=3)
                        assert 400 <= rejected.value.code < 500
                with urlopen(
                    make_callback(
                        login_env, query["state"], code="fixture-code"
                    ),
                    timeout=3,
                ) as page:
                    assert b"terminal" in page.read()

            tasks.append(worker.submit(send_callback))
            return True

        monkeypatch.setattr("webbrowser.open", click_browser)
        assert auth_main([]) == 0
        tasks[0].result()

    assert len(exchanges) == 1
    assert_pkce_exchange(query, exchanges[0])
    cache = TokenCache(load_settings())
    assert cache.read()["access_token"] == "fixture-access"
    output = capsys.readouterr().out
    assert "saved" in output.lower()
    for secret in (
        "fixture-code",
        "fixture-access",
        "fixture-refresh",
        exchanges[0]["data"]["code_verifier"],
    ):
        assert secret not in output


@pytest.mark.parametrize("legacy", [False, True])
def test_manual_login_uses_shared_exchange(
    login_env, exchanges, monkeypatch, capsys, legacy
):
    if legacy:
        monkeypatch.setenv("SPOTIFY_AUTH_MODE", "legacy")
        monkeypatch.setenv("SPOTIPY_CLIENT_SECRET", "fixture-secret")
    query = {}

    def paste(_prompt):
        (url,) = [
            line
            for line in capsys.readouterr().out.splitlines()
            if line.startswith("https://accounts.spotify.com")
        ]
        query.update(authorize_query(url))
        return make_callback(login_env, query["state"], code="fixture-code")

    monkeypatch.setattr("builtins.input", paste)
    monkeypatch.setattr(
        "webbrowser.open",
        lambda _: pytest.fail("Manual login opened a browser"),
    )
    result = legacy_main([]) if legacy else auth_main(["--manual"])

    assert result == 0
    assert len(exchanges) == 1
    if legacy:
        assert exchanges[0]["headers"]["Authorization"].startswith("Basic ")
    else:
        assert_pkce_exchange(query, exchanges[0])
    assert (
        TokenCache(load_settings()).read()["access_token"] == "fixture-access"
    )


@pytest.mark.parametrize(
    "failure",
    [
        "denied",
        "wrong-state",
        "wrong-redirect",
        "missing-code",
        "cancelled",
        "unwritable",
    ],
)
def test_failed_manual_login_preserves_previous_cache(
    login_env, exchanges, monkeypatch, capsys, failure
):
    cache = TokenCache(load_settings())
    cache.write({"access_token": "older-access"})
    original = cache.path.read_bytes()

    def paste(_prompt):
        (url,) = [
            line
            for line in capsys.readouterr().out.splitlines()
            if line.startswith("https://accounts.spotify.com")
        ]
        state = authorize_query(url)["state"]
        if failure == "cancelled":
            raise KeyboardInterrupt
        if failure == "denied":
            return make_callback(login_env, state, error="access_denied")
        if failure == "missing-code":
            return make_callback(login_env, state)
        if failure == "wrong-redirect":
            return make_callback(
                login_env + "-wrong", state, code="fixture-code"
            )
        return make_callback(
            login_env,
            "wrong" if failure == "wrong-state" else state,
            code="fixture-code",
        )

    monkeypatch.setattr("builtins.input", paste)
    if failure == "unwritable":

        def deny_write(*args):
            raise PermissionError

        monkeypatch.setattr("os.replace", deny_write)

    assert auth_main(["--manual"]) == 1
    assert cache.path.read_bytes() == original
    assert len(exchanges) == (1 if failure == "unwritable" else 0)
    output = capsys.readouterr()
    assert output.err
    assert "fixture-code" not in output.err


def test_browser_port_conflict_and_deadline_are_actionable(
    login_env, exchanges, monkeypatch, capsys
):
    from spotify_mcp.cli import oauth_callback

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", urlsplit(login_env).port))
        sock.listen()
        assert auth_main(["--no-open"]) == 1
    assert "--manual" in capsys.readouterr().err

    monkeypatch.setattr(oauth_callback, "CALLBACK_TIMEOUT", 0.01)
    assert auth_main(["--no-open"]) == 1
    assert "timed out" in capsys.readouterr().err
    assert exchanges == []


def test_manual_redirect_is_not_echoed_on_a_terminal(
    login_env, exchanges, monkeypatch, capsys
):
    def masked_input(_prompt):
        url = next(
            line
            for line in capsys.readouterr().out.splitlines()
            if line.startswith("https://accounts.spotify.com")
        )
        return make_callback(
            login_env, authorize_query(url)["state"], code="fixture-code"
        )

    def echoed_input(_prompt):
        pytest.fail(
            "Interactive sign-in attempted to echo the authorization code"
        )

    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("getpass.getpass", masked_input)
    monkeypatch.setattr("builtins.input", echoed_input)
    assert auth_main(["--manual"]) == 0
    assert len(exchanges) == 1
