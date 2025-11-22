from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, JSON, Index, Numeric
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.db.base import Base


class User(Base):
    """User model for admin authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Category(Base):
    """Product categories with Amazon browse node mapping"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)
    
    # Multiple Amazon Browse Node IDs (JSON array)
    # Example: ["13393813031", "13393814031"] for "Türk Kahve", "Filtre Kahve"
    amazon_browse_node_ids = Column(JSON, default=[])
    
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # SEO fields
    meta_title = Column(String(255))
    meta_description = Column(Text)
    meta_keywords = Column(Text)
    display_order = Column(Integer, default=0)
    
    # Product selection rules (JSON)
    # Popüler ve kaliteli ürünleri filtrelemek için
    selection_rules = Column(JSON, default={})
    # Example: {
    #     "min_rating": 4.0,
    #     "max_rating": 5.0,
    #     "min_review_count": 50,
    #     "min_price": 100.0,
    #     "max_price": 5000.0,
    #     "min_discount_percentage": 20.0,
    #     "include_keywords": ["premium", "profesyonel"],
    #     "exclude_keywords": ["ikinci el", "yenilenmiş"],
    #     "only_prime": true,
    #     "only_deals": false
    # }
    
    # Tracking settings
    check_interval_hours = Column(Integer, default=6)
    max_products = Column(Integer, default=100)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    parent = relationship("Category", remote_side=[id], backref="subcategories")
    products = relationship("Product", back_populates="category")
    
    @property
    def product_count(self):
        """Dynamic property for product count"""
        return len(self.products) if self.products else 0
    
    @property
    def active_deal_count(self):
        """Dynamic property for active deal count"""
        if not self.products:
            return 0
        return sum(1 for p in self.products for d in p.deals if d.is_active)


class Product(Base):
    """Amazon products being tracked"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    asin = Column(String(20), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    brand = Column(String(255))
    
    # Category
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    
    # Current pricing
    current_price = Column(Numeric(10, 2))
    list_price = Column(Numeric(10, 2))  # Original/MSRP price
    currency = Column(String(3), default="TRY")
    
    # Product details
    image_url = Column(String(500))
    detail_page_url = Column(String(500))
    availability = Column(String(100))
    
    # Ratings
    rating = Column(Float)
    review_count = Column(Integer)
    
    # Amazon data (JSON)
    amazon_data = Column(JSON, default={})
    
    # Tracking
    is_active = Column(Boolean, default=True)
    is_available = Column(Boolean, default=True)
    last_checked_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    category = relationship("Category", back_populates="products")
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    deals = relationship("Deal", back_populates="product", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('ix_products_category_active', 'category_id', 'is_active'),
        Index('ix_products_last_checked', 'last_checked_at'),
    )


class PriceHistory(Base):
    """Price change history for products"""
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    # Price data
    price = Column(Numeric(10, 2), nullable=False)
    list_price = Column(Numeric(10, 2))
    currency = Column(String(3), default="TRY")
    
    # Discount calculation
    discount_amount = Column(Numeric(10, 2))
    discount_percentage = Column(Float)
    
    # Availability
    is_available = Column(Boolean, default=True)
    availability_status = Column(String(100))
    
    # Timestamp
    recorded_at = Column(DateTime, default=func.now(), index=True)
    
    # Relationships
    product = relationship("Product", back_populates="price_history")
    
    # Indexes
    __table_args__ = (
        Index('ix_price_history_product_recorded', 'product_id', 'recorded_at'),
    )


class Deal(Base):
    """Detected deals and promotions"""
    __tablename__ = "deals"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    # Deal details
    title = Column(String(500), nullable=False)
    description = Column(Text)
    
    # Price information
    original_price = Column(Numeric(10, 2), nullable=False)
    deal_price = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), nullable=False)
    discount_percentage = Column(Float, nullable=False)
    currency = Column(String(3), default="TRY")
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime)
    
    # Telegram
    telegram_sent = Column(Boolean, default=False)
    telegram_message_id = Column(String(50))
    telegram_sent_at = Column(DateTime)
    
    # Validity
    valid_from = Column(DateTime, default=func.now())
    valid_until = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="deals")
    
    # Indexes
    __table_args__ = (
        Index('ix_deals_active_published', 'is_active', 'is_published'),
        Index('ix_deals_telegram_sent', 'telegram_sent'),
        Index('ix_deals_created_at', 'created_at'),
    )


class SystemSetting(Base):
    """System-wide settings"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text)
    data_type = Column(String(20), default="string")  # string, int, float, bool, json
    description = Column(Text)
    group = Column(String(50), default="general")  # general, amazon, telegram, worker, proxy
    is_secret = Column(Boolean, default=False)  # Hide value in UI (passwords, API keys)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class WorkerLog(Base):
    """Worker job execution logs"""
    __tablename__ = "worker_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String(100), nullable=False, index=True)
    job_type = Column(String(50), nullable=False)  # fetch_products, check_prices, send_telegram, etc.
    
    # Status
    status = Column(String(20), nullable=False, index=True)  # pending, running, completed, failed
    
    # Execution details
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)
    
    # Results
    items_processed = Column(Integer, default=0)
    items_created = Column(Integer, default=0)
    items_updated = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    
    # Error details
    error_message = Column(Text)
    error_trace = Column(Text)
    
    # Additional data
    job_metadata = Column(JSON, default={})
    
    created_at = Column(DateTime, default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('ix_worker_logs_job_status', 'job_name', 'status'),
        Index('ix_worker_logs_created_at', 'created_at'),
    )
