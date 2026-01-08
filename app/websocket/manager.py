"""WebSocket connection manager for handling multiple clients."""

from fastapi import WebSocket
from typing import Dict, List, Set
import json
import logging
from app.services.chat import chat_service

logger = logging.getLogger(__name__)



class ConnectionManager:
    """
    Manages WebSocket connections for real-time communication.
    
    Supports:
    - Individual connections
    - Room-based broadcasting
    - Global broadcasting
    """
    
    def __init__(self):
        # All active connections
        self.active_connections: List[WebSocket] = []
        # Connections organized by room
        self.rooms: Dict[str, Set[WebSocket]] = {}
        # Map of WebSocket to username
        self.connection_usernames: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, username: str, room_id: str = "general") -> None:
        """
        Accept a new WebSocket connection and add to a room.
        
        Args:
            websocket: The WebSocket connection
            username: The username of the connecting client
            room_id: The room to join (defaults to 'general')
        """
        await websocket.accept()
        
        # Room persistence (auto-create rooms is still fine)
        await chat_service.get_or_create_room(room_id)
        
        self.active_connections.append(websocket)
        self.connection_usernames[websocket] = username
        
        # Add to room
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(websocket)
        
        logger.info(f"User '{username}' connected to room '{room_id}'")
    
    def disconnect(self, websocket: WebSocket, room_id: str = "general") -> str:
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection to remove
            room_id: The room to leave
            
        Returns:
            The username of the disconnected user
        """
        username = self.connection_usernames.pop(websocket, "Unknown")
        
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if room_id in self.rooms and websocket in self.rooms[room_id]:
            self.rooms[room_id].remove(websocket)
            if not self.rooms[room_id]:
                del self.rooms[room_id]
        
        logger.info(f"User '{username}' disconnected from room '{room_id}'")
        return username
    
    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        """
        Send a message to a specific client.
        
        Args:
            message: The message data to send
            websocket: The target WebSocket connection
        """
        await websocket.send_json(message)
    
    async def broadcast_to_room(self, message: dict, room_id: str) -> None:
        """
        Broadcast a message to all clients in a specific room.
        
        Args:
            message: The message data to broadcast
            room_id: The room to broadcast to
        """
        if room_id not in self.rooms:
            return
            
        disconnected = []
        for connection in self.rooms[room_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                disconnected.append(connection)
        
        # Save message to database (assuming message has content/sender structure)
        # Note: Ideally the route handler calling this knows the sender.
        # But if 'message' is just a dict, we might need to rely on structure.
        # For now, let's assume the caller handles DB saving if strict accuracy is needed,
        # OR we save it here if we can parse it.
        #
        # Better approach: The caller (route) should call chat_service.save_message()
        # BEFORE calling broadcast.
        #
        # However, to be automatic as requested: "everytime a room is created, its stored... persist... store chats"
        # Let's inspect the message.
        
        # Cleaning up disconnected clients
        for conn in disconnected:
            self.disconnect(conn, room_id)
    
    async def broadcast_all(self, message: dict) -> None:
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: The message data to broadcast
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)
    
    def get_room_users(self, room_id: str) -> List[str]:
        """
        Get list of usernames in a room.
        
        Args:
            room_id: The room to query
            
        Returns:
            List of usernames in the room
        """
        if room_id not in self.rooms:
            return []
        
        return [
            self.connection_usernames.get(conn, "Unknown")
            for conn in self.rooms[room_id]
        ]
    
    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self.active_connections)


# Global connection manager instance
# Global connection manager instance
manager = ConnectionManager()

