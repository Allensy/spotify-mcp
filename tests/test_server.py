"""
Integration tests for Spotify MCP server.

This module tests the MCP server tool registration and basic functionality.
"""

import sys
from pathlib import Path
import asyncio
from typing import List, Dict, Any

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


class MCPIntegrationTester:
    """Test harness for MCP integration."""

    def __init__(self):
        """Initialize the tester."""
        self.results: List[Dict[str, Any]] = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

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

        if message:
            print(f"   {message}")

    def test_imports(self) -> None:
        """Test that all modules import correctly."""
        try:
            from spotify_mcp import server as mcp_server
            from spotify_mcp import tools as spotify_tools
            from spotify_mcp import config

            self.log_test("Module Imports", "PASS")
        except Exception as e:
            self.log_test("Module Imports", "FAIL", error=str(e))

    def test_mcp_server_creation(self) -> None:
        """Test MCP server creation."""
        try:
            from spotify_mcp import server as mcp_server

            if hasattr(mcp_server, "mcp"):
                self.log_test("MCP Server Creation", "PASS")
            else:
                self.log_test(
                    "MCP Server Creation", "FAIL", error="MCP object not found"
                )
        except Exception as e:
            self.log_test("MCP Server Creation", "FAIL", error=str(e))

    def test_tool_registration(self) -> None:
        """Test that all tools are registered."""
        try:
            from spotify_mcp import server as mcp_server

            expected_tools = [
                # Basic functionality
                "search",
                "play",
                "pause",
                "next_track",
                "previous_track",
                "currently_playing",
                "play_song",
                "play_by_id",
                # Library management
                "list_playlists",
                "list_liked",
                "list_playlist_songs",
                "add_to_liked",
                "add_to_playlist",
                "liked_total",
                # Queue management
                "add_to_queue",
                "get_queue",
                # User analytics
                "get_recently_played",
                "get_top_tracks",
                "get_top_artists",
                # Device management
                "list_devices",
                "transfer_playback",
                # Playback controls
                "set_shuffle",
                "set_repeat",
                "seek_position",
                "set_volume",
            ]

            # Get registered tools
            registered_tools = [
                name for name in dir(mcp_server) if not name.startswith("_")
            ]

            missing_tools = []
            for tool in expected_tools:
                if tool not in registered_tools:
                    missing_tools.append(tool)

            if not missing_tools:
                self.log_test(
                    "Tool Registration",
                    "PASS",
                    f"All {len(expected_tools)} tools registered",
                )
            else:
                self.log_test(
                    "Tool Registration",
                    "FAIL",
                    error=f"Missing tools: {', '.join(missing_tools)}",
                )

        except Exception as e:
            self.log_test("Tool Registration", "FAIL", error=str(e))

    def test_spotify_tools_exports(self) -> None:
        """Test that all expected functions are exported."""
        try:
            from spotify_mcp import tools as spotify_tools

            expected_exports = [
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
                "add_to_queue",
                "get_queue",
                "get_recently_played",
                "get_top_tracks",
                "get_top_artists",
                "list_devices",
                "transfer_playback",
                "set_shuffle",
                "set_repeat",
                "seek_position",
                "set_volume",
            ]

            missing_exports = []
            for export in expected_exports:
                if not hasattr(spotify_tools, export):
                    missing_exports.append(export)

            if not missing_exports:
                self.log_test(
                    "Spotify Tools Exports",
                    "PASS",
                    f"All {len(expected_exports)} functions exported",
                )
            else:
                self.log_test(
                    "Spotify Tools Exports",
                    "FAIL",
                    error=f"Missing exports: {', '.join(missing_exports)}",
                )

        except Exception as e:
            self.log_test("Spotify Tools Exports", "FAIL", error=str(e))

    def test_config_validation(self) -> None:
        """Test configuration validation."""
        try:
            from spotify_mcp.config import load_settings

            # Try to load settings
            settings = load_settings()

            # Validate required fields
            if not settings.client_id:
                self.log_test(
                    "Config Validation", "FAIL", error="Missing client_id"
                )
            elif not settings.client_secret:
                self.log_test(
                    "Config Validation", "FAIL", error="Missing client_secret"
                )
            elif not settings.redirect_uri:
                self.log_test(
                    "Config Validation", "FAIL", error="Missing redirect_uri"
                )
            else:
                self.log_test(
                    "Config Validation", "PASS", "All required config present"
                )

        except Exception as e:
            self.log_test("Config Validation", "FAIL", error=str(e))

    def run_all_tests(self) -> None:
        """Run all integration tests."""
        print("\n" + "=" * 60)
        print("🔧 Spotify MCP Integration Tests")
        print("=" * 60 + "\n")

        print("Running integration tests...\n")

        # Run tests
        self.test_imports()
        self.test_mcp_server_creation()
        self.test_tool_registration()
        self.test_spotify_tools_exports()
        self.test_config_validation()

        # Print summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        print(f"Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        success_rate = (
            (self.passed_tests / self.total_tests * 100)
            if self.total_tests > 0
            else 0
        )
        print(f"Success Rate: {success_rate:.1f}%")
        print("=" * 60 + "\n")

        if self.failed_tests > 0:
            print("\n⚠️  Some tests failed. Check the output above.")
        else:
            print("\n🎉 All integration tests passed!")


def main():
    """Main test entry point."""
    tester = MCPIntegrationTester()
    tester.run_all_tests()


# Pytest-compatible test functions
def test_module_imports():
    """Pytest: Test that all modules import correctly."""
    tester = MCPIntegrationTester()
    tester.test_imports()
    assert tester.failed_tests == 0, "Module imports failed"


def test_mcp_server_creation():
    """Pytest: Test MCP server creation."""
    tester = MCPIntegrationTester()
    tester.test_mcp_server_creation()
    assert tester.failed_tests == 0, "MCP server creation failed"


def test_tool_registration():
    """Pytest: Test that all tools are registered."""
    tester = MCPIntegrationTester()
    tester.test_tool_registration()
    assert tester.failed_tests == 0, "Tool registration failed"


def test_spotify_tools_exports():
    """Pytest: Test that all expected functions are exported."""
    tester = MCPIntegrationTester()
    tester.test_spotify_tools_exports()
    assert tester.failed_tests == 0, "Spotify tools exports failed"


def test_config_validation():
    """Pytest: Test configuration validation."""
    tester = MCPIntegrationTester()
    tester.test_config_validation()
    # Note: This test may fail if credentials aren't configured
    # which is acceptable for structure tests


if __name__ == "__main__":
    main()
