#!/bin/bash
# Diagnostic script to check MCP container behavior

echo "=== Spotify MCP Container Diagnostics ==="
echo ""

echo "Current containers:"
docker ps -a --filter "ancestor=spotify-mcp-local:latest" --format "table {{.ID}}\t{{.Status}}\t{{.CreatedAt}}"
echo ""

RUNNING=$(docker ps --filter "ancestor=spotify-mcp-local:latest" -q | wc -l | tr -d ' ')
STOPPED=$(docker ps -a --filter "ancestor=spotify-mcp-local:latest" --filter "status=exited" -q | wc -l | tr -d ' ')

echo "Summary:"
echo "  Running: $RUNNING"
echo "  Stopped: $STOPPED"
echo ""

if [ "$RUNNING" -gt 1 ]; then
    echo "⚠️  WARNING: Multiple containers running! This indicates the old ones didn't exit."
    echo ""
    echo "Container details:"
    for id in $(docker ps --filter "ancestor=spotify-mcp-local:latest" -q); do
        echo "  Container $id:"
        docker inspect $id --format '    Created: {{.Created}}'
        docker inspect $id --format '    State: {{.State.Status}}'
        docker top $id || echo "    (cannot get process list)"
        echo ""
    done
fi

if [ "$STOPPED" -gt 0 ]; then
    echo "ℹ️  Found $STOPPED stopped container(s). These should have been auto-removed by --rm."
    echo "   Cleaning them up now..."
    docker ps -a --filter "ancestor=spotify-mcp-local:latest" --filter "status=exited" -q | xargs -r docker rm
    echo "   Done."
fi

if [ "$RUNNING" -eq 0 ] && [ "$STOPPED" -eq 0 ]; then
    echo "✅ No containers found. Everything is clean!"
fi

