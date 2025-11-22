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
@cache(expire=60)  # Cache for 60 seconds
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=10000),
    category_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    is_available: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List products with filtering and pagination (CACHED)"""
    
    query = db.query(models.Product)
    
    if category_id:
        query = query.filter(models.Product.category_id == category_id)
    
    if is_active is not None:
        query = query.filter(models.Product.is_active == is_active)
    
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
    
    # Get paginated results - Sort by review_count (popularity) then rating
    products = query.order_by(
        desc(models.Product.review_count),
        desc(models.Product.rating),
        desc(models.Product.updated_at)
    ).offset(skip).limit(limit).all()
    
    return {
        "items": products,
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
