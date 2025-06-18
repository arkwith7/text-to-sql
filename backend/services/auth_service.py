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
import asyncio

from core.config import get_settings
from database.connection_manager import DatabaseManager
from services.analytics_service import AnalyticsService, EventType
from utils.logging_config import AuthLogger

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

        # 로거 설정
        self.logger = logging.getLogger(__name__)
        self.auth_logger = logging.getLogger("authentication")
        
        self.logger.info("인증 서비스 초기화 완료")

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return self.pwd_context.hash(password)
    
    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash asynchronously."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, self.pwd_context.verify, plain_password, hashed_password
        )
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({
            "exp": int(expire.timestamp()),
            "type": TokenType.ACCESS.value,
            "iat": int(now.timestamp())
        })
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create a JWT refresh token."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=self.refresh_token_expire_days)
        to_encode = {
            "sub": user_id,
            "type": TokenType.REFRESH.value,
            "exp": int(expire.timestamp()),
            "iat": int(now.timestamp()),
            "jti": str(uuid.uuid4())  # JWT ID for token revocation
        }
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, token_type: TokenType = TokenType.ACCESS) -> Dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("type") != token_type.value:
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
        """Record failed login attempt with logging."""
        now = datetime.now(timezone.utc)
        if email in self.failed_login_attempts:
            self.failed_login_attempts[email]["count"] += 1
            self.failed_login_attempts[email]["last_attempt"] = now
        else:
            self.failed_login_attempts[email] = {
                "count": 1,
                "last_attempt": now
            }
        
        self.logger.warning(
            f"🔒 로그인 실패 기록 - Email: {email}, 실패 횟수: {self.failed_login_attempts[email]['count']}",
            extra={
                'email': email,
                'failed_attempt_count': self.failed_login_attempts[email]['count'],
                'max_attempts': self.max_failed_attempts
            }
        )
    
    def _clear_failed_attempts(self, email: str):
        """Clear failed login attempts with logging."""
        if email in self.failed_login_attempts:
            failed_count = self.failed_login_attempts[email]["count"]
            del self.failed_login_attempts[email]
            
            self.logger.info(
                f"🔓 로그인 실패 기록 초기화 - Email: {email}, 이전 실패 횟수: {failed_count}",
                extra={'email': email, 'cleared_failed_attempts': failed_count}
            )
    
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
        """Register a new user with comprehensive logging."""
        self.logger.info(
            f"👤 새 사용자 등록 시작 - Email: {user_data.email}",
            extra={
                'email': user_data.email,
                'full_name': user_data.full_name,
                'company': user_data.company,
                'role': user_data.role.value
            }
        )
        
        try:
            # 중복 사용자 확인
            existing_user = await self.get_user_by_email(user_data.email)
            if existing_user:
                self.logger.warning(
                    f"⚠️ 사용자 등록 실패 - 이미 존재하는 이메일: {user_data.email}",
                    extra={'email': user_data.email, 'reason': 'duplicate_email'}
                )
                
                # 인증 로그
                AuthLogger.log_auth_event(
                    event_type="registration_failed",
                    email=user_data.email,
                    success=False,
                    error_message="User with this email already exists"
                )
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
            
            # 비밀번호 강도 검증
            self.logger.debug(f"🔒 비밀번호 강도 검증 중")
            self._validate_password_strength(user_data.password)
            
            # 비밀번호 해싱
            hashed_password = self.hash_password(user_data.password)
            user_id = str(uuid.uuid4())
            
            self.logger.debug(
                f"🔐 사용자 데이터 준비 완료 - ID: {user_id}",
                extra={'user_id': user_id, 'email': user_data.email}
            )
            
            # 데이터베이스에 사용자 삽입
            query = """
                INSERT INTO users (id, email, password_hash, full_name, company, role, is_active, created_at, updated_at, token_usage)
                VALUES (:id, :email, :password_hash, :full_name, :company, :role, TRUE, :created_at, :updated_at, :token_usage)
            """
            now = datetime.now(timezone.utc)
            
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

            result = await self.db_manager.execute_query("app", query, insert_params)
            
            if not result.get("success"):
                error_msg = result.get("error", "Unknown database error")
                self.logger.error(
                    f"❌ 사용자 등록 DB 오류: {error_msg}",
                    extra={'user_id': user_id, 'email': user_data.email, 'error_details': error_msg}
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user."
                )

            # 새로 생성된 사용자 조회
            select_query = "SELECT id, email, full_name, company, role, is_active, created_at, last_login, token_usage FROM users WHERE id = :user_id"
            fetch_result = await self.db_manager.execute_query("app", select_query, {"user_id": user_id})

            if not fetch_result.get("success") or not fetch_result.get("data"):
                self.logger.error(f"❌ 새 사용자 조회 실패 - ID: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch newly created user."
                )
            
            new_user = dict(fetch_result["data"][0])
            
            # 성공 로깅
            self.logger.info(
                f"✅ 사용자 등록 성공 - ID: {user_id}, Email: {user_data.email}",
                extra={
                    'user_id': user_id,
                    'email': user_data.email,
                    'full_name': user_data.full_name,
                    'role': user_data.role.value,
                    'company': user_data.company
                }
            )
            
            # 인증 로그
            AuthLogger.log_auth_event(
                event_type="registration_success",
                user_id=user_id,
                email=user_data.email,
                success=True
            )
            
            # 분석 로깅
            await self._log_auth_event(analytics_service, new_user['id'], EventType.USER_REGISTERED, new_user['email'])
            
            return new_user
            
        except HTTPException:
            raise
        except ValueError as e:
            self.logger.warning(
                f"⚠️ 비밀번호 검증 실패 - Email: {user_data.email}, 오류: {str(e)}",
                extra={'email': user_data.email, 'validation_error': str(e)}
            )
            
            AuthLogger.log_auth_event(
                event_type="registration_failed",
                email=user_data.email,
                success=False,
                error_message=str(e)
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            self.logger.error(
                f"❌ 사용자 등록 실패 - Email: {user_data.email}, 오류: {str(e)}",
                extra={'email': user_data.email, 'error_details': str(e)},
                exc_info=True
            )
            
            AuthLogger.log_auth_event(
                event_type="registration_failed",
                email=user_data.email,
                success=False,
                error_message=str(e)
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register user"
            )
    
    
    async def authenticate_user(
        self, login_data: UserLogin, analytics_service: AnalyticsService, 
        ip_address: str = None, user_agent: str = None
    ) -> Dict[str, Any]:
        """Authenticate a user - optimized for performance."""
        try:
            # 계정 잠금 확인
            if self._is_locked_out(login_data.email):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many failed login attempts. Please try again later."
                )
            
            # 사용자 조회
            user = await self.get_user_by_email(login_data.email)
            if not user:
                self._record_failed_attempt(login_data.email)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # 비밀번호 검증
            if not await self.verify_password(login_data.password, user["password_hash"]):
                self._record_failed_attempt(login_data.email)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # 계정 활성화 확인
            if not user["is_active"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account is disabled"
                )
            
            # 로그인 성공 처리
            self._clear_failed_attempts(login_data.email)
            await self._update_last_login(user["id"])
            
            # 성공 로깅 (간단하게)
            logger.info(f"Login success: {login_data.email}")
            
            # 분석 로깅 (백그라운드로 처리)
            asyncio.create_task(
                self._log_auth_event(analytics_service, user["id"], EventType.USER_LOGGED_IN, login_data.email)
            )

            return user
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login error for {login_data.email}: {str(e)}")
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
        """Get current authenticated user with enhanced logging."""
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        try:
            # 모든 헤더를 로그로 확인 (디버깅용)
            self.logger.debug(f"🔍 Request headers - Request ID: {request_id}")
            for key, value in request.headers.items():
                # Authorization 헤더는 마스킹해서 로그
                if key.lower() == 'authorization':
                    masked_value = f"{value[:20]}..." if len(value) > 20 else value
                    self.logger.debug(f"  {key}: {masked_value}")
                else:
                    self.logger.debug(f"  {key}: {value}")
            
            # 인증 헤더 확인
            authorization = request.headers.get("authorization")
            if not authorization:
                self.logger.debug(f"🔍 Authorization 헤더가 없습니다 - Request ID: {request_id}")
                if required:
                    self.logger.debug(f"🔍 인증 헤더 없음 - Request ID: {request_id}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authorization header missing",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                return None
            
            self.logger.debug(f"🔑 Authorization 헤더 발견: {authorization[:30]}... - Request ID: {request_id}")
            
            # 토큰 추출
            try:
                scheme, token = authorization.split(' ', 1)  # maxsplit=1로 수정
                self.logger.debug(f"🔑 Scheme: {scheme}, Token 길이: {len(token)} - Request ID: {request_id}")
            except ValueError:
                if required:
                    self.logger.debug(f"🔍 잘못된 인증 헤더 형식: {authorization} - Request ID: {request_id}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid authorization header format",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                return None
                
            if scheme.lower() != "bearer":
                if required:
                    self.logger.debug(f"🔍 잘못된 인증 스키마: {scheme} - Request ID: {request_id}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid authentication scheme",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                return None
            
            # 토큰 검증
            self.logger.debug(f"🔑 토큰 검증 중 - Request ID: {request_id}, Token: {token[:20]}...")
            payload = self.verify_token(token, TokenType.ACCESS)
            user_id = payload.get("sub")
            
            if not user_id:
                if required:
                    self.logger.debug(f"🔍 토큰에 사용자 ID 없음 - Request ID: {request_id}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token payload"
                    )
                return None
            
            # 사용자 조회
            user = await self.get_user_by_id(user_id)
            if not user:
                if required:
                    self.logger.warning(f"⚠️ 사용자 찾을 수 없음 - User ID: {user_id}, Request ID: {request_id}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not found"
                    )
                return None
            
            if not user.get("is_active"):
                if required:
                    self.logger.warning(f"🚫 비활성화된 계정 - User ID: {user_id}, Request ID: {request_id}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User account is disabled"
                    )
                return None
            
            self.logger.debug(
                f"✅ 인증 성공 - User: {user['email']}, Request ID: {request_id}",
                extra={
                    'user_id': user['id'],
                    'email': user['email'],
                    'role': user['role'],
                    'request_id': request_id
                }
            )
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(
                f"❌ 사용자 인증 오류 - Request ID: {request_id}, 오류: {str(e)}",
                extra={'request_id': request_id, 'error_details': str(e)},
                exc_info=True
            )
            
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
        """Invalidate a specific refresh token."""
        try:
            query = """
                DELETE FROM refresh_tokens 
                WHERE user_id = :user_id AND token_hash = :token_hash
            """
            
            token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            
            await self.db_manager.execute_query(
                "app", 
                query, 
                {"user_id": user_id, "token_hash": token_hash}
            )
            
        except Exception as e:
            logger.error(f"Error invalidating refresh token: {str(e)}")

    async def get_auth_stats(self) -> Dict[str, Any]:
        """Get authentication statistics."""
        try:
            # Get total users
            total_users_query = "SELECT COUNT(*) as count FROM users"
            total_users_result = await self.db_manager.execute_query("app", total_users_query)
            total_users = total_users_result.get("data", [{}])[0].get("count", 0) if total_users_result.get("success") else 0
            
            # Get active users (logged in within last 30 days)
            active_users_query = """
                SELECT COUNT(*) as count FROM users 
                WHERE last_login >= datetime('now', '-30 days')
            """
            active_users_result = await self.db_manager.execute_query("app", active_users_query)
            active_users = active_users_result.get("data", [{}])[0].get("count", 0) if active_users_result.get("success") else 0
            
            # Get recent logins (last 24 hours)
            recent_logins_query = """
                SELECT COUNT(*) as count FROM users 
                WHERE last_login >= datetime('now', '-1 day')
            """
            recent_logins_result = await self.db_manager.execute_query("app", recent_logins_query)
            recent_logins = recent_logins_result.get("data", [{}])[0].get("count", 0) if recent_logins_result.get("success") else 0
            
            # Get user registrations today
            registrations_today_query = """
                SELECT COUNT(*) as count FROM users 
                WHERE date(created_at) = date('now')
            """
            registrations_today_result = await self.db_manager.execute_query("app", registrations_today_query)
            registrations_today = registrations_today_result.get("data", [{}])[0].get("count", 0) if registrations_today_result.get("success") else 0
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "recent_logins": recent_logins,
                "user_registrations_today": registrations_today
            }
            
        except Exception as e:
            logger.error(f"Error getting auth stats: {str(e)}")
            # Return default values on error
            return {
                "total_users": 0,
                "active_users": 0,
                "recent_logins": 0,
                "user_registrations_today": 0
            }

    async def get_token_usage_stats(self, user_id: str) -> Dict[str, Any]:
        """Get LLM token usage statistics for a specific user."""
        try:
            # Get user's current token usage
            user_query = "SELECT token_usage FROM users WHERE id = :user_id"
            user_result = await self.db_manager.execute_query("app", user_query, {"user_id": user_id})
            user_token_usage = user_result.get("data", [{}])[0].get("token_usage", 0) if user_result.get("success") and user_result.get("data") else 0
            
            # Initialize default values
            total_queries = 0
            queries_today = 0
            
            # Try to get total queries by user from query_analytics table (if it exists)
            try:
                total_queries_query = """
                    SELECT COUNT(*) as count FROM query_analytics 
                    WHERE user_id = :user_id
                """
                total_queries_result = await self.db_manager.execute_query("app", total_queries_query, {"user_id": user_id})
                if total_queries_result.get("success") and total_queries_result.get("data"):
                    total_queries = total_queries_result["data"][0].get("count", 0)
            except Exception as e:
                logger.debug(f"query_analytics table not available: {str(e)}")
                # Table might not exist yet, use default value
                total_queries = 0
            
            # Try to get queries today from query_analytics table (if it exists)
            try:
                queries_today_query = """
                    SELECT COUNT(*) as count FROM query_analytics 
                    WHERE user_id = :user_id 
                    AND date(created_at) = date('now')
                """
                queries_today_result = await self.db_manager.execute_query("app", queries_today_query, {"user_id": user_id})
                if queries_today_result.get("success") and queries_today_result.get("data"):
                    queries_today = queries_today_result["data"][0].get("count", 0)
            except Exception as e:
                logger.debug(f"query_analytics table not available for today's queries: {str(e)}")
                # Table might not exist yet, use default value
                queries_today = 0
            
            # Calculate average tokens per query
            average_tokens_per_query = 0.0
            if total_queries > 0:
                average_tokens_per_query = round(user_token_usage / total_queries, 2)
            
            return {
                "user_token_usage": user_token_usage,
                "total_queries": total_queries,
                "queries_today": queries_today,
                "average_tokens_per_query": average_tokens_per_query
            }
            
        except Exception as e:
            logger.error(f"Error getting token usage stats for user {user_id}: {str(e)}")
            # Return default values on error
            return {
                "user_token_usage": 0,
                "total_queries": 0,
                "queries_today": 0,
                "average_tokens_per_query": 0.0
            }

    async def authenticate_user_simple(self, email: str, password: str) -> Dict[str, Any]:
        """단순 사용자 인증 (이메일/패스워드)."""
        
        # Rate limit 확인
        if self._is_locked_out(email):
            self.logger.warning(f"🔒 로그인 시도 차단됨 - Email: {email}")
            raise ValueError("너무 많은 로그인 시도 실패. 잠시 후 다시 시도해주세요.")
        
        # 사용자 조회
        user = await self.get_user_by_email(email)
        
        if not user or not user["is_active"]:
            self.logger.warning(f"👤 존재하지 않거나 비활성화된 사용자 - Email: {email}")
            self._record_failed_attempt(email)
            raise ValueError("잘못된 이메일 또는 패스워드입니다.")
        
        # 비밀번호 검증
        if not await self.verify_password(password, user["password_hash"]):
            self.logger.warning(f"🔑 비밀번호 불일치 - Email: {email}")
            self._record_failed_attempt(email)
            raise ValueError("잘못된 이메일 또는 패스워드입니다.")
        
        # 성공 시 실패 기록 초기화 및 마지막 로그인 시간 업데이트
        self._clear_failed_attempts(email)
        await self._update_last_login(user["id"])
        
        self.logger.info(f"✅ 사용자 인증 성공 - Email: {email}")
        
        return user

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
