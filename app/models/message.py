"""Message models for WebSocket communication."""

from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class MessageType(str, Enum):
    """Types of messages that can be sent via WebSocket."""
    
    CHAT = "chat"
    SYSTEM = "system"
    JOIN = "join"
    LEAVE = "leave"
    ERROR = "error"
    DELETE = "delete"
    SYNC = "sync"


class Message(BaseModel):
    """Schema for WebSocket messages."""
    
    type: MessageType = Field(default=MessageType.CHAT)
    content: str = Field(..., min_length=1, max_length=4096)
    sender: str = Field(..., min_length=1, max_length=50)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    room_id: Optional[str] = Field(default=None)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
