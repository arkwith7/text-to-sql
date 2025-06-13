"""
Authentication endpoints for Text-to-SQL application.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import Optional

from services.auth_service import AuthService, UserCreate, UserLogin, UserResponse
from services.auth_dependencies import get_current_user, get_current_admin_user

router = APIRouter()
security = HTTPBearer()

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

@router.post("/register", response_model=TokenResponse)
async def register(
    user_data: UserCreate,
    request: Request
):
    """Register a new user."""
    auth_service: AuthService = request.app.state.auth_service
    
    try:
        result = await auth_service.register_user(user_data)
        return result
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
    
    try:
        result = await auth_service.authenticate_user(user_credentials)
        return result
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