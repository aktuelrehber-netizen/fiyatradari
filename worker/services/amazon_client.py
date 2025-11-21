"""
Production-ready Amazon PA API Client
Features: Retry logic, rate limiting, error handling, connection pooling
"""
import time
from typing import List, Dict, Optional, Any
from decimal import Decimal
from datetime import datetime, timedelta
from loguru import logger
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

try:
    from amazon_paapi import AmazonApi
    PAAPI_AVAILABLE = True
except ImportError:
    PAAPI_AVAILABLE = False
    logger.warning("amazon-paapi not installed. Using mock mode.")

from config import config


class RateLimiter:
    """Token bucket rate limiter for API calls"""
    
    def __init__(self, calls_per_second: float = 1.0):
        self.calls_per_second = calls_per_second
        self.tokens = calls_per_second
        self.last_update = time.time()
        self.min_interval = 1.0 / calls_per_second
    
    def wait_if_needed(self):
        """Wait if rate limit is exceeded"""
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.calls_per_second, self.tokens + elapsed * self.calls_per_second)
        self.last_update = now
        
        if self.tokens < 1:
            sleep_time = (1 - self.tokens) / self.calls_per_second
            logger.debug(f"Rate limit: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
            self.tokens = 1
        
        self.tokens -= 1


class AmazonPAAPIClient:
    """
    Professional Amazon Product Advertising API Client
    
    Features:
    - Retry logic with exponential backoff
    - Rate limiting (1 request/second default)
    - Error handling and logging
    - Connection pooling
    - Batch processing support
    - Selection rules filtering
    """
    
    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None, 
                 partner_tag: Optional[str] = None, region: str = "eu-west-1",
                 marketplace: str = "www.amazon.com.tr"):
        """
        Initialize Amazon PA API client
        
        Args:
            access_key: AWS access key (from env if not provided)
            secret_key: AWS secret key (from env if not provided)
            partner_tag: Amazon partner tag (from env if not provided)
            region: AWS region
            marketplace: Amazon marketplace domain
        """
        # Load credentials from database first, then fall back to env
        self.access_key = access_key
        self.secret_key = secret_key
        self.partner_tag = partner_tag
        
        if not all([self.access_key, self.secret_key, self.partner_tag]):
            # Try to load from database
            from database import get_db, SystemSetting
            
            try:
                with get_db() as db:
                    access_key_setting = db.query(SystemSetting).filter(
                        SystemSetting.key == "amazon_access_key"
                    ).first()
                    secret_key_setting = db.query(SystemSetting).filter(
                        SystemSetting.key == "amazon_secret_key"
                    ).first()
                    partner_tag_setting = db.query(SystemSetting).filter(
                        SystemSetting.key == "amazon_partner_tag"
                    ).first()
                    
                    if access_key_setting and access_key_setting.value:
                        self.access_key = access_key_setting.value
                    if secret_key_setting and secret_key_setting.value:
                        self.secret_key = secret_key_setting.value
                    if partner_tag_setting and partner_tag_setting.value:
                        self.partner_tag = partner_tag_setting.value
                    
                    logger.info("✅ Amazon PA API credentials loaded from database")
            except Exception as e:
                logger.warning(f"Could not load Amazon credentials from database: {e}")
                # Fall back to env
                self.access_key = self.access_key or config.AMAZON_ACCESS_KEY
                self.secret_key = self.secret_key or config.AMAZON_SECRET_KEY
                self.partner_tag = self.partner_tag or config.AMAZON_PARTNER_TAG
        
        self.region = region or config.AMAZON_REGION
        self.marketplace = marketplace or config.AMAZON_MARKETPLACE
        
        # Check if PA API is available and configured
        if not PAAPI_AVAILABLE:
            logger.warning(f"❌ Amazon PA API library not available (PAAPI_AVAILABLE={PAAPI_AVAILABLE})")
            self.api = None
            self.enabled = False
            return
        
        if not all([self.access_key, self.secret_key, self.partner_tag]):
            logger.warning(f"❌ Amazon PA API credentials incomplete:")
            logger.warning(f"   Access Key: {'✓' if self.access_key else '✗'}")
            logger.warning(f"   Secret Key: {'✓' if self.secret_key else '✗'}")
            logger.warning(f"   Partner Tag: {'✓' if self.partner_tag else '✗'}")
            self.api = None
            self.enabled = False
            return
        
        # Rate limiter: 1 request/second (Amazon limit)
        self.rate_limiter = RateLimiter(calls_per_second=1.0)
        
        # Initialize API client with resources including ExternalIds for barcodes
        try:
            self.api = AmazonApi(
                key=self.access_key,
                secret=self.secret_key,
                tag=self.partner_tag,
                country='TR',  # Turkey
                resources=[
                    'ItemInfo.Title',
                    'ItemInfo.ByLineInfo',
                    'ItemInfo.ExternalIds',  # EAN, UPC, ISBN barcodes
                    'ItemInfo.Classifications',
                    'Offers.Listings.Price',
                    'Offers.Listings.Availability',
                    'Offers.Listings.DeliveryInfo.IsPrimeEligible',
                    'Images.Primary.Large',
                    'CustomerReviews.StarRating',
                    'CustomerReviews.Count'
                ]
            )
            self.enabled = True
            logger.info("✅ Amazon PA API client initialized successfully with barcode support")
        except Exception as e:
            logger.error(f"Failed to initialize Amazon PA API: {e}")
            self.api = None
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if API is properly configured"""
        return self.enabled
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, Exception))
    )
    def search_items_by_browse_node(
        self,
        browse_node_id: str,
        page: int = 1,
        items_per_page: int = 10,
        selection_rules: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None
    ) -> List[Dict]:
        """
        Search items by browse node with filtering
        
        Args:
            browse_node_id: Amazon browse node ID
            page: Page number (1-10)
            items_per_page: Items per page (max 10)
            selection_rules: Category selection rules for filtering
            sort_by: Sort order (Price:LowToHigh, Price:HighToLow, Relevance, NewestArrivals)
        
        Returns:
            List of product items
        """
        if not self.enabled:
            logger.warning("Amazon PA API not enabled, returning empty list")
            return []
        
        # Rate limiting
        self.rate_limiter.wait_if_needed()
        
        try:
            sort_str = f", sort={sort_by}" if sort_by else ""
            logger.info(f"Searching browse node {browse_node_id}, page {page}{sort_str}")
            
            # Search using Amazon PA API
            result = self.api.search_items(
                browse_node_id=browse_node_id,
                item_page=page,
                item_count=min(items_per_page, 10),
                sort_by=sort_by if sort_by else None
            )
            
            if not result or not hasattr(result, 'items') or not result.items:
                logger.info("No items found in response")
                return []
            
            logger.info(f"Found {len(result.items)} items")
            
            # Convert to dict and filter by selection rules
            product_items = []
            for item in result.items:
                product_dict = self._item_to_dict(item)
                
                # Apply selection rules
                if selection_rules and not self._passes_selection_rules(product_dict, selection_rules):
                    logger.debug(f"Item {product_dict.get('asin')} filtered out by selection rules")
                    continue
                
                product_items.append(product_dict)
            
            logger.info(f"After filtering: {len(product_items)} items")
            return product_items
            
        except Exception as e:
            logger.error(f"Error searching browse node {browse_node_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def get_items(self, asins: List[str]) -> List[Dict]:
        """
        Get multiple items by ASIN (batch)
        
        Args:
            asins: List of ASINs (max 10 per request)
        
        Returns:
            List of product items
        """
        if not self.enabled or not asins:
            return []
        
        # Rate limiting
        self.rate_limiter.wait_if_needed()
        
        # Amazon PA API allows max 10 ASINs per request
        asins = asins[:10]
        
        try:
            logger.info(f"Fetching {len(asins)} items by ASIN")
            
            # Call amazon-paapi get_items (resources are set in API initialization)
            items = self.api.get_items(items=asins)
            
            if not items:
                return []
            
            # Convert to dict format
            return [self._item_to_dict(item) for item in items]
            
        except Exception as e:
            logger.error(f"Error fetching items {asins}: {e}")
            raise
    
    def _item_to_dict(self, item) -> Dict:
        """Convert PA API item to dictionary"""
        try:
            # Extract price data (find LOWEST price from all listings)
            price = None
            is_prime = False
            availability = None
            
            if hasattr(item, 'offers') and item.offers:
                listings = item.offers.listings
                if listings and len(listings) > 0:
                    # Find the lowest price among all available listings
                    valid_prices = []
                    for listing in listings:
                        if hasattr(listing, 'price') and listing.price and listing.price.amount:
                            listing_price = float(listing.price.amount)
                            valid_prices.append({
                                'price': listing_price,
                                'listing': listing
                            })
                    
                    if valid_prices:
                        # Sort by price and get the cheapest
                        all_prices = [p['price'] for p in valid_prices]
                        if len(valid_prices) > 1:
                            logger.info(f"ASIN {item.asin}: Found {len(valid_prices)} prices: {all_prices}")
                        
                        cheapest = min(valid_prices, key=lambda x: x['price'])
                        price = cheapest['price']
                        listing = cheapest['listing']
                        
                        logger.info(f"ASIN {item.asin}: Selected lowest price: {price} TRY (from {len(valid_prices)} listings)")
                        
                        if hasattr(listing, 'availability'):
                            availability = listing.availability.message if listing.availability else None
                        
                        if hasattr(listing, 'delivery_info') and listing.delivery_info:
                            is_prime = listing.delivery_info.is_prime_eligible or False
            
            # Extract rating data
            rating = None
            review_count = None
            if hasattr(item, 'customer_reviews') and item.customer_reviews:
                if hasattr(item.customer_reviews, 'star_rating'):
                    rating = float(item.customer_reviews.star_rating.value) if item.customer_reviews.star_rating else None
                if hasattr(item.customer_reviews, 'count'):
                    review_count = int(item.customer_reviews.count) if item.customer_reviews.count else None
            
            # Extract image
            image_url = None
            if hasattr(item, 'images') and item.images:
                if hasattr(item.images, 'primary') and item.images.primary:
                    if hasattr(item.images.primary, 'large'):
                        image_url = item.images.primary.large.url if item.images.primary.large else None
            
            # Extract title and brand
            title = None
            brand = None
            if hasattr(item, 'item_info') and item.item_info:
                if hasattr(item.item_info, 'title'):
                    title = item.item_info.title.display_value if item.item_info.title else None
                if hasattr(item.item_info, 'by_line_info') and item.item_info.by_line_info:
                    if hasattr(item.item_info.by_line_info, 'brand'):
                        brand = item.item_info.by_line_info.brand.display_value if item.item_info.by_line_info.brand else None
            
            # Extract barcode information (EAN, UPC, ISBN)
            ean = None
            upc = None
            isbn = None
            if hasattr(item, 'item_info') and item.item_info:
                if hasattr(item.item_info, 'external_ids') and item.item_info.external_ids:
                    external_ids = item.item_info.external_ids
                    
                    # EAN (European Article Number)
                    if hasattr(external_ids, 'ea_ns') and external_ids.ea_ns:
                        if hasattr(external_ids.ea_ns, 'display_values') and external_ids.ea_ns.display_values:
                            ean = external_ids.ea_ns.display_values[0] if len(external_ids.ea_ns.display_values) > 0 else None
                    
                    # UPC (Universal Product Code)
                    if hasattr(external_ids, 'up_cs') and external_ids.up_cs:
                        if hasattr(external_ids.up_cs, 'display_values') and external_ids.up_cs.display_values:
                            upc = external_ids.up_cs.display_values[0] if len(external_ids.up_cs.display_values) > 0 else None
                    
                    # ISBN (for books)
                    if hasattr(external_ids, 'is_bns') and external_ids.is_bns:
                        if hasattr(external_ids.is_bns, 'display_values') and external_ids.is_bns.display_values:
                            isbn = external_ids.is_bns.display_values[0] if len(external_ids.is_bns.display_values) > 0 else None
            
            return {
                'asin': item.asin,
                'title': title or '',
                'brand': brand,
                'current_price': price,  # Only real price, no fake list_price
                'currency': 'TRY',
                'image_url': image_url,
                'detail_page_url': item.detail_page_url,
                'rating': rating,
                'review_count': review_count,
                'is_available': availability != 'Out of Stock' if availability else True,
                'availability': availability,
                'is_prime': is_prime,
                'ean': ean,  # European Article Number (barcode)
                'upc': upc,  # Universal Product Code (barcode)
                'isbn': isbn,  # International Standard Book Number
                'fetched_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error converting item to dict: {e}")
            return {}
    
    def _passes_selection_rules(self, product: Dict, rules: Dict[str, Any]) -> bool:
        """
        Check if product passes selection rules
        
        Rules:
            min_rating, max_rating: Rating range
            min_review_count: Minimum reviews
            min_price, max_price: Price range
            min_discount_percentage: Minimum discount
            include_keywords: Must contain these words
            exclude_keywords: Must not contain these words
            only_prime: Prime eligible only
            only_deals: Has discount only
        """
        try:
            # Rating check
            if 'min_rating' in rules and rules['min_rating']:
                if not product.get('rating') or product['rating'] < rules['min_rating']:
                    return False
            
            if 'max_rating' in rules and rules['max_rating']:
                if not product.get('rating') or product['rating'] > rules['max_rating']:
                    return False
            
            # Review count check
            if 'min_review_count' in rules and rules['min_review_count']:
                if not product.get('review_count') or product['review_count'] < rules['min_review_count']:
                    return False
            
            # Price check
            if 'min_price' in rules and rules['min_price']:
                if not product.get('current_price') or product['current_price'] < rules['min_price']:
                    return False
            
            if 'max_price' in rules and rules['max_price']:
                if not product.get('current_price') or product['current_price'] > rules['max_price']:
                    return False
            
            # Note: We don't filter by discount here since we don't have historical data yet
            # Discount filtering will be done by DealDetector after price history is built
            
            # Keyword checks
            title_lower = (product.get('title') or '').lower()
            
            if 'include_keywords' in rules and rules['include_keywords']:
                # Must contain at least one keyword
                if not any(keyword.lower() in title_lower for keyword in rules['include_keywords']):
                    return False
            
            if 'exclude_keywords' in rules and rules['exclude_keywords']:
                # Must not contain any keyword
                if any(keyword.lower() in title_lower for keyword in rules['exclude_keywords']):
                    return False
            
            # Prime check
            if rules.get('only_prime', False):
                if not product.get('is_prime', False):
                    return False
            
            # Note: 'only_deals' filter will be applied by DealDetector
            # after we have price history to compare against
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking selection rules: {e}")
            return True  # On error, include the product
    
