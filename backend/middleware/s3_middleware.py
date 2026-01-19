"""
S3 middleware.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from config.aws_config import get_s3_client


class S3Middleware(BaseHTTPMiddleware):
    """S3 client middleware."""

    async def dispatch(self, request: Request, call_next):
        """Add S3 client to request state."""
        request.state.s3_client = get_s3_client()
        response = await call_next(request)
        return response
