# 📊 Gerçek Fiyat Takip Sistemi

## Felsefe

**Amazon'un liste fiyatlarına güvenmiyoruz.** Liste fiyatları genelde şişirilmiş olduğundan, sadece **gerçek fiyat geçmişine** göre fırsat tespit ediyoruz.

---

## 🎯 Nasıl Çalışır?

### 1. **Sadece Current Price Takibi**

```python
# Amazon'dan SADECE current_price alıyoruz
item = amazon_api.get_item(asin)
current_price = item['offers']['price']  # Gerçek fiyat

# ❌ KULLANMIYORUZ:
# list_price = item['saving_basis']  # Sahte "liste fiyatı"
```

### 2. **Price History Tablosuna Kayıt**

Her fiyat kontrolünde:
```python
if current_price != old_price:
    # Price history'ye kaydet
    PriceHistory.create(
        product_id=product.id,
        price=current_price,          # Gerçek fiyat
        list_price=None,               # Yok!
        discount_amount=None,          # Henüz hesaplanmadı
        discount_percentage=None,
        recorded_at=now()
    )
```

**Örnek Price History:**
| id | product_id | price | recorded_at  |
|----|------------|-------|--------------|
| 1  | 123        | 3200₺ | 2025-11-01   |
| 2  | 123        | 3100₺ | 2025-11-03   |
| 3  | 123        | 3300₺ | 2025-11-07   |
| 4  | 123        | 2800₺ | 2025-11-12   | ← Şimdi

---

### 3. **Tarihi Ortalama Hesaplama**

```python
# Son 30 günün fiyat geçmişi
history = get_price_history(product, last_30_days)

# Metrikler
historical_avg = AVG(history.prices)  # 3200₺
historical_min = MIN(history.prices)  # 2800₺
historical_max = MAX(history.prices)  # 3300₺

current_price = 2800₺

# Gerçek indirim hesaplama
discount_vs_avg = (historical_avg - current_price) / historical_avg * 100
# (3200 - 2800) / 3200 * 100 = 12.5%

is_historical_low = (current_price <= historical_min)  # True
```

---

### 4. **Akıllı Fırsat Tespiti**

```python
def is_deal(product):
    # 1. Price history olmalı (min 3 kayıt)
    if history_count < 3:
        return False  # Henüz yeterli veri yok
    
    # 2. Tarihi ortalamadan ucuz olmalı
    discount_vs_avg = (historical_avg - current_price) / historical_avg * 100
    if discount_vs_avg < threshold (15%):
        return False
    
    # 3. Deal skoru yeterli olmalı
    score = calculate_score(
        discount_vs_avg,
        is_historical_low,
        product_quality,
        availability
    )
    
    if score < 50:
        return False
    
    return True  # ✅ Gerçek fırsat!
```

---

## 📊 Deal Skoru (0-100)

### **Yeni Ağırlıklar:**
```
50 puan: Tarihi fiyat düşüşü
20 puan: Tarihi en düşük bonusu
30 puan: Ürün kalitesi (rating + reviews)
20 puan: Availability & Prime
```

### **Örnek Hesaplama:**

```python
# Ürün: Nespresso Kahve Makinesi
current_price = 2800₺
historical_avg = 3200₺
historical_min = 2800₺
rating = 4.5 / 5
reviews = 1,234
is_available = True
is_prime = True

# Skor hesaplama:
score = 0

# 1. Tarihi indirim (50 puan)
discount = (3200 - 2800) / 3200 * 100 = 12.5%
→ 10 puan (10-15% arası)

# 2. Tarihi en düşük (20 puan)
is_historical_low = True
→ 20 puan (bonus!)

# 3. Ürün kalitesi (30 puan)
rating >= 4.5 → 20 puan
reviews >= 1000 → 10 puan
→ Toplam 30 puan

# 4. Availability (20 puan)
is_available → 10 puan
is_prime → 10 puan
→ Toplam 20 puan

# TOPLAM: 10 + 20 + 30 + 20 = 80 puan
```

**Sonuç:** 💎 **MUHTEŞEM FIRSAT** (score >= 80)

---

## ✅ Gerçek Fırsat vs ❌ Sahte İndirim

### ✅ **Gerçek Fırsat Örneği**

```
Ürün: Kahve Makinesi
Mevcut Fiyat: 2,800₺
Tarihi Ortalama: 3,200₺
Tarihi Min: 2,900₺

Analiz:
✓ discount_vs_avg: 12.5% (ortalamanın altında)
✓ is_historical_low: Evet (tarihindeki en düşük!)
✓ score: 80/100
✓ has_history: 15 kayıt

Sonuç: 🔥 FIRSAT! (Gerçekten ucuzlamış)
```

### ❌ **Sahte İndirim Örneği**

```
Ürün: Sahte Ürün
Amazon "Liste Fiyatı": 10,000₺ (sahte/şişirilmiş!)
Mevcut Fiyat: 3,000₺
Tarihi Ortalama: 3,100₺
Tarihi Min: 2,900₺

Analiz:
✗ discount_vs_avg: 3.2% (neredeyse aynı)
✗ is_historical_low: Hayır
✗ score: 42/100 (< 50)
✓ has_history: 12 kayıt

Sonuç: ❌ FIRSAT DEĞİL (Normal fiyatı 3000₺)
```

---

## 🔧 Sistem Gereksinimleri

### **Minimum Price History:**
- En az **3 kayıt** olmalı
- Tercihen **30 günlük** veri
- Yoksa fırsat tespit edilmez (güvenli yaklaşım)

### **İlk Günler:**
```
Gün 1: Ürün eklendi, current_price = 3000₺
       → Fırsat yok (history yok)

Gün 2: Fiyat değişmedi, 3000₺
       → Fırsat yok (sadece 2 kayıt)

Gün 3: Fiyat değişti, 2900₺
       → Fırsat yok (3 kayıt var ama çok az veri)

Gün 7: Fiyat 2800₺
       → history_avg = 2950₺
       → discount = 5.1%
       → Fırsat yok (< 15% threshold)

Gün 30: Fiyat 2500₺
        → history_avg = 2900₺
        → discount = 13.8%
        → ❌ Hala fırsat değil (< 15%)

Gün 45: Fiyat 2400₺
        → history_avg = 2850₺
        → discount = 15.8%
        → ✅ İLK FIRSAT! (score: 62/100)
```

---

## 📈 Örnek Senaryo: 30 Günlük Takip

```
# Ürün: Kahve Makinesi

Gün 1-5:   3200₺  (normal fiyat)
Gün 6-10:  3100₺  (hafif düşüş)
Gün 11-20: 3300₺  (hafif artış)
Gün 21-25: 3200₺  (normal)
Gün 26:    3000₺  (kampanya başladı?)
Gün 27:    2900₺  (devam ediyor)
Gün 28-30: 2800₺  (dip yaptı!)

# Gün 30 Analizi:
historical_avg = 3150₺  (30 günün ortalaması)
current_price = 2800₺
discount_vs_avg = 11.1%

# Sonuç: ❌ Henüz fırsat değil (< 15%)
# Fiyat birkaç gün daha bu seviyede kalırsa
# ortalama düşer ve fırsat olabilir
```

---

## 🎯 Avantajları

### **1. Sahte İndirimleri Engeller**
```
Amazon: "70% İNDİRİM!" (10,000₺ → 3,000₺)
Sistem: "Normal fiyatı 3,000₺, fırsat yok!"
```

### **2. Gerçek Fiyat Düşüşlerini Bulur**
```
Tarihi ortalama: 3,200₺
Mevcut: 2,700₺
Sistem: "15.6% düşmüş, FIRSAT!"
```

### **3. Black Friday Gibi Kampanyaları Yakalar**
```
Normal: 3,000₺ (11 ay boyunca)
Black Friday: 2,000₺ (1 hafta)
Sistem: "33% düşüş + tarihi en düşük = MUHTESEM FIRSAT!"
```

### **4. Mevsimsel Değişiklikleri İzler**
```
Yaz: 2,500₺ (düşük talep)
Kış: 3,500₺ (yüksek talep)
Sistem: Her mevsim kendi ortalamasını hesaplar
```

---

## 🚀 Kullanım

### **Worker Çalıştırma:**
```bash
python main_v2.py
```

### **Örnek Loglar:**
```
[14:00:00] Price changed: B08XYZ123 3200₺ -> 2800₺
[14:00:01] Deal analysis:
           - Historical avg: 3150₺
           - Discount vs avg: 11.1%
           - Is historical low: False
           - Deal score: 48/100
[14:00:02] ❌ Not a deal (score < 50)

[15:00:00] Price changed: B07ABC456 3000₺ -> 2500₺
[15:00:01] Deal analysis:
           - Historical avg: 2900₺
           - Discount vs avg: 13.8%
           - Is historical low: False
           - Deal score: 52/100
[15:00:02] ❌ Not a deal (discount < 15%)

[16:00:00] Price changed: B09DEF789 3500₺ -> 2800₺
[16:00:01] Deal analysis:
           - Historical avg: 3300₺
           - Discount vs avg: 15.2%
           - Is historical low: True
           - Deal score: 78/100
[16:00:02] ✅ Deal created! (💎 Harika Fırsat)
```

---

## 📝 Veritabanı Yapısı

```sql
-- Price History (sadece gerçek fiyatlar)
CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    product_id INT,
    price DECIMAL(10,2),          -- Gerçek current_price
    list_price DECIMAL(10,2),     -- NULL (kullanmıyoruz)
    discount_amount DECIMAL(10,2), -- NULL (henüz hesaplanmadı)
    discount_percentage FLOAT,     -- NULL
    recorded_at TIMESTAMP
);

-- Deals (tarihi ortalamaya göre)
CREATE TABLE deals (
    id SERIAL PRIMARY KEY,
    product_id INT,
    original_price DECIMAL(10,2),  -- historical_avg (gerçek referans)
    deal_price DECIMAL(10,2),      -- current_price
    discount_percentage FLOAT,      -- discount_vs_avg
    is_active BOOLEAN
);
```

---

## 🎓 Sonuç

**Bu sistem:**
- ✅ Amazon'un sahte liste fiyatlarını görmezden gelir
- ✅ Sadece gerçek fiyat değişikliklerini takip eder
- ✅ Tarihi verilere göre akıllı karar verir
- ✅ Kullanıcılara güvenilir fırsatlar sunar
- ✅ %100 şeffaf ve doğru çalışır

**İlk 30 gün:**
- Fırsatlar az olacak (tarih birikiyor)
- Normal, sistem öğreniyor

**30 günden sonra:**
- Sistem tam hızda çalışır
- Gerçek fırsatlar tespit edilir
- Kullanıcı güveni artar
