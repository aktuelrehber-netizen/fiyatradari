# 🚀 Fiyat Radarı - Hızlı Başlangıç

## Local Development (5 Dakikada Başlat!)

```bash
# 1. Projeyi klonla
git clone <repo-url> fiyatradari
cd fiyatradari

# 2. Environment dosyasını oluştur
cp .env.example .env

# 3. Docker ile başlat
docker-compose up -d

# 4. Database kurulumu
docker-compose exec backend python -m app.db.init_db

# 5. Hazır!
```

**Erişim Adresleri:**
- Admin Panel: http://localhost:3001 (admin / admin123)
- API Docs: http://localhost:8000/docs
- Public Web: http://localhost:3000

## Production Deployment (Ubuntu 22.04)

```bash
# 1. Sunucuya bağlan
ssh user@your-server

# 2. Docker kurulumu
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# 3. Projeyi kur
cd /opt && sudo mkdir fiyatradari && sudo chown $USER:$USER fiyatradari
cd fiyatradari
git clone <repo-url> .

# 4. Environment ayarla
cp .env.example .env
nano .env  # Gerçek bilgileri gir

# 5. Servisleri başlat
docker-compose -f docker-compose.prod.yml up -d
docker-compose exec backend python -m app.db.init_db

# 6. Nginx ve SSL
sudo apt install nginx certbot python3-certbot-nginx -y
# Nginx config'leri için docs/deployment.md'ye bakın
```

Detaylı bilgi için:
- Local: `docs/local-development.md`
- Production: `docs/deployment.md`
