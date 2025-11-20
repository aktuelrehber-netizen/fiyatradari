#!/bin/bash
# Fiyatradari Quick Deployment Script
# Ubuntu 24.04 LTS için otomatik kurulum

set -e

echo "🚀 Fiyatradari Production Deployment"
echo "======================================"
echo ""

# Renkler
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonksiyonlar
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Root kontrolü
if [ "$EUID" -ne 0 ]; then 
    print_error "Lütfen root olarak çalıştırın: sudo ./QUICK_DEPLOY.sh"
    exit 1
fi

print_info "Sistem hazırlığı başlıyor..."

# 1. Sistem güncelleme
print_info "Sistem güncelleniyor..."
apt update && apt upgrade -y
apt dist-upgrade -y
apt autoremove -y
print_success "Sistem güncellendi"

# 2. Gerekli paketler
print_info "Gerekli paketler kuruluyor..."
apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    ufw \
    fail2ban \
    nginx \
    certbot \
    python3-certbot-nginx
print_success "Paketler kuruldu"

# 3. Firewall
print_info "Firewall yapılandırılıyor..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
print_success "Firewall aktif"

# 4. Fail2ban
print_info "Fail2ban yapılandırılıyor..."
systemctl enable fail2ban
systemctl start fail2ban
print_success "Fail2ban aktif"

# 5. Docker kurulumu
if ! command -v docker &> /dev/null; then
    print_info "Docker kuruluyor..."
    
    # Docker GPG key
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
        gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Docker repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
      https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Kur
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    print_success "Docker kuruldu"
else
    print_success "Docker zaten kurulu"
fi

# 6. Proje klasörü
print_info "Proje klasörü oluşturuluyor..."
mkdir -p /var/www
cd /var/www

# Git repository
if [ ! -d "/var/www/fiyatradari" ]; then
    print_info "GitHub repository URL'sini girin (örn: https://github.com/user/fiyatradari.git):"
    read REPO_URL
    
    git clone $REPO_URL fiyatradari
    print_success "Proje klonlandı"
else
    print_success "Proje klasörü mevcut"
fi

cd /var/www/fiyatradari

# 7. Environment variables
if [ ! -f ".env" ]; then
    print_info ".env dosyası oluşturuluyor..."
    
    if [ -f ".env.production" ]; then
        cp .env.production .env
        print_success ".env dosyası oluşturuldu (.env.production'dan)"
        print_error "UYARI: .env dosyasını düzenlemeyi unutma!"
        print_info "nano /var/www/fiyatradari/.env"
    else
        print_error ".env.production bulunamadı!"
        exit 1
    fi
else
    print_success ".env dosyası mevcut"
fi

# 8. Docker Compose başlat
print_info "Docker servisleri başlatılıyor..."
docker compose up -d
print_success "Docker servisleri başlatıldı"

# Servis durumu
sleep 5
docker compose ps

# 9. Nginx yapılandırma
print_info "Domain adınızı girin (örn: fiyatradari.com):"
read DOMAIN

cat > /etc/nginx/sites-available/$DOMAIN << EOF
# HTTP → HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN www.$DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://\$host\$request_uri;
    }
}

# HTTPS - Main Site
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;
    
    # SSL config (certbot sonrası)
    # ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl reload nginx
print_success "Nginx yapılandırıldı"

# 10. SSL Certificate
print_info "SSL certificate almak ister misiniz? (y/n)"
read SSL_CHOICE

if [ "$SSL_CHOICE" = "y" ]; then
    print_info "Email adresinizi girin:"
    read EMAIL
    
    certbot --nginx -d $DOMAIN -d www.$DOMAIN --email $EMAIL --agree-tos --no-eff-email
    print_success "SSL certificate kuruldu"
fi

# 11. Backup script
cat > /usr/local/bin/backup-fiyatradari.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/fiyatradari"
mkdir -p $BACKUP_DIR

# Database backup
docker exec fiyatradari_postgres pg_dump -U fiyatradari fiyatradari | \
    gzip > $BACKUP_DIR/db_$DATE.sql.gz

# .env backup
cp /var/www/fiyatradari/.env $BACKUP_DIR/env_$DATE

# Cleanup old backups
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
find $BACKUP_DIR -name "env_*" -mtime +30 -delete

echo "✅ Backup completed: $DATE"
EOF

chmod +x /usr/local/bin/backup-fiyatradari.sh
print_success "Backup scripti oluşturuldu"

# 12. Cron jobs
(crontab -l 2>/dev/null; echo "0 3 * * * /usr/local/bin/backup-fiyatradari.sh >> /var/log/fiyatradari-backup.log 2>&1") | crontab -
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
print_success "Cron jobs eklendi"

# Özet
echo ""
echo "======================================"
print_success "Kurulum tamamlandı!"
echo "======================================"
echo ""
echo "📋 Özet:"
echo "   - Docker servisleri: docker compose ps"
echo "   - Nginx: systemctl status nginx"
echo "   - SSL: certbot certificates"
echo "   - Logs: docker compose logs -f"
echo "   - Backup: /usr/local/bin/backup-fiyatradari.sh"
echo ""
echo "🌐 Web adresleri:"
echo "   - https://$DOMAIN"
echo "   - https://api.$DOMAIN"
echo "   - https://admin.$DOMAIN"
echo ""
echo "⚠️  Önemli:"
echo "   1. .env dosyasını düzenle: nano /var/www/fiyatradari/.env"
echo "   2. Şifreleri değiştir (POSTGRES_PASSWORD, SECRET_KEY, vb.)"
echo "   3. Amazon API keys ekle"
echo "   4. Telegram bot token ekle"
echo ""
print_info "Detaylı bilgi: cat /var/www/fiyatradari/PRODUCTION_DEPLOYMENT.md"
