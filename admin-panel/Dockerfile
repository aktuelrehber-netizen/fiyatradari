FROM node:18-alpine AS base

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Set environment variables for build
ENV NEXT_PUBLIC_API_URL=https://api.firsatradari.com
ENV NODE_ENV=production

# Build Next.js app
RUN npm run build

# Expose port
EXPOSE 3001

# Start production server
CMD ["npm", "start"]
