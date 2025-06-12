"""
API routes for analytics and system metrics.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth.dependencies import get_current_user
from app.analytics.service import AnalyticsService
from pydantic import BaseModel

class AnalyticsResponse(BaseModel):
    user_analytics: Dict[str, Any]
    system_metrics: Dict[str, Any]

router = APIRouter()

@router.get("/analytics", response_model=AnalyticsResponse, tags=["Analytics"])
async def get_analytics(
    request: Request,
    current_user=Depends(get_current_user)
):
    """Get user and system analytics."""
    analytics_service: AnalyticsService = request.app.state.analytics_service
        
    try:
        user_analytics = await analytics_service.get_user_analytics(current_user["id"])
        system_metrics = await analytics_service.get_system_metrics()
        
        return AnalyticsResponse(
            user_analytics=user_analytics,
            system_metrics=system_metrics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analytics: {str(e)}") 