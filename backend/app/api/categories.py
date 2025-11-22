from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import httpx
from celery import Celery
import os

from app.db.database import get_db
from app.db import models
from app.schemas import category as category_schema
from app.core.security import get_current_active_admin

router = APIRouter()

# Celery client for task dispatch
celery_app = Celery(
    'tasks',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
)


@router.get("/", response_model=List[category_schema.CategoryWithStats])
async def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    is_active: Optional[bool] = None,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List all categories with statistics"""
    
    # Simple query without complex joins to avoid SQL errors
    query = db.query(models.Category)
    
    if is_active is not None:
        query = query.filter(models.Category.is_active == is_active)
    
    if parent_id is not None:
        query = query.filter(models.Category.parent_id == parent_id)
    
    categories = query.offset(skip).limit(limit).all()
    
    result = []
    for cat in categories:
        # Get counts separately
        product_count = db.query(models.Product).filter(
            models.Product.category_id == cat.id
        ).count()
        
        deal_count = db.query(models.Deal).join(models.Product).filter(
            models.Product.category_id == cat.id,
            models.Deal.is_active == True
        ).count()
        
        cat_dict = category_schema.Category.from_orm(cat).dict()
        cat_dict['product_count'] = product_count
        cat_dict['active_deal_count'] = deal_count
        result.append(category_schema.CategoryWithStats(**cat_dict))
    
    return result


@router.post("/", response_model=category_schema.Category, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: category_schema.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Create a new category (admin only)"""
    
    # Validate name is not empty
    if not category.name or not category.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name is required"
        )
    
    # Check if name already exists (case-insensitive)
    existing_name = db.query(models.Category).filter(
        models.Category.name.ilike(category.name.strip())
    ).first()
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with name '{category.name}' already exists"
        )
    
    # Check if slug exists
    existing_slug = db.query(models.Category).filter(
        models.Category.slug == category.slug
    ).first()
    if existing_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with slug '{category.slug}' already exists"
        )
    
    # Validate parent exists if provided
    if category.parent_id:
        parent = db.query(models.Category).filter(
            models.Category.id == category.parent_id
        ).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent category with ID {category.parent_id} not found"
            )
    
    db_category = models.Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    return db_category


@router.get("/slug/{slug}", response_model=category_schema.CategoryWithStats)
async def get_category_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """Get category by slug"""
    
    category = db.query(models.Category).filter(models.Category.slug == slug).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with slug '{slug}' not found"
        )
    
    # Get stats
    product_count = db.query(models.Product).filter(
        models.Product.category_id == category.id
    ).count()
    
    deal_count = db.query(models.Deal).join(models.Product).filter(
        models.Product.category_id == category.id,
        models.Deal.is_active == True
    ).count()
    
    cat_dict = category_schema.Category.from_orm(category).dict()
    cat_dict['product_count'] = product_count
    cat_dict['active_deal_count'] = deal_count
    
    return category_schema.CategoryWithStats(**cat_dict)


@router.get("/{category_id}", response_model=category_schema.Category)
async def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """Get category by ID"""
    
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return category


@router.put("/{category_id}", response_model=category_schema.Category)
async def update_category(
    category_id: int,
    category_update: category_schema.CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Update category (admin only)"""
    
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Validate name is not empty if being updated
    if category_update.name is not None:
        if not category_update.name or not category_update.name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category name cannot be empty"
            )
        
        # Check if name already exists (excluding current category, case-insensitive)
        existing_name = db.query(models.Category).filter(
            models.Category.name.ilike(category_update.name.strip()),
            models.Category.id != category_id
        ).first()
        if existing_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with name '{category_update.name}' already exists"
            )
    
    # Check slug uniqueness if being updated
    if category_update.slug and category_update.slug != category.slug:
        existing_slug = db.query(models.Category).filter(
            models.Category.slug == category_update.slug
        ).first()
        if existing_slug:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with slug '{category_update.slug}' already exists"
            )
    
    # Validate parent exists if being updated
    if category_update.parent_id is not None:
        # Prevent self-referencing
        if category_update.parent_id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category cannot be its own parent"
            )
        
        parent = db.query(models.Category).filter(
            models.Category.id == category_update.parent_id
        ).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent category with ID {category_update.parent_id} not found"
            )
        
        # Prevent circular reference (check if new parent is a descendant)
        def is_descendant(parent_id: int, ancestor_id: int) -> bool:
            parent_cat = db.query(models.Category).filter(models.Category.id == parent_id).first()
            if not parent_cat or not parent_cat.parent_id:
                return False
            if parent_cat.parent_id == ancestor_id:
                return True
            return is_descendant(parent_cat.parent_id, ancestor_id)
        
        if is_descendant(category_update.parent_id, category_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot set parent: would create circular reference"
            )
    
    update_data = category_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    
    db.commit()
    db.refresh(category)
    
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Delete category (admin only)"""
    
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Check if category has products
    product_count = db.query(models.Product).filter(models.Product.category_id == category_id).count()
    if product_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category with {product_count} products"
        )
    
    db.delete(category)
    db.commit()
    
    return None


@router.post("/{category_id}/fetch-products", status_code=status.HTTP_202_ACCEPTED)
async def trigger_product_fetch(
    category_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """
    Manually trigger product fetching for a category (admin only)
    This will dispatch Celery tasks to fetch products from Amazon
    """
    
    # Validate category exists and is active
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    if not category.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category is not active"
        )
    
    if not category.amazon_browse_node_ids or len(category.amazon_browse_node_ids) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category has no Amazon browse nodes configured"
        )
    
    # Dispatch Celery tasks directly to message broker
    tasks_dispatched = 0
    try:
        max_products = category.max_products or 100
        max_pages = min((max_products // 10), 10)
        
        for browse_node in category.amazon_browse_node_ids:
            for page in range(1, max_pages + 1):
                celery_app.send_task(
                    'celery_tasks.fetch_category_products',
                    args=[category_id, browse_node, page],
                    kwargs={},
                    queue='product_fetch',  # Specify queue
                    priority=8
                )
                tasks_dispatched += 1
    except Exception as e:
        print(f"Error dispatching tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to dispatch tasks: {str(e)}"
        )
    
    # Use actual dispatched count
    total_tasks = tasks_dispatched
    
    return {
        "status": "accepted",
        "message": f"Product fetch triggered for category '{category.name}'",
        "category_id": category_id,
        "category_name": category.name,
        "browse_nodes": len(category.amazon_browse_node_ids),
        "pages_per_node": max_pages,
        "total_tasks": total_tasks,
        "estimated_products": total_tasks * 10
    }
