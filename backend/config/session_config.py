"""
Session configuration.
"""

from config.env_config import settings


def get_session_config():
    """Get session configuration."""
    return {
        "secret_key": settings.SESSION_SECRET_KEY,
        "max_age": 3600,  # 1 hour
        "same_site": "lax",
        "httponly": True,
    }
