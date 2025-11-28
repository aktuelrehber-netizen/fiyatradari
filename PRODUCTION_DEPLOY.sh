#!/bin/bash

# Production Deployment Script
# Domains: fiyatradari.com, admin.fiyatradari.com, api.fiyatradari.com

set -e

echo "🚀 Starting Production Deployment..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if SSH host is provided
if [ -z "$1" ]; then
    echo "${RED}Error: SSH host not provided${NC}"
    echo "Usage: ./PRODUCTION_DEPLOY.sh user@server"
    exit 1
fi

SSH_HOST=$1
SSH_PORT=${2:-22}
REMOTE_PATH="/var/www/fiyatradari"

echo "${YELLOW}📡 Connecting to $SSH_HOST (port $SSH_PORT)...${NC}"

# Execute deployment on remote server
ssh -p $SSH_PORT $SSH_HOST << 'ENDSSH'
set -e

echo "📂 Navigating to project directory..."
cd /var/www/fiyatradari

echo "🔄 Pulling latest changes from git..."
git pull origin main

echo "🛑 Stopping services..."
docker compose down

echo "🧹 Cleaning up old images and volumes..."
docker system prune -f

echo "🔨 Building new images..."
docker compose build --no-cache

echo "🗄️ Running database migrations..."
docker compose run --rm backend alembic upgrade head

echo "🚀 Starting services..."
docker compose up -d

echo "⏳ Waiting for services to be healthy..."
sleep 10

echo "✅ Checking service health..."
docker compose ps

echo "📊 Checking logs..."
docker compose logs --tail=50 backend
docker compose logs --tail=50 celery-worker
docker compose logs --tail=50 celery-beat

echo "🎉 Deployment completed successfully!"

ENDSSH

echo "${GREEN}✅ Deployment to production completed!${NC}"
echo ""
echo "Services:"
echo "  - Web: https://fiyatradari.com"
echo "  - Admin: https://admin.fiyatradari.com"
echo "  - API: https://api.fiyatradari.com"
echo ""
echo "To check logs:"
echo "  ssh $SSH_HOST 'cd /var/www/fiyatradari && docker compose logs -f'"
