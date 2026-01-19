"""
Session management utilities.
"""

from config.session_config import get_session_config
from config.redis_config import get_redis

session_config = get_session_config()
redis_client = get_redis()


def create_session(session_id: str, data: dict):
    """Create a session."""
    redis_client.setex(f"session:{session_id}", session_config["max_age"], str(data))


def get_session(session_id: str) -> dict:
    """Get session data."""
    data = redis_client.get(f"session:{session_id}")
    return eval(data) if data else {}


def delete_session(session_id: str):
    """Delete a session."""
    redis_client.delete(f"session:{session_id}")
