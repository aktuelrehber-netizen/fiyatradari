#!/bin/bash

# Remote Deployment Script - Runs on Server

set -e

echo "🚀 Starting Deployment..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Project path
PROJECT_PATH="/var/www/fiyatradari"
BACKUP_PATH="/root/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Navigate to project
cd $PROJECT_PATH

echo "${YELLOW}💾 Creating backup...${NC}"
mkdir -p $BACKUP_PATH

# Backup database
echo "Backing up database..."
docker compose exec -T postgres pg_dump -U fiyatradari fiyatradari > $BACKUP_PATH/db_backup_$TIMESTAMP.sql

# Backup .env files
echo "Backing up configuration..."
cp .env $BACKUP_PATH/.env.backup_$TIMESTAMP
cp admin-panel/.env.local $BACKUP_PATH/.env.admin.backup_$TIMESTAMP 2>/dev/null || true
cp web/.env.local $BACKUP_PATH/.env.web.backup_$TIMESTAMP 2>/dev/null || true

echo "${GREEN}✅ Backup completed!${NC}"

echo "${YELLOW}🔄 Pulling latest changes...${NC}"
git pull origin main

echo "${YELLOW}🛑 Stopping services...${NC}"
docker compose down

echo "${YELLOW}🧹 Cleaning up...${NC}"
docker system prune -f

echo "${YELLOW}🔨 Building new images...${NC}"
docker compose build --no-cache

echo "${YELLOW}🗄️ Running database migrations...${NC}"
docker compose run --rm backend alembic upgrade head

echo "${YELLOW}🚀 Starting services...${NC}"
docker compose up -d

echo "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
sleep 15

echo "${GREEN}✅ Checking service status...${NC}"
docker compose ps

echo ""
echo "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo "Backup saved to: $BACKUP_PATH/db_backup_$TIMESTAMP.sql"
echo ""
echo "Services:"
echo "  - Web: https://fiyatradari.com"
echo "  - Admin: https://admin.fiyatradari.com"
echo "  - API: https://api.fiyatradari.com"
echo ""
echo "To check logs:"
echo "  cd $PROJECT_PATH"
echo "  docker compose logs -f [service_name]"
