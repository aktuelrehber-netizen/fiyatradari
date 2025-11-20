# Fiyat Radarı - Production Deployment Rehberi

Bu doküman, Fiyat Radarı sisteminin Ubuntu 22.04 LTS sunucusunda production ortamına kurulumunu anlatmaktadır.

## 📋 Gereksinimler

### Sunucu Özellikleri
- **İşletim Sistemi:** Ubuntu 22.04 LTS
- **Minimum Kaynaklar:**
  - 2 CPU cores
  - 4GB RAM
  - 20GB disk alanı
  - Sabit IP adresi

### Domain Yapısı
- `api.firsatradari.com` - Backend API
- `admin.firsatradari.com` - Admin Panel
- `firsatradari.com` - Public Website

## 🔧 1. Sunucu Hazırlığı

### 1.1 Sistem Güncelleme
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Gerekli Paketlerin Kurulumu
```bash
# Docker kurulumu
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose kurulumu
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Git kurulumu
sudo apt install git -y

# Nginx kurulumu (reverse proxy için)
sudo apt install nginx -y

# Certbot kurulumu (SSL için)
sudo apt install certbot python3-certbot-nginx -y

# Sistem yeniden başlatma (opsiyonel)
sudo reboot
```

## 📦 2. Proje Kurulumu

### 2.1 Proje Dizinini Oluşturma
```bash
cd /opt
sudo mkdir fiyatradari
sudo chown $USER:$USER fiyatradari
cd fiyatradari
```

### 2.2 Kodu Sunucuya Aktarma

**Seçenek 1: Git Clone (önerilen)**
```bash
git clone <your-repo-url> .
```

**Seçenek 2: Local'den Upload**
```bash
# Local makinenizde:
rsync -avz --exclude 'node_modules' --exclude '.next' --exclude '__pycache__' \
  /Users/abdullahozturk/Sites/fiyatradari/ \
  user@your-server-ip:/opt/fiyatradari/
```

### 2.3 Environment Dosyasını Oluşturma
```bash
cp .env.example .env
nano .env
```

**Production .env örneği:**
```bash
# Database
DATABASE_URL=postgresql://fiyatradari:GÜÇLÜ_ŞİFRE@postgres:5432/fiyatradari
POSTGRES_USER=fiyatradari
POSTGRES_PASSWORD=GÜÇLÜ_ŞİFRE
POSTGRES_DB=fiyatradari

# API Security
SECRET_KEY=UZUN_RASGELE_GÜVENL_BİR_ANAHTAR_ÜRETİN
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Amazon PA API (gerçek bilgilerinizi girin)
AMAZON_ACCESS_KEY=AXXXXXXXXXXXXXXXXXXX
AMAZON_SECRET_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
AMAZON_PARTNER_TAG=yourpartner-21
AMAZON_REGION=eu-west-1
AMAZON_MARKETPLACE=www.amazon.com.tr

# Telegram Bot (gerçek bilgilerinizi girin)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
TELEGRAM_CHANNEL_ID=@yourchannelname

# CORS Origins (production domainleri)
ALLOWED_ORIGINS=https://firsatradari.com,https://admin.firsatradari.com

# Environment
ENVIRONMENT=production
```

**Güvenlik notu:** `.env` dosyası asla git'e commit edilmemelidir!

## 🐳 3. Docker ile Deployment

### 3.1 Production Docker Compose Oluşturma

`docker-compose.prod.yml` dosyasını oluşturun:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: fiyatradari_postgres
    env_file: .env
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - fiyatradari_network
    restart: always

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: fiyatradari_backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
    env_file: .env
    depends_on:
      - postgres
    networks:
      - fiyatradari_network
    restart: always

  worker:
    build:
      context: ./worker
      dockerfile: Dockerfile
    container_name: fiyatradari_worker
    command: python main.py
    env_file: .env
    depends_on:
      - postgres
    networks:
      - fiyatradari_network
    restart: always

volumes:
  postgres_data:

networks:
  fiyatradari_network:
    driver: bridge
```

### 3.2 Backend ve Worker'ı Çalıştırma
```bash
docker-compose -f docker-compose.prod.yml up -d postgres backend worker
```

### 3.3 Database İlk Kurulum
```bash
# Database tablolarını oluşturma
docker-compose -f docker-compose.prod.yml exec backend python -m app.db.init_db

# Varsayılan admin kullanıcısı oluşturulacaktır:
# Username: admin
# Password: admin123
# ⚠️ İLK GİRİŞTE ŞİFREYİ DEĞİŞTİRİN!
```

### 3.4 Container'ların Durumunu Kontrol
```bash
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f backend
```

## 🌐 4. Nginx Reverse Proxy Kurulumu

### 4.1 Backend API için Nginx Config

`/etc/nginx/sites-available/api.firsatradari.com`:

```nginx
server {
    listen 80;
    server_name api.firsatradari.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 10M;
}
```

### 4.2 Admin Panel için Nginx Config

**Admin Panel'i Build Etme:**
```bash
cd /opt/fiyatradari/admin-panel
npm install
NEXT_PUBLIC_API_URL=https://api.firsatradari.com npm run build

# PM2 ile çalıştırma (opsiyonel)
npm install -g pm2
pm2 start npm --name "admin-panel" -- start
pm2 save
pm2 startup
```

`/etc/nginx/sites-available/admin.firsatradari.com`:

```nginx
server {
    listen 80;
    server_name admin.firsatradari.com;

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

### 4.3 Nginx'i Etkinleştirme
```bash
sudo ln -s /etc/nginx/sites-available/api.firsatradari.com /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/admin.firsatradari.com /etc/nginx/sites-enabled/

# Nginx config test
sudo nginx -t

# Nginx restart
sudo systemctl restart nginx
```

## 🔒 5. SSL Sertifikası (Let's Encrypt)

```bash
# API için SSL
sudo certbot --nginx -d api.firsatradari.com

# Admin panel için SSL
sudo certbot --nginx -d admin.firsatradari.com

# Public website için SSL (hazır olduğunda)
sudo certbot --nginx -d firsatradari.com -d www.firsatradari.com

# Otomatik yenileme testi
sudo certbot renew --dry-run
```

## 🔥 6. Firewall Ayarları

```bash
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
sudo ufw status
```

## 📊 7. Monitoring & Logging

### 7.1 Container Loglarını İzleme
```bash
# Tüm loglar
docker-compose -f docker-compose.prod.yml logs -f

# Sadece backend
docker-compose -f docker-compose.prod.yml logs -f backend

# Sadece worker
docker-compose -f docker-compose.prod.yml logs -f worker
```

### 7.2 Disk Kullanımı Kontrolü
```bash
df -h
docker system df
```

### 7.3 Worker Durumu Kontrolü
Admin panel üzerinden **Sistem Sağlığı** sayfasından kontrol edebilirsiniz.

## 🔄 8. Güncelleme Prosedürü

```bash
cd /opt/fiyatradari

# Kodu güncelleme
git pull

# Container'ları yeniden build ve başlatma
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Admin panel güncelleme
cd admin-panel
npm install
NEXT_PUBLIC_API_URL=https://api.firsatradari.com npm run build
pm2 restart admin-panel
```

## 💾 9. Backup Stratejisi

### 9.1 Database Backup Script

`/opt/fiyatradari/scripts/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/fiyatradari"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# PostgreSQL backup
docker exec fiyatradari_postgres pg_dump -U fiyatradari fiyatradari > "$BACKUP_DIR/db_$DATE.sql"

# Compress
gzip "$BACKUP_DIR/db_$DATE.sql"

# Keep only last 7 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete

echo "Backup completed: db_$DATE.sql.gz"
```

### 9.2 Otomatik Backup (Cron)
```bash
chmod +x /opt/fiyatradari/scripts/backup.sh

# Crontab düzenleme
crontab -e

# Her gün saat 02:00'de backup
0 2 * * * /opt/fiyatradari/scripts/backup.sh >> /var/log/fiyatradari-backup.log 2>&1
```

## 🔍 10. Troubleshooting

### Backend API Çalışmıyor
```bash
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml restart backend
```

### Database Bağlantı Sorunu
```bash
docker-compose -f docker-compose.prod.yml exec postgres psql -U fiyatradari -d fiyatradari
```

### Worker Çalışmıyor
```bash
docker-compose -f docker-compose.prod.yml logs worker
docker-compose -f docker-compose.prod.yml restart worker
```

### Disk Doldu
```bash
# Docker temizliği
docker system prune -a --volumes

# Log dosyalarını temizleme
sudo journalctl --vacuum-time=3d
```

## 📈 11. Performance Optimization

### Database Optimization
```sql
-- PostgreSQL container içinde
docker exec -it fiyatradari_postgres psql -U fiyatradari

-- Index'leri kontrol etme
\di

-- Slow query monitoring
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();
```

### Nginx Caching
```nginx
# Nginx config'e ekleyin
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;
proxy_cache_key "$scheme$request_method$host$request_uri";
```

## ✅ 12. Production Checklist

- [ ] `.env` dosyası güvenli şifreler içeriyor
- [ ] Database backup cron job kuruldu
- [ ] SSL sertifikaları yüklendi
- [ ] Firewall aktif ve doğru portlar açık
- [ ] Admin şifresi değiştirildi
- [ ] Amazon PA API credentials girildi
- [ ] Telegram bot token ve channel ID girildi
- [ ] Nginx reverse proxy çalışıyor
- [ ] Docker container'lar otomatik başlıyor (restart: always)
- [ ] Monitoring kuruldu
- [ ] Log rotation yapılandırıldı

## 🚀 13. İlk Kullanım

1. `https://admin.firsatradari.com` adresine gidin
2. `admin` / `admin123` ile giriş yapın
3. **Ayarlar** sayfasından Amazon ve Telegram bilgilerini girin
4. Şifrenizi değiştirin
5. İlk kategoriyi ekleyin
6. Worker'ın çalışmasını bekleyin

## 📞 Destek

Sorun yaşarsanız:
1. Log dosyalarını kontrol edin
2. GitHub issues açın
3. support@firsatradari.com adresine yazın
