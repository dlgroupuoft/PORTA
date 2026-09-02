"""Generation strategy abstraction for event sequence generation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import logging

from src.stateful.models import Event, EventSequence, OracleCheck

# Canonical invariant definitions live in src.models.invariants.
# Re-exported here for backward compatibility — all existing imports of
# ``from src.stateful.generation_strategy import INVARIANT_DEFINITIONS``
# continue to work.
from src.models.invariants import INVARIANT_DEFINITIONS  # noqa: F401

logger = logging.getLogger(__name__)


@dataclass
class GenerationConfig:
    """Configuration for a generation strategy."""
    invariant_focus: str = "I4"
    num_sequences: int = 5
    previously_generated: list[str] = field(default_factory=list)
    custom_hints: list[str] = field(default_factory=list)
    coverage_gaps: list[str] = field(default_factory=list)
    # Whether to include few-shot examples in the prompt.
    # Set to False for ablation experiments.
    use_examples: bool = True
    # Maximum number of examples to include (for ablation: 0, 1, 3, all)
    max_examples: int = -1  # -1 = all available
    # Whether to include I1-I5 invariant definitions in the system prompt.
    # Set to False for G_blind baseline (RQ1 ablation).
    use_invariants: bool = True


class GenerationStrategy(ABC):
    """Base class for event sequence generation strategies."""

    # Subclasses must set self.profile in their __init__
    profile = None

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Return strategy identifier: 'coverage' or 'attack'."""
        ...

    @abstractmethod
    def generate(self, config: GenerationConfig) -> list[EventSequence]:
        """Generate event sequences according to this strategy."""
        ...

    @abstractmethod
    def build_mode_instruction(self, config: GenerationConfig) -> str:
        """Return the mode-specific instruction block for the user prompt."""
        ...

    # ------------------------------------------------------------------
    # Shared parsing/validation helpers — used by concrete strategies
    # ------------------------------------------------------------------

    def _parse_sequences(self, raw: dict, protocol: str = "oidc_jwt") -> list[EventSequence]:
        """Parse LLM JSON output into validated EventSequence objects.

        Handles common LLM response quirks:
        - raw is a list instead of {"sequences": [...]}
        - individual sequences are JSON-encoded strings instead of dicts

        If the subclass has a `last_quality` SequenceQualityReport attribute,
        it is updated with L0/L1 counts here.
        """
        import json as _json

        sequences = []
        quality = getattr(self, 'last_quality', None)

        # Handle raw being a list instead of {"sequences": [...]}
        if isinstance(raw, list):
            raw_seqs = raw
        else:
            raw_seqs = raw.get("sequences", [])

        if quality is not None:
            quality.total_generated = len(raw_seqs)
        for seq_data in raw_seqs:
            # Handle JSON-encoded string sequences
            if isinstance(seq_data, str):
                try:
                    seq_data = _json.loads(seq_data)
                except (ValueError, TypeError):
                    logger.warning(f"Skipping non-parseable string sequence element")
                    if quality is not None:
                        quality.record_parse_error("sequence element is unparseable string")
                    continue
            try:
                seq = self._parse_sequence(seq_data)
                if quality is not None:
                    quality.record_parse_success()
                if self._validate_sequence(seq, protocol=protocol):
                    if quality is not None:
                        quality.record_validation_success()
                    sequences.append(seq)
                else:
                    logger.warning(f"Invalid sequence rejected: {seq_data.get('id', '?')}")
                    if quality is not None:
                        quality.record_validation_error(seq_data.get('id', '?'))
            except Exception as e:
                logger.warning(f"Failed to parse sequence: {e}")
                if quality is not None:
                    quality.record_parse_error(str(e))
        return sequences

    def _parse_sequence(self, data: dict) -> EventSequence:
        """Parse LLM output dict into EventSequence."""
        events = []
        for e in data.get("events", []):
            # LLM sometimes emits events as bare strings — skip them
            if isinstance(e, str):
                continue
            # Accept common LLM aliases for event_type when examples are omitted
            etype = (e.get("event_type") or e.get("op") or e.get("type") or
                     e.get("action") or e.get("operation") or e.get("name") or "")
            if not etype:
                raise KeyError("event_type")
            events.append(Event(
                event_type=etype,
                params=e.get("params", {}),
                auth_as=e.get("auth_as", "admin"),
                expected_outcome=e.get("expected_outcome", "any"),
                captures=e.get("captures", {}),
                phase=e.get("phase", ""),
            ))

        checks = []
        for idx, c in enumerate(data.get("oracle_checks", [])):
            # Handle bare assertion strings (LLM omits dict structure without examples)
            if isinstance(c, str):
                c = {
                    "assertion": c,
                    "violation_description": c,
                }
            checks.append(OracleCheck(
                check_id=c.get("check_id", f"check_{data.get('id', 'unknown')}_{idx}"),
                invariant=c.get("invariant", data.get("primary_invariant", "")),
                assertion=c.get("assertion", ""),
                violation_description=c.get("violation_description", c.get("description", "")),
                cve_analog=c.get("cve_analog", ""),
            ))

        return EventSequence(
            sequence_id=data["id"],
            description=data["description"],
            invariant_hypothesis=data.get("invariant_hypothesis", ""),
            events=events,
            oracle_checks=checks,
            cve_analog=data.get("cve_analog", ""),
            primary_invariant=data.get("primary_invariant", ""),
        )

    # Auth event suffixes/names recognised as "login" regardless of prefix
    _AUTH_EVENT_NAMES = frozenset({
        "saml_login",
        "start_oidc_auth",
        "exchange_code_for_token",
        "token_exchange",
        "test_request_object",
        "complete_jwt_idp_login",
    })

    def _is_login_event(self, etype: str) -> bool:
        return etype.startswith("login_") or etype in self._AUTH_EVENT_NAMES

    def _validate_sequence(self, seq: EventSequence, protocol: str = "oidc_jwt") -> bool:
        """Validate that a sequence is well-formed."""
        if not seq.events:
            logger.warning("Sequence rejected: no events")
            return False

        has_login = any(self._is_login_event(e.event_type) for e in seq.events)
        if not has_login:
            etypes = [e.event_type for e in seq.events]
            logger.warning(f"Sequence rejected: no login/auth event — events={etypes}")
            return False

        has_verify = any(
            e.event_type.startswith("verify_") or e.event_type.startswith("read_role")
            or e.event_type in ("introspect_token", "session_token_inspect",
                                "access_test", "enforce_permission",
                                "test_request_object",
                                "complete_jwt_idp_login", "retrieve_idp_intent")
            for e in seq.events
        )
        if not has_verify:
            etypes = [e.event_type for e in seq.events]
            logger.warning(f"Sequence rejected: no verify event — events={etypes}")
            return False

        # Coverage mode allows empty oracle_checks (PlatformVerifier handles verification)
        if not seq.oracle_checks and self.strategy_name != "coverage":
            logger.warning("Sequence rejected: no oracle_checks")
            return False

        profile = getattr(self, "profile", None)
        if profile:
            profile_ops = set(profile.api_mapping.get(protocol, {}).keys())
            valid_events = []
            for e in seq.events:
                if e.event_type in profile_ops:
                    valid_events.append(e)
                else:
                    logger.warning(
                        f"Dropping event {e.event_type!r} — not in {profile.name}/{protocol} profile"
                    )
            if len(valid_events) < len(seq.events):
                seq.events = valid_events
                has_login_filtered = any(self._is_login_event(e.event_type) for e in seq.events)
                has_verify_filtered = any(
                    e.event_type.startswith("verify_") or e.event_type.startswith("read_role")
                    or e.event_type in ("introspect_token", "session_token_inspect",
                                        "access_test", "enforce_permission")
                    for e in seq.events
                )
                if not has_login_filtered or not has_verify_filtered:
                    logger.warning("Sequence lost login/verify after filtering — rejecting")
                    return False
        else:
            # Legacy mode: validate against Vault event registry
            from src.stateful.vault_event_types import EVENT_REGISTRY
            for e in seq.events:
                if e.event_type not in EVENT_REGISTRY:
                    logger.warning(f"Unknown event type: {e.event_type}")
                    return False

        return True
