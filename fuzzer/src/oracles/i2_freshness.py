"""I2 Freshness Oracle — context-dependent replay and expiration checking."""

from __future__ import annotations

import time

from src.models.types import AuthContext, AuthResult, Invariant, MutationRecord, Verdict, VerdictType
from src.oracles.base import SecurityOracle


class I2FreshnessOracle(SecurityOracle):

    def __init__(self, invariant: Invariant = Invariant.I2_FRESHNESS):
        super().__init__(invariant)

    def check(
        self,
        mutation: MutationRecord,
        auth_result: AuthResult,
        context: dict | None = None,
    ) -> Verdict:
        try:
            return self._check_inner(mutation, auth_result, context)
        except Exception as exc:
            return self._verdict(
                VerdictType.ERROR, "LOW",
                f"Oracle error: {exc}", {"exception": str(exc)},
            )

    def _check_inner(
        self, mutation: MutationRecord, auth_result: AuthResult, context: dict | None,
    ) -> Verdict:
        auth_ctx = (
            AuthContext(context.get("auth_context", AuthContext.JWT_BEARER))
            if context and "auth_context" in context
            else AuthContext.JWT_BEARER
        )
        mutation_type = mutation.mutation_type

        if not auth_result.success:
            return self._rejected(mutation_type, auth_result.error_message)

        # --- Replay mutations ---
        if mutation_type in ("i2_replay_same_token", "i2_replay_same_response",
                             "i2_saml_assertion_id_replay",
                             "i2_saml_one_time_use_replay"):
            return self._check_replay(mutation, auth_result, auth_ctx, context)

        if mutation_type == "i2_reuse_jti_new_exp":
            return self._check_jti_reuse(mutation, auth_result, auth_ctx, context)

        if mutation_type == "i2_code_replay":
            return self._check_code_replay(mutation, auth_result, context)

        # --- Expiration mutations ---
        if mutation_type in ("i2_expired_token", "i2_expired_assertion"):
            return self._check_expired(mutation, auth_result, context)

        if mutation_type == "i2_future_token":
            return self._check_future(mutation, auth_result, context)

        if mutation_type == "i2_missing_exp":
            return self._check_missing_exp(mutation, auth_result, context)

        if mutation_type == "i2_missing_iat":
            return self._check_missing_iat(mutation, auth_result, context)

        if mutation_type == "i2_inresponseto_mismatch":
            return self._check_inresponseto(mutation, auth_result, context)

        if mutation_type == "i2_missing_inresponseto":
            return self._check_inresponseto(mutation, auth_result, context)

        if mutation_type == "i2_disabled_user_login":
            return self._check_disabled_user(mutation, auth_result, context)

        if mutation_type == "i2_password_changed_replay":
            return self._check_password_replay(mutation, auth_result, context)

        if mutation_type == "i2_refresh_token_after_revocation":
            return self._check_refresh_revocation(mutation, auth_result, context)

        if mutation_type == "i2_stateless_jwt_no_jti":
            return self._check_no_jti(mutation, auth_result, context)

        if mutation_type in ("i2_extreme_exp", "i2_old_session_index"):
            return self._check_generic_freshness(mutation, auth_result, context)

        if mutation_type == "i2_oidc_sso_nonce_bypass":
            return self._check_oidc_sso_nonce_bypass(mutation, auth_result, context)

        if mutation_type == "i2_saml_no_conditions":
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "SAML assertion with no Conditions element accepted. "
                "Broker must reject assertions with no temporal constraints in SP/broker context.",
                {},
                spec_reference="SAML Core 2.0 Section 2.5.1",
            )

        return self._verdict(
            VerdictType.ERROR, "LOW",
            f"Unhandled I2 mutation: {mutation_type}", {},
        )

    # ------------------------------------------------------------------
    # Replay
    # ------------------------------------------------------------------

    def _check_replay(
        self, mutation: MutationRecord, auth_result: AuthResult,
        auth_ctx: AuthContext, context: dict | None,
    ) -> Verdict:
        prior_results = (context or {}).get("prior_submission_results", [])
        prior_accepted = any(r.success for r in prior_results)

        if not prior_accepted:
            return self._verdict(
                VerdictType.BY_DESIGN, "HIGH",
                "First submission accepted (expected)", {},
            )

        # This IS a replay (prior submission was also accepted)
        if auth_ctx == AuthContext.JWT_BEARER:
            return self._verdict(
                VerdictType.BY_DESIGN, "HIGH",
                "JWT bearer token replay accepted. This is correct behavior: "
                "bearer tokens are designed for multiple uses within their "
                "validity window (RFC 6750 Section 1.2). jti enforcement is "
                "OPTIONAL per RFC 7519 Section 4.1.7.",
                {"auth_context": auth_ctx.value,
                 "replay_count": len(prior_results) + 1},
                spec_reference="RFC 6750 Section 1.2, RFC 7519 Section 4.1.7",
            )

        if auth_ctx == AuthContext.OAUTH2_CLIENT_ASSERTION:
            jti = None
            if mutation.mutated and hasattr(mutation.mutated, "claims"):
                jti = mutation.mutated.claims.get("jti")
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "Client assertion JWT replay accepted. RFC 7523 Section 3 REQUIRES "
                "the authorization server to reject assertions with a jti value "
                "that has already been processed.",
                {"auth_context": auth_ctx.value, "jti": jti},
                spec_reference="RFC 7523 Section 3",
                cve_pattern="CVE-2020-15222",
            )

        if auth_ctx == AuthContext.SAML_ASSERTION:
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "SAML assertion replay accepted. SAML Core Section 2.5.1 REQUIRES "
                "relying parties to track assertion IDs and reject duplicates.",
                {"auth_context": auth_ctx.value},
                spec_reference="SAML Core 2.0 Section 2.5.1",
                cve_pattern="CVE-2018-14637",
            )

        if auth_ctx == AuthContext.LDAP_BIND:
            return self._verdict(
                VerdictType.BY_DESIGN, "HIGH",
                "LDAP bind with same credentials accepted. LDAP authentication "
                "is a stateless credential check; replay is expected.",
                {"auth_context": auth_ctx.value},
            )

        return self._verdict(
            VerdictType.UNEXPECTED, "MEDIUM",
            f"Replay accepted in context {auth_ctx.value}. Manual review needed.",
            {"auth_context": auth_ctx.value},
            requires_manual_review=True,
        )

    def _check_jti_reuse(
        self, mutation: MutationRecord, auth_result: AuthResult,
        auth_ctx: AuthContext, context: dict | None,
    ) -> Verdict:
        if auth_ctx == AuthContext.OAUTH2_CLIENT_ASSERTION:
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "Reused jti accepted in client assertion context. "
                "RFC 7523 Section 3 requires jti uniqueness.",
                {"auth_context": auth_ctx.value},
                spec_reference="RFC 7523 Section 3",
                cve_pattern="CVE-2020-15222",
            )
        if auth_ctx == AuthContext.JWT_BEARER:
            return self._verdict(
                VerdictType.BY_DESIGN, "HIGH",
                "JWT is stateless by design (RFC 7519). jti tracking is "
                "optional per RFC 7519 Section 4.1.7 and not implemented "
                "by any major JWT auth system (AWS IAM, Google IAM, K8s OIDC). "
                "Reused jti in a stateless JWT verifier is expected behavior.",
                {"auth_context": auth_ctx.value},
                spec_reference="RFC 7519 Section 4.1.7 (OPTIONAL)",
            )
        if auth_ctx == AuthContext.SAML_ASSERTION:
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "Reused assertion ID accepted in SAML context. "
                "SAML Core Section 2.5.1 requires assertion ID tracking.",
                {"auth_context": auth_ctx.value},
                spec_reference="SAML Core 2.0 Section 2.5.1",
            )
        return self._verdict(
            VerdictType.UNEXPECTED, "MEDIUM",
            "Reused jti accepted. jti enforcement is optional for bearer tokens "
            "but indicates weak replay protection.",
            {"auth_context": auth_ctx.value},
            requires_manual_review=True,
        )

    # ------------------------------------------------------------------
    # Code replay
    # ------------------------------------------------------------------

    def _check_code_replay(
        self, mutation: MutationRecord, auth_result: AuthResult,
        context: dict | None,
    ) -> Verdict:
        first_result = (context or {}).get("first_exchange_result")
        if not first_result or not first_result.success:
            return self._verdict(
                VerdictType.ERROR, "LOW",
                "Missing first exchange result in context", {},
            )
        return self._verdict(
            VerdictType.VIOLATION, "HIGH",
            "OAuth2 authorization code accepted on second use. "
            "RFC 6749 Section 4.1.2 states: 'The client MUST NOT use the "
            "authorization code more than once. If an authorization code is "
            "used more than once, the authorization server MUST deny the request.'",
            {"first_status": first_result.http_status,
             "second_status": auth_result.http_status},
            spec_reference="RFC 6749 Section 4.1.2",
        )

    # ------------------------------------------------------------------
    # Expiration
    # ------------------------------------------------------------------

    def _check_expired(
        self, mutation: MutationRecord, auth_result: AuthResult,
        context: dict | None,
    ) -> Verdict:
        exp = None
        if mutation.mutated and hasattr(mutation.mutated, "claims"):
            exp = mutation.mutated.claims.get("exp")
        now = time.time()
        clock_skew = (context or {}).get("clock_skew_tolerance", 60)
        delta = (now - exp) if exp is not None else None

        if delta is not None and delta > clock_skew + 60:
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                f"Expired credential accepted. Expired {int(delta)}s ago, "
                f"well beyond {clock_skew}s clock skew tolerance.",
                {"exp": exp, "now": now, "delta_seconds": int(delta),
                 "clock_skew_tolerance": clock_skew},
                spec_reference="RFC 7519 Section 4.1.4",
            )
        if delta is not None and delta > 0:
            return self._verdict(
                VerdictType.UNEXPECTED, "MEDIUM",
                f"Credential expired {int(delta)}s ago but accepted. "
                f"Within plausible clock skew range ({clock_skew}s configured).",
                {"exp": exp, "now": now, "delta_seconds": int(delta)},
                requires_manual_review=True,
            )
        return self._verdict(
            VerdictType.BY_DESIGN, "HIGH",
            "Credential not actually expired at time of check", {},
        )

    def _check_future(
        self, mutation: MutationRecord, auth_result: AuthResult,
        context: dict | None,
    ) -> Verdict:
        nbf = None
        if mutation.mutated and hasattr(mutation.mutated, "claims"):
            nbf = mutation.mutated.claims.get("nbf") or mutation.mutated.claims.get("iat")
        now = time.time()
        clock_skew = (context or {}).get("clock_skew_tolerance", 60)

        if nbf is not None:
            delta = nbf - now
            if delta > clock_skew + 60:
                return self._verdict(
                    VerdictType.VIOLATION, "HIGH",
                    f"Future-dated credential accepted. Not valid for {int(delta)}s, "
                    f"well beyond {clock_skew}s clock skew tolerance.",
                    {"nbf": nbf, "now": now, "delta_seconds": int(delta)},
                    spec_reference="RFC 7519 Section 4.1.5",
                )
            if delta > 0:
                return self._verdict(
                    VerdictType.UNEXPECTED, "MEDIUM",
                    f"Future-dated credential accepted ({int(delta)}s ahead). "
                    f"Within plausible clock skew range.",
                    {"nbf": nbf, "now": now, "delta_seconds": int(delta)},
                    requires_manual_review=True,
                )
        return self._verdict(
            VerdictType.BY_DESIGN, "HIGH",
            "Future token accepted within tolerance", {},
        )

    def _check_missing_exp(
        self, mutation: MutationRecord, auth_result: AuthResult,
        context: dict | None,
    ) -> Verdict:
        auth_ctx = (
            AuthContext(context.get("auth_context", AuthContext.JWT_BEARER))
            if context and "auth_context" in context
            else AuthContext.JWT_BEARER
        )
        if auth_ctx == AuthContext.EXTERNAL_JWT_PROVIDER:
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "External JWT / OIDC ID Token accepted without exp. "
                "OIDC Core requires exp on ID Tokens; missing exp enables non-expiring credentials.",
                {},
                spec_reference="OpenID Connect Core 1.0 §2 (ID Token — exp REQUIRED)",
            )
        return self._verdict(
            VerdictType.UNEXPECTED, "MEDIUM",
            "Token without exp claim accepted. While exp is not universally "
            "required by RFC 7519, best practice dictates tokens should have "
            "a bounded lifetime. Platform may be relying on other mechanisms.",
            {},
            spec_reference="RFC 7519 Section 4.1.4",
            requires_manual_review=True,
        )

    def _check_missing_iat(
        self, mutation: MutationRecord, auth_result: AuthResult,
        context: dict | None,
    ) -> Verdict:
        auth_ctx = (
            AuthContext(context.get("auth_context", AuthContext.JWT_BEARER))
            if context and "auth_context" in context
            else AuthContext.JWT_BEARER
        )
        if auth_ctx == AuthContext.EXTERNAL_JWT_PROVIDER:
            return self._verdict(
                VerdictType.VIOLATION, "MEDIUM",
                "External JWT provider accepted token without iat; max-age / freshness "
                "enforcement (e.g. CheckIssuedAt) is bypassed when iat is absent.",
                {},
                spec_reference="RFC 7519 Section 4.1.6 (iat)",
            )
        return self._verdict(
            VerdictType.UNEXPECTED, "MEDIUM",
            "Token without iat accepted. Issued-at is not universally required; "
            "platform-specific freshness policies may be skipped.",
            {},
            spec_reference="RFC 7519 Section 4.1.6",
            requires_manual_review=True,
        )

    # ------------------------------------------------------------------
    # SAML-specific
    # ------------------------------------------------------------------

    def _check_inresponseto(
        self, mutation: MutationRecord, auth_result: AuthResult,
        context: dict | None,
    ) -> Verdict:
        expected_request_id = (context or {}).get("original_request_id")
        actual_irt = None
        if mutation.mutated and hasattr(mutation.mutated, "metadata"):
            actual_irt = mutation.mutated.metadata.get("in_response_to")

        if actual_irt is None:
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "SAML Response accepted without InResponseTo attribute. "
                "When SP-initiated SSO is used, InResponseTo binding is required "
                "to prevent response injection attacks.",
                {"expected": expected_request_id, "actual": None},
                spec_reference="SAML Core 2.0 Section 3.2.2",
                cve_pattern="CVE-2023-0264",
            )

        if actual_irt != expected_request_id:
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "SAML Response accepted with mismatched InResponseTo. "
                "Response was issued for a different authentication request.",
                {"expected": expected_request_id, "actual": actual_irt},
                spec_reference="SAML Core 2.0 Section 3.2.2",
                cve_pattern="CVE-2023-0264",
            )

        return self._verdict(
            VerdictType.BY_DESIGN, "HIGH",
            "InResponseTo correctly matched", {},
        )

    # ------------------------------------------------------------------
    # LDAP-specific
    # ------------------------------------------------------------------

    def _check_disabled_user(
        self, mutation: MutationRecord, auth_result: AuthResult,
        context: dict | None,
    ) -> Verdict:
        return self._verdict(
            VerdictType.VIOLATION, "HIGH",
            "Disabled user account was able to authenticate. "
            "Platform should check account status during authentication.",
            {},
        )

    def _check_password_replay(
        self, mutation: MutationRecord, auth_result: AuthResult,
        context: dict | None,
    ) -> Verdict:
        return self._verdict(
            VerdictType.VIOLATION, "HIGH",
            "Old password accepted after password change. "
            "Platform should invalidate previous credentials.",
            {},
        )

    def _check_refresh_revocation(
        self, mutation: MutationRecord, auth_result: AuthResult,
        context: dict | None,
    ) -> Verdict:
        return self._verdict(
            VerdictType.VIOLATION, "HIGH",
            "Refresh token accepted after revocation. "
            "RFC 7009 requires revoked tokens to be rejected.",
            {},
            spec_reference="RFC 7009 Section 2.1",
        )

    def _check_no_jti(
        self, mutation: MutationRecord, auth_result: AuthResult,
        context: dict | None,
    ) -> Verdict:
        """JWT without jti claim accepted — tests replay detection without
        unique identifier.

        JWT is stateless by design (RFC 7519). The jti claim is OPTIONAL
        per Section 4.1.7. No major JWT auth system (AWS IAM, Google IAM,
        K8s OIDC, Vault JWT auth) implements jti tracking. Accepting a
        JWT without jti is standard, expected behavior for stateless
        JWT verifiers.
        """
        auth_ctx = (
            AuthContext(context.get("auth_context", AuthContext.JWT_BEARER))
            if context and "auth_context" in context
            else AuthContext.JWT_BEARER
        )

        # For stateless JWT verifiers, no jti is expected behavior
        if auth_ctx == AuthContext.JWT_BEARER:
            return self._verdict(
                VerdictType.BY_DESIGN, "HIGH",
                "JWT is stateless by design (RFC 7519). jti tracking is "
                "optional per RFC 7519 Section 4.1.7 and not implemented "
                "by any major JWT auth system. Accepting a JWT without jti "
                "is standard behavior for stateless JWT verifiers.",
                {"auth_context": auth_ctx.value},
                spec_reference="RFC 7519 Section 4.1.7 (OPTIONAL)",
            )

        # For client assertions, jti is REQUIRED
        if auth_ctx == AuthContext.OAUTH2_CLIENT_ASSERTION:
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "Client assertion JWT without jti accepted. "
                "RFC 7523 Section 3 REQUIRES jti for client assertions.",
                {"auth_context": auth_ctx.value},
                spec_reference="RFC 7523 Section 3",
            )

        # For SAML, assertion ID tracking is required
        if auth_ctx == AuthContext.SAML_ASSERTION:
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "SAML assertion without unique identifier accepted. "
                "SAML Core Section 2.5.1 requires assertion ID tracking.",
                {"auth_context": auth_ctx.value},
                spec_reference="SAML Core 2.0 Section 2.5.1",
            )

        prior_results = (context or {}).get("prior_submission_results", [])
        prior_accepted = any(r.success for r in prior_results)

        if not prior_accepted:
            return self._verdict(
                VerdictType.BY_DESIGN, "HIGH",
                "Token without jti accepted on first submission. "
                "jti is OPTIONAL per RFC 7519 Section 4.1.7.",
                {"auth_context": auth_ctx.value},
                spec_reference="RFC 7519 Section 4.1.7 (OPTIONAL)",
            )

        return self._verdict(
            VerdictType.BY_DESIGN, "HIGH",
            "Token without jti accepted on replay. jti tracking is "
            "OPTIONAL per RFC 7519 Section 4.1.7 and not implemented "
            "by any major JWT auth system.",
            {"auth_context": auth_ctx.value},
            spec_reference="RFC 7519 Section 4.1.7 (OPTIONAL), RFC 6750 Section 1.2",
        )

    def _check_oidc_sso_nonce_bypass(
        self, mutation: MutationRecord, auth_result: AuthResult,
        context: dict | None,
    ) -> Verdict:
        """OIDC SSO login accepted with nonce absent from id_token.

        Per OIDC Core 3.1.3.7 §11, when the RP sends a nonce in the authorization
        request, it MUST validate the nonce in the returned id_token and MUST reject
        tokens where the nonce is missing or does not match.
        """
        return self._verdict(
            VerdictType.VIOLATION, "HIGH",
            "OIDC SSO login accepted without nonce claim in id_token. "
            "Per OIDC Core 3.1.3.7 §11, the RP must verify the nonce and reject "
            "id_tokens where nonce is absent or mismatched when nonce was sent in "
            "the authorization request. Missing nonce validation enables id_token "
            "replay and injection attacks.",
            {},
            spec_reference="OpenID Connect Core 1.0 §3.1.3.7",
        )

    def _check_generic_freshness(
        self, mutation: MutationRecord, auth_result: AuthResult,
        context: dict | None,
    ) -> Verdict:
        return self._verdict(
            VerdictType.UNEXPECTED, "MEDIUM",
            f"Freshness mutation {mutation.mutation_type} accepted. Manual review needed.",
            {},
            requires_manual_review=True,
        )
