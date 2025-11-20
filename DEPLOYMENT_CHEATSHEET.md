# 📖 DEPLOYMENT CHEATSHEET

Hızlı referans için en sık kullanılan komutlar.

---

## 🚀 İLK KURULUM (Tek Sefer)

### Sunucuda:
```bash
# 1. Script'i indir ve çalıştır:
curl -o QUICK_DEPLOY.sh https://raw.githubusercontent.com/USER/fiyatradari/main/QUICK_DEPLOY.sh
chmod +x QUICK_DEPLOY.sh
sudo ./QUICK_DEPLOY.sh

# 2. .env dosyasını düzenle:
nano /var/www/fiyatradari/.env

# 3. Servisleri restart:
cd /var/www/fiyatradari
docker compose restart
```

### Local'de:
```bash
# deploy.sh'i ayarla:
nano deploy.sh
# SERVER_IP değiştir

chmod +x deploy.sh
```

---

## 🔄 GÜNLÜK İŞLEMLER

### Local → Production Deploy
```bash
# Tek komut:
./deploy.sh "Commit mesajı"

# Örnek:
./deploy.sh "Feature: Yeni kategori eklendi"
```

### Sunucuda Log Kontrol
```bash
# SSH bağlan:
ssh root@SUNUCU_IP

# Container logları:
cd /var/www/fiyatradari
docker compose logs -f

# Sadece backend:
docker compose logs -f backend

# Sadece worker:
docker compose logs -f worker

# Son 100 satır:
docker compose logs --tail=100
```

### Container Yönetimi
```bash
cd /var/www/fiyatradari

# Durumu görüntüle:
docker compose ps

# Restart (tümü):
docker compose restart

# Restart (tek servis):
docker compose restart backend

# Stop:
docker compose stop

# Start:
docker compose start

# Rebuild & restart:
docker compose up -d --build
```

---

## 🔧 MAINTENANCE

### Backup
```bash
# Manuel backup:
sudo /usr/local/bin/backup-fiyatradari.sh

# Backup'ları listele:
ls -lh /var/backups/fiyatradari/

# Restore:
sudo /usr/local/bin/restore-fiyatradari.sh /var/backups/fiyatradari/db_YYYYMMDD_HHMMSS.sql.gz
```

### Database İşlemleri
```bash
cd /var/www/fiyatradari

# Database shell:
docker compose exec postgres psql -U fiyatradari fiyatradari

# Migration:
docker compose exec backend alembic upgrade head

# Migration geri al:
docker compose exec backend alembic downgrade -1

# Database backup:
docker exec fiyatradari_postgres pg_dump -U fiyatradari fiyatradari > backup.sql
```

### Temizlik
```bash
# Docker temizlik:
docker system prune -a
docker volume prune

# Eski log'ları sil:
sudo find /var/log -name "*.log" -mtime +30 -delete

# Disk kullanımı:
df -h
docker system df
```

---

## 🐛 TROUBLESHOOTING

### Container Başlamıyor
```bash
# 1. Logları kontrol:
docker compose logs container_name

# 2. Manuel başlat:
docker compose up container_name

# 3. Rebuild:
docker compose up -d --build container_name

# 4. .env kontrol:
cat .env
```

### Database Bağlanamıyor
```bash
# 1. PostgreSQL container çalışıyor mu?
docker compose ps postgres

# 2. Loglar:
docker compose logs postgres

# 3. Bağlantı test:
docker compose exec postgres psql -U fiyatradari -d fiyatradari -c "SELECT 1;"

# 4. .env DATABASE_URL kontrol:
grep DATABASE_URL .env
```

### Nginx 502 Bad Gateway
```bash
# 1. Backend çalışıyor mu?
curl http://localhost:8000/health

# 2. Nginx logları:
sudo tail -f /var/log/nginx/error.log

# 3. Nginx test:
sudo nginx -t

# 4. Nginx restart:
sudo systemctl restart nginx
```

### SSL Hatası
```bash
# Certificate kontrol:
sudo certbot certificates

# Yenileme:
sudo certbot renew

# Manuel yenileme:
sudo certbot --nginx -d fiyatradari.com -d www.fiyatradari.com
```

### Disk Doldu
```bash
# Disk kullanımı:
df -h

# Büyük dosyalar bul:
du -sh /var/* | sort -hr | head -10

# Docker temizlik:
docker system prune -a --volumes

# Log rotation:
sudo journalctl --vacuum-time=7d
```

---

## 📊 MONİTORİNG

### Servis Durumu
```bash
# Docker:
docker compose ps

# Nginx:
sudo systemctl status nginx

# SSL:
curl -I https://fiyatradari.com | grep "HTTP/2"

# Health check:
curl https://api.fiyatradari.com/health
```

### Resource Kullanımı
```bash
# Docker stats:
docker stats

# Disk:
df -h

# Memory:
free -h

# CPU:
top
```

### Loglar
```bash
# Application logs:
docker compose logs -f --tail=100

# Nginx logs:
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# System logs:
sudo journalctl -f
```

---

## 🔐 GÜVENLİK

### Şifre Değiştirme
```bash
# .env dosyasını düzenle:
nano /var/www/fiyatradari/.env

# Yeni şifre oluştur:
openssl rand -base64 32

# Restart:
docker compose restart
```

### SSL Yenileme
```bash
# Otomatik yenileme test:
sudo certbot renew --dry-run

# Manuel yenileme:
sudo certbot renew

# Cron job kontrol:
sudo crontab -l | grep certbot
```

### Firewall
```bash
# Durum:
sudo ufw status

# Kural ekle:
sudo ufw allow 8080/tcp

# Kural sil:
sudo ufw delete allow 8080/tcp

# Reset (dikkat!):
sudo ufw reset
```

---

## 📈 PERFORMANCE

### Cache Temizle
```bash
# Redis:
docker compose exec redis redis-cli FLUSHALL

# Nginx:
sudo rm -rf /var/cache/nginx/*
sudo systemctl reload nginx
```

### Optimize Et
```bash
# Docker image'ları temizle:
docker image prune -a

# PostgreSQL vacuum:
docker compose exec postgres psql -U fiyatradari -d fiyatradari -c "VACUUM ANALYZE;"

# Nginx cache optimize:
sudo nginx -t && sudo systemctl reload nginx
```

---

## 🔗 YARALI LİNKLER

### Production
- Main: https://fiyatradari.com
- API: https://api.fiyatradari.com/docs
- Admin: https://admin.fiyatradari.com
- Grafana: https://grafana.fiyatradari.com

### Komutlar
```bash
# SSH:
ssh root@SUNUCU_IP

# Proje klasörü:
cd /var/www/fiyatradari

# Deploy:
./deploy.sh "mesaj"

# Logs:
docker compose logs -f

# Backup:
sudo /usr/local/bin/backup-fiyatradari.sh
```

---

## 💡 İPUÇLARI

1. **Her zaman backup al** deployment'tan önce
2. **Test et** local'de önce
3. **Logları takip et** deployment sırasında
4. **Health check** sonrasında mutlaka kontrol et
5. **Rollback planı** hazır olsun

---

## 🆘 ACİL DURUM

### Site Çöktü!
```bash
# 1. SSH bağlan:
ssh root@SUNUCU_IP

# 2. Container durumu:
cd /var/www/fiyatradari
docker compose ps

# 3. Restart:
docker compose restart

# 4. Loglar:
docker compose logs -f

# 5. Health check:
curl http://localhost:8000/health
```

### Rollback (Eski Versiyona Dön)
```bash
# 1. Git'te eski commit'e dön:
git log --oneline  # commit hash'i bul
git reset --hard COMMIT_HASH

# 2. Rebuild:
docker compose up -d --build

# 3. Database restore (gerekirse):
sudo /usr/local/bin/restore-fiyatradari.sh /var/backups/fiyatradari/db_LATEST.sql.gz
```

---

**Son Güncelleme:** 2025-11-20  
**Detaylı Bilgi:** PRODUCTION_DEPLOYMENT.md
