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

from core.config import get_settings
from database.connection_manager import DatabaseManager
from services.analytics_service import AnalyticsService, EventType

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
        self.algorithm = self.settings.jwt_algorithm
        self.access_token_expire_minutes = self.settings.access_token_expire_minutes
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
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address."""
        try:
            query = """
                SELECT id, email, password_hash, full_name, company, role, is_active, 
                       created_at, updated_at, last_login, token_usage 
                FROM users 
                WHERE email = :email
            """
            
            result = await self.db_manager.execute_query("app", query, {"email": email})
            
            if result.get("success") and result.get("data"):
                return dict(result["data"][0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            query = """
                SELECT id, email, password_hash, full_name, company, role, is_active, 
                       created_at, updated_at, last_login, token_usage 
                FROM users 
                WHERE id = :user_id
            """
            
            result = await self.db_manager.execute_query("app", query, {"user_id": user_id})
            
            if result.get("success") and result.get("data"):
                return dict(result["data"][0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            return None
    
    def _is_locked_out(self, email: str) -> bool:
        """Check if user is locked out due to failed login attempts."""
        if email not in self.failed_login_attempts:
            return False
        
        attempts_data = self.failed_login_attempts[email]
        if attempts_data["count"] >= self.max_failed_attempts:
            # Check if lockout period has expired
            if datetime.now(timezone.utc) - attempts_data["last_attempt"] < self.lockout_duration:
                return True
            else:
                # Lockout expired, clear attempts
                self._clear_failed_attempts(email)
                return False
        
        return False
    
    def _record_failed_attempt(self, email: str):
        """Record a failed login attempt."""
        now = datetime.now(timezone.utc)
        if email in self.failed_login_attempts:
            self.failed_login_attempts[email]["count"] += 1
            self.failed_login_attempts[email]["last_attempt"] = now
        else:
            self.failed_login_attempts[email] = {
                "count": 1,
                "last_attempt": now
            }
    
    def _clear_failed_attempts(self, email: str):
        """Clear failed login attempts for email."""
        if email in self.failed_login_attempts:
            del self.failed_login_attempts[email]
    
    async def _update_last_login(self, user_id: str):
        """Update last login timestamp for user."""
        try:
            query = """
                UPDATE users 
                SET last_login = :last_login, updated_at = :updated_at
                WHERE id = :user_id
            """
            
            now = datetime.now(timezone.utc)
            await self.db_manager.execute_query("app", query, {
                "user_id": user_id,
                "last_login": now,
                "updated_at": now
            })
            
        except Exception as e:
            logger.error(f"Error updating last login: {str(e)}")
    
    async def _log_auth_event(self, analytics_service: AnalyticsService, user_id: str, event_type: EventType, email: str):
        """Log authentication event."""
        try:
            await analytics_service.log_event(
                event_type=event_type,
                user_id=user_id,
                metadata={"email": email}
            )
        except Exception as e:
            logger.error(f"Error logging auth event: {str(e)}")
    
    def _validate_password_strength(self, password: str):
        """Validate password strength."""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            logger.warning("Password should contain at least one uppercase letter")
        
        if not any(c.isdigit() for c in password):
            logger.warning("Password should contain at least one digit")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            logger.warning("Password should contain at least one special character")

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
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Verify password
            if not self.verify_password(login_data.password, user["password_hash"]):
                self._record_failed_attempt(login_data.email)
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
        """Create access and refresh tokens for a user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Create access token
        access_token_data = {
            "sub": user["id"],
            "email": user["email"],
            "role": user["role"]
        }
        access_token = self.create_access_token(access_token_data)
        
        # Create refresh token
        refresh_token = self.create_refresh_token(user["id"])
        
        # Store refresh token in database
        await self._store_refresh_token(user["id"], refresh_token)
        
        # Convert user data to UserResponse format
        user_response = UserResponse(
            id=user["id"],
            email=user["email"],
            full_name=user["full_name"],
            company=user.get("company"),
            role=UserRole(user["role"]),
            is_active=user["is_active"],
            created_at=user["created_at"],
            last_login=user.get("last_login"),
            token_usage=user.get("token_usage", 0)
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60,
            user=user_response
        )
    
    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Refresh an access token using a refresh token."""
        try:
            # Verify refresh token
            payload = self.verify_token(refresh_token, TokenType.REFRESH)
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            # Check if refresh token exists in database
            if not await self._is_refresh_token_valid(user_id, refresh_token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token not found or expired"
                )
            
            # Create new tokens
            return await self.create_token(user_id)
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
    
    async def get_current_user(self, request: Request, required: bool = True) -> Optional[Dict[str, Any]]:
        """Get the current authenticated user from request."""
        try:
            # Get authorization header
            authorization = request.headers.get("authorization")
            if not authorization:
                logger.debug("No authorization header found")
                if required:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authorization header missing",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                return None
            
            # Extract token
            try:
                scheme, token = authorization.split()
            except ValueError:
                logger.debug("Invalid authorization header format")
                if required:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid authorization header format",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                return None
                
            if scheme.lower() != "bearer":
                logger.debug(f"Invalid authentication scheme: {scheme}")
                if required:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid authentication scheme",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                return None
            
            # Verify token
            logger.debug(f"Verifying token: {token[:20]}...")
            payload = self.verify_token(token, TokenType.ACCESS)
            user_id = payload.get("sub")
            
            if not user_id:
                logger.debug("No user ID in token payload")
                if required:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token payload"
                    )
                return None
            
            # Get user from database
            user = await self.get_user_by_id(user_id)
            if not user:
                logger.debug(f"User not found: {user_id}")
                if required:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not found"
                    )
                return None
            
            if not user.get("is_active"):
                logger.debug(f"User account disabled: {user_id}")
                if required:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User account is disabled"
                    )
                return None
            
            logger.debug(f"Authentication successful for user: {user['email']}")
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting current user: {str(e)}")
            if required:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication failed"
                )
            return None
    
    async def logout(self, refresh_token: str):
        """Logout user by invalidating refresh token."""
        try:
            payload = self.verify_token(refresh_token, TokenType.REFRESH)
            user_id = payload.get("sub")
            
            if user_id:
                await self._invalidate_refresh_token(user_id, refresh_token)
                
        except JWTError:
            # Token already invalid, no need to raise error
            pass
    
    async def _store_refresh_token(self, user_id: str, refresh_token: str):
        """Store refresh token in database."""
        # Extract JWT ID from token
        payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
        jti = payload.get("jti")
        expires_at = datetime.fromtimestamp(payload["exp"], timezone.utc)
        
        query = """
            INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at, created_at, is_active, is_revoked)
            VALUES (:id, :user_id, :token_hash, :expires_at, :created_at, :is_active, :is_revoked)
        """
        
        await self.db_manager.execute_query("app", query, {
            "id": jti,
            "user_id": user_id,
            "token_hash": hashlib.sha256(refresh_token.encode()).hexdigest(),
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc),
            "is_active": True,
            "is_revoked": False
        })
    
    async def _is_refresh_token_valid(self, user_id: str, refresh_token: str) -> bool:
        """Check if refresh token is valid and not expired."""
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        
        query = """
            SELECT COUNT(*) as count FROM refresh_tokens 
            WHERE user_id = :user_id AND token_hash = :token_hash 
            AND expires_at > :now AND is_revoked = FALSE
        """
        
        result = await self.db_manager.execute_query("app", query, {
            "user_id": user_id,
            "token_hash": token_hash,
            "now": datetime.now(timezone.utc)
        })
        
        return result and result.get("success") and result["data"][0]["count"] > 0
    
    async def _invalidate_refresh_token(self, user_id: str, refresh_token: str):
        """Invalidate a refresh token."""
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        
        query = """
            UPDATE refresh_tokens 
            SET is_revoked = TRUE, revoked_at = :revoked_at
            WHERE user_id = :user_id AND token_hash = :token_hash
        """
        
        await self.db_manager.execute_query("app", query, {
            "user_id": user_id,
            "token_hash": token_hash,
            "revoked_at": datetime.now(timezone.utc)
        })

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
