"""
API routes for administrative tasks.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth.dependencies import require_admin
from app.utils.cache import cache

router = APIRouter()

@router.delete("/cache", tags=["Admin"])
async def clear_cache(
    request: Request,
    pattern: Optional[str] = None,
    current_user=Depends(require_admin())
):
    """Admin endpoint to clear Redis cache."""
    cleared_count = cache.clear_cache(pattern)
    return {"message": f"Cleared {cleared_count} cache keys.", "pattern": pattern or "*"}

@router.get("/cache/stats", tags=["Admin"])
async def get_cache_stats(
    request: Request,
    current_user=Depends(require_admin())
):
    """Admin endpoint to get cache statistics."""
    return cache.get_cache_stats()

@router.get("/users", tags=["Admin"])
async def list_users(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    current_user=Depends(require_admin())
):
    """Admin endpoint to list all users."""
    # TODO: Implement user listing
    return {"message": "User listing functionality to be implemented"}

@router.post("/users/{user_id}/deactivate", tags=["Admin"])
async def deactivate_user(
    user_id: str,
    request: Request,
    current_user=Depends(require_admin())
):
    """Admin endpoint to deactivate a user."""
    # TODO: Implement user deactivation
    return {"message": f"User {user_id} deactivation functionality to be implemented"} 