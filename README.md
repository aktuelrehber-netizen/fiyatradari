# Fiyat Radarı - Amazon Price Tracker

Amazon ürünlerinin fiyatlarını takip eden, indirimleri tespit eden ve Telegram + web sitesi üzerinden paylaşan kapsamlı bir platform.

## 🏗️ Proje Yapısı

```
fiyatradari/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Configuration & security
│   │   ├── db/          # Database models & migrations
│   │   ├── services/    # Business logic
│   │   └── schemas/     # Pydantic schemas
│   ├── requirements.txt
│   └── Dockerfile
├── worker/              # Background job runner
│   ├── jobs/
│   ├── requirements.txt
│   └── Dockerfile
├── admin-panel/         # Next.js admin panel
├── public-web/          # Next.js public website
├── docker-compose.yml   # Local development
└── docs/                # Documentation
```

## 🚀 Teknolojiler

- **Backend:** Python 3.11 + FastAPI
- **Database:** PostgreSQL 15
- **Admin Panel:** Next.js 14 + TypeScript + TailwindCSS + shadcn/ui
- **Public Web:** Next.js 14 + TypeScript + TailwindCSS
- **Worker:** Python (custom job runner)
- **API Integration:** Amazon Product Advertising API 5.0
- **Notifications:** Telegram Bot API

## 📋 Özellikler

### Backend API
- Ürün yönetimi (CRUD)
- Kategori yönetimi ve Amazon node eşleştirme
- Fiyat geçmişi ve fırsat tespiti
- Kullanıcı yönetimi ve authentication
- Amazon PA API proxy
- Telegram entegrasyonu
- Health check & monitoring

### Worker System
- Kategori bazlı ürün fetching (Amazon PA API)
- Fiyat güncelleme ve takip
- Fırsat tespiti (indirim algılama)
- Telegram bildirimleri
- Otomatik görev planlama

### Admin Panel
- Dashboard (istatistikler, grafikler)
- Kategori yönetimi (Amazon browse nodes)
- Ürün yönetimi ve filtreleme
- Fiyat geçmişi görselleştirme
- Fırsat/indirim yönetimi
- Telegram ayarları ve test
- Amazon API ayarları
- Kullanıcı yönetimi
- Sistem sağlığı & servis durumu
- Genel ayarlar

### Public Website
- SEO optimize edilmiş fırsat listesi
- Kategori bazlı filtreleme
- Ürün detay sayfaları
- Fiyat grafikleri
- Amazon affiliate linkleri
- Responsive tasarım

## 🛠️ Local Development

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (admin panel ve public web için)
- Python 3.11+ (backend geliştirme için)

### İlk Kurulum

```bash
# Repository clone
git clone <repo-url>
cd fiyatradari

# Environment variables
cp .env.example .env
# .env dosyasını düzenleyin

# Docker ile tüm servisleri başlat
docker-compose up -d

# Database migration
docker-compose exec backend alembic upgrade head

# Admin kullanıcı oluştur
docker-compose exec backend python -m app.db.init_db
```

### Servisler

- **Backend API:** http://localhost:8000
- **Admin Panel:** http://localhost:3001
- **Public Web:** http://localhost:3000
- **PostgreSQL:** localhost:5432
- **API Docs:** http://localhost:8000/docs

## 🌐 Production Deployment

### Domain Yapısı
- `api.firsatradari.com` - Backend API
- `admin.firsatradari.com` - Admin Panel
- `firsatradari.com` - Public Website

### Server Requirements (Ubuntu 22.04 LTS)
- 2+ CPU cores
- 4GB+ RAM
- 20GB+ disk space
- Docker & Docker Compose

Deployment detayları için `docs/deployment.md` dosyasına bakın.

## 🔑 Environment Variables

Backend için gerekli environment variables:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/fiyatradari

# API Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Amazon PA API
AMAZON_ACCESS_KEY=your-access-key
AMAZON_SECRET_KEY=your-secret-key
AMAZON_PARTNER_TAG=your-partner-tag
AMAZON_REGION=eu-west-1

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHANNEL_ID=your-channel-id

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

## 📚 API Documentation

Backend çalıştığında otomatik dokümantasyon:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Contributing

1. Feature branch oluştur (`git checkout -b feature/amazing-feature`)
2. Değişikliklerini commit et (`git commit -m 'Add some amazing feature'`)
3. Branch'i push et (`git push origin feature/amazing-feature`)
4. Pull Request aç

## 📄 License

MIT License - detaylar için `LICENSE` dosyasına bakın.

## 👥 Team

- Backend & Worker: Python/FastAPI
- Frontend: Next.js/TypeScript
- DevOps: Docker/Ubuntu

## 📞 Support

Sorularınız için: support@firsatradari.com
