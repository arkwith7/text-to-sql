"""
Database connection management for multi-database architecture
Handles both application database (SQLite) and business data sources (PostgreSQL)
"""
from sqlalchemy import text, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, Generator, List
import structlog
from app.config import settings

logger = structlog.get_logger(__name__)

# SQLAlchemy base for ORM models
Base = declarative_base()


class DatabaseManager:
    """Manages connections to multiple databases with appropriate connection pooling"""

    def __init__(self):
        self.engines: Dict[str, Any] = {}
        self.session_makers: Dict[str, Any] = {}
        # Initialization is now deferred to an async method
    
    async def initialize(self):
        """Initialize database connections asynchronously."""
        self._initialize_connections()
        # Create all tables for the application database
        await self.create_app_db_tables()
        logger.info("Database manager initialized and app tables created.")

    def _initialize_connections(self):
        """Initialize database connections with proper configuration"""
        # Application database (SQLite)
        if settings.app_database_url:
            is_sqlite = settings.app_database_url.startswith("sqlite")
            
            engine_args = {
                "echo": settings.debug
            }

            app_db_url = settings.app_database_url
            if is_sqlite and not app_db_url.startswith("sqlite+aiosqlite"):
                 app_db_url = app_db_url.replace("sqlite://", "sqlite+aiosqlite://")

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
        """Execute SQL query safely with error handling"""
        try:
            async with self.get_connection(db_name) as conn:
                result = await conn.execute(text(query), params or {})
                
                if result.returns_rows:
                    columns = list(result.keys())
                    data = [dict(row._mapping) for row in result.all()]
                    return {
                        'success': True,
                        'data': data,
                        'columns': columns,
                        'row_count': len(data)
                    }
                else:
                    await conn.commit() 
                    return {
                        'success': True,
                        'affected_rows': result.rowcount
                    }
                    
        except Exception as e:
            logger.error(f"Query execution failed", query=query, error=str(e))
            return {
                'success': False,
                'error': str(e),
                'query': query
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
            logger.info(f"Connection test successful for {db_name}")
            return True
        except Exception as e:
            logger.error(f"Connection test failed for {db_name}", error=str(e))
            return False
    
    async def close_all_connections(self):
        """Dispose all engine connections."""
        for name, engine in self.engines.items():
            await engine.dispose()
            logger.info(f"Closed connections for {name} database")


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
