"""
Products fetch endpoint - Amazon PA API ile ürün çekme
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from decimal import Decimal

from app.api.auth import get_current_user
from app.db import models
from app.db.database import get_db

router = APIRouter()


class FetchProductsResponse(BaseModel):
    """Ürün çekme işlemi sonuç"""
    category_id: int
    category_name: str
    nodes_processed: int
    total_found: int
    products_created: int
    products_updated: int
    products_skipped: int
    deals_created: int
    deals_updated: int
    duration_seconds: float


def fetch_category_products_logic(category_id: int, db: Session) -> Dict[str, Any]:
    """
    Kategori için ürün çekme mantığı (hem endpoint hem task için)
    """
    start_time = datetime.now()
    
    # Kategori kontrolü
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if not category.is_active:
        raise HTTPException(status_code=400, detail="Category is not active")
    
    if not category.amazon_browse_node_ids or len(category.amazon_browse_node_ids) == 0:
        raise HTTPException(status_code=400, detail="Category has no browse node IDs")
    
    # Amazon API credentials'ı settings'ten al
    access_key_setting = db.query(models.SystemSetting).filter(
        models.SystemSetting.key == "amazon_access_key"
    ).first()
    
    secret_key_setting = db.query(models.SystemSetting).filter(
        models.SystemSetting.key == "amazon_secret_key"
    ).first()
    
    partner_tag_setting = db.query(models.SystemSetting).filter(
        models.SystemSetting.key == "amazon_partner_tag"
    ).first()
    
    if not access_key_setting or not secret_key_setting or not partner_tag_setting:
        raise HTTPException(
            status_code=400, 
            detail="Amazon PA API credentials not configured in settings"
        )
    
    if not access_key_setting.value or not secret_key_setting.value or not partner_tag_setting.value:
        raise HTTPException(
            status_code=400, 
            detail="Amazon PA API credentials are empty"
        )
    
    # Import Amazon PA API
    try:
        from amazon_paapi import AmazonApi
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Amazon PA API library not installed"
        )
    
    # Initialize Amazon PA API
    # NOT: resources parametresini kullanmayalım, SDK otomatik tüm dataları çeker
    amazon = AmazonApi(
        key=access_key_setting.value,
        secret=secret_key_setting.value,
        tag=partner_tag_setting.value,
        country='TR',
        throttling=2.0  # 2 saniye bekle (rate limiting - Amazon API limitleri için)
    )
    
    # İstatistikler
    stats = {
        "nodes_processed": 0,
        "total_found": 0,
        "products_created": 0,
        "products_updated": 0,
        "products_skipped": 0,
        "deals_created": 0,
        "deals_updated": 0
    }
    
    # Her browse node için ürün çek
    max_products = category.max_products or 100
    products_per_node = max_products // len(category.amazon_browse_node_ids)
    
    for node_id in category.amazon_browse_node_ids:
        try:
            # SearchItems API call
            items = search_items_by_node(
                amazon=amazon,
                browse_node_id=node_id,
                category=category,
                max_items=products_per_node
            )
            
            stats["nodes_processed"] += 1
            stats["total_found"] += len(items)
            
            # Ürünleri işle
            for item_data in items:
                result = upsert_product(
                    amazon_item=item_data,
                    category_id=category_id,
                    category=category,
                    db=db
                )
                
                if result["action"] == "created":
                    stats["products_created"] += 1
                elif result["action"] == "updated":
                    stats["products_updated"] += 1
                else:
                    stats["products_skipped"] += 1
                
                # Deal detection
                if result["deal"]:
                    if result["deal_action"] == "created":
                        stats["deals_created"] += 1
                    elif result["deal_action"] == "updated":
                        stats["deals_updated"] += 1
            
        except Exception as e:
            # Node hatası, devam et
            print(f"Error fetching node {node_id}: {str(e)}")
            continue
    
    # Kategori last_checked_at güncelle
    category.last_checked_at = datetime.now()
    
    # Commit all changes
    db.commit()
    
    # Süre hesapla
    duration = (datetime.now() - start_time).total_seconds()
    
    return {
        "category_id": category_id,
        "category_name": category.name,
        "nodes_processed": stats["nodes_processed"],
        "total_found": stats["total_found"],
        "products_created": stats["products_created"],
        "products_updated": stats["products_updated"],
        "products_skipped": stats["products_skipped"],
        "deals_created": stats["deals_created"],
        "deals_updated": stats["deals_updated"],
        "duration_seconds": duration
    }


@router.post("/categories/{category_id}/fetch-products", response_model=FetchProductsResponse)
async def fetch_category_products(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Manuel endpoint: Kategori için Amazon PA API'den ürün çek
    Background task olarak da çalışabilir (celery task)
    """
    result = fetch_category_products_logic(category_id, db)
    return FetchProductsResponse(**result)


def search_items_by_node(
    amazon: Any,
    browse_node_id: str,
    category: models.Category,
    max_items: int
) -> List[Dict[str, Any]]:
    """
    Browse node'a göre ürün ara (sadece PA API filtreleri)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    rules = category.selection_rules or {}
    
    # SearchItems parametreleri
    # NOT: resources parametresini SDK otomatik handle ediyor, manuel eklemeye gerek yok
    search_params = {
        "browse_node_id": browse_node_id,
        "item_count": 10,  # Sayfa başı max
    }
    
    # Fiyat filtreleri (TL → Kuruş)
    if rules.get('min_price'):
        search_params['min_price'] = int(rules['min_price'] * 100)
    
    if rules.get('max_price'):
        search_params['max_price'] = int(rules['max_price'] * 100)
    
    # Rating filtresi
    if rules.get('min_rating'):
        search_params['min_reviews_rating'] = int(rules['min_rating'])
    
    # İndirim filtresi
    if rules.get('min_discount_percentage'):
        search_params['min_saving_percent'] = int(rules['min_discount_percentage'])
    
    # Prime filtresi
    if rules.get('only_prime'):
        search_params['delivery_flags'] = ['Prime']
    
    all_items = []
    pages_to_fetch = min((max_items // 10) + 1, 10)  # Max 10 sayfa
    
    for page in range(1, pages_to_fetch + 1):
        try:
            search_params['item_page'] = page
            # Tüm parametreleri kwargs olarak gönder (resources dahil)
            result = amazon.search_items(**search_params)
            
            logger.warning(f"DEBUG: Page {page} for node {browse_node_id}: hasattr items={hasattr(result, 'items')}, items_count={len(result.items) if hasattr(result, 'items') and result.items else 0}")
            
            if not hasattr(result, 'items') or not result.items:
                logger.warning(f"DEBUG: Breaking - No items found on page {page} for node {browse_node_id}")
                break
            
            # Parse items - Filtresiz, direkt ekle
            for item in result.items:
                item_data = parse_amazon_item(item)
                all_items.append(item_data)
                
                if len(all_items) >= max_items:
                    break
            
        except Exception as e:
            logger.warning(f"Error fetching page {page} for node {browse_node_id}: {str(e)}")
            break
    
    return all_items[:max_items]
def parse_amazon_item(item: Any) -> Dict[str, Any]:
    """Amazon PA API item'ını dict'e çevir"""
    data = {
        "asin": item.asin,
        "title": None,
        "brand": None,
        "current_price": None,
        "list_price": None,
        "image_url": None,
        "detail_page_url": None,
        "availability": None,
        "is_available": False,
        "is_prime": False,
        "rating": None,
        "review_count": None,
        "ean": None
    }
    
    # Title & Brand
    if hasattr(item, 'item_info') and item.item_info:
        if hasattr(item.item_info, 'title') and item.item_info.title:
            data["title"] = item.item_info.title.display_value
        
        if hasattr(item.item_info, 'by_line_info') and item.item_info.by_line_info:
            if hasattr(item.item_info.by_line_info, 'brand') and item.item_info.by_line_info.brand:
                data["brand"] = item.item_info.by_line_info.brand.display_value
        
        # EAN
        if hasattr(item.item_info, 'external_ids') and item.item_info.external_ids:
            if hasattr(item.item_info.external_ids, 'ea_ns') and item.item_info.external_ids.ea_ns:
                if hasattr(item.item_info.external_ids.ea_ns, 'display_values'):
                    if item.item_info.external_ids.ea_ns.display_values:
                        data["ean"] = item.item_info.external_ids.ea_ns.display_values[0]
    
    # Pricing & Availability
    if hasattr(item, 'offers') and item.offers:
        if hasattr(item.offers, 'listings') and item.offers.listings:
            listing = item.offers.listings[0]
            
            # Current price
            if hasattr(listing, 'price') and listing.price:
                if hasattr(listing.price, 'amount') and listing.price.amount:
                    try:
                        # Amazon PA API returns price directly in TL (not Kuruş)
                        price_amount = float(listing.price.amount)
                        data["current_price"] = price_amount
                    except (ValueError, TypeError, AttributeError) as e:
                        print(f"Error parsing current_price: {e}")
                        data["current_price"] = None
            
            # List price (original)
            if hasattr(listing, 'saving_basis') and listing.saving_basis:
                if hasattr(listing.saving_basis, 'amount') and listing.saving_basis.amount:
                    try:
                        # Amazon PA API returns price directly in TL (not Kuruş)
                        list_price_amount = float(listing.saving_basis.amount)
                        data["list_price"] = list_price_amount
                    except (ValueError, TypeError, AttributeError) as e:
                        print(f"Error parsing list_price: {e}")
                        data["list_price"] = None
            
            # Availability
            if hasattr(listing, 'availability') and listing.availability:
                if hasattr(listing.availability, 'message'):
                    data["availability"] = listing.availability.message
                    # Stok durumunu kontrol et
                    availability_text = (data["availability"] or "").lower()
                    # Stokta olduğunu gösteren kelimeler
                    in_stock_keywords = ['stokta var', 'stock', 'in stock', 'kargoya verilir']
                    # Stok dışı olduğunu gösteren kelimeler
                    out_of_stock_keywords = ['stokta yok', 'out of stock', 'mevcut değil', 'unavailable']
                    
                    # Önce stok dışı kontrol et
                    is_out_of_stock = any(keyword in availability_text for keyword in out_of_stock_keywords)
                    if is_out_of_stock:
                        data["is_available"] = False
                    else:
                        # Stokta olduğunu gösteren kelime var mı?
                        data["is_available"] = any(keyword in availability_text for keyword in in_stock_keywords)
            
            # Prime
            if hasattr(listing, 'delivery_info') and listing.delivery_info:
                if hasattr(listing.delivery_info, 'is_prime_eligible'):
                    data["is_prime"] = listing.delivery_info.is_prime_eligible or False
        else:
            # Listing yok → Satılmıyor
            data["is_available"] = False
    else:
        # Offers yok → Satılmıyor
        data["is_available"] = False
    
    # Reviews (Not available for TR marketplace via Amazon PA API)
    if hasattr(item, 'customer_reviews') and item.customer_reviews:
        if hasattr(item.customer_reviews, 'star_rating') and item.customer_reviews.star_rating:
            if hasattr(item.customer_reviews.star_rating, 'value') and item.customer_reviews.star_rating.value:
                try:
                    data["rating"] = float(item.customer_reviews.star_rating.value)
                except (ValueError, TypeError, AttributeError) as e:
                    data["rating"] = None
        
        if hasattr(item.customer_reviews, 'count') and item.customer_reviews.count:
            try:
                data["review_count"] = int(item.customer_reviews.count)
            except (ValueError, TypeError, AttributeError) as e:
                data["review_count"] = None
    
    # Image
    if hasattr(item, 'images') and item.images:
        if hasattr(item.images, 'primary') and item.images.primary:
            if hasattr(item.images.primary, 'large') and item.images.primary.large:
                if hasattr(item.images.primary.large, 'url'):
                    data["image_url"] = item.images.primary.large.url
    
    return data


def upsert_product(
    amazon_item: Dict[str, Any],
    category_id: int,
    category: models.Category,
    db: Session
) -> Dict[str, Any]:
    """
    Ürün ekle veya güncelle + Fiyat geçmişi mantığı
    """
    asin = amazon_item["asin"]
    new_price = amazon_item.get("current_price")
    
    if not new_price:
        return {"action": "skipped", "deal": None, "deal_action": None}
    
    # Ürün var mı?
    product = db.query(models.Product).filter(models.Product.asin == asin).first()
    
    if product:
        # ✅ GÜNCELLEME
        old_price = float(product.current_price) if product.current_price else None
        price_changed = old_price != new_price
        
        # Ürün bilgilerini güncelle
        product.title = amazon_item.get("title") or product.title
        product.brand = amazon_item.get("brand") or product.brand
        product.current_price = Decimal(str(new_price))
        product.list_price = Decimal(str(amazon_item.get("list_price", new_price)))
        product.image_url = amazon_item.get("image_url") or product.image_url
        product.detail_page_url = amazon_item.get("detail_page_url") or product.detail_page_url
        product.availability = amazon_item.get("availability")
        # is_available: Eğer Amazon'dan bilgi gelmezse False (stok dışı kabul et)
        product.is_available = amazon_item.get("is_available", False)
        product.rating = amazon_item.get("rating")
        product.review_count = amazon_item.get("review_count")
        product.ean = amazon_item.get("ean") or product.ean
        product.last_checked_at = datetime.now()
        
        # Fiyat geçmişi mantığı
        if price_changed:
            # 🔴 FİYAT DEĞİŞTİ → Yeni kayıt ekle
            add_price_history(product, new_price, amazon_item.get("list_price"), db)
        else:
            # 🟡 FİYAT AYNI → Bugün kayıt var mı kontrol et
            last_record = get_last_price_record(product.id, db)
            if last_record:
                today = datetime.now().date()
                last_date = last_record.recorded_at.date()
                
                if last_date < today:
                    # ✅ Bugün kayıt yok → Günlük snapshot ekle
                    add_price_history(product, new_price, amazon_item.get("list_price"), db)
            else:
                # İlk kayıt
                add_price_history(product, new_price, amazon_item.get("list_price"), db)
        
        action = "updated"
        
    else:
        # ✅ YENİ ÜRÜN
        product = models.Product(
            asin=asin,
            title=amazon_item.get("title", "Unknown"),
            brand=amazon_item.get("brand"),
            category_id=category_id,
            current_price=Decimal(str(new_price)),
            list_price=Decimal(str(amazon_item.get("list_price", new_price))),
            image_url=amazon_item.get("image_url"),
            detail_page_url=amazon_item.get("detail_page_url"),
            availability=amazon_item.get("availability"),
            # is_available: Eğer Amazon'dan bilgi gelmezse False (stok dışı kabul et)
            is_available=amazon_item.get("is_available", False),
            rating=amazon_item.get("rating"),
            review_count=amazon_item.get("review_count"),
            ean=amazon_item.get("ean"),
            is_active=True,
            last_checked_at=datetime.now(),
            created_at=datetime.now()
        )
        db.add(product)
        db.flush()  # ID almak için
        
        # İlk fiyat kaydı
        add_price_history(product, new_price, amazon_item.get("list_price"), db)
        
        action = "created"
    
    # Deal detection
    deal_result = check_and_create_deal(product, category, db)
    
    return {
        "action": action,
        "deal": deal_result["deal"],
        "deal_action": deal_result["action"]
    }


def add_price_history(
    product: models.Product,
    price: float,
    list_price: float | None,
    db: Session
):
    """Fiyat geçmişi kaydı ekle"""
    list_price_decimal = Decimal(str(list_price)) if list_price else None
    price_decimal = Decimal(str(price))
    
    # İndirim hesapla
    discount_amount = None
    discount_percentage = None
    if list_price and list_price > price:
        discount_amount = Decimal(str(list_price - price))
        discount_percentage = float((list_price - price) / list_price * 100)
    
    price_history = models.PriceHistory(
        product_id=product.id,
        price=price_decimal,
        list_price=list_price_decimal,
        discount_amount=discount_amount,
        discount_percentage=discount_percentage,
        is_available=product.is_available,
        availability_status=product.availability,
        recorded_at=datetime.now()
    )
    db.add(price_history)


def get_last_price_record(product_id: int, db: Session) -> models.PriceHistory | None:
    """Son fiyat kaydını getir"""
    return db.query(models.PriceHistory)\
        .filter(models.PriceHistory.product_id == product_id)\
        .order_by(models.PriceHistory.recorded_at.desc())\
        .first()


def check_and_create_deal(
    product: models.Product,
    category: models.Category,
    db: Session
) -> Dict[str, Any]:
    """
    Deal tespiti ve oluşturma - YENİ MANTIK
    NOT: Bu fonksiyon price history'ye ekleme SONRASINDA çağrılmalı!
    
    1. Son 2 fiyat kaydını al (en yeni ve bir önceki)
    2. Kategori indirim oranı kadar fark varsa deal oluştur
    3. Zaman dilimlerine göre "en ucuz" bayraklarını set et
    """
    
    # Son 2 fiyat kaydını al
    last_2_records = db.query(models.PriceHistory).filter(
        models.PriceHistory.product_id == product.id,
        models.PriceHistory.price.isnot(None)
    ).order_by(models.PriceHistory.recorded_at.desc()).limit(2).all()
    
    # En az 2 kayıt olmalı karşılaştırma için
    if len(last_2_records) < 2:
        return {"deal": None, "action": None}
    
    # Son kayıt (yeni eklenen)
    current_price = float(last_2_records[0].price)
    
    # Bir önceki kayıt (eski fiyat)
    previous_price = float(last_2_records[1].price)
    
    # Kategori filtrelerini kontrol et
    rules = category.selection_rules or {}
    min_discount = rules.get('min_discount_percentage', 20)
    
    # İndirim hesapla (önceki fiyata göre)
    if previous_price <= current_price:
        # Fiyat düşmemiş veya artmış
        return {"deal": None, "action": None}
    
    discount_amount = previous_price - current_price
    discount_percentage = (discount_amount / previous_price) * 100
    
    # Minimum indirim yüzdesi kontrolü
    if discount_percentage < min_discount:
        return {"deal": None, "action": None}
    
    # Zaman dilimlerine göre en ucuz fiyat kontrolü
    cheapest_flags = check_cheapest_price_flags(product.id, current_price, db)
    
    # Aktif deal var mı?
    existing_deal = db.query(models.Deal).filter(
        models.Deal.product_id == product.id,
        models.Deal.is_active == True
    ).first()
    
    if existing_deal:
        # Fiyat değiştiyse güncelle
        if float(existing_deal.deal_price) != current_price:
            existing_deal.original_price = Decimal(str(previous_price))
            existing_deal.deal_price = Decimal(str(current_price))
            existing_deal.previous_price = Decimal(str(previous_price))
            existing_deal.discount_amount = Decimal(str(discount_amount))
            existing_deal.discount_percentage = discount_percentage
            existing_deal.is_cheapest_14days = cheapest_flags['is_cheapest_14days']
            existing_deal.is_cheapest_1month = cheapest_flags['is_cheapest_1month']
            existing_deal.is_cheapest_3months = cheapest_flags['is_cheapest_3months']
            existing_deal.is_cheapest_6months = cheapest_flags['is_cheapest_6months']
            existing_deal.updated_at = datetime.now()
            return {"deal": existing_deal, "action": "updated"}
        
        return {"deal": existing_deal, "action": None}
    
    # Bugün bu fiyatla deal oluşturulmuş mu kontrol et
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_deal = db.query(models.Deal).filter(
        models.Deal.product_id == product.id,
        models.Deal.created_at >= today_start,
        models.Deal.deal_price == Decimal(str(current_price))
    ).first()
    
    if today_deal:
        # Bugün aynı fiyatla deal zaten oluşturulmuş, tekrar oluşturma
        return {"deal": None, "action": "skipped_duplicate"}
    
    # Yeni deal oluştur (otomatik yayınla)
    deal = models.Deal(
        product_id=product.id,
        title=product.title,
        original_price=Decimal(str(previous_price)),   # Önceki fiyat
        deal_price=Decimal(str(current_price)),        # Şu anki fiyat (indirimli)
        previous_price=Decimal(str(previous_price)),   # Önceki fiyat (referans)
        discount_amount=Decimal(str(discount_amount)),
        discount_percentage=discount_percentage,
        is_cheapest_14days=cheapest_flags['is_cheapest_14days'],
        is_cheapest_1month=cheapest_flags['is_cheapest_1month'],
        is_cheapest_3months=cheapest_flags['is_cheapest_3months'],
        is_cheapest_6months=cheapest_flags['is_cheapest_6months'],
        is_active=True,
        is_published=True,  # ✅ Otomatik yayınla
        valid_from=datetime.now(),
        created_at=datetime.now()
    )
    db.add(deal)
    db.flush()  # Get deal ID without committing
    
    # 🚀 Telegram'a gönder (otomatik)
    try:
        from app.services.telegram import send_deal_notification
        send_deal_notification(deal, db)
        logger.info(f"Deal {deal.id} sent to Telegram")
    except Exception as e:
        logger.error(f"Failed to send deal {deal.id} to Telegram: {str(e)}")
        # Telegram hatası deal oluşturmayı engellemez
    
    return {"deal": deal, "action": "created"}


def check_cheapest_price_flags(
    product_id: int,
    current_price: float,
    db: Session
) -> Dict[str, bool]:
    """
    Zaman dilimlerine göre en ucuz fiyat kontrolü
    NOT: Sadece yeterli veri varsa flag'i TRUE yapar
    """
    now = datetime.now()
    
    # Zaman dilimleri (gün sayısı)
    periods = {
        '14days': 14,
        '1month': 30,
        '3months': 90,
        '6months': 180,
    }
    
    flags = {
        'is_cheapest_14days': False,
        'is_cheapest_1month': False,
        'is_cheapest_3months': False,
        'is_cheapest_6months': False,
    }
    
    # Ürünün en eski fiyat kaydını bul
    oldest_record = db.query(models.PriceHistory).filter(
        models.PriceHistory.product_id == product_id,
        models.PriceHistory.price.isnot(None)
    ).order_by(models.PriceHistory.recorded_at.asc()).first()
    
    if not oldest_record:
        return flags
    
    # Kaç günlük veri var?
    data_age_days = (now - oldest_record.recorded_at).days
    
    for period_name, required_days in periods.items():
        # Yeterli veri yoksa bu flag FALSE kalır
        if data_age_days < required_days:
            continue
        
        # Yeterli veri var, kontrol et
        start_date = now - timedelta(days=required_days)
        
        # Bu zaman dilimindeki minimum fiyatı bul
        min_price_record = db.query(models.PriceHistory).filter(
            models.PriceHistory.product_id == product_id,
            models.PriceHistory.recorded_at >= start_date,
            models.PriceHistory.price.isnot(None)
        ).order_by(models.PriceHistory.price.asc()).first()
        
        # Eğer current price bu dönemin minimum fiyatından düşük veya eşitse
        if min_price_record and current_price <= float(min_price_record.price):
            flags[f'is_cheapest_{period_name}'] = True
    
    return flags
