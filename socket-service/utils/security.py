"""
Security utilities for WebSocket authentication.
"""

import logging
import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from core.utils.jwt_hanlder import jwt_handler
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


async def validate_websocket_token(token: str) -> dict:
    """
    Validate JWT token for WebSocket connection.

    Args:
        token: JWT token string

    Returns:
        dict: Decoded token payload with user_id

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        logger.info("STEP 1: Validating WebSocket token")

        if not token:
            logger.error("Token is missing")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token required",
            )

        logger.info("STEP 2: Verifying JWT token")

        # Verify and decode token
        payload = jwt_handler.verify_token(token)
        user_id = payload.get("user_id")

        if not user_id:
            logger.error("Token does not contain user_id")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no user_id found",
            )

        logger.info(f"STEP 3: Token validated successfully for user_id: {user_id}")

        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "payload": payload,
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error validating WebSocket token: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


def extract_token_from_query(query_string: str) -> str | None:
    """
    Extract JWT token from query string.

    Args:
        query_string: Query string from WebSocket connection request

    Returns:
        str: Token if found, None otherwise
    """
    try:
        if not query_string:
            return None

        # Parse query string
        params = {}
        for param in query_string.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                params[key] = value

        return params.get("token") or params.get("access_token")

    except Exception as exc:
        logger.error(f"Error extracting token from query: {exc}")
        return None


def extract_token_from_headers(headers: dict) -> str | None:
    """
    Extract JWT token from headers.

    Args:
        headers: Request headers dictionary

    Returns:
        str: Token if found, None otherwise
    """
    try:
        # Check Authorization header
        auth_header = headers.get("authorization") or headers.get("Authorization")
        if auth_header:
            if auth_header.startswith("Bearer "):
                return auth_header[7:]
            return auth_header

        # Check custom header
        return headers.get("x-socket-token") or headers.get("X-Socket-Token")

    except Exception as exc:
        logger.error(f"Error extracting token from headers: {exc}")
        return None

