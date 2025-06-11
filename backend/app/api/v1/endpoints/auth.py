"""
API routes for user authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request

from app.auth.service import AuthService, UserCreate, UserLogin, TokenResponse, RefreshTokenRequest
from app.analytics.service import AnalyticsService, EventType

router = APIRouter()

@router.post("/register", response_model=TokenResponse, tags=["Authentication"])
async def register(user_data: UserCreate, request: Request):
    """Register a new user and return tokens."""
    auth_service: AuthService = request.app.state.auth_service
    analytics_service: AnalyticsService = request.app.state.analytics_service
    
    user = await auth_service.create_user(user_data, analytics_service=analytics_service)
    
    return await auth_service.create_token(user.id)

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
    return await auth_service.refresh_token(refresh_request.refresh_token) 