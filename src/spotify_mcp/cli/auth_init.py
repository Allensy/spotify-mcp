#!/usr/bin/env python3
"""
Auth initialization script for Spotify MCP.

This script performs the initial OAuth flow to create and cache a Spotify token.
Run this once to authenticate, then the MCP server can reuse the cached token.

Usage:
    python -m spotify_mcp.cli.auth_init [--auto]

Options:
    --auto: Automatically open browser and start local callback server (recommended)
"""

from __future__ import annotations

import sys
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import threading

from spotipy.oauth2 import SpotifyOAuth

from spotify_mcp.config import load_settings


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    auth_code = None
    server_instance = None  # Will be set to allow shutdown

    def do_GET(self):
        """Handle the OAuth callback and other requests."""
        # Parse the query parameters
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        # Ignore favicon and other non-callback requests
        if self.path.startswith("/favicon"):
            self.send_response(404)
            self.end_headers()
            return

        if "code" in params:
            CallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html_content = """
                <html>
                <head><title>Spotify MCP - Authorization Successful</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: #1DB954;">&#x2713; Authorization Successful!</h1>
                    <p>You can now close this window and return to your terminal.</p>
                    <p style="color: #666; font-size: 14px;">The Spotify MCP server is now ready to use.</p>
                </body>
                </html>
            """
            self.wfile.write(html_content.encode("utf-8"))

            # Auth code is set, main thread will detect and shutdown server
            # Do NOT call shutdown() here to avoid double-shutdown race condition
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html_content = """
                <html>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: #E22134;">&#x2717; Authorization Failed</h1>
                    <p>No authorization code received. Please try again.</p>
                </body>
                </html>
            """
            self.wfile.write(html_content.encode("utf-8"))

    def log_message(self, format, *args):
        """Suppress server logs."""
        pass


def auto_auth(settings) -> bool:
    """Perform automatic browser-based OAuth flow.

    Returns:
        bool: True if successful, False otherwise.
    """
    # Reset auth_code to avoid reusing stale codes from previous runs
    CallbackHandler.auth_code = None

    print("🔐 Starting automatic browser-based authentication...")
    print(f"📍 Redirect URI: {settings.redirect_uri}")

    # Parse port from redirect URI
    parsed_uri = urlparse(settings.redirect_uri)
    port = parsed_uri.port or 8888

    auth_manager_kwargs = {
        "client_id": settings.client_id,
        "client_secret": settings.client_secret,
        "redirect_uri": settings.redirect_uri,
        "scope": settings.scope,
        "open_browser": False,  # We'll open it ourselves
    }
    if settings.cache_path:
        auth_manager_kwargs["cache_path"] = settings.cache_path

    auth_manager = SpotifyOAuth(**auth_manager_kwargs)
    auth_url = auth_manager.get_authorize_url()

    # Start local server
    server = HTTPServer(("127.0.0.1", port), CallbackHandler)
    CallbackHandler.server_instance = (
        server  # Allow handler to shutdown server
    )

    # Use serve_forever() to handle multiple requests (favicon, callback, etc.)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    print(f"\n🌐 Opening browser for authorization...")
    print(f"   URL: {auth_url}\n")

    # Open browser
    browser_opened = webbrowser.open(auth_url)
    if not browser_opened:
        print("⚠️  Could not open browser automatically from Docker.")
        print(f"   Please visit this URL in your browser: {auth_url}\n")
        print("💡 Tip: For manual copy-paste flow, run without --auto flag")
        print(
            "\nAfter authorizing, paste the full redirect URL here (or press Ctrl+C to cancel):"
        )

        # Fall back to manual input
        try:
            redirect_response = input().strip()
            server.shutdown()
            server.server_close()
            server_thread.join(timeout=5)

            if redirect_response:
                try:
                    code = auth_manager.parse_response_code(redirect_response)
                    CallbackHandler.auth_code = code
                except Exception as e:
                    print(
                        f"\n✗ Failed to parse redirect URL: {e}",
                        file=sys.stderr,
                    )
                    return False
            else:
                print("\n✗ No URL provided", file=sys.stderr)
                return False
        except KeyboardInterrupt:
            print("\n\n✗ Authorization cancelled by user")
            server.shutdown()
            server.server_close()
            server_thread.join(timeout=5)
            return False
    else:
        print("⏳ Waiting for authorization...")
        # Wait for auth code or timeout
        start_time = time.time()
        while not CallbackHandler.auth_code and (
            time.time() - start_time < 120
        ):
            time.sleep(0.5)

        # Shutdown server
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=5)

    if CallbackHandler.auth_code:
        print("✓ Authorization code received!")
        try:
            token_info = auth_manager.get_access_token(
                CallbackHandler.auth_code, as_dict=True
            )
            if token_info:
                cache_location = settings.cache_path or ".cache"
                print(f"\n✓ Success! Token cached at: {cache_location}")
                print("🎵 You can now use the Spotify MCP server.")
                return True
        except Exception as e:
            print(f"\n✗ Failed to obtain token: {e}", file=sys.stderr)
            return False

    print("\n✗ Authorization timeout or failed", file=sys.stderr)
    return False


def manual_auth(settings) -> bool:
    """Perform manual copy-paste OAuth flow.

    Returns:
        bool: True if successful, False otherwise.
    """
    # Reset auth_code to avoid reusing stale codes from previous runs
    CallbackHandler.auth_code = None

    auth_manager_kwargs = {
        "client_id": settings.client_id,
        "client_secret": settings.client_secret,
        "redirect_uri": settings.redirect_uri,
        "scope": settings.scope,
        "open_browser": False,
    }
    if settings.cache_path:
        auth_manager_kwargs["cache_path"] = settings.cache_path

    auth_manager = SpotifyOAuth(**auth_manager_kwargs)
    auth_url = auth_manager.get_authorize_url()

    print("Please visit this URL to authorize the application:")
    print(f"\n{auth_url}\n")
    print("After authorizing, you will be redirected to a URL.")
    print("Please paste the full redirect URL here:")

    redirect_response = input().strip()

    if not redirect_response:
        print("Error: No redirect URL provided", file=sys.stderr)
        return False

    try:
        code = auth_manager.parse_response_code(redirect_response)
        token_info = auth_manager.get_access_token(code, as_dict=True)

        if token_info:
            cache_location = settings.cache_path or ".cache"
            print(f"\n✓ Success! Token cached at: {cache_location}")
            print("You can now use the Spotify MCP server.")
            return True
    except Exception as e:
        print(f"\n✗ Failed: {e}", file=sys.stderr)
        return False

    return False


def main() -> None:
    """Initialize Spotify OAuth and cache the token."""
    print("=== Spotify MCP Authentication Initializer ===\n")

    try:
        settings = load_settings()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Check for --auto flag
    use_auto = "--auto" in sys.argv or "-a" in sys.argv

    if use_auto:
        success = auto_auth(settings)
    else:
        print(
            "💡 Tip: Use --auto for automatic browser-based authentication\n"
        )
        success = manual_auth(settings)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
