"""Tests for the verification pipeline (oracle path only)."""
import pytest
from unittest.mock import MagicMock
from dataclasses import dataclass, field

from src.models.types import Verdict, VerdictType
from src.verification.path_b_oracle import OracleVerifier
from src.verification.verifier_pipeline import VerifierPipeline
from src.filters.known_behavior_filter import KnownBehaviorFilter
from src.models.platform_profile import KnownBehaviorRule


@dataclass
class FakeEvent:
    event_type: str = "login_with_jwt"
    params: dict = field(default_factory=dict)
    auth_as: str = "user_A"
    captures: dict = field(default_factory=dict)


@dataclass
class FakeSequence:
    sequence_id: str = "test_seq"
    description: str = "Test"
    primary_invariant: str = "I4"
    invariant_hypothesis: str = "I4"
    events: list = field(default_factory=list)
    oracle_checks: list = field(default_factory=list)


@dataclass
class FakeResult:
    verdicts: list = field(default_factory=list)
    captured_state: dict = field(default_factory=dict)
    status: str = "COMPLETED"


class TestOracleVerifier:
    def test_no_filter_returns_raw(self):
        verifier = OracleVerifier()
        v = Verdict(invariant="I4", verdict_type=VerdictType.VIOLATION,
                    confidence="HIGH", description="test violation",
                    evidence={}, spec_reference="", cve_pattern="")
        result = FakeResult(verdicts=[v])
        output = verifier.verify(FakeSequence(), result)
        assert len(output) == 1
        assert output[0].verdict_type == VerdictType.VIOLATION

    def test_filter_suppresses_known(self):
        rules = [KnownBehaviorRule(
            id="test_rule", description="Known behavior",
            invariants=["I4"], conditions={"mismatch_type": "case"},
        )]
        kbf = KnownBehaviorFilter(rules)
        verifier = OracleVerifier(known_behavior_filter=kbf)

        v = Verdict(invariant="I4", verdict_type=VerdictType.VIOLATION,
                    confidence="HIGH", description="case collision",
                    evidence={"mismatch_type": "case"},
                    spec_reference="", cve_pattern="")
        result = FakeResult(verdicts=[v])
        output = verifier.verify(FakeSequence(), result)
        assert len(output) == 1
        assert output[0].verdict_type == VerdictType.BY_DESIGN

    def test_empty_verdicts(self):
        verifier = OracleVerifier()
        result = FakeResult(verdicts=[])
        output = verifier.verify(FakeSequence(), result)
        assert output == []

    def test_extra_kwargs_ignored(self):
        verifier = OracleVerifier(
            known_behavior_filter=None,
            profile=None,
            oracles={},
            llm_client=None,
        )
        assert verifier.filter is None

    def test_context_includes_role_config(self):
        seq = FakeSequence(events=[
            FakeEvent(event_type="create_auth_role",
                      params={"role_name": "test-role", "audience_restriction": ["vault"]}),
        ])
        verifier = OracleVerifier()
        context = verifier._build_filter_context(seq, FakeResult())
        assert context.get("role_config.role_name") == "test-role"


class TestVerifierPipeline:
    def test_oracle_only(self):
        v = Verdict(invariant="I4", verdict_type=VerdictType.VIOLATION,
                    confidence="HIGH", description="test",
                    evidence={}, spec_reference="", cve_pattern="")

        pipeline = VerifierPipeline({"paths": ["oracle"]})
        result = FakeResult(verdicts=[v])
        output = pipeline.verify(FakeSequence(), result)
        assert "oracle" in output["verdicts"]
        assert len(output["verdicts"]["oracle"]) == 1

    def test_sequence_id_in_output(self):
        pipeline = VerifierPipeline({"paths": ["oracle"]})
        seq = FakeSequence(sequence_id="my_test_seq")
        output = pipeline.verify(seq, FakeResult())
        assert output["sequence_id"] == "my_test_seq"
