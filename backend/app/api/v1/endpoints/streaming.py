"""
Server Sent Events (SSE) implementation for real-time chat streaming.
"""
import asyncio
import json
import uuid
from typing import AsyncGenerator, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
from starlette.responses import Response
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.chat.service import ChatSessionService
from app.agents.sql_agent import SQLAgent
from app.analytics.service import AnalyticsService, EventType

router = APIRouter()

class StreamQueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    context: Optional[str] = None

class StreamEvent(BaseModel):
    event: str
    data: Dict[str, Any]
    timestamp: datetime = datetime.utcnow()

async def format_sse_message(event: str, data: Dict[str, Any]) -> str:
    """Format a message for Server-Sent Events."""
    event_data = StreamEvent(event=event, data=data)
    return f"data: {json.dumps(event_data.dict(), default=str)}\n\n"

async def stream_query_execution(
    question: str,
    session_id: Optional[str],
    user_id: str,
    chat_service: ChatSessionService,
    sql_agent: SQLAgent,
    analytics_service: AnalyticsService
) -> AsyncGenerator[str, None]:
    """Stream the query execution process with real-time updates."""
    
    try:
        # Send initial event
        yield await format_sse_message("query_started", {
            "message": "처리를 시작합니다...",
            "question": question,
            "session_id": session_id
        })
        
        # Create session if needed
        if not session_id:
            yield await format_sse_message("session_creating", {
                "message": "새로운 대화를 시작합니다..."
            })
            
            session = await chat_service.create_session(
                user_id=user_id,
                title=f"Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            session_id = session["session_id"]
            
            yield await format_sse_message("session_created", {
                "message": "대화가 시작되었습니다.",
                "session_id": session_id
            })
        
        # Analyze question
        yield await format_sse_message("analyzing", {
            "message": "질문을 분석하고 있습니다..."
        })
        
        await asyncio.sleep(0.5)  # Small delay for UX
        
        # Generate SQL
        yield await format_sse_message("generating_sql", {
            "message": "SQL 쿼리를 생성하고 있습니다..."
        })
        
        # Execute query using SQL agent
        agent_result = await sql_agent.aexecute({
            "question": question,
            "input": question,
            "user_id": user_id,
            "session_id": session_id or f"stream_{datetime.now().timestamp()}",
            "chat_history": []
        })
        
        if not agent_result.get("success"):
            yield await format_sse_message("error", {
                "message": "쿼리 실행에 실패했습니다.",
                "error": agent_result.get("error", "Query execution failed")
            })
            return
        
        # Extract SQL query and results from agent output
        result_data = agent_result.get("result", {})
        intermediate_steps = result_data.get("intermediate_steps", [])
        
        # Find the SQL execution step to get the query and results
        sql_query = "Not executed"
        query_data = []
        query_columns = []
        query_row_count = 0
        execution_time = 0
        
        sql_execution_step = next(
            (step for step in reversed(intermediate_steps) 
             if hasattr(step[0], 'tool') and step[0].tool == 'sql_execution'), 
            None
        )
        
        if sql_execution_step:
            sql_query = sql_execution_step[0].tool_input.get('query', 'SQL not found')
            # The tool output contains formatted results, we need to re-execute for structured data
            from app.database.connection_manager import db_manager
            db_result = await db_manager.execute_query_safe(sql_query, 'northwind')
            if db_result.get("success"):
                query_data = db_result.get("data", [])
                query_columns = db_result.get("columns", [])
                query_row_count = db_result.get("row_count", 0)
        
        # Prepare the query result in the expected format
        query_result = {
            "sql_query": sql_query,
            "data": query_data,
            "columns": query_columns,
            "row_count": query_row_count,
            "execution_time": execution_time,
            "explanation": result_data.get("output", ""),
            "confidence": "high"
        }
        
        # Send SQL generated event
        yield await format_sse_message("sql_generated", {
            "message": "SQL 쿼리가 생성되었습니다.",
            "sql_query": query_result.get("sql_query", "")
        })
        
        # Execute query
        yield await format_sse_message("executing_query", {
            "message": "데이터베이스에서 쿼리를 실행하고 있습니다..."
        })
        
        await asyncio.sleep(0.3)  # Small delay for UX
        
        # Process results
        yield await format_sse_message("processing_results", {
            "message": "결과를 처리하고 있습니다..."
        })
        
        # Generate insights if available
        insights = None
        if query_result.get("data") and len(query_result["data"]) > 0:
            yield await format_sse_message("generating_insights", {
                "message": "인사이트를 생성하고 있습니다..."
            })
            await asyncio.sleep(0.5)
            # Here you could call an AI service to generate insights
            insights = "데이터 분석 결과를 확인해보세요."
        
        # Save to chat session
        ai_response = f"질문: \"{question}\"\n\n결과를 확인해주세요."
        
        message = await chat_service.add_message(
            session_id=session_id,
            user_message=question,
            ai_response=ai_response,
            query_result=query_result
        )
        
        # Send final success event
        yield await format_sse_message("query_completed", {
            "message": "쿼리가 성공적으로 완료되었습니다!",
            "query_result": query_result,
            "insights": insights,
            "message_id": message["message_id"],
            "session_id": session_id,
            "execution_time": query_result.get("execution_time", 0)
        })
        
        # Log analytics
        await analytics_service.log_event(
            user_id=user_id,
            event_type=EventType.QUERY_EXECUTED,
            metadata={
                "session_id": session_id,
                "question": question,
                "execution_time": query_result.get("execution_time", 0),
                "row_count": query_result.get("row_count", 0),
                "streaming": True
            }
        )
        
    except Exception as e:
        yield await format_sse_message("error", {
            "message": f"오류가 발생했습니다: {str(e)}",
            "error": str(e)
        })

@router.post("/stream-query", tags=["Chat", "Streaming"])
async def stream_query(
    request_data: StreamQueryRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Execute a query with real-time streaming updates via Server-Sent Events.
    
    This endpoint provides real-time feedback during query execution:
    - Query analysis
    - SQL generation
    - Query execution
    - Results processing
    - Insights generation
    """
    chat_service: ChatSessionService = request.app.state.chat_service
    sql_agent: SQLAgent = request.app.state.sql_agent
    analytics_service: AnalyticsService = request.app.state.analytics_service
    
    # Validate session if provided
    if request_data.session_id:
        try:
            user_sessions = await chat_service.get_user_sessions(user_id=current_user["id"])
            session_ids = [s["session_id"] for s in user_sessions["sessions"]]
            
            if request_data.session_id not in session_ids:
                raise HTTPException(
                    status_code=404,
                    detail="Chat session not found or access denied"
                )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to validate session: {str(e)}"
            )
    
    return StreamingResponse(
        stream_query_execution(
            question=request_data.question,
            session_id=request_data.session_id,
            user_id=current_user["id"],
            chat_service=chat_service,
            sql_agent=sql_agent,
            analytics_service=analytics_service
        ),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@router.get("/stream-session/{session_id}", tags=["Chat", "Streaming"])
async def stream_session_updates(
    session_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Stream real-time updates for a specific chat session.
    This can be used for collaborative features or session monitoring.
    """
    chat_service: ChatSessionService = request.app.state.chat_service
    
    # Verify session access
    try:
        user_sessions = await chat_service.get_user_sessions(user_id=current_user["id"])
        session_ids = [s["session_id"] for s in user_sessions["sessions"]]
        
        if session_id not in session_ids:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found or access denied"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate session: {str(e)}"
        )
    
    async def generate_session_updates():
        """Generate session update events."""
        # Send initial connection event
        yield await format_sse_message("connected", {
            "message": "세션에 연결되었습니다.",
            "session_id": session_id,
            "timestamp": datetime.utcnow()
        })
        
        # Keep connection alive with periodic heartbeat
        try:
            while True:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                yield await format_sse_message("heartbeat", {
                    "timestamp": datetime.utcnow(),
                    "session_id": session_id
                })
        except asyncio.CancelledError:
            yield await format_sse_message("disconnected", {
                "message": "연결이 종료되었습니다.",
                "session_id": session_id
            })
    
    return StreamingResponse(
        generate_session_updates(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )
