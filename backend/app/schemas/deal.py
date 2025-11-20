from __future__ import annotations
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, TYPE_CHECKING, Any
from decimal import Decimal

if TYPE_CHECKING:
    from .product import Product


class DealBase(BaseModel):
    product_id: int
    title: str
    description: Optional[str] = None
    original_price: Decimal
    deal_price: Decimal
    discount_amount: Decimal
    discount_percentage: float
    currency: str = "TRY"
    is_active: bool = True
    is_published: bool = False
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class DealCreate(DealBase):
    pass


class DealUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    original_price: Optional[Decimal] = None
    deal_price: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    discount_percentage: Optional[float] = None
    is_active: Optional[bool] = None
    is_published: Optional[bool] = None
    valid_until: Optional[datetime] = None


class Deal(DealBase):
    id: int
    telegram_sent: bool
    telegram_message_id: Optional[str] = None
    telegram_sent_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DealWithProduct(Deal):
    product_asin: Optional[str] = None
    product_title: Optional[str] = None
    product_image: Optional[str] = None
    product_url: Optional[str] = None
    category_name: Optional[str] = None
