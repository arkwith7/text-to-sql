"""
Chat session management service.

This service handles:
- Creating and managing chat sessions
- Storing and retrieving chat messages
- Managing conversation context and history
- Session lifecycle management
- Token usage tracking for chat interactions
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
import structlog
import json

from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from database.connection_manager import DatabaseManager
from models.models import ChatSession, ChatMessage, User
from utils.cache import cache
from services.token_usage_service import TokenUsageService

logger = structlog.get_logger(__name__)


class ChatSessionService:
    """Service for managing chat sessions and messages."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize chat session service with database manager."""
        self.db_manager = db_manager
        # Token usage service 초기화
        self.token_usage_service = TokenUsageService(db_manager)
        
    async def create_session(self, user_id: str, title: Optional[str] = None, database: str = "northwind") -> Dict[str, Any]:
        """
        Create a new chat session for a user and return session data.
        
        Args:
            user_id: The user ID
            title: Optional session title
            database: Target database name
        """
        session_id = str(uuid.uuid4())
        
        try:
            query = """
            INSERT INTO chat_sessions (
                id, user_id, title, is_active,
                created_at, updated_at, last_message_at, message_count
            ) VALUES (
                :id, :user_id, :title, :is_active,
                :created_at, :updated_at, :last_message_at, :message_count
            )
            """
            now = datetime.now(timezone.utc)
            params = {
                "id": session_id,
                "user_id": user_id,
                "title": title or f"Chat Session {now.strftime('%Y-%m-%d %H:%M')}",
                "is_active": True,
                "created_at": now,
                "updated_at": now,
                "last_message_at": now,
                "message_count": 0
            }
            
            await self.db_manager.execute_query_safe(query, params=params, database_type="app")
            
            logger.info(f"Created new chat session {session_id} for user {user_id} (database: {database})")
            return {
                "session_id": session_id,
                "title": params["title"],
                "database": database,
                "created_at": params["created_at"],
                "updated_at": params["updated_at"],
                "is_active": True,
                "message_count": 0
            }
        except Exception as e:
            logger.error(f"Error creating chat session: {str(e)}")
            raise
    
    async def get_user_sessions(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all active chat sessions for a user.
        
        Args:
            user_id: The user ID
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            
        Returns:
            List of session dictionaries
        """
        try:
            query = """
            SELECT id, title, created_at, updated_at, last_message_at, message_count
            FROM chat_sessions 
            WHERE user_id = :user_id AND is_active = true
            ORDER BY updated_at DESC
            LIMIT :limit OFFSET :offset
            """
            
            result = await self.db_manager.execute_query_safe(
                query, 
                params={"user_id": user_id, "limit": limit, "offset": offset}, 
                database_type="app"
            )
            
            if result.get("success"):
                return result.get("data", [])
            else:
                logger.error(f"Error fetching user sessions: {result.get('error')}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching user sessions: {str(e)}")
            return []
    
    async def get_session(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific chat session for a user.
        
        Args:
            session_id: The session ID
            user_id: The user ID (for security)
            
        Returns:
            Session dictionary or None if not found
        """
        try:
            query = """
            SELECT id, title, created_at, updated_at, last_message_at, message_count, is_active
            FROM chat_sessions 
            WHERE id = :session_id AND user_id = :user_id AND is_active = true
            """
            
            result = await self.db_manager.execute_query_safe(
                query, 
                params={"session_id": session_id, "user_id": user_id}, 
                database_type="app"
            )
            
            if result.get("success") and result.get("data"):
                return result["data"][0]
            else:
                logger.warning(f"Session {session_id} not found for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching session: {str(e)}")
            return None
    
    async def get_session_messages(self, session_id: str, user_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all messages in a chat session for a specific user.
        
        Args:
            session_id: The session ID
            user_id: The user ID (for security)
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            
        Returns:
            List of message dictionaries
        """
        try:
            # First verify the session belongs to the user
            session = await self.get_session(session_id, user_id)
            if not session:
                logger.warning(f"Session {session_id} not found for user {user_id}")
                return []
            
            query = """
            SELECT id, message_type, content, query_id, sql_query, query_result,
                   execution_time, error_message, timestamp, sequence_number
            FROM chat_messages 
            WHERE session_id = :session_id
            ORDER BY sequence_number ASC
            LIMIT :limit OFFSET :offset
            """
            
            result = await self.db_manager.execute_query_safe(
                query,
                params={"session_id": session_id, "limit": limit, "offset": offset},
                database_type="app"
            )
            
            if result.get("success"):
                return result.get("data", [])
            else:
                logger.error(f"Error fetching session messages: {result.get('error')}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching session messages: {str(e)}")
            return []
    
    async def add_message(
        self, 
        session_id: str, 
        message_type: str, 
        content: str,
        query_id: Optional[str] = None,
        sql_query: Optional[str] = None,
        query_result: Optional[Dict[str, Any]] = None,
        execution_time: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> str:
        """
        Add a new message to a chat session.
        
        Args:
            session_id: The session ID
            message_type: Type of message ('user' or 'assistant')
            content: The message content
            query_id: Optional query ID for assistant messages
            sql_query: Optional SQL query for assistant messages
            query_result: Optional query results for assistant messages
            execution_time: Optional execution time for assistant messages
            error_message: Optional error message
            
        Returns:
            The ID of the newly created message
        """
        message_id = str(uuid.uuid4())
        
        try:
            # Get the next sequence number for this session
            seq_query = """
            SELECT COALESCE(MAX(sequence_number), 0) + 1 as next_seq
            FROM chat_messages 
            WHERE session_id = :session_id
            """
            
            seq_result = await self.db_manager.execute_query_safe(
                seq_query,
                params={"session_id": session_id},
                database_type="app"
            )
            
            sequence_number = 1
            if seq_result.get("success") and seq_result.get("data"):
                sequence_number = seq_result["data"][0]["next_seq"]
            
            # Insert the new message
            insert_query = """
            INSERT INTO chat_messages (
                id, session_id, message_type, content, query_id, sql_query,
                query_result, execution_time, error_message, timestamp, sequence_number
            ) VALUES (
                :id, :session_id, :message_type, :content, :query_id, :sql_query,
                :query_result, :execution_time, :error_message, :timestamp, :sequence_number
            )
            """
            
            # Convert query_result to JSON string if it's a dict/list
            query_result_json = None
            if query_result is not None:
                if isinstance(query_result, (dict, list)):
                    query_result_json = json.dumps(query_result)
                else:
                    query_result_json = str(query_result)
            
            params = {
                "id": message_id,
                "session_id": session_id,
                "message_type": message_type,
                "content": content,
                "query_id": query_id,
                "sql_query": sql_query,
                "query_result": query_result_json,
                "execution_time": execution_time,
                "error_message": error_message,
                "timestamp": datetime.now(timezone.utc),
                "sequence_number": sequence_number
            }
            
            await self.db_manager.execute_query_safe(insert_query, params=params, database_type="app")
            
            # Update session metadata
            await self._update_session_metadata(session_id)
            
            logger.info(f"Added message {message_id} to session {session_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Error adding message to session: {str(e)}")
            raise
    
    async def get_chat_history_for_agent(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Get formatted chat history for AI agent context.
        
        Args:
            session_id: The session ID
            limit: Maximum number of recent messages to include
            
        Returns:
            List of messages formatted for AI agent
        """
        try:
            messages = await self.get_session_messages(session_id, limit)
            
            formatted_history = []
            for msg in messages[-limit:]:  # Get most recent messages
                role = "human" if msg["message_type"] == "user" else "assistant"
                formatted_history.append({
                    "role": role,
                    "content": msg["content"]
                })
            
            return formatted_history
            
        except Exception as e:
            logger.error(f"Error formatting chat history: {str(e)}")
            return []
    
    async def deactivate_session(self, session_id: str) -> bool:
        """
        Deactivate a chat session.
        
        Args:
            session_id: The session ID to deactivate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
            UPDATE chat_sessions 
            SET is_active = false, updated_at = :updated_at
            WHERE id = :session_id
            """
            
            result = await self.db_manager.execute_query_safe(
                query,
                params={
                    "session_id": session_id,
                    "updated_at": datetime.now(timezone.utc)
                },
                database_type="app"
            )
            
            return result.get("success", False)
            
        except Exception as e:
            logger.error(f"Error deactivating session: {str(e)}")
            return False
    
    async def _update_session_metadata(self, session_id: str):
        """Update session metadata like last_message_at and message_count."""
        try:
            query = """
            UPDATE chat_sessions 
            SET 
                last_message_at = :last_message_at,
                updated_at = :updated_at,
                message_count = (
                    SELECT COUNT(*) FROM chat_messages 
                    WHERE session_id = :session_id
                )
            WHERE id = :session_id
            """
            
            await self.db_manager.execute_query_safe(
                query,
                params={
                    "session_id": session_id,
                    "last_message_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                },
                database_type="app"
            )
            
        except Exception as e:
            logger.error(f"Error updating session metadata: {str(e)}")
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific chat session.
        
        Args:
            session_id: The session ID
            
        Returns:
            Session information dictionary or None if not found
        """
        try:
            query = """
            SELECT id, user_id, title, is_active, created_at, updated_at, 
                   last_message_at, message_count
            FROM chat_sessions 
            WHERE id = :session_id
            """
            
            result = await self.db_manager.execute_query_safe(
                query,
                params={"session_id": session_id},
                database_type="app"
            )
            
            if result.get("success") and result.get("data"):
                return result["data"][0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error fetching session info: {str(e)}")
            return None
    
    async def record_chat_token_usage(
        self,
        user_id: str,
        session_id: str,
        message_id: str,
        token_usage: Dict[str, int],
        model_name: str,
        question: str,
        response: str
    ) -> bool:
        """
        채팅 상호작용에서 발생한 토큰 사용량을 기록합니다.
        
        Args:
            user_id: 사용자 ID
            session_id: 채팅 세션 ID
            message_id: 메시지 ID
            token_usage: 토큰 사용량 정보
            model_name: 사용된 모델명
            question: 사용자 질문
            response: AI 응답
            
        Returns:
            성공 여부
        """
        try:
            success = await self.token_usage_service.record_token_usage(
                user_id=user_id,
                session_id=session_id,
                message_id=message_id,
                token_usage=token_usage,
                model_name=model_name,
                query_type="chat_interaction",
                additional_metadata={
                    "question": question[:100],  # 처음 100자만 저장
                    "response_length": len(response),
                    "interaction_type": "chat"
                }
            )
            
            if success:
                logger.info(
                    f"채팅 토큰 사용량 기록 완료",
                    user_id=user_id,
                    session_id=session_id,
                    total_tokens=token_usage.get("total_tokens", 0)
                )
            
            return success
            
        except Exception as e:
            logger.error(
                f"채팅 토큰 사용량 기록 실패: {str(e)}",
                user_id=user_id,
                session_id=session_id
            )
            return False
