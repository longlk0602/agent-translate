"""
Main API router
"""

from fastapi import APIRouter
from api.v1.endpoints.translation import router as translation_router
from api.v1.endpoints.sessions import router as sessions_router

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(translation_router, prefix="/api/v1")
api_router.include_router(sessions_router, prefix="/api/v1")

__all__ = ["api_router"]
