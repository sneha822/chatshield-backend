"""Health check endpoints."""

from fastapi import APIRouter
from datetime import datetime

from ..config import settings
from ..websocket.manager import manager

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        Health status of the application
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/stats")
async def get_stats():
    """
    Get server statistics.
    
    Returns:
        Current server statistics including connection count
    """
    return {
        "active_connections": manager.get_connection_count(),
        "active_rooms": len(manager.rooms),
        "timestamp": datetime.utcnow().isoformat()
    }
