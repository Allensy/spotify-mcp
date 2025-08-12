import asyncio
import os
from typing import List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.server.stdio import stdio_server

import spotify_tools as st


mcp = FastMCP("spotify-mcp")


@mcp.tool()
async def search(query: str, search_type: str = "track", limit: int = 5, offset: int = 0) -> str:
    """Search Spotify for tracks, albums, artists, or playlists.

    - search_type: one of 'track', 'album', 'artist', 'playlist'
    - limit: max results to return
    - offset: index of first item to return
    """
    return await st.search_spotify(query=query, search_type=search_type, limit=limit, offset=offset)


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
async def list_playlist_songs(playlist_id: str, limit: int = 20, offset: int = 0) -> str:
    """List songs in a playlist by playlist ID."""
    return await st.list_playlist_songs(playlist_id=playlist_id, limit=limit, offset=offset)


@mcp.tool()
async def add_to_liked(song_ids: List[str]) -> str:
    """Add one or more track IDs/URIs to Liked Songs."""
    return await st.add_songs_to_liked(song_ids)


@mcp.tool()
async def add_to_playlist(playlist_id: str, song_ids: List[str]) -> str:
    """Add one or more track IDs/URIs to a playlist by playlist ID."""
    return await st.add_songs_to_playlist(playlist_id=playlist_id, song_ids=song_ids)


@mcp.tool()
async def liked_total() -> int:
    """Return total count of tracks in Liked Songs."""
    return await st.get_liked_songs_total()


async def main() -> None:
    # Basic sanity check that required env vars are present; Spotipy will raise clearer errors later too.
    required_envs = ["SPOTIPY_CLIENT_ID", "SPOTIPY_CLIENT_SECRET", "SPOTIPY_REDIRECT_URI"]
    missing = [name for name in required_envs if not os.getenv(name)]
    if missing:
        missing_str = ", ".join(missing)
        raise RuntimeError(
            f"Missing required environment variables: {missing_str}. "
            "Provide them in your MCP client config under env."
        )

    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(read_stream, write_stream)


if __name__ == "__main__":
    asyncio.run(main())


