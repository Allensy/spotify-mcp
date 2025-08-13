# Spotify MCP Server (Docker)

A Dockerized Model Context Protocol (MCP) server that exposes Spotify controls and queries as MCP tools using Spotipy.

The server reads Spotify credentials from environment variables provided by your MCP client config and communicates over stdio.

## Features (tools)

- search: search tracks, albums, artists, or playlists
- play / pause / next_track / previous_track
- currently_playing: friendly now-playing string
- play_song: search by name and play first result
- play_by_id: play a track or playlist by Spotify ID/URI
- list_playlists: list user playlists
- list_liked: list liked songs
- list_playlist_songs: list songs in a playlist by ID
- add_to_liked: add tracks to Liked Songs
- add_to_playlist: add tracks to a playlist
- liked_total: count of tracks in Liked Songs

## Prerequisites

- Spotify Developer app (Client ID/Secret) from the Spotify Dashboard
- Redirect URI configured in the Spotify app (e.g., `http://localhost:8765/callback`)
- Docker installed

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
        "SPOTIPY_REDIRECT_URI": "http://localhost:8765/callback",
        "SPOTIPY_CACHE_PATH": "/app/.cache/token" // optional
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
  -e SPOTIPY_REDIRECT_URI=http://localhost:8765/callback \
  -e SPOTIPY_CACHE_PATH=/app/.cache/token \
  docker.io/allesy/spotify-mcp:latest python -u auth_init.py
```

Follow the prompt: open the printed URL, log in, then paste the redirected URL back into the terminal. The token is saved to `/app/.cache/token` (on host: `${HOME}/.cache/spotify-mcp/token`).

After that, your MCP client can run the server container and reuse the cached token automatically.

### Alternative: Local run once

Recommended flow for a smooth auth experience:

1. Run the server locally once (outside Docker) so it can open a browser easily and write a `.cache` token:

   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
    SPOTIPY_CLIENT_ID=... SPOTIPY_CLIENT_SECRET=... SPOTIPY_REDIRECT_URI=http://localhost:8765/callback \
    SPOTIFY_SCOPE="user-read-playback-state user-modify-playback-state" \
    SPOTIPY_CACHE_PATH=".cache/token" \
   python mcp_server.py
   ```

2. Complete the Spotify login in the browser. After success, a `.cache` file is created in the working directory.
3. Use Docker with a bind mount to persist that cache (as shown above) so the container reuses the token.

Alternatively, you can perform the OAuth entirely inside Docker using the command above.

## Local development (without Docker)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export SPOTIPY_CLIENT_ID=...
export SPOTIPY_CLIENT_SECRET=...
export SPOTIPY_REDIRECT_URI=http://localhost:8765/callback
python mcp_server.py
```

Your MCP client can also run `python -u mcp_server.py` directly instead of Docker if preferred.

## API reference (tool signatures)

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
- liked_total() -> number

## Security

- Never commit secrets. Provide credentials via your MCP client config env entries.
- Prefer mounting a cache directory rather than baking tokens into an image.
- Keep dependencies updated.

## Troubleshooting

- Missing env: The server exits with a helpful error if `SPOTIPY_*` vars are absent.
- Redirect URI mismatch: Ensure the exact URI is configured in both Spotify Dashboard and env.
- No active device: Some playback operations require an active Spotify device; open Spotify on a device first.
- Auth loop in Docker: Run locally once to generate `.cache` and mount it into the container.

## License

MIT
