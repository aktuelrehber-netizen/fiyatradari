from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Union
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = "postgresql://fiyatradari:fiyatradari123@localhost:5432/fiyatradari"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production-32chars-minimum"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    
    @field_validator('SECRET_KEY', mode='before')
    @classmethod
    def validate_secret_key(cls, v):
        # Only enforce in production
        from os import getenv
        environment = getenv('ENVIRONMENT', 'development')
        
        if environment == 'production':
            if not v or v.startswith('dev-') or len(v) < 32:
                raise ValueError("SECRET_KEY must be set to a secure random value (32+ chars) in production")
        elif v and len(v) < 32:
            import logging
            logging.warning("⚠️  WARNING: SECRET_KEY is too short! Generate a secure key for production!")
        
        return v
    
    # Amazon PA API
    AMAZON_ACCESS_KEY: str = ""
    AMAZON_SECRET_KEY: str = ""
    AMAZON_PARTNER_TAG: str = ""
    AMAZON_REGION: str = "eu-west-1"
    AMAZON_MARKETPLACE: str = "www.amazon.com.tr"
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHANNEL_ID: str = ""
    
    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] = "http://localhost:3000,http://localhost:3001,http://localhost:3002"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra='ignore'
    )
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v


settings = Settings()
