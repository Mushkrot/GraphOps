"""Pydantic models for core vertex types and API request/response schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    EXCEL = "excel"
    API = "api"
    MANUAL = "manual"
    LLM_EXTRACTED = "llm_extracted"
    COMPUTED = "computed"


class ViewMode(str, Enum):
    RESOLVED = "resolved"
    ALL_CLAIMS = "all_claims"


class ChangeDetectionMode(str, Enum):
    STRICT = "strict"
    NORMALIZED = "normalized"


class EventType(str, Enum):
    IMPORT_DIFF = "import_diff"
    MANUAL_RESOLVE = "manual_resolve"
    SCENARIO_DELTA = "scenario_delta"
    MANUAL_EDIT = "manual_edit"


class ValueType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"
    JSON = "json"


# --- Core vertex models ---


class EntityModel(BaseModel):
    entity_id: str
    workspace_id: str
    entity_type: str
    primary_key: str
    display_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AssertionRecordModel(BaseModel):
    assertion_id: str
    workspace_id: str
    assertion_key: str
    raw_hash: str
    normalized_hash: str
    source_type: SourceType
    source_ref: Optional[str] = None
    source_id: Optional[str] = None
    import_run_id: Optional[str] = None
    recorded_at: datetime
    valid_from: datetime
    valid_to: Optional[datetime] = None
    scenario_id: str = "base"
    confidence: float = 1.0
    supersedes: Optional[str] = None
    relationship_type: str
    property_key: Optional[str] = None


class PropertyValueModel(BaseModel):
    property_value_id: str
    workspace_id: str
    property_key: str
    value: Optional[str] = None
    value_type: ValueType


class ChangeEventModel(BaseModel):
    change_event_id: str
    workspace_id: str
    event_type: EventType
    description: Optional[str] = None
    timestamp: datetime
    import_run_id: Optional[str] = None
    actor: Optional[str] = None
    stats: Optional[str] = None  # JSON string


class SourceModel(BaseModel):
    source_id: str
    workspace_id: str
    source_name: str
    source_type: str
    authority_rank: int
    authority_domains: Optional[str] = None  # JSON string
    update_frequency: Optional[str] = None
    description: Optional[str] = None


class ImportRunModel(BaseModel):
    import_run_id: str
    workspace_id: str
    source_file: Optional[str] = None
    spec_name: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    stats: Optional[str] = None  # JSON string
    error_message: Optional[str] = None


# --- API request/response models ---


class WorkspaceCreate(BaseModel):
    workspace_id: str = Field(
        ..., pattern=r"^[a-z0-9_]+$", max_length=64,
        description="Unique workspace identifier (lowercase alphanumeric + underscore)"
    )
    display_name: str
    schema_yaml: str = Field(
        ..., description="Domain schema YAML content"
    )


class WorkspaceResponse(BaseModel):
    workspace_id: str
    display_name: str
    schema_version: Optional[str] = None
    entity_types: list[str] = []
    relationship_types: list[str] = []


# --- Import API models ---


class ImportCreateResponse(BaseModel):
    import_run_id: str
    status: str
    message: str


class ImportRunResponse(BaseModel):
    import_run_id: str
    workspace_id: str
    source_file: Optional[str] = None
    spec_name: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    stats: Optional[dict] = None
    error_message: Optional[str] = None


class ImportDiffResponse(BaseModel):
    import_run_id: str
    change_event_id: Optional[str] = None
    stats: Optional[dict] = None
    created_assertions: list[dict] = []
    closed_assertions: list[dict] = []


# --- Entity API models ---


class EntitySearchResult(BaseModel):
    entity_id: str
    entity_type: str
    primary_key: str
    display_name: Optional[str] = None


class EntitySearchResponse(BaseModel):
    entities: list[EntitySearchResult]
    total: int


class PropertyView(BaseModel):
    property_key: str
    value: Optional[str] = None
    value_type: str
    source_ref: Optional[str] = None
    assertion_id: str
    confidence: float


class RelationshipView(BaseModel):
    relationship_type: str
    target_entity_id: str
    target_entity_type: str
    target_primary_key: str
    target_display_name: Optional[str] = None
    assertion_id: str
    source_ref: Optional[str] = None
    confidence: float


class EntityDetailResponse(BaseModel):
    entity_id: str
    entity_type: str
    primary_key: str
    display_name: Optional[str] = None
    properties: list[PropertyView] = []
    relationships: list[RelationshipView] = []
    view_mode: str = "resolved"
