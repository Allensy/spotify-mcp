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
- get_liked_songs_total: Returns the total count of tracks in Liked Songs.
- get_audio_features: Get detailed audio features for tracks.
- analyze_track: Get comprehensive audio analysis for a single track.
- find_similar_tracks: Find tracks with similar audio characteristics.
- filter_tracks_by_features: Filter tracks based on audio feature criteria.
- get_track_recommendations: Get recommendations based on audio features.
"""

from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List, Union, Optional
from config import load_settings

# Load a local .env if present. In Docker/MCP usage, envs should come from the process environment.
load_dotenv()

# Lazy-load settings to allow module import without credentials (for testing/CI)
_settings = None


def _get_settings():
    """Lazy-load settings to allow module imports without credentials."""
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


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
    "get_audio_features",
    "analyze_track",
    "find_similar_tracks",
    "filter_tracks_by_features",
    "get_track_recommendations",
]


def get_spotify_client():
    """
    Create and return an authenticated Spotipy client using credentials from environment variables.

    Returns:
        spotipy.Spotify: An authenticated Spotipy client instance.
    """
    settings = _get_settings()
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
        # Spotify returns the total count in the paging object;
        # limit=1 keeps the payload tiny.
        return sp.current_user_saved_tracks(limit=1)["total"]
    except Exception as e:
        raise Exception(f"Error fetching liked songs total: {e}")


async def get_audio_features(track_ids: Union[str, List[str]]) -> str:
    """
    Get detailed audio features for one or more tracks.

    Audio features include: danceability, energy, key, loudness, mode, 
    speechiness, acousticness, instrumentalness, liveness, valence, tempo, 
    duration_ms, time_signature.

    Args:
        track_ids (Union[str, List[str]]): Single track ID/URI or list of 
            track IDs/URIs.

    Returns:
        str: Formatted string with audio features for each track.
    """
    sp = get_spotify_client()

    if isinstance(track_ids, str):
        track_ids = [track_ids]

    # Clean track IDs (remove URI prefix if present)
    cleaned_ids: List[str] = []
    for track_id in track_ids:
        if track_id.startswith("spotify:track:"):
            cleaned_ids.append(track_id.split(":")[-1])
        else:
            cleaned_ids.append(track_id)

    try:
        # Get track info and audio features
        tracks = sp.tracks(cleaned_ids)
        features = sp.audio_features(cleaned_ids)

        if not features:
            return "No audio features found for the provided tracks."

        formatted = []
        for i, (track_info, track_features) in enumerate(
            zip(tracks["tracks"], features)
        ):
            if not track_features:
                continue

            track_name = track_info["name"]
            artists = ", ".join(artist["name"]
                                for artist in track_info["artists"])

            formatted.append(
                f"🎵 {track_name} by {artists}\n"
                f"  🕺 Danceability: {track_features['danceability']:.2f}\n"
                f"  ⚡ Energy: {track_features['energy']:.2f}\n"
                f"  😊 Valence (positivity): {track_features['valence']:.2f}\n"
                f"  🥁 Tempo: {track_features['tempo']:.0f} BPM\n"
                f"  🎸 Acousticness: {track_features['acousticness']:.2f}\n"
                f"  🎼 Instrumentalness: {track_features['instrumentalness']:.2f}\n"
                f"  🎤 Speechiness: {track_features['speechiness']:.2f}\n"
                f"  🎪 Liveness: {track_features['liveness']:.2f}\n"
                f"  🔊 Loudness: {track_features['loudness']:.1f} dB\n"
                f"  🎹 Key: {track_features['key']} | "
                f"Mode: {'Major' if track_features['mode'] == 1 else 'Minor'}"
            )

        return "\n\n".join(formatted)

    except Exception as e:
        return f"Error fetching audio features: {e}"


async def analyze_track(track_id: str) -> str:
    """
    Get comprehensive audio analysis for a single track including detailed 
    breakdowns and insights.

    Args:
        track_id (str): Spotify track ID/URI.

    Returns:
        str: Detailed analysis with insights and recommendations.
    """
    sp = get_spotify_client()

    # Clean track ID
    if track_id.startswith("spotify:track:"):
        clean_id = track_id.split(":")[-1]
    else:
        clean_id = track_id

    try:
        # Get track info and features
        track = sp.track(clean_id)
        features = sp.audio_features([clean_id])[0]

        if not features:
            return f"Could not analyze track {track_id}."

        track_name = track["name"]
        artists = ", ".join(artist["name"] for artist in track["artists"])
        album = track["album"]["name"]

        # Generate insights based on audio features
        insights = []

        # Dance/Energy insights
        if features["danceability"] > 0.7 and features["energy"] > 0.7:
            insights.append("Perfect for dancing and workouts! 💃🏋️")
        elif features["danceability"] > 0.7:
            insights.append("Great for dancing! 🕺")
        elif features["energy"] > 0.8:
            insights.append("High energy track! ⚡")

        # Mood insights
        if features["valence"] > 0.7:
            insights.append("Very positive and uplifting! 😊")
        elif features["valence"] < 0.3:
            insights.append("Melancholic or somber mood 😔")

        # Musical style insights
        if features["acousticness"] > 0.7:
            insights.append("Acoustic/unplugged style 🎸")
        if features["instrumentalness"] > 0.5:
            insights.append("Mostly instrumental 🎼")
        if features["liveness"] > 0.3:
            insights.append("Live recording feel 🎪")
        if features["speechiness"] > 0.5:
            insights.append("Speech-like (rap/spoken word) 🎤")

        # Tempo insights
        tempo = features["tempo"]
        if tempo < 60:
            tempo_desc = "Very slow ballad"
        elif tempo < 90:
            tempo_desc = "Slow/relaxed"
        elif tempo < 120:
            tempo_desc = "Moderate pace"
        elif tempo < 140:
            tempo_desc = "Upbeat"
        else:
            tempo_desc = "Very fast/energetic"

        result = (
            f"🎵 **{track_name}** by **{artists}**\n"
            f"📀 Album: {album}\n\n"
            f"**Audio Analysis:**\n"
            f"🕺 Danceability: {features['danceability']:.2f}/1.0\n"
            f"⚡ Energy: {features['energy']:.2f}/1.0\n"
            f"😊 Positivity: {features['valence']:.2f}/1.0\n"
            f"🥁 Tempo: {tempo:.0f} BPM ({tempo_desc})\n"
            f"🎸 Acousticness: {features['acousticness']:.2f}/1.0\n"
            f"🎼 Instrumentalness: {features['instrumentalness']:.2f}/1.0\n"
            f"🎤 Speechiness: {features['speechiness']:.2f}/1.0\n"
            f"🎪 Liveness: {features['liveness']:.2f}/1.0\n"
            f"🔊 Loudness: {features['loudness']:.1f} dB\n"
            f"🎹 Key: {features['key']} "
            f"({'Major' if features['mode'] == 1 else 'Minor'})\n\n"
        )

        if insights:
            result += "**Insights:** " + " | ".join(insights)

        return result

    except Exception as e:
        return f"Error analyzing track: {e}"


async def find_similar_tracks(
    track_id: str,
    source: str = "liked",
    similarity_threshold: float = 0.15
) -> str:
    """
    Find tracks similar to the given track based on audio features.

    Args:
        track_id (str): Reference track ID/URI.
        source (str): Where to search - 'liked', 'playlists', or a playlist ID.
        similarity_threshold (float): Maximum difference for similarity 
            (0.0 = identical, 1.0 = completely different).

    Returns:
        str: List of similar tracks with similarity scores.
    """
    sp = get_spotify_client()

    # Clean track ID
    if track_id.startswith("spotify:track:"):
        clean_id = track_id.split(":")[-1]
    else:
        clean_id = track_id

    try:
        # Get reference track features
        ref_features = sp.audio_features([clean_id])[0]
        if not ref_features:
            return f"Could not get features for reference track {track_id}."

        ref_track = sp.track(clean_id)
        ref_name = ref_track["name"]
        ref_artists = ", ".join(artist["name"]
                                for artist in ref_track["artists"])

        # Get tracks to compare against
        candidate_tracks = []

        if source == "liked":
            # Search in liked songs
            results = sp.current_user_saved_tracks(limit=50)
            for item in results["items"]:
                candidate_tracks.append(item["track"])
        elif source == "playlists":
            # Search in user's playlists (first 100 tracks total)
            playlists = sp.current_user_playlists(limit=10)
            track_count = 0
            for playlist in playlists["items"]:
                if track_count >= 100:
                    break
                tracks = sp.playlist_tracks(playlist["id"], limit=20)
                for item in tracks["items"]:
                    if item["track"] and track_count < 100:
                        candidate_tracks.append(item["track"])
                        track_count += 1
        else:
            # Treat as playlist ID
            tracks = sp.playlist_tracks(source, limit=50)
            for item in tracks["items"]:
                if item["track"]:
                    candidate_tracks.append(item["track"])

        if not candidate_tracks:
            return f"No tracks found in source '{source}'."

        # Get audio features for candidates
        candidate_ids = [track["id"] for track in candidate_tracks
                         if track["id"] != clean_id]  # Exclude reference track
        if not candidate_ids:
            return "No other tracks to compare against."

        candidate_features = sp.audio_features(candidate_ids)

        # Calculate similarities
        similar_tracks = []
        feature_keys = ["danceability", "energy", "valence", "tempo",
                        "acousticness", "instrumentalness", "speechiness",
                        "liveness"]

        for i, features in enumerate(candidate_features):
            if not features:
                continue

            # Calculate weighted similarity score
            score = 0
            weights = {"danceability": 1.5, "energy": 1.5, "valence": 1.2,
                       "tempo": 0.8, "acousticness": 1.0, "instrumentalness": 1.0,
                       "speechiness": 1.0, "liveness": 0.8}

            total_weight = 0
            for key in feature_keys:
                if key == "tempo":
                    # Normalize tempo difference (0-200 BPM range)
                    diff = abs(ref_features[key] - features[key]) / 200
                else:
                    diff = abs(ref_features[key] - features[key])

                score += diff * weights[key]
                total_weight += weights[key]

            score = score / total_weight  # Normalize by total weight

            if score <= similarity_threshold:
                track = candidate_tracks[i]
                artists = ", ".join(artist["name"]
                                    for artist in track["artists"])
                similar_tracks.append(
                    (score, track["name"], artists, track["id"]))

        # Sort by similarity (lower score = more similar)
        similar_tracks.sort(key=lambda x: x[0])

        if not similar_tracks:
            return (
                f"No similar tracks found to '{ref_name}' by {ref_artists} "
                f"within similarity threshold {similarity_threshold:.2f}."
            )

        result = f"🎯 Tracks similar to **{ref_name}** by **{ref_artists}**:\n\n"
        for score, name, artists, track_id in similar_tracks[:10]:
            similarity_pct = (1 - score) * 100
            result += f"🎵 {name} by {artists} ({similarity_pct:.0f}% similar) [ID: {track_id}]\n"

        return result

    except Exception as e:
        return f"Error finding similar tracks: {e}"


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
    """
    Filter tracks based on specific audio feature criteria.

    Args:
        source (str): Where to search - 'liked', 'playlists', or playlist ID.
        min_danceability, max_danceability (float): Danceability range (0-1).
        min_energy, max_energy (float): Energy range (0-1).
        min_valence, max_valence (float): Valence/positivity range (0-1).
        min_tempo, max_tempo (float): Tempo range in BPM.
        min_acousticness, max_acousticness (float): Acousticness range (0-1).
        limit (int): Maximum number of results to return.

    Returns:
        str: Filtered tracks matching the criteria.
    """
    sp = get_spotify_client()

    try:
        # Get tracks to filter
        candidate_tracks = []

        if source == "liked":
            results = sp.current_user_saved_tracks(limit=50)
            for item in results["items"]:
                candidate_tracks.append(item["track"])
        elif source == "playlists":
            playlists = sp.current_user_playlists(limit=10)
            track_count = 0
            for playlist in playlists["items"]:
                if track_count >= 100:
                    break
                tracks = sp.playlist_tracks(playlist["id"], limit=20)
                for item in tracks["items"]:
                    if item["track"] and track_count < 100:
                        candidate_tracks.append(item["track"])
                        track_count += 1
        else:
            # Treat as playlist ID
            tracks = sp.playlist_tracks(source, limit=100)
            for item in tracks["items"]:
                if item["track"]:
                    candidate_tracks.append(item["track"])

        if not candidate_tracks:
            return f"No tracks found in source '{source}'."

        # Get audio features
        track_ids = [track["id"] for track in candidate_tracks]
        features_list = sp.audio_features(track_ids)

        # Filter tracks
        filtered_tracks = []
        for i, features in enumerate(features_list):
            if not features:
                continue

            # Check all criteria
            if min_danceability is not None and features["danceability"] < min_danceability:
                continue
            if max_danceability is not None and features["danceability"] > max_danceability:
                continue
            if min_energy is not None and features["energy"] < min_energy:
                continue
            if max_energy is not None and features["energy"] > max_energy:
                continue
            if min_valence is not None and features["valence"] < min_valence:
                continue
            if max_valence is not None and features["valence"] > max_valence:
                continue
            if min_tempo is not None and features["tempo"] < min_tempo:
                continue
            if max_tempo is not None and features["tempo"] > max_tempo:
                continue
            if min_acousticness is not None and features["acousticness"] < min_acousticness:
                continue
            if max_acousticness is not None and features["acousticness"] > max_acousticness:
                continue

            track = candidate_tracks[i]
            artists = ", ".join(artist["name"] for artist in track["artists"])
            filtered_tracks.append((
                track["name"], artists, track["id"], features
            ))

        if not filtered_tracks:
            return "No tracks match the specified criteria."

        # Sort by danceability (or another metric) and limit results
        filtered_tracks.sort(key=lambda x: x[3]["danceability"], reverse=True)
        filtered_tracks = filtered_tracks[:limit]

        # Build criteria description
        criteria_parts = []
        if min_danceability is not None or max_danceability is not None:
            criteria_parts.append(
                f"danceability {min_danceability or 0:.1f}-{max_danceability or 1:.1f}")
        if min_energy is not None or max_energy is not None:
            criteria_parts.append(
                f"energy {min_energy or 0:.1f}-{max_energy or 1:.1f}")
        if min_valence is not None or max_valence is not None:
            criteria_parts.append(
                f"positivity {min_valence or 0:.1f}-{max_valence or 1:.1f}")
        if min_tempo is not None or max_tempo is not None:
            criteria_parts.append(
                f"tempo {min_tempo or 0:.0f}-{max_tempo or 300:.0f} BPM")
        if min_acousticness is not None or max_acousticness is not None:
            criteria_parts.append(
                f"acousticness {min_acousticness or 0:.1f}-{max_acousticness or 1:.1f}")

        criteria_desc = ", ".join(
            criteria_parts) if criteria_parts else "no specific criteria"

        result = f"🎯 Tracks matching criteria ({criteria_desc}):\n\n"
        for name, artists, track_id, features in filtered_tracks:
            result += (
                f"🎵 {name} by {artists}\n"
                f"   🕺 Dance: {features['danceability']:.2f} | "
                f"⚡ Energy: {features['energy']:.2f} | "
                f"😊 Mood: {features['valence']:.2f} | "
                f"🥁 {features['tempo']:.0f} BPM\n"
                f"   [ID: {track_id}]\n\n"
            )

        return result

    except Exception as e:
        return f"Error filtering tracks: {e}"


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
    """
    Get track recommendations based on seed tracks, artists, genres, 
    and target audio features.

    Args:
        seed_track_ids (List[str]): Up to 5 track IDs as seeds.
        seed_artists (List[str]): Up to 5 artist IDs as seeds.
        seed_genres (List[str]): Up to 5 genre names as seeds.
        target_danceability (float): Target danceability (0-1).
        target_energy (float): Target energy (0-1).
        target_valence (float): Target valence/positivity (0-1).
        target_tempo (float): Target tempo in BPM.
        limit (int): Number of recommendations (max 100).

    Returns:
        str: Recommended tracks with their audio features.
    """
    sp = get_spotify_client()

    try:
        # Build recommendation parameters
        kwargs = {"limit": min(limit, 100)}

        if seed_track_ids:
            # Clean track IDs
            clean_ids = []
            for track_id in seed_track_ids[:5]:  # Max 5 seeds
                if track_id.startswith("spotify:track:"):
                    clean_ids.append(track_id.split(":")[-1])
                else:
                    clean_ids.append(track_id)
            kwargs["seed_tracks"] = clean_ids

        if seed_artists:
            kwargs["seed_artists"] = seed_artists[:5]

        if seed_genres:
            kwargs["seed_genres"] = seed_genres[:5]

        # Add target audio features
        if target_danceability is not None:
            kwargs["target_danceability"] = target_danceability
        if target_energy is not None:
            kwargs["target_energy"] = target_energy
        if target_valence is not None:
            kwargs["target_valence"] = target_valence
        if target_tempo is not None:
            kwargs["target_tempo"] = target_tempo

        # Ensure we have at least one seed
        if not any(key.startswith("seed_") for key in kwargs.keys()):
            return "At least one seed (track, artist, or genre) is required."

        # Get recommendations
        recommendations = sp.recommendations(**kwargs)
        tracks = recommendations["tracks"]

        if not tracks:
            return "No recommendations found with the given parameters."

        # Get audio features for recommended tracks
        track_ids = [track["id"] for track in tracks]
        features_list = sp.audio_features(track_ids)

        # Build result
        seed_info = []
        if seed_track_ids:
            seed_info.append(f"{len(seed_track_ids)} track(s)")
        if seed_artists:
            seed_info.append(f"{len(seed_artists)} artist(s)")
        if seed_genres:
            seed_info.append(f"{len(seed_genres)} genre(s)")

        target_info = []
        if target_danceability is not None:
            target_info.append(f"danceability {target_danceability:.1f}")
        if target_energy is not None:
            target_info.append(f"energy {target_energy:.1f}")
        if target_valence is not None:
            target_info.append(f"positivity {target_valence:.1f}")
        if target_tempo is not None:
            target_info.append(f"tempo {target_tempo:.0f} BPM")

        result = f"🎯 Recommendations based on {', '.join(seed_info)}"
        if target_info:
            result += f" (targeting {', '.join(target_info)})"
        result += ":\n\n"

        for i, (track, features) in enumerate(zip(tracks, features_list)):
            artists = ", ".join(artist["name"] for artist in track["artists"])
            result += f"{i+1}. {track['name']} by {artists}\n"

            if features:
                result += (
                    f"   🕺 Dance: {features['danceability']:.2f} | "
                    f"⚡ Energy: {features['energy']:.2f} | "
                    f"😊 Mood: {features['valence']:.2f} | "
                    f"🥁 {features['tempo']:.0f} BPM\n"
                )

            result += f"   [ID: {track['id']}]\n\n"

        return result

    except Exception as e:
        return f"Error getting recommendations: {e}"
