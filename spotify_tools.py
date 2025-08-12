"""
spotify_tools.py

This module provides utility functions to interact with the Spotify Web API using the Spotipy library. It supports authentication, playback control, searching, and retrieving playback information. Spotify credentials are read from environment variables, which in an MCP setup should be provided via the MCP server config.

Functions:
- get_spotify_client: Returns an authenticated Spotify client.
- get_current_playback: Gets the current playback state.
- search_spotify: Searches for tracks, albums, artists, or playlists.
- play: Starts playback on the user's active device.
- pause: Pauses playback on the user's active device.
- next_track: Skips to the next track.
- previous_track: Returns to the previous track.
- get_currently_playing: Gets information about the currently playing track.
- play_song: Searches for a song by name and plays the first result on the user's active Spotify device.
- play_song_by_id: Plays a song or playlist directly by its Spotify track or playlist ID/URI on the user's active Spotify device.
- list_user_playlists: Lists the user's Spotify playlists.
- list_liked_songs: Lists the user's liked (saved) songs.
- list_playlist_songs: Lists the songs in a playlist by its Spotify playlist ID.
- add_songs_to_liked: Adds one or more songs to the user's Liked Songs (library).
- add_songs_to_playlist: Adds one or more songs to a specified playlist.
- get_liked_songs_total: Returns the total count of tracks in the user's Liked Songs library.
"""

from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List, Union
from config import load_settings

# Load a local .env if present. In Docker/MCP usage, envs should come from the process environment.
load_dotenv()

settings = load_settings()

__all__ = [
    "get_spotify_client",
    "get_current_playback",
    "search_spotify",
    "play",
    "pause",
    "next_track",
    "previous_track",
    "get_currently_playing",
    "play_song",
    "play_song_by_id",
    "list_user_playlists",
    "list_liked_songs",
    "list_playlist_songs",
    "add_songs_to_liked",
    "add_songs_to_playlist",
    "get_liked_songs_total",
]


def get_spotify_client():
    """
    Create and return an authenticated Spotipy client using credentials from environment variables.

    Returns:
        spotipy.Spotify: An authenticated Spotipy client instance.
    """
    auth_manager_kwargs = {
        "client_id": settings.client_id,
        "client_secret": settings.client_secret,
        "redirect_uri": settings.redirect_uri,
        "scope": settings.scope,
    }
    if settings.cache_path:
        auth_manager_kwargs["cache_path"] = settings.cache_path

    return spotipy.Spotify(auth_manager=SpotifyOAuth(**auth_manager_kwargs))


def get_current_playback():
    """
    Retrieve the current playback state for the authenticated user.

    Returns:
        dict or None: The current playback information, or None if nothing is playing.
    """
    sp = get_spotify_client()
    return sp.current_playback()


async def search_spotify(query: str, search_type: str = "track", limit: int = 5, offset: int = 0):
    """Search Spotify for tracks, albums, artists, or playlists.

    Args:
        query (str): The search query string.
        search_type (str, optional): The type ('track'|'album'|'artist'|'playlist').
        limit (int, optional): Max number of results. Defaults to 5.
        offset (int, optional): Index of first item. Defaults to 0.

    Returns:
        str: A formatted string of results or a not-found message.
    """
    sp = get_spotify_client()
    results = sp.search(q=query, type=search_type, limit=limit, offset=offset)
    items = results.get(f"{search_type}s", {}).get("items", [])
    if not items:
        return f"No {search_type}s found for '{query}'."
    formatted = []
    for item in items:
        if search_type == "track":
            artists = ", ".join(artist["name"] for artist in item["artists"])
            formatted.append(
                f"{item['name']} by {artists} (Album: {item['album']['name']}) "
                f"[ID: {item['id']}]"
            )
        elif search_type == "album":
            artists = ", ".join(artist["name"] for artist in item["artists"])
            formatted.append(f"{item['name']} by {artists} [ID: {item['id']}]")
        elif search_type == "artist":
            formatted.append(f"{item['name']} [ID: {item['id']}]")
        elif search_type == "playlist":
            owner = item['owner']['display_name']
            formatted.append(f"{item['name']} by {owner} [ID: {item['id']}]")
    return "\n".join(formatted)


async def play():
    """Start playback on the user's active Spotify device.

    Returns:
        str: Success or error message.
    """
    sp = get_spotify_client()
    try:
        sp.start_playback()
        return "Playback started."
    except Exception as e:
        return f"Error starting playback: {e}"


async def pause():
    """Pause playback on the user's active Spotify device.

    Returns:
        str: Success or error message.
    """
    sp = get_spotify_client()
    try:
        sp.pause_playback()
        return "Playback paused."
    except Exception as e:
        return f"Error pausing playback: {e}"


async def next_track():
    """Skip to the next track in the user's active Spotify playback.

    Returns:
        str: Success or error message.
    """
    sp = get_spotify_client()
    try:
        sp.next_track()
        return "Skipped to next track."
    except Exception as e:
        return f"Error skipping to next track: {e}"


async def previous_track():
    """Return to the previous track in the user's active Spotify playback.

    Returns:
        str: Success or error message.
    """
    sp = get_spotify_client()
    try:
        sp.previous_track()
        return "Went to previous track."
    except Exception as e:
        return f"Error going to previous track: {e}"


async def get_currently_playing():
    """Get information about the currently playing track for the authenticated user.

    Returns:
        str: A formatted now-playing string, or a message if nothing is playing.
    """
    sp = get_spotify_client()
    playback = sp.current_playback()
    if playback and playback.get("item"):
        item = playback["item"]
        artists = ", ".join(artist["name"] for artist in item["artists"])
        return f"Currently playing: {item['name']} by {artists} (Album: {item['album']['name']})"
    else:
        return "No track is currently playing."


async def play_song(song_name: str):
    """Search for a song by name and play the first result on the active device.

    Args:
        song_name (str): The name of the song to search and play.

    Returns:
        str: What was played or an error message.
    """
    sp = get_spotify_client()
    results = sp.search(q=song_name, type="track", limit=1)
    tracks = results.get("tracks", {}).get("items", [])
    if not tracks:
        return f"No tracks found for '{song_name}'."
    track = tracks[0]
    track_uri = track["uri"]
    track_name = track["name"]
    artists = ", ".join(artist["name"] for artist in track["artists"])
    try:
        sp.start_playback(uris=[track_uri])
        return f"Now playing: {track_name} by {artists}."
    except Exception as e:
        return f"Error playing '{track_name}': {e}"


async def play_song_by_id(song_id: str):
    """Play a song or playlist by Spotify ID/URI on the active device.

    Args:
        song_id (str): Track or playlist ID/URI.

    Returns:
        str: What was played or an error message.
    """
    sp = get_spotify_client()

    # Detect playlist URIs/IDs
    if (
        song_id.startswith("spotify:playlist:")
        or (
            song_id.startswith("playlist:") or len(
                song_id) == 22 and song_id.isalnum()
        )
    ):
        # Treat as playlist
        if not song_id.startswith("spotify:playlist:"):
            playlist_uri = f"spotify:playlist:{song_id}"
        else:
            playlist_uri = song_id
        try:
            # Get playlist details for friendly name
            playlist = sp.playlist(playlist_uri)
            playlist_name = playlist.get("name", "Playlist")
            sp.start_playback(context_uri=playlist_uri)
            return f"Now playing playlist: {playlist_name}."
        except Exception as e:
            return f"Error playing playlist '{song_id}': {e}"

    # Fallback: treat as track
    if not song_id.startswith("spotify:track:"):
        track_uri = f"spotify:track:{song_id}"
    else:
        track_uri = song_id
    try:
        # Fetch track info for a friendly message
        track = sp.track(track_uri)
        track_name = track["name"]
        artists = ", ".join(artist["name"] for artist in track["artists"])
        sp.start_playback(uris=[track_uri])
        return f"Now playing: {track_name} by {artists}."
    except Exception as e:
        return f"Error playing track '{song_id}': {e}"


async def list_user_playlists(limit: int = 20, offset: int = 0):
    """
    List the user's Spotify playlists.

    Args:
        limit (int, optional): The maximum number of playlists to return. Defaults to 20.
        offset (int, optional): The index of the first playlist to return. Defaults to 0.

    Returns:
        str: A formatted string of playlist names and IDs.
    """
    sp = get_spotify_client()
    playlists = sp.current_user_playlists(limit=limit, offset=offset)
    items = playlists.get("items", [])
    if not items:
        return "No playlists found."
    formatted = []
    for playlist in items:
        name = playlist.get("name", "Unknown")
        playlist_id = playlist.get("id", "N/A")
        owner = playlist.get("owner", {}).get("display_name", "Unknown")
        formatted.append(f"{name} by {owner} [ID: {playlist_id}]")
    return "\n".join(formatted)


async def list_liked_songs(limit: int = 20, offset: int = 0):
    """
    List the user's liked (saved) songs.

    Args:
        limit (int, optional): The maximum number of liked songs to return. Defaults to 20.
        offset (int, optional): The index of the first song to return. Defaults to 0.

    Returns:
        str: A formatted string of liked songs.
    """
    sp = get_spotify_client()
    results = sp.current_user_saved_tracks(limit=limit, offset=offset)
    items = results.get("items", [])
    if not items:
        return "No liked songs found."
    formatted = []
    for item in items:
        track = item.get("track", {})
        name = track.get("name", "Unknown")
        artists = ", ".join(artist["name"]
                            for artist in track.get("artists", []))
        track_id = track.get("id", "N/A")
        formatted.append(f"{name} by {artists} [ID: {track_id}]")
    return "\n".join(formatted)


async def list_playlist_songs(playlist_id: str, limit: int = 20, offset: int = 0):
    """
    List the songs in a playlist by its Spotify playlist ID.

    Args:
        playlist_id (str): The Spotify playlist ID.
        limit (int, optional): The maximum number of songs to return. Defaults to 20.
        offset (int, optional): The index of the first song to return. Defaults to 0.

    Returns:
        str: A formatted string of songs in the playlist.
    """
    sp = get_spotify_client()
    try:
        results = sp.playlist_tracks(playlist_id, limit=limit, offset=offset)
        items = results.get("items", [])
        if not items:
            return "No songs found in this playlist."
        formatted = []
        for item in items:
            track = item.get("track", {})
            name = track.get("name", "Unknown")
            artists = ", ".join(artist["name"]
                                for artist in track.get("artists", []))
            track_id = track.get("id", "N/A")
            formatted.append(f"{name} by {artists} [ID: {track_id}]")
        return "\n".join(formatted)
    except Exception as e:
        return f"Error fetching playlist songs: {e}"


async def add_songs_to_liked(song_ids: Union[str, List[str]]):
    """
    Add one or more songs to the user's Liked Songs (library).

    Args:
        song_ids (Union[str, List[str]]): A single Spotify track ID/URI or a list of IDs/URIs.

    Returns:
        str: Success or error message.
    """
    sp = get_spotify_client()

    # Ensure we have a list of Spotify IDs (not full URIs) as required by the Web API
    if isinstance(song_ids, str):
        song_ids = [song_ids]

    cleaned_ids: List[str] = []
    for track in song_ids:
        # Allow full URIs like "spotify:track:ID" or just plain IDs
        if track.startswith("spotify:track:"):
            cleaned_ids.append(track.split(":")[-1])
        else:
            cleaned_ids.append(track)

    try:
        sp.current_user_saved_tracks_add(cleaned_ids)
        return f"Added {len(cleaned_ids)} track(s) to your Liked Songs."
    except Exception as e:
        return f"Error adding track(s) to Liked Songs: {e}"


async def add_songs_to_playlist(playlist_id: str, song_ids: Union[str, List[str]]):
    """
    Add one or more songs to a specified playlist.

    Args:
        playlist_id (str): Spotify playlist ID.
        song_ids (Union[str, List[str]]): A single Spotify track ID/URI or a list of IDs/URIs.

    Returns:
        str: Success or error message.
    """
    sp = get_spotify_client()

    if isinstance(song_ids, str):
        song_ids = [song_ids]

    # Spotify API expects URIs for playlist_add_items
    uris: List[str] = []
    for track in song_ids:
        if track.startswith("spotify:track:"):
            uris.append(track)
        else:
            uris.append(f"spotify:track:{track}")

    try:
        sp.playlist_add_items(playlist_id, uris)
        return f"Added {len(uris)} track(s) to playlist {playlist_id}."
    except Exception as e:
        return f"Error adding track(s) to playlist {playlist_id}: {e}"


async def get_liked_songs_total() -> int:
    """Return the total count of tracks in the user's Liked Songs library."""
    sp = get_spotify_client()
    try:
        # Spotify returns the total count in the paging object; limit=1 keeps the payload tiny.
        return sp.current_user_saved_tracks(limit=1)["total"]
    except Exception as e:
        raise Exception(f"Error fetching liked songs total: {e}")
