"""Workspace-scoped import endpoints — M1 implementation.

Handles file upload, import execution, status queries, and diff views.
"""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from backend.api.deps import get_workspace_id
from backend.core import graph_ops
from backend.core.ingestion_engine import run_import
from backend.core.models import ImportCreateResponse, ImportDiffResponse, ImportRunResponse
from backend.core.spec_loader import load_spec

logger = logging.getLogger(__name__)

router = APIRouter()

# Raw file storage directory
DATA_RAW_DIR = Path("data/raw")


@router.post("/imports", response_model=ImportCreateResponse)
async def create_import(
    file: UploadFile = File(...),
    spec_name: str = Form(...),
    wid: str = Depends(get_workspace_id),
):
    """Upload an Excel file and run data import.

    - **file**: Excel file (.xlsx)
    - **spec_name**: Name of the ingestion spec (without .yaml extension)
    """
    # Validate file type
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")

    # Load ingestion spec
    try:
        spec = load_spec(spec_name)
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail=f"Ingestion spec '{spec_name}' not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid ingestion spec: {e}")

    # Save uploaded file
    upload_dir = DATA_RAW_DIR / wid
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename
    content = await file.read()
    file_path.write_bytes(content)

    # Run import synchronously
    try:
        result = run_import(
            workspace_id=wid,
            file_path=file_path,
            spec=spec,
        )
    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Import failed: {e}")

    status_msg = "Import completed successfully" if result.status == "completed" else "Import failed"
    if result.errors:
        status_msg += f" with {len(result.errors)} errors"

    return ImportCreateResponse(
        import_run_id=result.import_run_id,
        status=result.status,
        message=status_msg,
    )


@router.get("/imports", response_model=list[ImportRunResponse])
async def list_imports(wid: str = Depends(get_workspace_id)):
    """List import runs for the workspace."""
    runs = graph_ops.list_import_runs(wid)
    return [
        ImportRunResponse(
            import_run_id=r.import_run_id,
            workspace_id=r.workspace_id,
            source_file=r.source_file,
            spec_name=r.spec_name,
            started_at=r.started_at,
            completed_at=r.completed_at,
            status=r.status,
            stats=json.loads(r.stats) if r.stats else None,
            error_message=r.error_message,
        )
        for r in runs
    ]


@router.get("/imports/{import_run_id}", response_model=ImportRunResponse)
async def get_import(import_run_id: str, wid: str = Depends(get_workspace_id)):
    """Get details of a specific import run."""
    ir = graph_ops.get_import_run(wid, import_run_id)
    if not ir:
        raise HTTPException(status_code=404, detail="Import run not found")
    return ImportRunResponse(
        import_run_id=ir.import_run_id,
        workspace_id=ir.workspace_id,
        source_file=ir.source_file,
        spec_name=ir.spec_name,
        started_at=ir.started_at,
        completed_at=ir.completed_at,
        status=ir.status,
        stats=json.loads(ir.stats) if ir.stats else None,
        error_message=ir.error_message,
    )


@router.get("/imports/{import_run_id}/diff", response_model=ImportDiffResponse)
async def get_import_diff(import_run_id: str, wid: str = Depends(get_workspace_id)):
    """Get the change diff for an import run.

    Returns the ChangeEvent details with lists of created and closed assertions.
    """
    # Verify import run exists and belongs to workspace
    ir = graph_ops.get_import_run(wid, import_run_id)
    if not ir:
        raise HTTPException(status_code=404, detail="Import run not found")

    # Find ChangeEvent for this import run
    # LOOKUP ChangeEvent by import_run_id
    from backend.core.graph_client import execute_query
    from backend.core.graph_ops import _escape

    ngql = (
        f'LOOKUP ON ChangeEvent WHERE ChangeEvent.import_run_id == {_escape(import_run_id)} '
        f'YIELD id(vertex) AS vid, ChangeEvent.stats AS stats;'
    )
    result = execute_query(ngql)

    if result.row_size() == 0:
        return ImportDiffResponse(import_run_id=import_run_id)

    ce_vid = result.row_values(0)[0].as_string()
    ce_stats_str = result.row_values(0)[1].as_string() if not result.row_values(0)[1].is_empty() else None
    ce_stats = json.loads(ce_stats_str) if ce_stats_str else None

    # Get created assertions
    created = _get_linked_assertions(ce_vid, "CREATED_ASSERTION")
    closed = _get_linked_assertions(ce_vid, "CLOSED_ASSERTION")

    return ImportDiffResponse(
        import_run_id=import_run_id,
        change_event_id=ce_vid,
        stats=ce_stats,
        created_assertions=created,
        closed_assertions=closed,
    )


def _get_linked_assertions(change_event_id: str, edge_type: str) -> list[dict]:
    """Get assertions linked to a ChangeEvent via CREATED/CLOSED edges."""
    from backend.core.graph_client import execute_query
    from backend.core.graph_ops import _escape

    ngql = (
        f'GO FROM {_escape(change_event_id)} OVER {edge_type} '
        f'YIELD dst(edge) AS assertion_vid;'
    )
    result = execute_query(ngql)
    if result.row_size() == 0:
        return []

    vids = [result.row_values(i)[0].as_string() for i in range(result.row_size())]
    assertions = graph_ops._fetch_assertions(vids, filter_open=False)
    return [a.model_dump(mode="json") for a in assertions]
