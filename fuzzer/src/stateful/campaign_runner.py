"""Orchestrator: generate → dedup → execute → report."""
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.models.types import VerdictType
from src.stateful.sequence_executor import resolve_jwt_claim_templates

logger = logging.getLogger(__name__)

# Canonical SAML IdP issuer — used by PlatformInitializer when creating
# test SAML providers AND by SAMLEngine for mutation sweep baselines.
# All platforms share this single value so sweep doesn't need per-platform config.
VALENCE_SAML_IDP_ISSUER = "http://fake-idp.valence.local"
VALENCE_SAML_IDP_SSO_URL = "http://fake-idp.valence.local/saml/sso"


def _admin_configured_pattern_match(seq) -> bool:
    """Return True if the sequence explicitly configures pattern-based claim matching.

    General principle: when the admin explicitly configures a pattern-matching
    mode (glob wildcards, regex, etc.) in the role definition, logins that
    match those patterns are BY_DESIGN admin intent, not vulnerabilities.
    This covers any ``bound_claims_type`` / ``claim_constraint_type`` value
    that enables non-literal matching (currently: 'glob'), as well as SAML
    ``bound_subjects_type`` and ``bound_attributes_type``.

    Mutation-sweep findings are unaffected — they test attacker-injected
    patterns against admin-configured literal constraints.
    """
    _NON_LITERAL_TYPES = {"glob"}  # extend with "regex" etc. if platforms add them

    for ev in seq.events:
        if ev.event_type in ("create_auth_role", "create_saml_role"):
            # JWT / generic: claim_constraint_type or bound_claims_type
            cct = (
                ev.params.get("claim_constraint_type", "")
                or ev.params.get("bound_claims_type", "")
            )
            if cct in _NON_LITERAL_TYPES:
                return True
            # SAML: bound_subjects_type and bound_attributes_type
            if ev.params.get("bound_subjects_type", "") in _NON_LITERAL_TYPES:
                return True
            if ev.params.get("bound_attributes_type", "") in _NON_LITERAL_TYPES:
                return True
    return False


class StatefulCampaignRunner:
    """Orchestrate stateful fuzzing campaigns against any supported platform."""

    def __init__(self, config):
        """Initialize campaign runner with CampaignConfig."""
        from src.config import CampaignConfig

        self.config = config

        # Load platform profile
        from src.models.platform_profile import PlatformProfile
        self.profile = PlatformProfile.from_json(self.config.profile_path)

        # Runtime overrides: apply --base-url / --admin-token (or env vars)
        # without modifying the profile file on disk.
        _rt_base_url = getattr(self.config, 'runtime_base_url', '') or os.environ.get('VALENCE_BASE_URL', '')
        _rt_admin_token = getattr(self.config, 'runtime_admin_token', '') or os.environ.get('VALENCE_ADMIN_TOKEN', '')
        if _rt_base_url:
            self.profile.base_url = _rt_base_url
        if _rt_admin_token:
            token_val = _rt_admin_token if _rt_admin_token.startswith("Bearer ") else f"Bearer {_rt_admin_token}"
            self.profile.admin_auth["value"] = token_val

        # Auto-detect protocol from profile when not explicitly set
        if (getattr(self.config, 'protocol', 'oidc_jwt') == 'oidc_jwt'
                and self.profile and self.profile.supported_protocols
                and 'oidc_jwt' not in self.profile.supported_protocols):
            self.config.protocol = self.profile.supported_protocols[0]

        # Initialize LLM (not needed in replay mode)
        from src.llm.client import LLMClient
        if not getattr(self.config, "replay_path", ""):
            self.llm = LLMClient(
                model=self.config.llm_model,
                temperature=self.config.llm_temperature,
            )
        else:
            self.llm = None

        # Initialize components
        self._init_jwt_factory()
        self._init_generator()
        self._init_executor()
        self._init_verifier_pipeline()
        logger.info(f"Mutation sweep enabled: {self.config.enable_mutation_sweep}")
        if self.config.enable_mutation_sweep:
            self._init_mutation_sweep()
            logger.info("Mutation sweep initialized")

        # Output directory with timestamp
        self.output_dir = Path(self.config.output_dir) / f"campaign_{self.config.platform}_{self.config.timestamp}"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _init_jwt_factory(self):
        """Create JWT factory with fresh key pair."""
        from src.utils.jwt_factory import JWTFactory
        from src.utils.crypto import generate_rsa_key_pair
        private_key, public_key = generate_rsa_key_pair()
        self.jwt_factory = JWTFactory(default_signing_key=private_key)
        self._public_key = public_key

    def _init_generator(self):
        """Create sequence generator with profile if available."""
        from src.stateful.sequence_generator import SequenceGenerator
        self.generator = SequenceGenerator(
            llm_client=self.llm,
            profile=self.profile,
        )

    def _init_executor(self):
        """Create sequence executor."""
        from src.stateful.sequence_executor import SequenceExecutor

        # Load Sprint 3 oracles
        from src.oracles.i1_proof_integrity import I1ProofIntegrityOracle
        from src.oracles.i2_freshness import I2FreshnessOracle
        from src.oracles.i4_principal_binding import I4PrincipalBindingOracle
        from src.oracles.i5_authorization_binding import I5AuthorizationBindingOracle
        oracles = {
            "I1": I1ProofIntegrityOracle(),
            "I2": I2FreshnessOracle(),
            "I4": I4PrincipalBindingOracle(),
            "I5": I5AuthorizationBindingOracle(),
        }

        adapter = self._create_adapter_from_profile()
        admin_token = self.profile.admin_auth.get("value", "root")

        # Get public key PEM for JWT validation config injection
        public_key_pem = ""
        if hasattr(self, '_public_key'):
            from cryptography.hazmat.primitives import serialization
            public_key_pem = self._public_key.public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()

        self.executor = SequenceExecutor(
            vault_adapter=adapter,
            jwt_factory=self.jwt_factory,
            oracles=oracles,
            admin_token=admin_token,
            profile=self.profile,
            protocol=self.config.protocol,
            public_key_pem=public_key_pem,
        )

    def _init_verifier_pipeline(self):
        """Initialize verification pipeline based on config.verification_paths."""
        from src.verification.verifier_pipeline import VerifierPipeline
        from src.filters.known_behavior_filter import KnownBehaviorFilter

        kbf = KnownBehaviorFilter.from_profile(self.profile)

        paths = getattr(self.config, 'verification_paths', ["oracle"])

        pipeline_config = {
            "paths": paths,
            "known_behavior_filter": kbf,
            "profile": self.profile,
            "llm_model": getattr(self.config, 'llm_model', None),
            "include_invariants_in_judge": getattr(
                self.config, 'include_invariants_in_judge', False),
        }

        self.verifier_pipeline = VerifierPipeline(pipeline_config)

    def _default_issuer(self) -> str:
        """Derive default issuer from profile or use a sensible fallback."""
        if self.profile:
            base = self.profile.base_url.rstrip("/")
            return base
        return "http://localhost"

    def _default_audience(self) -> str:
        """Derive default audience from platform name."""
        if self.profile:
            return self.profile.name  # e.g. "vault", "keycloak", "dex"
        return "vault"

    def _default_subject(self) -> str:
        return "test-user"

    def _init_mutation_sweep(self):
        """Initialize mutation engine for post-sequence sweeps."""
        from src.stateful.mutation_sweep import MutationSweep
        from src.engines.jwt_engine import JWTEngine

        # Configure JWT engine with the same keys as the fuzzer.
        # Defaults are placeholders — run() overrides them per-environment
        # from env.baseline_claims extracted from each sequence's actual events.
        jwt_config = {
            "legitimate_signing_key": self.jwt_factory._private_key,
            "legitimate_issuer": self._default_issuer(),
            "legitimate_audience": self._default_audience(),
            "legitimate_subject": self._default_subject(),
        }
        self.jwt_engine = JWTEngine(jwt_config)

        # Initialize SAML engine if platform supports SAML
        saml_engine = None
        _all_protocols = list((self.profile.supported_protocols or []))
        # Also check if any sibling profile has saml
        if self.profile and not any("saml" in p for p in _all_protocols):
            import glob as _glob
            for _sib in _glob.glob(f"src/profiles/{self.profile.name}_saml_*.json"):
                _all_protocols.append("saml")
                break
        if self.profile and any("saml" in p for p in _all_protocols):
            from src.engines.saml_engine import SAMLEngine
            # Use the canonical issuer — same value PlatformInitializer sets
            # on the SAML provider. All platforms use this single issuer.
            _env = getattr(self.profile, 'environment_defaults', {}) or {}
            _sp_acs = _env.get("saml_sp_acs_url", f"{self.profile.base_url}/api/acs")
            saml_config = {
                "idp_entity_id": VALENCE_SAML_IDP_ISSUER,
                "sp_acs_url": _sp_acs,
            }
            saml_engine = SAMLEngine(saml_config)

        # Reuse existing oracles
        oracles = {}
        if hasattr(self, 'executor') and self.executor.oracles:
            oracles = self.executor.oracles

        self.mutation_sweep = MutationSweep(
            executor=self.executor,
            jwt_engine=self.jwt_engine,
            saml_engine=saml_engine,
            oracles=oracles,
            profile=self.profile,
        )

    def _extract_environment(self, seq, result) -> Optional["EnvironmentConfig"]:
        """Extract environment config from a completed sequence for mutation sweep.

        Collects all role definitions and logins, then returns an environment
        for each unique (role_name, mount) pair with claims from its first login.
        Currently returns only the first environment (the primary test role).
        """
        from src.stateful.mutation_sweep import EnvironmentConfig

        # Collect all roles and their configs
        roles = {}  # (role_name, mount) -> role_config
        role_order = []  # preserve insertion order
        for event in seq.events:
            if event.event_type in ("create_auth_role", "setup_jwt_role"):
                rn = event.params.get("role_name") or event.params.get("name")
                mt = event.params.get("mount", event.params.get("auth_mount", "jwt"))
                if rn:
                    key = (rn, mt)
                    if key not in roles:
                        role_order.append(key)
                    roles[key] = dict(event.params)

        if not roles:
            # Profile-based platforms: build environment from create_application
            # and login events instead of Vault-style auth roles.
            return self._extract_environment_from_profile(seq, result)

        # Collect claims from the first login targeting each role
        role_claims = {}  # (role_name, mount) -> baseline_claims
        for event in seq.events:
            if event.event_type in ("login_with_jwt", "login_jwt"):
                rn = event.params.get("role") or event.params.get("role_name") or event.params.get("name")
                mt = event.params.get("mount", event.params.get("auth_mount", "jwt"))
                key = (rn, mt)
                if key in roles and key not in role_claims:
                    role_claims[key] = resolve_jwt_claim_templates(
                        dict(event.params.get("jwt_claims", {}))
                    )

        # Build environment for the first role (primary test target)
        role_name, mount = role_order[0]
        role_config = roles[(role_name, mount)]
        baseline_claims = role_claims.get((role_name, mount), {})

        # Enrich role_config from captured state (read_role_config captures
        # fields like bound_claims_type that may not be in create_auth_role params)
        _config_fields = {
            "bound_issuer", "bound_audiences", "bound_claims_type",
            "bound_claims", "groups_claim", "user_claim", "token_policies",
            "bound_subject", "claim_constraints", "claim_constraint_type",
        }
        if hasattr(seq, 'captured_state'):
            for key, val in seq.captured_state.items():
                if val is not None:
                    for field in _config_fields:
                        if (key == field or key.endswith(f"_{field}")) and field not in role_config:
                            role_config[field] = val
                            break

        # Infer aud from role config if not in jwt_claims
        if "aud" not in baseline_claims:
            aud = role_config.get("audience_restriction", role_config.get("bound_audiences", []))
            if isinstance(aud, list) and aud:
                baseline_claims["aud"] = aud[0]
            elif isinstance(aud, str) and aud:
                baseline_claims["aud"] = aud

        return EnvironmentConfig(
            role_name=role_name,
            mount=mount,
            role_config=role_config,
            baseline_claims=baseline_claims,
            platform=self.config.platform,
            protocol=self.config.protocol,
        )

    def _extract_environment_from_profile(self, seq, result) -> Optional["EnvironmentConfig"]:
        """Extract environment config for profile-based platforms (non-Vault).

        Builds EnvironmentConfig from create_application / login events
        so mutation sweep knows the app name, org, and baseline claims.
        """
        from src.stateful.mutation_sweep import EnvironmentConfig

        # Find application name from sequence events
        app_name = ""
        org_name = ""
        for event in seq.events:
            if event.event_type == "create_application":
                app_name = event.params.get("name", "")
                org_name = event.params.get("organization", "")
            elif event.event_type == "create_organization":
                if not org_name:
                    org_name = event.params.get("name", "")

        # Fallback to environment defaults
        env_defaults = getattr(self.profile, 'environment_defaults', {}) or {}
        if not app_name:
            app_name = env_defaults.get("application", "app-test")
        if not org_name:
            org_name = env_defaults.get("organization", "test-org")

        # Collect baseline claims + real access token from first successful login
        baseline_claims = {}
        captures = result.captured_state if hasattr(result, 'captured_state') else {}
        # Look for JWT tokens in captures (session_token, or any value that looks like a JWT)
        for key, val in captures.items():
            if val and isinstance(val, str) and "." in val and len(val) > 64:
                # Looks like a JWT (has dots, long enough)
                parts = val.split(".")
                if len(parts) == 3:
                    baseline_claims["_real_access_token"] = val
                    try:
                        import base64, json as _json
                        payload = parts[1]
                        payload += "=" * (4 - len(payload) % 4)
                        decoded = _json.loads(base64.b64decode(payload))
                        baseline_claims.update(decoded)
                    except Exception:
                        pass
                    break

        return EnvironmentConfig(
            role_name=app_name,
            mount="",
            role_config={
                "application": app_name,
                "organization": org_name,
                "provider": env_defaults.get("provider_name", "provider-saml-test"),
            },
            baseline_claims=baseline_claims,
            platform=self.config.platform,
            protocol=self.config.protocol,
        )

    def _create_adapter_from_profile(self):
        """Create the appropriate BrokerAdapter based on platform profile."""
        platform = self.profile.name
        if platform == "vault":
            from src.adapters.vault_adapter import VaultAdapter
            return VaultAdapter({
                "base_url": self.profile.base_url,
                "admin_token": self.profile.admin_auth.get("value", "root"),
                "auth_mount_path": "jwt",
            })
        elif platform == "authentik":
            # No adapter — MutationSweep uses profile-based HTTP login instead
            return None
        else:
            # No adapter — MutationSweep uses profile-based HTTP login instead
            return None

    def _run_deferred_cleanup(self, cleanup_events):
        """Execute deferred cleanup_auth_method events via direct HTTP."""
        import requests as req_lib
        h = self.profile.admin_auth.get("header", "Authorization")
        v = self.profile.admin_auth.get("value", "")
        headers = {h: v}
        base_url = self.profile.base_url

        for event in cleanup_events:
            mount = event.params.get("mount", "jwt")
            try:
                req_lib.delete(f"{base_url}/v1/sys/auth/{mount}", headers=headers)
                logger.info(f"  [Deferred cleanup] Deleted auth mount '{mount}'")
            except Exception as e:
                logger.debug(f"  [Deferred cleanup] Failed to delete mount '{mount}': {e}")

    def _pre_campaign_cleanup(self):
        """Sweep leftover test resources from previous campaigns using profile cleanup_rules.

        For each rule in profile.cleanup_rules: list all resources at the given
        endpoint, delete any whose name matches name_pattern (and does NOT match
        name_exclude_pattern). Runs with admin credentials. Errors are logged
        as warnings and never raise — cleanup is best-effort.

        Cookie-auth platforms (e.g. Casdoor): uses session-cookie authentication
        by logging in as admin first — header-based Basic auth does not work because
        Casdoor's Basic auth expects clientId:clientSecret, not admin credentials.
        """
        if not self.profile or not self.profile.cleanup_rules:
            return

        import re
        import requests as req_lib

        base_url = self.profile.base_url.rstrip("/")
        uses_cookie_auth = getattr(self.profile, 'session_auth_method', 'bearer') == 'cookie'

        # Build an authenticated session for cleanup requests
        cleanup_session = req_lib.Session()

        if uses_cookie_auth:
            # Cookie-auth platforms: login as admin to get session cookie.
            # Header-based auth (Basic {admin_token}) does NOT work for Casdoor
            # because Casdoor's Basic auth expects clientId:clientSecret.
            try:
                login_body = {
                    "type": "login",
                    "application": "app-built-in",
                    "organization": "built-in",
                    "username": "admin",
                    "password": "123",
                }
                login_resp = cleanup_session.post(
                    f"{base_url}/api/login",
                    json=login_body, timeout=15,
                )
                if not login_resp.ok or login_resp.json().get("status") != "ok":
                    _msg = login_resp.json().get("msg", "") if login_resp.ok else f"HTTP {login_resp.status_code}"
                    logger.warning(f"  [Pre-campaign cleanup] Admin login failed: {_msg}")
                    print(f"[Pre-campaign cleanup] SKIPPED: admin login failed ({_msg})")
                    return
            except Exception as e:
                logger.warning(f"  [Pre-campaign cleanup] Admin login error: {e}")
                print(f"[Pre-campaign cleanup] SKIPPED: admin login error")
                return
        else:
            # Header-auth platforms: resolve admin auth header
            auth_header = self.profile.admin_auth.get("header", "Authorization")
            auth_value = self.profile.admin_auth.get("value", "")
            # Resolve {admin_token} for platforms like Keycloak
            if "{admin_token}" in auth_value:
                try:
                    resp = cleanup_session.post(
                        f"{base_url}/realms/master/protocol/openid-connect/token",
                        data={
                            "grant_type": "password",
                            "client_id": "admin-cli",
                            "username": "admin",
                            "password": "admin",
                        },
                        timeout=15,
                    )
                    if resp.ok:
                        auth_value = auth_value.replace("{admin_token}", resp.json()["access_token"])
                except Exception:
                    pass  # Fall through with unresolved template
            cleanup_session.headers.update({auth_header: auth_value})

        cleanup_session.headers.update({"Content-Type": "application/json"})

        print("\n[Pre-campaign cleanup] Sweeping leftover test resources...")
        for rule in self.profile.cleanup_rules:
            try:
                # Paginated listing: some platforms limit results per page.
                # Loop until we get an empty page or hit a safety limit.
                all_items = []
                page = 1
                max_pages = 20  # Safety limit to prevent infinite loops
                while page <= max_pages:
                    list_path = rule.list_path
                    # Update page number in the query string if present
                    if "p=" in list_path:
                        import re as _re
                        list_path = _re.sub(r'p=\d+', f'p={page}', list_path)

                    resp = cleanup_session.get(f"{base_url}{list_path}", timeout=15)

                    # Check for application-level errors (Casdoor returns HTTP 200
                    # with {"status": "error"} when auth fails)
                    if not resp.ok:
                        logger.warning(
                            f"  [{rule.resource_type}] List failed: HTTP {resp.status_code}"
                        )
                        break
                    resp_json = resp.json()
                    if isinstance(resp_json, dict) and resp_json.get("status") == "error":
                        logger.warning(
                            f"  [{rule.resource_type}] List error: {resp_json.get('msg', '')}"
                        )
                        break

                    items = resp_json
                    # Navigate dot-path to the list (e.g. "data")
                    for part in rule.list_response_path.split("."):
                        items = items.get(part, []) if isinstance(items, dict) else []
                    if not isinstance(items, list) or len(items) == 0:
                        break

                    all_items.extend(items)
                    # If we got fewer items than pageSize, we've reached the end
                    if len(items) < 500:
                        break
                    page += 1

                if not all_items:
                    print(f"  {rule.resource_type}: 0 found, nothing to clean")
                    continue

                name_re = re.compile(rule.name_pattern)
                exclude_re = re.compile(rule.name_exclude_pattern) if rule.name_exclude_pattern else None

                deleted = skipped = errors = 0
                for item in all_items:
                    name = str(item.get(rule.name_field, ""))
                    if not name_re.search(name):
                        skipped += 1
                        continue
                    if exclude_re and exclude_re.search(name):
                        skipped += 1
                        continue
                    body = {f: item.get(f, "") for f in rule.delete_body_fields if f in item}
                    del_resp = cleanup_session.request(
                        rule.delete_method, f"{base_url}{rule.delete_path}",
                        json=body, timeout=10,
                    )
                    # Check both HTTP status and application-level status
                    del_ok = del_resp.ok
                    if del_ok:
                        try:
                            del_body = del_resp.json()
                            if isinstance(del_body, dict) and del_body.get("status") == "error":
                                del_ok = False
                        except Exception:
                            pass
                    if del_ok:
                        deleted += 1
                        logger.debug(f"  [{rule.resource_type}] Deleted {name!r}")
                    else:
                        errors += 1
                        logger.debug(
                            f"  [{rule.resource_type}] Failed to delete {name!r}: "
                            f"HTTP {del_resp.status_code}"
                        )

                print(
                    f"  {rule.resource_type}: {deleted} deleted, "
                    f"{skipped} skipped (protected), {errors} errors"
                    f"  (total listed: {len(all_items)})"
                )
            except Exception as e:
                logger.warning(f"  [{rule.resource_type}] Cleanup error: {e}")

    def _load_sequences(self, sequences_path: str) -> list:
        """Load EventSequence objects from a sequences.json replay file."""
        import json as _json
        from src.stateful.models import Event, EventSequence, OracleCheck

        with open(sequences_path) as f:
            records = _json.load(f)

        sequences = []
        for d in records:
            events = [
                Event(
                    event_type=e["event_type"],
                    params=e.get("params", {}),
                    auth_as=e.get("auth_as", "admin"),
                    expected_outcome=e.get("expected_outcome", "any"),
                    captures=e.get("captures", {}),
                    phase=e.get("phase", ""),
                )
                for e in d.get("events", [])
            ]
            oracle_checks = [
                OracleCheck(
                    check_id=c["check_id"],
                    invariant=c["invariant"],
                    assertion=c["assertion"],
                    violation_description=c["violation_description"],
                    cve_analog=c.get("cve_analog", ""),
                )
                for c in d.get("oracle_checks", [])
            ]
            seq = EventSequence(
                sequence_id=d["sequence_id"],
                description=d["description"],
                invariant_hypothesis=d.get("invariant_hypothesis", ""),
                primary_invariant=d.get("primary_invariant", ""),
                cve_analog=d.get("cve_analog", ""),
                events=events,
                oracle_checks=oracle_checks,
                metadata=d.get("sequence_metadata", {}),
            )
            sequences.append(seq)

        return sequences

    def run(self,
            invariants: list[str] = None,
            sequences_per_invariant: int = 6,
            generation_batch_size: int = 3) -> dict:
        """Run a full stateful fuzzing campaign."""
        import hashlib as _hashlib
        from src.reporting.campaign_report import CampaignReport, FindingRecord, SequenceRecord

        invariants = invariants or self.config.invariant_focus
        all_sequences = []
        from src.stateful.sequence_quality import SequenceQualityReport
        overall_quality = SequenceQualityReport()

        platform_name = self.profile.name if self.profile else "vault"
        base_url = self.executor.base_url

        # Guard: skip Vault SAML if the auth method is not available (OSS lacks SAML plugin)
        protocol = getattr(self.config, 'protocol', 'oidc_jwt')
        if platform_name == "vault" and protocol == "saml" and not getattr(self, '_vault_saml_available', True):
            print("[SKIP] Vault SAML auth method is not available in this build (requires Enterprise or plugin).")
            print("       Skipping vault_saml cell. No sequences will be generated or executed.")
            return {"skipped": True, "reason": "vault_saml_not_available"}

        print(f"\n{'='*70}")
        print(f"VALENCE Stateful Campaign — {datetime.now(timezone.utc).isoformat()}")
        print(f"Platform: {platform_name}")
        print(f"Invariants: {invariants}")
        print(f"Target: {base_url}")
        print(f"LLM: {(self.llm.model if self.llm else 'replay')}")
        print(f"{'='*70}\n")

        # Initialise structured campaign report
        _eval_mode_name = getattr(self.config, '_eval_mode_name', None)
        _eval_mode_description = getattr(self.config, '_eval_mode_description', None)
        report = CampaignReport(
            campaign_id=self.config.timestamp,
            timestamp=datetime.now(timezone.utc).isoformat(),
            platform=platform_name,
            base_url=base_url,
            llm_model=(self.llm.model if self.llm else "replay"),
            invariants_tested=list(invariants),
            config={
                "platform": platform_name,
                "base_url": base_url,
                "llm_model": (self.llm.model if self.llm else "replay"),
                "invariants": invariants,
                "verification_paths": getattr(self.config, "verification_paths", ["oracle"]),
                "use_examples": getattr(self.config, "use_examples", True),
                "max_examples": getattr(self.config, "max_examples", -1),
                "replay_path": getattr(self.config, "replay_path", ""),
                "eval_mode": _eval_mode_name or "custom",
                "eval_mode_description": _eval_mode_description or "",
                "generation_mode": getattr(self.config, "generation_mode", "attack"),
                "use_invariants": getattr(self.config, "use_invariants", True),
                "enable_mutation_sweep": getattr(self.config, "enable_mutation_sweep", False),
            },
        )

        # Pre-campaign cleanup: remove leftover test resources from previous runs
        if getattr(self.config, 'pre_campaign_cleanup', True):
            self._pre_campaign_cleanup()

        # Phase 1: Generate sequences (or load from replay file)
        if getattr(self.config, "replay_path", ""):
            print(f"[Replay Mode] Loading sequences from: {self.config.replay_path}")
            all_sequences = self._load_sequences(self.config.replay_path)
            print(f"  Loaded {len(all_sequences)} sequences")
            unique = all_sequences  # Replay skips deduplication
        else:
            print("[Phase 1] Generating event sequences...")
            gen_mode = getattr(self.config, 'generation_mode', 'attack')
            use_examples = getattr(self.config, 'use_examples', True)
            use_invariants = getattr(self.config, 'use_invariants', True)
            max_examples = getattr(self.config, 'max_examples', -1)

            for inv in invariants:
                generated_descs = [s.description for s in all_sequences]
                total_batches = (sequences_per_invariant + generation_batch_size - 1) // generation_batch_size

                for batch in range(total_batches):
                    batch_size = min(generation_batch_size,
                                     sequences_per_invariant - batch * generation_batch_size)
                    seqs = self.generator.generate(
                        invariant_focus=inv,
                        num_sequences=batch_size,
                        previously_generated=generated_descs,
                        mode=gen_mode,
                        use_examples=use_examples,
                        max_examples=max_examples,
                        use_invariants=use_invariants,
                        protocol=self.config.protocol,
                    )
                    all_sequences.extend(seqs)
                    generated_descs.extend([s.description for s in seqs])
                    print(f"  {inv} {gen_mode} batch {batch+1}: generated {len(seqs)} sequences")

                    # Accumulate quality
                    strategy = (self.generator.coverage_strategy if gen_mode == "coverage"
                                else self.generator.attack_strategy)
                    q = strategy.last_quality
                    overall_quality.total_generated += q.total_generated
                    overall_quality.level0_parseable += q.level0_parseable
                    overall_quality.level1_valid_structure += q.level1_valid_structure
                    overall_quality.parse_errors.extend(q.parse_errors)
                    overall_quality.validation_errors.extend(q.validation_errors)

            print(f"\n  Total generated: {len(all_sequences)}")

        # Phase 2: Deduplicate (skip in replay mode — already done)
        if not getattr(self.config, "replay_path", ""):
            print("\n[Phase 2] Deduplicating...")
            from src.stateful.dedup import deduplicate
            unique = deduplicate(all_sequences)
            print(f"  {len(all_sequences)} → {len(unique)} unique sequences")

        # Phase 3: Execute
        print(f"\n[Phase 3] Executing {len(unique)} sequences against {platform_name}...\n")
        from src.stateful.models import SequenceResult
        results: list[SequenceResult] = []
        findings = []

        for i, seq in enumerate(unique):
            print(f"--- [{i+1}/{len(unique)}] {seq.sequence_id}: {seq.description[:80]} ---")

            # If sweep is enabled, defer cleanup events so the auth mount
            # still exists when the sweep runs its baseline login.
            deferred_cleanup = []
            if self.config.enable_mutation_sweep:
                deferred_cleanup = [e for e in seq.events if e.event_type == "cleanup_auth_method"]
                if deferred_cleanup:
                    seq.events = [e for e in seq.events if e.event_type != "cleanup_auth_method"]

            result = self.executor.execute(seq)

            # Check if any login event succeeded in this sequence.
            # If none did, all assertion failures are test-setup noise, not real findings.
            # Exception: sequences with NO login events at all (e.g., SSH signing,
            # admin-only operations) should not be suppressed.
            login_events = [
                er for er in result.event_results
                if er.event.event_type.startswith("login_") or er.event.event_type in ("saml_login", "test_request_object")
            ]
            any_login_succeeded = any(er.success for er in login_events)
            has_login_events = len(login_events) > 0
            if has_login_events and not any_login_succeeded and result.event_results:
                filtered_verdicts = [
                    v for v in result.verdicts
                    if v.verdict_type.value == "REJECTED"
                ]
                suppressed_count = len(result.verdicts) - len(filtered_verdicts)
                if suppressed_count > 0:
                    logger.warning(
                        f"  [SUPPRESSED] All logins failed in {seq.sequence_id} — "
                        f"suppressing {suppressed_count} verdicts"
                    )
                result.verdicts = filtered_verdicts
                if result.status == "COMPLETED":
                    result.status = "LOGIN_FAILED"

            # Pre-pipeline executor verdicts (from oracle_check assertions)
            # are attributed to verdict_path "assertion"
            pre_pipeline_verdicts = list(result.verdicts)

            # Admin-intent recognition: when the sequence itself configures
            # pattern-based matching (glob, etc.), logins matching those patterns
            # are by-design admin configuration — not a vulnerability.
            # (Mutation sweep findings are unaffected — they test attacker-injected patterns.)
            if _admin_configured_pattern_match(seq):
                for _v in pre_pipeline_verdicts:
                    if _v.verdict_type in (VerdictType.VIOLATION, VerdictType.UNEXPECTED):
                        _v.verdict_type = VerdictType.BY_DESIGN
                        _v.confidence = "HIGH"
                        _v.description = "[BY_DESIGN: admin-configured glob] " + _v.description

            # Optionally run VerifierPipeline (applies KnownBehaviorFilter and/or prediction)
            # Track verdicts per path for structured FindingRecord creation
            verdicts_by_path: dict[str, list] = {}
            if hasattr(self, 'verifier_pipeline') and self.verifier_pipeline:
                pipeline_result = self.verifier_pipeline.verify(seq, result)
                # When plain_llm is the sole verdict path (no oracle),
                # clear pre-pipeline verdicts so only LLM judge results remain.
                _pipeline_paths = getattr(self.verifier_pipeline, 'paths', [])
                if "plain_llm" in _pipeline_paths and "oracle" not in _pipeline_paths:
                    result.verdicts = []
                for path_name, path_verdicts in pipeline_result.get("verdicts", {}).items():
                    if path_verdicts:
                        verdicts_by_path[path_name] = path_verdicts
                        if path_name == "oracle":
                            # Replace executor verdicts with filtered ones
                            result.verdicts = path_verdicts
                        else:
                            # Add prediction / oracle_guided / plain_llm verdicts alongside
                            result.verdicts.extend(path_verdicts)
            else:
                # No pipeline — executor assertion verdicts are the only source
                verdicts_by_path["assertion"] = pre_pipeline_verdicts

            # If pipeline ran but produced no oracle path AND no plain_llm path,
            # keep pre-pipeline assertions as fallback.  When plain_llm is the
            # sole verdict source we must NOT mix in assertion-oracle verdicts.
            if verdicts_by_path and "oracle" not in verdicts_by_path and "plain_llm" not in verdicts_by_path:
                verdicts_by_path["assertion"] = pre_pipeline_verdicts

            # Run mutation sweep if enabled and sequence completed successfully
            if result.status == "COMPLETED" and self.config.enable_mutation_sweep:
                env_config = self._extract_environment(seq, result)
                logger.info(f"Sweep: status={result.status}, env_config={'found' if env_config else 'NONE'}")
                if env_config:
                    sweep_result = self.mutation_sweep.run(
                        env_config,
                        invariants=self.config.invariant_focus,
                        min_priority=self.config.sweep_min_priority,
                    )

                    # Apply KBF to sweep verdicts (same as sequence verdicts)
                    sweep_verdicts_to_merge = []
                    if sweep_result.violations:
                        raw_sweep_verdicts = [v for _, v in sweep_result.violations]

                        kbf = None
                        if self.profile:
                            from src.filters.known_behavior_filter import KnownBehaviorFilter
                            kbf = KnownBehaviorFilter.from_profile(self.profile)

                        if kbf:
                            sweep_context = {"primary_invariant": seq.primary_invariant}
                            sweep_context.update(env_config.role_config)
                            # Also provide nested role_config for KBF rules using
                            # dotted paths like "role_config.bound_claims_type"
                            _rc = dict(env_config.role_config)
                            # Normalize: profile-mode uses claim_constraint_type,
                            # Vault native uses bound_claims_type. Ensure both exist
                            # for KBF rule matching.
                            if "claim_constraint_type" in _rc and "bound_claims_type" not in _rc:
                                _rc["bound_claims_type"] = _rc["claim_constraint_type"]
                            if "bound_claims_type" in _rc and "claim_constraint_type" not in _rc:
                                _rc["claim_constraint_type"] = _rc["bound_claims_type"]
                            sweep_context["role_config"] = _rc
                            filtered = kbf.filter_verdicts(raw_sweep_verdicts, sweep_context)
                            sweep_verdicts_to_merge = filtered
                        else:
                            sweep_verdicts_to_merge = raw_sweep_verdicts

                    # Tag and merge sweep verdicts
                    for verdict in sweep_verdicts_to_merge:
                        if not verdict.evidence:
                            verdict.evidence = {}
                        verdict.evidence["source"] = "mutation_sweep"
                        result.verdicts.append(verdict)

                    # Register sweep verdicts under their own path for FindingRecord tagging
                    if sweep_verdicts_to_merge:
                        verdicts_by_path["mutation_sweep"] = sweep_verdicts_to_merge

                    # Store sweep summary
                    result.captured_state["mutation_sweep"] = {
                        "total_mutations": sweep_result.total_mutations,
                        "violations_raw": len(sweep_result.violations),
                        "violations_after_kbf": sum(
                            1 for v in sweep_verdicts_to_merge
                            if v.verdict_type in (VerdictType.VIOLATION, VerdictType.UNEXPECTED)
                        ),
                        "baseline_success": sweep_result.baseline_success,
                    }
                    print(f"  [Sweep] {sweep_result.total_mutations} mutations, "
                          f"{len(sweep_result.violations)} raw violations, "
                          f"{sum(1 for v in sweep_verdicts_to_merge if v.verdict_type in (VerdictType.VIOLATION, VerdictType.UNEXPECTED))} after KBF")

            # Run deferred cleanup: delete auth mounts that were held for sweep
            if deferred_cleanup:
                self._run_deferred_cleanup(deferred_cleanup)
                # Restore events list so report/logging sees original sequence
                seq.events = seq.events + deferred_cleanup

            results.append(result)

            # Track quality levels L2-L4
            if result.status == "COMPLETED":
                overall_quality.record_execution_success()
                if result.captured_state:
                    overall_quality.record_meaningful()
            has_finding = any(
                v.verdict_type.value in ("VIOLATION", "UNEXPECTED")
                for v in result.verdicts
            )
            if has_finding:
                overall_quality.record_finding()

            # Build SequenceRecord for this execution
            generation_strategy = seq.metadata.get("generation_strategy", "unknown")
            seq_record = SequenceRecord(
                sequence_id=seq.sequence_id,
                description=seq.description,
                generation_strategy=generation_strategy,
                primary_invariant=seq.primary_invariant,
                invariant_hypothesis=seq.invariant_hypothesis,
                cve_analog=seq.cve_analog,
                status=result.status,
                events_total=len(result.event_results),
                events_succeeded=sum(1 for er in result.event_results if er.success),
                events_failed=sum(1 for er in result.event_results if not er.success),
                used_examples=seq.metadata.get("used_examples", True),
                num_examples=seq.metadata.get("num_examples", -1),
                events=[
                    {
                        "event_type": e.event_type,
                        "params": e.params,
                        "auth_as": e.auth_as,
                        "expected_outcome": e.expected_outcome,
                        "captures": e.captures,
                        "phase": e.phase,
                    }
                    for e in seq.events
                ],
                oracle_checks=[
                    {
                        "check_id": c.check_id,
                        "invariant": c.invariant,
                        "assertion": c.assertion,
                        "violation_description": c.violation_description,
                        "cve_analog": c.cve_analog,
                    }
                    for c in seq.oracle_checks
                ],
                sequence_metadata=dict(seq.metadata),
                captured_state=result.captured_state,
            )
            report.add_sequence(seq_record)

            # Print and collect findings from all verdict paths
            for path_name, path_verdicts in verdicts_by_path.items():
                for v in path_verdicts:
                    status_marker = {
                        "VIOLATION": "[VIOLATION]",
                        "UNEXPECTED": "[UNEXPECTED]",
                        "BY_DESIGN": "[BY_DESIGN]",
                        "REJECTED": "[REJECTED]",
                        "ERROR": "[ERROR]",
                    }.get(v.verdict_type.value, v.verdict_type.value)

                    detection_source = getattr(v, 'detection_source', '') or path_name
                    print(f"  [{detection_source}] {status_marker} [{v.invariant}] {v.description[:90]}")

                    if v.verdict_type.value in ("VIOLATION", "UNEXPECTED"):
                        # Legacy flat findings list (backward compat)
                        findings.append({
                            "sequence_id": seq.sequence_id,
                            "sequence_description": seq.description,
                            "invariant": v.invariant,
                            "verdict": v.verdict_type.value,
                            "verdict_path": path_name,
                            "description": v.description,
                            "evidence": v.evidence,
                            "cve_pattern": v.cve_pattern,
                        })

                        # Structured FindingRecord
                        finding_id = _hashlib.md5(
                            f"{seq.sequence_id}:{v.invariant}:{path_name}:{v.description}".encode()
                        ).hexdigest()[:16]
                        effective_gen_strategy = (
                            "mutation_sweep" if path_name == "mutation_sweep"
                            else generation_strategy
                        )
                        # Safety net: resolve invariant from mutation_name prefix when empty
                        _inv = v.invariant or (v.evidence or {}).get("invariant", "")
                        if not _inv or _inv == "UNKNOWN":
                            mn = (v.evidence or {}).get("mutation_name", "")
                            if mn.startswith("i1_"): _inv = "I1"
                            elif mn.startswith("i2_"): _inv = "I2"
                            elif mn.startswith("i3_"): _inv = "I3"
                            elif mn.startswith("i4_"): _inv = "I4"
                            elif mn.startswith("i5_"): _inv = "I5"
                        if not _inv:
                            _inv = seq.primary_invariant or "UNKNOWN"
                        finding_record = FindingRecord(
                            finding_id=finding_id,
                            sequence_id=seq.sequence_id,
                            sequence_description=seq.description,
                            generation_strategy=effective_gen_strategy,
                            verdict_path=path_name,
                            invariant=_inv,
                            identified_invariant=v.invariant,
                            verdict_type=v.verdict_type.value,
                            confidence=v.confidence if isinstance(v.confidence, str) else v.confidence.value,
                            description=v.description,
                            cve_analog=v.cve_pattern or seq.cve_analog,
                            evidence=v.evidence or {},
                            detection_source=getattr(v, 'detection_source', ''),
                        )
                        report.add_finding(finding_record)
            print()

        # Phase 4: Report
        print(f"\n{'='*70}")
        print(f"CAMPAIGN COMPLETE")
        print(f"{'='*70}")
        login_failed = sum(1 for r in results if r.status == 'LOGIN_FAILED')
        print(f"Sequences executed: {len(results)}")
        print(f"Completed: {sum(1 for r in results if r.status == 'COMPLETED')}")
        print(f"Setup failed: {sum(1 for r in results if r.status == 'SETUP_FAILED')}")
        print(f"Login failed (suppressed): {login_failed}")
        print(f"Findings: {len(findings)}")

        if findings:
            print(f"\n--- FINDINGS ---")
            for f in findings:
                print(f"  [{f['verdict']}] {f['invariant']}: {f['sequence_description'][:60]}")
                print(f"    {f['description'][:120]}")
                if f.get('cve_pattern'):
                    print(f"    CVE pattern: {f['cve_pattern']}")
                print()

        # Finalize and save structured CampaignReport
        report.finalize()

        # Attach sequence quality after finalize() (finalize replaces summary dict)
        report.summary["sequence_quality"] = overall_quality.to_dict()
        report.summary["sweep_summary"] = report.sweep_findings_summary()
        if hasattr(self.generator, 'coverage_strategy'):
            report.summary["coverage_quality"] = self.generator.coverage_strategy.last_quality.to_dict()
        if hasattr(self.generator, 'attack_strategy'):
            report.summary["attack_quality"] = self.generator.attack_strategy.last_quality.to_dict()
        campaign_dir = report.save(str(self.output_dir.parent))
        print(f"\nStructured report saved: {campaign_dir}/")
        print(f"  Unique findings: {report.summary.get('unique_findings', 0)}")
        print(f"  By strategy: {report.summary.get('by_strategy', {})}")
        print(f"  By verdict path: {report.summary.get('findings_by_verdict_path', {})}")

        # Also save legacy flat report for backward compatibility
        legacy_report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "config": {
                "platform": platform_name,
                "base_url": base_url,
                "llm_model": (self.llm.model if self.llm else "replay"),
                "invariants": invariants,
            },
            "summary": {
                "total_sequences": len(unique),
                "completed": sum(1 for r in results if r.status == "COMPLETED"),
                "setup_failed": sum(1 for r in results if r.status == "SETUP_FAILED"),
                "findings": len(findings),
            },
            "findings": findings,
            "sequences": [
                {
                    "id": r.sequence.sequence_id,
                    "description": r.sequence.description,
                    "invariant_hypothesis": r.sequence.invariant_hypothesis,
                    "primary_invariant": r.sequence.primary_invariant,
                    "cve_analog": r.sequence.cve_analog,
                    "status": r.status,
                    "events": [
                        {
                            "event_type": e.event_type,
                            "params": e.params,
                            "auth_as": e.auth_as,
                            "expected_outcome": e.expected_outcome,
                            "captures": e.captures,
                            "phase": e.phase,
                        }
                        for e in r.sequence.events
                    ],
                    "oracle_checks": [
                        {
                            "check_id": c.check_id,
                            "invariant": c.invariant,
                            "assertion": c.assertion,
                            "violation_description": c.violation_description,
                            "cve_analog": c.cve_analog,
                        }
                        for c in r.sequence.oracle_checks
                    ],
                    "verdicts": [
                        {"invariant": v.invariant, "type": v.verdict_type.value,
                         "description": v.description[:200]}
                        for v in r.verdicts
                    ],
                    "captured_state": r.captured_state,
                    "sweep": r.captured_state.get("mutation_sweep", None),
                }
                for r in results
            ],
            "llm_stats": getattr(self.llm, 'stats', {}),
        }

        report_path = self.output_dir / "campaign_report.json"
        with open(report_path, "w") as f:
            json.dump(legacy_report, f, indent=2, default=str)
        print(f"Legacy report saved: {report_path}")

        # Post-campaign cleanup: remove test realms/resources created during execution.
        self._post_campaign_cleanup()

        return legacy_report

    def _post_campaign_cleanup(self):
        """Remove test resources created during campaign execution.

        For Keycloak: delete all non-master realms.
        For other platforms: use cleanup_rules if defined.
        Generic and safe — only deletes resources matching test patterns.
        """
        import requests as req_lib

        platform = self.profile.name if self.profile else ""
        base_url = self.profile.base_url.rstrip("/") if self.profile else ""

        if platform == "keycloak":
            try:
                # Get fresh admin token
                resp = req_lib.post(
                    f"{base_url}/realms/master/protocol/openid-connect/token",
                    data={"grant_type": "password", "client_id": "admin-cli",
                          "username": "admin", "password": "admin"},
                    timeout=15,
                )
                if not resp.ok:
                    return
                token = resp.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
                realms = req_lib.get(
                    f"{base_url}/admin/realms", headers=headers, timeout=15,
                ).json()
                test_realms = [r["realm"] for r in realms if r["realm"] != "master"]
                for realm_name in test_realms:
                    req_lib.delete(
                        f"{base_url}/admin/realms/{realm_name}",
                        headers=headers, timeout=10,
                    )
                # Also clean IdPs from master realm (some profiles create IdPs there)
                idps = req_lib.get(
                    f"{base_url}/admin/realms/master/identity-provider/instances",
                    headers=headers, timeout=15,
                ).json()
                for idp in idps:
                    req_lib.delete(
                        f"{base_url}/admin/realms/master/identity-provider/instances/{idp['alias']}",
                        headers=headers, timeout=10,
                    )
                cleaned = len(test_realms) + len(idps)
                if cleaned:
                    print(f"\n[Post-campaign cleanup] Deleted {len(test_realms)} test realms, {len(idps)} master IdPs")
            except Exception as e:
                logger.warning(f"Post-campaign cleanup failed: {e}")
        # For other platforms, pre_campaign_cleanup (using cleanup_rules) handles it.


def _setup_platform(runner: StatefulCampaignRunner):
    """One-time platform setup: enable auth method, configure validation keys."""
    import requests as req_lib
    from cryptography.hazmat.primitives import serialization

    profile = runner.profile
    if profile is None:
        logger.error("Cannot setup platform without a profile")
        return

    base_url = profile.base_url
    admin_headers = {
        profile.admin_auth["header"]: profile.admin_auth["value"]
    }

    if profile.name == "vault":
        # Enable JWT auth
        req_lib.post(f"{base_url}/v1/sys/auth/jwt",
                     headers=admin_headers, json={"type": "jwt"})
        # Enable SAML auth (if available — requires enterprise or plugin)
        r = req_lib.post(f"{base_url}/v1/sys/auth/saml",
                         headers=admin_headers, json={"type": "saml"})
        if r.status_code < 300:
            logger.info("[Setup] Vault SAML auth method enabled")
            runner._vault_saml_available = True
        else:
            logger.info(f"[Setup] Vault SAML auth not available: {r.status_code}")
            runner._vault_saml_available = False

        # Configure with test public key
        if hasattr(runner, '_public_key'):
            public_pem = runner._public_key.public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()
            req_lib.post(f"{base_url}/v1/auth/jwt/config",
                         headers=admin_headers,
                         json={"jwt_validation_pubkeys": [public_pem]})

        # Enable KV v2
        r = req_lib.get(f"{base_url}/v1/sys/mounts", headers=admin_headers)
        if "secret/" not in r.json().get("data", {}):
            req_lib.post(f"{base_url}/v1/sys/mounts/secret",
                         headers=admin_headers,
                         json={"type": "kv", "options": {"version": "2"}})

        print(f"[Setup] Vault at {base_url} configured for JWT testing")

    elif profile.name == "keycloak":
        # Get admin token
        token_resp = req_lib.post(f"{base_url}/realms/master/protocol/openid-connect/token", data={
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": "admin",
            "password": "admin",
        })
        if token_resp.status_code != 200:
            print(f"[Setup] Keycloak admin login failed: {token_resp.status_code}")
            return
        admin_token = token_resp.json()["access_token"]
        kc_headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}

        # Create test realm
        realm = "valence-test"
        req_lib.delete(f"{base_url}/admin/realms/{realm}", headers=kc_headers)
        req_lib.post(f"{base_url}/admin/realms", headers=kc_headers, json={
            "realm": realm, "enabled": True, "sslRequired": "none"
        })

        # Create OIDC client
        client_id = "valence-client"
        client_secret = "valence-secret"
        req_lib.post(f"{base_url}/admin/realms/{realm}/clients", headers=kc_headers, json={
            "clientId": client_id,
            "enabled": True,
            "protocol": "openid-connect",
            "publicClient": False,
            "secret": client_secret,
            "redirectUris": ["*"],
            "directAccessGrantsEnabled": True,
            "standardFlowEnabled": True,
        })

        # Disable required user profile attributes (Keycloak 26+ requires firstName/lastName/email by default)
        kc_profile = req_lib.get(f"{base_url}/admin/realms/{realm}/users/profile", headers=kc_headers)
        if kc_profile.ok:
            try:
                profile_cfg = kc_profile.json()
                for attr in profile_cfg.get("attributes", []):
                    if attr.get("required"):
                        attr["required"] = {}
                req_lib.put(f"{base_url}/admin/realms/{realm}/users/profile", headers=kc_headers, json=profile_cfg)
            except Exception:
                pass  # users/profile API not available on older Keycloak versions

        # Create SAML Identity Provider for SAML protocol testing
        saml_idp_resp = req_lib.post(f"{base_url}/admin/realms/{realm}/identity-provider/instances", headers=kc_headers, json={
            "alias": "mock-saml-idp",
            "providerId": "saml",
            "enabled": True,
            "config": {
                "singleSignOnServiceUrl": "http://localhost:9090/saml/sso",
                "singleLogoutServiceUrl": "http://localhost:9090/saml/slo",
                "nameIDPolicyFormat": "urn:oasis:names:tc:SAML:2.0:nameid-format:emailAddress",
                "validateSignature": "false",
                "postBindingResponse": "true",
                "postBindingAuthnRequest": "true"
            }
        })
        if saml_idp_resp.status_code in (200, 201):
            print(f"[Setup] Keycloak SAML IdP 'mock-saml-idp' created in realm={realm}")
        elif saml_idp_resp.status_code == 409:
            print(f"[Setup] Keycloak SAML IdP 'mock-saml-idp' already exists in realm={realm}")
        else:
            print(f"[Setup] Keycloak SAML IdP creation returned {saml_idp_resp.status_code}: {saml_idp_resp.text[:200]}")

        print(f"[Setup] Keycloak at {base_url} configured (realm={realm}, client={client_id})")

    elif profile.name == "zitadel":
        # Create project + OIDC application for OIDC code-flow testing
        env = profile.environment_defaults or {}
        project_name = env.get("project_id", "valence-project")
        client_id_hint = env.get("client_id", "valence-test-client")
        redirect_uri = f"{base_url}/callback"

        # 1. Create project
        r = req_lib.post(f"{base_url}/management/v1/projects",
                         headers=admin_headers, json={"name": project_name})
        project_id = None
        if r.status_code in (200, 201):
            project_id = r.json().get("id")
            print(f"[Setup] ZITADEL project created: {project_name} (id={project_id})")
        elif "already" in r.text.lower():
            # List projects to find existing one
            lr = req_lib.post(f"{base_url}/management/v1/projects/_search",
                              headers=admin_headers, json={"queries": [{"nameQuery": {"name": project_name, "method": "TEXT_QUERY_METHOD_EQUALS"}}]})
            for p in (lr.json().get("result") or []):
                if p.get("name") == project_name:
                    project_id = p.get("id")
                    break
            print(f"[Setup] ZITADEL project already exists: {project_name} (id={project_id})")
        else:
            print(f"[Setup] ZITADEL project creation failed: {r.status_code} {r.text[:200]}")

        if project_id:
            runner.executor._persistent_captures["project_id"] = project_id

            # 2. Create OIDC application (PKCE native/SPA)
            app_body = {
                "name": client_id_hint,
                "redirectUris": [redirect_uri],
                "responseTypes": ["OIDC_RESPONSE_TYPE_CODE"],
                "grantTypes": ["OIDC_GRANT_TYPE_AUTHORIZATION_CODE",
                               "OIDC_GRANT_TYPE_REFRESH_TOKEN",
                               "OIDC_GRANT_TYPE_TOKEN_EXCHANGE"],
                "appType": "OIDC_APP_TYPE_NATIVE",
                "authMethodType": "OIDC_AUTH_METHOD_TYPE_NONE",
                "accessTokenType": "OIDC_TOKEN_TYPE_JWT",
            }
            r = req_lib.post(f"{base_url}/management/v1/projects/{project_id}/apps/oidc",
                             headers=admin_headers, json=app_body)
            if r.status_code in (200, 201):
                resp_data = r.json()
                real_client_id = resp_data.get("clientId", "")
                app_id = resp_data.get("appId", "")
                print(f"[Setup] ZITADEL OIDC app created: {client_id_hint} (client_id={real_client_id}, app_id={app_id})")
                runner.executor._persistent_captures["client_id"] = real_client_id
                runner.executor._persistent_captures["redirect_uri"] = redirect_uri
                runner.executor._persistent_captures["app_id"] = app_id
                # Update environment_defaults with the real client_id
                if profile.environment_defaults is not None:
                    profile.environment_defaults["client_id"] = real_client_id
            elif "already" in r.text.lower():
                # App exists — look up its client_id
                _apps_r = req_lib.post(
                    f"{base_url}/management/v1/projects/{project_id}/apps/_search",
                    headers=admin_headers, json={})
                for _app in (_apps_r.json().get("result") or []):
                    _oc = _app.get("oidcConfig") or {}
                    if _oc.get("clientId"):
                        real_client_id = _oc["clientId"]
                        app_id = _app.get("id", "")
                        runner.executor._persistent_captures["client_id"] = real_client_id
                        runner.executor._persistent_captures["redirect_uri"] = redirect_uri
                        runner.executor._persistent_captures["app_id"] = app_id
                        if profile.environment_defaults is not None:
                            profile.environment_defaults["client_id"] = real_client_id
                        print(f"[Setup] ZITADEL OIDC app exists: {_app.get('name')} (client_id={real_client_id})")
                        break
            else:
                print(f"[Setup] ZITADEL OIDC app creation failed: {r.status_code} {r.text[:200]}")

            # 3. Enable token exchange on the project
            req_lib.put(f"{base_url}/management/v1/projects/{project_id}",
                        headers=admin_headers,
                        json={"name": project_name, "hasProjectCheck": True})

        # 4. Create a custom login policy (enable external login)
        r = req_lib.post(f"{base_url}/management/v1/policies/login",
                         headers=admin_headers,
                         json={"allowExternalIdp": True,
                               "allowRegister": True,
                               "allowUsernamePassword": True})
        if r.status_code in (200, 201):
            print(f"[Setup] ZITADEL login policy created with external IdP enabled")
        elif "already" in r.text.lower():
            print(f"[Setup] ZITADEL login policy already exists")

        # 5. Grant IAM_LOGIN_CLIENT role to admin SA.
        # CreateCallback (POST /v2/oidc/auth_requests/{id}) requires
        # session.link permission, which IAM_OWNER alone does not provide.
        # Adding IAM_LOGIN_CLIENT to the admin SA lets the admin PAT work
        # for both management API calls AND CreateCallback — no separate
        # login-client PAT or Docker volume discovery needed.
        try:
            _sa_resp = req_lib.post(
                f"{base_url}/management/v1/users/_search",
                headers=admin_headers,
                json={"queries": [{"typeQuery": {"type": "TYPE_MACHINE"}}]},
                timeout=10,
            )
            _sa_id = None
            for _u in _sa_resp.json().get("result", []):
                _sa_id = _u["id"]
                break
            if _sa_id:
                _role_resp = req_lib.put(
                    f"{base_url}/admin/v1/members/{_sa_id}",
                    headers=admin_headers,
                    json={"roles": ["IAM_OWNER", "IAM_LOGIN_CLIENT"]},
                    timeout=10,
                )
                if _role_resp.ok:
                    print(f"[Setup] ZITADEL: granted IAM_LOGIN_CLIENT to admin SA ({_sa_id})")
                else:
                    print(f"[Setup] ZITADEL: IAM_LOGIN_CLIENT grant failed: {_role_resp.text[:100]}")
        except Exception as e:
            print(f"[Setup] ZITADEL: IAM_LOGIN_CLIENT grant error: {e}")

        # 6. Register mock-idp as JWT IdP for JWT validation testing
        mock_idp_url = "http://mock-idp:9090"
        jwt_idp_body = {
            "name": "valence-jwt-idp",
            "issuer": mock_idp_url,
            "jwtEndpoint": f"{mock_idp_url}/authorize",
            "keysEndpoint": f"{mock_idp_url}/keys",
            "headerName": "x-jwt-assertion",
            "providerOptions": {
                "isAutoCreation": True,
                "isLinkingAllowed": True,
                "isCreationAllowed": True,
                "autoLinking": 1,
            },
        }
        r = req_lib.post(f"{base_url}/management/v1/idps/generic_jwt",
                         headers=admin_headers, json=jwt_idp_body)
        jwt_idp_id = ""
        if r.status_code in (200, 201):
            jwt_idp_id = r.json().get("id", "")
            print(f"[Setup] ZITADEL JWT IdP created: valence-jwt-idp (id={jwt_idp_id})")
        elif "already" in r.text.lower():
            _idps_r = req_lib.post(f"{base_url}/management/v1/idps/_search",
                                   headers=admin_headers, json={})
            for _idp in (_idps_r.json().get("result") or []):
                if _idp.get("name") == "valence-jwt-idp":
                    jwt_idp_id = _idp.get("id", "")
                    break
            print(f"[Setup] ZITADEL JWT IdP exists (id={jwt_idp_id})")
        if jwt_idp_id:
            runner.executor._persistent_captures["jwt_idp_id"] = jwt_idp_id
            runner.executor._persistent_captures["mock_idp_url"] = "http://localhost:9090"
            runner.executor._persistent_captures["jwt_idp_header"] = "x-jwt-assertion"
            # Add to login policy
            req_lib.post(f"{base_url}/management/v1/policies/login/idps",
                         headers=admin_headers,
                         json={"idpId": jwt_idp_id, "ownerType": "IDP_OWNER_TYPE_ORG"})
            # Connect mock-idp container to zitadel network
            try:
                import subprocess as _sp
                _sp.run(["docker", "network", "connect", "--alias", "mock-idp",
                         "zitadel", "valence-mock-idp"],
                        capture_output=True, timeout=5)
            except Exception:
                pass

            # Inject JWT IdP operations into the profile so the LLM can
            # generate sequences that exercise the JWT IdP validateToken()
            from src.models.platform_profile import APIEndpoint
            _proto = profile.supported_protocols[0] if profile.supported_protocols else "oidc_jwt"
            _ops = profile.api_mapping.setdefault(_proto, {})

            _ops["start_idp_intent"] = APIEndpoint(
                method="POST", path="/v2/idp_intents",
                body_map={"idp_id": "idpId",
                           "success_url": "urls.successUrl",
                           "failure_url": "urls.failureUrl"},
                response_map={"auth_url": "authUrl",
                               "idp_intent_id": "details.resourceOwner",
                               "http_status": "_http_status"},
                auth="admin",
                note="Start an external IdP login intent. Returns auth_url to redirect to.",
            )
            _ops["complete_jwt_idp_login"] = APIEndpoint(
                method="GET", path="/idps/jwt",
                body_map={"auth_request_id": "authRequestID",
                           "user_agent_id": "userAgentID"},
                response_map={"http_status": "_http_status",
                               "idp_intent_id": "idp_intent_id",
                               "idp_intent_token": "idp_intent_token"},
                auth="none", content_type="query",
                metadata={"follow_redirects": False,
                           "inject_jwt_header": True,
                           "jwt_header_name": "x-jwt-assertion"},
                note="Complete JWT IdP login by hitting ZITADEL's /idps/jwt with a JWT in the configured header. "
                     "The JWT is passed via the x-jwt-assertion header. "
                     "On success, redirects to success_url with id= and token= params. "
                     "On failure, redirects to failure_url with error= param. "
                     "This triggers ZITADEL's validateToken() which checks issuer and signature "
                     "but does NOT check aud, accepts missing exp, accepts missing iat.",
            )
            _ops["mint_custom_jwt"] = APIEndpoint(
                method="POST", path="/admin/mint-jwt",
                body_map={"sub": "sub", "iss": "iss",
                           "email": "email", "name": "name"},
                response_map={"minted_token": "token",
                               "kid": "kid",
                               "http_status": "_http_status"},
                auth="none",
                note="Mint a custom JWT signed by the mock-idp's trusted key. "
                     "Only sub and iss are required. ALL other fields are OPTIONAL. "
                     "Fields NOT listed in body_map (exp, iat, aud, nonce, groups, nbf) "
                     "can still be passed as extra params and will be included in the JWT. "
                     "CRITICAL: to test missing-claim handling, do NOT include the field at all. "
                     "For example, a JWT with NO exp tests whether the broker skips expiry checks. "
                     "A JWT with NO iat tests whether the broker skips freshness checks.",
                metadata={"base_url_override": "http://localhost:9090",
                          "pass_all_params": True},
            )
            _ops["retrieve_idp_intent"] = APIEndpoint(
                method="POST", path="/v2/idp_intents/{idp_intent_id}",
                body_map={"idp_intent_id": "idpIntentId",
                           "idp_intent_token": "idpIntentToken"},
                response_map={"user_id": "userId",
                               "idp_user_id": "idpInformation.rawInformation",
                               "http_status": "_http_status"},
                auth="admin",
                note="Retrieve the result of a completed IdP Intent. Returns the linked user info.",
            )

            # Also add environment_defaults for the LLM
            _env = profile.environment_defaults or {}
            _env["jwt_idp_id"] = jwt_idp_id
            _env["mock_idp_issuer"] = "http://mock-idp:9090"
            _env["jwt_idp_header"] = "x-jwt-assertion"
            _env["jwt_idp_flow_doc"] = (
                "To test JWT IdP validation: "
                "1) mint_custom_jwt → captures minted_token. "
                "2) start_idp_intent with idp_id={{jwt_idp_id}} → captures auth_url, plus auto-parsed auth_url_authRequestID and auth_url_userAgentID. "
                "3) complete_jwt_idp_login with auth_request_id={{auth_url_authRequestID}}, user_agent_id={{auth_url_userAgentID}}, jwt_token={{minted_token}} "
                "   → returns http_status 200 (accepted) or 400 (rejected). "
                "IMPORTANT: the CONTROL JWT MUST include sub, iss, exp, iat, email. "
                "The ATTACK JWT should differ in exactly one dimension: "
                "  I2 missing-exp: omit exp entirely (do NOT include exp key). If accepted, broker skips expiry. "
                "  I2 missing-iat: omit iat entirely (do NOT include iat key). If accepted, broker skips freshness. "
                "  I1 wrong-aud: include exp+iat but set aud to a wrong value. If accepted, broker ignores audience. "
                "CRITICAL: mint_custom_jwt always signs with the TRUSTED IdP key. "
                "You CANNOT test signature-trust (re-sign with attacker key) using mint_custom_jwt alone. "
                "For I1, test AUDIENCE validation (set aud to a wrong value) — that is the exploitable gap. "
                "Do NOT assert 'attacker re-signed JWT should be rejected' when using mint_custom_jwt. "
                "The oracle MUST assert: control_status == 200 AND attack_status >= 400. "
                "Use DIFFERENT capture variable names for control vs attack."
            )
            profile.environment_defaults = _env
            print(f"[Setup] ZITADEL JWT IdP operations injected into profile")

        print(f"[Setup] ZITADEL at {base_url} configured (project={project_name})")

    elif profile.name == "logto":
        # Logto setup: create SSO connectors (OIDC + SAML) pointing to mock-idp,
        # create test applications, and inject environment_defaults so the LLM
        # knows about available infrastructure for generating attack sequences.
        import requests as req_lib

        mock_idp_docker = "http://mock-idp:9090"
        mock_idp_host = "http://localhost:9090"
        admin_port = base_url.replace(":3001", ":3002")

        # Resolve admin token via M2M client_credentials from admin tenant
        admin_auth_value = profile.admin_auth.get("value", "")
        if "{admin_token}" in admin_auth_value:
            # Discover M2M credentials from the database via docker exec
            try:
                import subprocess as _sp
                _m2m = _sp.check_output(
                    ["docker", "exec", "logto-postgres", "psql", "-U", "postgres",
                     "-d", "logto", "-t", "-A", "-c",
                     "SELECT id, secret FROM applications WHERE id = 'm-default' LIMIT 1;"],
                    stderr=_sp.DEVNULL, timeout=10
                ).decode().strip()
                if "|" in _m2m:
                    m2m_id, m2m_secret = _m2m.split("|", 1)
                    tok_resp = req_lib.post(f"{admin_port}/oidc/token", data={
                        "grant_type": "client_credentials",
                        "client_id": m2m_id.strip(),
                        "client_secret": m2m_secret.strip(),
                        "resource": "https://default.logto.app/api",
                        "scope": "all",
                    }, timeout=10)
                    if tok_resp.ok:
                        _token = tok_resp.json()["access_token"]
                        admin_auth_value = f"Bearer {_token}"
                        profile.admin_auth["value"] = admin_auth_value
                        print(f"[Setup] Logto admin token obtained via M2M client_credentials")
            except Exception as e:
                print(f"[Setup] Logto M2M token resolution failed: {e}")

        admin_headers = {
            profile.admin_auth["header"]: admin_auth_value,
            "Content-Type": "application/json",
        }

        # Pre-campaign cleanup: remove stale test users and applications
        try:
            users_r = req_lib.get(f"{base_url}/api/users?page=1&page_size=100",
                                  headers=admin_headers, timeout=10)
            if users_r.ok:
                import re
                _deleted = 0
                for u in users_r.json():
                    uname = u.get("username", "")
                    uid = u.get("id", "")
                    _is_builtin = uid in ("admin",) or uname in ("admin",)
                    if uname and not _is_builtin:
                        req_lib.delete(f"{base_url}/api/users/{u['id']}",
                                       headers=admin_headers, timeout=5)
                        _deleted += 1
                if _deleted:
                    print(f"[Setup] Logto cleanup: removed {_deleted} stale test users")

            apps_r = req_lib.get(f"{base_url}/api/applications",
                                 headers=admin_headers, timeout=10)
            if apps_r.ok:
                _del_apps = 0
                for a in apps_r.json():
                    aname = a.get("name", "")
                    atype = a.get("type", "")
                    _is_valence = aname.startswith("valence-")
                    _is_test = not _is_valence and atype not in ("MachineToMachine",)
                    if aname and _is_test:
                        req_lib.delete(f"{base_url}/api/applications/{a['id']}",
                                       headers=admin_headers, timeout=5)
                        _del_apps += 1
                if _del_apps:
                    print(f"[Setup] Logto cleanup: removed {_del_apps} stale test apps")
        except Exception as e:
            print(f"[Setup] Logto cleanup warning: {e}")

        # Ensure Logto and mock-idp can reach each other on the Docker network.
        # With platform-images.yml both are on valence-net already (service name = DNS).
        # For the legacy logto/docker-compose.yml setup (separate logto-net), try to bridge.
        try:
            import subprocess as _sp
            # Legacy: connect mock-idp to logto_logto-net (if it exists)
            _sp.run(["docker", "network", "connect", "--alias", "mock-idp",
                     "logto_logto-net", "valence-mock-idp"],
                    capture_output=True, timeout=5)
            # Legacy: connect logto to valence-net (if not already)
            _sp.run(["docker", "network", "connect",
                     "docker_valence-net", "logto-app-1"],
                    capture_output=True, timeout=5)
        except Exception:
            pass

        # Fetch mock-idp SAML certificate for connector config
        saml_cert_pem = ""
        try:
            cert_resp = req_lib.get(f"{mock_idp_host}/saml/metadata", timeout=5)
            if cert_resp.ok:
                import re
                cert_match = re.search(r'<ds:X509Certificate>(.*?)</ds:X509Certificate>',
                                       cert_resp.text, re.DOTALL)
                if cert_match:
                    saml_cert_pem = (f"-----BEGIN CERTIFICATE-----\n"
                                     f"{cert_match.group(1).strip()}\n"
                                     f"-----END CERTIFICATE-----\n")
        except Exception:
            pass

        # 1. Create OIDC SSO connector pointing to mock-idp
        oidc_connector_id = ""
        r = req_lib.post(f"{base_url}/api/sso-connectors", headers=admin_headers, json={
            "providerName": "OIDC",
            "connectorName": "valence-oidc-idp",
            "domains": ["oidc.valence.local"],
            "config": {
                "clientId": "valence-sso-client",
                "clientSecret": "valence-sso-secret",
                "issuer": mock_idp_docker,
            },
        })
        if r.status_code in (200, 201):
            oidc_connector_id = r.json().get("id", "")
            print(f"[Setup] Logto OIDC SSO connector created (id={oidc_connector_id})")
        else:
            # Check if it already exists
            lr = req_lib.get(f"{base_url}/api/sso-connectors", headers=admin_headers, timeout=10)
            if lr.ok:
                for c in lr.json():
                    if c.get("connectorName") == "valence-oidc-idp":
                        oidc_connector_id = c.get("id", "")
                        print(f"[Setup] Logto OIDC SSO connector exists (id={oidc_connector_id})")
                        break
            if not oidc_connector_id:
                print(f"[Setup] Logto OIDC SSO connector creation failed: {r.status_code} {r.text[:200]}")

        # 2. Create SAML SSO connector pointing to mock-idp
        saml_connector_id = ""
        saml_config = {
            "entityId": "http://mock-idp:9090",
            "signInEndpoint": f"{mock_idp_docker}/saml/sso",
        }
        if saml_cert_pem:
            saml_config["x509Certificate"] = saml_cert_pem
        r = req_lib.post(f"{base_url}/api/sso-connectors", headers=admin_headers, json={
            "providerName": "SAML",
            "connectorName": "valence-saml-idp",
            "domains": ["saml.valence.local"],
            "config": saml_config,
        })
        if r.status_code in (200, 201):
            saml_connector_id = r.json().get("id", "")
            print(f"[Setup] Logto SAML SSO connector created (id={saml_connector_id})")
        else:
            lr = req_lib.get(f"{base_url}/api/sso-connectors", headers=admin_headers, timeout=10)
            if lr.ok:
                for c in lr.json():
                    if c.get("connectorName") == "valence-saml-idp":
                        saml_connector_id = c.get("id", "")
                        # Sync cert in case mock-idp was rebuilt
                        if saml_cert_pem:
                            req_lib.patch(
                                f"{base_url}/api/sso-connectors/{saml_connector_id}",
                                headers=admin_headers,
                                json={"config": saml_config})
                        print(f"[Setup] Logto SAML SSO connector exists (id={saml_connector_id}, cert synced)")
                        break
            if not saml_connector_id:
                print(f"[Setup] Logto SAML SSO connector creation failed: {r.status_code} {r.text[:200]}")

        # 3. Create test applications (Traditional Web for code flow, M2M for client_credentials)
        test_app_id = ""
        test_app_secret = ""
        r = req_lib.post(f"{base_url}/api/applications", headers=admin_headers, json={
            "name": "valence-test-app",
            "type": "Traditional",
            "description": "VALENCE fuzzing test application",
            "oidcClientMetadata": {
                "redirectUris": ["http://localhost:9090/callback"],
                "postLogoutRedirectUris": ["http://localhost:9090/callback"],
            },
        })
        if r.status_code in (200, 201):
            resp = r.json()
            test_app_id = resp.get("id", "")
            test_app_secret = resp.get("secret", "")
            print(f"[Setup] Logto test app created (id={test_app_id})")
        else:
            lr = req_lib.get(f"{base_url}/api/applications", headers=admin_headers, timeout=10)
            if lr.ok:
                for a in lr.json():
                    if a.get("name") == "valence-test-app":
                        test_app_id = a.get("id", "")
                        test_app_secret = a.get("secret", "")
                        print(f"[Setup] Logto test app exists (id={test_app_id})")
                        break

        # 3b. Enable token exchange on the Traditional test app so LLM-generated
        #     token_exchange operations don't fail with "grant type not allowed".
        if test_app_id:
            r = req_lib.patch(f"{base_url}/api/applications/{test_app_id}",
                              headers=admin_headers,
                              json={"customClientMetadata": {"allowTokenExchange": True}})
            if r.ok:
                print(f"[Setup] Logto test app: allowTokenExchange enabled")
            else:
                print(f"[Setup] Logto test app: allowTokenExchange PATCH failed: {r.status_code}")

        # 3c. Create a MachineToMachine app for client_credentials grant (login_with_jwt).
        #     Traditional apps only support authorization_code + refresh_token.
        m2m_app_id = ""
        m2m_app_secret = ""
        r = req_lib.post(f"{base_url}/api/applications", headers=admin_headers, json={
            "name": "valence-m2m-app",
            "type": "MachineToMachine",
            "description": "VALENCE M2M app for client_credentials testing",
        })
        if r.status_code in (200, 201):
            resp = r.json()
            m2m_app_id = resp.get("id", "")
            m2m_app_secret = resp.get("secret", "")
            print(f"[Setup] Logto M2M app created (id={m2m_app_id})")
        else:
            lr = req_lib.get(f"{base_url}/api/applications", headers=admin_headers, timeout=10)
            if lr.ok:
                for a in lr.json():
                    if a.get("name") == "valence-m2m-app":
                        m2m_app_id = a.get("id", "")
                        m2m_app_secret = a.get("secret", "")
                        print(f"[Setup] Logto M2M app exists (id={m2m_app_id})")
                        break

        # 4. Enable SSO and auto-registration in sign-in experience
        r = req_lib.patch(f"{base_url}/api/sign-in-exp", headers=admin_headers,
                          json={"singleSignOnEnabled": True,
                                "signUp": {"identifiers": [], "password": False, "verify": False}})
        if r.ok:
            print(f"[Setup] Logto SSO + auto-registration enabled in sign-in experience")

        # 5. Create an API resource for JWT testing
        test_resource = "https://valence.local/api"
        r = req_lib.post(f"{base_url}/api/resources", headers=admin_headers, json={
            "name": "Valence Test API",
            "indicator": test_resource,
        })
        if r.status_code in (200, 201):
            print(f"[Setup] Logto API resource created: {test_resource}")
        elif r.status_code == 422 and "duplicate" in r.text.lower():
            print(f"[Setup] Logto API resource already exists: {test_resource}")

        # 5. Inject environment_defaults so LLM generates correct sequences
        _env = profile.environment_defaults or {}
        _env["mock_idp_issuer"] = "http://mock-idp:9090"
        _env["mock_idp_host_url"] = mock_idp_host
        if oidc_connector_id:
            _env["oidc_sso_connector_id"] = oidc_connector_id
        if saml_connector_id:
            _env["saml_sso_connector_id"] = saml_connector_id
        if test_app_id:
            _env["test_app_client_id"] = test_app_id
        if test_app_secret:
            _env["test_app_client_secret"] = test_app_secret
        if m2m_app_id:
            _env["m2m_app_client_id"] = m2m_app_id
        if m2m_app_secret:
            _env["m2m_app_client_secret"] = m2m_app_secret
        _env["test_api_resource"] = test_resource
        _env["redirect_uri"] = "http://localhost:9090/callback"
        _env["sso_connector_setup_note"] = (
            "SSO connectors (OIDC and SAML) are pre-configured pointing to a mock IdP. "
            "The mock IdP is controllable: POST /admin/set-claims to change identity attributes "
            "(sub, email, name, groups, email_verified). POST /admin/mint-jwt to mint custom JWTs. "
            "GET /saml/key to obtain the trusted SAML signing key for crafting assertions. "
            "To test SSO-related flows, use create_provider with providerName 'OIDC' or 'SAML' (uppercase). "
            "For SAML connectors, config requires signInEndpoint and either x509Certificate or metadataUrl.\n"
            "\n"
            "CRITICAL — OIDC SSO nonce bypass (I2): The mock IdP ALWAYS omits the nonce claim "
            "from OIDC id_tokens by default. Per OIDC Core 3.1.3.7 §11, the RP MUST reject "
            "id_tokens where nonce is absent when nonce was sent in the authorization request. "
            "Test pattern: saml_login event with connector_id={{oidc_sso_connector_id}} and "
            "mutation_type='i2_oidc_sso_nonce_bypass' in params. "
            "Oracle assertion: user_X_http_status >= 400 — the login MUST be REJECTED. "
            "If user_X_http_status == 200, the RP accepted a nonce-less id_token — I2 VIOLATION. "
            "DO NOT assert user_X_http_status == 200 for this test; that checks the vulnerable behavior.\n"
            "\n"
            "CRITICAL — Unverified email account linking (I4): The mock IdP defaults to "
            "email_verified=false. For I4 tests, use set_idp_claims to explicitly set "
            "email_verified=false along with email=<victim_email> and sub=<attacker_sub>, "
            "then SSO-login. The platform MUST NOT auto-link to an existing account based on "
            "an unverified email. If it does, an attacker at a permissive IdP can claim any "
            "victim's email and get linked to the victim's account — account takeover. "
            "Oracle assertion: attacker_entity_id != victim_entity_id."
        )
        _env["login_strategy"] = (
            "For user authentication, use login_with_password with username and password. "
            "The executor handles the multi-step OIDC Experience API flow transparently. "
            "For machine/service tokens, use login_with_jwt (client_credentials grant) with "
            "client_id={{m2m_app_client_id}} and client_secret={{m2m_app_client_secret}} — "
            "client_credentials requires a MachineToMachine app (the executor auto-resolves this). "
            "Token exchange is pre-enabled on the test app (allowTokenExchange=true). "
            "Both methods produce valid access tokens for verify_granted_identity and introspect_token."
        )

        # 6. Make mock-idp ops available as profile endpoints
        from src.models.platform_profile import APIEndpoint
        _proto = profile.supported_protocols[0] if profile.supported_protocols else "oidc_jwt"
        _ops = profile.api_mapping.setdefault(_proto, {})

        if "mint_custom_jwt" not in _ops:
            _ops["mint_custom_jwt"] = APIEndpoint(
                method="POST", path="/admin/mint-jwt",
                body_map={"sub": "sub", "iss": "iss",
                           "email": "email", "name": "name",
                           "email_verified": "email_verified"},
                response_map={"minted_token": "token",
                               "kid": "kid",
                               "http_status": "_http_status"},
                auth="none",
                note="Mint a custom JWT signed by the mock IdP's trusted key. "
                     "Only sub and iss are required; other fields are optional. "
                     "Fields not listed (exp, iat, aud, nonce, groups, nbf) can be "
                     "passed as extra params. Omitting a field entirely tests "
                     "missing-claim handling by the broker.",
                metadata={"base_url_override": mock_idp_host,
                          "pass_all_params": True},
            )

        if "set_idp_claims" not in _ops:
            _ops["set_idp_claims"] = APIEndpoint(
                method="POST", path="/admin/set-claims",
                body_map={"sub": "sub", "email": "email",
                           "name": "name", "groups": "groups",
                           "email_verified": "email_verified"},
                response_map={"http_status": "_http_status"},
                auth="none", content_type="form",
                note="Change the mock IdP's default identity claims. Subsequent "
                     "SSO logins will use these values. Useful for testing identity "
                     "collision, email verification, and attribute manipulation.",
                metadata={"base_url_override": mock_idp_host,
                          "pass_all_params": True},
            )

        profile.environment_defaults = _env

        # Persist connector IDs in executor captures so LLM-generated sequences can reference them
        if oidc_connector_id:
            runner.executor._persistent_captures["oidc_sso_connector_id"] = oidc_connector_id
        if saml_connector_id:
            runner.executor._persistent_captures["saml_sso_connector_id"] = saml_connector_id
        if test_app_id:
            runner.executor._persistent_captures["test_app_client_id"] = test_app_id
        if test_app_secret:
            runner.executor._persistent_captures["test_app_client_secret"] = test_app_secret
        if m2m_app_id:
            runner.executor._persistent_captures["m2m_app_client_id"] = m2m_app_id
        if m2m_app_secret:
            runner.executor._persistent_captures["m2m_app_client_secret"] = m2m_app_secret
        runner.executor._persistent_captures["test_api_resource"] = test_resource
        runner.executor._persistent_captures["redirect_uri"] = "http://localhost:9090/callback"

        print(f"[Setup] Logto at {base_url} configured "
              f"(oidc_sso={oidc_connector_id}, saml_sso={saml_connector_id}, "
              f"app={test_app_id}, m2m={m2m_app_id})")

    else:
        print(f"WARNING: No setup routine for platform '{profile.name}'. "
              f"Ensure the platform is manually configured before running.")


def _build_config_from_mode(args, mode) -> "CampaignConfig":
    """Build CampaignConfig from parsed args + eval mode."""
    from src.config import CampaignConfig
    config = CampaignConfig(
        platform=args.platform,
        protocol=args.protocol,
        profile_path=args.profile or f"src/profiles/{args.platform}.json",
        llm_model=args.llm_model or os.getenv("VALENCE_LLM_MODEL", "gpt-5.2"),
        llm_temperature=args.temperature,
        invariant_focus=[i.strip() for i in args.invariants.split(",")],
        num_sequences=args.sequences_per_invariant,
        output_dir=os.path.join(args.output_dir, mode.name),
        verification_paths=mode.verdict_paths,
        enable_mutation_sweep=args.mutation_sweep if args.mutation_sweep is not None else mode.enable_mutation_sweep,
        sweep_min_priority=args.sweep_priority,
        use_examples=mode.use_examples,
        max_examples=-1,
        replay_path=args.replay or "",
        generation_mode=mode.generation_mode,
        use_invariants=mode.use_invariants,
    )
    # Pass invariant-in-judge flag if set on mode
    config.include_invariants_in_judge = getattr(mode, 'include_invariants_in_judge', False)
    # Store eval mode metadata for report
    config._eval_mode_name = mode.name
    config._eval_mode_description = mode.description
    # Runtime overrides — attached to config so __init__ can pick them up
    config.runtime_base_url = getattr(args, 'base_url', None) or ''
    config.runtime_admin_token = getattr(args, 'admin_token', None) or ''
    return config


def main():
    """CLI entry point for stateful campaigns."""
    import argparse
    from src.eval_modes import EVAL_MODES, ALL_ABLATION_MODES

    parser = argparse.ArgumentParser(description="VALENCE Stateful Campaign")

    # Platform selection
    parser.add_argument("--platform", default="vault",
                        help="Target platform (must have a profile in src/profiles/)")
    parser.add_argument("--protocol", default="oidc_jwt",
                        help="Protocol to test")
    parser.add_argument("--profile", default=None,
                        help="Path to platform profile JSON (default: src/profiles/{platform}.json)")

    # Test parameters
    parser.add_argument("--invariants", type=str, default="I4,I5",
                        help="Comma-separated invariants to test")
    parser.add_argument("--sequences-per-invariant", type=int, default=6)

    # LLM
    parser.add_argument("--llm-model", type=str, default=None)
    parser.add_argument("--temperature", type=float, default=0.01,
                        help="LLM temperature (default: 0.01 for near-deterministic)")

    # Output
    parser.add_argument("--output-dir", type=str, default="results")

    # Eval mode (primary interface)
    parser.add_argument("--eval-mode", default="full",
                        choices=list(EVAL_MODES.keys()),
                        help="Evaluation mode. 'full' = complete system. "
                             "'all' = run all ablation conditions. "
                             "See src/eval_modes.py for details.")

    # Advanced overrides (kept for backward compat; overridden by --eval-mode)
    parser.add_argument("--verify-path", nargs="+", default=None,
                        choices=["oracle", "prediction", "oracle_guided", "plain_llm"],
                        dest="verify_path",
                        help="(Advanced) Override verdict paths. Prefer --eval-mode.")
    parser.add_argument("--mutation-sweep", action="store_true", default=None,
                        help="(Advanced) Override mutation sweep. Prefer --eval-mode.")
    parser.add_argument("--sweep-priority", default="high",
                        choices=["critical", "high", "normal", "low"],
                        help="Minimum mutation priority for sweep (default: high)")
    parser.add_argument("--use-examples", dest="use_examples", action="store_true",
                        default=None, help="(Advanced) Override examples. Prefer --eval-mode.")
    parser.add_argument("--no-examples", dest="use_examples", action="store_false",
                        help="(Advanced) Disable examples. Prefer --eval-mode.")
    parser.add_argument("--max-examples", type=int, default=-1,
                        help="Max few-shot examples to include (-1 = all)")

    # Replay mode
    parser.add_argument("--replay", type=str, default=None,
                        help="Path to a sequences.json file. Skip generation, "
                             "execute these sequences directly. For reproducibility.")

    # PoC mode: load CVE PoC sequences from a directory
    parser.add_argument("--poc-mode", type=str, default=None, metavar="CVE_POCS_DIR",
                        help="Load all JSON files from directory as sequences. "
                             "Skips LLM generation. For CVE PoC replay.")

    # Platform setup (needed for first run)
    parser.add_argument("--setup-platform", action="store_true",
                        help="Run platform setup (enable auth method, configure keys)")

    # Runtime overrides (apply at load time without modifying the profile file)
    parser.add_argument("--base-url", type=str, default=None,
                        help="Override profile base_url (e.g. http://localhost:8085). "
                             "Also settable via VALENCE_BASE_URL env var.")
    parser.add_argument("--admin-token", type=str, default=None,
                        help="Override profile admin_auth token (e.g. a PAT). "
                             "Also settable via VALENCE_ADMIN_TOKEN env var.")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

    eval_mode_name = args.eval_mode

    if eval_mode_name == "all":
        # Run all ablation modes sequentially.
        # oracle_gen sequences are saved and replayed for verdict_compare so
        # all three verdict paths see the SAME sequences (fair RQ2 comparison).
        oracle_gen_sequences_path = None

        for mode_name in ALL_ABLATION_MODES:
            mode = EVAL_MODES[mode_name]
            print(f"\n{'='*70}")
            print(f"ABLATION: {mode.name} — {mode.description}")
            print(f"{'='*70}\n")
            config = _build_config_from_mode(args, mode)

            # For verdict_compare: replay sequences from oracle_gen
            if mode_name == "verdict_compare" and oracle_gen_sequences_path:
                config.replay_path = oracle_gen_sequences_path
                print(f"  [Replay from oracle_gen: {oracle_gen_sequences_path}]")

            runner = StatefulCampaignRunner(config=config)
            if args.setup_platform:
                _setup_platform(runner)
            runner.run(
                invariants=config.invariant_focus,
                sequences_per_invariant=config.num_sequences,
            )

            # After oracle_gen completes, find its sequences.json for replay
            if mode_name == "oracle_gen":
                import glob as _glob
                pattern = os.path.join(config.output_dir, "campaign_*/sequences.json")
                matches = sorted(_glob.glob(pattern))
                if matches:
                    oracle_gen_sequences_path = matches[-1]
                    print(f"  [Saved sequences for verdict_compare replay: {oracle_gen_sequences_path}]")
    else:
        # PoC mode: load all CVE PoC JSON files as replay sequences
        if args.poc_mode:
            import tempfile
            poc_sequences = []
            for fname in sorted(os.listdir(args.poc_mode)):
                if fname.endswith(".json"):
                    with open(os.path.join(args.poc_mode, fname)) as f:
                        poc_sequences.extend(json.load(f))
            if poc_sequences:
                tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
                json.dump(poc_sequences, tmp, indent=2)
                tmp.close()
                args.replay = tmp.name
                print(f"[PoC Mode] Loaded {len(poc_sequences)} sequences from {args.poc_mode}")
            else:
                print(f"[PoC Mode] No JSON files found in {args.poc_mode}")
                return

        mode = EVAL_MODES[eval_mode_name]
        config = _build_config_from_mode(args, mode)
        runner = StatefulCampaignRunner(config=config)
        if args.setup_platform:
            _setup_platform(runner)
        runner.run(
            invariants=config.invariant_focus,
            sequences_per_invariant=config.num_sequences,
        )


if __name__ == "__main__":
    main()
