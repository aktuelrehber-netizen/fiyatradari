"""
Amazon Product Fetcher Job
Fetches products from Amazon PA API based on category settings
"""
from datetime import datetime
from decimal import Decimal
from loguru import logger

from database import get_db, Category, Product
from config import config


class AmazonProductFetcher:
    """Fetch products from Amazon PA API"""
    
    def __init__(self):
        self.access_key = config.AMAZON_ACCESS_KEY
        self.secret_key = config.AMAZON_SECRET_KEY
        self.partner_tag = config.AMAZON_PARTNER_TAG
        self.region = config.AMAZON_REGION
        self.marketplace = config.AMAZON_MARKETPLACE
    
    def run(self):
        """Main job execution"""
        logger.info("Starting Amazon product fetch job...")
        
        if not self.access_key or not self.secret_key:
            logger.warning("Amazon API credentials not configured, skipping...")
            return {
                "status": "skipped",
                "message": "Amazon API credentials not configured"
            }
        
        with get_db() as db:
            # Get active categories
            categories = db.query(Category).filter(Category.is_active == True).all()
            
            total_processed = 0
            total_created = 0
            total_updated = 0
            
            for category in categories:
                logger.info(f"Processing category: {category.name}")
                
                if not category.amazon_browse_node_id:
                    logger.warning(f"Category {category.name} has no browse node ID, skipping...")
                    continue
                
                try:
                    # Fetch products from Amazon
                    # NOTE: This is a placeholder - you need to implement actual Amazon PA API calls
                    # using the python-amazon-paapi library
                    
                    # Example:
                    # from amazon.paapi import AmazonAPI
                    # amazon = AmazonAPI(self.access_key, self.secret_key, self.partner_tag, self.region)
                    # items = amazon.search_items(browse_node_id=category.amazon_browse_node_id)
                    
                    # For now, we'll log the intent
                    logger.info(f"Would fetch products for browse node: {category.amazon_browse_node_id}")
                    
                    # Process each product
                    # products = self._process_amazon_items(items, category, db)
                    # total_processed += len(products)
                    
                except Exception as e:
                    logger.error(f"Error fetching products for category {category.name}: {e}")
                    continue
            
            db.commit()
            
            logger.info(f"Amazon fetch job completed: {total_processed} processed, {total_created} created, {total_updated} updated")
            
            return {
                "status": "completed",
                "items_processed": total_processed,
                "items_created": total_created,
                "items_updated": total_updated
            }
    
    def _process_amazon_items(self, items, category, db):
        """Process Amazon API items and create/update products"""
        products = []
        
        for item in items:
            try:
                # Extract product data from Amazon API response
                asin = item.get("ASIN")
                
                # Check if product exists
                product = db.query(Product).filter(Product.asin == asin).first()
                
                if product:
                    # Update existing product
                    self._update_product(product, item, db)
                else:
                    # Create new product
                    product = self._create_product(item, category, db)
                
                products.append(product)
                
            except Exception as e:
                logger.error(f"Error processing item: {e}")
                continue
        
        return products
    
    def _create_product(self, item, category, db):
        """Create a new product from Amazon data"""
        # Extract data from Amazon API response
        # This is a placeholder - adapt to actual Amazon PA API response structure
        
        product = Product(
            asin=item.get("ASIN"),
            title=item.get("ItemInfo", {}).get("Title", {}).get("DisplayValue", ""),
            brand=item.get("ItemInfo", {}).get("ByLineInfo", {}).get("Brand", {}).get("DisplayValue"),
            category_id=category.id,
            current_price=self._extract_price(item),
            list_price=self._extract_list_price(item),
            image_url=self._extract_image_url(item),
            detail_page_url=item.get("DetailPageURL"),
            rating=self._extract_rating(item),
            review_count=self._extract_review_count(item),
            amazon_data=item,
            is_active=True,
            is_available=True,
            last_checked_at=datetime.utcnow()
        )
        
        db.add(product)
        return product
    
    def _update_product(self, product, item, db):
        """Update existing product with new Amazon data"""
        product.title = item.get("ItemInfo", {}).get("Title", {}).get("DisplayValue", product.title)
        product.current_price = self._extract_price(item)
        product.list_price = self._extract_list_price(item)
        product.image_url = self._extract_image_url(item)
        product.detail_page_url = item.get("DetailPageURL", product.detail_page_url)
        product.rating = self._extract_rating(item)
        product.review_count = self._extract_review_count(item)
        product.amazon_data = item
        product.last_checked_at = datetime.utcnow()
    
    def _extract_price(self, item):
        """Extract current price from Amazon item"""
        try:
            offers = item.get("Offers", {})
            listings = offers.get("Listings", [])
            if listings:
                price = listings[0].get("Price", {}).get("Amount")
                return Decimal(str(price)) if price else None
        except:
            return None
    
    def _extract_list_price(self, item):
        """Extract list price from Amazon item"""
        try:
            offers = item.get("Offers", {})
            listings = offers.get("Listings", [])
            if listings:
                price = listings[0].get("SavingBasis", {}).get("Amount")
                return Decimal(str(price)) if price else None
        except:
            return None
    
    def _extract_image_url(self, item):
        """Extract image URL from Amazon item"""
        try:
            images = item.get("Images", {})
            primary = images.get("Primary", {})
            large = primary.get("Large", {})
            return large.get("URL")
        except:
            return None
    
    def _extract_rating(self, item):
        """Extract rating from Amazon item"""
        try:
            rating = item.get("CustomerReviews", {}).get("StarRating", {}).get("Value")
            return float(rating) if rating else None
        except:
            return None
    
    def _extract_review_count(self, item):
        """Extract review count from Amazon item"""
        try:
            count = item.get("CustomerReviews", {}).get("Count")
            return int(count) if count else None
        except:
            return None
