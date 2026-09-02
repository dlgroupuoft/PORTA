"""Abstract base class for security oracles."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.models.types import AuthResult, Invariant, MutationRecord, Verdict, VerdictType


class SecurityOracle(ABC):
    """Base oracle that checks whether a mutation + auth result violates an invariant."""

    def __init__(self, invariant: Invariant):
        self.invariant = invariant

    @abstractmethod
    def check(
        self,
        mutation: MutationRecord,
        auth_result: AuthResult,
        context: dict | None = None,
    ) -> Verdict:
        pass

    def _verdict(
        self,
        verdict_type: VerdictType,
        confidence: str,
        description: str,
        evidence: dict[str, Any],
        spec_reference: str = "",
        cve_pattern: str = "",
        requires_manual_review: bool = False,
    ) -> Verdict:
        return Verdict(
            invariant=self.invariant.value,
            verdict_type=verdict_type,
            confidence=confidence,
            description=description,
            evidence=evidence,
            spec_reference=spec_reference,
            cve_pattern=cve_pattern,
            requires_manual_review=requires_manual_review,
        )

    def _rejected(self, mutation_type: str, error: str) -> Verdict:
        """Shortcut for when the platform correctly rejected the mutation."""
        return self._verdict(
            VerdictType.REJECTED,
            "HIGH",
            f"Platform correctly rejected {mutation_type}",
            {"error": error},
        )
