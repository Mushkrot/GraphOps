"""Workspace-scoped entity endpoints — skeleton for M0.

Full implementation in M1 (after ingestion is working).
"""

from fastapi import APIRouter, Depends

from backend.api.deps import get_workspace_id

router = APIRouter()


@router.get("/entities/search")
async def search_entities(wid: str = Depends(get_workspace_id)):
    """Search entities. Not implemented in M0."""
    return {"status": "not_implemented", "message": "Entity search will be available in M1"}


@router.get("/entities/{entity_id}")
async def get_entity(entity_id: str, wid: str = Depends(get_workspace_id)):
    """Get entity details. Not implemented in M0."""
    return {"status": "not_implemented", "message": "Entity details will be available in M1"}
