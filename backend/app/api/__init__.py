from fastapi import APIRouter

from app.api import auth, users, categories, products, deals, settings, workers, amazon, cache, system

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(deals.router, prefix="/deals", tags=["deals"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(workers.router, prefix="/workers", tags=["workers"])
api_router.include_router(amazon.router, prefix="/amazon", tags=["amazon"])
api_router.include_router(cache.router, prefix="/cache", tags=["cache"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
