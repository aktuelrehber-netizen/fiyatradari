"""
Production-ready Amazon PA API Client
Features: Retry logic, rate limiting, error handling, connection pooling
"""
import time
import re
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import os
import json
import redis
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
from services.amazon_crawler import AmazonCrawler


class RateLimiter:
    """
    Distributed rate limiter using Redis
    Ensures all workers respect 1 request/second limit globally
    """
    def __init__(self, calls_per_second: float = 1.0):
        self.min_interval = 1.0 / calls_per_second  # 1 second between requests
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'redis'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=2,  # Separate DB for rate limiting
                decode_responses=False,
                socket_connect_timeout=2
            )
            self.redis_client.ping()  # Test connection
            self.use_redis = True
            logger.info("✅ Redis rate limiter initialized")
        except Exception as e:
            logger.warning(f"⚠️  Redis unavailable, using local rate limiter: {e}")
            self.use_redis = False
            self.last_call = 0
        
        self.key = 'amazon_api_last_call'
    
    def wait_if_needed(self):
        """Wait if needed to respect rate limit (distributed across workers)"""
        if not self.use_redis:
            # Fallback: Local rate limiter (not distributed)
            now = time.time()
            elapsed = now - self.last_call
            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                logger.debug(f"Local rate limit: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
            self.last_call = time.time()
            return
        
        # Redis-based distributed rate limiter
        try:
            # Acquire lock and wait if needed
            lock_acquired = False
            max_wait = 10  # Maximum 10 seconds wait
            start_time = time.time()
            
            while not lock_acquired and (time.time() - start_time) < max_wait:
                # Try to acquire lock
                lock_acquired = self.redis_client.set(
                    f'{self.key}:lock',
                    '1',
                    ex=2,  # Lock expires in 2 seconds
                    nx=True  # Only set if doesn't exist
                )
                
                if not lock_acquired:
                    time.sleep(0.01)  # Wait 10ms and retry
            
            if not lock_acquired:
                logger.warning("Failed to acquire rate limit lock, proceeding anyway")
                return
            
            # Check last call time
            last_call_bytes = self.redis_client.get(self.key)
            last_call = float(last_call_bytes.decode()) if last_call_bytes else 0
            
            now = time.time()
            elapsed = now - last_call
            
            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                logger.debug(f"Distributed rate limit: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
            
            # Update last call time
            self.redis_client.set(self.key, str(time.time()), ex=10)
            
            # Release lock
            self.redis_client.delete(f'{self.key}:lock')
            
        except Exception as e:
            logger.error(f"Rate limiter error: {e}, proceeding without rate limit")
            # Release lock on error
            try:
                self.redis_client.delete(f'{self.key}:lock')
            except:
                pass


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
        
        # Initialize crawler as fallback
        self.crawler = AmazonCrawler()
        logger.info("✅ Amazon Crawler initialized as fallback")
    
    def is_enabled(self) -> bool:
        """Check if API is properly configured"""
        return self.enabled
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, Exception))
    )
    def get_products_batch(self, asins: List[str]) -> List[Dict]:
        """
        🚀 BATCH API: Get up to 10 products in a single API call
        
        This is 10x faster than getting products one by one!
        
        Args:
            asins: List of ASINs (max 10 per Amazon PA API limit)
        
        Returns:
            List of product data dicts
        """
        if not self.enabled:
            logger.warning("Amazon PA API not enabled, falling back to crawler")
            return self.crawler.get_products(asins)
        
        # Amazon PA API limit: 10 items per request
        if len(asins) > 10:
            logger.warning(f"Too many ASINs ({len(asins)}), truncating to 10")
            asins = asins[:10]
        
        if not asins:
            return []
        
        # Rate limiting (still 1 req/sec, but now we get 10 products!)
        self.rate_limiter.wait_if_needed()
        
        try:
            logger.info(f"🚀 BATCH API: Fetching {len(asins)} products in 1 request: {asins}")
            
            # Use get_items() for batch retrieval
            result = self.api.get_items(item_ids=asins)
            
            if not result or not hasattr(result, 'items'):
                logger.warning(f"No items returned from batch API for ASINs: {asins}")
                return []
            
            items = result.items
            logger.info(f"✅ BATCH API: Got {len(items)}/{len(asins)} products")
            
            # Parse each item
            products = []
            for item in items:
                try:
                    product_data = self._parse_item(item)
                    if product_data:
                        products.append(product_data)
                except Exception as e:
                    logger.error(f"Error parsing batch item {item.asin}: {e}")
                    continue
            
            # If some products failed, try crawler for those
            if len(products) < len(asins):
                fetched_asins = {p['asin'] for p in products}
                missing_asins = [a for a in asins if a not in fetched_asins]
                logger.warning(f"⚠️ {len(missing_asins)} products failed from PA API, trying crawler: {missing_asins}")
                
                # Fallback to crawler for missing products
                crawler_products = self.crawler.get_products(missing_asins)
                products.extend(crawler_products)
            
            logger.info(f"✅ BATCH COMPLETE: {len(products)} products fetched")
            return products
            
        except Exception as e:
            logger.error(f"Batch API error for {asins}: {e}")
            # Fallback to crawler
            logger.info("Falling back to crawler for all products")
            return self.crawler.get_products(asins)
    
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
            # Build API filter parameters from selection rules
            api_filters = {}
            
            if selection_rules:
                # Price filters (convert to kuruş/cents)
                if selection_rules.get('min_price'):
                    api_filters['min_price'] = int(selection_rules['min_price'] * 100)
                if selection_rules.get('max_price'):
                    api_filters['max_price'] = int(selection_rules['max_price'] * 100)
                
                # Rating filter
                if selection_rules.get('min_rating'):
                    # Amazon accepts 1-5, we have float, convert to int
                    api_filters['min_reviews_rating'] = int(selection_rules['min_rating'])
                
                # Prime filter
                if selection_rules.get('only_prime'):
                    api_filters['delivery_flags'] = ['Prime']
            
            sort_str = f", sort={sort_by}" if sort_by else ""
            filters_str = f", filters={api_filters}" if api_filters else ""
            logger.info(f"Searching browse node {browse_node_id}, page {page}{sort_str}{filters_str}")
            
            # Search using Amazon PA API with filters
            # Note: Using minimal resources set - amazon_paapi library may handle defaults
            try:
                result = self.api.search_items(
                    browse_node_id=browse_node_id,
                    item_page=page,
                    item_count=min(items_per_page, 10),
                    sort_by=sort_by if sort_by else None,
                    **api_filters  # Pass filters to API
                )
            except Exception as e:
                logger.error(f"Amazon API error: {e}")
                raise
            
            if not result or not hasattr(result, 'items') or not result.items:
                logger.info("No items found in response")
                return []
            
            logger.info(f"Found {len(result.items)} items (already filtered by Amazon API)")
            
            # Convert to dict and apply additional client-side filters
            # (for rules not supported by API like keywords, review_count)
            product_items = []
            for item in result.items:
                product_dict = self._item_to_dict(item)
                
                # Apply remaining client-side filters
                if selection_rules and not self._passes_client_side_filters(product_dict, selection_rules):
                    logger.debug(f"Item {product_dict.get('asin')} filtered out by client-side rules")
                    continue
                
                product_items.append(product_dict)
            
            logger.info(f"After client-side filtering: {len(product_items)} items")
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
            logger.info(f"Fetching {len(asins)} items by ASIN (PA-API)")
            
            # Call amazon-paapi get_items (resources are set in API initialization)
            items = self.api.get_items(items=asins)
            
            if not items:
                return []
            
            # Convert to dict format
            return [self._item_to_dict(item) for item in items]
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check if it's a rate limit error
            if 'limit' in error_msg or 'throttl' in error_msg or 'requests limit reached' in error_msg:
                logger.warning(f"⚠️ API rate limit reached for {asins}, falling back to crawler")
                
                try:
                    # Fallback to crawler
                    crawled_items = self.crawler.get_products(asins)
                    if crawled_items:
                        logger.info(f"✅ Successfully crawled {len(crawled_items)} items as fallback")
                        return crawled_items
                    else:
                        logger.error(f"❌ Crawler also failed for {asins}")
                        raise Exception(f"Both API and crawler failed for {asins}")
                except Exception as crawl_error:
                    logger.error(f"❌ Crawler error for {asins}: {crawl_error}")
                    raise
            else:
                # Not a rate limit error, just log and raise
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
            
            # Debug: Check if customer_reviews exists
            if not hasattr(item, 'customer_reviews'):
                logger.warning(f"ASIN {item.asin}: No customer_reviews attribute in API response")
            elif not item.customer_reviews:
                logger.warning(f"ASIN {item.asin}: customer_reviews is None/empty")
            else:
                logger.info(f"ASIN {item.asin}: customer_reviews EXISTS - checking fields...")
            
            if hasattr(item, 'customer_reviews') and item.customer_reviews:
                # Parse star rating (format: "4.5 out of 5 stars" or float)
                if hasattr(item.customer_reviews, 'star_rating') and item.customer_reviews.star_rating:
                    try:
                        if hasattr(item.customer_reviews.star_rating, 'value'):
                            # If it has .value attribute, use it
                            rating_str = str(item.customer_reviews.star_rating.value)
                        else:
                            # Otherwise use the object directly
                            rating_str = str(item.customer_reviews.star_rating)
                        
                        # Extract number from string (e.g., "4.5 out of 5 stars" -> 4.5)
                        match = re.search(r'(\d+\.?\d*)', rating_str)
                        if match:
                            rating = float(match.group(1))
                            logger.info(f"✅ ASIN {item.asin}: Parsed rating {rating} from '{rating_str}'")
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"ASIN {item.asin}: Failed to parse rating: {e}")
                
                # Parse review count
                if hasattr(item.customer_reviews, 'count'):
                    try:
                        review_count = int(item.customer_reviews.count) if item.customer_reviews.count else None
                        if review_count:
                            logger.info(f"✅ ASIN {item.asin}: Found {review_count} reviews")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"ASIN {item.asin}: Failed to parse review count: {e}")
            
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
            
            # Add partner tag to URL for affiliate tracking
            detail_url = item.detail_page_url
            if self.partner_tag and detail_url and 'tag=' not in detail_url:
                separator = '&' if '?' in detail_url else '?'
                detail_url = f"{detail_url}{separator}tag={self.partner_tag}"
            
            return {
                'asin': item.asin,
                'title': title or '',
                'brand': brand,
                'current_price': price,  # Only real price, no fake list_price
                'currency': 'TRY',
                'image_url': image_url,
                'detail_page_url': detail_url,
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
    
    def _passes_client_side_filters(self, product: Dict, rules: Dict[str, Any]) -> bool:
        """
        Check if product passes client-side selection rules
        (Filters not supported by Amazon PA-API)
        
        Client-side rules:
            min_review_count: Minimum review count
            include_keywords: Must contain these words
            exclude_keywords: Must not contain these words
        
        Note: Price, rating, and prime filters are handled by Amazon API
        """
        try:
            # Review count check (not supported by API)
            if 'min_review_count' in rules and rules['min_review_count']:
                if not product.get('review_count') or product['review_count'] < rules['min_review_count']:
                    return False
            
            # Keyword checks (not supported by API)
            title_lower = (product.get('title') or '').lower()
            
            if 'include_keywords' in rules and rules['include_keywords']:
                # Must contain at least one keyword
                if not any(keyword.lower() in title_lower for keyword in rules['include_keywords']):
                    return False
            
            if 'exclude_keywords' in rules and rules['exclude_keywords']:
                # Must not contain any keyword
                if any(keyword.lower() in title_lower for keyword in rules['exclude_keywords']):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking client-side filters: {e}")
            return True  # On error, include the product
    
    def _passes_selection_rules(self, product: Dict, rules: Dict[str, Any]) -> bool:
        """
        DEPRECATED: Use _passes_client_side_filters instead
        Legacy method for backward compatibility
        
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
    
