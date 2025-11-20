# 🔒 WEB GÜVENLİK RAPORU

## 🔍 YAPILAN KONTROLLER

### ✅ GÜVENLİ OLANLAR

#### 1. **External Links** ✅
```tsx
// Tüm dış linklerde:
<a 
  href="https://amazon.com/..." 
  target="_blank"
  rel="noopener noreferrer"  // ✅ Güvenli!
>
```

**Neden Güvenli?**
- `noopener`: Yeni pencere parent window'a erişemez (tabnabbing saldırısı önlenir)
- `noreferrer`: Referrer bilgisi gönderilmez (privacy koruması)

#### 2. **Structured Data (JSON-LD)** ✅
```tsx
dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
```

**Neden Güvenli?**
- JSON.stringify() kullanılıyor (XSS korumalı)
- Sadece kendi oluşturduğumuz data
- Kullanıcı girdisi yok

#### 3. **Image Loading** ✅
```typescript
// next.config.ts
images: {
  remotePatterns: [
    { protocol: 'https', hostname: '**.ssl-images-amazon.com' },
    { protocol: 'https', hostname: 'm.media-amazon.com' }
  ]
}
```

**Neden Güvenli?**
- Sadece Amazon domain'lerinden image
- HTTPS zorunlu
- Next.js Image Optimization kullanılıyor

#### 4. **React JSX Auto-Escaping** ✅
```tsx
<h1>{category.name}</h1>  // React otomatik escape eder
<p>{product.title}</p>     // XSS korumalı
```

---

## ⚠️ GÜVENLİK AÇIKLARI VE ÖNERİLER

### 1. **API URL Hardcoded** ⚠️

#### Mevcut Durum:
```typescript
// utils/api.ts
const getApiUrl = () => {
  if (typeof window === 'undefined') {
    return 'http://backend:8000'  // ❌ Hardcoded
  }
  return 'http://localhost:8000'   // ❌ Hardcoded
}
```

#### Sorunlar:
- Environment variable kullanılmıyor
- HTTP kullanılıyor (HTTPS değil)
- Production/development ayrımı yok
- Sensitive bilgi kodda

#### Önerilen Çözüm:
```typescript
const getApiUrl = () => {
  if (typeof window === 'undefined') {
    // Server-side
    return process.env.NEXT_PRIVATE_API_URL || 'http://backend:8000'
  }
  // Client-side
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
}
```

**Etki:** ORTA  
**Öncelik:** YÜKSEK

---

### 2. **CSP (Content Security Policy) Yok** ⚠️

#### Mevcut Durum:
```
Content-Security-Policy header yok
```

#### Sorunlar:
- XSS saldırılarına karşı ekstra koruma yok
- Inline script'ler kısıtlanmamış
- External resource'lar kısıtlanmamış

#### Önerilen Çözüm:
```typescript
// next.config.ts
async headers() {
  return [
    {
      source: '/(.*)',
      headers: [
        {
          key: 'Content-Security-Policy',
          value: [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.googletagmanager.com",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https: blob:",
            "font-src 'self' data:",
            "connect-src 'self' http://localhost:8000 https://api.fiyatradari.com",
            "frame-ancestors 'none'",
          ].join('; ')
        }
      ]
    }
  ]
}
```

**Etki:** YÜKSEK  
**Öncelik:** ORTA

---

### 3. **Security Headers Eksik** ⚠️

#### Mevcut Durum:
```
X-Frame-Options: YOK
X-Content-Type-Options: YOK
Referrer-Policy: YOK
Permissions-Policy: YOK
```

#### Sorunlar:
- Clickjacking saldırısına açık
- MIME type sniffing riski
- Referrer leakage

#### Önerilen Çözüm:
```typescript
// next.config.ts
async headers() {
  return [
    {
      source: '/(.*)',
      headers: [
        { key: 'X-Frame-Options', value: 'DENY' },
        { key: 'X-Content-Type-Options', value: 'nosniff' },
        { key: 'X-XSS-Protection', value: '1; mode=block' },
        { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
      ]
    }
  ]
}
```

**Etki:** ORTA  
**Öncelik:** ORTA

---

### 4. **Rate Limiting Yok** ⚠️

#### Mevcut Durum:
```
API çağrılarında rate limiting yok (client-side)
```

#### Sorunlar:
- DDoS saldırısına karşı savunmasız
- Abuse edilebilir
- Resource tükenmesi riski

#### Önerilen Çözüm:
```typescript
// middleware.ts (oluştur)
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const ratelimit = new Map()

export function middleware(request: NextRequest) {
  const ip = request.ip ?? 'anonymous'
  const limit = 100 // requests per minute
  const windowMs = 60 * 1000 // 1 minute
  
  const now = Date.now()
  const userRequests = ratelimit.get(ip) || []
  
  // Clean old requests
  const recentRequests = userRequests.filter((time: number) => now - time < windowMs)
  
  if (recentRequests.length >= limit) {
    return new NextResponse('Too many requests', { status: 429 })
  }
  
  recentRequests.push(now)
  ratelimit.set(ip, recentRequests)
  
  return NextResponse.next()
}
```

**Etki:** ORTA  
**Öncelik:** DÜŞÜK (Backend'de var)

---

### 5. **HTTPS Enforcement Yok** ⚠️

#### Mevcut Durum:
```
HTTP ve HTTPS'e aynı şekilde yanıt veriyor
```

#### Sorunlar:
- Man-in-the-middle saldırısı riski
- Cookie çalınması
- Data interception

#### Önerilen Çözüm:
```typescript
// next.config.ts
async headers() {
  return [
    {
      source: '/(.*)',
      headers: [
        {
          key: 'Strict-Transport-Security',
          value: 'max-age=63072000; includeSubDomains; preload'
        }
      ]
    }
  ]
}
```

**Etki:** YÜKSEK  
**Öncelik:** YÜKSEK (Production)

---

## 🛡️ ÖNERİLEN DÜZELTMELER

### Öncelik 1: Kritik (Hemen)

1. **Environment Variables Kullan**
   ```bash
   NEXT_PUBLIC_API_URL=https://api.fiyatradari.com
   NEXT_PUBLIC_SITE_URL=https://fiyatradari.com
   ```

2. **HTTPS Enforcement** (Production)
   ```typescript
   Strict-Transport-Security header
   ```

### Öncelik 2: Yüksek (Bu Hafta)

3. **Security Headers Ekle**
   ```typescript
   X-Frame-Options, X-Content-Type-Options, etc.
   ```

4. **CSP Header Ekle**
   ```typescript
   Content-Security-Policy
   ```

### Öncelik 3: Orta (Bu Ay)

5. **Input Validation**
   - URL parameters sanitization
   - Query string validation

6. **Error Handling**
   - Sensitive info leakage kontrolü
   - Generic error messages

---

## 📊 GÜVENLİK SKORU

| Kategori | Durum | Skor |
|----------|-------|------|
| **XSS Koruması** | ✅ İyi | 9/10 |
| **External Links** | ✅ Mükemmel | 10/10 |
| **Image Security** | ✅ Mükemmel | 10/10 |
| **HTTPS** | ⚠️ Eksik | 5/10 |
| **Headers** | ⚠️ Eksik | 4/10 |
| **API Security** | ⚠️ İyileştirilebilir | 6/10 |
| **Rate Limiting** | ⚠️ Backend'de var | 7/10 |

**Toplam:** 7.3/10

---

## 🔧 HIZLI DÜZELTME PLANI

### 1. Environment Variables (5 dakika)
```bash
# .env.local oluştur
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SITE_URL=http://localhost:3000

# utils/api.ts güncelle
```

### 2. Security Headers (10 dakika)
```typescript
// next.config.ts'e headers ekle
```

### 3. Production HTTPS (5 dakika)
```typescript
// HSTS header ekle
```

**Toplam Süre:** ~20 dakika  
**Etki:** Güvenlik skoru 7.3 → 9.0

---

## ✅ ZATEN GÜVENLİ OLANLAR

1. ✅ React'in otomatik XSS koruması
2. ✅ External link güvenliği (noopener noreferrer)
3. ✅ Image domain whitelisting
4. ✅ JSON.stringify kullanımı
5. ✅ Next.js built-in security features
6. ✅ CORS (backend'de yapılandırılmış)
7. ✅ Input escaping (React JSX)

---

## 🚨 KRİTİK NOTLAR

### Production'da Mutlaka Yap:
1. ✅ HTTPS kullan (Let's Encrypt)
2. ✅ Environment variables kullan
3. ✅ Security headers ekle
4. ✅ Regular security updates
5. ✅ Dependency audit (`npm audit`)

### Yapmaman Gerekenler:
1. ❌ Sensitive data client-side'da saklama
2. ❌ API keys client-side'da
3. ❌ dangerouslySetInnerHTML kullanıcı girdisi ile
4. ❌ eval() veya Function() kullanma
5. ❌ Inline event handlers (onclick="...")

---

**Son Güncelleme:** 2025-11-20  
**Güvenlik Durumu:** İyi (Küçük iyileştirmeler gerekli)
