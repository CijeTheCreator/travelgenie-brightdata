# Use Python 3.13
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install dependencies
RUN pip install requests flask "mcp[cli]" langchain-mcp-adapters python-dotenv langgraph langchain-google-genai

# Copy source code
COPY . .

# Expose port
EXPOSE 5000

# Start the Flask server
CMD ["python", "flask_server.py"]
