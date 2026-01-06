"""
ChatShield Backend - Main Application Entry Point

A real-time chat application backend with WebSocket support.
"""

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import logging

from .config import settings
from .routes import health_router, chat_router
from .websocket import websocket_endpoint

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A real-time chat application backend with WebSocket support",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST API routers
app.include_router(health_router)
app.include_router(chat_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.websocket("/ws/{username}")
async def websocket_route(websocket: WebSocket, username: str, room: str = "general"):
    """
    WebSocket endpoint for real-time chat.
    
    Args:
        websocket: The WebSocket connection
        username: The username of the connecting client
        room: Optional room ID (defaults to 'general')
    """
    await websocket_endpoint(websocket, username, room)


@app.websocket("/ws/{username}/{room_id}")
async def websocket_room_route(websocket: WebSocket, username: str, room_id: str):
    """
    WebSocket endpoint for room-specific chat.
    
    Args:
        websocket: The WebSocket connection
        username: The username of the connecting client
        room_id: The room to join
    """
    await websocket_endpoint(websocket, username, room_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
