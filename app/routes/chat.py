"""Chat-related REST API endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from pydantic import BaseModel
from app.models.sql import User

from ..websocket.manager import manager
from ..services.chat import chat_service
from ..services.mute import mute_service
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
                "created_at": r.created_at,
                "creator_id": r.creator_id,
                "is_creator": r.creator_id == current_user.id
            } for r in rooms
        ]
    }


@router.get("/rooms/{room_id}")
async def get_room(
    room_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get room details including whether current user is the creator.
    """
    room = await chat_service.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return {
        "id": room.id,
        "name": room.name,
        "created_at": room.created_at,
        "creator_id": room.creator_id,
        "creator_username": room.creator.username if room.creator else None,
        "is_creator": room.creator_id == current_user.id
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
async def create_room(
    request: CreateRoomRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new chat room.
    Fails if room_id already exists.
    """
    try:
        room = await chat_service.create_room(request.room_id, request.name, current_user.id)
        return {
            "id": room.id,
            "name": room.name,
            "created_at": room.created_at,
            "creator_id": room.creator_id,
            "is_creator": True
        }
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
    room_id = await chat_service.delete_message(message_id, current_user.id)
    
    if not room_id:
        # We use 403 for unauthorized/not found to avoid leaking existence, 
        # or 404/403 split if we checked existence separately.
        # chat_service.delete_message returns None for both mismatch and not found currently to be safe.
        # For better UX, we might want to know why, but security-wise this is okay.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Message not found or you are not the author"
        )
        
    # Broadcast deletion to the room via WebSocket
    from app.models.message import MessageType
    from datetime import datetime
    
    delete_event = {
        "type": MessageType.DELETE.value,
        "message_id": message_id,
        "room_id": room_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await manager.broadcast_to_room(delete_event, room_id)


@router.get("/mute-status/{room_id}")
async def get_mute_status(
    room_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get the current user's mute status in a specific room.
    
    Returns:
        Mute status info including:
        - is_muted: Whether user is currently muted
        - mute_expires_at: When the mute expires (UTC ISO timestamp)
        - remaining_seconds: Seconds until unmute
        - warning_count: Total warnings received
        - consecutive_toxic_count: Current consecutive toxic messages
        - total_mute_count: How many times user has been muted in this room
    """
    mute_status = await mute_service.check_mute_status(
        username=current_user.username,
        room_id=room_id
    )
    
    return {
        "username": current_user.username,
        "room_id": room_id,
        **mute_status
    }


@router.get("/mute-stats")
async def get_mute_stats(
    room_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Get the current user's mute/warning statistics.
    
    If room_id is provided, returns stats for that specific room.
    Otherwise, returns aggregate stats across all rooms.
    
    Returns:
        User statistics including warnings and mutes
    """
    stats = await mute_service.get_user_stats(
        username=current_user.username,
        room_id=room_id
    )
    
    return stats


@router.get("/rooms/{room_id}/muted-users")
async def get_muted_users(
    room_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get all currently muted users in a room.
    Only the room creator can access this endpoint.
    """
    # Check if room exists and user is creator
    room = await chat_service.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the room creator can view muted users"
        )
    
    muted_users = await mute_service.get_muted_users(room_id)
    
    return {
        "room_id": room_id,
        "count": len(muted_users),
        "muted_users": muted_users
    }


@router.post("/rooms/{room_id}/unmute/{username}")
async def unmute_user(
    room_id: str,
    username: str,
    current_user: User = Depends(get_current_user)
):
    """
    Manually unmute a user in a room.
    Only the room creator can unmute users.
    """
    # Check if room exists and user is creator
    room = await chat_service.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the room creator can unmute users"
        )
    
    success = await mute_service.unmute_user(username, room_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="User not found or not currently muted"
        )
    
    # Broadcast unmute to the room
    from app.models.message import MessageType
    from datetime import datetime
    
    unmute_event = {
        "type": MessageType.UNMUTED.value,
        "content": f"{username} has been unmuted by the room admin.",
        "sender": "System",
        "room_id": room_id,
        "username": username,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await manager.broadcast_to_room(unmute_event, room_id)
    
    return {
        "success": True,
        "message": f"User {username} has been unmuted",
        "room_id": room_id,
        "username": username
    }

