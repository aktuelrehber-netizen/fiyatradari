"""
Background task to update Prometheus metrics
"""
import asyncio
from sqlalchemy import func
from app.db.database import SessionLocal
from app.db import models
from app.core.monitoring import products_total, deals_total
import logging

logger = logging.getLogger(__name__)


async def update_business_metrics():
    """Update business metrics (products, deals count)"""
    while True:
        try:
            db = SessionLocal()
            
            # Update products count
            total_products = db.query(func.count(models.Product.id)).scalar() or 0
            products_total.set(total_products)
            
            # Update active deals count
            total_deals = db.query(func.count(models.Deal.id)).filter(
                models.Deal.is_active == True
            ).scalar() or 0
            deals_total.set(total_deals)
            
            logger.debug(f"📊 Metrics updated - Products: {total_products}, Deals: {total_deals}")
            
            db.close()
            
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
        
        # Update every 60 seconds
        await asyncio.sleep(60)
