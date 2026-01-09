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

    async def delete_message(self, message_id: int, user_id: int) -> bool:
        """
        Delete a message if the user is the valid author.
        
        Args:
            message_id: ID of the message to delete
            user_id: ID of the user attempting deletion
            
        Returns:
            True if deleted, False if not found or unauthorized
        """
        async with AsyncSessionLocal() as session:
            try:
                # Find the message
                result = await session.execute(
                    select(Message).where(Message.id == message_id)
                )
                message = result.scalar_one_or_none()
                
                if not message:
                    return False
                
                # Check authorship
                if message.sender_id != user_id:
                    logger.warning(f"User {user_id} attempted to delete message {message_id} but is not the author")
                    return False
                
                # Delete message
                await session.delete(message)
                await session.commit()
                logger.info(f"Message {message_id} deleted by user {user_id}")
                return True
                
            except Exception as e:
                logger.error(f"Error deleting message {message_id}: {e}")
                await session.rollback()
                raise

    async def join_room(self, username: str, room_id: str) -> bool:
        """
        Add user to room if not already a member.
        
        Returns:
            True if user was newly added (joined for first time),
            False if user was already a member.
        """
        async with AsyncSessionLocal() as session:
            try:
                # Get user and room (eager load appropriately if needed, but here simple fetch)
                user = await self._get_user_by_username(session, username)
                room = await self._get_room_by_id(session, room_id)
                
                if not user or not room:
                    # Should inherently exist if we reached here via WS logic usually, 
                    # better to ensure they exist.
                    if not user:
                       user = await self._create_user_internal(session, username)
                    if not room:
                       room = await self._create_room_internal(session, room_id)
                
                # Check strict membership
                # We need to load user's rooms to check efficiently or query association
                # re-fetching user with rooms loaded
                stmt = select(User).where(User.id == user.id).options(selectinload(User.rooms))
                result = await session.execute(stmt)
                user_loaded = result.scalar_one()
                
                # Check if already in room
                for r in user_loaded.rooms:
                    if r.id == room_id:
                        return False # Already a member
                
                # Add to room
                # We need to attach the specific room object bound to this session
                # user_loaded.rooms.append(room) -- room needs to be in session or merged
                # Since 'room' was fetched in this session potentially, or we re-fetch it.
                # Simplest: use list append
                
                # Re-fetch room to be sure it's attached to this session object (though it should be)
                # Actually user_loaded.rooms is a list.
                # Ensure we append the room object
                user_loaded.rooms.append(room)
                
                await session.commit()
                logger.info(f"User {username} joined room {room_id}")
                return True
                
            except Exception as e:
                logger.error(f"Error joining room {username} -> {room_id}: {e}")
                await session.rollback()
                raise

    async def get_user_rooms(self, username: str) -> List[Room]:
        """Get all rooms a user has joined."""
        async with AsyncSessionLocal() as session:
            try:
                stmt = select(User).where(User.username == username).options(selectinload(User.rooms))
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                
                if user:
                    return user.rooms
                return []
            except Exception as e:
                logger.error(f"Error getting rooms for user {username}: {e}")
                return []

    # Helper methods for internal session reuse to avoid code duplication
    # Ideally refactor get_or_create_user but for now keep backward compat 
    # and just add helpers
    
    async def _get_user_by_username(self, session, username):
        result = await session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
        
    async def _get_room_by_id(self, session, room_id):
        result = await session.execute(select(Room).where(Room.id == room_id))
        return result.scalar_one_or_none()
        
    async def _create_user_internal(self, session, username):
        user = User(username=username)
        session.add(user)
        # We don't commit here immediately if part of larger transaction logic, but usually we flush
        await session.flush() 
        return user
        
    async def _create_room_internal(self, session, room_id):
        room = Room(id=room_id, name=room_id.capitalize())
        session.add(room)
        await session.flush()
        return room


chat_service = ChatService()
