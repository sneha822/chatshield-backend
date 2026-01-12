# Frontend Integration Guide: Toxic Message Muting System

This guide explains how to integrate the toxic message warning and muting system into your React + JavaScript frontend application.

## Table of Contents

1. [Overview](#overview)
2. [WebSocket Message Types](#websocket-message-types)
3. [Data Structures](#data-structures)
4. [Implementation Steps](#implementation-steps)
5. [Complete Code Examples](#complete-code-examples)
6. [UI/UX Best Practices](#uiux-best-practices)
7. [Testing](#testing)

---

## Overview

The muting system works as follows:

1. **Warning System**: When a user sends a toxic message, they receive a warning
2. **Consecutive Tracking**: The system tracks consecutive toxic messages (not total)
3. **Mute Trigger**: After **5 consecutive toxic messages**, the user is muted for **5 minutes**
4. **Room-Specific**: Mutes are specific to each chat room
5. **Auto-Unmute**: Users are automatically unmuted when the timer expires
6. **Cycle Repeats**: After unmute, the cycle resets and can happen again

### Key Behaviors

- Sending a **non-toxic message resets** the consecutive toxic count to 0
- The **total warning count** is cumulative and never resets
- Muted users **cannot send messages** until the mute expires
- The frontend receives real-time notifications for all mute-related events

---

## WebSocket Message Types

The backend sends the following new message types for the muting system:

| Type | Description | When Sent |
|------|-------------|-----------|
| `warning` | User sent a toxic message | After each toxic message (before mute) |
| `muted` | User has been muted | After 5th consecutive toxic message |
| `unmuted` | User's mute has expired | When mute timer expires |
| `mute_status` | Current mute status | On WebSocket connection |
| `mute_rejected` | Message rejected (user is muted) | When muted user tries to send |

---

## Data Structures

### MuteInfo Object

All mute-related messages include a `mute_info` object:

```javascript
{
  is_muted: boolean,           // Whether user is currently muted
  mute_expires_at: string,     // ISO timestamp when mute expires (UTC)
  remaining_seconds: number,   // Seconds until unmute (or null)
  warning_count: number,       // Total warnings received (cumulative)
  consecutive_toxic_count: number, // Current consecutive toxic messages
  total_mute_count: number,    // How many times user has been muted
  warnings_until_mute: number, // Messages until next mute (5 - consecutive)
  mute_duration_minutes: number, // Mute duration (5 minutes)
  toxic_threshold: number      // Consecutive toxics to trigger mute (5)
}
```

### Example Message Payloads

#### Warning Message
```javascript
{
  type: "warning",
  content: "⚠️ Your message was flagged as toxic. Warning 3/5...",
  sender: "System",
  timestamp: "2026-01-12T15:30:00.000Z",
  room_id: "general",
  mute_info: {
    is_muted: false,
    consecutive_toxic_count: 3,
    warnings_until_mute: 2,
    warning_count: 15,
    total_mute_count: 2,
    // ... other fields
  }
}
```

#### Muted Message (to the muted user)
```javascript
{
  type: "muted",
  content: "🔇 You have been muted for 5 minutes...",
  sender: "System",
  timestamp: "2026-01-12T15:30:00.000Z",
  room_id: "general",
  mute_info: {
    is_muted: true,
    mute_expires_at: "2026-01-12T15:35:00.000Z",
    remaining_seconds: 300,
    // ... other fields
  }
}
```

#### Muted Message (broadcast to room)
```javascript
{
  type: "muted",
  content: "john_doe has been muted for 5 minutes.",
  sender: "System",
  timestamp: "2026-01-12T15:30:00.000Z",
  room_id: "general",
  username: "john_doe",
  mute_expires_at: "2026-01-12T15:35:00.000Z"
}
```

#### Mute Rejected Message
```javascript
{
  type: "mute_rejected",
  content: "You are muted. Please wait 180 seconds.",
  sender: "System",
  timestamp: "2026-01-12T15:32:00.000Z",
  room_id: "general",
  mute_info: {
    is_muted: true,
    remaining_seconds: 180,
    // ... other fields
  }
}
```

---

## Implementation Steps

### Step 1: Create Mute State Management

Create a custom hook or context to manage mute state:

```javascript
// hooks/useMuteStatus.js
import { useState, useCallback, useEffect, useRef } from 'react';

export const useMuteStatus = () => {
  const [muteInfo, setMuteInfo] = useState({
    isMuted: false,
    muteExpiresAt: null,
    remainingSeconds: null,
    warningCount: 0,
    consecutiveToxicCount: 0,
    totalMuteCount: 0,
    warningsUntilMute: 5,
  });
  
  const timerRef = useRef(null);

  // Update mute info from server response
  const updateMuteInfo = useCallback((serverMuteInfo) => {
    setMuteInfo({
      isMuted: serverMuteInfo.is_muted ?? false,
      muteExpiresAt: serverMuteInfo.mute_expires_at ?? null,
      remainingSeconds: serverMuteInfo.remaining_seconds ?? null,
      warningCount: serverMuteInfo.warning_count ?? 0,
      consecutiveToxicCount: serverMuteInfo.consecutive_toxic_count ?? 0,
      totalMuteCount: serverMuteInfo.total_mute_count ?? 0,
      warningsUntilMute: serverMuteInfo.warnings_until_mute ?? 5,
    });
  }, []);

  // Start countdown timer when muted
  useEffect(() => {
    if (muteInfo.isMuted && muteInfo.remainingSeconds > 0) {
      // Clear any existing timer
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }

      timerRef.current = setInterval(() => {
        setMuteInfo(prev => {
          const newRemaining = Math.max(0, (prev.remainingSeconds ?? 0) - 1);
          
          // Auto-unmute when timer reaches 0
          if (newRemaining === 0) {
            clearInterval(timerRef.current);
            return {
              ...prev,
              isMuted: false,
              remainingSeconds: null,
              muteExpiresAt: null,
              consecutiveToxicCount: 0,
            };
          }
          
          return {
            ...prev,
            remainingSeconds: newRemaining,
          };
        });
      }, 1000);
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [muteInfo.isMuted, muteInfo.muteExpiresAt]);

  // Format remaining time for display
  const formatRemainingTime = useCallback(() => {
    if (!muteInfo.remainingSeconds) return null;
    
    const minutes = Math.floor(muteInfo.remainingSeconds / 60);
    const seconds = muteInfo.remainingSeconds % 60;
    
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  }, [muteInfo.remainingSeconds]);

  return {
    muteInfo,
    updateMuteInfo,
    formatRemainingTime,
    canSendMessage: !muteInfo.isMuted,
  };
};
```

### Step 2: Create Warning/Mute Notification Components

```javascript
// components/MuteNotifications.jsx
import React from 'react';
import './MuteNotifications.css';

// Warning Toast Component
export const WarningToast = ({ message, muteInfo, onClose }) => {
  return (
    <div className="warning-toast">
      <div className="warning-icon">⚠️</div>
      <div className="warning-content">
        <p className="warning-message">{message}</p>
        <div className="warning-progress">
          <div 
            className="warning-progress-bar"
            style={{ 
              width: `${(muteInfo.consecutiveToxicCount / muteInfo.toxic_threshold) * 100}%` 
            }}
          />
        </div>
        <p className="warning-count">
          {muteInfo.warningsUntilMute} more toxic messages until mute
        </p>
      </div>
      <button className="warning-close" onClick={onClose}>×</button>
    </div>
  );
};

// Mute Banner Component
export const MuteBanner = ({ remainingTime, muteInfo }) => {
  return (
    <div className="mute-banner">
      <div className="mute-icon">🔇</div>
      <div className="mute-content">
        <p className="mute-title">You are muted</p>
        <p className="mute-timer">
          Time remaining: <strong>{remainingTime}</strong>
        </p>
        <p className="mute-info">
          Total mutes in this room: {muteInfo.totalMuteCount}
        </p>
      </div>
    </div>
  );
};

// Unmute Notification Component
export const UnmuteNotification = ({ onClose }) => {
  return (
    <div className="unmute-notification">
      <div className="unmute-icon">🔊</div>
      <p>Your mute has expired. You can send messages again!</p>
      <button onClick={onClose}>OK</button>
    </div>
  );
};
```

### Step 3: Update WebSocket Message Handler

```javascript
// hooks/useWebSocket.js (or your existing WebSocket hook)
import { useCallback, useEffect, useRef, useState } from 'react';
import { useMuteStatus } from './useMuteStatus';

export const useWebSocket = (token, roomId) => {
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [notification, setNotification] = useState(null);
  const wsRef = useRef(null);
  
  const { muteInfo, updateMuteInfo, formatRemainingTime, canSendMessage } = useMuteStatus();

  // Handle incoming WebSocket messages
  const handleMessage = useCallback((event) => {
    const data = JSON.parse(event.data);
    
    switch (data.type) {
      case 'chat':
        // Regular chat message
        setMessages(prev => [...prev, data]);
        break;
        
      case 'mute_status':
        // Initial mute status on connection
        if (data.mute_info) {
          updateMuteInfo(data.mute_info);
        }
        break;
        
      case 'warning':
        // User received a warning for toxic message
        if (data.mute_info) {
          updateMuteInfo(data.mute_info);
        }
        setNotification({
          type: 'warning',
          message: data.content,
          muteInfo: data.mute_info,
        });
        // Auto-dismiss warning after 5 seconds
        setTimeout(() => setNotification(null), 5000);
        break;
        
      case 'muted':
        // User has been muted OR someone in room was muted
        if (data.mute_info) {
          // This is for the muted user themselves
          updateMuteInfo(data.mute_info);
          setNotification({
            type: 'muted',
            message: data.content,
            muteInfo: data.mute_info,
          });
        } else if (data.username) {
          // This is a broadcast about another user being muted
          setMessages(prev => [...prev, {
            type: 'system',
            content: data.content,
            sender: 'System',
            timestamp: data.timestamp,
          }]);
        }
        break;
        
      case 'unmuted':
        // User has been unmuted
        if (data.mute_info) {
          updateMuteInfo(data.mute_info);
          setNotification({
            type: 'unmuted',
            message: data.content,
          });
          // Auto-dismiss after 3 seconds
          setTimeout(() => setNotification(null), 3000);
        } else if (data.username) {
          // Broadcast about another user being unmuted
          setMessages(prev => [...prev, {
            type: 'system',
            content: data.content,
            sender: 'System',
            timestamp: data.timestamp,
          }]);
        }
        break;
        
      case 'mute_rejected':
        // Message was rejected because user is muted
        if (data.mute_info) {
          updateMuteInfo(data.mute_info);
        }
        setNotification({
          type: 'rejected',
          message: data.content,
          muteInfo: data.mute_info,
        });
        setTimeout(() => setNotification(null), 3000);
        break;
        
      case 'join':
      case 'leave':
      case 'sync':
        // Handle join/leave/sync as before
        if (data.content) {
          setMessages(prev => [...prev, data]);
        }
        break;
        
      case 'error':
        console.error('WebSocket error:', data.content);
        break;
        
      default:
        console.log('Unknown message type:', data.type);
    }
  }, [updateMuteInfo]);

  // Connect to WebSocket
  useEffect(() => {
    const wsUrl = `ws://localhost:8000/ws/${roomId}?token=${token}`;
    wsRef.current = new WebSocket(wsUrl);
    
    wsRef.current.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };
    
    wsRef.current.onmessage = handleMessage;
    
    wsRef.current.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    };
    
    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [token, roomId, handleMessage]);

  // Send message function
  const sendMessage = useCallback((content) => {
    if (!canSendMessage) {
      setNotification({
        type: 'rejected',
        message: `You are muted. Please wait ${formatRemainingTime()}.`,
        muteInfo: muteInfo,
      });
      return false;
    }
    
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ content }));
      return true;
    }
    return false;
  }, [canSendMessage, formatRemainingTime, muteInfo]);

  return {
    messages,
    isConnected,
    sendMessage,
    muteInfo,
    formatRemainingTime,
    canSendMessage,
    notification,
    clearNotification: () => setNotification(null),
  };
};
```

### Step 4: Create the Chat Component

```javascript
// components/ChatRoom.jsx
import React, { useState, useRef, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { WarningToast, MuteBanner, UnmuteNotification } from './MuteNotifications';
import './ChatRoom.css';

const ChatRoom = ({ token, roomId }) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);
  
  const {
    messages,
    isConnected,
    sendMessage,
    muteInfo,
    formatRemainingTime,
    canSendMessage,
    notification,
    clearNotification,
  } = useWebSocket(token, roomId);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim() && canSendMessage) {
      const success = sendMessage(inputValue);
      if (success) {
        setInputValue('');
      }
    }
  };

  return (
    <div className="chat-room">
      {/* Connection Status */}
      <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
        {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
      </div>

      {/* Mute Banner - Show when muted */}
      {muteInfo.isMuted && (
        <MuteBanner 
          remainingTime={formatRemainingTime()} 
          muteInfo={muteInfo} 
        />
      )}

      {/* Warning Progress Bar - Show when not muted but has warnings */}
      {!muteInfo.isMuted && muteInfo.consecutiveToxicCount > 0 && (
        <div className="warning-status">
          <span>⚠️ Toxic message warnings: {muteInfo.consecutiveToxicCount}/5</span>
          <div className="warning-progress-mini">
            <div 
              className="warning-progress-bar-mini"
              style={{ width: `${(muteInfo.consecutiveToxicCount / 5) * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Messages Container */}
      <div className="messages-container">
        {messages.map((msg, index) => (
          <MessageBubble key={index} message={msg} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form className="message-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder={
            muteInfo.isMuted 
              ? `Muted for ${formatRemainingTime()}...` 
              : "Type a message..."
          }
          disabled={!isConnected || muteInfo.isMuted}
          className={muteInfo.isMuted ? 'input-muted' : ''}
        />
        <button 
          type="submit" 
          disabled={!isConnected || !canSendMessage || !inputValue.trim()}
        >
          Send
        </button>
      </form>

      {/* Notifications */}
      {notification?.type === 'warning' && (
        <WarningToast
          message={notification.message}
          muteInfo={notification.muteInfo}
          onClose={clearNotification}
        />
      )}
      
      {notification?.type === 'unmuted' && (
        <UnmuteNotification onClose={clearNotification} />
      )}
      
      {notification?.type === 'rejected' && (
        <div className="rejected-toast">
          {notification.message}
        </div>
      )}
    </div>
  );
};

// Message Bubble Component
const MessageBubble = ({ message }) => {
  const isSystem = message.type === 'system' || message.sender === 'System';
  const isToxic = message.toxicity?.is_toxic;

  return (
    <div className={`message-bubble ${isSystem ? 'system' : 'user'} ${isToxic ? 'toxic' : ''}`}>
      {!isSystem && <span className="message-sender">{message.sender}</span>}
      <p className="message-content">{message.content}</p>
      {isToxic && (
        <span className="toxicity-badge" title={`Toxicity: ${Math.round(message.toxicity.toxicity * 100)}%`}>
          ⚠️ Toxic
        </span>
      )}
      <span className="message-time">
        {new Date(message.timestamp).toLocaleTimeString()}
      </span>
    </div>
  );
};

export default ChatRoom;
```

### Step 5: Add CSS Styles

```css
/* styles/MuteNotifications.css */

/* Warning Toast */
.warning-toast {
  position: fixed;
  top: 20px;
  right: 20px;
  background: linear-gradient(135deg, #ff9800, #f57c00);
  color: white;
  padding: 16px 20px;
  border-radius: 12px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  max-width: 400px;
  box-shadow: 0 4px 20px rgba(255, 152, 0, 0.4);
  animation: slideIn 0.3s ease-out;
  z-index: 1000;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.warning-icon {
  font-size: 24px;
}

.warning-content {
  flex: 1;
}

.warning-message {
  margin: 0 0 8px 0;
  font-weight: 500;
}

.warning-progress {
  height: 6px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 6px;
}

.warning-progress-bar {
  height: 100%;
  background: white;
  transition: width 0.3s ease;
}

.warning-count {
  margin: 0;
  font-size: 12px;
  opacity: 0.9;
}

.warning-close {
  background: none;
  border: none;
  color: white;
  font-size: 20px;
  cursor: pointer;
  padding: 0;
  opacity: 0.7;
}

.warning-close:hover {
  opacity: 1;
}

/* Mute Banner */
.mute-banner {
  background: linear-gradient(135deg, #ef5350, #c62828);
  color: white;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 0;
}

.mute-icon {
  font-size: 32px;
}

.mute-content {
  flex: 1;
}

.mute-title {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
}

.mute-timer {
  margin: 0 0 4px 0;
  font-size: 24px;
}

.mute-info {
  margin: 0;
  font-size: 12px;
  opacity: 0.8;
}

/* Unmute Notification */
.unmute-notification {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: linear-gradient(135deg, #4caf50, #2e7d32);
  color: white;
  padding: 24px 32px;
  border-radius: 16px;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  animation: popIn 0.3s ease-out;
  z-index: 1001;
}

@keyframes popIn {
  from {
    transform: translate(-50%, -50%) scale(0.8);
    opacity: 0;
  }
  to {
    transform: translate(-50%, -50%) scale(1);
    opacity: 1;
  }
}

.unmute-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.unmute-notification p {
  margin: 0 0 16px 0;
  font-size: 18px;
}

.unmute-notification button {
  background: white;
  color: #2e7d32;
  border: none;
  padding: 10px 32px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
}

/* Rejected Toast */
.rejected-toast {
  position: fixed;
  bottom: 100px;
  left: 50%;
  transform: translateX(-50%);
  background: #616161;
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  animation: fadeInUp 0.3s ease-out;
  z-index: 1000;
}

@keyframes fadeInUp {
  from {
    transform: translateX(-50%) translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateX(-50%) translateY(0);
    opacity: 1;
  }
}

/* Warning Status Bar (mini) */
.warning-status {
  background: #fff3e0;
  border-left: 4px solid #ff9800;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: #e65100;
}

.warning-progress-mini {
  flex: 1;
  max-width: 100px;
  height: 4px;
  background: #ffe0b2;
  border-radius: 2px;
  overflow: hidden;
}

.warning-progress-bar-mini {
  height: 100%;
  background: #ff9800;
  transition: width 0.3s ease;
}

/* Input Muted State */
.input-muted {
  background: #f5f5f5 !important;
  color: #9e9e9e !important;
  cursor: not-allowed;
}

/* Toxicity Badge */
.toxicity-badge {
  display: inline-block;
  background: #ffebee;
  color: #c62828;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  margin-left: 8px;
}

/* Message with toxic content */
.message-bubble.toxic {
  border-left: 3px solid #ef5350;
  background: linear-gradient(to right, #ffebee, transparent);
}
```

---

## Complete Code Examples

### Full Context Provider Implementation

For larger applications, use a React Context:

```javascript
// context/MuteContext.jsx
import React, { createContext, useContext, useReducer, useCallback } from 'react';

const MuteContext = createContext(null);

const initialState = {
  rooms: {}, // { roomId: muteInfo }
};

function muteReducer(state, action) {
  switch (action.type) {
    case 'UPDATE_MUTE_INFO':
      return {
        ...state,
        rooms: {
          ...state.rooms,
          [action.roomId]: action.muteInfo,
        },
      };
    case 'CLEAR_ROOM':
      const { [action.roomId]: _, ...remainingRooms } = state.rooms;
      return { ...state, rooms: remainingRooms };
    default:
      return state;
  }
}

export function MuteProvider({ children }) {
  const [state, dispatch] = useReducer(muteReducer, initialState);

  const updateMuteInfo = useCallback((roomId, muteInfo) => {
    dispatch({ type: 'UPDATE_MUTE_INFO', roomId, muteInfo });
  }, []);

  const getMuteInfo = useCallback((roomId) => {
    return state.rooms[roomId] || null;
  }, [state.rooms]);

  const isMutedInRoom = useCallback((roomId) => {
    return state.rooms[roomId]?.isMuted || false;
  }, [state.rooms]);

  return (
    <MuteContext.Provider value={{ 
      state, 
      updateMuteInfo, 
      getMuteInfo,
      isMutedInRoom 
    }}>
      {children}
    </MuteContext.Provider>
  );
}

export function useMuteContext() {
  const context = useContext(MuteContext);
  if (!context) {
    throw new Error('useMuteContext must be used within MuteProvider');
  }
  return context;
}
```

### Using with Redux

If you're using Redux:

```javascript
// redux/muteSlice.js
import { createSlice } from '@reduxjs/toolkit';

const muteSlice = createSlice({
  name: 'mute',
  initialState: {
    rooms: {},
    notifications: [],
  },
  reducers: {
    updateMuteInfo: (state, action) => {
      const { roomId, muteInfo } = action.payload;
      state.rooms[roomId] = {
        isMuted: muteInfo.is_muted,
        muteExpiresAt: muteInfo.mute_expires_at,
        remainingSeconds: muteInfo.remaining_seconds,
        warningCount: muteInfo.warning_count,
        consecutiveToxicCount: muteInfo.consecutive_toxic_count,
        totalMuteCount: muteInfo.total_mute_count,
        warningsUntilMute: muteInfo.warnings_until_mute,
      };
    },
    decrementTimer: (state, action) => {
      const { roomId } = action.payload;
      if (state.rooms[roomId]?.remainingSeconds > 0) {
        state.rooms[roomId].remainingSeconds -= 1;
      }
      if (state.rooms[roomId]?.remainingSeconds === 0) {
        state.rooms[roomId].isMuted = false;
        state.rooms[roomId].remainingSeconds = null;
      }
    },
    addNotification: (state, action) => {
      state.notifications.push({
        id: Date.now(),
        ...action.payload,
      });
    },
    removeNotification: (state, action) => {
      state.notifications = state.notifications.filter(
        n => n.id !== action.payload
      );
    },
  },
});

export const { 
  updateMuteInfo, 
  decrementTimer, 
  addNotification, 
  removeNotification 
} = muteSlice.actions;

export default muteSlice.reducer;

// Selectors
export const selectMuteInfo = (roomId) => (state) => state.mute.rooms[roomId];
export const selectIsMuted = (roomId) => (state) => state.mute.rooms[roomId]?.isMuted ?? false;
export const selectNotifications = (state) => state.mute.notifications;
```

---

## UI/UX Best Practices

### 1. Visual Feedback

- **Warning Progress**: Show a progress bar indicating how close the user is to being muted
- **Countdown Timer**: Display a real-time countdown when muted
- **Color Coding**: Use orange/amber for warnings, red for mutes, green for unmute

### 2. Non-Intrusive Notifications

```javascript
// Use toast notifications that auto-dismiss
const showWarningToast = (message, duration = 5000) => {
  // Show warning
  // Auto-dismiss after duration
};
```

### 3. Prevent Message Loss

```javascript
// Save draft message when muted
const handleMuted = () => {
  if (inputValue.trim()) {
    localStorage.setItem(`draft_${roomId}`, inputValue);
  }
};

// Restore draft when unmuted
const handleUnmuted = () => {
  const draft = localStorage.getItem(`draft_${roomId}`);
  if (draft) {
    setInputValue(draft);
    localStorage.removeItem(`draft_${roomId}`);
  }
};
```

### 4. Accessibility

```javascript
// Announce mute status changes to screen readers
useEffect(() => {
  if (muteInfo.isMuted) {
    const announcement = `You have been muted for ${formatRemainingTime()}`;
    // Use aria-live region
    setAriaAnnouncement(announcement);
  }
}, [muteInfo.isMuted]);

// In JSX:
<div aria-live="polite" className="sr-only">
  {ariaAnnouncement}
</div>
```

---

## Testing

### Test Cases to Cover

1. **Warning Flow**
   - Send 1-4 toxic messages, verify warning count increments
   - Send non-toxic message, verify count resets

2. **Mute Flow**
   - Send 5 toxic messages, verify user gets muted
   - Verify mute timer starts at 5 minutes
   - Try to send message while muted, verify rejection

3. **Unmute Flow**
   - Wait for mute to expire (or mock timer)
   - Verify unmute notification appears
   - Verify user can send messages again

4. **Room Isolation**
   - Get muted in Room A
   - Verify user can still chat in Room B

### Example Test

```javascript
// __tests__/muteSystem.test.js
import { renderHook, act } from '@testing-library/react-hooks';
import { useMuteStatus } from '../hooks/useMuteStatus';

describe('useMuteStatus', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('should start with default values', () => {
    const { result } = renderHook(() => useMuteStatus());
    
    expect(result.current.muteInfo.isMuted).toBe(false);
    expect(result.current.canSendMessage).toBe(true);
  });

  it('should update mute info from server response', () => {
    const { result } = renderHook(() => useMuteStatus());
    
    act(() => {
      result.current.updateMuteInfo({
        is_muted: true,
        remaining_seconds: 300,
        warning_count: 5,
        consecutive_toxic_count: 0,
      });
    });
    
    expect(result.current.muteInfo.isMuted).toBe(true);
    expect(result.current.muteInfo.remainingSeconds).toBe(300);
    expect(result.current.canSendMessage).toBe(false);
  });

  it('should countdown and auto-unmute', () => {
    const { result } = renderHook(() => useMuteStatus());
    
    act(() => {
      result.current.updateMuteInfo({
        is_muted: true,
        remaining_seconds: 3,
      });
    });
    
    expect(result.current.muteInfo.remainingSeconds).toBe(3);
    
    // Advance timer
    act(() => {
      jest.advanceTimersByTime(3000);
    });
    
    expect(result.current.muteInfo.isMuted).toBe(false);
    expect(result.current.canSendMessage).toBe(true);
  });
});
```

---

## Summary

The muting system provides:

| Feature | Implementation |
|---------|----------------|
| **Real-time warnings** | WebSocket `warning` messages |
| **Mute enforcement** | Backend rejects messages, sends `mute_rejected` |
| **Countdown timer** | Frontend timer + `remaining_seconds` from server |
| **Auto-unmute** | Server checks on each request, sends `unmuted` |
| **Room isolation** | `room_id` in all mute records |
| **Persistent stats** | Database stores `warning_count`, `total_mute_count` |

Remember to handle edge cases like:
- Reconnection while muted (server sends `mute_status` on connect)
- Multiple tabs (consider localStorage sync)
- Slow networks (optimistic UI with server confirmation)

For questions or issues, check the backend logs for detailed mute/warning events.
