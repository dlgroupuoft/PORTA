"""JWT / OIDC mutation engine — covers I1, I2, I4, I5."""

from __future__ import annotations

import copy
import time
import uuid

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives import serialization

from src.engines.base import MutationEngine
from src.models.types import Credential, Invariant, Protocol
from src.utils.crypto import generate_rsa_key_pair
from src.utils.jwt_factory import JWTFactory


class JWTEngine(MutationEngine):
    """Mutation engine for OIDC / JWT tokens."""

    def __init__(self, config: dict | None = None):
        super().__init__(Protocol.JWT)
        config = config or {}

        self.legitimate_issuer: str = config.get("legitimate_issuer", "http://idp.valence.local")
        self.legitimate_audience: str = config.get("legitimate_audience", "test-client")
        self.legitimate_subject: str = config.get("legitimate_subject", "alice")
        self.extra_claims: dict = config.get("extra_claims", {})

        # Keys
        legit_key = config.get("legitimate_signing_key")
        if legit_key is None:
            legit_key, _ = generate_rsa_key_pair()
        self.legitimate_key: RSAPrivateKey = legit_key

        attacker_key = config.get("attacker_signing_key")
        if attacker_key is None:
            attacker_key, _ = generate_rsa_key_pair()
        self.attacker_key: RSAPrivateKey = attacker_key

        self.factory = JWTFactory(self.legitimate_key)

        self._register_all()

    # ------------------------------------------------------------------
    # Baseline
    # ------------------------------------------------------------------

    def generate_baseline(self, config: dict | None = None) -> Credential:
        now = int(time.time())
        claims = {
            "iss": self.legitimate_issuer,
            "sub": self.legitimate_subject,
            "aud": self.legitimate_audience,
            "exp": now + 3600,
            "iat": now,
            "nbf": now,
            "jti": str(uuid.uuid4()),
            "nonce": uuid.uuid4().hex,
        }
        claims.update(self.extra_claims)
        token = self.factory.create_token(claims)
        return Credential(
            protocol=Protocol.JWT,
            raw_token=token,
            claims=claims,
            metadata={"role": (config or {}).get("role",
                                (config or {}).get("role_name", "test-role"))},
        )

    # ------------------------------------------------------------------
    # Mutation dispatch
    # ------------------------------------------------------------------

    def _apply_mutation(self, name: str, baseline: Credential, config: dict) -> Credential:
        entry = self._mutation_registry.get(name)
        if entry is None:
            raise ValueError(f"Unknown mutation: {name}")
        return entry["fn"](baseline)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def _register_all(self) -> None:
        # ============================================================
        # I1 — Proof Integrity (existing, re-prioritized)
        # ============================================================
        self.register_mutation("i1_alg_none", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_alg_none,
                               "Set alg=none, remove signature",
                               priority="low")
        self.register_mutation("i1_alg_confusion_rs256_to_hs256", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_alg_confusion,
                               "Change RS256→HS256, sign with public key as HMAC secret",
                               priority="low")
        self.register_mutation("i1_resign_attacker_key", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_resign_attacker,
                               "Re-sign with attacker private key, same claims",
                               priority="low")
        self.register_mutation("i1_trust_anchor_substitution", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_trust_anchor,
                               "Change iss to attacker IdP, re-sign with attacker key",
                               priority="normal")
        self.register_mutation("i1_kid_injection", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_kid_injection,
                               "Set kid header to attacker key ID, sign with attacker key",
                               priority="normal")
        self.register_mutation("i1_jwks_url_injection", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_jku_injection,
                               "Inject jku header pointing to attacker JWKS URL",
                               priority="low")

        # I1 — URL canonicalization (CVE-2023-6291 pattern)
        self.register_mutation("i1_iss_trailing_slash", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_iss_trailing_slash,
                               "Add trailing slash to issuer URL",
                               priority="high", cve_pattern="CVE-2023-6291")
        self.register_mutation("i1_iss_case_variation", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_iss_case_variation,
                               "Case variation in issuer hostname",
                               priority="high", cve_pattern="CVE-2023-6291")
        self.register_mutation("i1_iss_unicode_homoglyph", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_iss_unicode_homoglyph,
                               "Unicode homoglyph in issuer domain",
                               priority="high", cve_pattern="CVE-2023-6291")
        self.register_mutation("i1_iss_port_variation", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_iss_port_variation,
                               "Add default port to issuer URL",
                               priority="normal", cve_pattern="CVE-2023-6291")
        self.register_mutation("i1_iss_path_traversal", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_iss_path_traversal,
                               "Path traversal sequences in issuer URL",
                               priority="high")

        # ============================================================
        # I2 — Freshness / Anti-Replay (existing, re-prioritized)
        # ============================================================
        self.register_mutation("i2_replay_same_token", Invariant.I2_FRESHNESS,
                               self._i2_replay,
                               "Return exact same token (for replay testing)",
                               priority="low")
        self.register_mutation("i2_reuse_jti_new_exp", Invariant.I2_FRESHNESS,
                               self._i2_reuse_jti,
                               "Same jti but fresh exp",
                               priority="low")
        self.register_mutation("i2_expired_token", Invariant.I2_FRESHNESS,
                               self._i2_expired,
                               "Set exp to past",
                               priority="low")
        self.register_mutation("i2_future_token", Invariant.I2_FRESHNESS,
                               self._i2_future,
                               "Set nbf to future",
                               priority="low")
        self.register_mutation("i2_missing_exp", Invariant.I2_FRESHNESS,
                               self._i2_missing_exp,
                               "Remove exp claim entirely",
                               priority="normal")
        self.register_mutation("i2_missing_iat", Invariant.I2_FRESHNESS,
                               self._i2_missing_iat,
                               "Remove iat claim (freshness / max-age bypass)",
                               priority="normal")
        self.register_mutation("i2_extreme_exp", Invariant.I2_FRESHNESS,
                               self._i2_extreme_exp,
                               "Set exp to 10 years in the future",
                               priority="normal")

        # ============================================================
        # I4 — Principal Binding (existing, re-prioritized)
        # ============================================================
        self.register_mutation("i4_sub_overwrite", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_sub_overwrite,
                               "Change sub to 'admin'",
                               priority="normal")
        self.register_mutation("i4_email_overwrite", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_email_overwrite,
                               "Change email to admin@target.com",
                               priority="normal")
        self.register_mutation("i4_groups_escalation", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_groups_escalation,
                               "Add 'admins' to groups claim",
                               priority="normal")
        self.register_mutation("i4_claim_in_header", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_claim_in_header,
                               "Move identity claims to JWT header",
                               priority="normal")
        self.register_mutation("i4_unicode_collision", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_unicode_collision,
                               "Use unicode confusable for subject",
                               priority="normal")
        self.register_mutation("i4_case_confusion", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_case_confusion,
                               "Flip case of subject",
                               priority="normal")

        # I4 — Type confusion on sub (CVE-2024-5798 pattern)
        self.register_mutation("i4_sub_type_number", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_sub_type_number,
                               "Set sub to numeric value",
                               priority="high", cve_pattern="CVE-2024-5798")
        self.register_mutation("i4_sub_type_object", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_sub_type_object,
                               "Set sub to JSON object",
                               priority="high", cve_pattern="CVE-2024-5798")
        self.register_mutation("i4_sub_type_null", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_sub_type_null,
                               "Set sub to null",
                               priority="high", cve_pattern="CVE-2024-5798")
        self.register_mutation("i4_sub_type_array", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_sub_type_array,
                               "Set sub to array",
                               priority="high", cve_pattern="CVE-2024-5798")
        self.register_mutation("i4_sub_type_boolean", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_sub_type_boolean,
                               "Set sub to boolean true",
                               priority="high", cve_pattern="CVE-2024-5798")
        self.register_mutation("i4_sub_type_empty_string", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_sub_type_empty_string,
                               "Set sub to empty string",
                               priority="high", cve_pattern="CVE-2024-7594")

        # I4 — Type confusion on groups (CVE-2024-5798 pattern)
        self.register_mutation("i4_groups_type_string", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_groups_type_string,
                               "Set groups to string instead of array",
                               priority="critical", cve_pattern="CVE-2024-5798")
        self.register_mutation("i4_groups_type_object", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_groups_type_object,
                               "Set groups to JSON object",
                               priority="critical", cve_pattern="CVE-2024-5798")
        self.register_mutation("i4_groups_type_null", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_groups_type_null,
                               "Set groups to null",
                               priority="high", cve_pattern="CVE-2024-5798")
        self.register_mutation("i4_groups_type_number", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_groups_type_number,
                               "Set groups to number",
                               priority="high", cve_pattern="CVE-2024-5798")
        self.register_mutation("i4_groups_type_boolean", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_groups_type_boolean,
                               "Set groups to boolean true",
                               priority="high", cve_pattern="CVE-2024-5798")
        self.register_mutation("i4_groups_type_array_with_non_string", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_groups_type_array_mixed,
                               "Set groups to array with mixed types",
                               priority="critical", cve_pattern="CVE-2024-5798")

        # I4 — Glob/wildcard injection (CVE-2025-11621 pattern)
        self.register_mutation("i4_bound_claims_glob_star", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_glob_star,
                               "Set bound claim value to wildcard *",
                               priority="critical", cve_pattern="CVE-2025-11621")
        self.register_mutation("i4_bound_claims_glob_question", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_glob_question,
                               "Set bound claim value with ? glob",
                               priority="high", cve_pattern="CVE-2025-11621")
        self.register_mutation("i4_bound_claims_glob_bracket", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_glob_bracket,
                               "Set bound claim value with [a-z]* pattern",
                               priority="high", cve_pattern="CVE-2025-11621")
        self.register_mutation("i4_bound_claims_empty_value", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_bound_claims_empty,
                               "Set bound claim to empty string",
                               priority="critical", cve_pattern="CVE-2024-7594")

        # I1/I3 — HTTP header injection (identity via upstream proxy headers)
        self.register_mutation("i1_http_header_injection_identity", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_header_injection_identity,
                               "Inject identity via X-Remote-User/X-Forwarded-User HTTP headers",
                               priority="high")
        self.register_mutation("i1_http_header_injection_groups", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_header_injection_groups,
                               "Inject group membership via X-Remote-Group/X-Forwarded-Group headers",
                               priority="high")
        self.register_mutation("i1_http_header_injection_email", Invariant.I1_PROOF_INTEGRITY,
                               self._i1_header_injection_email,
                               "Inject email identity via X-Remote-Email/X-Forwarded-Email headers",
                               priority="high")

        # I4 — Config-change mutations (CVE-2024-7594 pattern)
        self.register_mutation("i4_bound_claims_empty_config", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_bound_claims_empty_config,
                               "Reconfigure role with empty bound_claims map",
                               priority="critical", cve_pattern="CVE-2024-7594")
        self.register_mutation("i4_user_claim_nonexistent_field", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_user_claim_nonexistent,
                               "Configure user_claim to nonexistent JWT field",
                               priority="high")

        # I4 — NFC/NFD Unicode normalization (RFC 7613 pattern)
        self.register_mutation("i4_subject_nfd_nfc_normalization", Invariant.I4_PRINCIPAL_BINDING,
                               self._i4_subject_nfd_nfc,
                               "Create subject with NFD decomposed form vs NFC composed form",
                               priority="high")

        # ============================================================
        # I2 — Additional freshness mutations
        # ============================================================
        self.register_mutation("i2_stateless_jwt_no_jti", Invariant.I2_FRESHNESS,
                               self._i2_no_jti,
                               "Remove jti claim and submit token twice — tests uniqueness tracking without jti",
                               priority="normal")

        # ============================================================
        # I5 — Authorization Binding (existing, re-prioritized)
        # ============================================================
        self.register_mutation("i5_aud_wrong", Invariant.I5_AUTHORIZATION_BINDING,
                               self._i5_aud_wrong,
                               "Set audience to different service",
                               priority="normal")
        self.register_mutation("i5_aud_empty", Invariant.I5_AUTHORIZATION_BINDING,
                               self._i5_aud_empty,
                               "Set audience to empty string",
                               priority="normal")
        self.register_mutation("i5_aud_missing", Invariant.I5_AUTHORIZATION_BINDING,
                               self._i5_aud_missing,
                               "Remove audience claim",
                               priority="normal")
        self.register_mutation("i5_aud_array_with_extra", Invariant.I5_AUTHORIZATION_BINDING,
                               self._i5_aud_array_extra,
                               "Add extra audiences to aud array",
                               priority="normal")
        self.register_mutation("i5_scope_inflation", Invariant.I5_AUTHORIZATION_BINDING,
                               self._i5_scope_inflation,
                               "Add extra scopes including admin:full",
                               priority="low")
        self.register_mutation("i5_scope_empty", Invariant.I5_AUTHORIZATION_BINDING,
                               self._i5_scope_empty,
                               "Set scope to empty string",
                               priority="low")

        # I5 — Type confusion on aud (CVE-2024-5798 pattern)
        self.register_mutation("i5_aud_type_number", Invariant.I5_AUTHORIZATION_BINDING,
                               self._i5_aud_type_number,
                               "Set aud to JSON number",
                               priority="critical", cve_pattern="CVE-2024-5798")
        self.register_mutation("i5_aud_type_boolean", Invariant.I5_AUTHORIZATION_BINDING,
                               self._i5_aud_type_boolean,
                               "Set aud to JSON boolean true",
                               priority="critical", cve_pattern="CVE-2024-5798")
        self.register_mutation("i5_aud_type_null", Invariant.I5_AUTHORIZATION_BINDING,
                               self._i5_aud_type_null,
                               "Set aud to JSON null",
                               priority="critical", cve_pattern="CVE-2024-5798")
        self.register_mutation("i5_aud_type_object", Invariant.I5_AUTHORIZATION_BINDING,
                               self._i5_aud_type_object,
                               "Set aud to JSON object",
                               priority="critical", cve_pattern="CVE-2024-5798")
        self.register_mutation("i5_aud_type_empty_array", Invariant.I5_AUTHORIZATION_BINDING,
                               self._i5_aud_type_empty_array,
                               "Set aud to empty JSON array",
                               priority="critical", cve_pattern="CVE-2024-5798")
        self.register_mutation("i5_aud_type_array_with_null", Invariant.I5_AUTHORIZATION_BINDING,
                               self._i5_aud_type_array_with_null,
                               "Set aud to array containing null",
                               priority="critical", cve_pattern="CVE-2024-5798")
        self.register_mutation("i5_aud_type_array_with_number", Invariant.I5_AUTHORIZATION_BINDING,
                               self._i5_aud_type_array_with_number,
                               "Set aud to array with mixed types",
                               priority="critical", cve_pattern="CVE-2024-5798")
        self.register_mutation("i5_aud_type_nested_array", Invariant.I5_AUTHORIZATION_BINDING,
                               self._i5_aud_type_nested_array,
                               "Set aud to nested array",
                               priority="critical", cve_pattern="CVE-2024-5798")

        # I5 — Token exchange with wrong-audience token
        self.register_mutation("i5_token_exchange_wrong_audience", Invariant.I5_AUTHORIZATION_BINDING,
                               self._i5_token_exchange_wrong_aud,
                               "Token for exchange carries audience of a different service/client",
                               priority="high")
        self.register_mutation("i5_token_exchange_no_audience", Invariant.I5_AUTHORIZATION_BINDING,
                               self._i5_token_exchange_no_aud,
                               "Token for exchange has no audience claim at all",
                               priority="high")

        # I5 — Config-change mutations (CVE-2024-7594 pattern)
        self.register_mutation("i5_bound_audiences_empty_array_config", Invariant.I5_AUTHORIZATION_BINDING,
                               self._i5_bound_aud_empty_config,
                               "Reconfigure role with bound_audiences=[]",
                               priority="critical", cve_pattern="CVE-2024-7594")
        self.register_mutation("i5_bound_audiences_unset_config", Invariant.I5_AUTHORIZATION_BINDING,
                               self._i5_bound_aud_unset_config,
                               "Remove bound_audiences from role config",
                               priority="critical", cve_pattern="CVE-2024-7594")

        # I5 — Numeric type coercion on bound claims (RFC 7519 pattern)
        self.register_mutation("i5_bound_claim_numeric_type_coercion", Invariant.I5_AUTHORIZATION_BINDING,
                               self._i5_bound_claim_numeric_coercion,
                               "Set numeric bound_claim value as float (100.7 vs bound 100) — tests type coercion",
                               priority="high")

    # ==================================================================
    # I1 mutations — existing
    # ==================================================================

    def _i1_alg_none(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        token = self.factory.create_unsigned_token(claims)
        return self._cred(token, baseline)

    def _i1_alg_confusion(self, baseline: Credential) -> Credential:
        """Algorithm confusion: RS256 → HS256 with public key as HMAC secret."""
        import hmac
        import hashlib
        import json
        from src.utils.crypto import base64url_encode
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        pub_pem = self.legitimate_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        header = {"alg": "HS256", "typ": "JWT"}
        h_b64 = base64url_encode(json.dumps(header, separators=(",", ":")).encode())
        p_b64 = base64url_encode(json.dumps(claims, separators=(",", ":"), default=str).encode())
        signing_input = f"{h_b64}.{p_b64}"
        sig = hmac.new(pub_pem, signing_input.encode(), hashlib.sha256).digest()
        sig_b64 = base64url_encode(sig)
        token = f"{signing_input}.{sig_b64}"
        return self._cred(token, baseline)

    def _i1_resign_attacker(self, baseline: Credential) -> Credential:
        token = self.factory.resign_token(baseline.raw_token, self.attacker_key)
        return self._cred(token, baseline)

    def _i1_trust_anchor(self, baseline: Credential) -> Credential:
        token = self.factory.tamper_claims(
            baseline.raw_token,
            {"iss": "http://attacker-idp:9090"},
            signing_key=self.attacker_key,
        )
        return self._cred(token, baseline)

    def _i1_kid_injection(self, baseline: Credential) -> Credential:
        import jwt as pyjwt
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        token = pyjwt.encode(
            claims, self.attacker_key, algorithm="RS256",
            headers={"kid": "attacker-key-id"},
        )
        return self._cred(token, baseline)

    def _i1_jku_injection(self, baseline: Credential) -> Credential:
        import jwt as pyjwt
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        token = pyjwt.encode(
            claims, self.attacker_key, algorithm="RS256",
            headers={"jku": "http://attacker-idp:9090/keys"},
        )
        return self._cred(token, baseline)

    # I1 — URL canonicalization (new)

    def _i1_iss_trailing_slash(self, baseline: Credential) -> Credential:
        iss = self.legitimate_issuer.rstrip("/") + "/"
        token = self.factory.tamper_claims(baseline.raw_token, {"iss": iss})
        return self._cred(token, baseline)

    def _i1_iss_case_variation(self, baseline: Credential) -> Credential:
        iss = self.legitimate_issuer
        # Uppercase hostname portion
        if "://" in iss:
            scheme, rest = iss.split("://", 1)
            rest = rest.upper()
            iss = f"{scheme}://{rest}"
        token = self.factory.tamper_claims(baseline.raw_token, {"iss": iss})
        return self._cred(token, baseline)

    def _i1_iss_unicode_homoglyph(self, baseline: Credential) -> Credential:
        iss = self.legitimate_issuer
        # Try common homoglyph replacements
        if "a" in iss:
            iss = iss.replace("a", "\u0430", 1)  # Cyrillic а
        elif "e" in iss:
            iss = iss.replace("e", "\u0435", 1)  # Cyrillic е
        elif "o" in iss:
            iss = iss.replace("o", "\u043e", 1)  # Cyrillic о
        elif "p" in iss:
            iss = iss.replace("p", "\u0440", 1)  # Cyrillic р
        elif "i" in iss:
            iss = iss.replace("i", "\u0456", 1)  # Cyrillic і
        else:
            iss = iss + "\u200b"  # zero-width space as fallback
        token = self.factory.tamper_claims(
            baseline.raw_token, {"iss": iss}, signing_key=self.attacker_key)
        return self._cred(token, baseline)

    def _i1_iss_port_variation(self, baseline: Credential) -> Credential:
        iss = self.legitimate_issuer
        if iss.startswith("https://") and ":443" not in iss:
            # Insert :443 before path
            parts = iss.split("://", 1)
            host_and_path = parts[1]
            slash_idx = host_and_path.find("/")
            if slash_idx == -1:
                iss = f"{parts[0]}://{host_and_path}:443"
            else:
                iss = f"{parts[0]}://{host_and_path[:slash_idx]}:443{host_and_path[slash_idx:]}"
        elif iss.startswith("http://") and ":80" not in iss:
            parts = iss.split("://", 1)
            host_and_path = parts[1]
            slash_idx = host_and_path.find("/")
            if slash_idx == -1:
                iss = f"{parts[0]}://{host_and_path}:80"
            else:
                iss = f"{parts[0]}://{host_and_path[:slash_idx]}:80{host_and_path[slash_idx:]}"
        token = self.factory.tamper_claims(baseline.raw_token, {"iss": iss})
        return self._cred(token, baseline)

    def _i1_iss_path_traversal(self, baseline: Credential) -> Credential:
        iss = self.legitimate_issuer.rstrip("/") + "/./extra/../"
        token = self.factory.tamper_claims(baseline.raw_token, {"iss": iss})
        return self._cred(token, baseline)

    # ==================================================================
    # I2 mutations — existing
    # ==================================================================

    def _i2_replay(self, baseline: Credential) -> Credential:
        return copy.deepcopy(baseline)

    def _i2_reuse_jti(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        now = int(time.time())
        claims["exp"] = now + 3600
        claims["iat"] = now
        token = self.factory.create_token(claims)
        return self._cred(token, baseline)

    def _i2_expired(self, baseline: Credential) -> Credential:
        token = self.factory.tamper_claims(
            baseline.raw_token, {"exp": int(time.time()) - 3600}
        )
        return self._cred(token, baseline)

    def _i2_future(self, baseline: Credential) -> Credential:
        token = self.factory.tamper_claims(
            baseline.raw_token, {"nbf": int(time.time()) + 7200}
        )
        return self._cred(token, baseline)

    def _i2_missing_exp(self, baseline: Credential) -> Credential:
        import jwt as pyjwt
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims.pop("exp", None)
        token = pyjwt.encode(claims, self.legitimate_key, algorithm="RS256")
        return self._cred(token, baseline)

    def _i2_missing_iat(self, baseline: Credential) -> Credential:
        import jwt as pyjwt
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims.pop("iat", None)
        token = pyjwt.encode(claims, self.legitimate_key, algorithm="RS256")
        return self._cred(token, baseline)

    def _i2_extreme_exp(self, baseline: Credential) -> Credential:
        token = self.factory.tamper_claims(
            baseline.raw_token, {"exp": int(time.time()) + 315360000}
        )
        return self._cred(token, baseline)

    # ==================================================================
    # I4 mutations — existing
    # ==================================================================

    def _i4_sub_overwrite(self, baseline: Credential) -> Credential:
        token = self.factory.tamper_claims(baseline.raw_token, {"sub": "admin"})
        return self._cred(token, baseline)

    def _i4_email_overwrite(self, baseline: Credential) -> Credential:
        token = self.factory.tamper_claims(
            baseline.raw_token, {"email": "admin@target.com"}
        )
        return self._cred(token, baseline)

    def _i4_groups_escalation(self, baseline: Credential) -> Credential:
        token = self.factory.tamper_claims(
            baseline.raw_token, {"groups": ["users", "admins"]}
        )
        return self._cred(token, baseline)

    def _i4_claim_in_header(self, baseline: Credential) -> Credential:
        import jwt as pyjwt
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        original_sub = claims.get("sub", "")
        original_email = claims.get("email", "")
        claims["sub"] = "nobody"
        claims.pop("email", None)
        token = pyjwt.encode(
            claims, self.legitimate_key, algorithm="RS256",
            headers={"sub": original_sub, "email": original_email},
        )
        return self._cred(token, baseline)

    def _i4_unicode_collision(self, baseline: Credential) -> Credential:
        sub = self.legitimate_subject.replace("a", "\u0430", 1)
        token = self.factory.tamper_claims(baseline.raw_token, {"sub": sub})
        return self._cred(token, baseline)

    def _i4_case_confusion(self, baseline: Credential) -> Credential:
        sub = self.legitimate_subject
        flipped = sub[0].upper() + sub[1:] if sub else sub
        token = self.factory.tamper_claims(baseline.raw_token, {"sub": flipped})
        return self._cred(token, baseline)

    # I4 — Type confusion on sub (new)

    def _i4_sub_type_number(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["sub"] = 12345
        token = self.factory.create_token_raw_claims(claims)
        return self._cred(token, baseline)

    def _i4_sub_type_object(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["sub"] = {"username": "admin"}
        token = self.factory.create_token_raw_claims(claims)
        return self._cred(token, baseline)

    def _i4_sub_type_null(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["sub"] = None
        token = self.factory.create_token_raw_claims(claims)
        return self._cred(token, baseline)

    def _i4_sub_type_array(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["sub"] = ["alice", "admin"]
        token = self.factory.create_token_raw_claims(claims)
        return self._cred(token, baseline)

    def _i4_sub_type_boolean(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["sub"] = True
        token = self.factory.create_token_raw_claims(claims)
        return self._cred(token, baseline)

    def _i4_sub_type_empty_string(self, baseline: Credential) -> Credential:
        token = self.factory.tamper_claims(baseline.raw_token, {"sub": ""})
        return self._cred(token, baseline)

    # I4 — Type confusion on groups (new)

    def _i4_groups_type_string(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["groups"] = "admins"
        token = self.factory.create_token_raw_claims(claims)
        return self._cred(token, baseline)

    def _i4_groups_type_object(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["groups"] = {"name": "admins", "role": "admin"}
        token = self.factory.create_token_raw_claims(claims)
        return self._cred(token, baseline)

    def _i4_groups_type_null(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["groups"] = None
        token = self.factory.create_token_raw_claims(claims)
        return self._cred(token, baseline)

    def _i4_groups_type_number(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["groups"] = 1
        token = self.factory.create_token_raw_claims(claims)
        return self._cred(token, baseline)

    def _i4_groups_type_boolean(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["groups"] = True
        token = self.factory.create_token_raw_claims(claims)
        return self._cred(token, baseline)

    def _i4_groups_type_array_mixed(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["groups"] = ["developers", 123, None, True]
        token = self.factory.create_token_raw_claims(claims)
        return self._cred(token, baseline)

    # I4 — Glob/wildcard injection (new)

    def _i4_glob_star(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["department"] = "*"
        token = self.factory.create_token(claims)
        return self._cred(token, baseline)

    def _i4_glob_question(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["department"] = "engineerin?"
        token = self.factory.create_token(claims)
        return self._cred(token, baseline)

    def _i4_glob_bracket(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["department"] = "[a-z]*"
        token = self.factory.create_token(claims)
        return self._cred(token, baseline)

    def _i4_bound_claims_empty(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["department"] = ""
        token = self.factory.create_token(claims)
        return self._cred(token, baseline)

    # I1/I3 — HTTP header injection (new)

    def _i1_header_injection_identity(self, baseline: Credential) -> Credential:
        """Inject identity via HTTP proxy headers commonly trusted by auth proxies.

        Many platforms support authenticating proxy connectors that trust
        upstream headers like X-Remote-User, X-Forwarded-User, etc.
        If the platform accepts these headers from untrusted sources,
        any client can impersonate any user by setting the header.
        """
        c = copy.deepcopy(baseline)
        c.headers = {
            "X-Remote-User": "admin",
            "X-Forwarded-User": "admin",
            "X-Remote-Extra-Admin": "true",
        }
        c.metadata["mutation_note"] = (
            "HTTP headers injected: X-Remote-User=admin, X-Forwarded-User=admin. "
            "If platform trusts these from client, identity is spoofable."
        )
        return c

    def _i1_header_injection_groups(self, baseline: Credential) -> Credential:
        """Inject group membership via HTTP proxy headers."""
        c = copy.deepcopy(baseline)
        c.headers = {
            "X-Remote-Group": "admins",
            "X-Forwarded-Group": "admins",
            "X-Remote-Groups": "admins,superusers",
        }
        c.metadata["mutation_note"] = (
            "HTTP headers injected: X-Remote-Group=admins. "
            "If platform trusts these from client, group membership is spoofable."
        )
        return c

    def _i1_header_injection_email(self, baseline: Credential) -> Credential:
        """Inject email identity via HTTP proxy headers."""
        c = copy.deepcopy(baseline)
        c.headers = {
            "X-Remote-Email": "admin@target.com",
            "X-Forwarded-Email": "admin@target.com",
        }
        c.metadata["mutation_note"] = (
            "HTTP headers injected: X-Remote-Email=admin@target.com. "
            "If platform trusts these from client, email identity is spoofable."
        )
        return c

    # I4 — Config-change mutations (new)

    def _i4_bound_claims_empty_config(self, baseline: Credential) -> Credential:
        c = copy.deepcopy(baseline)
        c.metadata["mutation_step"] = "config_change"
        c.metadata["config_change"] = {"bound_claims": {}}
        return c

    def _i4_user_claim_nonexistent(self, baseline: Credential) -> Credential:
        c = copy.deepcopy(baseline)
        c.metadata["mutation_step"] = "config_change"
        c.metadata["config_change"] = {"user_claim": "nonexistent_field_xyz"}
        return c

    # ==================================================================
    # I5 mutations — existing
    # ==================================================================

    def _i5_aud_wrong(self, baseline: Credential) -> Credential:
        token = self.factory.tamper_claims(
            baseline.raw_token, {"aud": "other-service"}
        )
        return self._cred(token, baseline)

    def _i5_aud_empty(self, baseline: Credential) -> Credential:
        token = self.factory.tamper_claims(baseline.raw_token, {"aud": ""})
        return self._cred(token, baseline)

    def _i5_aud_missing(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims.pop("aud", None)
        token = self.factory.create_token(claims)
        return self._cred(token, baseline)

    def _i5_aud_array_extra(self, baseline: Credential) -> Credential:
        token = self.factory.tamper_claims(
            baseline.raw_token,
            {"aud": [self.legitimate_audience, "attacker-service"]},
        )
        return self._cred(token, baseline)

    def _i5_scope_inflation(self, baseline: Credential) -> Credential:
        token = self.factory.tamper_claims(
            baseline.raw_token,
            {"scope": "openid profile email admin:full"},
        )
        return self._cred(token, baseline)

    def _i5_scope_empty(self, baseline: Credential) -> Credential:
        token = self.factory.tamper_claims(baseline.raw_token, {"scope": ""})
        return self._cred(token, baseline)

    # I5 — Type confusion on aud (new)

    def _i5_aud_type_number(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["aud"] = 12345
        token = self.factory.create_token_raw_claims(claims)
        return self._cred(token, baseline)

    def _i5_aud_type_boolean(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["aud"] = True
        token = self.factory.create_token_raw_claims(claims)
        return self._cred(token, baseline)

    def _i5_aud_type_null(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["aud"] = None
        token = self.factory.create_token_raw_claims(claims)
        return self._cred(token, baseline)

    def _i5_aud_type_object(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["aud"] = {"value": self.legitimate_audience}
        token = self.factory.create_token_raw_claims(claims)
        return self._cred(token, baseline)

    def _i5_aud_type_empty_array(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["aud"] = []
        token = self.factory.create_token_raw_claims(claims)
        return self._cred(token, baseline)

    def _i5_aud_type_array_with_null(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["aud"] = [self.legitimate_audience, None]
        token = self.factory.create_token_raw_claims(claims)
        return self._cred(token, baseline)

    def _i5_aud_type_array_with_number(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["aud"] = [self.legitimate_audience, 0]
        token = self.factory.create_token_raw_claims(claims)
        return self._cred(token, baseline)

    def _i5_aud_type_nested_array(self, baseline: Credential) -> Credential:
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["aud"] = [[self.legitimate_audience]]
        token = self.factory.create_token_raw_claims(claims)
        return self._cred(token, baseline)

    # I5 — Token exchange with wrong-audience token (new)

    def _i5_token_exchange_wrong_aud(self, baseline: Credential) -> Credential:
        """Create a token whose audience is a different service, intended
        for use as a subject_token in token exchange flows.

        Per RFC 8693 Section 2.1, token exchange should verify that the
        subject_token's audience matches the resource server performing
        the exchange. If a token minted for service-A is accepted by
        service-B's token exchange endpoint, audience binding is broken.
        """
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims["aud"] = "other-service-not-intended-recipient"
        token = self.factory.create_token(claims)
        c = self._cred(token, baseline)
        c.metadata["mutation_note"] = (
            "Token carries audience of a different service — if accepted in "
            "token exchange, audience binding is not enforced"
        )
        c.metadata["token_exchange_role"] = "subject_token"
        return c

    def _i5_token_exchange_no_aud(self, baseline: Credential) -> Credential:
        """Create a token with no audience claim, intended for token exchange.

        If the exchange endpoint accepts a token with no audience, it cannot
        verify the token was intended for it.
        """
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims.pop("aud", None)
        token = self.factory.create_token(claims)
        c = self._cred(token, baseline)
        c.metadata["mutation_note"] = (
            "Token has no audience claim — if accepted in token exchange, "
            "audience validation is not enforced"
        )
        c.metadata["token_exchange_role"] = "subject_token"
        return c

    # I5 — Config-change mutations (new)

    def _i5_bound_aud_empty_config(self, baseline: Credential) -> Credential:
        c = copy.deepcopy(baseline)
        c.metadata["mutation_step"] = "config_change"
        c.metadata["config_change"] = {"bound_audiences": []}
        return c

    def _i5_bound_aud_unset_config(self, baseline: Credential) -> Credential:
        c = copy.deepcopy(baseline)
        c.metadata["mutation_step"] = "config_change"
        c.metadata["config_change"] = {"bound_audiences": None}
        return c

    # I5 — Numeric type coercion on bound claims (new)

    def _i5_bound_claim_numeric_coercion(self, baseline: Credential) -> Credential:
        """Set a numeric bound_claim value as a float to test type coercion.

        Per RFC 7519, claim values have specific JSON types. If a platform
        performs loose numeric comparison (e.g., int(100.7) == 100), a
        floating-point claim value could match a bound_claim intended for
        an integer, bypassing strict claim matching.
        """
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        # Find an existing numeric claim to coerce, or inject one
        coerced = False
        for claim_name, claim_value in list(claims.items()):
            if claim_name in ("iat", "exp", "nbf", "jti", "nonce"):
                continue  # Skip standard timing/ID claims
            if isinstance(claim_value, (int, float)) and claim_name not in ("iat", "exp", "nbf"):
                claims[claim_name] = float(claim_value) + 0.7
                coerced = True
                break
        if not coerced:
            # Inject a department_id claim with float coercion
            claims["department_id"] = 100.7
        token = self.factory.create_token(claims)
        c = self._cred(token, baseline)
        c.metadata["mutation_note"] = (
            "Numeric bound_claim set as float — tests whether platform "
            "performs strict type comparison or truncates/rounds to int"
        )
        return c

    # I4 — NFC/NFD Unicode normalization (new)

    def _i4_subject_nfd_nfc(self, baseline: Credential) -> Credential:
        """Create JWT with subject in NFD form vs the NFC baseline.

        Per RFC 7613 (PRECIS), identity strings should be normalized
        before comparison. NFC "cafe\\u0301" (decomposed e-acute) and
        NFC "caf\\u00e9" (composed) are the same logical string but
        different byte sequences. If the platform compares raw bytes,
        they map to different identities — an I4 violation.
        """
        import unicodedata
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        original_sub = claims.get("sub", "alice")
        # Convert to NFD (decomposed) form
        nfd_sub = unicodedata.normalize("NFD", original_sub)
        if nfd_sub == original_sub:
            # If NFD == NFC for this string (pure ASCII), inject a
            # distinguishing character that differs under normalization
            nfd_sub = original_sub + "\u0301"  # combining acute accent
        claims["sub"] = nfd_sub
        token = self.factory.create_token(claims)
        c = self._cred(token, baseline)
        c.metadata["mutation_note"] = (
            f"Subject in NFD form ({repr(nfd_sub)}) vs NFC baseline "
            f"({repr(original_sub)}) — tests Unicode normalization"
        )
        return c

    # I2 — Stateless JWT without jti (new)

    def _i2_no_jti(self, baseline: Credential) -> Credential:
        """Create JWT without jti claim for replay testing.

        Different from i2_replay_same_token which replays WITH jti.
        This tests whether the server can track token uniqueness when
        the token itself has no unique identifier. Without jti, the
        server must use other mechanisms (e.g., hash of the full token)
        to detect replays.
        """
        _, claims = self.factory.decode_without_verification(baseline.raw_token)
        claims.pop("jti", None)
        token = self.factory.create_token(claims)
        c = self._cred(token, baseline)
        c.metadata["mutation_note"] = (
            "JWT without jti claim — tests whether server can detect "
            "replay without a unique token identifier"
        )
        return c

    # ==================================================================
    # Helper
    # ==================================================================

    @staticmethod
    def _cred(token: str, baseline: Credential) -> Credential:
        return Credential(
            protocol=Protocol.JWT,
            raw_token=token,
            claims=baseline.claims,
            metadata=dict(baseline.metadata),
        )
