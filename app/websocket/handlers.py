"""WebSocket endpoint handlers."""

from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import json
import logging

from .manager import manager
from ..models import Message, MessageType

logger = logging.getLogger(__name__)


async def websocket_endpoint(websocket: WebSocket, username: str, room_id: str = "general"):
    """
    Main WebSocket endpoint handler.
    
    Args:
        websocket: The WebSocket connection
        username: The username of the connecting client
        room_id: The room to join
    """
    # Connect the user
    await manager.connect(websocket, username, room_id)
    
    # Notify room about new user
    join_message = {
        "type": MessageType.JOIN.value,
        "content": f"{username} has joined the chat",
        "sender": "System",
        "timestamp": datetime.utcnow().isoformat(),
        "room_id": room_id,
        "users": manager.get_room_users(room_id)
    }
    await manager.broadcast_to_room(join_message, room_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                
                # Validate and create message
                message = Message(
                    type=MessageType.CHAT,
                    content=message_data.get("content", ""),
                    sender=username,
                    room_id=room_id
                )
                
                # Broadcast to room
                await manager.broadcast_to_room(
                    message.model_dump(mode="json"),
                    room_id
                )
                
            except json.JSONDecodeError:
                # Handle plain text messages
                message = Message(
                    type=MessageType.CHAT,
                    content=data,
                    sender=username,
                    room_id=room_id
                )
                await manager.broadcast_to_room(
                    message.model_dump(mode="json"),
                    room_id
                )
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                error_message = {
                    "type": MessageType.ERROR.value,
                    "content": "Failed to process message",
                    "sender": "System",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await manager.send_personal_message(error_message, websocket)
                
    except WebSocketDisconnect:
        # Handle disconnection
        disconnected_user = manager.disconnect(websocket, room_id)
        
        leave_message = {
            "type": MessageType.LEAVE.value,
            "content": f"{disconnected_user} has left the chat",
            "sender": "System",
            "timestamp": datetime.utcnow().isoformat(),
            "room_id": room_id,
            "users": manager.get_room_users(room_id)
        }
        await manager.broadcast_to_room(leave_message, room_id)
