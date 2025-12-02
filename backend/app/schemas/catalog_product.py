"""
Catalog Product schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CatalogProductBase(BaseModel):
    """Base catalog product schema"""
    title: str = Field(..., max_length=500)
    slug: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    category_id: int
    brand: Optional[str] = Field(None, max_length=255)
    meta_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = None


class CatalogProductCreate(CatalogProductBase):
    """Schema for creating catalog product"""
    pass


class CatalogProductUpdate(BaseModel):
    """Schema for updating catalog product (all fields optional)"""
    title: Optional[str] = Field(None, max_length=500)
    slug: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    category_id: Optional[int] = None
    brand: Optional[str] = Field(None, max_length=255)
    meta_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = None


class CatalogProduct(CatalogProductBase):
    """Schema for catalog product response"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    seller_products_count: int = 0
    min_price: Optional[float] = None
    category_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class CatalogProductList(BaseModel):
    """Schema for paginated catalog products list"""
    items: list[CatalogProduct]
    total: int
    skip: int
    limit: int
