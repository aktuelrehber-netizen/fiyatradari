# 🎯 1M ÜRÜN İÇİN ÖLÇEKLENDİRME PLANI

## 📊 MEVCUT DURUM ANALİZİ

### Sorunlar:
1. **Amazon PA-API Rate Limit:** 1 TPS = 1M ürün için 27.7 saat ❌
2. **Worker Kapasitesi:** 80 paralel task = YETER ✅
3. **Database:** 365M kayıt/yıl = 36.5 GB ⚠️
4. **Telegram:** 10K mesaj/gün = SPAM riski ❌

---

## ✅ ÇÖZÜM: HİBRİT SİSTEM

### Ürün Segmentasyonu:

```
┌─────────────────────────────────────────────────────┐
│ Tier 1: VIP (10K ürün)                             │
│ ├─ Source: PA-API                                   │
│ ├─ Interval: 4 saat                                 │
│ ├─ Priority: 10 (Critical)                          │
│ ├─ Telegram: ✅ Anında bildirim                     │
│ └─ API Cost: 60 request/gün × 10K = 600K/ay        │
├─────────────────────────────────────────────────────┤
│ Tier 2: High Priority (50K ürün)                   │
│ ├─ Source: PA-API                                   │
│ ├─ Interval: 12 saat                                │
│ ├─ Priority: 8 (High)                               │
│ ├─ Telegram: ✅ Batch bildirim                      │
│ └─ API Cost: 10 request/gün × 50K = 500K/ay        │
├─────────────────────────────────────────────────────┤
│ Tier 3: Medium Priority (200K ürün)                │
│ ├─ Source: Crawler (proxy pool)                    │
│ ├─ Interval: 24 saat                                │
│ ├─ Priority: 5 (Medium)                             │
│ ├─ Telegram: ❌ Sadece web'de göster               │
│ └─ API Cost: 0 (crawler)                            │
├─────────────────────────────────────────────────────┤
│ Tier 4: Low Priority (740K ürün)                   │
│ ├─ Source: Crawler (low frequency)                 │
│ ├─ Interval: 7 gün                                  │
│ ├─ Priority: 1 (Low)                                │
│ ├─ Telegram: ❌ Sadece web'de göster               │
│ └─ API Cost: 0 (crawler)                            │
└─────────────────────────────────────────────────────┘

TOPLAM: 1M ürün
PA-API Usage: 1.1M request/ay (Amazon limit içinde ✅)
```

---

## 🛠️ IMPLEMENTATION STEPS

### 1. Ürün Tier Sistemi Ekle

```sql
-- Product model'e tier field ekle
ALTER TABLE products ADD COLUMN tier INTEGER DEFAULT 4;
ALTER TABLE products ADD COLUMN source VARCHAR(20) DEFAULT 'api'; -- 'api' or 'crawler'
ALTER TABLE products ADD COLUMN telegram_enabled BOOLEAN DEFAULT false;

-- Index ekle
CREATE INDEX idx_products_tier ON products(tier, is_active);
```

### 2. Tier Assignment Logic

```python
# services/tier_manager.py
class TierManager:
    def calculate_tier(self, product: Product) -> int:
        """
        Tier 1 (10K): Review count > 1000, rating > 4.5
        Tier 2 (50K): Review count > 100, rating > 4.0
        Tier 3 (200K): Review count > 10
        Tier 4 (740K): Others
        """
        if product.review_count > 1000 and product.rating > 4.5:
            return 1
        elif product.review_count > 100 and product.rating > 4.0:
            return 2
        elif product.review_count > 10:
            return 3
        else:
            return 4
    
    def get_check_interval(self, tier: int) -> timedelta:
        intervals = {
            1: timedelta(hours=4),
            2: timedelta(hours=12),
            3: timedelta(days=1),
            4: timedelta(days=7)
        }
        return intervals.get(tier, timedelta(days=7))
```

### 3. Queue Refill Güncellemesi

```python
# celery_tasks.py - continuous_queue_refill güncelle
@app.task
def continuous_queue_refill() -> Dict:
    with get_db() as db:
        # Tier 1: Her 4 saatte
        tier1 = db.query(Product).filter(
            Product.is_active == True,
            Product.tier == 1,
            Product.last_checked_at < datetime.utcnow() - timedelta(hours=4)
        ).limit(500).all()
        
        # Tier 2: Her 12 saatte
        tier2 = db.query(Product).filter(
            Product.is_active == True,
            Product.tier == 2,
            Product.last_checked_at < datetime.utcnow() - timedelta(hours=12)
        ).limit(1000).all()
        
        # Tier 3: Günde 1
        tier3 = db.query(Product).filter(
            Product.is_active == True,
            Product.tier == 3,
            Product.source == 'crawler',
            Product.last_checked_at < datetime.utcnow() - timedelta(days=1)
        ).limit(5000).all()
        
        # Tier 4: Haftada 1
        tier4 = db.query(Product).filter(
            Product.is_active == True,
            Product.tier == 4,
            Product.source == 'crawler',
            Product.last_checked_at < datetime.utcnow() - timedelta(days=7)
        ).limit(10000).all()
        
        # Queue'ya ekle (source'a göre farklı task)
        for product in tier1 + tier2:
            check_product_price_api.apply_async(
                args=[product.id],
                priority=_calculate_celery_priority(product.check_priority)
            )
        
        for product in tier3 + tier4:
            check_product_price_crawler.apply_async(
                args=[product.id],
                priority=_calculate_celery_priority(product.check_priority)
            )
```

### 4. Crawler Task Ekleme

```python
@app.task(bind=True, max_retries=3)
def check_product_price_crawler(self, product_id: int) -> Dict:
    """
    Crawler ile fiyat kontrolü (PA-API kullanmadan)
    """
    try:
        crawler = AmazonCrawler()
        
        with get_db() as db:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return {"status": "not_found"}
            
            # Crawler ile fiyat çek
            product_data = crawler.crawl_product_page(product.asin)
            
            if not product_data or not product_data.get('price'):
                product.is_available = False
                product.last_checked_at = datetime.utcnow()
                db.commit()
                return {"status": "unavailable"}
            
            # Fiyat güncelle
            old_price = product.current_price
            new_price = Decimal(str(product_data['price']))
            
            product.current_price = new_price
            product.is_available = product_data.get('is_available', True)
            product.last_checked_at = datetime.utcnow()
            
            # PriceHistory (sadece değişimler)
            if old_price and abs(new_price - old_price) > Decimal('0.01'):
                history = PriceHistory(
                    product_id=product.id,
                    price=new_price,
                    is_available=product.is_available,
                    recorded_at=datetime.utcnow()
                )
                db.add(history)
            
            # Deal kontrolü (sadece Tier 1-2 için Telegram)
            if product.tier <= 2:
                deal_detector = DealDetector()
                is_deal, deal_info = deal_detector.analyze_product(product, db)
                
                if is_deal:
                    created, deal = deal_detector.create_or_update_deal(product, deal_info, db)
                    if created and product.telegram_enabled:
                        send_deal_notification.apply_async(args=[deal.id], countdown=5)
            
            db.commit()
            
            return {"status": "success", "source": "crawler"}
            
    except Exception as e:
        logger.error(f"Crawler error for product {product_id}: {e}")
        raise self.retry(exc=e)
```

### 5. Proxy Pool Setup

```python
# services/proxy_manager.py
class ProxyManager:
    """
    Rotating proxy pool for crawler
    """
    def __init__(self):
        self.proxies = [
            "http://proxy1.com:8080",
            "http://proxy2.com:8080",
            # ... 10-20 proxy
        ]
        self.current_index = 0
    
    def get_next_proxy(self) -> str:
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy
```

---

## 📊 BEKLENEN PERFORMANS

### API Usage:

```
Tier 1: 10K × 6 kontrol/gün = 60K request/gün
Tier 2: 50K × 2 kontrol/gün = 100K request/gün
─────────────────────────────────────────────
TOPLAM: 160K request/gün = 4.8M request/ay ⚠️

Not: Amazon limit ~2M/ay, TPS artırımı gerekebilir!
Çözüm: Tier 1'i 5K'ya düşür veya interval'i uzat
```

### Adjusted Plan:

```
Tier 1: 5K × 6 kontrol/gün = 30K request/gün
Tier 2: 30K × 2 kontrol/gün = 60K request/gün
─────────────────────────────────────────────
TOPLAM: 90K request/gün = 2.7M request/ay ✅
```

### Database Growth:

```
Tier 1-2 (35K): Daily snapshot = 35K/gün = 1M/ay
Tier 3-4 (965K): Weekly snapshot = 138K/gün = 4.1M/ay
───────────────────────────────────────────────────
TOPLAM: 5.1M kayıt/ay = 61M/yıl = 6.1 GB/yıl ✅
```

### Telegram Messages:

```
Tier 1-2 (35K) × 1% indirim = 350 mesaj/gün ✅
Makul ve kullanıcı dostu!
```

---

## 💰 MALİYET TAHMİNİ

### Infrastructure:

```
Worker Servers (10 containers):
- CPU: 8 core × 10 = 80 core
- RAM: 4 GB × 10 = 40 GB
- AWS EC2 c5.4xlarge: $600/ay

Database (PostgreSQL):
- RDS db.r5.xlarge: $300/ay
- Storage (100 GB): $10/ay

Redis (Cache + Broker):
- ElastiCache: $50/ay

Proxy Pool (20 proxies):
- Rotating residential: $100-200/ay

────────────────────────────────
TOPLAM: ~$1,100/ay
```

### Amazon PA-API:

```
Ücretsiz (affiliate programı ile)
Ama satış komisyonu: %2-8
```

---

## 🎯 SONUÇ

### ✅ Hibrit Sistem ile:
- 1M ürün tracking mümkün
- PA-API limit içinde
- Database yönetilebilir
- Telegram spam yok
- Maliyet: ~$1,100/ay

### ⚠️ Trade-offs:
- Tier 3-4 ürünler günlük değil haftalık
- Crawler bakımı gerekli
- Proxy maliyeti var

### 🚀 Alternatif (Sadece PA-API):
- 200-300K ürün ile başla
- Amazon satış arttıkça TPS artacak
- Daha sonra 1M'a scale et
