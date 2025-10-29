"""
Structure validation for Spotify MCP.

This script validates the structure and completeness of the MCP implementation
without requiring Spotify credentials.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any
import inspect
import ast

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


class StructureValidator:
    """Validates the structure of the Spotify MCP implementation."""

    def __init__(self):
        """Initialize the validator."""
        self.results: List[Dict[str, Any]] = []
        self.total_checks = 0
        self.passed_checks = 0
        self.failed_checks = 0

    def log_check(
        self, check_name: str, status: str, message: str = "", error: str = ""
    ) -> None:
        """Log validation check result."""
        self.total_checks += 1
        if status == "PASS":
            self.passed_checks += 1
            print(f"✅ {check_name}")
            if message:
                print(f"   {message}")
        elif status == "FAIL":
            self.failed_checks += 1
            print(f"❌ {check_name}")
            if error:
                print(f"   Error: {error}")

    def validate_imports(self) -> None:
        """Validate that all modules can be imported."""
        try:
            from spotify_mcp import server  # noqa: F401
            from spotify_mcp import tools  # noqa: F401
            from spotify_mcp import config  # noqa: F401
            from spotify_mcp.cli import auth_init  # noqa: F401

            self.log_check(
                "Module Imports",
                "PASS",
                "All core modules import successfully",
            )
        except Exception as e:
            self.log_check("Module Imports", "FAIL", error=str(e))

    def validate_mcp_tools(self) -> None:
        """Validate MCP tool definitions."""
        try:
            from spotify_mcp import server as mcp_server

            # Expected tools
            expected_tools = {
                # Basic playback
                "search",
                "play",
                "pause",
                "next_track",
                "previous_track",
                "currently_playing",
                "play_song",
                "play_by_id",
                # Library
                "list_playlists",
                "list_liked",
                "list_playlist_songs",
                "add_to_liked",
                "add_to_playlist",
                "liked_total",
                # Queue
                "add_to_queue",
                "get_queue",
                # Analytics
                "get_recently_played",
                "get_top_tracks",
                "get_top_artists",
                # Devices
                "list_devices",
                "transfer_playback",
                # Playback controls
                "set_shuffle",
                "set_repeat",
                "seek_position",
                "set_volume",
            }

            # Get registered functions (exclude imports and special names)
            registered = set()
            exclude_names = {
                "main",
                "load_settings",
                "FastMCP",
                "List",
                "Optional",
                "st",  # spotify_tools alias
            }
            for name in dir(mcp_server):
                obj = getattr(mcp_server, name)
                if callable(obj) and not name.startswith("_"):
                    if name not in exclude_names:
                        registered.add(name)

            missing = expected_tools - registered
            extra = registered - expected_tools

            if not missing and not extra:
                self.log_check(
                    "MCP Tool Registration",
                    "PASS",
                    f"All {len(expected_tools)} expected tools registered",
                )
            elif missing:
                self.log_check(
                    "MCP Tool Registration",
                    "FAIL",
                    error=f"Missing tools: {', '.join(sorted(missing))}",
                )
            elif extra:
                self.log_check(
                    "MCP Tool Registration",
                    "FAIL",
                    error=f"Unexpected tools: {', '.join(sorted(extra))}",
                )

        except Exception as e:
            self.log_check("MCP Tool Registration", "FAIL", error=str(e))

    def validate_spotify_functions(self) -> None:
        """Validate Spotify tools function definitions."""
        try:
            from spotify_mcp import tools as spotify_tools

            expected_functions = {
                # Core
                "get_spotify_client",
                "get_current_playback",
                "search_spotify",
                # Playback
                "play",
                "pause",
                "next_track",
                "previous_track",
                "get_currently_playing",
                "play_song",
                "play_song_by_id",
                # Library
                "list_user_playlists",
                "list_liked_songs",
                "list_playlist_songs",
                "add_songs_to_liked",
                "add_songs_to_playlist",
                "get_liked_songs_total",
                # Queue
                "add_to_queue",
                "get_queue",
                # Analytics
                "get_recently_played",
                "get_top_tracks",
                "get_top_artists",
                # Devices
                "list_devices",
                "transfer_playback",
                # Playback controls
                "set_shuffle",
                "set_repeat",
                "seek_position",
                "set_volume",
            }

            # Check functions exist
            missing = []
            for func_name in expected_functions:
                if not hasattr(spotify_tools, func_name):
                    missing.append(func_name)

            if not missing:
                self.log_check(
                    "Spotify Tools Functions",
                    "PASS",
                    f"All {len(expected_functions)} functions defined",
                )
            else:
                self.log_check(
                    "Spotify Tools Functions",
                    "FAIL",
                    error=f"Missing functions: {', '.join(sorted(missing))}",
                )

            # Validate __all__ export
            if hasattr(spotify_tools, "__all__"):
                exported = set(spotify_tools.__all__)
                expected_exports = expected_functions - {"get_spotify_client"}
                missing_exports = expected_exports - exported

                if not missing_exports:
                    self.log_check(
                        "Spotify Tools __all__ Export",
                        "PASS",
                        f"{len(exported)} functions properly exported",
                    )
                else:
                    self.log_check(
                        "Spotify Tools __all__ Export",
                        "FAIL",
                        error=f"Not exported: {', '.join(missing_exports)}",
                    )
            else:
                self.log_check(
                    "Spotify Tools __all__ Export",
                    "FAIL",
                    error="__all__ not defined",
                )

        except Exception as e:
            self.log_check("Spotify Tools Functions", "FAIL", error=str(e))

    def validate_async_functions(self) -> None:
        """Validate that async functions are properly defined."""
        try:
            from spotify_mcp import tools as spotify_tools

            async_functions = [
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

            not_async = []
            for func_name in async_functions:
                if hasattr(spotify_tools, func_name):
                    func = getattr(spotify_tools, func_name)
                    if not inspect.iscoroutinefunction(func):
                        not_async.append(func_name)

            if not not_async:
                self.log_check(
                    "Async Function Definitions",
                    "PASS",
                    f"All {len(async_functions)} functions are async",
                )
            else:
                self.log_check(
                    "Async Function Definitions",
                    "FAIL",
                    error=f"Not async: {', '.join(not_async)}",
                )

        except Exception as e:
            self.log_check("Async Function Definitions", "FAIL", error=str(e))

    def validate_type_hints(self) -> None:
        """Validate that functions have type hints."""
        try:
            from spotify_mcp import tools as spotify_tools

            functions_to_check = [
                "search_spotify",
                "play",
                "pause",
                "add_to_queue",
                "get_queue",
                "list_devices",
                "get_top_tracks",
            ]

            missing_hints = []
            for func_name in functions_to_check:
                if hasattr(spotify_tools, func_name):
                    func = getattr(spotify_tools, func_name)
                    sig = inspect.signature(func)
                    # Check return annotation
                    if sig.return_annotation == inspect.Signature.empty:
                        missing_hints.append(f"{func_name} (return)")

            if not missing_hints:
                self.log_check(
                    "Type Hints",
                    "PASS",
                    "Sample functions have proper type hints",
                )
            else:
                self.log_check(
                    "Type Hints",
                    "FAIL",
                    error=f"Missing hints: {', '.join(missing_hints)}",
                )

        except Exception as e:
            self.log_check("Type Hints", "FAIL", error=str(e))

    def validate_docstrings(self) -> None:
        """Validate that functions have docstrings."""
        try:
            from spotify_mcp import tools as spotify_tools

            # Check spotify_tools functions
            functions_to_check = [
                "search_spotify",
                "play",
                "pause",
                "add_to_queue",
                "get_queue",
                "list_devices",
                "get_top_tracks",
            ]

            missing_docs = []
            for func_name in functions_to_check:
                if hasattr(spotify_tools, func_name):
                    func = getattr(spotify_tools, func_name)
                    if not func.__doc__ or len(func.__doc__.strip()) < 10:
                        missing_docs.append(func_name)

            if not missing_docs:
                self.log_check(
                    "Function Docstrings",
                    "PASS",
                    "All sample functions have docstrings",
                )
            else:
                self.log_check(
                    "Function Docstrings",
                    "FAIL",
                    error=f"Missing/short docs: {', '.join(missing_docs)}",
                )

        except Exception as e:
            self.log_check("Function Docstrings", "FAIL", error=str(e))

    def validate_error_handling(self) -> None:
        """Validate error handling in functions."""
        try:
            with open("src/spotify_mcp/tools.py", "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            # Count async functions with try/except
            async_funcs_with_try = 0
            total_async_funcs = 0

            for node in ast.walk(tree):
                if isinstance(node, ast.AsyncFunctionDef):
                    total_async_funcs += 1
                    # Check if function body has try/except
                    for child in ast.walk(node):
                        if isinstance(child, ast.Try):
                            async_funcs_with_try += 1
                            break

            if total_async_funcs > 0:
                coverage = (async_funcs_with_try / total_async_funcs) * 100
                if coverage >= 80:
                    self.log_check(
                        "Error Handling Coverage",
                        "PASS",
                        f"{coverage:.0f}% of async functions have "
                        f"error handling",
                    )
                else:
                    self.log_check(
                        "Error Handling Coverage",
                        "FAIL",
                        error=f"Only {coverage:.0f}% coverage "
                        f"(expected ≥80%)",
                    )

        except Exception as e:
            self.log_check("Error Handling Coverage", "FAIL", error=str(e))

    def validate_file_structure(self) -> None:
        """Validate project file structure."""
        import os

        required_files = [
            "src/spotify_mcp/server.py",
            "src/spotify_mcp/tools.py",
            "src/spotify_mcp/config.py",
            "src/spotify_mcp/cli/auth_init.py",
            "requirements.txt",
            "Dockerfile",
            "README.md",
            "TESTING.md",
        ]

        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)

        if not missing_files:
            self.log_check(
                "Project File Structure",
                "PASS",
                f"All {len(required_files)} required files present",
            )
        else:
            self.log_check(
                "Project File Structure",
                "FAIL",
                error=f"Missing: {', '.join(missing_files)}",
            )

    def validate_requirements(self) -> None:
        """Validate requirements.txt content."""
        try:
            with open("requirements.txt", "r", encoding="utf-8") as f:
                content = f.read()

            required_packages = [
                "spotipy",
                "python-dotenv",
                "mcp",
            ]

            missing_packages = []
            for package in required_packages:
                if package not in content:
                    missing_packages.append(package)

            if not missing_packages:
                self.log_check(
                    "Requirements File",
                    "PASS",
                    f"All {len(required_packages)} required packages listed",
                )
            else:
                self.log_check(
                    "Requirements File",
                    "FAIL",
                    error=f"Missing: {', '.join(missing_packages)}",
                )

            # Check spotipy version
            if "spotipy>=2.25" in content:
                self.log_check(
                    "Spotipy Version", "PASS", "Using spotipy>=2.25.0"
                )
            else:
                self.log_check(
                    "Spotipy Version",
                    "FAIL",
                    error="Should use spotipy>=2.25.0",
                )

        except Exception as e:
            self.log_check("Requirements File", "FAIL", error=str(e))

    def run_all_validations(self) -> None:
        """Run all validation checks."""
        print("\n" + "=" * 60)
        print("🔍 Spotify MCP Structure Validation")
        print("=" * 60 + "\n")

        # Run validations
        print("📋 Validating project structure...\n")
        self.validate_file_structure()
        self.validate_requirements()

        print("\n📦 Validating code structure...\n")
        self.validate_imports()
        self.validate_mcp_tools()
        self.validate_spotify_functions()

        print("\n🔧 Validating code quality...\n")
        self.validate_async_functions()
        self.validate_type_hints()
        self.validate_docstrings()
        self.validate_error_handling()

        # Print summary
        print("\n" + "=" * 60)
        print("📊 Validation Summary")
        print("=" * 60)
        print(f"Total Checks: {self.total_checks}")
        print(f"✅ Passed: {self.passed_checks}")
        print(f"❌ Failed: {self.failed_checks}")
        success_rate = (
            (self.passed_checks / self.total_checks * 100)
            if self.total_checks > 0
            else 0
        )
        print(f"Success Rate: {success_rate:.1f}%")
        print("=" * 60 + "\n")

        if self.failed_checks > 0:
            print("⚠️  Some validations failed. Review the output above.\n")
        else:
            print("🎉 All structure validations passed!\n")
            print("Next steps:")
            print("  1. Set up Spotify credentials")
            print("  2. Run: python test_mcp_integration.py")
            print("  3. Run: python test_spotify_tools.py")
            print("  4. See TESTING.md for detailed testing guide\n")


def main():
    """Main validation entry point."""
    validator = StructureValidator()
    validator.run_all_validations()


# Pytest-compatible test functions
def test_file_structure():
    """Pytest: Validate project file structure."""
    validator = StructureValidator()
    validator.validate_file_structure()
    assert validator.failed_checks == 0, "File structure validation failed"


def test_requirements():
    """Pytest: Validate requirements.txt content."""
    validator = StructureValidator()
    validator.validate_requirements()
    assert validator.failed_checks == 0, "Requirements validation failed"


def test_imports():
    """Pytest: Validate that all modules can be imported."""
    validator = StructureValidator()
    validator.validate_imports()
    assert validator.failed_checks == 0, "Module imports failed"


def test_mcp_tools():
    """Pytest: Validate MCP tool definitions."""
    validator = StructureValidator()
    validator.validate_mcp_tools()
    assert validator.failed_checks == 0, "MCP tool validation failed"


def test_spotify_functions():
    """Pytest: Validate Spotify tools function definitions."""
    validator = StructureValidator()
    validator.validate_spotify_functions()
    assert validator.failed_checks == 0, "Spotify functions validation failed"


def test_async_functions():
    """Pytest: Validate that async functions are properly defined."""
    validator = StructureValidator()
    validator.validate_async_functions()
    assert validator.failed_checks == 0, "Async functions validation failed"


def test_type_hints():
    """Pytest: Validate that functions have type hints."""
    validator = StructureValidator()
    validator.validate_type_hints()
    assert validator.failed_checks == 0, "Type hints validation failed"


def test_docstrings():
    """Pytest: Validate that functions have docstrings."""
    validator = StructureValidator()
    validator.validate_docstrings()
    assert validator.failed_checks == 0, "Docstrings validation failed"


def test_error_handling():
    """Pytest: Validate error handling in functions."""
    validator = StructureValidator()
    validator.validate_error_handling()
    assert validator.failed_checks == 0, "Error handling validation failed"


if __name__ == "__main__":
    main()
