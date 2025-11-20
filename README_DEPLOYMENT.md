# 🚀 Fiyatradari - Production Deployment

Ubuntu 24.04 LTS sunucuda production deployment için hızlı başlangıç rehberi.

---

## 📚 DOKÜMANTASYON

| Dosya | Açıklama |
|-------|----------|
| **PRODUCTION_DEPLOYMENT.md** | Detaylı deployment rehberi (adım adım) |
| **DEPLOYMENT_CHEATSHEET.md** | Hızlı komut referansı |
| **QUICK_DEPLOY.sh** | Otomatik sunucu kurulum scripti |
| **deploy.sh** | Local → Production deployment scripti |

---

## ⚡ HIZLI BAŞLANGIÇ

### 1. Sunucuda İlk Kurulum (Tek Sefer)

```bash
# SSH ile sunucuya bağlan:
ssh root@SUNUCU_IP

# Kurulum scriptini çalıştır:
curl -o QUICK_DEPLOY.sh https://raw.githubusercontent.com/USER/fiyatradari/main/QUICK_DEPLOY.sh
chmod +x QUICK_DEPLOY.sh
sudo ./QUICK_DEPLOY.sh

# .env dosyasını düzenle:
nano /var/www/fiyatradari/.env
# Şifreleri, API keys'leri güncelle

# Servisleri restart:
cd /var/www/fiyatradari
docker compose restart
```

### 2. Local'de Deploy Script Ayarla

```bash
# deploy.sh'i düzenle:
nano deploy.sh

# SERVER_IP'yi değiştir:
SERVER_IP="123.456.789.012"

# Executable yap:
chmod +x deploy.sh
```

### 3. Her Deployment

```bash
# Local'de kod değişikliklerini yap
# Sonra:
./deploy.sh "Yeni özellik eklendi"

# Otomatik olarak:
# - Git commit & push
# - Production'da git pull
# - Docker rebuild
# - Servisleri restart
# - Health check
```

---

## 🔧 GÜNLÜK KULLANIM

### Deployment
```bash
./deploy.sh "Commit mesajı"
```

### Log Kontrol
```bash
ssh root@SUNUCU_IP
cd /var/www/fiyatradari
docker compose logs -f backend
```

### Backup
```bash
ssh root@SUNUCU_IP
sudo /usr/local/bin/backup-fiyatradari.sh
```

---

## 📋 DEPLOYMENT ADIMLARI (Manuel)

Eğer script kullanmak istemiyorsan:

### Sunucuda:
```bash
cd /var/www/fiyatradari
git pull origin main
docker compose build
docker compose up -d
docker compose exec backend alembic upgrade head
```

### Test:
```bash
curl https://api.fiyatradari.com/health
curl https://fiyatradari.com
```

---

## 🎯 ÖN GEREKSİNİMLER

### Sunucu
- Ubuntu 24.04 LTS
- En az 2GB RAM
- 20GB disk
- Root erişimi
- Public IP adresi

### Domain
- Domain satın alınmış
- DNS A kayıtları ayarlanmış:
  - `fiyatradari.com` → Sunucu IP
  - `www.fiyatradari.com` → Sunucu IP
  - `api.fiyatradari.com` → Sunucu IP
  - `admin.fiyatradari.com` → Sunucu IP

### Servisler
- GitHub repository
- Amazon API credentials
- Telegram bot
- Google Analytics (opsiyonel)
- Sentry (opsiyonel)

---

## 🔒 GÜVENLİK

### .env Dosyası
```bash
# Sunucuda MUTLAKA düzenle:
nano /var/www/fiyatradari/.env

# Değiştir:
POSTGRES_PASSWORD=<güçlü-şifre>
SECRET_KEY=<64-karakter>
AMAZON_ACCESS_KEY=<key>
AMAZON_SECRET_KEY=<secret>
TELEGRAM_BOT_TOKEN=<token>
```

### Güçlü Şifre Oluştur
```bash
# PostgreSQL:
openssl rand -base64 32

# SECRET_KEY:
openssl rand -hex 32
```

---

## 📊 MONİTORİNG

### Servis Durumu
```bash
ssh root@SUNUCU_IP
cd /var/www/fiyatradari
docker compose ps
```

### Loglar
```bash
docker compose logs -f
```

### Grafana
```
https://grafana.fiyatradari.com
User: admin
Pass: (GRAFANA_PASSWORD from .env)
```

---

## 🐛 SORUN GİDERME

### Container Başlamıyor
```bash
docker compose logs <service_name>
docker compose restart <service_name>
```

### Database Hatası
```bash
docker compose logs postgres
docker compose exec postgres psql -U fiyatradari
```

### Nginx 502
```bash
curl http://localhost:8000/health
sudo tail -f /var/log/nginx/error.log
```

Detaylı troubleshooting: **DEPLOYMENT_CHEATSHEET.md**

---

## 📞 DESTEK

### Dokümantasyon
- [Production Deployment Guide](PRODUCTION_DEPLOYMENT.md)
- [Deployment Cheatsheet](DEPLOYMENT_CHEATSHEET.md)
- [Security Report](WEB_SECURITY_REPORT.md)
- [Monitoring Setup](MONITORING_SETUP.md)

### Hızlı Linkler
- GitHub Issues: Sorun bildir
- Deployment Cheatsheet: Hızlı komutlar
- Production Deployment: Detaylı rehber

---

## ✅ DEPLOYMENT CHECKLIST

- [ ] Sunucu hazır (Ubuntu 24.04 LTS)
- [ ] Domain DNS ayarları yapıldı
- [ ] QUICK_DEPLOY.sh çalıştırıldı
- [ ] .env dosyası düzenlendi
- [ ] Şifreler değiştirildi
- [ ] SSL certificate alındı
- [ ] Docker servisleri başlatıldı
- [ ] Health check başarılı
- [ ] Backup cron job aktif
- [ ] Monitoring çalışıyor
- [ ] deploy.sh yapılandırıldı

---

## 🎉 BAŞARILI DEPLOYMENT

Deployment sonrası kontrol et:

- ✅ https://fiyatradari.com - Ana site
- ✅ https://api.fiyatradari.com/health - API health
- ✅ https://admin.fiyatradari.com - Admin panel
- ✅ https://grafana.fiyatradari.com - Monitoring

**Production'da! 🚀**

---

**İlk Kurulum:** QUICK_DEPLOY.sh  
**Her Deployment:** deploy.sh  
**Komut Referansı:** DEPLOYMENT_CHEATSHEET.md  
**Detaylı Rehber:** PRODUCTION_DEPLOYMENT.md
