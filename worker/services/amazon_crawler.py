"""
Amazon Web Crawler - Fallback for PA-API Rate Limits
Scrapes product data from Amazon.com.tr when API is unavailable
"""
import re
import time
from typing import Dict, Optional, List
from decimal import Decimal
from loguru import logger
import httpx
from bs4 import BeautifulSoup


class AmazonCrawler:
    """
    Amazon.com.tr web crawler for product data extraction
    Used as fallback when PA-API rate limit is reached
    """
    
    def __init__(self):
        self.base_url = "https://www.amazon.com.tr"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        # Rate limiting: 1 request per 2 seconds to be respectful
        self.last_request_time = 0
        self.min_interval = 2.0
    
    def _wait_if_needed(self):
        """Rate limiting"""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def get_product(self, asin: str) -> Optional[Dict]:
        """
        Crawl product page and extract data
        
        Args:
            asin: Amazon ASIN
            
        Returns:
            Product data dict or None if failed
        """
        self._wait_if_needed()
        
        url = f"{self.base_url}/dp/{asin}"
        
        try:
            with httpx.Client(timeout=30.0, follow_redirects=True, headers=self.headers) as client:
                logger.info(f"Crawling: {url}")
                response = client.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract data
                product_data = {
                    'asin': asin,
                    'title': self._extract_title(soup),
                    'current_price': self._extract_price(soup),
                    'currency': 'TRY',
                    'is_available': self._check_availability(soup),
                    'image_url': self._extract_image(soup),
                    'rating': self._extract_rating(soup),
                    'review_count': self._extract_review_count(soup),
                    'detail_page_url': url,
                    'source': 'crawler'  # Mark as crawled data
                }
                
                logger.info(f"Crawled ASIN {asin}: {product_data.get('title', 'N/A')[:50]}, Price: {product_data.get('current_price')}")
                return product_data
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Product not found: {asin}")
            else:
                logger.error(f"HTTP error crawling {asin}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error crawling {asin}: {e}")
            return None
    
    def get_products(self, asins: List[str]) -> List[Dict]:
        """
        Crawl multiple products
        
        Args:
            asins: List of ASINs
            
        Returns:
            List of product data dicts
        """
        results = []
        for asin in asins:
            product = self.get_product(asin)
            if product:
                results.append(product)
        return results
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product title"""
        selectors = [
            '#productTitle',
            '#title',
            'h1.a-size-large'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        return None
    
    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract current price from JSON data only"""
        
        # Extract price from JSON data embedded in page
        # Amazon stores structured price data in twister-plus-buying-options-price-data
        try:
            json_price_div = soup.select_one('.twister-plus-buying-options-price-data')
            if json_price_div:
                import json
                price_data = json.loads(json_price_div.get_text().strip())
                
                # Extract from desktop_buybox_group_1
                if 'desktop_buybox_group_1' in price_data and len(price_data['desktop_buybox_group_1']) > 0:
                    display_price = price_data['desktop_buybox_group_1'][0].get('displayPrice')
                    if display_price:
                        # Parse displayPrice (e.g., "149,90 TL" → 149.90)
                        price = self._parse_price(display_price)
                        if price:
                            logger.info(f"✅ Found price from JSON displayPrice: {display_price} → {price}")
                            return price
                
                logger.warning(f"⚠️ JSON data found but no valid price in desktop_buybox_group_1")
            else:
                logger.warning("⚠️ No JSON price data found on page")
                
        except (json.JSONDecodeError, KeyError, ValueError, AttributeError) as e:
            logger.error(f"❌ JSON price extraction failed: {e}")
        
        logger.error("❌ No price found - product may be unavailable or page structure changed")
        return None
    
    def _parse_price(self, text: str) -> Optional[float]:
        """Parse price from text"""
        try:
            # Remove currency symbols and whitespace
            text = text.replace('TL', '').replace('₺', '').strip()
            
            # Handle Turkish format: 1.234,56 → 1234.56
            if ',' in text and '.' in text:
                # Both separators present
                text = text.replace('.', '').replace(',', '.')
            elif ',' in text:
                # Only comma (decimal separator in Turkish)
                text = text.replace(',', '.')
            elif '.' in text:
                # Only dot - could be thousands or decimal
                # If more than 2 digits after dot, it's thousands
                parts = text.split('.')
                if len(parts[-1]) > 2:
                    text = text.replace('.', '')
            
            price = float(text)
            return price if price > 0 else None
        except (ValueError, AttributeError):
            return None
    
    def _check_availability(self, soup: BeautifulSoup) -> bool:
        """Check if product is available"""
        # Check for out of stock indicators
        out_of_stock_indicators = [
            'Şu anda mevcut değil',
            'Currently unavailable',
            'Out of stock',
            'Stokta yok'
        ]
        
        page_text = soup.get_text().lower()
        for indicator in out_of_stock_indicators:
            if indicator.lower() in page_text:
                return False
        
        # If we found a price, assume it's available
        price = self._extract_price(soup)
        return price is not None
    
    def _extract_image(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main product image"""
        selectors = [
            '#landingImage',
            '#imgBlkFront',
            '.a-dynamic-image'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                # Try src first, then data-old-hires, then data-a-dynamic-image
                src = element.get('src') or element.get('data-old-hires')
                if src and src.startswith('http'):
                    return src
                
                # Try parsing data-a-dynamic-image JSON
                dynamic = element.get('data-a-dynamic-image')
                if dynamic:
                    try:
                        import json
                        images = json.loads(dynamic)
                        if images:
                            return list(images.keys())[0]
                    except:
                        pass
        
        return None
    
    def _extract_rating(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract product rating"""
        selectors = [
            'span.a-icon-alt',
            'i.a-star-small span',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text()
                # Extract number from "4.5 out of 5 stars" or "5 üzerinden 4.5"
                match = re.search(r'(\d+[.,]\d+)', text)
                if match:
                    try:
                        rating = float(match.group(1).replace(',', '.'))
                        if 0 <= rating <= 5:
                            return rating
                    except ValueError:
                        pass
        
        return None
    
    def _extract_review_count(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract review count"""
        selectors = [
            '#acrCustomerReviewText',
            'span.a-size-base.a-color-secondary',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text()
                # Extract number from "1.234 ratings" or "1.234 değerlendirme"
                text = text.replace('.', '').replace(',', '')
                match = re.search(r'(\d+)', text)
                if match:
                    try:
                        return int(match.group(1))
                    except ValueError:
                        pass
        
        return None
