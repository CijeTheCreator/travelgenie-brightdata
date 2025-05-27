# Use Python 3.13 with Node.js 22.14.0
FROM python:3.13-slim

# Install curl, Node.js 22.14.0, and system dependencies
RUN apt-get update && apt-get install -y curl && \
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
  apt-get install -y nodejs build-essential && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

# Install uv (dependency manager)
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy pyproject and lock file for uv sync
COPY pyproject.toml poetry.lock* README.md ./

# Sync dependencies
RUN uv sync

# Copy application source code
COPY . .

# Expose desired port
EXPOSE 3002

# Start the server using uv run
CMD ["uv", "run", "python", "calendar-mcp-server.py", "sse"]
