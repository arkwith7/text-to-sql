"""
Query endpoints for Text-to-SQL application.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import asyncio
import logging

from services.auth_dependencies import get_current_user
from services.auth_service import UserResponse
from core.agents.sql_agent import SQLAgent

logger = logging.getLogger(__name__)

router = APIRouter()

class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question")
    database: str = Field(default="northwind", description="Target database")
    context: Optional[str] = Field(None, description="Additional context for the query")
    include_explanation: bool = Field(default=True, description="Include SQL explanation")
    max_rows: Optional[int] = Field(default=100, description="Maximum rows to return")

class QueryResponse(BaseModel):
    question: str
    sql_query: str
    results: List[Dict[str, Any]]
    explanation: Optional[str] = None
    execution_time: float
    row_count: int
    database: str
    success: bool
    error_message: Optional[str] = None

class QueryValidationRequest(BaseModel):
    sql_query: str = Field(..., description="SQL query to validate")
    database: str = Field(default="northwind", description="Target database")

class QueryValidationResponse(BaseModel):
    is_valid: bool
    error_message: Optional[str] = None
    suggestions: Optional[List[str]] = None

@router.post("/", response_model=QueryResponse)
async def execute_query(
    query_request: QueryRequest,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """Execute natural language query and return SQL results."""
    sql_agent: SQLAgent = request.app.state.sql_agent
    
    try:
        # Execute the query using the SQL agent
        result = await sql_agent.execute_query(
            question=query_request.question,
            database=query_request.database,
            context=query_request.context,
            user_id=current_user.id,
            include_explanation=query_request.include_explanation,
            max_rows=query_request.max_rows
        )
        
        return QueryResponse(
            question=query_request.question,
            sql_query=result["sql_query"],
            results=result["results"],
            explanation=result.get("explanation"),
            execution_time=result["execution_time"],
            row_count=len(result["results"]),
            database=query_request.database,
            success=True
        )
        
    except Exception as e:
        logger.error(f"Query execution failed: {str(e)}")
        return QueryResponse(
            question=query_request.question,
            sql_query="",
            results=[],
            execution_time=0.0,
            row_count=0,
            database=query_request.database,
            success=False,
            error_message=str(e)
        )

@router.post("/validate", response_model=QueryValidationResponse)
async def validate_query(
    validation_request: QueryValidationRequest,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """Validate SQL query syntax and structure."""
    sql_agent: SQLAgent = request.app.state.sql_agent
    
    try:
        result = await sql_agent.validate_query(
            sql_query=validation_request.sql_query,
            database=validation_request.database
        )
        
        return QueryValidationResponse(
            is_valid=result["is_valid"],
            error_message=result.get("error_message"),
            suggestions=result.get("suggestions", [])
        )
        
    except Exception as e:
        logger.error(f"Query validation failed: {str(e)}")
        return QueryValidationResponse(
            is_valid=False,
            error_message=str(e)
        )

@router.get("/history")
async def get_query_history(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    """Get user's query history."""
    try:
        # This would typically fetch from a database
        # For now, return a placeholder response
        return {
            "queries": [],
            "total": 0,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch query history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch query history"
        )

@router.delete("/history/{query_id}")
async def delete_query_from_history(
    query_id: int,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a query from user's history."""
    try:
        # This would typically delete from a database
        # For now, return a success response
        return {"message": "Query deleted from history"}
        
    except Exception as e:
        logger.error(f"Failed to delete query from history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete query from history"
        ) 