"""
Celery Application Configuration
Distributed task queue for handling 1M+ products

Usage:
    # Start Celery worker
    celery -A celery_app worker --loglevel=info --concurrency=4

    # Start Celery beat (scheduler)
    celery -A celery_app beat --loglevel=info
    
    # Monitor tasks
    celery -A celery_app flower
"""
from celery import Celery
from celery.schedules import crontab
from kombu import Queue, Exchange
from config import config

# Initialize Celery app
app = Celery('fiyatradari')

# Celery Configuration
app.conf.update(
    # Broker & Backend
    broker_url=config.CELERY_BROKER_URL,
    result_backend=config.CELERY_RESULT_BACKEND,
    
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task settings
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 min soft limit
    task_acks_late=True,  # Acknowledge after task completes
    worker_prefetch_multiplier=1,  # One task at a time per worker
    
    # Results
    result_expires=86400,  # Keep results for 24 hours
    
    # Retry settings
    task_autoretry_for=(Exception,),
    task_retry_kwargs={'max_retries': 3},
    task_default_retry_delay=60,  # 1 minute delay
    
    # Rate limiting
    task_default_rate_limit='100/m',  # 100 tasks per minute default
    
    # Queue routing
    task_routes={
        'celery_tasks.check_product_price': {'queue': 'price_check'},
        'celery_tasks.fetch_category_products': {'queue': 'product_fetch'},
        'celery_tasks.send_deal_notification': {'queue': 'notifications'},
        'celery_tasks.batch_price_check': {'queue': 'batch_processing'},
        'celery_tasks.continuous_queue_refill': {'queue': 'price_check'},  # Refill uses price_check queue
        'celery_tasks.update_product_priorities': {'queue': 'batch_processing'},
        'celery_tasks.schedule_high_priority_checks': {'queue': 'batch_processing'},
        'celery_tasks.schedule_medium_priority_checks': {'queue': 'batch_processing'},
        'celery_tasks.schedule_low_priority_checks': {'queue': 'batch_processing'},
        'celery_tasks.schedule_notifications': {'queue': 'notifications'},
    },
    
    # Queue definitions with priorities
    task_queues=(
        Queue('price_check', Exchange('price_check'), routing_key='price_check',
              queue_arguments={'x-max-priority': 10}),
        Queue('product_fetch', Exchange('product_fetch'), routing_key='product_fetch',
              queue_arguments={'x-max-priority': 5}),
        Queue('notifications', Exchange('notifications'), routing_key='notifications',
              queue_arguments={'x-max-priority': 8}),
        Queue('batch_processing', Exchange('batch_processing'), routing_key='batch_processing',
              queue_arguments={'x-max-priority': 3}),
    ),
    
    # Beat schedule (periodic tasks) - ULTRA AGGRESSIVE SCHEDULING (CRAWLER MODE)
    beat_schedule={
        # Continuous queue refill - every 1 minute (MAXIMUM THROUGHPUT!)
        'continuous-queue-refill': {
            'task': 'celery_tasks.continuous_queue_refill',
            'schedule': crontab(minute='*/1'),  # Every 1 minute (was 3)
        },
        
        # High priority products - every 10 minutes (REAL-TIME DEALS!)
        'check-high-priority-products': {
            'task': 'celery_tasks.schedule_high_priority_checks',
            'schedule': crontab(minute='*/10'),  # Every 10 minutes (was 30)
        },
        
        # Medium priority products - every 1 hour (FAST TRACKING)
        'check-medium-priority-products': {
            'task': 'celery_tasks.schedule_medium_priority_checks',
            'schedule': crontab(minute=0, hour='*/1'),  # Every 1 hour (was 3)
        },
        
        # Low priority products - every 6 hours (2X FASTER)
        'check-low-priority-products': {
            'task': 'celery_tasks.schedule_low_priority_checks',
            'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours (was 12)
        },
        
        # Fetch new products - daily
        'fetch-new-products': {
            'task': 'celery_tasks.schedule_product_fetch',
            'schedule': crontab(minute=0, hour=4),  # 4 AM (unchanged)
        },
        
        # Send notifications - every 5 minutes (INSTANT ALERTS!)
        'send-notifications': {
            'task': 'celery_tasks.schedule_notifications',
            'schedule': crontab(minute='*/5'),  # Every 5 minutes (was 15)
        },
        
        # Update priorities - every 30 minutes (DYNAMIC ADJUSTMENT)
        'update-product-priorities': {
            'task': 'celery_tasks.update_product_priorities',
            'schedule': crontab(minute='*/30'),  # Every 30 minutes (was 2 hours)
        },
        
        # Cleanup old data - daily
        'cleanup-old-data': {
            'task': 'celery_tasks.cleanup_old_data',
            'schedule': crontab(minute=0, hour=2),  # 2 AM (unchanged)
        },
        
        # Update missing ratings via crawler - every 8 hours
        # NOTE: PA-API doesn't return customer reviews without special access
        # Runs 3x daily (25 products each = 75/day) to avoid bot detection
        'update-missing-ratings': {
            'task': 'celery_tasks.update_missing_ratings',
            'schedule': crontab(minute=0, hour='*/8'),  # Every 8 hours (00:00, 08:00, 16:00)
        },
    },
)

# Import tasks (must be after app configuration)
import celery_tasks  # noqa: E402

if __name__ == '__main__':
    app.start()
