"""Structured campaign report for experimental evaluation."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import json
import hashlib
import os


@dataclass
class FindingRecord:
    """A single finding from any verdict path."""
    finding_id: str          # Unique hash for dedup
    sequence_id: str
    sequence_description: str
    generation_strategy: str  # "coverage" or "attack"
    verdict_path: str         # "oracle", "oracle_guided", "plain_llm", "assertion"
    invariant: str            # I1-I5 or "UNKNOWN" — sequence primary invariant
    identified_invariant: str # What the verdict path said (invariant from the Verdict object)
    verdict_type: str         # VIOLATION, UNEXPECTED, REJECTED, BY_DESIGN
    confidence: str           # HIGH, MEDIUM, LOW
    description: str
    cve_analog: str
    evidence: dict = field(default_factory=dict)
    detection_source: str = ""  # "L1_syntactic" | "L2_platform_verifier" | "L3_assertion" | "mutation_sweep"
    # Manual triage result (filled in later)
    triage_result: str = ""  # "TP", "FP", "DISPUTED", ""

    def dedup_key(self) -> str:
        """Generate dedup key based on root cause pattern.

        For mutation_sweep findings: dedup by mutation_name + identified_invariant.
        For sequence oracle findings: dedup by invariant + description hash.
        """
        source = self.evidence.get("source", "")
        if source == "mutation_sweep" or self.verdict_path == "mutation_sweep":
            # Mutation sweep: same mutation = same root cause regardless of sequence
            mutation_name = self.evidence.get("mutation_name", "unknown")
            # Bug 6 fix: glob star/question/bracket are all the same root cause
            # (Vault's strutil.GlobbedStringsMatch treating claim values as patterns).
            if mutation_name.startswith("i4_bound_claims_glob"):
                mutation_name = "i4_bound_claims_glob"
            return f"sweep:{self.identified_invariant}:{mutation_name}"
        else:
            # Sequence-level finding: dedup by invariant + description pattern
            core = f"seq:{self.identified_invariant}:{self.verdict_path}"
            desc_hash = hashlib.md5(self.description.lower().encode()).hexdigest()[:8]
            return f"{core}:{desc_hash}"

    def to_dict(self) -> dict:
        return {
            "finding_id": self.finding_id,
            "sequence_id": self.sequence_id,
            "sequence_description": self.sequence_description,
            "generation_strategy": self.generation_strategy,
            "verdict_path": self.verdict_path,
            "invariant": self.invariant,
            "identified_invariant": self.identified_invariant,
            "verdict_type": self.verdict_type,
            "confidence": self.confidence,
            "description": self.description,
            "cve_analog": self.cve_analog,
            "evidence": self.evidence,
            "detection_source": self.detection_source,
            "triage_result": self.triage_result,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FindingRecord":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class SequenceRecord:
    """Record of a single sequence execution."""
    sequence_id: str
    description: str
    generation_strategy: str  # "coverage" or "attack"
    primary_invariant: str
    invariant_hypothesis: str
    cve_analog: str
    # Execution
    status: str  # "COMPLETED", "SETUP_FAILED", "EXECUTION_ERROR"
    events_total: int = 0
    events_succeeded: int = 0
    events_failed: int = 0
    # Quality
    used_examples: bool = True
    num_examples: int = -1
    # Events detail (serialised Event dicts — sufficient for replay)
    events: list = field(default_factory=list)
    # Oracle checks detail (serialised OracleCheck dicts — needed for replay)
    oracle_checks: list = field(default_factory=list)
    # Sequence metadata (generation_strategy tag, ablation params, etc.)
    sequence_metadata: dict = field(default_factory=dict)
    captured_state: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "sequence_id": self.sequence_id,
            "description": self.description,
            "generation_strategy": self.generation_strategy,
            "primary_invariant": self.primary_invariant,
            "invariant_hypothesis": self.invariant_hypothesis,
            "cve_analog": self.cve_analog,
            "status": self.status,
            "events_total": self.events_total,
            "events_succeeded": self.events_succeeded,
            "events_failed": self.events_failed,
            "used_examples": self.used_examples,
            "num_examples": self.num_examples,
            "events": self.events,
            "oracle_checks": self.oracle_checks,
            "sequence_metadata": self.sequence_metadata,
            "captured_state": {k: str(v)[:200] for k, v in self.captured_state.items()},
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SequenceRecord":
        known = {k for k in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})


@dataclass
class CampaignReport:
    """Complete campaign report with experimental breakdowns."""

    # Metadata
    campaign_id: str = ""
    timestamp: str = ""
    platform: str = ""
    base_url: str = ""
    llm_model: str = ""
    invariants_tested: list[str] = field(default_factory=list)

    # Run configuration (for reproducibility)
    config: dict = field(default_factory=dict)

    # Raw data
    sequences: list[SequenceRecord] = field(default_factory=list)
    findings: list[FindingRecord] = field(default_factory=list)

    # Aggregated stats (computed in finalize())
    summary: dict = field(default_factory=dict)

    def add_sequence(self, record: SequenceRecord):
        self.sequences.append(record)

    def add_finding(self, record: FindingRecord):
        self.findings.append(record)

    def finalize(self):
        """Compute all summary statistics after campaign completes."""
        self.summary = {
            "total_sequences": len(self.sequences),
            "by_strategy": self._group_by("sequences", "generation_strategy"),
            "by_status": self._group_by("sequences", "status"),
            "by_invariant": self._group_by("sequences", "primary_invariant"),

            "total_findings": len(self.findings),
            "findings_by_strategy": self._group_findings("generation_strategy"),
            "findings_by_verdict_path": self._group_findings("verdict_path"),
            "findings_by_invariant": self._group_findings("invariant"),
            "findings_by_confidence": self._group_findings("confidence"),

            # Dedup stats
            "unique_findings": len(self._deduplicated_findings()),
            "duplicate_count": len(self.findings) - len(self._deduplicated_findings()),

            # Execution quality
            "execution_rate": self._execution_rate(),
            "event_success_rates": self._event_success_rates(),

            # Cross-tabulation: strategy × verdict_path
            "cross_tab": self._cross_tabulation(),
        }

    def _group_by(self, collection_name: str, field_name: str) -> dict:
        collection = getattr(self, collection_name)
        groups: dict[str, int] = {}
        for item in collection:
            key = getattr(item, field_name, "UNKNOWN")
            groups[key] = groups.get(key, 0) + 1
        return groups

    def _group_findings(self, field_name: str) -> dict:
        groups: dict[str, int] = {}
        for f in self.findings:
            key = getattr(f, field_name, "UNKNOWN")
            groups[key] = groups.get(key, 0) + 1
        return groups

    def _deduplicated_findings(self) -> list[FindingRecord]:
        seen: set[str] = set()
        unique: list[FindingRecord] = []
        for f in self.findings:
            key = f.dedup_key()
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    def _execution_rate(self) -> dict:
        rates: dict[str, float] = {}
        for strategy in ["coverage", "attack"]:
            seqs = [s for s in self.sequences if s.generation_strategy == strategy]
            if seqs:
                completed = sum(1 for s in seqs if s.status == "COMPLETED")
                rates[strategy] = completed / len(seqs)
        return rates

    def _event_success_rates(self) -> dict:
        rates: dict[str, float] = {}
        for strategy in ["coverage", "attack"]:
            seqs = [s for s in self.sequences if s.generation_strategy == strategy]
            total_events = sum(s.events_total for s in seqs)
            succeeded = sum(s.events_succeeded for s in seqs)
            if total_events:
                rates[strategy] = succeeded / total_events
        return rates

    def _cross_tabulation(self) -> dict:
        tab: dict[str, int] = {}
        for f in self.findings:
            key = f"{f.generation_strategy}:{f.verdict_path}"
            tab[key] = tab.get(key, 0) + 1
        return tab

    def sweep_findings_summary(self) -> dict:
        """Break down sweep findings by mutation_name and verdict_type."""
        sweep = [f for f in self.findings if f.detection_source == "mutation_sweep"]
        by_mutation: dict[str, dict] = {}
        for f in sweep:
            name = f.evidence.get("mutation_name", "unknown")
            entry = by_mutation.setdefault(name, {"VIOLATION": 0, "UNEXPECTED": 0, "count": 0})
            entry[f.verdict_type] = entry.get(f.verdict_type, 0) + 1
            entry["count"] += 1
        return {
            "total_sweep_findings": len(sweep),
            "by_mutation": by_mutation,
            "violations_only": [f.to_dict() for f in sweep if f.verdict_type == "VIOLATION"],
        }

    def save(self, output_dir: str) -> str:
        """Save report to structured directory. Returns the campaign directory path."""
        campaign_dir = os.path.join(output_dir, f"campaign_{self.campaign_id}")
        os.makedirs(campaign_dir, exist_ok=True)

        # Summary
        with open(os.path.join(campaign_dir, "summary.json"), "w") as f:
            json.dump(self.summary, f, indent=2, default=str)

        # All sequences (also serves as replay source)
        with open(os.path.join(campaign_dir, "sequences.json"), "w") as f:
            json.dump([s.to_dict() for s in self.sequences], f, indent=2, default=str)

        # All findings
        with open(os.path.join(campaign_dir, "findings.json"), "w") as f:
            json.dump([f.to_dict() for f in self.findings], f, indent=2, default=str)

        # Split by strategy
        for strategy in ["coverage", "attack"]:
            strategy_dir = os.path.join(campaign_dir, strategy)
            os.makedirs(strategy_dir, exist_ok=True)

            strat_seqs = [s for s in self.sequences if s.generation_strategy == strategy]
            strat_findings = [f for f in self.findings if f.generation_strategy == strategy]

            with open(os.path.join(strategy_dir, "sequences.json"), "w") as f:
                json.dump([s.to_dict() for s in strat_seqs], f, indent=2, default=str)

            with open(os.path.join(strategy_dir, "findings.json"), "w") as f:
                json.dump([f.to_dict() for f in strat_findings], f, indent=2, default=str)

            # Further split findings by verdict path
            for path in ["oracle", "oracle_guided", "plain_llm", "assertion"]:
                path_findings = [f for f in strat_findings if f.verdict_path == path]
                if path_findings:
                    with open(os.path.join(strategy_dir, f"findings_{path}.json"), "w") as f:
                        json.dump([f.to_dict() for f in path_findings], f, indent=2, default=str)

        # Deduplicated findings
        deduped = self._deduplicated_findings()
        with open(os.path.join(campaign_dir, "unique_findings.json"), "w") as f:
            json.dump([f.to_dict() for f in deduped], f, indent=2, default=str)

        # Unique finding sequences: for each unique finding, include the
        # full sequence that produced it (events, oracle_checks, captured_state).
        _seq_by_id = {s.sequence_id: s for s in self.sequences}
        unique_seqs = []
        for finding in deduped:
            seq = _seq_by_id.get(finding.sequence_id)
            if seq:
                unique_seqs.append({
                    "finding": finding.to_dict(),
                    "sequence": seq.to_dict(),
                })
        with open(os.path.join(campaign_dir, "unique_finding_sequences.json"), "w") as f:
            json.dump(unique_seqs, f, indent=2, default=str)

        return campaign_dir
