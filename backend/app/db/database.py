from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings

# Create database engine with optimized pool settings
# 4 uvicorn workers * 5 connections = 20 base + 10 overflow = 30 total
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,          # Base connection pool (4 workers * 5)
    max_overflow=10,       # Additional overflow connections
    pool_recycle=3600,     # Recycle connections after 1 hour
    pool_timeout=30,       # Wait 30s for connection from pool
    echo=False             # Disable SQL query logging for performance
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
