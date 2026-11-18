"""Validate and receive OAuth redirects for the standalone login command."""

from __future__ import annotations

import hmac
import socket
import webbrowser
from contextlib import suppress
from http.server import BaseHTTPRequestHandler, HTTPServer
from time import monotonic
from urllib.parse import ParseResult, parse_qs, urlparse

CALLBACK_TIMEOUT = 300


class CallbackError(RuntimeError):
    """A Spotify callback could not complete the sign-in attempt."""


class AuthorizationDenied(CallbackError):
    """The matching sign-in attempt was denied."""


def _target(url: ParseResult) -> tuple[str, str | None, int | None, str]:
    return url.scheme, url.hostname, url.port, url.path


def parse_callback(redirected: str, redirect_uri: str, state: str) -> str:
    try:
        actual = urlparse(redirected.strip())
        expected = urlparse(redirect_uri)
        actual_query = parse_qs(actual.query, keep_blank_values=True)
        expected_query = parse_qs(expected.query, keep_blank_values=True)
        if (
            _target(actual) != _target(expected)
            or actual.username is not None
            or actual.fragment
            or actual.params != expected.params
            or any(
                actual_query.get(key) != value
                for key, value in expected_query.items()
            )
        ):
            raise CallbackError(
                "The response did not match the registered redirect URI."
            )
    except ValueError:
        raise CallbackError("The response URL is invalid.") from None

    states = actual_query.get("state", [])
    if len(states) != 1 or not hmac.compare_digest(
        states[0].encode(), state.encode()
    ):
        raise CallbackError(
            "The response did not match this sign-in attempt. Start again."
        )
    if "error" in actual_query:
        raise AuthorizationDenied("Spotify authorization was denied.")
    codes = actual_query.get("code", [])
    if len(codes) != 1 or not codes[0].strip():
        raise CallbackError(
            "The response did not include an authorization code."
        )
    return codes[0]


class _CallbackServer(HTTPServer):
    def get_request(self) -> tuple[socket.socket, tuple[str, int]]:
        connection, address = super().get_request()
        # A connection that never finishes its request must not block sign-in.
        connection.settimeout(2)
        return connection, address


class _IPv6CallbackServer(_CallbackServer):
    address_family = socket.AF_INET6


def receive_callback(
    redirect_uri: str,
    state: str,
    auth_url: str,
    *,
    open_browser: bool,
    bind_address: str | None,
) -> str:
    try:
        redirect = urlparse(redirect_uri)
        host = redirect.hostname
        port = redirect.port
    except ValueError:
        host, port = None, None
    if not (
        host in ("127.0.0.1", "::1")
        and port
        and redirect.scheme == "http"
        and redirect.username is None
        and not redirect.fragment
    ):
        raise CallbackError(
            "Browser sign-in requires an HTTP loopback redirect with a port. "
            "Use a registered loopback URL or run with --manual."
        )
    if bind_address is not None and host != "127.0.0.1":
        raise CallbackError(
            "--callback-bind requires an IPv4 loopback redirect."
        )

    code: str | None = None
    denial: AuthorizationDenied | None = None

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            nonlocal code, denial
            if not self.path.startswith("/") or self.path.startswith("//"):
                self._reply(
                    400, "This request did not match the Spotify callback."
                )
                return
            try:
                candidate = f"http://{self.headers.get('Host', '')}{self.path}"
                code = parse_callback(candidate, redirect_uri, state)
            except AuthorizationDenied as exc:
                denial = exc
                self._reply(
                    403,
                    "Spotify authorization was denied. Return to your terminal.",
                )
            except CallbackError:
                self._reply(
                    400, "This request did not match the Spotify callback."
                )
            else:
                self._reply(
                    200,
                    "Authorization response received. Return to your terminal to finish.",
                )

        def log_message(self, format: str, *args: object) -> None:
            pass  # Request URLs contain the authorization code.

        def _reply(self, status: int, message: str) -> None:
            content = message.encode()
            with suppress(OSError):
                self.send_response(status)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(content)

    server_class = _IPv6CallbackServer if host == "::1" else _CallbackServer
    try:
        server = server_class((bind_address or host, port), Handler)
    except OSError:
        raise CallbackError(
            f"Could not listen for the Spotify callback on port {port}. "
            "Use another registered port or run with --manual."
        ) from None
    with server:
        print(f"Open this URL to authorize Spotify:\n{auth_url}", flush=True)
        deadline = monotonic() + CALLBACK_TIMEOUT
        if open_browser:
            with suppress(OSError, webbrowser.Error):
                webbrowser.open(auth_url)
        while code is None and denial is None:
            remaining = deadline - monotonic()
            if remaining <= 0:
                raise CallbackError(
                    "Spotify sign-in timed out. Run the sign-in command again."
                )
            server.timeout = remaining
            server.handle_request()
    if denial is not None:
        raise denial
    if code is None:
        raise CallbackError(
            "Spotify sign-in did not return an authorization code."
        )
    return code
