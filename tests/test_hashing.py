"""Tests for the hashing engine — dual-hash computation and assertion keys."""

import pytest

from backend.core.hashing import (
    compute_assertion_key_property,
    compute_assertion_key_relationship,
    compute_normalized_hash,
    compute_property_normalized_hash,
    compute_property_raw_hash,
    compute_raw_hash,
)
from backend.core.ingestion_spec import NormalizationRule, RawHashSerialization


@pytest.fixture
def default_spec():
    return RawHashSerialization()


@pytest.fixture
def default_rules():
    return NormalizationRule()


# ---------------------------------------------------------------------------
# Raw hash tests
# ---------------------------------------------------------------------------

class TestComputeRawHash:
    def test_deterministic(self, default_spec):
        values = ["hello", "world", 42]
        h1 = compute_raw_hash(values, default_spec)
        h2 = compute_raw_hash(values, default_spec)
        assert h1 == h2

    def test_different_values_different_hash(self, default_spec):
        h1 = compute_raw_hash(["a", "b"], default_spec)
        h2 = compute_raw_hash(["a", "c"], default_spec)
        assert h1 != h2

    def test_null_representation(self, default_spec):
        h = compute_raw_hash([None, "test"], default_spec)
        assert h == compute_raw_hash([None, "test"], default_spec)
        # None serializes as <NULL>
        h2 = compute_raw_hash(["<NULL>", "test"], default_spec)
        # Since None becomes "<NULL>", these should match
        assert h == h2

    def test_custom_delimiter(self):
        spec = RawHashSerialization(delimiter=",")
        h1 = compute_raw_hash(["a", "b"], spec)
        h2 = compute_raw_hash(["a", "b"], RawHashSerialization(delimiter="|"))
        assert h1 != h2

    def test_whitespace_matters(self, default_spec):
        h1 = compute_raw_hash(["hello"], default_spec)
        h2 = compute_raw_hash(["hello "], default_spec)
        assert h1 != h2

    def test_casing_matters(self, default_spec):
        h1 = compute_raw_hash(["Hello"], default_spec)
        h2 = compute_raw_hash(["hello"], default_spec)
        assert h1 != h2

    def test_empty_values(self, default_spec):
        h = compute_raw_hash([], default_spec)
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex

    def test_number_as_displayed(self, default_spec):
        h1 = compute_raw_hash([42], default_spec)
        h2 = compute_raw_hash([42.0], default_spec)
        # int and float serialize differently: "42" vs "42.0"
        assert h1 != h2

    def test_returns_sha256_hex(self, default_spec):
        h = compute_raw_hash(["test"], default_spec)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


# ---------------------------------------------------------------------------
# Normalized hash tests
# ---------------------------------------------------------------------------

class TestComputeNormalizedHash:
    def test_trim_whitespace_ignored(self, default_spec, default_rules):
        h1 = compute_normalized_hash(["hello"], default_spec, default_rules)
        h2 = compute_normalized_hash(["  hello  "], default_spec, default_rules)
        assert h1 == h2

    def test_casing_ignored_for_strings(self, default_spec, default_rules):
        h1 = compute_normalized_hash(["Hello"], default_spec, default_rules)
        h2 = compute_normalized_hash(["hello"], default_spec, default_rules)
        assert h1 == h2

    def test_null_patterns_normalized(self, default_spec, default_rules):
        h1 = compute_normalized_hash([None], default_spec, default_rules)
        h2 = compute_normalized_hash(["N/A"], default_spec, default_rules)
        h3 = compute_normalized_hash(["null"], default_spec, default_rules)
        h4 = compute_normalized_hash(["-"], default_spec, default_rules)
        assert h1 == h2 == h3 == h4

    def test_number_formatting(self, default_spec):
        rules = NormalizationRule(number_format={"decimal_places": 2})
        h1 = compute_normalized_hash(["42"], default_spec, rules, ["number"])
        h2 = compute_normalized_hash(["42.00"], default_spec, rules, ["number"])
        assert h1 == h2

    def test_meaningful_change_detected(self, default_spec, default_rules):
        h1 = compute_normalized_hash(["active"], default_spec, default_rules)
        h2 = compute_normalized_hash(["inactive"], default_spec, default_rules)
        assert h1 != h2

    def test_different_from_raw_hash(self, default_spec, default_rules):
        values = ["  Hello  ", "N/A"]
        raw = compute_raw_hash(values, default_spec)
        norm = compute_normalized_hash(values, default_spec, default_rules)
        # These should differ because normalization changes values
        assert raw != norm

    def test_value_types_default_to_string(self, default_spec, default_rules):
        h = compute_normalized_hash(["test", "value"], default_spec, default_rules)
        assert isinstance(h, str)


# ---------------------------------------------------------------------------
# Property hash tests
# ---------------------------------------------------------------------------

class TestPropertyHashes:
    def test_property_raw_hash(self, default_spec):
        h = compute_property_raw_hash("100Mbps", default_spec)
        assert len(h) == 64

    def test_property_normalized_hash(self, default_spec, default_rules):
        h1 = compute_property_normalized_hash("100Mbps", default_spec, default_rules)
        h2 = compute_property_normalized_hash("  100mbps  ", default_spec, default_rules)
        assert h1 == h2

    def test_property_raw_hash_sensitive(self, default_spec):
        h1 = compute_property_raw_hash("100Mbps", default_spec)
        h2 = compute_property_raw_hash("100mbps", default_spec)
        assert h1 != h2


# ---------------------------------------------------------------------------
# Assertion key tests
# ---------------------------------------------------------------------------

class TestAssertionKeys:
    def test_relationship_key_format(self):
        key = compute_assertion_key_relationship(
            "ws1", "Location", "LOC001", "HAS_CONNECTION", "Connection", "CONN001"
        )
        assert key == "ws1:Location:LOC001:HAS_CONNECTION:Connection:CONN001"

    def test_property_key_format(self):
        key = compute_assertion_key_property("ws1", "Connection", "CONN001", "speed")
        assert key == "ws1:Connection:CONN001:prop:speed"

    def test_relationship_key_different_entities(self):
        k1 = compute_assertion_key_relationship("ws1", "A", "1", "REL", "B", "2")
        k2 = compute_assertion_key_relationship("ws1", "A", "1", "REL", "B", "3")
        assert k1 != k2

    def test_property_key_different_properties(self):
        k1 = compute_assertion_key_property("ws1", "Entity", "pk1", "speed")
        k2 = compute_assertion_key_property("ws1", "Entity", "pk1", "cost")
        assert k1 != k2

    def test_workspace_isolation_in_keys(self):
        k1 = compute_assertion_key_property("ws1", "Entity", "pk1", "speed")
        k2 = compute_assertion_key_property("ws2", "Entity", "pk1", "speed")
        assert k1 != k2
