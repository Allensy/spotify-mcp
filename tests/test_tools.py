"""
Test suite for Spotify MCP tools.

This module provides comprehensive tests for all Spotify MCP functionalities.
Tests are designed to work with real Spotify API calls using user credentials.
"""

import sys
from pathlib import Path
import asyncio
from typing import List, Dict, Any
from datetime import datetime

import pytest

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


# Check if credentials are available for Spotify API tests
def _has_spotify_credentials() -> bool:
    """Check if Spotify credentials are configured."""
    try:
        from spotify_mcp.config import load_settings

        settings = load_settings()
        return bool(settings.client_id and settings.client_secret)
    except Exception:
        return False


# Skip marker for tests requiring Spotify credentials
skip_without_credentials = pytest.mark.skipif(
    not _has_spotify_credentials(), reason="Spotify credentials not configured"
)


class SpotifyMCPTester:
    """Test harness for Spotify MCP functionality."""

    def __init__(self):
        """Initialize the tester."""
        self.results: List[Dict[str, Any]] = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.skipped_tests = 0

    def log_test(
        self, test_name: str, status: str, message: str = "", error: str = ""
    ) -> None:
        """Log test result."""
        self.total_tests += 1
        if status == "PASS":
            self.passed_tests += 1
            print(f"✅ {test_name}: PASSED")
        elif status == "FAIL":
            self.failed_tests += 1
            print(f"❌ {test_name}: FAILED - {error}")
        elif status == "SKIP":
            self.skipped_tests += 1
            print(f"⏭️  {test_name}: SKIPPED - {message}")

        self.results.append(
            {
                "test_name": test_name,
                "status": status,
                "message": message,
                "error": error,
                "timestamp": datetime.now().isoformat(),
            }
        )

    async def test_search(self) -> None:
        """Test search functionality."""
        try:
            from spotify_mcp.tools import search_spotify

            # Test track search
            result = await search_spotify("test", "track", limit=5)
            if result and "No tracks found" not in result:
                self.log_test("Search Tracks", "PASS")
            else:
                self.log_test("Search Tracks", "FAIL", error="No results")

            # Test artist search
            result = await search_spotify("Beatles", "artist", limit=5)
            if result and "No artists found" not in result:
                self.log_test("Search Artists", "PASS")
            else:
                self.log_test("Search Artists", "FAIL", error="No results")

            # Test album search
            result = await search_spotify("Abbey Road", "album", limit=5)
            if result and "No albums found" not in result:
                self.log_test("Search Albums", "PASS")
            else:
                self.log_test("Search Albums", "FAIL", error="No results")

            # Test playlist search
            result = await search_spotify("chill", "playlist", limit=5)
            if result and "No playlists found" not in result:
                self.log_test("Search Playlists", "PASS")
            else:
                self.log_test("Search Playlists", "FAIL", error="No results")

        except Exception as e:
            self.log_test("Search", "FAIL", error=str(e))

    async def test_playback_info(self) -> None:
        """Test playback information retrieval."""
        try:
            from spotify_mcp.tools import (
                get_currently_playing,
                get_current_playback,
            )

            # Test currently playing
            result = await get_currently_playing()
            if result:
                self.log_test("Get Currently Playing", "PASS")
            else:
                self.log_test(
                    "Get Currently Playing", "SKIP", "No active playback"
                )

            # Test current playback
            playback = get_current_playback()
            if playback is not None:
                self.log_test("Get Current Playback", "PASS")
            else:
                self.log_test(
                    "Get Current Playback", "SKIP", "No active playback"
                )

        except Exception as e:
            self.log_test("Playback Info", "FAIL", error=str(e))

    async def test_library_management(self) -> None:
        """Test library management functions."""
        try:
            from spotify_mcp.tools import (
                list_liked_songs,
                get_liked_songs_total,
                list_user_playlists,
            )

            # Test liked songs total
            total = await get_liked_songs_total()
            if isinstance(total, int) and total >= 0:
                self.log_test("Get Liked Songs Total", "PASS")
            else:
                self.log_test(
                    "Get Liked Songs Total", "FAIL", error="Invalid total"
                )

            # Test list liked songs
            result = await list_liked_songs(limit=5)
            if result:
                self.log_test("List Liked Songs", "PASS")
            else:
                self.log_test("List Liked Songs", "FAIL", error="No result")

            # Test list playlists
            result = await list_user_playlists(limit=5)
            if result:
                self.log_test("List User Playlists", "PASS")
            else:
                self.log_test("List User Playlists", "FAIL", error="No result")

        except Exception as e:
            self.log_test("Library Management", "FAIL", error=str(e))

    async def test_queue_management(self) -> None:
        """Test queue management functions."""
        try:
            from spotify_mcp.tools import get_queue

            # Test get queue
            result = await get_queue()
            if result:
                self.log_test("Get Queue", "PASS")
            else:
                self.log_test("Get Queue", "FAIL", error="No result")

        except Exception as e:
            self.log_test("Queue Management", "FAIL", error=str(e))

    async def test_device_management(self) -> None:
        """Test device management functions."""
        try:
            from spotify_mcp.tools import list_devices

            # Test list devices
            result = await list_devices()
            if result:
                self.log_test("List Devices", "PASS")
            else:
                self.log_test("List Devices", "FAIL", error="No result")

        except Exception as e:
            self.log_test("Device Management", "FAIL", error=str(e))

    async def test_user_analytics(self) -> None:
        """Test user analytics functions."""
        try:
            from spotify_mcp.tools import (
                get_recently_played,
                get_top_tracks,
                get_top_artists,
            )

            # Test recently played
            result = await get_recently_played(limit=5)
            if result and "No recently played" not in result:
                self.log_test("Get Recently Played", "PASS")
            else:
                self.log_test("Get Recently Played", "FAIL", error="No result")

            # Test top tracks
            result = await get_top_tracks(limit=5, time_range="short_term")
            if result and "No top tracks" not in result:
                self.log_test("Get Top Tracks", "PASS")
            else:
                self.log_test("Get Top Tracks", "FAIL", error="No result")

            # Test top artists
            result = await get_top_artists(limit=5, time_range="short_term")
            if result and "No top artists" not in result:
                self.log_test("Get Top Artists", "PASS")
            else:
                self.log_test("Get Top Artists", "FAIL", error="No result")

        except Exception as e:
            self.log_test("User Analytics", "FAIL", error=str(e))

    async def run_all_tests(self) -> None:
        """Run all test suites."""
        print("\n" + "=" * 60)
        print("🎵 Spotify MCP Functionality Tests")
        print("=" * 60 + "\n")

        # Check if credentials are configured
        from spotify_mcp.config import load_settings

        try:
            settings = load_settings()
            print("✅ Credentials configured")
            print(f"   Client ID: {settings.client_id[:10]}...")
            print(f"   Scopes: {settings.scope}\n")
        except Exception as e:
            print(f"❌ Credential check failed: {e}")
            print("Please configure your Spotify API credentials.\n")
            return

        print("Running test suites...\n")

        # Run test suites
        await self.test_search()
        await self.test_playback_info()
        await self.test_library_management()
        await self.test_queue_management()
        await self.test_device_management()
        await self.test_user_analytics()

        # Print summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        print(f"Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"⏭️  Skipped: {self.skipped_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")
        print("=" * 60 + "\n")

        if self.failed_tests > 0:
            print("\n⚠️  Some tests failed. Check the output above.")
        else:
            print("\n🎉 All tests passed successfully!")


async def main():
    """Main test entry point."""
    tester = SpotifyMCPTester()
    await tester.run_all_tests()


# Pytest-compatible async test functions
@skip_without_credentials
async def test_search():
    """Pytest: Test search functionality."""
    tester = SpotifyMCPTester()
    await tester.test_search()
    # Skip assertion if tests were skipped, only fail on actual failures
    if tester.total_tests > 0:
        assert tester.failed_tests == 0, "Search tests failed"


@skip_without_credentials
async def test_playback_info():
    """Pytest: Test playback information retrieval."""
    tester = SpotifyMCPTester()
    await tester.test_playback_info()
    if tester.total_tests > 0:
        assert tester.failed_tests == 0, "Playback info tests failed"


@skip_without_credentials
async def test_library_management():
    """Pytest: Test library management functions."""
    tester = SpotifyMCPTester()
    await tester.test_library_management()
    if tester.total_tests > 0:
        assert tester.failed_tests == 0, "Library management tests failed"


@skip_without_credentials
async def test_audio_features():
    """Pytest: Test audio features and analysis."""
    tester = SpotifyMCPTester()
    await tester.test_audio_features()
    if tester.total_tests > 0:
        assert tester.failed_tests == 0, "Audio features tests failed"


@skip_without_credentials
async def test_recommendations():
    """Pytest: Test recommendation functions."""
    tester = SpotifyMCPTester()
    await tester.test_recommendations()
    if tester.total_tests > 0:
        assert tester.failed_tests == 0, "Recommendations tests failed"


@skip_without_credentials
async def test_queue_management():
    """Pytest: Test queue management functions."""
    tester = SpotifyMCPTester()
    await tester.test_queue_management()
    if tester.total_tests > 0:
        assert tester.failed_tests == 0, "Queue management tests failed"


@skip_without_credentials
async def test_device_management():
    """Pytest: Test device management functions."""
    tester = SpotifyMCPTester()
    await tester.test_device_management()
    if tester.total_tests > 0:
        assert tester.failed_tests == 0, "Device management tests failed"


@skip_without_credentials
async def test_user_analytics():
    """Pytest: Test user analytics functions."""
    tester = SpotifyMCPTester()
    await tester.test_user_analytics()
    if tester.total_tests > 0:
        assert tester.failed_tests == 0, "User analytics tests failed"


if __name__ == "__main__":
    asyncio.run(main())
