# Use Python 3.13 with Node.js 22.14.0
FROM python:3.13-slim

# Install curl, Node.js 22.14.0, nginx, and system dependencies
RUN apt-get update && apt-get install -y curl nginx && \
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

# Create nginx configuration
RUN echo 'server {\n\
  listen 80;\n\
  server_name localhost;\n\
  \n\
  location /calendars/ {\n\
  proxy_pass http://localhost:3030/;\n\
  proxy_set_header Host $host;\n\
  proxy_set_header X-Real-IP $remote_addr;\n\
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\
  proxy_set_header X-Forwarded-Proto $scheme;\n\
  }\n\
  \n\
  location /mcp/ {\n\
  proxy_pass http://localhost:3002/;\n\
  proxy_set_header Host $host;\n\
  proxy_set_header X-Real-IP $remote_addr;\n\
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\
  proxy_set_header X-Forwarded-Proto $scheme;\n\
  # For WebSocket support if needed\n\
  proxy_http_version 1.1;\n\
  proxy_set_header Upgrade $http_upgrade;\n\
  proxy_set_header Connection "upgrade";\n\
  }\n\
  \n\
  # Optional: Add a health check endpoint\n\
  location /health {\n\
  return 200 "OK";\n\
  add_header Content-Type text/plain;\n\
  }\n\
  }' > /etc/nginx/sites-available/default

# Expose port 80 for nginx (remove internal ports since they'll be proxied)
EXPOSE 80

# Create a startup script
RUN echo '#!/bin/bash\n\
  # Start nginx in the background\n\
  nginx &\n\
  # Start the file server in the background\n\
  cd /app/calendar && python -m http.server 3030 &\n\
  # Return to app directory and start the main server\n\
  cd /app && uv run python calendar-mcp-server.py sse\n\
  ' > /app/start.sh && chmod +x /app/start.sh

# Start all services using the startup script
CMD ["/app/start.sh"]
