"""
Celery background tasks
"""
from datetime import datetime, timedelta
from typing import Dict, Any
from celery import Task
from celery.utils.log import get_task_logger

from app.celery_app import celery_app
from app.db.database import SessionLocal
from app.db import models

logger = get_task_logger(__name__)


class DatabaseTask(Task):
    """Base task with database session"""
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(bind=True, base=DatabaseTask, name='app.tasks.check_categories_for_update')
def check_categories_for_update(self):
    """
    Günde 1 kere (20:00) çalışır, güncellenecek kategorileri bulur ve fetch task'ını başlatır.
    Manuel tetikleme de desteklenir.
    """
    logger.info("Checking categories for update...")
    
    now = datetime.now()
    categories_to_update = []
    
    # Tüm aktif kategorileri al
    categories = self.db.query(models.Category).filter(
        models.Category.is_active == True
    ).all()
    
    for category in categories:
        # Browse node'u yoksa skip
        if not category.amazon_browse_node_ids or len(category.amazon_browse_node_ids) == 0:
            continue
        
        # Güncellenecek mi kontrol et
        should_update = False
        
        if not category.last_checked_at:
            # Hiç çekilmemiş
            should_update = True
            logger.info(f"Category {category.id} ({category.name}) - Never checked before")
        else:
            # Son kontrolden bu yana geçen süre
            hours_passed = (now - category.last_checked_at).total_seconds() / 3600
            check_interval = category.check_interval_hours or 6
            
            if hours_passed >= check_interval:
                should_update = True
                logger.info(
                    f"Category {category.id} ({category.name}) - "
                    f"{hours_passed:.1f} hours passed (interval: {check_interval}h)"
                )
        
        if should_update:
            categories_to_update.append(category.id)
            # Background task'ı başlat
            fetch_category_products_async.delay(category.id)
    
    logger.info(f"Started fetch tasks for {len(categories_to_update)} categories: {categories_to_update}")
    
    return {
        "checked_categories": len(categories),
        "started_tasks": len(categories_to_update),
        "category_ids": categories_to_update
    }


@celery_app.task(bind=True, base=DatabaseTask, name='app.tasks.fetch_category_products_async')
def fetch_category_products_async(self, category_id: int):
    """
    Kategori için ürün çekme - Background task
    """
    logger.info(f"Starting product fetch for category {category_id}")
    
    try:
        # Import here to avoid circular dependency
        from app.api.products_fetch import fetch_category_products_logic
        
        result = fetch_category_products_logic(category_id, self.db)
        
        logger.info(
            f"Category {category_id} fetch completed: "
            f"{result['products_created']} created, "
            f"{result['products_updated']} updated, "
            f"{result['deals_created']} deals created"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching products for category {category_id}: {str(e)}")
        raise


@celery_app.task(bind=True, base=DatabaseTask, name='app.tasks.update_statistics')
def update_statistics(self):
    """
    İstatistikleri güncelle (dashboard için)
    """
    logger.info("Updating statistics...")
    
    stats = {
        "total_products": self.db.query(models.Product).count(),
        "active_products": self.db.query(models.Product).filter(
            models.Product.is_active == True
        ).count(),
        "total_deals": self.db.query(models.Deal).count(),
        "active_deals": self.db.query(models.Deal).filter(
            models.Deal.is_active == True
        ).count(),
        "published_deals": self.db.query(models.Deal).filter(
            models.Deal.is_published == True
        ).count(),
        "total_categories": self.db.query(models.Category).count(),
        "active_categories": self.db.query(models.Category).filter(
            models.Category.is_active == True
        ).count(),
    }
    
    logger.info(f"Statistics updated: {stats}")
    return stats


@celery_app.task(bind=True, base=DatabaseTask, name='app.tasks.cleanup_old_deals')
def cleanup_old_deals(self):
    """
    Eski ve geçersiz deal'leri temizle
    """
    logger.info("Cleaning up old deals...")
    
    now = datetime.now()
    
    # 30 günden eski, aktif olmayan deal'leri sil
    threshold = now - timedelta(days=30)
    
    old_deals = self.db.query(models.Deal).filter(
        models.Deal.is_active == False,
        models.Deal.created_at < threshold
    ).all()
    
    deleted_count = len(old_deals)
    
    for deal in old_deals:
        self.db.delete(deal)
    
    self.db.commit()
    
    logger.info(f"Deleted {deleted_count} old deals")
    
    return {
        "deleted_deals": deleted_count,
        "threshold_date": threshold.isoformat()
    }


@celery_app.task(bind=True, base=DatabaseTask, name='app.tasks.check_deal_prices')
def check_deal_prices(self):
    """
    Aktif deal'lerin fiyatlarını kontrol et, artış varsa deaktive et
    """
    logger.info("Checking active deal prices...")
    
    active_deals = self.db.query(models.Deal).filter(
        models.Deal.is_active == True
    ).all()
    
    deactivated = 0
    
    for deal in active_deals:
        product = deal.product
        
        if not product or not product.current_price:
            continue
        
        # Fiyat arttıysa deal'i deaktive et
        if float(product.current_price) > float(deal.deal_price):
            deal.is_active = False
            deactivated += 1
            logger.info(
                f"Deal {deal.id} deactivated - "
                f"Price increased from {deal.deal_price} to {product.current_price}"
            )
    
    self.db.commit()
    
    logger.info(f"Checked {len(active_deals)} deals, deactivated {deactivated}")
    
    return {
        "checked_deals": len(active_deals),
        "deactivated_deals": deactivated
    }


@celery_app.task(bind=True, base=DatabaseTask, name='app.tasks.update_product_prices_batch')
def update_product_prices_batch(self):
    """
    Database'deki aktif ürünlerin fiyat, stok, rating bilgilerini güncelle
    Son 30 dakika içinde güncellenmemiş ürünleri seç ve 10'arlı batch'lerle Amazon'dan çek
    """
    logger.info("Starting batch product price update...")
    
    now = datetime.now()
    threshold = now - timedelta(minutes=30)
    
    # Son 30 dakika içinde güncellenmemiş aktif ürünleri al
    products = self.db.query(models.Product).filter(
        models.Product.is_active == True,
        models.Product.last_checked_at < threshold
    ).order_by(
        models.Product.last_checked_at.asc()
    ).limit(500).all()  # Her çalıştırmada max 500 ürün
    
    if not products:
        logger.info("No products to update")
        return {
            "total_products": 0,
            "updated_products": 0,
            "failed_products": 0,
            "deals_created": 0,
            "deals_updated": 0
        }
    
    logger.info(f"Found {len(products)} products to update")
    
    # Amazon API credentials
    access_key_setting = self.db.query(models.SystemSetting).filter(
        models.SystemSetting.key == "amazon_access_key"
    ).first()
    
    secret_key_setting = self.db.query(models.SystemSetting).filter(
        models.SystemSetting.key == "amazon_secret_key"
    ).first()
    
    partner_tag_setting = self.db.query(models.SystemSetting).filter(
        models.SystemSetting.key == "amazon_partner_tag"
    ).first()
    
    if not access_key_setting or not secret_key_setting or not partner_tag_setting:
        logger.error("Amazon PA API credentials not configured")
        return {"error": "Amazon PA API credentials not configured"}
    
    if not access_key_setting.value or not secret_key_setting.value or not partner_tag_setting.value:
        logger.error("Amazon PA API credentials are empty")
        return {"error": "Amazon PA API credentials are empty"}
    
    # Import Amazon PA API
    try:
        from amazon_paapi import AmazonApi
        import time
    except ImportError as e:
        logger.error(f"Amazon PA API library not installed: {e}")
        return {"error": "Amazon PA API library not installed"}
    
    # Initialize Amazon PA API
    # NOT: resources parametresini kullanmayalım, SDK otomatik handle eder
    amazon = AmazonApi(
        key=access_key_setting.value,
        secret=secret_key_setting.value,
        tag=partner_tag_setting.value,
        country='TR',
        throttling=1.0
    )
    
    stats = {
        "total_products": len(products),
        "updated_products": 0,
        "failed_products": 0,
        "deals_created": 0,
        "deals_updated": 0
    }
    
    # ASIN'leri al
    asins = [p.asin for p in products]
    product_map = {p.asin: p for p in products}
    
    # 10'arlı batch'lere böl
    for i in range(0, len(asins), 10):
        batch_asins = asins[i:i+10]
        
        try:
            # Amazon'dan bilgileri çek
            items = amazon.get_items(items=batch_asins)
            
            if not items:
                logger.warning(f"No items returned for batch {i//10 + 1}")
                stats["failed_products"] += len(batch_asins)
                continue
            
            # Her item'i işle
            for item in items:
                try:
                    product = product_map.get(item.asin)
                    if not product:
                        continue
                    
                    # Amazon item'ını parse et
                    from app.api.products_fetch import parse_amazon_item
                    amazon_data = parse_amazon_item(item)
                    
                    # Ürünü güncelle
                    result = update_product_from_amazon(
                        product=product,
                        amazon_data=amazon_data,
                        db=self.db
                    )
                    
                    if result["updated"]:
                        stats["updated_products"] += 1
                    
                    if result["deal_created"]:
                        stats["deals_created"] += 1
                    elif result["deal_updated"]:
                        stats["deals_updated"] += 1
                    
                except Exception as e:
                    # Use self.app.log for logging inside task
                    print(f"Error processing item {item.asin}: {str(e)}")
                    stats["failed_products"] += 1
            
            # Commit after each batch
            self.db.commit()
            
            # Rate limiting between batches
            if i + 10 < len(asins):
                time.sleep(1)
                
        except Exception as e:
            print(f"Error processing batch {i//10 + 1}: {str(e)}")
            stats["failed_products"] += len(batch_asins)
            continue
    
    logger.info(
        f"Batch update completed: {stats['updated_products']}/{stats['total_products']} updated, "
        f"{stats['deals_created']} deals created, {stats['deals_updated']} deals updated"
    )
    
    return stats


def update_product_from_amazon(product: models.Product, amazon_data: Dict[str, Any], db) -> Dict[str, Any]:
    """
    Amazon'dan çekilen verilerle ürünü güncelle ve deal detection yap
    """
    from decimal import Decimal
    from app.api.products_fetch import add_price_history, check_and_create_deal
    
    new_price = amazon_data.get("current_price")
    
    if not new_price:
        # Fiyat yoksa stok durumunu güncelle ve timestamp
        product.availability = amazon_data.get("availability")
        product.is_available = amazon_data.get("is_available", False)
        product.last_checked_at = datetime.now()
        return {"updated": False, "deal_created": False, "deal_updated": False}
    
    # Eski fiyat
    old_price = float(product.current_price) if product.current_price else None
    price_changed = old_price != new_price
    
    # Ürün bilgilerini güncelle
    product.title = amazon_data.get("title") or product.title
    product.brand = amazon_data.get("brand") or product.brand
    product.current_price = Decimal(str(new_price))
    
    # List price güvenli parse
    list_price_value = amazon_data.get("list_price")
    if list_price_value:
        try:
            product.list_price = Decimal(str(list_price_value))
        except (ValueError, TypeError):
            product.list_price = Decimal(str(new_price))
    else:
        product.list_price = Decimal(str(new_price))
    
    product.image_url = amazon_data.get("image_url") or product.image_url
    product.detail_page_url = amazon_data.get("detail_page_url") or product.detail_page_url
    product.availability = amazon_data.get("availability")
    # is_available: Eğer Amazon'dan bilgi gelmezse False (stok dışı kabul et)
    product.is_available = amazon_data.get("is_available", False)
    
    # Rating güvenli parse
    rating_value = amazon_data.get("rating")
    if rating_value:
        try:
            product.rating = float(rating_value)
        except (ValueError, TypeError):
            product.rating = None
    else:
        product.rating = None
    
    # Review count güvenli parse
    review_count_value = amazon_data.get("review_count")
    if review_count_value:
        try:
            product.review_count = int(review_count_value)
        except (ValueError, TypeError):
            product.review_count = None
    else:
        product.review_count = None
    
    product.ean = amazon_data.get("ean") or product.ean
    product.last_checked_at = datetime.now()
    
    # Fiyat geçmişi mantığı
    if price_changed:
        # Fiyat değişti → Yeni kayıt ekle
        add_price_history(product, new_price, amazon_data.get("list_price"), db)
    else:
        # Fiyat aynı → Bugün kayıt var mı kontrol et (günlük snapshot)
        from app.api.products_fetch import get_last_price_record
        last_record = get_last_price_record(product.id, db)
        if last_record:
            today = datetime.now().date()
            last_date = last_record.recorded_at.date()
            
            if last_date < today:
                # Bugün kayıt yok → Günlük snapshot ekle
                add_price_history(product, new_price, amazon_data.get("list_price"), db)
        else:
            # İlk kayıt
            add_price_history(product, new_price, amazon_data.get("list_price"), db)
    
    # Deal detection
    category = product.category
    deal_result = check_and_create_deal(product, category, db)
    
    return {
        "updated": True,
        "deal_created": deal_result["action"] == "created",
        "deal_updated": deal_result["action"] == "updated"
    }
