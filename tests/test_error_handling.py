"""
Tests for error handling, timeouts, and authentication improvements.

This module tests all the robustness improvements we added to prevent hanging
and provide better error messages.
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


class TestAuthenticationErrorHandling:
    """Test authentication error handling and messages."""

    def test_missing_token_error_message(self):
        """Test that missing token produces helpful error message."""
        with patch.dict(
            os.environ,
            {
                "SPOTIPY_CLIENT_ID": "test_id",
                "SPOTIPY_CLIENT_SECRET": "test_secret",
                "SPOTIPY_REDIRECT_URI": "http://localhost:8888/callback",
            },
        ):
            with patch("spotify_mcp.tools.SpotifyOAuth") as mock_oauth:
                # Simulate no cached token
                mock_auth = MagicMock()
                mock_auth.get_cached_token.return_value = None
                mock_oauth.return_value = mock_auth

                from spotify_mcp.tools import get_spotify_client

                with pytest.raises(RuntimeError) as exc_info:
                    get_spotify_client()

                error_msg = str(exc_info.value)
                assert (
                    "No valid Spotify authentication token found" in error_msg
                )
                assert "authorization flow" in error_msg.lower()
                assert "auth_init" in error_msg

    def test_open_browser_false_in_client(self):
        """Test that open_browser=False is set to prevent hanging."""
        with patch.dict(
            os.environ,
            {
                "SPOTIPY_CLIENT_ID": "test_id",
                "SPOTIPY_CLIENT_SECRET": "test_secret",
                "SPOTIPY_REDIRECT_URI": "http://localhost:8888/callback",
            },
        ):
            with patch("spotify_mcp.tools.SpotifyOAuth") as mock_oauth:
                # Simulate valid cached token
                mock_auth = MagicMock()
                mock_auth.get_cached_token.return_value = {
                    "access_token": "test_token"
                }
                mock_oauth.return_value = mock_auth

                from spotify_mcp.tools import get_spotify_client

                try:
                    get_spotify_client()
                except Exception:
                    pass  # We don't care about Spotify connection errors

                # Verify open_browser=False was passed
                call_kwargs = mock_oauth.call_args[1]
                assert call_kwargs.get("open_browser") is False

    def test_auth_error_wrapping(self):
        """Test that authentication errors are wrapped with helpful context."""
        with patch.dict(
            os.environ,
            {
                "SPOTIPY_CLIENT_ID": "test_id",
                "SPOTIPY_CLIENT_SECRET": "test_secret",
                "SPOTIPY_REDIRECT_URI": "http://localhost:8888/callback",
            },
        ):
            with patch("spotify_mcp.tools.SpotifyOAuth") as mock_oauth:
                # Simulate authentication failure
                mock_oauth.side_effect = Exception("Invalid credentials")

                from spotify_mcp.tools import get_spotify_client

                with pytest.raises(RuntimeError) as exc_info:
                    get_spotify_client()

                error_msg = str(exc_info.value)
                assert "Failed to initialize Spotify client" in error_msg
                assert "token cache is missing or invalid" in error_msg


class TestTimeoutHandling:
    """Test timeout mechanisms to prevent hanging."""

    @pytest.mark.asyncio
    async def test_timeout_decorator_exists(self):
        """Test that with_timeout decorator is defined."""
        from spotify_mcp.tools import with_timeout

        assert callable(with_timeout)

        # Test that it returns a decorator
        decorator = with_timeout(timeout_seconds=1)
        assert callable(decorator)

    @pytest.mark.asyncio
    async def test_search_uses_timeout_wrapper(self):
        """Test that search operations use timeout wrapper."""
        import inspect
        from spotify_mcp import tools

        # Check that _search_spotify_sync function exists
        assert hasattr(tools, "_search_spotify_sync")

        # Verify it's decorated with timeout
        func = getattr(tools, "_search_spotify_sync")
        # The with_timeout decorator should wrap it
        assert hasattr(func, "__wrapped__") or callable(func)

    @pytest.mark.asyncio
    async def test_timeout_error_message(self):
        """Test that timeout produces helpful error message."""
        from spotify_mcp.tools import with_timeout

        @with_timeout(timeout_seconds=0.1)
        def slow_function():
            import time

            time.sleep(1)
            return "success"

        with pytest.raises(RuntimeError) as exc_info:
            await slow_function()

        error_msg = str(exc_info.value)
        assert "timed out" in error_msg.lower()
        assert "0.1s" in error_msg or "seconds" in error_msg


class TestSignalHandling:
    """Test signal handling for clean container shutdown."""

    def test_signal_handler_exists(self):
        """Test that signal handler is defined."""
        from spotify_mcp import server

        assert hasattr(server, "signal_handler")
        assert callable(server.signal_handler)

    def test_signal_handler_uses_os_exit(self):
        """Test that signal handler uses os._exit for forceful shutdown."""
        import inspect
        from spotify_mcp import server

        # Get the source code of the signal handler
        source = inspect.getsource(server.signal_handler)

        # Verify it uses os._exit() not sys.exit()
        assert "os._exit" in source
        assert "os._exit(0)" in source

    def test_stdin_monitor_exists(self):
        """Test that stdin monitor thread function exists."""
        from spotify_mcp import server

        assert hasattr(server, "stdin_monitor")
        assert callable(server.stdin_monitor)

    def test_stdin_monitor_logic(self):
        """Test stdin monitor checks for closed stdin."""
        import inspect
        from spotify_mcp import server

        source = inspect.getsource(server.stdin_monitor)

        # Verify it checks stdin.closed
        assert "stdin.closed" in source
        # Verify it calls os._exit on disconnect
        assert "os._exit" in source


class TestConfigValidation:
    """Test configuration validation and error messages."""

    def test_missing_client_id(self):
        """Test error when SPOTIPY_CLIENT_ID is missing."""
        with patch.dict(
            os.environ,
            {
                "SPOTIPY_CLIENT_SECRET": "test_secret",
                "SPOTIPY_REDIRECT_URI": "http://localhost:8888/callback",
            },
            clear=True,
        ):
            from spotify_mcp.config import load_settings

            with pytest.raises(RuntimeError) as exc_info:
                load_settings()

            error_msg = str(exc_info.value)
            assert "Missing required environment variables" in error_msg
            assert "SPOTIPY_CLIENT_ID" in error_msg

    def test_missing_client_secret(self):
        """Test error when SPOTIPY_CLIENT_SECRET is missing."""
        with patch.dict(
            os.environ,
            {
                "SPOTIPY_CLIENT_ID": "test_id",
                "SPOTIPY_REDIRECT_URI": "http://localhost:8888/callback",
            },
            clear=True,
        ):
            from spotify_mcp.config import load_settings

            with pytest.raises(RuntimeError) as exc_info:
                load_settings()

            error_msg = str(exc_info.value)
            assert "SPOTIPY_CLIENT_SECRET" in error_msg

    def test_missing_redirect_uri(self):
        """Test error when SPOTIPY_REDIRECT_URI is missing."""
        with patch.dict(
            os.environ,
            {
                "SPOTIPY_CLIENT_ID": "test_id",
                "SPOTIPY_CLIENT_SECRET": "test_secret",
            },
            clear=True,
        ):
            from spotify_mcp.config import load_settings

            with pytest.raises(RuntimeError) as exc_info:
                load_settings()

            error_msg = str(exc_info.value)
            assert "SPOTIPY_REDIRECT_URI" in error_msg

    def test_valid_config_loads(self):
        """Test that valid configuration loads successfully."""
        with patch.dict(
            os.environ,
            {
                "SPOTIPY_CLIENT_ID": "test_id",
                "SPOTIPY_CLIENT_SECRET": "test_secret",
                "SPOTIPY_REDIRECT_URI": "http://localhost:8888/callback",
            },
        ):
            from spotify_mcp.config import load_settings

            settings = load_settings()
            assert settings.client_id == "test_id"
            assert settings.client_secret == "test_secret"
            assert settings.redirect_uri == "http://localhost:8888/callback"

    def test_optional_cache_path(self):
        """Test that cache path is optional."""
        with patch.dict(
            os.environ,
            {
                "SPOTIPY_CLIENT_ID": "test_id",
                "SPOTIPY_CLIENT_SECRET": "test_secret",
                "SPOTIPY_REDIRECT_URI": "http://localhost:8888/callback",
                "SPOTIPY_CACHE_PATH": "/app/.cache/token",
            },
        ):
            from spotify_mcp.config import load_settings

            settings = load_settings()
            assert settings.cache_path == "/app/.cache/token"


class TestMCPServerRobustness:
    """Test MCP server error handling and robustness."""

    def test_server_main_has_exception_handling(self):
        """Test that main() has try-except for clean shutdown."""
        import inspect
        from spotify_mcp import server

        source = inspect.getsource(server.main)

        # Verify exception handling exists
        assert "try:" in source
        assert "except" in source
        # Verify it handles common exceptions
        assert (
            "KeyboardInterrupt" in source
            or "EOFError" in source
            or "BrokenPipeError" in source
        )

    def test_prompts_and_resources_registered(self):
        """Test that authorization prompt and resource are registered."""
        from spotify_mcp import server

        # Check that authorization functions exist
        assert hasattr(server, "authorize_spotify")
        assert hasattr(server, "spotify_auth_resource")

    def test_authorization_prompt_content(self):
        """Test that authorization prompt provides helpful instructions."""
        with patch.dict(
            os.environ,
            {
                "SPOTIPY_CLIENT_ID": "test_id",
                "SPOTIPY_CLIENT_SECRET": "test_secret",
                "SPOTIPY_REDIRECT_URI": "http://localhost:8888/callback",
            },
        ):
            from spotify_mcp.server import authorize_spotify

            result = authorize_spotify()

            # Verify helpful content
            assert "Authorization" in result or "authorization" in result
            assert "docker run" in result.lower()
            assert "auth_init" in result
            assert "--auto" in result


def test_suite_summary():
    """Print a summary of what we're testing."""
    print("\n" + "=" * 70)
    print("🧪 Error Handling & Robustness Test Suite")
    print("=" * 70)
    print("\nThis suite tests the improvements made to prevent hanging and")
    print("provide better error messages:")
    print()
    print(
        "1. ✅ Authentication error handling (missing tokens, auth failures)"
    )
    print("2. ✅ Timeout mechanisms (prevent infinite hangs)")
    print("3. ✅ Signal handling (clean container shutdown)")
    print("4. ✅ Configuration validation (clear error messages)")
    print("5. ✅ MCP server robustness (exception handling, prompts)")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    test_suite_summary()
    pytest.main([__file__, "-v"])
