"""Workspace-scoped import endpoints — skeleton for M0.

Full implementation in M1 (ingestion engine).
"""

from fastapi import APIRouter, Depends

from backend.api.deps import get_workspace_id

router = APIRouter()


@router.get("/imports")
async def list_imports(wid: str = Depends(get_workspace_id)):
    """List import runs. Not implemented in M0."""
    return {"status": "not_implemented", "message": "Import management will be available in M1"}


@router.post("/imports")
async def create_import(wid: str = Depends(get_workspace_id)):
    """Upload file and create import job. Not implemented in M0."""
    return {"status": "not_implemented", "message": "Data import will be available in M1"}
