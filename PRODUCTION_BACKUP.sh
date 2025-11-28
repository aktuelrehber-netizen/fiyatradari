#!/bin/bash

# Production Backup Script
# Create backup before deployment

set -e

echo "💾 Starting Production Backup..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if SSH host is provided
if [ -z "$1" ]; then
    echo "${RED}Error: SSH host not provided${NC}"
    echo "Usage: ./PRODUCTION_BACKUP.sh user@server"
    exit 1
fi

SSH_HOST=$1
SSH_PORT=${2:-22}
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create local backup directory
mkdir -p $BACKUP_DIR

echo "${YELLOW}📡 Connecting to $SSH_HOST (port $SSH_PORT)...${NC}"

# Create backup on remote server and download
ssh -p $SSH_PORT $SSH_HOST << ENDSSH
set -e

echo "📂 Creating backup directory..."
mkdir -p /tmp/fiyatradari_backup

echo "🗄️ Backing up PostgreSQL database..."
cd /var/www/fiyatradari
docker compose exec -T postgres pg_dump -U fiyatradari fiyatradari > /tmp/fiyatradari_backup/database_$TIMESTAMP.sql

echo "📦 Backing up .env files..."
cp .env /tmp/fiyatradari_backup/.env.backend
cp admin-panel/.env.local /tmp/fiyatradari_backup/.env.admin 2>/dev/null || true
cp web/.env.local /tmp/fiyatradari_backup/.env.web 2>/dev/null || true

echo "🔒 Backing up docker-compose.yml..."
cp docker-compose.yml /tmp/fiyatradari_backup/docker-compose.yml

echo "📋 Creating backup archive..."
cd /tmp
tar -czf fiyatradari_backup_$TIMESTAMP.tar.gz fiyatradari_backup/

echo "✅ Backup created: /tmp/fiyatradari_backup_$TIMESTAMP.tar.gz"

ENDSSH

echo "${YELLOW}📥 Downloading backup to local machine...${NC}"
scp -P $SSH_PORT $SSH_HOST:/tmp/fiyatradari_backup_$TIMESTAMP.tar.gz $BACKUP_DIR/

echo "${GREEN}✅ Backup completed!${NC}"
echo "Backup saved to: $BACKUP_DIR/fiyatradari_backup_$TIMESTAMP.tar.gz"

# Cleanup remote backup
ssh -p $SSH_PORT $SSH_HOST "rm -rf /tmp/fiyatradari_backup /tmp/fiyatradari_backup_$TIMESTAMP.tar.gz"

echo ""
echo "To restore from backup:"
echo "  tar -xzf $BACKUP_DIR/fiyatradari_backup_$TIMESTAMP.tar.gz"
echo "  # Then restore database and .env files manually"
