"""Mutation sweep: systematic credential mutations against a configured environment.

After System B (stateful sequences) sets up an auth role + policy environment,
this module uses System A (mutation engines) to systematically test that
environment with 55+ credential mutations.

Usage:
    sweep = MutationSweep(executor, jwt_engine, oracles)
    results = sweep.run(environment_config, baseline_credential)
"""
import logging
from dataclasses import dataclass, field
from typing import Optional

from src.engines.jwt_engine import JWTEngine
from src.engines.base import MutationEngine
from src.models.types import (
    AuthResult, Credential, Invariant, MutationRecord, Protocol, Verdict, VerdictType
)

logger = logging.getLogger(__name__)


@dataclass
class EnvironmentConfig:
    """Describes a configured auth environment to sweep mutations against."""
    role_name: str
    mount: str = ""  # Extracted from sequence event; empty triggers fallback in _run_login
    role_config: dict = field(default_factory=dict)  # bound_audiences, token_policies, etc.
    policies: dict = field(default_factory=dict)       # policy_name -> policy_document
    protected_resources: dict = field(default_factory=dict)  # path -> expected_status
    identity_groups: list = field(default_factory=list)
    baseline_claims: dict = field(default_factory=dict)  # JWT claims for baseline
    platform: str = "vault"
    protocol: str = "oidc_jwt"


@dataclass
class SweepResult:
    """Results of a mutation sweep against one environment."""
    environment: EnvironmentConfig
    total_mutations: int
    verdicts: list  # list of (mutation_name, Verdict)
    violations: list  # subset of verdicts with VIOLATION/UNEXPECTED
    baseline_success: bool
    baseline_captures: dict  # entity_id, policies, etc from baseline login


class MutationSweep:
    """Run systematic credential mutations against a configured environment."""

    def __init__(self,
                 executor,       # SequenceExecutor instance (for HTTP calls)
                 jwt_engine: JWTEngine = None,
                 oracles: dict = None,  # {invariant_name: SecurityOracle}
                 profile=None,
                 saml_engine: "MutationEngine | None" = None):
        self.executor = executor
        self.jwt_engine = jwt_engine
        self.saml_engine = saml_engine
        self.oracles = oracles or {}
        self.profile = profile

    def _get_engine(self, protocol: str) -> "MutationEngine | None":
        """Select the appropriate mutation engine for a protocol."""
        if protocol == "saml" and self.saml_engine:
            return self.saml_engine
        return self.jwt_engine

    def run(self, env: EnvironmentConfig,
            invariants: list[str] = None,
            min_priority: str = "normal",
            max_mutations: int = 100) -> SweepResult:
        """Run mutation sweep against configured environment.

        Args:
            env: The environment configuration to test against
            invariants: Filter mutations by invariant (e.g. ["I1", "I5"])
            min_priority: Minimum mutation priority ("critical", "high", "normal", "low")
            max_mutations: Cap on number of mutations to run
        """
        # Profile-based platforms use HTTP login; adapter-based (Vault) use adapter.
        # Both paths are supported — no need to skip.

        engine = self._get_engine(env.protocol)
        if not engine:
            logger.warning(f"No mutation engine for protocol {env.protocol} — skipping sweep")
            return SweepResult(
                environment=env, total_mutations=0, verdicts=[],
                violations=[], baseline_success=False, baseline_captures={}
            )

        engine = self._get_engine(env.protocol)

        # For JWT engine, align defaults with this environment's actual claims
        if env.protocol != "saml" and self.jwt_engine:
            saved = (self.jwt_engine.legitimate_issuer,
                     self.jwt_engine.legitimate_audience,
                     self.jwt_engine.legitimate_subject)
            try:
                if env.baseline_claims.get("iss"):
                    self.jwt_engine.legitimate_issuer = env.baseline_claims["iss"]
                if env.baseline_claims.get("aud"):
                    aud = env.baseline_claims["aud"]
                    self.jwt_engine.legitimate_audience = aud if isinstance(aud, str) else aud[0] if aud else "vault"
                if env.baseline_claims.get("sub"):
                    self.jwt_engine.legitimate_subject = env.baseline_claims["sub"]

                return self._run_sweep(env, invariants, min_priority, max_mutations)
            finally:
                self.jwt_engine.legitimate_issuer, self.jwt_engine.legitimate_audience, self.jwt_engine.legitimate_subject = saved
        else:
            # SAML or other protocols: no JWT defaults to align
            return self._run_sweep(env, invariants, min_priority, max_mutations)

    def _run_sweep(self, env: EnvironmentConfig,
                   invariants: list[str] = None,
                   min_priority: str = "normal",
                   max_mutations: int = 100) -> SweepResult:
        """Internal sweep logic after engine defaults are aligned."""
        engine = self._get_engine(env.protocol)

        # Step 1: Generate baseline credential
        # For non-Vault JWT platforms: use the REAL token from the sequence
        # (Casdoor/Keycloak/etc. only accept their own tokens, not engine-signed)
        _has_real_token = (
            env.protocol != "saml"
            and env.baseline_claims.get("_real_access_token")
            and self.executor.adapter is None  # non-Vault
        )
        if _has_real_token:
            real_token = env.baseline_claims.pop("_real_access_token")
            baseline = Credential(
                protocol=Protocol.JWT,
                raw_token=real_token,
                claims=env.baseline_claims,
                metadata={"role": env.role_name, "mount": env.mount},
            )
            baseline_claims = dict(env.baseline_claims)
        else:
            baseline = engine.generate_baseline({
                "role": env.role_name,
                "role_name": env.role_name,
            })
            # For JWT (Vault), override baseline claims with environment-specific claims
            if env.protocol != "saml" and self.jwt_engine:
                if env.baseline_claims:
                    baseline_claims = dict(baseline.claims)
                    baseline_claims.update(env.baseline_claims)
                else:
                    baseline_claims = dict(baseline.claims)

                # Ensure baseline JWT meets role constraints
                role_cfg = env.role_config

                # Audience: if baseline doesn't have aud, use role's bound_audiences
                if "aud" not in baseline_claims or not baseline_claims["aud"]:
                    bound_aud = role_cfg.get("audience_restriction",
                                role_cfg.get("bound_audiences", []))
                    if isinstance(bound_aud, list) and bound_aud:
                        baseline_claims["aud"] = bound_aud[0]

                # Groups: if role expects groups claim, add a default
                groups_claim_name = role_cfg.get("groups_claim")
                if groups_claim_name and groups_claim_name not in baseline_claims:
                    baseline_claims[groups_claim_name] = ["users"]

                # Subject: if role uses different user_claim, ensure it exists
                user_claim = role_cfg.get("identity_claim", role_cfg.get("user_claim", "sub"))
                if user_claim != "sub" and user_claim not in baseline_claims:
                    baseline_claims[user_claim] = baseline_claims.get("sub", "test-user")

                baseline = Credential(
                    protocol=baseline.protocol,
                    raw_token=self.jwt_engine.factory.create_token(baseline_claims),
                    claims=baseline_claims,
                    metadata={**baseline.metadata, "role": env.role_name, "mount": env.mount},
                )
            # For SAML, baseline is used as-is from the engine

        # Step 2: Run baseline login to verify environment works
        baseline_result = self._run_login(env, baseline)
        if not baseline_result.success:
            logger.warning(f"Sweep baseline failed for '{env.role_name}': "
                          f"HTTP {baseline_result.http_status} — "
                          f"{baseline_result.error_message}")
            _bc = baseline.claims if hasattr(baseline, 'claims') and baseline.claims else {}
            logger.info(f"  Claims sent: {sorted(_bc.keys())}")
            logger.info(f"  Role config: {env.role_config}")
            return SweepResult(
                environment=env, total_mutations=0, verdicts=[],
                violations=[], baseline_success=False, baseline_captures={}
            )

        baseline_captures = self._capture_identity(env, baseline_result)
        logger.info(f"Baseline OK: entity_id={baseline_captures.get('entity_id')}, "
                    f"policies={baseline_captures.get('policies')}")

        # Step 3: Generate mutations
        inv_filter = None
        if invariants:
            inv_map = {
                "I1": Invariant.I1_PROOF_INTEGRITY,
                "I2": Invariant.I2_FRESHNESS,
                "I3": Invariant.I3_FLOW_COHERENCE,
                "I4": Invariant.I4_PRINCIPAL_BINDING,
                "I5": Invariant.I5_AUTHORIZATION_BINDING,
            }
            inv_filter = [inv_map[i] for i in invariants if i in inv_map]

        all_mutations = []

        # For non-Vault JWT: generate bearer-token mutations (tamper real token)
        if _has_real_token:
            all_mutations = self._generate_bearer_mutations(real_token, inv_filter)
        else:
            for inv in (inv_filter or [None]):
                mutations = engine.generate_mutations(
                    baseline, invariant=inv, min_priority=min_priority
            )
            all_mutations.extend(mutations)

        if len(all_mutations) > max_mutations:
            logger.info(f"Capping mutations from {len(all_mutations)} to {max_mutations}")
            all_mutations = all_mutations[:max_mutations]

        logger.info(f"Running {len(all_mutations)} mutations against environment "
                    f"'{env.role_name}' (mount={env.mount})")

        # Step 4: Run each mutation
        verdicts = []
        violations = []
        for i, mutation in enumerate(all_mutations):
            try:
                mutation_result = self._run_login(env, mutation.credential)
                mutation_type = mutation.mutation_type

                # HTTP 5xx from a mutation login is a server bug — the server
                # should never crash regardless of input.  Report immediately.
                if not mutation_result.success and mutation_result.http_status >= 500:
                    verdicts.append((mutation_type, Verdict(
                        invariant=mutation.metadata.get("invariant") or "I1",
                        verdict_type=VerdictType.VIOLATION,
                        confidence="HIGH",
                        description=f"Server crash on mutation {mutation_type}: "
                                    f"HTTP {mutation_result.http_status}. "
                                    f"Login endpoints must never return 5xx.",
                        evidence={
                            "source": "mutation_sweep",
                            "mutation_name": mutation_type,
                            "http_status": mutation_result.http_status,
                            "error": mutation_result.error_message or "",
                        },
                        detection_source="mutation_sweep",
                    )))
                    violations.append((mutation_type, verdicts[-1][1]))
                    continue

                # CRITICAL: If login was rejected (4xx), the mutation was properly blocked.
                # Don't report as VIOLATION — report as CORRECTLY_REJECTED.
                if not mutation_result.success:
                    verdicts.append((mutation_type, Verdict(
                        invariant=mutation.metadata.get("invariant") or "I1",
                        verdict_type=VerdictType.REJECTED,
                        confidence="HIGH",
                        description=f"Mutation correctly rejected: {mutation_type} "
                                    f"(HTTP {mutation_result.http_status})",
                        evidence={
                            "source": "mutation_sweep",
                            "mutation_name": mutation_type,
                            "http_status": mutation_result.http_status,
                            "error": mutation_result.error_message or "",
                        },
                        detection_source="mutation_sweep",
                    )))
                    continue  # Skip oracle checks — mutation was blocked

                # Config-change mutations: admin modifies role, then logins as same user.
                # These are admin operations, not attacker operations.
                if mutation.metadata.get("mutation_step") == "config_change" or \
                   any(mutation_type.startswith(p) for p in [
                       "i4_bound_claims_empty_config", "i5_bound_audiences_empty",
                       "i5_bound_audiences_unset", "i4_user_claim_nonexistent"]):
                    config_change = mutation.metadata.get("config_change", {})
                    verdicts.append((mutation_type, Verdict(
                        invariant="I5",
                        verdict_type=VerdictType.BY_DESIGN,
                        confidence="LOW",
                        description=f"Config-change {mutation_type}: admin modified role config. "
                                    f"Login succeeded under new config (expected behavior).",
                        evidence={
                            "source": "mutation_sweep",
                            "mutation_name": mutation_type,
                            "config_change": config_change,
                            "classification": "ADMIN_OPERATION",
                        },
                        detection_source="mutation_sweep",
                    )))
                    continue  # Don't run standard oracles on admin operations

                # Login succeeded — check for permission escalation
                mutation_captures = self._verify_post_login(env, mutation_result)
                escalation = self._check_escalation(baseline_captures, mutation_captures)

                if escalation:
                    v = Verdict(
                        invariant=mutation.metadata.get("invariant") or "I5",
                        verdict_type=VerdictType.VIOLATION,
                        confidence="HIGH",
                        description=f"Permission escalation via {mutation_type}: "
                                    f"baseline policies={baseline_captures.get('policies', [])}, "
                                    f"mutation policies={mutation_captures.get('policies', [])}",
                        evidence={
                            "source": "mutation_sweep",
                            "mutation_name": mutation_type,
                            "baseline_policies": baseline_captures.get("policies", []),
                            "mutation_policies": mutation_captures.get("policies", []),
                            "escalated_permissions": escalation,
                        },
                        detection_source="mutation_sweep",
                    )
                    verdicts.append((mutation_type, v))
                    violations.append((mutation_type, v))
                    logger.warning(
                        f"  [{i+1}/{len(all_mutations)}] {mutation_type}: "
                        f"ESCALATION — {v.description[:100]}"
                    )
                    continue

                # No escalation — run oracles for other checks
                for inv_name, oracle in self.oracles.items():
                    try:
                        auth_context = {
                            "oidc_jwt": "JWT_BEARER",
                            "saml": "SAML_BEARER",
                            "oauth2_code": "OAUTH2_CODE",
                        }.get(env.protocol, "JWT_BEARER")
                        # Enrich role_config from executor captures (read_role_config
                        # events capture fields like bound_claims_type that may not
                        # be in create_auth_role params)
                        _enriched_role_config = dict(env.role_config)
                        _config_fields = {
                            "bound_issuer", "bound_audiences", "bound_claims_type",
                            "bound_claims", "groups_claim", "user_claim",
                            "token_policies", "bound_subject",
                        }
                        if hasattr(self.executor, 'captures'):
                            for k, v in self.executor.captures.items():
                                if v is not None:
                                    for fld in _config_fields:
                                        if (k == fld or k.endswith(f"_{fld}")) and fld not in _enriched_role_config:
                                            _enriched_role_config[fld] = v
                                            break

                        context = {
                            "auth_context": auth_context,
                            "platform_config": {"base_url": self.executor.base_url},
                            "baseline_result": baseline_result,
                            "baseline_captures": baseline_captures,
                            "mutation_captures": mutation_captures,
                            "environment": env,
                            "role_config": _enriched_role_config,
                        }
                        verdict = oracle.check(mutation, mutation_result, context)
                        verdict.detection_source = "mutation_sweep"
                        # Tag mutation_name into evidence for KBF matching
                        if not verdict.evidence:
                            verdict.evidence = {}
                        verdict.evidence["mutation_name"] = mutation_type
                        verdict.evidence["source"] = "mutation_sweep"
                        verdicts.append((mutation_type, verdict))

                        if verdict.verdict_type in (VerdictType.VIOLATION, VerdictType.UNEXPECTED):
                            violations.append((mutation_type, verdict))
                            logger.warning(
                                f"  [{i+1}/{len(all_mutations)}] {mutation_type}: "
                                f"{verdict.verdict_type.value} — {verdict.description[:100]}"
                            )
                    except Exception as e:
                        logger.debug(f"Oracle {inv_name} error on {mutation_type}: {e}")

            except Exception as e:
                logger.error(f"Mutation {mutation.mutation_type} failed: {e}")

        # Deduplicate verdicts with same invariant + description pattern
        verdicts = self._deduplicate_verdicts(verdicts)
        violations = [(m, v) for m, v in verdicts
                      if v.verdict_type in (VerdictType.VIOLATION, VerdictType.UNEXPECTED)]

        logger.info(f"Sweep complete: {len(verdicts)} verdicts, "
                    f"{len(violations)} violations/unexpected")

        return SweepResult(
            environment=env,
            total_mutations=len(all_mutations),
            verdicts=verdicts,
            violations=violations,
            baseline_success=True,
            baseline_captures=baseline_captures,
        )

    def _run_login(self, env: EnvironmentConfig, credential: Credential) -> AuthResult:
        """Execute a login against the configured environment.

        Supports two modes:
        - Adapter mode (Vault): uses BrokerAdapter.authenticate()
        - Profile HTTP mode (all other platforms): POSTs the mutated
          JWT/SAML token to the platform's login endpoint via profile mapping.
        """
        from src.models.types import Platform

        # Adapter mode: Vault and other platforms with a BrokerAdapter
        if self.executor.adapter is not None:
            mount = env.mount or env.protocol.replace("oidc_", "") or "jwt"
            cred = Credential(
                protocol=credential.protocol,
                raw_token=credential.raw_token,
                claims=credential.claims,
                metadata={
                    **credential.metadata,
                    "role": env.role_name,
                    "mount": mount,
                },
            )
            return self.executor.adapter.authenticate(cred)

        # Profile HTTP mode: send mutated token via platform's login endpoint
        return self._run_profile_login(env, credential)

    def _run_profile_login(self, env: EnvironmentConfig, credential: Credential) -> AuthResult:
        """Profile-based HTTP login with a mutated credential.

        For JWT: POST the raw JWT to the platform's login_with_jwt or
                 login_with_password endpoint (as a bearer token or body param).
        For SAML: POST the raw SAMLResponse to the saml_login endpoint.
        """
        import requests as _requests
        from src.models.types import Platform

        base_url = self.executor.base_url
        protocol = env.protocol
        token = credential.raw_token
        _env_defaults = getattr(self.profile, 'environment_defaults', {}) or {}

        # Find the appropriate login endpoint from the profile
        if protocol == "saml":
            endpoint = self.profile.get_endpoint("saml", "saml_login")
            if not endpoint:
                endpoint = self.profile.get_endpoint(protocol, "saml_login")
            if not endpoint:
                return AuthResult(
                    success=False, platform=Platform.VAULT, protocol=Protocol.SAML,
                    error_message="No saml_login endpoint in profile", http_status=0,
                )

            # SP-initiated SAML: start a fresh auth request and rebuild
            # the SAML response using the executor's trusted-key method.
            # This ensures correct InResponseTo, signing key, and XML format.
            # Only triggers when saml_login metadata has initiate_saml_flow=true.
            _ep_meta = getattr(endpoint, 'metadata', {}) or {}
            _relay_state = ""
            if _ep_meta.get("initiate_saml_flow"):
                _req_id, _relay_state = self._sp_initiate_saml(env)
                if _req_id:
                    _rebuilt = self._rebuild_saml_with_trusted_key(
                        credential, _req_id, env)
                    if _rebuilt:
                        token = _rebuilt
                    else:
                        logger.warning("Sweep SAML: rebuild with trusted key failed")

            # Build SAML login body
            body = {}
            # Map the SAMLResponse into the correct body field
            saml_key = None
            for abstract, platform_field in endpoint.body_map.items():
                if "saml" in abstract.lower() and "response" in abstract.lower():
                    saml_key = platform_field
                    break
            if not saml_key:
                saml_key = "SAMLResponse"  # fallback
            # Token should be base64-encoded XML. For form POST, don't URL-encode
            # (requests.post(data=...) handles form-encoding automatically).
            import base64 as _b64
            if token:
                try:
                    _b64.b64decode(token, validate=True)
                    body[saml_key] = token  # already valid base64
                except Exception:
                    # Raw XML — encode to base64
                    body[saml_key] = _b64.b64encode(token.encode()).decode()
            else:
                body[saml_key] = ""

            # Include RelayState from SP-initiated flow
            if _relay_state:
                _relay_key = "RelayState"
                for abstract, pf in endpoint.body_map.items():
                    if "relay" in abstract.lower():
                        _relay_key = pf
                        break
                body[_relay_key] = _relay_state

            # Merge default_params (type=code, method=signup, etc.)
            for k, v in (getattr(endpoint, 'default_params', {}) or {}).items():
                body.setdefault(k, v)

            # Platform-specific: Casdoor needs application/org/provider in body
            if self.profile.name == "casdoor":
                body.setdefault("application", env.role_config.get("application", "app-test"))
                body.setdefault("organization", env.role_config.get("organization", "test-org"))
                body.setdefault("provider", env.role_config.get("provider", "provider-saml-test"))
                body.setdefault("type", "code")
                body.setdefault("method", "signup")
                body.setdefault("state", "casdoor")
                body.setdefault("redirectUri", "http://localhost:8000/callback")

            # Resolve path templates ({realm}, {connector_id}, {source_slug}, etc.)
            _path = endpoint.path
            _path_vars = {
                "realm": env.role_config.get("realm", _env_defaults.get("realm", "valence-test")),
                "provider": env.role_config.get("provider", _env_defaults.get("provider_name", "saml")),
                "connector_id": env.role_config.get("connector_id", _env_defaults.get("saml_connector_id", "test-saml")),
                "source_slug": env.role_config.get("source_slug", _env_defaults.get("saml_source_slug", "saml-test")),
                "saml_request_id": env.role_config.get("saml_request_id", ""),
            }
            for k, v in _path_vars.items():
                _path = _path.replace(f"{{{k}}}", str(v))
            url = f"{base_url}{_path}"

            # Add OAuth query params for Casdoor
            if self.profile.name == "casdoor":
                try:
                    self.executor._ensure_admin_session()
                    app_name = body.get("application", "app-test")
                    ar = self.executor.session.get(
                        f"{base_url}/api/get-application",
                        params={"id": f"admin/{app_name}"}, timeout=10)
                    app_data = ar.json().get("data", {})
                    if isinstance(app_data, dict) and app_data.get("clientId"):
                        from urllib.parse import urlencode
                        query = urlencode({
                            "clientId": app_data["clientId"],
                            "responseType": "code",
                            "redirectUri": body.get("redirectUri", "http://localhost:8000/callback"),
                            "scope": "openid profile",
                            "state": "casdoor",
                        })
                        url = f"{url}?{query}"
                except Exception:
                    pass

            content_type = getattr(endpoint, 'content_type', 'json') or 'json'

        else:
            # JWT/OIDC: Use the mutated JWT as a Bearer token against the
            # verify_granted_identity (userinfo) endpoint. This tests whether
            # the platform correctly validates JWT signatures, expiry, claims, etc.
            # If the platform accepts a mutated JWT, that's a finding.
            endpoint = self.profile.get_endpoint(protocol, "verify_granted_identity")
            if not endpoint:
                # Fallback: try login_with_jwt for Vault-style direct JWT login
                endpoint = self.profile.get_endpoint(protocol, "login_with_jwt")
            if not endpoint:
                return AuthResult(
                    success=False, platform=Platform.VAULT, protocol=Protocol.JWT,
                    error_message="No verify/login endpoint in profile", http_status=0,
                )

            # Build request: send JWT as Bearer token to verify endpoint
            body = {}
            # For query-param auth (e.g., Casdoor ?accessToken=...)
            if getattr(endpoint, 'content_type', '') == 'query':
                for abstract, platform_field in endpoint.body_map.items():
                    if "token" in abstract.lower() or "session" in abstract.lower():
                        body[platform_field] = token
                        break
            # For login_with_jwt: token goes in body field
            elif endpoint.path and "login" in endpoint.path:
                for abstract, platform_field in endpoint.body_map.items():
                    if "token" in abstract.lower() or "jwt" in abstract.lower():
                        body[platform_field] = token
                        break

            # Merge default_params
            for k, v in (getattr(endpoint, 'default_params', {}) or {}).items():
                body.setdefault(k, v)

            # Resolve path templates
            _path = endpoint.path
            for k, v in {
                "realm": env.role_config.get("realm", _env_defaults.get("realm", "valence-test")),
                "mount": env.mount or "jwt",
            }.items():
                _path = _path.replace(f"{{{k}}}", str(v))
            url = f"{base_url}{_path}"
            content_type = getattr(endpoint, 'content_type', 'json') or 'json'

        # Execute HTTP request
        try:
            headers = {"Content-Type": "application/json"}

            # For JWT: always send Bearer auth header (verify endpoint needs it)
            if protocol != "saml" and token:
                headers["Authorization"] = f"Bearer {token}"

            method = getattr(endpoint, 'method', 'POST') if endpoint else 'POST'
            if content_type == "form":
                headers.pop("Content-Type", None)
                resp = _requests.request(method, url, data=body, headers=headers,
                                         allow_redirects=False, timeout=15)
            elif content_type == "query":
                resp = _requests.request(method, url, params=body, headers=headers,
                                         allow_redirects=False, timeout=15)
            else:
                resp = _requests.request(method, url, json=body or None, headers=headers,
                                         allow_redirects=False, timeout=15)

            # Parse response
            try:
                resp_body = resp.json()
            except Exception:
                resp_body = {}

            success = resp.status_code < 400
            # Casdoor: check status field in body
            if isinstance(resp_body, dict) and resp_body.get("status") == "error":
                success = False

            # SP-initiated SAML: callback returns 302 with auth code in redirect.
            # Extract code and exchange it for tokens.
            if protocol == "saml" and resp.status_code in (302, 303):
                _loc = resp.headers.get("Location", "")
                from urllib.parse import urlparse as _urlparse, parse_qs as _parse_qs
                _qs = _parse_qs(_urlparse(_loc).query)
                _code = _qs.get("code", [None])[0]
                if _code:
                    _exc_result = self._exchange_auth_code(_code, env)
                    if _exc_result:
                        success = True
                        resp_body = _exc_result
                    else:
                        success = False

            # Extract downstream token
            downstream_token = ""
            if endpoint and endpoint.response_map:
                token_path = endpoint.response_map.get("session_token", "")
                if token_path and isinstance(resp_body, dict):
                    downstream_token = str(resp_body.get(token_path, ""))

            return AuthResult(
                success=success,
                platform=Platform.VAULT,  # placeholder
                protocol=Protocol.SAML if protocol == "saml" else Protocol.JWT,
                downstream_token=downstream_token,
                downstream_claims=credential.claims,
                error_message=resp_body.get("msg", resp_body.get("error_description", "")) if isinstance(resp_body, dict) else "",
                http_status=resp.status_code,
                raw_response=resp_body if isinstance(resp_body, dict) else {},
            )

        except Exception as e:
            return AuthResult(
                success=False, platform=Platform.VAULT,
                protocol=Protocol.SAML if protocol == "saml" else Protocol.JWT,
                error_message=str(e), http_status=0,
            )

    # ------------------------------------------------------------------
    # SP-initiated SAML helpers (for sweep against Dex-style SPs)
    # ------------------------------------------------------------------

    def _sp_initiate_saml(self, env: EnvironmentConfig) -> tuple:
        """Start an SP-initiated SAML flow and return (authn_request_id, relay_state).

        Sends GET to the SP's auth endpoint, follows the redirect to the IdP
        SSO URL, and extracts the AuthnRequest ID from the SAMLRequest param.
        Only called when saml_login metadata has initiate_saml_flow=true.
        """
        import requests as _req
        import base64, zlib
        from urllib.parse import urlparse, parse_qs
        from lxml import etree

        _env_defaults = getattr(self.profile, 'environment_defaults', {}) or {}
        base_url = self.executor.base_url
        connector_id = env.role_config.get(
            "connector_id",
            _env_defaults.get("saml_connector_id", "test-saml"),
        )

        # Build auth URL — reuse executor logic for known platforms
        if "/dex" in base_url:
            auth_url = f"{base_url}/auth"
        else:
            auth_url = f"{base_url}/auth"

        params = {
            "client_id": _env_defaults.get("client_id", "valence-test-client"),
            "redirect_uri": _env_defaults.get("redirect_uri", "http://localhost:8080/callback"),
            "response_type": "code",
            "scope": "openid email profile groups",
            "state": f"sweep-{id(self)}",
            "connector_id": connector_id,
        }

        try:
            r = self.executor.session.get(auth_url, params=params, allow_redirects=False, timeout=10)
            # Follow redirects hop by hop to find SAMLRequest
            for _ in range(5):
                if r.status_code not in (301, 302, 303, 307):
                    break
                loc = r.headers.get("Location", "")
                if not loc:
                    break
                # Check if this redirect contains SAMLRequest
                parsed = urlparse(loc)
                qs = parse_qs(parsed.query)
                if "SAMLRequest" in qs:
                    saml_req_b64 = qs["SAMLRequest"][0]
                    relay = qs.get("RelayState", [""])[0]
                    try:
                        raw = base64.b64decode(saml_req_b64)
                        xml_bytes = zlib.decompress(raw, -15)
                    except Exception:
                        xml_bytes = base64.b64decode(saml_req_b64)
                    root = etree.fromstring(xml_bytes)
                    req_id = root.get("ID", "")
                    if req_id:
                        logger.debug(f"SP-SAML sweep: captured AuthnRequest ID={req_id}")
                        return req_id, relay or req_id
                    return None, ""
                # Check for POST binding (HTML form with SAMLRequest)
                if not loc.startswith("http"):
                    # Build absolute URL from the host, not base_url (which may include a path prefix)
                    from urllib.parse import urlparse as _up
                    _p = _up(base_url)
                    loc = f"{_p.scheme}://{_p.netloc}{loc}"
                r = self.executor.session.get(loc, allow_redirects=False, timeout=10)

            # POST binding: parse HTML form
            if r.status_code == 200 and b"SAMLRequest" in r.content:
                import re
                m = re.search(rb'name="SAMLRequest"\s+value="([^"]+)"', r.content)
                rm = re.search(rb'name="RelayState"\s+value="([^"]+)"', r.content)
                if m:
                    saml_req_b64 = m.group(1).decode()
                    relay = rm.group(1).decode() if rm else ""
                    xml_bytes = base64.b64decode(saml_req_b64)
                    root = etree.fromstring(xml_bytes)
                    req_id = root.get("ID", "")
                    if req_id:
                        logger.debug(f"SP-SAML sweep (POST): captured AuthnRequest ID={req_id}")
                        return req_id, relay or req_id

        except Exception as e:
            logger.warning(f"SP-SAML sweep initiation failed: {e}")

        return None, ""

    def _exchange_auth_code(self, code: str, env: EnvironmentConfig) -> dict | None:
        """Exchange an authorization code for tokens (SAML→OIDC code flow)."""
        import requests as _req
        _env = getattr(self.profile, 'environment_defaults', {}) or {}
        token_ep = self.profile.get_endpoint(env.protocol, "exchange_code_for_token")
        if not token_ep:
            return None
        _path = token_ep.path
        url = f"{self.executor.base_url}{_path}"
        body = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": _env.get("redirect_uri", "http://localhost:8080/callback"),
            "client_id": _env.get("client_id", "valence-test-client"),
            "client_secret": _env.get("client_secret", "valence-test-secret"),
        }
        try:
            r = _req.post(url, data=body, allow_redirects=False, timeout=10)
            if r.ok:
                return r.json()
        except Exception as e:
            logger.warning(f"Sweep: auth code exchange failed: {e}")
        return None

    def _rebuild_saml_with_trusted_key(
        self, credential: Credential, in_response_to: str,
        env: EnvironmentConfig,
    ) -> str | None:
        """Rebuild a SAML response using the executor's trusted-key signing.

        Takes the mutation's claims (name_id, issuer, etc.) but builds and signs
        the XML using the platform-trusted key, matching the executor's format
        (Assertion-level signing, correct Signature placement for goxmldsig, etc.).
        Returns base64-encoded SAML response, or None on failure.
        """
        try:
            # Load trusted signing key via executor
            key, cert = self.executor._fetch_trusted_idp_key()
            if not key or not cert:
                logger.warning("Sweep: no trusted SAML key available, cannot rebuild")
                return None

            # Extract mutation claims
            claims = credential.claims or {}
            name_id = claims.get("name_id", "sweep-user@test.local")
            issuer = claims.get("issuer", "http://mock-idp:9090")

            # Build params dict that _build_saml_response_with_key expects
            params = {
                "target_identity": name_id,
                "email": claims.get("email", name_id),
                "idp_entity_id": issuer,
                "displayName": claims.get("display_name", name_id),
            }

            # Propagate mutation flags (remove_conditions, wrong audience, etc.)
            for flag in ("remove_conditions", "include_onetimeuse",
                         "fixed_assertion_id", "sp_entity_id"):
                if flag in claims:
                    params[flag] = claims[flag]

            # Create a minimal event-like object for the executor method
            class _FakeEvent:
                event_type = "saml_login"
            _evt = _FakeEvent()

            b64_response = self.executor._build_saml_response_with_key(
                _evt, params, in_response_to, key, cert
            )
            return b64_response

        except Exception as e:
            logger.warning(f"Sweep: failed to rebuild SAML with trusted key: {e}")
            return None

    def _generate_bearer_mutations(self, real_token: str,
                                    inv_filter: list = None) -> list:
        """Generate mutations by tampering with a real platform-issued JWT.

        Unlike engine mutations (which create new JWTs), these modify the
        actual token bytes to test the platform's validation.
        """
        import base64 as _b64
        import json as _json
        mutations = []

        # Parse the real token
        parts = real_token.split(".")
        if len(parts) != 3:
            return mutations  # Not a valid JWT

        header_b64, payload_b64, sig_b64 = parts
        try:
            _pad = lambda s: s + "=" * (4 - len(s) % 4)
            header = _json.loads(_b64.b64decode(_pad(header_b64)))
            payload = _json.loads(_b64.b64decode(_pad(payload_b64)))
        except Exception:
            return mutations

        def _encode_jwt(h, p, s):
            hb = _b64.urlsafe_b64encode(_json.dumps(h).encode()).rstrip(b"=").decode()
            pb = _b64.urlsafe_b64encode(_json.dumps(p).encode()).rstrip(b"=").decode()
            return f"{hb}.{pb}.{s}"

        # I1: alg=none (strip signature)
        mut_header = dict(header)
        mut_header["alg"] = "none"
        mutations.append(MutationRecord(
            mutation_type="i1_bearer_alg_none",
            description="Set alg=none and strip signature from real token",
            metadata={"invariant": "I1"},
            credential=Credential(protocol=Protocol.JWT,
                raw_token=_encode_jwt(mut_header, payload, ""),
                claims=payload),
        ))

        # I1: signature bit-flip (corrupt last 10 chars of signature)
        if len(sig_b64) > 10:
            flipped = sig_b64[:-10] + "AAAAAAAAAA"
            mutations.append(MutationRecord(
                mutation_type="i1_bearer_sig_corrupt",
                description="Corrupt JWT signature bytes",
                metadata={"invariant": "I1"},
                credential=Credential(protocol=Protocol.JWT,
                    raw_token=f"{header_b64}.{payload_b64}.{flipped}",
                    claims=payload),
            ))

        # I1: empty signature
        mutations.append(MutationRecord(
            mutation_type="i1_bearer_sig_empty",
            description="Empty JWT signature",
            metadata={"invariant": "I1"},
            credential=Credential(protocol=Protocol.JWT,
                raw_token=f"{header_b64}.{payload_b64}.",
                claims=payload),
        ))

        # I2: modify exp to past
        mut_payload = dict(payload)
        mut_payload["exp"] = 1000000000  # 2001 — definitely expired
        mutations.append(MutationRecord(
            mutation_type="i2_bearer_expired",
            description="Set exp to far past in real token",
            metadata={"invariant": "I2"},
            credential=Credential(protocol=Protocol.JWT,
                raw_token=_encode_jwt(header, mut_payload, sig_b64),
                claims=mut_payload),
        ))

        # I2: modify exp to far future
        mut_payload2 = dict(payload)
        mut_payload2["exp"] = 9999999999
        mutations.append(MutationRecord(
            mutation_type="i2_bearer_far_future",
            description="Set exp to far future in real token",
            metadata={"invariant": "I2"},
            credential=Credential(protocol=Protocol.JWT,
                raw_token=_encode_jwt(header, mut_payload2, sig_b64),
                claims=mut_payload2),
        ))

        # I4: change sub claim
        if "sub" in payload:
            mut_payload3 = dict(payload)
            mut_payload3["sub"] = "attacker-" + str(payload["sub"])[:20]
            mutations.append(MutationRecord(
                mutation_type="i4_bearer_sub_overwrite",
                description="Change sub claim in real token",
                metadata={"invariant": "I4"},
                credential=Credential(protocol=Protocol.JWT,
                    raw_token=_encode_jwt(header, mut_payload3, sig_b64),
                    claims=mut_payload3),
            ))

        # I4: change email claim
        if "email" in payload:
            mut_payload4 = dict(payload)
            mut_payload4["email"] = "attacker@evil.com"
            mutations.append(MutationRecord(
                mutation_type="i4_bearer_email_overwrite",
                description="Change email claim in real token",
                metadata={"invariant": "I4"},
                credential=Credential(protocol=Protocol.JWT,
                    raw_token=_encode_jwt(header, mut_payload4, sig_b64),
                    claims=mut_payload4),
            ))

        # I5: add admin role
        mut_payload5 = dict(payload)
        mut_payload5["roles"] = ["admin", "superuser"]
        mut_payload5["isAdmin"] = True
        mutations.append(MutationRecord(
            mutation_type="i5_bearer_role_escalation",
            description="Inject admin role into real token claims",
            metadata={"invariant": "I5"},
            credential=Credential(protocol=Protocol.JWT,
                raw_token=_encode_jwt(header, mut_payload5, sig_b64),
                claims=mut_payload5),
        ))

        # Filter by invariant if specified
        if inv_filter:
            inv_names = {str(i.value) if hasattr(i, 'value') else str(i) for i in inv_filter}
            inv_prefixes = set()
            for inv in inv_filter:
                name = inv.name if hasattr(inv, 'name') else str(inv)
                inv_prefixes.add(name.split("_")[0].lower())  # e.g., "i1"
            mutations = [m for m in mutations
                         if any(m.mutation_type.startswith(p) for p in inv_prefixes)]

        return mutations

    def _capture_identity(self, env: EnvironmentConfig, auth_result: AuthResult) -> dict:
        """After successful login, capture identity details for comparison."""
        captures = {}
        if auth_result.downstream_token:
            captures["token"] = auth_result.downstream_token
        if auth_result.downstream_claims:
            captures.update(auth_result.downstream_claims)
        return captures

    def _verify_post_login(self, env: EnvironmentConfig, auth_result: AuthResult) -> dict:
        """After successful login, check what was actually granted."""
        captures = self._capture_identity(env, auth_result)

        # If we have a session token, do a token lookup for authoritative data
        token = auth_result.downstream_token
        if token and self.profile:
            verify_ep = self.profile.get_endpoint(env.protocol, "verify_granted_identity")
            if verify_ep:
                import requests
                headers = {"Content-Type": "application/json"}
                # Session auth: use the mutation's token
                auth_header = self.profile.admin_auth.get("header", "Authorization")
                if auth_header == "Authorization":
                    headers[auth_header] = f"Bearer {token}" if not token.startswith("Bearer ") else token
                else:
                    headers[auth_header] = token

                url = f"{self.executor.base_url}{verify_ep.path}"
                # For query-based auth (e.g., Casdoor ?accessToken=...), use body_map
                params = {}
                if verify_ep.body_map and getattr(verify_ep, 'content_type', '') == 'query':
                    for abstract, platform_field in verify_ep.body_map.items():
                        if "token" in abstract.lower() or "session" in abstract.lower():
                            params[platform_field] = token
                try:
                    resp = requests.request(verify_ep.method, url, headers=headers,
                                            params=params or None, timeout=10)
                    if resp.ok:
                        body = resp.json()
                        for abstract_key, json_path in (verify_ep.response_map or {}).items():
                            val = self._extract_json_path(body, json_path)
                            if val is not None:
                                captures[abstract_key] = val
                except Exception as e:
                    logger.debug(f"Post-login verification failed: {e}")

        return captures

    def _check_escalation(self, baseline: dict, mutation: dict) -> list:
        """Check if mutation got permissions beyond baseline."""
        baseline_policies = set(
            (baseline.get("policies") or []) +
            (baseline.get("identity_policies") or [])
        )
        mutation_policies = set(
            (mutation.get("policies") or []) +
            (mutation.get("identity_policies") or [])
        )

        extra = mutation_policies - baseline_policies
        if extra and extra != {"default"}:
            return sorted(extra)

        return []

    def _deduplicate_verdicts(self, verdicts: list) -> list:
        """Remove duplicate findings with same invariant + description pattern."""
        seen = set()
        unique = []
        for mutation_name, verdict in verdicts:
            sig = f"{verdict.invariant}:{verdict.description[:80]}"
            if sig not in seen:
                seen.add(sig)
                unique.append((mutation_name, verdict))
            else:
                logger.debug(f"Dedup: suppressed duplicate verdict for {mutation_name}")
        return unique

    def _extract_json_path(self, data: dict, path: str):
        """Extract value from nested dict using dot-notation."""
        if not data or not path:
            return None
        current = data
        for part in path.split("."):
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
            if current is None:
                return None
        return current
