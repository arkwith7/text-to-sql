"""
Analytics module for tracking usage, performance, and generating insights.

This module provides:
- Query usage tracking
- Performance monitoring
- User analytics
- System health metrics
- Business intelligence on usage patterns
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from enum import Enum
import json

from ..database.connection_manager import DatabaseManager
from ..config import get_settings

logger = logging.getLogger(__name__)

class EventType(str, Enum):
    """Types of events to track."""
    QUERY_EXECUTED = "query_executed"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    ERROR_OCCURRED = "error_occurred"
    API_REQUEST = "api_request"
    SCHEMA_ANALYZED = "schema_analyzed"

class QueryAnalytics(BaseModel):
    """Query analytics data model."""
    query_id: str
    user_id: str
    question: str
    sql_query: str
    execution_time: float
    row_count: int
    success: bool
    error_message: Optional[str] = None
    chart_type: Optional[str] = None
    timestamp: datetime

class UserAnalytics(BaseModel):
    """User analytics data model."""
    user_id: str
    total_queries: int
    successful_queries: int
    failed_queries: int
    avg_execution_time: float
    most_used_tables: List[str]
    most_common_chart_types: List[str]
    first_query: datetime
    last_query: datetime

class SystemMetrics(BaseModel):
    """System performance metrics."""
    total_users: int
    active_users_today: int
    total_queries_today: int
    avg_response_time: float
    error_rate: float
    top_error_types: List[Dict[str, Any]]
    database_health: Dict[str, Any]

class AnalyticsService:
    """
    Service for collecting, storing, and analyzing usage data.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.settings = get_settings()
        
        # Initialize analytics tables if they don't exist
        self._initialize_tables()
    
    def _initialize_tables(self):
        """Initialize analytics tables in the application database."""
        try:
            # Query analytics table
            create_query_analytics = """
            CREATE TABLE IF NOT EXISTS query_analytics (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                query_id VARCHAR(255) NOT NULL,
                user_id VARCHAR(255) NOT NULL,
                question TEXT NOT NULL,
                sql_query TEXT NOT NULL,
                execution_time FLOAT NOT NULL,
                row_count INTEGER NOT NULL,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                chart_type VARCHAR(50),
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            # Events table for general event tracking
            create_events = """
            CREATE TABLE IF NOT EXISTS events (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                event_type VARCHAR(50) NOT NULL,
                user_id VARCHAR(255),
                event_data JSONB,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                ip_address INET,
                user_agent TEXT
            )
            """
            
            # Performance metrics table
            create_performance = """
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                metric_name VARCHAR(100) NOT NULL,
                metric_value FLOAT NOT NULL,
                metric_unit VARCHAR(20),
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                additional_data JSONB
            )
            """
            
            # User sessions table
            create_sessions = """
            CREATE TABLE IF NOT EXISTS user_sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR(255) NOT NULL,
                session_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                session_end TIMESTAMP WITH TIME ZONE,
                ip_address INET,
                user_agent TEXT,
                queries_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE
            )
            """
            
            # Execute table creation queries
            for query in [create_query_analytics, create_events, create_performance, create_sessions]:
                self.db_manager.execute_query_safe(
                    query,
                    database_type="app"
                )
            
            # Create indexes for better performance
            self._create_indexes()
            
        except Exception as e:
            logger.error(f"Error initializing analytics tables: {str(e)}")
    
    def _create_indexes(self):
        """Create indexes for analytics tables."""
        try:
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_query_analytics_user_id ON query_analytics(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_query_analytics_timestamp ON query_analytics(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_events_type_timestamp ON events(event_type, timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_performance_name_timestamp ON performance_metrics(metric_name, timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_sessions_start ON user_sessions(session_start)"
            ]
            
            for index_query in indexes:
                self.db_manager.execute_query_safe(
                    index_query,
                    database_type="app"
                )
                
        except Exception as e:
            logger.error(f"Error creating analytics indexes: {str(e)}")
    
    async def log_query_execution(
        self,
        query_id: str,
        user_id: str,
        question: str,
        sql_query: str,
        execution_time: float,
        row_count: int,
        success: bool,
        error_message: Optional[str] = None,
        chart_type: Optional[str] = None
    ):
        """Log a query execution event."""
        try:
            insert_query = """
            INSERT INTO query_analytics (
                query_id, user_id, question, sql_query, execution_time,
                row_count, success, error_message, chart_type
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            self.db_manager.execute_query_safe(
                insert_query,
                params=(
                    query_id, user_id, question, sql_query, execution_time,
                    row_count, success, error_message, chart_type
                ),
                database_type="app"
            )
            
            # Also log as a general event
            await self.log_event(
                EventType.QUERY_EXECUTED,
                user_id,
                {
                    "query_id": query_id,
                    "success": success,
                    "execution_time": execution_time,
                    "row_count": row_count
                }
            )
            
        except Exception as e:
            logger.error(f"Error logging query execution: {str(e)}")
    
    async def log_event(
        self,
        event_type: EventType,
        user_id: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log a general event."""
        try:
            insert_query = """
            INSERT INTO events (event_type, user_id, event_data, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            self.db_manager.execute_query_safe(
                insert_query,
                params=(
                    event_type.value,
                    user_id,
                    json.dumps(event_data) if event_data else None,
                    ip_address,
                    user_agent
                ),
                database_type="app"
            )
            
        except Exception as e:
            logger.error(f"Error logging event: {str(e)}")
    
    async def log_performance_metric(
        self,
        metric_name: str,
        metric_value: float,
        metric_unit: str = "ms",
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """Log a performance metric."""
        try:
            insert_query = """
            INSERT INTO performance_metrics (metric_name, metric_value, metric_unit, additional_data)
            VALUES (%s, %s, %s, %s)
            """
            
            self.db_manager.execute_query_safe(
                insert_query,
                params=(
                    metric_name,
                    metric_value,
                    metric_unit,
                    json.dumps(additional_data) if additional_data else None
                ),
                database_type="app"
            )
            
        except Exception as e:
            logger.error(f"Error logging performance metric: {str(e)}")
    
    async def start_user_session(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """Start a new user session and return session ID."""
        try:
            insert_query = """
            INSERT INTO user_sessions (user_id, ip_address, user_agent)
            VALUES (%s, %s, %s)
            RETURNING id
            """
            
            result = self.db_manager.execute_query_safe(
                insert_query,
                params=(user_id, ip_address, user_agent),
                database_type="app"
            )
            
            session_id = result["data"][0]["id"] if result["data"] else None
            
            await self.log_event(
                EventType.USER_LOGIN,
                user_id,
                {"session_id": str(session_id)}
            )
            
            return str(session_id)
            
        except Exception as e:
            logger.error(f"Error starting user session: {str(e)}")
            return ""
    
    async def end_user_session(self, session_id: str, user_id: str):
        """End a user session."""
        try:
            update_query = """
            UPDATE user_sessions 
            SET session_end = CURRENT_TIMESTAMP, is_active = FALSE
            WHERE id = %s AND user_id = %s
            """
            
            self.db_manager.execute_query_safe(
                update_query,
                params=(session_id, user_id),
                database_type="app"
            )
            
            await self.log_event(
                EventType.USER_LOGOUT,
                user_id,
                {"session_id": session_id}
            )
            
        except Exception as e:
            logger.error(f"Error ending user session: {str(e)}")
    
    async def get_user_analytics(self, user_id: str) -> UserAnalytics:
        """Get analytics data for a specific user."""
        try:
            # Get basic query statistics
            stats_query = """
            SELECT 
                COUNT(*) as total_queries,
                COUNT(*) FILTER (WHERE success = true) as successful_queries,
                COUNT(*) FILTER (WHERE success = false) as failed_queries,
                AVG(execution_time) as avg_execution_time,
                MIN(timestamp) as first_query,
                MAX(timestamp) as last_query
            FROM query_analytics
            WHERE user_id = %s
            """
            
            result = self.db_manager.execute_query_safe(
                stats_query,
                params=(user_id,),
                database_type="app"
            )
            
            if not result["data"]:
                # Return default analytics for new users
                return UserAnalytics(
                    user_id=user_id,
                    total_queries=0,
                    successful_queries=0,
                    failed_queries=0,
                    avg_execution_time=0.0,
                    most_used_tables=[],
                    most_common_chart_types=[],
                    first_query=datetime.now(timezone.utc),
                    last_query=datetime.now(timezone.utc)
                )
            
            stats = result["data"][0]
            
            # Get most used tables (extract from SQL queries)
            tables_query = """
            SELECT sql_query
            FROM query_analytics
            WHERE user_id = %s AND success = true
            ORDER BY timestamp DESC
            LIMIT 100
            """
            
            tables_result = self.db_manager.execute_query_safe(
                tables_query,
                params=(user_id,),
                database_type="app"
            )
            
            most_used_tables = self._extract_most_used_tables(
                [row["sql_query"] for row in tables_result["data"]]
            )
            
            # Get most common chart types
            charts_query = """
            SELECT chart_type, COUNT(*) as count
            FROM query_analytics
            WHERE user_id = %s AND chart_type IS NOT NULL
            GROUP BY chart_type
            ORDER BY count DESC
            LIMIT 5
            """
            
            charts_result = self.db_manager.execute_query_safe(
                charts_query,
                params=(user_id,),
                database_type="app"
            )
            
            most_common_chart_types = [
                row["chart_type"] for row in charts_result["data"]
            ]
            
            return UserAnalytics(
                user_id=user_id,
                total_queries=stats["total_queries"] or 0,
                successful_queries=stats["successful_queries"] or 0,
                failed_queries=stats["failed_queries"] or 0,
                avg_execution_time=float(stats["avg_execution_time"] or 0),
                most_used_tables=most_used_tables,
                most_common_chart_types=most_common_chart_types,
                first_query=stats["first_query"] or datetime.now(timezone.utc),
                last_query=stats["last_query"] or datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {str(e)}")
            raise
    
    async def get_system_metrics(self) -> SystemMetrics:
        """Get overall system metrics."""
        try:
            # Get basic system statistics
            today = datetime.now(timezone.utc).date()
            
            # Total users
            users_query = "SELECT COUNT(*) as total_users FROM users"
            users_result = self.db_manager.execute_query_safe(
                users_query,
                database_type="app"
            )
            total_users = users_result["data"][0]["total_users"] if users_result["data"] else 0
            
            # Active users today
            active_users_query = """
            SELECT COUNT(DISTINCT user_id) as active_users
            FROM query_analytics
            WHERE timestamp >= %s
            """
            
            active_result = self.db_manager.execute_query_safe(
                active_users_query,
                params=(today,),
                database_type="app"
            )
            active_users_today = active_result["data"][0]["active_users"] if active_result["data"] else 0
            
            # Total queries today
            queries_today_query = """
            SELECT COUNT(*) as total_queries
            FROM query_analytics
            WHERE timestamp >= %s
            """
            
            queries_result = self.db_manager.execute_query_safe(
                queries_today_query,
                params=(today,),
                database_type="app"
            )
            total_queries_today = queries_result["data"][0]["total_queries"] if queries_result["data"] else 0
            
            # Average response time
            response_time_query = """
            SELECT AVG(execution_time) as avg_response_time
            FROM query_analytics
            WHERE timestamp >= %s AND success = true
            """
            
            response_result = self.db_manager.execute_query_safe(
                response_time_query,
                params=(today,),
                database_type="app"
            )
            avg_response_time = float(
                response_result["data"][0]["avg_response_time"] or 0
            ) if response_result["data"] else 0
            
            # Error rate
            error_rate_query = """
            SELECT 
                COUNT(*) FILTER (WHERE success = false) * 100.0 / COUNT(*) as error_rate
            FROM query_analytics
            WHERE timestamp >= %s
            """
            
            error_result = self.db_manager.execute_query_safe(
                error_rate_query,
                params=(today,),
                database_type="app"
            )
            error_rate = float(
                error_result["data"][0]["error_rate"] or 0
            ) if error_result["data"] else 0
            
            # Top error types
            errors_query = """
            SELECT error_message, COUNT(*) as count
            FROM query_analytics
            WHERE timestamp >= %s AND success = false AND error_message IS NOT NULL
            GROUP BY error_message
            ORDER BY count DESC
            LIMIT 5
            """
            
            errors_result = self.db_manager.execute_query_safe(
                errors_query,
                params=(today,),
                database_type="app"
            )
            
            top_error_types = [
                {"error": row["error_message"], "count": row["count"]}
                for row in errors_result["data"]
            ]
            
            # Database health (simplified)
            database_health = await self._check_database_health()
            
            return SystemMetrics(
                total_users=total_users,
                active_users_today=active_users_today,
                total_queries_today=total_queries_today,
                avg_response_time=avg_response_time,
                error_rate=error_rate,
                top_error_types=top_error_types,
                database_health=database_health
            )
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {str(e)}")
            raise
    
    def _extract_most_used_tables(self, sql_queries: List[str]) -> List[str]:
        """Extract most frequently used tables from SQL queries."""
        import re
        from collections import Counter
        
        table_pattern = r'\bFROM\s+(\w+)|\bJOIN\s+(\w+)'
        all_tables = []
        
        for query in sql_queries:
            matches = re.findall(table_pattern, query.upper())
            for match in matches:
                table = match[0] if match[0] else match[1]
                if table and table not in ['SELECT', 'WHERE', 'ORDER', 'GROUP']:
                    all_tables.append(table.lower())
        
        # Get top 5 most used tables
        table_counts = Counter(all_tables)
        return [table for table, count in table_counts.most_common(5)]
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check basic database health metrics."""
        try:
            # Check connection to both databases
            app_health = True
            business_health = True
            
            try:
                self.db_manager.execute_query_safe(
                    "SELECT 1",
                    database_type="app"
                )
            except:
                app_health = False
            
            try:
                self.db_manager.execute_query_safe(
                    "SELECT 1",
                    database_type="business"
                )
            except:
                business_health = False
            
            return {
                "app_database": "healthy" if app_health else "unhealthy",
                "business_database": "healthy" if business_health else "unhealthy",
                "overall_status": "healthy" if app_health and business_health else "unhealthy",
                "last_checked": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking database health: {str(e)}")
            return {
                "app_database": "unknown",
                "business_database": "unknown",
                "overall_status": "unknown",
                "error": str(e)
            }
    
    async def get_popular_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular queries across all users."""
        try:
            query = """
            SELECT 
                question,
                COUNT(*) as usage_count,
                AVG(execution_time) as avg_execution_time,
                COUNT(*) FILTER (WHERE success = true) as success_count
            FROM query_analytics
            WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY question
            HAVING COUNT(*) > 1
            ORDER BY usage_count DESC
            LIMIT %s
            """
            
            result = self.db_manager.execute_query_safe(
                query,
                params=(limit,),
                database_type="app"
            )
            
            return result["data"]
            
        except Exception as e:
            logger.error(f"Error getting popular queries: {str(e)}")
            return []
    
    async def get_usage_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get usage trends over the specified number of days."""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            trends_query = """
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as total_queries,
                COUNT(DISTINCT user_id) as unique_users,
                AVG(execution_time) as avg_execution_time,
                COUNT(*) FILTER (WHERE success = true) as successful_queries
            FROM query_analytics
            WHERE timestamp >= %s
            GROUP BY DATE(timestamp)
            ORDER BY date
            """
            
            result = self.db_manager.execute_query_safe(
                trends_query,
                params=(start_date,),
                database_type="app"
            )
            
            return {
                "trends": result["data"],
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting usage trends: {str(e)}")
            return {"trends": [], "period_days": days}
