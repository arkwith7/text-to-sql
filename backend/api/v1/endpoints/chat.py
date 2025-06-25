"""
Chat endpoints for Text-to-SQL application.
Enhanced with improved Core Module agents and token usage tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
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
from services.token_usage_service import TokenUsageService
from core.utils.cost_calculator import calculate_cost_from_usage
from utils.logging_config import ChatLogger, RequestLogger

logger = logging.getLogger(__name__)

router = APIRouter()

class QuerySaveRequest(BaseModel):
    title: str = Field(..., description="Query title/name")
    question: str = Field(..., description="Original question")
    sql_query: str = Field(..., description="Generated SQL query")
    query_results: Optional[List[Dict[str, Any]]] = Field(None, description="Query results")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for categorization")
    notes: Optional[str] = Field(None, description="User notes")

class QueryUpdateRequest(BaseModel):
    title: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None

class SavedQueryResponse(BaseModel):
    id: str
    title: str
    question: str
    sql_query: str
    query_results: Optional[List[Dict[str, Any]]] = None
    tags: List[str]
    notes: Optional[str] = None
    created_at: str
    updated_at: str
    user_id: str

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

# Enhanced Chat Query Models
class ChatQueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question")
    connection_id: Optional[str] = Field(
        None,
        description="분석할 데이터베이스 연결 ID (생략 시 기본 northwind 사용)",
    )
    context: Optional[str] = Field(None, description="Additional context for the query")
    include_explanation: bool = Field(default=True, description="Include SQL explanation")
    max_rows: Optional[int] = Field(default=100, description="Maximum rows to return")
    agent_type: str = Field(default="enhanced", description="Agent type: 'enhanced', 'langchain', or 'auto'")

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
    agent_used: str = Field(description="Which agent was used for processing")
    agent_info: Optional[Dict[str, Any]] = None

# 다른 함수들도 비슷하게 로깅 추가
@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    request: Request,
    current_user = Depends(get_current_user)
):
    """Create a new chat session with enhanced logging."""
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.info(
        f"🚀 새 채팅 세션 생성 요청 - User: {user_id}",
        extra={
            'request_id': request_id,
            'user_id': user_id,
            'session_title': session_data.title,
            'database': session_data.database
        }
    )
    
    try:
        chat_service: ChatSessionService = request.app.state.chat_service
        
        session = await chat_service.create_session(
            user_id=user_id,
            title=session_data.title,
            database=session_data.database
        )
        
        logger.info(
            f"✅ 채팅 세션 생성 완료 - Session ID: {session['session_id']}",
            extra={
                'request_id': request_id,
                'user_id': user_id,
                'session_id': session['session_id'],
                'session_title': session['title']
            }
        )
        
        # 세션 이벤트 로깅
        ChatLogger.log_session_event(
            session_id=session['session_id'],
            user_id=user_id,
            event_type="created",
            details={
                'title': session['title'],
                'database': session_data.database
            }
        )
        
        return ChatSessionResponse(
            id=session["session_id"],
            title=session["title"],
            database=session_data.database,
            created_at=session["created_at"].isoformat(),
            updated_at=session["updated_at"].isoformat(),
            message_count=session["message_count"]
        )
        
    except Exception as e:
        logger.error(
            f"❌ 채팅 세션 생성 실패 - User: {user_id}, 오류: {str(e)}",
            extra={
                'request_id': request_id,
                'user_id': user_id,
                'error_details': str(e)
            },
            exc_info=True
        )
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

# process_chat_query 함수의 로깅 개선 예시:
@router.post("/sessions/{session_id}/query", response_model=ChatQueryResponse)
async def process_chat_query(
    session_id: str,
    query_request: ChatQueryRequest,
    request: Request,
    current_user = Depends(get_current_user)
):
    """Process a natural language query in a chat session."""
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    # 요청 시작 로깅
    ChatLogger.log_chat_message(
        session_id=session_id,
        user_id=user_id,
        message_type="user",
        content=query_request.question
    )
    
    logger.info(
        f"🤖 AI 쿼리 처리 시작 - Session: {session_id}, User: {user_id}",
        extra={
            'request_id': request_id,
            'session_id': session_id,
            'user_id': user_id,
            'question_length': len(query_request.question),
            'include_explanation': query_request.include_explanation,
            'max_rows': query_request.max_rows
        }
    )
    
    try:
        chat_service: ChatSessionService = request.app.state.chat_service
        sql_agent = request.app.state.sql_agent
        analytics_service = request.app.state.analytics_service
        db_manager = request.app.state.db_manager
        
        # 세션 검증 로깅
        session = await chat_service.get_session(session_id, user_id)
        if not session:
            logger.warning(
                f"⚠️ 세션을 찾을 수 없음 - Session: {session_id}, User: {user_id}",
                extra={'request_id': request_id, 'session_id': session_id, 'user_id': user_id}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # 사용자 메시지 추가 로깅
        user_message_id = await chat_service.add_message(
            session_id=session_id,
            message_type="user",
            content=query_request.question
        )
        
        logger.info(
            f"💬 사용자 메시지 추가됨 - Message ID: {user_message_id}",
            extra={'request_id': request_id, 'session_id': session_id, 'user_id': user_id, 'message_id': user_message_id}
        )
        
        # 채팅 히스토리 조회 로깅
        chat_history = await chat_service.get_chat_history_for_agent(session_id, limit=5)
        logger.debug(
            f"📜 채팅 히스토리 조회 완료 - {len(chat_history)}개 메시지",
            extra={'request_id': request_id, 'session_id': session_id, 'history_count': len(chat_history)}
        )
        
        # 데이터베이스 엔진 준비 (connection_id가 전달된 경우 동적 엔진 사용)
        analysis_engine = None
        if query_request.connection_id:
            analysis_engine = await db_manager.get_analysis_db_engine(
                connection_id=query_request.connection_id,
                user_id=user_id,
            )

        # Enhanced Agent 선택 및 실행 로깅
        start_time = time.time()
        agent_used = "enhanced"  # 기본값
        
        # Agent 선택 로직
        enhanced_sql_agent = sql_agent  # 기본 Enhanced SQL Agent
        langchain_agent = getattr(request.app.state, 'langchain_agent', None)
        
        # Agent 선택
        if query_request.agent_type == "langchain" and langchain_agent:
            selected_agent = langchain_agent
            agent_used = "langchain"
            logger.info(f"🤖 LangChain Agent 선택됨")
        elif query_request.agent_type == "auto":
            # 복잡한 질문은 LangChain, 간단한 질문은 Enhanced SQL Agent
            if len(query_request.question.split()) > 10 and langchain_agent:
                selected_agent = langchain_agent
                agent_used = "langchain_auto"
                logger.info(f"🤖 자동 선택: LangChain Agent (복잡한 질문)")
            else:
                selected_agent = enhanced_sql_agent
                agent_used = "enhanced_auto"
                logger.info(f"⚡ 자동 선택: Enhanced SQL Agent (간단한 질문)")
        else:
            # Default: Enhanced SQL Agent
            selected_agent = enhanced_sql_agent
            agent_used = "enhanced"
            logger.info(f"⚡ Enhanced SQL Agent 선택됨 (기본)")
        
        logger.info(
            f"🚀 {agent_used.upper()} Agent 실행 시작 - Question: '{query_request.question[:100]}...'",
            extra={
                'request_id': request_id,
                'session_id': session_id,
                'user_id': user_id,
                'agent_type': agent_used,
                'agent_class': type(selected_agent).__name__,
                'question_length': len(query_request.question)
            }
        )
        
        try:
            # --- 에이전트 유형별 실행 ---
            is_langchain_agent = type(selected_agent).__name__ == 'LangChainTextToSQLAgent'

            if is_langchain_agent:
                # LangChain Agent 는 여전히 northwind 고정 (추후 개선)
                result = await selected_agent.execute_query(
                    question=query_request.question,
                    user_id=str(user_id),
                    include_debug_info=False,
                )
            else:
                # Enhanced SQL Agent
                if analysis_engine is not None:
                    # 동적 연결 사용
                    result = await selected_agent.execute_query(
                        question=query_request.question,
                        engine=analysis_engine,
                        context=query_request.context,
                        user_id=user_id,
                        include_explanation=query_request.include_explanation,
                        max_rows=query_request.max_rows,
                    )
                else:
                    # 기존 northwind 엔진 (execute_query_sync 지원)
                    if hasattr(selected_agent, "execute_query_sync"):
                        result = selected_agent.execute_query_sync(
                            question=query_request.question,
                            database="northwind",
                            include_explanation=query_request.include_explanation,
                            max_rows=query_request.max_rows,
                        )
                    else:
                        result = await selected_agent.execute_query(
                            question=query_request.question,
                            database="northwind",
                            context=query_request.context,
                            user_id=user_id,
                            include_explanation=query_request.include_explanation,
                            max_rows=query_request.max_rows,
                        )
            
            execution_time = time.time() - start_time
            
            logger.info(
                f"🎯 {agent_used.upper()} Agent 실행 완료 - 시간: {execution_time:.3f}s, 결과: {len(result.get('results', []))}행",
                extra={
                    'request_id': request_id,
                    'session_id': session_id,
                    'user_id': user_id,
                    'agent_type': agent_used,
                    'execution_time': execution_time,
                    'result_count': len(result.get('results', [])),
                    'sql_query': result.get('sql_query', 'N/A')[:200] + '...' if len(result.get('sql_query', '')) > 200 else result.get('sql_query', 'N/A'),
                    'success': True
                }
            )
            
            # 어시스턴트 응답 생성 - 순수한 AI 설명만 포함
            assistant_content = ""
            
            # AI의 답변/설명만 포함 (SQL과 결과는 별도 필드에 저장)
            if result.get('explanation'):
                assistant_content = result['explanation']
            elif result.get('answer'):
                assistant_content = result['answer']
            else:
                # 기본 메시지
                if result.get('results') and len(result['results']) > 0:
                    assistant_content = f"쿼리가 성공적으로 실행되어 {len(result['results'])}개의 결과를 찾았습니다."
                else:
                    assistant_content = "쿼리가 실행되었지만 결과를 찾지 못했습니다."
            
            # 어시스턴트 메시지 추가
            assistant_message_id = await chat_service.add_message(
                session_id=session_id,
                message_type="assistant",
                content=assistant_content,
                query_id=str(uuid.uuid4()),
                sql_query=result.get('sql_query'),
                query_result=result.get('results', []),
                execution_time=execution_time
            )
            
            logger.info(
                f"🤖 어시스턴트 응답 생성 완료 - Message ID: {assistant_message_id}",
                extra={
                    'request_id': request_id,
                    'session_id': session_id,
                    'user_id': user_id,
                    'message_id': assistant_message_id,
                    'response_length': len(assistant_content)
                }
            )
            
            # 채팅 메시지 로깅
            ChatLogger.log_chat_message(
                session_id=session_id,
                user_id=user_id,
                message_type="assistant",
                content=assistant_content,
                query_result=result.get('results', []),
                execution_time=execution_time
            )
            
            # 분석 로깅 - 토큰 사용량 포함
            token_usage = result.get('token_usage', {})
            await analytics_service.log_query_execution_with_tokens(
                query_id=str(uuid.uuid4()),
                user_id=user_id,
                question=query_request.question,
                sql_query=result.get('sql_query', ''),
                execution_time=execution_time,
                row_count=len(result.get('results', [])),
                success=True,
                prompt_tokens=token_usage.get('prompt_tokens', 0),
                completion_tokens=token_usage.get('completion_tokens', 0),
                total_tokens=token_usage.get('total_tokens', 0),
                llm_model=result.get('model', 'gpt-4o-mini'),
                llm_cost_estimate=calculate_cost_from_usage(
                    {
                        'prompt_tokens': token_usage.get('prompt_tokens', 0),
                        'completion_tokens': token_usage.get('completion_tokens', 0)
                    },
                    result.get('model', 'gpt-4o-mini')
                )
            )
            
            logger.info(
                f"✅ 채팅 쿼리 처리 완료 - 총 시간: {time.time() - start_time:.3f}s",
                extra={
                    'request_id': request_id,
                    'session_id': session_id,
                    'user_id': user_id,
                    'total_time': time.time() - start_time,
                    'success': True
                }
            )
            
            # Agent 정보 수집
            agent_info = result.get('agent_info', {})
            if not agent_info:
                agent_info = {
                    'agent_type': agent_used,
                    'class_name': type(selected_agent).__name__,
                    'database': "northwind",
                    'postgres_optimized': True,
                    'simulation_mode': getattr(selected_agent, 'enable_simulation', True) if hasattr(selected_agent, 'enable_simulation') else True
                }
                
            return ChatQueryResponse(
                user_message_id=user_message_id,
                assistant_message_id=assistant_message_id,
                question=query_request.question,
                sql_query=result.get('sql_query', ''),
                results=result.get('results', []),
                explanation=result.get('explanation'),
                execution_time=execution_time,
                row_count=len(result.get('results', [])),
                success=True,
                agent_used=agent_used,
                agent_info=agent_info
            )
            
        except Exception as query_error:
            execution_time = time.time() - start_time
            error_message = str(query_error)
            
            logger.error(
                f"❌ SQL 에이전트 실행 실패 - 오류: {error_message}",
                extra={
                    'request_id': request_id,
                    'session_id': session_id,
                    'user_id': user_id,
                    'execution_time': execution_time,
                    'error_details': error_message,
                    'success': False
                },
                exc_info=True
            )
            
            # 오류 응답 생성
            assistant_content = f"죄송합니다. 질문을 처리하는 중 오류가 발생했습니다:\n\n**오류:** {error_message}\n\n질문을 다시 작성해 주시거나 데이터베이스에 해당 정보가 있는지 확인해 주세요."
            
            assistant_message_id = await chat_service.add_message(
                session_id=session_id,
                message_type="assistant",
                content=assistant_content,
                error_message=error_message,
                execution_time=execution_time
            )
            
            # 오류 분석 로깅 - 토큰 사용량 포함 (가능한 경우)
            token_usage = {}
            if 'result' in locals() and result and isinstance(result, dict):
                token_usage = result.get('token_usage', {})
            
            await analytics_service.log_query_execution_with_tokens(
                query_id=str(uuid.uuid4()),
                user_id=user_id,
                question=query_request.question,
                sql_query="",
                execution_time=execution_time,
                row_count=0,
                success=False,
                error_message=error_message,
                prompt_tokens=token_usage.get('prompt_tokens', 0),
                completion_tokens=token_usage.get('completion_tokens', 0),
                total_tokens=token_usage.get('total_tokens', 0),
                llm_model=result.get('model', 'gpt-4o-mini') if 'result' in locals() and result else 'gpt-4o-mini',
                llm_cost_estimate=calculate_cost_from_usage(
                    {
                        'prompt_tokens': token_usage.get('prompt_tokens', 0),
                        'completion_tokens': token_usage.get('completion_tokens', 0)
                    },
                    result.get('model', 'gpt-4o-mini') if 'result' in locals() and result else 'gpt-4o-mini'
                )
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
                error_message=error_message,
                agent_used=query_request.agent_type,
                agent_info=None
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ 채팅 쿼리 처리 실패 - 예상치 못한 오류: {str(e)}",
            extra={
                'request_id': request_id,
                'session_id': session_id,
                'user_id': user_id,
                'error_details': str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat query: {str(e)}"
        )

# Enhanced Agent 테스트 엔드포인트 추가
@router.get("/test/agents", tags=["Testing"])
async def test_agents(
    request: Request,
    question: str = Query(default="고객 수를 알려주세요", description="Test question"),
    agent_type: str = Query(default="enhanced", description="Agent type to test")
):
    """Test enhanced agents without session requirement."""
    logger.info(f"🧪 Agent 테스트 시작 - 질문: '{question}', Agent: {agent_type}")
    
    try:
        # Agent 선택
        enhanced_sql_agent = getattr(request.app.state, 'sql_agent', None)
        langchain_agent = getattr(request.app.state, 'langchain_agent', None)
        
        start_time = time.time()
        
        if agent_type == "enhanced" and enhanced_sql_agent:
            if hasattr(enhanced_sql_agent, 'execute_query_sync'):
                result = enhanced_sql_agent.execute_query_sync(question)
            else:
                result = await enhanced_sql_agent.execute_query(question, database="northwind", user_id=1)
                
        elif agent_type == "langchain" and langchain_agent:
            result = await langchain_agent.execute_query(question, user_id="test_user")
            
        else:
            # 기본 PostgreSQL 스키마 테스트
            from core.tools import get_database_schema, generate_sql_from_question, execute_sql_query_sync
            
            try:
                schema = json.loads(get_database_schema("northwind"))
                sql_result = json.loads(generate_sql_from_question(question))
                execution_result = json.loads(execute_sql_query_sync(sql_result.get('sql_query', 'SELECT 1')))
                
                result = {
                    'success': True,
                    'sql_query': sql_result.get('sql_query', ''),
                    'results': execution_result.get('results', []),
                    'explanation': sql_result.get('explanation', ''),
                    'database_tables': len(schema.get('tables', {})),
                    'agent_type': 'function_tools'
                }
            except Exception as tool_error:
                result = {
                    'success': False,
                    'error': f"Function tools 테스트 실패: {str(tool_error)}",
                    'agent_type': 'function_tools'
                }
        
        execution_time = time.time() - start_time
        
        test_result = {
            'success': result.get('success', False),
            'question': question,
            'agent_type': agent_type,
            'execution_time': execution_time,
            'result': result,
            'agents_available': {
                'enhanced_sql_agent': enhanced_sql_agent is not None,
                'langchain_agent': langchain_agent is not None,
                'function_tools': True
            }
        }
        
        logger.info(f"✅ Agent 테스트 완료 - Agent: {agent_type}, 성공: {result.get('success', False)}, 시간: {execution_time:.3f}s")
        
        return test_result
        
    except Exception as e:
        logger.error(f"❌ Agent 테스트 실패: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'question': question,
            'agent_type': agent_type
        }

@router.get("/status", tags=["System"])
async def get_chat_system_status(request: Request):
    """Get chat system status with enhanced agent information."""
    try:
        enhanced_sql_agent = getattr(request.app.state, 'sql_agent', None)
        langchain_agent = getattr(request.app.state, 'langchain_agent', None)
        
        # Enhanced SQL Agent 테스트
        enhanced_status = "❌ 비활성"
        if enhanced_sql_agent:
            try:
                if hasattr(enhanced_sql_agent, 'execute_query_sync'):
                    test_result = enhanced_sql_agent.execute_query_sync("SELECT 1")
                    enhanced_status = "✅ 활성 (동기 지원)" if test_result.get('success') else "⚠️ 오류 발생"
                else:
                    enhanced_status = "✅ 활성 (비동기만)"
            except Exception:
                enhanced_status = "⚠️ 초기화됨, 테스트 실패"
        
        # LangChain Agent 테스트
        langchain_status = "❌ 비활성"
        if langchain_agent:
            try:
                agent_info = langchain_agent.get_agent_info()
                langchain_status = f"✅ 활성 ({agent_info.get('model', 'Unknown')})"
            except Exception:
                langchain_status = "⚠️ 초기화됨, 테스트 실패"
        
        # Function Tools 테스트
        function_tools_status = "❌ 비활성"
        try:
            from core.tools import get_database_schema
            schema = get_database_schema("northwind")
            function_tools_status = "✅ 활성 (PostgreSQL Northwind)"
        except Exception:
            function_tools_status = "⚠️ 오류"
        
        return {
            'chat_system': {
                'status': 'active',
                'enhanced_sql_agent': enhanced_status,
                'langchain_agent': langchain_status,
                'function_tools': function_tools_status
            },
            'database': {
                'northwind': '✅ PostgreSQL 최적화',
                'tables': 8,
                'simulation_mode': True
            },
            'core_module': {
                'version': '2.0.0',
                'jupyter_patterns': '✅ 적용됨',
                'postgres_optimized': True
            }
        }
        
    except Exception as e:
        logger.error(f"시스템 상태 조회 실패: {str(e)}")
        return {
            'error': str(e),
            'status': 'error'
        }


@router.post("/queries/save", response_model=SavedQueryResponse)
async def save_query(
    request: QuerySaveRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    쿼리를 저장합니다.
    """
    try:
        from database.connection_manager import get_db_manager
        
        db_manager = get_db_manager()
        query_id = str(uuid.uuid4())
        
        # query_templates 테이블에 저장
        save_query_sql = """
            INSERT INTO query_templates (
                id, user_id, name, description, sql_template, 
                parameters, tags, created_at, updated_at,
                question, query_results
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        now = datetime.now(timezone.utc)
        await db_manager.execute_query(
            save_query_sql,
            [
                query_id,
                current_user.id,
                request.title,
                request.notes or f"Saved query: {request.title}",
                request.sql_query,
                "{}",  # Empty parameters JSON
                ",".join(request.tags) if request.tags else "",
                now,
                now,
                request.question,
                json.dumps(request.query_results) if request.query_results else None
            ]
        )
        
        logger.info(f"쿼리 저장 완료 - ID: {query_id}, 사용자: {current_user.email}")
        
        return SavedQueryResponse(
            id=query_id,
            title=request.title,
            question=request.question,
            sql_query=request.sql_query,
            query_results=request.query_results,
            tags=request.tags or [],
            notes=request.notes,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            user_id=current_user.id
        )
        
    except Exception as e:
        logger.error(f"쿼리 저장 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"쿼리 저장 실패: {str(e)}"
        )


@router.get("/queries/saved", response_model=List[SavedQueryResponse])
async def get_saved_queries(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    search: Optional[str] = Query(None, description="Search in title or question"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    사용자의 저장된 쿼리 목록을 조회합니다.
    """
    try:
        from database.connection_manager import get_db_manager
        
        db_manager = get_db_manager()
        
        # 기본 쿼리
        base_query = """
            SELECT 
                id, name as title, description, sql_template as sql_query,
                tags, created_at, updated_at, question, query_results
            FROM query_templates 
            WHERE user_id = ?
        """
        params = [current_user.id]
        
        # 필터링 조건 추가
        if tag:
            base_query += " AND (tags LIKE ? OR tags LIKE ? OR tags LIKE ?)"
            params.extend([f"{tag},%", f"%,{tag},%", f"%,{tag}"])
        
        if search:
            base_query += " AND (name LIKE ? OR question LIKE ? OR description LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        base_query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        results = await db_manager.execute_query(base_query, params)
        
        saved_queries = []
        for row in results:
            query_results = None
            if row[8]:  # query_results column
                try:
                    query_results = json.loads(row[8])
                except:
                    query_results = None
            
            saved_queries.append(SavedQueryResponse(
                id=row[0],
                title=row[1],
                question=row[7] or row[1],  # question or title as fallback
                sql_query=row[3],
                query_results=query_results,
                tags=row[4].split(',') if row[4] else [],
                notes=row[2],
                created_at=row[5].isoformat() if hasattr(row[5], 'isoformat') else str(row[5]),
                updated_at=row[6].isoformat() if hasattr(row[6], 'isoformat') else str(row[6]),
                user_id=current_user.id
            ))
        
        logger.info(f"저장된 쿼리 조회 완료 - 사용자: {current_user.email}, 결과: {len(saved_queries)}개")
        return saved_queries
        
    except Exception as e:
        logger.error(f"저장된 쿼리 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"저장된 쿼리 조회 실패: {str(e)}"
        )


@router.put("/queries/{query_id}", response_model=SavedQueryResponse)
async def update_saved_query(
    query_id: str,
    request: QueryUpdateRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    저장된 쿼리를 업데이트합니다.
    """
    try:
        from database.connection_manager import get_db_manager
        
        db_manager = get_db_manager()
        
        # 기존 쿼리 확인
        check_query = """
            SELECT id, name, description, sql_template, tags, question, query_results
            FROM query_templates 
            WHERE id = ? AND user_id = ?
        """
        existing = await db_manager.execute_query(check_query, [query_id, current_user.id])
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="저장된 쿼리를 찾을 수 없습니다."
            )
        
        existing_row = existing[0]
        
        # 업데이트할 필드들
        update_fields = []
        params = []
        
        if request.title is not None:
            update_fields.append("name = ?")
            params.append(request.title)
        
        if request.notes is not None:
            update_fields.append("description = ?")
            params.append(request.notes)
        
        if request.tags is not None:
            update_fields.append("tags = ?")
            params.append(",".join(request.tags))
        
        if update_fields:
            update_fields.append("updated_at = ?")
            params.append(datetime.now(timezone.utc))
            params.append(query_id)
            params.append(current_user.id)
            
            update_query = f"""
                UPDATE query_templates 
                SET {', '.join(update_fields)}
                WHERE id = ? AND user_id = ?
            """
            
            await db_manager.execute_query(update_query, params)
        
        # 업데이트된 데이터 반환
        updated = await db_manager.execute_query(check_query, [query_id, current_user.id])
        updated_row = updated[0]
        
        query_results = None
        if updated_row[6]:
            try:
                query_results = json.loads(updated_row[6])
            except:
                query_results = None
        
        logger.info(f"쿼리 업데이트 완료 - ID: {query_id}, 사용자: {current_user.email}")
        
        return SavedQueryResponse(
            id=updated_row[0],
            title=updated_row[1],
            question=updated_row[5] or updated_row[1],
            sql_query=updated_row[3],
            query_results=query_results,
            tags=updated_row[4].split(',') if updated_row[4] else [],
            notes=updated_row[2],
            created_at=existing_row[5] if hasattr(existing_row[5], 'isoformat') else str(existing_row[5]),
            updated_at=datetime.now(timezone.utc).isoformat(),
            user_id=current_user.id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"쿼리 업데이트 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"쿼리 업데이트 실패: {str(e)}"
        )


@router.delete("/queries/{query_id}")
async def delete_saved_query(
    query_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    저장된 쿼리를 삭제합니다.
    """
    try:
        from database.connection_manager import get_db_manager
        
        db_manager = get_db_manager()
        
        # 쿼리 존재 확인
        check_query = """
            SELECT id FROM query_templates 
            WHERE id = ? AND user_id = ?
        """
        existing = await db_manager.execute_query(check_query, [query_id, current_user.id])
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="저장된 쿼리를 찾을 수 없습니다."
            )
        
        # 삭제 실행
        delete_query = """
            DELETE FROM query_templates 
            WHERE id = ? AND user_id = ?
        """
        await db_manager.execute_query(delete_query, [query_id, current_user.id])
        
        logger.info(f"쿼리 삭제 완료 - ID: {query_id}, 사용자: {current_user.email}")
        
        return {"message": "쿼리가 성공적으로 삭제되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"쿼리 삭제 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"쿼리 삭제 실패: {str(e)}"
        )
