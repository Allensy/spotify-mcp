# Testing Guide for Spotify MCP

This guide explains how to test all functionalities of the Spotify MCP to ensure everything works as expected.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Test Scripts](#test-scripts)
3. [Manual Testing](#manual-testing)
4. [Integration Testing](#integration-testing)
5. [Docker Testing](#docker-testing)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Setup

1. **Spotify Developer Credentials**
   - Client ID and Client Secret from [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Configured redirect URI (e.g., `http://localhost:8765/callback`)

2. **Environment Variables**
   ```bash
   export SPOTIPY_CLIENT_ID="your_client_id"
   export SPOTIPY_CLIENT_SECRET="your_client_secret"
   export SPOTIPY_REDIRECT_URI="http://localhost:8765/callback"
   export SPOTIPY_CACHE_PATH=".cache/token"
   ```

3. **Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Active Spotify Session**
   - Have Spotify running on at least one device
   - Be playing or have played some music

## Test Scripts

### 1. Integration Tests

Tests the MCP server structure, tool registration, and configuration.

```bash
python test_mcp_integration.py
```

**What it tests:**
- ✅ Module imports
- ✅ MCP server creation
- ✅ Tool registration (32 tools)
- ✅ Function exports
- ✅ Configuration validation

**Expected Output:**
```
🔧 Spotify MCP Integration Tests
============================================================

Running integration tests...

✅ Module Imports: PASSED
✅ MCP Server Creation: PASSED
✅ Tool Registration: PASSED
   All 32 tools registered
✅ Spotify Tools Exports: PASSED
   All 33 functions exported
✅ Config Validation: PASSED
   All required config present

📊 Test Summary
============================================================
Total Tests: 5
✅ Passed: 5
❌ Failed: 0
Success Rate: 100.0%
============================================================

🎉 All integration tests passed!
```

### 2. Functionality Tests

Tests actual Spotify API interactions with your account.

```bash
python test_spotify_tools.py
```

**What it tests:**
- 🔍 **Search**: tracks, albums, artists, playlists
- 🎵 **Playback**: currently playing, playback state
- 📚 **Library**: liked songs, playlists, counts
- 🎼 **Audio Features**: features, analysis, recommendations
- 📋 **Queue**: queue viewing
- 📱 **Devices**: device listing
- 📊 **Analytics**: recently played, top tracks, top artists

**Expected Output:**
```
🎵 Spotify MCP Functionality Tests
============================================================

✅ Credentials configured
   Client ID: 1234567890...
   Scopes: user-read-playback-state user-modify-playback-state...

Running test suites...

✅ Search Tracks: PASSED
✅ Search Artists: PASSED
✅ Search Albums: PASSED
✅ Search Playlists: PASSED
✅ Get Currently Playing: PASSED
✅ Get Current Playback: PASSED
✅ Get Liked Songs Total: PASSED
✅ List Liked Songs: PASSED
✅ List User Playlists: PASSED
✅ Get Audio Features: PASSED
✅ Analyze Track: PASSED
✅ Get Audio Analysis: PASSED
✅ Get Track Recommendations: PASSED
✅ Get Queue: PASSED
✅ List Devices: PASSED
✅ Get Recently Played: PASSED
✅ Get Top Tracks: PASSED
✅ Get Top Artists: PASSED

📊 Test Summary
============================================================
Total Tests: 18
✅ Passed: 18
❌ Failed: 0
⏭️  Skipped: 0
Success Rate: 100.0%
============================================================

🎉 All tests passed successfully!
```

## Manual Testing

### Testing Individual Functions

Create a test script to test specific functionality:

```python
import asyncio
from spotify_tools import *

async def test_individual():
    # Test search
    result = await search_spotify("Beatles", "artist", limit=3)
    print(result)
    
    # Test currently playing
    result = await get_currently_playing()
    print(result)
    
    # Test queue
    result = await get_queue()
    print(result)
    
    # Test devices
    result = await list_devices()
    print(result)
    
    # Test top tracks
    result = await get_top_tracks(limit=5, time_range="short_term")
    print(result)

asyncio.run(test_individual())
```

### Testing via MCP Client

If you have an MCP client configured (like Claude Desktop):

1. **Start the MCP Server**
   ```bash
   python mcp_server.py
   ```

2. **Use the MCP Tools**
   - Ask Claude to search for songs
   - Request currently playing track
   - Ask for top tracks or artists
   - Request queue information
   - Control playback (play, pause, skip)

## Integration Testing

### Test with Cursor/Claude Desktop

1. **Configure MCP Client** (`claude_desktop_config.json` or similar):
   ```json
   {
     "mcpServers": {
       "spotify-mcp": {
         "command": "python",
         "args": ["/path/to/spotify-mcp/mcp_server.py"],
         "env": {
           "SPOTIPY_CLIENT_ID": "your_client_id",
           "SPOTIPY_CLIENT_SECRET": "your_client_secret",
           "SPOTIPY_REDIRECT_URI": "http://localhost:8765/callback",
           "SPOTIPY_CACHE_PATH": "/path/to/.cache/token"
         }
       }
     }
   }
   ```

2. **Test Through Chat**
   - "Search for rock music on Spotify"
   - "What am I currently listening to?"
   - "Show me my top 10 tracks from this month"
   - "List my Spotify devices"
   - "Add this song to my queue"

## Docker Testing

### Build and Test Docker Image

1. **Build the Image**
   ```bash
   docker build -t spotify-mcp:test .
   ```

2. **Run Authentication**
   ```bash
   docker run --rm -it \
     -v ${HOME}/.cache/spotify-mcp:/app/.cache \
     -e SPOTIPY_CLIENT_ID=your_id \
     -e SPOTIPY_CLIENT_SECRET=your_secret \
     -e SPOTIPY_REDIRECT_URI=http://localhost:8765/callback \
     -e SPOTIPY_CACHE_PATH=/app/.cache/token \
     spotify-mcp:test python -u auth_init.py
   ```

3. **Test MCP Server in Docker**
   ```bash
   docker run --rm -i \
     -v ${HOME}/.cache/spotify-mcp:/app/.cache \
     -e SPOTIPY_CLIENT_ID \
     -e SPOTIPY_CLIENT_SECRET \
     -e SPOTIPY_REDIRECT_URI \
     -e SPOTIPY_CACHE_PATH \
     spotify-mcp:test
   ```

## Troubleshooting

### Common Issues

#### 1. Authentication Errors
**Error:** `No token available`
**Solution:**
- Run `auth_init.py` to generate token
- Ensure redirect URI matches exactly
- Check that token cache path is writable

#### 2. No Active Device
**Error:** `No active device found`
**Solution:**
- Open Spotify app on any device
- Start playing something
- Run device listing: `await list_devices()`

#### 3. Permission Errors
**Error:** `Insufficient scope`
**Solution:**
- Delete cached token: `rm .cache/token`
- Re-authenticate with proper scopes
- Default scopes should include:
  - `user-read-playback-state`
  - `user-modify-playback-state`
  - `user-read-currently-playing`
  - `user-library-read`
  - `user-library-modify`
  - `user-top-read`
  - `user-read-recently-played`
  - `playlist-read-private`
  - `playlist-modify-public`
  - `playlist-modify-private`

#### 4. Rate Limiting
**Error:** `429 Too Many Requests`
**Solution:**
- Wait a few seconds between requests
- Spotify has rate limits per endpoint
- Tests include built-in delays

#### 5. Import Errors
**Error:** `ModuleNotFoundError: No module named 'spotipy'`
**Solution:**
```bash
pip install -r requirements.txt
```

### Debugging Tips

1. **Enable Verbose Logging**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Check Token Cache**
   ```bash
   cat .cache/token | python -m json.tool
   ```

3. **Test Credentials**
   ```python
   from spotify_tools import get_spotify_client
   sp = get_spotify_client()
   print(sp.current_user())
   ```

4. **Verify API Endpoints**
   - Check [Spotify Web API Reference](https://developer.spotify.com/documentation/web-api)
   - Ensure endpoints are available in your region

## Testing Checklist

Use this checklist to ensure comprehensive testing:

### Core Functionality
- [ ] Search tracks, albums, artists, playlists
- [ ] Get currently playing track
- [ ] Play/pause/next/previous controls
- [ ] Play specific songs by name or ID

### Library Management
- [ ] List liked songs
- [ ] Get liked songs count
- [ ] List user playlists
- [ ] List playlist tracks
- [ ] Add songs to liked
- [ ] Add songs to playlist

### Audio Features
- [ ] Get audio features for tracks
- [ ] Analyze track characteristics
- [ ] Get detailed audio analysis
- [ ] Find similar tracks
- [ ] Filter tracks by features
- [ ] Get recommendations

### Queue Management
- [ ] Add track to queue
- [ ] View current queue

### Device Management
- [ ] List available devices
- [ ] Transfer playback between devices

### Playback Controls
- [ ] Set shuffle on/off
- [ ] Set repeat mode
- [ ] Seek to position in track
- [ ] Adjust volume

### User Analytics
- [ ] Get recently played tracks
- [ ] Get top tracks (all time ranges)
- [ ] Get top artists (all time ranges)

### Integration
- [ ] MCP server starts successfully
- [ ] All tools registered correctly
- [ ] Works with MCP clients
- [ ] Docker container runs properly
- [ ] Authentication flow works

## Continuous Testing

### Before Committing Changes

Run both test suites:
```bash
python test_mcp_integration.py && python test_spotify_tools.py
```

### Before Releasing

1. Run full test suite
2. Test Docker build and run
3. Test with actual MCP client
4. Verify all 32 tools work
5. Check documentation is up-to-date

## Reporting Issues

If you find issues during testing:

1. Note the exact error message
2. Check which test failed
3. Verify credentials are correct
4. Check Spotify service status
5. Review the [Troubleshooting](#troubleshooting) section
6. Create an issue with:
   - Test output
   - Error logs
   - Environment details
   - Steps to reproduce


