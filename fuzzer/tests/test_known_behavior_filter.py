"""Tests for KnownBehaviorFilter."""
import pytest

from src.models.types import Verdict, VerdictType
from src.models.platform_profile import KnownBehaviorRule, PlatformProfile
from src.filters.known_behavior_filter import KnownBehaviorFilter


def _make_verdict(invariant="I5", verdict_type=VerdictType.VIOLATION, evidence=None):
    return Verdict(
        invariant=invariant,
        verdict_type=verdict_type,
        confidence="HIGH",
        description=f"Test verdict for {invariant}",
        evidence=evidence or {},
    )


def _make_rule(id="rule1", invariants=None, conditions=None, action="downgrade_to_informational", source="test"):
    return KnownBehaviorRule(
        id=id,
        description=f"Test rule {id}",
        invariants=invariants or ["I5"],
        conditions=conditions or {},
        action=action,
        source=source,
    )


class TestKnownBehaviorFilter:
    def test_violation_matching_rule_becomes_by_design(self):
        rule = _make_rule(conditions={"field": "value"})
        f = KnownBehaviorFilter([rule])
        verdict = _make_verdict(invariant="I5", verdict_type=VerdictType.VIOLATION)
        result = f.filter_verdicts([verdict], {"field": "value"})
        assert len(result) == 1
        assert result[0].verdict_type == VerdictType.BY_DESIGN
        assert "SUPPRESSED: rule1" in result[0].description

    def test_violation_no_matching_rule_stays_violation(self):
        rule = _make_rule(conditions={"field": "other_value"})
        f = KnownBehaviorFilter([rule])
        verdict = _make_verdict(invariant="I5", verdict_type=VerdictType.VIOLATION)
        result = f.filter_verdicts([verdict], {"field": "value"})
        assert result[0].verdict_type == VerdictType.VIOLATION

    def test_unexpected_matching_rule_becomes_by_design(self):
        rule = _make_rule(conditions={"x": 1})
        f = KnownBehaviorFilter([rule])
        verdict = _make_verdict(invariant="I5", verdict_type=VerdictType.UNEXPECTED)
        result = f.filter_verdicts([verdict], {"x": 1})
        assert result[0].verdict_type == VerdictType.BY_DESIGN

    def test_rejected_verdict_unchanged(self):
        rule = _make_rule(conditions={"x": 1})
        f = KnownBehaviorFilter([rule])
        verdict = _make_verdict(invariant="I5", verdict_type=VerdictType.REJECTED)
        result = f.filter_verdicts([verdict], {"x": 1})
        assert result[0].verdict_type == VerdictType.REJECTED

    def test_nested_dotted_key_condition(self):
        rule = _make_rule(conditions={"role_config.bound_claims": {}})
        f = KnownBehaviorFilter([rule])
        verdict = _make_verdict(invariant="I5", verdict_type=VerdictType.VIOLATION)
        context = {"role_config": {"bound_claims": {}}}
        result = f.filter_verdicts([verdict], context)
        assert result[0].verdict_type == VerdictType.BY_DESIGN

    def test_contains_condition(self):
        rule = _make_rule(
            invariants=["I2"],
            conditions={"check_id_contains": "after_tighten"},
        )
        f = KnownBehaviorFilter([rule])
        verdict = _make_verdict(invariant="I2", verdict_type=VerdictType.VIOLATION)
        context = {"check_id": "policy_check_after_tighten_role"}
        result = f.filter_verdicts([verdict], context)
        assert result[0].verdict_type == VerdictType.BY_DESIGN

    def test_invariant_mismatch_no_suppress(self):
        rule = _make_rule(invariants=["I4"], conditions={"x": 1})
        f = KnownBehaviorFilter([rule])
        verdict = _make_verdict(invariant="I5", verdict_type=VerdictType.VIOLATION)
        result = f.filter_verdicts([verdict], {"x": 1})
        assert result[0].verdict_type == VerdictType.VIOLATION

    def test_evidence_merged_with_context(self):
        rule = _make_rule(conditions={"mismatch_type": "case"}, invariants=["I4"])
        f = KnownBehaviorFilter([rule])
        verdict = _make_verdict(
            invariant="I4",
            verdict_type=VerdictType.VIOLATION,
            evidence={"mismatch_type": "case"},
        )
        result = f.filter_verdicts([verdict], {})
        assert result[0].verdict_type == VerdictType.BY_DESIGN

    def test_downgraded_verdict_has_suppress_metadata(self):
        rule = _make_rule(conditions={}, source="test_source.go:42")
        f = KnownBehaviorFilter([rule])
        verdict = _make_verdict(invariant="I5", verdict_type=VerdictType.VIOLATION)
        result = f.filter_verdicts([verdict], {})
        assert result[0].evidence["suppress_rule"] == "rule1"
        assert result[0].evidence["suppress_source"] == "test_source.go:42"

    def test_from_profile(self):
        profile = PlatformProfile.from_json("src/profiles/vault.json")
        f = KnownBehaviorFilter.from_profile(profile)
        assert len(f.rules) == 7

    def test_multiple_verdicts_mixed(self):
        rule = _make_rule(conditions={"x": 1})
        f = KnownBehaviorFilter([rule])
        verdicts = [
            _make_verdict(invariant="I5", verdict_type=VerdictType.VIOLATION),
            _make_verdict(invariant="I5", verdict_type=VerdictType.REJECTED),
            _make_verdict(invariant="I4", verdict_type=VerdictType.VIOLATION),
        ]
        result = f.filter_verdicts(verdicts, {"x": 1})
        assert result[0].verdict_type == VerdictType.BY_DESIGN  # matched
        assert result[1].verdict_type == VerdictType.REJECTED    # not filtered
        assert result[2].verdict_type == VerdictType.VIOLATION   # wrong invariant

    def test_contains_condition_no_match(self):
        rule = _make_rule(
            invariants=["I2"],
            conditions={"check_id_contains": "nonexistent"},
        )
        f = KnownBehaviorFilter([rule])
        verdict = _make_verdict(invariant="I2", verdict_type=VerdictType.VIOLATION)
        result = f.filter_verdicts([verdict], {"check_id": "some_check"})
        assert result[0].verdict_type == VerdictType.VIOLATION

    def test_case_collision_suppressed_via_description(self):
        """KBF should suppress case-collision verdicts from AssertionEngine."""
        rules = [KnownBehaviorRule(
            id="vault_case_insensitive_alias",
            description="Case-insensitive aliases",
            invariants=["I4"],
            conditions={"mismatch_type": "case"},
        )]
        kbf = KnownBehaviorFilter(rules)
        verdict = Verdict(
            invariant="I4",
            verdict_type=VerdictType.UNEXPECTED,
            confidence="HIGH",
            description="Case-variant principals collapsed into same entity_id (case-insensitive alias collision)",
            evidence={"assertion": "entity_a != entity_b", "captured_values": {"entity_a": "x", "entity_b": "x"}},
        )
        result = kbf.filter_verdicts([verdict], {})
        assert result[0].verdict_type == VerdictType.BY_DESIGN

    def test_no_audience_binding_suppressed(self):
        """KBF should suppress no-audience-binding when role was created without audiences."""
        rules = [KnownBehaviorRule(
            id="vault_no_audience_when_omitted",
            description="No audience restriction",
            invariants=["I5"],
            conditions={"mismatch_type": "no_audience_binding"},
        )]
        kbf = KnownBehaviorFilter(rules)
        verdict = Verdict(
            invariant="I5",
            verdict_type=VerdictType.UNEXPECTED,
            confidence="HIGH",
            description="[AutoVerify] No audience binding: role has empty bound_audiences",
            evidence={"mismatch_type": "no_audience_binding", "bound_audiences": []},
        )
        result = kbf.filter_verdicts([verdict], {})
        assert result[0].verdict_type == VerdictType.BY_DESIGN

    def test_enrich_context_does_not_overwrite_existing(self):
        """If mismatch_type already in evidence, _enrich_context should not overwrite."""
        rules = [KnownBehaviorRule(
            id="test_rule",
            description="Test",
            invariants=["I4"],
            conditions={"mismatch_type": "explicit_value"},
        )]
        kbf = KnownBehaviorFilter(rules)
        verdict = Verdict(
            invariant="I4",
            verdict_type=VerdictType.UNEXPECTED,
            confidence="HIGH",
            description="Case-insensitive collision",  # would infer "case"
            evidence={"mismatch_type": "explicit_value"},  # but this takes priority
        )
        result = kbf.filter_verdicts([verdict], {})
        assert result[0].verdict_type == VerdictType.BY_DESIGN

    def test_enrich_context_glob_wildcard(self):
        """KBF should infer mismatch_type='glob' from description."""
        rules = [KnownBehaviorRule(
            id="vault_glob_bound_claims",
            description="glob matching",
            invariants=["I5"],
            conditions={"mismatch_type": "glob"},
        )]
        kbf = KnownBehaviorFilter(rules)
        verdict = Verdict(
            invariant="I5",
            verdict_type=VerdictType.UNEXPECTED,
            confidence="HIGH",
            description="Glob wildcard sub='*' matched all subjects",
            evidence={},
        )
        result = kbf.filter_verdicts([verdict], {})
        assert result[0].verdict_type == VerdictType.BY_DESIGN
