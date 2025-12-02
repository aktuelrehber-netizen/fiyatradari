"""
Catalog Products API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
from slugify import slugify

from app.db.database import get_db
from app.db import models
from app.schemas import catalog_product as catalog_schema
from app.core.security import get_current_active_admin

router = APIRouter()


@router.get("/", response_model=catalog_schema.CatalogProductList)
async def list_catalog_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    category_id: Optional[int] = None,
    brand: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """List catalog products with filtering and pagination (admin only)"""
    
    # Base query with seller products count and min price
    query = db.query(
        models.CatalogProduct,
        func.count(models.Product.id).label('seller_products_count'),
        func.min(models.Product.current_price).label('min_price')
    ).outerjoin(
        models.Product,
        models.Product.catalog_product_id == models.CatalogProduct.id
    ).group_by(models.CatalogProduct.id)
    
    # Filters
    if category_id:
        query = query.filter(models.CatalogProduct.category_id == category_id)
    
    if brand:
        query = query.filter(models.CatalogProduct.brand.ilike(f"%{brand}%"))
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (models.CatalogProduct.title.ilike(search_term)) |
            (models.CatalogProduct.slug.ilike(search_term)) |
            (models.CatalogProduct.brand.ilike(search_term))
        )
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    results = query.order_by(desc(models.CatalogProduct.created_at)).offset(skip).limit(limit).all()
    
    # Format response
    items = []
    for catalog_product, seller_count, min_price in results:
        # Get category name
        category_name = catalog_product.category.name if catalog_product.category else None
        
        item_dict = {
            **catalog_product.__dict__,
            "seller_products_count": seller_count or 0,
            "min_price": float(min_price) if min_price else None,
            "category_name": category_name
        }
        items.append(catalog_schema.CatalogProduct(**item_dict))
    
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{catalog_id}", response_model=catalog_schema.CatalogProduct)
async def get_catalog_product(
    catalog_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Get catalog product by ID (admin only)"""
    
    # Query with seller products count and min price
    result = db.query(
        models.CatalogProduct,
        func.count(models.Product.id).label('seller_products_count'),
        func.min(models.Product.current_price).label('min_price')
    ).outerjoin(
        models.Product,
        models.Product.catalog_product_id == models.CatalogProduct.id
    ).filter(
        models.CatalogProduct.id == catalog_id
    ).group_by(models.CatalogProduct.id).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catalog product not found"
        )
    
    catalog_product, seller_count, min_price = result
    
    # Get category name
    category_name = catalog_product.category.name if catalog_product.category else None
    
    item_dict = {
        **catalog_product.__dict__,
        "seller_products_count": seller_count or 0,
        "min_price": float(min_price) if min_price else None,
        "category_name": category_name
    }
    
    return catalog_schema.CatalogProduct(**item_dict)


@router.post("/", response_model=catalog_schema.CatalogProduct, status_code=status.HTTP_201_CREATED)
async def create_catalog_product(
    catalog_data: catalog_schema.CatalogProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Create new catalog product (admin only)"""
    
    # Generate slug if not provided
    if not catalog_data.slug:
        catalog_data.slug = slugify(catalog_data.title)
    else:
        catalog_data.slug = slugify(catalog_data.slug)
    
    # Check if slug exists
    existing_slug = db.query(models.CatalogProduct).filter(
        models.CatalogProduct.slug == catalog_data.slug
    ).first()
    
    if existing_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Catalog product with slug '{catalog_data.slug}' already exists"
        )
    
    # Create catalog product
    catalog_product = models.CatalogProduct(**catalog_data.dict())
    db.add(catalog_product)
    db.commit()
    db.refresh(catalog_product)
    
    # Get category name
    category_name = catalog_product.category.name if catalog_product.category else None
    
    item_dict = {
        **catalog_product.__dict__,
        "seller_products_count": 0,
        "min_price": None,
        "category_name": category_name
    }
    
    return catalog_schema.CatalogProduct(**item_dict)


@router.put("/{catalog_id}", response_model=catalog_schema.CatalogProduct)
async def update_catalog_product(
    catalog_id: int,
    catalog_update: catalog_schema.CatalogProductUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Update catalog product (admin only)"""
    
    catalog_product = db.query(models.CatalogProduct).filter(
        models.CatalogProduct.id == catalog_id
    ).first()
    
    if not catalog_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catalog product not found"
        )
    
    # Update fields
    update_data = catalog_update.dict(exclude_unset=True)
    
    # Slugify slug if updated
    if 'slug' in update_data and update_data['slug']:
        new_slug = slugify(update_data['slug'])
        
        # Check if new slug exists (and is not the current product)
        existing_slug = db.query(models.CatalogProduct).filter(
            models.CatalogProduct.slug == new_slug,
            models.CatalogProduct.id != catalog_id
        ).first()
        
        if existing_slug:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Catalog product with slug '{new_slug}' already exists"
            )
        
        update_data['slug'] = new_slug
    
    # Apply updates
    for field, value in update_data.items():
        setattr(catalog_product, field, value)
    
    db.commit()
    db.refresh(catalog_product)
    
    # Get seller products count and min price
    result = db.query(
        func.count(models.Product.id).label('seller_products_count'),
        func.min(models.Product.current_price).label('min_price')
    ).filter(
        models.Product.catalog_product_id == catalog_id
    ).first()
    
    seller_count, min_price = result if result else (0, None)
    
    # Get category name
    category_name = catalog_product.category.name if catalog_product.category else None
    
    item_dict = {
        **catalog_product.__dict__,
        "seller_products_count": seller_count or 0,
        "min_price": float(min_price) if min_price else None,
        "category_name": category_name
    }
    
    return catalog_schema.CatalogProduct(**item_dict)


@router.delete("/{catalog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_catalog_product(
    catalog_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Delete catalog product (admin only)
    
    Note: This will also unlink all seller products from this catalog
    """
    
    catalog_product = db.query(models.CatalogProduct).filter(
        models.CatalogProduct.id == catalog_id
    ).first()
    
    if not catalog_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catalog product not found"
        )
    
    # Unlink seller products
    db.query(models.Product).filter(
        models.Product.catalog_product_id == catalog_id
    ).update({"catalog_product_id": None})
    
    # Delete catalog product
    db.delete(catalog_product)
    db.commit()
    
    return None


@router.get("/{catalog_id}/seller-products", response_model=list)
async def get_catalog_seller_products(
    catalog_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Get seller products linked to this catalog product (admin only)"""
    
    catalog_product = db.query(models.CatalogProduct).filter(
        models.CatalogProduct.id == catalog_id
    ).first()
    
    if not catalog_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catalog product not found"
        )
    
    seller_products = db.query(models.Product).filter(
        models.Product.catalog_product_id == catalog_id
    ).all()
    
    return [
        {
            "id": p.id,
            "asin": p.asin,
            "title": p.title,
            "current_price": float(p.current_price) if p.current_price else None,
            "brand": p.brand,
            "is_active": p.is_active,
            "is_available": p.is_available
        }
        for p in seller_products
    ]
