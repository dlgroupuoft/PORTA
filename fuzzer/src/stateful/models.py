"""Data models for stateful fuzzing sequences."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Event:
    """A single API operation in a test sequence."""
    event_type: str              # Key into EVENT_REGISTRY
    params: dict = field(default_factory=dict)
    auth_as: str = "admin"       # "admin" | "user_A" | "session_user_A" | etc.
    expected_outcome: str = "any"  # "success" | "failure" | "any"
    captures: dict = field(default_factory=dict)
    # captures maps local_var_name -> json_path_in_response
    # e.g. {"user_a_entity": "auth.entity_id"}
    phase: str = ""  # "setup" | "login" | "verify" — populated by generator or inferred


@dataclass
class OracleCheck:
    """A post-sequence invariant assertion."""
    check_id: str
    invariant: str               # "I1" | "I2" | "I3" | "I4" | "I5"
    assertion: str               # e.g. "user_a_entity != user_b_entity"
    violation_description: str   # Human-readable: what it means if assertion fails
    cve_analog: str = ""


@dataclass
class EventSequence:
    """An ordered list of events forming a complete test scenario."""
    sequence_id: str
    description: str
    invariant_hypothesis: str    # "I4: ..." or "I5: ..."
    events: list[Event]
    oracle_checks: list[OracleCheck]
    cve_analog: str = ""
    primary_invariant: str = ""  # "I4" | "I5" etc.
    metadata: dict = field(default_factory=dict)  # generation strategy tags, ablation params


@dataclass
class EventResult:
    """Result of executing a single event."""
    event: Event
    http_status: int = 0
    response_body: dict = field(default_factory=dict)
    success: bool = False
    error: str = ""
    captured_values: dict = field(default_factory=dict)


@dataclass
class LoginContext:
    """Complete context for one login — what was sent vs what was granted."""

    # Input side (what we sent)
    jwt_claims: dict = field(default_factory=dict)
    role_name: str = ""
    role_config: dict = field(default_factory=dict)
    # role_config includes: user_claim, groups_claim, bound_audiences,
    #   bound_claims, token_policies, bound_subject, etc.

    # Output side (what Vault granted)
    login_success: bool = False
    http_status: int = 0
    granted_entity_id: str = ""
    granted_policies: list = field(default_factory=list)
    granted_metadata: dict = field(default_factory=dict)

    # From verify events (filled after verify_token_self, verify_entity run)
    entity_aliases: list = field(default_factory=list)
    entity_name: str = ""
    entity_policies: list = field(default_factory=list)
    identity_policies: list = field(default_factory=list)
    group_ids: list = field(default_factory=list)
    token_lookup: dict = field(default_factory=dict)
    auth_as: str = ""  # "user_A", "attacker", etc.


@dataclass
class UniversalLoginContext:
    """Platform-agnostic login verification context.

    Fields are populated from profile.verification_fields + captured data.
    No Vault-specific concepts (no entity_aliases, no identity_policies).
    """
    # What we sent
    login_type: str = ""                # "jwt" | "password" | "saml"
    sent_identity: str = ""             # The identity we claimed (sub, username, nameid)
    sent_audience: str = ""             # Audience we claimed (if applicable)
    login_params: dict = field(default_factory=dict)  # Raw login params for reference
    auth_as: str = ""                   # "user_A", "attacker", etc.

    # What was configured (from setup events)
    configured_permissions: list = field(default_factory=list)  # Roles/policies the admin set
    configured_constraints: dict = field(default_factory=dict)  # bound_claims, bound_audiences, etc.

    # What was granted (from verify events)
    login_success: bool = False
    http_status: int = 0
    granted_identity: str = ""          # WHO platform says we are
    granted_identity_id: str = ""       # Internal ID (entity_id, user UUID, etc.)
    granted_permissions: list = field(default_factory=list)  # Roles/policies we received
    granted_groups: list = field(default_factory=list)       # Group memberships
    granted_metadata: dict = field(default_factory=dict)     # Any extra metadata

    # All captured values (full dict for LLM assertions)
    captured: dict = field(default_factory=dict)


@dataclass
class SequenceResult:
    """Result of executing an entire sequence."""
    sequence: EventSequence
    event_results: list[EventResult] = field(default_factory=list)
    verdicts: list = field(default_factory=list)  # list of Verdict from oracles
    status: str = "PENDING"  # COMPLETED | SETUP_FAILED | EXECUTION_ERROR
    captured_state: dict = field(default_factory=dict)  # all captured vars
    universal_contexts: list = field(default_factory=list)  # list[UniversalLoginContext]

    @property
    def event_outcomes(self) -> list[dict]:
        """Convert event_results to the dict format expected by verdict paths."""
        return [
            {
                "event_type": er.event.event_type,
                "http_status": er.http_status,
                "success": er.success,
                "error": er.error,
            }
            for er in self.event_results
        ]
