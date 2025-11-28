from fastapi import APIRouter

from app.api import (
    auth, users, categories, products, deals, settings, 
    amazon, cache, products_fetch, celery_monitor, health
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(products_fetch.router, prefix="/products-fetch", tags=["products-fetch"])
api_router.include_router(deals.router, prefix="/deals", tags=["deals"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(amazon.router, prefix="/amazon", tags=["amazon"])
api_router.include_router(cache.router, prefix="/cache", tags=["cache"])
api_router.include_router(celery_monitor.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(health.router, tags=["health"])
