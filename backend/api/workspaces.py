"""Workspace management endpoints (not workspace-scoped)."""

from fastapi import APIRouter, HTTPException, Request

from backend.core.models import WorkspaceCreate, WorkspaceResponse

router = APIRouter()


@router.get("/workspaces")
async def list_workspaces(request: Request):
    """List all registered workspaces."""
    registry = request.app.state.schema_registry
    workspace_ids = registry.list_schemas()
    return {"workspaces": workspace_ids}


@router.post("/workspaces", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(body: WorkspaceCreate, request: Request):
    """Create a new workspace with a domain schema."""
    registry = request.app.state.schema_registry
    try:
        schema = registry.load_schema_from_yaml(body.schema_yaml)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid schema YAML: {e}")

    if schema.workspace != body.workspace_id:
        raise HTTPException(
            status_code=400,
            detail=f"Schema workspace '{schema.workspace}' does not match "
                   f"request workspace_id '{body.workspace_id}'"
        )

    errors = registry.validate_schema(schema)
    if errors:
        raise HTTPException(status_code=400, detail={"validation_errors": errors})

    registry.register_schema(schema)

    return WorkspaceResponse(
        workspace_id=schema.workspace,
        display_name=body.display_name,
        schema_version=schema.version,
        entity_types=list(schema.entity_types.keys()),
        relationship_types=list(schema.relationship_types.keys()),
    )


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(workspace_id: str, request: Request):
    """Get workspace details and schema."""
    registry = request.app.state.schema_registry
    try:
        schema = registry.get_schema(workspace_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Workspace '{workspace_id}' not found")

    return WorkspaceResponse(
        workspace_id=schema.workspace,
        display_name=schema.workspace,  # TODO: store display_name separately
        schema_version=schema.version,
        entity_types=list(schema.entity_types.keys()),
        relationship_types=list(schema.relationship_types.keys()),
    )
