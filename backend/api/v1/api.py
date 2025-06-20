"""
Main API router for v1 endpoints.
"""

from fastapi import APIRouter
from .endpoints import auth, query, schema, chat, analytics, admin, tokens, connections

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(query.router, prefix="/query", tags=["AI Query"])
api_router.include_router(schema.router, prefix="/schema", tags=["Schema"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(tokens.router, prefix="/tokens", tags=["Token Usage"])
api_router.include_router(connections.router, prefix="/connections", tags=["Database Connections"]) 