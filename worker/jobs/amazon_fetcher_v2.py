"""
Production Amazon Product Fetcher
Handles 100K+ products with batch processing, multi-node support, and selection rules
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
from loguru import logger

from database import get_db, Category, Product, PriceHistory
from config import config
from services.amazon_client import AmazonPAAPIClient


class AmazonProductFetcher:
    """
    Enterprise-grade Amazon product fetcher
    
    Features:
    - Multi-node support (Türk Kahve + Filtre Kahve + Espresso)
    - Batch processing (prevents memory issues with 100K products)
    - Selection rules filtering
    - Progress tracking
    - Price history recording
    - Duplicate prevention
    """
    
    def __init__(self):
        self.amazon_client = AmazonPAAPIClient()
        self.batch_size = 10  # Amazon PA API max items per page
        self.max_pages_per_node = 10  # Max 100 products per node (10 pages x 10 items)
    
    def run(self) -> Dict:
        """Main job execution"""
        logger.info("=" * 80)
        logger.info("Starting Amazon Product Fetch Job")
        logger.info("=" * 80)
        
        if not self.amazon_client.is_enabled():
            logger.warning("Amazon PA API not configured")
            return {
                "status": "skipped",
                "message": "Amazon PA API not configured",
                "items_processed": 0,
                "items_created": 0,
                "items_updated": 0,
                "items_failed": 0
            }
        
        stats = {
            "categories_processed": 0,
            "nodes_processed": 0,
            "items_processed": 0,
            "items_created": 0,
            "items_updated": 0,
            "items_failed": 0,
            "items_filtered": 0
        }
        
        with get_db() as db:
            # Get active categories
            categories = db.query(Category).filter(Category.is_active == True).all()
            logger.info(f"Found {len(categories)} active categories")
            
            for category in categories:
                try:
                    category_stats = self._process_category(category, db)
                    stats["categories_processed"] += 1
                    stats["nodes_processed"] += category_stats["nodes_processed"]
                    stats["items_processed"] += category_stats["items_processed"]
                    stats["items_created"] += category_stats["items_created"]
                    stats["items_updated"] += category_stats["items_updated"]
                    stats["items_failed"] += category_stats["items_failed"]
                    stats["items_filtered"] += category_stats["items_filtered"]
                    
                except Exception as e:
                    logger.error(f"Error processing category {category.name}: {e}")
                    stats["items_failed"] += 1
                    continue
            
            db.commit()
        
        logger.info("=" * 80)
        logger.info("Amazon Product Fetch Job Completed")
        logger.info(f"Categories: {stats['categories_processed']}")
        logger.info(f"Nodes: {stats['nodes_processed']}")
        logger.info(f"Items processed: {stats['items_processed']}")
        logger.info(f"Items created: {stats['items_created']}")
        logger.info(f"Items updated: {stats['items_updated']}")
        logger.info(f"Items filtered: {stats['items_filtered']}")
        logger.info(f"Items failed: {stats['items_failed']}")
        logger.info("=" * 80)
        
        return {
            "status": "completed",
            **stats
        }
    
    def _process_category(self, category: Category, db) -> Dict:
        """
        Process a single category with multiple browse nodes
        
        Example: Kahve Makinesi category has:
        - Node 1: Türk Kahve Makinesi
        - Node 2: Filtre Kahve Makinesi
        - Node 3: Espresso Makinesi
        """
        logger.info(f"Processing category: {category.name}")
        
        stats = {
            "nodes_processed": 0,
            "items_processed": 0,
            "items_created": 0,
            "items_updated": 0,
            "items_failed": 0,
            "items_filtered": 0
        }
        
        # Get browse node IDs
        browse_node_ids = category.amazon_browse_node_ids or []
        if not browse_node_ids:
            logger.warning(f"Category {category.name} has no browse node IDs")
            return stats
        
        logger.info(f"Category has {len(browse_node_ids)} browse nodes")
        
        # Get selection rules
        selection_rules = category.selection_rules or {}
        logger.info(f"Selection rules: {selection_rules}")
        
        # Check max products limit
        current_product_count = db.query(Product).filter(
            Product.category_id == category.id,
            Product.is_active == True
        ).count()
        
        max_products = category.max_products or 100
        if current_product_count >= max_products:
            logger.info(f"Category already has {current_product_count}/{max_products} products, skipping fetch")
            return stats
        
        remaining_slots = max_products - current_product_count
        logger.info(f"Can add {remaining_slots} more products to this category")
        
        # Process each browse node
        products_added = 0
        
        for node_id in browse_node_ids:
            if products_added >= remaining_slots:
                logger.info(f"Reached max products limit for category")
                break
            
            try:
                node_stats = self._process_browse_node(
                    node_id,
                    category,
                    selection_rules,
                    remaining_slots - products_added,
                    db
                )
                
                stats["nodes_processed"] += 1
                stats["items_processed"] += node_stats["items_processed"]
                stats["items_created"] += node_stats["items_created"]
                stats["items_updated"] += node_stats["items_updated"]
                stats["items_failed"] += node_stats["items_failed"]
                stats["items_filtered"] += node_stats["items_filtered"]
                
                products_added += node_stats["items_created"]
                
            except Exception as e:
                logger.error(f"Error processing browse node {node_id}: {e}")
                stats["items_failed"] += 1
                continue
        
        logger.info(f"Category {category.name} completed: {stats['items_created']} new products")
        return stats
    
    def _process_browse_node(
        self,
        browse_node_id: str,
        category: Category,
        selection_rules: Dict,
        max_products: int,
        db
    ) -> Dict:
        """Process a single browse node with pagination and multiple sort strategies"""
        logger.info(f"Processing browse node: {browse_node_id}")
        
        stats = {
            "items_processed": 0,
            "items_created": 0,
            "items_updated": 0,
            "items_failed": 0,
            "items_filtered": 0
        }
        
        # Multiple sort strategies to get different products
        sort_strategies = [
            None,                    # Default (Relevance)
            "Price:LowToHigh",      # Ucuzdan pahalıya
            "Price:HighToLow",      # Pahalıdan ucuza
            "NewestArrivals"        # Yeni ürünler
        ]
        
        # Track ASINs to avoid duplicates across different sorts
        seen_asins = set()
        products_added = 0
        
        for sort_by in sort_strategies:
            if products_added >= max_products:
                logger.info(f"Reached max products limit")
                break
            
            sort_name = sort_by or "Default"
            logger.info(f"Processing with sort strategy: {sort_name}")
            
            page = 1
            
            # Fetch pages until max products or max pages reached
            while products_added < max_products and page <= self.max_pages_per_node:
                try:
                    logger.info(f"Fetching page {page} from node {browse_node_id} (sort: {sort_name})")
                    
                    # Fetch items from Amazon
                    items = self.amazon_client.search_items_by_browse_node(
                        browse_node_id=browse_node_id,
                        page=page,
                        items_per_page=self.batch_size,
                        selection_rules=selection_rules,
                        sort_by=sort_by
                    )
                    
                    if not items:
                        logger.info(f"No more items on page {page}, stopping this sort strategy")
                        break
                    
                    stats["items_processed"] += len(items)
                    logger.info(f"Processing {len(items)} items from page {page}")
                    
                    # Process each item
                    for item in items:
                        if products_added >= max_products:
                            break
                        
                        # Skip duplicates (same ASIN from different sort)
                        asin = item.get('asin')
                        if asin in seen_asins:
                            logger.debug(f"Skipping duplicate ASIN: {asin}")
                            continue
                        
                        seen_asins.add(asin)
                        
                        try:
                            created = self._process_item(item, category, db)
                            if created:
                                stats["items_created"] += 1
                                products_added += 1
                            else:
                                stats["items_updated"] += 1
                        
                        except Exception as e:
                            logger.error(f"Error processing item {asin}: {e}")
                            stats["items_failed"] += 1
                            continue
                    
                    # If we got less than batch size, no more pages for this sort
                    if len(items) < self.batch_size:
                        break
                    
                    page += 1
                    
                except Exception as e:
                    logger.error(f"Error fetching page {page} from node {browse_node_id} (sort: {sort_name}): {e}")
                    break
        
        logger.info(f"Browse node {browse_node_id} completed: {stats['items_created']} new, {stats['items_updated']} updated")
        return stats
    
    def _process_item(self, item: Dict, category: Category, db) -> bool:
        """
        Process a single item - create or update
        
        Returns:
            True if created, False if updated
        """
        asin = item.get('asin')
        if not asin:
            logger.warning("Item has no ASIN, skipping")
            return False
        
        # Check if product exists
        product = db.query(Product).filter(Product.asin == asin).first()
        
        if product:
            # Update existing product
            self._update_product(product, item, db)
            return False
        else:
            # Create new product
            self._create_product(item, category, db)
            return True
    
    def _create_product(self, item: Dict, category: Category, db):
        """Create new product with price history"""
        current_price = Decimal(str(item['current_price'])) if item.get('current_price') else None
        
        product = Product(
            asin=item['asin'],
            title=item.get('title', '')[:500],  # Limit title length
            brand=item.get('brand', '')[:255] if item.get('brand') else None,
            category_id=category.id,
            current_price=current_price,
            list_price=None,  # We don't use Amazon's fake list prices
            currency=item.get('currency', 'TRY'),
            image_url=item.get('image_url'),
            detail_page_url=item.get('detail_page_url'),
            rating=item.get('rating'),
            review_count=item.get('review_count'),
            is_active=True,
            is_available=item.get('is_available', True),
            availability=item.get('availability'),
            amazon_data={'last_fetch': item, 'is_prime': item.get('is_prime', False)},
            last_checked_at=datetime.utcnow()
        )
        
        db.add(product)
        db.flush()  # Get product ID
        
        # Create initial price history (just the current price)
        if current_price:
            price_history = PriceHistory(
                product_id=product.id,
                price=current_price,
                list_price=None,  # No fake list price
                currency=item.get('currency', 'TRY'),
                discount_amount=None,  # Will be calculated from historical avg later
                discount_percentage=None,
                is_available=item.get('is_available', True),
                availability_status=item.get('availability'),
                recorded_at=datetime.utcnow()
            )
            db.add(price_history)
        
        logger.info(f"Created product: {product.asin} - {product.title[:50]} @ {current_price}₺")
    
    def _update_product(self, product: Product, item: Dict, db):
        """Update existing product and add price history if changed"""
        old_price = product.current_price
        new_price = Decimal(str(item['current_price'])) if item.get('current_price') else None
        
        # Update product fields
        product.title = item.get('title', product.title)[:500]
        product.current_price = new_price
        product.list_price = None  # We don't track fake list prices
        product.image_url = item.get('image_url', product.image_url)
        product.detail_page_url = item.get('detail_page_url', product.detail_page_url)
        product.rating = item.get('rating', product.rating)
        product.review_count = item.get('review_count', product.review_count)
        product.is_available = item.get('is_available', True)
        product.availability = item.get('availability')
        product.last_checked_at = datetime.utcnow()
        
        # Update amazon_data
        if not product.amazon_data:
            product.amazon_data = {}
        product.amazon_data['last_fetch'] = item
        product.amazon_data['is_prime'] = item.get('is_prime', False)
        
        # Add price history if price changed
        if new_price and (not old_price or abs(new_price - old_price) >= Decimal('0.01')):
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
            
            logger.info(f"Updated product price: {product.asin} {old_price}₺ -> {new_price}₺")
        else:
            logger.debug(f"Updated product: {product.asin} (no price change)")
