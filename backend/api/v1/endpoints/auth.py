"""
Authentication endpoints for Text-to-SQL application.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any

from services.auth_service import AuthService, UserCreate, UserLogin, UserResponse
from services.auth_dependencies import get_current_user, get_current_admin_user

router = APIRouter()
security = HTTPBearer()

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class AuthStatsResponse(BaseModel):
    total_users: int
    active_users: int
    recent_logins: int
    user_registrations_today: int

@router.post("/register", response_model=TokenResponse)
async def register(
    user_data: UserCreate,
    request: Request
):
    """Register a new user."""
    auth_service: AuthService = request.app.state.auth_service
    analytics_service = request.app.state.analytics_service
    
    try:
        # Create user
        user = await auth_service.create_user(user_data, analytics_service)
        
        # Create tokens
        token_response = await auth_service.create_token(user["id"])
        return token_response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=TokenResponse)
async def login(
    user_credentials: UserLogin,
    request: Request
):
    """Authenticate user and return access token."""
    auth_service: AuthService = request.app.state.auth_service
    analytics_service = request.app.state.analytics_service
    
    try:
        # Authenticate user
        user = await auth_service.authenticate_user(
            login_data=user_credentials,
            analytics_service=analytics_service,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        # Create tokens
        token_response = await auth_service.create_token(user["id"])
        return token_response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get current user information."""
    return current_user

@router.get("/stats")
async def get_user_stats(
    request: Request,
    current_user = Depends(get_current_user)
):
    """Get user usage statistics including token usage."""
    analytics_service = request.app.state.analytics_service
    
    try:
        # current_user is a dict, so we need to access it properly
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        
        # Get user statistics from analytics service
        stats = await analytics_service.get_user_stats(user_id)
        
        return {
            "user_id": user_id,
            "total_queries": stats.get("total_queries", 0),
            "total_tokens": stats.get("total_tokens", 0),
            "input_tokens": stats.get("input_tokens", 0),
            "output_tokens": stats.get("output_tokens", 0),
            "last_query_at": stats.get("last_query_at"),
            "daily_usage": stats.get("daily_usage", {}),
            "monthly_usage": stats.get("monthly_usage", {}),
            "average_tokens_per_query": stats.get("average_tokens_per_query", 0)
        }
    except Exception as e:
        # Return default stats if analytics service fails
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        return {
            "user_id": user_id,
            "total_queries": 0,
            "total_tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "last_query_at": None,
            "daily_usage": {},
            "monthly_usage": {},
            "average_tokens_per_query": 0
        }

@router.get("/admin/stats", response_model=AuthStatsResponse)
async def get_auth_stats(
    request: Request,
    current_user: UserResponse = Depends(get_current_admin_user)
):
    """Get authentication statistics (admin only)."""
    auth_service: AuthService = request.app.state.auth_service
    
    try:
        stats = await auth_service.get_auth_stats()
        return AuthStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve authentication statistics"
        )

@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """Change user password."""
    auth_service: AuthService = request.app.state.auth_service
    
    try:
        await auth_service.change_password(
            current_user.id,
            password_data.current_password,
            password_data.new_password
        )
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

@router.post("/logout")
async def logout(
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """Logout user (invalidate token)."""
    auth_service: AuthService = request.app.state.auth_service
    
    try:
        # In a real implementation, you might want to blacklist the token
        # For now, we'll just return a success message
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        ) 