"""Redis client wrapper for job queue and cache.

For M0: connection setup and health check only.
Job queue (RQ) will be configured in M1.
"""

import logging
from typing import Optional

import redis as redis_lib

from backend.core.config import settings

logger = logging.getLogger(__name__)

_client: Optional[redis_lib.Redis] = None


def init_redis_client() -> redis_lib.Redis:
    """Initialize the Redis client."""
    global _client
    _client = redis_lib.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        decode_responses=True,
    )
    logger.info("Redis client initialized")
    return _client


def get_redis_client() -> redis_lib.Redis:
    """Get the active Redis client."""
    if _client is None:
        raise RuntimeError("Redis client not initialized.")
    return _client


def close_redis_client() -> None:
    """Close the Redis client."""
    global _client
    if _client:
        _client.close()
        _client = None
        logger.info("Redis client closed")


def check_connection() -> bool:
    """Check if Redis is reachable."""
    try:
        if _client is None:
            return False
        return _client.ping()
    except Exception:
        return False
