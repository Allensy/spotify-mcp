from typing import List, Optional
from config import load_settings

from mcp.server.fastmcp import FastMCP

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


@mcp.tool()
async def get_audio_features(track_ids: List[str]) -> str:
    """Get detailed audio features for one or more tracks.

    Audio features include: danceability, energy, key, loudness, mode, 
    speechiness, acousticness, instrumentalness, liveness, valence, tempo, 
    duration_ms, time_signature.

    Args:
        track_ids: List of Spotify track IDs or URIs
    """
    return await st.get_audio_features(track_ids)


@mcp.tool()
async def analyze_track(track_id: str) -> str:
    """Get comprehensive audio analysis for a single track with insights.

    Provides detailed analysis including audio features, musical insights,
    and recommendations based on the track's characteristics.

    Args:
        track_id: Spotify track ID or URI
    """
    return await st.analyze_track(track_id)


@mcp.tool()
async def find_similar_tracks(
    track_id: str,
    source: str = "liked",
    similarity_threshold: float = 0.15
) -> str:
    """Find tracks similar to the given track based on audio features.

    Args:
        track_id: Reference track ID/URI to find similar tracks to
        source: Where to search - 'liked', 'playlists', or a specific playlist ID
        similarity_threshold: Maximum difference for similarity (0.0-1.0, lower = more similar)
    """
    return await st.find_similar_tracks(track_id, source, similarity_threshold)


@mcp.tool()
async def filter_tracks_by_features(
    source: str = "liked",
    min_danceability: Optional[float] = None,
    max_danceability: Optional[float] = None,
    min_energy: Optional[float] = None,
    max_energy: Optional[float] = None,
    min_valence: Optional[float] = None,
    max_valence: Optional[float] = None,
    min_tempo: Optional[float] = None,
    max_tempo: Optional[float] = None,
    min_acousticness: Optional[float] = None,
    max_acousticness: Optional[float] = None,
    limit: int = 20
) -> str:
    """Filter tracks based on specific audio feature criteria.

    Find tracks that match your mood or activity by filtering on audio characteristics
    like danceability, energy, positivity (valence), tempo, and acousticness.

    Args:
        source: Where to search - 'liked', 'playlists', or a specific playlist ID
        min_danceability, max_danceability: Danceability range (0.0-1.0)
        min_energy, max_energy: Energy level range (0.0-1.0)  
        min_valence, max_valence: Musical positivity range (0.0-1.0)
        min_tempo, max_tempo: Tempo range in beats per minute
        min_acousticness, max_acousticness: Acoustic vs electronic range (0.0-1.0)
        limit: Maximum number of results to return
    """
    return await st.filter_tracks_by_features(
        source=source,
        min_danceability=min_danceability,
        max_danceability=max_danceability,
        min_energy=min_energy,
        max_energy=max_energy,
        min_valence=min_valence,
        max_valence=max_valence,
        min_tempo=min_tempo,
        max_tempo=max_tempo,
        min_acousticness=min_acousticness,
        max_acousticness=max_acousticness,
        limit=limit
    )


@mcp.tool()
async def get_track_recommendations(
    seed_track_ids: Optional[List[str]] = None,
    seed_artists: Optional[List[str]] = None,
    seed_genres: Optional[List[str]] = None,
    target_danceability: Optional[float] = None,
    target_energy: Optional[float] = None,
    target_valence: Optional[float] = None,
    target_tempo: Optional[float] = None,
    limit: int = 10
) -> str:
    """Get track recommendations based on seed tracks, artists, genres, and target audio features.

    Discover new music by providing seeds (up to 5 total across all seed types) and
    optionally specifying target audio characteristics.

    Args:
        seed_track_ids: Up to 5 track IDs as recommendation seeds
        seed_artists: Up to 5 artist IDs as recommendation seeds  
        seed_genres: Up to 5 genre names as recommendation seeds
        target_danceability: Target danceability (0.0-1.0)
        target_energy: Target energy level (0.0-1.0)
        target_valence: Target musical positivity (0.0-1.0) 
        target_tempo: Target tempo in beats per minute
        limit: Number of recommendations to return (max 100)
    """
    return await st.get_track_recommendations(
        seed_track_ids=seed_track_ids,
        seed_artists=seed_artists,
        seed_genres=seed_genres,
        target_danceability=target_danceability,
        target_energy=target_energy,
        target_valence=target_valence,
        target_tempo=target_tempo,
        limit=limit
    )


def main() -> None:
    # Load settings early to validate required environment variables.
    # This keeps behavior consistent across Docker and local runs.
    load_settings()

    # Run the FastMCP server with stdio transport
    mcp.run("stdio")


if __name__ == "__main__":
    main()
