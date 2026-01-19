"""
CORS configuration.
"""

from config.env_config import settings


def get_cors_config():
    """Get CORS configuration."""
    allowed_origins = ["*"]  # Allow all origins   
    

    if settings.ENVIRONMENT == "production":
        # Add production origins
        pass

    return {
        "allow_origins": allowed_origins,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }
