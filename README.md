# ChatShield Backend 🛡️

A real-time chat application backend built with FastAPI and WebSocket support.

## Features

- ⚡ **Real-time messaging** with WebSocket
- 🏠 **Room-based chat** - Join different chat rooms
- 📡 **REST API** - Health checks and room management
- 🔒 **CORS enabled** - Secure cross-origin requests
- 📚 **Auto-generated docs** - Swagger UI & ReDoc

## Project Structure

```
chatshield-backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application entry point
│   ├── config.py         # Configuration settings
│   ├── models/
│   │   ├── __init__.py
│   │   └── message.py    # Message data models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py     # Health check endpoints
│   │   └── chat.py       # Chat REST endpoints
│   └── websocket/
│       ├── __init__.py
│       ├── manager.py    # WebSocket connection manager
│       └── handlers.py   # WebSocket event handlers
├── .env.example          # Environment variables template
├── .gitignore
├── requirements.txt
├── run.py                # Server startup script
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/chatshield-backend.git
   cd chatshield-backend
   ```

2. **Create a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Copy the example env file
   # Windows
   copy .env.example .env

   # macOS/Linux
   cp .env.example .env
   ```

5. **Run the server**
   ```bash
   python run.py
   ```

   The server will start at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/health/stats` | Server statistics |
| GET | `/chat/rooms` | List active rooms |
| GET | `/chat/rooms/{room_id}/users` | Get users in a room |

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `ws://localhost:8000/ws/{username}` | Connect to default room |
| `ws://localhost:8000/ws/{username}/{room_id}` | Connect to specific room |

## WebSocket Usage

### Connecting

```javascript
// Connect to the general room
const ws = new WebSocket('ws://localhost:8000/ws/YourUsername');

// Connect to a specific room
const ws = new WebSocket('ws://localhost:8000/ws/YourUsername/room123');
```

### Sending Messages

```javascript
// Send a chat message
ws.send(JSON.stringify({
    content: "Hello, World!"
}));

// Or send plain text
ws.send("Hello, World!");
```

### Receiving Messages

```javascript
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log(message);
    // {
    //     type: "chat",
    //     content: "Hello, World!",
    //     sender: "Username",
    //     timestamp: "2024-01-01T12:00:00",
    //     room_id: "general"
    // }
};
```

### Message Types

- `chat` - Regular chat message
- `system` - System notification
- `join` - User joined the room
- `leave` - User left the room
- `error` - Error message

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | ChatShield |
| `APP_VERSION` | Application version | 1.0.0 |
| `DEBUG` | Enable debug mode | False |
| `HOST` | Server host | 0.0.0.0 |
| `PORT` | Server port | 8000 |
| `ALLOWED_ORIGINS` | CORS allowed origins | http://localhost:3000 |

## Development

### Running in Debug Mode

Set `DEBUG=True` in your `.env` file to enable:
- Auto-reload on code changes
- Detailed error messages
- Debug logging

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## License

MIT License - feel free to use this project for your own purposes.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
