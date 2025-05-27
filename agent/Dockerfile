# Use Python 3.12.9 slim base image
FROM python:3.12.9-slim

# Install Node.js 22.14.0
RUN apt-get update && apt-get install -y curl gnupg && \
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
  apt-get install -y nodejs && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
  ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Set the working directory
WORKDIR /app

# Copy Poetry files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --no-root

# Copy the rest of the app
COPY . .

# Expose port (adjust if your app uses a different one)
EXPOSE 8000

# Start the app (replace with your actual command if different)
CMD ["poetry", "run", "server"]
