"""SQLAlchemy models for the application."""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Float, JSON, Table, Column, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


# Association table for User <-> Room many-to-many relationship
user_rooms = Table(
    "user_rooms",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("room_id", String, ForeignKey("rooms.id"), primary_key=True),
    Column("joined_at", DateTime, default=datetime.utcnow)
)


class User(Base):
    """User model."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    messages: Mapped[List["Message"]] = relationship(back_populates="sender")
    rooms: Mapped[List["Room"]] = relationship(
        secondary=user_rooms, 
        back_populates="users",
        lazy="selectin" # Eager load rooms for user
    )
    created_rooms: Mapped[List["Room"]] = relationship(back_populates="creator", foreign_keys="Room.creator_id")
    mutes: Mapped[List["UserMute"]] = relationship(back_populates="user")


class Room(Base):
    """Chat room model."""
    __tablename__ = "rooms"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # Using slug/name as ID
    name: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Creator of the room
    creator_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    creator: Mapped[Optional["User"]] = relationship(back_populates="created_rooms", foreign_keys=[creator_id])
    messages: Mapped[List["Message"]] = relationship(back_populates="room")
    users: Mapped[List["User"]] = relationship(
        secondary=user_rooms, 
        back_populates="rooms",
        lazy="selectin"
    )
    mutes: Mapped[List["UserMute"]] = relationship(back_populates="room")


class Message(Base):
    """Message model to store chat history."""
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content: Mapped[str] = mapped_column(String(4096))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Toxicity scores stored as JSON
    toxicity_scores: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Foreign keys
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    room_id: Mapped[str] = mapped_column(String, ForeignKey("rooms.id"))

    # Relationships
    sender: Mapped["User"] = relationship(back_populates="messages")
    room: Mapped["Room"] = relationship(back_populates="messages")


class UserMute(Base):
    """
    Model to track user mutes and warnings per room.
    
    When a user sends 5 consecutive toxic messages in a room,
    they get muted for 5 minutes. All times stored in UTC.
    """
    __tablename__ = "user_mutes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    room_id: Mapped[str] = mapped_column(String, ForeignKey("rooms.id"), index=True)
    
    # Warning tracking
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    consecutive_toxic_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Mute status
    is_muted: Mapped[bool] = mapped_column(Boolean, default=False)
    muted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    mute_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Tracking timestamps (all UTC)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Total mute count (how many times user has been muted in this room)
    total_mute_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="mutes")
    room: Mapped["Room"] = relationship(back_populates="mutes")
