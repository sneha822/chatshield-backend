"""Chat-related REST API endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from pydantic import BaseModel
from app.models.sql import User

from ..websocket.manager import manager
from ..services.chat import chat_service
from ..core.deps import get_current_user

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


@router.get("/my-rooms")
async def get_my_rooms(current_user: User = Depends(get_current_user)):
    """
    Get list of rooms the current user has joined.
    """
    rooms = await chat_service.get_user_rooms(current_user.username)
    
    return {
        "count": len(rooms),
        "rooms": [
            {
                "id": r.id,
                "name": r.name,
                "created_at": r.created_at
            } for r in rooms
        ]
    }


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


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: int, 
    current_user: User = Depends(get_current_user)
):
    """
    Delete a specific message.
    Only the author of the message can delete it.
    """
    success = await chat_service.delete_message(message_id, current_user.id)
    
    if not success:
        # We use 403 for unauthorized/not found to avoid leaking existence, 
        # or 404/403 split if we checked existence separately.
        # chat_service.delete_message returns False for both mismatch and not found currently to be safe.
        # For better UX, we might want to know why, but security-wise this is okay.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Message not found or you are not the author"
        )

