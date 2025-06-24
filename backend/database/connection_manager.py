"""
Database connection management for multi-database architecture
Handles both application database (SQLite) and business data sources (PostgreSQL)
"""
from sqlalchemy import text, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, Generator, List, AsyncGenerator
import structlog
import time
from datetime import datetime
from functools import lru_cache
from core.config import get_settings
from .base import Base
# ConnectionService is now imported locally to prevent circular imports

logger = structlog.get_logger(__name__)

# SQLAlchemy base for ORM models is now in database/base.py

class DatabaseManager:
    """Enhanced Database Manager with performance monitoring and caching capabilities"""

    def __init__(self):
        self.engines: Dict[str, Any] = {}
        self.session_makers: Dict[str, Any] = {}
        
        # Performance monitoring (노트북의 EnhancedDatabaseManager 기능 추가)
        self.performance_stats = {
            'total_queries': 0,
            'total_time': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0,
            'successful_connections': 0,
            'failed_connections': 0
        }
        
        # Query logging for performance analysis
        self.query_log = []
        self.schema_cache = {}
        
        # LRU cache for query results (up to 100 entries)
        self.query_cache = {}
        self._max_cache_size = 100
        
        # Initialization is now deferred to an async method
    
    async def initialize(self):
        """Initialize database connections asynchronously."""
        self._initialize_connections()
        # Create all tables for the application database
        await self.create_app_db_tables()
        logger.info("Database manager initialized and app tables created.")

    def _initialize_connections(self):
        """Initialize database connections with proper configuration"""
        settings = get_settings()
        
        # Application database (SQLite)
        if settings.app_database_url:
            is_sqlite = settings.app_database_url.startswith("sqlite")
            
            engine_args = {
                "echo": settings.debug
            }

            app_db_url = settings.app_database_url
            if is_sqlite and not app_db_url.startswith("sqlite+aiosqlite"):
                 app_db_url = app_db_url.replace("sqlite://", "sqlite+aiosqlite://")
            
            logger.info(f"Using app database URL: {app_db_url}")

            self.engines['app'] = create_async_engine(
                app_db_url,
                **engine_args
            )
            self.session_makers['app'] = sessionmaker(
                bind=self.engines['app'], 
                class_=AsyncSession, 
                expire_on_commit=False
            )
            logger.info("Application database connection initialized", type="sqlite" if is_sqlite else "other")

        # Northwind business database (PostgreSQL)
        if settings.northwind_database_url:
            northwind_db_url = settings.northwind_database_url
            if "postgresql" in northwind_db_url and not northwind_db_url.startswith("postgresql+asyncpg"):
                northwind_db_url = northwind_db_url.replace("postgresql://", "postgresql+asyncpg://")
            
            logger.info(f"Using northwind database URL: {northwind_db_url}")

            self.engines['northwind'] = create_async_engine(
                northwind_db_url,
                pool_size=settings.connection_pool_size,
                max_overflow=10,
                pool_pre_ping=True,
                echo=settings.debug
            )
            self.session_makers['northwind'] = sessionmaker(
                bind=self.engines['northwind'], 
                class_=AsyncSession,
                expire_on_commit=False
            )
            logger.info("Northwind database connection initialized", type="postgresql")

    async def create_app_db_tables(self):
        """Creates all tables in the application database based on the Base metadata."""
        if 'app' in self.engines:
            engine = self.get_engine('app')
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Tables created for the 'app' database.")
    
    def get_engine(self, db_name: str):
        """Get database engine by name"""
        if db_name not in self.engines:
            raise ValueError(f"Database '{db_name}' not configured")
        return self.engines[db_name]
    
    @asynccontextmanager
    async def get_session(self, db_name: str) -> Generator:
        """Get database session with automatic cleanup"""
        if db_name not in self.session_makers:
            raise ValueError(f"Database '{db_name}' not configured")
        
        session = self.session_makers[db_name]()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error in {db_name}", error=str(e))
            raise
        finally:
            await session.close()
    
    @asynccontextmanager
    async def get_connection(self, db_name: str) -> Generator:
        """Get raw database connection for direct SQL execution"""
        engine = self.get_engine(db_name)
        async with engine.connect() as conn:
            try:
                yield conn
            except Exception as e:
                logger.error(f"Connection error in {db_name}", error=str(e))
                raise
    
    async def execute_query(self, db_name: str, query: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute SQL query safely with error handling and performance monitoring"""
        start_time = time.time()
        query_id = f"query_{len(self.query_log) + 1}"
        
        try:
            async with self.get_connection(db_name) as conn:
                result = await conn.execute(text(query), params or {})
                execution_time = time.time() - start_time
                
                if result.returns_rows:
                    columns = list(result.keys())
                    data = [dict(row._mapping) for row in result.all()]
                    
                    # 성능 로깅
                    self._log_query_performance(query, execution_time, True)
                    
                    return {
                        'success': True,
                        'data': data,
                        'columns': columns,
                        'row_count': len(data),
                        'execution_time': round(execution_time, 3),
                        'query_id': query_id,
                        'database': db_name
                    }
                else:
                    await conn.commit()
                    
                    # 성능 로깅
                    self._log_query_performance(query, execution_time, True)
                    
                    return {
                        'success': True,
                        'affected_rows': result.rowcount,
                        'execution_time': round(execution_time, 3),
                        'query_id': query_id,
                        'database': db_name
                    }
                    
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            # 성능 로깅 (에러 포함)
            self._log_query_performance(query, execution_time, False, error_msg)
            
            logger.error(f"Query execution failed", query=query, error=error_msg)
            return {
                'success': False,
                'error': error_msg,
                'query': query,
                'execution_time': round(execution_time, 3),
                'query_id': query_id,
                'database': db_name
            }
    
    async def execute_query_safe(self, query: str, database_type: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Executes a query on the specified database. This is the primary method for running queries.
        """
        return await self.execute_query(database_type, query, params)
    
    async def get_schema_info(self, db_name: str = 'northwind') -> List[Dict[str, Any]]:
        """
        Get database schema information for a given database.
        Returns a list of tables with their columns.
        """
        engine = self.get_engine(db_name)
        metadata = MetaData()
        
        async with engine.connect() as conn:
            try:
                await conn.run_sync(metadata.reflect)
                schema_info = []
                for table_name, table in metadata.tables.items():
                    columns = [{
                        "column_name": col.name,
                        "data_type": str(col.type),
                        "is_nullable": col.nullable,
                    } for col in table.columns]
                    
                    schema_info.append({
                        "table_name": table_name,
                        "columns": columns
                    })
                return schema_info
            except Exception as e:
                logger.error(f"Schema retrieval failed for {db_name}", error=str(e))
                raise

    async def test_connections(self) -> None:
        """Test all configured database connections."""
        for name in self.engines:
            await self.test_connection(name)

    async def test_connection(self, db_name: str) -> bool:
        """Test database connection health asynchronously."""
        try:
            engine = self.get_engine(db_name)
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            # northwind 관련 로그만 제거, 다른 DB는 유지
            if db_name != 'northwind':
                logger.info(f"Connection test successful for {db_name}")
            return True
        except Exception as e:
            if db_name != 'northwind':
                logger.error(f"Connection test failed for {db_name}", error=str(e))
            return False
    
    async def close_all_connections(self):
        """Dispose all engine connections."""
        for name, engine in self.engines.items():
            await engine.dispose()
            # northwind 관련 로그만 제거, 다른 DB는 유지
            if name != 'northwind':
                logger.info(f"Closed connections for {name} database")

    # === 노트북의 EnhancedDatabaseManager 성능 모니터링 기능 ===
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """상세 성능 통계 반환 (노트북 EnhancedDatabaseManager 기능)"""
        stats = self.performance_stats.copy()
        
        if stats['total_queries'] > 0:
            stats['avg_query_time'] = round(stats['total_time'] / stats['total_queries'], 3)
            stats['cache_hit_rate'] = round(stats['cache_hits'] / (stats['cache_hits'] + stats['cache_misses']) * 100, 1) if (stats['cache_hits'] + stats['cache_misses']) > 0 else 0
        else:
            stats['avg_query_time'] = 0
            stats['cache_hit_rate'] = 0
        
        # 최근 쿼리 성능 분석
        recent_queries = self.query_log[-10:] if len(self.query_log) >= 10 else self.query_log
        if recent_queries:
            execution_times = [q['execution_time'] for q in recent_queries if q.get('execution_time')]
            if execution_times:
                stats['recent_avg_time'] = round(sum(execution_times) / len(execution_times), 3)
                stats['recent_max_time'] = round(max(execution_times), 3)
                stats['recent_min_time'] = round(min(execution_times), 3)
        
        stats['cache_size'] = len(self.query_cache)
        stats['total_query_log'] = len(self.query_log)
        
        return stats
    
    def get_query_log(self, limit: int = 10) -> List[Dict]:
        """최근 쿼리 로그 반환 (노트북 EnhancedDatabaseManager 기능)"""
        return self.query_log[-limit:] if len(self.query_log) >= limit else self.query_log
    
    def clear_performance_cache(self):
        """성능 캐시 초기화"""
        self.query_cache.clear()
        self.schema_cache.clear()
        logger.info("🧹 성능 캐시 초기화 완료")
    
    @lru_cache(maxsize=1)
    def get_enhanced_schema_info(self, db_name: str = 'northwind') -> Dict[str, Any]:
        """향상된 스키마 정보 조회 with 캐싱 (노트북 EnhancedDatabaseManager 기능)"""
        if db_name in self.schema_cache:
            logger.info(f"📋 스키마 캐시 HIT: {db_name}")
            return self.schema_cache[db_name]
        
        # 실제 스키마 정보는 기존 get_schema_info 메서드 활용
        # 이 메서드는 향후 실제 PostgreSQL 스키마 쿼리로 확장 가능
        enhanced_info = {
            'database': db_name,
            'cached_at': datetime.now().isoformat(),
            'performance_optimized': True,
            'cache_enabled': True
        }
        
        self.schema_cache[db_name] = enhanced_info
        logger.info(f"📋 스키마 정보 캐시 저장: {db_name}")
        
        return enhanced_info
    
    def _log_query_performance(self, query: str, execution_time: float, success: bool, error: str = None):
        """쿼리 성능 로깅 (노트북 EnhancedDatabaseManager 기능)"""
        query_entry = {
            'id': f"query_{len(self.query_log) + 1}",
            'sql': query[:200] + '...' if len(query) > 200 else query,
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat(),
            'status': 'SUCCESS' if success else 'ERROR',
            'error': error
        }
        
        self.query_log.append(query_entry)
        
        # 로그 크기 제한 (최대 1000개)
        if len(self.query_log) > 1000:
            self.query_log = self.query_log[-500:]  # 절반으로 줄임
        
        # 성능 통계 업데이트
        self.performance_stats['total_queries'] += 1
        self.performance_stats['total_time'] += execution_time
        
        if success:
            logger.debug(f"⚡ 쿼리 실행 완료: {query_entry['id']} ({execution_time:.3f}초)")
        else:
            self.performance_stats['errors'] += 1
            logger.error(f"❌ 쿼리 실행 실패: {query_entry['id']} - {error}")

    async def get_analysis_db_engine(self, connection_id: str, user_id: str):
        """
        Dynamically creates an SQLAlchemy engine for a user-defined analysis database.
        Supports PostgreSQL and MS SQL Server.
        """
        from services.connection_service import ConnectionService

        # The app DB session is needed to fetch the connection details
        async with self.get_session('app') as session:
            service = ConnectionService(session)
            conn_details = await service.get_connection(user_id=user_id, connection_id=connection_id)

        if not conn_details:
            raise ValueError("Database connection not found or access denied.")

        db_type = conn_details['db_type']
        db_user = conn_details['db_user']
        db_password = conn_details.get('db_password', '')
        db_host = conn_details['db_host']
        db_port = conn_details['db_port']
        db_name = conn_details['db_name']
        connection_name = conn_details['connection_name']

        # 분석 대상 데이터베이스 연결 정보 로깅 (비밀번호 제외)
        connection_info = f"{connection_name} ({db_type}://{db_user}@{db_host}:{db_port}/{db_name})"
        print(f"🔗 분석 대상 데이터베이스 엔진 생성: {connection_info}")
        
        # 데이터베이스 타입별 연결 URL 생성
        if db_type == 'postgresql':
            analysis_db_url = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        elif db_type == 'mssql' or db_type == 'sqlserver':
            # MS SQL Server 연결 URL
            # ODBC 드라이버 사용
            analysis_db_url = f"mssql+aioodbc://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?driver=ODBC+Driver+17+for+SQL+Server"
        elif db_type == 'mysql':
            # MySQL 지원 (향후 확장용)
            raise NotImplementedError(f"Database type '{db_type}' support is planned but not yet implemented.")
        else:
            raise NotImplementedError(f"Database type '{db_type}' is not supported. Supported types: postgresql, mssql, sqlserver")
        
        # TODO: Cache the created engine based on connection_id
        return create_async_engine(analysis_db_url, pool_pre_ping=True)


# Global database manager instance
db_manager = DatabaseManager()


# Convenience functions for common operations
@asynccontextmanager
async def get_northwind_connection():
    """Get connection to Northwind business database"""
    async with db_manager.get_connection('northwind') as conn:
        yield conn


@asynccontextmanager
async def get_app_connection():
    """Get connection to application database (if configured)"""
    if 'app' not in db_manager.engines:
        raise ValueError("Application database not configured")
    async with db_manager.get_connection('app') as conn:
        yield conn


async def execute_business_query(query: str, params: Optional[Dict] = None) -> Dict[str, Any]:
    """Execute query on business data (Northwind)"""
    return await db_manager.execute_query('northwind', query, params)


async def get_business_schema() -> List[Dict[str, Any]]:
    """Get business database schema for AI context"""
    return await db_manager.get_schema_info('northwind')


# FastAPI dependency functions
async def get_db_manager() -> DatabaseManager:
    """Get database manager instance for FastAPI dependency injection"""
    return db_manager

async def get_db_session(database: str = "app"):
    """Get database session for FastAPI dependency injection"""
    async with db_manager.get_session(database) as session:
        yield session
