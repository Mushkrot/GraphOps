"""Tests for the ingestion engine — mocked graph_ops for unit testing."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import openpyxl
import pytest

from backend.core.ingestion_engine import (
    ImportResult,
    ImportStats,
    run_import,
    _get_comparison_hash,
)
from backend.core.ingestion_spec import (
    ChangeDetection,
    ColumnMapping,
    EntityMapping,
    IngestionSpec,
    NormalizationRule,
    RawHashSerialization,
    RelationshipMapping,
    SheetSpec,
)
from backend.core.models import AssertionRecordModel, SourceType


def _create_test_workbook(rows: list[list], sheet_name: str = "Items") -> Path:
    """Create a test Excel file."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name
    for row in rows:
        ws.append(row)
    path = Path(tempfile.mktemp(suffix=".xlsx"))
    wb.save(path)
    wb.close()
    return path


def _make_spec(mode: str = "normalized") -> IngestionSpec:
    """Build a test ingestion spec."""
    return IngestionSpec(
        spec_name="test_spec",
        spec_version="1.0",
        workspace_id="test_ws",
        change_detection=ChangeDetection(mode=mode),
        sheets=[
            SheetSpec(
                sheet_name="Items",
                header_row=0,
                entities={
                    "item": EntityMapping(
                        entity_type="Item",
                        key_columns=["item_code"],
                        key_template="{item_code}",
                        properties=[
                            ColumnMapping(source_column="Item Code", target_property="item_code"),
                            ColumnMapping(source_column="Name", target_property="name"),
                            ColumnMapping(source_column="Price", target_property="price"),
                        ],
                    ),
                },
                relationships=[],
            )
        ],
    )


def _make_spec_with_relationships() -> IngestionSpec:
    return IngestionSpec(
        spec_name="test_spec",
        spec_version="1.0",
        workspace_id="test_ws",
        sheets=[
            SheetSpec(
                sheet_name="Items",
                header_row=0,
                entities={
                    "item": EntityMapping(
                        entity_type="Item",
                        key_columns=["item_code"],
                        key_template="{item_code}",
                        properties=[
                            ColumnMapping(source_column="Item Code", target_property="item_code"),
                            ColumnMapping(source_column="Name", target_property="name"),
                        ],
                    ),
                    "category": EntityMapping(
                        entity_type="Category",
                        key_columns=["category_code"],
                        key_template="{category_code}",
                        properties=[
                            ColumnMapping(source_column="Category Code", target_property="category_code"),
                            ColumnMapping(source_column="Category Name", target_property="name"),
                        ],
                    ),
                },
                relationships=[
                    RelationshipMapping(
                        relationship_type="BELONGS_TO",
                        from_entity="item",
                        to_entity="category",
                    ),
                ],
            )
        ],
    )


# ---------------------------------------------------------------------------
# Helper tests
# ---------------------------------------------------------------------------

class TestGetComparisonHash:
    def test_strict_returns_raw_hash(self):
        a = AssertionRecordModel(
            assertion_id="a1", workspace_id="ws", assertion_key="k",
            raw_hash="raw123", normalized_hash="norm456",
            source_type=SourceType.EXCEL, recorded_at=datetime.now(timezone.utc),
            valid_from=datetime.now(timezone.utc), relationship_type="HAS_PROPERTY",
        )
        assert _get_comparison_hash(a, "strict") == "raw123"

    def test_normalized_returns_normalized_hash(self):
        a = AssertionRecordModel(
            assertion_id="a1", workspace_id="ws", assertion_key="k",
            raw_hash="raw123", normalized_hash="norm456",
            source_type=SourceType.EXCEL, recorded_at=datetime.now(timezone.utc),
            valid_from=datetime.now(timezone.utc), relationship_type="HAS_PROPERTY",
        )
        assert _get_comparison_hash(a, "normalized") == "norm456"


# ---------------------------------------------------------------------------
# Import run tests (mocked graph_ops)
# ---------------------------------------------------------------------------

class TestRunImport:
    @patch("backend.core.ingestion_engine.graph_ops")
    def test_new_import_creates_entities_and_assertions(self, mock_ops):
        """First import — all entities and assertions should be created."""
        mock_ops.insert_import_run.return_value = "ir_1"
        mock_ops.upsert_entity.return_value = "ent_1"
        mock_ops.lookup_assertions_by_key.return_value = []
        mock_ops.insert_property_value.return_value = "pv_1"
        mock_ops.insert_assertion.return_value = "asrt_1"
        mock_ops.list_import_runs.return_value = []

        path = _create_test_workbook([
            ["Item Code", "Name", "Price"],
            ["ITM001", "Widget", 9.99],
        ])
        spec = _make_spec()
        result = run_import("test_ws", path, spec)

        assert result.status == "completed"
        assert result.stats["assertions_created"] > 0
        assert result.stats["assertions_unchanged"] == 0
        assert mock_ops.upsert_entity.called
        assert mock_ops.insert_assertion.called
        assert mock_ops.insert_property_value.called
        assert mock_ops.create_asserted_rel.called
        path.unlink()

    @patch("backend.core.ingestion_engine.graph_ops")
    def test_reimport_unchanged_data(self, mock_ops):
        """Re-import with same data — all should be unchanged."""
        mock_ops.insert_import_run.return_value = "ir_2"
        mock_ops.upsert_entity.return_value = "ent_1"
        mock_ops.list_import_runs.return_value = []

        path = _create_test_workbook([
            ["Item Code", "Name", "Price"],
            ["ITM001", "Widget", 9.99],
        ])
        spec = _make_spec()

        # Parse to get expected hashes
        from backend.core.excel_parser import parse_excel
        from backend.core.hashing import compute_property_normalized_hash, compute_property_raw_hash
        staged = parse_excel(path, spec)

        # Mock existing assertions that match the data
        def mock_lookup(wid, akey, scenario_id="base"):
            # Return an assertion with matching normalized_hash for each property
            for entity in staged[0].entities:
                for prop_key, prop_value in entity.properties.items():
                    expected_key = f"{wid}:{entity.entity_type}:{entity.primary_key}:prop:{prop_key}"
                    if akey == expected_key:
                        raw_h = compute_property_raw_hash(prop_value, spec.raw_hash_serialization)
                        norm_h = compute_property_normalized_hash(
                            prop_value, spec.raw_hash_serialization,
                            spec.change_detection.normalization_rules, "string"
                        )
                        return [AssertionRecordModel(
                            assertion_id="existing_asrt",
                            workspace_id=wid,
                            assertion_key=akey,
                            raw_hash=raw_h,
                            normalized_hash=norm_h,
                            source_type=SourceType.EXCEL,
                            recorded_at=datetime.now(timezone.utc),
                            valid_from=datetime.now(timezone.utc),
                            relationship_type="HAS_PROPERTY",
                            property_key=prop_key,
                        )]
            return []

        mock_ops.lookup_assertions_by_key.side_effect = mock_lookup

        result = run_import("test_ws", path, spec)

        assert result.status == "completed"
        assert result.stats["assertions_unchanged"] > 0
        assert result.stats["assertions_created"] == 0
        assert result.stats["assertions_modified"] == 0
        # No new assertions or property values should be created
        mock_ops.insert_assertion.assert_not_called()
        mock_ops.insert_property_value.assert_not_called()
        path.unlink()

    @patch("backend.core.ingestion_engine.graph_ops")
    def test_reimport_with_changed_data(self, mock_ops):
        """Re-import with changed data — old closed, new created."""
        mock_ops.insert_import_run.return_value = "ir_3"
        mock_ops.upsert_entity.return_value = "ent_1"
        mock_ops.list_import_runs.return_value = []
        mock_ops.insert_property_value.return_value = "pv_1"
        mock_ops.insert_assertion.return_value = "asrt_new"

        # Existing assertion with DIFFERENT hash
        def mock_lookup(wid, akey, scenario_id="base"):
            return [AssertionRecordModel(
                assertion_id="old_asrt",
                workspace_id=wid,
                assertion_key=akey,
                raw_hash="old_hash",
                normalized_hash="old_hash",
                source_type=SourceType.EXCEL,
                recorded_at=datetime.now(timezone.utc),
                valid_from=datetime.now(timezone.utc),
                relationship_type="HAS_PROPERTY",
                property_key="name",
            )]

        mock_ops.lookup_assertions_by_key.side_effect = mock_lookup

        path = _create_test_workbook([
            ["Item Code", "Name", "Price"],
            ["ITM001", "NewWidget", 19.99],
        ])
        spec = _make_spec()
        result = run_import("test_ws", path, spec)

        assert result.status == "completed"
        assert result.stats["assertions_modified"] > 0
        assert mock_ops.close_assertion.called
        assert mock_ops.insert_assertion.called
        path.unlink()

    @patch("backend.core.ingestion_engine.graph_ops")
    def test_relationship_assertions_created(self, mock_ops):
        """Import with relationships creates relationship assertions."""
        mock_ops.insert_import_run.return_value = "ir_4"
        mock_ops.upsert_entity.side_effect = lambda w, t, p, d=None: f"ent_{p}"
        mock_ops.lookup_assertions_by_key.return_value = []
        mock_ops.insert_assertion.return_value = "asrt_1"
        mock_ops.insert_property_value.return_value = "pv_1"
        mock_ops.list_import_runs.return_value = []

        path = _create_test_workbook([
            ["Item Code", "Name", "Category Code", "Category Name"],
            ["ITM001", "Widget", "CAT01", "Electronics"],
        ])
        spec = _make_spec_with_relationships()
        result = run_import("test_ws", path, spec)

        assert result.status == "completed"
        assert result.stats["relationships_created"] > 0
        path.unlink()

    @patch("backend.core.ingestion_engine.graph_ops")
    def test_change_event_created(self, mock_ops):
        """Import with changes should create a ChangeEvent."""
        mock_ops.insert_import_run.return_value = "ir_5"
        mock_ops.upsert_entity.return_value = "ent_1"
        mock_ops.lookup_assertions_by_key.return_value = []
        mock_ops.insert_assertion.return_value = "asrt_1"
        mock_ops.insert_property_value.return_value = "pv_1"
        mock_ops.list_import_runs.return_value = []
        mock_ops.insert_change_event.return_value = "ce_1"

        path = _create_test_workbook([
            ["Item Code", "Name", "Price"],
            ["ITM001", "Widget", 9.99],
        ])
        spec = _make_spec()
        result = run_import("test_ws", path, spec)

        assert result.status == "completed"
        assert result.change_event_id is not None
        assert mock_ops.insert_change_event.called
        assert mock_ops.link_triggered_by.called
        assert mock_ops.link_created_assertion.called
        path.unlink()

    @patch("backend.core.ingestion_engine.graph_ops")
    def test_failed_import_records_error(self, mock_ops):
        """Failed import should update ImportRun with error status."""
        mock_ops.insert_import_run.return_value = "ir_err"
        mock_ops.upsert_entity.side_effect = RuntimeError("DB connection lost")
        mock_ops.list_import_runs.return_value = []

        path = _create_test_workbook([
            ["Item Code", "Name", "Price"],
            ["ITM001", "Widget", 9.99],
        ])
        spec = _make_spec()
        result = run_import("test_ws", path, spec)

        # Should still complete (errors tracked per-entity, not fatal)
        assert result.status == "completed"
        assert result.stats["errors"] > 0
        path.unlink()

    @patch("backend.core.ingestion_engine.graph_ops")
    def test_strict_mode_uses_raw_hash(self, mock_ops):
        """Strict mode should compare using raw_hash."""
        mock_ops.insert_import_run.return_value = "ir_strict"
        mock_ops.upsert_entity.return_value = "ent_1"
        mock_ops.list_import_runs.return_value = []
        mock_ops.insert_property_value.return_value = "pv_1"
        mock_ops.insert_assertion.return_value = "asrt_1"

        from backend.core.hashing import compute_property_raw_hash, compute_property_normalized_hash

        spec = _make_spec(mode="strict")

        # Create assertion with matching normalized_hash but different raw_hash
        def mock_lookup(wid, akey, scenario_id="base"):
            return [AssertionRecordModel(
                assertion_id="old_asrt",
                workspace_id=wid,
                assertion_key=akey,
                raw_hash="different_raw",
                normalized_hash="will_match_normalized",
                source_type=SourceType.EXCEL,
                recorded_at=datetime.now(timezone.utc),
                valid_from=datetime.now(timezone.utc),
                relationship_type="HAS_PROPERTY",
            )]

        mock_ops.lookup_assertions_by_key.side_effect = mock_lookup

        path = _create_test_workbook([
            ["Item Code", "Name", "Price"],
            ["ITM001", "Widget", 9.99],
        ])
        result = run_import("test_ws", path, spec)

        # In strict mode, different raw_hash means modified
        assert result.stats["assertions_modified"] > 0
        path.unlink()

    @patch("backend.core.ingestion_engine.graph_ops")
    def test_multiple_rows(self, mock_ops):
        """Multiple rows should create entities and assertions for each."""
        mock_ops.insert_import_run.return_value = "ir_multi"
        call_count = 0
        def mock_upsert(w, t, p, d=None):
            nonlocal call_count
            call_count += 1
            return f"ent_{call_count}"
        mock_ops.upsert_entity.side_effect = mock_upsert
        mock_ops.lookup_assertions_by_key.return_value = []
        mock_ops.insert_assertion.return_value = "asrt_1"
        mock_ops.insert_property_value.return_value = "pv_1"
        mock_ops.list_import_runs.return_value = []
        mock_ops.insert_change_event.return_value = "ce_1"

        path = _create_test_workbook([
            ["Item Code", "Name", "Price"],
            ["ITM001", "Widget", 9.99],
            ["ITM002", "Gadget", 19.99],
            ["ITM003", "Doohickey", 29.99],
        ])
        spec = _make_spec()
        result = run_import("test_ws", path, spec)

        assert result.status == "completed"
        # 3 entities, each with 3 properties = 9 assertions
        assert result.stats["assertions_created"] == 9
        path.unlink()
