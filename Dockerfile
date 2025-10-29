FROM python:3.14-slim

# Install system dependencies required by spotipy (none heavy), and runtime basics
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# Environment variables are provided by the MCP client config at runtime
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# The container runs over stdio; no port is exposed. CMD must keep process in foreground.
CMD ["python", "-u", "-m", "spotify_mcp.server"]


