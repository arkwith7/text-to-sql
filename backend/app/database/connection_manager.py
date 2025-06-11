"""
Database connection management for multi-database architecture
Handles both application database and business data sources
"""
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Dict, Any, Optional, Generator
import structlog
from app.config import settings

logger = structlog.get_logger(__name__)

# SQLAlchemy base for ORM models
Base = declarative_base()


class DatabaseManager:
    """Manages connections to multiple databases with connection pooling"""
    
    def __init__(self):
        self.engines: Dict[str, Any] = {}
        self.session_makers: Dict[str, Any] = {}
        self._initialize_connections()
    
    def _initialize_connections(self):
        """Initialize database connections with proper configuration"""
        # Application database (if configured)
        if settings.app_database_url:
            self.engines['app'] = create_engine(
                settings.app_database_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                echo=settings.debug
            )
            self.session_makers['app'] = sessionmaker(bind=self.engines['app'])
            logger.info("Application database connection initialized")
        
        # Northwind business database
        self.engines['northwind'] = create_engine(
            settings.database_url,  # Uses legacy DATABASE_URL for compatibility
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=settings.debug
        )
        self.session_makers['northwind'] = sessionmaker(bind=self.engines['northwind'])
        logger.info("Northwind database connection initialized")
    
    async def initialize(self):
        """Initialize database connections - compatibility method"""
        # Connections are already initialized in __init__
        # This method is for compatibility with startup/shutdown lifecycle
        logger.info("Database manager initialized")
        return True
    
    def get_engine(self, db_name: str):
        """Get database engine by name"""
        if db_name not in self.engines:
            raise ValueError(f"Database '{db_name}' not configured")
        return self.engines[db_name]
    
    @contextmanager
    def get_session(self, db_name: str) -> Generator:
        """Get database session with automatic cleanup"""
        if db_name not in self.session_makers:
            raise ValueError(f"Database '{db_name}' not configured")
        
        session = self.session_makers[db_name]()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error in {db_name}", error=str(e))
            raise
        finally:
            session.close()
    
    @contextmanager
    def get_connection(self, db_name: str) -> Generator:
        """Get raw database connection for direct SQL execution"""
        engine = self.get_engine(db_name)
        conn = engine.connect()
        try:
            yield conn
        except Exception as e:
            logger.error(f"Connection error in {db_name}", error=str(e))
            raise
        finally:
            conn.close()
    
    def execute_query(self, db_name: str, query: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute SQL query safely with error handling"""
        try:
            with self.get_connection(db_name) as conn:
                result = conn.execute(text(query), params or {})
                
                # Handle different query types
                if result.returns_rows:
                    columns = list(result.keys())
                    data = [dict(row._mapping) for row in result.fetchall()]
                    return {
                        'success': True,
                        'data': data,
                        'columns': columns,
                        'row_count': len(data)
                    }
                else:
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
    
    def execute_query_safe(self, *args, **kwargs) -> Dict[str, Any]:
        """Alias for execute_query with flexible parameter handling"""
        # Handle different calling patterns for backward compatibility
        if len(args) >= 2:
            # Pattern: execute_query_safe(db_name, query, params)
            return self.execute_query(args[0], args[1], args[2] if len(args) > 2 else kwargs.get('params'))
        elif len(args) == 1 and 'database_type' in kwargs:
            # Pattern: execute_query_safe(query, database_type="app")
            return self.execute_query(kwargs['database_type'], args[0], kwargs.get('params'))
        else:
            # Fallback
            db_name = kwargs.get('database_type', kwargs.get('db_name', 'app'))
            query = args[0] if args else kwargs.get('query')
            params = kwargs.get('params')
            return self.execute_query(db_name, query, params)
    
    def get_schema_info(self, db_name: str) -> Dict[str, Any]:
        """Get database schema information for AI context"""
        try:
            with self.get_connection(db_name) as conn:
                metadata = MetaData()
                metadata.reflect(bind=conn)
                
                schema_info = []
                for table_name in metadata.tables:
                    table = metadata.tables[table_name]
                    columns = []
                    
                    for column in table.columns:
                        columns.append({
                            'name': column.name,
                            'type': str(column.type),
                            'nullable': column.nullable,
                            'primary_key': column.primary_key,
                            'foreign_key': len(column.foreign_keys) > 0
                        })
                    
                    schema_info.append({
                        'table_name': table_name,
                        'columns': columns,
                        'primary_keys': [col.name for col in table.primary_key]
                    })
                
                return {
                    'success': True,
                    'schema': schema_info,
                    'table_count': len(schema_info)
                }
                
        except Exception as e:
            logger.error(f"Schema retrieval failed for {db_name}", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_connection(self, db_name: str) -> bool:
        """Test database connection health"""
        try:
            with self.get_connection(db_name) as conn:
                conn.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Connection test failed for {db_name}", error=str(e))
            return False
    
    def close_all_connections(self):
        """Close all database connections"""
        for name, engine in self.engines.items():
            engine.dispose()
            logger.info(f"Closed connections for {name} database")


# Global database manager instance
db_manager = DatabaseManager()


# Convenience functions for common operations
def get_northwind_connection():
    """Get connection to Northwind business database"""
    return db_manager.get_connection('northwind')


def get_app_connection():
    """Get connection to application database (if configured)"""
    if 'app' not in db_manager.engines:
        raise ValueError("Application database not configured")
    return db_manager.get_connection('app')


def execute_business_query(query: str, params: Optional[Dict] = None) -> Dict[str, Any]:
    """Execute query on business data (Northwind)"""
    return db_manager.execute_query('northwind', query, params)


def get_business_schema() -> Dict[str, Any]:
    """Get business database schema for AI context"""
    return db_manager.get_schema_info('northwind')
