# MCP Spotify Server - Improvements Summary

## Changes Made to Fix Hanging Issues and Improve Auth

### Problem Identified

The MCP tools were hanging indefinitely when called by the AI agent. Root causes:

1. **Missing/invalid authentication tokens** - Spotipy tried to open a browser for OAuth in Docker stdio mode, causing infinite hang
2. **No timeout handling** - Network/API calls could block forever
3. **Poor error messages** - Users didn't know what went wrong

### Solutions Implemented

#### 1. ✅ Prevent Hanging with Better Error Handling

**File: `src/spotify_mcp/tools.py`**

- Added `open_browser=False` to SpotifyOAuth to prevent browser opening attempts in Docker
- Check for cached token before initializing client
- Raise informative `RuntimeError` if token is missing/invalid with clear instructions
- Created `spotify_api_call()` helper function for universal timeout protection (15s default)
- Applied timeout protection to **ALL 25 async Spotify API functions**:
  - Playback controls: play, pause, next_track, previous_track, get_currently_playing
  - Song playback: play_song, play_song_by_id, search_spotify
  - Library management: list_user_playlists, list_liked_songs, list_playlist_songs, add_songs_to_liked, add_songs_to_playlist, get_liked_songs_total
  - Queue operations: add_to_queue, get_queue  
  - Analytics: get_recently_played, get_top_tracks, get_top_artists
  - Device control: list_devices, transfer_playback
  - Playback settings: set_shuffle, set_repeat, seek_position, set_volume
- All Spotify API calls now run in thread pool with timeout via `asyncio.wait_for()` and `asyncio.to_thread()`

**Benefits:**

- Tools now **fail fast with clear error messages** instead of hanging
- Users get actionable instructions on how to fix auth issues
- Network/API issues timeout after 15s with helpful error message

#### 2. ✅ Improved Browser-Based Authentication

**File: `src/spotify_mcp/cli/auth_init.py`**

Added **automatic browser-based OAuth flow** (similar to Atlassian MCP server):

**New `--auto` flag:**

```bash
python -m spotify_mcp.cli.auth_init --auto
```

Features:

- Automatically opens browser to Spotify auth page
- Starts local HTTP server to catch OAuth callback
- Shows success/failure page in browser
- No copy-paste needed!

**Manual flow still available** (omit `--auto` flag) for environments where browser opening doesn't work.

**Benefits:**

- Much better UX - no copy-pasting URLs
- Works like professional OAuth flows
- Clear success/failure feedback in browser

#### 3. ✅ Updated Documentation

**File: `README.md`**

- Added automatic auth flow instructions with `--auto` flag
- Improved troubleshooting section with new error messages
- Added timeout error handling guidance
- Clarified token cache path requirements

**File: `scripts/build-local.sh`** (NEW)

- Quick script to rebuild Docker image locally for testing
- Shows usage examples

#### 4. ✅ Fixed Container Lifecycle

**File: `src/spotify_mcp/server.py`**

- Changed exception handler in `main()` to use `os._exit(0)` instead of `sys.exit(0)`
- Ensures forceful termination consistent with signal_handler and stdin_monitor
- Prevents hanging from atexit handlers or cleanup code that could block sys.exit()
- All three shutdown paths now use `os._exit()` for reliability

### How to Test the Fixes

#### Step 1: Rebuild Docker Image Locally

```bash
cd /Users/allenjacobson/Dev/spotify-mcp
./scripts/build-local.sh
```

This creates `spotify-mcp-local:latest` with your changes.

#### Step 2: Update MCP Config

Edit your MCP client config (`~/.cursor/mcp.json` or similar):

```json
{
  "mcpServers": {
    "spotify-mcp": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "/Users/allenjacobson/.cache/spotify-mcp:/app/.cache",
        "-e", "SPOTIPY_CLIENT_ID",
        "-e", "SPOTIPY_CLIENT_SECRET",
        "-e", "SPOTIPY_REDIRECT_URI",
        "-e", "SPOTIPY_CACHE_PATH",
        "spotify-mcp-local:latest"
      ],
      "env": {
        "SPOTIPY_CLIENT_ID": "mockid",
        "SPOTIPY_CLIENT_SECRET": "mocksecret",
        "SPOTIPY_REDIRECT_URI": "http://127.0.0.1:8888/callback",
        "SPOTIPY_CACHE_PATH": "/app/.cache/token"
      }
    }
  }
}
```

**Note:** Changed from `docker.io/allesy/spotify-mcp` to `spotify-mcp-local:latest`

#### Step 3: Test Authentication with Browser Flow

```bash
docker run --rm -it \
  -v /Users/allenjacobson/.cache/spotify-mcp:/app/.cache \
  -e SPOTIPY_CLIENT_ID=mockid \
  -e SPOTIPY_CLIENT_SECRET=mocksecret \
  -e SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback \
  -e SPOTIPY_CACHE_PATH=/app/.cache/token \
  spotify-mcp-local:latest python -u -m spotify_mcp.cli.auth_init --auto
```

Expected behavior:

- Browser opens automatically to Spotify auth page
- Click "Agree"
- Browser shows success page
- Terminal confirms token saved
- Token cached at `/Users/allenjacobson/.cache/spotify-mcp/token`

#### Step 4: Test MCP Tools

1. Restart your MCP client (Cursor)
2. Try using a Spotify tool (e.g., "search for Taylor Swift")
3. Expected outcomes:
   - ✅ **If authenticated**: Tool works normally
   - ✅ **If not authenticated**: Clear error message: "No valid Spotify authentication token found. Please run the authorization flow first..."
   - ✅ **If network issue**: Timeout after 15s with clear error
   - ❌ **No more hanging!**

### Expected Behavior Changes

| Scenario | Before | After |
|----------|--------|-------|
| Missing token | Hangs forever | Clear error: "No valid token found. Please run auth..." |
| Network timeout | Hangs forever | Fails after 15s: "Operation timed out..." |
| Invalid credentials | Hangs forever | Clear error with troubleshooting steps |
| Auth flow | Manual copy-paste only | Automatic browser flow with `--auto` |

### Error Messages You'll See

1. **Missing Token:**

   ```
   RuntimeError: No valid Spotify authentication token found. 
   Please run the authorization flow first. 
   In Docker: docker run -it -v /path/to/cache:/app/.cache <image> python -m spotify_mcp.cli.auth_init
   ```

2. **Timeout:**

   ```
   RuntimeError: Operation 'search_spotify' timed out after 15s. 
   This may indicate network issues or authentication problems. 
   Please check your Spotify token and network connectivity.
   ```

3. **Auth Error:**

   ```
   RuntimeError: Failed to initialize Spotify client: <details>. 
   This usually means the token cache is missing or invalid. 
   Please complete the OAuth authorization flow.
   ```

### Technical Details

**Timeout Implementation:**

- Created `spotify_api_call()` helper that wraps ANY Spotify API call
- Uses `asyncio.to_thread()` to run sync Spotipy calls in thread pool  
- `asyncio.wait_for()` with 15s timeout (configurable)
- Catches `asyncio.TimeoutError` and converts to helpful RuntimeError with function name
- Applied universally to ALL 25 async functions (100% coverage)

**Auth Changes:**

- `open_browser=False` prevents Spotipy's automatic browser opening
- Token validation happens at client creation time
- Clear error messages guide users to fix auth issues

**Browser Flow:**

- Local HTTP server on port 8888 (matches redirect URI)
- Handles OAuth callback automatically
- Shows HTML success/failure page
- 120s timeout for user action

### Next Steps

1. **Test the changes** using the steps above
2. **If everything works**, you can:
   - Push changes to GitHub
   - Rebuild and push to Docker registry
   - Update the published image tag
3. **If issues remain**, we have detailed logs and error messages to debug further

### Files Changed

- `src/spotify_mcp/tools.py` - Added comprehensive timeout protection to ALL 25 Spotify API functions
- `src/spotify_mcp/server.py` - Fixed exception handler to use os._exit() for consistency
- `src/spotify_mcp/cli/auth_init.py` - Added automatic browser OAuth flow
- `README.md` - Updated documentation with new auth flow and troubleshooting
- `scripts/build-local.sh` - NEW: Quick build script for testing
- `IMPROVEMENTS.md` - THIS FILE: Accurately documents all changes

No breaking changes - existing manual auth flow still works!
