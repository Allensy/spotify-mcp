#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-spotify-mcp:test}"
PORT="${PORT:-8000}"

docker run --rm -d \
  --name spotify-mcp-smoke \
  -p "${PORT}:8000" \
  -e MCP_TRANSPORT=sse \
  -e MCP_HOST=0.0.0.0 \
  -e MCP_PORT=8000 \
  -e MCP_SSE_PATH=/sse \
  -e SPOTIPY_CLIENT_ID=dummy \
  -e SPOTIPY_CLIENT_SECRET=dummy \
  -e SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback \
  "${IMAGE}"

cleanup() {
  docker rm -f spotify-mcp-smoke >/dev/null 2>&1 || true
}
trap cleanup EXIT

sleep 3

docker logs spotify-mcp-smoke

curl -fsS "http://127.0.0.1:${PORT}/sse" >/dev/null || {
  echo "SSE endpoint did not respond"
  exit 1
}

echo "SSE smoke test passed"
