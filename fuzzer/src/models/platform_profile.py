"""Platform Profile — maps protocol operations to platform-specific APIs."""
from __future__ import annotations
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class APIEndpoint:
    """A single platform API endpoint."""
    method: str              # GET, POST, PUT, DELETE, LIST
    path: str                # e.g. "/v1/auth/{mount}/login"
    body_map: dict = field(default_factory=dict)     # abstract_param → platform_param
    response_map: dict = field(default_factory=dict)  # abstract_field → json_path
    auth: str = "admin"      # "admin" | "session" | "none"
    headers_map: dict = field(default_factory=dict)
    content_type: str = "json"  # "json" | "form" — how to send body
    default_params: dict = field(default_factory=dict)  # default values merged into params if absent
    metadata: dict = field(default_factory=dict)  # operation metadata (e.g. read_before_write path)
    note: str = ""  # human-readable note for LLM/documentation
    # Optional body transformation applied before sending the request.
    # Examples:
    #   {"type": "role_repr_lookup", "lookup_path": "/admin/realms/{realm}/roles/{role_name}",
    #    "result_format": "array"}
    #   {"type": "wrap_field", "field": "password", "target_key": "credentials",
    #    "wrapper": {"type": "password", "value": "{password}", "temporary": false},
    #    "target_format": "array"}
    # When empty (default), no transform is applied.
    body_transform: dict = field(default_factory=dict)


@dataclass
class CleanupRule:
    """Describes how to sweep leftover test resources before a campaign starts.

    The runner GETs ``list_path``, navigates ``list_response_path`` to the
    array, filters items by ``name_pattern`` (and excludes ``name_exclude_pattern``),
    then sends ``delete_method`` to ``delete_path`` with a body built from
    ``delete_body_fields`` extracted from each matching list item.
    """
    resource_type: str          # human label, e.g. "user", "application"
    list_path: str              # GET path (may include query params)
    list_response_path: str     # dot-path to the array in the response, e.g. "data"
    name_field: str             # field in each item to match against patterns
    name_pattern: str           # regex — delete items whose name matches
    delete_method: str          # e.g. "POST"
    delete_path: str            # delete endpoint
    delete_body_fields: list    # field names from each list item to send as delete body
    name_exclude_pattern: str = ""  # regex — never delete if name matches (safety guard)


@dataclass
class KnownBehaviorRule:
    """A rule describing a known by-design behavior that should not be flagged."""
    id: str
    description: str
    invariants: list[str]           # ["I4", "I5"]
    conditions: dict[str, Any]      # field → expected_value for matching
    action: str = "downgrade_to_informational"  # or "suppress"
    source: str = ""                # Code reference or doc link
    note: str = ""


@dataclass
class PlatformProfile:
    """Complete description of a platform for VALENCE testing."""
    name: str
    base_url: str
    admin_auth: dict                # {"header": "X-Vault-Token", "value": "root"}
    supported_protocols: list[str]  # ["oidc_jwt", "saml", "ldap"]

    # Protocol operation → platform API mapping
    # Structure: { "oidc_jwt": { "login_with_jwt": APIEndpoint, ... } }
    api_mapping: dict[str, dict[str, APIEndpoint]] = field(default_factory=dict)

    # Known by-design behaviors (for false positive suppression)
    known_behaviors: list[KnownBehaviorRule] = field(default_factory=list)

    # Pre-campaign cleanup rules (sweep leftover test resources before each run)
    cleanup_rules: list[CleanupRule] = field(default_factory=list)

    # Platform-specific verification field names
    verification_fields: dict[str, str] = field(default_factory=dict)

    # Platform-specific constraints the LLM should know about
    api_constraints: list[str] = field(default_factory=list)

    # Login types that explicitly carry an identity claim (e.g. JWT sub,
    # password username). Used by _check_empty_identity to decide whether
    # empty sent_identity is suspicious. Falls back to a default set if
    # not specified in the profile JSON.
    identity_carrying_types: list[str] = field(default_factory=list)

    # How session auth is transmitted: "bearer" (default) or "cookie"
    # "cookie" means the platform sets a session cookie on login and
    # subsequent requests must send that cookie (not a Bearer header).
    session_auth_method: str = "bearer"

    # Login strategy: "jwt_factory" (build JWT then POST) or "http" (direct HTTP).
    # Empty string means auto-detect: use "jwt_factory" when jwt_factory is available
    # and no other login strategy is configured.  New platforms should set this
    # explicitly; existing profiles that omit it get backward-compatible inference.
    login_strategy: str = ""

    # Cookie-based admin login config.  Only used when session_auth_method == "cookie".
    # Contains {"path": "/api/login", "body": {...}, "success_check": "status == ok"}.
    # When absent, falls back to hardcoded defaults for backward compatibility.
    cookie_login: dict = field(default_factory=dict)

    # Pre-campaign initialization hooks.  Each entry describes a setup action
    # (ensure_org, ensure_app, ensure_realm, ensure_saml_provider, etc.)
    # that PlatformInitializer executes before sequences run.
    init_hooks: list = field(default_factory=list)

    # Deployment-specific default values (client_id, redirect_uri, connector_id, etc.)
    # Injected into the sequence generator prompt so the LLM uses correct values.
    environment_defaults: dict = field(default_factory=dict)

    # Keywords that indicate a constraint contains security/invariant knowledge.
    # Used to filter constraints in blind mode (use_invariants=False) so that
    # the ablation baseline does not receive invariant-specific hints.
    SECURITY_HINT_KEYWORDS = [
        "I1 ", "I2 ", "I3 ", "I4 ", "I5 ",
        "I1:", "I2:", "I3:", "I4:", "I5:",
        "ATTACKER", "violation", "testing I",
        "flag as", "Only flag", "attack sequence",
        "assertion polarity", "SAML cert substitution",
        "MFA bypass", "PKCE", "jti", "replay",
        "forged", "HARDENING CHECK",
    ]

    def get_filtered_constraints(self, include_security_hints: bool = True) -> list[str]:
        """Return api_constraints, optionally filtering out security-hint constraints.

        Args:
            include_security_hints: When True (default), return all constraints.
                When False (blind mode), strip constraints containing invariant
                references (I1-I5) or attack-strategy vocabulary.
        """
        if include_security_hints:
            return self.api_constraints
        return [c for c in self.api_constraints
                if not any(kw in c for kw in self.SECURITY_HINT_KEYWORDS)]

    @classmethod
    def from_json(cls, path: str | Path) -> "PlatformProfile":
        """Load a PlatformProfile from a JSON file."""
        p = Path(path)
        if not p.is_absolute() and not p.exists():
            # Resolve relative paths against the fuzzer package root (the
            # directory that contains "src/"), derived from this file's own
            # location so it works regardless of the process working directory.
            fuzzer_root = Path(__file__).parent.parent.parent
            candidate = fuzzer_root / p
            if candidate.exists():
                p = candidate
        with open(p) as f:
            data = json.load(f)

        # known_behaviors: handle both flat list (legacy) and per-protocol dict
        raw_kb = data.pop("known_behaviors", [])
        if isinstance(raw_kb, dict):
            known = []
            for proto_kb in raw_kb.values():
                known.extend(KnownBehaviorRule(**r) for r in proto_kb)
        else:
            known = [KnownBehaviorRule(**r) for r in raw_kb]

        # api_constraints: handle both flat list (legacy) and per-protocol dict
        raw_ac = data.pop("api_constraints", [])
        if isinstance(raw_ac, dict):
            api_constraints = []
            for proto_ac in raw_ac.values():
                api_constraints.extend(proto_ac)
        else:
            api_constraints = raw_ac

        cleanup = [CleanupRule(**r) for r in data.pop("cleanup_rules", [])]

        api_mapping = {}
        for proto, ops in data.pop("api_mapping", {}).items():
            api_mapping[proto] = {
                op_name: APIEndpoint(**ep_data) for op_name, ep_data in ops.items()
            }

        return cls(
            **data,
            api_mapping=api_mapping,
            known_behaviors=known,
            cleanup_rules=cleanup,
            api_constraints=api_constraints,
        )

    def get_endpoint(self, protocol: str, operation: str) -> Optional[APIEndpoint]:
        return self.api_mapping.get(protocol, {}).get(operation)

    def get_constraints_text(self, include_security_hints: bool = True) -> str:
        """Return constraints as text for LLM prompt injection.

        Args:
            include_security_hints: When True (default), include all constraints.
                When False (blind mode), filter out constraints that reference
                invariants or attack strategies.
        """
        constraints = self.get_filtered_constraints(include_security_hints)
        if not constraints:
            return ""
        return "\n".join(f"- {c}" for c in constraints)
