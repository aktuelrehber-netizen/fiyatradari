# 🎯 Akıllı Fırsat Tespit Sistemi

## Özet

Fiyat Radarı, **price history** tablosunu kullanarak **akıllı fırsat tespiti** yapar. Sadece Amazon'un "liste fiyatı" değil, ürünün geçmiş fiyat ortalamasına göre gerçek indirimleri tespit eder.

---

## 🔍 Nasıl Çalışır?

### 1. **Fiyat Takibi (Price History)**

Her fiyat kontrolünde:
```python
# Fiyat değişti mi kontrol et
if new_price != old_price:
    # Price history tablosuna kaydet
    PriceHistory.create(
        product_id=product.id,
        price=new_price,
        list_price=list_price,
        discount_amount=...,
        discount_percentage=...,
        recorded_at=now()
    )
```

**Price History Tablosu:**
| id | product_id | price | list_price | discount_% | recorded_at |
|----|------------|-------|------------|-----------|-------------|
| 1  | 123        | 3000₺ | 5000₺     | 40%       | 2025-11-01  |
| 2  | 123        | 3200₺ | 5000₺     | 36%       | 2025-11-05  |
| 3  | 123        | 2800₺ | 5000₺     | 44%       | 2025-11-12  |

---

### 2. **Akıllı Fırsat Tespiti (Deal Detection)**

```python
# DealDetector servisi price history'yi analiz eder
is_deal, deal_info = deal_detector.analyze_product(product, db)

if is_deal:
    # Deal oluştur/güncelle
    deal_detector.create_or_update_deal(product, deal_info, db)
```

**Analiz Kriterleri:**

#### A. **Fiyat Metrikleri**
```python
metrics = {
    'current_price': 2800₺,
    'list_price': 5000₺,
    'historical_avg': 3200₺,      # Son 30 günün ortalaması
    'historical_min': 2800₺,       # En düşük fiyat
    'historical_max': 3500₺,       # En yüksek fiyat
    'discount_vs_list': 44%,       # Liste fiyatına göre indirim
    'discount_vs_avg': 12.5%,      # Ortalama fiyata göre indirim
    'is_historical_low': True      # Tarihindeki en düşük fiyat mı?
}
```

#### B. **Fırsat Skoru (0-100)**
```python
score = 0

# 1. İndirim yüzdesi (40 puan)
if discount >= 50%:   score += 40
elif discount >= 30%: score += 30
elif discount >= 20%: score += 20
elif discount >= 15%: score += 15

# 2. Tarihi karşılaştırma (30 puan)
if is_historical_low:              score += 30
elif discount_vs_avg >= 20%:       score += 25
elif discount_vs_avg >= 10%:       score += 15

# 3. Ürün kalitesi (20 puan)
if rating >= 4.5:                  score += 15
if review_count >= 1000:           score += 5

# 4. Availability (10 puan)
if is_available:                   score += 5
if is_prime:                       score += 5
```

#### C. **Fırsat mı Değil mi?**
```python
def _is_deal(metrics):
    # 1. Minimum indirim kontrolü
    if max_discount < threshold (15%):
        return False
    
    # 2. Skor kontrolü
    if deal_score < 50:
        return False
    
    # 3. Tarihi fiyat kontrolü (önemli!)
    if has_history:
        # Ortalamadan en az %5 ucuz VEYA tarihi en düşük olmalı
        if discount_vs_avg < 5% AND not is_historical_low:
            return False  # Sahte indirim!
    
    return True
```

---

## 📊 Örnek Senaryolar

### ✅ **Gerçek Fırsat**
```
Ürün: Nespresso Kahve Makinesi
Liste Fiyatı: 5,000₺
Mevcut Fiyat: 2,800₺
Tarihi Ortalama: 3,200₺
Tarihi Min: 2,800₺

Analiz:
- discount_vs_list: 44% ✓
- discount_vs_avg: 12.5% ✓
- is_historical_low: True ✓
- deal_score: 85/100 ✓

Sonuç: 🔥🔥 MUHTEŞEM FIRSAT
```

### ❌ **Sahte İndirim (Engellendi)**
```
Ürün: Fake Product
Liste Fiyatı: 10,000₺ (şişirilmiş!)
Mevcut Fiyat: 3,000₺
Tarihi Ortalama: 3,100₺
Tarihi Min: 2,900₺

Analiz:
- discount_vs_list: 70% (yüksek ama sahte)
- discount_vs_avg: 3.2% ✗ (neredeyse aynı)
- is_historical_low: False ✗
- deal_score: 45/100 ✗

Sonuç: ❌ FIRSAT DEĞİL (normal fiyat)
```

### ⚠️ **İlk Kez Görülen Ürün**
```
Ürün: Yeni Ürün
Liste Fiyatı: 2,000₺
Mevcut Fiyat: 1,500₺
Tarihi: YOK (ilk kez)

Analiz:
- discount_vs_list: 25% ✓
- has_history: False (sadece liste fiyatına güven)
- deal_score: 55/100 ✓

Sonuç: ✨ İYİ FIRSAT (dikkatli)
```

---

## 🎨 Fırsat Kategorileri

```python
if score >= 80:   "💎 MUHTEŞEM FIRSAT"
elif score >= 70: "🔥 HAR İKA FIRSAT"
elif score >= 60: "✨ İYİ FIRSAT"
elif score >= 50: "👍 FIRSAT"
else:             "❌ FIRSAT DEĞİL"
```

---

## 📈 Sistem Akışı

```
1. Price Checker
   ↓
   Her 6 saatte bir ürünleri kontrol et
   ↓
2. Fiyat değişti mi?
   ├─ EVET → Price History'ye kaydet
   └─ HAYIR → Devam
   ↓
3. DealDetector.analyze_product()
   ↓
   - Price history'yi oku (son 30 gün)
   - Metrics hesapla
   - Deal score hesapla
   - is_deal kontrolü
   ↓
4. Fırsat mı?
   ├─ EVET → Deal oluştur/güncelle
   └─ HAYIR → Devam
   ↓
5. Telegram Sender
   ↓
   Published ve sent=false olan deals'leri gönder
```

---

## 🔧 Konfigürasyon

```env
# Minimum indirim yüzdesi
DEAL_THRESHOLD_PERCENTAGE=15

# Fiyat kontrol aralığı (saat)
PRICE_CHECK_INTERVAL_HOURS=6

# Price history bakış süresi (gün)
HISTORY_LOOKBACK_DAYS=30

# Minimum price history sayısı
MIN_HISTORY_RECORDS=3
```

---

## 💡 Avantajlar

1. **Sahte indirimleri engeller**
   - Liste fiyatı şişirilmiş ürünleri tespit eder
   - Gerçek fiyat düşüşlerini bulur

2. **Tarihi en düşük fiyatları yakalar**
   - "Black Friday" gibi gerçek kampanyalar
   - Nadir fırsatları kaçırmaz

3. **Ürün kalitesini dikkate alır**
   - Düşük puanlı ürünleri filtreleme
   - Popüler ürünlere öncelik

4. **Otomatik deal expiration**
   - Fiyat normale döndüğünde deal'i kapatır
   - Güncel olmayan fırsatları göstermez

---

## 📝 Veritabanı İlişkisi

```sql
-- Price History (tüm fiyat değişiklikleri)
CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(id),
    price DECIMAL(10,2),
    list_price DECIMAL(10,2),
    discount_percentage FLOAT,
    recorded_at TIMESTAMP
);

-- Deals (tespit edilen fırsatlar)
CREATE TABLE deals (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(id),
    original_price DECIMAL(10,2),  -- list_price veya historical_avg
    deal_price DECIMAL(10,2),      -- current_price
    discount_percentage FLOAT,
    is_active BOOLEAN,
    is_published BOOLEAN,
    telegram_sent BOOLEAN
);
```

---

## 🚀 Kullanım

```bash
# Worker'ı çalıştır
python main_v2.py

# Loglar:
# [14:00:00] Price changed: B08XYZ123 3200₺ -> 2800₺ (44% off)
# [14:00:01] Deal analysis: score=85, historical_low=True
# [14:00:02] ✓ Created deal: %44 İndirim • 🔥 En Düşük Fiyat
```

---

## 🎯 Sonuç

**Bu sistem sayesinde:**
- ✅ Sadece **gerçek fırsatlar** tespit edilir
- ✅ Sahte indirimler engellenir
- ✅ Kullanıcılara **kaliteli** öneriler sunulur
- ✅ Sistem **ölçeklenebilir** (100K+ ürün)
