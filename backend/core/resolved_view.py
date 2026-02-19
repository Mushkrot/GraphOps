"""Resolved View Engine — assertion resolution algorithm (PRD 9.4).

Given a set of assertions for the same assertion_key, determines the
"winning" assertion based on the resolution priority chain:

1. Temporal validity: filter to valid_from <= at_time < valid_to
2. Scenario preference: prefer target scenario_id; fall back to base
3. Manual override: source_type=manual wins over all others
4. Authority rank: lowest authority_rank number wins (rank 1 > rank 2)
5. Recency: most recent recorded_at
6. Confidence: highest confidence value
"""

from datetime import datetime
from typing import Optional

from backend.core.models import AssertionRecordModel


def _filter_temporal(
    assertions: list[AssertionRecordModel],
    at_time: Optional[datetime] = None,
) -> list[AssertionRecordModel]:
    """Filter assertions to those valid at the given time."""
    if at_time is None:
        return assertions
    result = []
    for a in assertions:
        if a.valid_from > at_time:
            continue
        if a.valid_to is not None and a.valid_to <= at_time:
            continue
        result.append(a)
    return result


def _filter_scenario(
    assertions: list[AssertionRecordModel],
    scenario_id: str = "base",
) -> list[AssertionRecordModel]:
    """Prefer assertions in the target scenario; fall back to base."""
    scenario_assertions = [a for a in assertions if a.scenario_id == scenario_id]
    if scenario_assertions:
        return scenario_assertions
    if scenario_id != "base":
        return [a for a in assertions if a.scenario_id == "base"]
    return assertions


def resolve_assertion(
    assertions: list[AssertionRecordModel],
    scenario_id: str = "base",
    at_time: Optional[datetime] = None,
    source_authority: Optional[dict[str, int]] = None,
) -> Optional[AssertionRecordModel]:
    """Resolve a set of competing assertions to a single winner.

    Args:
        assertions: All assertions for the same assertion_key.
        scenario_id: Target scenario to prefer.
        at_time: Point-in-time filter (only valid assertions at this time).
        source_authority: Map of source_id -> authority_rank.
            If provided, overrides the assertion's own rank assumption.

    Returns:
        The winning assertion, or None if no valid assertions remain.
    """
    if not assertions:
        return None

    # Step 1: Temporal filter
    candidates = _filter_temporal(assertions, at_time)
    if not candidates:
        return None

    # Step 2: Scenario preference
    candidates = _filter_scenario(candidates, scenario_id)
    if not candidates:
        return None

    # Step 3: Manual override — source_type=manual wins
    manual = [a for a in candidates if a.source_type == "manual"]
    if manual:
        candidates = manual

    # Steps 4-5-6: Sort by authority (asc), recency (desc), confidence (desc)
    def sort_key(a: AssertionRecordModel):
        if source_authority and a.source_id and a.source_id in source_authority:
            rank = source_authority[a.source_id]
        else:
            # Default rank: high number (low priority) if unknown
            rank = 999
        return (
            rank,                       # Lower rank = higher authority (ascending)
            -a.recorded_at.timestamp(), # Most recent first (descending via negation)
            -a.confidence,              # Highest confidence first (descending via negation)
        )

    candidates.sort(key=sort_key)
    return candidates[0]


def resolve_entity_view(
    assertions: list[AssertionRecordModel],
    scenario_id: str = "base",
    at_time: Optional[datetime] = None,
    source_authority: Optional[dict[str, int]] = None,
) -> dict[str, AssertionRecordModel]:
    """Resolve all assertions for an entity, grouped by assertion_key.

    Returns a dict mapping assertion_key -> winning assertion.
    """
    grouped: dict[str, list[AssertionRecordModel]] = {}
    for a in assertions:
        grouped.setdefault(a.assertion_key, []).append(a)

    resolved = {}
    for key, group in grouped.items():
        winner = resolve_assertion(group, scenario_id, at_time, source_authority)
        if winner is not None:
            resolved[key] = winner
    return resolved


def get_all_claims(
    assertions: list[AssertionRecordModel],
    scenario_id: str = "base",
    at_time: Optional[datetime] = None,
    source_authority: Optional[dict[str, int]] = None,
) -> list[dict]:
    """Return all assertions annotated with is_winner flag.

    Each assertion is returned as a dict with an additional 'is_winner' field
    indicating whether it would be the resolved winner for its assertion_key.
    """
    winners = resolve_entity_view(assertions, scenario_id, at_time, source_authority)
    winner_ids = {w.assertion_id for w in winners.values()}

    result = []
    for a in assertions:
        claim = a.model_dump()
        claim["is_winner"] = a.assertion_id in winner_ids
        result.append(claim)
    return result
