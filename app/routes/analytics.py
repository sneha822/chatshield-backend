"""API endpoints for analytics."""

from fastapi import APIRouter, Depends, HTTPException
from app.services.analytics import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/rooms/{room_id}")
async def get_room_analytics(room_id: str):
    """
    Get analytics data for a specific room.
    """
    result = await analytics_service.get_room_analytics(room_id)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result
