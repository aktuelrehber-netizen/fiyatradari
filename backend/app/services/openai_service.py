"""
OpenAI Service for AI-powered features
"""
import os
from openai import OpenAI
from typing import Optional
from sqlalchemy.orm import Session
from app.db import models


class OpenAIService:
    """Service for OpenAI API interactions"""
    
    def __init__(self, db: Session):
        self.db = db
        self.client = None
        self._load_settings()
    
    def _load_settings(self):
        """Load OpenAI settings from database"""
        # Get OpenAI settings
        api_key_setting = self.db.query(models.SystemSetting).filter(
            models.SystemSetting.key == "openai_api_key"
        ).first()
        
        model_setting = self.db.query(models.SystemSetting).filter(
            models.SystemSetting.key == "openai_model"
        ).first()
        
        max_tokens_setting = self.db.query(models.SystemSetting).filter(
            models.SystemSetting.key == "openai_max_tokens"
        ).first()
        
        temperature_setting = self.db.query(models.SystemSetting).filter(
            models.SystemSetting.key == "openai_temperature"
        ).first()
        
        enabled_setting = self.db.query(models.SystemSetting).filter(
            models.SystemSetting.key == "openai_enabled"
        ).first()
        
        # Set attributes
        self.api_key = api_key_setting.value if api_key_setting else None
        self.model = model_setting.value if model_setting else "gpt-3.5-turbo"
        self.max_tokens = int(max_tokens_setting.value) if max_tokens_setting else 1000
        self.temperature = float(temperature_setting.value) if temperature_setting else 0.7
        self.enabled = enabled_setting.value == "true" if enabled_setting else False
        
        # Configure OpenAI client (new API v1.0+)
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
    
    def is_enabled(self) -> bool:
        """Check if OpenAI is enabled and configured"""
        return self.enabled and self.api_key is not None
    
    def optimize_product_title(
        self, 
        amazon_title: str, 
        category_name: str,
        brand: Optional[str] = None
    ) -> Optional[str]:
        """
        Optimize Amazon product title for SEO
        
        Args:
            amazon_title: Original Amazon product title
            category_name: Product category name
            brand: Brand name (optional)
        
        Returns:
            SEO-optimized title or None if failed
        """
        if not self.is_enabled():
            # Fallback: clean Amazon title
            return self._fallback_title_cleaning(amazon_title, brand)
        
        try:
            # Construct prompt
            prompt = f"""Aşağıdaki Amazon ürünü için SEO'ya uygun, kullanıcı dostu bir KATALOG BAŞLIĞI oluştur.
Orijinal başlığı olduğu gibi kullanma, yeni bir başlık yarat.

Kategori: {category_name}
{f"Marka: {brand}" if brand else ""}
Amazon Ürün Başlığı: {amazon_title}

KURALLAR:
1. Maksimum 100 karakter
2. Marka + Model/Özellik + Beden/Renk formatı kullan
3. Arama motorları için optimize et (anahtar kelimeler önde)
4. Gereksiz kelimeleri çıkar: "Ürün", "Satış", "Kampanya", "(Yeni)", "Amazon'da"
5. Virgülleri tire (-) ile değiştir
6. Türkçe büyük/küçük harf kurallarına uy
7. Net ve anlaşılır olsun

İYİ ÖRNEKLER:
❌ "Philips HD7431/20 Daily Collection Filtre Kahve Makinesi 1000W Siyah/Kırmızı Ürün ( Yeni )"
✅ "Philips Daily Collection HD7431/20 Filtre Kahve Makinesi - 1000W"

❌ "adidas ALPHAEDGE + Kadın Spor Ayakkabı, shadow fig, 38"
✅ "Adidas Alphaedge+ Kadın Spor Ayakkabı - Shadow Fig - 38 Numara"

Sadece yeni katalog başlığını döndür, başka açıklama yapma."""

            # Call OpenAI API (v1.0+ client)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Sen bir e-ticaret SEO uzmanısın. Amazon ürün başlıklarını alıp, katalog siteleri için SEO'ya uygun YENİ başlıklar oluşturuyorsun. Orijinal başlıkları kopyalamıyorsun, yeniden yazıyorsun."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Extract optimized title
            optimized_title = response.choices[0].message.content.strip()
            
            # Validation
            if len(optimized_title) > 150:
                optimized_title = optimized_title[:147] + "..."
            
            return optimized_title
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fallback
            return self._fallback_title_cleaning(amazon_title, brand)
    
    def _fallback_title_cleaning(self, amazon_title: str, brand: Optional[str] = None) -> str:
        """
        Fallback title cleaning when OpenAI is not available
        Minimal cleaning to preserve product information
        
        Args:
            amazon_title: Original Amazon title
            brand: Brand name
        
        Returns:
            Cleaned title (minimal changes)
        """
        import re
        
        title = amazon_title
        
        # Only remove obvious junk patterns (very conservative)
        junk_patterns = [
            r"\s*\(Yeni\)\s*$",      # " (Yeni)" at end
            r"\s*\(\s*Yeni\s*\)\s*", # " ( Yeni )" anywhere
            r"Amazon'?da\s*",         # "Amazon'da"
            r"Ücretsiz\s+Kargo\s*",   # "Ücretsiz Kargo"
            r"Hızlı\s+Kargo\s*",      # "Hızlı Kargo"
        ]
        
        for pattern in junk_patterns:
            title = re.sub(pattern, " ", title, flags=re.IGNORECASE)
        
        # Clean up multiple spaces
        title = re.sub(r'\s+', ' ', title)
        
        # Clean up extra punctuation/spaces at start and end only
        title = title.strip(' ,-;:')
        
        # Limit length if too long (preserve as much as possible)
        if len(title) > 120:
            # Cut at word boundary
            title = title[:117].rsplit(' ', 1)[0] + "..."
        
        return title
    
    def generate_meta_description(
        self, 
        product_title: str, 
        category_name: str,
        brand: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate SEO meta description for catalog product
        
        Args:
            product_title: Product title
            category_name: Category name
            brand: Brand name
        
        Returns:
            Meta description or None
        """
        if not self.is_enabled():
            return self._fallback_meta_description(product_title, category_name, brand)
        
        try:
            prompt = f"""Aşağıdaki katalog ürünü için SEO'ya uygun bir meta description oluştur.

Ürün Başlığı: {product_title}
Kategori: {category_name}
{f"Marka: {brand}" if brand else ""}

KURALLAR:
1. Maksimum 155 karakter (Google limit)
2. Ürünün faydalarını ve özelliklerini vurgula
3. Arama motorları için anahtar kelimeler ekle
4. Kullanıcıyı tıklamaya teşvik et
5. Doğal Türkçe kullan
6. Fiyat bilgisi ekleme

ÖRNEK:
Ürün: "Philips Daily Collection HD7431/20 Filtre Kahve Makinesi - 1000W"
Meta: "Philips Daily Collection filtre kahve makinesi ile her sabah taze kahve keyfi. 1000W güç, kolay temizlik. Hızlı kargo ve güvenli alışveriş."

Sadece meta description'ı döndür, başka açıklama yapma."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "Sen bir e-ticaret SEO uzmanısın. Ürünler için arama motorlarında iyi sıralama alan meta description'lar yazıyorsun."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=self.temperature
            )
            
            meta_desc = response.choices[0].message.content.strip()
            
            if len(meta_desc) > 160:
                meta_desc = meta_desc[:157] + "..."
            
            return meta_desc
            
        except Exception as e:
            print(f"OpenAI API error for meta description: {e}")
            return self._fallback_meta_description(product_title, category_name, brand)
    
    def _fallback_meta_description(
        self, 
        product_title: str, 
        category_name: str, 
        brand: Optional[str] = None
    ) -> str:
        """Fallback meta description"""
        brand_text = f"{brand} " if brand else ""
        return f"{brand_text}{product_title} - En uygun fiyatlarla Amazon'da. {category_name} kategorisinde fırsat ürünleri incele, karşılaştır ve hemen satın al!"[:160]
