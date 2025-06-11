"""
API routes for AI-powered query execution and schema management.
"""
import time
import uuid
import json
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.analytics.service import AnalyticsService, EventType
from app.utils.validators import SQLValidator
from app.agents.sql_agent import SQLAgent
from app.database.connection_manager import DatabaseManager
from app.auth.service import AuthService
from app.utils.cache import cache

class QueryRequest(BaseModel):
    question: str
    context: Optional[str] = None

class QueryResponse(BaseModel):
    query_id: str
    sql_query: str
    data: List[Dict[str, Any]]
    columns: List[str]
    chart_suggestion: Optional[str] = None
    insights: Optional[str] = None
    explanation: Optional[str] = None
    confidence: str
    execution_time: float
    row_count: int

class SchemaResponse(BaseModel):
    tables: List[Dict[str, Any]]
    database_info: Dict[str, Any]

router = APIRouter()

async def get_current_user_optional(request: Request):
    auth_service: AuthService = request.app.state.auth_service
    # Assuming get_current_user can handle being called without credentials
    return await auth_service.get_current_user(request, required=False)

async def check_rate_limit(request: Request):
    """Check rate limits for the current user/IP."""
    settings = request.app.state.settings
    if not settings.rate_limit_enabled:
        return
    
    identifier = request.client.host
    # request.state.user might be set by the dependency
    user = getattr(request.state, "user", None)
    if user:
        identifier = user.id
    
    rate_limit_result = cache.check_rate_limit(
        f"ratelimit_{identifier}",
        settings.rate_limit_requests_per_minute,
        60
    )
    
    if not rate_limit_result["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={
                "X-RateLimit-Limit": str(rate_limit_result["limit"]),
                "X-RateLimit-Remaining": str(max(0, rate_limit_result["limit"] - rate_limit_result["count"])),
                "X-RateLimit-Reset": str(int(rate_limit_result["reset_at"].timestamp()))
            }
        )

@router.post("/query", response_model=QueryResponse, dependencies=[Depends(check_rate_limit)], tags=["AI Query"])
async def execute_query(
    query_request: QueryRequest,
    request: Request,
    current_user=Depends(get_current_user_optional)
):
    """
    Process a natural language query, convert it to SQL, execute it,
    and return the results with analytics.
    """
    start_time = time.time()
    query_id = str(uuid.uuid4())
    user_id = current_user.id if current_user else None
    
    sql_agent: SQLAgent = request.app.state.sql_agent
    analytics_service: AnalyticsService = request.app.state.analytics_service
    db_manager: DatabaseManager = request.app.state.db_manager
    
    if not all([sql_agent, analytics_service, db_manager]):
        raise HTTPException(status_code=503, detail="A required service is not available.")

    # Log query event
    await analytics_service.log_event(
        EventType.QUERY_SUBMITTED,
        user_id=user_id,
        details={"question": query_request.question},
        request=request
    )

    # Prepare agent input
    agent_input = {
        "question": query_request.question,
        "context": query_request.context,
        "user_id": user_id,
        "session_id": getattr(request.state, 'request_id', str(uuid.uuid4())),
        "chat_history": []
    }
    
    agent_result = await sql_agent.aexecute(agent_input)

    if not agent_result.get("success"):
        error_msg = agent_result.get("error", "Unknown agent error")
        raise HTTPException(status_code=400, detail=f"AI Agent failed: {error_msg}")
    
    result_data = agent_result.get("result", {})
    final_output = result_data.get("output", "")
    intermediate_steps = result_data.get("intermediate_steps", [])
    
    sql_query, data, columns, row_count = "Not executed", [], [], 0

    sql_execution_step = next((step for step in reversed(intermediate_steps) if hasattr(step[0], 'tool') and step[0].tool == 'sql_execution'), None)
    
    if sql_execution_step:
        sql_query = sql_execution_step[0].tool_input.get('query', 'SQL not found')
        # Re-execute query to ensure we have fresh, structured data
        db_result = await db_manager.execute_query_safe(sql_query, 'northwind')
        if db_result.get("success"):
            data = db_result.get("data", [])
            columns = db_result.get("columns", [])
            row_count = db_result.get("row_count", 0)
        else:
            final_output = f"Error during query re-execution: {db_result.get('error')}"

    execution_time = time.time() - start_time
    
    response_data = QueryResponse(
        query_id=query_id,
        sql_query=sql_query,
        data=data,
        columns=columns,
        row_count=row_count,
        chart_suggestion="bar_chart",
        insights="This is a sample insight.",
        explanation=final_output,
        confidence="high",
        execution_time=execution_time
    )

    await analytics_service.log_event(
        EventType.QUERY_COMPLETED,
        user_id=user_id,
        details={"query_id": query_id, "sql_query": sql_query, "row_count": row_count, "execution_time_ms": execution_time * 1000},
        request=request
    )

    return response_data

@router.get("/schema", response_model=SchemaResponse, tags=["Schema"])
async def get_schema(request: Request, current_user=Depends(get_current_user_optional)):
    """Get database schema information for the business database."""
    sql_agent: SQLAgent = request.app.state.sql_agent
    schema_analyzer = next((tool for tool in sql_agent.tools if tool.name == "schema_analyzer"), None)
    if not schema_analyzer:
        raise HTTPException(status_code=503, detail="Schema analyzer tool not found in agent")
    
    try:
        schema_json_str = schema_analyzer._run() 
        schema_data = json.loads(schema_json_str)
        
        return SchemaResponse(
            tables=schema_data.get("tables", []),
            database_info={"type": schema_data.get("database_type"), "total_tables": schema_data.get("total_tables")}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get schema: {str(e)}")

@router.get("/queries/popular", tags=["Query"])
async def get_popular_queries(request: Request, limit: int = 10, current_user=Depends(get_current_user_optional)):
    """Get most popular queries."""
    analytics_service: AnalyticsService = request.app.state.analytics_service
    return await analytics_service.get_popular_queries(limit)

@router.post("/queries/suggestions", tags=["Query"])
async def get_query_suggestions(query_data: Dict[str, Any], request: Request, current_user=Depends(get_current_user_optional)):
    """Get AI-powered query suggestions based on context. (Placeholder)"""
    return {
        "suggestions": ["What are the top 5 best-selling products?", "Show me the total sales per country.", "Who are the most valuable customers?"],
        "message": "Feature under development."
    } 