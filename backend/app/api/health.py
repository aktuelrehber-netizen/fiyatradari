from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta

from app.db.database import get_db
from app.db import models
from app.schemas.setting import DashboardStats

router = APIRouter()


@router.get("/")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint with database status"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow(),
        "database": db_status,
        "service": "fiyatradari-api"
    }


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    
    # Count products
    total_products = db.query(models.Product).count()
    active_products = db.query(models.Product).filter(
        models.Product.is_active == True
    ).count()
    
    # Count categories
    total_categories = db.query(models.Category).filter(
        models.Category.is_active == True
    ).count()
    
    # Count active deals
    active_deals = db.query(models.Deal).filter(
        models.Deal.is_active == True
    ).count()
    
    # Count telegram messages sent
    telegram_messages_sent = db.query(models.Deal).filter(
        models.Deal.telegram_sent == True
    ).count()
    
    # Count price checks today (products checked today)
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    total_price_checks_today = db.query(models.Product).filter(
        models.Product.last_checked_at >= today
    ).count()
    
    # Count price changes today (only when price actually changed)
    price_changes_today = db.query(models.PriceHistory).filter(
        models.PriceHistory.recorded_at >= today
    ).count()
    
    # Get last worker run
    last_worker_log = db.query(models.WorkerLog).order_by(
        models.WorkerLog.created_at.desc()
    ).first()
    last_worker_run = last_worker_log.created_at if last_worker_log else None
    
    # Determine system health
    system_health = "healthy"
    if last_worker_run:
        hours_since_last_run = (datetime.utcnow() - last_worker_run).total_seconds() / 3600
        if hours_since_last_run > 24:
            system_health = "warning"
    
    return DashboardStats(
        total_products=total_products,
        active_products=active_products,
        total_categories=total_categories,
        active_deals=active_deals,
        total_price_checks_today=total_price_checks_today,
        price_changes_today=price_changes_today,
        telegram_messages_sent=telegram_messages_sent,
        last_worker_run=last_worker_run,
        system_health=system_health
    )


@router.get("/analytics/trends")
async def get_trends(db: Session = Depends(get_db)):
    """Get trend data for charts"""
    
    # Last 7 days price checks
    trends = []
    for i in range(6, -1, -1):
        day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
        next_day = day + timedelta(days=1)
        
        count = db.query(models.PriceHistory).filter(
            models.PriceHistory.recorded_at >= day,
            models.PriceHistory.recorded_at < next_day
        ).count()
        
        deals_count = db.query(models.Deal).filter(
            models.Deal.created_at >= day,
            models.Deal.created_at < next_day
        ).count()
        
        trends.append({
            "date": day.strftime("%d %b"),
            "price_checks": count,
            "deals": deals_count
        })
    
    return {"trends": trends}


@router.get("/analytics/categories")
async def get_category_stats(db: Session = Depends(get_db)):
    """Get category distribution"""
    
    from sqlalchemy import func
    
    # Product count by category
    category_data = db.query(
        models.Category.name,
        func.count(models.Product.id).label('product_count')
    ).outerjoin(
        models.Product, models.Category.id == models.Product.category_id
    ).filter(
        models.Category.is_active == True
    ).group_by(
        models.Category.id, models.Category.name
    ).order_by(
        func.count(models.Product.id).desc()
    ).limit(10).all()
    
    return {
        "categories": [
            {"name": name, "value": count}
            for name, count in category_data
        ]
    }


@router.get("/analytics/top-deals")
async def get_top_deals(db: Session = Depends(get_db)):
    """Get top deals by discount"""
    
    deals = db.query(models.Deal).filter(
        models.Deal.is_active == True
    ).order_by(
        models.Deal.discount_percentage.desc()
    ).limit(5).all()
    
    return {
        "deals": [
            {
                "id": deal.id,
                "title": deal.title,
                "discount_percentage": float(deal.discount_percentage),
                "deal_price": str(deal.deal_price),
                "original_price": str(deal.original_price),
                "currency": deal.currency,
                "created_at": deal.created_at.isoformat() if deal.created_at else datetime.utcnow().isoformat()
            }
            for deal in deals
        ]
    }


@router.get("/analytics/recent-products")
async def get_recent_products(db: Session = Depends(get_db)):
    """Get recently added products"""
    
    products = db.query(models.Product).filter(
        models.Product.is_active == True
    ).order_by(
        models.Product.created_at.desc()
    ).limit(5).all()
    
    return {
        "products": [
            {
                "id": product.id,
                "title": product.title,
                "brand": product.brand,
                "current_price": str(product.current_price),
                "currency": product.currency,
                "image_url": product.image_url,
                "created_at": product.created_at.isoformat() if product.created_at else datetime.utcnow().isoformat()
            }
            for product in products
        ]
    }


@router.get("/services")
async def get_service_status(db: Session = Depends(get_db)):
    """Get status of all services"""
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        database_status = "healthy"
    except:
        database_status = "unhealthy"
    
    # Check Redis (optional - if you want to add later)
    # For now, just return API and Database status
    
    return {
        "services": {
            "api": {
                "status": "healthy",
                "uptime": "running"
            },
            "database": {
                "status": database_status
            }
        },
        "timestamp": datetime.utcnow()
    }
