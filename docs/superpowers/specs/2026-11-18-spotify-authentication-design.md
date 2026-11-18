# Spotify MCP authentication design

## Problem and goal

The current setup asks users to put a Spotify client secret in their configuration and paste a browser redirect into a terminal. The Docker module and the installed `spotify-mcp-auth` command implement that sequence separately. At runtime, the server passes an interactive OAuth manager to Spotipy, so a missing or unusable token can kick off sign-in during a tool call.

A new local user should register a Spotify app, provide its Client ID, approve access in a browser, and return to a terminal that confirms the token was saved. The same OAuth implementation should serve Python and Docker installs. Existing installations should continue using their saved tokens without any config changes. A tool call should either have an authenticated Spotify client or return a clear, noninteractive error.

## Approaches

| Approach | Tradeoff |
| --- | --- |
| Add a browser callback to the existing client-secret flow | Smaller change that removes redirect pasting, but retains secret handling in desktop and container configurations. |
| Use Authorization Code with PKCE locally, with a manual option and a compatible legacy path | Removes the client secret and the default copy-paste step. Requires coordinating configuration, token storage, sign-in, and refresh. **Selected for this design.** |
| Host a shared authorization service | Could hide app setup from end users, but requires a service, user isolation, and a separate Spotify access and policy review. Out of scope. |

## Configuration and compatibility

- Add `SPOTIFY_AUTH_MODE` with values `pkce` and `legacy`. An unset or empty value selects `legacy` if a nonblank `SPOTIPY_CLIENT_SECRET` is present, and `pkce` otherwise. Unknown values are configuration errors. An explicit mode takes precedence over inference.
- Both modes require `SPOTIPY_CLIENT_ID`. PKCE defaults `SPOTIPY_REDIRECT_URI` to `http://127.0.0.1:8888/callback`, accepts an override, and never sends or requires a client secret. Legacy continues requiring `SPOTIPY_CLIENT_SECRET` and `SPOTIPY_REDIRECT_URI`, as it does today.
- Preserve `SPOTIFY_SCOPE` and the default scopes in both modes. The authorization request and cached token must cover the configured scopes. Changes to the tool set, names, schemas, and Spotify endpoints are out of scope.
- Preserve the legacy cache location and format, including `SPOTIPY_CACHE_PATH` and Spotipy's existing default when it is unset. Use `~/.cache/spotify-mcp/token-pkce.json` by default for PKCE. An explicit `SPOTIPY_CACHE_PATH` is an exact file path in either mode. A Docker example sets it to `/app/.cache/token-pkce.json` and mounts the same directory for sign-in and runtime.
- A new PKCE cache carries a schema version and the originating Client ID. Reject a cache from another Client ID or mode, and keep unmatched files intact. PKCE never interprets an unmarked legacy cache as its own. Legacy refuses marked PKCE files, but keeps accepting existing unmarked Spotipy caches. An invalid cache gets an actionable error that identifies the configured cache path and tells the user to choose a new path or move the old file aside. A valid PKCE cache can be replaced by explicit successful login for the same Client ID.

## Sign-in

The canonical Python command is `spotify-mcp-auth`. The current Docker entry point `python -m spotify_mcp.cli.auth_init` and the equivalent `python -m spotify_mcp.cli.main` remain callable and delegate to the same implementation. The `spotify-mcp` server command is unchanged.

1. In PKCE mode, the default flow starts a temporary HTTP listener on the configured loopback IP and port, then prints and opens the Spotify consent URL. Supported automatic callback addresses use `http://127.0.0.1:<port>/<path>` or `http://[::1]:<port>/<path>`. The configured URI must match the registered one. If opening the browser fails, the printed link remains usable. If the port is in use, fail with a clear message and suggest `--manual` or another registered port. The listener times out after five minutes and closes on success, denial, interruption, or timeout.
2. `--manual` prints the consent URL and asks for the full redirect URL, with no browser launch or listener. This is the documented headless path and remains the default for legacy configurations. Both paths generate a fresh OAuth state, match the returned state and redirect target to that attempt, and exchange only a nonempty authorization code. PKCE uses S256 and a fresh verifier retained in memory. Unrelated HTTP requests must not consume the listener's one valid callback. A callback denial with matching state is a normal failed sign-in.
3. Local Docker sign-in uses a one-shot container with `--no-open --callback-bind 0.0.0.0` and publishes the callback on **host loopback only**, for example `-p 127.0.0.1:8888:8888`. The advertised redirect stays `127.0.0.1`. Non-loopback listener binding is explicit and limited to automatic sign-in inside a container. Runtime containers never publish a Spotify callback port. Headless users can keep that port closed and use `--manual`.
4. Confirm success only after a usable token is saved. Exit nonzero on a denied, invalid, interrupted or failed sign-in. Keep any existing usable token if a new sign-in fails. The success page and terminal never display tokens, codes, verifiers, or secrets. Give users a clear next action for port errors, expired attempts, and unwritable cache locations.

For new cache writes, create files with owner-only permissions on POSIX and replace atomically. Serialize refresh and sign-in writes across processes sharing a cache so an in-flight refresh cannot overtake a new sign-in. Refresh must preserve the prior refresh token if Spotify omits a replacement. In an interactive terminal, mask manual redirect input. Protect OAuth material from application logs and SDK debug output. Keep legacy data compatible with existing Spotipy readers. No new persistent service or credential store is required.

## MCP runtime

- Validate configuration at startup as today. A configured server can initialize and list tools even before the user signs in.
- When a tool needs Spotify, use a cached access token if usable, or refresh it through the configured mode. The runtime path must never invoke a browser, listener, prompt, or interaction with MCP standard input. Each tool uses one authenticated client. Read the cache on each client creation so a completed login is recognized without restarting the MCP server.
- Missing tokens, insufficient scopes, an invalid cache, or a revoked or expired refresh token must surface as an MCP tool error, not a successful tool response containing an error string. The message directs the user to run `spotify-mcp-auth` or the Docker sign-in command from the quick start and gives any specific remediation, such as an incompatible cache path. Temporary Spotify or network failures get a retryable error and leave the cache intact. Never retry an operation that can change playback or the library merely because authentication failed.
- If Spotify returns HTTP 401 for a token that looked usable locally, surface the same sign-in error. Do not refresh or replay the request in that tool call, even for a read. Keep the cache intact until the user signs in again. This keeps the recovery rule the same for reads and mutations.

## Acceptance

- PKCE works in a clean configuration with only a Client ID. The browser callback uses `state` and S256, saves a token to the expected path, and renders a plain completion page. Wrong state, wrong callback path, refusal, timeout, port conflict, cancellation, and failed token writes have explicit outcomes.
- The Docker callback works via the documented host loopback port and the runtime container reuses the mounted cache with no auth port. Manual PKCE sign-in produces the same cache without a listener. One command guide covers the shared behavior and explains when to use manual mode.
- An existing client-secret configuration uses its existing cache unchanged and refreshes through the legacy flow. Neither mode can read the other mode's cache or replace it on login. A server already running reads the newly saved token on its next tool call.
- An installed MCP client can list tools when signed out, receives a prompt-free MCP error when calling Spotify while signed out, and can run a search after sign-in. CI uses a fake Spotify endpoint or mocked token transport and dummy credentials. A real local or Docker browser sign-in with a Developer Dashboard app and a search against Spotify are release checks, separate from CI.

## Out of scope

Creating a Spotify Developer Dashboard app programmatically, managing multiple users in one runtime, hosted authorization, changing MCP transports, changing playback behavior, migrating old caches to PKCE, or switching Spotify library endpoints. UI wording and helper layout may be chosen during implementation. The mode selection and cache compatibility rules above are part of the public behavior.

References: [Spotify authorization flows](https://developer.spotify.com/documentation/web-api/concepts/authorization), [PKCE flow](https://developer.spotify.com/documentation/web-api/tutorials/code-pkce-flow), [redirect URI rules](https://developer.spotify.com/documentation/web-api/concepts/redirect_uri), [refreshing tokens](https://developer.spotify.com/documentation/web-api/tutorials/refreshing-tokens).
