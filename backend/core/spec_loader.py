"""Ingestion Spec Loader — loads and validates YAML spec files."""

import logging
from pathlib import Path

import yaml

from backend.core.config import settings
from backend.core.ingestion_spec import IngestionSpec

logger = logging.getLogger(__name__)


def load_spec(spec_name: str) -> IngestionSpec:
    """Load an ingestion spec from the specs directory.

    Looks for {specs_dir}/{spec_name}.yaml
    """
    specs_dir = Path(settings.specs_dir)
    spec_path = specs_dir / f"{spec_name}.yaml"

    if not spec_path.exists():
        raise FileNotFoundError(f"Ingestion spec not found: {spec_path}")

    with open(spec_path) as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid spec format in {spec_path}: expected a YAML mapping")

    return IngestionSpec(**data)


def list_specs() -> list[str]:
    """List available spec names (without .yaml extension)."""
    specs_dir = Path(settings.specs_dir)
    if not specs_dir.exists():
        return []
    return [p.stem for p in specs_dir.glob("*.yaml") if not p.stem.startswith("_")]
