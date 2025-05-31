# Use Node.js 22.14.0
FROM node:22.14.0-alpine

# Install pnpm
RUN npm install -g pnpm

# Set working directory
WORKDIR /app

# Copy environmental variables files
COPY .env.production .env

# Copy package files
COPY package.json pnpm-lock.yaml* ./

# Install dependencies
RUN pnpm install

# Copy source code
COPY . .

# Build the application
RUN pnpm build

# Expose port
EXPOSE 3000

# Start the production server
CMD ["npm", "run", "start"]
