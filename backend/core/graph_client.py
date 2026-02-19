"""NebulaGraph connection pool and query helpers.

Provides a singleton connection pool initialized on app startup.
All queries are automatically scoped to the 'graphops' space.
"""

import logging
from typing import Any, Optional

from nebula3.Config import Config as NebulaConfig
from nebula3.gclient.net import ConnectionPool
from nebula3.data.ResultSet import ResultSet

from backend.core.config import settings

logger = logging.getLogger(__name__)

_pool: Optional[ConnectionPool] = None


def init_graph_pool() -> ConnectionPool:
    """Initialize the NebulaGraph connection pool. Call once at app startup."""
    global _pool
    config = NebulaConfig()
    config.max_connection_pool_size = 10
    _pool = ConnectionPool()
    ok = _pool.init(
        [(settings.nebula_graphd_host, settings.nebula_graphd_port)],
        config,
    )
    if not ok:
        raise RuntimeError(
            f"Failed to connect to NebulaGraph at "
            f"{settings.nebula_graphd_host}:{settings.nebula_graphd_port}"
        )
    logger.info("NebulaGraph connection pool initialized")
    return _pool


def close_graph_pool() -> None:
    """Close the connection pool. Call at app shutdown."""
    global _pool
    if _pool:
        _pool.close()
        _pool = None
        logger.info("NebulaGraph connection pool closed")


def get_pool() -> ConnectionPool:
    """Get the active connection pool."""
    if _pool is None:
        raise RuntimeError("NebulaGraph pool not initialized. Call init_graph_pool() first.")
    return _pool


def execute_query(ngql: str) -> ResultSet:
    """Execute an nGQL query using a session from the pool.

    Automatically prefixes with USE <space>.
    """
    pool = get_pool()
    session = pool.get_session(settings.nebula_user, settings.nebula_password)
    try:
        # Always use the configured space
        use_result = session.execute(f"USE {settings.nebula_space}")
        if not use_result.is_succeeded():
            raise RuntimeError(f"Failed to USE {settings.nebula_space}: {use_result.error_msg()}")

        result = session.execute(ngql)
        if not result.is_succeeded():
            raise RuntimeError(f"nGQL query failed: {result.error_msg()}\nQuery: {ngql}")
        return result
    finally:
        session.release()


def execute_query_raw(ngql: str) -> ResultSet:
    """Execute an nGQL query without automatic USE prefix."""
    pool = get_pool()
    session = pool.get_session(settings.nebula_user, settings.nebula_password)
    try:
        result = session.execute(ngql)
        if not result.is_succeeded():
            raise RuntimeError(f"nGQL query failed: {result.error_msg()}\nQuery: {ngql}")
        return result
    finally:
        session.release()


def check_connection() -> bool:
    """Check if NebulaGraph is reachable."""
    try:
        result = execute_query("SHOW TAGS")
        return result.is_succeeded()
    except Exception:
        return False
