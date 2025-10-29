from typing import List, Optional

from mcp.server.fastmcp import FastMCP

from spotify_mcp.config import load_settings
from spotify_mcp import tools as st


mcp = FastMCP("spotify-mcp")


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

    # Run the FastMCP server with stdio transport
    mcp.run("stdio")


if __name__ == "__main__":
    main()
