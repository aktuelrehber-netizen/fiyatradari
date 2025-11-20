# Amazon Browse Node ID'leri (amazon.com.tr)

## ☕ Kahve Kategorileri

### Ana Kahve Node'ları:
```
Kahve & Çay: 12407997031

Alt Kategoriler:
- Filtre Kahve: 12407998031
- Türk Kahvesi: 12407999031  
- Espresso: 12408000031
```

## 🔍 Browse Node Nasıl Bulunur?

### Yöntem 1: Amazon URL'den
```
https://www.amazon.com.tr/s?k=kahve&i=grocery&rh=n:12407997031

URL'deki "n:12407997031" kısmı Browse Node ID'dir
```

### Yöntem 2: Amazon PA API ile Arama
```python
from amazon_paapi import AmazonApi

api = AmazonApi(KEY, SECRET, TAG, COUNTRY)
result = api.search_items(keywords='kahve')

# Response'da BrowseNode bilgisi gelir
```

### Yöntem 3: ScrapeStorm / Manuel
1. Amazon.com.tr'de kategori sayfasına git
2. Tarayıcı Developer Tools > Network
3. Filtre uygula, request'leri incele
4. Browse Node ID'yi bul

## 📝 Kategori Oluşturma

**Admin Panel > Categories > Yeni Kategori:**
```json
{
  "name": "Kahve",
  "slug": "kahve",
  "amazon_browse_node_ids": [
    "12407997031",
    "12407998031",
    "12407999031"
  ]
}
```

## 🎯 Popüler Kategoriler (Türkiye)

### Gıda & İçecek
```
Ana Kategori: 12407997031 (Kahve & Çay)
Kuruyemiş: 12408028031
Çikolata: 12408015031
```

### Elektronik
```
Bilgisayar: 12466439031
Cep Telefonu: 12466459031
Kulaklık: 12466519031
```

### Ev & Yaşam
```
Mutfak: 12466719031
Ev Tekstili: 12466759031
Ev Dekorasyon: 12466799031
```

## ⚠️ Önemli Notlar:

1. **Browse Node ID'ler ülkeye özel** - Türkiye için farklı, ABD için farklı
2. **Her kategori için 1-3 node yeterli** - Çok fazla node ekleme
3. **Node'lar değişebilir** - Amazon zaman zaman günceller
4. **Test et** - Node ID'yi ekledikten sonra "Manuel Başlat" ile test et

## 🔗 Kaynaklar:

- Amazon PA API Docs: https://webservices.amazon.com/paapi5/documentation/
- Browse Node Finder Tool: (üçüncü parti araçlar)
