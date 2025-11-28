# Fiyat Radarı

Amazon ürün fiyat takip ve fırsat platformu.

## 🏗️ Proje Yapısı

```
fiyatradari/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Configuration & security
│   │   ├── db/          # Database models
│   │   └── schemas/     # Pydantic schemas
│   └── Dockerfile
├── admin-panel/         # Next.js admin panel
├── web/                 # Next.js public website
└── docker-compose.yml
```

## 🚀 Teknolojiler

- **Backend:** Python 3.11 + FastAPI
- **Database:** PostgreSQL 15
- **Cache:** Redis 7
- **Admin Panel:** Next.js 14 + TypeScript + shadcn/ui
- **Web:** Next.js 14 + TypeScript
- **Reverse Proxy:** Nginx

## 📋 Özellikler

### Backend API
- Ürün yönetimi (CRUD)
- Kategori yönetimi
- Fiyat geçmişi ve fırsat yönetimi
- Kullanıcı yönetimi ve authentication
- Amazon PA API entegrasyonu
- Redis cache

### Admin Panel
- **Dashboard:** İstatistikler ve sistem özeti
- **Kategori Yönetimi:** Amazon browse node eşleştirme
- **Ürün Yönetimi:** Ürün CRUD işlemleri ve filtreleme
- **Fırsat Yönetimi:** İndirim fırsatlarını görüntüleme ve düzenleme
- **Kullanıcı Yönetimi:** Admin kullanıcıları yönetme
- **Ayarlar (Settings):**
  - **Amazon API Tab:** Access key, secret key, partner tag, region ayarları
  - **Telegram Tab:** Bot token, channel ID ve mesaj şablonu editörü
  - **Proxy Tab:** Proxy ayarları (host, port, username, password, rotation list)
  - Tek kaydet butonu ile tüm değişiklikleri kaydetme
  - Gizli alanları göster/gizle özelliği
  - Yeni ayar ekleme dialog'u
  - Gerçek zamanlı değişiklik takibi

### Public Website
- Fırsat listesi
- Kategori filtreleme
- Ürün detay sayfaları
- SEO optimize

## 🛠️ Local Development

### Prerequisites
- Docker & Docker Compose

### İlk Kurulum

```bash
# Docker ile tüm servisleri başlat
docker-compose up -d

# Admin kullanıcı oluştur
docker-compose exec backend python create_admin.py
```

### Servisler

- **Backend API:** http://localhost:8000
- **Admin Panel:** http://localhost:3001
- **Web:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs

## 🔑 Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@postgres:5432/fiyatradari

# API Security
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Amazon PA API
AMAZON_ACCESS_KEY=your-access-key
AMAZON_SECRET_KEY=your-secret-key
AMAZON_PARTNER_TAG=your-partner-tag
AMAZON_REGION=eu-west-1

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHANNEL_ID=your-channel-id
```

> **Not:** Proxy ayarları admin panel Settings sayfasından dinamik olarak yönetilir. Environment variable olarak tanımlanmaz.

## ⚙️ Settings Sayfası Kullanımı

Admin panel'de **Ayarlar** sayfası sistem konfigürasyonunu yönetir:

### Amazon API Ayarları
- Access Key, Secret Key, Partner Tag ve Region ayarlarını girin
- Ayarlar veritabanında saklanır ve API çağrılarında kullanılır

### Telegram Bot Ayarları
- Bot Token ve Channel ID bilgilerini girin
- **Mesaj Şablonu Editörü:**
  - Telegram bildirim şablonunu özelleştirin
  - Önizleme özelliği ile gerçek veri ile test edin
  - Desteklenen değişkenler: `{title}`, `{brand_line}`, `{discount_percentage}`, `{original_price}`, `{deal_price}`, `{discount_amount}`, `{rating_line}`, `{product_url}`

### Proxy Ayarları
- **Yeni Ayar Ekle** butonu ile proxy konfigürasyonu ekleyin
- Desteklenen ayarlar:
  - `proxy_enabled`: Proxy kullanımını aktif/pasif etme (true/false)
  - `http_proxy`: Tek proxy adresi (format: `http://user:pass@proxy.com:8080`)
  - `proxy_list`: Virgülle ayrılmış proxy listesi (rotation için)
  - `proxy_host`, `proxy_port`, `proxy_username`, `proxy_password`: Premium proxy authentication

### Özellikler
- **Tek Kaydet Butonu:** Tüm değişiklikleri tek seferde kaydedin
- **Değişiklik Takibi:** Sadece değiştirilen ayarlar kaydedilir
- **Gizli Alan Maskeleme:** Şifre/token alanlarını gizleyin/gösterin
- **Tab Yapısı:** Organize edilmiş grup bazlı ayarlar

## 📚 API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
