from typing import List
import sys
import signal
import os
import threading
import select

from mcp.server.fastmcp import FastMCP

from spotify_mcp import tools as st
from spotify_mcp.config import load_settings

mcp = FastMCP("spotify-mcp")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(
        f"\nReceived signal {signum}, shutting down gracefully...",
        file=sys.stderr,
    )
    # Use os._exit() instead of sys.exit() to bypass exception handlers
    # that might be preventing clean shutdown
    os._exit(0)


def stdin_monitor():
    """Monitor stdin and exit if it closes (Docker disconnect)."""
    import time

    # Wait a bit before starting monitoring to let FastMCP initialize
    time.sleep(2)

    try:
        while True:
            # Simple check: if stdin is closed, exit
            if sys.stdin.closed:
                print("\nStdin closed, shutting down...", file=sys.stderr)
                os._exit(0)

            # Sleep between checks to avoid being too aggressive
            time.sleep(2)
    except Exception as e:
        # Any error means we should exit
        print(
            f"\nStdin monitor error ({e}), shutting down...", file=sys.stderr
        )
        os._exit(0)


@mcp.resource("auth://spotify/setup")
def spotify_auth_resource() -> str:
    """Authorization setup instructions for Spotify MCP."""
    settings = load_settings()

    # Generate a direct auth URL (though we can't complete it in Docker stdio mode)
    from spotipy.oauth2 import SpotifyOAuth

    auth_manager = SpotifyOAuth(
        client_id=settings.client_id,
        client_secret=settings.client_secret,
        redirect_uri=settings.redirect_uri,
        scope=settings.scope,
        open_browser=False,
    )
    auth_url = auth_manager.get_authorize_url()

    return f"""# Spotify Authorization Required

🔗 **Authorization URL**: {auth_url}

⚠️ **Note**: Due to Docker stdio limitations, you need to complete authorization in your terminal.

## Run This Command:

```bash
docker run --rm -it \\
  -v ${{HOME}}/.cache/spotify-mcp:/app/.cache \\
  -e SPOTIPY_CLIENT_ID={settings.client_id} \\
  -e SPOTIPY_CLIENT_SECRET={settings.client_secret} \\
  -e SPOTIPY_REDIRECT_URI={settings.redirect_uri} \\
  -e SPOTIPY_CACHE_PATH={settings.cache_path or '/app/.cache/token'} \\
  spotify-mcp-local:latest python -u -m spotify_mcp.cli.auth_init --auto
```

After completing authorization, restart Cursor to use Spotify tools.
"""


@mcp.prompt()
def authorize_spotify() -> str:
    """Get instructions to authorize Spotify MCP server with your account.

    Use this if you're getting 'No valid Spotify authentication token found' errors.
    """
    settings = load_settings()

    return f"""# Spotify MCP Authorization Required

You need to complete the OAuth flow to authorize this MCP server with your Spotify account.

## Quick Authorization (Automatic Browser Flow)

Run this command in your terminal:

```bash
docker run --rm -it \\
  -v ${{HOME}}/.cache/spotify-mcp:/app/.cache \\
  -e SPOTIPY_CLIENT_ID={settings.client_id} \\
  -e SPOTIPY_CLIENT_SECRET={settings.client_secret} \\
  -e SPOTIPY_REDIRECT_URI={settings.redirect_uri} \\
  -e SPOTIPY_CACHE_PATH={settings.cache_path or '/app/.cache/token'} \\
  spotify-mcp-local:latest python -u -m spotify_mcp.cli.auth_init --auto
```

This will:
1. Open your browser automatically to Spotify's authorization page
2. After you click "Agree", redirect you back automatically
3. Save your token for future use

## After Authorization

1. The token will be cached at: `{settings.cache_path or '~/.cache/spotify-mcp/token'}`
2. Restart your MCP client (Cursor)
3. Try using Spotify tools again

## Troubleshooting

- **Make sure the volume mount path matches** between this command and your MCP config
- **Use the correct image name**: Use `spotify-mcp-local:latest` if built locally, or `docker.io/allesy/spotify-mcp:latest` for the published image
- **Check your Spotify Developer App**: Your email must be added to User Management if the app is in Development Mode

## Need Your Spotify Developer Credentials?

1. Go to: https://developer.spotify.com/dashboard
2. Create or select your app
3. Note your Client ID and Client Secret
4. Add `http://127.0.0.1:8888/callback` to Redirect URIs
5. Add your email to User Management (if in Development Mode)
"""


@mcp.tool()
async def search(
    query: str, search_type: str = "track", limit: int = 5, offset: int = 0
) -> str:
    """Search Spotify for tracks, albums, artists, or playlists.

    - search_type: one of 'track', 'album', 'artist', 'playlist'
    - limit: max results to return
    - offset: index of first item to return
    """
    return await st.search_spotify(
        query=query, search_type=search_type, limit=limit, offset=offset
    )


@mcp.tool()
async def play() -> str:
    """Start playback on the user's active device."""
    return await st.play()


@mcp.tool()
async def pause() -> str:
    """Pause playback on the user's active device."""
    return await st.pause()


@mcp.tool()
async def next_track() -> str:
    """Skip to the next track."""
    return await st.next_track()


@mcp.tool()
async def previous_track() -> str:
    """Return to the previous track."""
    return await st.previous_track()


@mcp.tool()
async def currently_playing() -> str:
    """Get a friendly description of the currently playing track."""
    return await st.get_currently_playing()


@mcp.tool()
async def play_song(name: str) -> str:
    """Search for a song by name and play the first result."""
    return await st.play_song(name)


@mcp.tool()
async def play_by_id(spotify_id_or_uri: str) -> str:
    """Play a track or playlist by Spotify ID or URI.

    Examples:
    - Track ID: 3n3Ppam7vgaVa1iaRUc9Lp
    - Track URI: spotify:track:3n3Ppam7vgaVa1iaRUc9Lp
    - Playlist ID: 37i9dQZF1DXcBWIGoYBM5M
    - Playlist URI: spotify:playlist:37i9dQZF1DXcBWIGoYBM5M
    """
    return await st.play_song_by_id(spotify_id_or_uri)


@mcp.tool()
async def list_playlists(limit: int = 20, offset: int = 0) -> str:
    """List user's playlists."""
    return await st.list_user_playlists(limit=limit, offset=offset)


@mcp.tool()
async def list_liked(limit: int = 20, offset: int = 0) -> str:
    """List user's liked songs."""
    return await st.list_liked_songs(limit=limit, offset=offset)


@mcp.tool()
async def list_playlist_songs(
    playlist_id: str, limit: int = 20, offset: int = 0
) -> str:
    """List songs in a playlist by playlist ID."""
    return await st.list_playlist_songs(
        playlist_id=playlist_id, limit=limit, offset=offset
    )


@mcp.tool()
async def add_to_liked(song_ids: List[str]) -> str:
    """Add one or more track IDs/URIs to Liked Songs."""
    return await st.add_songs_to_liked(song_ids)


@mcp.tool()
async def add_to_playlist(playlist_id: str, song_ids: List[str]) -> str:
    """Add one or more track IDs/URIs to a playlist by playlist ID."""
    return await st.add_songs_to_playlist(
        playlist_id=playlist_id, song_ids=song_ids
    )


@mcp.tool()
async def liked_total() -> int:
    """Return total count of tracks in Liked Songs."""
    return await st.get_liked_songs_total()


@mcp.tool()
async def add_to_queue(track_id: str) -> str:
    """Add a track to the user's playback queue.

    Args:
        track_id: Spotify track ID or URI to add to queue
    """
    return await st.add_to_queue(track_id)


@mcp.tool()
async def get_queue() -> str:
    """Get the user's current playback queue."""
    return await st.get_queue()


@mcp.tool()
async def get_recently_played(limit: int = 20) -> str:
    """Get the user's recently played tracks.

    Args:
        limit: Maximum number of tracks to return (default 20)
    """
    return await st.get_recently_played(limit)


@mcp.tool()
async def get_top_tracks(
    limit: int = 20, time_range: str = "medium_term"
) -> str:
    """Get the user's top tracks.

    Args:
        limit: Maximum number of tracks to return (default 20)
        time_range: Time range - 'short_term', 'medium_term', or 'long_term' (default 'medium_term')
    """
    return await st.get_top_tracks(limit, time_range)


@mcp.tool()
async def get_top_artists(
    limit: int = 20, time_range: str = "medium_term"
) -> str:
    """Get the user's top artists.

    Args:
        limit: Maximum number of artists to return (default 20)
        time_range: Time range - 'short_term', 'medium_term', or 'long_term' (default 'medium_term')
    """
    return await st.get_top_artists(limit, time_range)


@mcp.tool()
async def list_devices() -> str:
    """List all available Spotify devices."""
    return await st.list_devices()


@mcp.tool()
async def transfer_playback(device_id: str) -> str:
    """Transfer playback to a different device.

    Args:
        device_id: The ID of the device to transfer playback to
    """
    return await st.transfer_playback(device_id)


@mcp.tool()
async def set_shuffle(state: bool) -> str:
    """Set shuffle mode for playback.

    Args:
        state: True to enable shuffle, False to disable
    """
    return await st.set_shuffle(state)


@mcp.tool()
async def set_repeat(state: str) -> str:
    """Set repeat mode for playback.

    Args:
        state: Repeat mode - 'track', 'context', or 'off'
    """
    return await st.set_repeat(state)


@mcp.tool()
async def seek_position(position_ms: int) -> str:
    """Seek to a position in the current track.

    Args:
        position_ms: Position in milliseconds to seek to
    """
    return await st.seek_position(position_ms)


@mcp.tool()
async def set_volume(volume_percent: int) -> str:
    """Set the volume for the current playback device.

    Args:
        volume_percent: Volume level from 0 to 100
    """
    return await st.set_volume(volume_percent)


def main() -> None:
    # Load settings early to validate required environment variables.
    # This keeps behavior consistent across Docker and local runs.
    load_settings()

    # Register signal handlers for clean shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Start stdin monitor thread to detect disconnects
    monitor_thread = threading.Thread(target=stdin_monitor, daemon=True)
    monitor_thread.start()

    try:
        # Run the FastMCP server with stdio transport
        mcp.run("stdio")
    except (KeyboardInterrupt, EOFError, BrokenPipeError):
        # Clean exit when stdio closes or interrupted
        print("\nShutting down MCP server...", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
