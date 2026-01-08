
import asyncio
import aiohttp
import sys

# Constants
BASE_URL = "http://localhost:8000"
USERNAME = "test_verifier"
PASSWORD = "password123"

async def main():
    async with aiohttp.ClientSession() as session:
        # 1. Register/Login
        print(f"Authenticating as {USERNAME}...")
        await session.post(f"{BASE_URL}/auth/register", data={"username": USERNAME, "password": PASSWORD})
        async with session.post(f"{BASE_URL}/auth/login", data={"username": USERNAME, "password": PASSWORD}) as resp:
            data = await resp.json()
            token = data.get("access_token")
            if not token:
                print("Login failed")
                return
            headers = {"Authorization": f"Bearer {token}"}
            print("Logged in.")

        # 2. Create Room
        room_id = "test-room-unique"
        print(f"\nCreating room '{room_id}'...")
        async with session.post(
            f"{BASE_URL}/chat/rooms", 
            json={"room_id": room_id, "name": "Test Room"},
            headers=headers
        ) as resp:
            if resp.status == 201:
                print("Room created successfully.")
            elif resp.status == 400:
                print("Room already exists (expected if running twice).")
            else:
                print(f"Create room failed: {resp.status} {await resp.text()}")

        # 3. Create Duplicate Room
        print(f"\nCreating duplicate room '{room_id}'...")
        async with session.post(
            f"{BASE_URL}/chat/rooms", 
            json={"room_id": room_id, "name": "Duplicate Room"},
            headers=headers
        ) as resp:
            if resp.status == 400:
                print("SUCCESS: Duplicate creation blocked (400 Bad Request).")
            else:
                print(f"FAIL: Expected 400, got {resp.status}")

        # 4. Get Messages
        print(f"\nGetting messages for '{room_id}'...")
        async with session.get(f"{BASE_URL}/chat/rooms/{room_id}/messages", headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"Got {data['count']} messages.")
                print("SUCCESS: Messages retrieved.")
            else:
                print(f"FAIL: Message retrieval failed {resp.status}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
