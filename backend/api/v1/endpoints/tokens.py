"""
Token Usage API endpoints for tracking LLM token consumption.
Provides user-level token usage statistics and limits management.
"""

from typing import Dict, Any, Optional, List, TYPE_CHECKING
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
import logging

if TYPE_CHECKING:
    from models.models import User
else:
    pass

from services.auth_dependencies import get_current_user
from services.token_usage_service import TokenUsageService
from database.connection_manager import get_db_manager

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/tokens", tags=["Token Usage"])

# Pydantic models for request/response
class TokenUsageStatsResponse(BaseModel):
    """Response model for token usage statistics."""
    user_id: str
    summary: Dict[str, Any] = Field(..., description="Overall token usage summary")
    period_stats: Dict[str, Any] = Field(..., description="Statistics for specified period")
    last_updated: Optional[str] = Field(None, description="Last update timestamp")
    generated_at: str = Field(..., description="Response generation timestamp")
    details: Optional[Dict[str, Any]] = Field(None, description="Detailed usage breakdown")

class TokenLimitsResponse(BaseModel):
    """Response model for token usage limits."""
    user_id: str
    limits: Dict[str, int] = Field(..., description="Token usage limits")
    current_usage: Dict[str, int] = Field(..., description="Current token usage")
    remaining: Dict[str, int] = Field(..., description="Remaining token allowance")
    status: Dict[str, bool] = Field(..., description="Limit status flags")

class RateLimitResponse(BaseModel):
    """Response model for rate limit checking."""
    user_id: str
    allowed: bool = Field(..., description="Whether request is allowed")
    limits_status: Dict[str, bool] = Field(..., description="Detailed limit status")
    usage: Dict[str, int] = Field(..., description="Current usage across periods")
    limits: Dict[str, int] = Field(..., description="Configured limits")

# Dependency to get token usage service
async def get_token_usage_service(request: Request) -> TokenUsageService:
    """Get token usage service instance."""
    # Get the initialized db_manager from app state
    db_manager = request.app.state.db_manager
    return TokenUsageService(db_manager)

@router.get(
    "/usage",
    response_model=TokenUsageStatsResponse,
    summary="Get user token usage statistics",
    description="""
    Retrieve detailed token usage statistics for the authenticated user.
    
    - **start_date**: Optional start date for filtering (YYYY-MM-DD format)
    - **end_date**: Optional end date for filtering (YYYY-MM-DD format)  
    - **include_details**: Include daily and model-specific breakdowns
    
    Returns comprehensive token usage statistics including:
    - Total tokens consumed
    - Breakdown by prompt/completion tokens
    - Usage patterns over time
    - Model-specific usage statistics
    """,
    responses={
        200: {"description": "Token usage statistics retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Access forbidden"},
        404: {"description": "User not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_user_token_usage(
    request: Request,
    start_date: Optional[str] = Query(
        None, 
        description="Start date for filtering (YYYY-MM-DD)",
        regex=r"^\d{4}-\d{2}-\d{2}$"
    ),
    end_date: Optional[str] = Query(
        None, 
        description="End date for filtering (YYYY-MM-DD)",
        regex=r"^\d{4}-\d{2}-\d{2}$"
    ),
    include_details: bool = Query(
        False, 
        description="Include detailed daily and model breakdowns"
    ),
    current_user = Depends(get_current_user),
    token_service: TokenUsageService = Depends(get_token_usage_service)
) -> TokenUsageStatsResponse:
    """
    Get token usage statistics for the current user.
    
    Args:
        start_date: Optional start date filter
        end_date: Optional end date filter
        include_details: Include detailed breakdowns
        current_user: Authenticated user
        token_service: Token usage service
        
    Returns:
        Token usage statistics
    """
    try:
        # Get user ID from current_user (handle both dict and object types)
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        # Parse date parameters
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use YYYY-MM-DD"
                )
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use YYYY-MM-DD"
                )
        
        # Validate date range
        if start_dt and end_dt and start_dt > end_dt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date cannot be after end_date"
            )
        
        # Get token usage statistics
        usage_stats = await token_service.get_user_token_usage(
            user_id=user_id,
            start_date=start_dt,
            end_date=end_dt,
            include_details=include_details
        )
        
        if "error" in usage_stats:
            logger.error(
                f"Failed to get token usage for user {user_id}: {usage_stats['error']}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve token usage statistics"
            )
        
        logger.info(
            f"Token usage retrieved for user {user_id}",
            extra={
                "user_id": user_id,
                "start_date": start_date,
                "end_date": end_date,
                "include_details": include_details,
                "total_tokens": usage_stats.get("period_stats", {}).get("total_tokens", 0)
            }
        )
        
        return TokenUsageStatsResponse(**usage_stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error getting token usage for user {user_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get(
    "/limits",
    response_model=TokenLimitsResponse,
    summary="Get user token usage limits",
    description="""
    Retrieve token usage limits and current status for the authenticated user.
    
    Returns information about:
    - Daily, monthly, and hourly token limits
    - Current usage against those limits
    - Remaining token allowances
    - Whether any limits have been exceeded
    """,
    responses={
        200: {"description": "Token limits retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Access forbidden"},
        404: {"description": "User not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_user_token_limits(
    request: Request,
    current_user = Depends(get_current_user),
    token_service: TokenUsageService = Depends(get_token_usage_service)
) -> TokenLimitsResponse:
    """
    Get token usage limits for the current user.
    
    Args:
        current_user: Authenticated user
        token_service: Token usage service
        
    Returns:
        Token usage limits and status
    """
    try:
        # Get user ID from current_user (handle both dict and object types)  
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        
        limits_info = await token_service.get_token_usage_limits(user_id)
        
        if "error" in limits_info:
            logger.error(
                f"Failed to get token limits for user {user_id}: {limits_info['error']}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve token usage limits"
            )
        
        logger.info(
            f"Token limits retrieved for user {user_id}",
            extra={
                "user_id": user_id,
                "daily_limit": limits_info.get("limits", {}).get("daily_limit", 0),
                "monthly_limit": limits_info.get("limits", {}).get("monthly_limit", 0)
            }
        )
        
        return TokenLimitsResponse(**limits_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error getting token limits for user {user_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get(
    "/rate-limit-check",
    response_model=RateLimitResponse,
    summary="Check rate limit status",
    description="""
    Check whether the user has exceeded any rate limits before making a request.
    
    This endpoint helps prevent requests that would exceed:
    - Daily token limit
    - Monthly token limit  
    - Hourly rate limit
    
    Use this to implement client-side rate limiting and user feedback.
    """,
    responses={
        200: {"description": "Rate limit status checked successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Access forbidden"},
        500: {"description": "Internal server error"}
    }
)
async def check_rate_limit(
    request: Request,
    current_user = Depends(get_current_user),
    token_service: TokenUsageService = Depends(get_token_usage_service)
) -> RateLimitResponse:
    """
    Check rate limit status for the current user.
    
    Args:
        current_user: Authenticated user
        token_service: Token usage service
        
    Returns:
        Rate limit status
    """
    try:
        # Get user ID from current_user (handle both dict and object types)
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        
        rate_status = await token_service.check_rate_limit(user_id)
        
        if "error" in rate_status:
            logger.error(
                f"Failed to check rate limit for user {user_id}: {rate_status['error']}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to check rate limit status"
            )
        
        logger.info(
            f"Rate limit checked for user {user_id}",
            extra={
                "user_id": user_id,
                "allowed": rate_status.get("allowed", False),
                "daily_exceeded": rate_status.get("limits_status", {}).get("daily_exceeded", False),
                "monthly_exceeded": rate_status.get("limits_status", {}).get("monthly_exceeded", False),
                "hourly_exceeded": rate_status.get("limits_status", {}).get("hourly_exceeded", False)
            }
        )
        
        return RateLimitResponse(**rate_status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error checking rate limit for user {user_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get(
    "/dashboard",
    summary="Get token usage dashboard data",
    description="""
    Get comprehensive token usage data for dashboard display.
    
    Returns a summary of token usage including:
    - Current month usage and trends
    - Recent activity
    - Usage by model
    - Limit status with visual indicators
    """,
    responses={
        200: {"description": "Dashboard data retrieved successfully"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"}
    }
)
async def get_token_usage_dashboard(
    request: Request,
    current_user = Depends(get_current_user),
    token_service: TokenUsageService = Depends(get_token_usage_service)
) -> Dict[str, Any]:
    """
    Get token usage dashboard data for the current user.
    
    Args:
        current_user: Authenticated user
        token_service: Token usage service
        
    Returns:
        Dashboard data dictionary
    """
    try:
        # Get user ID from current_user (handle both dict and object types)
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        
        # Get current month data
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get usage statistics with details
        usage_stats = await token_service.get_user_token_usage(
            user_id=user_id,
            start_date=month_start,
            end_date=now,
            include_details=True
        )
        
        # Get limits and rate status
        limits_info = await token_service.get_token_usage_limits(user_id)
        rate_status = await token_service.check_rate_limit(user_id)
        
        # Prepare dashboard data
        dashboard_data = {
            "user_id": user_id,
            "current_month": {
                "usage": usage_stats.get("period_stats", {}),
                "limits": limits_info.get("limits", {}),
                "remaining": limits_info.get("remaining", {}),
                "status": limits_info.get("status", {})
            },
            "rate_limit": {
                "allowed": rate_status.get("allowed", True),
                "status": rate_status.get("limits_status", {}),
                "usage": rate_status.get("usage", {})
            },
            "trends": usage_stats.get("details", {}).get("daily_usage", {}),
            "models": usage_stats.get("details", {}).get("model_usage", {}),
            "last_updated": usage_stats.get("last_updated"),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(
            f"Dashboard data retrieved for user {user_id}",
            extra={
                "user_id": user_id,
                "month_usage": dashboard_data["current_month"]["usage"].get("total_tokens", 0),
                "rate_allowed": dashboard_data["rate_limit"]["allowed"]
            }
        )
        
        return dashboard_data
        
    except Exception as e:
        logger.error(
            f"Failed to get dashboard data for user {user_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data"
        )
