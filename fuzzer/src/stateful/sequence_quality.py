"""Measure event sequence quality at multiple levels."""

from dataclasses import dataclass, field
from src.stateful.models import EventSequence


@dataclass
class SequenceQualityReport:
    """Quality metrics for a batch of generated sequences.

    Tracks quality at 5 progressive levels:
      0 — parseable JSON (LLM output was valid JSON with expected structure)
      1 — structurally valid (has setup→login→verify, uses known ops)
      2 — all events executed without unexpected errors
      3 — produced meaningful captured state (non-empty captures)
      4 — found at least one finding (VIOLATION or UNEXPECTED verdict)
    """
    total_generated: int = 0
    # Level 0: parseable JSON
    level0_parseable: int = 0
    # Level 1: structurally valid (has setup→login→verify, known ops)
    level1_valid_structure: int = 0
    # Level 2: all events executed without unexpected errors
    level2_executable: int = 0
    # Level 3: produced meaningful captured state
    level3_meaningful: int = 0
    # Level 4: found at least one finding (TP or FP)
    level4_finding: int = 0

    # Detailed breakdowns
    parse_errors: list[str] = field(default_factory=list)
    validation_errors: list[str] = field(default_factory=list)
    execution_errors: list[str] = field(default_factory=list)

    def record_parse_success(self):
        self.level0_parseable += 1

    def record_parse_error(self, error: str):
        self.parse_errors.append(error)

    def record_validation_success(self):
        self.level1_valid_structure += 1

    def record_validation_error(self, error: str):
        self.validation_errors.append(error)

    def record_execution_success(self):
        self.level2_executable += 1

    def record_execution_error(self, error: str):
        self.execution_errors.append(error)

    def record_meaningful(self):
        self.level3_meaningful += 1

    def record_finding(self):
        self.level4_finding += 1

    def to_dict(self) -> dict:
        # Detect replay mode: L2+ populated but L0/L1 are zero
        is_replay = (self.level2_executable > 0 and self.total_generated == 0)

        if is_replay:
            rates = {
                "mode": "replay",
                "execution_rate": 1.0,
                "meaningful_rate": self.level3_meaningful / max(self.level2_executable, 1),
                "finding_rate": self.level4_finding / max(self.level2_executable, 1),
                # L0/L1 rates not applicable in replay
                "parse_rate": None,
                "validity_rate": None,
            }
        else:
            rates = {
                "mode": "generate",
                "parse_rate": self.level0_parseable / max(self.total_generated, 1),
                "validity_rate": self.level1_valid_structure / max(self.level0_parseable, 1),
                "execution_rate": self.level2_executable / max(self.level1_valid_structure, 1),
                "meaningful_rate": self.level3_meaningful / max(self.level2_executable, 1),
                "finding_rate": self.level4_finding / max(self.level2_executable, 1),
            }

        return {
            "total_generated": self.total_generated,
            "level0_parseable": self.level0_parseable,
            "level1_valid_structure": self.level1_valid_structure,
            "level2_executable": self.level2_executable,
            "level3_meaningful": self.level3_meaningful,
            "level4_finding": self.level4_finding,
            "rates": rates,
            "parse_errors": self.parse_errors[:10],
            "validation_errors": self.validation_errors[:10],
            "execution_errors": self.execution_errors[:10],
        }
