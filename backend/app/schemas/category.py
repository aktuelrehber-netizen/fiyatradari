from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List


class SelectionRules(BaseModel):
    """Product selection rules for filtering"""
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="Minimum product rating")
    max_rating: Optional[float] = Field(None, ge=0, le=5, description="Maximum product rating")
    min_review_count: Optional[int] = Field(None, ge=0, description="Minimum number of reviews")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price")
    min_discount_percentage: Optional[float] = Field(None, ge=0, le=100, description="Minimum discount %")
    include_keywords: Optional[List[str]] = Field(default_factory=list, description="Keywords that must be present")
    exclude_keywords: Optional[List[str]] = Field(default_factory=list, description="Keywords to exclude")
    only_prime: Optional[bool] = Field(False, description="Only Prime eligible products")
    only_deals: Optional[bool] = Field(False, description="Only products with active deals")


class CategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    amazon_browse_node_ids: List[str] = Field(default_factory=list, description="Multiple Amazon Browse Node IDs")
    parent_id: Optional[int] = None
    is_active: bool = True
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    display_order: int = 0
    selection_rules: Optional[Dict[str, Any]] = Field(default_factory=dict)
    check_interval_hours: int = 6
    max_products: int = 100


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    amazon_browse_node_ids: Optional[List[str]] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    display_order: Optional[int] = None
    selection_rules: Optional[Dict[str, Any]] = None
    check_interval_hours: Optional[int] = None
    max_products: Optional[int] = None


class Category(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CategoryWithStats(Category):
    product_count: int = 0
    active_deal_count: int = 0
