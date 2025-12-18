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
- Added `with_timeout()` decorator for async operations (15s timeout default)
- Wrapped sync Spotify API calls to run in thread pool with timeout

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
- Uses `asyncio.to_thread()` to run sync Spotipy calls in thread pool
- `asyncio.wait_for()` with 15s timeout
- Catches `asyncio.TimeoutError` and converts to helpful RuntimeError

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

- `src/spotify_mcp/tools.py` - Added error handling and timeouts
- `src/spotify_mcp/cli/auth_init.py` - Added automatic browser OAuth flow
- `README.md` - Updated documentation with new auth flow and troubleshooting
- `build-local.sh` - NEW: Quick build script for testing

No breaking changes - existing manual auth flow still works!

