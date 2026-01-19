"""
Logging Configuration

This module handles application logging configuration.

"""

import logging
import logging.config
import logging.handlers
import os
import sys
from pathlib import Path
from config.env_config import get_settings


class SafeStreamHandler(logging.StreamHandler):
    """StreamHandler that safely handles Unicode encoding errors."""
    
    def __init__(self, stream=None):
        if stream is None:
            stream = sys.stdout
        super().__init__(stream)
    
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # Try to write with error handling
            try:
                stream.write(msg + self.terminator)
            except UnicodeEncodeError:
                # If encoding fails, replace problematic characters
                safe_msg = msg.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
                stream.write(safe_msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


# Get settings
settings = get_settings()

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Validate log level
valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
log_level = (
    settings.LOG_LEVEL.upper()
    if hasattr(settings, "LOG_LEVEL") and settings.LOG_LEVEL
    else ("DEBUG" if settings.DEBUG else "INFO")
)

if log_level not in valid_log_levels:
    log_level = "INFO"

# Determine handlers based on environment
# In Docker/production, prefer console logging; file logging is optional
use_file_handlers = (
    not settings.DEBUG and os.path.exists("logs") and os.access("logs", os.W_OK)
) or settings.DEBUG  # Also use file handlers in debug mode

# Build handlers dict
handlers_dict = {
    "default": {
        "formatter": "default",
        "class": "logging.StreamHandler",
        "stream": "ext://sys.stdout",
    },
}

# Add file handlers only if directory is writable
if use_file_handlers:
    handlers_dict["file"] = {
        "formatter": "detailed",
        "class": "logging.handlers.RotatingFileHandler",
        "filename": "logs/app.log",
        "maxBytes": 10485760,  # 10MB
        "backupCount": 5,
        "encoding": "utf8",
    }
    handlers_dict["error_file"] = {
        "formatter": "detailed",
        "class": "logging.handlers.RotatingFileHandler",
        "filename": "logs/error.log",
        "maxBytes": 10485760,  # 10MB
        "backupCount": 5,
        "encoding": "utf8",
        "level": "ERROR",
    }

# Determine root logger handlers
root_handlers = ["default"]
if use_file_handlers:
    root_handlers.extend(["file", "error_file"])

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
        },
    },
    "handlers": handlers_dict,
    "loggers": {
        "": {  # root logger
            "level": log_level,
            "handlers": root_handlers,
        },
        "uvicorn": {
            "level": "WARNING" if settings.DEBUG else "INFO",
            "handlers": ["default"],
            "propagate": False,
        },
        "uvicorn.access": {
            "level": "WARNING",
            "handlers": [],
            "propagate": False,
        },
        "sqlalchemy.engine": {
            "level": "WARNING",
            "handlers": root_handlers if not settings.DEBUG else ["default"],
            "propagate": False,
        },
        "watchfiles": {
            "level": "ERROR",
            "handlers": [],
            "propagate": False,
        },
        "watchfiles.main": {
            "level": "ERROR",
            "handlers": [],
            "propagate": False,
        },
    },
}


def configure_logging():
    """Configure application logging."""
    # Suppress watchfiles logging BEFORE configuring
    logging.getLogger("watchfiles.main").setLevel(logging.ERROR)
    logging.getLogger("watchfiles").setLevel(logging.ERROR)
    logging.getLogger("watchfiles.main").propagate = False
    logging.getLogger("watchfiles").propagate = False
    
    try:
        logging.config.dictConfig(LOGGING_CONFIG)
        
        # Replace StreamHandler with SafeStreamHandler for Unicode support
        # This applies to root logger and any logger using the default handler
        def replace_stream_handlers(logger):
            for handler in logger.handlers[:]:
                if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                    logger.removeHandler(handler)
                    safe_handler = SafeStreamHandler(sys.stdout)
                    safe_handler.setFormatter(handler.formatter)
                    safe_handler.setLevel(handler.level)
                    logger.addHandler(safe_handler)
        
        # Replace for root logger
        replace_stream_handlers(logging.getLogger())
        
        # Replace for uvicorn logger if it exists
        uvicorn_logger = logging.getLogger("uvicorn")
        if uvicorn_logger.handlers:
            replace_stream_handlers(uvicorn_logger)
        
    except (ValueError, KeyError) as e:
        # Fallback to basic logging if configuration fails
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        logging.warning(
            f"Failed to configure logging from dict: {e}. Using basic logging."
        )


def setup_logging():
    """
    Setup application logging.
    Alias for configure_logging() for backward compatibility.
    """
    configure_logging()
    return logging.getLogger(__name__)


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance.

    Args:
        name: Logger name

    Returns:
        Logger: Logger instance
    """
    return logging.getLogger(name)
