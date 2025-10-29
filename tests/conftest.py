"""Pytest configuration and fixtures for Spotify MCP tests."""

import pytest


@pytest.fixture
def mock_spotify_client():
    """Mock Spotify client for testing."""
    # Add mocking logic here when needed
    pass


@pytest.fixture
def test_config():
    """Test configuration."""
    return {
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "redirect_uri": "http://localhost:8765/callback",
    }

