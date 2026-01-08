"""Service for handling chat-related database operations."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from typing import List
from app.models.sql import User, Room, Message
from app.database import AsyncSessionLocal
import logging

logger = logging.getLogger(__name__)


class ChatService:
    """Service for persisting chat data."""

    async def get_or_create_user(self, username: str) -> User:
        """Get existing user or create a new one."""
        async with AsyncSessionLocal() as session:
            try:
                # Check for existing user
                result = await session.execute(select(User).where(User.username == username))
                user = result.scalar_one_or_none()
                
                if user:
                    return user
                
                # Create new user
                user = User(username=username)
                session.add(user)
                await session.commit()
                await session.refresh(user)
                logger.info(f"Created new user: {username}")
                return user
            except Exception as e:
                logger.error(f"Error getting/creating user {username}: {e}")
                raise

    async def get_or_create_room(self, room_id: str) -> Room:
        """Get existing room or create a new one."""
        async with AsyncSessionLocal() as session:
            try:
                # Check for existing room
                result = await session.execute(select(Room).where(Room.id == room_id))
                room = result.scalar_one_or_none()
                
                if room:
                    return room
                
                # Create new room
                # For now, using room_id as name if not specified
                room = Room(id=room_id, name=room_id.capitalize())
                session.add(room)
                await session.commit()
                await session.refresh(room)
                logger.info(f"Created new room: {room_id}")
                return room
            except Exception as e:
                logger.error(f"Error getting/creating room {room_id}: {e}")
                raise

    async def save_message(self, content: str, username: str, room_id: str, toxicity_scores: dict = None) -> Message:
        """Save a new message to the database."""
        # We need a new session here because we might need to query for user/room first
        # Ideally, we should reuse sessions, but for async/await simplicity in WS handler, 
        # independent sessions are safer to avoid conflicts.
        
        async with AsyncSessionLocal() as session:
            try:
                # Ensure user and room exist (re-querying within transaction for safety)
                user_res = await session.execute(select(User).where(User.username == username))
                user = user_res.scalar_one_or_none()
                if not user:
                    user = User(username=username)
                    session.add(user)
                
                room_res = await session.execute(select(Room).where(Room.id == room_id))
                room = room_res.scalar_one_or_none()
                if not room:
                    room = Room(id=room_id, name=room_id.capitalize())
                    session.add(room)
                
                # Flush to get IDs if new
                await session.flush()
                
                # Create message
                message = Message(
                    content=content,
                    sender_id=user.id,
                    room_id=room.id,
                    toxicity_scores=toxicity_scores
                )
                session.add(message)
                await session.commit()
                logger.debug(f"Saved message from {username} in {room_id}")
                return message
            except Exception as e:
                logger.error(f"Error saving message: {e}")
                await session.rollback()
                pass  # Don't crash WS if DB save fails



    async def create_room(self, room_id: str, name: str) -> Room:
        """Create a new room, error if exists."""
        async with AsyncSessionLocal() as session:
            try:
                # Check for existing room
                result = await session.execute(select(Room).where(Room.id == room_id))
                if result.scalar_one_or_none():
                    raise ValueError(f"Room '{room_id}' already exists")
                
                # Create new room
                room = Room(id=room_id, name=name)
                session.add(room)
                await session.commit()
                await session.refresh(room)
                logger.info(f"Created new room: {room_id}")
                return room
            except Exception as e:
                logger.error(f"Error creating room {room_id}: {e}")
                raise

    async def get_room_messages(self, room_id: str, limit: int = 50) -> List[Message]:
        """Get recent messages for a room."""
        async with AsyncSessionLocal() as session:
            try:
                query = (
                    select(Message)
                    .where(Message.room_id == room_id)
                    .options(selectinload(Message.sender))
                    .order_by(desc(Message.timestamp))
                    .limit(limit)
                )
                result = await session.execute(query)
                messages = result.scalars().all()
                # Reverse to return in chronological order
                return list(reversed(messages))
            except Exception as e:
                logger.error(f"Error fetching messages for room {room_id}: {e}")
                return []


chat_service = ChatService()
