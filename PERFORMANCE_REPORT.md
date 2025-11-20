# 🚀 Performans Analizi ve İyileştirme Önerileri

## 📊 Mevcut Durum

### Container Resource Kullanımı
- **Web (Next.js)**: 530MB RAM - Development mode
- **Admin Panel**: 496MB RAM - Development mode  
- **Backend (FastAPI)**: 342MB RAM, 1.63% CPU
- **PostgreSQL**: 175MB RAM
- **Redis**: 9MB RAM, 1.68% CPU

### Database Connection Pool
- **Aktif Bağlantı**: 95/100 ⚠️ **KRİTİK**
- **Backend Pool**: 10 + 20 overflow = 30 max
- **Worker Pool**: Default (5 + 10 = 15) * 10 worker = 150 potential ⚠️
- **Problem**: Worker'lar connection limit'i aşıyor!

### Tespit Edilen Performans Sorunları

## ⚠️ KRİTİK SORUNLAR

### 1. Database Connection Pool Krizi
**Durum**: PostgreSQL 95/100 connection kullanılıyor
**Sebep**: 10 celery worker + 4 uvicorn worker = çok fazla connection
**Etki**: Connection timeout, slow queries

### 2. Worker Database Pool Yapılandırması Yok
**Durum**: Worker'lar default pool settings kullanıyor
**Sebep**: `pool_size` ve `max_overflow` belirtilmemiş
**Etki**: Her worker unlimited connection açabiliyor

### 3. N+1 Query Problemi - Backend API
**Konum**: `backend/app/api/workers.py`, `settings.py`, `amazon.py`
**Problem**: Birden fazla sequential `.count()` ve `.filter()` query
**Örnek**:
```python
# ❌ Yavaş
total_products = db.query(Product).filter(...).count()
total_deals = db.query(Deal).filter(...).count()
published_deals = db.query(Deal).filter(...).count()

# ✅ Hızlı
stats = db.query(
    func.count(Product.id).label('total_products'),
    func.count(Deal.id).label('total_deals'),
    func.count(case((Deal.is_published == True, 1))).label('published')
).first()
```

### 4. Missing Eager Loading
**Konum**: Çoğu list endpoint
**Problem**: Sadece `deals.py` joinedload kullanıyor
**Etki**: Her item için ayrı query (N+1)

## 🔧 ORTA ÖNCELİKLİ SORUNLAR

### 5. Development Mode in Production
- Next.js `npm run dev` çalışıyor (530MB + 496MB RAM)
- Volume mount aktif (hot reload)
- Uvicorn development mode

### 6. Admin Panel Polling
**Konum**: `workers/page.tsx`
**Durum**: Her 10 saniyede fetch
**Öneri**: WebSocket kullan veya interval'i 30s'ye çıkar

### 7. No Response Caching
- Backend API'de cache yok
- Static data tekrar tekrar fetch ediliyor

## ✅ İYİLEŞTİRME ÖNERİLERİ

### Hemen Yapılması Gerekenler

#### 1. PostgreSQL Max Connections Artır
```yaml
# docker-compose.yml
postgres:
  command: postgres -c max_connections=200
```

#### 2. Worker Pool Settings Ekle
```python
# worker/database.py
engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=2,           # Her worker için 2 connection
    max_overflow=3,        # Max 5 connection per worker
    pool_recycle=3600      # 1 saat sonra recycle
)
```

#### 3. Backend Pool Optimize Et  
```python
# backend/app/db/database.py
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,          # 4 worker * 5 connection
    max_overflow=10,
    pool_recycle=3600,
    pool_timeout=30
)
```

#### 4. N+1 Query'leri Düzelt
- `workers.py`: Tek query ile statistics al
- `settings.py`: Bulk operations kullan
- Tüm list endpoint'lerine `joinedload` ekle

### Orta Vadede Yapılacaklar

#### 5. Response Caching
```python
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

@router.get("/categories")
@cache(expire=300)  # 5 dakika cache
async def list_categories():
    ...
```

#### 6. Production Build
```dockerfile
# Next.js production build
CMD ["npm", "run", "build", "&&", "npm", "start"]
```

#### 7. Database Query Optimization
- Composite index'ler ekle
- Explain analyze ile slow query'leri bul
- Connection pooler (PgBouncer) kullan

#### 8. Redis Caching Strategy
- Frequently accessed data cache'le
- API response cache
- Session management için Redis kullan

### Uzun Vadede Yapılacaklar

#### 9. Load Balancing
- Multiple backend instance
- Nginx reverse proxy

#### 10. Database Optimization
- Read replicas
- Partitioning
- Materialized views

#### 11. Monitoring & Alerting
- Prometheus + Grafana
- APM (Application Performance Monitoring)
- Slow query logging

## 📈 Beklenen İyileştirmeler

| Metrik | Öncesi | Sonrası | İyileştirme |
|--------|--------|---------|-------------|
| DB Connections | 95/100 | 60/200 | %370 ⬆️ |
| API Response Time | ~200ms | ~50ms | %75 ⬇️ |
| Memory (Frontend) | 1GB | 200MB | %80 ⬇️ |
| Query Count (List) | N+1 | 1-2 | %95 ⬇️ |

## 🎯 Öncelik Sıralaması

1. **P0 (Hemen)**: Database connection pool ayarları
2. **P1 (Bugün)**: N+1 query düzeltmeleri
3. **P2 (Bu Hafta)**: Response caching, production builds
4. **P3 (Bu Ay)**: Monitoring, load balancing
