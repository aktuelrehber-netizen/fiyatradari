# Fiyat Radarı - Local Development Rehberi

Bu rehber, projeyi local makinenizde geliştirmek için gerekli adımları içerir.

## 📋 Gereksinimler

- Docker Desktop
- Node.js 18+
- Python 3.11+
- Git

## 🚀 Hızlı Başlangıç

### 1. Projeyi Clone Etme

```bash
cd ~/Sites
git clone <repo-url> fiyatradari
cd fiyatradari
```

### 2. Environment Dosyasını Oluşturma

```bash
cp .env.example .env
```

`.env` dosyasını düzenleyin (development için varsayılan değerler çalışır):

```bash
# Database - local için varsayılan değerler
DATABASE_URL=postgresql://fiyatradari:fiyatradari123@postgres:5432/fiyatradari
POSTGRES_USER=fiyatradari
POSTGRES_PASSWORD=fiyatradari123
POSTGRES_DB=fiyatradari

# API Security - development için basit değerler
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Amazon PA API - henüz yoksa boş bırakabilirsiniz
AMAZON_ACCESS_KEY=
AMAZON_SECRET_KEY=
AMAZON_PARTNER_TAG=
AMAZON_REGION=eu-west-1
AMAZON_MARKETPLACE=www.amazon.com.tr

# Telegram Bot - henüz yoksa boş bırakabilirsiniz
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHANNEL_ID=

# CORS - local development URL'leri
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001

# Environment
ENVIRONMENT=development
```

### 3. Docker ile Tüm Servisleri Başlatma

```bash
# Tüm servisleri başlat
docker-compose up -d

# Logları izle
docker-compose logs -f
```

Bu komut şunları başlatır:
- PostgreSQL (port 5432)
- Backend API (port 8000)
- Worker (arka planda)
- Admin Panel (port 3001)
- Public Web (port 3000)

### 4. Database İlk Kurulum

```bash
# Container içinde database initialization çalıştır
docker-compose exec backend python -m app.db.init_db
```

Bu komut:
- Database tablolarını oluşturur
- Varsayılan admin kullanıcısı oluşturur (admin / admin123)
- Örnek kategori oluşturur
- Sistem ayarlarını oluşturur

### 5. Servislere Erişim

- **Backend API:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/docs
- **Admin Panel:** http://localhost:3001
- **Public Website:** http://localhost:3000
- **PostgreSQL:** localhost:5432

## 🛠️ Development Workflows

### Backend Geliştirme (Python/FastAPI)

#### Container Dışında Geliştirme
```bash
cd backend

# Virtual environment oluştur
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencies yükle
pip install -r requirements.txt

# Local'de çalıştır (hot-reload ile)
DATABASE_URL=postgresql://fiyatradari:fiyatradari123@localhost:5432/fiyatradari \
uvicorn app.main:app --reload --port 8000
```

#### Container İçinde Geliştirme
```bash
# Backend container'ı restart et
docker-compose restart backend

# Logları izle
docker-compose logs -f backend

# Container içine gir
docker-compose exec backend bash
```

#### Database Migration (Alembic)
```bash
# Container içinde
docker-compose exec backend bash

# Yeni migration oluştur
alembic revision --autogenerate -m "Add new field"

# Migration'ı uygula
alembic upgrade head

# Migration'ı geri al
alembic downgrade -1
```

### Worker Geliştirme

```bash
cd worker

# Dependencies yükle
pip install -r requirements.txt

# Local'de test et
DATABASE_URL=postgresql://fiyatradari:fiyatradari123@localhost:5432/fiyatradari \
python main.py
```

### Admin Panel Geliştirme (Next.js)

#### Container Dışında Geliştirme
```bash
cd admin-panel

# Dependencies yükle
npm install

# .env.local oluştur
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Development server başlat
npm run dev

# Browser'da aç: http://localhost:3001
```

#### Build ve Production Test
```bash
npm run build
npm start
```

### Database Yönetimi

#### psql ile Bağlanma
```bash
docker-compose exec postgres psql -U fiyatradari -d fiyatradari
```

#### Useful SQL Commands
```sql
-- Tüm tabloları listele
\dt

-- Kategori sayısı
SELECT COUNT(*) FROM categories;

-- Ürün sayısı
SELECT COUNT(*) FROM products;

-- Aktif fırsatlar
SELECT * FROM deals WHERE is_active = true;

-- Son eklenen ürünler
SELECT title, current_price, created_at FROM products ORDER BY created_at DESC LIMIT 10;

-- Price history
SELECT p.title, ph.price, ph.recorded_at 
FROM price_history ph 
JOIN products p ON ph.product_id = p.id 
ORDER BY ph.recorded_at DESC LIMIT 20;
```

#### Database Backup & Restore
```bash
# Backup
docker-compose exec postgres pg_dump -U fiyatradari fiyatradari > backup.sql

# Restore
docker-compose exec -T postgres psql -U fiyatradari -d fiyatradari < backup.sql

# Database sıfırlama
docker-compose down -v
docker-compose up -d postgres
docker-compose exec backend python -m app.db.init_db
```

## 🧪 Testing

### Backend Tests
```bash
cd backend

# Test dependencies yükle
pip install pytest pytest-asyncio httpx

# Testleri çalıştır
pytest tests/

# Coverage ile
pytest --cov=app tests/
```

### API Testleri (Swagger UI)
1. http://localhost:8000/docs adresine git
2. "Authorize" butonuna tıkla
3. Login endpoint'i ile token al
4. Token'ı authorize et
5. API endpoint'lerini test et

## 🐛 Debugging

### Backend Debug Mode
```python
# app/main.py dosyasına ekle
import debugpy
debugpy.listen(("0.0.0.0", 5678))
print("⏳ Waiting for debugger attach...")
debugpy.wait_for_client()
```

### VS Code Debug Config
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--port",
        "8000"
      ],
      "jinja": true,
      "justMyCode": true
    },
    {
      "name": "Next.js: debug admin panel",
      "type": "node",
      "request": "launch",
      "cwd": "${workspaceFolder}/admin-panel",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "dev"],
      "console": "integratedTerminal",
      "internalConsoleOptions": "neverOpen"
    }
  ]
}
```

## 🔧 Troubleshooting

### Port Çakışması
```bash
# Port 8000 meşgulse
lsof -ti:8000 | xargs kill -9

# Port 3001 meşgulse
lsof -ti:3001 | xargs kill -9

# Port 5432 meşgulse (PostgreSQL)
lsof -ti:5432 | xargs kill -9
```

### Docker Issues
```bash
# Tüm container'ları durdur ve temizle
docker-compose down -v

# Docker cache temizliği
docker system prune -a

# Yeniden başlat
docker-compose up -d --build
```

### Database Connection Refused
```bash
# PostgreSQL container'ın çalıştığından emin ol
docker-compose ps

# PostgreSQL loglarına bak
docker-compose logs postgres

# Manuel olarak PostgreSQL başlat
docker-compose up -d postgres
sleep 5
docker-compose up -d backend
```

### Admin Panel Build Hatası
```bash
cd admin-panel

# node_modules ve .next temizle
rm -rf node_modules .next

# Yeniden yükle
npm install
npm run dev
```

## 📝 Code Style & Linting

### Backend (Python)
```bash
cd backend

# Black formatter
pip install black
black app/

# Flake8 linter
pip install flake8
flake8 app/

# isort import organizer
pip install isort
isort app/
```

### Frontend (TypeScript)
```bash
cd admin-panel

# ESLint
npm run lint

# Prettier (eğer eklenirse)
npm run format
```

## 🎯 Development Tips

1. **Hot Reload:** Docker compose'da backend ve frontend otomatik reload yapacak şekilde ayarlıdır
2. **Database GUI:** DBeaver veya pgAdmin kullanabilirsiniz (localhost:5432)
3. **API Testing:** Postman veya Insomnia kullanabilirsiniz
4. **Logs:** `docker-compose logs -f [service-name]` ile gerçek zamanlı log izleyin
5. **Container Shell:** `docker-compose exec [service-name] bash` ile container içine girin

## 📚 Ek Kaynaklar

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Amazon PA API Documentation](https://webservices.amazon.com/paapi5/documentation/)

## 🤝 Katkıda Bulunma

1. Feature branch oluşturun: `git checkout -b feature/amazing-feature`
2. Değişikliklerinizi commit edin: `git commit -m 'Add amazing feature'`
3. Branch'i push edin: `git push origin feature/amazing-feature`
4. Pull Request açın

## 📞 Yardım

Sorun yaşıyorsanız:
1. Önce `docker-compose logs -f` ile logları kontrol edin
2. Bu dokümandaki troubleshooting bölümüne bakın
3. GitHub issues açın
