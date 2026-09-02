"""Tests for generation strategies: CoverageStrategy, AttackStrategy, SequenceGenerator facade."""
import json
import pytest
from unittest.mock import MagicMock, patch

from src.stateful.generation_strategy import GenerationConfig, GenerationStrategy, INVARIANT_DEFINITIONS
from src.stateful.prompt_builder import PromptBuilder
from src.stateful.strategies.coverage_strategy import CoverageStrategy
from src.stateful.strategies.attack_strategy import AttackStrategy
from src.stateful.sequence_generator import SequenceGenerator
from src.stateful.sequence_quality import SequenceQualityReport
from src.stateful.models import Event, EventSequence, OracleCheck


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_llm_mock(sequences: list[dict]) -> MagicMock:
    """Create a mock LLM client that returns the given sequences JSON."""
    mock = MagicMock()
    mock.generate_json.return_value = {"sequences": sequences}
    return mock


_DEFAULT_ORACLE_CHECKS = [
    {"check_id": "chk1", "invariant": "I4",
     "assertion": "user_a_entity != user_b_entity",
     "violation_description": "entities differ"}
]

_SENTINEL = object()


def _minimal_sequence(seq_id: str, oracle_checks=_SENTINEL) -> dict:
    """Return a minimal valid LLM sequence dict using legacy Vault event types.

    Uses event types from the Vault EVENT_REGISTRY (login_jwt, verify_token_self)
    so it passes validation in legacy (no-profile) mode.

    Pass oracle_checks=[] explicitly to get an empty oracle_checks list.
    """
    checks = _DEFAULT_ORACLE_CHECKS if oracle_checks is _SENTINEL else oracle_checks
    return {
        "id": seq_id,
        "description": f"Test sequence {seq_id}",
        "invariant_hypothesis": "I4: test",
        "primary_invariant": "I4",
        "cve_analog": "none",
        "events": [
            {"event_type": "login_jwt",
             "params": {"role": "test-role", "jwt_claims": {"sub": "alice", "aud": "vault"}},
             "auth_as": "user_A", "phase": "login"},
            {"event_type": "verify_token_self",
             "params": {}, "auth_as": "session_user_A", "phase": "verify"},
        ],
        "oracle_checks": checks,
    }


def _make_profile_mock(ops: list[str] = None) -> MagicMock:
    """Create a minimal profile mock with the given op names."""
    ops = ops or ["login_with_jwt", "verify_granted_identity"]
    profile = MagicMock()
    profile.name = "vault"
    profile.api_mapping = {
        "oidc_jwt": {op: _make_endpoint_mock(op) for op in ops}
    }
    profile.get_constraints_text.return_value = ""
    return profile


def _make_endpoint_mock(op_name: str) -> MagicMock:
    ep = MagicMock()
    ep.method = "POST"
    ep.path = f"/v1/{op_name}"
    ep.content_type = "json"
    ep.body_map = {}
    ep.response_map = {}
    return ep


# ---------------------------------------------------------------------------
# GenerationConfig tests
# ---------------------------------------------------------------------------

class TestGenerationConfig:
    def test_defaults(self):
        cfg = GenerationConfig()
        assert cfg.invariant_focus == "I4"
        assert cfg.num_sequences == 5
        assert cfg.use_examples is True
        assert cfg.max_examples == -1
        assert cfg.previously_generated == []
        assert cfg.custom_hints == []
        assert cfg.coverage_gaps == []

    def test_custom_values(self):
        cfg = GenerationConfig(
            invariant_focus="I5",
            num_sequences=3,
            use_examples=False,
            max_examples=2,
        )
        assert cfg.invariant_focus == "I5"
        assert cfg.use_examples is False
        assert cfg.max_examples == 2


# ---------------------------------------------------------------------------
# INVARIANT_DEFINITIONS tests
# ---------------------------------------------------------------------------

class TestInvariantDefinitions:
    def test_all_five_defined(self):
        for inv in ["I1", "I2", "I3", "I4", "I5"]:
            assert inv in INVARIANT_DEFINITIONS
            assert len(INVARIANT_DEFINITIONS[inv]) > 20


# ---------------------------------------------------------------------------
# CoverageStrategy tests
# ---------------------------------------------------------------------------

class TestCoverageStrategy:
    def test_strategy_name(self):
        mock_llm = _make_llm_mock([])
        pb = PromptBuilder(None)
        strategy = CoverageStrategy(mock_llm, None, pb)
        assert strategy.strategy_name == "coverage"

    def test_mode_instruction_no_oracle_checks(self):
        mock_llm = _make_llm_mock([])
        pb = PromptBuilder(None)
        strategy = CoverageStrategy(mock_llm, None, pb)
        config = GenerationConfig()
        instruction = strategy.build_mode_instruction(config)
        assert "COVERAGE" in instruction
        assert "oracle_checks array MUST be EMPTY" in instruction or "EMPTY" in instruction

    def test_generate_returns_sequences(self):
        """CoverageStrategy can generate sequences with empty oracle_checks."""
        seq_no_checks = _minimal_sequence("seq_cov_1", oracle_checks=[])
        mock_llm = _make_llm_mock([seq_no_checks])
        pb = PromptBuilder(None)
        strategy = CoverageStrategy(mock_llm, None, pb)
        config = GenerationConfig(num_sequences=1)
        seqs = strategy.generate(config)
        assert len(seqs) == 1
        assert seqs[0].oracle_checks == []

    def test_generate_tags_strategy_metadata(self):
        seq_no_checks = _minimal_sequence("seq_cov_2", oracle_checks=[])
        mock_llm = _make_llm_mock([seq_no_checks])
        pb = PromptBuilder(None)
        strategy = CoverageStrategy(mock_llm, None, pb)
        config = GenerationConfig(num_sequences=1, use_examples=False, max_examples=2)
        seqs = strategy.generate(config)
        assert len(seqs) == 1
        assert seqs[0].metadata["generation_strategy"] == "coverage"
        assert seqs[0].metadata["used_examples"] is False
        assert seqs[0].metadata["num_examples"] == 2

    def test_generate_rejects_sequences_needing_oracle_in_attack(self):
        """Coverage mode accepts empty oracle_checks; attack mode rejects them."""
        seq_no_checks = _minimal_sequence("seq_cov_3", oracle_checks=[])
        mock_llm = _make_llm_mock([seq_no_checks])
        pb = PromptBuilder(None)
        attack = AttackStrategy(mock_llm, None, pb)
        config = GenerationConfig(num_sequences=1)
        seqs = attack.generate(config)
        # Attack mode should reject sequences with empty oracle_checks
        assert len(seqs) == 0


# ---------------------------------------------------------------------------
# AttackStrategy tests
# ---------------------------------------------------------------------------

class TestAttackStrategy:
    def test_strategy_name(self):
        mock_llm = _make_llm_mock([])
        pb = PromptBuilder(None)
        strategy = AttackStrategy(mock_llm, None, pb)
        assert strategy.strategy_name == "attack"

    def test_mode_instruction_references_invariant(self):
        mock_llm = _make_llm_mock([])
        pb = PromptBuilder(None)
        strategy = AttackStrategy(mock_llm, None, pb)
        config = GenerationConfig(invariant_focus="I4")
        instruction = strategy.build_mode_instruction(config)
        assert "ATTACK" in instruction
        assert "I4" in instruction
        assert "oracle_checks MUST NOT be empty" in instruction

    def test_generate_returns_sequences_with_checks(self):
        seq = _minimal_sequence("seq_atk_1")
        mock_llm = _make_llm_mock([seq])
        pb = PromptBuilder(None)
        strategy = AttackStrategy(mock_llm, None, pb)
        config = GenerationConfig(num_sequences=1)
        seqs = strategy.generate(config)
        assert len(seqs) == 1
        assert len(seqs[0].oracle_checks) > 0

    def test_generate_tags_strategy_metadata(self):
        seq = _minimal_sequence("seq_atk_2")
        mock_llm = _make_llm_mock([seq])
        pb = PromptBuilder(None)
        strategy = AttackStrategy(mock_llm, None, pb)
        config = GenerationConfig(num_sequences=1, invariant_focus="I5", use_examples=True)
        seqs = strategy.generate(config)
        assert len(seqs) == 1
        meta = seqs[0].metadata
        assert meta["generation_strategy"] == "attack"
        assert meta["invariant_focus"] == "I5"
        assert meta["used_examples"] is True


# ---------------------------------------------------------------------------
# SequenceGenerator facade tests
# ---------------------------------------------------------------------------

class TestSequenceGeneratorFacade:
    def test_init_creates_strategies(self):
        mock_llm = MagicMock()
        gen = SequenceGenerator(mock_llm)
        assert hasattr(gen, 'coverage_strategy')
        assert hasattr(gen, 'attack_strategy')
        assert hasattr(gen, 'prompt_builder')
        assert isinstance(gen.coverage_strategy, CoverageStrategy)
        assert isinstance(gen.attack_strategy, AttackStrategy)

    def test_generate_delegates_to_coverage(self):
        seq = _minimal_sequence("seq_fac_cov", oracle_checks=[])
        mock_llm = _make_llm_mock([seq])
        gen = SequenceGenerator(mock_llm)
        seqs = gen.generate(mode="coverage", num_sequences=1)
        mock_llm.generate_json.assert_called_once()
        # Coverage call passes coverage mode instruction
        call_args = mock_llm.generate_json.call_args
        system_prompt, user_prompt = call_args[0]
        assert "COVERAGE" in user_prompt

    def test_generate_delegates_to_attack(self):
        seq = _minimal_sequence("seq_fac_atk")
        mock_llm = _make_llm_mock([seq])
        gen = SequenceGenerator(mock_llm)
        seqs = gen.generate(mode="attack", num_sequences=1, invariant_focus="I4")
        mock_llm.generate_json.assert_called_once()
        call_args = mock_llm.generate_json.call_args
        system_prompt, user_prompt = call_args[0]
        assert "ATTACK" in user_prompt

    def test_generate_coverage_sequences_have_metadata(self):
        seq = _minimal_sequence("seq_meta_cov", oracle_checks=[])
        mock_llm = _make_llm_mock([seq])
        gen = SequenceGenerator(mock_llm)
        seqs = gen.generate(mode="coverage", num_sequences=1)
        assert len(seqs) == 1
        assert seqs[0].metadata["generation_strategy"] == "coverage"

    def test_generate_attack_sequences_have_metadata(self):
        seq = _minimal_sequence("seq_meta_atk")
        mock_llm = _make_llm_mock([seq])
        gen = SequenceGenerator(mock_llm)
        seqs = gen.generate(mode="attack", num_sequences=1, invariant_focus="I5")
        assert len(seqs) == 1
        meta = seqs[0].metadata
        assert meta["generation_strategy"] == "attack"
        assert meta["invariant_focus"] == "I5"

    def test_use_examples_false_omits_examples_from_prompt(self):
        seq = _minimal_sequence("seq_no_ex", oracle_checks=[])
        mock_llm = _make_llm_mock([seq])
        gen = SequenceGenerator(mock_llm)
        gen.generate(mode="coverage", num_sequences=1, use_examples=False)
        call_args = mock_llm.generate_json.call_args
        system_prompt = call_args[0][0]
        assert "Few-Shot Examples" not in system_prompt

    def test_use_examples_true_includes_examples_in_prompt(self):
        seq = _minimal_sequence("seq_with_ex")
        mock_llm = _make_llm_mock([seq])
        gen = SequenceGenerator(mock_llm)
        gen.generate(mode="attack", num_sequences=1, use_examples=True)
        call_args = mock_llm.generate_json.call_args
        system_prompt = call_args[0][0]
        assert "Few-Shot Examples" in system_prompt

    def test_invalid_sequences_rejected(self):
        """Sequences missing login event are rejected."""
        bad_seq = {
            "id": "bad_seq",
            "description": "No login",
            "invariant_hypothesis": "I4: test",
            "primary_invariant": "I4",
            "cve_analog": "none",
            "events": [
                {"event_type": "verify_granted_identity",
                 "params": {}, "auth_as": "session_user_A", "phase": "verify"},
            ],
            "oracle_checks": [
                {"check_id": "c", "invariant": "I4", "assertion": "x == y",
                 "violation_description": "test"}
            ],
        }
        mock_llm = _make_llm_mock([bad_seq])
        gen = SequenceGenerator(mock_llm)
        seqs = gen.generate(mode="attack", num_sequences=1)
        assert len(seqs) == 0

    def test_backward_compat_build_system_prompt_v2(self):
        """_build_system_prompt_v2 still works for existing tests."""
        mock_llm = MagicMock()
        gen = SequenceGenerator(mock_llm)  # no profile = legacy mode
        prompt = gen._build_system_prompt_v2("oidc_jwt")
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_backward_compat_invariant_definitions_import(self):
        """INVARIANT_DEFINITIONS importable from sequence_generator for backward compat."""
        from src.stateful.sequence_generator import INVARIANT_DEFINITIONS as ID
        assert "I4" in ID
        assert "I5" in ID


# ---------------------------------------------------------------------------
# SequenceQualityReport tests
# ---------------------------------------------------------------------------

class TestSequenceQualityReport:
    def test_defaults(self):
        report = SequenceQualityReport()
        assert report.total_generated == 0
        assert report.level0_parseable == 0
        assert report.level4_finding == 0

    def test_to_dict(self):
        report = SequenceQualityReport(
            total_generated=10,
            level0_parseable=8,
            level1_valid_structure=6,
            level2_executable=5,
            level3_meaningful=4,
            level4_finding=2,
        )
        d = report.to_dict()
        assert d["total_generated"] == 10
        assert d["level0_parseable"] == 8
        assert d["rates"]["parse_rate"] == pytest.approx(0.8)
        assert d["rates"]["validity_rate"] == pytest.approx(6 / 8)
        assert d["rates"]["finding_rate"] == pytest.approx(2 / 5)

    def test_to_dict_zero_division_safe(self):
        report = SequenceQualityReport()
        d = report.to_dict()
        assert d["rates"]["parse_rate"] == 0.0
        assert d["rates"]["validity_rate"] == 0.0

    def test_record_methods(self):
        report = SequenceQualityReport(total_generated=5)
        report.record_parse_success()
        report.record_parse_success()
        report.record_validation_success()
        report.record_execution_success()
        report.record_meaningful()
        report.record_finding()
        assert report.level0_parseable == 2
        assert report.level1_valid_structure == 1
        assert report.level2_executable == 1
        assert report.level3_meaningful == 1
        assert report.level4_finding == 1

    def test_error_lists_capped_at_10(self):
        report = SequenceQualityReport()
        for i in range(15):
            report.record_parse_error(f"error {i}")
        d = report.to_dict()
        assert len(d["parse_errors"]) == 10


# ---------------------------------------------------------------------------
# PromptBuilder use_invariants tests (Part C of Prompt 7)
# ---------------------------------------------------------------------------

class TestPromptBuilderUseInvariants:
    def test_system_prompt_without_invariants(self):
        """When use_invariants=False, prompt must NOT contain I1-I5 definitions."""
        pb = PromptBuilder(None)
        prompt = pb.build_system_prompt(use_invariants=False)
        assert "## The 5 Security Invariants" not in prompt
        assert "Proof Integrity: The broker must" not in prompt
        assert "Principal Binding: Security-distinct" not in prompt

    def test_system_prompt_with_invariants_default(self):
        """Default behaviour (use_invariants=True) includes invariant section."""
        pb = PromptBuilder(None)
        prompt = pb.build_system_prompt(use_invariants=True)
        assert "## The 5 Security Invariants" in prompt

    def test_use_invariants_false_passed_through_generate(self):
        """use_invariants=False reaches the LLM call: system prompt omits invariant section."""
        seq = _minimal_sequence("seq_no_inv", oracle_checks=[])
        mock_llm = _make_llm_mock([seq])
        gen = SequenceGenerator(mock_llm)
        gen.generate(mode="coverage", num_sequences=1, use_invariants=False)
        call_args = mock_llm.generate_json.call_args
        system_prompt = call_args[0][0]
        assert "## The 5 Security Invariants" not in system_prompt

    def test_generation_config_default_use_invariants_true(self):
        cfg = GenerationConfig()
        assert cfg.use_invariants is True

    def test_generation_config_use_invariants_false(self):
        cfg = GenerationConfig(use_invariants=False)
        assert cfg.use_invariants is False
