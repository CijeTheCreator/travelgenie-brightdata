# Use Python 3.13
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy files
COPY . .

# Expose port
EXPOSE 3030

# Start the file server
CMD ["python", "-m", "http.server", "3030"]
