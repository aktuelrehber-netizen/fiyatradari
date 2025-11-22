"""
Amazon Web Crawler - Fallback for PA-API Rate Limits
Scrapes product data from Amazon.com.tr when API is unavailable
"""
import re
import time
import asyncio
import random
from typing import Dict, Optional, List
from decimal import Decimal
from loguru import logger
import httpx
from bs4 import BeautifulSoup
from services.proxy_manager import get_proxy_manager


class AmazonCrawler:
    """
    Amazon.com.tr web crawler for product data extraction
    Used as fallback when PA-API rate limit is reached
    
    Features:
    - Async support with 2 concurrent requests (2x faster)
    - User-Agent rotation (looks like different browsers)
    - Retry logic with exponential backoff
    - Random delays (5-8s) to avoid pattern detection
    """
    
    # Multiple User-Agents to rotate (look like different browsers)
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    ]
    
    def __init__(self, use_proxies: bool = True):
        self.base_url = "https://www.amazon.com.tr"
        self._base_headers = {
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
        
        # 🌐 Proxy support
        self.use_proxies = use_proxies
        self.proxy_manager = get_proxy_manager() if use_proxies else None
        if self.proxy_manager:
            stats = self.proxy_manager.get_stats()
            logger.info(f"🌐 Proxy rotation enabled: {stats['available']}/{stats['total']} proxies available")
        else:
            logger.info("Direct connection (no proxies)")
        
        # Rate limiting: 5-8 seconds between requests to avoid bot detection
        # Amazon is aggressive with bot detection, need slower crawling
        self.last_request_time = 0
        self.min_interval = 5.0  # Minimum 5 seconds
        self.max_interval = 8.0  # Maximum 8 seconds (randomized)
        self.semaphore = asyncio.Semaphore(2)  # Max 2 concurrent requests
    
    def _get_random_headers(self) -> dict:
        """Get headers with random User-Agent"""
        headers = self._base_headers.copy()
        headers['User-Agent'] = random.choice(self.USER_AGENTS)
        return headers
    
    def _wait_if_needed(self):
        """Rate limiting with random delay to avoid pattern detection"""
        now = time.time()
        elapsed = now - self.last_request_time
        
        # Random delay between min and max interval
        required_interval = random.uniform(self.min_interval, self.max_interval)
        
        if elapsed < required_interval:
            sleep_time = required_interval - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def _wait_if_needed_async(self):
        """Async rate limiting with random delay"""
        now = time.time()
        elapsed = now - self.last_request_time
        
        # Random delay between min and max interval
        required_interval = random.uniform(self.min_interval, self.max_interval)
        
        if elapsed < required_interval:
            sleep_time = required_interval - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.1f}s")
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_product(self, asin: str) -> Optional[Dict]:
        """
        Crawl product page and extract data (sync version)
        
        Args:
            asin: Amazon ASIN
            
        Returns:
            Product data dict or None if failed
        """
        self._wait_if_needed()
        
        url = f"{self.base_url}/dp/{asin}"
        
        try:
            with httpx.Client(timeout=30.0, follow_redirects=True, headers=self._get_random_headers()) as client:
                logger.info(f"Crawling: {url}")
                response = client.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract data
                # If no price found, product is out of stock
                current_price = self._extract_price(soup)
                is_available = current_price is not None
                
                product_data = {
                    'asin': asin,
                    'title': self._extract_title(soup),
                    'current_price': current_price,
                    'currency': 'TRY',
                    'is_available': is_available,
                    'image_url': self._extract_image(soup),
                    'rating': self._extract_rating(soup),
                    'review_count': self._extract_review_count(soup),
                    'detail_page_url': url,
                    'source': 'crawler'  # Mark as crawled data
                }
                
                if not is_available:
                    logger.warning(f"⚠️ ASIN {asin}: No price found → Marked as OUT OF STOCK")
                
                title = product_data.get('title') or 'N/A'
                title_preview = title[:50] if title else 'N/A'
                logger.info(f"Crawled ASIN {asin}: {title_preview}, Price: {product_data.get('current_price')}")
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
    
    async def get_product_async(self, asin: str, max_retries: int = 2) -> Optional[Dict]:
        """
        Crawl product page asynchronously with retry logic and proxy rotation
        
        Args:
            asin: Amazon ASIN
            max_retries: Maximum retry attempts on failure
            
        Returns:
            Product data dict or None if failed
        """
        url = f"{self.base_url}/dp/{asin}"
        
        for attempt in range(max_retries + 1):
            # Get proxy for this request (rotation)
            proxy = self.proxy_manager.get_proxy() if self.proxy_manager else None
            
            try:
                async with self.semaphore:  # Limit concurrent requests
                    await self._wait_if_needed_async()
                    
                    # Build client with proxy if available
                    client_kwargs = {
                        'timeout': 30.0,
                        'follow_redirects': True,
                        'headers': self._get_random_headers()
                    }
                    if proxy:
                        client_kwargs['proxies'] = proxy
                        logger.info(f"🌐 Crawling with proxy: {url} (attempt {attempt + 1}/{max_retries + 1})")
                    else:
                        logger.info(f"Crawling: {url} (attempt {attempt + 1}/{max_retries + 1})")
                    
                    async with httpx.AsyncClient(**client_kwargs) as client:
                        response = await client.get(url)
                        response.raise_for_status()
                        
                        # Mark proxy as successful if used
                        if proxy and self.proxy_manager:
                            self.proxy_manager.mark_proxy_success(proxy)
                        
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Extract data
                        current_price = self._extract_price(soup)
                        is_available = current_price is not None
                        
                        product_data = {
                            'asin': asin,
                            'title': self._extract_title(soup),
                            'current_price': current_price,
                            'currency': 'TRY',
                            'is_available': is_available,
                            'image_url': self._extract_image(soup),
                            'rating': self._extract_rating(soup),
                            'review_count': self._extract_review_count(soup),
                            'detail_page_url': url,
                            'source': 'crawler'
                        }
                        
                        if not is_available:
                            logger.warning(f"⚠️ ASIN {asin}: No price found → Marked as OUT OF STOCK")
                        
                        title = product_data.get('title') or 'N/A'
                        title_preview = title[:50] if title else 'N/A'
                        logger.info(f"Crawled ASIN {asin}: {title_preview}, Price: {product_data.get('current_price')}")
                        return product_data
                        
            except httpx.HTTPStatusError as e:
                # Mark proxy as failed if used
                if proxy and self.proxy_manager:
                    self.proxy_manager.mark_proxy_failed(proxy)
                
                if e.response.status_code == 404:
                    logger.warning(f"Product not found: {asin}")
                    return None
                elif attempt < max_retries:
                    backoff = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"HTTP error {e.response.status_code} for {asin}, retrying in {backoff}s...")
                    await asyncio.sleep(backoff)
                else:
                    logger.error(f"HTTP error crawling {asin} after {max_retries} retries: {e}")
                    return None
            except Exception as e:
                # Mark proxy as failed if used
                if proxy and self.proxy_manager:
                    self.proxy_manager.mark_proxy_failed(proxy)
                
                if attempt < max_retries:
                    backoff = 2 ** attempt
                    logger.warning(f"Error crawling {asin}, retrying in {backoff}s: {e}")
                    await asyncio.sleep(backoff)
                else:
                    logger.error(f"Error crawling {asin} after {max_retries} retries: {e}")
                    return None
        
        return None
    
    async def get_products_async(self, asins: List[str]) -> List[Dict]:
        """
        Crawl multiple products concurrently (max 2 at a time)
        
        Args:
            asins: List of ASINs
            
        Returns:
            List of product data dicts (None entries filtered out)
        """
        logger.info(f"Starting async crawl for {len(asins)} products (max 2 concurrent)")
        tasks = [self.get_product_async(asin) for asin in asins]
        results = await asyncio.gather(*tasks)
        
        # Filter out None results
        valid_results = [r for r in results if r is not None]
        logger.info(f"Async crawl complete: {len(valid_results)}/{len(asins)} succeeded")
        return valid_results
    
    def get_products(self, asins: List[str]) -> List[Dict]:
        """
        Crawl multiple products (sync wrapper for async method)
        
        Args:
            asins: List of ASINs
            
        Returns:
            List of product data dicts
        """
        return asyncio.run(self.get_products_async(asins))
    
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
        """Extract current price - PRIMARY: hidden input, FALLBACK: JSON"""
        
        # PRIMARY: Extract from hidden input (user-specified selector)
        try:
            hidden_input = soup.select_one('input[name="items[0.base][customerVisiblePrice][amount]"]')
            if hidden_input:
                value = hidden_input.get('value')
                if value:
                    price = float(value)
                    if price > 0:
                        logger.info(f"✅ Found price from hidden input: {price}")
                        return price
        except (ValueError, AttributeError) as e:
            logger.debug(f"Hidden input extraction failed: {e}")
        
        # FALLBACK: Extract price from JSON data
        try:
            json_price_div = soup.select_one('.twister-plus-buying-options-price-data')
            if json_price_div:
                import json
                price_data = json.loads(json_price_div.get_text().strip())
                
                if 'desktop_buybox_group_1' in price_data and len(price_data['desktop_buybox_group_1']) > 0:
                    display_price = price_data['desktop_buybox_group_1'][0].get('displayPrice')
                    if display_price:
                        price = self._parse_price(display_price)
                        if price:
                            logger.info(f"✅ Found price from JSON: {display_price} → {price}")
                            return price
        except (json.JSONDecodeError, KeyError, ValueError, AttributeError) as e:
            logger.debug(f"JSON extraction failed: {e}")
        
        logger.warning("⚠️ No price found - product will be marked as out of stock")
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
        """Check if product is available - PRIMARY: specific span, FALLBACK: price"""
        
        # PRIMARY: Check user-specified out-of-stock span
        out_of_stock_span = soup.select_one('span.a-color-price.a-text-bold')
        if out_of_stock_span:
            text = out_of_stock_span.get_text().strip()
            if 'Şu anda mevcut değil' in text:
                logger.info("⚠️ Found out-of-stock indicator span")
                return False
        
        # FALLBACK: Check for other out of stock indicators
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
        """Extract product rating - PRIMARY: user-specified span, FALLBACK: standard selectors"""
        
        # PRIMARY: User-specified selector - aria-hidden span with rating
        try:
            rating_span = soup.select_one('span.a-size-small.a-color-base[aria-hidden="true"]')
            if rating_span:
                text = rating_span.get_text().strip()
                # Extract number like "3,8" or "3.8"
                match = re.search(r'(\d+[.,]\d+)', text)
                if match:
                    rating = float(match.group(1).replace(',', '.'))
                    if 0 <= rating <= 5:
                        logger.info(f"✅ Found rating from aria-hidden span: {rating}")
                        return rating
        except (ValueError, AttributeError) as e:
            logger.debug(f"User-specified rating extraction failed: {e}")
        
        # FALLBACK: Standard selectors
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
                            logger.info(f"✅ Found rating from fallback: {rating}")
                            return rating
                    except ValueError:
                        pass
        
        return None
    
    def _extract_review_count(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract review count - PRIMARY: #acrCustomerReviewText with parentheses, FALLBACK: other selectors"""
        
        # PRIMARY: User-specified selector - #acrCustomerReviewText with (28) format
        try:
            review_element = soup.select_one('#acrCustomerReviewText')
            if review_element:
                text = review_element.get_text()
                # Extract number from parentheses: "(28)" or "(1.234)"
                match = re.search(r'\((\d+(?:[.,]\d+)?)\)', text)
                if match:
                    # Remove dots/commas used as thousands separator
                    count_str = match.group(1).replace('.', '').replace(',', '')
                    count = int(count_str)
                    logger.info(f"✅ Found review count from #acrCustomerReviewText: {count}")
                    return count
        except (ValueError, AttributeError) as e:
            logger.debug(f"Primary review count extraction failed: {e}")
        
        # FALLBACK: Other selectors
        fallback_selectors = [
            'span.a-size-base.a-color-secondary',
        ]
        
        for selector in fallback_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text()
                # Extract number from "1.234 ratings" or "1.234 değerlendirme"
                text = text.replace('.', '').replace(',', '')
                match = re.search(r'(\d+)', text)
                if match:
                    try:
                        count = int(match.group(1))
                        logger.info(f"✅ Found review count from fallback: {count}")
                        return count
                    except ValueError:
                        pass
        
        return None
