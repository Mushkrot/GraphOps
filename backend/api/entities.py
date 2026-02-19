"""Workspace-scoped entity endpoints — M1 implementation.

Provides entity search and detail views with resolved view integration.
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.deps import get_workspace_id
from backend.core import graph_ops
from backend.core.graph_client import execute_query
from backend.core.graph_ops import _escape, _is_null
from backend.core.models import (
    EntityDetailResponse,
    EntitySearchResponse,
    EntitySearchResult,
    PropertyView,
    RelationshipView,
    ViewMode,
)
from backend.core.resolved_view import get_all_claims, resolve_entity_view

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/entities/search", response_model=EntitySearchResponse)
async def search_entities(
    wid: str = Depends(get_workspace_id),
    type: Optional[str] = Query(None, description="Filter by entity_type"),
    primary_key: Optional[str] = Query(None, description="Filter by primary_key"),
    q: Optional[str] = Query(None, description="Search display_name (prefix match)"),
    limit: int = Query(50, ge=1, le=200),
):
    """Search entities in the workspace.

    Supports filtering by entity_type, primary_key, or display_name prefix.
    """
    entities = graph_ops.search_entities(
        workspace_id=wid,
        entity_type=type,
        primary_key=primary_key,
        limit=limit,
    )

    # Apply display_name filter in Python if q is provided
    if q:
        q_lower = q.lower()
        entities = [
            e for e in entities
            if e.display_name and q_lower in e.display_name.lower()
        ]

    results = [
        EntitySearchResult(
            entity_id=e.entity_id,
            entity_type=e.entity_type,
            primary_key=e.primary_key,
            display_name=e.display_name,
        )
        for e in entities[:limit]
    ]
    return EntitySearchResponse(entities=results, total=len(results))


@router.get("/entities/{entity_id}", response_model=EntityDetailResponse)
async def get_entity(
    entity_id: str,
    wid: str = Depends(get_workspace_id),
    view_mode: ViewMode = Query(ViewMode.RESOLVED, description="View mode"),
    scenario_id: str = Query("base", description="Scenario ID"),
):
    """Get entity details with properties and relationships.

    Uses the resolved view engine to pick winning assertions per assertion_key.
    """
    # Fetch entity
    entity = graph_ops.get_entity(wid, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # Fetch all assertions for this entity
    assertions = graph_ops.get_assertions_for_entity(wid, entity_id)

    # Build source authority map
    authority_map = graph_ops.get_source_authority_map(wid)

    # Resolve or get all claims
    properties: list[PropertyView] = []
    relationships: list[RelationshipView] = []

    if view_mode == ViewMode.RESOLVED:
        resolved = resolve_entity_view(assertions, scenario_id, source_authority=authority_map)
        for key, winner in resolved.items():
            if winner.relationship_type == "HAS_PROPERTY":
                pv = _get_property_value_via_edge(winner.assertion_id)
                properties.append(PropertyView(
                    property_key=winner.property_key or "",
                    value=pv.get("value") if pv else None,
                    value_type=pv.get("value_type", "string") if pv else "string",
                    source_ref=winner.source_ref,
                    assertion_id=winner.assertion_id,
                    confidence=winner.confidence,
                ))
            else:
                target = _get_relationship_target(winner.assertion_id)
                if target:
                    relationships.append(RelationshipView(
                        relationship_type=winner.relationship_type,
                        target_entity_id=target["entity_id"],
                        target_entity_type=target["entity_type"],
                        target_primary_key=target["primary_key"],
                        target_display_name=target.get("display_name"),
                        assertion_id=winner.assertion_id,
                        source_ref=winner.source_ref,
                        confidence=winner.confidence,
                    ))
    else:
        # All claims mode
        all_claims = get_all_claims(assertions, scenario_id, source_authority=authority_map)
        for claim in all_claims:
            if claim.get("relationship_type") == "HAS_PROPERTY":
                pv = _get_property_value_via_edge(claim["assertion_id"])
                properties.append(PropertyView(
                    property_key=claim.get("property_key", ""),
                    value=pv.get("value") if pv else None,
                    value_type=pv.get("value_type", "string") if pv else "string",
                    source_ref=claim.get("source_ref"),
                    assertion_id=claim["assertion_id"],
                    confidence=claim.get("confidence", 1.0),
                ))
            else:
                target = _get_relationship_target(claim["assertion_id"])
                if target:
                    relationships.append(RelationshipView(
                        relationship_type=claim.get("relationship_type", ""),
                        target_entity_id=target["entity_id"],
                        target_entity_type=target["entity_type"],
                        target_primary_key=target["primary_key"],
                        target_display_name=target.get("display_name"),
                        assertion_id=claim["assertion_id"],
                        source_ref=claim.get("source_ref"),
                        confidence=claim.get("confidence", 1.0),
                    ))

    return EntityDetailResponse(
        entity_id=entity.entity_id,
        entity_type=entity.entity_type,
        primary_key=entity.primary_key,
        display_name=entity.display_name,
        properties=properties,
        relationships=relationships,
        view_mode=view_mode.value,
    )


def _get_property_value_via_edge(assertion_id: str) -> Optional[dict]:
    """Follow ASSERTED_REL from assertion to PropertyValue vertex."""
    try:
        ngql = (
            f'GO FROM {_escape(assertion_id)} OVER ASSERTED_REL '
            f'YIELD dst(edge) AS target_vid;'
        )
        result = execute_query(ngql)
        if result.row_size() == 0:
            return None

        # The target could be a PropertyValue or an Entity.
        # Try FETCH as PropertyValue first.
        for i in range(result.row_size()):
            vid = result.row_values(i)[0].as_string()
            pv_ngql = (
                f'FETCH PROP ON PropertyValue {_escape(vid)} '
                f'YIELD PropertyValue.property_key AS pk, PropertyValue.value AS val, '
                f'PropertyValue.value_type AS vt;'
            )
            pv_result = execute_query(pv_ngql)
            if pv_result.row_size() > 0:
                row = pv_result.row_values(0)
                return {
                    "property_key": row[0].as_string(),
                    "value": row[1].as_string() if not _is_null(row[1]) else None,
                    "value_type": row[2].as_string(),
                }
    except Exception as e:
        logger.warning(f"Failed to fetch PropertyValue for assertion {assertion_id}: {e}")
    return None


def _get_relationship_target(assertion_id: str) -> Optional[dict]:
    """Follow ASSERTED_REL from assertion to target Entity vertex."""
    try:
        ngql = (
            f'GO FROM {_escape(assertion_id)} OVER ASSERTED_REL '
            f'YIELD dst(edge) AS target_vid;'
        )
        result = execute_query(ngql)
        if result.row_size() == 0:
            return None

        for i in range(result.row_size()):
            vid = result.row_values(i)[0].as_string()
            ent_ngql = (
                f'FETCH PROP ON Entity {_escape(vid)} '
                f'YIELD id(vertex) AS vid, Entity.entity_type AS etype, '
                f'Entity.primary_key AS pk, Entity.display_name AS dname;'
            )
            ent_result = execute_query(ent_ngql)
            if ent_result.row_size() > 0:
                row = ent_result.row_values(0)
                return {
                    "entity_id": row[0].as_string(),
                    "entity_type": row[1].as_string(),
                    "primary_key": row[2].as_string(),
                    "display_name": row[3].as_string() if not _is_null(row[3]) else None,
                }
    except Exception as e:
        logger.warning(f"Failed to fetch target entity for assertion {assertion_id}: {e}")
    return None
