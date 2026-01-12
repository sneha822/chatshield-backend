"""Message models for WebSocket communication."""

from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class MessageType(str, Enum):
    """Types of messages that can be sent via WebSocket."""
    
    CHAT = "chat"
    SYSTEM = "system"
    JOIN = "join"
    LEAVE = "leave"
    ERROR = "error"
    DELETE = "delete"
    SYNC = "sync"
    
    # Mute/Warning related message types
    WARNING = "warning"          # User received a toxicity warning
    MUTED = "muted"              # User has been muted
    UNMUTED = "unmuted"          # User has been unmuted (auto or manual)
    MUTE_STATUS = "mute_status"  # Response to mute status check
    MUTE_REJECTED = "mute_rejected"  # Message rejected because user is muted


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


class MuteInfo(BaseModel):
    """Schema for mute information in WebSocket messages."""
    
    is_muted: bool = False
    mute_expires_at: Optional[str] = None  # ISO format UTC timestamp
    remaining_seconds: Optional[int] = None
    warning_count: int = 0
    consecutive_toxic_count: int = 0
    total_mute_count: int = 0
    warnings_until_mute: int = 5
    mute_duration_minutes: int = 5
    toxic_threshold: int = 5

