"""
Admin endpoints for Text-to-SQL application.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from services.auth_dependencies import get_current_admin_user, get_current_user, get_auth_service
from services.auth_service import UserResponse, AuthService, UserCreate, UserRole
from services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter()

class UserManagementResponse(BaseModel):
    id: str  # UUID는 문자열로 반환
    email: str
    full_name: str  # username 대신 full_name 사용
    company: Optional[str] = None
    role: str
    is_active: bool
    created_at: str
    updated_at: str
    last_login: Optional[str] = None
    token_usage: int = 0

class UserDetailResponse(UserManagementResponse):
    """사용자 상세 정보 응답 모델"""
    password_changed_at: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class UserCreateRequest(BaseModel):
    email: str
    password: str
    full_name: str
    company: Optional[str] = None
    role: str = "user"
    
    @validator('email')
    def validate_email(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v
    
    @validator('role')
    def validate_role(cls, v):
        if v not in [role.value for role in UserRole]:
            raise ValueError('Invalid role')
        return v

class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    
    @validator('email')
    def validate_email(cls, v):
        if v is not None:
            import re
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
                raise ValueError('Invalid email format')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if v is not None and len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v
    
    @validator('role')
    def validate_role(cls, v):
        if v is not None and v not in [role.value for role in UserRole]:
            raise ValueError('Invalid role')
        return v

class UserListResponse(BaseModel):
    users: List[UserManagementResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int

class UpdateUserRoleRequest(BaseModel):
    new_role: str

class UpdateUserStatusRequest(BaseModel):
    is_active: bool

class SystemStatusResponse(BaseModel):
    status: str
    uptime: str
    database_connections: Dict[str, str]
    cache_status: str
    total_users: int
    active_sessions: int

@router.get("/users", response_model=UserListResponse)
async def get_all_users(
    request: Request,
    current_user: UserResponse = Depends(get_current_admin_user),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(10, ge=1, le=100, description="페이지 크기"),
    search: Optional[str] = Query(None, description="검색어 (이메일, 이름, 회사명)"),
    role: Optional[str] = Query(None, description="역할 필터"),
    status: Optional[str] = Query(None, description="상태 필터")
):
    """Get all users with pagination and search (admin only)."""
    try:
        auth_service: AuthService = request.app.state.auth_service
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Convert status to boolean if provided
        is_active_filter = None
        if status:
            is_active_filter = status.lower() == 'active'
        
        # Get users and total count
        users = await auth_service.get_all_users(
            limit=page_size, 
            offset=offset, 
            search_query=search,
            role_filter=role,
            is_active_filter=is_active_filter
        )
        total_count = await auth_service.get_users_count(
            search_query=search,
            role_filter=role,
            is_active_filter=is_active_filter
        )
        
        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size
        
        user_responses = [
            UserManagementResponse(
                id=str(user["id"]),
                full_name=user["full_name"],
                email=user["email"],
                company=user.get("company"),
                role=user["role"],
                is_active=user["is_active"],
                created_at=user["created_at"],
                updated_at=user.get("updated_at", user["created_at"]),
                last_login=user.get("last_login"),
                token_usage=user.get("token_usage", 0)
            )
            for user in users
        ]
        
        return UserListResponse(
            users=user_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Failed to get all users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@router.get("/users/{user_id}", response_model=dict)
async def get_user_detail(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get user details by ID"""
    try:
        # 관리자 권한 확인
        if current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # AuthService 인스턴스 가져오기
        from services.auth_service import AuthService
        from database.connection_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        auth_service = AuthService(db_manager)
        
        user = await auth_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "success": True,
            "data": user
        }
    except Exception as e:
        logger.error(f"사용자 상세 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users", response_model=dict)
async def create_user(
    user_data: UserCreateRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Create a new user"""
    try:
        # 관리자 권한 확인
        if current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # AnalyticsService 가져오기 (app state에서)
        analytics_service = getattr(request.app.state, 'analytics_service', None)
        
        # UserCreate 객체 생성
        try:
            # role을 UserRole enum으로 변환
            role_enum = UserRole(user_data.role) if user_data.role else UserRole.ANALYST
        except ValueError:
            # 유효하지 않은 role인 경우 기본값 사용
            role_enum = UserRole.ANALYST
            
        user_create_data = UserCreate(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            company=user_data.company,
            role=role_enum
        )
        
        new_user = await auth_service.create_user(user_create_data, analytics_service)
        
        return {
            "success": True,
            "message": "User created successfully",
            "data": new_user
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"사용자 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{user_id}", response_model=dict)
async def update_user(
    user_id: str,
    user_data: UserUpdateRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Update user information"""
    try:
        # 관리자 권한 확인
        if current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # None이 아닌 값들만 업데이트 데이터로 변환
        update_data = {k: v for k, v in user_data.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No data to update")
        
        # 사용자 업데이트
        updated_user = await auth_service.update_user(user_id, update_data)
        
        return {
            "success": True,
            "message": "User updated successfully",
            "data": updated_user
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"사용자 업데이트 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role_data: UpdateUserRoleRequest,
    request: Request,
    current_user: UserResponse = Depends(get_current_admin_user)
):
    """Update user role (admin only)."""
    try:
        auth_service: AuthService = request.app.state.auth_service
        
        await auth_service.update_user_role(user_id=user_id, new_role=role_data.new_role)
        
        return {"message": f"User role updated to {role_data.new_role}"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update user role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user role"
        )

@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    status_data: UpdateUserStatusRequest,
    request: Request,
    current_user: UserResponse = Depends(get_current_admin_user)
):
    """Update user active status (admin only)."""
    try:
        auth_service: AuthService = request.app.state.auth_service
        
        await auth_service.update_user_status(user_id=user_id, is_active=status_data.is_active)
        
        status_text = "activated" if status_data.is_active else "deactivated"
        return {"message": f"User {status_text} successfully"}
        
    except Exception as e:
        logger.error(f"Failed to update user status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user status"
        )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    request: Request,
    current_user: UserResponse = Depends(get_current_admin_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Delete user (admin only)."""
    try:
        # Prevent admin from deleting themselves
        if user_id == current_user.get("id"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        # Check if user exists
        user = await auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        await auth_service.delete_user(user_id=user_id)
        
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

@router.get("/system/status", response_model=SystemStatusResponse)
async def get_system_status(
    request: Request,
    current_user: UserResponse = Depends(get_current_admin_user)
):
    """Get system status (admin only)."""
    try:
        db_manager = request.app.state.db_manager
        auth_service: AuthService = request.app.state.auth_service
        
        # Get database connection status
        db_status = await db_manager.get_connection_status()
        
        # Get cache status
        cache = request.app.state.cache
        cache_status = "connected" if cache.redis_client else "disconnected"
        
        # Get user statistics
        total_users = await auth_service.get_total_user_count()
        
        return SystemStatusResponse(
            status="healthy",
            uptime="N/A",  # Would need to track application start time
            database_connections=db_status,
            cache_status=cache_status,
            total_users=total_users,
            active_sessions=0  # Would need to track active sessions
        )
        
    except Exception as e:
        logger.error(f"Failed to get system status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system status"
        )

@router.post("/system/cache/clear")
async def clear_system_cache(
    request: Request,
    current_user: UserResponse = Depends(get_current_admin_user)
):
    """Clear system cache (admin only)."""
    try:
        cache = request.app.state.cache
        
        # Clear all cache patterns
        cleared_count = await cache.clear_pattern("*")
        
        return {
            "message": "System cache cleared successfully",
            "cleared_keys": cleared_count
        }
        
    except Exception as e:
        logger.error(f"Failed to clear system cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear system cache"
        )

@router.get("/logs")
async def get_system_logs(
    request: Request,
    current_user: UserResponse = Depends(get_current_admin_user),
    limit: int = 100,
    level: str = "INFO"
):
    """Get system logs (admin only)."""
    try:
        # This would typically read from log files or a logging service
        # For now, return a placeholder response
        return {
            "logs": [],
            "total": 0,
            "limit": limit,
            "level": level,
            "message": "Log retrieval not implemented yet"
        }
        
    except Exception as e:
        logger.error(f"Failed to get system logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system logs"
        )