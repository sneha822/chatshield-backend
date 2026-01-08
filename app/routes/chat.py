"""Chat-related REST API endpoints."""

from fastapi import APIRouter, HTTPException, status
from typing import List
from pydantic import BaseModel

from ..websocket.manager import manager
from ..services.chat import chat_service

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


class CreateRoomRequest(BaseModel):
    """Request model for creating a room."""
    room_id: str
    name: str


@router.post("/rooms", status_code=status.HTTP_201_CREATED)
async def create_room(request: CreateRoomRequest):
    """
    Create a new chat room.
    Fails if room_id already exists.
    """
    try:
        room = await chat_service.create_room(request.room_id, request.name)
        return {"id": room.id, "name": room.name, "created_at": room.created_at}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/rooms/{room_id}/messages")
async def get_room_messages(room_id: str, limit: int = 50):
    """
    Get recent messages for a specific room.
    """
    messages = await chat_service.get_room_messages(room_id, limit)
    
    return {
        "room_id": room_id,
        "count": len(messages),
        "messages": [
            {
                "id": m.id,
                "content": m.content,
                "sender": m.sender.username, # Uses eager loaded relationship
                "timestamp": m.timestamp,
                "toxicity": m.toxicity_scores
            } for m in messages
        ]
    }
