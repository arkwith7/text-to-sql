"""
Token Usage Service for tracking LLM token consumption per user.
Implements Azure best practices for error handling, logging, and security.
"""

import logging
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from datetime import datetime, timedelta
import json

# TYPE_CHECKING을 사용하여 순환 import 방지
if TYPE_CHECKING:
    from database.connection_manager import DatabaseManager
    from models.models import User, QueryAnalytics, ChatSession, ChatMessage
else:
    # 런타임에는 지연 import 사용
    pass

from sqlalchemy import select, func
from utils.logging_config import setup_logging

logger = logging.getLogger(__name__)

class TokenUsageService:
    """
    Service for tracking and managing LLM token usage per user.
    Follows Azure best practices for security, error handling, and performance.
    """
    
    def __init__(self, db_manager: "DatabaseManager"):
        """
        Initialize Token Usage Service.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
    async def record_token_usage(
        self,
        user_id: str,
        session_id: str,
        message_id: str,
        token_usage: Dict[str, int],
        model_name: str,
        query_type: str = "text_to_sql",
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Record token usage for a specific query.
        
        Args:
            user_id: User ID
            session_id: Chat session ID
            message_id: Message ID
            token_usage: Token usage dict with prompt_tokens, completion_tokens, total_tokens
            model_name: LLM model name
            query_type: Type of query (text_to_sql, chat, etc.)
            additional_metadata: Additional metadata to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate input parameters
            if not all([user_id, session_id, message_id, token_usage]):
                self.logger.error("Missing required parameters for token usage recording")
                return False
            
            # Validate token usage structure
            required_fields = ['prompt_tokens', 'completion_tokens', 'total_tokens']
            if not all(field in token_usage for field in required_fields):
                self.logger.error(f"Invalid token usage structure. Required fields: {required_fields}")
                return False
            
            # 런타임에 import하여 순환 import 방지
            from models.models import QueryAnalytics
            import uuid
            
            # Prepare event data
            event_data = {
                "user_id": user_id,
                "session_id": session_id,
                "message_id": message_id,
                "token_usage": token_usage,
                "model_name": model_name,
                "query_type": query_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if additional_metadata:
                event_data["metadata"] = additional_metadata
            
            # Get database session
            async with self.db_manager.get_session("app") as session:
                # Create analytics record with token information
                analytics_record = QueryAnalytics(
                    user_id=user_id,
                    query_id=str(uuid.uuid4()),
                    question="Token usage tracking",
                    sql_query="",
                    execution_time=0.0,
                    row_count=0,
                    success=True,
                    error_message=None,
                    # Store token usage in dedicated columns
                    prompt_tokens=token_usage.get("prompt_tokens", 0),
                    completion_tokens=token_usage.get("completion_tokens", 0),
                    total_tokens=token_usage.get("total_tokens", 0),
                    llm_model=model_name,
                    llm_cost_estimate=0.0,  # Could be calculated based on model pricing
                    created_at=datetime.utcnow()
                )
                
                session.add(analytics_record)
                # Commit is handled by the context manager
                
                # Update user's token usage summary
                await self._update_user_token_summary(session, user_id, token_usage)
                
                self.logger.info(
                    f"Token usage recorded successfully",
                    extra={
                        "user_id": user_id,
                        "session_id": session_id,
                        "message_id": message_id,
                        "total_tokens": token_usage.get("total_tokens", 0),
                        "model_name": model_name
                    }
                )
                
                return True
                
        except Exception as e:
            self.logger.error(
                f"Failed to record token usage: {str(e)}",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "error": str(e)
                }
            )
            return False
    
    async def _update_user_token_summary(
        self,
        session,  # 타입 힌트 제거하여 순환 import 방지
        user_id: str,
        token_usage: Dict[str, int]
    ) -> None:
        """
        Update user's token usage summary in the user record.
        
        Args:
            session: Database session
            user_id: User ID
            token_usage: Token usage to add
        """
        try:
            # 런타임에 import하여 순환 import 방지
            from models.models import User
            
            # Get user record
            user = await session.get(User, user_id)
            if not user:
                self.logger.warning(f"User not found for token usage update: {user_id}")
                return
            
            # Initialize or update token usage summary
            if not user.preferences:
                user.preferences = {}
            
            if "token_usage" not in user.preferences:
                user.preferences["token_usage"] = {
                    "total_tokens": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "last_updated": datetime.utcnow().isoformat()
                }
            
            # Update token counts
            user.preferences["token_usage"]["total_tokens"] += token_usage.get("total_tokens", 0)
            user.preferences["token_usage"]["prompt_tokens"] += token_usage.get("prompt_tokens", 0)
            user.preferences["token_usage"]["completion_tokens"] += token_usage.get("completion_tokens", 0)
            user.preferences["token_usage"]["last_updated"] = datetime.utcnow().isoformat()
            
            # Mark as modified for SQLAlchemy to detect changes
            user.preferences = user.preferences.copy()
            
            # Commit is handled by the context manager
            
        except Exception as e:
            self.logger.error(f"Failed to update user token summary: {str(e)}")
            raise
    
    async def get_user_token_usage(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_details: bool = False
    ) -> Dict[str, Any]:
        """
        Get user's token usage statistics.
        
        Args:
            user_id: User ID
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            include_details: Include detailed usage breakdown
            
        Returns:
            Token usage statistics
        """
        try:
            # 런타임에 import하여 순환 import 방지
            from models.models import User, QueryAnalytics
            
            async with self.db_manager.get_session("app") as session:
                # Get user's total token usage from preferences
                user = await session.get(User, user_id)
                if not user:
                    return {"error": "User not found"}
                
                user_token_summary = user.preferences.get("token_usage", {}) if user.preferences else {}
                
                # Prepare base query for detailed analytics
                stmt = select(QueryAnalytics).filter(
                    QueryAnalytics.user_id == user_id,
                    QueryAnalytics.total_tokens.isnot(None),
                    QueryAnalytics.total_tokens > 0
                )
                
                # Apply date filters if provided
                if start_date:
                    stmt = stmt.filter(QueryAnalytics.created_at >= start_date)
                if end_date:
                    stmt = stmt.filter(QueryAnalytics.created_at <= end_date)
                
                # Get basic statistics
                total_queries = len((await session.execute(stmt)).scalars().all())
                
                # Calculate usage statistics from detailed records
                detailed_usage = {
                    "total_tokens": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "query_count": 0,
                    "models_used": set()
                }
                
                if include_details:
                    result = await session.execute(stmt)
                    records = result.scalars().all()
                    daily_usage = {}
                    model_usage = {}
                    
                    for record in records:
                        # Aggregate totals from token columns
                        detailed_usage["total_tokens"] += record.total_tokens or 0
                        detailed_usage["prompt_tokens"] += record.prompt_tokens or 0
                        detailed_usage["completion_tokens"] += record.completion_tokens or 0
                        detailed_usage["query_count"] += 1
                        
                        model_name = record.llm_model or "unknown"
                        detailed_usage["models_used"].add(model_name)
                        
                        # Daily breakdown
                        day_key = record.created_at.strftime("%Y-%m-%d")
                        if day_key not in daily_usage:
                            daily_usage[day_key] = {"total_tokens": 0, "query_count": 0}
                        daily_usage[day_key]["total_tokens"] += record.total_tokens or 0
                        daily_usage[day_key]["query_count"] += 1
                        
                        # Model breakdown
                        if model_name not in model_usage:
                            model_usage[model_name] = {"total_tokens": 0, "query_count": 0}
                        model_usage[model_name]["total_tokens"] += record.total_tokens or 0
                        model_usage[model_name]["query_count"] += 1
                    
                    detailed_usage["models_used"] = list(detailed_usage["models_used"])
                
                # Prepare response
                response = {
                    "user_id": user_id,
                    "summary": user_token_summary,
                    "period_stats": {
                        "start_date": start_date.isoformat() if start_date else None,
                        "end_date": end_date.isoformat() if end_date else None,
                        "total_queries": total_queries,
                        **detailed_usage
                    },
                    "last_updated": user_token_summary.get("last_updated"),
                    "generated_at": datetime.utcnow().isoformat()
                }
                
                if include_details:
                    response["details"] = {
                        "daily_usage": daily_usage,
                        "model_usage": model_usage
                    }
                
                return response
                
        except Exception as e:
            self.logger.error(f"Failed to get user token usage: {str(e)}")
            return {"error": str(e)}
    
    async def get_token_usage_limits(self, user_id: str) -> Dict[str, Any]:
        """
        Get token usage limits for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Token usage limits and current status
        """
        try:
            # 런타임에 import하여 순환 import 방지
            from models.models import User
            
            async with self.db_manager.get_session("app") as session:
                user = await session.get(User, user_id)
                if not user:
                    return {"error": "User not found"}
                
                # Default limits (could be configurable per user role/plan)
                default_limits = {
                    "daily_limit": 10000,  # tokens per day
                    "monthly_limit": 100000,  # tokens per month
                    "rate_limit": 1000  # tokens per hour
                }
                
                user_limits = user.preferences.get("token_limits", default_limits) if user.preferences else default_limits
                current_usage = user.preferences.get("token_usage", {}) if user.preferences else {}
                
                # Calculate usage for today and this month
                today = datetime.utcnow().date()
                this_month = datetime.utcnow().replace(day=1).date()
                
                daily_usage = await self._calculate_usage_for_period(
                    user_id, today, today + timedelta(days=1)
                )
                monthly_usage = await self._calculate_usage_for_period(
                    user_id, this_month, datetime.utcnow().date() + timedelta(days=1)
                )
                
                return {
                    "user_id": user_id,
                    "limits": user_limits,
                    "current_usage": {
                        "total": current_usage.get("total_tokens", 0),
                        "daily": daily_usage,
                        "monthly": monthly_usage
                    },
                    "remaining": {
                        "daily": max(0, user_limits["daily_limit"] - daily_usage),
                        "monthly": max(0, user_limits["monthly_limit"] - monthly_usage)
                    },
                    "status": {
                        "daily_exceeded": daily_usage >= user_limits["daily_limit"],
                        "monthly_exceeded": monthly_usage >= user_limits["monthly_limit"]
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get token usage limits: {str(e)}")
            return {"error": str(e)}
    
    async def _calculate_usage_for_period(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """
        Calculate token usage for a specific period.
        
        Args:
            user_id: User ID
            start_date: Start date
            end_date: End date
            
        Returns:
            Total tokens used in the period
        """
        try:
            # 런타임에 import하여 순환 import 방지
            from models.models import QueryAnalytics
            
            async with self.db_manager.get_session("app") as session:
                # Query analytics records for the period
                stmt = select(QueryAnalytics).filter(
                    QueryAnalytics.user_id == user_id,
                    QueryAnalytics.created_at >= start_date,
                    QueryAnalytics.created_at < end_date,
                    QueryAnalytics.total_tokens.isnot(None),
                    QueryAnalytics.total_tokens > 0
                )
                
                result = await session.execute(stmt)
                records = result.scalars().all()
                total_tokens = 0
                
                for record in records:
                    total_tokens += record.total_tokens or 0
                
                return total_tokens
                
        except Exception as e:
            self.logger.error(f"Failed to calculate usage for period: {str(e)}")
            return 0
    
    async def check_rate_limit(self, user_id: str) -> Dict[str, Any]:
        """
        Check if user has exceeded rate limits.
        
        Args:
            user_id: User ID
            
        Returns:
            Rate limit status
        """
        try:
            limits_info = await self.get_token_usage_limits(user_id)
            
            if "error" in limits_info:
                return limits_info
            
            # Check hourly rate limit
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            hourly_usage = await self._calculate_usage_for_period(
                user_id, one_hour_ago, datetime.utcnow()
            )
            
            rate_limit = limits_info["limits"]["rate_limit"]
            daily_exceeded = limits_info["status"]["daily_exceeded"]
            monthly_exceeded = limits_info["status"]["monthly_exceeded"]
            hourly_exceeded = hourly_usage >= rate_limit
            
            return {
                "user_id": user_id,
                "allowed": not (daily_exceeded or monthly_exceeded or hourly_exceeded),
                "limits_status": {
                    "daily_exceeded": daily_exceeded,
                    "monthly_exceeded": monthly_exceeded,
                    "hourly_exceeded": hourly_exceeded
                },
                "usage": {
                    "hourly": hourly_usage,
                    "daily": limits_info["current_usage"]["daily"],
                    "monthly": limits_info["current_usage"]["monthly"]
                },
                "limits": limits_info["limits"]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to check rate limit: {str(e)}")
            return {"error": str(e), "allowed": False}
    
    async def record_usage(
        self,
        user_id: str,
        session_id: str,
        question: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int
    ) -> bool:
        """
        Simple wrapper for recording token usage from LangChain Agent.
        
        Args:
            user_id: User ID
            session_id: Session ID
            question: Original question
            model_name: Model name
            prompt_tokens: Input tokens
            completion_tokens: Output tokens
            total_tokens: Total tokens
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import uuid
            
            token_usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }
            
            message_id = str(uuid.uuid4())
            
            # 기존 record_token_usage 메서드 호출
            return await self.record_token_usage(
                user_id=user_id,
                session_id=session_id,
                message_id=message_id,
                token_usage=token_usage,
                model_name=model_name,
                query_type="text_to_sql",
                additional_metadata={"question": question}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to record usage: {str(e)}")
            return False
