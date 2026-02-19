"""GraphOps Intelligence Platform — FastAPI application entry point.

Initializes all service connections on startup and registers API routers.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.core import graph_client, vector_client, redis_client
from backend.core.schema_registry import SchemaRegistry
from backend.api import health, workspaces, schemas, entities, imports

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize service connections on startup, close on shutdown."""
    logger.info("Starting GraphOps backend...")

    # Initialize NebulaGraph connection pool
    try:
        graph_client.init_graph_pool()
    except Exception as e:
        logger.error(f"Failed to connect to NebulaGraph: {e}")

    # Initialize Qdrant client
    try:
        vector_client.init_vector_client()
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant: {e}")

    # Initialize Redis client
    try:
        redis_client.init_redis_client()
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")

    # Initialize schema registry
    app.state.schema_registry = SchemaRegistry()
    logger.info("Schema registry initialized")

    logger.info("GraphOps backend ready")
    yield

    # Shutdown
    logger.info("Shutting down GraphOps backend...")
    graph_client.close_graph_pool()
    vector_client.close_vector_client()
    redis_client.close_redis_client()
    logger.info("GraphOps backend stopped")


app = FastAPI(
    title="GraphOps Intelligence Platform",
    version="0.1.0",
    description="Universal platform for structuring, analyzing, and reasoning "
                "about complex multi-layered dependency data.",
    lifespan=lifespan,
)

# --- Top-level routes (not workspace-scoped) ---
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(workspaces.router, prefix="/api", tags=["workspaces"])

# --- Workspace-scoped routes: /api/w/{wid}/... ---
app.include_router(schemas.router, prefix="/api/w/{wid}", tags=["schemas"])
app.include_router(entities.router, prefix="/api/w/{wid}", tags=["entities"])
app.include_router(imports.router, prefix="/api/w/{wid}", tags=["imports"])
