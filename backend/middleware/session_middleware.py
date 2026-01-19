"""
Session middleware.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi import Response
import uuid


class SessionMiddleware(BaseHTTPMiddleware):
    """Session management middleware."""

    async def dispatch(self, request: Request, call_next):
        """Process request with session."""
        session_id = request.cookies.get("session_id")

        if not session_id:
            session_id = str(uuid.uuid4())

        request.state.session_id = session_id

        response: Response = await call_next(request)
        response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=3600)

        return response
