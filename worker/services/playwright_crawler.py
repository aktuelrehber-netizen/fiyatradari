"""
Playwright-based Amazon Crawler - Advanced bot detection bypass
Uses real browser automation to bypass Amazon's bot detection
"""
import re
import asyncio
import random
from typing import Dict, Optional, List
from decimal import Decimal
from loguru import logger

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. Run: pip install playwright && playwright install chromium")

from services.proxy_manager import get_proxy_manager


class PlaywrightCrawler:
    """
    Advanced Amazon crawler using Playwright (real browser)
    
    Features:
    - Real browser automation (Chromium headless)
    - JavaScript rendering
    - Anti-bot detection (realistic user behavior)
    - Proxy support
    - CAPTCHA detection (manual intervention required)
    - Cookie persistence
    
    Use cases:
    - When httpx crawler gets blocked
    - For JavaScript-heavy pages
    - When you need high success rate
    
    Trade-offs:
    - Slower than httpx (2-3x)
    - More resource intensive (RAM, CPU)
    - But much better success rate!
    """
    
    def __init__(self, headless: bool = True, use_proxies: bool = True):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright not installed. Run: pip install playwright && playwright install chromium")
        
        self.base_url = "https://www.amazon.com.tr"
        self.headless = headless
        self.use_proxies = use_proxies
        self.proxy_manager = get_proxy_manager() if use_proxies else None
        
        # Amazon partner tag for affiliate tracking
        from config import config
        self.partner_tag = config.AMAZON_PARTNER_TAG
        
        # Browser instances (lazy init)
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        
        logger.info(f"🎭 Playwright crawler initialized (headless={headless}, proxies={use_proxies})")
    
    async def _init_browser(self):
        """Initialize browser if not already done"""
        if self._browser:
            return
        
        self._playwright = await async_playwright().start()
        
        # Browser launch args (stealth mode)
        launch_args = {
            'headless': self.headless,
            'args': [
                '--disable-blink-features=AutomationControlled',  # Hide automation
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        }
        
        # Add proxy if available
        if self.proxy_manager:
            proxy = self.proxy_manager.get_proxy()
            if proxy:
                proxy_url = proxy.get('http://') or proxy.get('https://')
                # Parse proxy URL
                if proxy_url:
                    # Format: http://user:pass@host:port or http://host:port
                    if '@' in proxy_url:
                        auth_part, server_part = proxy_url.split('@')
                        username, password = auth_part.replace('http://', '').replace('https://', '').split(':')
                        server = server_part
                    else:
                        server = proxy_url.replace('http://', '').replace('https://', '')
                        username = None
                        password = None
                    
                    launch_args['proxy'] = {
                        'server': f'http://{server}'
                    }
                    if username and password:
                        launch_args['proxy']['username'] = username
                        launch_args['proxy']['password'] = password
                    
                    logger.info(f"🌐 Playwright using proxy: {server}")
        
        # Launch browser
        self._browser = await self._playwright.chromium.launch(**launch_args)
        
        # Create context with realistic settings
        self._context = await self._browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            locale='tr-TR',
            timezone_id='Europe/Istanbul',
            geolocation={'longitude': 28.9784, 'latitude': 41.0082},  # Istanbul
            permissions=['geolocation']
        )
        
        # Inject anti-detection scripts
        await self._context.add_init_script("""
            // Override navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
            
            // Override plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['tr-TR', 'tr', 'en-US', 'en'],
            });
        """)
        
        logger.info("✅ Playwright browser initialized")
    
    async def close(self):
        """Close browser and cleanup"""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        
        logger.info("🎭 Playwright browser closed")
    
    async def get_product_async(self, asin: str, max_retries: int = 2) -> Optional[Dict]:
        """
        Crawl product page using Playwright
        
        Args:
            asin: Amazon ASIN
            max_retries: Maximum retry attempts
        
        Returns:
            Product data dict or None if failed
        """
        await self._init_browser()
        
        url = f"{self.base_url}/dp/{asin}"
        
        # Add partner tag for affiliate tracking
        detail_url = url
        if self.partner_tag:
            detail_url = f"{url}?tag={self.partner_tag}"
        
        for attempt in range(max_retries + 1):
            page: Optional[Page] = None
            try:
                page = await self._context.new_page()
                
                logger.info(f"🎭 Playwright crawling: {url} (attempt {attempt + 1}/{max_retries + 1})")
                
                # Random delay before navigation (human-like)
                await asyncio.sleep(random.uniform(1, 2))
                
                # Navigate to product page
                response = await page.goto(detail_url, wait_until='networkidle', timeout=30000)
                
                if response.status == 404:
                    logger.warning(f"Product not found: {asin}")
                    await page.close()
                    return None
                
                # Check for CAPTCHA
                captcha_present = await page.locator('form[action="/errors/validateCaptcha"]').count() > 0
                if captcha_present:
                    logger.error(f"⚠️ CAPTCHA detected for {asin}! Manual intervention required.")
                    # Save screenshot for debugging
                    await page.screenshot(path=f'/tmp/captcha_{asin}.png')
                    await page.close()
                    return None
                
                # Wait for page to load (random delay)
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                # Scroll page randomly (human-like behavior)
                await page.evaluate('window.scrollBy(0, Math.random() * 500)')
                await asyncio.sleep(random.uniform(0.3, 0.7))
                
                # Extract product data
                product_data = await self._extract_product_data(page, asin, detail_url)
                
                await page.close()
                
                if product_data:
                    logger.info(f"✅ Playwright crawled: {asin}")
                    return product_data
                else:
                    logger.warning(f"Failed to extract data for {asin}")
                    return None
                
            except Exception as e:
                logger.error(f"Playwright error for {asin}: {e}")
                if page:
                    await page.close()
                
                if attempt < max_retries:
                    backoff = 2 ** attempt
                    logger.warning(f"Retrying in {backoff}s...")
                    await asyncio.sleep(backoff)
                else:
                    logger.error(f"Failed after {max_retries} retries")
                    return None
        
        return None
    
    async def _extract_product_data(self, page: Page, asin: str, url: str) -> Optional[Dict]:
        """Extract product data from page"""
        try:
            # Title
            title = None
            try:
                title = await page.locator('#productTitle').text_content(timeout=5000)
                title = title.strip() if title else None
            except:
                pass
            
            # Price (try multiple selectors)
            current_price = None
            try:
                # Try hidden input first
                price_input = await page.locator('input[name="items[0.base][customerVisiblePrice][amount]"]').get_attribute('value')
                if price_input:
                    current_price = float(price_input)
            except:
                pass
            
            if not current_price:
                # Try JSON data
                try:
                    json_div = await page.locator('.twister-plus-buying-options-price-data').text_content()
                    if json_div:
                        import json
                        price_data = json.loads(json_div)
                        if 'desktop_buybox_group_1' in price_data and len(price_data['desktop_buybox_group_1']) > 0:
                            display_price = price_data['desktop_buybox_group_1'][0].get('displayPrice')
                            if display_price:
                                # Parse Turkish price format
                                price_str = display_price.replace('TL', '').replace('₺', '').strip()
                                price_str = price_str.replace('.', '').replace(',', '.')
                                current_price = float(price_str)
                except:
                    pass
            
            # Image
            image_url = None
            try:
                image_el = await page.locator('#landingImage').get_attribute('src')
                if image_el and image_el.startswith('http'):
                    image_url = image_el
            except:
                pass
            
            # Rating
            rating = None
            try:
                rating_text = await page.locator('span.a-icon-alt').first.text_content(timeout=3000)
                if rating_text:
                    match = re.search(r'(\d+[.,]\d+)', rating_text)
                    if match:
                        rating = float(match.group(1).replace(',', '.'))
            except:
                pass
            
            # Review count
            review_count = None
            try:
                review_text = await page.locator('#acrCustomerReviewText').text_content(timeout=3000)
                if review_text:
                    match = re.search(r'\((\d+(?:[.,]\d+)?)\)', review_text)
                    if match:
                        count_str = match.group(1).replace('.', '').replace(',', '')
                        review_count = int(count_str)
            except:
                pass
            
            # Availability
            is_available = current_price is not None
            
            return {
                'asin': asin,
                'title': title,
                'current_price': current_price,
                'currency': 'TRY',
                'is_available': is_available,
                'image_url': image_url,
                'rating': rating,
                'review_count': review_count,
                'detail_page_url': url,
                'source': 'playwright'
            }
            
        except Exception as e:
            logger.error(f"Error extracting data: {e}")
            return None
    
    async def get_products_async(self, asins: List[str]) -> List[Dict]:
        """
        Crawl multiple products
        
        Args:
            asins: List of ASINs
        
        Returns:
            List of product data dicts
        """
        await self._init_browser()
        
        results = []
        for asin in asins:
            product_data = await self.get_product_async(asin)
            if product_data:
                results.append(product_data)
            
            # Random delay between products (human-like)
            await asyncio.sleep(random.uniform(2, 4))
        
        return results
    
    def get_products(self, asins: List[str]) -> List[Dict]:
        """Sync wrapper for async method"""
        return asyncio.run(self.get_products_async(asins))


# Async context manager support
class PlaywrightCrawlerContext:
    """Context manager for Playwright crawler with automatic cleanup"""
    
    def __init__(self, headless: bool = True, use_proxies: bool = True):
        self.crawler = PlaywrightCrawler(headless=headless, use_proxies=use_proxies)
    
    async def __aenter__(self):
        await self.crawler._init_browser()
        return self.crawler
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.crawler.close()
