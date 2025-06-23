from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import List, Optional

from services.auth_dependencies import get_current_user
from services.auth_service import UserResponse
from services.connection_service import ConnectionService
from database.connection_manager import get_db_session as get_session

router = APIRouter()

class ConnectionBase(BaseModel):
    connection_name: str = Field(..., max_length=100)
    db_type: str = Field("postgresql", max_length=50)
    db_host: str = Field(..., max_length=255)
    db_port: int
    db_user: str = Field(..., max_length=100)
    db_name: str = Field(..., max_length=100)

class ConnectionCreate(ConnectionBase):
    db_password: str

class ConnectionUpdate(BaseModel):
    connection_name: Optional[str] = Field(None, max_length=100)
    db_host: Optional[str] = Field(None, max_length=255)
    db_port: Optional[int] = None
    db_user: Optional[str] = Field(None, max_length=100)
    db_password: Optional[str] = None
    db_name: Optional[str] = Field(None, max_length=100)

class ConnectionResponse(ConnectionBase):
    id: str
    user_id: str

    class Config:
        orm_mode = True

class ConnectionTestResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None

@router.post("/", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    conn_data: ConnectionCreate,
    current_user: UserResponse = Depends(get_current_user),
    session = Depends(get_session)
):
    """Create a new database connection."""
    service = ConnectionService(session)
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    created_conn = await service.create_connection(user_id=user_id, conn_data=conn_data.dict())
    return created_conn

@router.get("/", response_model=List[ConnectionResponse])
async def get_all_connections(
    current_user: UserResponse = Depends(get_current_user),
    session = Depends(get_session)
):
    """Get all database connections for the current user."""
    service = ConnectionService(session)
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    return await service.get_all_connections(user_id=user_id)

@router.get("/{connection_id}", response_model=ConnectionResponse)
async def get_connection(
    connection_id: str,
    current_user: UserResponse = Depends(get_current_user),
    session = Depends(get_session)
):
    """Get a specific database connection."""
    service = ConnectionService(session)
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    conn = await service.get_connection(user_id=user_id, connection_id=connection_id)
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    # Note: get_connection with decrypt=True returns db_password, but Pydantic model won't include it
    return conn

@router.put("/{connection_id}", response_model=ConnectionResponse)
async def update_connection(
    connection_id: str,
    conn_data: ConnectionUpdate,
    current_user: UserResponse = Depends(get_current_user),
    session = Depends(get_session)
):
    """Update a database connection."""
    service = ConnectionService(session)
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    updated_conn = await service.update_connection(
        user_id=user_id,
        connection_id=connection_id,
        conn_data=conn_data.dict(exclude_unset=True)
    )
    if not updated_conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    return updated_conn

@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: str,
    current_user: UserResponse = Depends(get_current_user),
    session = Depends(get_session)
):
    """Delete a database connection."""
    service = ConnectionService(session)
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    success = await service.delete_connection(user_id=user_id, connection_id=connection_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    return None

@router.post("/{connection_id}/test", response_model=ConnectionTestResponse)
async def test_connection(
    connection_id: str,
    current_user: UserResponse = Depends(get_current_user),
    session = Depends(get_session)
):
    """Test a database connection."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"🔌 연결 테스트 시작: connection_id={connection_id}")
        service = ConnectionService(session)
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        logger.info(f"🔌 사용자 ID: {user_id}")
        
        result = await service.test_connection(user_id=user_id, connection_id=connection_id)
        logger.info(f"🔌 연결 테스트 결과: {result}")
        return result
    except Exception as e:
        logger.error(f"💥 연결 테스트 중 예외 발생: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Connection test failed: {str(e)}"
        ) 