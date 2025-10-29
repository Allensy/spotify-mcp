# Spotify MCP Server

A Model Context Protocol (MCP) server that exposes Spotify controls and queries as MCP tools using Spotipy.

**Ready to use via Docker** - No local Python install required!

## Quick Start (3 steps)

### 1. Get Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create an app (or use an existing one)
3. Note your **Client ID** and **Client Secret**
4. Add `http://127.0.0.1:8888/callback` to **Redirect URIs** in app settings
5. If your app is in "Development Mode", add your Spotify account email to the **User Management** section

### 2. One-Time Authentication (Docker)

Run this command to authenticate (replace with your credentials):

```bash
docker run --rm -it \
  -v ${HOME}/.cache/spotify-mcp:/app/.cache \
  -e SPOTIPY_CLIENT_ID=your-client-id \
  -e SPOTIPY_CLIENT_SECRET=your-client-secret \
  -e SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback \
  -e SPOTIPY_CACHE_PATH=/app/.cache/token \
  docker.io/allesy/spotify-mcp:latest python -u -m spotify_mcp.cli.auth_init
```

- Open the URL shown in your browser
- Authorize the app
- Copy the full redirect URL from your browser and paste it back into the terminal
- Done! Token is saved.

### 3. Add to Your MCP Client

Add this to your MCP client config (e.g., `~/.cursor/mcp.json` for Cursor, or Claude Desktop's config):

```json
{
  "mcpServers": {
    "spotify": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "/Users/YOUR_USERNAME/.cache/spotify-mcp:/app/.cache",
        "-e", "SPOTIPY_CLIENT_ID",
        "-e", "SPOTIPY_CLIENT_SECRET",
        "-e", "SPOTIPY_REDIRECT_URI",
        "-e", "SPOTIPY_CACHE_PATH",
        "docker.io/allesy/spotify-mcp:latest"
      ],
      "env": {
        "SPOTIPY_CLIENT_ID": "your-client-id",
        "SPOTIPY_CLIENT_SECRET": "your-client-secret",
        "SPOTIPY_REDIRECT_URI": "http://127.0.0.1:8888/callback",
        "SPOTIPY_CACHE_PATH": "/app/.cache/token"
      }
    }
  }
}
```

**Important**: Replace `/Users/YOUR_USERNAME` with your actual home directory path (some MCP clients don't expand `${HOME}`).

That's it! Restart your MCP client and start controlling Spotify! 🎵

---

## Features (tools)

### Playback & Library

- **search**: Search tracks, albums, artists, or playlists
- **play / pause / next_track / previous_track**: Control playback
- **currently_playing**: Get friendly now-playing string
- **play_song**: Search by name and play first result
- **play_by_id**: Play a track or playlist by Spotify ID/URI
- **list_playlists**: List user playlists
- **list_liked**: List liked songs
- **list_playlist_songs**: List songs in a playlist by ID
- **add_to_liked**: Add tracks to Liked Songs
- **add_to_playlist**: Add tracks to a playlist
- **liked_total**: Count of tracks in Liked Songs
- **add_to_queue**: Add tracks to playback queue
- **get_queue**: View current queue
- **get_recently_played**: View listening history
- **get_top_tracks / get_top_artists**: View your most played tracks and artists
- **list_devices**: List available Spotify devices
- **transfer_playback**: Move playback to different device
- **set_shuffle / set_repeat**: Control playback modes
- **seek_position / set_volume**: Fine-tune playback

## Prerequisites

- **Docker** installed on your system
- **Spotify Developer app** (free) - Create one at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
  - Client ID and Client Secret
  - Redirect URI: `http://127.0.0.1:8888/callback` added to app settings
  - Your Spotify email added to User Management (if in Development Mode)

## Pull from registry (no local build)

If you are using the published image, pull it directly:

```bash
docker pull docker.io/allesy/spotify-mcp:latest
```

Then follow the First-time OAuth section below and the MCP client config example, both of which reference the registry image.

## Environment variables

Provide these via your MCP client config (do not hardcode). These names match Spotipy conventions and are what the server expects.

Required:

- `SPOTIPY_CLIENT_ID`
- `SPOTIPY_CLIENT_SECRET`
- `SPOTIPY_REDIRECT_URI`

Optional:

- `SPOTIFY_SCOPE`: Override the default OAuth scope (space-delimited scopes). Defaults to a broad set enabling playback and library/playlist operations.
- `SPOTIPY_CACHE_PATH`: Token cache file path (inside container). Useful when you want to control the exact cache location. When running Docker, combine with a bind mount to persist the cache.

## Build

```bash
docker build -t spotify-mcp:latest .
```

## Using with an MCP client (Docker/stdio)

Example MCP client configuration (JSON) that runs the server via Docker and passes env vars. Adapt paths for your client (Claude Desktop, Cursor, etc.).

```json
{
  "mcpServers": {
    "spotify-mcp": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-v",
        "${HOME}/.cache/spotify-mcp:/app/.cache",
        "-e", "SPOTIPY_CLIENT_ID",
        "-e", "SPOTIPY_CLIENT_SECRET",
        "-e", "SPOTIPY_REDIRECT_URI",
        "-e", "SPOTIPY_CACHE_PATH",
        "docker.io/allesy/spotify-mcp:latest"
      ],
      "env": {
        "SPOTIPY_CLIENT_ID": "your-client-id",
        "SPOTIPY_CLIENT_SECRET": "your-client-secret",
        "SPOTIPY_REDIRECT_URI": "http://127.0.0.1:8888/callback",
        "SPOTIPY_CACHE_PATH": "/app/.cache/token"
      }
    }
  }
}
```

Notes:

- The volume mount `${HOME}/.cache/spotify-mcp:/app/.cache` persists Spotipy's token cache between runs. If you set `SPOTIPY_CACHE_PATH`, ensure it points somewhere under `/app/.cache` (e.g., `/app/.cache/token`). Some MCP clients do not expand `${HOME}`; if you see issues, use an absolute path like `/Users/<you>/.cache/spotify-mcp:/app/.cache`.
- The redirect URI must exactly match the one configured in your Spotify app.

## First-time OAuth

Spotipy performs user authorization on first use.

### Zero-install Docker OAuth (recommended)

Run this once to create and persist a token cache (no local installs needed):

```bash
docker run --rm -it \
  -v ${HOME}/.cache/spotify-mcp:/app/.cache \
  -e SPOTIPY_CLIENT_ID=your-client-id \
  -e SPOTIPY_CLIENT_SECRET=your-client-secret \
  -e SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback \
  -e SPOTIPY_CACHE_PATH=/app/.cache/token \
  docker.io/allesy/spotify-mcp:latest python -u -m spotify_mcp.cli.auth_init
```

Follow the prompt: open the printed URL, log in, then paste the redirected URL back into the terminal. The token is saved to `/app/.cache/token` (on host: `${HOME}/.cache/spotify-mcp/token`).

After that, your MCP client can run the server container and reuse the cached token automatically.

### Alternative: Local run once

Recommended flow for a smooth auth experience:

1. Install dependencies and run the auth script locally:

   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   
   export SPOTIPY_CLIENT_ID=your-client-id
   export SPOTIPY_CLIENT_SECRET=your-client-secret
   export SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
   export SPOTIPY_CACHE_PATH=/Users/$(whoami)/.cache/spotify-mcp/token
   
   python -m spotify_mcp.cli.auth_init
   ```

2. Follow the prompt: open the URL in your browser, authorize, and paste the redirect URL back.
3. The token is now cached and can be used by the MCP server.

Alternatively, you can let your MCP client handle the OAuth automatically on first connection (it will open your browser).

## Local development (without Docker)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export SPOTIPY_CLIENT_ID=...
export SPOTIPY_CLIENT_SECRET=...
export SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
export PYTHONPATH=src
python -m spotify_mcp.server
```

Your MCP client can also run `python -m spotify_mcp.server` directly instead of Docker if preferred (set `PYTHONPATH=src` in the env).

## API reference (tool signatures)

### Core Playback & Library

- search(query: string, search_type: 'track'|'album'|'artist'|'playlist' = 'track', limit: int = 5, offset: int = 0) -> string
- play() -> string
- pause() -> string
- next_track() -> string
- previous_track() -> string
- currently_playing() -> string
- play_song(name: string) -> string
- play_by_id(spotify_id_or_uri: string) -> string
- list_playlists(limit: int = 20, offset: int = 0) -> string
- list_liked(limit: int = 20, offset: int = 0) -> string
- list_playlist_songs(playlist_id: string, limit: int = 20, offset: int = 0) -> string
- add_to_liked(song_ids: string[]) -> string
- add_to_playlist(playlist_id: string, song_ids: string[]) -> string
- liked_total() -> int
- add_to_queue(track_id: string) -> string
- get_queue() -> string
- get_recently_played(limit: int = 20) -> string
- get_top_tracks(limit: int = 20, time_range: string = "medium_term") -> string
- get_top_artists(limit: int = 20, time_range: string = "medium_term") -> string
- list_devices() -> string
- transfer_playback(device_id: string) -> string
- set_shuffle(state: bool) -> string
- set_repeat(state: string) -> string
- seek_position(position_ms: int) -> string
- set_volume(volume_percent: int) -> string

## Security

- Never commit secrets. Provide credentials via your MCP client config env entries.
- Prefer mounting a cache directory rather than baking tokens into an image.
- Keep dependencies updated.

## Troubleshooting

### Authentication Issues

**403 Forbidden Error**

- ✅ Check that your Spotify account email is added to **User Management** in your Spotify Developer app (required for Development Mode)
- ✅ Verify the redirect URI is **exactly** `http://127.0.0.1:8888/callback` in both:
  - Spotify Developer Dashboard app settings
  - Your MCP client config and auth command

**Token Expired or Invalid**

- Delete the cached token and re-authenticate:

  ```bash
  rm ~/.cache/spotify-mcp/token
  # Then run the auth_init command again
  ```

### Docker Issues

**Volume Mount Path Not Working**

- Some MCP clients don't expand `${HOME}` - use absolute paths like `/Users/YOUR_USERNAME/.cache/spotify-mcp`
- On Windows, use: `C:\Users\YOUR_USERNAME\.cache\spotify-mcp`

**Container Can't Find Token**

- Ensure `SPOTIPY_CACHE_PATH` in your MCP config matches the path used during authentication (`/app/.cache/token`)
- Check that the volume mount maps correctly: `-v /local/path:/app/.cache`

### Playback Issues

**"No active device" Error**

- Open Spotify on any device (phone, desktop, web player) before trying playback commands
- The device must be actively playing or at least opened and visible in Spotify

**Commands Not Working**

- Restart your MCP client after configuration changes
- Check that the Spotify app server is running: look for it in your MCP client's server list

## License

MIT
