"""
Production Price Checker
Efficient incremental price updates for 100K+ products
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Tuple
from loguru import logger

from database import get_db, Product, PriceHistory, Deal
from config import config
from services.amazon_client import AmazonPAAPIClient
from services.deal_detector import DealDetector


class PriceChecker:
    """
    Efficient price checker for large-scale product tracking
    
    Features:
    - Incremental updates (oldest checked first)
    - Batch processing (10 ASINs per API call)
    - Smart scheduling based on check_interval
    - Price history tracking
    - Automatic deal detection
    """
    
    def __init__(self):
        self.amazon_client = AmazonPAAPIClient()
        self.deal_detector = DealDetector(deal_threshold_percentage=config.DEAL_THRESHOLD_PERCENTAGE)
        self.batch_size = 10  # Amazon PA API max
        self.check_interval_hours = config.PRICE_CHECK_INTERVAL_HOURS
    
    def run(self) -> Dict:
        """Main job execution"""
        logger.info("=" * 80)
        logger.info("Starting Price Check Job")
        logger.info("=" * 80)
        
        if not self.amazon_client.is_enabled():
            logger.warning("Amazon PA API not configured")
            return {
                "status": "skipped",
                "message": "Amazon PA API not configured",
                "items_processed": 0,
                "items_updated": 0,
                "items_failed": 0
            }
        
        stats = {
            "items_processed": 0,
            "items_updated": 0,
            "items_failed": 0,
            "price_changes": 0,
            "deals_created": 0,
            "deals_expired": 0
        }
        
        with get_db() as db:
            # Get products that need checking
            products_to_check = self._get_products_needing_check(db)
            logger.info(f"Found {len(products_to_check)} products to check")
            
            if not products_to_check:
                logger.info("No products need checking at this time")
                return {"status": "completed", **stats}
            
            # Process in batches
            for i in range(0, len(products_to_check), self.batch_size):
                batch = products_to_check[i:i + self.batch_size]
                
                try:
                    batch_stats = self._process_batch(batch, db)
                    stats["items_processed"] += batch_stats["items_processed"]
                    stats["items_updated"] += batch_stats["items_updated"]
                    stats["items_failed"] += batch_stats["items_failed"]
                    stats["price_changes"] += batch_stats["price_changes"]
                    stats["deals_created"] += batch_stats["deals_created"]
                    
                    # Commit after each batch
                    db.commit()
                    
                except Exception as e:
                    logger.error(f"Error processing batch: {e}")
                    db.rollback()
                    stats["items_failed"] += len(batch)
                    continue
            
            # Check for expired deals
            expired_count = self._expire_old_deals(db)
            stats["deals_expired"] = expired_count
            db.commit()
        
        logger.info("=" * 80)
        logger.info("Price Check Job Completed")
        logger.info(f"Processed: {stats['items_processed']}")
        logger.info(f"Updated: {stats['items_updated']}")
        logger.info(f"Price changes: {stats['price_changes']}")
        logger.info(f"Deals created: {stats['deals_created']}")
        logger.info(f"Deals expired: {stats['deals_expired']}")
        logger.info(f"Failed: {stats['items_failed']}")
        logger.info("=" * 80)
        
        return {"status": "completed", **stats}
    
    def _get_products_needing_check(self, db, limit: int = 500) -> List[Product]:
        """
        Get products that need price checking
        
        Priority:
        1. Never checked
        2. Oldest checked first
        3. Active products only
        
        Args:
            limit: Max products to check per run (prevents API overload)
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=self.check_interval_hours)
        
        # Get active products that haven't been checked recently
        products = db.query(Product).filter(
            Product.is_active == True,
            (Product.last_checked_at == None) | (Product.last_checked_at < cutoff_time)
        ).order_by(
            Product.last_checked_at.asc().nullsfirst()
        ).limit(limit).all()
        
        return products
    
    def _process_batch(self, products: List[Product], db) -> Dict:
        """
        🚀 Process batch of products using BATCH API (10 products per request)
        
        OLD: 1 request per product = slow
        NEW: 1 request per 10 products = 10x faster!
        """
        asins = [p.asin for p in products]
        logger.info(f"🚀 BATCH MODE: Checking prices for {len(asins)} ASINs")
        
        stats = {
            "items_processed": 0,
            "items_updated": 0,
            "items_failed": 0,
            "price_changes": 0,
            "deals_created": 0
        }
        
        try:
            # Split into chunks of 10 (Amazon PA API limit)
            chunk_size = 10
            all_items = []
            
            for i in range(0, len(asins), chunk_size):
                chunk_asins = asins[i:i + chunk_size]
                logger.info(f"📦 Batch {i//chunk_size + 1}: Fetching {len(chunk_asins)} products in 1 API call")
                
                # 🚀 BATCH API CALL - Get 10 products at once!
                chunk_items = self.amazon_client.get_products_batch(chunk_asins)
                all_items.extend(chunk_items)
                
                logger.info(f"✅ Batch {i//chunk_size + 1}: Got {len(chunk_items)}/{len(chunk_asins)} products")
            
            # Create lookup dict
            items_dict = {item['asin']: item for item in all_items}
            
            logger.info(f"✅ BATCH COMPLETE: Fetched {len(all_items)}/{len(asins)} products")
            
            # Update each product
            for product in products:
                stats["items_processed"] += 1
                
                item = items_dict.get(product.asin)
                if not item:
                    logger.warning(f"No data for ASIN {product.asin}")
                    product.last_checked_at = datetime.utcnow()
                    stats["items_failed"] += 1
                    continue
                
                # Update product
                price_changed, deal_created = self._update_product_price(product, item, db)
                
                if price_changed:
                    stats["price_changes"] += 1
                if deal_created:
                    stats["deals_created"] += 1
                
                stats["items_updated"] += 1
            
        except Exception as e:
            logger.error(f"Error fetching batch: {e}")
            stats["items_failed"] = len(products)
            raise
        
        return stats
    
    def _update_product_price(self, product: Product, item: Dict, db) -> Tuple[bool, bool]:
        """
        Update product price and create price history
        
        Returns:
            (price_changed, deal_created)
        """
        old_price = product.current_price
        new_price = Decimal(str(item['current_price'])) if item.get('current_price') else None
        
        price_changed = False
        deal_created = False
        
        # Update product fields
        product.current_price = new_price
        product.list_price = None  # We don't track fake list prices
        product.rating = item.get('rating', product.rating)
        product.review_count = item.get('review_count', product.review_count)
        product.is_available = item.get('is_available', True)
        product.availability = item.get('availability')
        product.last_checked_at = datetime.utcnow()
        
        # Update amazon_data with is_prime info
        if not product.amazon_data:
            product.amazon_data = {}
        product.amazon_data['is_prime'] = item.get('is_prime', False)
        product.amazon_data['last_update'] = datetime.utcnow().isoformat()
        
        # Check for price change
        if new_price and (not old_price or abs(new_price - old_price) >= Decimal('0.01')):
            price_changed = True
            
            # Add price history (only current price, no fake discounts)
            price_history = PriceHistory(
                product_id=product.id,
                price=new_price,
                list_price=None,  # No fake list price
                currency=item.get('currency', 'TRY'),
                discount_amount=None,  # Will be calculated from historical avg
                discount_percentage=None,
                is_available=item.get('is_available', True),
                availability_status=item.get('availability'),
                recorded_at=datetime.utcnow()
            )
            db.add(price_history)
            db.flush()  # Make sure price history is saved before analyzing
            
            logger.info(f"Price changed: {product.asin} {old_price}₺ -> {new_price}₺")
        
        # Smart deal detection (works with or without price change)
        # Analyzes historical data to detect real deals
        is_deal, deal_info = self.deal_detector.analyze_product(product, db)
        
        if is_deal:
            created, deal = self.deal_detector.create_or_update_deal(product, deal_info, db)
            deal_created = created
        
        return price_changed, deal_created
    
    
    def _expire_old_deals(self, db) -> int:
        """
        Expire deals where product is no longer a good deal
        Uses smart detection to verify deal validity
        """
        # Get active deals
        active_deals = db.query(Deal).filter(Deal.is_active == True).all()
        
        expired_count = 0
        for deal in active_deals:
            product = deal.product
            
            # Check if product is still available
            if not product or not product.is_available:
                deal.is_active = False
                deal.valid_until = datetime.utcnow()
                expired_count += 1
                logger.info(f"Expired deal (unavailable): {deal.title[:50]}")
                continue
            
            # Use smart deal detector to verify if still a deal
            is_deal, deal_info = self.deal_detector.analyze_product(product, db)
            
            if not is_deal:
                deal.is_active = False
                deal.valid_until = datetime.utcnow()
                expired_count += 1
                logger.info(f"Expired deal (no longer qualifies): {deal.title[:50]}")
        
        return expired_count
