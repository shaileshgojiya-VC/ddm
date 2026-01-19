# Socket Service

Separate FastAPI application for WebSocket/Socket.IO real-time communication.

## Overview

This service handles all real-time WebSocket communication for the Dana Dairy platform, including:
- One-to-one chat messaging
- Group chat messaging
- Read receipts tracking
- Presence tracking (online/offline status)
- Typing indicators
- Heartbeat/ping-pong for connection health

## Architecture

- **Separate FastAPI Application**: Runs independently on port 8001 (configurable)
- **Redis Pub/Sub**: Enables horizontal scaling across multiple instances
- **Connection Manager**: Tracks active connections, rooms, and presence
- **Pydantic Schemas**: Type-safe event validation
- **JWT Authentication**: Secure WebSocket connections

## Project Structure

```
socket-service/
├── app.py                    # FastAPI entry point
├── connection_manager.py     # Connection, room, presence management
├── handlers/
│   ├── auth_handler.py       # WebSocket authentication
│   ├── chat_handler.py      # Chat message events
│   └── receipt_handler.py   # Read receipt events
├── models/
│   └── schemas.py           # Pydantic event schemas
├── services/
│   ├── persistence_service.py  # DB operations
│   ├── pubsub_service.py       # Redis Pub/Sub
│   └── presence_service.py      # Presence tracking
├── utils/
│   ├── constants.py         # Socket-specific constants
│   ├── security.py          # JWT validation
│   └── heartbeat.py         # Ping/pong keep-alive
└── docs/
    └── asyncapi.yaml        # AsyncAPI specification
```

## Setup

1. Install dependencies:
```bash
cd socket-service
pip install -e .
```

2. Set environment variables (uses same `.env` as backend):
- `REDIS_HOST`
- `REDIS_PORT`
- `REDIS_DB`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- Database connection settings

3. Run the service:
```bash
python app.py
```

Or with uvicorn:
```bash
uvicorn app:application --host 0.0.0.0 --port 8001
```

## Connection

Clients connect with JWT token in query string or Authorization header:

```
ws://localhost:8001/?token=<JWT_TOKEN>
```

## Events

### Client → Server
- `message` - Send chat message (one-to-one)
- `group_message` - Send group message
- `join_room` - Join a conversation room
- `leave_room` - Leave a conversation room
- `typing` - Send typing indicator
- `read_receipt` - Mark message as read
- `heartbeat` - Ping/pong keep-alive

### Server → Client
- `connection_response` - Connection confirmation
- `message_response` - Message delivery confirmation
- `group_message_response` - Group message delivery
- `typing_response` - Typing indicator broadcast
- `read_receipt_response` - Read receipt broadcast
- `presence_response` - Presence status updates

## Database Migration

Run Alembic migration to create `message_read_receipts` table:

```bash
cd backend
alembic upgrade head
```

## Integration with Main Backend

The socket-service imports from the main backend:
- Database models (`apps.v1.api.chat.models`)
- Database methods (`apps.v1.api.chat.models.methods`)
- JWT handler (`core.utils.jwt_hanlder`)
- Redis config (`config.redis_config`)
- Environment config (`config.env_config`)

## Horizontal Scaling

The service uses Redis Pub/Sub to broadcast messages across multiple instances:

1. Instance A receives message → persists to DB → publishes to Redis
2. All instances (A, B, C) subscribe to Redis channels
3. Each instance delivers to its local connections
4. No sticky sessions required

## Documentation

See `docs/asyncapi.yaml` for complete API specification.

## Notes

- Socket.IO functionality has been migrated from `backend/apps/v1/api/chat/view.py`
- REST API endpoints remain in the main backend
- This service runs separately but shares database and Redis with main backend

