"""VALENCE shared data models."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Protocol(str, Enum):
    JWT = "jwt"
    SAML = "saml"
    OAUTH2_CODE = "oauth2_code"
    LDAP = "ldap"


class Invariant(str, Enum):
    I1_PROOF_INTEGRITY = "I1"
    I2_FRESHNESS = "I2"
    I3_FLOW_COHERENCE = "I3"
    I4_PRINCIPAL_BINDING = "I4"
    I5_AUTHORIZATION_BINDING = "I5"


class Platform(str, Enum):
    VAULT = "vault"
    KEYCLOAK = "keycloak"
    DEX = "dex"


class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class VerdictType(str, Enum):
    VIOLATION = "VIOLATION"
    UNEXPECTED = "UNEXPECTED"
    BY_DESIGN = "BY_DESIGN"
    REJECTED = "REJECTED"
    ERROR = "ERROR"
    INCONCLUSIVE = "INCONCLUSIVE"


class AuthContext(str, Enum):
    JWT_BEARER = "jwt_bearer"
    # External IdP JWT login (e.g. ZITADEL JWT provider); OIDC ID Token rules apply.
    EXTERNAL_JWT_PROVIDER = "external_jwt_provider"
    OAUTH2_CLIENT_ASSERTION = "client_assertion"
    SAML_ASSERTION = "saml_assertion"
    OAUTH2_CODE = "oauth2_code"
    LDAP_BIND = "ldap_bind"


# ---------------------------------------------------------------------------
# Helper for datetime serialization
# ---------------------------------------------------------------------------

def _serialize(obj: Any) -> Any:
    """Recursively convert an object for JSON serialization."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(v) for v in obj]
    return obj


def _to_dict(obj: Any) -> dict:
    return _serialize(asdict(obj))


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Credential:
    """An upstream credential to be submitted to a broker."""
    protocol: Protocol
    raw_token: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    claims: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Credential:
        d = dict(data)
        d["protocol"] = Protocol(d["protocol"])
        return cls(**d)


@dataclass
class AuthResult:
    """The result of submitting a credential to a broker."""
    success: bool
    platform: Platform
    protocol: Protocol
    upstream_credential: dict[str, Any] = field(default_factory=dict)
    downstream_token: str = ""
    downstream_claims: dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    http_status: int = 0
    raw_response: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> AuthResult:
        d = dict(data)
        d["platform"] = Platform(d["platform"])
        d["protocol"] = Protocol(d["protocol"])
        if isinstance(d.get("timestamp"), str):
            d["timestamp"] = datetime.fromisoformat(d["timestamp"])
        return cls(**d)


@dataclass
class Verdict:
    """Oracle verdict on whether an invariant was violated."""
    invariant: str
    verdict_type: VerdictType
    confidence: str
    description: str
    evidence: dict[str, Any] = field(default_factory=dict)
    spec_reference: str = ""
    cve_pattern: str = ""
    requires_manual_review: bool = False
    detection_source: str = ""  # "L1_syntactic" | "L2_platform_verifier" | "L3_assertion" | "mutation_sweep"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Verdict:
        d = dict(data)
        d["verdict_type"] = VerdictType(d["verdict_type"])
        if isinstance(d.get("timestamp"), str):
            d["timestamp"] = datetime.fromisoformat(d["timestamp"])
        return cls(**d)


@dataclass
class MutationRecord:
    """Record of a single mutation applied during fuzzing."""
    mutation_type: str = ""
    target_field: str = ""
    original_value: Any = None
    mutated_value: Any = None
    description: str = ""
    mutation_step: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    credential: Any = None  # The mutated Credential
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def mutated(self) -> Any:
        """Alias for credential — the mutated Credential."""
        return self.credential

    def to_dict(self) -> dict:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> MutationRecord:
        d = dict(data)
        if isinstance(d.get("timestamp"), str):
            d["timestamp"] = datetime.fromisoformat(d["timestamp"])
        return cls(**d)


@dataclass
class CampaignResult:
    """Aggregate result of a fuzzing campaign."""
    campaign_id: str = ""
    platform: Platform = Platform.VAULT
    protocol: Protocol = Protocol.JWT
    total_tests: int = 0
    verdicts: list[dict[str, Any]] = field(default_factory=list)
    mutations: list[dict[str, Any]] = field(default_factory=list)
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> CampaignResult:
        d = dict(data)
        d["platform"] = Platform(d["platform"])
        d["protocol"] = Protocol(d["protocol"])
        if isinstance(d.get("start_time"), str):
            d["start_time"] = datetime.fromisoformat(d["start_time"])
        if isinstance(d.get("end_time"), str):
            d["end_time"] = datetime.fromisoformat(d["end_time"])
        return cls(**d)
