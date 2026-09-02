"""Verify that blind mode prompts do NOT contain invariant knowledge.

This test is CRITICAL for paper validity — if it fails, the RQ1 ablation is invalid.
"""
import pytest
from unittest.mock import MagicMock

from src.stateful.prompt_builder import PromptBuilder
from src.stateful.generation_strategy import GenerationConfig, INVARIANT_DEFINITIONS
from src.stateful.strategies.coverage_strategy import CoverageStrategy


INVARIANT_TERMS = [
    "Proof Integrity", "Freshness", "Anti-Replay", "Flow Coherence",
    "Principal Binding", "Authorization Binding",
    "SemanticContent(Verify", "Accept(artifact_id",
    "ValidAuth(trace)", "SecurityDistinct(p1",
    "EffectivePerms(session)",
]

INVARIANT_IDS_IN_CONTEXT = ["I1:", "I2:", "I3:", "I4:", "I5:"]


class TestBlindModeNoContamination:
    """Verify that G_blind prompts contain ZERO invariant knowledge."""

    def _get_blind_prompts(self, platform="vault"):
        """Generate the actual prompts that would be sent to LLM in blind mode."""
        from src.models.platform_profile import PlatformProfile
        profile = PlatformProfile.from_json(f"src/profiles/{platform}.json")
        pb = PromptBuilder(profile)

        system_prompt = pb.build_system_prompt(
            use_examples=False,  # blind mode
            use_invariants=False,  # blind mode
        )

        config = GenerationConfig(
            invariant_focus="I4",
            num_sequences=3,
            use_examples=False,
            use_invariants=False,
        )
        strategy = CoverageStrategy(MagicMock(), profile, pb)
        mode_instruction = strategy.build_mode_instruction(config)
        user_prompt = pb.build_user_prompt(mode_instruction, config)

        return system_prompt, user_prompt

    def test_system_prompt_no_invariant_definitions(self):
        sys_p, _ = self._get_blind_prompts()
        assert "## The 5 Security Invariants" not in sys_p
        for term in INVARIANT_TERMS:
            assert term not in sys_p, f"System prompt contains '{term}'"

    def test_user_prompt_no_invariant_definitions(self):
        _, user_p = self._get_blind_prompts()
        for term in INVARIANT_TERMS:
            assert term not in user_p, f"User prompt contains '{term}'"

    def test_user_prompt_no_invariant_focus(self):
        _, user_p = self._get_blind_prompts()
        assert "Focus invariant:" not in user_p
        assert "Definition:" not in user_p or "Principal Binding" not in user_p

    def test_user_prompt_no_attack_pattern_hints(self):
        _, user_p = self._get_blind_prompts()
        assert "Mutation patterns to explore:" not in user_p or \
               user_p.split("Mutation patterns to explore:")[1].strip().startswith("\n")

    def test_no_few_shot_examples_in_blind(self):
        sys_p, _ = self._get_blind_prompts()
        assert "Few-Shot Examples" not in sys_p

    def test_no_cve_references_in_blind(self):
        """Blind mode should not mention specific CVEs."""
        sys_p, user_p = self._get_blind_prompts()
        combined = sys_p + user_p
        assert "CVE-2021-41802" not in combined
        assert "CVE-2024-7594" not in combined
        assert "CVE-2025-11621" not in combined

    def test_user_prompt_no_attack_vocabulary_in_blind(self):
        """Blind user prompt must not mention 'attack', 'invariant', or 'assertion'."""
        _, user_p = self._get_blind_prompts()
        for term in ["attack angles", "same invariant", "Assertions must"]:
            assert term not in user_p, (
                f"Blind user prompt contains '{term}' — contamination!"
            )


class TestAttackModeHasInvariants:
    """Sanity check: attack mode DOES contain invariant knowledge."""

    def _get_attack_prompts(self):
        from src.models.platform_profile import PlatformProfile
        from src.stateful.strategies.attack_strategy import AttackStrategy
        profile = PlatformProfile.from_json("src/profiles/vault.json")
        pb = PromptBuilder(profile)

        system_prompt = pb.build_system_prompt(
            use_examples=True,
            use_invariants=True,
        )

        config = GenerationConfig(
            invariant_focus="I4",
            num_sequences=3,
            use_examples=True,
            use_invariants=True,
        )
        strategy = AttackStrategy(MagicMock(), profile, pb)
        mode_instruction = strategy.build_mode_instruction(config)
        user_prompt = pb.build_user_prompt(mode_instruction, config)

        return system_prompt, user_prompt

    def test_system_prompt_has_invariants(self):
        sys_p, _ = self._get_attack_prompts()
        assert "## The 5 Security Invariants" in sys_p
        assert "Principal Binding" in sys_p

    def test_user_prompt_has_focus_invariant(self):
        _, user_p = self._get_attack_prompts()
        assert "Focus invariant: I4" in user_p

    def test_system_prompt_has_examples(self):
        sys_p, _ = self._get_attack_prompts()
        assert "Few-Shot Examples" in sys_p
