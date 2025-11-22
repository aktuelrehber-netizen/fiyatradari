# 🔴 Admin Panel 502 Bad Gateway - Debug

## 1️⃣ Container Durumunu Kontrol Et

```bash
cd /var/www/fiyatradari
docker compose ps
```

**Bakılacak:**
- `admin-panel` container'ı `Up` durumunda mı?
- Eğer `Exited` veya `Restarting` durumundaysa sorun var

---

## 2️⃣ Admin Panel Loglarını Kontrol Et

```bash
docker compose logs admin-panel --tail=100
```

**Aranacak hatalar:**
- Build hatası
- Port binding hatası
- Module not found
- Syntax error

---

## 3️⃣ Nginx Loglarını Kontrol Et

```bash
docker compose logs nginx --tail=50 | grep admin
```

**Aranacak:**
- `connect() failed (111: Connection refused)`
- `upstream timed out`
- `no live upstreams`

---

## 4️⃣ Admin Panel Container'ını Restart Et

```bash
docker compose restart admin-panel
docker compose logs -f admin-panel
```

**Beklenen:**
```
admin-panel | > next start
admin-panel | ▲ Next.js 14.x.x
admin-panel | - Local:        http://localhost:3001
admin-panel | ✓ Ready in 2.1s
```

---

## 5️⃣ Eğer Restart Düzeltmezse: Rebuild

```bash
# Stop admin panel
docker compose stop admin-panel

# Remove container
docker compose rm -f admin-panel

# Rebuild from scratch
docker compose up -d --build admin-panel

# Watch logs
docker compose logs -f admin-panel
```

---

## 6️⃣ Nginx Config Kontrol Et

```bash
docker compose exec nginx cat /etc/nginx/conf.d/default.conf | grep -A 5 "admin.firsatradari.com"
```

**Bakılacak:**
```nginx
server {
    server_name admin.firsatradari.com;
    
    location / {
        proxy_pass http://admin-panel:3001;  # ← Port doğru mu?
    }
}
```

---

## 🚨 Hızlı Fix

Genellikle container down olmuştur. Restart yeterlidir:

```bash
cd /var/www/fiyatradari
docker compose restart admin-panel
# 10 saniye bekle
curl -I http://localhost:3001
# HTTP/1.1 200 OK görmeli sin
```

---

## 📊 Tam Sistem Durumu

```bash
# Tüm container'lar
docker compose ps

# Admin panel health
docker compose exec admin-panel curl -s http://localhost:3001 | head -20

# Nginx admin proxy test
docker compose exec nginx curl -s http://admin-panel:3001 | head -20
```

---

## ⚡ Acil Durum: Full Restart

```bash
cd /var/www/fiyatradari
docker compose restart
```

Bu tüm servisleri yeniden başlatır (2-3 dakika downtime).
