"""
Chat endpoints for Text-to-SQL application.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

from services.auth_dependencies import get_current_user
from services.auth_service import UserResponse
from services.chat_service import ChatSessionService

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatSessionCreate(BaseModel):
    title: Optional[str] = Field(None, description="Session title")
    database: str = Field(default="northwind", description="Target database")

class ChatMessageCreate(BaseModel):
    content: str = Field(..., description="Message content")
    message_type: str = Field(default="user", description="Message type (user/assistant)")

class ChatSessionResponse(BaseModel):
    id: int
    title: str
    database: str
    created_at: str
    updated_at: str
    message_count: int

class ChatMessageResponse(BaseModel):
    id: int
    content: str
    message_type: str
    created_at: str
    sql_query: Optional[str] = None
    query_results: Optional[List[Dict[str, Any]]] = None

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new chat session."""
    try:
        chat_service: ChatSessionService = request.app.state.chat_service
        
        session = await chat_service.create_session(
            user_id=current_user.id,
            title=session_data.title,
            database=session_data.database
        )
        
        return ChatSessionResponse(
            id=session.id,
            title=session.title,
            database=session.database,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            message_count=0
        )
        
    except Exception as e:
        logger.error(f"Failed to create chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat session"
        )

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    """Get user's chat sessions."""
    try:
        chat_service: ChatSessionService = request.app.state.chat_service
        
        sessions = await chat_service.get_user_sessions(
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        
        return [
            ChatSessionResponse(
                id=session.id,
                title=session.title,
                database=session.database,
                created_at=session.created_at.isoformat(),
                updated_at=session.updated_at.isoformat(),
                message_count=session.message_count or 0
            )
            for session in sessions
        ]
        
    except Exception as e:
        logger.error(f"Failed to get chat sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat sessions"
        )

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: int,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific chat session."""
    try:
        chat_service: ChatSessionService = request.app.state.chat_service
        
        session = await chat_service.get_session(
            session_id=session_id,
            user_id=current_user.id
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        return ChatSessionResponse(
            id=session.id,
            title=session.title,
            database=session.database,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            message_count=session.message_count or 0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat session"
        )

@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def add_chat_message(
    session_id: int,
    message_data: ChatMessageCreate,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """Add a message to a chat session."""
    try:
        chat_service: ChatSessionService = request.app.state.chat_service
        
        message = await chat_service.add_message(
            session_id=session_id,
            user_id=current_user.id,
            content=message_data.content,
            message_type=message_data.message_type
        )
        
        return ChatMessageResponse(
            id=message.id,
            content=message.content,
            message_type=message.message_type,
            created_at=message.created_at.isoformat(),
            sql_query=message.sql_query,
            query_results=message.query_results
        )
        
    except Exception as e:
        logger.error(f"Failed to add chat message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add chat message"
        )

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_chat_messages(
    session_id: int,
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0
):
    """Get messages from a chat session."""
    try:
        chat_service: ChatSessionService = request.app.state.chat_service
        
        messages = await chat_service.get_session_messages(
            session_id=session_id,
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        
        return [
            ChatMessageResponse(
                id=message.id,
                content=message.content,
                message_type=message.message_type,
                created_at=message.created_at.isoformat(),
                sql_query=message.sql_query,
                query_results=message.query_results
            )
            for message in messages
        ]
        
    except Exception as e:
        logger.error(f"Failed to get chat messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat messages"
        )

@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: int,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a chat session."""
    try:
        chat_service: ChatSessionService = request.app.state.chat_service
        
        await chat_service.delete_session(
            session_id=session_id,
            user_id=current_user.id
        )
        
        return {"message": "Chat session deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete chat session"
        ) 