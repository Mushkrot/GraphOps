"""Qdrant vector database client wrapper.

For M0: connection setup and health check only.
Collections will be created in M1 when ingestion starts.
"""

import logging
from typing import Optional

from qdrant_client import QdrantClient

from backend.core.config import settings

logger = logging.getLogger(__name__)

_client: Optional[QdrantClient] = None


def init_vector_client() -> QdrantClient:
    """Initialize the Qdrant client."""
    global _client
    _client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    logger.info("Qdrant client initialized")
    return _client


def get_vector_client() -> QdrantClient:
    """Get the active Qdrant client."""
    if _client is None:
        raise RuntimeError("Qdrant client not initialized.")
    return _client


def close_vector_client() -> None:
    """Close the Qdrant client."""
    global _client
    if _client:
        _client.close()
        _client = None
        logger.info("Qdrant client closed")


def check_connection() -> bool:
    """Check if Qdrant is reachable."""
    try:
        if _client is None:
            return False
        _client.get_collections()
        return True
    except Exception:
        return False
