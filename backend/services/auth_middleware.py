"""
JWT Authentication Middleware for FastAPI
"""
import logging
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError

from services.auth_service import AuthService, TokenType

logger = logging.getLogger(__name__)

class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to handle JWT authentication globally."""
    
    def __init__(self, app, auth_service: AuthService):
        super().__init__(app)
        self.auth_service = auth_service
        
        # Paths that don't require authentication
        self.public_paths = {
            "/",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/health",
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/auth/refresh",
        }
        
        # Paths that require authentication (all others)
        self.protected_path_prefixes = [
            "/api/v1/query",
            "/api/v1/analytics",
            "/api/v1/admin",
            "/api/v1/auth/logout",
            "/api/v1/auth/me",
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and check authentication if needed."""
        path = request.url.path
        
        # Skip authentication for public paths
        if path in self.public_paths:
            return await call_next(request)
        
        # Check if path requires authentication
        requires_auth = any(path.startswith(prefix) for prefix in self.protected_path_prefixes)
        
        if requires_auth:
            try:
                # Extract and verify token
                user = await self.auth_service.get_current_user(request, required=True)
                
                # Add user to request state for use in endpoints
                request.state.current_user = user
                
            except HTTPException as e:
                return JSONResponse(
                    status_code=e.status_code,
                    content={"detail": e.detail},
                    headers=e.headers or {}
                )
            except Exception as e:
                logger.error(f"Authentication middleware error: {str(e)}")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"detail": "Authentication error"}
                )
        
        # Process request
        return await call_next(request)


def get_user_from_request(request: Request) -> Optional[dict]:
    """Helper function to get user from request state."""
    return getattr(request.state, 'current_user', None)
