"""Chat-related REST API endpoints."""

from fastapi import APIRouter
from typing import List

from ..websocket.manager import manager

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/rooms")
async def get_rooms():
    """
    Get list of active chat rooms.
    
    Returns:
        List of active rooms with user counts
    """
    rooms_info = []
    for room_id, connections in manager.rooms.items():
        rooms_info.append({
            "room_id": room_id,
            "user_count": len(connections),
            "users": manager.get_room_users(room_id)
        })
    
    return {"rooms": rooms_info}


@router.get("/rooms/{room_id}/users")
async def get_room_users(room_id: str) -> dict:
    """
    Get users in a specific room.
    
    Args:
        room_id: The room ID to query
        
    Returns:
        List of users in the room
    """
    users = manager.get_room_users(room_id)
    return {
        "room_id": room_id,
        "users": users,
        "count": len(users)
    }
