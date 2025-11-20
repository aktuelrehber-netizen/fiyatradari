from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from contextlib import contextmanager
from datetime import datetime

from config import config

# Create engine with connection pool limits
# With 10 workers * (2 + 3) = 50 max connections
engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=2,           # Base connections per worker
    max_overflow=3,        # Additional connections when needed
    pool_recycle=3600,     # Recycle connections after 1 hour
    pool_timeout=30        # Wait 30s for connection from pool
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class
Base = declarative_base()


@contextmanager
def get_db():
    """Get database session context manager"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Import models from backend (simplified versions)
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    username = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    slug = Column(String(255), unique=True)
    description = Column(Text)
    amazon_browse_node_ids = Column(JSON, default=[])  # Multiple nodes
    parent_id = Column(Integer, ForeignKey("categories.id"))
    is_active = Column(Boolean, default=True)
    selection_rules = Column(JSON, default={})
    check_interval_hours = Column(Integer, default=6)
    max_products = Column(Integer, default=100)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
    
    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    asin = Column(String(20), unique=True, index=True)
    title = Column(String(500))
    description = Column(Text)
    brand = Column(String(255))
    category_id = Column(Integer, ForeignKey("categories.id"), index=True)
    current_price = Column(Numeric(10, 2))
    list_price = Column(Numeric(10, 2))
    currency = Column(String(3), default="TRY")
    image_url = Column(String(500))
    detail_page_url = Column(String(500))
    availability = Column(String(100))
    rating = Column(Float)
    review_count = Column(Integer)
    amazon_data = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    is_available = Column(Boolean, default=True)
    last_checked_at = Column(DateTime)
    check_priority = Column(Integer, default=50, index=True)  # Priority score 0-100
    check_count = Column(Integer, default=0)  # Number of times checked
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
    
    category = relationship("Category", back_populates="products")
    price_history = relationship("PriceHistory", back_populates="product")
    deals = relationship("Deal", back_populates="product")


class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    price = Column(Numeric(10, 2))
    list_price = Column(Numeric(10, 2))
    currency = Column(String(3), default="TRY")
    discount_amount = Column(Numeric(10, 2))
    discount_percentage = Column(Float)
    is_available = Column(Boolean, default=True)
    availability_status = Column(String(100))
    recorded_at = Column(DateTime, default=func.now())
    
    product = relationship("Product", back_populates="price_history")


class Deal(Base):
    __tablename__ = "deals"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    title = Column(String(500))
    description = Column(Text)
    original_price = Column(Numeric(10, 2))
    deal_price = Column(Numeric(10, 2))
    discount_amount = Column(Numeric(10, 2))
    discount_percentage = Column(Float)
    currency = Column(String(3), default="TRY")
    is_active = Column(Boolean, default=True, index=True)
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime)
    telegram_sent = Column(Boolean, default=False)
    telegram_message_id = Column(String(50))
    telegram_sent_at = Column(DateTime)
    valid_from = Column(DateTime, default=func.now())
    valid_until = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
    
    product = relationship("Product", back_populates="deals")


class WorkerLog(Base):
    """Worker execution log"""
    __tablename__ = 'worker_logs'
    
    id = Column(Integer, primary_key=True)
    job_name = Column(String(200))
    job_type = Column(String(100))
    status = Column(String(50))  # pending, running, completed, failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    items_processed = Column(Integer, nullable=True)
    items_created = Column(Integer, nullable=True)
    items_updated = Column(Integer, nullable=True)
    items_failed = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    job_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())


class SystemSetting(Base):
    """System settings (for reading from database)"""
    __tablename__ = 'system_settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
