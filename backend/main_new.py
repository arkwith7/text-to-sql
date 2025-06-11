"""
Main FastAPI application with AI Agent-based architecture.

This is the modernized version of the Text-to-SQL application using:
- LangChain AI Agents
- Azure OpenAI Tool Calling
- Multi-database architecture
- Enhanced security and authentication
- Redis caching
- Analytics and monitoring
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Application imports
from app.config import get_settings, validate_settings
from app.database.connection_manager import DatabaseManager
from app.agents.sql_agent import SQLAgent
from app.auth.service import AuthService, UserCreate, UserLogin, TokenResponse, RefreshTokenRequest
from app.analytics.service import AnalyticsService, EventType
from app.utils.cache import cache
from app.utils.validators import SQLValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
db_manager: Optional[DatabaseManager] = None
sql_agent: Optional[SQLAgent] = None
auth_service: Optional[AuthService] = None
analytics_service: Optional[AnalyticsService] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logger.info("Starting Text-to-SQL AI Agent application...")
    
    try:
        # Validate configuration
        validate_settings()
        
        # Initialize global services
        global db_manager, sql_agent, auth_service, analytics_service
        
        settings = get_settings()
        
        # Initialize database connection manager
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        # Initialize services
        auth_service = AuthService(db_manager)
        analytics_service = AnalyticsService(db_manager)
        
        # Initialize SQL Agent
        sql_agent = SQLAgent(db_manager)
        
        # Test connections
        await db_manager.test_connections()
        
        logger.info("Application startup completed successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")
        raise
    
    # Shutdown
    logger.info("Shutting down application...")
    if db_manager:
        await db_manager.close_all_connections()
    logger.info("Application shutdown completed")

# Create FastAPI app
app = FastAPI(
    title="Smart Business Analytics Assistant",
    description="AI-powered Text-to-SQL application with advanced analytics",
    version="2.0.0",
    lifespan=lifespan
)

# Get settings
settings = get_settings()

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["*"]  # Configure appropriately for production
    )

# Request/Response Models
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

class AnalyticsResponse(BaseModel):
    user_analytics: Dict[str, Any]
    system_metrics: Dict[str, Any]

# Middleware for request tracking
@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Middleware to track API requests and performance."""
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    # Add request ID to headers
    request.state.request_id = request_id
    
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log request
    logger.info(
        f"Request {request_id}: {request.method} {request.url.path} "
        f"completed in {process_time:.3f}s with status {response.status_code}"
    )
    
    # Add performance metric
    if analytics_service:
        await analytics_service.log_performance_metric(
            "api_request_duration",
            process_time * 1000,  # Convert to milliseconds
            "ms",
            {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "request_id": request_id
            }
        )
    
    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Rate limiting decorator
async def check_rate_limit(request: Request):
    """Check rate limits for the current user/IP."""
    if not settings.rate_limit_enabled:
        return
    
    # Get user identifier (IP or user ID)
    identifier = request.client.host
    if hasattr(request.state, "user"):
        identifier = request.state.user.id
    
    # Check rate limit
    rate_limit_result = cache.check_rate_limit(
        identifier,
        settings.rate_limit_requests_per_minute,
        60  # 1 minute window
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

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connections
        if db_manager:
            await db_manager.test_connections()
        
        # Check cache
        cache_stats = cache.get_cache_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "2.0.0",
            "database": "connected",
            "cache": cache_stats,
            "services": {
                "sql_agent": bool(sql_agent),
                "auth_service": bool(auth_service),
                "analytics_service": bool(analytics_service)
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

# Authentication endpoints
@app.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate, request: Request):
    """Register a new user."""
    try:
        await check_rate_limit(request)
        
        if not auth_service:
            raise HTTPException(status_code=500, detail="Authentication service not available")
        
        # Register user
        user = await auth_service.register_user(user_data)
        
        # Authenticate and return tokens
        login_data = UserLogin(email=user_data.email, password=user_data.password)
        token_response = await auth_service.authenticate_user(login_data)
        
        # Log registration event
        if analytics_service:
            await analytics_service.log_event(
                EventType.USER_LOGIN,
                token_response.user.id,
                {"action": "registration", "email": user_data.email},
                request.client.host,
                request.headers.get("user-agent")
            )
        
        return token_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/auth/login", response_model=TokenResponse)
async def login(login_data: UserLogin, request: Request):
    """Authenticate user and return tokens."""
    try:
        await check_rate_limit(request)
        
        if not auth_service:
            raise HTTPException(status_code=500, detail="Authentication service not available")
        
        token_response = await auth_service.authenticate_user(login_data)
        
        # Log login event
        if analytics_service:
            await analytics_service.log_event(
                EventType.USER_LOGIN,
                token_response.user.id,
                {"action": "login", "email": login_data.email},
                request.client.host,
                request.headers.get("user-agent")
            )
        
        return token_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication failed")

@app.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(refresh_request: RefreshTokenRequest, request: Request):
    """Refresh access token."""
    try:
        await check_rate_limit(request)
        
        if not auth_service:
            raise HTTPException(status_code=500, detail="Authentication service not available")
        
        return await auth_service.refresh_access_token(refresh_request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(status_code=500, detail="Token refresh failed")

# Main query endpoint
@app.post("/query", response_model=QueryResponse)
async def execute_query(
    query_request: QueryRequest,
    request: Request,
    current_user=Depends(lambda: auth_service.get_current_user() if auth_service else None)
):
    """Execute a natural language query using the SQL Agent."""
    try:
        await check_rate_limit(request)
        
        if not sql_agent:
            raise HTTPException(status_code=500, detail="SQL Agent not available")
        
        user_id = current_user.id if current_user else "anonymous"
        query_id = str(uuid.uuid4())
        
        start_time = time.time()
        
        # Process the question using SQL Agent
        result = await sql_agent.process_question(
            question=query_request.question,
            context=query_request.context,
            user_id=user_id
        )
        
        execution_time = time.time() - start_time
        
        # Log query execution
        if analytics_service:
            await analytics_service.log_query_execution(
                query_id=query_id,
                user_id=user_id,
                question=query_request.question,
                sql_query=result["sql_query"],
                execution_time=execution_time,
                row_count=len(result["data"]),
                success=True,
                chart_type=result.get("chart_suggestion")
            )
        
        return QueryResponse(
            query_id=query_id,
            sql_query=result["sql_query"],
            data=result["data"],
            columns=result["columns"],
            chart_suggestion=result.get("chart_suggestion"),
            insights=result.get("insights"),
            explanation=result.get("explanation"),
            confidence=result.get("confidence", "medium"),
            execution_time=execution_time,
            row_count=len(result["data"])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query execution error: {str(e)}")
        
        # Log failed query
        if analytics_service:
            await analytics_service.log_query_execution(
                query_id=str(uuid.uuid4()),
                user_id=current_user.id if current_user else "anonymous",
                question=query_request.question,
                sql_query="",
                execution_time=time.time() - start_time,
                row_count=0,
                success=False,
                error_message=str(e)
            )
        
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")

# Schema information endpoint
@app.get("/schema", response_model=SchemaResponse)
async def get_schema(
    current_user=Depends(lambda: auth_service.get_current_user() if auth_service else None)
):
    """Get database schema information."""
    try:
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not available")
        
        # Check cache first
        cached_schema = cache.get_cached_schema_info("northwind")
        if cached_schema:
            return SchemaResponse(
                tables=cached_schema,
                database_info={"source": "cache", "database": "northwind"}
            )
        
        # Get fresh schema info
        schema_info = db_manager.get_schema_info()
        
        # Cache the result
        cache.cache_schema_info("northwind", schema_info)
        
        return SchemaResponse(
            tables=schema_info,
            database_info={"source": "database", "database": "northwind"}
        )
        
    except Exception as e:
        logger.error(f"Schema retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve schema information")

# Analytics endpoint
@app.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    current_user=Depends(lambda: auth_service.get_current_user() if auth_service else None)
):
    """Get user and system analytics."""
    try:
        if not analytics_service:
            raise HTTPException(status_code=500, detail="Analytics service not available")
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Get user analytics
        user_analytics = await analytics_service.get_user_analytics(current_user.id)
        
        # Get system metrics (only for admin users)
        system_metrics = {}
        if current_user.role in ["admin", "analyst"]:
            system_metrics = await analytics_service.get_system_metrics()
        
        return AnalyticsResponse(
            user_analytics=user_analytics.dict(),
            system_metrics=system_metrics.dict() if hasattr(system_metrics, 'dict') else system_metrics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")

# Popular queries endpoint
@app.get("/queries/popular")
async def get_popular_queries(
    limit: int = 10,
    current_user=Depends(lambda: auth_service.get_current_user() if auth_service else None)
):
    """Get most popular queries."""
    try:
        if not analytics_service:
            raise HTTPException(status_code=500, detail="Analytics service not available")
        
        popular_queries = await analytics_service.get_popular_queries(limit)
        
        return {
            "popular_queries": popular_queries,
            "limit": limit,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Popular queries error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve popular queries")

# Suggest follow-up questions endpoint
@app.post("/queries/suggestions")
async def get_query_suggestions(
    query_data: Dict[str, Any],
    current_user=Depends(lambda: auth_service.get_current_user() if auth_service else None)
):
    """Get follow-up question suggestions based on query results."""
    try:
        if not sql_agent:
            raise HTTPException(status_code=500, detail="SQL Agent not available")
        
        sql_query = query_data.get("sql_query", "")
        results = query_data.get("results", [])
        
        suggestions = await sql_agent.suggest_follow_up_questions(sql_query, results)
        
        return {
            "suggestions": suggestions,
            "count": len(suggestions)
        }
        
    except Exception as e:
        logger.error(f"Query suggestions error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate suggestions")

# Cache management endpoints (admin only)
@app.delete("/admin/cache")
async def clear_cache(
    pattern: Optional[str] = None,
    current_user=Depends(lambda: auth_service.get_current_user() if auth_service else None)
):
    """Clear cache entries (admin only)."""
    try:
        if not current_user or current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        if pattern:
            cleared_count = cache.invalidate_pattern(pattern)
        else:
            # Clear all cache - implement if needed
            cleared_count = 0
        
        return {
            "message": "Cache cleared",
            "pattern": pattern,
            "cleared_count": cleared_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache clear error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

@app.get("/admin/cache/stats")
async def get_cache_stats(
    current_user=Depends(lambda: auth_service.get_current_user() if auth_service else None)
):
    """Get cache statistics (admin only)."""
    try:
        if not current_user or current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        stats = cache.get_cache_stats()
        
        return {
            "cache_stats": stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache stats")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper logging."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.method} {request.url}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)} - {request.method} {request.url}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main_new:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
