"""Tests for graph_ops — verify nGQL generation and helper functions.

Uses mocked execute_query to test without live NebulaGraph.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from backend.core.graph_ops import (
    _escape,
    _fmt_dt,
    _fmt_opt_str,
    upsert_entity,
    insert_assertion,
    close_assertion,
    insert_property_value,
    insert_change_event,
    insert_import_run,
    update_import_run,
    create_asserted_rel,
    link_created_assertion,
    link_closed_assertion,
    link_triggered_by,
)
from backend.core.models import (
    AssertionRecordModel,
    ChangeEventModel,
    ImportRunModel,
    PropertyValueModel,
    SourceType,
    EventType,
    ValueType,
)


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------

class TestEscape:
    def test_simple_string(self):
        assert _escape("hello") == "'hello'"

    def test_single_quote(self):
        assert _escape("it's") == "'it\\'s'"

    def test_backslash(self):
        assert _escape("a\\b") == "'a\\\\b'"

    def test_newline(self):
        assert _escape("a\nb") == "'a\\nb'"

    def test_none(self):
        assert _escape(None) == "''"

    def test_number_as_string(self):
        assert _escape(42) == "'42'"


class TestFormatDatetime:
    def test_valid_datetime(self):
        dt = datetime(2026, 2, 19, 12, 30, 0, 123456)
        result = _fmt_dt(dt)
        assert result == 'datetime("2026-02-19T12:30:00.123456")'

    def test_none(self):
        assert _fmt_dt(None) == "NULL"


class TestFormatOptStr:
    def test_none(self):
        assert _fmt_opt_str(None) == "NULL"

    def test_value(self):
        assert _fmt_opt_str("test") == "'test'"


# ---------------------------------------------------------------------------
# Entity operations (mocked)
# ---------------------------------------------------------------------------

class TestUpsertEntity:
    @patch("backend.core.graph_ops.execute_query")
    @patch("backend.core.graph_ops.lookup_entity", return_value=None)
    @patch("backend.core.graph_ops.generate_id", return_value="ent_abc123")
    def test_creates_new_entity(self, mock_gen, mock_lookup, mock_exec):
        mock_exec.return_value = MagicMock()
        eid = upsert_entity("ws1", "Location", "LOC001", "Main Office")
        assert eid == "ent_abc123"
        mock_exec.assert_called_once()
        call_args = mock_exec.call_args[0][0]
        assert "INSERT VERTEX Entity" in call_args
        assert "'ws1'" in call_args
        assert "'Location'" in call_args
        assert "'LOC001'" in call_args

    @patch("backend.core.graph_ops.lookup_entity")
    def test_returns_existing_entity(self, mock_lookup):
        from backend.core.models import EntityModel
        mock_lookup.return_value = EntityModel(
            entity_id="ent_existing",
            workspace_id="ws1",
            entity_type="Location",
            primary_key="LOC001",
        )
        eid = upsert_entity("ws1", "Location", "LOC001")
        assert eid == "ent_existing"


# ---------------------------------------------------------------------------
# Assertion operations (mocked)
# ---------------------------------------------------------------------------

class TestInsertAssertion:
    @patch("backend.core.graph_ops.execute_query")
    def test_insert_generates_correct_ngql(self, mock_exec):
        mock_exec.return_value = MagicMock()
        now = datetime(2026, 2, 19, 12, 0, 0, 0)
        a = AssertionRecordModel(
            assertion_id="asrt_test1",
            workspace_id="ws1",
            assertion_key="ws1:Location:LOC001:prop:status",
            raw_hash="abc123",
            normalized_hash="def456",
            source_type=SourceType.EXCEL,
            source_ref="sheet:Stores,row:2",
            import_run_id="ir_run1",
            recorded_at=now,
            valid_from=now,
            scenario_id="base",
            confidence=1.0,
            relationship_type="HAS_PROPERTY",
            property_key="status",
        )
        result = insert_assertion(a)
        assert result == "asrt_test1"
        call_args = mock_exec.call_args[0][0]
        assert "INSERT VERTEX AssertionRecord" in call_args
        assert "'asrt_test1'" in call_args
        assert "'HAS_PROPERTY'" in call_args


class TestCloseAssertion:
    @patch("backend.core.graph_ops.execute_query")
    def test_sets_valid_to(self, mock_exec):
        mock_exec.return_value = MagicMock()
        now = datetime(2026, 2, 19, 12, 0, 0, 0)
        close_assertion("asrt_test1", now)
        call_args = mock_exec.call_args[0][0]
        assert "UPDATE VERTEX ON AssertionRecord" in call_args
        assert "valid_to" in call_args


# ---------------------------------------------------------------------------
# Edge operations (mocked)
# ---------------------------------------------------------------------------

class TestEdgeOperations:
    @patch("backend.core.graph_ops.execute_query")
    def test_create_asserted_rel(self, mock_exec):
        mock_exec.return_value = MagicMock()
        create_asserted_rel("ent_1", "asrt_1", "pv_1")
        assert mock_exec.call_count == 2
        # First call: from_entity -> assertion
        call1 = mock_exec.call_args_list[0][0][0]
        assert "INSERT EDGE ASSERTED_REL" in call1
        assert "'ent_1'" in call1
        assert "'asrt_1'" in call1
        # Second call: assertion -> to_entity
        call2 = mock_exec.call_args_list[1][0][0]
        assert "'asrt_1'" in call2
        assert "'pv_1'" in call2

    @patch("backend.core.graph_ops.execute_query")
    def test_link_created_assertion(self, mock_exec):
        mock_exec.return_value = MagicMock()
        link_created_assertion("ce_1", "asrt_1")
        call_args = mock_exec.call_args[0][0]
        assert "INSERT EDGE CREATED_ASSERTION" in call_args

    @patch("backend.core.graph_ops.execute_query")
    def test_link_closed_assertion(self, mock_exec):
        mock_exec.return_value = MagicMock()
        link_closed_assertion("ce_1", "asrt_1")
        call_args = mock_exec.call_args[0][0]
        assert "INSERT EDGE CLOSED_ASSERTION" in call_args

    @patch("backend.core.graph_ops.execute_query")
    def test_link_triggered_by(self, mock_exec):
        mock_exec.return_value = MagicMock()
        link_triggered_by("ce_1", "ir_1")
        call_args = mock_exec.call_args[0][0]
        assert "INSERT EDGE TRIGGERED_BY" in call_args


# ---------------------------------------------------------------------------
# PropertyValue operations (mocked)
# ---------------------------------------------------------------------------

class TestInsertPropertyValue:
    @patch("backend.core.graph_ops.execute_query")
    def test_insert(self, mock_exec):
        mock_exec.return_value = MagicMock()
        pv = PropertyValueModel(
            property_value_id="pv_test1",
            workspace_id="ws1",
            property_key="speed",
            value="100Mbps",
            value_type=ValueType.STRING,
        )
        result = insert_property_value(pv)
        assert result == "pv_test1"
        call_args = mock_exec.call_args[0][0]
        assert "INSERT VERTEX PropertyValue" in call_args
        assert "'speed'" in call_args
        assert "'100Mbps'" in call_args


# ---------------------------------------------------------------------------
# ChangeEvent operations (mocked)
# ---------------------------------------------------------------------------

class TestInsertChangeEvent:
    @patch("backend.core.graph_ops.execute_query")
    def test_insert(self, mock_exec):
        mock_exec.return_value = MagicMock()
        now = datetime(2026, 2, 19, 12, 0, 0, 0)
        ce = ChangeEventModel(
            change_event_id="ce_test1",
            workspace_id="ws1",
            event_type=EventType.IMPORT_DIFF,
            description="Test import",
            timestamp=now,
            import_run_id="ir_run1",
            actor="system:import",
            stats='{"created": 5}',
        )
        result = insert_change_event(ce)
        assert result == "ce_test1"
        call_args = mock_exec.call_args[0][0]
        assert "INSERT VERTEX ChangeEvent" in call_args
        assert "'ce_test1'" in call_args


# ---------------------------------------------------------------------------
# ImportRun operations (mocked)
# ---------------------------------------------------------------------------

class TestImportRunOps:
    @patch("backend.core.graph_ops.execute_query")
    def test_insert_import_run(self, mock_exec):
        mock_exec.return_value = MagicMock()
        now = datetime(2026, 2, 19, 12, 0, 0, 0)
        ir = ImportRunModel(
            import_run_id="ir_test1",
            workspace_id="ws1",
            source_file="test.xlsx",
            spec_name="test_spec",
            started_at=now,
            status="running",
        )
        result = insert_import_run(ir)
        assert result == "ir_test1"
        call_args = mock_exec.call_args[0][0]
        assert "INSERT VERTEX ImportRun" in call_args

    @patch("backend.core.graph_ops.execute_query")
    def test_update_import_run(self, mock_exec):
        mock_exec.return_value = MagicMock()
        now = datetime(2026, 2, 19, 13, 0, 0, 0)
        update_import_run("ir_test1", status="completed", completed_at=now, stats='{"created": 5}')
        call_args = mock_exec.call_args[0][0]
        assert "UPDATE VERTEX ON ImportRun" in call_args
        assert "status" in call_args
        assert "completed_at" in call_args
        assert "stats" in call_args

    @patch("backend.core.graph_ops.execute_query")
    def test_update_import_run_no_changes(self, mock_exec):
        update_import_run("ir_test1")
        mock_exec.assert_not_called()
