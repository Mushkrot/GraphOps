"""Graph Data Access Layer — nGQL CRUD wrappers for all core vertex/edge types.

All operations are scoped by workspace_id. Uses graph_client.execute_query()
which auto-prefixes with USE graphops.

VID format: FIXED_STRING(64). IDs are prefix + 32-char UUID7 hex (~36 chars).
nGQL rules: single-line statements, # comments, string values must be escaped.
ChangeEvent uses `ts` field (not `timestamp` — reserved word in NebulaGraph).
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from backend.core.graph_client import execute_query
from backend.core.id_gen import generate_id
from backend.core.models import (
    AssertionRecordModel,
    ChangeEventModel,
    EntityModel,
    ImportRunModel,
    PropertyValueModel,
    SourceModel,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _escape(value: str) -> str:
    """Escape a string value for nGQL insertion (single-quoted)."""
    if value is None:
        return "''"
    s = str(value)
    s = s.replace("\\", "\\\\")
    s = s.replace("'", "\\'")
    s = s.replace("\n", "\\n")
    s = s.replace("\r", "\\r")
    return f"'{s}'"


def _fmt_dt(dt: Optional[datetime]) -> str:
    """Format a Python datetime as an nGQL datetime literal."""
    if dt is None:
        return "NULL"
    return f'datetime("{dt.strftime("%Y-%m-%dT%H:%M:%S.%f")}")'


def _fmt_opt_str(value: Optional[str]) -> str:
    """Format an optional string: NULL or escaped."""
    if value is None:
        return "NULL"
    return _escape(value)


def _fmt_opt_dt(dt: Optional[datetime]) -> str:
    """Format an optional datetime."""
    return _fmt_dt(dt)


def _parse_entity_row(row) -> EntityModel:
    """Parse a NebulaGraph result row into EntityModel."""
    return EntityModel(
        entity_id=row[0].as_string(),
        workspace_id=row[1].as_string(),
        entity_type=row[2].as_string(),
        primary_key=row[3].as_string(),
        display_name=row[4].as_string() if not row[4].is_empty() else None,
        created_at=None,
        updated_at=None,
    )


def _parse_assertion_row(row) -> AssertionRecordModel:
    """Parse a NebulaGraph result row into AssertionRecordModel."""
    return AssertionRecordModel(
        assertion_id=row[0].as_string(),
        workspace_id=row[1].as_string(),
        assertion_key=row[2].as_string(),
        raw_hash=row[3].as_string(),
        normalized_hash=row[4].as_string(),
        source_type=row[5].as_string(),
        source_ref=row[6].as_string() if not row[6].is_empty() else None,
        source_id=row[7].as_string() if not row[7].is_empty() else None,
        import_run_id=row[8].as_string() if not row[8].is_empty() else None,
        recorded_at=row[9].as_datetime(),
        valid_from=row[10].as_datetime(),
        valid_to=row[11].as_datetime() if not row[11].is_empty() else None,
        scenario_id=row[12].as_string(),
        confidence=row[13].as_double(),
        supersedes=row[14].as_string() if not row[14].is_empty() else None,
        relationship_type=row[15].as_string(),
        property_key=row[16].as_string() if not row[16].is_empty() else None,
    )


def _parse_import_run_row(row) -> ImportRunModel:
    """Parse a NebulaGraph result row into ImportRunModel."""
    return ImportRunModel(
        import_run_id=row[0].as_string(),
        workspace_id=row[1].as_string(),
        source_file=row[2].as_string() if not row[2].is_empty() else None,
        spec_name=row[3].as_string() if not row[3].is_empty() else None,
        started_at=row[4].as_datetime(),
        completed_at=row[5].as_datetime() if not row[5].is_empty() else None,
        status=row[6].as_string(),
        stats=row[7].as_string() if not row[7].is_empty() else None,
        error_message=row[8].as_string() if not row[8].is_empty() else None,
    )


# ---------------------------------------------------------------------------
# Entity operations
# ---------------------------------------------------------------------------

def upsert_entity(
    workspace_id: str,
    entity_type: str,
    primary_key: str,
    display_name: Optional[str] = None,
) -> str:
    """Insert or find an existing Entity vertex. Returns the entity VID."""
    # First try to find existing entity
    existing = lookup_entity(workspace_id, entity_type, primary_key)
    if existing:
        return existing.entity_id

    # Create new entity
    entity_id = generate_id("ent_")
    now = datetime.now(timezone.utc)
    ngql = (
        f'INSERT VERTEX Entity(workspace_id, entity_type, primary_key, display_name, created_at, updated_at) '
        f'VALUES {_escape(entity_id)}:({_escape(workspace_id)}, {_escape(entity_type)}, '
        f'{_escape(primary_key)}, {_fmt_opt_str(display_name)}, {_fmt_dt(now)}, {_fmt_dt(now)});'
    )
    execute_query(ngql)
    return entity_id


def lookup_entity(
    workspace_id: str,
    entity_type: str,
    primary_key: str,
) -> Optional[EntityModel]:
    """Find an entity by workspace + type + primary_key. Returns None if not found."""
    ngql = (
        f'LOOKUP ON Entity WHERE Entity.workspace_id == {_escape(workspace_id)} '
        f'AND Entity.entity_type == {_escape(entity_type)} '
        f'AND Entity.primary_key == {_escape(primary_key)} '
        f'YIELD id(vertex) AS vid, Entity.workspace_id AS wid, Entity.entity_type AS etype, '
        f'Entity.primary_key AS pk, Entity.display_name AS dname;'
    )
    result = execute_query(ngql)
    if result.row_size() == 0:
        return None
    row = result.row_values(0)
    return EntityModel(
        entity_id=row[0].as_string(),
        workspace_id=row[1].as_string(),
        entity_type=row[2].as_string(),
        primary_key=row[3].as_string(),
        display_name=row[4].as_string() if not row[4].is_empty() else None,
    )


def get_entity(workspace_id: str, entity_id: str) -> Optional[EntityModel]:
    """Fetch a single Entity by VID."""
    ngql = (
        f'FETCH PROP ON Entity {_escape(entity_id)} '
        f'YIELD id(vertex) AS vid, Entity.workspace_id AS wid, Entity.entity_type AS etype, '
        f'Entity.primary_key AS pk, Entity.display_name AS dname, '
        f'Entity.created_at AS cat, Entity.updated_at AS uat;'
    )
    result = execute_query(ngql)
    if result.row_size() == 0:
        return None
    row = result.row_values(0)
    ent = EntityModel(
        entity_id=row[0].as_string(),
        workspace_id=row[1].as_string(),
        entity_type=row[2].as_string(),
        primary_key=row[3].as_string(),
        display_name=row[4].as_string() if not row[4].is_empty() else None,
    )
    # Validate workspace
    if ent.workspace_id != workspace_id:
        return None
    return ent


def search_entities(
    workspace_id: str,
    entity_type: Optional[str] = None,
    primary_key: Optional[str] = None,
    limit: int = 50,
) -> list[EntityModel]:
    """Search entities with optional filters."""
    conditions = [f'Entity.workspace_id == {_escape(workspace_id)}']
    if entity_type:
        conditions.append(f'Entity.entity_type == {_escape(entity_type)}')
    if primary_key:
        conditions.append(f'Entity.primary_key == {_escape(primary_key)}')

    where_clause = " AND ".join(conditions)
    ngql = (
        f'LOOKUP ON Entity WHERE {where_clause} '
        f'YIELD id(vertex) AS vid, Entity.workspace_id AS wid, Entity.entity_type AS etype, '
        f'Entity.primary_key AS pk, Entity.display_name AS dname '
        f'| LIMIT {limit};'
    )
    result = execute_query(ngql)
    entities = []
    for i in range(result.row_size()):
        row = result.row_values(i)
        entities.append(EntityModel(
            entity_id=row[0].as_string(),
            workspace_id=row[1].as_string(),
            entity_type=row[2].as_string(),
            primary_key=row[3].as_string(),
            display_name=row[4].as_string() if not row[4].is_empty() else None,
        ))
    return entities


# ---------------------------------------------------------------------------
# AssertionRecord operations
# ---------------------------------------------------------------------------

def insert_assertion(assertion: AssertionRecordModel) -> str:
    """Insert an AssertionRecord vertex. Returns the assertion VID."""
    a = assertion
    ngql = (
        f'INSERT VERTEX AssertionRecord(workspace_id, assertion_key, raw_hash, normalized_hash, '
        f'source_type, source_ref, source_id, import_run_id, recorded_at, valid_from, valid_to, '
        f'scenario_id, confidence, supersedes, relationship_type, property_key) '
        f'VALUES {_escape(a.assertion_id)}:({_escape(a.workspace_id)}, {_escape(a.assertion_key)}, '
        f'{_escape(a.raw_hash)}, {_escape(a.normalized_hash)}, {_escape(a.source_type.value if hasattr(a.source_type, "value") else str(a.source_type))}, '
        f'{_fmt_opt_str(a.source_ref)}, {_fmt_opt_str(a.source_id)}, {_fmt_opt_str(a.import_run_id)}, '
        f'{_fmt_dt(a.recorded_at)}, {_fmt_dt(a.valid_from)}, {_fmt_opt_dt(a.valid_to)}, '
        f'{_escape(a.scenario_id)}, {a.confidence}, {_fmt_opt_str(a.supersedes)}, '
        f'{_escape(a.relationship_type)}, {_fmt_opt_str(a.property_key)});'
    )
    execute_query(ngql)
    return a.assertion_id


def close_assertion(assertion_id: str, valid_to: datetime) -> None:
    """Close an assertion by setting valid_to."""
    ngql = (
        f'UPDATE VERTEX ON AssertionRecord {_escape(assertion_id)} '
        f'SET valid_to = {_fmt_dt(valid_to)};'
    )
    execute_query(ngql)


def lookup_assertions_by_key(
    workspace_id: str,
    assertion_key: str,
    scenario_id: str = "base",
) -> list[AssertionRecordModel]:
    """Find open assertions for a given assertion_key (valid_to is NULL).

    Since NebulaGraph LOOKUP can't filter on NULL, we fetch all and filter in Python.
    """
    ngql = (
        f'LOOKUP ON AssertionRecord WHERE AssertionRecord.workspace_id == {_escape(workspace_id)} '
        f'AND AssertionRecord.assertion_key == {_escape(assertion_key)} '
        f'AND AssertionRecord.scenario_id == {_escape(scenario_id)} '
        f'YIELD id(vertex) AS vid;'
    )
    result = execute_query(ngql)
    if result.row_size() == 0:
        return []

    # Fetch full properties
    vids = [result.row_values(i)[0].as_string() for i in range(result.row_size())]
    return _fetch_assertions(vids, filter_open=True)


def lookup_assertions_by_import_run(import_run_id: str) -> list[AssertionRecordModel]:
    """Find all assertions created in a specific import run."""
    ngql = (
        f'LOOKUP ON AssertionRecord WHERE AssertionRecord.import_run_id == {_escape(import_run_id)} '
        f'YIELD id(vertex) AS vid;'
    )
    result = execute_query(ngql)
    if result.row_size() == 0:
        return []

    vids = [result.row_values(i)[0].as_string() for i in range(result.row_size())]
    return _fetch_assertions(vids, filter_open=False)


def get_assertions_for_entity(workspace_id: str, entity_id: str) -> list[AssertionRecordModel]:
    """Get all assertions connected to an entity via ASSERTED_REL (reverse traversal)."""
    ngql = (
        f'GO FROM {_escape(entity_id)} OVER ASSERTED_REL REVERSELY '
        f'YIELD src(edge) AS assertion_vid;'
    )
    result = execute_query(ngql)
    if result.row_size() == 0:
        return []

    vids = [result.row_values(i)[0].as_string() for i in range(result.row_size())]
    assertions = _fetch_assertions(vids, filter_open=False)
    return [a for a in assertions if a.workspace_id == workspace_id]


def _fetch_assertions(vids: list[str], filter_open: bool = False) -> list[AssertionRecordModel]:
    """Fetch AssertionRecord vertices by VID list."""
    if not vids:
        return []

    vid_list = ", ".join(_escape(v) for v in vids)
    ngql = (
        f'FETCH PROP ON AssertionRecord {vid_list} '
        f'YIELD id(vertex) AS vid, '
        f'AssertionRecord.workspace_id AS wid, AssertionRecord.assertion_key AS akey, '
        f'AssertionRecord.raw_hash AS rh, AssertionRecord.normalized_hash AS nh, '
        f'AssertionRecord.source_type AS stype, AssertionRecord.source_ref AS sref, '
        f'AssertionRecord.source_id AS sid, AssertionRecord.import_run_id AS irid, '
        f'AssertionRecord.recorded_at AS rat, AssertionRecord.valid_from AS vf, '
        f'AssertionRecord.valid_to AS vt, AssertionRecord.scenario_id AS scid, '
        f'AssertionRecord.confidence AS conf, AssertionRecord.supersedes AS sups, '
        f'AssertionRecord.relationship_type AS rtype, AssertionRecord.property_key AS pkey;'
    )
    result = execute_query(ngql)
    assertions = []
    for i in range(result.row_size()):
        row = result.row_values(i)
        valid_to = None
        if not row[11].is_empty():
            valid_to = row[11].as_datetime()

        a = AssertionRecordModel(
            assertion_id=row[0].as_string(),
            workspace_id=row[1].as_string(),
            assertion_key=row[2].as_string(),
            raw_hash=row[3].as_string(),
            normalized_hash=row[4].as_string(),
            source_type=row[5].as_string(),
            source_ref=row[6].as_string() if not row[6].is_empty() else None,
            source_id=row[7].as_string() if not row[7].is_empty() else None,
            import_run_id=row[8].as_string() if not row[8].is_empty() else None,
            recorded_at=row[9].as_datetime(),
            valid_from=row[10].as_datetime(),
            valid_to=valid_to,
            scenario_id=row[12].as_string(),
            confidence=row[13].as_double(),
            supersedes=row[14].as_string() if not row[14].is_empty() else None,
            relationship_type=row[15].as_string(),
            property_key=row[16].as_string() if not row[16].is_empty() else None,
        )
        if filter_open and a.valid_to is not None:
            continue
        assertions.append(a)
    return assertions


# ---------------------------------------------------------------------------
# ASSERTED_REL edge operations
# ---------------------------------------------------------------------------

def create_asserted_rel(from_entity_id: str, assertion_id: str, to_entity_id: str) -> None:
    """Create ASSERTED_REL edges: from_entity→assertion and assertion→to_entity."""
    ngql = (
        f'INSERT EDGE ASSERTED_REL(assertion_id) '
        f'VALUES {_escape(from_entity_id)}->{_escape(assertion_id)}:({_escape(assertion_id)});'
    )
    execute_query(ngql)

    ngql2 = (
        f'INSERT EDGE ASSERTED_REL(assertion_id) '
        f'VALUES {_escape(assertion_id)}->{_escape(to_entity_id)}:({_escape(assertion_id)});'
    )
    execute_query(ngql2)


# ---------------------------------------------------------------------------
# PropertyValue operations
# ---------------------------------------------------------------------------

def insert_property_value(pv: PropertyValueModel) -> str:
    """Insert a PropertyValue vertex. Returns the VID."""
    ngql = (
        f'INSERT VERTEX PropertyValue(workspace_id, property_key, value, value_type) '
        f'VALUES {_escape(pv.property_value_id)}:({_escape(pv.workspace_id)}, '
        f'{_escape(pv.property_key)}, {_fmt_opt_str(pv.value)}, '
        f'{_escape(pv.value_type.value if hasattr(pv.value_type, "value") else str(pv.value_type))});'
    )
    execute_query(ngql)
    return pv.property_value_id


# ---------------------------------------------------------------------------
# ChangeEvent operations
# ---------------------------------------------------------------------------

def insert_change_event(ce: ChangeEventModel) -> str:
    """Insert a ChangeEvent vertex. Returns the VID."""
    ngql = (
        f'INSERT VERTEX ChangeEvent(workspace_id, event_type, description, ts, '
        f'import_run_id, actor, stats) '
        f'VALUES {_escape(ce.change_event_id)}:({_escape(ce.workspace_id)}, '
        f'{_escape(ce.event_type.value if hasattr(ce.event_type, "value") else str(ce.event_type))}, '
        f'{_fmt_opt_str(ce.description)}, {_fmt_dt(ce.timestamp)}, '
        f'{_fmt_opt_str(ce.import_run_id)}, {_fmt_opt_str(ce.actor)}, '
        f'{_fmt_opt_str(ce.stats)});'
    )
    execute_query(ngql)
    return ce.change_event_id


def link_created_assertion(change_event_id: str, assertion_id: str) -> None:
    """Create CREATED_ASSERTION edge from ChangeEvent to AssertionRecord."""
    ngql = (
        f'INSERT EDGE CREATED_ASSERTION(description) '
        f'VALUES {_escape(change_event_id)}->{_escape(assertion_id)}:({_escape("created")});'
    )
    execute_query(ngql)


def link_closed_assertion(change_event_id: str, assertion_id: str) -> None:
    """Create CLOSED_ASSERTION edge from ChangeEvent to AssertionRecord."""
    ngql = (
        f'INSERT EDGE CLOSED_ASSERTION(description) '
        f'VALUES {_escape(change_event_id)}->{_escape(assertion_id)}:({_escape("closed")});'
    )
    execute_query(ngql)


def link_triggered_by(change_event_id: str, trigger_id: str) -> None:
    """Create TRIGGERED_BY edge from ChangeEvent to the trigger (e.g., ImportRun)."""
    ngql = (
        f'INSERT EDGE TRIGGERED_BY(description) '
        f'VALUES {_escape(change_event_id)}->{_escape(trigger_id)}:({_escape("import")});'
    )
    execute_query(ngql)


# ---------------------------------------------------------------------------
# ImportRun operations
# ---------------------------------------------------------------------------

def insert_import_run(ir: ImportRunModel) -> str:
    """Insert an ImportRun vertex. Returns the VID."""
    ngql = (
        f'INSERT VERTEX ImportRun(workspace_id, source_file, spec_name, started_at, '
        f'completed_at, status, stats, error_message) '
        f'VALUES {_escape(ir.import_run_id)}:({_escape(ir.workspace_id)}, '
        f'{_fmt_opt_str(ir.source_file)}, {_fmt_opt_str(ir.spec_name)}, '
        f'{_fmt_dt(ir.started_at)}, {_fmt_opt_dt(ir.completed_at)}, '
        f'{_escape(ir.status)}, {_fmt_opt_str(ir.stats)}, {_fmt_opt_str(ir.error_message)});'
    )
    execute_query(ngql)
    return ir.import_run_id


def update_import_run(
    import_run_id: str,
    status: Optional[str] = None,
    completed_at: Optional[datetime] = None,
    stats: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    """Update an ImportRun vertex fields."""
    sets = []
    if status is not None:
        sets.append(f'status = {_escape(status)}')
    if completed_at is not None:
        sets.append(f'completed_at = {_fmt_dt(completed_at)}')
    if stats is not None:
        sets.append(f'stats = {_escape(stats)}')
    if error_message is not None:
        sets.append(f'error_message = {_escape(error_message)}')
    if not sets:
        return

    set_clause = ", ".join(sets)
    ngql = f'UPDATE VERTEX ON ImportRun {_escape(import_run_id)} SET {set_clause};'
    execute_query(ngql)


def get_import_run(workspace_id: str, import_run_id: str) -> Optional[ImportRunModel]:
    """Fetch a single ImportRun by VID."""
    ngql = (
        f'FETCH PROP ON ImportRun {_escape(import_run_id)} '
        f'YIELD id(vertex) AS vid, ImportRun.workspace_id AS wid, '
        f'ImportRun.source_file AS sf, ImportRun.spec_name AS sn, '
        f'ImportRun.started_at AS sa, ImportRun.completed_at AS ca, '
        f'ImportRun.status AS st, ImportRun.stats AS stats, '
        f'ImportRun.error_message AS em;'
    )
    result = execute_query(ngql)
    if result.row_size() == 0:
        return None
    row = result.row_values(0)
    ir = ImportRunModel(
        import_run_id=row[0].as_string(),
        workspace_id=row[1].as_string(),
        source_file=row[2].as_string() if not row[2].is_empty() else None,
        spec_name=row[3].as_string() if not row[3].is_empty() else None,
        started_at=row[4].as_datetime(),
        completed_at=row[5].as_datetime() if not row[5].is_empty() else None,
        status=row[6].as_string(),
        stats=row[7].as_string() if not row[7].is_empty() else None,
        error_message=row[8].as_string() if not row[8].is_empty() else None,
    )
    if ir.workspace_id != workspace_id:
        return None
    return ir


def list_import_runs(workspace_id: str, limit: int = 50) -> list[ImportRunModel]:
    """List import runs for a workspace."""
    ngql = (
        f'LOOKUP ON ImportRun WHERE ImportRun.workspace_id == {_escape(workspace_id)} '
        f'YIELD id(vertex) AS vid;'
    )
    result = execute_query(ngql)
    if result.row_size() == 0:
        return []

    vids = [result.row_values(i)[0].as_string() for i in range(result.row_size())]
    vid_list = ", ".join(_escape(v) for v in vids[:limit])
    ngql2 = (
        f'FETCH PROP ON ImportRun {vid_list} '
        f'YIELD id(vertex) AS vid, ImportRun.workspace_id AS wid, '
        f'ImportRun.source_file AS sf, ImportRun.spec_name AS sn, '
        f'ImportRun.started_at AS sa, ImportRun.completed_at AS ca, '
        f'ImportRun.status AS st, ImportRun.stats AS stats, '
        f'ImportRun.error_message AS em;'
    )
    result2 = execute_query(ngql2)
    runs = []
    for i in range(result2.row_size()):
        row = result2.row_values(i)
        runs.append(ImportRunModel(
            import_run_id=row[0].as_string(),
            workspace_id=row[1].as_string(),
            source_file=row[2].as_string() if not row[2].is_empty() else None,
            spec_name=row[3].as_string() if not row[3].is_empty() else None,
            started_at=row[4].as_datetime(),
            completed_at=row[5].as_datetime() if not row[5].is_empty() else None,
            status=row[6].as_string(),
            stats=row[7].as_string() if not row[7].is_empty() else None,
            error_message=row[8].as_string() if not row[8].is_empty() else None,
        ))
    # Sort by started_at descending
    runs.sort(key=lambda r: r.started_at, reverse=True)
    return runs


# ---------------------------------------------------------------------------
# Source operations
# ---------------------------------------------------------------------------

def upsert_source(source: SourceModel) -> str:
    """Insert or update a Source vertex. Returns the VID."""
    ngql = (
        f'INSERT VERTEX Source(workspace_id, source_name, source_type, authority_rank, '
        f'authority_domains, update_frequency, description) '
        f'VALUES {_escape(source.source_id)}:({_escape(source.workspace_id)}, '
        f'{_escape(source.source_name)}, {_escape(source.source_type)}, '
        f'{source.authority_rank}, {_fmt_opt_str(source.authority_domains)}, '
        f'{_fmt_opt_str(source.update_frequency)}, {_fmt_opt_str(source.description)});'
    )
    execute_query(ngql)
    return source.source_id


def list_sources(workspace_id: str) -> list[SourceModel]:
    """List all registered sources for a workspace."""
    ngql = (
        f'LOOKUP ON Source WHERE Source.workspace_id == {_escape(workspace_id)} '
        f'YIELD id(vertex) AS vid, Source.workspace_id AS wid, Source.source_name AS sn, '
        f'Source.source_type AS st, Source.authority_rank AS ar, '
        f'Source.authority_domains AS ad, Source.update_frequency AS uf, '
        f'Source.description AS desc;'
    )
    result = execute_query(ngql)
    sources = []
    for i in range(result.row_size()):
        row = result.row_values(i)
        sources.append(SourceModel(
            source_id=row[0].as_string(),
            workspace_id=row[1].as_string(),
            source_name=row[2].as_string(),
            source_type=row[3].as_string(),
            authority_rank=row[4].as_int(),
            authority_domains=row[5].as_string() if not row[5].is_empty() else None,
            update_frequency=row[6].as_string() if not row[6].is_empty() else None,
            description=row[7].as_string() if not row[7].is_empty() else None,
        ))
    return sources


def get_source_authority_map(workspace_id: str) -> dict[str, int]:
    """Build a source_id -> authority_rank map for resolved view."""
    sources = list_sources(workspace_id)
    return {s.source_id: s.authority_rank for s in sources}
