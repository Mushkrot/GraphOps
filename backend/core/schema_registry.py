"""Domain Schema Registry — loads and validates YAML domain schemas.

Schemas define entity types, relationship types, and property schemas
for a specific workspace. The registry provides runtime access to these
definitions for validation, ingestion, and query routing.
"""

import logging
import re
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel

from backend.core.config import settings

logger = logging.getLogger(__name__)


VALID_PROPERTY_TYPES = {"string", "number", "date", "boolean", "json"}


class PropertyDef(BaseModel):
    type: str
    required: bool = False
    pattern: Optional[str] = None
    enum: Optional[list[str]] = None
    description: Optional[str] = None


class EntityTypeDef(BaseModel):
    primary_key: str
    properties: dict[str, PropertyDef] = {}
    description: Optional[str] = None


class RelationshipTypeDef(BaseModel):
    from_type: str
    to_type: str
    properties: Optional[dict[str, PropertyDef]] = None
    description: Optional[str] = None


class AliasConfig(BaseModel):
    entity_type: str
    alias_entity_type: str
    alias_key: str


class DomainSchema(BaseModel):
    workspace: str
    version: str
    entity_types: dict[str, EntityTypeDef] = {}
    relationship_types: dict[str, RelationshipTypeDef] = {}
    alias_config: Optional[AliasConfig] = None


def _parse_relationship(name: str, raw: dict) -> RelationshipTypeDef:
    """Parse a relationship definition, handling YAML 'from'/'to' keys."""
    return RelationshipTypeDef(
        from_type=raw.get("from", raw.get("from_type", "")),
        to_type=raw.get("to", raw.get("to_type", "")),
        properties={
            k: PropertyDef(**v) for k, v in raw.get("properties", {}).items()
        } if raw.get("properties") else None,
        description=raw.get("description"),
    )


class SchemaRegistry:
    """Singleton registry that loads, validates, and caches domain schemas."""

    def __init__(self, schemas_dir: Optional[str] = None):
        self._schemas: dict[str, DomainSchema] = {}
        self._schemas_dir = Path(
            schemas_dir or settings.schemas_dir
        )
        if not self._schemas_dir.is_absolute():
            self._schemas_dir = settings.project_root / self._schemas_dir

    def load_schema_from_yaml(self, yaml_content: str) -> DomainSchema:
        """Parse and validate a domain schema from YAML string."""
        raw = yaml.safe_load(yaml_content)
        if not isinstance(raw, dict):
            raise ValueError("Schema YAML must be a mapping")

        entity_types = {}
        for name, edef in raw.get("entity_types", {}).items():
            entity_types[name] = EntityTypeDef(**edef)

        relationship_types = {}
        for name, rdef in raw.get("relationship_types", {}).items():
            relationship_types[name] = _parse_relationship(name, rdef)

        alias_config = None
        if raw.get("alias_config"):
            alias_config = AliasConfig(**raw["alias_config"])

        schema = DomainSchema(
            workspace=raw["workspace"],
            version=raw["version"],
            entity_types=entity_types,
            relationship_types=relationship_types,
            alias_config=alias_config,
        )
        return schema

    def load_schema(self, workspace_id: str) -> DomainSchema:
        """Load schema from YAML file for the given workspace."""
        candidates = list(self._schemas_dir.glob("*.yaml")) + \
                     list(self._schemas_dir.glob("*.yml"))

        for path in candidates:
            if path.name.startswith("_"):
                continue
            try:
                content = path.read_text()
                raw = yaml.safe_load(content)
                if isinstance(raw, dict) and raw.get("workspace") == workspace_id:
                    schema = self.load_schema_from_yaml(content)
                    errors = self.validate_schema(schema)
                    if errors:
                        raise ValueError(
                            f"Schema validation errors for {workspace_id}: {errors}"
                        )
                    self._schemas[workspace_id] = schema
                    logger.info(f"Loaded schema for workspace '{workspace_id}' from {path}")
                    return schema
            except yaml.YAMLError:
                continue

        raise FileNotFoundError(
            f"No schema file found for workspace '{workspace_id}' in {self._schemas_dir}"
        )

    def get_schema(self, workspace_id: str) -> DomainSchema:
        """Get cached schema or load it from disk."""
        if workspace_id not in self._schemas:
            return self.load_schema(workspace_id)
        return self._schemas[workspace_id]

    def register_schema(self, schema: DomainSchema) -> None:
        """Register a schema directly (e.g. from API create workspace)."""
        errors = self.validate_schema(schema)
        if errors:
            raise ValueError(f"Schema validation errors: {errors}")
        self._schemas[schema.workspace] = schema

    def validate_schema(self, schema: DomainSchema) -> list[str]:
        """Validate schema integrity. Returns list of error messages (empty = valid)."""
        errors: list[str] = []
        entity_names = set(schema.entity_types.keys())

        for etype_name, etype in schema.entity_types.items():
            # Primary key must exist in properties
            if etype.primary_key not in etype.properties:
                errors.append(
                    f"Entity '{etype_name}': primary_key '{etype.primary_key}' "
                    f"not found in properties"
                )
            # Property types must be valid
            for prop_name, prop in etype.properties.items():
                if prop.type not in VALID_PROPERTY_TYPES:
                    errors.append(
                        f"Entity '{etype_name}'.{prop_name}: invalid type '{prop.type}'. "
                        f"Must be one of {VALID_PROPERTY_TYPES}"
                    )
                # Pattern must compile
                if prop.pattern:
                    try:
                        re.compile(prop.pattern)
                    except re.error as e:
                        errors.append(
                            f"Entity '{etype_name}'.{prop_name}: invalid regex "
                            f"pattern '{prop.pattern}': {e}"
                        )

        for rel_name, rel in schema.relationship_types.items():
            if rel.from_type not in entity_names:
                errors.append(
                    f"Relationship '{rel_name}': from_type '{rel.from_type}' "
                    f"not found in entity_types"
                )
            if rel.to_type not in entity_names:
                errors.append(
                    f"Relationship '{rel_name}': to_type '{rel.to_type}' "
                    f"not found in entity_types"
                )
            if rel.properties:
                for prop_name, prop in rel.properties.items():
                    if prop.type not in VALID_PROPERTY_TYPES:
                        errors.append(
                            f"Relationship '{rel_name}'.{prop_name}: invalid type "
                            f"'{prop.type}'"
                        )

        return errors

    def list_schemas(self) -> list[str]:
        """List all available schema workspace IDs from disk."""
        workspaces = list(self._schemas.keys())
        candidates = list(self._schemas_dir.glob("*.yaml")) + \
                     list(self._schemas_dir.glob("*.yml"))
        for path in candidates:
            if path.name.startswith("_"):
                continue
            try:
                raw = yaml.safe_load(path.read_text())
                if isinstance(raw, dict) and raw.get("workspace"):
                    ws = raw["workspace"]
                    if ws not in workspaces:
                        workspaces.append(ws)
            except Exception:
                continue
        return workspaces
