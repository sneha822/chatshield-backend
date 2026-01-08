"""SQLAlchemy models for the application."""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    """User model."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    messages: Mapped[List["Message"]] = relationship(back_populates="sender")


class Room(Base):
    """Chat room model."""
    __tablename__ = "rooms"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # Using slug/name as ID
    name: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    messages: Mapped[List["Message"]] = relationship(back_populates="room")


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
