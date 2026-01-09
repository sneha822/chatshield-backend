# Room Membership Integration Guide

This guide explains how to use the new persistent room membership features.

## Why this change?

Previously, users were only "in" a room while their WebSocket was connected. If they refreshed, they "left" and "rejoined", causing repeated "User has joined the chat" messages.

Now, **membership is persistent**.
- **Join**: Happens automatically when you connect to the WebSocket for a room for the first time.
- **Alerts**: "User has joined" is only broadcast the FIRST time they connect. Subsequent connections (e.g. refresh) are silent.
- **My Rooms**: You can now fetch a list of all rooms a user has ever joined.

## API Endpoints

### Get My Rooms
Fetch the list of rooms the logged-in user belongs to.

- **URL**: `/chat/my-rooms`
- **Method**: `GET`
- **Auth**: Requires Bearer Token.

**Response**:
```json
{
  "count": 2,
  "rooms": [
    {
      "id": "general",
      "name": "General",
      "created_at": "2024-01-01T12:00:00"
    },
    {
      "id": "random",
      "name": "Random",
      "created_at": "2024-01-02T15:30:00"
    }
  ]
}
```

## Frontend Implementation

### 1. Show "My Rooms" Sidebar
Use the `/chat/my-rooms` endpoint to populate a sidebar of joined rooms.

```javascript
// React Example
useEffect(() => {
  async function fetchRooms() {
    const res = await fetch('http://localhost:8000/chat/my-rooms', {
      headers: { Authorization: \`Bearer \${token}\` }
    });
    const data = await res.json();
    setMyRooms(data.rooms);
  }
  fetchRooms();
}, [token]);
```

### 2. Handling Join Alerts
You don't need to change much logic for alerts. The backend now filters them.
- **Old Behavior**: received "JOIN" event on every connect.
- **New Behavior**: receive "JOIN" event only on *new* membership.

**Recommendation**:
- Differentiate between "Online Users" (ws connections) and "Room Members" (historical).
- Use the existing `/chat/rooms/{room_id}/users` endpoint to see who is currently *active* (online).
