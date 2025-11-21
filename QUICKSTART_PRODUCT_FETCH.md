# 🚀 ÜRÜN ÇEKME SİSTEMİ - HIZLI BAŞLANGIÇ

## 📋 ÖN KOŞULLAR

### 1. Amazon PA-API Credentials ✅

```bash
# .env dosyasında olmalı:
AMAZON_ACCESS_KEY=your_access_key
AMAZON_SECRET_KEY=your_secret_key
AMAZON_PARTNER_TAG=your_partner_tag
AMAZON_REGION=eu-west-1
AMAZON_MARKETPLACE=www.amazon.com.tr
```

**Nasıl alınır?**
1. https://affiliate-program.amazon.com.tr/ → Üye ol
2. Product Advertising API'ye başvur
3. Credentials'ı kopyala

---

## 🎯 ADIM ADIM SETUP

### ADIM 1: Kategori Oluştur

#### Admin Panel'den:
```
1. http://your-domain.com/admin/categories
2. "Yeni Kategori" butonuna tıkla
3. Doldur:
   - Name: Elektronik
   - Slug: elektronik
   - Amazon Browse Node IDs: ["11601346031"]
   - Max Products: 100
   - Is Active: ✅
4. Kaydet
```

#### Browse Node ID Nasıl Bulunur?

**Yöntem 1: URL'den**
```
Amazon.com.tr'de kategori sayfasına git:
https://www.amazon.com.tr/s?i=electronics&rh=n%3A11601346031

URL'deki n%3A11601346031 → Browse Node ID: 11601346031
```

**Yöntem 2: Popüler Browse Node'lar**
```json
{
  "Elektronik": "11601346031",
  "Bilgisayar": "12466439031",
  "Cep Telefonu": "12466496031",
  "Ev & Yaşam": "9688644031",
  "Moda": "11465775031",
  "Spor": "12466674031",
  "Kitap": "12466441031",
  "Oyuncak": "12466443031",
  "Otomotiv": "12466589031",
  "Kozmetik": "12466612031"
}
```

---

### ADIM 2: Test Et (Sunucuda)

```bash
# Worker container'a gir
docker compose exec celery_worker bash

# Test script'i çalıştır
python3 /app/test_product_fetch.py
```

**Beklenen Çıktı:**
```
🧪 PRODUCT FETCH SYSTEM TEST SUITE
====================================================
🔍 TEST 1: Amazon PA-API Connection
====================================================
✅ PA-API client initialized successfully
   Region: eu-west-1
   Marketplace: www.amazon.com.tr

🔍 TEST 2: Category Configuration
====================================================
✅ Found 1 active categories:

📦 Elektronik (ID: 1)
   Browse Nodes: 1
   Nodes: ['11601346031']
   Max Products: 100
   Selection Rules: ✅

🔍 TEST 3: Browse Node Search - Elektronik
====================================================
📡 Fetching from browse node: 11601346031
   Page: 1
   Items per page: 10
   Selection rules: None

✅ Found 10 items!

1. Apple iPhone 15 Pro Max 256GB Doğal Titanyum Cep Telefonu
   ASIN: B0CHX1W1XY
   Price: 52999.0 TRY
   Rating: 4.5 (1234 reviews)
   Available: True

2. Samsung Galaxy S24 Ultra 256GB Titanium Black
   ASIN: B0CXYZ123A
   Price: 48999.0 TRY
   Rating: 4.7 (890 reviews)
   Available: True

...

✅ ALL TESTS COMPLETE!
```

**Hata Alırsan:**

❌ **"PA-API not enabled"**
→ Credentials kontrol et (.env veya database)

❌ **"No active categories found"**
→ Admin panel'den kategori oluştur

❌ **"No items found"**
→ Browse Node ID yanlış olabilir

---

### ADIM 3: Manuel Tetikleme (Admin Panel)

```
1. http://your-domain.com/admin/categories
2. Kategori satırında mavi Download (⬇️) ikonunu gör
3. İkona tıkla
4. Toast mesajı: "10 task oluşturuldu. Yaklaşık 100 ürün çekilecek."
```

**Logs İzle:**
```bash
# Backend logs (task gönderimi)
docker compose logs backend -f --tail=50

# Worker logs (task işleme)
docker compose logs celery_worker -f --tail=100 | grep -E "Fetching|items_created|items_updated"
```

**Beklenen Log:**
```
celery_worker | [2024-11-22 01:00:00] INFO: Fetching from browse node 11601346031, page 1
celery_worker | [2024-11-22 01:00:02] INFO: Found 10 items
celery_worker | [2024-11-22 01:00:03] INFO: After filtering: 10 items
celery_worker | [2024-11-22 01:00:05] INFO: Task complete: items_created=10, items_updated=0
```

---

### ADIM 4: Ürünleri Kontrol Et

```
1. http://your-domain.com/admin/products
2. Yeni eklenen ürünleri göreceksin:
   - ASIN
   - Title
   - Price
   - Category
   - Rating
   - Last Checked
```

---

## 🔧 SORUN GİDERME

### Problem: "Task dispatched but no products"

**Kontrol 1: Worker çalışıyor mu?**
```bash
docker compose ps | grep celery_worker
# Status: Up olmalı
```

**Kontrol 2: Queue'da task var mı?**
```bash
docker compose exec celery_worker celery -A celery_app inspect active
# Output: task listesi
```

**Kontrol 3: Redis bağlantısı?**
```bash
docker compose exec celery_worker python3 -c "
from celery_app import app
inspector = app.control.inspect()
stats = inspector.stats()
print('Workers:', stats.keys() if stats else 'NO WORKERS!')
"
```

---

### Problem: "PA-API rate limit"

**Çözüm:** Rate limiter var (1 TPS) ama yine de:
```python
# Crawler fallback devrede
# Error: "API rate limit reached, falling back to crawler"
# → Normal, crawler otomatik devreye girer
```

---

### Problem: "Browse node returns no items"

**Nedenleri:**
1. Browse Node ID yanlış
2. Selection rules çok sıkı
3. O kategoride ürün yok

**Çözüm:**
```bash
# Selection rules'u kaldır
# Admin panel → Category → Edit → Selection Rules: {}
```

---

## 📊 PERFORMANS BEKLENTİLERİ

### Tek Kategori:
```
1 browse node × 10 sayfa = 10 task
10 task × 10 ürün = 100 ürün
Süre: ~30-60 saniye
```

### Çok Kategori:
```
10 kategori × 1 browse node × 10 sayfa = 100 task
100 task × 10 ürün = 1000 ürün
Süre: ~5-10 dakika
```

### PA-API Limitleri:
```
1 TPS (Transaction Per Second)
= 3600 request/saat
= 86,400 request/gün

10 ürün/request
= 36,000 ürün/saat
= 864,000 ürün/gün ✅
```

**Not:** Gerçekte 2-3 TPS'e kadar çıkabiliyor (satış yapınca).

---

## 🎯 SONRAKI ADIMLAR

1. ✅ **Test:** test_product_fetch.py çalıştır
2. ✅ **Manuel:** Download butonunu dene
3. ✅ **Logs:** Başarılı olduğunu doğrula
4. ✅ **Verify:** Admin panel'de ürünleri gör
5. ⏰ **Schedule:** Otomatik (her gün 04:00'da çalışıyor)

---

## 📞 YARDIM

**Log komutu:**
```bash
docker compose logs celery_worker -f --tail=100
```

**Task durumu:**
```bash
docker compose exec celery_worker celery -A celery_app inspect active
docker compose exec celery_worker celery -A celery_app inspect scheduled
docker compose exec celery_worker celery -A celery_app inspect stats
```

**Flower Dashboard:**
```
http://localhost:5555
- Active tasks
- Completed tasks
- Failed tasks
- Worker status
```

**Database kontrol:**
```bash
docker compose exec celery_worker python3 -c "
from database import get_db, Product

with get_db() as db:
    count = db.query(Product).count()
    print(f'Total products: {count}')
    
    recent = db.query(Product).order_by(Product.created_at.desc()).limit(5).all()
    print('\\nRecent products:')
    for p in recent:
        print(f'  {p.asin}: {p.title[:50]}')
"
```
