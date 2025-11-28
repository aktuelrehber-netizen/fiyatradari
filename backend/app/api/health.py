from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.db.database import get_db
from app.db import models
from app.api.auth import get_current_user

router = APIRouter()


@router.get("/health/dashboard")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Dashboard ana istatistikleri
    """
    # Bugünün başlangıcı
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Temel istatistikler
    total_products = db.query(models.Product).count()
    active_products = db.query(models.Product).filter(
        models.Product.is_active == True
    ).count()
    
    total_categories = db.query(models.Category).count()
    
    active_deals = db.query(models.Deal).filter(
        models.Deal.is_active == True
    ).count()
    
    # Bugün oluşturulan fiyat değişiklikleri (deals)
    price_changes_today = db.query(models.Deal).filter(
        models.Deal.created_at >= today
    ).count()
    
    # Telegram mesajları (published deals)
    telegram_messages_sent = db.query(models.Deal).filter(
        models.Deal.is_published == True
    ).count()
    
    # Son worker çalışma zamanı (son kategori kontrolü)
    last_category = db.query(models.Category).order_by(
        desc(models.Category.last_checked_at)
    ).first()
    
    last_worker_run = last_category.last_checked_at.isoformat() if last_category and last_category.last_checked_at else None
    
    return {
        "total_products": total_products,
        "active_products": active_products,
        "total_categories": total_categories,
        "active_deals": active_deals,
        "total_price_checks_today": price_changes_today,
        "price_changes_today": price_changes_today,
        "telegram_messages_sent": telegram_messages_sent,
        "last_worker_run": last_worker_run,
        "system_health": "operational"
    }


@router.get("/health/analytics/trends")
async def get_trends(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Son 7 günün aktivite trendi
    """
    # Son 7 gün
    trends = []
    for i in range(7):
        day = datetime.now() - timedelta(days=6-i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        # O gün oluşturulan price check'ler (products)
        price_checks = db.query(models.Product).filter(
            and_(
                models.Product.created_at >= day_start,
                models.Product.created_at < day_end
            )
        ).count()
        
        # O gün oluşturulan deals
        deals = db.query(models.Deal).filter(
            and_(
                models.Deal.created_at >= day_start,
                models.Deal.created_at < day_end
            )
        ).count()
        
        trends.append({
            "date": day.strftime("%d.%m"),
            "price_checks": price_checks,
            "deals": deals
        })
    
    return {"trends": trends}


@router.get("/health/analytics/categories")
async def get_category_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Kategorilere göre ürün dağılımı
    """
    # Her kategorideki ürün sayısı
    category_stats = db.query(
        models.Category.name,
        func.count(models.Product.id).label('count')
    ).join(
        models.Product,
        models.Product.category_id == models.Category.id
    ).group_by(
        models.Category.id,
        models.Category.name
    ).all()
    
    categories = [
        {"name": name, "value": count}
        for name, count in category_stats
    ]
    
    return {"categories": categories}


@router.get("/health/analytics/top-deals")
async def get_top_deals(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    limit: int = 5
):
    """
    En yüksek indirimli deals
    """
    deals = db.query(models.Deal).filter(
        models.Deal.is_active == True
    ).order_by(
        desc(models.Deal.discount_percentage)
    ).limit(limit).all()
    
    result = []
    for deal in deals:
        product = db.query(models.Product).filter(
            models.Product.id == deal.product_id
        ).first()
        
        if product:
            result.append({
                "id": deal.id,
                "title": product.title,
                "discount_percentage": float(deal.discount_percentage) if deal.discount_percentage else 0,
                "deal_price": str(deal.deal_price),
                "original_price": str(deal.original_price),
                "currency": product.currency or "TRY",
                "created_at": deal.created_at.isoformat() if deal.created_at else None
            })
    
    return {"deals": result}


@router.get("/health/analytics/recent-products")
async def get_recent_products(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    limit: int = 5
):
    """
    Yeni eklenen ürünler
    """
    products = db.query(models.Product).order_by(
        desc(models.Product.created_at)
    ).limit(limit).all()
    
    result = []
    for product in products:
        result.append({
            "id": product.id,
            "title": product.title,
            "brand": product.brand,
            "current_price": str(product.current_price) if product.current_price else "0",
            "currency": product.currency or "TRY",
            "image_url": product.image_url,
            "created_at": product.created_at.isoformat() if product.created_at else None
        })
    
    return {"products": result}
