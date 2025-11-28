from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

try:
    from fastapi_cache.decorator import cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    def cache(expire: int = 60):
        """Dummy cache decorator when fastapi-cache not available"""
        def decorator(func):
            return func
        return decorator

from app.db.database import get_db
from app.db import models
from app.schemas import deal as deal_schema
from app.core.security import get_current_active_admin

router = APIRouter()


@router.get("/")
@cache(expire=30)  # Cache for 30 seconds (deals change frequently)
async def list_deals(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    is_published: Optional[bool] = None,
    telegram_sent: Optional[bool] = None,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List deals with filtering and pagination"""
    
    query = db.query(models.Deal).join(models.Product)
    
    if is_active is not None:
        query = query.filter(models.Deal.is_active == is_active)
    
    if is_published is not None:
        query = query.filter(models.Deal.is_published == is_published)
    
    if telegram_sent is not None:
        query = query.filter(models.Deal.telegram_sent == telegram_sent)
    
    if category_id:
        query = query.filter(models.Product.category_id == category_id)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    deals = query.order_by(desc(models.Deal.created_at)).offset(skip).limit(limit).all()
    
    # Manually construct response with product info
    items = []
    for deal in deals:
        product = db.query(models.Product).filter(models.Product.id == deal.product_id).first()
        deal_dict = {
            "id": deal.id,
            "product_id": deal.product_id,
            "title": deal.title,
            "description": deal.description,
            "original_price": str(deal.original_price),
            "deal_price": str(deal.deal_price),
            "discount_amount": str(deal.discount_amount),
            "discount_percentage": float(deal.discount_percentage),
            "currency": deal.currency,
            "is_active": deal.is_active,
            "is_published": deal.is_published,
            "telegram_sent": deal.telegram_sent,
            "telegram_message_id": deal.telegram_message_id,
            "telegram_sent_at": deal.telegram_sent_at.isoformat() if deal.telegram_sent_at else None,
            "published_at": deal.published_at.isoformat() if deal.published_at else None,
            "created_at": deal.created_at.isoformat() if deal.created_at else None,
            "updated_at": deal.updated_at.isoformat() if deal.updated_at else None,
            "valid_from": deal.valid_from.isoformat() if deal.valid_from else None,
            "valid_until": deal.valid_until.isoformat() if deal.valid_until else None,
            "product": {
                "image_url": product.image_url if product else None,
                "detail_page_url": product.detail_page_url if product and product.detail_page_url 
                    else f"https://www.amazon.com.tr/dp/{product.asin}" if product and product.asin else None,
                "brand": product.brand if product else None,
                "asin": product.asin if product else None,
                "rating": float(product.rating) if product and product.rating else None,
                "review_count": product.review_count if product else None,
                "category_id": product.category_id if product else None,
            } if product else None
        }
        items.append(deal_dict)
    
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/", response_model=deal_schema.Deal, status_code=status.HTTP_201_CREATED)
async def create_deal(
    deal: deal_schema.DealCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Create a new deal (admin only)"""
    
    # Check if product exists
    product = db.query(models.Product).filter(models.Product.id == deal.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    db_deal = models.Deal(**deal.dict())
    db.add(db_deal)
    db.commit()
    db.refresh(db_deal)
    
    return db_deal


@router.get("/{deal_id}", response_model=deal_schema.Deal)
async def get_deal(
    deal_id: int,
    db: Session = Depends(get_db)
):
    """Get deal by ID"""
    from sqlalchemy.orm import noload
    
    deal = db.query(models.Deal).options(noload(models.Deal.product)).filter(models.Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found"
        )
    
    return deal


@router.put("/{deal_id}", response_model=deal_schema.Deal)
async def update_deal(
    deal_id: int,
    deal_update: deal_schema.DealUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Update deal (admin only)"""
    
    deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found"
        )
    
    update_data = deal_update.dict(exclude_unset=True)
    
    # Handle publish status change
    if "is_published" in update_data and update_data["is_published"] and not deal.is_published:
        update_data["published_at"] = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(deal, field, value)
    
    db.commit()
    db.refresh(deal)
    
    return deal


@router.delete("/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Delete deal (admin only)"""
    
    deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found"
        )
    
    db.delete(deal)
    db.commit()
    
    return None


@router.post("/{deal_id}/publish", response_model=deal_schema.Deal)
async def publish_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Publish a deal"""
    
    deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found"
        )
    
    deal.is_published = True
    deal.published_at = datetime.utcnow()
    
    db.commit()
    db.refresh(deal)
    
    return deal


@router.post("/{deal_id}/unpublish", response_model=deal_schema.Deal)
async def unpublish_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Unpublish a deal"""
    
    deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found"
        )
    
    deal.is_published = False
    
    db.commit()
    db.refresh(deal)
    
    return deal
