"""Health check endpoint — verifies backend + all service connections."""

from fastapi import APIRouter

from backend.core import graph_client, vector_client, redis_client

router = APIRouter()


@router.get("/health")
async def health_check():
    """Check backend status and connectivity to all infrastructure services."""
    nebula_ok = graph_client.check_connection()
    qdrant_ok = vector_client.check_connection()
    redis_ok = redis_client.check_connection()

    all_ok = nebula_ok and qdrant_ok and redis_ok

    return {
        "status": "ok" if all_ok else "degraded",
        "services": {
            "nebula": "ok" if nebula_ok else "error",
            "qdrant": "ok" if qdrant_ok else "error",
            "redis": "ok" if redis_ok else "error",
        }
    }
