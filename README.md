# ChatShield Backend 🛡️

A real-time chat application backend built with FastAPI and WebSocket support, featuring **AI-powered toxicity detection** for every message.

## Features

- ⚡ **Real-time messaging** with WebSocket
- 🛡️ **Toxicity Detection** - NLP-powered message analysis using Detoxify
- 🏠 **Room-based chat** - Join different chat rooms with history
- 📊 **Analytics** - View room statistics
- 📡 **REST API** - Health checks, room management, and history retrieval
- 🔒 **CORS enabled** - Secure cross-origin requests
- 📚 **Auto-generated docs** - Swagger UI & ReDoc

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Getting Started](#getting-started)
3. [API Documentation](#api-documentation)
4. [Frontend Integration Guide](#frontend-integration-guide)
   - [Setting Up WebSocket Connection](#1-setting-up-websocket-connection)
   - [Handling Connection Events](#2-handling-connection-events)
   - [Sending Messages](#3-sending-messages)
   - [Receiving Messages](#4-receiving-messages)
   - [Displaying Toxicity Scores](#5-displaying-toxicity-scores)
   - [Getting Room Users](#6-getting-room-users-via-rest-api)
   - [Complete React Example](#7-complete-react-example)
   - [Complete Vanilla JS Example](#8-complete-vanilla-javascript-example)
5. [Toxicity Detection](#toxicity-detection)
6. [Environment Variables](#environment-variables)
7. [Troubleshooting](#troubleshooting)

---

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
│   ├── services/
│   │   ├── __init__.py
│   │   └── toxicity.py   # Toxicity detection NLP service
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

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- ~2GB disk space (for the toxicity detection model)

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

   > ⚠️ **Note:** First startup may take 1-2 minutes as the toxicity model downloads (~700MB)
   >
   > 💡 **Tip:** To skip the download, see [Sharing the Model](#sharing-the-toxicity-model) below

### Sharing the Toxicity Model

If you've already downloaded the model and want to share it with teammates (or vice versa):

**To Export Your Model:**
```bash
python export_model.py
```
This creates a `model_export/` folder (~700MB). Compress it and share it via Google Drive, USB, etc.

**To Use a Shared Model:**

Option 1 (Recommended): Extract the `model_export/` folder to your project root, then modify `app/services/toxicity.py` line 36:
```python
# Change from:
self._model = pipeline("text-classification", model="textdetox/bert-multilingual-toxicity-classifier")

# To:
self._model = pipeline("text-classification", model="./model_export")
```

Option 2: Place the model in your Hugging Face cache directory (see `model_export/SHARED_MODEL_README.txt` for details)

> ⚠️ **Note:** DO NOT commit the `model_export/` folder to GitHub - it's already in `.gitignore` due to file size limits (GitHub max is 100MB)

---

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/health/stats` | Server statistics (connections, rooms) |
| GET | `/chat/rooms` | List all active rooms |
| POST | `/chat/rooms` | Create a new room (Strict Mode) |
| GET | `/chat/rooms/{room_id}/messages` | Get chat history for a room |
| GET | `/chat/rooms/{room_id}/users` | Get users in a specific room |
| GET | `/analytics/rooms/{room_id}` | Get analytics for a room |

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `ws://localhost:8000/ws/{username}` | Connect to default "general" room |
| `ws://localhost:8000/ws/{username}/{room_id}` | Connect to a specific room |

---

## Frontend Integration Guide

> **Note**: For detailed integration instructions, please refer to:
> - [**Frontend Integration Guide**](FRONTEND_INTEGRATION.md) - Comprehensive guide for Auth, API, and WebSockets.
> - [**Frontend Changes**](FRONTEND_CHANGES.md) - Specific details on new Room and History features.

This section provides step-by-step instructions for integrating the ChatShield backend with your frontend application.

### 1. Setting Up WebSocket Connection

#### Basic Connection

```javascript
// Replace with your actual values
const username = "JohnDoe";
const roomId = "room123";  // Optional - defaults to "general"

// Connect to a specific room
const ws = new WebSocket(`ws://localhost:8000/ws/${username}/${roomId}`);

// OR connect to the default "general" room
const ws = new WebSocket(`ws://localhost:8000/ws/${username}`);
```

#### Connection with Error Handling

```javascript
function connectToChat(username, roomId = "general") {
    const wsUrl = `ws://localhost:8000/ws/${username}/${roomId}`;
    const ws = new WebSocket(wsUrl);
    
    // Connection opened successfully
    ws.onopen = () => {
        console.log("✅ Connected to chat server!");
        console.log(`📍 Room: ${roomId}`);
        console.log(`👤 Username: ${username}`);
    };
    
    // Connection closed
    ws.onclose = (event) => {
        console.log("❌ Disconnected from chat server");
        console.log(`Code: ${event.code}, Reason: ${event.reason}`);
        
        // Optional: Attempt to reconnect after 3 seconds
        setTimeout(() => {
            console.log("🔄 Attempting to reconnect...");
            connectToChat(username, roomId);
        }, 3000);
    };
    
    // Connection error
    ws.onerror = (error) => {
        console.error("⚠️ WebSocket error:", error);
    };
    
    return ws;
}

// Usage
const chatConnection = connectToChat("JohnDoe", "room123");
```

---

### 2. Handling Connection Events

When users join or leave the chat room, the server broadcasts system messages. Here's how to handle them:

```javascript
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    switch (message.type) {
        case "join":
            handleUserJoin(message);
            break;
        case "leave":
            handleUserLeave(message);
            break;
        case "chat":
            handleChatMessage(message);
            break;
        case "error":
            handleError(message);
            break;
        default:
            console.log("Unknown message type:", message);
    }
};

// Handle user joining
function handleUserJoin(message) {
    console.log(`👋 ${message.content}`);  // "JohnDoe has joined the chat"
    
    // Update your user list with the latest users
    const users = message.users;  // Array of usernames in the room
    updateUserList(users);
    
    // Show a notification in the chat
    displaySystemMessage(message.content);
}

// Handle user leaving
function handleUserLeave(message) {
    console.log(`👋 ${message.content}`);  // "JohnDoe has left the chat"
    
    // Update your user list
    const users = message.users;
    updateUserList(users);
    
    // Show a notification in the chat
    displaySystemMessage(message.content);
}

// Handle errors
function handleError(message) {
    console.error("Error:", message.content);
    displayErrorMessage(message.content);
}
```

#### Join Message Structure

When a user joins, everyone in the room receives:

```json
{
    "type": "join",
    "content": "JohnDoe has joined the chat",
    "sender": "System",
    "timestamp": "2026-01-06T12:00:00.000000",
    "room_id": "room123",
    "users": ["Alice", "Bob", "JohnDoe"]
}
```

#### Leave Message Structure

When a user leaves/disconnects:

```json
{
    "type": "leave",
    "content": "JohnDoe has left the chat",
    "sender": "System",
    "timestamp": "2026-01-06T12:05:00.000000",
    "room_id": "room123",
    "users": ["Alice", "Bob"]
}
```

---

### 3. Sending Messages

#### Send a Chat Message

```javascript
function sendMessage(ws, messageContent) {
    // Check if connection is open
    if (ws.readyState !== WebSocket.OPEN) {
        console.error("Cannot send message - not connected!");
        return false;
    }
    
    // Send as JSON (recommended)
    const messageData = {
        content: messageContent
    };
    
    ws.send(JSON.stringify(messageData));
    return true;
}

// Usage
sendMessage(chatConnection, "Hello everyone! 👋");
```

#### With Input Form

```javascript
// HTML: <input id="messageInput" /> <button id="sendBtn">Send</button>

const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");

sendBtn.addEventListener("click", () => {
    const content = messageInput.value.trim();
    
    if (content) {
        sendMessage(chatConnection, content);
        messageInput.value = "";  // Clear input after sending
    }
});

// Also send on Enter key
messageInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        sendBtn.click();
    }
});
```

---

### 4. Receiving Messages

#### Chat Message Structure

Every chat message includes toxicity analysis:

```json
{
    "type": "chat",
    "content": "Hello everyone!",
    "sender": "JohnDoe",
    "timestamp": "2026-01-06T12:00:00.000000",
    "room_id": "room123",
    "toxicity": {
        "toxicity": 0.0012,
        "severe_toxicity": 0.0001,
        "obscene": 0.0005,
        "threat": 0.0002,
        "insult": 0.0008,
        "identity_attack": 0.0003,
        "is_toxic": false,
        "toxicity_level": "safe"
    }
}
```

#### Complete Message Handler

```javascript
function handleChatMessage(message) {
    // Extract message data
    const { content, sender, timestamp, toxicity } = message;
    
    // Format timestamp
    const time = new Date(timestamp).toLocaleTimeString();
    
    // Create message element
    const messageElement = document.createElement("div");
    messageElement.className = "chat-message";
    
    // Add toxicity warning class if needed
    if (toxicity.is_toxic) {
        messageElement.classList.add("toxic-message");
    }
    
    // Build message HTML
    messageElement.innerHTML = `
        <div class="message-header">
            <span class="sender">${sender}</span>
            <span class="time">${time}</span>
            ${getToxicityBadge(toxicity)}
        </div>
        <div class="message-content">${escapeHtml(content)}</div>
    `;
    
    // Add to chat container
    document.getElementById("chatMessages").appendChild(messageElement);
    
    // Scroll to bottom
    scrollToBottom();
}

// Helper to escape HTML to prevent XSS attacks
function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// Scroll chat to bottom
function scrollToBottom() {
    const container = document.getElementById("chatMessages");
    container.scrollTop = container.scrollHeight;
}
```

---

### 5. Displaying Toxicity Scores

#### Toxicity Levels Explained

| Level | Score Range | Recommended Action |
|-------|-------------|-------------------|
| `safe` | 0.0 - 0.2 | Display normally |
| `mild` | 0.2 - 0.4 | Display normally, maybe subtle indicator |
| `moderate` | 0.4 - 0.6 | Show warning indicator |
| `high` | 0.6 - 0.8 | Blur/hide message, show warning |
| `severe` | 0.8 - 1.0 | Hide message, strong warning |

#### Create Toxicity Badge

```javascript
function getToxicityBadge(toxicity) {
    const { toxicity_level, toxicity: score } = toxicity;
    
    // Define colors for each level
    const colors = {
        safe: "#4CAF50",      // Green
        mild: "#8BC34A",      // Light Green
        moderate: "#FFC107",  // Yellow
        high: "#FF9800",      // Orange
        severe: "#F44336"     // Red
    };
    
    // Define emojis for each level
    const emojis = {
        safe: "✅",
        mild: "🟡",
        moderate: "⚠️",
        high: "🔶",
        severe: "🚫"
    };
    
    const color = colors[toxicity_level] || "#999";
    const emoji = emojis[toxicity_level] || "❓";
    const percentage = (score * 100).toFixed(1);
    
    return `
        <span class="toxicity-badge" style="background-color: ${color}">
            ${emoji} ${toxicity_level} (${percentage}%)
        </span>
    `;
}
```

#### CSS for Toxicity Display

```css
/* Toxicity Badge */
.toxicity-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 12px;
    color: white;
    margin-left: 8px;
}

/* Toxic Message Styling */
.toxic-message {
    border-left: 3px solid #F44336;
    background-color: rgba(244, 67, 54, 0.1);
}

/* Blur highly toxic content */
.toxic-message.severe .message-content {
    filter: blur(5px);
    transition: filter 0.3s;
}

.toxic-message.severe .message-content:hover {
    filter: none;
}

/* Warning overlay for toxic messages */
.toxic-warning {
    background-color: #FFF3E0;
    border: 1px solid #FF9800;
    padding: 8px 12px;
    border-radius: 4px;
    margin-bottom: 8px;
    font-size: 14px;
}
```

#### Advanced Toxicity Display with Details

```javascript
function createToxicityDetails(toxicity) {
    const categories = [
        { key: "toxicity", label: "Toxicity", icon: "☠️" },
        { key: "severe_toxicity", label: "Severe", icon: "💀" },
        { key: "obscene", label: "Obscene", icon: "🤬" },
        { key: "threat", label: "Threat", icon: "⚔️" },
        { key: "insult", label: "Insult", icon: "😤" },
        { key: "identity_attack", label: "Identity Attack", icon: "🎯" }
    ];
    
    let html = '<div class="toxicity-details">';
    
    categories.forEach(({ key, label, icon }) => {
        const score = toxicity[key];
        const percentage = (score * 100).toFixed(1);
        const barWidth = Math.min(score * 100, 100);
        const barColor = getScoreColor(score);
        
        html += `
            <div class="toxicity-row">
                <span class="toxicity-label">${icon} ${label}</span>
                <div class="toxicity-bar-container">
                    <div class="toxicity-bar" style="width: ${barWidth}%; background: ${barColor}"></div>
                </div>
                <span class="toxicity-score">${percentage}%</span>
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

function getScoreColor(score) {
    if (score < 0.2) return "#4CAF50";
    if (score < 0.4) return "#8BC34A";
    if (score < 0.6) return "#FFC107";
    if (score < 0.8) return "#FF9800";
    return "#F44336";
}
```

#### CSS for Toxicity Details

```css
.toxicity-details {
    background: #f5f5f5;
    padding: 12px;
    border-radius: 8px;
    margin-top: 8px;
}

.toxicity-row {
    display: flex;
    align-items: center;
    margin-bottom: 6px;
}

.toxicity-label {
    width: 140px;
    font-size: 13px;
}

.toxicity-bar-container {
    flex: 1;
    height: 8px;
    background: #ddd;
    border-radius: 4px;
    overflow: hidden;
    margin: 0 10px;
}

.toxicity-bar {
    height: 100%;
    border-radius: 4px;
    transition: width 0.3s ease;
}

.toxicity-score {
    width: 50px;
    text-align: right;
    font-size: 12px;
    font-weight: bold;
}
```

---

### 6. Getting Room Users (via REST API)

Besides getting user lists through WebSocket events, you can also fetch them via REST API:

```javascript
async function getRoomUsers(roomId) {
    try {
        const response = await fetch(`http://localhost:8000/chat/rooms/${roomId}/users`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Response format:
        // {
        //     "room_id": "room123",
        //     "users": ["Alice", "Bob", "JohnDoe"],
        //     "count": 3
        // }
        
        return data;
    } catch (error) {
        console.error("Failed to fetch room users:", error);
        return null;
    }
}

// Usage
async function updateUserListFromAPI(roomId) {
    const data = await getRoomUsers(roomId);
    
    if (data) {
        updateUserList(data.users);
        updateUserCount(data.count);
    }
}

// Update the UI with user list
function updateUserList(users) {
    const userListContainer = document.getElementById("userList");
    userListContainer.innerHTML = "";
    
    users.forEach(username => {
        const userElement = document.createElement("div");
        userElement.className = "user-item";
        userElement.innerHTML = `
            <span class="user-avatar">${username.charAt(0).toUpperCase()}</span>
            <span class="user-name">${username}</span>
        `;
        userListContainer.appendChild(userElement);
    });
}

function updateUserCount(count) {
    document.getElementById("userCount").textContent = `${count} online`;
}
```

#### Get All Active Rooms

```javascript
async function getAllRooms() {
    try {
        const response = await fetch("http://localhost:8000/chat/rooms");
        const data = await response.json();
        
        // Response format:
        // {
        //     "rooms": [
        //         {
        //             "room_id": "general",
        //             "user_count": 5,
        //             "users": ["Alice", "Bob", "Charlie", "Dave", "Eve"]
        //         },
        //         {
        //             "room_id": "room123",
        //             "user_count": 2,
        //             "users": ["JohnDoe", "JaneDoe"]
        //         }
        //     ]
        // }
        
        return data.rooms;
    } catch (error) {
        console.error("Failed to fetch rooms:", error);
        return [];
    }
}
```

---

### 7. Complete React Example

Here's a complete React component for the chat:

```jsx
import React, { useState, useEffect, useRef, useCallback } from "react";

const BACKEND_URL = "localhost:8000";

function ChatApp({ username, roomId = "general" }) {
    const [messages, setMessages] = useState([]);
    const [users, setUsers] = useState([]);
    const [inputValue, setInputValue] = useState("");
    const [isConnected, setIsConnected] = useState(false);
    const [connectionError, setConnectionError] = useState(null);
    
    const wsRef = useRef(null);
    const messagesEndRef = useRef(null);
    
    // Scroll to bottom when new messages arrive
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };
    
    useEffect(() => {
        scrollToBottom();
    }, [messages]);
    
    // Connect to WebSocket
    useEffect(() => {
        const ws = new WebSocket(`ws://${BACKEND_URL}/ws/${username}/${roomId}`);
        wsRef.current = ws;
        
        ws.onopen = () => {
            console.log("Connected to chat");
            setIsConnected(true);
            setConnectionError(null);
        };
        
        ws.onclose = () => {
            console.log("Disconnected from chat");
            setIsConnected(false);
        };
        
        ws.onerror = (error) => {
            console.error("WebSocket error:", error);
            setConnectionError("Failed to connect to chat server");
        };
        
        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            
            // Update user list for join/leave events
            if (message.type === "join" || message.type === "leave") {
                setUsers(message.users || []);
            }
            
            // Add message to list
            setMessages((prev) => [...prev, message]);
        };
        
        // Cleanup on unmount
        return () => {
            ws.close();
        };
    }, [username, roomId]);
    
    // Send message handler
    const sendMessage = useCallback(() => {
        if (!inputValue.trim() || !wsRef.current) return;
        
        if (wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ content: inputValue }));
            setInputValue("");
        }
    }, [inputValue]);
    
    // Handle Enter key
    const handleKeyPress = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };
    
    // Get toxicity badge color
    const getToxicityColor = (level) => {
        const colors = {
            safe: "#4CAF50",
            mild: "#8BC34A",
            moderate: "#FFC107",
            high: "#FF9800",
            severe: "#F44336"
        };
        return colors[level] || "#999";
    };
    
    return (
        <div className="chat-container">
            {/* Header */}
            <div className="chat-header">
                <h2>Room: {roomId}</h2>
                <span className={`status ${isConnected ? "online" : "offline"}`}>
                    {isConnected ? "🟢 Connected" : "🔴 Disconnected"}
                </span>
            </div>
            
            {connectionError && (
                <div className="error-banner">{connectionError}</div>
            )}
            
            <div className="chat-main">
                {/* User List Sidebar */}
                <div className="user-sidebar">
                    <h3>Users ({users.length})</h3>
                    <ul className="user-list">
                        {users.map((user, index) => (
                            <li key={index} className="user-item">
                                <span className="user-avatar">
                                    {user.charAt(0).toUpperCase()}
                                </span>
                                {user}
                                {user === username && " (you)"}
                            </li>
                        ))}
                    </ul>
                </div>
                
                {/* Messages Area */}
                <div className="messages-area">
                    <div className="messages-container">
                        {messages.map((msg, index) => (
                            <div
                                key={index}
                                className={`message ${msg.type} ${
                                    msg.toxicity?.is_toxic ? "toxic" : ""
                                }`}
                            >
                                {msg.type === "chat" ? (
                                    <>
                                        <div className="message-header">
                                            <strong>{msg.sender}</strong>
                                            <span className="timestamp">
                                                {new Date(msg.timestamp).toLocaleTimeString()}
                                            </span>
                                            {msg.toxicity && (
                                                <span
                                                    className="toxicity-badge"
                                                    style={{
                                                        backgroundColor: getToxicityColor(
                                                            msg.toxicity.toxicity_level
                                                        )
                                                    }}
                                                >
                                                    {msg.toxicity.toxicity_level}
                                                    {" "}
                                                    ({(msg.toxicity.toxicity * 100).toFixed(1)}%)
                                                </span>
                                            )}
                                        </div>
                                        <div className="message-content">{msg.content}</div>
                                    </>
                                ) : (
                                    <div className="system-message">{msg.content}</div>
                                )}
                            </div>
                        ))}
                        <div ref={messagesEndRef} />
                    </div>
                    
                    {/* Input Area */}
                    <div className="input-area">
                        <input
                            type="text"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="Type a message..."
                            disabled={!isConnected}
                        />
                        <button onClick={sendMessage} disabled={!isConnected}>
                            Send
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default ChatApp;
```

#### React CSS (App.css)

```css
.chat-container {
    display: flex;
    flex-direction: column;
    height: 100vh;
    max-width: 1200px;
    margin: 0 auto;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.chat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    background: #1976D2;
    color: white;
}

.chat-header h2 {
    margin: 0;
}

.status {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 14px;
}

.status.online {
    background: rgba(255, 255, 255, 0.2);
}

.status.offline {
    background: rgba(244, 67, 54, 0.8);
}

.error-banner {
    background: #FFEBEE;
    color: #C62828;
    padding: 12px;
    text-align: center;
}

.chat-main {
    display: flex;
    flex: 1;
    overflow: hidden;
}

.user-sidebar {
    width: 200px;
    background: #F5F5F5;
    border-right: 1px solid #E0E0E0;
    padding: 16px;
    overflow-y: auto;
}

.user-sidebar h3 {
    margin: 0 0 16px 0;
    font-size: 14px;
    color: #666;
    text-transform: uppercase;
}

.user-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.user-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px;
    border-radius: 4px;
}

.user-item:hover {
    background: #EEEEEE;
}

.user-avatar {
    width: 32px;
    height: 32px;
    background: #1976D2;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
}

.messages-area {
    flex: 1;
    display: flex;
    flex-direction: column;
}

.messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
}

.message {
    margin-bottom: 16px;
    padding: 12px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.message.toxic {
    border-left: 4px solid #F44336;
    background: #FFF8F8;
}

.message.join,
.message.leave {
    background: #E3F2FD;
    text-align: center;
    font-style: italic;
    color: #666;
}

.message-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
}

.timestamp {
    color: #999;
    font-size: 12px;
}

.toxicity-badge {
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    color: white;
    margin-left: auto;
}

.message-content {
    color: #333;
    line-height: 1.5;
}

.system-message {
    color: #666;
}

.input-area {
    display: flex;
    gap: 8px;
    padding: 16px;
    background: #F5F5F5;
    border-top: 1px solid #E0E0E0;
}

.input-area input {
    flex: 1;
    padding: 12px 16px;
    border: 1px solid #E0E0E0;
    border-radius: 24px;
    font-size: 14px;
    outline: none;
}

.input-area input:focus {
    border-color: #1976D2;
}

.input-area button {
    padding: 12px 24px;
    background: #1976D2;
    color: white;
    border: none;
    border-radius: 24px;
    cursor: pointer;
    font-size: 14px;
}

.input-area button:hover {
    background: #1565C0;
}

.input-area button:disabled {
    background: #BDBDBD;
    cursor: not-allowed;
}
```

---

### 8. Complete Vanilla JavaScript Example

For those not using React, here's a complete vanilla JS implementation:

#### HTML (index.html)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChatShield</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <!-- Login Screen -->
    <div id="loginScreen" class="screen">
        <div class="login-box">
            <h1>🛡️ ChatShield</h1>
            <input type="text" id="usernameInput" placeholder="Enter your username">
            <input type="text" id="roomInput" placeholder="Room ID (optional)" value="general">
            <button id="joinBtn">Join Chat</button>
        </div>
    </div>
    
    <!-- Chat Screen -->
    <div id="chatScreen" class="screen hidden">
        <header>
            <div class="header-info">
                <h2 id="roomName">Room: general</h2>
                <span id="connectionStatus" class="status">🔴 Connecting...</span>
            </div>
            <button id="leaveBtn">Leave</button>
        </header>
        
        <main>
            <aside id="sidebar">
                <h3>Users <span id="userCount">(0)</span></h3>
                <ul id="userList"></ul>
            </aside>
            
            <section id="chatArea">
                <div id="messages"></div>
                
                <form id="messageForm">
                    <input type="text" id="messageInput" placeholder="Type a message..." disabled>
                    <button type="submit" id="sendBtn" disabled>Send</button>
                </form>
            </section>
        </main>
    </div>
    
    <script src="chat.js"></script>
</body>
</html>
```

#### JavaScript (chat.js)

```javascript
// ChatShield Frontend - Vanilla JavaScript

const BACKEND_URL = "localhost:8000";

// DOM Elements
const loginScreen = document.getElementById("loginScreen");
const chatScreen = document.getElementById("chatScreen");
const usernameInput = document.getElementById("usernameInput");
const roomInput = document.getElementById("roomInput");
const joinBtn = document.getElementById("joinBtn");
const leaveBtn = document.getElementById("leaveBtn");
const roomName = document.getElementById("roomName");
const connectionStatus = document.getElementById("connectionStatus");
const userList = document.getElementById("userList");
const userCount = document.getElementById("userCount");
const messages = document.getElementById("messages");
const messageForm = document.getElementById("messageForm");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");

// State
let ws = null;
let currentUsername = "";
let currentRoom = "";

// ============ CONNECTION ============

function connect(username, roomId) {
    currentUsername = username;
    currentRoom = roomId;
    
    // Create WebSocket connection
    ws = new WebSocket(`ws://${BACKEND_URL}/ws/${username}/${roomId}`);
    
    ws.onopen = () => {
        console.log("✅ Connected!");
        setConnected(true);
    };
    
    ws.onclose = (event) => {
        console.log("❌ Disconnected:", event.code, event.reason);
        setConnected(false);
        
        // Show login screen if unexpectedly disconnected
        if (!event.wasClean) {
            showLoginScreen();
            alert("Connection lost. Please rejoin.");
        }
    };
    
    ws.onerror = (error) => {
        console.error("⚠️ WebSocket error:", error);
        setConnected(false);
    };
    
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleMessage(message);
    };
}

function disconnect() {
    if (ws) {
        ws.close(1000, "User left");
        ws = null;
    }
}

function setConnected(connected) {
    connectionStatus.textContent = connected ? "🟢 Connected" : "🔴 Disconnected";
    connectionStatus.className = `status ${connected ? "online" : "offline"}`;
    messageInput.disabled = !connected;
    sendBtn.disabled = !connected;
}

// ============ MESSAGE HANDLING ============

function handleMessage(message) {
    switch (message.type) {
        case "join":
        case "leave":
            updateUsers(message.users);
            addSystemMessage(message.content);
            break;
        case "chat":
            addChatMessage(message);
            break;
        case "error":
            addErrorMessage(message.content);
            break;
    }
}

function addSystemMessage(content) {
    const div = document.createElement("div");
    div.className = "message system";
    div.innerHTML = `<em>${escapeHtml(content)}</em>`;
    messages.appendChild(div);
    scrollToBottom();
}

function addChatMessage(message) {
    const { content, sender, timestamp, toxicity } = message;
    const time = new Date(timestamp).toLocaleTimeString();
    const isToxic = toxicity?.is_toxic;
    const toxicityLevel = toxicity?.toxicity_level || "unknown";
    
    const div = document.createElement("div");
    div.className = `message chat ${isToxic ? "toxic" : ""} ${toxicityLevel}`;
    
    div.innerHTML = `
        <div class="message-header">
            <strong class="sender">${escapeHtml(sender)}</strong>
            <span class="time">${time}</span>
            ${createToxicityBadge(toxicity)}
        </div>
        <div class="message-content ${isToxic && toxicityLevel === "severe" ? "blurred" : ""}">
            ${escapeHtml(content)}
        </div>
        ${isToxic ? createToxicityWarning(toxicity) : ""}
    `;
    
    messages.appendChild(div);
    scrollToBottom();
}

function addErrorMessage(content) {
    const div = document.createElement("div");
    div.className = "message error";
    div.textContent = `⚠️ Error: ${content}`;
    messages.appendChild(div);
    scrollToBottom();
}

function createToxicityBadge(toxicity) {
    if (!toxicity) return "";
    
    const colors = {
        safe: "#4CAF50",
        mild: "#8BC34A",
        moderate: "#FFC107",
        high: "#FF9800",
        severe: "#F44336"
    };
    
    const emojis = {
        safe: "✅",
        mild: "🟡",
        moderate: "⚠️",
        high: "🔶",
        severe: "🚫"
    };
    
    const level = toxicity.toxicity_level;
    const score = (toxicity.toxicity * 100).toFixed(1);
    
    return `
        <span class="toxicity-badge" style="background-color: ${colors[level]}">
            ${emojis[level]} ${level} (${score}%)
        </span>
    `;
}

function createToxicityWarning(toxicity) {
    if (!toxicity.is_toxic) return "";
    
    return `
        <div class="toxicity-warning">
            ⚠️ This message may contain ${toxicity.toxicity_level} toxic content.
            <button onclick="this.parentElement.previousElementSibling.classList.remove('blurred')">
                Show anyway
            </button>
        </div>
    `;
}

// ============ USER LIST ============

function updateUsers(users) {
    userCount.textContent = `(${users.length})`;
    userList.innerHTML = "";
    
    users.forEach(user => {
        const li = document.createElement("li");
        li.className = "user-item";
        li.innerHTML = `
            <span class="avatar">${user.charAt(0).toUpperCase()}</span>
            <span class="name">${escapeHtml(user)}${user === currentUsername ? " (you)" : ""}</span>
        `;
        userList.appendChild(li);
    });
}

// ============ SEND MESSAGE ============

function sendMessage(content) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        console.error("Not connected!");
        return false;
    }
    
    ws.send(JSON.stringify({ content }));
    return true;
}

// ============ UI HELPERS ============

function showLoginScreen() {
    loginScreen.classList.remove("hidden");
    chatScreen.classList.add("hidden");
    messages.innerHTML = "";
    updateUsers([]);
}

function showChatScreen() {
    loginScreen.classList.add("hidden");
    chatScreen.classList.remove("hidden");
    roomName.textContent = `Room: ${currentRoom}`;
    messageInput.focus();
}

function scrollToBottom() {
    messages.scrollTop = messages.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// ============ EVENT LISTENERS ============

// Join button
joinBtn.addEventListener("click", () => {
    const username = usernameInput.value.trim();
    const room = roomInput.value.trim() || "general";
    
    if (!username) {
        alert("Please enter a username!");
        return;
    }
    
    connect(username, room);
    showChatScreen();
});

// Enter key on username input
usernameInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") joinBtn.click();
});

// Leave button
leaveBtn.addEventListener("click", () => {
    disconnect();
    showLoginScreen();
});

// Send message form
messageForm.addEventListener("submit", (e) => {
    e.preventDefault();
    
    const content = messageInput.value.trim();
    if (content) {
        sendMessage(content);
        messageInput.value = "";
    }
});

// Initialize
showLoginScreen();
```

#### CSS (styles.css)

```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #f0f2f5;
    height: 100vh;
}

.hidden {
    display: none !important;
}

/* ============ LOGIN SCREEN ============ */

#loginScreen {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    background: linear-gradient(135deg, #1976D2, #1565C0);
}

.login-box {
    background: white;
    padding: 40px;
    border-radius: 16px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
    text-align: center;
    width: 100%;
    max-width: 400px;
}

.login-box h1 {
    margin-bottom: 24px;
    color: #333;
}

.login-box input {
    width: 100%;
    padding: 14px 16px;
    margin-bottom: 16px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 16px;
    transition: border-color 0.2s;
}

.login-box input:focus {
    outline: none;
    border-color: #1976D2;
}

.login-box button {
    width: 100%;
    padding: 14px;
    background: #1976D2;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    cursor: pointer;
    transition: background 0.2s;
}

.login-box button:hover {
    background: #1565C0;
}

/* ============ CHAT SCREEN ============ */

#chatScreen {
    display: flex;
    flex-direction: column;
    height: 100vh;
}

header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    background: #1976D2;
    color: white;
}

.header-info h2 {
    margin-bottom: 4px;
}

.status {
    font-size: 14px;
    opacity: 0.9;
}

header button {
    padding: 8px 16px;
    background: rgba(255, 255, 255, 0.2);
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

header button:hover {
    background: rgba(255, 255, 255, 0.3);
}

main {
    display: flex;
    flex: 1;
    overflow: hidden;
}

/* ============ SIDEBAR ============ */

#sidebar {
    width: 220px;
    background: white;
    border-right: 1px solid #e0e0e0;
    padding: 16px;
    overflow-y: auto;
}

#sidebar h3 {
    color: #666;
    font-size: 14px;
    text-transform: uppercase;
    margin-bottom: 16px;
}

#userList {
    list-style: none;
}

.user-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px;
    border-radius: 8px;
    margin-bottom: 4px;
}

.user-item:hover {
    background: #f5f5f5;
}

.avatar {
    width: 36px;
    height: 36px;
    background: #1976D2;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
}

/* ============ CHAT AREA ============ */

#chatArea {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: #f0f2f5;
}

#messages {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
}

.message {
    margin-bottom: 16px;
    max-width: 80%;
}

.message.system {
    text-align: center;
    color: #666;
    max-width: 100%;
    padding: 8px;
    background: #e3f2fd;
    border-radius: 8px;
}

.message.chat {
    background: white;
    padding: 12px 16px;
    border-radius: 12px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.message.chat.toxic {
    border-left: 4px solid #F44336;
}

.message-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
    flex-wrap: wrap;
}

.sender {
    color: #1976D2;
}

.time {
    color: #999;
    font-size: 12px;
}

.toxicity-badge {
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    color: white;
    margin-left: auto;
}

.message-content {
    color: #333;
    line-height: 1.5;
    word-wrap: break-word;
}

.message-content.blurred {
    filter: blur(6px);
    user-select: none;
}

.toxicity-warning {
    margin-top: 8px;
    padding: 8px 12px;
    background: #fff3e0;
    border-radius: 6px;
    font-size: 13px;
    color: #e65100;
}

.toxicity-warning button {
    margin-left: 8px;
    padding: 4px 8px;
    background: #ff9800;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
}

.message.error {
    background: #ffebee;
    color: #c62828;
    padding: 12px;
    border-radius: 8px;
    text-align: center;
}

/* ============ MESSAGE INPUT ============ */

#messageForm {
    display: flex;
    gap: 12px;
    padding: 16px 20px;
    background: white;
    border-top: 1px solid #e0e0e0;
}

#messageInput {
    flex: 1;
    padding: 14px 20px;
    border: 2px solid #e0e0e0;
    border-radius: 24px;
    font-size: 15px;
    outline: none;
    transition: border-color 0.2s;
}

#messageInput:focus {
    border-color: #1976D2;
}

#messageInput:disabled {
    background: #f5f5f5;
}

#sendBtn {
    padding: 14px 28px;
    background: #1976D2;
    color: white;
    border: none;
    border-radius: 24px;
    font-size: 15px;
    cursor: pointer;
    transition: background 0.2s;
}

#sendBtn:hover:not(:disabled) {
    background: #1565C0;
}

#sendBtn:disabled {
    background: #bdbdbd;
    cursor: not-allowed;
}

/* ============ RESPONSIVE ============ */

@media (max-width: 768px) {
    #sidebar {
        display: none;
    }
    
    .message {
        max-width: 90%;
    }
}
```

---

## Toxicity Detection

Every message is automatically analyzed for toxicity using the [Detoxify](https://github.com/unitaryai/detoxify) NLP model. The toxicity scores are included in the message response.

### Toxicity Scores

| Score | Description |
|-------|-------------|
| `toxicity` | Overall toxicity score (0.0 - 1.0) |
| `severe_toxicity` | Severe/extreme toxicity |
| `obscene` | Obscene language |
| `threat` | Threatening language |
| `insult` | Insulting language |
| `identity_attack` | Identity-based attacks |
| `is_toxic` | Boolean flag (true if toxicity > 0.5) |
| `toxicity_level` | Human-readable level |

### Toxicity Levels

| Level | Score Range |
|-------|-------------|
| `safe` | 0.0 - 0.2 |
| `mild` | 0.2 - 0.4 |
| `moderate` | 0.4 - 0.6 |
| `high` | 0.6 - 0.8 |
| `severe` | 0.8 - 1.0 |

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | ChatShield |
| `APP_VERSION` | Application version | 1.0.0 |
| `DEBUG` | Enable debug mode | False |
| `HOST` | Server host | 0.0.0.0 |
| `PORT` | Server port | 8000 |
| `ALLOWED_ORIGINS` | CORS allowed origins | http://localhost:3000 |

---

## Troubleshooting

### Common Issues

#### 1. "WebSocket connection failed"
- Make sure the backend server is running (`python run.py`)
- Check if the port 8000 is not blocked by firewall
- Verify the URL matches your backend (localhost vs IP address)

#### 2. "CORS Error"
- Add your frontend URL to `ALLOWED_ORIGINS` in `.env` file
- Example: `ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173`

#### 3. "Toxicity model not loading"
- First startup downloads ~400MB model (may take time)
- Ensure you have stable internet connection
- Check you have enough disk space (~2GB)

#### 4. "Message not sending"
- Check WebSocket connection status
- Verify `ws.readyState === WebSocket.OPEN` before sending
- Check browser console for errors

#### 5. "Users not updating"
- User list updates come through WebSocket `join`/`leave` events
- You can also poll the REST API: `/chat/rooms/{room_id}/users`

### Debug Mode

Enable debug mode for detailed logs:

```bash
# In .env file
DEBUG=True
```

This enables:
- Auto-reload on code changes
- Detailed error messages
- Debug logging in console

---

## License

MIT License - feel free to use this project for your own purposes.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
