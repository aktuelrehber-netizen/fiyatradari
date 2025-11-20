"""
Price Checker Job
Checks prices for tracked products and creates price history records
"""
from datetime import datetime, timedelta
from decimal import Decimal
from loguru import logger

from database import get_db, Product, PriceHistory, Deal
from config import config


class PriceChecker:
    """Check and track product prices"""
    
    def __init__(self):
        self.check_interval_hours = config.PRICE_CHECK_INTERVAL_HOURS
        self.deal_threshold = config.DEAL_THRESHOLD_PERCENTAGE
    
    def run(self):
        """Main job execution"""
        logger.info("Starting price check job...")
        
        with get_db() as db:
            # Get products that need price check
            cutoff_time = datetime.utcnow() - timedelta(hours=self.check_interval_hours)
            
            products = db.query(Product).filter(
                Product.is_active == True,
                (Product.last_checked_at == None) | (Product.last_checked_at < cutoff_time)
            ).all()
            
            logger.info(f"Found {len(products)} products to check")
            
            total_processed = 0
            total_price_changes = 0
            total_deals_created = 0
            
            for product in products:
                try:
                    result = self._check_product_price(product, db)
                    total_processed += 1
                    
                    if result.get("price_changed"):
                        total_price_changes += 1
                    
                    if result.get("deal_created"):
                        total_deals_created += 1
                    
                except Exception as e:
                    logger.error(f"Error checking price for product {product.asin}: {e}")
                    continue
            
            db.commit()
            
            logger.info(f"Price check completed: {total_processed} checked, {total_price_changes} price changes, {total_deals_created} deals created")
            
            return {
                "status": "completed",
                "items_processed": total_processed,
                "price_changes": total_price_changes,
                "deals_created": total_deals_created
            }
    
    def _check_product_price(self, product, db):
        """Check price for a single product"""
        # In a real implementation, you would fetch fresh data from Amazon API
        # For now, we'll just create a price history record if price exists
        
        result = {
            "price_changed": False,
            "deal_created": False
        }
        
        if not product.current_price:
            logger.warning(f"Product {product.asin} has no price, skipping...")
            return result
        
        # Get last price record
        last_price_record = db.query(PriceHistory).filter(
            PriceHistory.product_id == product.id
        ).order_by(PriceHistory.recorded_at.desc()).first()
        
        # Calculate discount
        discount_amount = None
        discount_percentage = None
        
        if product.list_price and product.current_price < product.list_price:
            discount_amount = product.list_price - product.current_price
            discount_percentage = (discount_amount / product.list_price) * 100
        
        # Check if price changed
        if last_price_record and last_price_record.price != product.current_price:
            result["price_changed"] = True
            logger.info(f"Price changed for {product.title}: {last_price_record.price} -> {product.current_price}")
        
        # Create price history record
        price_history = PriceHistory(
            product_id=product.id,
            price=product.current_price,
            list_price=product.list_price,
            currency=product.currency,
            discount_amount=discount_amount,
            discount_percentage=discount_percentage,
            is_available=product.is_available,
            availability_status=product.availability
        )
        db.add(price_history)
        
        # Check if we should create a deal
        if discount_percentage and discount_percentage >= self.deal_threshold:
            # Check if active deal already exists
            existing_deal = db.query(Deal).filter(
                Deal.product_id == product.id,
                Deal.is_active == True
            ).first()
            
            if not existing_deal:
                deal = self._create_deal(product, discount_amount, discount_percentage, db)
                result["deal_created"] = True
                logger.info(f"Deal created for {product.title}: {discount_percentage:.1f}% off")
        
        # Update product last checked time
        product.last_checked_at = datetime.utcnow()
        
        return result
    
    def _create_deal(self, product, discount_amount, discount_percentage, db):
        """Create a new deal"""
        deal = Deal(
            product_id=product.id,
            title=f"{product.title} - %{discount_percentage:.0f} İndirim",
            description=f"{product.title} ürünü şimdi {discount_percentage:.1f}% indirimde!",
            original_price=product.list_price,
            deal_price=product.current_price,
            discount_amount=discount_amount,
            discount_percentage=discount_percentage,
            currency=product.currency,
            is_active=True,
            is_published=False,  # Will be published after review or automatically
            telegram_sent=False
        )
        
        db.add(deal)
        return deal
