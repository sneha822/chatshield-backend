
import asyncio
import aiohttp
import sys

# Constants
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"
USERNAME = "debug_user"
PASSWORD = "debug_password"

async def main():
    async with aiohttp.ClientSession() as session:
        # 1. Register
        print(f"Attempting to register user: {USERNAME}")
        async with session.post(f"{BASE_URL}/auth/register", data={"username": USERNAME, "password": PASSWORD}) as resp:
            print(f"Register status: {resp.status}")
            if resp.status not in [200, 400]: # 400 if already exists is fine
                print(await resp.text())
                return

        # 2. Login
        print(f"Attempting to login...")
        async with session.post(f"{BASE_URL}/auth/login", data={"username": USERNAME, "password": PASSWORD}) as resp:
            if resp.status != 200:
                print(f"Login failed: {resp.status}")
                print(await resp.text())
                return
            data = await resp.json()
            token = data["access_token"]
            print(f"Got token: {token[:20]}...")

        # 3. Connect WebSocket
        print(f"Connecting to WebSocket...")
        ws_url_with_token = f"{WS_URL}?token={token}&room=general"
        
        try:
            async with session.ws_connect(ws_url_with_token) as ws:
                print("WebSocket Connected!")
                
                # Send a test message
                await ws.send_json({"content": "Hello Debug"})
                
                # Wait for response
                msg = await ws.receive()
                print(f"Received: {msg.type}")
                if msg.type == aiohttp.WSMsgType.TEXT:
                    print(f"Message data: {msg.data}")
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    print("WebSocket Closed")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print("WebSocket Error")
                    
        except Exception as e:
            print(f"WebSocket connection failed: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
