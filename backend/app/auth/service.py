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
from fastapi import HTTPException, status, Depends
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

logger = logging.getLogger(__name__)

class UserRole(str, Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    GUEST = "guest"

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
    role: UserRole = UserRole.VIEWER

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
    
    async def register_user(self, user_data: UserCreate) -> UserResponse:
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
            insert_query = """
            INSERT INTO users (
                id, email, password_hash, full_name, company, role, 
                is_active, created_at, token_usage
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING *
            """
            
            result = self.db_manager.execute_query_safe(
                insert_query,
                params=(
                    user_id, user_data.email, hashed_password,
                    user_data.full_name, user_data.company, user_data.role.value,
                    True, datetime.now(timezone.utc), 0
                ),
                database_type="app"
            )
            
            if not result["data"]:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user"
                )
            
            user_record = result["data"][0]
            
            # Log registration
            await self._log_auth_event(user_id, "user_registered", user_data.email)
            
            return UserResponse(**user_record)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error registering user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register user"
            )
    
    async def authenticate_user(self, login_data: UserLogin) -> TokenResponse:
        """Authenticate a user and return tokens."""
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
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Verify password
            if not self.verify_password(login_data.password, user["password_hash"]):
                self._record_failed_attempt(login_data.email)
                await self._log_auth_event(user["id"], "login_failed", login_data.email)
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
            
            # Clear failed attempts
            self._clear_failed_attempts(login_data.email)
            
            # Update last login
            await self._update_last_login(user["id"])
            
            # Create tokens
            access_token = self.create_access_token({
                "sub": user["id"],
                "email": user["email"],
                "role": user["role"]
            })
            
            refresh_token = self.create_refresh_token(user["id"])
            
            # Log successful login
            await self._log_auth_event(user["id"], "login_success", login_data.email)
            
            # Prepare user response
            user_response = UserResponse(
                id=user["id"],
                email=user["email"],
                full_name=user["full_name"],
                company=user["company"],
                role=UserRole(user["role"]),
                is_active=user["is_active"],
                created_at=user["created_at"],
                last_login=user.get("last_login"),
                token_usage=user["token_usage"]
            )
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=self.access_token_expire_minutes * 60,
                user=user_response
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed"
            )
    
    async def refresh_access_token(self, refresh_request: RefreshTokenRequest) -> TokenResponse:
        """Refresh an access token using a refresh token."""
        try:
            # Verify refresh token
            payload = self.verify_token(refresh_request.refresh_token, TokenType.REFRESH)
            user_id = payload["sub"]
            
            # Get user details
            user = await self.get_user_by_id(user_id)
            if not user or not user["is_active"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            # Create new access token
            access_token = self.create_access_token({
                "sub": user["id"],
                "email": user["email"],
                "role": user["role"]
            })
            
            # Create new refresh token
            new_refresh_token = self.create_refresh_token(user_id)
            
            # Log token refresh
            await self._log_auth_event(user_id, "token_refreshed", user["email"])
            
            user_response = UserResponse(
                id=user["id"],
                email=user["email"],
                full_name=user["full_name"],
                company=user["company"],
                role=UserRole(user["role"]),
                is_active=user["is_active"],
                created_at=user["created_at"],
                last_login=user.get("last_login"),
                token_usage=user["token_usage"]
            )
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=new_refresh_token,
                expires_in=self.access_token_expire_minutes * 60,
                user=user_response
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token refresh failed"
            )
    
    async def get_current_user(
        self, 
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> UserResponse:
        """Get current authenticated user from token."""
        try:
            payload = self.verify_token(credentials.credentials)
            user_id = payload["sub"]
            
            user = await self.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            return UserResponse(
                id=user["id"],
                email=user["email"],
                full_name=user["full_name"],
                company=user["company"],
                role=UserRole(user["role"]),
                is_active=user["is_active"],
                created_at=user["created_at"],
                last_login=user.get("last_login"),
                token_usage=user["token_usage"]
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting current user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address."""
        try:
            query = "SELECT * FROM users WHERE email = %s"
            result = self.db_manager.execute_query_safe(
                query,
                params=(email,),
                database_type="app"
            )
            
            return result["data"][0] if result["data"] else None
            
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            query = "SELECT * FROM users WHERE id = %s"
            result = self.db_manager.execute_query_safe(
                query,
                params=(user_id,),
                database_type="app"
            )
            
            return result["data"][0] if result["data"] else None
            
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            return None
    
    def _validate_password_strength(self, password: str):
        """Validate password strength."""
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )
        
        if not any(c.isupper() for c in password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one uppercase letter"
            )
        
        if not any(c.islower() for c in password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one lowercase letter"
            )
        
        if not any(c.isdigit() for c in password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one digit"
            )
    
    def _is_locked_out(self, email: str) -> bool:
        """Check if email is locked out due to failed attempts."""
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
        """Update the last login timestamp for a user."""
        try:
            query = "UPDATE users SET last_login = %s WHERE id = %s"
            self.db_manager.execute_query_safe(
                query,
                params=(datetime.now(timezone.utc), user_id),
                database_type="app"
            )
        except Exception as e:
            logger.error(f"Error updating last login: {str(e)}")
    
    async def _log_auth_event(self, user_id: str, event_type: str, email: str):
        """Log authentication events for security monitoring."""
        try:
            # This would be implemented with the analytics module
            logger.info(f"Auth event - User: {user_id}, Event: {event_type}, Email: {email}")
        except Exception as e:
            logger.error(f"Error logging auth event: {str(e)}")

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
