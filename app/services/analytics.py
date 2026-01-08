"""Service for calculating chat analytics."""

from sqlalchemy import select, func, desc, asc
from app.models.sql import Message, User
from app.database import AsyncSessionLocal
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service to retrieve analytics data from the database."""

    async def get_room_analytics(self, room_id: str) -> Dict[str, Any]:
        """
        Get analytics for a specific room.
        
        Returns:
            Dictionary containing:
            - total_messages
            - most_toxic_users (top 5)
            - safest_users (top 5 by lowest avg toxicity)
            - active_users (by message count)
        """
        async with AsyncSessionLocal() as session:
            try:
                # 1. Total Messages
                total_msgs_query = select(func.count(Message.id)).where(Message.room_id == room_id)
                total_msgs = (await session.execute(total_msgs_query)).scalar() or 0
                
                if total_msgs == 0:
                    return {"message": "No data available for this room"}

                # 2. Most Toxic Users
                # We'll order by average toxicity score
                # Note: This assumes toxicity_scores stores 'toxicity' key.
                # SQLite JSON extraction syntax is different, but SQLAlchemy generic functions might help.
                # However, calculating avg on JSON fields in DB is complex across backends.
                # For simplicity in this localized setup, checking just numeric value if possible, 
                # OR (better for MVP) fetching recent messages and processing in python if DB is small,
                # BUT properly, we should extract the value.
                
                # Let's try to do it in python for flexibility with SQLite JSON first, 
                # or assume 'toxicity' is a key. 
                # SQLAlchemy's JSON access: Message.toxicity_scores['toxicity']
                
                # Determining "Toxic User": accumulated toxicity or average?
                # Let's go with Average Toxicity of their messages.
                
                # Complex aggregation on JSON in SQLite via SQLAlchemy can be tricky.
                # Let's fetch all messages for the room (with user) and aggregate in memory for now.
                # This is "safest" for a quick reliable implementation without debugging SQLite JSON syntax nuances.
                
                msgs_query = (
                    select(Message, User.username)
                    .join(User)
                    .where(Message.room_id == room_id)
                )
                result = await session.execute(msgs_query)
                rows = result.all()
                
                user_stats = {}
                
                for msg, username in rows:
                    if username not in user_stats:
                        user_stats[username] = {
                            "msg_count": 0,
                            "total_toxicity": 0.0,
                            "toxic_msg_count": 0
                        }
                    
                    user_stats[username]["msg_count"] += 1
                    
                    scores = msg.toxicity_scores or {}
                    tox_score = scores.get("toxicity", 0.0)
                    user_stats[username]["total_toxicity"] += tox_score
                    
                    if tox_score > 0.5: # Threshold for "toxic message"
                        user_stats[username]["toxic_msg_count"] += 1
                
                # Calculate Averages and Ranks
                analytics_data = []
                for username, stats in user_stats.items():
                    avg_tox = stats["total_toxicity"] / stats["msg_count"] if stats["msg_count"] > 0 else 0
                    analytics_data.append({
                        "username": username,
                        "message_count": stats["msg_count"],
                        "average_toxicity": round(avg_tox, 4),
                        "toxic_messages": stats["toxic_msg_count"]
                    })
                
                # Sort for Most Toxic
                most_toxic = sorted(analytics_data, key=lambda x: x["average_toxicity"], reverse=True)[:5]
                
                # Sort for Safest (Least Toxic)
                safest = sorted(analytics_data, key=lambda x: x["average_toxicity"])[:5]
                
                # Sort for Most Active
                most_active = sorted(analytics_data, key=lambda x: x["message_count"], reverse=True)[:5]
                
                return {
                    "room_id": room_id,
                    "total_messages": total_msgs,
                    "most_toxic_users": most_toxic,
                    "safest_users": safest,
                    "most_active_users": most_active
                }

            except Exception as e:
                logger.error(f"Error generating analytics for {room_id}: {e}")
                return {"error": str(e)}


analytics_service = AnalyticsService()
