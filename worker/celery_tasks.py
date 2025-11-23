"""
Celery Tasks for Distributed Processing
Individual tasks for 1M+ product handling
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
from loguru import logger
from celery import group, chord, chain
from sqlalchemy import or_

from celery_app import app
from database import get_db, Product, PriceHistory, Deal, WorkerLog, Category
from services.amazon_client import AmazonPAAPIClient
from services.deal_detector import DealDetector
from config import config
from worker_control import WorkerControl

# Initialize worker control
worker_control = WorkerControl()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _calculate_celery_priority(product_priority: int) -> int:
    """
    Map product priority score (0-100) to Celery priority (1-10)
    
    More granular mapping for better queue management:
    - 90-100: Priority 10 (Critical - new deals, hot items)
    - 80-89:  Priority 9  (Very High)
    - 70-79:  Priority 8  (High)
    - 60-69:  Priority 7  (Above Medium)
    - 50-59:  Priority 6  (Medium-High)
    - 40-49:  Priority 5  (Medium)
    - 30-39:  Priority 4  (Below Medium)
    - 20-29:  Priority 3  (Low-Medium)
    - 10-19:  Priority 2  (Low)
    - 0-9:    Priority 1  (Very Low)
    """
    if product_priority >= 90:
        return 10
    elif product_priority >= 80:
        return 9
    elif product_priority >= 70:
        return 8
    elif product_priority >= 60:
        return 7
    elif product_priority >= 50:
        return 6
    elif product_priority >= 40:
        return 5
    elif product_priority >= 30:
        return 4
    elif product_priority >= 20:
        return 3
    elif product_priority >= 10:
        return 2
    else:
        return 1


# ============================================================================
# INDIVIDUAL PRODUCT TASKS
# ============================================================================

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def check_product_price(self, product_id: int, priority: int = 5) -> Dict:
    """
    Check price for a single product
    
    Args:
        product_id: Product ID to check
        priority: Task priority (0-10, higher = more important)
    
    Returns:
        Result dict with status and metrics
    """
    try:
        import asyncio
        from services.amazon_crawler import AmazonCrawler
        
        deal_detector = DealDetector(deal_threshold_percentage=config.DEAL_THRESHOLD_PERCENTAGE)
        
        with get_db() as db:
            # Get product
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                logger.warning(f"Product {product_id} not found")
                return {"status": "not_found", "product_id": product_id}
            
            # Fetch current price from Amazon using crawler
            crawler = AmazonCrawler(use_proxies=True)
            
            async def crawl():
                return await crawler.get_product_async(product.asin)
            
            item_data = asyncio.run(crawl())
            
            if not item_data:
                logger.warning(f"No data from Amazon for {product.asin}")
                product.last_checked_at = datetime.utcnow()
                product.check_count = (product.check_count or 0) + 1
                db.commit()
                return {"status": "no_data", "product_id": product_id, "asin": product.asin}
            old_price = product.current_price
            new_price = Decimal(str(item_data['current_price'])) if item_data.get('current_price') else None
            
            if not new_price:
                product.is_available = False
                product.last_checked_at = datetime.utcnow()
                product.check_count = (product.check_count or 0) + 1
                db.commit()
                return {"status": "unavailable", "product_id": product_id, "asin": product.asin}
            
            # Update product (including rating and review_count from crawler-burasi)
            product.current_price = new_price
            product.rating = item_data.get('rating', product.rating)
            product.review_count = item_data.get('review_count', product.review_count)
            product.is_available = item_data.get('is_available', True)
            product.last_checked_at = datetime.utcnow()
            product.check_count = (product.check_count or 0) + 1
            
            # Track price change and record history
            price_changed = False
            should_record_history = False
            
            # Check if price changed
            if old_price and abs(new_price - old_price) > Decimal('0.01'):
                price_changed = True
                should_record_history = True
                change_pct = float((new_price - old_price) / old_price * 100)
                logger.info(f"Price changed for {product.asin}: {old_price} -> {new_price} ({change_pct:+.1f}%)")
            else:
                # Check if we should record daily snapshot (even if price didn't change)
                last_history = db.query(PriceHistory).filter(
                    PriceHistory.product_id == product.id
                ).order_by(PriceHistory.recorded_at.desc()).first()
                
                if not last_history:
                    should_record_history = True  # First record
                elif last_history.recorded_at.date() < datetime.utcnow().date():
                    should_record_history = True  # New day, record daily snapshot
            
            # Record price history
            if should_record_history:
                history = PriceHistory(
                    product_id=product.id,
                    price=new_price,
                    is_available=product.is_available,
                    recorded_at=datetime.utcnow()
                )
                db.add(history)
                
                if not price_changed:
                    logger.debug(f"Daily price snapshot for {product.asin}: {new_price}")
            
            # Check for deals
            is_deal, deal_info = deal_detector.analyze_product(product, db)
            deal_created = False
            
            if is_deal:
                created, deal = deal_detector.create_or_update_deal(product, deal_info, db)
                deal_created = created
                deal_id_for_notification = deal.id if created else None
                if created:
                    logger.success(f"New deal created for {product.asin}: {deal_info['discount_vs_avg']:.1f}% off")
            
            db.commit()
            
            # Send Telegram notification immediately for new deals (after commit)
            if deal_created and deal_id_for_notification:
                try:
                    app.send_task('celery_tasks.send_deal_notification', args=[deal_id_for_notification], countdown=5)
                    logger.info(f"Telegram notification scheduled for deal {deal_id_for_notification}")
                except Exception as e:
                    logger.warning(f"Could not schedule telegram notification: {e}")
            
            return {
                "status": "success",
                "product_id": product_id,
                "asin": product.asin,
                "old_price": float(old_price) if old_price else None,
                "new_price": float(new_price),
                "price_changed": price_changed,
                "deal_created": deal_created,
                "is_deal": is_deal
            }
            
    except Exception as e:
        logger.error(f"Error checking product {product_id}: {e}")
        raise self.retry(exc=e)


@app.task(bind=True, max_retries=2)
def fetch_category_products(self, category_id: int, browse_node_id: str, page: int = 1) -> Dict:
    """
    Fetch products from Amazon for a category
    
    Args:
        category_id: Category ID
        browse_node_id: Amazon browse node ID
        page: Page number
    """
    try:
        amazon_client = AmazonPAAPIClient()
        
        with get_db() as db:
            category = db.query(Category).filter(Category.id == category_id).first()
            if not category or not category.is_active:
                return {"status": "category_not_active", "category_id": category_id}
            
            # Fetch products from Amazon
            # Selection rules are now applied by Amazon API (server-side)
            # Only client-side filters (keywords, review_count) are applied after
            items = amazon_client.search_items_by_browse_node(
                browse_node_id=browse_node_id,
                page=page,
                items_per_page=10,
                selection_rules=category.selection_rules
            )
            
            items_created = 0
            items_updated = 0
            
            for item_data in items:
                asin = item_data.get('asin')
                if not asin:
                    continue
                
                # Check if product exists
                product = db.query(Product).filter(Product.asin == asin).first()
                
                if product:
                    # Update existing
                    product.current_price = Decimal(str(item_data['current_price'])) if item_data.get('current_price') else None
                    product.is_available = item_data.get('is_available', True)
                    product.rating = item_data.get('rating')
                    product.review_count = item_data.get('review_count')
                    product.last_checked_at = datetime.utcnow()
                    items_updated += 1
                else:
                    # Create new
                    product = Product(
                        asin=asin,
                        title=item_data.get('title', '')[:500],
                        brand=item_data.get('brand'),
                        current_price=Decimal(str(item_data['current_price'])) if item_data.get('current_price') else None,
                        currency=item_data.get('currency', 'TRY'),
                        image_url=item_data.get('image_url'),
                        rating=item_data.get('rating'),
                        review_count=item_data.get('review_count'),
                        is_available=item_data.get('is_available', True),
                        category_id=category_id,
                        amazon_data=item_data,
                        last_checked_at=datetime.utcnow()
                    )
                    db.add(product)
                    items_created += 1
            
            db.commit()
            
            return {
                "status": "success",
                "category_id": category_id,
                "page": page,
                "items_created": items_created,
                "items_updated": items_updated
            }
            
    except Exception as e:
        logger.error(f"Error fetching category {category_id} products: {e}")
        raise self.retry(exc=e)


@app.task(bind=True, max_retries=3)
def send_deal_notification(self, deal_id: int) -> Dict:
    """
    Send Telegram notification for a deal
    
    Args:
        deal_id: Deal ID
    """
    try:
        from jobs.telegram_sender import TelegramSender
        
        with get_db() as db:
            deal = db.query(Deal).filter(Deal.id == deal_id).first()
            if not deal:
                return {"status": "not_found", "deal_id": deal_id}
            
            if deal.telegram_sent:
                return {"status": "already_sent", "deal_id": deal_id}
            
            # Send notification
            telegram_sender = TelegramSender()
            if not telegram_sender.enabled:
                return {"status": "telegram_not_configured", "deal_id": deal_id}
            
            # Get product
            product = deal.product
            if not product:
                return {"status": "product_not_found", "deal_id": deal_id}
            
            # Send
            success = telegram_sender._send_deal(deal, db)
            
            if success:
                deal.telegram_sent = True
                deal.telegram_sent_at = datetime.utcnow()
                db.commit()
                return {"status": "success", "deal_id": deal_id}
            else:
                return {"status": "failed", "deal_id": deal_id}
                
    except Exception as e:
        logger.error(f"Error sending notification for deal {deal_id}: {e}")
        raise self.retry(exc=e)


# ============================================================================
# BATCH PROCESSING TASKS
# ============================================================================

@app.task
def batch_price_check(product_ids: List[int], priority: int = 5) -> Dict:
    """
    Check prices for a batch of products (dispatch individual tasks)
    
    Args:
        product_ids: List of product IDs
        priority: Task priority
    """
    logger.info(f"Dispatching price checks for {len(product_ids)} products (priority: {priority})")
    
    # Create individual tasks with priority
    job = group(
        check_product_price.s(product_id, priority=priority) 
        for product_id in product_ids
    )
    
    result = job.apply_async()
    
    return {
        "status": "dispatched",
        "product_count": len(product_ids),
        "priority": priority,
        "group_id": result.id
    }


# ============================================================================
# SCHEDULING TASKS (Called by Celery Beat)
# ============================================================================

@app.task
def continuous_queue_refill() -> Dict:
    """
    Continuously refill the queue with products to check
    Called every 3 minutes by Celery Beat
    
    Uses dynamic priority mapping with flexible intervals
    """
    # Check if job should run
    if not worker_control.should_run_job('check_prices'):
        logger.warning("Price check job is disabled or scheduler is paused")
        return {"status": "skipped", "reason": "Job disabled or scheduler paused"}
    
    try:
        with get_db() as db:
            # Critical priority (90-100): Check every 15 minutes
            critical_products = db.query(Product).filter(
                Product.is_active == True,
                Product.check_priority >= 90,
                or_(
                    Product.last_checked_at == None,
                    Product.last_checked_at < datetime.utcnow() - timedelta(minutes=15)
                )
            ).limit(200).all()
            
            # Very High priority (80-89): Check every 30 minutes
            very_high_products = db.query(Product).filter(
                Product.is_active == True,
                Product.check_priority >= 80,
                Product.check_priority < 90,
                or_(
                    Product.last_checked_at == None,
                    Product.last_checked_at < datetime.utcnow() - timedelta(minutes=30)
                )
            ).limit(300).all()
            
            # High priority (70-79): Check every hour
            high_priority_products = db.query(Product).filter(
                Product.is_active == True,
                Product.check_priority >= 70,
                Product.check_priority < 80,
                or_(
                    Product.last_checked_at == None,
                    Product.last_checked_at < datetime.utcnow() - timedelta(hours=1)
                )
            ).limit(400).all()
            
            # Medium-High (50-69): Check every 2 hours
            medium_high_products = db.query(Product).filter(
                Product.is_active == True,
                Product.check_priority >= 50,
                Product.check_priority < 70,
                or_(
                    Product.last_checked_at == None,
                    Product.last_checked_at < datetime.utcnow() - timedelta(hours=2)
                )
            ).limit(500).all()
            
            # Medium (30-49): Check every 4 hours
            medium_priority_products = db.query(Product).filter(
                Product.is_active == True,
                Product.check_priority >= 30,
                Product.check_priority < 50,
                or_(
                    Product.last_checked_at == None,
                    Product.last_checked_at < datetime.utcnow() - timedelta(hours=4)
                )
            ).limit(600).all()
            
            # Low priority (<30): Check every 8 hours
            low_priority_products = db.query(Product).filter(
                Product.is_active == True,
                Product.check_priority < 30,
                or_(
                    Product.last_checked_at == None,
                    Product.last_checked_at < datetime.utcnow() - timedelta(hours=8)
                )
            ).limit(800).all()
            
            total_queued = 0
            priority_distribution = {10: 0, 9: 0, 8: 0, 7: 0, 6: 0, 5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
            
            # Queue all products with dynamic priority
            all_products = (critical_products + very_high_products + high_priority_products + 
                          medium_high_products + medium_priority_products + low_priority_products)
            
            for product in all_products:
                celery_priority = _calculate_celery_priority(product.check_priority)
                check_product_price.apply_async(
                    args=[product.id, product.check_priority],
                    priority=celery_priority
                )
                priority_distribution[celery_priority] += 1
                total_queued += 1
            
            logger.info(f"Queue refilled: {total_queued} total products")
            logger.info(f"Priority distribution: {priority_distribution}")
            
            return {
                "status": "success",
                "critical": len(critical_products),
                "very_high": len(very_high_products),
                "high": len(high_priority_products),
                "medium_high": len(medium_high_products),
                "medium": len(medium_priority_products),
                "low": len(low_priority_products),
                "total_queued": total_queued,
                "priority_distribution": priority_distribution
            }
            
    except Exception as e:
        logger.error(f"Error in continuous queue refill: {e}")
        return {"status": "error", "error": str(e)}


@app.task
def schedule_high_priority_checks() -> Dict:
    """
    Schedule price checks for high-priority products
    Called every hour by Celery Beat
    """
    logger.info("Scheduling high-priority product checks")
    
    from services.smart_batch_processor import SmartBatchProcessor
    batch_processor = SmartBatchProcessor()
    batches = batch_processor.get_high_priority_batches()
    
    tasks_dispatched = 0
    for batch in batches:
        batch_price_check.apply_async(
            args=[batch['product_ids']],
            kwargs={'priority': 10},
            priority=10
        )
        tasks_dispatched += len(batch['product_ids'])
    
    logger.info(f"Dispatched {tasks_dispatched} high-priority checks")
    return {"status": "success", "tasks_dispatched": tasks_dispatched}


@app.task
def schedule_medium_priority_checks() -> Dict:
    """
    Schedule price checks for medium-priority products
    Called every 6 hours by Celery Beat
    """
    logger.info("Scheduling medium-priority product checks")
    
    from services.smart_batch_processor import SmartBatchProcessor
    batch_processor = SmartBatchProcessor()
    batches = batch_processor.get_medium_priority_batches()
    
    tasks_dispatched = 0
    for batch in batches:
        batch_price_check.apply_async(
            args=[batch['product_ids']],
            kwargs={'priority': 5},
            priority=5
        )
        tasks_dispatched += len(batch['product_ids'])
    
    logger.info(f"Dispatched {tasks_dispatched} medium-priority checks")
    return {"status": "success", "tasks_dispatched": tasks_dispatched}


@app.task
def schedule_low_priority_checks() -> Dict:
    """
    Schedule price checks for low-priority products
    Called daily by Celery Beat
    """
    logger.info("Scheduling low-priority product checks")
    
    from services.smart_batch_processor import SmartBatchProcessor
    batch_processor = SmartBatchProcessor()
    batches = batch_processor.get_low_priority_batches()
    
    tasks_dispatched = 0
    for batch in batches:
        batch_price_check.apply_async(
            args=[batch['product_ids']],
            kwargs={'priority': 1},
            priority=1
        )
        tasks_dispatched += len(batch['product_ids'])
    
    logger.info(f"Dispatched {tasks_dispatched} low-priority checks")
    return {"status": "success", "tasks_dispatched": tasks_dispatched}


@app.task
def schedule_product_fetch() -> Dict:
    """
    Schedule product fetching from Amazon
    Called daily by Celery Beat
    """
    # Check if job should run
    if not worker_control.should_run_job('fetch_products'):
        logger.warning("Product fetch job is disabled or scheduler is paused")
        return {"status": "skipped", "reason": "Job disabled or scheduler paused"}
    
    logger.info("Scheduling product fetch")
    
    with get_db() as db:
        categories = db.query(Category).filter(Category.is_active == True).all()
        
        tasks_dispatched = 0
        for category in categories:
            if not category.amazon_browse_node_ids:
                continue
            
            for browse_node_id in category.amazon_browse_node_ids:
                if not browse_node_id or not isinstance(browse_node_id, str):
                    continue
                
                # Calculate pages based on max_products
                # Each page = 10 products
                # Amazon PA API limitation: max 10 pages per browse node
                max_products = category.max_products or 100
                max_pages = min((max_products // 10), 10)  # Max 10 pages per node (Amazon API limit)
                
                logger.info(f"Category '{category.name}': max_products={max_products}, fetching {max_pages} pages")
                
                for page in range(1, max_pages + 1):
                    fetch_category_products.apply_async(
                        args=[category.id, browse_node_id, page],
                        priority=3
                    )
                    tasks_dispatched += 1
        
        logger.info(f"Dispatched {tasks_dispatched} product fetch tasks")
        return {"status": "success", "tasks_dispatched": tasks_dispatched}


@app.task
def schedule_notifications() -> Dict:
    """
    Schedule Telegram notifications for new deals
    Called every 30 minutes by Celery Beat
    """
    # Check if job should run
    if not worker_control.should_run_job('send_telegram'):
        logger.warning("Telegram notification job is disabled or scheduler is paused")
        return {"status": "skipped", "reason": "Job disabled or scheduler paused"}
    
    logger.info("Scheduling deal notifications")
    
    with get_db() as db:
        # Get published deals not sent yet
        deals = db.query(Deal).filter(
            Deal.is_published == True,
            Deal.is_active == True,
            Deal.telegram_sent == False
        ).order_by(Deal.discount_percentage.desc()).limit(50).all()
        
        tasks_dispatched = 0
        for deal in deals:
            send_deal_notification.apply_async(
                args=[deal.id],
                priority=8
            )
            tasks_dispatched += 1
        
        logger.info(f"Dispatched {tasks_dispatched} notification tasks")
        return {"status": "success", "tasks_dispatched": tasks_dispatched}


@app.task
def update_product_priorities() -> Dict:
    """
    Update priority scores for all products
    Called every 4 hours by Celery Beat
    """
    logger.info("Updating product priorities")
    
    from services.priority_calculator import PriorityCalculator
    priority_calculator = PriorityCalculator()
    
    with get_db() as db:
        # Update priorities in batches
        offset = 0
        batch_size = 1000
        total_updated = 0
        
        while True:
            products = db.query(Product).offset(offset).limit(batch_size).all()
            if not products:
                break
            
            for product in products:
                priority = priority_calculator.calculate_priority(product, db)
                product.check_priority = priority
            
            db.commit()
            total_updated += len(products)
            offset += batch_size
            
            logger.info(f"Updated priorities for {total_updated} products")
        
        logger.info(f"Completed priority update for {total_updated} products")
        return {"status": "success", "products_updated": total_updated}


@app.task
def cleanup_old_data() -> Dict:
    """
    Cleanup old data (price history, logs, etc.)
    Called daily by Celery Beat
    """
    logger.info("Cleaning up old data")
    
    with get_db() as db:
        # Delete price history older than 90 days
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        deleted_history = db.query(PriceHistory).filter(
            PriceHistory.recorded_at < cutoff_date
        ).delete()
        
        # Delete worker logs older than 30 days
        log_cutoff = datetime.utcnow() - timedelta(days=30)
        deleted_logs = db.query(WorkerLog).filter(
            WorkerLog.created_at < log_cutoff
        ).delete()
        
        # Expire old inactive deals
        deal_cutoff = datetime.utcnow() - timedelta(days=7)
        expired_deals = db.query(Deal).filter(
            Deal.is_active == True,
            Deal.updated_at < deal_cutoff
        ).update({"is_active": False})
        
        db.commit()
        
        logger.info(f"Cleanup complete: {deleted_history} price records, {deleted_logs} logs, {expired_deals} deals expired")
        return {
            "status": "success",
            "price_history_deleted": deleted_history,
            "logs_deleted": deleted_logs,
            "deals_expired": expired_deals
        }


@app.task
def update_missing_ratings() -> Dict:
    """
    Update ratings for products missing rating data using web crawler
    Called daily by Celery Beat
    
    NOTE: Amazon PA-API doesn't return CustomerReviews data without special access.
    This task fills the gap by crawling Amazon.com.tr for rating/review data.
    """
    # Check if job should run
    if not worker_control.should_run_job('update_missing_ratings'):
        logger.warning("Update ratings job is disabled or scheduler is paused")
        return {"status": "skipped", "reason": "Job disabled or scheduler paused"}
    
    logger.info("Starting missing ratings update via crawler")
    
    from services.amazon_crawler import AmazonCrawler
    crawler = AmazonCrawler()
    
    with get_db() as db:
        # Get products without rating that are available
        # LIMIT reduced to 25 to avoid Amazon bot detection
        # At 5-8s per request, 25 products = 2-3 minutes (safe)
        # Full 743 products will be completed in ~30 days
        products_without_rating = db.query(Product).filter(
            Product.rating == None,
            Product.is_available == True,
            Product.is_active == True
        ).order_by(Product.created_at.desc()).limit(25).all()
        
        # Extract ASINs
        asins = [p.asin for p in products_without_rating]
        
        # Crawl all products concurrently (2 at a time with retry logic)
        # This will be 2x faster than sequential crawling
        crawled_products = crawler.get_products(asins)
        
        # Create ASIN -> data mapping for quick lookup
        crawled_map = {p['asin']: p for p in crawled_products}
        
        updated_count = 0
        failed_count = 0
        
        # Update database with crawled data
        for product in products_without_rating:
            crawled_data = crawled_map.get(product.asin)
            
            if crawled_data:
                # Update rating and review count
                if crawled_data.get('rating'):
                    product.rating = crawled_data['rating']
                    logger.info(f"✓ ASIN {product.asin}: Updated rating to {crawled_data['rating']}")
                
                if crawled_data.get('review_count'):
                    product.review_count = crawled_data['review_count']
                    logger.info(f"✓ ASIN {product.asin}: Updated review_count to {crawled_data['review_count']}")
                
                product.last_checked_at = datetime.utcnow()
                updated_count += 1
            else:
                failed_count += 1
                logger.warning(f"✗ ASIN {product.asin}: Crawler returned no data")
        
        db.commit()
        
        logger.info(f"Missing ratings update complete: {updated_count} updated, {failed_count} failed")
        return {
            "status": "success",
            "updated": updated_count,
            "failed": failed_count,
            "total_processed": len(products_without_rating)
        }
