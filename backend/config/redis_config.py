"""
Redis configuration.
"""

import redis
from config.env_config import settings

redis_client = redis.Redis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB, decode_responses=True
)


def get_redis():
    """Get Redis client."""
    return redis_client
