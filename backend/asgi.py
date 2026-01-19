"""
ASGI Configuration for Dana Dairy Backend

This module configures the ASGI application for the FastAPI backend.

It sets up the application for both development and production environments.

For more information on ASGI, see:

https://asgi.readthedocs.io/en/latest/

https://fastapi.tiangolo.com/deployment/

"""

import os
import sys
import logging
from pathlib import Path

# Suppress watchfiles logging BEFORE any other imports
# This must be done first to prevent infinite logging loops
logging.getLogger("watchfiles.main").setLevel(logging.ERROR)
logging.getLogger("watchfiles").setLevel(logging.ERROR)
logging.getLogger("watchfiles.main").propagate = False
logging.getLogger("watchfiles").propagate = False

# Add the project root directory to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up environment variables early
from config.env_config import get_settings
from config.logging_config import setup_logging

# Initialize settings and logging
settings = get_settings()
setup_logging()

try:
    # Import the FastAPI application
    from apps.server import app

    # ASGI application instance
    # Note: Socket.IO/WebSocket functionality has been migrated to socket-service/
    application = app

    print(f"🚀 ASGI application initialized successfully")
    print(f"📦 Project: {app.title}")
    print(f"🔢 Version: {app.version}")
    print(f"🔧 Debug Mode: {settings.DEBUG}")
    print(f"🌐 Environment: {settings.ENVIRONMENT}")
    print(f"📡 Socket Service: Running separately on port 8001 (see socket-service/app.py)")

except ImportError as e:
    print(f"❌ Failed to import FastAPI application: {e}")
    sys.exit(1)

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"❌ Unexpected error during ASGI initialization: {e}")
    sys.exit(1)

# Export the application for ASGI servers
__all__ = ["application"]

if __name__ == "__main__":
    import uvicorn

    # Development server configuration
    # Use default host and port, can be overridden by environment variables
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))

    uvicorn.run(
        "asgi:application",
        host=host,
        port=port,
        reload=settings.DEBUG,
        reload_excludes=[
            "venv/*",
            "node_modules/*",
            "*.log",
            "**/*.log",
            "app.log",
            "logs/*",
            "logs/**",
            "**/__pycache__/**",
            "**/.git/**",
            "*.pyc",
            "*.pyo",
        ],
        reload_delay=0.25,  # Add small delay to prevent rapid reloads
        log_level="warning" if not settings.DEBUG else "info",
        access_log=True,
        use_colors=True,
    )
