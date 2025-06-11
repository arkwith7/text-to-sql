"""
API routes for administrative tasks.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth.service import AuthService
from app.utils.cache import cache

router = APIRouter()

async def get_admin_user(request: Request):
    auth_service: AuthService = request.app.state.auth_service
    return await auth_service.get_current_user(request, is_admin=True, required=True)

@router.delete("/admin/cache", tags=["Admin"])
async def clear_cache(
    request: Request,
    pattern: Optional[str] = None,
    current_user=Depends(get_admin_user)
):
    """Admin endpoint to clear Redis cache."""
    cleared_count = cache.clear_cache(pattern)
    return {"message": f"Cleared {cleared_count} cache keys.", "pattern": pattern or "*"}

@router.get("/admin/cache/stats", tags=["Admin"])
async def get_cache_stats(
    request: Request,
    current_user=Depends(get_admin_user)
):
    """Admin endpoint to get cache statistics."""
    return cache.get_cache_stats() 