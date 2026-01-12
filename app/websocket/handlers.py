"""WebSocket endpoint handlers."""

from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import json
import logging

from .manager import manager
from ..models import Message, MessageType
from ..services import toxicity_analyzer, mute_service
from ..services.chat import chat_service
from ..core.deps import get_ws_user



logger = logging.getLogger(__name__)


async def websocket_endpoint(websocket: WebSocket, token: str, room_id: str = "general"):
    """
    Main WebSocket endpoint handler.
    
    Handles:
    - User authentication
    - Room joining
    - Message sending with toxicity analysis
    - Mute/warning system for toxic messages
    - Auto-unmute after mute expiry
    """
    # Authenticate
    user = await get_ws_user(token)
    if not user:
        await websocket.close(code=4003, reason="Unauthorized")
        return

    username = user.username

    # Connect the user
    await manager.connect(websocket, username, room_id)
    
    # Check if user was previously muted and send status
    mute_status = await mute_service.check_mute_status(username, room_id)
    
    # If user was just unmuted, notify them
    if mute_status.get("just_unmuted"):
        unmute_message = {
            "type": MessageType.UNMUTED.value,
            "content": "Your mute has expired. You can send messages again.",
            "sender": "System",
            "timestamp": datetime.utcnow().isoformat(),
            "room_id": room_id,
            "mute_info": mute_status
        }
        await manager.send_personal_message(unmute_message, websocket)
    
    # Send current mute status to the connecting user
    status_message = {
        "type": MessageType.MUTE_STATUS.value,
        "content": "",
        "sender": "System",
        "timestamp": datetime.utcnow().isoformat(),
        "room_id": room_id,
        "mute_info": mute_status
    }
    await manager.send_personal_message(status_message, websocket)
    
    # Check if user is new to the room
    is_new_member = await chat_service.join_room(username, room_id)
    
    if is_new_member:
        # Notify room about new user if they just joined (persisted)
        join_message = {
            "type": MessageType.JOIN.value,
            "content": f"{username} has joined the chat",
            "sender": "System",
            "timestamp": datetime.utcnow().isoformat(),
            "room_id": room_id,
            "users": manager.get_room_users(room_id)
        }
        await manager.broadcast_to_room(join_message, room_id)
    else:
        # Just notify about presence update (sync user list)
        sync_message = {
            "type": MessageType.SYNC.value,
            "content": "", # No chat bubble
            "sender": "System",
            "timestamp": datetime.utcnow().isoformat(),
            "room_id": room_id,
            "users": manager.get_room_users(room_id)
        }
        await manager.broadcast_to_room(sync_message, room_id)
    
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
                # First, check if user is muted
                mute_status = await mute_service.check_mute_status(username, room_id)
                
                # If user was just auto-unmuted, notify them
                if mute_status.get("just_unmuted"):
                    unmute_message = {
                        "type": MessageType.UNMUTED.value,
                        "content": "Your mute has expired. You can send messages again.",
                        "sender": "System",
                        "timestamp": datetime.utcnow().isoformat(),
                        "room_id": room_id,
                        "mute_info": mute_status
                    }
                    await manager.send_personal_message(unmute_message, websocket)
                    
                    # Also broadcast to room that user is unmuted
                    room_unmute_message = {
                        "type": MessageType.UNMUTED.value,
                        "content": f"{username}'s mute has expired.",
                        "sender": "System",
                        "timestamp": datetime.utcnow().isoformat(),
                        "room_id": room_id,
                        "username": username
                    }
                    await manager.broadcast_to_room(room_unmute_message, room_id)
                
                # If user is still muted, reject the message
                if mute_status.get("is_muted"):
                    reject_message = {
                        "type": MessageType.MUTE_REJECTED.value,
                        "content": f"You are muted. Please wait {mute_status.get('remaining_seconds', 0)} seconds.",
                        "sender": "System",
                        "timestamp": datetime.utcnow().isoformat(),
                        "room_id": room_id,
                        "mute_info": mute_status
                    }
                    await manager.send_personal_message(reject_message, websocket)
                    continue  # Skip processing this message
                
                # Analyze message for toxicity
                toxicity_scores = toxicity_analyzer.analyze(content)
                is_toxic = toxicity_scores.get("is_toxic", False)
                
                # Process toxicity and update mute/warning status
                mute_result = await mute_service.process_message_toxicity(
                    username=username,
                    room_id=room_id,
                    is_toxic=is_toxic
                )
                
                # Create message with toxicity data
                message = Message(
                    type=MessageType.CHAT,
                    content=content,
                    sender=username,
                    room_id=room_id
                )
                
                # Save to database
                await chat_service.save_message(
                    content=content,
                    username=username,
                    room_id=room_id,
                    toxicity_scores=toxicity_scores
                )

                
                # Build response with toxicity analysis
                message_response = message.model_dump(mode="json")
                message_response["toxicity"] = toxicity_scores
                
                # Broadcast to room with toxicity scores
                await manager.broadcast_to_room(message_response, room_id)
                
                # Handle warning/mute actions
                action = mute_result.get("action", "none")
                
                if action == "warning":
                    # Send warning to the user who sent the toxic message
                    warning_message = {
                        "type": MessageType.WARNING.value,
                        "content": (
                            f"⚠️ Your message was flagged as toxic. "
                            f"Warning {mute_result.get('consecutive_toxic_count')}/{mute_result.get('toxic_threshold')}. "
                            f"You will be muted for {mute_result.get('mute_duration_minutes')} minutes after "
                            f"{mute_result.get('warnings_until_mute')} more toxic messages."
                        ),
                        "sender": "System",
                        "timestamp": datetime.utcnow().isoformat(),
                        "room_id": room_id,
                        "mute_info": mute_result
                    }
                    await manager.send_personal_message(warning_message, websocket)
                    
                elif action == "muted":
                    # Send mute notification to the user
                    mute_message = {
                        "type": MessageType.MUTED.value,
                        "content": (
                            f"🔇 You have been muted for {mute_result.get('mute_duration_minutes')} minutes "
                            f"due to sending {mute_result.get('toxic_threshold')} toxic messages. "
                            f"You will be unmuted at {mute_result.get('mute_expires_at')} UTC."
                        ),
                        "sender": "System",
                        "timestamp": datetime.utcnow().isoformat(),
                        "room_id": room_id,
                        "mute_info": mute_result
                    }
                    await manager.send_personal_message(mute_message, websocket)
                    
                    # Also broadcast to room that user has been muted
                    room_mute_message = {
                        "type": MessageType.MUTED.value,
                        "content": f"{username} has been muted for {mute_result.get('mute_duration_minutes')} minutes.",
                        "sender": "System",
                        "timestamp": datetime.utcnow().isoformat(),
                        "room_id": room_id,
                        "username": username,
                        "mute_expires_at": mute_result.get("mute_expires_at")
                    }
                    await manager.broadcast_to_room(room_mute_message, room_id)
                
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
