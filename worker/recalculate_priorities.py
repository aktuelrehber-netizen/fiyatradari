"""
Recalculate priority for all products
Run this script to update priorities with the new algorithm
"""
from loguru import logger
from database import get_db, Product
from services.priority_calculator import PriorityCalculator

def recalculate_all_priorities():
    """Recalculate priority for all active products"""
    calculator = PriorityCalculator()
    
    with get_db() as db:
        products = db.query(Product).filter(Product.is_active == True).all()
        total = len(products)
        updated = 0
        
        logger.info(f"Starting priority recalculation for {total} products")
        
        for i, product in enumerate(products, 1):
            try:
                old_priority = product.check_priority
                new_priority = calculator.calculate_priority(product, db)
                
                if old_priority != new_priority:
                    product.check_priority = new_priority
                    updated += 1
                    
                    if updated % 100 == 0:
                        logger.info(f"Progress: {i}/{total} - Updated: {updated}")
                        db.commit()
                
            except Exception as e:
                logger.error(f"Error calculating priority for product {product.id}: {e}")
                continue
        
        db.commit()
        logger.success(f"✅ Priority recalculation complete!")
        logger.info(f"Total products: {total}")
        logger.info(f"Updated: {updated}")
        
        # Show new distribution
        high = db.query(Product).filter(Product.is_active == True, Product.check_priority >= 70).count()
        medium = db.query(Product).filter(Product.is_active == True, Product.check_priority >= 40, Product.check_priority < 70).count()
        low = db.query(Product).filter(Product.is_active == True, Product.check_priority < 40).count()
        
        logger.info(f"New distribution:")
        logger.info(f"  High (≥70): {high} products")
        logger.info(f"  Medium (40-69): {medium} products")
        logger.info(f"  Low (<40): {low} products")

if __name__ == "__main__":
    recalculate_all_priorities()
