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
from services.analytics_service import AnalyticsService
from services.chat_service import ChatSessionService
from utils.cache import cache
from api.v1.api import api_router
# main.py 상단에 추가할 import
from utils.logging_config import setup_logging, RequestLogger
import sys

# Configure logging
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# 새로운 로깅 설정:
# 로깅 시스템 초기화 (앱 시작 전에)
setup_logging()
logger = logging.getLogger(__name__)

# lifespan 함수에서 로깅 관련 정보 추가:
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

# 기존 track_requests 미들웨어를 다음으로 교체:
@app.middleware("http")
async def enhanced_request_tracking(request: Request, call_next):
    """향상된 API 요청 추적 및 로깅 미들웨어"""
    start_time = time.time()
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # 사용자 정보 추출 (가능한 경우)
    user_id = None
    try:
        if hasattr(request.app.state, 'auth_service'):
            user = await request.app.state.auth_service.get_current_user(request, required=False)
            user_id = user.get('id') if user else None
    except:
        pass  # 인증 실패 시 무시
    
    # 요청 본문 추출 (POST/PUT 요청인 경우)
    request_body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            # 요청 본문을 읽고 다시 설정 (한 번만 읽을 수 있으므로)
            body = await request.body()
            if body:
                try:
                    request_body = json.loads(body.decode('utf-8'))
                except json.JSONDecodeError:
                    request_body = {"raw_body": body.decode('utf-8', errors='ignore')[:500]}
        except Exception as e:
            logger.debug(f"요청 본문 읽기 실패: {str(e)}")
    
    # 요청 로깅
    RequestLogger.log_request(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        user_id=user_id,
        body=request_body,
        query_params=dict(request.query_params) if request.query_params else None
    )
    
    # 요청 처리
    response = None
    error_message = None
    try:
        response = await call_next(request)
    except Exception as e:
        error_message = str(e)
        logger.error(
            f"요청 처리 중 오류 발생: {error_message}",
            extra={
                'request_id': request_id,
                'user_id': user_id,
                'error_details': error_message
            }
        )
        # 오류 응답 생성
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id}
        )
    
    # 처리 시간 계산
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request_id
    
    # 응답 크기 계산 (가능한 경우)
    response_size = None
    if hasattr(response, 'body'):
        try:
            response_size = len(response.body)
        except:
            pass
    
    # 응답 로깅
    RequestLogger.log_response(
        request_id=request_id,
        status_code=response.status_code,
        response_time=process_time,
        user_id=user_id,
        response_size=response_size,
        error_message=error_message
    )
    
    # 성능 메트릭 로깅 (기존 analytics_service 사용)
    try:
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
                    "request_id": request_id,
                    "user_id": user_id
                }
            )
    except Exception as e:
        logger.warning(f"성능 메트릭 로깅 실패: {str(e)}")
    
    return response


# health check 엔드포인트도 로깅 추가:
@app.get("/health", tags=["System"])
async def health_check(request: Request):
    """Health check endpoint with enhanced logging."""
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.info(f"헬스 체크 요청 - Request ID: {request_id}")
    
    try:
        # 캐시 상태 확인
        cache_stats = {"status": "unknown"}
        try:
            if hasattr(request.app.state, 'cache'):
                cache = request.app.state.cache
                cache_stats = {
                    "status": "connected",
                    "info": cache.info() if hasattr(cache, 'info') else "available"
                }
        except Exception as cache_error:
            logger.warning(f"캐시 상태 확인 실패: {str(cache_error)}")
            cache_stats = {"status": "disconnected", "error": str(cache_error)}
        
        # 데이터베이스 상태 확인
        db_status = "unknown"
        try:
            if hasattr(request.app.state, 'db_manager'):
                db_manager = request.app.state.db_manager
                # 간단한 연결 테스트
                await db_manager.test_connections()
                db_status = "connected"
        except Exception as db_error:
            logger.warning(f"데이터베이스 상태 확인 실패: {str(db_error)}")
            db_status = f"error: {str(db_error)}"
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "2.0.0",
            "database": db_status,
            "cache": cache_stats,
            "services": {
                "sql_agent": hasattr(request.app.state, 'sql_agent'),
                "auth_service": hasattr(request.app.state, 'auth_service'),
                "analytics_service": hasattr(request.app.state, 'analytics_service'),
                "chat_service": hasattr(request.app.state, 'chat_service')
            },
            "request_id": request_id
        }
        
        logger.info(f"헬스 체크 성공 - Request ID: {request_id}")
        return health_status
        
    except Exception as e:
        logger.error(
            f"헬스 체크 실패 - Request ID: {request_id}",
            extra={'error_details': str(e)},
            exc_info=True
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": request_id
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

