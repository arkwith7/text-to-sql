"""
Authentication and Authorization module with enhanced security features.

This module provides:
- JWT-based authentication
- Role-based access control (RBAC)
- User management
- Token management with refresh tokens
- Rate limiting and security logging
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field
import uuid
import hashlib
import secrets
from enum import Enum

from ..config import get_settings
from ..database.connection_manager import DatabaseManager
from ..analytics.service import AnalyticsService, EventType

logger = logging.getLogger(__name__)

class UserRole(str, Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    ANALYST = "analyst"

class TokenType(str, Enum):
    """Token types."""
    ACCESS = "access"
    REFRESH = "refresh"

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    role: UserRole = UserRole.ANALYST

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    company: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    token_usage: int

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class AuthService:
    """
    Authentication service with enhanced security features.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.settings = get_settings()
        
        # Password hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # JWT settings
        self.secret_key = self.settings.jwt_secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60  # 1 hour
        self.refresh_token_expire_days = 7     # 7 days
        
        # Rate limiting
        self.failed_login_attempts = {}  # In production, use Redis
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=15)
        
        # Security headers
        self.security = HTTPBearer()
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({
            "exp": expire,
            "type": TokenType.ACCESS,
            "iat": datetime.now(timezone.utc)
        })
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create a JWT refresh token."""
        to_encode = {
            "sub": user_id,
            "type": TokenType.REFRESH,
            "exp": datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days),
            "iat": datetime.now(timezone.utc),
            "jti": str(uuid.uuid4())  # JWT ID for token revocation
        }
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, token_type: TokenType = TokenType.ACCESS) -> Dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("type") != token_type:
                raise JWTError("Invalid token type")
            
            # Check expiration
            if datetime.fromtimestamp(payload["exp"], timezone.utc) < datetime.now(timezone.utc):
                raise JWTError("Token has expired")
            
            return payload
            
        except JWTError as e:
            logger.warning(f"Token verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def create_user(self, user_data: UserCreate, analytics_service: AnalyticsService) -> Dict[str, Any]:
        """Register a new user."""
        try:
            # Check if user already exists
            existing_user = await self.get_user_by_email(user_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
            
            # Validate password strength
            self._validate_password_strength(user_data.password)
            
            # Hash password
            hashed_password = self.hash_password(user_data.password)
            
            # Create user ID
            user_id = str(uuid.uuid4())
            
            # Insert user into database
            query = """
                INSERT INTO users (id, email, password_hash, full_name, company, role, is_active, created_at, updated_at, token_usage)
                VALUES (:id, :email, :password_hash, :full_name, :company, :role, TRUE, :created_at, :updated_at, :token_usage)
            """
            now = datetime.now(timezone.utc)
            
            # The RETURNING clause is not universally supported, especially in older SQLite versions.
            # We will perform a SELECT after INSERT.
            
            insert_params = {
                "id": user_id,
                "email": user_data.email,
                "password_hash": hashed_password,
                "full_name": user_data.full_name,
                "company": user_data.company,
                "role": user_data.role.value,
                "created_at": now,
                "updated_at": now,
                "token_usage": 0,
            }

            result = await self.db_manager.execute_query(
                "app",
                query,
                insert_params,
            )
            
            if not result.get("success"):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user."
                )

            # Fetch the newly created user
            select_query = "SELECT id, email, full_name, company, role, is_active, created_at, last_login, token_usage FROM users WHERE id = :user_id"
            fetch_result = await self.db_manager.execute_query("app", select_query, {"user_id": user_id})

            if not fetch_result.get("success") or not fetch_result.get("data"):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch newly created user."
                )
            
            new_user = dict(fetch_result["data"][0])
            
            # Log registration
            await self._log_auth_event(
                analytics_service, new_user['id'], EventType.USER_REGISTERED, new_user['email']
            )
            
            return new_user
            
        except HTTPException:
            raise
        except ValueError as e:
            # Handle password validation errors specifically
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error registering user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register user"
            )
    
    async def authenticate_user(
        self, login_data: UserLogin, analytics_service: AnalyticsService
    ) -> Dict[str, Any]:
        """Authenticate a user and return user data."""
        try:
            # Check rate limiting
            if self._is_locked_out(login_data.email):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many failed login attempts. Please try again later."
                )
            
            # Get user by email
            user = await self.get_user_by_email(login_data.email)
            if not user:
                self._record_failed_attempt(login_data.email)
                await self._log_auth_event(
                    analytics_service, user["id"], EventType.USER_LOGGED_IN, login_data.email
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Verify password
            if not self.verify_password(login_data.password, user["password_hash"]):
                self._record_failed_attempt(login_data.email)
                await self._log_auth_event(
                    analytics_service, user["id"], EventType.USER_LOGGED_IN, login_data.email
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Check if user is active
            if not user["is_active"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account is disabled"
                )
            
            # Reset failed login attempts
            self._clear_failed_attempts(login_data.email)
            
            # Update last login time
            await self._update_last_login(user["id"])
            
            # Log successful login
            await self._log_auth_event(
                analytics_service, user["id"], EventType.USER_LOGGED_IN, login_data.email
            )

            return user
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed"
            )
    
    async def create_token(self, user_id: str) -> TokenResponse:
        """Create access and refresh tokens for a user ID."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="User not found"
            )

        user_response = UserResponse(**user)
        access_token = self.create_access_token({"sub": user["id"], "role": user["role"]})
        refresh_token = self.create_refresh_token(user["id"])

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.access_token_expire_minutes * 60,
            user=user_response,
        )
    
    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Refresh an access token using a refresh token."""
        try:
            payload = self.verify_token(refresh_token, TokenType.REFRESH)
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid refresh token")

            user = await self.get_user_by_id(user_id)
            if not user or not user.get("is_active"):
                raise HTTPException(status_code=401, detail="User not found or inactive")
            
            user_response = UserResponse(**user)
            new_access_token = self.create_access_token({"sub": user_id, "role": user.get("role")})
            
            return TokenResponse(
                access_token=new_access_token,
                refresh_token=refresh_token, # Return the same refresh token
                expires_in=self.access_token_expire_minutes * 60,
                user=user_response
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to refresh token"
            )
    
    async def get_current_user(self, request: Request, required: bool = True, is_admin: bool = False) -> Optional[Dict[str, Any]]:
        """Get current user from JWT token in request header."""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            if required:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authorization header missing"
                )
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            if required:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Authorization header format"
                )
            return None
        
        token = parts[1]
        
        try:
            payload = self.verify_token(token, TokenType.ACCESS)
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token payload")

            user = await self.get_user_by_id(user_id)
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            
            if is_admin and user.get("role") != "admin":
                raise HTTPException(status_code=403, detail="Admin access required")

            return user

        except HTTPException as e:
            if required:
                raise e
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Fetch a user by their email address."""
        query = "SELECT * FROM users WHERE email = :email"
        result = await self.db_manager.execute_query("app", query, {"email": email})
        if result and result.get("success") and result.get("data"):
            return dict(result["data"][0])
        return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a user by their ID."""
        query = "SELECT * FROM users WHERE id = :user_id"
        result = await self.db_manager.execute_query("app", query, {"user_id": user_id})
        if result and result.get("success") and result.get("data"):
            return dict(result["data"][0])
        return None
    
    def _validate_password_strength(self, password: str):
        """Validate password strength."""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isalpha() for char in password):
            raise ValueError("Password must contain at least one letter")
    
    def _is_locked_out(self, email: str) -> bool:
        """Check if a user is locked out due to failed login attempts."""
        if email not in self.failed_login_attempts:
            return False
        
        attempts = self.failed_login_attempts[email]
        if attempts["count"] >= self.max_failed_attempts:
            if datetime.now() < attempts["locked_until"]:
                return True
            else:
                # Lockout period expired, clear attempts
                del self.failed_login_attempts[email]
        
        return False
    
    def _record_failed_attempt(self, email: str):
        """Record a failed login attempt."""
        now = datetime.now()
        
        if email not in self.failed_login_attempts:
            self.failed_login_attempts[email] = {"count": 0, "locked_until": now}
        
        self.failed_login_attempts[email]["count"] += 1
        
        if self.failed_login_attempts[email]["count"] >= self.max_failed_attempts:
            self.failed_login_attempts[email]["locked_until"] = now + self.lockout_duration
    
    def _clear_failed_attempts(self, email: str):
        """Clear failed login attempts for an email."""
        if email in self.failed_login_attempts:
            del self.failed_login_attempts[email]
    
    async def _update_last_login(self, user_id: str):
        """Update the last_login timestamp for a user."""
        query = "UPDATE users SET last_login = :last_login WHERE id = :user_id"
        now = datetime.now(timezone.utc)
        await self.db_manager.execute_query("app", query, {"last_login": now, "user_id": user_id})
    
    async def _log_auth_event(
        self, analytics_service: AnalyticsService, user_id: str, event_type: EventType, email: str
    ):
        """Log authentication events using the AnalyticsService."""
        await analytics_service.log_event(
            event_type=event_type,
            user_id=user_id,
            event_data={"email": email},
            ip_address="script",  # Placeholder, should be from request
            user_agent="script",  # Placeholder, should be from request
        )

# Permission checking decorators
def require_role(required_role: UserRole):
    """Decorator to require a specific role or higher."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would be implemented to check user role
            # For now, just proceed
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_permissions(*permissions: str):
    """Decorator to require specific permissions."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would be implemented to check user permissions
            # For now, just proceed
            return await func(*args, **kwargs)
        return wrapper
    return decorator
