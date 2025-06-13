"""
Analytics endpoints for Text-to-SQL application.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from services.auth_dependencies import get_current_user, get_current_admin_user
from services.auth_service import UserResponse
from services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter()

class AnalyticsRequest(BaseModel):
    start_date: Optional[datetime] = Field(None, description="Start date for analytics")
    end_date: Optional[datetime] = Field(None, description="End date for analytics")
    metric_type: Optional[str] = Field(None, description="Specific metric type to retrieve")

class UsageMetrics(BaseModel):
    total_queries: int
    successful_queries: int
    failed_queries: int
    average_response_time: float
    unique_users: int
    most_used_tables: List[Dict[str, Any]]

class PerformanceMetrics(BaseModel):
    average_query_time: float
    slowest_queries: List[Dict[str, Any]]
    fastest_queries: List[Dict[str, Any]]
    error_rate: float

@router.get("/usage", response_model=UsageMetrics)
async def get_usage_analytics(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Get usage analytics for the current user."""
    try:
        analytics_service: AnalyticsService = request.app.state.analytics_service
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        metrics = await analytics_service.get_user_usage_metrics(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date
        )
        
        return UsageMetrics(
            total_queries=metrics.get("total_queries", 0),
            successful_queries=metrics.get("successful_queries", 0),
            failed_queries=metrics.get("failed_queries", 0),
            average_response_time=metrics.get("average_response_time", 0.0),
            unique_users=1,  # For user-specific metrics, this is always 1
            most_used_tables=metrics.get("most_used_tables", [])
        )
        
    except Exception as e:
        logger.error(f"Failed to get usage analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage analytics"
        )

@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_analytics(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Get performance analytics for the current user."""
    try:
        analytics_service: AnalyticsService = request.app.state.analytics_service
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        metrics = await analytics_service.get_user_performance_metrics(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date
        )
        
        return PerformanceMetrics(
            average_query_time=metrics.get("average_query_time", 0.0),
            slowest_queries=metrics.get("slowest_queries", []),
            fastest_queries=metrics.get("fastest_queries", []),
            error_rate=metrics.get("error_rate", 0.0)
        )
        
    except Exception as e:
        logger.error(f"Failed to get performance analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance analytics"
        )

@router.get("/system/usage", response_model=UsageMetrics)
async def get_system_usage_analytics(
    request: Request,
    current_user: UserResponse = Depends(get_current_admin_user),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Get system-wide usage analytics (admin only)."""
    try:
        analytics_service: AnalyticsService = request.app.state.analytics_service
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        metrics = await analytics_service.get_system_usage_metrics(
            start_date=start_date,
            end_date=end_date
        )
        
        return UsageMetrics(
            total_queries=metrics.get("total_queries", 0),
            successful_queries=metrics.get("successful_queries", 0),
            failed_queries=metrics.get("failed_queries", 0),
            average_response_time=metrics.get("average_response_time", 0.0),
            unique_users=metrics.get("unique_users", 0),
            most_used_tables=metrics.get("most_used_tables", [])
        )
        
    except Exception as e:
        logger.error(f"Failed to get system usage analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system usage analytics"
        )

@router.get("/system/performance", response_model=PerformanceMetrics)
async def get_system_performance_analytics(
    request: Request,
    current_user: UserResponse = Depends(get_current_admin_user),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Get system-wide performance analytics (admin only)."""
    try:
        analytics_service: AnalyticsService = request.app.state.analytics_service
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        metrics = await analytics_service.get_system_performance_metrics(
            start_date=start_date,
            end_date=end_date
        )
        
        return PerformanceMetrics(
            average_query_time=metrics.get("average_query_time", 0.0),
            slowest_queries=metrics.get("slowest_queries", []),
            fastest_queries=metrics.get("fastest_queries", []),
            error_rate=metrics.get("error_rate", 0.0)
        )
        
    except Exception as e:
        logger.error(f"Failed to get system performance analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system performance analytics"
        )

@router.get("/export")
async def export_analytics(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    format: str = "json"
):
    """Export analytics data for the current user."""
    try:
        analytics_service: AnalyticsService = request.app.state.analytics_service
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        data = await analytics_service.export_user_analytics(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            format=format
        )
        
        return {
            "data": data,
            "format": format,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to export analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export analytics data"
        ) 