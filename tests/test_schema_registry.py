"""Tests for the Domain Schema Registry."""

import pytest

from backend.core.schema_registry import SchemaRegistry, DomainSchema


VALID_SCHEMA_YAML = """
workspace: test_ws
version: "1.0"

entity_types:
  Item:
    primary_key: item_code
    properties:
      item_code:
        type: string
        required: true
      name:
        type: string
  Category:
    primary_key: cat_id
    properties:
      cat_id:
        type: string
        required: true
      title:
        type: string

relationship_types:
  BELONGS_TO:
    from: Item
    to: Category
"""


class TestLoadSchemaFromYaml:
    """Test YAML parsing into DomainSchema."""

    def test_valid_yaml_loads(self):
        registry = SchemaRegistry()
        schema = registry.load_schema_from_yaml(VALID_SCHEMA_YAML)
        assert schema.workspace == "test_ws"
        assert schema.version == "1.0"
        assert "Item" in schema.entity_types
        assert "Category" in schema.entity_types
        assert "BELONGS_TO" in schema.relationship_types

    def test_entity_type_properties(self):
        registry = SchemaRegistry()
        schema = registry.load_schema_from_yaml(VALID_SCHEMA_YAML)
        item = schema.entity_types["Item"]
        assert item.primary_key == "item_code"
        assert "item_code" in item.properties
        assert item.properties["item_code"].type == "string"
        assert item.properties["item_code"].required is True

    def test_relationship_type_parsing(self):
        registry = SchemaRegistry()
        schema = registry.load_schema_from_yaml(VALID_SCHEMA_YAML)
        rel = schema.relationship_types["BELONGS_TO"]
        assert rel.from_type == "Item"
        assert rel.to_type == "Category"

    def test_invalid_yaml_raises(self):
        registry = SchemaRegistry()
        with pytest.raises(Exception):
            registry.load_schema_from_yaml("not: [valid: yaml: {{")

    def test_non_mapping_raises(self):
        registry = SchemaRegistry()
        with pytest.raises(ValueError, match="must be a mapping"):
            registry.load_schema_from_yaml("- just\n- a\n- list")


class TestValidateSchema:
    """Test schema validation rules."""

    def test_valid_schema_no_errors(self):
        registry = SchemaRegistry()
        schema = registry.load_schema_from_yaml(VALID_SCHEMA_YAML)
        errors = registry.validate_schema(schema)
        assert errors == []

    def test_missing_primary_key_in_properties(self):
        yaml_str = """
workspace: test_ws
version: "1.0"
entity_types:
  Item:
    primary_key: nonexistent_key
    properties:
      name:
        type: string
"""
        registry = SchemaRegistry()
        schema = registry.load_schema_from_yaml(yaml_str)
        errors = registry.validate_schema(schema)
        assert any("primary_key" in e and "nonexistent_key" in e for e in errors)

    def test_invalid_property_type(self):
        yaml_str = """
workspace: test_ws
version: "1.0"
entity_types:
  Item:
    primary_key: code
    properties:
      code:
        type: invalid_type
"""
        registry = SchemaRegistry()
        schema = registry.load_schema_from_yaml(yaml_str)
        errors = registry.validate_schema(schema)
        assert any("invalid type" in e for e in errors)

    def test_invalid_relationship_from_type(self):
        yaml_str = """
workspace: test_ws
version: "1.0"
entity_types:
  Item:
    primary_key: code
    properties:
      code:
        type: string
relationship_types:
  BELONGS_TO:
    from: NonExistentType
    to: Item
"""
        registry = SchemaRegistry()
        schema = registry.load_schema_from_yaml(yaml_str)
        errors = registry.validate_schema(schema)
        assert any("from_type" in e and "NonExistentType" in e for e in errors)

    def test_invalid_relationship_to_type(self):
        yaml_str = """
workspace: test_ws
version: "1.0"
entity_types:
  Item:
    primary_key: code
    properties:
      code:
        type: string
relationship_types:
  BELONGS_TO:
    from: Item
    to: GhostType
"""
        registry = SchemaRegistry()
        schema = registry.load_schema_from_yaml(yaml_str)
        errors = registry.validate_schema(schema)
        assert any("to_type" in e and "GhostType" in e for e in errors)

    def test_invalid_regex_pattern(self):
        yaml_str = """
workspace: test_ws
version: "1.0"
entity_types:
  Item:
    primary_key: code
    properties:
      code:
        type: string
        pattern: "[invalid regex"
"""
        registry = SchemaRegistry()
        schema = registry.load_schema_from_yaml(yaml_str)
        errors = registry.validate_schema(schema)
        assert any("regex" in e.lower() or "pattern" in e.lower() for e in errors)


class TestRegisterAndRetrieve:
    """Test schema registration and retrieval."""

    def test_register_and_get(self):
        registry = SchemaRegistry()
        schema = registry.load_schema_from_yaml(VALID_SCHEMA_YAML)
        registry.register_schema(schema)
        retrieved = registry.get_schema("test_ws")
        assert retrieved.workspace == "test_ws"
        assert retrieved.version == "1.0"

    def test_get_nonexistent_raises(self):
        registry = SchemaRegistry()
        with pytest.raises(FileNotFoundError):
            registry.get_schema("nonexistent_workspace")

    def test_list_schemas_includes_registered(self):
        registry = SchemaRegistry()
        schema = registry.load_schema_from_yaml(VALID_SCHEMA_YAML)
        registry.register_schema(schema)
        schemas = registry.list_schemas()
        assert "test_ws" in schemas

    def test_register_invalid_schema_raises(self):
        registry = SchemaRegistry()
        yaml_str = """
workspace: bad_ws
version: "1.0"
entity_types:
  Item:
    primary_key: missing_prop
    properties:
      name:
        type: string
"""
        schema = registry.load_schema_from_yaml(yaml_str)
        with pytest.raises(ValueError, match="validation errors"):
            registry.register_schema(schema)
