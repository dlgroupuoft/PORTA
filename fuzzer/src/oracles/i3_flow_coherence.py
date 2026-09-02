"""I3 Flow Coherence Oracle — OAuth2/OIDC flow integrity checks."""

from __future__ import annotations

from src.models.types import AuthResult, Invariant, MutationRecord, Verdict, VerdictType
from src.oracles.base import SecurityOracle


class I3FlowCoherenceOracle(SecurityOracle):

    def __init__(self, invariant: Invariant = Invariant.I3_FLOW_COHERENCE):
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
        mt = mutation.mutation_type

        if not auth_result.success:
            return self._rejected(mt, auth_result.error_message)

        # --- Clear MUST requirement checks ---
        if mt == "i3_redirect_uri_mismatch":
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "Token endpoint accepted mismatched redirect_uri. "
                "RFC 6749 Section 4.1.3: 'The authorization server MUST ensure that "
                "the redirect_uri parameter is present if the redirect_uri parameter "
                "was included in the initial authorization request, and if included "
                "ensure that their values are identical.'",
                {},
                spec_reference="RFC 6749 Section 4.1.3",
            )

        if mt == "i3_code_injection":
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "Authorization code injection succeeded. Auth codes must be bound "
                "to the client and redirect_uri.",
                {},
                spec_reference="RFC 6749 Section 4.1.2",
            )

        if mt == "i3_pkce_skip":
            return self._verdict(
                VerdictType.BY_DESIGN, "HIGH",
                "PKCE (RFC 7636) is an optional extension. Not enforcing "
                "code_verifier when code_challenge was sent is standard behavior "
                "per RFC 6749. No CVE has been issued for not requiring PKCE. "
                "This is a hardening check, not a vulnerability.",
                {},
                spec_reference="RFC 7636 Section 4.6 (OPTIONAL), RFC 6749",
            )

        if mt == "i3_pkce_wrong_verifier":
            return self._verdict(
                VerdictType.BY_DESIGN, "HIGH",
                "PKCE (RFC 7636) is an optional extension. Accepting a "
                "mismatched code_verifier may indicate PKCE is not enforced, "
                "which is standard behavior per RFC 6749. Not enforcing PKCE "
                "is not a vulnerability.",
                {},
                spec_reference="RFC 7636 Section 4.6 (OPTIONAL), RFC 6749",
            )

        if mt == "i3_pkce_not_required_public_client":
            return self._verdict(
                VerdictType.BY_DESIGN, "HIGH",
                "PKCE (RFC 7636) is an optional extension. Not enforcing it "
                "for public clients is standard behavior per RFC 6749. While "
                "OAuth 2.1 (draft) will require PKCE, the current RFC 7636 "
                "only RECOMMENDS it. No CVE has been issued for not requiring "
                "PKCE. This is a hardening check, not a vulnerability.",
                {},
                spec_reference="RFC 7636 Section 4 (OPTIONAL), RFC 6749",
            )

        if mt == "i3_auth_code_no_client_auth":
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "Auth code exchanged without any client authentication and "
                "without PKCE. Neither client_secret nor code_verifier was "
                "provided. The authorization code can be stolen and used by "
                "any party.",
                {},
                spec_reference="RFC 6749 Section 4.1.3, RFC 7636",
            )

        # --- Context-dependent checks ---
        if mt == "i3_state_swap":
            return self._check_state_swap(mutation, auth_result, context)

        if mt == "i3_loopback_port_override":
            return self._verdict(
                VerdictType.BY_DESIGN, "HIGH",
                "Loopback redirect with different port accepted. "
                "RFC 8252 Section 7.3 explicitly allows port variation for "
                "loopback redirects in native app flows.",
                {},
                spec_reference="RFC 8252 Section 7.3",
                requires_manual_review=True,
            )

        if mt == "i3_nonce_mismatch":
            return self._verdict(
                VerdictType.UNEXPECTED, "MEDIUM",
                "Mismatched nonce accepted. Nonce is RECOMMENDED in OIDC "
                "but not REQUIRED in plain OAuth2. If the platform issues "
                "id_tokens, nonce binding should be enforced.",
                {},
                spec_reference="OpenID Connect Core Section 3.1.2.1",
                requires_manual_review=True,
            )

        if mt == "i3_scope_escalation_at_token":
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "Granted scope at token endpoint exceeds authorization request scope. "
                "RFC 6749 Section 3.3: the authorization server MUST NOT issue "
                "a token with broader scope than what was authorized.",
                {},
                spec_reference="RFC 6749 Section 3.3",
            )

        # SAML cross-session
        if mt == "i3_response_cross_session":
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "SAML response accepted in a different session than it was issued for.",
                {},
                spec_reference="SAML Core 2.0 Section 3.4",
            )

        return self._verdict(
            VerdictType.ERROR, "LOW",
            f"Unhandled I3 mutation: {mt}", {},
        )

    # ------------------------------------------------------------------
    # Context-dependent helpers
    # ------------------------------------------------------------------

    def _check_state_swap(
        self, mutation: MutationRecord, auth_result: AuthResult, context: dict | None,
    ) -> Verdict:
        # OAuth2 spec: state is for CLIENT-SIDE CSRF protection.
        # The authorization server does not validate state.
        id_token = (context or {}).get("id_token_claims", {})
        original_nonce = (context or {}).get("original_nonce")

        if id_token and original_nonce:
            token_nonce = id_token.get("nonce")
            if token_nonce and token_nonce != original_nonce:
                return self._verdict(
                    VerdictType.UNEXPECTED, "MEDIUM",
                    "State swap accepted and id_token nonce does not match "
                    "the original session nonce. This indicates the response "
                    "is bound to a different session.",
                    {"original_nonce": original_nonce,
                     "id_token_nonce": token_nonce},
                    requires_manual_review=True,
                )

        return self._verdict(
            VerdictType.BY_DESIGN, "HIGH",
            "State swap accepted. This is correct server-side behavior: "
            "OAuth2 state parameter is for client-side CSRF protection only. "
            "The authorization server does not validate state.",
            {},
            spec_reference="RFC 6749 Section 4.1.1 (state is recommended, not required)",
        )
