# 🔧 ALEMBIC MIGRATION FIX

## SORUN
```
FAILED: No config file 'alembic.ini' found, or file has no '[alembic]' section
```

`docker compose run --rm backend alembic upgrade head` komutu çalışmıyor çünkü working directory yanlış.

---

## ✅ ÇÖZÜM 1: Backend container'ı başlatıp içinde çalıştır

```bash
cd /var/www/fiyatradari

# Backend'i başlat
docker compose up -d backend postgres redis

# 5 saniye bekle
sleep 5

# Backend container'ında migration çalıştır
docker compose exec backend alembic upgrade head
```

---

## ✅ ÇÖZÜM 2: Working directory belirt

```bash
cd /var/www/fiyatradari

# Working directory'yi belirterek çalıştır
docker compose run --rm -w /app backend alembic upgrade head
```

---

## ✅ ÇÖZÜM 3: Manuel migration kontrol

Eğer migration zaten uygulandıysa, atlayabilirsin:

```bash
cd /var/www/fiyatradari

# Backend'i başlat
docker compose up -d backend postgres redis

# Migration durumunu kontrol et
docker compose exec backend alembic current

# Eğer migration gerekiyorsa
docker compose exec backend alembic upgrade head
```

---

## DEVAM ET

Migration'dan sonra diğer servisleri başlat:

```bash
cd /var/www/fiyatradari

# Tüm servisleri başlat
docker compose up -d

# Durumu kontrol et
docker compose ps

# Logları kontrol et
docker compose logs --tail=30 backend
docker compose logs --tail=30 celery-worker
```

---

## HIZLI FIX (TEK KOMUT)

```bash
cd /var/www/fiyatradari && \
docker compose up -d postgres redis backend && \
sleep 5 && \
docker compose exec backend alembic upgrade head && \
docker compose up -d && \
sleep 10 && \
docker compose ps
```
