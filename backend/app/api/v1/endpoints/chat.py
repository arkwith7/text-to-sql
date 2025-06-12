"""
API routes for chat session management.
"""
import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.chat.service import ChatSessionService
from app.analytics.service import AnalyticsService, EventType

router = APIRouter()

# Request/Response Models for Chat API
class CreateSessionRequest(BaseModel):
    title: Optional[str] = None
    context: Optional[str] = None

class SessionResponse(BaseModel):
    session_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    message_count: int

class MessageResponse(BaseModel):
    message_id: str
    session_id: str
    user_message: str
    ai_response: str
    query_result: Optional[dict] = None
    timestamp: datetime
    sequence_number: int

class AddMessageRequest(BaseModel):
    user_message: str
    ai_response: str
    query_result: Optional[dict] = None

class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
    total_count: int

class SessionMessagesResponse(BaseModel):
    session_id: str
    messages: List[MessageResponse]
    total_count: int

@router.post("/sessions", response_model=SessionResponse, tags=["Chat"])
async def create_chat_session(
    request_data: CreateSessionRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Create a new chat session for the current user."""
    chat_service: ChatSessionService = request.app.state.chat_service
    analytics_service: AnalyticsService = request.app.state.analytics_service
    
    try:
        session = await chat_service.create_session(
            user_id=current_user["id"],
            title=request_data.title,
            context=request_data.context
        )
        
        # Log analytics event
        await analytics_service.log_event(
            user_id=current_user["id"],
            event_type=EventType.CHAT_SESSION_CREATED,
            metadata={"session_id": session["session_id"]}
        )
        
        return SessionResponse(
            session_id=session["session_id"],
            title=session["title"],
            created_at=session["created_at"],
            updated_at=session["updated_at"],
            is_active=session["is_active"],
            message_count=0
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create chat session: {str(e)}"
        )

@router.get("/sessions", response_model=SessionListResponse, tags=["Chat"])
async def get_user_sessions(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get all chat sessions for the current user."""
    chat_service: ChatSessionService = request.app.state.chat_service
    
    try:
        sessions_data = await chat_service.get_user_sessions(
            user_id=current_user["id"],
            limit=limit,
            offset=offset
        )
        
        sessions = [
            SessionResponse(
                session_id=session["session_id"],
                title=session["title"],
                created_at=session["created_at"],
                updated_at=session["updated_at"],
                is_active=session["is_active"],
                message_count=session.get("message_count", 0)
            )
            for session in sessions_data["sessions"]
        ]
        
        return SessionListResponse(
            sessions=sessions,
            total_count=sessions_data["total_count"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sessions: {str(e)}"
        )

@router.get("/sessions/{session_id}/messages", response_model=SessionMessagesResponse, tags=["Chat"])
async def get_session_messages(
    session_id: str,
    request: Request,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get all messages for a specific chat session."""
    chat_service: ChatSessionService = request.app.state.chat_service
    
    try:
        # Verify session belongs to user (security check)
        user_sessions = await chat_service.get_user_sessions(user_id=current_user["id"])
        session_ids = [s["session_id"] for s in user_sessions["sessions"]]
        
        if session_id not in session_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found or access denied"
            )
        
        messages_data = await chat_service.get_session_messages(
            session_id=session_id,
            limit=limit,
            offset=offset
        )
        
        messages = [
            MessageResponse(
                message_id=msg["message_id"],
                session_id=msg["session_id"],
                user_message=msg["user_message"],
                ai_response=msg["ai_response"],
                query_result=msg.get("query_result"),
                timestamp=msg["timestamp"],
                sequence_number=msg["sequence_number"]
            )
            for msg in messages_data["messages"]
        ]
        
        return SessionMessagesResponse(
            session_id=session_id,
            messages=messages,
            total_count=messages_data["total_count"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve messages: {str(e)}"
        )

@router.post("/sessions/{session_id}/messages", response_model=MessageResponse, tags=["Chat"])
async def add_message_to_session(
    session_id: str,
    message_data: AddMessageRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Add a new message to a chat session."""
    chat_service: ChatSessionService = request.app.state.chat_service
    analytics_service: AnalyticsService = request.app.state.analytics_service
    
    try:
        # Verify session belongs to user (security check)
        user_sessions = await chat_service.get_user_sessions(user_id=current_user["id"])
        session_ids = [s["session_id"] for s in user_sessions["sessions"]]
        
        if session_id not in session_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found or access denied"
            )
        
        message = await chat_service.add_message(
            session_id=session_id,
            user_message=message_data.user_message,
            ai_response=message_data.ai_response,
            query_result=message_data.query_result
        )
        
        # Log analytics event
        await analytics_service.log_event(
            user_id=current_user["id"],
            event_type=EventType.QUERY_EXECUTED,  # Reusing existing event type
            metadata={
                "session_id": session_id,
                "message_id": message["message_id"],
                "has_query_result": message_data.query_result is not None
            }
        )
        
        return MessageResponse(
            message_id=message["message_id"],
            session_id=message["session_id"],
            user_message=message["user_message"],
            ai_response=message["ai_response"],
            query_result=message.get("query_result"),
            timestamp=message["timestamp"],
            sequence_number=message["sequence_number"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add message: {str(e)}"
        )

@router.delete("/sessions/{session_id}", tags=["Chat"])
async def deactivate_session(
    session_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Deactivate a chat session (soft delete)."""
    chat_service: ChatSessionService = request.app.state.chat_service
    analytics_service: AnalyticsService = request.app.state.analytics_service
    
    try:
        # Verify session belongs to user (security check)
        user_sessions = await chat_service.get_user_sessions(user_id=current_user["id"])
        session_ids = [s["session_id"] for s in user_sessions["sessions"]]
        
        if session_id not in session_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found or access denied"
            )
        
        await chat_service.deactivate_session(session_id=session_id)
        
        # Log analytics event
        await analytics_service.log_event(
            user_id=current_user["id"],
            event_type=EventType.USER_LOGOUT,  # Reusing closest existing event type
            metadata={
                "session_id": session_id,
                "action": "session_deactivated"
            }
        )
        
        return {"message": "Chat session deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate session: {str(e)}"
        )

@router.get("/sessions/{session_id}/context", tags=["Chat"])
async def get_session_context_for_ai(
    session_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get formatted chat history for AI agent context (internal use)."""
    chat_service: ChatSessionService = request.app.state.chat_service
    
    try:
        # Verify session belongs to user (security check)
        user_sessions = await chat_service.get_user_sessions(user_id=current_user["id"])
        session_ids = [s["session_id"] for s in user_sessions["sessions"]]
        
        if session_id not in session_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found or access denied"
            )
        
        chat_history = await chat_service.get_chat_history_for_agent(session_id=session_id)
        
        return {
            "session_id": session_id,
            "chat_history": chat_history,
            "context_length": len(chat_history)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session context: {str(e)}"
        )
