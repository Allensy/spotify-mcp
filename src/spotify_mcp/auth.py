"""Spotify OAuth helpers that keep interactive login out of tool calls."""

from __future__ import annotations

import logging
from time import time
from typing import Any

from requests import RequestException
from spotipy import Spotify, SpotifyException, SpotifyOAuth, SpotifyPKCE
from spotipy.cache_handler import CacheHandler, MemoryCacheHandler
from spotipy.exceptions import SpotifyOauthError

from spotify_mcp.auth_cache import TokenCache, TokenCacheBusy, TokenCacheError
from spotify_mcp.config import Settings

# Spotipy's debug logs include OAuth request payloads and bearer headers.
logging.getLogger("spotipy.oauth2").setLevel(logging.INFO)
logging.getLogger("spotipy.client").setLevel(logging.INFO)

SIGN_IN = (
    "Run spotify-mcp-auth or the Docker sign-in command in the quick start."
)


class AuthenticationRequired(RuntimeError):
    """Spotify requires the user to sign in again."""


class AuthenticationUnavailable(RuntimeError):
    """Authentication could not finish because of a temporary failure."""


class _LegacyOAuth(SpotifyOAuth):
    def _add_custom_values_to_token_info(
        self, token_info: dict[str, Any]
    ) -> dict[str, Any]:
        # SpotifyOAuth normally overwrites the scopes from the token response.
        token_info["expires_at"] = int(time()) + token_info["expires_in"]
        return token_info


def build_oauth_manager(
    settings: Settings,
    cache_handler: CacheHandler,
    *,
    state: str | None = None,
) -> SpotifyOAuth | SpotifyPKCE:
    if settings.auth_mode == "pkce":
        return SpotifyPKCE(
            client_id=settings.client_id,
            redirect_uri=settings.redirect_uri,
            scope=settings.scope,
            state=state,
            cache_handler=cache_handler,
            open_browser=False,
            requests_timeout=10,
        )
    return _LegacyOAuth(
        client_id=settings.client_id,
        client_secret=settings.client_secret,
        redirect_uri=settings.redirect_uri,
        scope=settings.scope,
        state=state,
        cache_handler=cache_handler,
        open_browser=False,
        requests_timeout=10,
    )


def token_covers_settings(token: dict[str, Any], settings: Settings) -> bool:
    scope = token.get("scope")
    return isinstance(scope, str) and set(settings.scope.split()).issubset(
        scope.split()
    )


def token_has_access(token: dict[str, Any]) -> bool:
    access_token = token.get("access_token")
    expires_at = token.get("expires_at")
    return (
        isinstance(access_token, str)
        and bool(access_token.strip())
        and isinstance(expires_at, int | float)
        and expires_at > time()
    )


def get_access_token(settings: Settings) -> str:
    cache = TokenCache(settings)
    try:
        token = _read_token(cache, settings)
        if token_has_access(token):
            return str(token["access_token"])

        # A concurrent login or refresh may already have replaced this token.
        with cache.lock():
            token = _read_token(cache, settings)
            if not token_has_access(token):
                token = _refresh_token(settings, token)
                cache.write(token)
        return str(token["access_token"])
    except TokenCacheBusy as exc:
        raise AuthenticationUnavailable(str(exc)) from None
    except TokenCacheError as exc:
        raise AuthenticationRequired(f"{exc} {SIGN_IN}") from None


def _read_token(cache: TokenCache, settings: Settings) -> dict[str, Any]:
    token = cache.read()
    if token is None:
        raise AuthenticationRequired(f"Spotify is signed out. {SIGN_IN}")
    if not token_covers_settings(token, settings):
        raise AuthenticationRequired(
            f"Spotify permissions have changed. {SIGN_IN}"
        )
    return token


def _refresh_token(
    settings: Settings, token: dict[str, Any]
) -> dict[str, Any]:
    refresh_token = token.get("refresh_token")
    if not isinstance(refresh_token, str) or not refresh_token.strip():
        raise AuthenticationRequired(
            f"Spotify authorization has expired. {SIGN_IN}"
        )

    manager = build_oauth_manager(settings, MemoryCacheHandler())
    try:
        renewed: dict[str, Any] = manager.refresh_access_token(refresh_token)
    except SpotifyOauthError as exc:
        if exc.error in {
            "invalid_grant",
            "invalid_client",
            "unauthorized_client",
        }:
            raise AuthenticationRequired(
                f"Spotify rejected authorization. {SIGN_IN}"
            ) from None
        raise AuthenticationUnavailable(
            "Spotify could not refresh authorization. Try again."
        ) from None
    except (RequestException, KeyError, TypeError, ValueError):
        raise AuthenticationUnavailable(
            "Spotify could not refresh authorization. Try again."
        ) from None

    renewed.setdefault("scope", token["scope"])
    renewed.setdefault("refresh_token", refresh_token)
    if not token_covers_settings(renewed, settings):
        raise AuthenticationRequired(
            f"Spotify permissions have changed. {SIGN_IN}"
        )
    if not token_has_access(renewed):
        raise AuthenticationUnavailable(
            "Spotify returned an unusable access token. Try again."
        )
    return renewed


class AuthenticatedSpotify(Spotify):
    """Translate Spotify's rejected bearer token to an actionable MCP error."""

    def _internal_call(
        self, method: str, url: str, payload: Any, params: dict[str, Any]
    ) -> Any:
        try:
            return super()._internal_call(method, url, payload, params)
        except SpotifyException as exc:
            if exc.http_status == 401:
                raise AuthenticationRequired(
                    f"Spotify rejected authorization. {SIGN_IN}"
                ) from None
            raise
