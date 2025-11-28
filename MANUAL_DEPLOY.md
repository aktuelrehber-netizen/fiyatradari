# Manual Production Deployment Guide

## SSH Bilgileri
```
Host: 31.40.198.133
Port: 4383
User: root
Password: ZdtO9kKoCbrF
Path: /var/www/fiyatradari
```

## Bağlantı
```bash
ssh -p 4383 root@31.40.198.133
# Password: ZdtO9kKoCbrF
```

---

## 1️⃣ BACKUP (Sunucuda)

```bash
# Backup dizini oluştur
mkdir -p /root/backups
cd /var/www/fiyatradari

# Database backup
docker compose exec -T postgres pg_dump -U fiyatradari fiyatradari > /root/backups/db_backup_$(date +%Y%m%d_%H%M%S).sql

# .env backup
cp .env /root/backups/.env.backup
cp admin-panel/.env.local /root/backups/.env.admin.backup 2>/dev/null || true
cp web/.env.local /root/backups/.env.web.backup 2>/dev/null || true

echo "✅ Backup tamamlandı: /root/backups/"
ls -lh /root/backups/
```

---

## 2️⃣ DEPLOYMENT (Sunucuda)

```bash
cd /var/www/fiyatradari

# Git pull
echo "🔄 Pulling latest changes..."
git pull origin main

# Servisleri durdur
echo "🛑 Stopping services..."
docker compose down

# Eski image'ları temizle
echo "🧹 Cleaning old images..."
docker system prune -af --volumes

# Yeni image'ları build et
echo "🔨 Building new images..."
docker compose build --no-cache

# Database migration
echo "🗄️ Running migrations..."
docker compose run --rm backend alembic upgrade head

# Servisleri başlat
echo "🚀 Starting services..."
docker compose up -d

# Sağlık kontrolü
echo "⏳ Waiting for services..."
sleep 15

echo "✅ Checking service status..."
docker compose ps
```

---

## 3️⃣ POST-DEPLOYMENT CHECK

```bash
# Container durumları
docker compose ps

# Backend logs
docker compose logs --tail=50 backend

# Celery worker logs
docker compose logs --tail=50 celery-worker

# Celery beat logs
docker compose logs --tail=50 celery-beat

# Nginx logs
docker compose logs --tail=50 nginx

# Database migration status
docker compose exec backend alembic current

# API health check
curl -I http://localhost:8000/health
```

---

## 4️⃣ VERIFICATION

**Test edilmesi gerekenler:**

1. **Web sitesi:**
   - https://fiyatradari.com
   - Ana sayfa açılıyor mu?
   - Deal'ler görünüyor mu?

2. **Admin panel:**
   - https://admin.fiyatradari.com
   - Login çalışıyor mu?
   - Dashboard açılıyor mu?
   - Monitoring sayfası çalışıyor mu?

3. **API:**
   - https://api.fiyatradari.com/health
   - https://api.fiyatradari.com/docs
   - Auth çalışıyor mu?

4. **Celery:**
   - Worker çalışıyor mu?
   - Beat scheduler çalışıyor mu?
   - Task'lar çalışıyor mu?

```bash
# Celery task test
docker compose exec backend python -c "
from app.tasks import update_product_prices_batch
result = update_product_prices_batch.apply_async()
print(f'Task started: {result.id}')
"

# Task durumunu kontrol et
docker compose logs -f celery-worker
```

---

## 5️⃣ ROLLBACK (Gerekirse)

```bash
cd /var/www/fiyatradari

# Servisleri durdur
docker compose down

# Önceki commit'e geri dön
git log --oneline -5  # Son 5 commit'i göster
git reset --hard <previous_commit_hash>

# Eski image'ları geri yükle
docker compose pull

# Database'i restore et
cat /root/backups/db_backup_XXXXXX.sql | docker compose exec -T postgres psql -U fiyatradari fiyatradari

# Servisleri başlat
docker compose up -d
```

---

## 6️⃣ TROUBLESHOOTING

### Servis başlamıyorsa:
```bash
docker compose logs <service_name>
docker compose restart <service_name>
```

### Port kullanımda hatası:
```bash
netstat -tlnp | grep :80
netstat -tlnp | grep :443
kill -9 <PID>
```

### Disk doluysa:
```bash
df -h
docker system prune -af --volumes
```

### Database bağlantı hatası:
```bash
docker compose exec postgres psql -U fiyatradari -d fiyatradari -c "SELECT version();"
```

---

## 📞 DESTEK

Sorun yaşanırsa:
1. Logları kontrol et
2. Service'leri restart et
3. Gerekirse rollback yap
4. Backup'tan restore et
