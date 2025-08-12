FROM python:3.11-slim

# Install system dependencies required by spotipy (none heavy), and runtime basics
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_server.py ./
COPY spotify_tools.py ./
COPY config.py ./
COPY auth_init.py ./

# Environment variables are provided by the MCP client config at runtime
ENV PYTHONUNBUFFERED=1

# The container runs over stdio; no port is exposed. CMD must keep process in foreground.
CMD ["python", "-u", "mcp_server.py"]


