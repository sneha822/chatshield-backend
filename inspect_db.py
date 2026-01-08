"""Simple script to inspect the database."""

import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.sql import User, Room, Message

async def inspect():
    async with AsyncSessionLocal() as session:
        print("\n--- USERS ---")
        result = await session.execute(select(User))
        for user in result.scalars():
            print(f"ID: {user.id}, Username: {user.username}")

        print("\n--- ROOMS ---")
        result = await session.execute(select(Room))
        for room in result.scalars():
            print(f"ID: {room.id}, Name: {room.name}")
            
        print("\n--- RECENT MESSAGES ---")
        result = await session.execute(select(Message).limit(5).order_by(Message.timestamp.desc()))
        for msg in result.scalars():
            print(f"[{msg.timestamp}] {msg.sender_id} in {msg.room_id}: {msg.content} (Toxic: {msg.toxicity_scores})")

if __name__ == "__main__":
    asyncio.run(inspect())
