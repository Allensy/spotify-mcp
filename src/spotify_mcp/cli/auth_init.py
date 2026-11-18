"""Sign in with Spotify and save the token for the MCP server."""

from __future__ import annotations

import argparse
import getpass
import secrets
import sys
import warnings

from dotenv import load_dotenv
from requests import RequestException
from spotipy import SpotifyOAuth
from spotipy.cache_handler import MemoryCacheHandler
from spotipy.exceptions import SpotifyOauthError

from spotify_mcp.auth import (
    build_oauth_manager,
    token_covers_settings,
    token_has_access,
)
from spotify_mcp.auth_cache import TokenCache, TokenCacheError
from spotify_mcp.cli.oauth_callback import (
    CallbackError,
    parse_callback,
    receive_callback,
)
from spotify_mcp.config import load_settings

# The Docker auth guide publishes the callback on host loopback only.
DOCKER_CALLBACK_BIND = "0.0.0.0"  # nosec B104


def _read_redirect() -> str:
    prompt = "Paste the full Spotify redirect URL: "
    if not sys.stdin.isatty():
        return input(prompt)
    with warnings.catch_warnings():
        warnings.simplefilter("error", getpass.GetPassWarning)
        try:
            return getpass.getpass(prompt)
        except getpass.GetPassWarning:
            raise CallbackError(
                "Could not hide the redirect in this terminal. Use another terminal or browser sign-in."
            ) from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manual",
        action="store_true",
        help="Paste the Spotify redirect URL without opening a listener.",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Print the authorization link without opening a browser.",
    )
    parser.add_argument(
        "--callback-bind",
        choices=[DOCKER_CALLBACK_BIND],
        help="Use only inside a sign-in container with a loopback-only host port.",
    )
    args = parser.parse_args(argv)

    load_dotenv()
    try:
        settings = load_settings()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    manual = args.manual or settings.auth_mode == "legacy"
    if manual and (args.no_open or args.callback_bind):
        parser.error(
            "--no-open and --callback-bind require automatic PKCE sign-in."
        )

    try:
        cache = TokenCache(settings)
        cache.read()
        staging = MemoryCacheHandler()
        state = secrets.token_urlsafe(32)
        manager = build_oauth_manager(settings, staging, state=state)
        auth_url = manager.get_authorize_url()
        if manual:
            print(
                f"Open this URL to authorize Spotify:\n{auth_url}", flush=True
            )
            redirected = _read_redirect()
            code = parse_callback(redirected, settings.redirect_uri, state)
        else:
            code = receive_callback(
                settings.redirect_uri,
                state,
                auth_url,
                open_browser=not args.no_open,
                bind_address=args.callback_bind,
            )

        if isinstance(manager, SpotifyOAuth):
            manager.get_access_token(
                code=code, as_dict=False, check_cache=False
            )
        else:
            manager.get_access_token(code=code, check_cache=False)
        token = staging.get_cached_token()
        if token is not None:
            token.setdefault("scope", settings.scope)
        if not (
            token
            and token_has_access(token)
            and token_covers_settings(token, settings)
            and isinstance(token.get("refresh_token"), str)
            and token["refresh_token"].strip()
        ):
            raise CallbackError(
                "Spotify returned an unusable token. Run the sign-in command again."
            )
        cache.write(token)
    except (CallbackError, TokenCacheError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("Spotify sign-in cancelled.", file=sys.stderr)
        return 1
    except (
        SpotifyOauthError,
        RequestException,
        KeyError,
        ValueError,
        TypeError,
    ):
        print(
            "Spotify sign-in failed. Check the Client ID and registered redirect URI, then try again.",
            file=sys.stderr,
        )
        return 1

    print(f"Spotify connected. Token saved to {cache.path}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
