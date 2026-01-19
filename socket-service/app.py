"""
Socket Service FastAPI Application Entry Point.

Separate FastAPI application for WebSocket/Socket.IO real-time communication.
"""

import os
import sys
import logging
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Suppress watchfiles logging
logging.getLogger("watchfiles.main").setLevel(logging.ERROR)
logging.getLogger("watchfiles").setLevel(logging.ERROR)

# Set up environment variables early
from config.env_config import get_settings
from config.logging_config import setup_logging

# Initialize settings and logging
settings = get_settings()
setup_logging()

import socketio
from fastapi import FastAPI
from handlers.auth_handler import authenticate_connection, handle_connection_response
from handlers.chat_handler import (
    handle_message,
    handle_group_message,
    handle_join_room,
    handle_leave_room,
    handle_typing,
    handle_redis_message,
)
from handlers.receipt_handler import handle_read_receipt, handle_redis_receipt
from connection_manager import connection_manager
from services.pubsub_service import pubsub_service
from services.presence_service import presence_service
from utils.heartbeat import heartbeat_manager
from utils.constants import (
    EVENT_CONNECT,
    EVENT_DISCONNECT,
    EVENT_MESSAGE,
    EVENT_GROUP_MESSAGE,
    EVENT_JOIN_ROOM,
    EVENT_LEAVE_ROOM,
    EVENT_TYPING,
    EVENT_READ_RECEIPT,
    EVENT_HEARTBEAT,
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Dana Dairy Socket Service",
    description="WebSocket service for real-time chat and notifications",
    version="1.0.0",
)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    allow_eio3=True,
    logger=True,
    engineio_logger=True,
)

# Wrap Socket.IO with ASGI
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)


# Socket.IO Event Handlers
@sio.event
async def connect(sid: str, environ: dict):
    """
    Handle client connection with authentication.
    """
    logger.info(f"STEP 1: New connection attempt from session {sid}")

    # Authenticate connection
    user_info = await authenticate_connection(sid, environ)

    if not user_info:
        logger.error(f"STEP 2: Connection rejected for session {sid}")
        await sio.disconnect(sid)
        return False

    logger.info(f"STEP 2: Connection accepted for user {user_info.get('user_id')}")

    # Send connection response
    await handle_connection_response(sio, sid, user_info)

    # Register heartbeat
    heartbeat_manager.register_connection(sid)
    await heartbeat_manager.start_heartbeat_task(
        sid, sio, lambda session_id: sio.emit(EVENT_HEARTBEAT, {}, to=session_id)
    )

    logger.info(f"STEP 3: Connection setup complete for session {sid}")

    return True


@sio.event
async def disconnect(sid: str):
    """
    Handle client disconnection.
    """
    logger.info(f"STEP 1: Disconnecting session {sid}")

    # Unregister heartbeat
    heartbeat_manager.unregister_connection(sid)

    # Disconnect from connection manager
    connection_info = connection_manager.get_connection_info(sid)
    if connection_info:
        user_id = connection_info.get("user_id")
        connection_manager.disconnect(sid)

        logger.info(f"STEP 2: Session {sid} disconnected for user {user_id}")
    else:
        logger.warning(f"STEP 2: No connection info found for session {sid}")


@sio.on(EVENT_MESSAGE)
async def on_message(sid: str, data: dict):
    """
    Handle chat message event.
    """
    await handle_message(sio, sid, data)


@sio.on(EVENT_GROUP_MESSAGE)
async def on_group_message(sid: str, data: dict):
    """
    Handle group message event.
    """
    await handle_group_message(sio, sid, data)


@sio.on(EVENT_JOIN_ROOM)
async def on_join_room(sid: str, data: dict):
    """
    Handle join room event.
    """
    await handle_join_room(sio, sid, data)


@sio.on(EVENT_LEAVE_ROOM)
async def on_leave_room(sid: str, data: dict):
    """
    Handle leave room event.
    """
    await handle_leave_room(sio, sid, data)


@sio.on(EVENT_TYPING)
async def on_typing(sid: str, data: dict):
    """
    Handle typing indicator event.
    """
    await handle_typing(sio, sid, data)


@sio.on(EVENT_READ_RECEIPT)
async def on_read_receipt(sid: str, data: dict):
    """
    Handle read receipt event.
    """
    await handle_read_receipt(sio, sid, data)


@sio.on(EVENT_HEARTBEAT)
async def on_heartbeat(sid: str, data: dict):
    """
    Handle heartbeat/ping event.
    """
    heartbeat_manager.update_heartbeat(sid)


# Startup and Shutdown Events
@app.on_event("startup")
async def startup_event():
    """
    Initialize services on startup.
    """
    logger.info("STEP 1: Starting socket service")

    try:
        # Initialize Redis Pub/Sub
        await pubsub_service.initialize()

        # Note: Room-specific subscriptions will be created dynamically
        # when rooms are created/joined
        logger.info("STEP 2: Redis Pub/Sub initialized (room subscriptions will be dynamic)")

        logger.info("STEP 2: Socket service started successfully")

    except Exception as exc:
        logger.error(f"STEP 2: Error starting socket service: {exc}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup services on shutdown.
    """
    logger.info("STEP 1: Shutting down socket service")

    try:
        # Close Redis Pub/Sub connections
        await pubsub_service.close()

        # Cleanup presence
        presence_service.cleanup_stale_presence()

        logger.info("STEP 2: Socket service shut down successfully")

    except Exception as exc:
        logger.error(f"STEP 2: Error shutting down socket service: {exc}", exc_info=True)


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "socket-service",
        "connections": len(connection_manager.connections),
    }


# Export ASGI application
application = socket_app

if __name__ == "__main__":
    import uvicorn

    # Development server configuration
    host = os.getenv("SOCKET_SERVICE_HOST", "0.0.0.0")
    port = int(os.getenv("SOCKET_SERVICE_PORT", "8001"))

    uvicorn.run(
        "app:application",
        host=host,
        port=port,
        reload=settings.DEBUG,
        log_level="warning" if not settings.DEBUG else "info",
        access_log=True,
        use_colors=True,
    )

