"""WebSocket endpoint handlers."""

from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import json
import logging

from .manager import manager
from ..models import Message, MessageType
from ..services import toxicity_analyzer

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
                content = message_data.get("content", "")
                
            except json.JSONDecodeError:
                # Handle plain text messages
                content = data
            
            try:
                # Analyze message for toxicity
                toxicity_scores = toxicity_analyzer.analyze(content)
                
                # Create message with toxicity data
                message = Message(
                    type=MessageType.CHAT,
                    content=content,
                    sender=username,
                    room_id=room_id
                )
                
                # Build response with toxicity analysis
                message_response = message.model_dump(mode="json")
                message_response["toxicity"] = toxicity_scores
                
                # Broadcast to room with toxicity scores
                await manager.broadcast_to_room(message_response, room_id)
                
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
