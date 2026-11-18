# Spotify MCP authentication implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give new users one browser sign-in flow that needs only a Spotify Client ID, preserve existing client-secret installs, and make authentication failures recoverable in MCP clients.

**Architecture:** Resolve the authentication mode and cache location in `config.py`. Share token exchange, refresh and storage between the standalone sign-in command and tool runtime. Keep the short-lived browser callback in the CLI and give Spotipy an already authenticated client at runtime.

**Tech Stack:** Python 3.10+, Spotipy (`SpotifyOAuth`, `SpotifyPKCE`), MCP Python SDK 1.x, pytest, Docker and Docker Compose.

**Spec:** [Spotify MCP authentication design](../specs/2026-11-18-spotify-authentication-design.md)

## Global constraints

- The registered app and Client ID still come from the user. Existing configurations with a nonblank secret continue using legacy OAuth and their existing cache unless they explicitly switch modes.
- Keep `spotify-mcp` as the server command. Preserve `spotify-mcp-auth`, `python -m spotify_mcp.cli.auth_init`, and `python -m spotify_mcp.cli.main` for sign-in.
- Keep the existing scope defaults, `SPOTIFY_SCOPE`, MCP tool names and schemas, and stdio and SSE transports. Maintain the current SDK major-version constraint. No Spotify library or playback API migration in this change.
- New PKCE files default to `~/.cache/spotify-mcp/token-pkce.json`. Existing unmarked legacy files remain readable. An incompatible file is neither read as an access token nor overwritten. Writes are atomic, owner-only on POSIX, and contain no credentials other than the tokens needed for reuse.
- Sign-in may be interactive. MCP tool calls must never open a browser, listen for callbacks, or read from protocol stdin. HTTP 401 becomes an MCP sign-in error with no replay, and temporary failures leave the cache intact.
- Use dummy credentials and mocked Spotify responses in automated checks. Preserve pre-existing worktree changes, including the Hermes Compose edits. Do not publish an image or release as part of implementation verification.

## Review focus

- **Old configs with a secret and no auth mode:** They keep both the old mode and the exact cache path. Task 1 tests this with and without an explicit path.
- **A path reused across modes or client IDs:** A failed sign-in never overwrites another cache. Tasks 2 and 4 exercise reads and writes against incompatible files.
- **Non-callback traffic or an incorrect state:** A callback listener can still accept the subsequent legitimate request. Task 4 exercises this with real loopback HTTP requests and mocked token exchange.
- **A token is rejected before its recorded expiry:** One error is returned to the client with no replay. Task 3 exercises both a read and a mutation.
- **Login works inside the container but the client cannot reuse it:** Task 5 checks the host-only callback port and shared volume with a disposable Docker setup.

## Task 1: Resolve the auth mode and settings

**Files:** `src/spotify_mcp/config.py`, `tests/test_auth_config.py`, and the mode-specific credential check in `tests/test_server.py`.

**Interface:** Keep `load_settings() -> Settings` and the current settings fields. Add `Settings.auth_mode` (`pkce` or `legacy`) and allow `client_secret` to be `None`. Preserve the meaning of `cache_path=None` for legacy. For PKCE, resolve the explicit path or the per-user default before returning settings.

- [x] Add `test_pkce_configuration_needs_only_client_id`, `test_legacy_configuration_preserves_cache_path`, and `test_explicit_auth_mode_overrides_secret_detection`. Parameterize unset, blank, legacy, PKCE, and unknown mode values. Assert the exact default URI `http://127.0.0.1:8888/callback`, unchanged custom scopes and paths, no secret in effective PKCE settings, and a clear error for legacy without a secret or redirect.
- [x] Run `python -m pytest tests/test_auth_config.py -q`. Confirm that the old code rejects the Client-ID-only case and cannot resolve the new modes.
- [x] Implement selection and mode-specific validation in `load_settings()`. Keep dotenv and runtime transport behavior as it is. Adjust `tests/test_server.py` so its config validation expects a secret only in legacy mode.
- [x] Run `python -m pytest tests/test_auth_config.py tests/test_server.py tests/test_server_runtime.py -q`. Confirm PKCE and legacy configuration plus both transports pass.

## Task 2: Protect cached tokens and keep legacy data compatible

**Files:** Create `src/spotify_mcp/auth_cache.py` and `tests/test_auth_cache.py`.

**Interface:** Provide `TokenCache(settings: Settings)` with `read() -> dict | None` and `write(token: dict) -> None`. Distinguish missing data from an unreadable, malformed, or incompatible file with a typed exception that can name the path without including file contents. Use a reserved top-level `_spotify_mcp` marker with `version: 1` and `client_id` for PKCE files. Preserve ordinary Spotipy token fields and do not add the marker to legacy files.

- [x] Add `test_reads_existing_legacy_cache_without_rewriting`, `test_pkce_cache_round_trip_uses_private_permissions`, `test_does_not_read_or_replace_incompatible_cache`, and `test_failed_atomic_replace_preserves_previous_token`. Test marked PKCE versus unmarked legacy in both directions, a different Client ID, an unknown schema version, and invalid JSON. Assert that errors and test logs omit fixture credentials.
- [x] Run `python -m pytest tests/test_auth_cache.py -q` and confirm the storage API or behavior is absent.
- [x] Use Spotipy's cache path resolution for an unspecified legacy path, including its username override. Read and validate the marker before using a token. Write and flush a private temp file in the destination directory and replace the target atomically. Check compatibility before replacement, and report write errors even when the OAuth exchange succeeded. Keep token dictionaries and their metadata private to the cache and auth layer.
- [x] Run `python -m pytest tests/test_auth_cache.py -q`. Verify the unmarked legacy fixture remains byte-for-byte unchanged on read, the owner-only mode check passes on POSIX, and the original file survives a simulated failed write.

## Task 3: Authenticate MCP tools without an interactive fallback

**Files:** Create `src/spotify_mcp/auth.py` and `tests/test_auth_runtime.py`. Update `src/spotify_mcp/tools.py` at `get_spotify_client()` and existing Spotify exception handlers.

**Interfaces:** `get_access_token(settings: Settings) -> str` returns a cached or refreshed access token. `build_oauth_manager(settings, cache_handler, *, state=None)` builds the mode-specific Spotipy manager for refresh and login. `AuthenticationRequired` and `AuthenticationUnavailable` carry sanitized messages usable by the MCP error mechanism. Keep `tools.get_spotify_client()` and every public tool signature unchanged.

- [x] Add `test_runtime_refreshes_in_both_modes`, `test_runtime_reconnects_after_cache_appears`, `test_signed_out_and_invalid_grant_are_mcp_errors`, `test_transient_refresh_failure_keeps_cache`, and `test_spotify_401_is_an_mcp_error_without_replay`. Use mocked Spotify token and API transports, while exercising the actual MCP tool wrappers. Assert `isError` for auth failures, no browser/stdin interactions, and one API attempt for both `search` and a mutation such as `pause`. Also cover a refresh response without a replacement refresh token, insufficient scopes, and cache read failures.
- [x] Run `python -m pytest tests/test_auth_runtime.py -q`. Confirm that the current path lacks noninteractive auth handling.
- [x] Read the cache on each client creation, check required scopes and expiration, and refresh only from cached credentials. Use the matching Spotipy manager's refresh operation with an in-memory cache handler so the app controls the persistent write and errors. If the response omits the refresh token or scope metadata, retain the old value. Check the refreshed token and scopes before persisting. Treat `invalid_grant` as a sign-in error and timeouts or temporary upstream failures as retryable. Avoid SDK debug traces that include OAuth requests.
- [x] Construct the Spotipy API client with the acquired access token so SDK fallback cannot be interactive. Normalize HTTP 401 into `AuthenticationRequired` before existing broad tool exception handlers format other errors. Propagate auth exceptions through those handlers so FastMCP reports a tool error. Preserve unrelated error behavior and never replay the request.
- [x] Run `python -m pytest tests/test_auth_runtime.py tests/test_server.py tests/test_server_runtime.py -q`. Verify the cache can appear after startup and the very next tool call uses it.

## Task 4: Share the sign-in command and add browser callbacks

**Files:** `src/spotify_mcp/cli/auth_init.py`, `src/spotify_mcp/cli/main.py`, a focused callback helper at `src/spotify_mcp/cli/oauth_callback.py`, and `tests/test_auth_login.py`. Reuse the OAuth manager factory and error handling in `src/spotify_mcp/auth.py`.

**Interfaces:** `cli.auth_init.main(argv: list[str] | None = None) -> int` is the common CLI implementation. Preserve zero-argument invocation of both module entry points and the installed command. Support `--manual`, `--no-open`, and `--callback-bind`. Automatic sign-in is the PKCE default, and legacy retains manual as its default.

- [x] Add `test_browser_login_saves_pkce_token`, `test_manual_login_uses_same_pkce_exchange`, `test_legacy_login_alias_uses_existing_flow`, and `test_listener_ignores_unrelated_requests`. Test with a mock token endpoint or patched HTTP transport and an ephemeral loopback listener. Inspect the authorize URL for state and `code_challenge_method=S256`. Confirm the exchange uses the corresponding verifier and no client secret. Assert the right status and safe output for wrong state or redirect, denial, missing code, port conflict, timeout, `Ctrl+C`, and failed cache writes. Use fixtures to verify that unsuccessful attempts preserve existing tokens.
- [x] Run `python -m pytest tests/test_auth_login.py -q`. Confirm that the current command cannot do PKCE with a loopback callback.
- [x] Parse flags and resolve settings once. Generate one random state per attempt. Use one OAuth manager instance to construct the URL and exchange the verified code with cache lookup disabled. Stage token data in memory, check the access token, refresh token, expiration, and required scopes, then persist it with `TokenCache`. Reject incompatible cache paths before sign-in and recheck on write. Keep the same exchange path and validation for browser and manual mode.
- [x] For automatic sign-in, secure the configured loopback address before opening the browser and enforce a five-minute overall deadline. Use the configured path and port. Accept only the matching callback request, and keep listening after unrelated or invalid input. Close the listener in every exit path. In Docker, `--callback-bind 0.0.0.0` binds inside the container while the redirect URI still points to `127.0.0.1` on the host. `--no-open` prints the link without invoking a browser. Keep manual mode listener-free and disallow listener-only flags with `--manual`.
- [x] Make the legacy module and installed script delegate to the common CLI and propagate its exit code. Keep port, denial, timeout, and cache errors actionable. Exclude codes, verifier values, secrets, and token data from status pages, callback request logs, and CLI output.
- [x] Run `python -m pytest tests/test_auth_login.py tests/test_auth_runtime.py -q`. Confirm the manual and automatic paths create the same token format and both Docker module entry points still work.

## Task 5: Document and verify the Python and Docker setup paths

**Files:** `README.md`, `.env.example`, `Makefile`, `docker-compose.spotify-mcp.yml`, and `TESTING.md`. Rely on the existing test workflow for mocked OAuth tests.

- [x] Update the main quick start to show the Developer Dashboard app, Client ID, exact redirect, one auth command, and a first search. Show local `spotify-mcp-auth`, Docker with `--no-open --callback-bind 0.0.0.0` and `-p 127.0.0.1:8888:8888`, and the `--manual` variant with no port. Use `/app/.cache/token-pkce.json` and the same host mount in both Docker commands. Keep the running MCP container free of auth port mappings. Explain how to reopen sign-in when a cached authorization expires or is revoked.
- [x] Retain the standalone Compose default cache `/app/.cache/token` for existing installs and allow `SPOTIPY_CACHE_PATH` to override it for new PKCE users. Pass through `SPOTIFY_AUTH_MODE` and use an empty default for the optional secret. Keep the legacy credentials and cache examples clearly labeled. Update `make docker-auth` to use the common module and PKCE path for a no-secret config while retaining the legacy cache for an existing secret-based config. Document that the current Hermes example keeps its legacy cache setup unless configured with a separate PKCE path. Preserve the existing Hermes edits.
- [x] Run `python -m pytest`, `python tests/test_structure.py`, and `git diff --check`. Run the repo's formatting checks on the changed Python files. Validate Compose with dummy values via `docker compose -f docker-compose.spotify-mcp.yml --env-file .env.example config`, and inspect the resolved cache mount and environment for both modes.
- [x] Build a disposable local image. Exercise the documented temporary callback and cache volume with a mocked Spotify token exchange, using a test-only harness and dummy credentials. Check that the browser's loopback request reaches the auth container, the container exits, and the normal container can mount the resulting token without a callback port. Connect with MCP Inspector over stdio and check tool discovery, the signed-out error, and a successful search using a mock response. Record the commands in `TESTING.md` if they are useful for maintainers to rerun.
- [ ] Before release, use a real Spotify Developer Dashboard app and run a fresh local or Docker browser sign-in, then search from an MCP client. Verify that the manual path and an old cache can still be used. Record which checks were run and which required credentials. This check does not require publishing a new image.

## Completion criteria

Run each task's verification before moving on. At the end, map results to the spec's acceptance list and report any missing real-account check explicitly. Stop for review before publishing. Stage only this change if asked to commit, since the checkout already has unrelated changes.

## Review adjustments

- [x] Serialize token refresh and sign-in writes with a file lock. Test that a refresh in flight cannot overwrite a newer sign-in.
- [x] Mask the pasted redirect in interactive terminals, while preserving redirected input. Test that the interactive path does not use the echoing prompt.
- [x] Have `make docker-auth` publish the port requested in an IPv4 loopback redirect. Validate the default, custom port, and manual paths with `make -n docker-auth`.
