"""
Main API router for version 1.
"""
from fastapi import APIRouter

from .endpoints import auth, query, analytics, admin

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(query.router, tags=["Query"])
api_router.include_router(analytics.router, tags=["Analytics"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"]) 