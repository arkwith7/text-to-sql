"""
API routes for user authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request

from app.auth.service import AuthService, UserCreate, UserLogin, TokenResponse, RefreshTokenRequest
from app.auth.dependencies import get_current_user
from app.analytics.service import AnalyticsService, EventType

router = APIRouter()

@router.post("/register", response_model=TokenResponse, tags=["Authentication"])
async def register(user_data: UserCreate, request: Request):
    """Register a new user and return tokens."""
    auth_service: AuthService = request.app.state.auth_service
    analytics_service: AnalyticsService = request.app.state.analytics_service
    
    user = await auth_service.create_user(user_data, analytics_service=analytics_service)
    
    return await auth_service.create_token(user["id"])

@router.post("/login", response_model=TokenResponse, tags=["Authentication"])
async def login(login_data: UserLogin, request: Request):
    """Authenticate user and return tokens."""
    auth_service: AuthService = request.app.state.auth_service
    analytics_service: AnalyticsService = request.app.state.analytics_service
        
    user = await auth_service.authenticate_user(
        login_data, analytics_service=analytics_service
    )
    
    return await auth_service.create_token(user['id'])

@router.post("/refresh", response_model=TokenResponse, tags=["Authentication"])
async def refresh_token(refresh_request: RefreshTokenRequest, request: Request):
    """Refresh access token."""
    auth_service: AuthService = request.app.state.auth_service
    return await auth_service.refresh_access_token(refresh_request.refresh_token)

@router.post("/logout", tags=["Authentication"])
async def logout(
    refresh_request: RefreshTokenRequest, 
    request: Request,
    current_user=Depends(get_current_user)
):
    """Logout user by invalidating refresh token."""
    auth_service: AuthService = request.app.state.auth_service
    await auth_service.logout(refresh_request.refresh_token)
    return {"message": "Successfully logged out"}

@router.get("/me", tags=["Authentication"])
async def get_current_user_info(
    request: Request,
    current_user=Depends(get_current_user)
):
    """Get current user information."""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "company": current_user.get("company"),
        "role": current_user["role"],
        "is_active": current_user["is_active"],
        "created_at": current_user["created_at"],
        "last_login": current_user.get("last_login"),
        "token_usage": current_user.get("token_usage", 0)
    }

@router.get("/stats", tags=["Authentication"])
async def get_user_stats(
    request: Request,
    current_user=Depends(get_current_user)
):
    """Get user usage statistics including token usage."""
    analytics_service: AnalyticsService = request.app.state.analytics_service
    
    try:
        # Get user statistics from analytics service
        stats = await analytics_service.get_user_stats(current_user["id"])
        
        return {
            "user_id": current_user["id"],
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
        return {
            "user_id": current_user["id"],
            "total_queries": 0,
            "total_tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "last_query_at": None,
            "daily_usage": {},
            "monthly_usage": {},
            "average_tokens_per_query": 0
        } 