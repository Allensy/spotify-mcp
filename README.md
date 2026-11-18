# Spotify MCP Server

[![CI](https://github.com/Allensy/spotify-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/Allensy/spotify-mcp/actions/workflows/ci.yml)
[![Docker Build & Push](https://github.com/Allensy/spotify-mcp/actions/workflows/docker.yml/badge.svg)](https://github.com/Allensy/spotify-mcp/actions/workflows/docker.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Model Context Protocol (MCP) server that exposes Spotify controls and queries as MCP tools using Spotipy.

[Source code on GitHub](https://github.com/Allensy/spotify-mcp) · [Report an issue](https://github.com/Allensy/spotify-mcp/issues) · [Docker Hub image](https://hub.docker.com/r/allesy/spotify-mcp)

**Ready to use via Docker** - No local Python install required!

## Quick Start (3 steps)

You’ll need Docker and a Spotify developer app. Spotify requires the owner of a [Development Mode app](https://developer.spotify.com/documentation/web-api/concepts/quota-modes) to have an active Spotify Premium subscription.

### 1. Register a Spotify app

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create an app (or use an existing one)
3. Copy your **Client ID**
4. Add `http://127.0.0.1:8888/callback` to **Redirect URIs** in app settings
5. If your app is in "Development Mode", add your Spotify account email to the **User Management** section

### 2. Sign in to Spotify (Docker)

Use your Client ID in this command:

```bash
docker run --rm -it \
  -p 127.0.0.1:8888:8888 \
  -v "${HOME}/.cache/spotify-mcp:/app/.cache" \
  -e SPOTIPY_CLIENT_ID=your-client-id \
  -e SPOTIPY_CACHE_PATH=/app/.cache/token-pkce.json \
  docker.io/allesy/spotify-mcp:latest python -u -m spotify_mcp.cli.auth_init \
  --no-open --callback-bind 0.0.0.0
```

Open the URL printed in the terminal and approve access. The browser returns to `127.0.0.1`, and the command saves the token and exits. The callback port is only open during sign-in. For a remote Docker host, use [manual sign-in](#manual-sign-in).

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
        "-e", "SPOTIPY_CACHE_PATH",
        "docker.io/allesy/spotify-mcp:latest"
      ],
      "env": {
        "SPOTIPY_CLIENT_ID": "your-client-id",
        "SPOTIPY_CACHE_PATH": "/app/.cache/token-pkce.json"
      }
    }
  }
}
```

**Important**: Replace `/Users/YOUR_USERNAME` with your actual home directory path (some MCP clients don't expand `${HOME}`).

Restart your MCP client and try asking, **“Search Spotify for ‘Get Lucky’ by Daft Punk.”** A Spotify track result confirms that your client can reach the server and the server can reach Spotify. If the search fails, see [Troubleshooting](#troubleshooting).

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
- **Spotify Developer app** - Create one at the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard). Development Mode app owners need Spotify Premium.
  - Client ID
  - Redirect URI: `http://127.0.0.1:8888/callback` added to app settings
  - Your Spotify email added to User Management (if in Development Mode)

## Pull from registry (no local build)

If you are using the published image, pull it directly:

```bash
docker pull docker.io/allesy/spotify-mcp:latest
```

Then follow the First-time OAuth section below and the MCP client config example, both of which reference the registry image.

## Transport Modes

This server supports two MCP transports:

| Mode | Use case | How to activate |
|------|----------|-----------------|
| `stdio` | Cursor, Claude Desktop, any client that launches the MCP process | default (no env var needed) |
| `sse` | Docker Compose sidecar, remote MCP clients (e.g. Hermes) | `MCP_TRANSPORT=sse` |

The Docker image always defaults to `stdio` so existing MCP client configs keep working unchanged.

### SSE mode environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Set to `sse` to enable HTTP/SSE mode |
| `MCP_HOST` | `0.0.0.0` | Bind host |
| `MCP_PORT` | `8000` | Bind port |
| `MCP_SSE_PATH` | `/sse` | SSE endpoint path |

### Run as SSE server (Docker)

```bash
docker run --rm \
  -p 8000:8000 \
  -v ${HOME}/.cache/spotify-mcp:/app/.cache \
  -e MCP_TRANSPORT=sse \
  -e MCP_HOST=0.0.0.0 \
  -e MCP_PORT=8000 \
  -e MCP_SSE_PATH=/sse \
  -e SPOTIPY_CLIENT_ID=your-client-id \
  -e SPOTIPY_CACHE_PATH=/app/.cache/token-pkce.json \
  docker.io/allesy/spotify-mcp:latest
```

### Docker Compose (standalone)

Copy [`.env.example`](.env.example) to `.env`, set your Client ID, and complete the Docker sign-in above using the same cache mount and file. Then start the server:

```bash
docker compose -f docker-compose.spotify-mcp.yml --env-file .env up
```

### Docker Compose with Hermes

See [`examples/hermes/docker-compose.yml`](examples/hermes/docker-compose.yml) for a full Hermes + Spotify MCP Compose stack. That example uses `/app/.cache/token`. When switching it to PKCE, use a new cache path in both the Compose configuration and your sign-in command.

Add this to your Hermes config (`~/.hermes/config.yaml`):

```yaml
mcp_servers:
  spotify:
    url: "http://spotify-mcp:8000/sse"
```

Then run:

```bash
docker compose -f examples/hermes/docker-compose.yml up
```

---

## Environment variables

- `SPOTIPY_CLIENT_ID` is required.
- `SPOTIFY_AUTH_MODE` accepts `pkce` or `legacy`. Without it, a nonblank `SPOTIPY_CLIENT_SECRET` selects legacy and the absence of a secret selects PKCE.
- `SPOTIPY_REDIRECT_URI` defaults to `http://127.0.0.1:8888/callback` for PKCE. Legacy requires this value and `SPOTIPY_CLIENT_SECRET`.
- `SPOTIFY_SCOPE` overrides the default Spotify scopes. Changing scopes can require sign-in again.
- `SPOTIPY_CACHE_PATH` overrides the token file. Use the same path for sign-in and runtime. For Docker, both commands need the same host bind mount.

## Build

```bash
docker build -t spotify-mcp:latest .
```

## Other sign-in options

### Manual sign-in

Use this if Docker runs on another machine or the callback port is unavailable. Open the printed link in your browser and paste the full redirect URL from its address bar into the terminal. The browser may report that it cannot connect to `127.0.0.1`, and the URL can still be copied.

```bash
docker run --rm -it \
  -v "${HOME}/.cache/spotify-mcp:/app/.cache" \
  -e SPOTIPY_CLIENT_ID=your-client-id \
  -e SPOTIPY_CACHE_PATH=/app/.cache/token-pkce.json \
  docker.io/allesy/spotify-mcp:latest python -u -m spotify_mcp.cli.auth_init --manual
```

### Existing client-secret installs

A configuration with `SPOTIPY_CLIENT_SECRET` and no explicit `SPOTIFY_AUTH_MODE` continues to use the original manual flow and cache. To sign in again, run `spotify-mcp-auth` or the Docker auth module with the same Client ID, secret, redirect URI, and cache path you already use. To switch to PKCE, remove the secret or set `SPOTIFY_AUTH_MODE=pkce`, choose a separate cache path, and sign in again.

## Local development (without Docker)

```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -e .
export SPOTIPY_CLIENT_ID=your-client-id
spotify-mcp-auth
```

For local PKCE, `spotify-mcp-auth` opens your browser and writes the token to `~/.cache/spotify-mcp/token-pkce.json` by default. To start the server from your MCP client, use the absolute path to `spotify-mcp` inside your virtual environment as the command and set `SPOTIPY_CLIENT_ID` to the same value. Pass any redirect or cache overrides to both commands.

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

- Run the same sign-in command again. If you changed the Client ID or authentication mode, use a separate cache path or move the old cache aside first.

### Docker Issues

**Volume Mount Path Not Working**

- Some MCP clients don't expand `${HOME}` - use absolute paths like `/Users/YOUR_USERNAME/.cache/spotify-mcp`
- On Windows, use: `C:\Users\YOUR_USERNAME\.cache\spotify-mcp`

**Container Can't Find Token**

- Ensure `SPOTIPY_CACHE_PATH` in your MCP config matches the path used during authentication (`/app/.cache/token-pkce.json` in the quick start)
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
