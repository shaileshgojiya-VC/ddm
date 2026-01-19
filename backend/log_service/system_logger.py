"""
System logger.
"""

import logging
from config.logging_config import setup_logging

logger = setup_logging()


def log_info(message: str):
    """Log info message."""
    logger.info(message)


def log_error(message: str, exc_info: bool = False):
    """Log error message."""
    logger.error(message, exc_info=exc_info)


def log_warning(message: str):
    """Log warning message."""
    logger.warning(message)


def log_debug(message: str):
    """Log debug message."""
    logger.debug(message)
