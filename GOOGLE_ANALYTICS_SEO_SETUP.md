# 📊 Google Analytics & SEO Setup Guide

## 🎯 YAPILAN İYİLEŞTİRMELER

### ✅ 1. GOOGLE ANALYTICS ENTEGRASYONU

#### Eklenen Dosyalar:
- ✅ `web/lib/analytics.ts` - Analytics fonksiyonları
- ✅ `web/components/Analytics.tsx` - Auto-tracking component
- ✅ `web/app/layout.tsx` - Analytics component eklendi

#### Özellikler:
```typescript
// Otomatik tracking:
✓ Page views
✓ Time on page
✓ Performance metrics (page load, TTFB)

// Manuel tracking:
✓ Product views
✓ Deal clicks
✓ Amazon link clicks (conversion!)
✓ Search queries
✓ Category views
✓ Filter changes
✓ Social sharing
✓ Error tracking
```

---

### ✅ 2. SEO OPTİMİZASYONU

#### Enhanced Metadata
```typescript
✓ OpenGraph tags (Facebook, LinkedIn)
✓ Twitter Cards
✓ Robots directives
✓ Canonical URLs
✓ Author & Publisher info
✓ Dynamic page titles
```

#### Structured Data (JSON-LD)
```typescript
✓ Organization schema
✓ WebSite schema
✓ Product schema
✓ Breadcrumb schema
✓ Search action
```

#### SEO Files
```
✓ robots.txt
✓ sitemap.xml (dynamic)
✓ .env.local.example
```

---

## 🚀 KURULUM ADIMLARI

### Adım 1: Google Analytics Hesabı Oluştur

1. **Google Analytics'e Git**
   ```
   https://analytics.google.com
   ```

2. **Yeni Property Oluştur**
   - Property name: "Fiyat Radarı"
   - Reporting time zone: "Turkey"
   - Currency: "Turkish Lira (TRY)"

3. **Data Stream Oluştur**
   - Platform: Web
   - Website URL: https://fiyatradari.com
   - Stream name: "Fiyat Radarı Web"

4. **Measurement ID'yi Kopyala**
   ```
   Format: G-XXXXXXXXXX
   ```

---

### Adım 2: Environment Variables Ekle

```bash
# web/.env.local dosyası oluştur
cd web
cp .env.local.example .env.local
nano .env.local
```

```bash
# İçeriği düzenle:
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX  # ← Kendi ID'ni buraya yaz
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SITE_URL=https://fiyatradari.com
```

---

### Adım 3: Production Deployment

```bash
# 1. Environment variables'ı production'a ekle
# Docker-compose veya hosting provider'da:
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
NEXT_PUBLIC_SITE_URL=https://fiyatradari.com

# 2. Build ve deploy
docker-compose build web
docker-compose up -d web
```

---

## 📊 GOOGLE ANALYTICS - TRACKING KULLANIMI

### Otomatik Tracking (Hiçbir Şey Yapma Gerekmiyor)

Analytics component layout'a eklendi, otomatik olarak şunlar track ediliyor:
- ✅ Her sayfa görüntüleme
- ✅ Sayfada kalma süresi
- ✅ Performance metrics

### Manuel Event Tracking (Örnek Kullanım)

#### 1. Product View Tracking
```typescript
// pages/urun/[asin]/page.tsx
import { trackProductView } from '@/lib/analytics';

// Component içinde:
useEffect(() => {
  trackProductView({
    id: product.asin,
    name: product.title,
    category: product.category.name,
    price: product.current_price,
    brand: product.brand
  });
}, [product]);
```

#### 2. Deal Click Tracking
```typescript
import { trackDealClick } from '@/lib/analytics';

const handleDealClick = () => {
  trackDealClick({
    id: deal.id,
    productName: deal.product.title,
    discount: deal.discount_percentage,
    price: deal.price_after_discount
  });
  
  // Then navigate to Amazon
  window.open(deal.amazon_url, '_blank');
};
```

#### 3. Amazon Link Click (CONVERSION!)
```typescript
import { trackAmazonClick } from '@/lib/analytics';

<button onClick={() => {
  trackAmazonClick(product.asin, product.title);
  window.open(amazonUrl, '_blank');
}}>
  Amazon'da Gör
</button>
```

#### 4. Search Tracking
```typescript
import { trackSearch } from '@/lib/analytics';

const handleSearch = (query: string, results: any[]) => {
  trackSearch(query, results.length);
};
```

---

## 🔍 SEO KONTROLÜ

### 1. Metadata Kontrolü

```bash
# Browser'da sayfayı aç ve view source:
curl https://fiyatradari.com | grep -A5 "og:title"

# Görmeli:
<meta property="og:title" content="Fiyat Radarı - Amazon Fırsat ve İndirim Takibi">
<meta property="og:description" content="...">
<meta property="og:image" content="/og-image.jpg">
```

### 2. Structured Data Kontrolü

```bash
# Google'ın Rich Results Test:
https://search.google.com/test/rich-results

# URL gir: https://fiyatradari.com
# Görmeli:
✓ Organization schema
✓ WebSite schema
✓ Search action
```

### 3. Sitemap Kontrolü

```bash
# Sitemap erişimi:
https://fiyatradari.com/sitemap.xml

# Google Search Console'a ekle:
1. https://search.google.com/search-console
2. Property ekle: fiyatradari.com
3. Sitemaps → Add sitemap → sitemap.xml
```

### 4. Robots.txt Kontrolü

```bash
# Kontrol:
https://fiyatradari.com/robots.txt

# İçerik:
User-agent: *
Allow: /
Sitemap: https://fiyatradari.com/sitemap.xml
```

---

## 📈 GOOGLE ANALYTICS DASHBOARD'U

### Real-Time Reports
```
Analytics → Reports → Realtime
```
Göreceksin:
- Şu anda sitede kaç kişi var
- Hangi sayfalar görüntüleniyor
- Nereden geliyorlar (traffic source)

### Events
```
Analytics → Reports → Engagement → Events
```
Göreceksin:
- `page_view` (otomatik)
- `view_item` (product views)
- `select_promotion` (deal clicks)
- `click_to_amazon` (conversions!)
- `search` (arama sorguları)

### Conversions
```
Analytics → Reports → Engagement → Conversions
```
`click_to_amazon` event'ini conversion olarak işaretle:
1. Configure → Events
2. `click_to_amazon` bulve "Mark as conversion"

---

## 🎯 ÖNEMLİ METRİKLER

### 1. Engagement Rate
```
Ne kadar kullanıcı sitede 10+ saniye kalıyor?
Hedef: >60%
```

### 2. Conversion Rate
```
Kaç kullanıcı Amazon linkine tıklıyor?
Hedef: >5%
```

### 3. Average Session Duration
```
Ortalama ne kadar kalıyorlar?
Hedef: >2 dakika
```

### 4. Bounce Rate
```
Tek sayfa görüp çıkanlar?
Hedef: <40%
```

---

## 🔥 SEO İYİLEŞTİRME TAKTİKLERİ

### 1. Content Strategy
```
✓ Her kategoriye özel landing page
✓ Ürün detay sayfaları SEO-friendly
✓ Blog yazıları (opsiyonel)
✓ FAQ sayfası
```

### 2. Technical SEO
```
✓ Core Web Vitals optimize et
✓ Mobile-first design
✓ Lazy loading images
✓ Minify CSS/JS
✓ Enable compression
```

### 3. Link Building
```
✓ Social media presence
✓ Guest posting
✓ Directory submissions
✓ Partner collaborations
```

### 4. Local SEO (Türkiye)
```
✓ hreflang="tr" tag
✓ Turkish keywords
✓ Local backlinks
✓ .com.tr domain mention
```

---

## 🛠️ DEBUGGING

### Analytics Çalışmıyor?

```bash
# 1. Browser console aç (F12)
# 2. Console'da:
typeof window.gtag

# Çıktı "function" olmalı
# Eğer "undefined" ise:
# - GA_ID doğru mu kontrol et
# - Network tab'da gtag script yükleniyor mu?
```

### Events Gözükmüyor?

```bash
# 1. GA Debug Mode aç:
# Browser console:
window.gtag('config', 'G-XXXXXXXXXX', {
  'debug_mode': true
});

# 2. Tekrar event trigger et
# 3. Console'da event loglarını gör
```

### Sitemap 404 Veriyor?

```bash
# Next.js build gerekebilir:
cd web
npm run build

# Docker'da:
docker-compose build web
docker-compose restart web
```

---

## ✅ CHECKLIST

### Google Analytics
- [ ] GA4 property oluşturuldu
- [ ] Measurement ID kopyalandı
- [ ] .env.local dosyasına eklendi
- [ ] Analytics component layout'a eklendi
- [ ] Real-time'da görünüyor
- [ ] Events kaydediliyor
- [ ] Conversions işaretlendi

### SEO
- [ ] Metadata tamamlandı (OpenGraph, Twitter)
- [ ] Structured Data eklendi
- [ ] robots.txt oluşturuldu
- [ ] Sitemap.xml çalışıyor
- [ ] Google Search Console eklendi
- [ ] Sitemap submit edildi
- [ ] Rich Results Test geçti

### Performance
- [ ] Core Web Vitals kontrolü
- [ ] PageSpeed Insights >90
- [ ] Mobile-friendly test geçti
- [ ] HTTPS aktif
- [ ] Compression enabled

---

## 📚 KAYNAKLAR

### Google Analytics
- [GA4 Documentation](https://developers.google.com/analytics/devguides/collection/ga4)
- [Event Reference](https://developers.google.com/analytics/devguides/collection/ga4/reference/events)

### SEO
- [Google Search Central](https://developers.google.com/search)
- [Schema.org](https://schema.org)
- [Rich Results Test](https://search.google.com/test/rich-results)

### Tools
- [PageSpeed Insights](https://pagespeed.web.dev)
- [Mobile-Friendly Test](https://search.google.com/test/mobile-friendly)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)

---

## 🎉 SON KONTROL

```bash
# 1. Web sitesini aç
open https://fiyatradari.com

# 2. Browser console'u aç (F12)

# 3. Şunları kontrol et:
✓ GA loaded: typeof window.gtag === 'function'
✓ Page view tracked (Network tab)
✓ No console errors

# 4. Bir deal'e tıkla

# 5. GA Real-time'da gör
✓ Event: click_to_amazon
✓ Location: Turkey
✓ Device: Desktop/Mobile

# 6. SEO kontrol
✓ View source → meta tags
✓ JSON-LD scripts
✓ Sitemap accessible
```

**Herşey hazır! 🚀**
