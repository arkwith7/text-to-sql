"""
Main FastAPI application with AI Agent-based architecture.

This is the modernized version of the Text-to-SQL application using:
- Enhanced Core Module with Jupyter Notebook proven patterns
- LangChain AI Agents with latest APIs
- Azure OpenAI Tool Calling
- Multi-database architecture
- Enhanced security and authentication
- Redis caching
- Analytics and monitoring
"""

import asyncio
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
from models import models
from core.config import get_settings, validate_settings
from database.connection_manager import DatabaseManager

# Enhanced Core Module imports (개선된 core 모듈)
from core import SQLAgent, LangChainTextToSQLAgent

from services.auth_service import AuthService
from services.auth_security import get_openapi_security_schemes
from services.analytics_service import AnalyticsService, EventType
from services.chat_service import ChatSessionService
from utils.cache import cache
from api.v1.api import api_router
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    logger.info("🚀 Text-to-SQL AI Agent 애플리케이션을 시작합니다... (Enhanced Core v2.0)")
    
    try:
        validate_settings()
        logger.info("✅ 설정 검증 완료")
        
        settings = get_settings()
        app.state.settings = settings
        
        db_manager = DatabaseManager()
        await db_manager.initialize()
        app.state.db_manager = db_manager
        logger.info("✅ 데이터베이스 매니저 초기화 완료")
        
        app.state.auth_service = AuthService(db_manager)
        logger.info("✅ 인증 서비스 초기화 완료")
        
        analytics_service = AnalyticsService(db_manager)
        app.state.analytics_service = analytics_service
        logger.info("✅ 분석 서비스 초기화 완료")

        app.state.chat_service = ChatSessionService(db_manager)
        logger.info("✅ 채팅 서비스 초기화 완료")

        # Enhanced SQL Agent 초기화 (개선된 버전)
        try:
            enhanced_sql_agent = SQLAgent(db_manager)
            app.state.sql_agent = enhanced_sql_agent
            logger.info("✅ Enhanced SQL Agent 초기화 완료 (PostgreSQL Northwind 최적화)")
            
            # 동기 실행 테스트
            test_result = enhanced_sql_agent.execute_query_sync("고객 수를 알려주세요")
            if test_result.get("success"):
                logger.info(f"🧪 Enhanced SQL Agent 테스트 성공 - 결과: {len(test_result.get('results', []))}행")
            else:
                logger.warning(f"⚠️ Enhanced SQL Agent 테스트 실패: {test_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"❌ Enhanced SQL Agent 초기화 실패: {str(e)}")
            # Fallback to basic functionality
            logger.info("🔄 기본 SQL Agent로 대체")
            app.state.sql_agent = None

        # LangChain Agent 초기화 (선택적)
        try:
            langchain_agent = LangChainTextToSQLAgent(
                db_manager=db_manager,
                enable_simulation=True,
                verbose=False  # Production에서는 False
            )
            app.state.langchain_agent = langchain_agent
            logger.info("✅ LangChain Text-to-SQL Agent 초기화 완료 (Latest APIs)")
            
            # Agent 테스트
            test_info = langchain_agent.get_agent_info()
            logger.info(f"🤖 Agent 정보: {test_info['agent_type']}, 모델: {test_info['model']}, 도구: {test_info['tools_count']}개")
            
        except Exception as e:
            logger.warning(f"⚠️ LangChain Agent 초기화 실패 (선택적 기능): {str(e)}")
            app.state.langchain_agent = None

        app.state.cache = cache
        logger.info("✅ 캐시 시스템 초기화 완료")
        
        await db_manager.test_connections()
        logger.info("✅ 데이터베이스 연결 테스트 완료")
        
        # 시스템 상태 로깅
        logger.info("📊 시스템 상태:")
        logger.info(f"  - Enhanced SQL Agent: {'✅ 활성' if app.state.sql_agent else '❌ 비활성'}")
        logger.info(f"  - LangChain Agent: {'✅ 활성' if hasattr(app.state, 'langchain_agent') and app.state.langchain_agent else '❌ 비활성'}")
        logger.info(f"  - 데이터베이스: ✅ 연결됨")
        logger.info(f"  - 캐시: ✅ 활성")
        
        logger.info("🎉 애플리케이션 시작 성공! (Enhanced Core Module 적용)")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ 애플리케이션 시작 실패: {str(e)}", exc_info=True)
        raise
    
    logger.info("🔄 애플리케이션을 종료합니다...")
    db_manager = app.state.db_manager if hasattr(app.state, 'db_manager') else None
    if db_manager:
        await db_manager.close_all_connections()
        logger.info("✅ 데이터베이스 연결 종료 완료")
    logger.info("👋 애플리케이션 종료 완료")

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
            "name": "Chat",
            "description": "Chat session management and conversation history"
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
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
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

# 기존 track_requests 미들웨어를 다음으로 교체:
@app.middleware("http")
async def simple_request_tracking(request: Request, call_next):
    """Simplified request tracking middleware - performance optimized."""
    start_time = time.time()
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # OPTIONS 요청은 로깅 없이 바로 처리
    if request.method == "OPTIONS":
        response = await call_next(request)
        return response
    
    # 요청 처리
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id}
        )
    
    # 처리 시간 계산 및 헤더 추가
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request_id
    
    # 느린 요청만 로깅 (1초 이상)
    if process_time > 1.0:
        logger.warning(f"Slow request: {request.method} {request.url.path} - {process_time:.3f}s")
    
    return response


@app.get("/health", tags=["System"])
async def health_check():
    """Simple health check endpoint - optimized for performance."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0"
    }

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

