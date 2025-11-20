import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()


class Config:
    """Worker configuration - reads from DB first, then .env"""
    
    _db_settings_cache = None
    _db_settings_loaded = False
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fiyatradari:fiyatradari123@localhost:5432/fiyatradari")
    
    @classmethod
    def _load_db_settings(cls):
        """Load settings from database (called once)"""
        if cls._db_settings_loaded:
            return cls._db_settings_cache
        
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(cls.DATABASE_URL)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT key, value FROM system_settings"))
                cls._db_settings_cache = {row[0]: row[1] for row in result}
                cls._db_settings_loaded = True
        except Exception:
            cls._db_settings_cache = {}
            cls._db_settings_loaded = True
        
        return cls._db_settings_cache
    
    @classmethod
    def _get_setting(cls, key: str, env_key: str, default: str = "") -> str:
        """Get setting from DB first, then .env, then default"""
        # Try database first
        db_settings = cls._load_db_settings()
        
        # Try dot notation (e.g., telegram.bot_token)
        if key in db_settings and db_settings[key]:
            return db_settings[key]
        
        # Try underscore notation (e.g., telegram_bot_token)
        key_underscore = key.replace(".", "_")
        if key_underscore in db_settings and db_settings[key_underscore]:
            return db_settings[key_underscore]
        
        # Fall back to environment variable
        return os.getenv(env_key, default)
    
    # Amazon PA API - read from DB or .env
    @property
    def AMAZON_ACCESS_KEY(self):
        return self._get_setting("amazon.access_key", "AMAZON_ACCESS_KEY", "")
    
    @property
    def AMAZON_SECRET_KEY(self):
        return self._get_setting("amazon.secret_key", "AMAZON_SECRET_KEY", "")
    
    @property
    def AMAZON_PARTNER_TAG(self):
        return self._get_setting("amazon.partner_tag", "AMAZON_PARTNER_TAG", "")
    
    @property
    def AMAZON_REGION(self):
        return self._get_setting("amazon.region", "AMAZON_REGION", "eu-west-1")
    
    @property
    def AMAZON_MARKETPLACE(self):
        return self._get_setting("amazon.marketplace", "AMAZON_MARKETPLACE", "www.amazon.com.tr")
    
    # Telegram - read from DB or .env
    @property
    def TELEGRAM_BOT_TOKEN(self):
        return self._get_setting("telegram.bot_token", "TELEGRAM_BOT_TOKEN", "")
    
    @property
    def TELEGRAM_CHANNEL_ID(self):
        return self._get_setting("telegram.channel_id", "TELEGRAM_CHANNEL_ID", "")
    
    # Worker Settings
    WORKER_INTERVAL_MINUTES = int(os.getenv("WORKER_INTERVAL_MINUTES", "60"))
    PRICE_CHECK_INTERVAL_HOURS = int(os.getenv("PRICE_CHECK_INTERVAL_HOURS", "6"))
    DEAL_THRESHOLD_PERCENTAGE = float(os.getenv("DEAL_THRESHOLD_PERCENTAGE", "15"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Celery Configuration (for distributed task queue)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", f"{REDIS_URL}/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", f"{REDIS_URL}/1")


config = Config()
