"""Ingestion Spec Format Definition.

Defines the YAML structure for data ingestion mapping specs.
The spec tells the ingestion engine how to:
1. Read a source file (which sheets, columns)
2. Map columns to entities and relationships
3. Compute assertion_key for change detection
4. Compute raw_hash (canonical row serialization)
5. Apply normalization rules for normalized_hash
6. Determine change_detection_mode (strict vs normalized)

Actual ingestion execution is implemented in M1.
"""

from typing import Optional
from pydantic import BaseModel


class RawHashSerialization(BaseModel):
    cell_order: str = "column_order"
    delimiter: str = "|"
    null_representation: str = "<NULL>"
    number_format: str = "as_displayed"
    date_format: str = "as_displayed"
    include_formatting: bool = False


class NormalizationRule(BaseModel):
    trim_whitespace: bool = True
    lowercase_strings: bool = True
    normalize_nulls: list[str] = ["", "N/A", "n/a", "null", "-"]
    number_format: Optional[dict] = None
    date_format: Optional[str] = None


class ChangeDetection(BaseModel):
    mode: str = "normalized"
    normalization_rules: NormalizationRule = NormalizationRule()


class ColumnMapping(BaseModel):
    source_column: str
    target_property: str
    transform: Optional[str] = None


class EntityMapping(BaseModel):
    entity_type: str
    key_columns: list[str]
    key_template: str
    properties: list[ColumnMapping]


class RelationshipMapping(BaseModel):
    relationship_type: str
    from_entity: str
    to_entity: str
    properties: Optional[list[ColumnMapping]] = None


class SheetSpec(BaseModel):
    sheet_name: Optional[str] = None
    sheet_index: Optional[int] = None
    header_row: int = 0
    skip_rows: Optional[list[int]] = None
    entities: dict[str, EntityMapping]
    relationships: list[RelationshipMapping] = []


class IngestionSpec(BaseModel):
    spec_name: str
    spec_version: str
    workspace_id: str
    source_type: str = "excel"
    file_pattern: Optional[str] = None
    raw_hash_serialization: RawHashSerialization = RawHashSerialization()
    change_detection: ChangeDetection = ChangeDetection()
    sheets: list[SheetSpec]
