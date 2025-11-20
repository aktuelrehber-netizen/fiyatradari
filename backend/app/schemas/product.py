from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal


class ProductBase(BaseModel):
    asin: str
    title: str
    description: Optional[str] = None
    brand: Optional[str] = None
    category_id: int
    current_price: Optional[Decimal] = None
    list_price: Optional[Decimal] = None
    currency: str = "TRY"
    image_url: Optional[str] = None
    detail_page_url: Optional[str] = None
    availability: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    amazon_data: Optional[Dict[str, Any]] = {}
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    category_id: Optional[int] = None
    current_price: Optional[Decimal] = None
    list_price: Optional[Decimal] = None
    currency: Optional[str] = None
    image_url: Optional[str] = None
    detail_page_url: Optional[str] = None
    availability: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    amazon_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_available: Optional[bool] = None


class Product(ProductBase):
    id: int
    is_available: bool
    last_checked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProductWithDetails(Product):
    category_name: Optional[str] = None
    latest_deal: Optional[Any] = None
    price_change_24h: Optional[Decimal] = None
    price_change_7d: Optional[Decimal] = None


class PriceHistoryBase(BaseModel):
    product_id: int
    price: Decimal
    list_price: Optional[Decimal] = None
    currency: str = "TRY"
    discount_amount: Optional[Decimal] = None
    discount_percentage: Optional[float] = None
    is_available: bool = True
    availability_status: Optional[str] = None


class PriceHistoryCreate(PriceHistoryBase):
    pass


class PriceHistory(PriceHistoryBase):
    id: int
    recorded_at: datetime
    
    class Config:
        from_attributes = True
