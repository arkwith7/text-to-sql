"""
Admin endpoints for Text-to-SQL application.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from services.auth_dependencies import get_current_admin_user
from services.auth_service import UserResponse, AuthService
from services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter()

class UserManagementResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: str
    last_login: Optional[str] = None

class SystemStatusResponse(BaseModel):
    status: str
    uptime: str
    database_connections: Dict[str, str]
    cache_status: str
    total_users: int
    active_sessions: int

@router.get("/users", response_model=List[UserManagementResponse])
async def get_all_users(
    request: Request,
    current_user: UserResponse = Depends(get_current_admin_user),
    limit: int = 100,
    offset: int = 0
):
    """Get all users (admin only)."""
    try:
        auth_service: AuthService = request.app.state.auth_service
        
        users = await auth_service.get_all_users(limit=limit, offset=offset)
        
        return [
            UserManagementResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at.isoformat(),
                last_login=user.last_login.isoformat() if user.last_login else None
            )
            for user in users
        ]
        
    except Exception as e:
        logger.error(f"Failed to get all users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    new_role: str,
    request: Request,
    current_user: UserResponse = Depends(get_current_admin_user)
):
    """Update user role (admin only)."""
    try:
        auth_service: AuthService = request.app.state.auth_service
        
        await auth_service.update_user_role(user_id=user_id, new_role=new_role)
        
        return {"message": f"User role updated to {new_role}"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update user role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user role"
        )

@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    is_active: bool,
    request: Request,
    current_user: UserResponse = Depends(get_current_admin_user)
):
    """Update user active status (admin only)."""
    try:
        auth_service: AuthService = request.app.state.auth_service
        
        await auth_service.update_user_status(user_id=user_id, is_active=is_active)
        
        status_text = "activated" if is_active else "deactivated"
        return {"message": f"User {status_text} successfully"}
        
    except Exception as e:
        logger.error(f"Failed to update user status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user status"
        )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    current_user: UserResponse = Depends(get_current_admin_user)
):
    """Delete user (admin only)."""
    try:
        # Prevent admin from deleting themselves
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        auth_service: AuthService = request.app.state.auth_service
        
        await auth_service.delete_user(user_id=user_id)
        
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

@router.get("/system/status", response_model=SystemStatusResponse)
async def get_system_status(
    request: Request,
    current_user: UserResponse = Depends(get_current_admin_user)
):
    """Get system status (admin only)."""
    try:
        db_manager = request.app.state.db_manager
        auth_service: AuthService = request.app.state.auth_service
        
        # Get database connection status
        db_status = await db_manager.get_connection_status()
        
        # Get cache status
        cache = request.app.state.cache
        cache_status = "connected" if cache.redis_client else "disconnected"
        
        # Get user statistics
        total_users = await auth_service.get_total_user_count()
        
        return SystemStatusResponse(
            status="healthy",
            uptime="N/A",  # Would need to track application start time
            database_connections=db_status,
            cache_status=cache_status,
            total_users=total_users,
            active_sessions=0  # Would need to track active sessions
        )
        
    except Exception as e:
        logger.error(f"Failed to get system status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system status"
        )

@router.post("/system/cache/clear")
async def clear_system_cache(
    request: Request,
    current_user: UserResponse = Depends(get_current_admin_user)
):
    """Clear system cache (admin only)."""
    try:
        cache = request.app.state.cache
        
        # Clear all cache patterns
        cleared_count = await cache.clear_pattern("*")
        
        return {
            "message": "System cache cleared successfully",
            "cleared_keys": cleared_count
        }
        
    except Exception as e:
        logger.error(f"Failed to clear system cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear system cache"
        )

@router.get("/logs")
async def get_system_logs(
    request: Request,
    current_user: UserResponse = Depends(get_current_admin_user),
    limit: int = 100,
    level: str = "INFO"
):
    """Get system logs (admin only)."""
    try:
        # This would typically read from log files or a logging service
        # For now, return a placeholder response
        return {
            "logs": [],
            "total": 0,
            "limit": limit,
            "level": level,
            "message": "Log retrieval not implemented yet"
        }
        
    except Exception as e:
        logger.error(f"Failed to get system logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system logs"
        ) 