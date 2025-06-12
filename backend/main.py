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
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import uvicorn

# Application imports
# Ensure models are registered with Base before other components use it
from app.database import models
from app.config import get_settings, validate_settings
from app.database.connection_manager import DatabaseManager
from app.agents.sql_agent import SQLAgent
from app.auth.service import AuthService
from app.auth.security import get_openapi_security_schemes
from app.analytics.service import AnalyticsService
from app.utils.cache import cache
from app.api.v1.api import api_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    logger.info("Starting Text-to-SQL AI Agent application...")
    
    try:
        validate_settings()
        
        settings = get_settings()
        app.state.settings = settings
        
        db_manager = DatabaseManager()
        await db_manager.initialize()
        app.state.db_manager = db_manager
        
        app.state.auth_service = AuthService(db_manager)
        
        analytics_service = AnalyticsService(db_manager)
        app.state.analytics_service = analytics_service

        app.state.sql_agent = SQLAgent(db_manager)
        app.state.cache = cache
        
        await db_manager.test_connections()
        
        logger.info("Application startup completed successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")
        raise
    
    logger.info("Shutting down application...")
    db_manager = app.state.db_manager if hasattr(app.state, 'db_manager') else None
    if db_manager:
        await db_manager.close_all_connections()
    logger.info("Application shutdown completed")

# Create FastAPI app
app = FastAPI(
    title="Smart Business Analytics Assistant",
    description="AI-powered Text-to-SQL application with advanced analytics",
    version="2.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User authentication and authorization"
        },
        {
            "name": "AI Query",
            "description": "Natural language to SQL query processing"
        },
        {
            "name": "Schema",
            "description": "Database schema information"
        },
        {
            "name": "Analytics",
            "description": "Usage analytics and system metrics"
        },
        {
            "name": "Admin",
            "description": "Administrative functions (requires admin role)"
        },
        {
            "name": "System",
            "description": "System health and status endpoints"
        }
    ]
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
if get_settings().environment == "production":
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["*"]
    )

app.include_router(api_router, prefix="/api/v1")


def custom_openapi():
    """Custom OpenAPI schema with JWT authentication."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = get_openapi_security_schemes()
    
    # Add security to all protected endpoints
    for path, path_data in openapi_schema["paths"].items():
        for method, operation in path_data.items():
            if isinstance(operation, dict) and "tags" in operation:
                # Skip authentication endpoints and system endpoints
                if any(tag in ["Authentication", "System"] for tag in operation["tags"]):
                    continue
                # Add security requirement for protected endpoints if not present
                if "security" not in operation:
                    operation["security"] = [{"JWTBearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Middleware to track API requests and performance."""
    start_time = time.time()
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    logger.info(
        f"Request {request_id}: {request.method} {request.url.path} "
        f"completed in {process_time:.3f}s with status {response.status_code}"
    )
    
    analytics_service = request.app.state.analytics_service if hasattr(request.app.state, 'analytics_service') else None
    if analytics_service:
        await analytics_service.log_performance_metric(
            "api_request_duration",
            process_time * 1000,
            "ms",
            {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "request_id": request_id
            }
        )
    
    return response

@app.get("/health", tags=["System"])
async def health_check(request: Request):
    """Health check endpoint."""
    try:
        db_manager = request.app.state.db_manager
        await db_manager.test_connections()
        
        cache_stats = request.app.state.cache.get_cache_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "2.0.0",
            "database": "connected",
            "cache": cache_stats,
            "services": {
                "sql_agent": hasattr(request.app.state, 'sql_agent'),
                "auth_service": hasattr(request.app.state, 'auth_service'),
                "analytics_service": hasattr(request.app.state, 'analytics_service')
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

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    request_id = request.state.request_id if hasattr(request.state, 'request_id') else "N/A"
    logger.error(
        f"Unhandled exception for request {request_id}",
        exc_info=exc,
        extra={"request_path": request.url.path}
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred."},
    )

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug,
        log_level="info"
    )

