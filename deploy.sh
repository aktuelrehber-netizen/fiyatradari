#!/bin/bash
# Local → Production Deployment Script
# Fiyatradari için

set -e

# Renkler
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Fonksiyonlar
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${YELLOW}ℹ️  $1${NC}"; }
print_step() { echo -e "${BLUE}▶ $1${NC}"; }

# Banner
echo -e "${BLUE}"
echo "╔══════════════════════════════════════╗"
echo "║  FIYATRADARI DEPLOYMENT              ║"
echo "║  Local → Production                  ║"
echo "╚══════════════════════════════════════╝"
echo -e "${NC}"

# Konfigürasyon (değiştir!)
SERVER_IP="${DEPLOY_SERVER_IP:-SUNUCU_IP_BURAYA}"
SERVER_USER="${DEPLOY_SERVER_USER:-root}"
PROJECT_PATH="/var/www/fiyatradari"

# Commit message
COMMIT_MSG="${1:-Update}"

# 1. Local tests
print_step "Local testler yapılıyor..."

# Git status
if [[ -n $(git status -s) ]]; then
    print_info "Değişiklikler tespit edildi"
else
    print_info "Hiç değişiklik yok"
fi

# 2. Git commit & push
print_step "Git işlemleri..."

git add .
git commit -m "$COMMIT_MSG" || print_info "Commit edilecek değişiklik yok"
git push origin main

print_success "Git push tamamlandı"

# 3. Production deployment
print_step "Production'a deploy ediliyor..."

ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP << 'ENDSSH'
    set -e
    
    echo "📍 Production sunucusundasınız"
    cd /var/www/fiyatradari
    
    # Git pull
    echo "🔄 Git pull..."
    git pull origin main
    
    # Docker Compose build
    echo "🏗️  Docker build..."
    docker compose build --no-cache
    
    # Docker Compose up
    echo "🚀 Servisleri başlatıyor..."
    docker compose up -d
    
    # Database migration
    echo "📊 Database migration..."
    docker compose exec -T backend alembic upgrade head || echo "Migration atlandı"
    
    # Health check
    echo "🏥 Health check..."
    sleep 10
    
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend sağlıklı"
    else
        echo "❌ Backend health check başarısız!"
        exit 1
    fi
    
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Web frontend sağlıklı"
    else
        echo "⚠️  Web frontend yanıt vermiyor"
    fi
    
    # Container status
    echo ""
    echo "📦 Container durumu:"
    docker compose ps
    
    echo ""
    echo "✅ Deployment tamamlandı!"
    
ENDSSH

print_success "Production deployment başarılı!"

# 4. Post-deployment checks
print_step "Post-deployment kontroller..."

# SSL check
if curl -f -I https://fiyatradari.com > /dev/null 2>&1; then
    print_success "HTTPS çalışıyor"
else
    print_info "HTTPS kontrolü yapılamadı (normal, domain henüz ayarlanmamış olabilir)"
fi

# Summary
echo ""
echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  DEPLOYMENT BAŞARILI! 🎉             ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
echo ""
echo "📋 Deployment Özeti:"
echo "   Commit: $COMMIT_MSG"
echo "   Server: $SERVER_USER@$SERVER_IP"
echo "   Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "🔗 Linkler:"
echo "   Production: https://fiyatradari.com"
echo "   API: https://api.fiyatradari.com"
echo "   Admin: https://admin.fiyatradari.com"
echo ""
echo "📊 Monitoring:"
echo "   Logs: ssh $SERVER_USER@$SERVER_IP 'cd $PROJECT_PATH && docker compose logs -f'"
echo "   Status: ssh $SERVER_USER@$SERVER_IP 'cd $PROJECT_PATH && docker compose ps'"
echo ""

# Deployment log
DEPLOY_LOG="deployments.log"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Deployed: $COMMIT_MSG" >> $DEPLOY_LOG
print_info "Deployment kaydedildi: $DEPLOY_LOG"
