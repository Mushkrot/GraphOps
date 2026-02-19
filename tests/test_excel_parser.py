"""Tests for the Excel parser — uses programmatic openpyxl workbooks."""

import tempfile
from pathlib import Path

import openpyxl
import pytest

from backend.core.excel_parser import (
    StagedEntity,
    StagedRelationship,
    StagedRow,
    _apply_transform,
    _build_header_map,
    _resolve_key,
    parse_excel,
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


def _create_test_workbook(rows: list[list], sheet_name: str = "Items") -> Path:
    """Create a test Excel file with given rows. First row is headers."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name
    for row in rows:
        ws.append(row)
    path = Path(tempfile.mktemp(suffix=".xlsx"))
    wb.save(path)
    wb.close()
    return path


def _make_spec(
    sheet_name: str = "Items",
    entities: dict | None = None,
    relationships: list | None = None,
) -> IngestionSpec:
    """Build a minimal IngestionSpec for testing."""
    if entities is None:
        entities = {
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
        }
    if relationships is None:
        relationships = []

    return IngestionSpec(
        spec_name="test_spec",
        spec_version="1.0",
        workspace_id="test_ws",
        sheets=[
            SheetSpec(
                sheet_name=sheet_name,
                header_row=0,
                entities=entities,
                relationships=relationships,
            )
        ],
    )


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------

class TestBuildHeaderMap:
    def test_basic_headers(self):
        headers = ["Item Code", "Name", "Price"]
        result = _build_header_map(headers)
        assert result == {"Item Code": 0, "Name": 1, "Price": 2}

    def test_none_headers_skipped(self):
        headers = ["A", None, "C"]
        result = _build_header_map(headers)
        assert result == {"A": 0, "C": 2}

    def test_strips_whitespace(self):
        headers = ["  Name  "]
        result = _build_header_map(headers)
        assert "Name" in result


class TestResolveKey:
    def test_simple_key(self):
        key = _resolve_key("{item_code}", ["item_code"], {"item_code": "ABC"})
        assert key == "ABC"

    def test_composite_key(self):
        key = _resolve_key("{a}_{b}", ["a", "b"], {"a": "X", "b": "Y"})
        assert key == "X_Y"

    def test_missing_key_column_returns_none(self):
        key = _resolve_key("{item_code}", ["item_code"], {"item_code": None})
        assert key is None

    def test_empty_string_returns_none(self):
        key = _resolve_key("{item_code}", ["item_code"], {"item_code": "  "})
        assert key is None


class TestApplyTransform:
    def test_strip(self):
        assert _apply_transform("  hello  ", "strip") == "hello"

    def test_lower(self):
        assert _apply_transform("HELLO", "lower") == "hello"

    def test_upper(self):
        assert _apply_transform("hello", "upper") == "HELLO"

    def test_int(self):
        assert _apply_transform("42.7", "int") == 42

    def test_float(self):
        assert _apply_transform("42", "float") == 42.0

    def test_none_returns_none(self):
        assert _apply_transform(None, "strip") is None

    def test_unknown_transform_passthrough(self):
        assert _apply_transform("test", "unknown") == "test"


# ---------------------------------------------------------------------------
# Integration tests with Excel files
# ---------------------------------------------------------------------------

class TestParseExcel:
    def test_basic_parsing(self):
        path = _create_test_workbook([
            ["Item Code", "Name", "Price"],
            ["ITM001", "Widget", 9.99],
            ["ITM002", "Gadget", 19.99],
        ])
        spec = _make_spec()
        rows = parse_excel(path, spec)
        assert len(rows) == 2
        assert rows[0].entities[0].entity_type == "Item"
        assert rows[0].entities[0].primary_key == "ITM001"
        assert rows[0].entities[0].properties["name"] == "Widget"
        assert rows[1].entities[0].primary_key == "ITM002"
        path.unlink()

    def test_hashes_computed(self):
        path = _create_test_workbook([
            ["Item Code", "Name", "Price"],
            ["ITM001", "Widget", 9.99],
        ])
        spec = _make_spec()
        rows = parse_excel(path, spec)
        assert len(rows[0].raw_hash) == 64
        assert len(rows[0].normalized_hash) == 64
        path.unlink()

    def test_hashes_deterministic(self):
        path = _create_test_workbook([
            ["Item Code", "Name", "Price"],
            ["ITM001", "Widget", 9.99],
        ])
        spec = _make_spec()
        rows1 = parse_excel(path, spec)
        rows2 = parse_excel(path, spec)
        assert rows1[0].raw_hash == rows2[0].raw_hash
        assert rows1[0].normalized_hash == rows2[0].normalized_hash
        path.unlink()

    def test_different_data_different_hashes(self):
        path1 = _create_test_workbook([
            ["Item Code", "Name", "Price"],
            ["ITM001", "Widget", 9.99],
        ])
        path2 = _create_test_workbook([
            ["Item Code", "Name", "Price"],
            ["ITM001", "Widget", 19.99],
        ])
        spec = _make_spec()
        rows1 = parse_excel(path1, spec)
        rows2 = parse_excel(path2, spec)
        assert rows1[0].raw_hash != rows2[0].raw_hash
        path1.unlink()
        path2.unlink()

    def test_empty_rows_skipped(self):
        path = _create_test_workbook([
            ["Item Code", "Name", "Price"],
            ["ITM001", "Widget", 9.99],
            [None, None, None],
            ["ITM002", "Gadget", 19.99],
        ])
        spec = _make_spec()
        rows = parse_excel(path, spec)
        assert len(rows) == 2
        path.unlink()

    def test_null_key_skips_entity(self):
        path = _create_test_workbook([
            ["Item Code", "Name", "Price"],
            [None, "No Code", 5.0],
        ])
        spec = _make_spec()
        rows = parse_excel(path, spec)
        # Row with null key produces no entities, so it's not staged
        assert len(rows) == 0
        path.unlink()

    def test_multi_entity_row(self):
        path = _create_test_workbook([
            ["Item Code", "Name", "Price", "Category Code", "Category Name"],
            ["ITM001", "Widget", 9.99, "CAT01", "Electronics"],
        ])
        spec = _make_spec(
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
        )
        rows = parse_excel(path, spec)
        assert len(rows) == 1
        assert len(rows[0].entities) == 2
        types = {e.entity_type for e in rows[0].entities}
        assert types == {"Item", "Category"}
        path.unlink()

    def test_relationship_extraction(self):
        path = _create_test_workbook([
            ["Item Code", "Name", "Category Code", "Category Name"],
            ["ITM001", "Widget", "CAT01", "Electronics"],
        ])
        spec = _make_spec(
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
        rows = parse_excel(path, spec)
        assert len(rows[0].relationships) == 1
        rel = rows[0].relationships[0]
        assert rel.relationship_type == "BELONGS_TO"
        assert rel.from_entity_type == "Item"
        assert rel.from_primary_key == "ITM001"
        assert rel.to_entity_type == "Category"
        assert rel.to_primary_key == "CAT01"
        path.unlink()

    def test_missing_sheet_skipped(self):
        path = _create_test_workbook([
            ["A"],
            ["1"],
        ], sheet_name="Other")
        spec = _make_spec(sheet_name="Missing")
        rows = parse_excel(path, spec)
        assert len(rows) == 0
        path.unlink()

    def test_display_name_from_first_non_key_prop(self):
        path = _create_test_workbook([
            ["Item Code", "Name", "Price"],
            ["ITM001", "Widget", 9.99],
        ])
        spec = _make_spec()
        rows = parse_excel(path, spec)
        assert rows[0].entities[0].display_name == "Widget"
        path.unlink()

    def test_source_ref_format(self):
        path = _create_test_workbook([
            ["Item Code", "Name", "Price"],
            ["ITM001", "Widget", 9.99],
        ])
        spec = _make_spec()
        rows = parse_excel(path, spec)
        assert rows[0].entities[0].source_ref.startswith("sheet:Items,row:")
        path.unlink()
