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
import uuid
from fastapi import Request
from core.utils.cost_calculator import calculate_cost_from_usage

from database.connection_manager import DatabaseManager
from core.config import get_settings

logger = logging.getLogger(__name__)

class EventType(str, Enum):
    """Types of events to track."""
    QUERY_EXECUTED = "query_executed"
    USER_LOGGED_IN = "user_logged_in"
    USER_REGISTERED = "user_registered"
    TOKEN_REFRESHED = "token_refreshed"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    ERROR_OCCURRED = "error_occurred"
    API_REQUEST = "api_request"
    SCHEMA_ANALYZED = "schema_analyzed"
    QUERY_SUBMITTED = "query_submitted"
    QUERY_COMPLETED = "query_completed"

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
        chart_type: Optional[str] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        llm_model: Optional[str] = None,
        llm_cost_estimate: Optional[float] = None
    ):
        """Log a query execution event."""
        try:
            insert_query = """
            INSERT INTO query_analytics (
                id, query_id, user_id, question, sql_query, execution_time,
                row_count, success, error_message, chart_type, timestamp, created_at,
                prompt_tokens, completion_tokens, total_tokens, llm_model, llm_cost_estimate
            ) VALUES (:id, :query_id, :user_id, :question, :sql_query, :execution_time, :row_count, :success, :error_message, :chart_type, :timestamp, :created_at, :prompt_tokens, :completion_tokens, :total_tokens, :llm_model, :llm_cost_estimate)
            """
            
            current_time = datetime.now(timezone.utc)
            params = {
                "id": str(uuid.uuid4()),
                "query_id": query_id,
                "user_id": user_id,
                "question": question,
                "sql_query": sql_query,
                "execution_time": execution_time,
                "row_count": row_count,
                "success": success,
                "error_message": error_message,
                "chart_type": chart_type,
                "timestamp": current_time,
                "created_at": current_time,
                "prompt_tokens": prompt_tokens or 0,
                "completion_tokens": completion_tokens or 0,
                "total_tokens": total_tokens or 0,
                "llm_model": llm_model,
                "llm_cost_estimate": llm_cost_estimate or 0.0
            }

            await self.db_manager.execute_query_safe(
                insert_query,
                params=params,
                database_type="app"
            )
            
            logger.info(f"📊 Query analytics logged - ID: {query_id}, Success: {success}, Execution Time: {execution_time}ms, Row Count: {row_count}")
            
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
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """
        Logs an event with optional details and request context.
        """
        try:
            event = {
                "type": event_type,
                "user_id": user_id,
                "data": event_data,
                "details": details,
                "timestamp": datetime.utcnow().isoformat(),
                "request": {
                    "method": request.method,
                    "url": str(request.url)
                } if request else None
            }
            # Save event to database or log it
            await self._save_event_to_db(event)
        except Exception as e:
            logger.error(f"Failed to log event: {e}")
    
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
            INSERT INTO performance_metrics (id, metric_name, metric_value, metric_unit, timestamp, additional_data)
            VALUES (:id, :metric_name, :metric_value, :metric_unit, :timestamp, :additional_data)
            """
            
            params = {
                "id": str(uuid.uuid4()),
                "metric_name": metric_name,
                "metric_value": metric_value,
                "metric_unit": metric_unit,
                "timestamp": datetime.now(timezone.utc),
                "additional_data": json.dumps(additional_data) if additional_data else None
            }

            await self.db_manager.execute_query_safe(
                insert_query,
                params=params,
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
            session_id = str(uuid.uuid4())
            insert_query = """
            INSERT INTO user_sessions (id, user_id, ip_address, user_agent)
            VALUES (:id, :user_id, :ip_address, :user_agent)
            """
            
            params = {
                "id": session_id,
                "user_id": user_id,
                "ip_address": ip_address,
                "user_agent": user_agent
            }

            result = await self.db_manager.execute_query_safe(
                insert_query,
                params=params,
                database_type="app"
            )
            
            await self.log_event(
                EventType.USER_LOGIN,
                user_id,
                {"session_id": session_id}
            )
            
            return session_id
            
        except Exception as e:
            logger.error(f"Error starting user session: {str(e)}")
            return ""
    
    async def end_user_session(self, session_id: str, user_id: str):
        """End a user session."""
        try:
            update_query = """
            UPDATE user_sessions
            SET session_end = :session_end, is_active = FALSE
            WHERE id = :id AND user_id = :user_id AND is_active = TRUE
            """
            
            params = {
                "session_end": datetime.now(timezone.utc).isoformat(),
                "id": session_id,
                "user_id": user_id
            }

            await self.db_manager.execute_query_safe(
                update_query,
                params=params,
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
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_queries,
                AVG(execution_time) as avg_execution_time,
                MIN(timestamp) as first_query,
                MAX(timestamp) as last_query,
                COALESCE(SUM(total_tokens), 0) as total_tokens,
                COALESCE(SUM(prompt_tokens), 0) as input_tokens,
                COALESCE(SUM(completion_tokens), 0) as output_tokens,
                COALESCE(SUM(llm_cost_estimate), 0) as total_cost
            FROM query_analytics WHERE user_id = :user_id
            """
            
            result = await self.db_manager.execute_query_safe(
                stats_query,
                params={"user_id": user_id},
                database_type="app"
            )
            
            if not result['success'] or not result['data']:
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
            
            stats = result['data'][0]
            
            # Get most used tables (extract from SQL queries)
            tables_query = """
            SELECT sql_query FROM query_analytics 
            WHERE user_id = :user_id AND success = TRUE
            """
            
            tables_result = await self.db_manager.execute_query_safe(
                tables_query,
                params={"user_id": user_id},
                database_type="app"
            )
            
            most_used_tables = self._extract_most_used_tables(
                [row["sql_query"] for row in tables_result['data']]
            )
            
            # Get most common chart types
            charts_query = """
            SELECT chart_type, COUNT(*) as count 
            FROM query_analytics
            WHERE user_id = :user_id AND chart_type IS NOT NULL
            GROUP BY chart_type
            ORDER BY count DESC
            """
            
            charts_result = await self.db_manager.execute_query_safe(
                charts_query,
                params={"user_id": user_id},
                database_type="app"
            )
            
            most_common_chart_types = [
                row["chart_type"] for row in charts_result['data']
            ]
            
            return UserAnalytics(
                user_id=user_id,
                total_queries=stats["total_queries"] or 0,
                successful_queries=stats["successful_queries"] or 0,
                failed_queries=stats["total_queries"] - stats["successful_queries"] or 0,
                avg_execution_time=float(stats["avg_execution_time"] or 0),
                most_used_tables=most_used_tables,
                most_common_chart_types=most_common_chart_types,
                first_query=stats["first_query"] or datetime.now(timezone.utc),
                last_query=stats["last_query"] or datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {str(e)}")
            raise
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user statistics including token usage."""
        try:
            # Get basic query statistics with cost information
            stats_query = """
            SELECT 
                COUNT(*) as total_queries,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_queries,
                AVG(execution_time) as avg_execution_time,
                SUM(row_count) as total_rows_processed,
                MAX(timestamp) as last_query_at,
                SUM(COALESCE(llm_cost_estimate, 0)) as total_cost,
                AVG(COALESCE(llm_cost_estimate, 0)) as avg_cost_per_query
            FROM query_analytics WHERE user_id = :user_id
            """
            
            result = await self.db_manager.execute_query_safe(
                stats_query,
                params={"user_id": user_id},
                database_type="app"
            )
            
            if not result['success'] or not result['data']:
                return {
                    "total_queries": 0,
                    "total_tokens": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "last_query_at": None,
                    "daily_usage": {},
                    "monthly_usage": {},
                    "average_tokens_per_query": 0
                }
            
            stats = result['data'][0]
            
            # Get token usage from events table (if exists)
            token_query = """
            SELECT 
                COALESCE(SUM(CAST(total_tokens AS INTEGER)), 0) as total_tokens,
                COALESCE(SUM(CAST(prompt_tokens AS INTEGER)), 0) as input_tokens,
                COALESCE(SUM(CAST(completion_tokens AS INTEGER)), 0) as output_tokens,
                COALESCE(SUM(llm_cost_estimate), 0.0) as total_cost
            FROM query_analytics 
            WHERE user_id = :user_id AND total_tokens > 0
            """
            
            token_result = await self.db_manager.execute_query_safe(
                token_query,
                params={"user_id": user_id},
                database_type="app"
            )
            
            token_stats = {"total_tokens": 0, "input_tokens": 0, "output_tokens": 0, "total_cost": 0.0}
            if token_result['success'] and token_result['data']:
                token_stats = token_result['data'][0]
            
            # Get daily usage for the last 30 days
            daily_usage_query = """
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as queries,
                COALESCE(SUM(total_tokens), 0) as tokens,
                COALESCE(SUM(llm_cost_estimate), 0.0) as cost
            FROM query_analytics
            
            WHERE user_id = :user_id 
            AND timestamp >= DATE('now', '-30 days')
            AND total_tokens > 0
            GROUP BY DATE(timestamp)
            ORDER BY DATE(timestamp)
            """
            
            daily_result = await self.db_manager.execute_query_safe(
                daily_usage_query,
                params={"user_id": user_id},
                database_type="app"
            )
            
            daily_usage = {}
            if daily_result['success'] and daily_result['data']:
                for row in daily_result['data']:
                    daily_usage[row['date']] = {
                        'queries': row['queries'],
                        'tokens': row['tokens'] or 0,
                        'cost': round(row.get('cost', 0.0), 6)
                    }
            
            # Calculate average tokens per query
            total_queries = stats.get('total_queries', 0)
            total_tokens = token_stats.get('total_tokens', 0)
            avg_tokens = total_tokens / total_queries if total_queries > 0 else 0
            
            return {
                "user_id": user_id,
                "total_queries": stats.get('total_queries', 0),
                "total_tokens": token_stats.get('total_tokens', 0),
                "input_tokens": token_stats.get('input_tokens', 0),
                "output_tokens": token_stats.get('output_tokens', 0),
                "total_cost": round(stats.get('total_cost', 0.0), 6),
                "last_query_at": stats.get('last_query_at'),
                "daily_usage": daily_usage,
                "monthly_usage": {},  # Could implement monthly aggregation if needed
                "average_tokens_per_query": round(avg_tokens, 2),
                "average_cost_per_query": round(stats.get('avg_cost_per_query', 0.0), 6)
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            # Return default stats on error
            return {
                "total_queries": 0,
                "total_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_cost": 0.0,
                "last_query_at": None,
                "daily_usage": {},
                "monthly_usage": {},
                "average_tokens_per_query": 0,
                "average_cost_per_query": 0.0
            }
    
    async def get_system_metrics(self) -> SystemMetrics:
        """Get overall system metrics."""
        try:
            # Get basic system statistics
            today = datetime.now(timezone.utc).date()
            
            # Total users
            users_query = "SELECT COUNT(*) as total_users FROM users"
            users_result = await self.db_manager.execute_query_safe(
                users_query,
                database_type="app"
            )
            total_users = users_result['data'][0]['total_users'] if users_result['success'] and users_result['data'] else 0
            
            # Active users today
            active_users_query = """
            SELECT COUNT(DISTINCT user_id) as active_users
            FROM query_analytics
            WHERE DATE(timestamp) = :today
            """
            
            active_result = await self.db_manager.execute_query_safe(
                active_users_query,
                params={"today": today},
                database_type="app"
            )
            active_users_today = active_result['data'][0]['active_users'] if active_result['success'] and active_result['data'] else 0
            
            # Total queries today
            queries_today_query = """
            SELECT COUNT(*) as total_queries
            FROM query_analytics
            WHERE DATE(timestamp) = :today
            """
            
            queries_result = await self.db_manager.execute_query_safe(
                queries_today_query,
                params={"today": today},
                database_type="app"
            )
            total_queries_today = queries_result['data'][0]['total_queries'] if queries_result['success'] and queries_result['data'] else 0
            
            # Avg response time today for API requests
            response_time_query = """
            SELECT AVG(metric_value) as avg_response_time
            FROM performance_metrics
            WHERE metric_name = 'api_request_duration' AND DATE(timestamp) = :today
            """
            
            response_result = await self.db_manager.execute_query_safe(
                response_time_query,
                params={"today": today},
                database_type="app"
            )
            avg_response_time = response_result['data'][0]['avg_response_time'] if response_result['success'] and response_result['data'] and response_result['data'][0]['avg_response_time'] is not None else 0.0
            
            # Error rate today
            error_rate_query = """
            SELECT 
                CAST(SUM(CASE WHEN success = FALSE THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) as error_rate
            FROM query_analytics
            WHERE DATE(timestamp) = :today
            """
            
            error_result = await self.db_manager.execute_query_safe(
                error_rate_query,
                params={"today": today},
                database_type="app"
            )
            error_rate = error_result['data'][0]['error_rate'] if error_result['success'] and error_result['data'] and error_result['data'][0]['error_rate'] is not None else 0.0
            
            # Top 5 error types today
            errors_query = """
            SELECT error_message, COUNT(*) as count
            FROM query_analytics
            WHERE success = FALSE AND DATE(timestamp) = :today AND error_message IS NOT NULL
            GROUP BY error_message
            ORDER BY count DESC
            LIMIT 5
            """
            
            errors_result = await self.db_manager.execute_query_safe(
                errors_query,
                params={"today": today},
                database_type="app"
            )
            top_errors = errors_result['data'] if errors_result['success'] else []
            
            # Database health (simplified)
            database_health = await self._check_database_health()
            
            return SystemMetrics(
                total_users=total_users,
                active_users_today=active_users_today,
                total_queries_today=total_queries_today,
                avg_response_time=avg_response_time,
                error_rate=error_rate,
                top_error_types=top_errors,
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
                await self.db_manager.execute_query_safe(
                    "SELECT 1",
                    database_type="app"
                )
            except:
                app_health = False
            
            try:
                await self.db_manager.execute_query_safe(
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
            SELECT question, COUNT(*) as count
            FROM query_analytics
            GROUP BY question
            ORDER BY count DESC
            LIMIT :limit
            """
            
            result = await self.db_manager.execute_query_safe(
                query,
                params={"limit": limit},
                database_type="app"
            )
            
            return result['data'] if result['success'] else []
            
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
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_queries
            FROM query_analytics
            WHERE timestamp >= :start_date
            GROUP BY DATE(timestamp)
            ORDER BY DATE(timestamp)
            """
            
            result = await self.db_manager.execute_query_safe(
                trends_query,
                params={"start_date": start_date},
                database_type="app"
            )
            
            if not result['success']:
                return {"trends": [], "period_days": days}
            
            trends = result['data']
            
            return {
                "trends": trends,
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting usage trends: {str(e)}")
            return {"trends": [], "period_days": days}

    async def _save_event_to_db(self, event: Dict[str, Any]):
        """Save event to database."""
        try:
            insert_query = """
            INSERT INTO events (id, event_type, user_id, event_data, timestamp, ip_address, user_agent, session_id)
            VALUES (:id, :event_type, :user_id, :event_data, :timestamp, :ip_address, :user_agent, :session_id)
            """
            
            params = {
                "id": str(uuid.uuid4()),
                "event_type": event.get("type"),
                "user_id": event.get("user_id"),
                "event_data": json.dumps(event.get("data")) if event.get("data") else None,
                "timestamp": datetime.now(timezone.utc),
                "ip_address": None,  # Could extract from request if needed
                "user_agent": None,  # Could extract from request if needed
                "session_id": None   # Could extract from request if needed
            }

            await self.db_manager.execute_query_safe(
                insert_query,
                params=params,
                database_type="app"
            )
            
        except Exception as e:
            logger.error(f"Error saving event to database: {str(e)}")
            # Don't raise exception to avoid breaking the main flow

    async def log_query_execution_with_tokens(
        self,
        query_id: str,
        user_id: str,
        question: str,
        sql_query: str,
        execution_time: float,
        row_count: int,
        success: bool,
        error_message: Optional[str] = None,
        chart_type: Optional[str] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        llm_model: Optional[str] = None,
        llm_cost_estimate: float = 0.0
    ):
        """Log a query execution event with token usage information."""
        try:
            # 토큰 정보가 있으면 실제 비용 계산
            if total_tokens > 0 and llm_model:
                calculated_cost = calculate_cost_from_usage(
                    {
                        'prompt_tokens': prompt_tokens,
                        'completion_tokens': completion_tokens,
                        'total_tokens': total_tokens
                    },
                    llm_model
                )
                # 계산된 비용이 0이 아니면 사용, 그렇지 않으면 기존 값 유지
                if calculated_cost > 0:
                    llm_cost_estimate = calculated_cost
            
            insert_query = """
            INSERT INTO query_analytics (
                id, query_id, user_id, question, sql_query, execution_time,
                row_count, success, error_message, chart_type, timestamp, created_at,
                prompt_tokens, completion_tokens, total_tokens, llm_model, llm_cost_estimate
            ) VALUES (:id, :query_id, :user_id, :question, :sql_query, :execution_time, :row_count, :success, :error_message, :chart_type, :timestamp, :created_at, :prompt_tokens, :completion_tokens, :total_tokens, :llm_model, :llm_cost_estimate)
            """
            
            current_time = datetime.now(timezone.utc)
            params = {
                "id": str(uuid.uuid4()),
                "query_id": query_id,
                "user_id": user_id,
                "question": question,
                "sql_query": sql_query,
                "execution_time": execution_time,
                "row_count": row_count,
                "success": success,
                "error_message": error_message,
                "chart_type": chart_type,
                "timestamp": current_time,
                "created_at": current_time,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "llm_model": llm_model,
                "llm_cost_estimate": llm_cost_estimate
            }

            await self.db_manager.execute_query_safe(
                insert_query,
                params=params,
                database_type="app"
            )
            
            logger.info(f"📊 Query analytics with tokens logged - ID: {query_id}, Tokens: {total_tokens}")
            
            # Also log as a general event
            await self.log_event(
                EventType.QUERY_EXECUTED,
                user_id,
                {
                    "query_id": query_id,
                    "success": success,
                    "execution_time": execution_time,
                    "row_count": row_count,
                    "total_tokens": total_tokens,
                    "llm_model": llm_model
                }
            )
            
        except Exception as e:
            logger.error(f"Error logging query execution with tokens: {str(e)}")

    async def get_user_model_stats(self, user_id: str) -> Dict[str, Any]:
        """Get detailed model usage statistics for a user."""
        try:
            # Get model breakdown statistics
            model_stats_query = """
            SELECT 
                COALESCE(llm_model, 'Unknown') as model_name,
                COUNT(*) as query_count,
                SUM(COALESCE(prompt_tokens, 0)) as total_input_tokens,
                SUM(COALESCE(completion_tokens, 0)) as total_output_tokens,
                SUM(COALESCE(total_tokens, 0)) as total_tokens,
                SUM(COALESCE(llm_cost_estimate, 0)) as total_cost,
                AVG(COALESCE(llm_cost_estimate, 0)) as avg_cost_per_query,
                AVG(COALESCE(total_tokens, 0)) as avg_tokens_per_query,
                MIN(created_at) as first_used,
                MAX(created_at) as last_used
            FROM query_analytics 
            WHERE user_id = :user_id 
            AND llm_model IS NOT NULL 
            AND total_tokens > 0
            GROUP BY llm_model
            ORDER BY total_cost DESC
            """
            
            result = await self.db_manager.execute_query_safe(
                model_stats_query,
                params={"user_id": user_id},
                database_type="app"
            )
            
            models_breakdown = []
            if result['success'] and result['data']:
                for row in result['data']:
                    # Calculate cost breakdown
                    input_cost = (row['total_input_tokens'] / 1000) * self._get_model_input_rate(row['model_name'])
                    output_cost = (row['total_output_tokens'] / 1000) * self._get_model_output_rate(row['model_name'])
                    
                    models_breakdown.append({
                        'model_name': row['model_name'],
                        'query_count': row['query_count'],
                        'total_tokens': row['total_tokens'],
                        'input_tokens': row['total_input_tokens'],
                        'output_tokens': row['total_output_tokens'],
                        'total_cost': round(row['total_cost'], 6),
                        'input_cost': round(input_cost, 6),
                        'output_cost': round(output_cost, 6),
                        'avg_cost_per_query': round(row['avg_cost_per_query'], 6),
                        'avg_tokens_per_query': round(row['avg_tokens_per_query'], 2),
                        'first_used': row['first_used'],
                        'last_used': row['last_used'],
                        'cost_per_token': round(row['total_cost'] / row['total_tokens'], 8) if row['total_tokens'] > 0 else 0
                    })
            
            # Get token type breakdown (전체)
            token_breakdown_query = """
            SELECT 
                SUM(COALESCE(prompt_tokens, 0)) as total_input_tokens,
                SUM(COALESCE(completion_tokens, 0)) as total_output_tokens,
                SUM(COALESCE(total_tokens, 0)) as total_tokens,
                SUM(COALESCE(llm_cost_estimate, 0)) as total_cost
            FROM query_analytics 
            WHERE user_id = :user_id AND total_tokens > 0
            """
            
            token_result = await self.db_manager.execute_query_safe(
                token_breakdown_query,
                params={"user_id": user_id},
                database_type="app"
            )
            
            token_breakdown = {
                'total_input_tokens': 0,
                'total_output_tokens': 0,
                'total_tokens': 0,
                'input_cost': 0.0,
                'output_cost': 0.0,
                'total_cost': 0.0
            }
            
            if token_result['success'] and token_result['data']:
                data = token_result['data'][0]
                # 전체 토큰별 비용 (주로 사용되는 모델 기준으로 계산)
                primary_model = models_breakdown[0]['model_name'] if models_breakdown else 'gpt-4o-mini'
                input_cost = (data['total_input_tokens'] / 1000) * self._get_model_input_rate(primary_model)
                output_cost = (data['total_output_tokens'] / 1000) * self._get_model_output_rate(primary_model)
                
                token_breakdown = {
                    'total_input_tokens': data['total_input_tokens'],
                    'total_output_tokens': data['total_output_tokens'],
                    'total_tokens': data['total_tokens'],
                    'input_cost': round(input_cost, 6),
                    'output_cost': round(output_cost, 6),
                    'total_cost': round(data['total_cost'], 6),
                    'input_cost_per_1k': self._get_model_input_rate(primary_model),
                    'output_cost_per_1k': self._get_model_output_rate(primary_model)
                }
            
            return {
                'models_breakdown': models_breakdown,
                'token_breakdown': token_breakdown,
                'summary': {
                    'total_models_used': len(models_breakdown),
                    'primary_model': models_breakdown[0]['model_name'] if models_breakdown else None,
                    'most_expensive_model': max(models_breakdown, key=lambda x: x['total_cost'])['model_name'] if models_breakdown else None,
                    'most_used_model': max(models_breakdown, key=lambda x: x['query_count'])['model_name'] if models_breakdown else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting user model stats: {str(e)}")
            return {
                'models_breakdown': [],
                'token_breakdown': {
                    'total_input_tokens': 0,
                    'total_output_tokens': 0,
                    'total_tokens': 0,
                    'input_cost': 0.0,
                    'output_cost': 0.0,
                    'total_cost': 0.0
                },
                'summary': {
                    'total_models_used': 0,
                    'primary_model': None,
                    'most_expensive_model': None,
                    'most_used_model': None
                }
            }
    
    def _get_model_input_rate(self, model_name: str) -> float:
        """Get input token rate for a model."""
        from core.utils.cost_calculator import ModelPricing
        pricing = ModelPricing.get_model_pricing(model_name)
        return pricing.get('input_price_per_1k', 0.001)
    
    def _get_model_output_rate(self, model_name: str) -> float:
        """Get output token rate for a model."""
        from core.utils.cost_calculator import ModelPricing
        pricing = ModelPricing.get_model_pricing(model_name)
        return pricing.get('output_price_per_1k', 0.002)
