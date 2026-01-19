"""
Authentication handler for WebSocket connections.
"""

import logging
from typing import Optional
from utils.security import validate_websocket_token, extract_token_from_query
from connection_manager import connection_manager
from utils.constants import EVENT_CONNECTION_RESPONSE, STATUS_CONNECTED

logger = logging.getLogger(__name__)


async def authenticate_connection(sid: str, environ: dict) -> Optional[dict]:
    """
    Authenticate WebSocket connection before accepting.

    Args:
        sid: Socket.IO session ID
        environ: WSGI environment dictionary

    Returns:
        dict with user_id and user info if authenticated, None otherwise
    """
    logger.info(f"STEP 1: Authenticating connection for session {sid}")

    try:
        # Extract token from query string or headers
        query_string = environ.get("QUERY_STRING", "")
        token = extract_token_from_query(query_string)

        if not token:
            # Try headers
            headers = {}
            for key, value in environ.items():
                if key.startswith("HTTP_"):
                    header_name = key[5:].replace("_", "-").lower()
                    headers[header_name] = value

            from utils.security import extract_token_from_headers

            token = extract_token_from_headers(headers)

        if not token:
            logger.error("STEP 2: No token found in connection request")
            return None

        logger.info("STEP 2: Token found, validating")

        # Validate token
        user_info = await validate_websocket_token(token)

        if not user_info:
            logger.error("STEP 3: Token validation failed")
            return None

        user_id = user_info.get("user_id")

        # Convert user_id to integer if it's a string
        if isinstance(user_id, str):
            try:
                user_id = int(user_id)
            except ValueError:
                logger.error(f"STEP 3: Invalid user_id format: {user_id}")
                return None

        logger.info(f"STEP 3: Connection authenticated for user {user_id}")

        # Register connection
        connection_manager.connect(session_id=sid, user_id=user_id)

        return {
            "user_id": user_id,
            "email": user_info.get("email"),
            "payload": user_info.get("payload"),
        }

    except Exception as exc:
        logger.error(f"STEP 3: Error authenticating connection: {exc}", exc_info=True)
        return None


async def handle_connection_response(sio, sid: str, user_info: dict) -> None:
    """
    Send connection response to client.

    Args:
        sio: Socket.IO server instance
        sid: Socket.IO session ID
        user_info: User information dictionary
    """
    logger.info(f"STEP 1: Sending connection response to session {sid}")

    await sio.emit(
        EVENT_CONNECTION_RESPONSE,
        {
            "status": STATUS_CONNECTED,
            "message": "Connected successfully",
            "session_id": sid,
            "user_id": user_info.get("user_id"),
        },
        to=sid,
    )

    logger.info(f"STEP 2: Connection response sent to session {sid}")

