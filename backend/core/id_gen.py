"""UUID v7 generator for time-sortable, globally unique IDs."""

from uuid_extensions import uuid7


def generate_id(prefix: str = "") -> str:
    """Generate a UUID v7 string with optional prefix.

    Args:
        prefix: e.g. "asrt_", "ce_", "pv_", "ent_", "ir_", "src_"

    Returns:
        String like "asrt_01926f4e8b7d7a8e9c0d1e2f3a4b5c6d" (no hyphens, fits 64 chars)
    """
    uid = uuid7().hex  # 32 hex chars, no hyphens
    return f"{prefix}{uid}" if prefix else uid
