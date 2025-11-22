# 🚀 PRODUCTION DEPLOYMENT GUIDE
## Ubuntu 24.04 LTS Sunucu Kurulumu ve Yayına Alma

**Hedef Sunucu:** Ubuntu 24.04 LTS  
**Deployment Yöntemi:** Docker + Git  
**SSL:** Let's Encrypt (Ücretsiz)  
**CI/CD:** Git-based deployment  

---

## 📋 ÖN HAZIRLIK

### 1. Sunucu Bilgileri
```bash
# Bunları not al:
Sunucu IP: __________________
Domain: fiyatradari.com
SSH User: __________________
SSH Port: 22 (varsayılan)
```

### 2. Domain Ayarları (İlk Yapılacak)
```
DNS kayıtlarını ayarla (domain sağlayıcında):

A Record:
fiyatradari.com           → Sunucu IP
www.fiyatradari.com       → Sunucu IP

A Record (Alt domainler - opsiyonel):
api.fiyatradari.com       → Sunucu IP
admin.fiyatradari.com     → Sunucu IP
grafana.fiyatradari.com   → Sunucu IP

# DNS propagation: 1-24 saat sürebilir
# Test: ping fiyatradari.com
```

---

## 🔧 ADIM 1: SUNUCUYA BAĞLAN

### SSH ile Bağlantı
```bash
# Local bilgisayardan:
ssh root@SUNUCU_IP

# veya sudo user ile:
ssh kullanici@SUNUCU_IP
```

### Güvenlik: SSH Key Oluştur (Önerilen)
```bash
# Local'de (Mac/Linux):
ssh-keygen -t ed25519 -C "fiyatradari-production"

# Public key'i kopyala:
cat ~/.ssh/id_ed25519.pub
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFHkN0ZZtVhDxWNbq2wOyeaorVbtdBN4ljmqS/OtIqRg fiyatradari-production

# Sunucuda:
mkdir -p ~/.ssh
nano ~/.ssh/authorized_keys
# Public key'i yapıştır, kaydet

# Sunucuda izinleri ayarla:
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# Artık şifresiz giriş:
ssh root@SUNUCU_IP
```

---

## 🔧 ADIM 2: SUNUCU HAZIRLIĞI

### Sistem Güncelleme
```bash
# Root olarak:
sudo apt update
sudo apt upgrade -y
sudo apt dist-upgrade -y
sudo apt autoremove -y
```

### Firewall Ayarları (UFW)
```bash
# UFW kur ve aktif et:
sudo apt install ufw -y

# Kurallar:
sudo ufw allow 22/tcp          # SSH
sudo ufw allow 80/tcp          # HTTP
sudo ufw allow 443/tcp         # HTTPS
sudo ufw allow 5432/tcp        # PostgreSQL (sadece local)
sudo ufw allow 6379/tcp        # Redis (sadece local)

# Aktif et:
sudo ufw enable
sudo ufw status

# Çıktı:
# Status: active
# To                         Action      From
# --                         ------      ----
# 22/tcp                     ALLOW       Anywhere
# 80/tcp                     ALLOW       Anywhere
# 443/tcp                    ALLOW       Anywhere
```

### Fail2ban (Güvenlik)
```bash
# Brute force saldırılarına karşı:
sudo apt install fail2ban -y

# Yapılandır:
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local

# [sshd] bölümünü bul ve düzenle:
[sshd]
enabled = true
port = ssh
logpath = %(sshd_log)s
maxretry = 5
bantime = 3600

# Başlat:
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
sudo fail2ban-client status
```

### Swap Oluştur (Önerilen - 4GB RAM altıysa)
```bash
# 2GB swap:
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Kalıcı yap:
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Kontrol:
free -h
```

---

## 🐳 ADIM 3: DOCKER KURULUMU

### Docker Engine Kurulumu
```bash
# Eski sürümleri kaldır:
sudo apt remove docker docker-engine docker.io containerd runc

# Gerekli paketler:
sudo apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Docker GPG key:
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Docker repository:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Kur:
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Test:
sudo docker run hello-world
# "Hello from Docker!" mesajı görmeli

# User'ı docker grubuna ekle:
sudo usermod -aG docker $USER
newgrp docker

# Test (sudo olmadan):
docker ps
```

### Docker Compose Kurulumu
```bash
# Docker Compose V2 (plugin olarak geldi)
docker compose version
# Docker Compose version v2.x.x

# Eski standalone versiyonu kaldır:
sudo rm /usr/local/bin/docker-compose
```

---

## 📦 ADIM 4: GIT KURULUMU VE PROJE KLONLAMA

### Git Kur
```bash
sudo apt install git -y
git --version
```

### GitHub SSH Key (Önerilen)
```bash
# Sunucuda SSH key oluştur:
ssh-keygen -t ed25519 -C "production-server"

# Public key'i göster:
cat ~/.ssh/id_ed25519.pub
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPeSv1fhpGbRXAC+13Vs4kvxPCJHkHS8J0rNYUml7oBN production-server

# GitHub'da:
# Settings → SSH Keys → New SSH key
# Title: "Production Server"
# Key: (yukarıdaki çıktıyı yapıştır)

# Test:
ssh -T git@github.com
# "Hi username! You've successfully authenticated"
```

### Proje Klasörü Oluştur
```bash
# Production klasörü:
sudo mkdir -p /var/www
cd /var/www

# Git clone (HTTPS veya SSH):
# HTTPS:
sudo git clone https://github.com/aktuelrehber-netizen/fiyatradari.git

# veya SSH (önerilen):
sudo git clone git@github.com:aktuelrehber-netizen/fiyatradari.git

# İzinleri ayarla:
sudo chown -R $USER:$USER /var/www/fiyatradari
    cd /var/www/fiyatradari
```

---

## 🔐 ADIM 5: ENVIRONMENT VARIABLES

### Production .env Dosyası
```bash
cd /var/www/fiyatradari

# .env.production'ı .env olarak kopyala:
cp .env.production .env

# Düzenle:
nano .env
```

### Kritik Ayarlar (.env):
```bash
# PostgreSQL
POSTGRES_PASSWORD=<güçlü-şifre-buraya>  # MUTLAKA DEĞİŞTİR!

# Backend
DATABASE_URL=postgresql://fiyatradari:<güçlü-şifre-buraya>@postgres:5432/fiyatradari
SECRET_KEY=<64-karakter-random-key>  # MUTLAKA DEĞİŞTİR!

# Amazon API
AMAZON_ACCESS_KEY=<amazon-access-key>
AMAZON_SECRET_KEY=<amazon-secret-key>
AMAZON_PARTNER_TAG=<partner-tag>

# Telegram
TELEGRAM_BOT_TOKEN=<bot-token>
TELEGRAM_CHANNEL_ID=<channel-id>

# Web Frontend
NEXT_PUBLIC_API_URL=https://api.fiyatradari.com
NEXT_PRIVATE_API_URL=http://backend:8000
NEXT_PUBLIC_SITE_URL=https://fiyatradari.com
NODE_ENV=production

# Monitoring
SENTRY_DSN=<sentry-dsn>
NEXT_PUBLIC_GA_ID=<google-analytics-id>
GRAFANA_PASSWORD=<güçlü-şifre>

# Email (opsiyonel)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<email>
SMTP_PASSWORD=<app-password>
```

### Güçlü Şifre Oluştur
```bash
# PostgreSQL şifresi:
openssl rand -base64 32
i+mgazu+AAMnbtB67DC3R43qNBim5/3Qjrv/t6tGhRs=

# SECRET_KEY:
openssl rand -hex 32
21fc1021203d4a31117b3c756f0325e8f0797824eb151c93f21df696d3104fa5

# Grafana şifresi:
openssl rand -base64 24
```
LtnLXt4PRZ9tybcxItEtM7bHL5/yAbnO

### .env Güvenliği
```bash
# Sadece owner okuyabilsin:
chmod 600 .env

# Git'e ekleme:
echo ".env" >> .gitignore
```

---

## 🏗️ ADIM 6: PRODUCTION DEPLOYMENT

### İlk Deploy
```bash
cd /var/www/fiyatradari

# Docker Compose ile başlat:
docker compose up -d

# Logları izle:
docker compose logs -f

# Servis durumu:
docker compose ps
```

### Healthcheck
```bash
# Backend:
curl http://localhost:8000/health
# {"status":"healthy"}

# Web:
curl http://localhost:3000
# HTML döner

# Admin:
curl http://localhost:3001
# HTML döner
```

### Database Migration & Seed
```bash
# Database migration (otomatik olmalı):
docker compose exec backend alembic upgrade head

# Test data (opsiyonel - ilk kurulumda):
docker compose exec backend python -c "
from app.db.database import SessionLocal, engine
from app.db import models
models.Base.metadata.create_all(bind=engine)
print('✅ Database initialized')
"

# Admin user oluştur (gerekirse):
docker compose exec backend python scripts/create_admin.py
```

---

## 🌐 ADIM 7: NGINX REVERSE PROXY (Host Makinede)

### Nginx Kur
```bash
sudo apt install nginx -y
sudo systemctl enable nginx
sudo systemctl start nginx
```

### Nginx Yapılandırması
```bash
# Ana config dosyası:
sudo nano /etc/nginx/sites-available/firsatradari.com

# İçerik:
```

```nginx
# HTTP → HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name firsatradari.com www.firsatradari.com;
    
    # Let's Encrypt için:
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS - Main Site
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name firsatradari.com www.firsatradari.com;
    
    # SSL certificates (Let's Encrypt sonrası)
    ssl_certificate /etc/letsencrypt/live/firsatradari.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/firsatradari.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Proxy to Next.js
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}

# API
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.firsatradari.com;
    
    ssl_certificate /etc/letsencrypt/live/firsatradari.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/firsatradari.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Admin Panel
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name admin.firsatradari.com;
    
    ssl_certificate /etc/letsencrypt/live/firsatradari.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/firsatradari.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Nginx Aktif Et
```bash
# Symlink oluştur:
sudo ln -s /etc/nginx/sites-available/firsatradari.com /etc/nginx/sites-enabled/

# Default site'ı kaldır:
sudo rm /etc/nginx/sites-enabled/default

# Test:
sudo nginx -t

# Reload:
sudo systemctl reload nginx
```

---

## 🔒 ADIM 8: SSL CERTIFICATE (Let's Encrypt)

### Certbot Kur
```bash
sudo apt install certbot python3-certbot-nginx -y
```

### SSL Certificate Al
```bash
# Önce DNS'in düzgün çalıştığından emin ol:
ping fiyatradari.com
ping www.fiyatradari.com
ping api.fiyatradari.com
ping admin.fiyatradari.com

# Certificate al (tüm domainler için):
sudo certbot --nginx -d fiyatradari.com \
                      -d www.fiyatradari.com \
                      -d api.fiyatradari.com \
                      -d admin.fiyatradari.com

# Sorular:
# Email: your-email@example.com
# Terms of Service: Agree
# Share email: No
```

### Auto-Renewal Test
```bash
# Test:
sudo certbot renew --dry-run

# Cron job (otomatik yenileme):
sudo crontab -e

# Ekle:
0 12 * * * /usr/bin/certbot renew --quiet
```

### SSL Test
```bash
# Online test:
https://www.ssllabs.com/ssltest/analyze.html?d=fiyatradari.com

# Hedef: A+ rating
```

---

## 📊 ADIM 9: MONİTORİNG SETUP

### Grafana & Prometheus
```bash
cd /var/www/fiyatradari

# Zaten docker-compose.yml'de var, aktif et:
docker compose up -d prometheus grafana

# Grafana'ya eriş:
# Nginx ile expose et (opsiyonel):
```

```nginx
# /etc/nginx/sites-available/fiyatradari.com'a ekle:

server {
    listen 443 ssl http2;
    server_name grafana.fiyatradari.com;
    
    ssl_certificate /etc/letsencrypt/live/fiyatradari.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/fiyatradari.com/privkey.pem;
    
    # Basic auth (opsiyonel):
    # auth_basic "Grafana";
    # auth_basic_user_file /etc/nginx/.htpasswd;
    
    location / {
        proxy_pass http://localhost:3002;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

```bash
# Nginx reload:
sudo systemctl reload nginx
```

---

## 💾 ADIM 10: BACKUP STRATEJİSİ

### Database Backup Script
```bash
# Backup script oluştur:
sudo nano /usr/local/bin/backup-fiyatradari.sh
```

```bash
#!/bin/bash
# Fiyatradari Backup Script

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/fiyatradari"
PROJECT_DIR="/var/www/fiyatradari"

# Backup klasörü oluştur:
mkdir -p $BACKUP_DIR

# Database backup:
docker exec fiyatradari_postgres pg_dump -U fiyatradari fiyatradari | \
    gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Redis backup (opsiyonel):
docker exec fiyatradari_redis redis-cli SAVE
docker cp fiyatradari_redis:/data/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# .env backup:
cp $PROJECT_DIR/.env $BACKUP_DIR/env_$DATE

# Docker volumes backup (opsiyonel):
# docker run --rm -v fiyatradari_postgres_data:/data -v $BACKUP_DIR:/backup \
#     alpine tar czf /backup/postgres_data_$DATE.tar.gz /data

# 30 günden eski backupları sil:
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +30 -delete
find $BACKUP_DIR -name "env_*" -mtime +30 -delete

echo "✅ Backup completed: $DATE"
```

```bash
# Çalıştırılabilir yap:
sudo chmod +x /usr/local/bin/backup-fiyatradari.sh

# Test:
sudo /usr/local/bin/backup-fiyatradari.sh

# Cron job (her gün 03:00):
sudo crontab -e

# Ekle:
0 3 * * * /usr/local/bin/backup-fiyatradari.sh >> /var/log/fiyatradari-backup.log 2>&1
```

### Restore Script
```bash
sudo nano /usr/local/bin/restore-fiyatradari.sh
```

```bash
#!/bin/bash
# Fiyatradari Restore Script

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo "Available backups:"
    ls -lh /var/backups/fiyatradari/*.sql.gz
    exit 1
fi

BACKUP_FILE=$1

# Container durdur:
cd /var/www/fiyatradari
docker compose stop backend worker

# Database restore:
gunzip < $BACKUP_FILE | \
    docker exec -i fiyatradari_postgres psql -U fiyatradari fiyatradari

# Container başlat:
docker compose start backend worker

echo "✅ Restore completed"
```

```bash
sudo chmod +x /usr/local/bin/restore-fiyatradari.sh

# Kullanım:
# sudo /usr/local/bin/restore-fiyatradari.sh /var/backups/fiyatradari/db_20251120_030000.sql.gz
```

---

## 🔄 ADIM 11: DEPLOYMENT WORKFLOW (LOCAL → PRODUCTION)

### Deployment Script
```bash
# Local'de (Mac/Linux):
nano deploy.sh
```

```bash
#!/bin/bash
# Fiyatradari Deployment Script

set -e  # Exit on error

echo "🚀 Starting deployment..."

# 1. Git push
echo "📤 Pushing to GitHub..."
git add .
git commit -m "${1:-Update}" || true
git push origin main

# 2. SSH to production
echo "🔧 Deploying to production..."
ssh root@SUNUCU_IP << 'ENDSSH'
    cd /var/www/fiyatradari
    
    # Pull latest
    git pull origin main
    
    # Rebuild & restart
    docker compose build
    docker compose up -d
    
    # Health check
    sleep 10
    curl -f http://localhost:8000/health || exit 1
    
    echo "✅ Deployment successful!"
ENDSSH

echo "🎉 Deployment completed!"
```

```bash
# Çalıştırılabilir yap:
chmod +x deploy.sh

# Kullanım:
./deploy.sh "Feature: Added new category"
```

### GitHub Actions CI/CD (Gelişmiş - Opsiyonel)
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_IP }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /var/www/fiyatradari
            git pull origin main
            docker compose build
            docker compose up -d
            docker compose exec -T backend alembic upgrade head
```

---

## 📊 ADIM 12: POST-DEPLOYMENT CHECKLIST

### Kontroller
```bash
# 1. Servisler çalışıyor mu?
docker compose ps
# Hepsi "Up" olmalı

# 2. Nginx çalışıyor mu?
sudo systemctl status nginx

# 3. SSL geçerli mi?
curl -I https://fiyatradari.com | grep "HTTP/2 200"

# 4. Database bağlantısı?
docker compose exec backend python -c "
from app.db.database import engine
engine.connect()
print('✅ Database OK')
"

# 5. API çalışıyor mu?
curl https://api.fiyatradari.com/health

# 6. Web açılıyor mu?
curl -I https://fiyatradari.com

# 7. Admin panel?
curl -I https://admin.fiyatradari.com
```

### Monitoring
```bash
# Grafana:
https://grafana.fiyatradari.com

# Prometheus:
http://SUNUCU_IP:9090

# Logs:
docker compose logs -f --tail=100
```

---

## 🔧 MAINTENANCE KOMUTLARI

### Günlük İşlemler
```bash
# Logları görüntüle:
docker compose logs -f backend
docker compose logs -f worker

# Container restart:
docker compose restart backend

# Database backup (manuel):
/usr/local/bin/backup-fiyatradari.sh

# Disk kullanımı:
df -h
docker system df
```

### Güncelleme
```bash
cd /var/www/fiyatradari

# Git pull:
git pull origin main

# Rebuild:
docker compose build

# Restart:
docker compose up -d

# Migration:
docker compose exec backend alembic upgrade head
```

### Temizlik
```bash
# Eski image'ları temizle:
docker system prune -a

# Eski log'ları temizle:
sudo find /var/log -name "*.log" -mtime +30 -delete

# Disk usage:
du -sh /var/www/fiyatradari/*
```

---

## 🚨 TROUBLESHOOTING

### Sorun: Container başlamıyor
```bash
# Logları kontrol:
docker compose logs container_name

# Restart:
docker compose restart container_name

# Rebuild:
docker compose up -d --build container_name
```

### Sorun: Database connection error
```bash
# PostgreSQL logları:
docker compose logs postgres

# Bağlantı test:
docker compose exec postgres psql -U fiyatradari -d fiyatradari

# .env kontrol:
cat .env | grep DATABASE_URL
```

### Sorun: Nginx 502 Bad Gateway
```bash
# Container çalışıyor mu?
docker compose ps

# Nginx logları:
sudo tail -f /var/log/nginx/error.log

# Test:
curl http://localhost:8000
curl http://localhost:3000
```

### Sorun: SSL hatası
```bash
# Certificate kontrol:
sudo certbot certificates

# Yenile:
sudo certbot renew

# Nginx reload:
sudo systemctl reload nginx
```

---

## 📈 PERFORMANCE TİPLERİ

### 1. Docker Optimization
```yaml
# docker-compose.yml'de:
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          memory: 1G
```

### 2. PostgreSQL Tuning
```bash
# postgres/postgresql.conf:
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 128MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
work_mem = 8MB
min_wal_size = 1GB
max_wal_size = 4GB
```

### 3. Nginx Caching
```nginx
# /etc/nginx/nginx.conf:
http {
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g inactive=60m;
    
    server {
        location /api/ {
            proxy_cache my_cache;
            proxy_cache_valid 200 5m;
            add_header X-Cache-Status $upstream_cache_status;
        }
    }
}
```

---

## ✅ DEPLOYMENT TAMAMLANDI!

### Çalışan Servisler:
- ✅ https://fiyatradari.com (Ana site)
- ✅ https://api.fiyatradari.com (API)
- ✅ https://admin.fiyatradari.com (Admin panel)
- ✅ https://grafana.fiyatradari.com (Monitoring)

### Güvenlik:
- ✅ SSL/TLS (Let's Encrypt)
- ✅ Firewall (UFW)
- ✅ Fail2ban
- ✅ SSH key authentication
- ✅ Security headers
- ✅ Regular backups

### Monitoring:
- ✅ Prometheus
- ✅ Grafana
- ✅ Health checks
- ✅ Log aggregation

### Next Steps:
1. Google Analytics entegrasyonu
2. Sentry error tracking
3. CDN (Cloudflare)
4. Load balancing (gelecekte)
5. Database replication (gelecekte)

**Production deployment başarıyla tamamlandı! 🎉**






# Docker servisleri restart et:
docker compose down
docker compose up -d

# Kontrol:
docker compose ps