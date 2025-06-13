"""
FastAPI dependencies for authentication and authorization.
"""
from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from services.auth_service import AuthService, UserRole


async def get_auth_service(request: Request) -> AuthService:
    """Get the authentication service from app state."""
    return request.app.state.auth_service


async def get_current_user(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get the current authenticated user."""
    return await auth_service.get_current_user(request, required=True)


async def get_current_user_optional(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get the current authenticated user (optional)."""
    return await auth_service.get_current_user(request, required=False)


async def get_current_active_user(
    current_user=Depends(get_current_user)
):
    """Get the current active user."""
    if not current_user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user


def require_role(required_role: UserRole):
    """Dependency to require a specific role."""
    async def role_checker(current_user=Depends(get_current_active_user)):
        user_role = UserRole(current_user.get("role"))
        
        # Admin has access to everything
        if user_role == UserRole.ADMIN:
            return current_user
            
        # Check if user has required role
        if user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    
    return role_checker


def require_admin():
    """Dependency to require admin role."""
    return require_role(UserRole.ADMIN)


async def get_current_admin_user(
    current_user=Depends(get_current_active_user)
):
    """Get the current user and ensure they have admin role."""
    user_role = UserRole(current_user.get("role"))
    
    if user_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


async def verify_api_key(request: Request) -> Optional[str]:
    """Verify API key from headers."""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None
    
    # TODO: Implement API key validation against database
    # For now, return the key if present
    return api_key


async def get_current_user_or_api_key(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get user from JWT token or API key."""
    # Try JWT authentication first
    user = await auth_service.get_current_user(request, required=False)
    if user:
        return {"user": user, "auth_type": "jwt"}
    
    # Try API key authentication
    api_key = await verify_api_key(request)
    if api_key:
        return {"api_key": api_key, "auth_type": "api_key"}
    
    # No authentication found
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
