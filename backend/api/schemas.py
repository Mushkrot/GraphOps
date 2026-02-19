"""Workspace-scoped schema endpoints — GET /api/w/{wid}/schema."""

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.api.deps import get_workspace_id

router = APIRouter()


@router.get("/schema")
async def get_schema(request: Request, wid: str = Depends(get_workspace_id)):
    """Get the full domain schema definition for this workspace."""
    registry = request.app.state.schema_registry
    try:
        schema = registry.get_schema(wid)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Workspace '{wid}' not found")

    return schema.model_dump()


@router.get("/schema/entity-types")
async def list_entity_types(request: Request, wid: str = Depends(get_workspace_id)):
    """List all entity types defined in this workspace's schema."""
    registry = request.app.state.schema_registry
    try:
        schema = registry.get_schema(wid)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Workspace '{wid}' not found")

    return {
        name: etype.model_dump()
        for name, etype in schema.entity_types.items()
    }


@router.get("/schema/relationship-types")
async def list_relationship_types(request: Request, wid: str = Depends(get_workspace_id)):
    """List all relationship types defined in this workspace's schema."""
    registry = request.app.state.schema_registry
    try:
        schema = registry.get_schema(wid)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Workspace '{wid}' not found")

    return {
        name: rtype.model_dump()
        for name, rtype in schema.relationship_types.items()
    }
