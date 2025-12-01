"""
Celery app configuration for background tasks
"""
from celery import Celery
from celery.schedules import crontab
import os

# Redis URL from environment
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# Create Celery app
celery_app = Celery(
    'fiyatradari',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.tasks']  # Task'ların bulunduğu modül
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Istanbul',
    enable_utc=False,
    task_track_started=True,
    result_extended=True,  # Task metadata'da name, args, kwargs'ı sakla
    broker_connection_retry_on_startup=True,  # Celery 6.0 için uyumluluk
    task_time_limit=3600,  # 1 saat max
    task_soft_time_limit=3300,  # 55 dakika soft limit
    worker_prefetch_multiplier=1,  # Bir task'ı al, bitir, sonraki
    worker_max_tasks_per_child=50,  # Her 50 task'ta worker restart
)

# Beat schedule - Scheduled tasks
celery_app.conf.beat_schedule = {
    # Günde 1 kere kategori kontrolü - Akşam 22:00
    'check-categories-for-update': {
        'task': 'app.tasks.check_categories_for_update',
        'schedule': crontab(hour=22, minute=0),  # Her gün 22:00
        'options': {'expires': 3600}  # 1 saat içinde çalışmazsa expire
    },
    
    # Her 5 dakikada bir istatistik güncelle
    'update-statistics': {
        'task': 'app.tasks.update_statistics',
        'schedule': 300.0,  # 5 dakika
    },
    
    # Gece yarısı eski deal'leri temizle
    'cleanup-old-deals': {
        'task': 'app.tasks.cleanup_old_deals',
        'schedule': crontab(hour=0, minute=0),  # 00:00
    },
    
    # Her 1 saatte bir deal fiyatlarını kontrol et (fiyat arttıysa deaktive et)
    'check-deal-prices': {
        'task': 'app.tasks.check_deal_prices',
        'schedule': 3600.0,  # 1 saat (3600 saniye)
        'options': {'expires': 3500}  # 58 dakika içinde expire
    },
    
    # Her 5 dakikada bir ürün fiyatlarını güncelle (batch)
    'update-product-prices-batch': {
        'task': 'app.tasks.update_product_prices_batch',
        'schedule': 300.0,  # 5 dakika (300 saniye)
        'options': {'expires': 280}  # 4.7 dakika içinde expire
    },
}

# Celery signals for logging
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task"""
    print(f'Request: {self.request!r}')
