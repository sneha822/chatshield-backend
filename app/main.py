"""
ChatShield Backend - Main Application Entry Point

A real-time chat application backend with WebSocket support.
"""

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import logging

from .config import settings
from .routes import health_router, chat_router, auth
from .routes.analytics import router as analytics_router

from .websocket import websocket_endpoint
from .services import toxicity_analyzer
from .database import init_db

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST API routers
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(analytics_router)
app.include_router(auth.router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    logger.info("Initializing toxicity detection model...")
    toxicity_analyzer.load_model()
    await init_db()
    logger.info("Application startup complete")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.websocket("/ws")
async def websocket_route(websocket: WebSocket, token: str, room: str = "general"):
    """
    WebSocket endpoint for real-time chat.
    Token is passed as query param: /ws?token=XYZ&room=general
    """
    await websocket_endpoint(websocket, token, room)


# Removed specific room route in favor of query param
# Default route handles both cases via 'room' param



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
