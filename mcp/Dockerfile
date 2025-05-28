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

# Expose both ports
EXPOSE 3002 3030

# Create a startup script
RUN echo '#!/bin/bash\n\
  # Start the file server in the background\n\
  cd /app/calendar && python -m http.server 3030 &\n\
  # Return to app directory and start the main server\n\
  cd /app && uv run python calendar-mcp-server.py sse\n\
  ' > /app/start.sh && chmod +x /app/start.sh

# Start both servers using the startup script
CMD ["/app/start.sh"]
