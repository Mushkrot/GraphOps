"""Dual-hash computation engine and assertion key builders.

Provides:
- raw_hash: SHA-256 of canonical row serialization (detects any cell value change)
- normalized_hash: SHA-256 after normalization rules (detects semantic changes only)
- Assertion key construction for relationships and properties

Both hashes are always computed and stored. The ingestion spec's change_detection
mode controls which hash triggers change detection during import.
"""

import hashlib
from datetime import date, datetime
from typing import Any, Optional

from backend.core.ingestion_spec import NormalizationRule, RawHashSerialization


def _serialize_value(value: Any, spec: RawHashSerialization) -> str:
    """Serialize a single cell value to its canonical string representation."""
    if value is None:
        return spec.null_representation

    if isinstance(value, bool):
        return str(value).lower()

    if isinstance(value, (int, float)):
        if spec.number_format == "as_displayed":
            return str(value)
        return str(value)

    if isinstance(value, (datetime, date)):
        if spec.date_format == "as_displayed":
            return str(value)
        return str(value)

    return str(value)


def compute_raw_hash(
    row_values: list[Any],
    spec: RawHashSerialization,
) -> str:
    """Compute raw_hash from canonical row serialization.

    Joins serialized cell values with the delimiter and returns SHA-256 hex.
    """
    parts = [_serialize_value(v, spec) for v in row_values]
    canonical = spec.delimiter.join(parts)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_value(
    value: Any,
    rules: NormalizationRule,
    value_type: str = "string",
) -> str:
    """Apply normalization rules to a single value."""
    if value is None:
        return ""

    s = str(value)

    # Check if value matches a null pattern
    if rules.normalize_nulls and s in rules.normalize_nulls:
        return ""

    # Trim whitespace
    if rules.trim_whitespace:
        s = s.strip()

    # Lowercase strings
    if rules.lowercase_strings and value_type == "string":
        s = s.lower()

    # Number formatting
    if rules.number_format and value_type == "number":
        decimal_places = rules.number_format.get("decimal_places")
        if decimal_places is not None:
            try:
                num = float(s)
                s = f"{num:.{decimal_places}f}"
            except (ValueError, TypeError):
                pass

    # Date formatting
    if rules.date_format and value_type == "date":
        fmt = rules.date_format
        # Try common date parsing
        for parse_fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
            try:
                dt = datetime.strptime(s, parse_fmt)
                # Convert format string from YYYY-MM-DD style to strftime
                out_fmt = fmt.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")
                s = dt.strftime(out_fmt)
                break
            except ValueError:
                continue

    return s


def compute_normalized_hash(
    row_values: list[Any],
    spec: RawHashSerialization,
    rules: NormalizationRule,
    value_types: Optional[list[str]] = None,
) -> str:
    """Compute normalized_hash after applying normalization rules.

    Same serialization pipeline as raw_hash, but values are normalized first.
    """
    if value_types is None:
        value_types = ["string"] * len(row_values)

    parts = []
    for i, value in enumerate(row_values):
        vtype = value_types[i] if i < len(value_types) else "string"
        normalized = _normalize_value(value, rules, vtype)
        parts.append(normalized)

    canonical = spec.delimiter.join(parts)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_property_raw_hash(
    value: Any,
    spec: RawHashSerialization,
) -> str:
    """Compute raw_hash for a single property value."""
    return compute_raw_hash([value], spec)


def compute_property_normalized_hash(
    value: Any,
    spec: RawHashSerialization,
    rules: NormalizationRule,
    value_type: str = "string",
) -> str:
    """Compute normalized_hash for a single property value."""
    return compute_normalized_hash([value], spec, rules, [value_type])


# ---------------------------------------------------------------------------
# Assertion key builders
# ---------------------------------------------------------------------------

def compute_assertion_key_relationship(
    workspace_id: str,
    entity_type_from: str,
    pk_from: str,
    relationship_type: str,
    entity_type_to: str,
    pk_to: str,
) -> str:
    """Build assertion_key for a relationship assertion.

    Format: {wid}:{type_from}:{pk_from}:{rel_type}:{type_to}:{pk_to}
    """
    return f"{workspace_id}:{entity_type_from}:{pk_from}:{relationship_type}:{entity_type_to}:{pk_to}"


def compute_assertion_key_property(
    workspace_id: str,
    entity_type: str,
    primary_key: str,
    property_key: str,
) -> str:
    """Build assertion_key for a property assertion.

    Format: {wid}:{entity_type}:{pk}:prop:{property_key}
    """
    return f"{workspace_id}:{entity_type}:{primary_key}:prop:{property_key}"
