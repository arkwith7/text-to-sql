"""
Chat endpoints for Text-to-SQL application.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import traceback
from datetime import datetime, timezone
import time
import uuid
import json

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
    id: str  # Changed from int to str to match UUID
    title: str
    database: str
    created_at: str
    updated_at: str
    message_count: int

class ChatMessageResponse(BaseModel):
    id: str  # Changed from int to str to match UUID
    content: str
    message_type: str
    created_at: str
    sql_query: Optional[str] = None
    query_results: Optional[List[Dict[str, Any]]] = None

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    request: Request,
    current_user = Depends(get_current_user)
):
    """Create a new chat session."""
    # Extract user_id properly
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    
    logger.info(f"🚀 Creating chat session for user {user_id}")
    logger.info(f"📝 Session data: title='{session_data.title}', database='{session_data.database}'")
    
    try:
        chat_service: ChatSessionService = request.app.state.chat_service
        
        session = await chat_service.create_session(
            user_id=user_id,
            title=session_data.title,
            database=session_data.database
        )
        
        logger.info(f"✅ Chat session created successfully: {session}")
        
        return ChatSessionResponse(
            id=session["session_id"],
            title=session["title"],
            database=session_data.database,  # Use from request since it's not in response
            created_at=session["created_at"].isoformat(),
            updated_at=session["updated_at"].isoformat(),
            message_count=session["message_count"]
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to create chat session: {str(e)}")
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create chat session: {str(e)}"
        )

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    request: Request,
    current_user = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    """Get user's chat sessions."""
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    
    logger.info(f"📋 Getting chat sessions for user {user_id} (limit={limit}, offset={offset})")
    
    try:
        chat_service: ChatSessionService = request.app.state.chat_service
        
        sessions = await chat_service.get_user_sessions(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        logger.info(f"✅ Retrieved {len(sessions)} chat sessions")
        
        return [
            ChatSessionResponse(
                id=session["id"],
                title=session["title"],
                database="northwind",  # Default database
                created_at=session["created_at"].isoformat() if hasattr(session["created_at"], 'isoformat') else str(session["created_at"]),
                updated_at=session["updated_at"].isoformat() if hasattr(session["updated_at"], 'isoformat') else str(session["updated_at"]),
                message_count=session.get("message_count", 0)
            )
            for session in sessions
        ]
        
    except Exception as e:
        logger.error(f"❌ Failed to get chat sessions: {str(e)}")
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat sessions: {str(e)}"
        )

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str,  # Changed from int to str
    request: Request,
    current_user = Depends(get_current_user)
):
    """Get a specific chat session."""
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    
    logger.info(f"🔍 Getting chat session {session_id} for user {user_id}")
    
    try:
        chat_service: ChatSessionService = request.app.state.chat_service
        
        session = await chat_service.get_session(
            session_id=session_id,
            user_id=user_id
        )
        
        if not session:
            logger.warning(f"⚠️ Chat session {session_id} not found for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        logger.info(f"✅ Retrieved chat session: {session}")
        
        return ChatSessionResponse(
            id=session["id"],
            title=session["title"],
            database="northwind",  # Default database
            created_at=session["created_at"].isoformat() if hasattr(session["created_at"], 'isoformat') else str(session["created_at"]),
            updated_at=session["updated_at"].isoformat() if hasattr(session["updated_at"], 'isoformat') else str(session["updated_at"]),
            message_count=session.get("message_count", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get chat session: {str(e)}")
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat session: {str(e)}"
        )

@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def add_chat_message(
    session_id: str,  # Changed from int to str
    message_data: ChatMessageCreate,
    request: Request,
    current_user = Depends(get_current_user)
):
    """Add a message to a chat session."""
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    
    logger.info(f"💬 Adding message to session {session_id} for user {user_id}")
    logger.info(f"📝 Message content: '{message_data.content[:100]}...' (type: {message_data.message_type})")
    
    try:
        chat_service: ChatSessionService = request.app.state.chat_service
        
        message_id = await chat_service.add_message(
            session_id=session_id,
            message_type=message_data.message_type,
            content=message_data.content
        )
        
        logger.info(f"✅ Message added successfully: {message_id}")
        
        # Return a basic response since add_message returns just the ID
        return ChatMessageResponse(
            id=message_id,
            content=message_data.content,
            message_type=message_data.message_type,
            created_at=datetime.now(timezone.utc).isoformat(),
            sql_query=None,
            query_results=None
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to add chat message: {str(e)}")
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add chat message: {str(e)}"
        )

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_chat_messages(
    session_id: str,  # Changed from int to str
    request: Request,
    current_user = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0
):
    """Get messages from a chat session."""
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    
    logger.info(f"📨 Getting messages for session {session_id} (user: {user_id}, limit: {limit}, offset: {offset})")
    
    try:
        chat_service: ChatSessionService = request.app.state.chat_service
        
        messages = await chat_service.get_session_messages(
            session_id=session_id,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        logger.info(f"✅ Retrieved {len(messages)} messages")
        
        # Parse and format messages
        formatted_messages = []
        for message in messages:
            # Parse query_result if it's a JSON string
            query_results = message.get("query_result")
            if query_results and isinstance(query_results, str):
                try:
                    query_results = json.loads(query_results)
                except (json.JSONDecodeError, ValueError):
                    query_results = None
            
            formatted_messages.append(
                ChatMessageResponse(
                    id=message["id"],
                    content=message["content"],
                    message_type=message["message_type"],
                    created_at=message["timestamp"].isoformat() if hasattr(message["timestamp"], 'isoformat') else str(message["timestamp"]),
                    sql_query=message.get("sql_query"),
                    query_results=query_results
                )
            )
        
        return formatted_messages
        
    except Exception as e:
        logger.error(f"❌ Failed to get chat messages: {str(e)}")
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat messages: {str(e)}"
        )

@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,  # Changed from int to str
    request: Request,
    current_user = Depends(get_current_user)
):
    """Delete a chat session."""
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    
    logger.info(f"🗑️ Deleting chat session {session_id} for user {user_id}")
    
    try:
        chat_service: ChatSessionService = request.app.state.chat_service
        
        success = await chat_service.deactivate_session(session_id)
        
        if success:
            logger.info(f"✅ Chat session {session_id} deleted successfully")
            return {"message": "Chat session deleted successfully"}
        else:
            logger.warning(f"⚠️ Failed to delete chat session {session_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found or could not be deleted"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete chat session: {str(e)}")
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete chat session: {str(e)}"
        )

# New endpoint for AI query processing
class ChatQueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question")
    context: Optional[str] = Field(None, description="Additional context for the query")
    include_explanation: bool = Field(default=True, description="Include SQL explanation")
    max_rows: Optional[int] = Field(default=100, description="Maximum rows to return")

class ChatQueryResponse(BaseModel):
    user_message_id: str
    assistant_message_id: str
    question: str
    sql_query: str
    results: List[Dict[str, Any]]
    explanation: Optional[str] = None
    execution_time: float
    row_count: int
    success: bool
    error_message: Optional[str] = None

@router.post("/sessions/{session_id}/query", response_model=ChatQueryResponse)
async def process_chat_query(
    session_id: str,
    query_request: ChatQueryRequest,
    request: Request,
    current_user = Depends(get_current_user)
):
    """Process a natural language query in a chat session."""
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    
    logger.info(f"🤖 Processing AI query in session {session_id} for user {user_id}")
    logger.info(f"❓ User question: '{query_request.question}'")
    
    try:
        chat_service: ChatSessionService = request.app.state.chat_service
        sql_agent = request.app.state.sql_agent
        analytics_service = request.app.state.analytics_service
        
        # Verify session exists and belongs to user
        session = await chat_service.get_session(session_id, user_id)
        if not session:
            logger.warning(f"⚠️ Session {session_id} not found for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Add user message to chat
        user_message_id = await chat_service.add_message(
            session_id=session_id,
            message_type="user",
            content=query_request.question
        )
        
        logger.info(f"💬 User message added: {user_message_id}")
        
        # Get chat history for context
        chat_history = await chat_service.get_chat_history_for_agent(session_id, limit=5)
        
        # Process the query with SQL agent
        start_time = time.time()
        
        try:
            # Execute the query using the SQL agent
            logger.info(f"🚀 About to call SQL Agent with question: '{query_request.question}'")
            logger.info(f"🔧 SQL Agent object: {sql_agent}")
            logger.info(f"🔧 SQL Agent type: {type(sql_agent)}")
            
            result = await sql_agent.execute_query(
                question=query_request.question,
                database="northwind",  # Default database
                context=query_request.context,
                user_id=user_id,
                include_explanation=query_request.include_explanation,
                max_rows=query_request.max_rows
            )
            
            logger.info(f"🎯 SQL Agent returned: {result}")
            
            execution_time = time.time() - start_time
            
            logger.info(f"🔍 SQL generated: {result.get('sql_query', 'N/A')}")
            logger.info(f"⏱️ Query executed in {execution_time:.3f}s")
            logger.info(f"📊 Results: {len(result.get('results', []))} rows")
            
            # Prepare assistant response content
            assistant_content = f"I found the answer to your question. Here's what I discovered:\n\n"
            
            if result.get('explanation'):
                assistant_content += f"**Explanation:** {result['explanation']}\n\n"
            
            if result.get('sql_query'):
                assistant_content += f"**SQL Query:**\n```sql\n{result['sql_query']}\n```\n\n"
            
            results = result.get('results', [])
            if results:
                assistant_content += f"**Results:** Found {len(results)} record(s)\n"
                # Add a summary of the first few results
                if len(results) <= 5:
                    assistant_content += "Here are all the results:\n"
                    for i, row in enumerate(results, 1):
                        assistant_content += f"{i}. {str(row)}\n"
                else:
                    assistant_content += f"Here are the first 3 results (showing 3 of {len(results)}):\n"
                    for i, row in enumerate(results[:3], 1):
                        assistant_content += f"{i}. {str(row)}\n"
            else:
                assistant_content += "No results found for your query."
            
            # Add assistant message to chat
            assistant_message_id = await chat_service.add_message(
                session_id=session_id,
                message_type="assistant",
                content=assistant_content,
                query_id=str(uuid.uuid4()),
                sql_query=result.get('sql_query'),
                query_result=results,
                execution_time=execution_time
            )
            
            logger.info(f"🤖 Assistant message added: {assistant_message_id}")
            
            # Log analytics
            await analytics_service.log_query_execution(
                query_id=str(uuid.uuid4()),
                user_id=user_id,
                question=query_request.question,
                sql_query=result.get('sql_query', ''),
                execution_time=execution_time,
                row_count=len(results),
                success=True
            )
            
            logger.info(f"✅ Chat query processed successfully")
            
            return ChatQueryResponse(
                user_message_id=user_message_id,
                assistant_message_id=assistant_message_id,
                question=query_request.question,
                sql_query=result.get('sql_query', ''),
                results=results,
                explanation=result.get('explanation'),
                execution_time=execution_time,
                row_count=len(results),
                success=True
            )
            
        except Exception as query_error:
            execution_time = time.time() - start_time
            error_message = str(query_error)
            
            logger.error(f"❌ Query execution failed: {error_message}")
            
            # Add error message to chat
            assistant_content = f"I encountered an error while processing your question:\n\n**Error:** {error_message}\n\nPlease try rephrasing your question or check if the data you're looking for exists in the database."
            
            assistant_message_id = await chat_service.add_message(
                session_id=session_id,
                message_type="assistant",
                content=assistant_content,
                error_message=error_message,
                execution_time=execution_time
            )
            
            # Log failed analytics
            await analytics_service.log_query_execution(
                query_id=str(uuid.uuid4()),
                user_id=user_id,
                question=query_request.question,
                sql_query="",
                execution_time=execution_time,
                row_count=0,
                success=False,
                error_message=error_message
            )
            
            return ChatQueryResponse(
                user_message_id=user_message_id,
                assistant_message_id=assistant_message_id,
                question=query_request.question,
                sql_query="",
                results=[],
                execution_time=execution_time,
                row_count=0,
                success=False,
                error_message=error_message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to process chat query: {str(e)}")
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat query: {str(e)}"
        ) 