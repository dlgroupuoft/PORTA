"""Path B: Deterministic oracle verification with KnownBehaviorFilter.

This path wraps the existing three-layer verification that SequenceExecutor
already performs, adding KnownBehaviorFilter post-processing.

The three layers (from SequenceExecutor):
  Layer 1: Sprint 3 syntactic oracles (during login)
  Layer 2: InvariantVerifier (after all events)
  Layer 3: AssertionEngine (LLM assertions from oracle_checks)

This path adds:
  Layer 4: KnownBehaviorFilter (suppress known by-design verdicts)
"""
import logging
from typing import Any

from src.models.types import Verdict, VerdictType

logger = logging.getLogger(__name__)


class OracleVerifier:
    """Post-process existing verdicts from SequenceExecutor with KnownBehaviorFilter."""

    def __init__(self, known_behavior_filter=None, **kwargs):
        # Accept and ignore extra kwargs for forward compatibility
        self.filter = known_behavior_filter

    def verify(self, sequence, execution_result) -> list[Verdict]:
        """Apply KnownBehaviorFilter to verdicts already produced by SequenceExecutor.

        Args:
            sequence: The EventSequence that was executed
            execution_result: The SequenceResult from SequenceExecutor.execute()
                Must have a .verdicts attribute (list[Verdict])

        Returns:
            Filtered list of Verdict objects
        """
        raw_verdicts = getattr(execution_result, 'verdicts', [])

        if not raw_verdicts:
            return []

        if not self.filter:
            return raw_verdicts

        context = self._build_filter_context(sequence, execution_result)
        filtered = self.filter.filter_verdicts(raw_verdicts, context)

        suppressed_count = sum(
            1 for v in filtered
            if v.evidence and v.evidence.get("suppress_rule")
        )
        if suppressed_count:
            logger.info(f"KnownBehaviorFilter suppressed {suppressed_count} verdicts")

        return filtered

    def _build_filter_context(self, sequence, execution_result) -> dict:
        """Build context dict for KnownBehaviorFilter from available data."""
        context = {
            "primary_invariant": sequence.primary_invariant,
            "sequence_id": sequence.sequence_id,
        }

        # Add captured state from execution
        captured = getattr(execution_result, 'captured_state', {})
        context.update(captured)

        # Extract role_config if available from events
        role_config = {}
        for event in sequence.events:
            if event.event_type in ("setup_jwt_role", "create_auth_role"):
                for k, v in event.params.items():
                    context[f"role_config.{k}"] = v
                role_config.update(event.params)
        if role_config:
            # Normalize field name aliases so KBF rules work regardless of
            # whether sequences use Vault-native or profile-mode names.
            if "claim_constraint_type" in role_config and "bound_claims_type" not in role_config:
                role_config["bound_claims_type"] = role_config["claim_constraint_type"]
                context["role_config.bound_claims_type"] = role_config["claim_constraint_type"]
            if "claim_constraints" in role_config and "bound_claims" not in role_config:
                role_config["bound_claims"] = role_config["claim_constraints"]
                context["role_config.bound_claims"] = role_config["claim_constraints"]
            context["role_config"] = role_config

        return context
