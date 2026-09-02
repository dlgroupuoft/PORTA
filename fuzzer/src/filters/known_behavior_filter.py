"""Filter that downgrades verdicts matching known platform by-design behaviors."""
from __future__ import annotations
import logging
from typing import Any

from src.models.types import Verdict, VerdictType
from src.models.platform_profile import KnownBehaviorRule

logger = logging.getLogger(__name__)


class KnownBehaviorFilter:
    """Post-verdict filter that downgrades findings matching known by-design behaviors."""

    def __init__(self, rules: list[KnownBehaviorRule]):
        self.rules = rules

    @classmethod
    def from_profile(cls, profile) -> "KnownBehaviorFilter":
        return cls(rules=profile.known_behaviors)

    def filter_verdicts(self, verdicts: list[Verdict], context: dict[str, Any]) -> list[Verdict]:
        """Check each verdict against known behavior rules.

        If a VIOLATION or UNEXPECTED verdict matches a rule:
          → Downgrade to BY_DESIGN with explanation
          → Keep in results (for audit trail) but mark as suppressed

        Rules are matched by:
          1. The verdict's invariant must be in rule.invariants
          2. All conditions in rule.conditions must match the context or evidence
        """
        filtered = []
        for verdict in verdicts:
            if verdict.verdict_type in (VerdictType.VIOLATION, VerdictType.UNEXPECTED):
                enriched = self._enrich_context(verdict, context)
                matched_rule = self._match_rule(verdict, enriched)
                if matched_rule:
                    verdict = self._downgrade(verdict, matched_rule)
                    logger.info(f"Suppressed: {matched_rule.id} → {verdict.description[:80]}")
            filtered.append(verdict)
        return filtered

    def _enrich_context(self, verdict: Verdict, context: dict) -> dict:
        """Add derived fields to context for better rule matching."""
        enriched = dict(context)
        evidence = verdict.evidence or {}

        # Propagate mutation_name from evidence to context for KBF rule matching
        if evidence.get("mutation_name") and "mutation_name" not in enriched:
            enriched["mutation_name"] = evidence["mutation_name"]

        # Already has mismatch_type? Normalize common aliases, then use it.
        _existing_mt = evidence.get("mismatch_type") or enriched.get("mismatch_type")
        if _existing_mt:
            # Normalize case_divergence → case for KBF rule matching
            if _existing_mt == "case_divergence":
                enriched["mismatch_type"] = "case"
            else:
                enriched["mismatch_type"] = _existing_mt
            return enriched

        # Infer mismatch_type from verdict description/evidence.
        # Only apply keyword-based inference to PlatformVerifier verdicts,
        # NOT to user-defined oracle_check assertions — those describe the
        # expected behavior, and their wording should not trigger suppression.
        desc_lower = verdict.description.lower()
        _is_platform_verifier = (
            getattr(verdict, 'detection_source', '') == "L2_platform_verifier"
            or "[platformverify:" in desc_lower  # backward compat fallback
        )

        if _is_platform_verifier:
            if "case" in desc_lower and ("collision" in desc_lower or "collapsed" in desc_lower or "insensitive" in desc_lower or "case_confusion" in desc_lower or "case_divergence" in desc_lower):
                enriched["mismatch_type"] = "case"
            elif "type" in desc_lower and ("coercion" in desc_lower or "confusion" in desc_lower):
                enriched["mismatch_type"] = "type_coercion"
            elif "glob" in desc_lower or "wildcard" in desc_lower:
                enriched["mismatch_type"] = "glob"
            elif "no audience" in desc_lower or "empty bound_audiences" in desc_lower:
                enriched["mismatch_type"] = "no_audience_binding"
            elif "policy" in desc_lower and ("escalation" in desc_lower or "override" in desc_lower):
                enriched["mismatch_type"] = "policy_escalation"
            elif ("introspect" in desc_lower or "cross_client" in desc_lower or "cross-client" in desc_lower) and ("client" in desc_lower):
                enriched["mismatch_type"] = "cross_client_introspection"

        return enriched

    def _match_rule(self, verdict: Verdict, context: dict) -> KnownBehaviorRule | None:
        """Find the first rule that matches this verdict + context."""
        merged_ctx = {**context, **(verdict.evidence or {})}

        for rule in self.rules:
            # Rules marked is_known_cve should NOT suppress findings —
            # they document known vulnerabilities, not by-design behaviors.
            if rule.conditions.get("is_known_cve"):
                continue
            if verdict.invariant not in rule.invariants:
                continue
            if self._conditions_match(rule.conditions, merged_ctx):
                return rule
        return None

    def _conditions_match(self, conditions: dict, context: dict) -> bool:
        """Check if all conditions are satisfied by the context.

        Supports:
          - Direct match: {"field": value}
          - Nested dotted paths: {"role_config.bound_claims": {}}
          - Contains check: {"check_id_contains": "after_tighten"}
        """
        for key, expected in conditions.items():
            if key.endswith("_contains"):
                actual_key = key.replace("_contains", "")
                actual = self._get_nested(context, actual_key)
                if actual is None or expected not in str(actual):
                    return False
            else:
                actual = self._get_nested(context, key)
                if actual != expected:
                    return False
        return True

    def _get_nested(self, d: dict, dotted_key: str) -> Any:
        """Get a value from a nested dict using dotted key notation."""
        parts = dotted_key.split(".")
        current = d
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    def _downgrade(self, verdict: Verdict, rule: KnownBehaviorRule) -> Verdict:
        """Downgrade a verdict to BY_DESIGN."""
        return Verdict(
            invariant=verdict.invariant,
            verdict_type=VerdictType.BY_DESIGN,
            confidence=verdict.confidence,
            description=f"[SUPPRESSED: {rule.id}] {verdict.description}",
            evidence={
                **(verdict.evidence or {}),
                "suppress_rule": rule.id,
                "suppress_reason": rule.description,
                "suppress_source": rule.source,
            },
            spec_reference=verdict.spec_reference,
            cve_pattern=verdict.cve_pattern,
            requires_manual_review=False,
        )
