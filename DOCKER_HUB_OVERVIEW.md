# 🎵 Spotify MCP Server

**A powerful Model Context Protocol (MCP) server that transforms Spotify into an intelligent music discovery engine**

[![Docker Hub](https://img.shields.io/docker/v/allesy/spotify-mcp?label=Docker%20Hub&logo=docker)](https://hub.docker.com/r/allesy/spotify-mcp)
[![Docker Pulls](https://img.shields.io/docker/pulls/allesy/spotify-mcp)](https://hub.docker.com/r/allesy/spotify-mcp)
[![License](https://img.shields.io/github/license/allensy/spotify-mcp)](https://github.com/allensy/spotify-mcp)

## 🚀 What Makes This Special

This isn't just another Spotify controller - it's a **smart music discovery engine** that understands the emotional and acoustic DNA of your music. Using Spotify's advanced audio analysis API, it can:

- 🎯 **Find songs by vibe**: "Give me high-energy workout tracks" or "Find chill acoustic songs"
- 🔍 **Discover similar music**: "Songs like this but more danceable"
- 📊 **Analyze musical DNA**: Deep insights into danceability, energy, mood, and acoustic characteristics
- 🎼 **Smart recommendations**: AI-powered suggestions based on audio features

## ✨ Core Features

### 🎮 Playback Control

- Play/pause, skip tracks, queue management
- Search across tracks, albums, artists, playlists
- Smart song search and instant playback

### 📚 Library Management  

- Browse and manage playlists
- Add/remove tracks from Liked Songs
- Playlist organization and track discovery

### 🧠 **Audio Intelligence** (The Game Changer)

- **`analyze_track`**: Get comprehensive audio analysis with smart insights
- **`find_similar_tracks`**: Discover music with similar audio characteristics
- **`filter_tracks_by_features`**: Filter your library by mood, energy, tempo, etc.
- **`get_track_recommendations`**: Personalized recommendations with precise targeting
- **`get_audio_features`**: Detailed audio characteristics for any track

## 🎯 Real-World Use Cases

### 🏋️ Fitness & Workouts

```bash
# Find high-energy workout music
filter_tracks_by_features(min_energy=0.8, min_tempo=120, min_danceability=0.7)
```

### 😌 Mood-Based Discovery

```bash
# Find chill acoustic songs for studying
filter_tracks_by_features(min_acousticness=0.7, max_energy=0.4, max_tempo=100)
```

### 🔍 Musical Exploration

```bash
# Find songs similar to your favorite track
find_similar_tracks("track_id", source="liked", similarity_threshold=0.15)
```

### 🎵 Smart Recommendations

```bash
# Get recommendations targeting specific vibes
get_track_recommendations(seed_track_ids=["track_id"], target_danceability=0.8)
```

## 🐳 Quick Start

### 1. One-Time Setup (OAuth)

```bash
docker run --rm -it \
  -v ${HOME}/.cache/spotify-mcp:/app/.cache \
  -e SPOTIPY_CLIENT_ID=your_client_id \
  -e SPOTIPY_CLIENT_SECRET=your_client_secret \
  -e SPOTIPY_REDIRECT_URI=http://localhost:8765/callback \
  -e SPOTIPY_CACHE_PATH=/app/.cache/token \
  allesy/spotify-mcp:latest python -u auth_init.py
```

### 2. Run MCP Server

```bash
docker run --rm -i \
  -v ${HOME}/.cache/spotify-mcp:/app/.cache \
  -e SPOTIPY_CLIENT_ID=your_client_id \
  -e SPOTIPY_CLIENT_SECRET=your_client_secret \
  -e SPOTIPY_REDIRECT_URI=http://localhost:8765/callback \
  -e SPOTIPY_CACHE_PATH=/app/.cache/token \
  allesy/spotify-mcp:latest
```

## 🔧 MCP Client Configuration

Add to your MCP client config (Claude Desktop, Cursor, etc.):

```json
{
  "mcpServers": {
    "spotify": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "/Users/you/.cache/spotify-mcp:/app/.cache",
        "-e", "SPOTIPY_CLIENT_ID",
        "-e", "SPOTIPY_CLIENT_SECRET", 
        "-e", "SPOTIPY_REDIRECT_URI",
        "-e", "SPOTIPY_CACHE_PATH",
        "allesy/spotify-mcp:latest"
      ]
    }
  }
}
```

## 📊 Audio Features Explained

Our audio analysis leverages Spotify's machine learning to understand:

| Feature | Range | Description |
|---------|-------|-------------|
| **Danceability** | 0.0-1.0 | How suitable for dancing (rhythm, beat strength) |
| **Energy** | 0.0-1.0 | Perceptual intensity and activity |
| **Valence** | 0.0-1.0 | Musical positivity (happy vs sad) |
| **Tempo** | BPM | Beats per minute |
| **Acousticness** | 0.0-1.0 | Acoustic vs electronic |
| **Instrumentalness** | 0.0-1.0 | Likelihood of no vocals |
| **Speechiness** | 0.0-1.0 | Presence of spoken words |
| **Liveness** | 0.0-1.0 | Live recording feel |

## 🎼 Example Interactions

**"Analyze this track for me"**

```
🎵 **Bohemian Rhapsody** by **Queen**
📀 Album: A Night at the Opera

**Audio Analysis:**
🕺 Danceability: 0.43/1.0
⚡ Energy: 0.87/1.0  
😊 Positivity: 0.52/1.0
🥁 Tempo: 149 BPM (Upbeat)
🎸 Acousticness: 0.01/1.0
🎼 Instrumentalness: 0.08/1.0

**Insights:** High energy track! | Mostly instrumental
```

**"Find me workout music from my library"**

```
🎯 Tracks matching criteria (energy 0.7-1.0, tempo 120-300 BPM):

🎵 Don't Stop Me Now by Queen
   🕺 Dance: 0.85 | ⚡ Energy: 0.95 | 😊 Mood: 0.93 | 🥁 156 BPM

🎵 Uptown Funk by Mark Ronson ft. Bruno Mars  
   🕺 Dance: 0.89 | ⚡ Energy: 0.88 | 😊 Mood: 0.91 | 🥁 115 BPM
```

## 🏗️ Architecture

- **Python 3.11** with async/await for performance
- **Spotipy** for robust Spotify Web API integration  
- **FastMCP** for efficient MCP protocol handling
- **Docker** for zero-dependency deployment
- **Persistent OAuth** via bind-mounted token cache

## 🔒 Security & Privacy

- ✅ No hardcoded credentials - all via environment variables
- ✅ Token persistence through secure bind mounts
- ✅ No data collection - pure API passthrough
- ✅ Compliant with Spotify Developer Terms

## 📚 Full API Reference

### Core Playback

- `search()` - Search tracks, albums, artists, playlists
- `play()` / `pause()` / `next_track()` / `previous_track()`
- `currently_playing()` - Now playing info
- `play_song(name)` - Search and play by name
- `play_by_id(spotify_id)` - Play by Spotify ID/URI

### Library Management

- `list_playlists()` / `list_liked()` / `list_playlist_songs()`
- `add_to_liked()` / `add_to_playlist()`
- `liked_total()` - Count liked songs

### Audio Intelligence

- `get_audio_features(track_ids)` - Detailed audio characteristics
- `analyze_track(track_id)` - Comprehensive analysis with insights
- `find_similar_tracks()` - Similarity-based discovery
- `filter_tracks_by_features()` - Filter by audio criteria
- `get_track_recommendations()` - Smart recommendations

## 🤝 Contributing

This project welcomes contributions! Check out the [GitHub repository](https://github.com/allensy/spotify-mcp) for:

- 🐛 Bug reports and feature requests
- 📖 Documentation improvements  
- 🔧 Code contributions
- 💡 New audio analysis ideas

## 📄 License

MIT License - see [LICENSE](https://github.com/allensy/spotify-mcp/blob/main/LICENSE) for details.

---

**Transform your music experience with intelligent audio analysis and discovery! 🎵✨**
