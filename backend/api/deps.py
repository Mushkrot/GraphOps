"""FastAPI dependencies for workspace extraction and validation."""

from fastapi import HTTPException, Path


async def get_workspace_id(
    wid: str = Path(..., description="Workspace ID", min_length=1, max_length=64)
) -> str:
    """Extract and validate workspace_id from URL path.

    Returns the validated workspace_id string.
    Raises 400 if format is invalid.
    """
    if not wid.replace("_", "").isalnum():
        raise HTTPException(
            status_code=400,
            detail=f"Invalid workspace ID format: '{wid}'. "
                   f"Must be lowercase alphanumeric with underscores."
        )
    return wid
