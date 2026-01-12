"""Service for handling user muting and warning system.

This service manages:
- Tracking cumulative toxic messages per user per room
- Muting users for 5 minutes after 10 toxic messages
- Checking mute status and auto-unmuting after expiry
- Warning count tracking
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.sql import User, UserMute
import logging

logger = logging.getLogger(__name__)

# Configuration constants
TOXIC_THRESHOLD = 5  # Number of toxic messages before mute
MUTE_DURATION_MINUTES = 5  # Duration of mute in minutes


class MuteService:
    """
    Service for managing user mutes and warnings.
    
    Flow:
    1. User sends a message
    2. If message is toxic, increment consecutive_toxic_count
    3. If message is NOT toxic, reset consecutive_toxic_count to 0
    4. If consecutive_toxic_count reaches TOXIC_THRESHOLD (5):
       - Mute user for MUTE_DURATION_MINUTES (5 minutes)
       - Reset consecutive_toxic_count to 0
       - Increment warning_count and total_mute_count
    5. When checking if user can send messages:
       - Check if muted and if mute has expired
       - If expired, auto-unmute
    """

    async def get_or_create_user_mute(self, username: str, room_id: str) -> UserMute:
        """
        Get existing UserMute record or create a new one.
        
        Args:
            username: The username
            room_id: The room ID
            
        Returns:
            UserMute record for this user in this room
        """
        async with AsyncSessionLocal() as session:
            try:
                # Get user
                user_result = await session.execute(
                    select(User).where(User.username == username)
                )
                user = user_result.scalar_one_or_none()
                
                if not user:
                    logger.warning(f"User {username} not found")
                    return None
                
                # Check for existing UserMute
                mute_result = await session.execute(
                    select(UserMute).where(
                        and_(
                            UserMute.user_id == user.id,
                            UserMute.room_id == room_id
                        )
                    )
                )
                user_mute = mute_result.scalar_one_or_none()
                
                if user_mute:
                    return user_mute
                
                # Create new UserMute record
                user_mute = UserMute(
                    user_id=user.id,
                    room_id=room_id,
                    warning_count=0,
                    consecutive_toxic_count=0,
                    is_muted=False,
                    total_mute_count=0
                )
                session.add(user_mute)
                await session.commit()
                await session.refresh(user_mute)
                logger.info(f"Created UserMute record for {username} in room {room_id}")
                return user_mute
                
            except Exception as e:
                logger.error(f"Error getting/creating UserMute for {username} in {room_id}: {e}")
                await session.rollback()
                raise

    async def check_mute_status(self, username: str, room_id: str) -> Dict[str, Any]:
        """
        Check if a user is currently muted in a room.
        Auto-unmutes if the mute has expired.
        
        Args:
            username: The username
            room_id: The room ID
            
        Returns:
            Dictionary with mute status info:
            {
                "is_muted": bool,
                "mute_expires_at": datetime or None,
                "remaining_seconds": int or None,
                "warning_count": int,
                "consecutive_toxic_count": int,
                "total_mute_count": int,
                "just_unmuted": bool  # True if we just auto-unmuted
            }
        """
        async with AsyncSessionLocal() as session:
            try:
                # Get user
                user_result = await session.execute(
                    select(User).where(User.username == username)
                )
                user = user_result.scalar_one_or_none()
                
                if not user:
                    return {
                        "is_muted": False,
                        "mute_expires_at": None,
                        "remaining_seconds": None,
                        "warning_count": 0,
                        "consecutive_toxic_count": 0,
                        "total_mute_count": 0,
                        "just_unmuted": False
                    }
                
                # Get UserMute record
                mute_result = await session.execute(
                    select(UserMute).where(
                        and_(
                            UserMute.user_id == user.id,
                            UserMute.room_id == room_id
                        )
                    )
                )
                user_mute = mute_result.scalar_one_or_none()
                
                if not user_mute:
                    return {
                        "is_muted": False,
                        "mute_expires_at": None,
                        "remaining_seconds": None,
                        "warning_count": 0,
                        "consecutive_toxic_count": 0,
                        "total_mute_count": 0,
                        "just_unmuted": False
                    }
                
                just_unmuted = False
                now = datetime.utcnow()
                
                # Check if mute has expired
                if user_mute.is_muted and user_mute.mute_expires_at:
                    if now >= user_mute.mute_expires_at:
                        # Auto-unmute
                        user_mute.is_muted = False
                        user_mute.muted_at = None
                        user_mute.mute_expires_at = None
                        user_mute.consecutive_toxic_count = 0  # Reset on unmute
                        await session.commit()
                        just_unmuted = True
                        logger.info(f"Auto-unmuted {username} in room {room_id}")
                
                # Calculate remaining time if still muted
                remaining_seconds = None
                if user_mute.is_muted and user_mute.mute_expires_at:
                    remaining = (user_mute.mute_expires_at - now).total_seconds()
                    remaining_seconds = max(0, int(remaining))
                
                return {
                    "is_muted": user_mute.is_muted,
                    "mute_expires_at": user_mute.mute_expires_at.isoformat() if user_mute.mute_expires_at else None,
                    "remaining_seconds": remaining_seconds,
                    "warning_count": user_mute.warning_count,
                    "consecutive_toxic_count": user_mute.consecutive_toxic_count,
                    "total_mute_count": user_mute.total_mute_count,
                    "just_unmuted": just_unmuted
                }
                
            except Exception as e:
                logger.error(f"Error checking mute status for {username} in {room_id}: {e}")
                return {
                    "is_muted": False,
                    "mute_expires_at": None,
                    "remaining_seconds": None,
                    "warning_count": 0,
                    "consecutive_toxic_count": 0,
                    "total_mute_count": 0,
                    "just_unmuted": False
                }

    async def process_message_toxicity(
        self, 
        username: str, 
        room_id: str, 
        is_toxic: bool
    ) -> Dict[str, Any]:
        """
        Process a message and update warning/mute status based on toxicity.
        
        Args:
            username: The username
            room_id: The room ID  
            is_toxic: Whether the message was toxic
            
        Returns:
            Dictionary with action taken:
            {
                "action": "none" | "warning" | "muted",
                "warning_count": int,
                "consecutive_toxic_count": int,
                "total_mute_count": int,
                "mute_expires_at": datetime or None,
                "remaining_seconds": int or None,
                "warnings_until_mute": int  # How many more warnings until mute
            }
        """
        async with AsyncSessionLocal() as session:
            try:
                # Get user
                user_result = await session.execute(
                    select(User).where(User.username == username)
                )
                user = user_result.scalar_one_or_none()
                
                if not user:
                    logger.warning(f"User {username} not found")
                    return {"action": "none", "error": "User not found"}
                
                # Get or create UserMute record
                mute_result = await session.execute(
                    select(UserMute).where(
                        and_(
                            UserMute.user_id == user.id,
                            UserMute.room_id == room_id
                        )
                    )
                )
                user_mute = mute_result.scalar_one_or_none()
                
                if not user_mute:
                    user_mute = UserMute(
                        user_id=user.id,
                        room_id=room_id,
                        warning_count=0,
                        consecutive_toxic_count=0,
                        is_muted=False,
                        total_mute_count=0
                    )
                    session.add(user_mute)
                    await session.flush()
                
                action = "none"
                now = datetime.utcnow()
                
                if is_toxic:
                    # Increment consecutive toxic count
                    user_mute.consecutive_toxic_count += 1
                    user_mute.warning_count += 1
                    action = "warning"
                    
                    logger.info(
                        f"User {username} sent toxic message #{user_mute.consecutive_toxic_count} "
                        f"in room {room_id} (total warnings: {user_mute.warning_count})"
                    )
                    
                    # Check if threshold reached
                    if user_mute.consecutive_toxic_count >= TOXIC_THRESHOLD:
                        # Mute the user
                        user_mute.is_muted = True
                        user_mute.muted_at = now
                        user_mute.mute_expires_at = now + timedelta(minutes=MUTE_DURATION_MINUTES)
                        user_mute.total_mute_count += 1
                        user_mute.consecutive_toxic_count = 0  # Reset after muting
                        action = "muted"
                        
                        logger.info(
                            f"User {username} muted in room {room_id} until "
                            f"{user_mute.mute_expires_at.isoformat()} (mute #{user_mute.total_mute_count})"
                        )
                else:
                    # Non-toxic message, do not reset count (cumulative system)
                    pass
                
                await session.commit()
                await session.refresh(user_mute)
                
                # Calculate remaining time if muted
                remaining_seconds = None
                if user_mute.is_muted and user_mute.mute_expires_at:
                    remaining = (user_mute.mute_expires_at - now).total_seconds()
                    remaining_seconds = max(0, int(remaining))
                
                # Calculate warnings until mute
                warnings_until_mute = TOXIC_THRESHOLD - user_mute.consecutive_toxic_count
                
                return {
                    "action": action,
                    "warning_count": user_mute.warning_count,
                    "consecutive_toxic_count": user_mute.consecutive_toxic_count,
                    "total_mute_count": user_mute.total_mute_count,
                    "mute_expires_at": user_mute.mute_expires_at.isoformat() if user_mute.mute_expires_at else None,
                    "remaining_seconds": remaining_seconds,
                    "warnings_until_mute": warnings_until_mute,
                    "mute_duration_minutes": MUTE_DURATION_MINUTES,
                    "toxic_threshold": TOXIC_THRESHOLD
                }
                
            except Exception as e:
                logger.error(f"Error processing toxicity for {username} in {room_id}: {e}")
                await session.rollback()
                return {"action": "none", "error": str(e)}

    async def get_user_stats(self, username: str, room_id: str = None) -> Dict[str, Any]:
        """
        Get mute/warning statistics for a user.
        
        Args:
            username: The username
            room_id: Optional room ID. If None, returns stats for all rooms.
            
        Returns:
            Dictionary with user statistics
        """
        async with AsyncSessionLocal() as session:
            try:
                # Get user
                user_result = await session.execute(
                    select(User).where(User.username == username)
                )
                user = user_result.scalar_one_or_none()
                
                if not user:
                    return {"error": "User not found"}
                
                if room_id:
                    # Get stats for specific room
                    mute_result = await session.execute(
                        select(UserMute).where(
                            and_(
                                UserMute.user_id == user.id,
                                UserMute.room_id == room_id
                            )
                        )
                    )
                    user_mute = mute_result.scalar_one_or_none()
                    
                    if not user_mute:
                        return {
                            "username": username,
                            "room_id": room_id,
                            "warning_count": 0,
                            "consecutive_toxic_count": 0,
                            "total_mute_count": 0,
                            "is_muted": False
                        }
                    
                    return {
                        "username": username,
                        "room_id": room_id,
                        "warning_count": user_mute.warning_count,
                        "consecutive_toxic_count": user_mute.consecutive_toxic_count,
                        "total_mute_count": user_mute.total_mute_count,
                        "is_muted": user_mute.is_muted,
                        "mute_expires_at": user_mute.mute_expires_at.isoformat() if user_mute.mute_expires_at else None
                    }
                else:
                    # Get stats for all rooms
                    mute_result = await session.execute(
                        select(UserMute).where(UserMute.user_id == user.id)
                    )
                    user_mutes = mute_result.scalars().all()
                    
                    rooms_stats = []
                    total_warnings = 0
                    total_mutes = 0
                    
                    for um in user_mutes:
                        total_warnings += um.warning_count
                        total_mutes += um.total_mute_count
                        rooms_stats.append({
                            "room_id": um.room_id,
                            "warning_count": um.warning_count,
                            "consecutive_toxic_count": um.consecutive_toxic_count,
                            "total_mute_count": um.total_mute_count,
                            "is_muted": um.is_muted,
                            "mute_expires_at": um.mute_expires_at.isoformat() if um.mute_expires_at else None
                        })
                    
                    return {
                        "username": username,
                        "total_warnings": total_warnings,
                        "total_mutes": total_mutes,
                        "rooms": rooms_stats
                    }
                    
            except Exception as e:
                logger.error(f"Error getting user stats for {username}: {e}")
                return {"error": str(e)}

    async def get_muted_users(self, room_id: str) -> list:
        """
        Get all currently muted users in a room.
        
        Args:
            room_id: The room ID
            
        Returns:
            List of muted users with their mute info
        """
        async with AsyncSessionLocal() as session:
            try:
                now = datetime.utcnow()
                
                # Get all muted users in this room
                result = await session.execute(
                    select(UserMute, User).join(User).where(
                        and_(
                            UserMute.room_id == room_id,
                            UserMute.is_muted == True,
                            UserMute.mute_expires_at > now
                        )
                    )
                )
                muted_records = result.all()
                
                muted_users = []
                for user_mute, user in muted_records:
                    remaining = (user_mute.mute_expires_at - now).total_seconds()
                    muted_users.append({
                        "username": user.username,
                        "user_id": user.id,
                        "muted_at": user_mute.muted_at.isoformat() if user_mute.muted_at else None,
                        "mute_expires_at": user_mute.mute_expires_at.isoformat(),
                        "remaining_seconds": max(0, int(remaining)),
                        "warning_count": user_mute.warning_count,
                        "total_mute_count": user_mute.total_mute_count
                    })
                
                return muted_users
                
            except Exception as e:
                logger.error(f"Error getting muted users for room {room_id}: {e}")
                return []

    async def unmute_user(self, username: str, room_id: str) -> bool:
        """
        Manually unmute a user in a room.
        
        Args:
            username: The username to unmute
            room_id: The room ID
            
        Returns:
            True if user was unmuted, False otherwise
        """
        async with AsyncSessionLocal() as session:
            try:
                # Get user
                user_result = await session.execute(
                    select(User).where(User.username == username)
                )
                user = user_result.scalar_one_or_none()
                
                if not user:
                    logger.warning(f"User {username} not found for unmute")
                    return False
                
                # Get UserMute record
                mute_result = await session.execute(
                    select(UserMute).where(
                        and_(
                            UserMute.user_id == user.id,
                            UserMute.room_id == room_id
                        )
                    )
                )
                user_mute = mute_result.scalar_one_or_none()
                
                if not user_mute or not user_mute.is_muted:
                    return False
                
                # Unmute the user
                user_mute.is_muted = False
                user_mute.muted_at = None
                user_mute.mute_expires_at = None
                user_mute.consecutive_toxic_count = 0
                await session.commit()
                
                logger.info(f"Manually unmuted {username} in room {room_id}")
                return True
                
            except Exception as e:
                logger.error(f"Error unmuting {username} in {room_id}: {e}")
                await session.rollback()
                return False


# Global singleton instance
mute_service = MuteService()
