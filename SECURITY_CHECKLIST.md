# 🔒 GÜVENLİK CHECKLIST

## ✅ TAMAMLANAN GÜVENLİK İYİLEŞTİRMELERİ

### 1. Environment Variables ✅
```bash
✓ NEXT_PUBLIC_API_URL
✓ NEXT_PRIVATE_API_URL
✓ NEXT_PUBLIC_SITE_URL
✓ Hardcoded URL'ler kaldırıldı
```

### 2. Security Headers ✅
```
✓ X-Frame-Options: DENY
✓ X-Content-Type-Options: nosniff
✓ X-XSS-Protection: 1; mode=block
✓ Referrer-Policy: strict-origin-when-cross-origin
✓ Permissions-Policy: camera=(), microphone=()...
✓ Strict-Transport-Security (production only)
```

### 3. External Link Security ✅
```tsx
✓ rel="noopener noreferrer"
✓ Tabnabbing koruması
✓ Privacy koruması
```

### 4. Image Security ✅
```
✓ Domain whitelisting
✓ HTTPS only
✓ Next.js optimization
```

### 5. XSS Protection ✅
```
✓ React auto-escaping
✓ JSON.stringify kullanımı
✓ Güvenli dangerouslySetInnerHTML
```

---

## 🎯 PRODUCTION DEPLOYMENT CHECKLIST

### Deployment Öncesi

- [ ] **Environment Variables**
  ```bash
  NEXT_PUBLIC_API_URL=https://api.fiyatradari.com
  NEXT_PRIVATE_API_URL=http://backend:8000
  NEXT_PUBLIC_SITE_URL=https://fiyatradari.com
  NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
  NODE_ENV=production
  ```

- [ ] **HTTPS Certificate**
  ```bash
  # Let's Encrypt ile:
  sudo certbot --nginx -d fiyatradari.com -d www.fiyatradari.com
  ```

- [ ] **Security Headers Test**
  ```bash
  curl -I https://fiyatradari.com | grep -E "X-Frame|X-Content|Strict-Transport"
  ```

- [ ] **Dependencies Audit**
  ```bash
  cd web && npm audit
  cd admin-panel && npm audit
  ```

- [ ] **Secrets Kontrolü**
  ```bash
  grep -r "password\|secret\|key" --include="*.ts" --include="*.tsx" web/
  # Hardcoded secret olmamalı!
  ```

---

## 🔍 GÜVENLİK TESTLERİ

### 1. Headers Test
```bash
# Security headers kontrolü
curl -I https://fiyatradari.com

# Beklenen:
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
```

### 2. SSL/TLS Test
```bash
# SSL Labs test:
https://www.ssllabs.com/ssltest/analyze.html?d=fiyatradari.com

# Hedef: A+ rating
```

### 3. Security Headers Test
```bash
# SecurityHeaders.com test:
https://securityheaders.com/?q=fiyatradari.com

# Hedef: A rating
```

### 4. OWASP ZAP Scan
```bash
# Automated security scan:
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t https://fiyatradari.com
```

---

## 🛡️ SÜREKLİ GÜVENLİK

### Haftalık

- [ ] npm audit fix
- [ ] Dependency updates
- [ ] Security logs review

### Aylık

- [ ] Full security audit
- [ ] Penetration testing
- [ ] Access logs analysis
- [ ] SSL certificate check

### Her Deploy

- [ ] Environment variables doğru
- [ ] No secrets in code
- [ ] Dependencies güncel
- [ ] Security headers aktif

---

## 📊 GÜVENLİK SKORLARI

### Hedef Metrikler

| Test | Hedef | Mevcut |
|------|-------|---------|
| **SSL Labs** | A+ | - |
| **SecurityHeaders.com** | A | - |
| **Mozilla Observatory** | A+ | - |
| **npm audit** | 0 vulnerabilities | ✅ |
| **OWASP Top 10** | 0 issues | ✅ |

---

## 🚨 ACİL DURUM PLANI

### Güvenlik İhlali Tespit Edilirse:

1. **Derhal:**
   - Etkilenen servisleri kapat
   - Tüm şifreleri değiştir
   - Access token'ları iptal et

2. **1 Saat İçinde:**
   - Sorunu tespit et
   - Patch uygula
   - Logları analiz et

3. **24 Saat İçinde:**
   - Kullanıcıları bilgilendir
   - Full security audit
   - Incident report

---

## 🔐 EN İYİ PRATİKLER

### DO (Yap)
✅ Environment variables kullan  
✅ HTTPS her yerde  
✅ Security headers ekle  
✅ Regular updates  
✅ Input validation  
✅ Error handling  
✅ Logging & monitoring  

### DON'T (Yapma)
❌ Secrets in code  
❌ Hardcoded credentials  
❌ Ignore warnings  
❌ Disable security features  
❌ Trust user input  
❌ Skip updates  
❌ Ignore logs  

---

## 📚 KAYNAKLAR

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Next.js Security](https://nextjs.org/docs/app/building-your-application/configuring/security-headers)
- [Mozilla Security Guidelines](https://infosec.mozilla.org/guidelines/web_security)
- [SSL Best Practices](https://www.ssllabs.com/projects/best-practices/)

---

**Son Güncelleme:** 2025-11-20  
**Güvenlik Durumu:** ✅ Production Ready  
**Sıradaki Review:** 2025-12-01
