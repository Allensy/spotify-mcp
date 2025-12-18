"""
Tests for authentication flow improvements.

This module tests the browser-based OAuth flow and auth_init functionality.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import pytest

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


class TestAuthInitModule:
    """Test auth_init.py module and functions."""

    def test_auth_init_imports(self):
        """Test that auth_init module imports correctly."""
        from spotify_mcp.cli import auth_init
        
        assert hasattr(auth_init, 'main')
        assert hasattr(auth_init, 'auto_auth')
        assert hasattr(auth_init, 'manual_auth')

    def test_callback_handler_exists(self):
        """Test that CallbackHandler class exists."""
        from spotify_mcp.cli.auth_init import CallbackHandler
        
        assert CallbackHandler is not None
        # Verify it's an HTTP request handler
        from http.server import BaseHTTPRequestHandler
        assert issubclass(CallbackHandler, BaseHTTPRequestHandler)

    def test_callback_handler_do_get(self):
        """Test that CallbackHandler has do_GET method."""
        from spotify_mcp.cli.auth_init import CallbackHandler
        
        assert hasattr(CallbackHandler, 'do_GET')
        assert callable(CallbackHandler.do_GET)


class TestAutoAuthFlow:
    """Test automatic browser-based OAuth flow."""

    @patch('spotify_mcp.cli.auth_init.webbrowser')
    @patch('spotify_mcp.cli.auth_init.HTTPServer')
    @patch('spotify_mcp.cli.auth_init.SpotifyOAuth')
    @patch.dict('os.environ', {
        'SPOTIPY_CLIENT_ID': 'test_id',
        'SPOTIPY_CLIENT_SECRET': 'test_secret',
        'SPOTIPY_REDIRECT_URI': 'http://127.0.0.1:8888/callback',
    })
    def test_auto_auth_starts_server(self, mock_oauth, mock_http_server, mock_webbrowser):
        """Test that auto_auth starts an HTTP server for callback."""
        from spotify_mcp.cli.auth_init import auto_auth
        from spotify_mcp.config import load_settings
        
        # Setup mocks
        mock_auth = MagicMock()
        mock_auth.get_authorize_url.return_value = 'http://test.url'
        mock_oauth.return_value = mock_auth
        
        mock_server = MagicMock()
        mock_http_server.return_value = mock_server
        
        mock_webbrowser.open.return_value = False  # Browser fails to open
        
        settings = load_settings()
        
        # Run auto_auth (will timeout waiting for callback)
        try:
            auto_auth(settings)
        except Exception:
            pass  # Expected to fail or timeout
        
        # Verify server was created on correct port
        mock_http_server.assert_called_once()
        call_args = mock_http_server.call_args[0]
        assert call_args[0] == ('127.0.0.1', 8888)

    @patch('spotify_mcp.cli.auth_init.webbrowser')
    @patch.dict('os.environ', {
        'SPOTIPY_CLIENT_ID': 'test_id',
        'SPOTIPY_CLIENT_SECRET': 'test_secret',
        'SPOTIPY_REDIRECT_URI': 'http://127.0.0.1:8888/callback',
    })
    def test_auto_auth_attempts_browser_open(self, mock_webbrowser):
        """Test that auto_auth attempts to open browser."""
        from spotify_mcp.cli.auth_init import auto_auth
        from spotify_mcp.config import load_settings
        
        with patch('spotify_mcp.cli.auth_init.HTTPServer'):
            with patch('spotify_mcp.cli.auth_init.SpotifyOAuth') as mock_oauth:
                mock_auth = MagicMock()
                mock_auth.get_authorize_url.return_value = 'http://test.url'
                mock_oauth.return_value = mock_auth
                
                mock_webbrowser.open.return_value = False
                
                settings = load_settings()
                
                try:
                    auto_auth(settings)
                except Exception:
                    pass
                
                # Verify browser.open was called with auth URL
                mock_webbrowser.open.assert_called_once_with('http://test.url')

    @patch('spotify_mcp.cli.auth_init.input')
    @patch('spotify_mcp.cli.auth_init.webbrowser')
    @patch.dict('os.environ', {
        'SPOTIPY_CLIENT_ID': 'test_id',
        'SPOTIPY_CLIENT_SECRET': 'test_secret',
        'SPOTIPY_REDIRECT_URI': 'http://127.0.0.1:8888/callback',
    })
    def test_auto_auth_falls_back_to_manual(self, mock_webbrowser, mock_input):
        """Test that auto_auth falls back to manual input when browser fails."""
        from spotify_mcp.cli.auth_init import auto_auth
        from spotify_mcp.config import load_settings
        
        with patch('spotify_mcp.cli.auth_init.HTTPServer'):
            with patch('spotify_mcp.cli.auth_init.SpotifyOAuth') as mock_oauth:
                mock_auth = MagicMock()
                mock_auth.get_authorize_url.return_value = 'http://test.url'
                mock_auth.parse_response_code.return_value = 'test_code'
                mock_auth.get_access_token.return_value = {'access_token': 'test_token'}
                mock_oauth.return_value = mock_auth
                
                # Browser fails to open
                mock_webbrowser.open.return_value = False
                # User provides redirect URL
                mock_input.return_value = 'http://127.0.0.1:8888/callback?code=test_code'
                
                settings = load_settings()
                result = auto_auth(settings)
                
                # Should succeed with manual input
                assert result is True
                mock_input.assert_called_once()


class TestManualAuthFlow:
    """Test manual copy-paste OAuth flow."""

    @patch('spotify_mcp.cli.auth_init.input')
    @patch('spotify_mcp.cli.auth_init.SpotifyOAuth')
    @patch.dict('os.environ', {
        'SPOTIPY_CLIENT_ID': 'test_id',
        'SPOTIPY_CLIENT_SECRET': 'test_secret',
        'SPOTIPY_REDIRECT_URI': 'http://127.0.0.1:8888/callback',
    })
    def test_manual_auth_prompts_for_url(self, mock_oauth, mock_input):
        """Test that manual_auth prompts user for redirect URL."""
        from spotify_mcp.cli.auth_init import manual_auth
        from spotify_mcp.config import load_settings
        
        mock_auth = MagicMock()
        mock_auth.get_authorize_url.return_value = 'http://test.url'
        mock_auth.parse_response_code.return_value = 'test_code'
        mock_auth.get_access_token.return_value = {'access_token': 'test_token'}
        mock_oauth.return_value = mock_auth
        
        mock_input.return_value = 'http://127.0.0.1:8888/callback?code=test_code'
        
        settings = load_settings()
        result = manual_auth(settings)
        
        assert result is True
        mock_input.assert_called_once()
        mock_auth.parse_response_code.assert_called_once_with('http://127.0.0.1:8888/callback?code=test_code')

    @patch('spotify_mcp.cli.auth_init.input')
    @patch('spotify_mcp.cli.auth_init.SpotifyOAuth')
    @patch.dict('os.environ', {
        'SPOTIPY_CLIENT_ID': 'test_id',
        'SPOTIPY_CLIENT_SECRET': 'test_secret',
        'SPOTIPY_REDIRECT_URI': 'http://127.0.0.1:8888/callback',
    })
    def test_manual_auth_handles_empty_input(self, mock_oauth, mock_input):
        """Test that manual_auth handles empty input gracefully."""
        from spotify_mcp.cli.auth_init import manual_auth
        from spotify_mcp.config import load_settings
        
        mock_auth = MagicMock()
        mock_auth.get_authorize_url.return_value = 'http://test.url'
        mock_oauth.return_value = mock_auth
        
        # User provides empty string
        mock_input.return_value = ''
        
        settings = load_settings()
        result = manual_auth(settings)
        
        assert result is False

    @patch('spotify_mcp.cli.auth_init.input')
    @patch('spotify_mcp.cli.auth_init.SpotifyOAuth')
    @patch.dict('os.environ', {
        'SPOTIPY_CLIENT_ID': 'test_id',
        'SPOTIPY_CLIENT_SECRET': 'test_secret',
        'SPOTIPY_REDIRECT_URI': 'http://127.0.0.1:8888/callback',
    })
    def test_manual_auth_handles_invalid_url(self, mock_oauth, mock_input):
        """Test that manual_auth handles invalid URL gracefully."""
        from spotify_mcp.cli.auth_init import manual_auth
        from spotify_mcp.config import load_settings
        
        mock_auth = MagicMock()
        mock_auth.get_authorize_url.return_value = 'http://test.url'
        mock_auth.parse_response_code.side_effect = Exception("Invalid URL")
        mock_oauth.return_value = mock_auth
        
        mock_input.return_value = 'invalid_url'
        
        settings = load_settings()
        result = manual_auth(settings)
        
        assert result is False


class TestAuthInitMain:
    """Test auth_init main function."""

    @patch('spotify_mcp.cli.auth_init.auto_auth')
    @patch.dict('os.environ', {
        'SPOTIPY_CLIENT_ID': 'test_id',
        'SPOTIPY_CLIENT_SECRET': 'test_secret',
        'SPOTIPY_REDIRECT_URI': 'http://127.0.0.1:8888/callback',
    })
    def test_main_uses_auto_when_flag_present(self, mock_auto_auth):
        """Test that main() uses auto_auth when --auto flag is present."""
        from spotify_mcp.cli import auth_init
        
        mock_auto_auth.return_value = True
        
        with patch('sys.argv', ['auth_init.py', '--auto']):
            with pytest.raises(SystemExit) as exc_info:
                auth_init.main()
            
            assert exc_info.value.code == 0
            mock_auto_auth.assert_called_once()

    @patch('spotify_mcp.cli.auth_init.manual_auth')
    @patch.dict('os.environ', {
        'SPOTIPY_CLIENT_ID': 'test_id',
        'SPOTIPY_CLIENT_SECRET': 'test_secret',
        'SPOTIPY_REDIRECT_URI': 'http://127.0.0.1:8888/callback',
    })
    def test_main_uses_manual_without_flag(self, mock_manual_auth):
        """Test that main() uses manual_auth when --auto flag is absent."""
        from spotify_mcp.cli import auth_init
        
        mock_manual_auth.return_value = True
        
        with patch('sys.argv', ['auth_init.py']):
            with pytest.raises(SystemExit) as exc_info:
                auth_init.main()
            
            assert exc_info.value.code == 0
            mock_manual_auth.assert_called_once()

    @patch.dict('os.environ', {}, clear=True)
    def test_main_exits_on_missing_credentials(self):
        """Test that main() exits with error when credentials are missing."""
        from spotify_mcp.cli import auth_init
        
        with pytest.raises(SystemExit) as exc_info:
            auth_init.main()
        
        # Should exit with non-zero code
        assert exc_info.value.code != 0


class TestCallbackHTMLResponses:
    """Test HTML responses from callback handler."""

    def test_success_html_contains_checkmark(self):
        """Test that success HTML contains success indicator."""
        import inspect
        from spotify_mcp.cli.auth_init import CallbackHandler
        
        source = inspect.getsource(CallbackHandler.do_GET)
        
        # Check for success HTML with checkmark (HTML entity)
        assert '&#x2713;' in source or 'Success' in source

    def test_failure_html_contains_error(self):
        """Test that failure HTML contains error indicator."""
        import inspect
        from spotify_mcp.cli.auth_init import CallbackHandler
        
        source = inspect.getsource(CallbackHandler.do_GET)
        
        # Check for failure HTML
        assert 'Failed' in source or 'Error' in source or '&#x2717;' in source


def test_suite_summary():
    """Print a summary of what we're testing."""
    print("\n" + "=" * 70)
    print("🔐 Authentication Flow Test Suite")
    print("=" * 70)
    print("\nThis suite tests the improved OAuth authentication flow:")
    print()
    print("1. ✅ Automatic browser-based auth (--auto flag)")
    print("2. ✅ Manual copy-paste auth (fallback)")
    print("3. ✅ HTTP callback server handling")
    print("4. ✅ Fallback to manual when browser fails")
    print("5. ✅ Error handling and user feedback")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    test_suite_summary()
    pytest.main([__file__, "-v"])

