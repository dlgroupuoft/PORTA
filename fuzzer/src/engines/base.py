"""Abstract base class for mutation engines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable

from src.models.types import Credential, Invariant, MutationRecord, Protocol

PRIORITY_LEVELS = ("critical", "high", "normal", "low")


class MutationEngine(ABC):
    """Base class that each protocol mutation engine must implement."""

    def __init__(self, protocol: Protocol):
        self.protocol = protocol
        self._mutation_registry: dict[str, dict] = {}

    def register_mutation(
        self,
        name: str,
        invariant: Invariant,
        mutation_fn: Callable,
        description: str = "",
        priority: str = "normal",
        cve_pattern: str | None = None,
    ) -> None:
        """Register a named mutation function with its target invariant."""
        self._mutation_registry[name] = {
            "name": name,
            "invariant": invariant,
            "fn": mutation_fn,
            "description": description or name,
            "priority": priority,
            "cve_pattern": cve_pattern,
        }

    def list_mutations(
        self,
        invariant: Invariant | None = None,
        min_priority: str | None = None,
    ) -> list[dict]:
        """List all registered mutations, optionally filtered by invariant and priority."""
        results = []
        for entry in self._mutation_registry.values():
            if invariant is not None and entry["invariant"] != invariant:
                continue
            if min_priority is not None and not _meets_priority(entry["priority"], min_priority):
                continue
            results.append({
                "name": entry["name"],
                "invariant": entry["invariant"],
                "description": entry["description"],
                "priority": entry["priority"],
                "cve_pattern": entry["cve_pattern"],
            })
        return results

    @abstractmethod
    def generate_baseline(self, config: dict | None = None) -> Credential:
        """Generate a valid, legitimate credential for this protocol."""

    def generate_mutations(
        self,
        baseline: Credential,
        invariant: Invariant | None = None,
        mutations: list[str] | None = None,
        min_priority: str | None = None,
    ) -> list[MutationRecord]:
        """Apply registered mutations to the baseline credential."""
        records: list[MutationRecord] = []
        for name, entry in self._mutation_registry.items():
            if invariant is not None and entry["invariant"] != invariant:
                continue
            if mutations is not None and name not in mutations:
                continue
            if min_priority is not None and not _meets_priority(entry["priority"], min_priority):
                continue
            mutated_cred = self._apply_mutation(name, baseline, {})
            records.append(MutationRecord(
                mutation_type=name,
                target_field=entry["description"],
                description=entry["description"],
                credential=mutated_cred,
            ))
        return records

    @abstractmethod
    def _apply_mutation(
        self, name: str, baseline: Credential, config: dict
    ) -> Credential:
        """Apply a specific named mutation to a credential."""


def _meets_priority(mutation_priority: str, min_priority: str) -> bool:
    """Return True if mutation_priority is at least as important as min_priority."""
    try:
        mut_idx = PRIORITY_LEVELS.index(mutation_priority)
        min_idx = PRIORITY_LEVELS.index(min_priority)
    except ValueError:
        return True
    return mut_idx <= min_idx
