```docker
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
```


modify this so that after the server starts, it cd's into calendar/, which is a folder inside the root folder, and starts a file server there.
Start the server with 
```bash
python -m http.server 3030
```

Modify the compose service environment variable to point to the url of that file server
```bash
  # MCP Service (third in startup order)
  mcp:
    build: ./mcp
    container_name: mcp-service
    ports:
      - "3002:3002"
    environment:
      - CURRENCY_API_KEY=${CURRENCY_API_KEY}
      - RAPIDAPI_KEY=${RAPIDAPI_KEY}
      - BRIGHTDATA_AGENT_URL=http://brightdata-agent:5000
      - FILE_SERVER_URL=http://file-server:3030
    depends_on:
      - brightdata-agent
    networks:
      - app-network


```
