from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime, timedelta

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
from app.schemas import product as product_schema
from app.core.security import get_current_active_admin

router = APIRouter()


@router.get("/")
@cache(expire=10)  # Cache for 10 seconds (faster updates after rating changes)
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=10000),
    category_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    is_available: Optional[bool] = Query(True, description="Show only in-stock products by default"),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List products with filtering and pagination (CACHED)"""
    
    query = db.query(models.Product)
    
    if category_id:
        # Get all subcategory IDs recursively
        def get_all_subcategory_ids(parent_id: int) -> list[int]:
            """Recursively get all subcategory IDs"""
            category_ids = [parent_id]
            subcategories = db.query(models.Category).filter(
                models.Category.parent_id == parent_id
            ).all()
            for subcat in subcategories:
                category_ids.extend(get_all_subcategory_ids(subcat.id))
            return category_ids
        
        # Include products from category and all subcategories
        all_category_ids = get_all_subcategory_ids(category_id)
        query = query.filter(models.Product.category_id.in_(all_category_ids))
    
    if is_active is not None:
        query = query.filter(models.Product.is_active == is_active)
    
    # Always filter by availability (default: show only available products)
    if is_available is not None:
        query = query.filter(models.Product.is_available == is_available)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (models.Product.title.ilike(search_term)) |
            (models.Product.brand.ilike(search_term)) |
            (models.Product.asin.ilike(search_term))
        )
    
    # Get total count
    total = query.count()
    
    # Get paginated results - Sort by: has_deal → rating → popularity → newest
    # Left join with deals and use max(deal.id) to prioritize products with deals
    products = query.outerjoin(
        models.Deal,
        (models.Deal.product_id == models.Product.id) &
        (models.Deal.is_active == True) &
        (models.Deal.is_published == True)
    ).group_by(models.Product.id).order_by(
        desc(func.coalesce(func.max(models.Deal.id), 0)),  # Deal olanlar EN ÜSTTE!
        desc(func.coalesce(models.Product.rating, 0)),  # Sonra rating
        desc(models.Product.review_count),  # Sonra popularity
        desc(models.Product.updated_at)     # Son olarak newest
    ).offset(skip).limit(limit).all()
    
    # Add deal information to products
    products_with_deals = []
    for product in products:
        product_dict = {
            "id": product.id,
            "asin": product.asin,
            "title": product.title,
            "brand": product.brand,
            "category_id": product.category_id,
            "current_price": product.current_price,
            "image_url": product.image_url,
            "detail_page_url": product.detail_page_url,
            "rating": product.rating,
            "review_count": product.review_count,
            "is_available": product.is_available,
            "is_active": product.is_active,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
            "last_checked_at": product.last_checked_at,
        }
        
        # Check if product has an active deal
        active_deal = db.query(models.Deal).filter(
            models.Deal.product_id == product.id,
            models.Deal.is_active == True,
            models.Deal.is_published == True
        ).first()
        
        if active_deal:
            product_dict["previous_price"] = active_deal.previous_price
            product_dict["discount_percentage"] = active_deal.discount_percentage
        
        products_with_deals.append(product_dict)
    
    return {
        "items": products_with_deals,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/", response_model=product_schema.Product, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: product_schema.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Create a new product (admin only)"""
    
    # Check if ASIN exists
    if db.query(models.Product).filter(models.Product.asin == product.asin).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product with this ASIN already exists"
        )
    
    # Check if category exists
    category = db.query(models.Category).filter(models.Category.id == product.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    return db_product


@router.get("/{product_id}", response_model=product_schema.Product)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Get product by ID"""
    
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product


@router.get("/asin/{asin}", response_model=product_schema.Product)
async def get_product_by_asin(
    asin: str,
    db: Session = Depends(get_db)
):
    """Get product by ASIN"""
    
    product = db.query(models.Product).filter(models.Product.asin == asin).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product


@router.put("/{product_id}", response_model=product_schema.Product)
async def update_product(
    product_id: int,
    product_update: product_schema.ProductUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Update product (admin only)"""
    
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    update_data = product_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    
    return product


@router.patch("/{product_id}", response_model=product_schema.Product)
async def toggle_product_active(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Toggle product active status (admin only)"""
    
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Toggle active status
    product.is_active = not product.is_active
    product.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(product)
    
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Delete product (admin only)"""
    
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    db.delete(product)
    db.commit()
    
    return None


@router.get("/{product_id}/price-history", response_model=List[product_schema.PriceHistory])
async def get_product_price_history(
    product_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get price history for a product"""
    
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    since_date = datetime.utcnow() - timedelta(days=days)
    
    price_history = db.query(models.PriceHistory).filter(
        models.PriceHistory.product_id == product_id,
        models.PriceHistory.recorded_at >= since_date
    ).order_by(models.PriceHistory.recorded_at).all()
    
    return price_history
