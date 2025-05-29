# Use Python 3.13
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install Node.js and npm
RUN apt-get update && apt-get install -y \
  curl \
  && curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
  && apt-get install -y nodejs \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install requests flask "mcp[cli]" langchain-mcp-adapters python-dotenv langgraph langchain-google-genai

# Copy source code
COPY . .

# Expose port
EXPOSE 5000

# Start the Flask server
CMD ["python", "flask_server.py"]
