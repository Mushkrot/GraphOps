"""Shared test fixtures for GraphOps test suite."""

from datetime import datetime, timezone
from typing import Optional

from backend.core.models import AssertionRecordModel, SourceType


def make_assertion(
    assertion_id: str = "a1",
    workspace_id: str = "test_ws",
    assertion_key: str = "entity1::HAS_PROPERTY::name",
    source_type: SourceType = SourceType.EXCEL,
    source_id: Optional[str] = "src_main",
    recorded_at: Optional[datetime] = None,
    valid_from: Optional[datetime] = None,
    valid_to: Optional[datetime] = None,
    scenario_id: str = "base",
    confidence: float = 1.0,
    relationship_type: str = "HAS_PROPERTY",
    property_key: Optional[str] = "name",
    **kwargs,
) -> AssertionRecordModel:
    """Helper to create assertion records for testing."""
    now = datetime.now(timezone.utc)
    return AssertionRecordModel(
        assertion_id=assertion_id,
        workspace_id=workspace_id,
        assertion_key=assertion_key,
        raw_hash="hash_" + assertion_id,
        normalized_hash="nhash_" + assertion_id,
        source_type=source_type,
        source_id=source_id,
        recorded_at=recorded_at or now,
        valid_from=valid_from or now,
        valid_to=valid_to,
        scenario_id=scenario_id,
        confidence=confidence,
        relationship_type=relationship_type,
        property_key=property_key,
        **kwargs,
    )
