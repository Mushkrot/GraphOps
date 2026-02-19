"""Tests for the ingestion spec loader."""

import pytest
from unittest.mock import patch

from backend.core.spec_loader import load_spec, list_specs


class TestLoadSpec:
    def test_load_example_spec(self):
        """The _example_spec.yaml should not be listed (underscore prefix)."""
        specs = list_specs()
        assert "_example_spec" not in specs

    def test_load_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError):
            load_spec("nonexistent_spec")

    def test_load_example_directly(self):
        """Can load _example_spec directly by name (underscore is just list filter)."""
        spec = load_spec("_example_spec")
        assert spec.spec_name == "example_items"
        assert spec.workspace_id == "test_minimal"
        assert len(spec.sheets) == 1
        assert "item" in spec.sheets[0].entities
        assert spec.change_detection.mode == "normalized"


class TestListSpecs:
    def test_returns_list(self):
        specs = list_specs()
        assert isinstance(specs, list)
