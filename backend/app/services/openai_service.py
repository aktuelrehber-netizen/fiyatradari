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
            prompt = f"""Amazon ürün başlığını SEO'ya uygun, kısa ve net hale getir.

Kategori: {category_name}
{f"Marka: {brand}" if brand else ""}
Amazon Başlığı: {amazon_title}

Kurallar:
- Maksimum 100 karakter
- Türkçe dilbilgisine uygun
- Marka + model + ana özellik formatı
- Gereksiz kelimeleri çıkar (örn: "Ürün", "Satış", "Kampanya")
- Anahtar kelimeleri önde tut
- Büyük harf kullanımını düzelt
- Özel karakterleri temizle

Örnek:
"Nespresso Inissia Kapsüllü Kahve Makinesi - Siyah"

Sadece optimize edilmiş başlığı döndür, başka açıklama yapma."""

            # Call OpenAI API (v1.0+ client)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Sen bir e-ticaret SEO uzmanısın. Ürün başlıklarını optimize ederken kullanıcı dostu ve arama motorları için uygun hale getiriyorsun."
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
        
        Args:
            amazon_title: Original Amazon title
            brand: Brand name
        
        Returns:
            Cleaned title
        """
        import re
        
        title = amazon_title
        
        # Remove common junk words and phrases
        junk_patterns = [
            r"Amazon'?da",
            r"Ürün\s*:",
            r"Satış",
            r"Kampanya",
            r"İndirim",
            r"Özel Fiyat",
            r"Hızlı Kargo",
            r"Ücretsiz Kargo",
            r"En İyi",
            r"Kaliteli",
            r"Orjinal",
            r"Orijinal",
            r"Garantili",
            r"\(Yeni\)",
            r"New",
            r"Prime",
            r"- \d+ Adet$",  # "- 2 Adet" gibi sonlardaki adet bilgisi
        ]
        
        for pattern in junk_patterns:
            title = re.sub(pattern, "", title, flags=re.IGNORECASE)
        
        # Remove extra punctuation at the end
        title = re.sub(r'[,\-\s]+$', '', title)
        
        # Remove multiple spaces and dashes
        title = re.sub(r'\s+', ' ', title)
        title = re.sub(r'-+', '-', title)
        
        # Capitalize first letter of each word (title case)
        title = title.title()
        
        # Fix Turkish characters (title() bozabiliyor)
        turkish_fixes = {
            'i̇': 'İ',
            'İ': 'İ',
            'I': 'I',
        }
        for old, new in turkish_fixes.items():
            title = title.replace(old, new)
        
        # Limit length
        if len(title) > 100:
            # Cut at word boundary
            title = title[:97].rsplit(' ', 1)[0] + "..."
        
        return title.strip()
    
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
            prompt = f"""Ürün için SEO meta description oluştur.

Ürün: {product_title}
Kategori: {category_name}
{f"Marka: {brand}" if brand else ""}

Kurallar:
- Maksimum 160 karakter
- Kullanıcıyı satın almaya teşvik etmeli
- Anahtar kelimeleri içermeli
- Call-to-action içermeli

Sadece meta description'ı döndür."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Sen bir SEO uzmanısın."},
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
