"""Pytest configuration and fixtures for Spotify MCP tests."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture
def mock_spotify_client():
    """Mock Spotify client for testing."""
    mock_client = MagicMock()
    mock_client.search.return_value = {
        "tracks": {
            "items": [
                {
                    "id": "test_track_id",
                    "name": "Test Track",
                    "artists": [{"name": "Test Artist"}],
                    "album": {"name": "Test Album"},
                }
            ]
        }
    }
    mock_client.current_playback.return_value = None
    return mock_client


@pytest.fixture
def test_config():
    """Test configuration."""
    return {
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "redirect_uri": "http://localhost:8765/callback",
    }


@pytest.fixture
def test_env(test_config):
    """Set up test environment variables."""
    original_env = os.environ.copy()
    os.environ.update({
        "SPOTIPY_CLIENT_ID": test_config["client_id"],
        "SPOTIPY_CLIENT_SECRET": test_config["client_secret"],
        "SPOTIPY_REDIRECT_URI": test_config["redirect_uri"],
    })
    yield test_config
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_spotify_oauth():
    """Mock SpotifyOAuth for testing."""
    mock_oauth = MagicMock()
    mock_oauth.get_authorize_url.return_value = "http://test.auth.url"
    mock_oauth.get_cached_token.return_value = {"access_token": "test_token"}
    mock_oauth.parse_response_code.return_value = "test_code"
    mock_oauth.get_access_token.return_value = {"access_token": "test_token"}
    return mock_oauth


@pytest.fixture
def clean_imports():
    """Clean imports between tests to avoid caching issues."""
    import importlib
    modules_to_reload = [
        'spotify_mcp.config',
        'spotify_mcp.tools',
        'spotify_mcp.server',
    ]
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
    yield
    # Cleanup after test
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
