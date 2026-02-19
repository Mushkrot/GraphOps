"""Ingestion Engine — orchestrates the full import pipeline.

Takes an Excel file + ingestion spec, parses rows, performs change detection
against existing graph data, and writes new/updated vertices and edges.

Synchronous-first design: runs inline in request handler. The function
signature is designed so it can be enqueued to RQ later with zero changes.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from backend.core import graph_ops
from backend.core.excel_parser import StagedRow, StagedEntity, StagedRelationship, parse_excel
from backend.core.hashing import (
    compute_assertion_key_property,
    compute_assertion_key_relationship,
    compute_property_normalized_hash,
    compute_property_raw_hash,
)
from backend.core.id_gen import generate_id
from backend.core.ingestion_spec import IngestionSpec
from backend.core.models import (
    AssertionRecordModel,
    ChangeEventModel,
    EventType,
    ImportRunModel,
    PropertyValueModel,
    SourceType,
    ValueType,
)

logger = logging.getLogger(__name__)


@dataclass
class ImportStats:
    """Tracks import statistics."""
    entities_created: int = 0
    entities_existing: int = 0
    assertions_created: int = 0
    assertions_closed: int = 0
    assertions_modified: int = 0
    assertions_unchanged: int = 0
    relationships_created: int = 0
    errors: int = 0


@dataclass
class ImportResult:
    """Result of an import run."""
    import_run_id: str
    status: str  # "completed" | "failed"
    stats: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    change_event_id: Optional[str] = None


def _get_comparison_hash(assertion: AssertionRecordModel, mode: str) -> str:
    """Get the hash to use for change detection based on mode."""
    if mode == "strict":
        return assertion.raw_hash
    return assertion.normalized_hash


def _infer_value_type(value) -> ValueType:
    """Infer ValueType from a Python value."""
    if isinstance(value, bool):
        return ValueType.BOOLEAN
    if isinstance(value, (int, float)):
        return ValueType.NUMBER
    if isinstance(value, (datetime,)):
        return ValueType.DATE
    return ValueType.STRING


def run_import(
    workspace_id: str,
    file_path: Path,
    spec: IngestionSpec,
    source_id: Optional[str] = None,
) -> ImportResult:
    """Run a full data import from an Excel file.

    Steps:
    1. Create ImportRun vertex (status=running)
    2. Parse Excel → staged rows
    3. Upsert entities (deduplicate by workspace + type + pk)
    4. Process property assertions (change detection)
    5. Process relationship assertions (change detection)
    6. Detect disappeared assertions from previous import
    7. Create ChangeEvent with CREATED/CLOSED edges
    8. Update ImportRun with stats
    """
    now = datetime.now(timezone.utc)
    import_run_id = generate_id("ir_")
    stats = ImportStats()
    errors: list[str] = []
    created_assertion_ids: list[str] = []
    closed_assertion_ids: list[str] = []

    # Step 1: Create ImportRun
    ir = ImportRunModel(
        import_run_id=import_run_id,
        workspace_id=workspace_id,
        source_file=str(file_path.name),
        spec_name=spec.spec_name,
        started_at=now,
        status="running",
    )
    try:
        graph_ops.insert_import_run(ir)
    except Exception as e:
        logger.error(f"Failed to create ImportRun: {e}")
        return ImportResult(import_run_id=import_run_id, status="failed", errors=[str(e)])

    try:
        # Step 2: Parse Excel
        staged_rows = parse_excel(file_path, spec)
        logger.info(f"Parsed {len(staged_rows)} rows from {file_path.name}")

        # Step 3: Upsert entities and build VID map
        entity_vid_map: dict[tuple[str, str], str] = {}  # (entity_type, primary_key) -> vid
        for row in staged_rows:
            for entity in row.entities:
                key = (entity.entity_type, entity.primary_key)
                if key not in entity_vid_map:
                    try:
                        vid = graph_ops.upsert_entity(
                            workspace_id, entity.entity_type,
                            entity.primary_key, entity.display_name,
                        )
                        entity_vid_map[key] = vid
                        if vid.startswith("ent_"):
                            stats.entities_created += 1
                        else:
                            stats.entities_existing += 1
                    except Exception as e:
                        errors.append(f"Entity upsert failed for {key}: {e}")
                        stats.errors += 1

        # Step 4: Process property assertions
        seen_assertion_keys: set[str] = set()
        change_mode = spec.change_detection.mode

        for row in staged_rows:
            for entity in row.entities:
                entity_key = (entity.entity_type, entity.primary_key)
                entity_vid = entity_vid_map.get(entity_key)
                if not entity_vid:
                    continue

                for prop_key, prop_value in entity.properties.items():
                    try:
                        _process_property_assertion(
                            workspace_id=workspace_id,
                            entity_vid=entity_vid,
                            entity_type=entity.entity_type,
                            primary_key=entity.primary_key,
                            property_key=prop_key,
                            value=prop_value,
                            source_ref=entity.source_ref,
                            source_id=source_id,
                            import_run_id=import_run_id,
                            spec=spec,
                            change_mode=change_mode,
                            now=now,
                            stats=stats,
                            created_ids=created_assertion_ids,
                            closed_ids=closed_assertion_ids,
                            seen_keys=seen_assertion_keys,
                        )
                    except Exception as e:
                        errors.append(f"Property assertion failed: {entity.entity_type}:{entity.primary_key}:{prop_key}: {e}")
                        stats.errors += 1

        # Step 5: Process relationship assertions
        for row in staged_rows:
            for rel in row.relationships:
                try:
                    _process_relationship_assertion(
                        workspace_id=workspace_id,
                        rel=rel,
                        entity_vid_map=entity_vid_map,
                        source_id=source_id,
                        import_run_id=import_run_id,
                        spec=spec,
                        change_mode=change_mode,
                        now=now,
                        stats=stats,
                        created_ids=created_assertion_ids,
                        closed_ids=closed_assertion_ids,
                        seen_keys=seen_assertion_keys,
                    )
                except Exception as e:
                    errors.append(f"Relationship assertion failed: {rel.relationship_type}: {e}")
                    stats.errors += 1

        # Step 6: Detect disappearances from previous import
        _detect_disappearances(
            workspace_id=workspace_id,
            spec_name=spec.spec_name,
            import_run_id=import_run_id,
            seen_keys=seen_assertion_keys,
            now=now,
            stats=stats,
            closed_ids=closed_assertion_ids,
        )

        # Step 7: Create ChangeEvent
        change_event_id = None
        if created_assertion_ids or closed_assertion_ids:
            change_event_id = _create_change_event(
                workspace_id=workspace_id,
                import_run_id=import_run_id,
                stats=stats,
                created_ids=created_assertion_ids,
                closed_ids=closed_assertion_ids,
                now=now,
            )

        # Step 8: Update ImportRun
        stats_dict = {
            "entities_created": stats.entities_created,
            "entities_existing": stats.entities_existing,
            "assertions_created": stats.assertions_created,
            "assertions_closed": stats.assertions_closed,
            "assertions_modified": stats.assertions_modified,
            "assertions_unchanged": stats.assertions_unchanged,
            "relationships_created": stats.relationships_created,
            "errors": stats.errors,
        }
        graph_ops.update_import_run(
            import_run_id,
            status="completed",
            completed_at=datetime.now(timezone.utc),
            stats=json.dumps(stats_dict),
        )

        return ImportResult(
            import_run_id=import_run_id,
            status="completed",
            stats=stats_dict,
            errors=errors,
            change_event_id=change_event_id,
        )

    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        graph_ops.update_import_run(
            import_run_id,
            status="failed",
            completed_at=datetime.now(timezone.utc),
            error_message=str(e),
        )
        return ImportResult(
            import_run_id=import_run_id,
            status="failed",
            errors=[str(e)],
        )


def _process_property_assertion(
    workspace_id: str,
    entity_vid: str,
    entity_type: str,
    primary_key: str,
    property_key: str,
    value,
    source_ref: str,
    source_id: Optional[str],
    import_run_id: str,
    spec: IngestionSpec,
    change_mode: str,
    now: datetime,
    stats: ImportStats,
    created_ids: list[str],
    closed_ids: list[str],
    seen_keys: set[str],
) -> None:
    """Process a single property assertion with change detection."""
    assertion_key = compute_assertion_key_property(
        workspace_id, entity_type, primary_key, property_key,
    )
    seen_keys.add(assertion_key)

    # Compute hashes for this property value
    raw_hash = compute_property_raw_hash(value, spec.raw_hash_serialization)
    normalized_hash = compute_property_normalized_hash(
        value, spec.raw_hash_serialization,
        spec.change_detection.normalization_rules,
        "string",
    )
    comparison_hash = raw_hash if change_mode == "strict" else normalized_hash

    # Lookup existing open assertions
    existing = graph_ops.lookup_assertions_by_key(workspace_id, assertion_key)

    if existing:
        existing_hash = _get_comparison_hash(existing[0], change_mode)
        if existing_hash == comparison_hash:
            stats.assertions_unchanged += 1
            return
        else:
            # Changed — close old, create new
            for old_assertion in existing:
                graph_ops.close_assertion(old_assertion.assertion_id, now)
                closed_ids.append(old_assertion.assertion_id)
            stats.assertions_modified += 1
    else:
        stats.assertions_created += 1

    # Create new PropertyValue vertex
    pv_id = generate_id("pv_")
    value_type = _infer_value_type(value)
    pv = PropertyValueModel(
        property_value_id=pv_id,
        workspace_id=workspace_id,
        property_key=property_key,
        value=str(value) if value is not None else None,
        value_type=value_type,
    )
    graph_ops.insert_property_value(pv)

    # Create new AssertionRecord
    assertion_id = generate_id("asrt_")
    assertion = AssertionRecordModel(
        assertion_id=assertion_id,
        workspace_id=workspace_id,
        assertion_key=assertion_key,
        raw_hash=raw_hash,
        normalized_hash=normalized_hash,
        source_type=SourceType.EXCEL,
        source_ref=source_ref,
        source_id=source_id,
        import_run_id=import_run_id,
        recorded_at=now,
        valid_from=now,
        scenario_id="base",
        confidence=1.0,
        relationship_type="HAS_PROPERTY",
        property_key=property_key,
    )
    graph_ops.insert_assertion(assertion)
    created_ids.append(assertion_id)

    # Create ASSERTED_REL edges: entity → assertion → property_value
    graph_ops.create_asserted_rel(entity_vid, assertion_id, pv_id)


def _process_relationship_assertion(
    workspace_id: str,
    rel: StagedRelationship,
    entity_vid_map: dict[tuple[str, str], str],
    source_id: Optional[str],
    import_run_id: str,
    spec: IngestionSpec,
    change_mode: str,
    now: datetime,
    stats: ImportStats,
    created_ids: list[str],
    closed_ids: list[str],
    seen_keys: set[str],
) -> None:
    """Process a single relationship assertion with change detection."""
    from_vid = entity_vid_map.get((rel.from_entity_type, rel.from_primary_key))
    to_vid = entity_vid_map.get((rel.to_entity_type, rel.to_primary_key))
    if not from_vid or not to_vid:
        return

    assertion_key = compute_assertion_key_relationship(
        workspace_id, rel.from_entity_type, rel.from_primary_key,
        rel.relationship_type, rel.to_entity_type, rel.to_primary_key,
    )
    seen_keys.add(assertion_key)

    # For relationships, hash is computed from the assertion key itself
    # (relationship identity is the key; the "value" IS the relationship)
    raw_hash = compute_property_raw_hash(assertion_key, spec.raw_hash_serialization)
    normalized_hash = compute_property_normalized_hash(
        assertion_key, spec.raw_hash_serialization,
        spec.change_detection.normalization_rules,
        "string",
    )
    comparison_hash = raw_hash if change_mode == "strict" else normalized_hash

    # Lookup existing
    existing = graph_ops.lookup_assertions_by_key(workspace_id, assertion_key)
    if existing:
        existing_hash = _get_comparison_hash(existing[0], change_mode)
        if existing_hash == comparison_hash:
            stats.assertions_unchanged += 1
            return
        else:
            for old in existing:
                graph_ops.close_assertion(old.assertion_id, now)
                closed_ids.append(old.assertion_id)
            stats.assertions_modified += 1
    else:
        stats.relationships_created += 1
        stats.assertions_created += 1

    # Create AssertionRecord
    assertion_id = generate_id("asrt_")
    assertion = AssertionRecordModel(
        assertion_id=assertion_id,
        workspace_id=workspace_id,
        assertion_key=assertion_key,
        raw_hash=raw_hash,
        normalized_hash=normalized_hash,
        source_type=SourceType.EXCEL,
        source_ref=rel.source_ref,
        source_id=source_id,
        import_run_id=import_run_id,
        recorded_at=now,
        valid_from=now,
        scenario_id="base",
        confidence=1.0,
        relationship_type=rel.relationship_type,
    )
    graph_ops.insert_assertion(assertion)
    created_ids.append(assertion_id)

    # Create ASSERTED_REL edges: from_entity → assertion → to_entity
    graph_ops.create_asserted_rel(from_vid, assertion_id, to_vid)


def _detect_disappearances(
    workspace_id: str,
    spec_name: str,
    import_run_id: str,
    seen_keys: set[str],
    now: datetime,
    stats: ImportStats,
    closed_ids: list[str],
) -> None:
    """Close assertions from previous import that weren't seen in current import."""
    # Find the previous import run for this spec
    all_runs = graph_ops.list_import_runs(workspace_id)
    previous_run = None
    for run in all_runs:
        if run.spec_name == spec_name and run.import_run_id != import_run_id and run.status == "completed":
            previous_run = run
            break  # list is sorted by started_at desc

    if not previous_run:
        return

    # Find all assertions from previous run
    prev_assertions = graph_ops.lookup_assertions_by_import_run(previous_run.import_run_id)
    for a in prev_assertions:
        if a.valid_to is not None:
            continue  # Already closed
        if a.assertion_key not in seen_keys:
            graph_ops.close_assertion(a.assertion_id, now)
            closed_ids.append(a.assertion_id)
            stats.assertions_closed += 1


def _create_change_event(
    workspace_id: str,
    import_run_id: str,
    stats: ImportStats,
    created_ids: list[str],
    closed_ids: list[str],
    now: datetime,
) -> str:
    """Create a ChangeEvent and link it to affected assertions."""
    change_event_id = generate_id("ce_")
    stats_dict = {
        "created": stats.assertions_created,
        "closed": stats.assertions_closed,
        "modified": stats.assertions_modified,
        "unchanged": stats.assertions_unchanged,
    }
    description = (
        f"Import run {import_run_id}: "
        f"{stats.assertions_created} created, "
        f"{stats.assertions_modified} modified, "
        f"{stats.assertions_closed} closed, "
        f"{stats.assertions_unchanged} unchanged"
    )
    ce = ChangeEventModel(
        change_event_id=change_event_id,
        workspace_id=workspace_id,
        event_type=EventType.IMPORT_DIFF,
        description=description,
        timestamp=now,
        import_run_id=import_run_id,
        actor="system:import",
        stats=json.dumps(stats_dict),
    )
    graph_ops.insert_change_event(ce)

    # Link to import run
    graph_ops.link_triggered_by(change_event_id, import_run_id)

    # Link to created assertions
    for aid in created_ids:
        graph_ops.link_created_assertion(change_event_id, aid)

    # Link to closed assertions
    for aid in closed_ids:
        graph_ops.link_closed_assertion(change_event_id, aid)

    return change_event_id
