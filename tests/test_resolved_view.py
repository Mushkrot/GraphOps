"""Tests for the Resolved View Engine (PRD 9.4 algorithm)."""

from datetime import datetime, timedelta, timezone

from backend.core.models import SourceType
from backend.core.resolved_view import (
    resolve_assertion,
    resolve_entity_view,
    get_all_claims,
)
from tests.conftest import make_assertion


NOW = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
HOUR = timedelta(hours=1)


class TestSingleAssertion:
    """When there is only one assertion, it should always win."""

    def test_single_assertion_wins(self):
        a = make_assertion(assertion_id="a1", recorded_at=NOW, valid_from=NOW)
        result = resolve_assertion([a])
        assert result is not None
        assert result.assertion_id == "a1"

    def test_empty_list_returns_none(self):
        result = resolve_assertion([])
        assert result is None


class TestTemporalFiltering:
    """Assertions outside their validity window should be excluded."""

    def test_expired_assertion_excluded(self):
        a = make_assertion(
            assertion_id="expired",
            recorded_at=NOW - 10 * HOUR,
            valid_from=NOW - 10 * HOUR,
            valid_to=NOW - 5 * HOUR,
        )
        result = resolve_assertion([a], at_time=NOW)
        assert result is None

    def test_future_assertion_excluded(self):
        a = make_assertion(
            assertion_id="future",
            recorded_at=NOW,
            valid_from=NOW + 5 * HOUR,
        )
        result = resolve_assertion([a], at_time=NOW)
        assert result is None

    def test_valid_assertion_included(self):
        a = make_assertion(
            assertion_id="valid",
            recorded_at=NOW - HOUR,
            valid_from=NOW - 2 * HOUR,
            valid_to=NOW + 2 * HOUR,
        )
        result = resolve_assertion([a], at_time=NOW)
        assert result is not None
        assert result.assertion_id == "valid"

    def test_open_ended_assertion_valid(self):
        """Assertion with valid_to=None is always valid after valid_from."""
        a = make_assertion(
            assertion_id="open",
            recorded_at=NOW - HOUR,
            valid_from=NOW - 2 * HOUR,
            valid_to=None,
        )
        result = resolve_assertion([a], at_time=NOW)
        assert result is not None
        assert result.assertion_id == "open"


class TestScenarioPreference:
    """Scenario assertions should be preferred over base."""

    def test_scenario_preferred_over_base(self):
        base = make_assertion(
            assertion_id="base_a",
            scenario_id="base",
            recorded_at=NOW,
            valid_from=NOW,
            source_id="src1",
        )
        scenario = make_assertion(
            assertion_id="scenario_a",
            scenario_id="what_if_1",
            recorded_at=NOW,
            valid_from=NOW,
            source_id="src1",
        )
        result = resolve_assertion(
            [base, scenario], scenario_id="what_if_1"
        )
        assert result.assertion_id == "scenario_a"

    def test_fallback_to_base_when_no_scenario_match(self):
        base = make_assertion(
            assertion_id="base_a",
            scenario_id="base",
            recorded_at=NOW,
            valid_from=NOW,
        )
        result = resolve_assertion([base], scenario_id="nonexistent_scenario")
        assert result.assertion_id == "base_a"


class TestManualOverride:
    """Manual assertions should always win over automated ones."""

    def test_manual_overrides_excel(self):
        excel = make_assertion(
            assertion_id="excel_a",
            source_type=SourceType.EXCEL,
            recorded_at=NOW,
            valid_from=NOW,
            source_id="src1",
        )
        manual = make_assertion(
            assertion_id="manual_a",
            source_type=SourceType.MANUAL,
            recorded_at=NOW - HOUR,  # older but manual
            valid_from=NOW - HOUR,
            source_id="src_manual",
        )
        authority = {"src1": 1, "src_manual": 10}
        result = resolve_assertion(
            [excel, manual], source_authority=authority
        )
        assert result.assertion_id == "manual_a"


class TestAuthorityRank:
    """Lower authority_rank number should win."""

    def test_lower_rank_wins(self):
        low_auth = make_assertion(
            assertion_id="low_rank",
            recorded_at=NOW,
            valid_from=NOW,
            source_id="src_trusted",
        )
        high_auth = make_assertion(
            assertion_id="high_rank",
            recorded_at=NOW,
            valid_from=NOW,
            source_id="src_untrusted",
        )
        authority = {"src_trusted": 1, "src_untrusted": 5}
        result = resolve_assertion(
            [high_auth, low_auth], source_authority=authority
        )
        assert result.assertion_id == "low_rank"


class TestRecencyTiebreaker:
    """When authority is equal, more recent recorded_at wins."""

    def test_more_recent_wins(self):
        old = make_assertion(
            assertion_id="old",
            recorded_at=NOW - 5 * HOUR,
            valid_from=NOW - 5 * HOUR,
            source_id="src1",
        )
        new = make_assertion(
            assertion_id="new",
            recorded_at=NOW,
            valid_from=NOW - 5 * HOUR,
            source_id="src1",
        )
        authority = {"src1": 1}
        result = resolve_assertion(
            [old, new], source_authority=authority
        )
        assert result.assertion_id == "new"


class TestConfidenceTiebreaker:
    """When authority and recency are equal, higher confidence wins."""

    def test_higher_confidence_wins(self):
        low_conf = make_assertion(
            assertion_id="low_conf",
            recorded_at=NOW,
            valid_from=NOW,
            confidence=0.5,
            source_id="src1",
        )
        high_conf = make_assertion(
            assertion_id="high_conf",
            recorded_at=NOW,
            valid_from=NOW,
            confidence=0.95,
            source_id="src1",
        )
        authority = {"src1": 1}
        result = resolve_assertion(
            [low_conf, high_conf], source_authority=authority
        )
        assert result.assertion_id == "high_conf"


class TestResolveEntityView:
    """Test multi-key resolution for an entity."""

    def test_resolves_multiple_keys(self):
        a1 = make_assertion(
            assertion_id="a1",
            assertion_key="e1::HAS_PROPERTY::name",
            recorded_at=NOW,
            valid_from=NOW,
            source_id="src1",
        )
        a2 = make_assertion(
            assertion_id="a2",
            assertion_key="e1::HAS_PROPERTY::name",
            recorded_at=NOW - HOUR,
            valid_from=NOW - HOUR,
            source_id="src1",
        )
        b1 = make_assertion(
            assertion_id="b1",
            assertion_key="e1::HAS_PROPERTY::price",
            recorded_at=NOW,
            valid_from=NOW,
            source_id="src1",
        )
        authority = {"src1": 1}
        resolved = resolve_entity_view(
            [a1, a2, b1], source_authority=authority
        )
        assert len(resolved) == 2
        assert resolved["e1::HAS_PROPERTY::name"].assertion_id == "a1"
        assert resolved["e1::HAS_PROPERTY::price"].assertion_id == "b1"


class TestGetAllClaims:
    """Test all-claims view with is_winner annotation."""

    def test_marks_winner_correctly(self):
        winner = make_assertion(
            assertion_id="winner",
            recorded_at=NOW,
            valid_from=NOW,
            source_id="src1",
            confidence=0.9,
        )
        loser = make_assertion(
            assertion_id="loser",
            recorded_at=NOW - HOUR,
            valid_from=NOW - HOUR,
            source_id="src1",
            confidence=0.5,
        )
        authority = {"src1": 1}
        claims = get_all_claims(
            [winner, loser], source_authority=authority
        )
        assert len(claims) == 2
        winner_claim = next(c for c in claims if c["assertion_id"] == "winner")
        loser_claim = next(c for c in claims if c["assertion_id"] == "loser")
        assert winner_claim["is_winner"] is True
        assert loser_claim["is_winner"] is False


class TestAtTimeFiltering:
    """Test point-in-time resolution."""

    def test_at_time_selects_correct_version(self):
        old = make_assertion(
            assertion_id="old_version",
            recorded_at=NOW - 10 * HOUR,
            valid_from=NOW - 10 * HOUR,
            valid_to=NOW - 5 * HOUR,
            source_id="src1",
        )
        current = make_assertion(
            assertion_id="current_version",
            recorded_at=NOW - 4 * HOUR,
            valid_from=NOW - 5 * HOUR,
            valid_to=NOW + 5 * HOUR,
            source_id="src1",
        )
        authority = {"src1": 1}

        # At NOW-7h, only old_version is valid
        result = resolve_assertion(
            [old, current],
            at_time=NOW - 7 * HOUR,
            source_authority=authority,
        )
        assert result.assertion_id == "old_version"

        # At NOW, only current_version is valid
        result = resolve_assertion(
            [old, current],
            at_time=NOW,
            source_authority=authority,
        )
        assert result.assertion_id == "current_version"
