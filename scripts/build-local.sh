#!/bin/bash
# Quick script to build Docker image locally for testing

echo "Building Spotify MCP Docker image locally..."
docker build -t spotify-mcp-local:latest .

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Build successful!"
    echo ""
    echo "To use this local image, update your MCP config to use:"
    echo "  spotify-mcp-local:latest"
    echo ""
    echo "To test auth with automatic browser flow:"
    echo "  docker run --rm -it \\"
    echo "    -v \${HOME}/.cache/spotify-mcp:/app/.cache \\"
    echo "    -e SPOTIPY_CLIENT_ID=your-client-id \\"
    echo "    -e SPOTIPY_CLIENT_SECRET=your-client-secret \\"
    echo "    -e SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback \\"
    echo "    -e SPOTIPY_CACHE_PATH=/app/.cache/token \\"
    echo "    spotify-mcp-local:latest python -u -m spotify_mcp.cli.auth_init --auto"
else
    echo "✗ Build failed"
    exit 1
fi

