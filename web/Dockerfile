FROM node:20-alpine AS base

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy project files
COPY . .

# Build Next.js app
RUN npm run build

# Expose port
EXPOSE 3000

# Start production server
CMD ["npm", "start"]
