"""
Monitoring and Error Tracking Configuration
Sentry, Prometheus, and Performance Monitoring
"""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from prometheus_client import Counter, Histogram, Gauge
from prometheus_fastapi_instrumentator import Instrumentator
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


# Prometheus Metrics
request_counter = Counter(
    'fiyatradari_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'fiyatradari_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_users = Gauge(
    'fiyatradari_active_users',
    'Number of active users'
)

products_total = Gauge(
    'fiyatradari_products_total',
    'Total number of products'
)

deals_total = Gauge(
    'fiyatradari_deals_total',
    'Total number of active deals'
)

worker_tasks = Counter(
    'fiyatradari_worker_tasks_total',
    'Total worker tasks processed',
    ['task_name', 'status']
)

cache_hits = Counter(
    'fiyatradari_cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses = Counter(
    'fiyatradari_cache_misses_total',
    'Total cache misses',
    ['cache_type']
)


def init_sentry(dsn: Optional[str] = None):
    """Initialize Sentry error tracking"""
    if not dsn or settings.ENVIRONMENT != "production":
        logger.info("Sentry disabled (development mode or no DSN)")
        return
    
    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=settings.ENVIRONMENT,
            # Performance monitoring
            traces_sample_rate=0.1,  # 10% of transactions
            # Error sampling
            sample_rate=1.0,  # 100% of errors
            # Integrations
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                RedisIntegration(),
            ],
            # Release tracking
            release=f"fiyatradari@1.0.0",
            # Additional context
            before_send=before_send_filter,
            # Performance
            profiles_sample_rate=0.1,
        )
        logger.info("✅ Sentry initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Sentry: {e}")


def before_send_filter(event, hint):
    """Filter events before sending to Sentry"""
    # Don't send health check errors
    if 'request' in event and event['request'].get('url', '').endswith('/health'):
        return None
    
    # Don't send 404 errors (expected behavior)
    if event.get('level') == 'error':
        exc_info = hint.get('exc_info')
        if exc_info and '404' in str(exc_info[1]):
            return None
    
    return event


def init_prometheus(app):
    """Initialize Prometheus metrics"""
    try:
        # Auto-instrument FastAPI app
        instrumentator = Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=True,
            should_respect_env_var=True,
            should_instrument_requests_inprogress=True,
            excluded_handlers=["/metrics", "/health", "/docs", "/openapi.json"],
            env_var_name="ENABLE_METRICS",
            inprogress_name="fiyatradari_requests_inprogress",
            inprogress_labels=True,
        )
        
        # Add custom metrics
        instrumentator.add(
            lambda info: request_counter.labels(
                method=info.method,
                endpoint=info.modified_handler,
                status=info.response.status_code
            ).inc()
        )
        
        instrumentator.add(
            lambda info: request_duration.labels(
                method=info.method,
                endpoint=info.modified_handler
            ).observe(info.modified_duration)
        )
        
        # Instrument the app
        instrumentator.instrument(app)
        
        # Don't expose here - we have manual endpoint in main.py
        # instrumentator.expose(app, endpoint="/metrics", tags=["monitoring"])
        
        logger.info("✅ Prometheus metrics initialized")
        return instrumentator
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Prometheus: {e}")
        return None


def track_user_action(user_id: int, action: str, metadata: dict = None):
    """Track user behavior for analytics"""
    try:
        # In production, send to analytics service
        if settings.ENVIRONMENT == "production":
            # TODO: Send to analytics platform (Mixpanel, Amplitude, etc.)
            pass
        
        logger.info(f"User action: {user_id} - {action} - {metadata}")
    except Exception as e:
        logger.error(f"Failed to track user action: {e}")


def track_performance(operation: str, duration: float, metadata: dict = None):
    """Track performance metrics"""
    try:
        # Record in Prometheus
        if duration > 1.0:  # Slow operation (> 1 second)
            logger.warning(f"Slow operation: {operation} took {duration:.2f}s - {metadata}")
        
        # In production, send to APM
        if settings.ENVIRONMENT == "production":
            # TODO: Send to APM service (New Relic, DataDog, etc.)
            pass
            
    except Exception as e:
        logger.error(f"Failed to track performance: {e}")
