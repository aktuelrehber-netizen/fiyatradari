"""
Smart Batch Processor
Efficiently fetches product batches based on priority and check intervals
"""
from datetime import datetime, timedelta
from typing import List, Dict
from loguru import logger

from database import get_db, Product, Deal


class SmartBatchProcessor:
    """
    Smart batch processor for 1M+ products
    
    Strategy:
    - High priority: Active deals, volatile prices (every 1 hour)
    - Medium priority: Popular products (every 6 hours)
    - Low priority: Stable products (every 24 hours)
    """
    
    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
    
    def get_high_priority_batches(self, limit: int = 10000) -> List[Dict]:
        """
        Get batches of high-priority products
        
        Criteria:
        - Has active deals
        - High check_priority (>= 80)
        - Not checked in last hour
        
        Returns:
            List of batch dicts with product_ids
        """
        logger.info("Fetching high-priority product batches")
        
        with get_db() as db:
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            
            # Get products with active deals
            deal_products = db.query(Product.id).join(Deal).filter(
                Deal.is_active == True,
                Product.is_available == True,
                Product.last_checked_at < cutoff_time
            ).limit(limit).all()
            
            # Get high priority products (not in deals)
            high_priority = db.query(Product.id).filter(
                Product.check_priority >= 80,
                Product.is_available == True,
                Product.last_checked_at < cutoff_time,
                ~Product.id.in_([p.id for p in deal_products])
            ).limit(limit - len(deal_products)).all()
            
            # Combine
            product_ids = [p.id for p in deal_products] + [p.id for p in high_priority]
            
            logger.info(f"Found {len(product_ids)} high-priority products")
            
            # Split into batches
            return self._create_batches(product_ids)
    
    def get_medium_priority_batches(self, limit: int = 50000) -> List[Dict]:
        """
        Get batches of medium-priority products
        
        Criteria:
        - check_priority 40-79
        - Not checked in last 6 hours
        
        Returns:
            List of batch dicts with product_ids
        """
        logger.info("Fetching medium-priority product batches")
        
        with get_db() as db:
            cutoff_time = datetime.utcnow() - timedelta(hours=6)
            
            products = db.query(Product.id).filter(
                Product.check_priority >= 40,
                Product.check_priority < 80,
                Product.is_available == True,
                Product.last_checked_at < cutoff_time
            ).limit(limit).all()
            
            product_ids = [p.id for p in products]
            logger.info(f"Found {len(product_ids)} medium-priority products")
            
            return self._create_batches(product_ids)
    
    def get_low_priority_batches(self, limit: int = 100000) -> List[Dict]:
        """
        Get batches of low-priority products
        
        Criteria:
        - check_priority < 40
        - Not checked in last 24 hours
        
        Returns:
            List of batch dicts with product_ids
        """
        logger.info("Fetching low-priority product batches")
        
        with get_db() as db:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            products = db.query(Product.id).filter(
                Product.check_priority < 40,
                Product.is_available == True,
                Product.last_checked_at < cutoff_time
            ).limit(limit).all()
            
            product_ids = [p.id for p in products]
            logger.info(f"Found {len(product_ids)} low-priority products")
            
            return self._create_batches(product_ids)
    
    def get_never_checked_batches(self, limit: int = 10000) -> List[Dict]:
        """
        Get batches of products that have never been checked
        
        Returns:
            List of batch dicts with product_ids
        """
        logger.info("Fetching never-checked products")
        
        with get_db() as db:
            products = db.query(Product.id).filter(
                Product.last_checked_at == None,
                Product.is_available == True
            ).limit(limit).all()
            
            product_ids = [p.id for p in products]
            logger.info(f"Found {len(product_ids)} never-checked products")
            
            return self._create_batches(product_ids)
    
    def get_overdue_batches(self, hours_overdue: int = 48) -> List[Dict]:
        """
        Get batches of products that are overdue for checking
        
        Args:
            hours_overdue: Hours since last check
        
        Returns:
            List of batch dicts with product_ids
        """
        logger.info(f"Fetching products overdue by {hours_overdue}+ hours")
        
        with get_db() as db:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_overdue)
            
            products = db.query(Product.id).filter(
                Product.last_checked_at < cutoff_time,
                Product.is_available == True
            ).order_by(Product.last_checked_at).limit(50000).all()
            
            product_ids = [p.id for p in products]
            logger.info(f"Found {len(product_ids)} overdue products")
            
            return self._create_batches(product_ids)
    
    def _create_batches(self, product_ids: List[int]) -> List[Dict]:
        """
        Split product IDs into batches
        
        Args:
            product_ids: List of product IDs
        
        Returns:
            List of batch dicts
        """
        batches = []
        
        for i in range(0, len(product_ids), self.batch_size):
            batch_ids = product_ids[i:i + self.batch_size]
            batches.append({
                'product_ids': batch_ids,
                'size': len(batch_ids),
                'batch_number': i // self.batch_size + 1
            })
        
        return batches
    
    def get_statistics(self) -> Dict:
        """
        Get current statistics for monitoring
        
        Returns:
            Stats dict
        """
        with get_db() as db:
            total = db.query(Product).count()
            available = db.query(Product).filter(Product.is_available == True).count()
            
            # Priority distribution
            high_priority = db.query(Product).filter(Product.check_priority >= 80).count()
            medium_priority = db.query(Product).filter(
                Product.check_priority >= 40,
                Product.check_priority < 80
            ).count()
            low_priority = db.query(Product).filter(Product.check_priority < 40).count()
            
            # Check status
            never_checked = db.query(Product).filter(Product.last_checked_at == None).count()
            
            checked_1h = db.query(Product).filter(
                Product.last_checked_at >= datetime.utcnow() - timedelta(hours=1)
            ).count()
            
            checked_6h = db.query(Product).filter(
                Product.last_checked_at >= datetime.utcnow() - timedelta(hours=6),
                Product.last_checked_at < datetime.utcnow() - timedelta(hours=1)
            ).count()
            
            checked_24h = db.query(Product).filter(
                Product.last_checked_at >= datetime.utcnow() - timedelta(hours=24),
                Product.last_checked_at < datetime.utcnow() - timedelta(hours=6)
            ).count()
            
            overdue_24h = db.query(Product).filter(
                Product.last_checked_at < datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            # Active deals
            active_deals = db.query(Deal).filter(Deal.is_active == True).count()
            
            return {
                "total_products": total,
                "available_products": available,
                "priority_distribution": {
                    "high": high_priority,
                    "medium": medium_priority,
                    "low": low_priority
                },
                "check_status": {
                    "never_checked": never_checked,
                    "checked_last_hour": checked_1h,
                    "checked_last_6h": checked_6h,
                    "checked_last_24h": checked_24h,
                    "overdue_24h+": overdue_24h
                },
                "active_deals": active_deals
            }
