from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.core.security import get_current_active_admin

try:
    from fastapi_cache import FastAPICache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

router = APIRouter()


@router.post("/clear")
async def clear_cache(
    pattern: Optional[str] = None,
    current_user = Depends(get_current_active_admin)
):
    """
    Clear FastAPI cache (Admin only)
    
    - **pattern**: Optional pattern to match cache keys (e.g., "deals:*")
    - If no pattern, clears all cache
    """
    if not CACHE_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Cache system not available"
        )
    
    try:
        # Clear all cache
        await FastAPICache.clear()
        
        return {
            "success": True,
            "message": "Cache cleared successfully",
            "pattern": pattern or "all"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get("/stats")
async def get_cache_stats(
    current_user = Depends(get_current_active_admin)
):
    """
    Get cache statistics (Admin only)
    """
    if not CACHE_AVAILABLE:
        return {
            "available": False,
            "message": "Cache system not available"
        }
    
    return {
        "available": True,
        "backend": "Redis",
        "ttl": {
            "deals": "30 seconds",
            "products": "60 seconds",
            "categories": "60 seconds"
        }
    }
