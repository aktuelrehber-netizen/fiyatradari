# 🚀 HEMEN DEPLOY ET!

## ADIM 1: Terminal'de bağlan

```bash
ssh -p 4383 root@31.40.198.133
```

**Şifre:** `ZdtO9kKoCbrF`

---

## ADIM 2: Deployment script'ini çalıştır

Sunucuya bağlandıktan sonra:

```bash
# Proje dizinine git
cd /var/www/fiyatradari

# Deployment script'ini oluştur
cat > deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting Deployment..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="/root/backups"
mkdir -p $BACKUP_PATH

# Backup
echo "💾 Creating backup..."
docker compose exec -T postgres pg_dump -U fiyatradari fiyatradari > $BACKUP_PATH/db_backup_$TIMESTAMP.sql
cp .env $BACKUP_PATH/.env.backup_$TIMESTAMP
echo "✅ Backup: $BACKUP_PATH/db_backup_$TIMESTAMP.sql"

# Git pull
echo "🔄 Pulling changes..."
git pull origin main

# Stop services
echo "🛑 Stopping services..."
docker compose down

# Cleanup
echo "🧹 Cleanup..."
docker system prune -f

# Build
echo "🔨 Building..."
docker compose build --no-cache

# Migrate
echo "🗄️ Migrating..."
docker compose run --rm backend alembic upgrade head

# Start
echo "🚀 Starting..."
docker compose up -d

# Wait
echo "⏳ Waiting..."
sleep 15

# Status
echo "✅ Status:"
docker compose ps

echo ""
echo "🎉 DEPLOYMENT COMPLETED!"
echo ""
echo "Check logs:"
echo "  docker compose logs -f backend"
echo "  docker compose logs -f celery-worker"
EOF

# Script'i çalıştırılabilir yap
chmod +x deploy.sh

# ÇA LIŞTIR!
./deploy.sh
```

---

## ADIM 3: Kontrol Et

Deployment tamamlandıktan sonra:

```bash
# Service durumları
docker compose ps

# Backend logs
docker compose logs --tail=30 backend

# Celery logs
docker compose logs --tail=30 celery-worker

# API test
curl -I http://localhost:8000/health
```

---

## ADIM 4: Browser'da Test Et

1. **Web:** https://fiyatradari.com
2. **Admin:** https://admin.fiyatradari.com
3. **API Docs:** https://api.fiyatradari.com/docs

---

## SORUN ÇÖZME

### Eğer bir servis başlamazsa:

```bash
# Logları kontrol et
docker compose logs <service-name>

# Restart et
docker compose restart <service-name>

# Tamamen yeniden başlat
docker compose down
docker compose up -d
```

### Eğer database hatası varsa:

```bash
# Database bağlantısını test et
docker compose exec postgres psql -U fiyatradari -d fiyatradari -c "SELECT version();"

# Migration durumunu kontrol et
docker compose exec backend alembic current
```

### Eğer her şey bozulursa (ROLLBACK):

```bash
# Servisleri durdur
docker compose down

# Önceki commit'e dön
git log --oneline -5
git reset --hard <previous_commit_hash>

# Database'i restore et
cat /root/backups/db_backup_XXXXXX.sql | docker compose exec -T postgres psql -U fiyatradari fiyatradari

# Başlat
docker compose up -d
```

---

## ÖNEMLİ NOTLAR

✅ **Backup otomatik alınır** → `/root/backups/`
✅ **Downtime ~5-10 dakika**
✅ **Zero data loss** (PostgreSQL ve Redis volumes korunur)
✅ **Rollback hazır** (git reset + db restore)

---

## HİZLI DEPLOYMENT (TEK KOMUT)

Eğer her şeyi tek komutta yapmak istersen:

```bash
ssh -p 4383 root@31.40.198.133 'cd /var/www/fiyatradari && git pull origin main && docker compose down && docker system prune -f && docker compose build --no-cache && docker compose run --rm backend alembic upgrade head && docker compose up -d && sleep 10 && docker compose ps'
```

**Not:** Backup almaz, dikkatli kullan!
