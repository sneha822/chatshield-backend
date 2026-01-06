"""
Script to run the ChatShield backend server.
"""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📡 Server running at http://{settings.HOST}:{settings.PORT}")
    print(f"📚 API docs available at http://localhost:{settings.PORT}/docs")
    print(f"🔌 WebSocket endpoint: ws://localhost:{settings.PORT}/ws/{{username}}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
