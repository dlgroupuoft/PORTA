"""I1 Proof Integrity Oracle — signature, key trust, and canonicalization checks."""

from __future__ import annotations

from src.models.types import AuthResult, Invariant, MutationRecord, Verdict, VerdictType
from src.oracles.base import SecurityOracle


class I1ProofIntegrityOracle(SecurityOracle):

    def __init__(self, invariant: Invariant = Invariant.I1_PROOF_INTEGRITY):
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

        # --- Clear-cut automated checks ---
        if mt == "i1_alg_none":
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "Token with alg=none accepted. The platform MUST reject unsigned tokens.",
                {},
                spec_reference="RFC 7518 Section 3.6",
            )

        if mt == "i1_alg_confusion_rs256_to_hs256":
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "Algorithm confusion attack succeeded. Platform accepted HMAC signature "
                "using the RSA public key as the HMAC secret.",
                {},
                cve_pattern="CVE-2016-10555",
            )

        if mt == "i1_resign_attacker_key":
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "Token signed with untrusted attacker key accepted. "
                "The platform failed to validate the signing key against its trust store.",
                {},
                cve_pattern="CVE-2025-49831",
            )

        if mt == "i1_trust_anchor_substitution":
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "Trust anchor substitution succeeded. Attacker-supplied signing "
                "material was accepted.",
                {},
                cve_pattern="CVE-2025-49831",
            )

        if mt == "i1_kid_injection":
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "kid header injection accepted. The platform selected a key based "
                "on an attacker-controlled kid value.",
                {},
            )

        if mt == "i1_jwks_url_injection":
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "jku/x5u header injection accepted. The platform fetched keys from "
                "an attacker-controlled URL.",
                {},
            )

        # --- XSW variants ---
        if mt.startswith("i1_xsw_"):
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                f"XML Signature Wrapping ({mt}) attack succeeded. "
                "The platform processed the unsigned/malicious assertion. "
                "Reviewer must verify that the authenticated identity matches "
                "the malicious NameID, not the legitimate signed one.",
                {},
                cve_pattern="Dex-CVE-2020-27847",
                requires_manual_review=True,
            )

        # --- SAML signature bypass ---
        if mt == "i1_unsigned_assertion_in_signed_response":
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "Unsigned assertion in signed response accepted. "
                "Platform verified response signature but did not require "
                "assertion-level signature.",
                {},
            )

        if mt == "i1_resign_attacker_cert":
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "SAML assertion signed with attacker certificate accepted. "
                "Platform failed to validate the signing certificate.",
                {},
                cve_pattern="CVE-2025-49831",
            )

        if mt == "i1_dtd_entity_expansion":
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "DTD entity expansion accepted. XML external entity processing "
                "was not disabled.",
                {},
            )

        if mt == "i1_comment_injection":
            return self._verdict(
                VerdictType.UNEXPECTED, "MEDIUM",
                "XML comment injection accepted. Check if comments affected "
                "signature verification or identity extraction.",
                {},
                requires_manual_review=True,
            )

        if mt == "i1_encoding_divergence":
            return self._verdict(
                VerdictType.UNEXPECTED, "MEDIUM",
                "Encoding divergence accepted. The signed content uses different "
                "encoding than what the platform consumed.",
                {},
                requires_manual_review=True,
            )

        # --- Canonicalization divergence checks (NEW) ---
        if mt == "i1_saml_comment_in_nameid":
            return self._check_comment_in_nameid(mutation, auth_result, context)

        if mt == "i1_saml_whitespace_in_nameid":
            return self._check_whitespace_in_nameid(mutation, auth_result, context)

        if mt == "i1_saml_namespace_prefix_manipulation":
            return self._verdict(
                VerdictType.UNEXPECTED, "MEDIUM",
                "SAML assertion with non-standard namespace prefixes accepted. "
                "XML canonicalization should handle prefix variations, but edge "
                "cases may exist.",
                {},
                requires_manual_review=True,
            )

        if mt == "i1_saml_multiple_nameid":
            return self._verdict(
                VerdictType.UNEXPECTED, "HIGH",
                "SAML assertion with multiple NameID elements accepted. "
                "Only one NameID should be present per Subject. Platform may "
                "pick the first or last, leading to identity confusion.",
                {},
                requires_manual_review=True,
            )

        if mt == "i1_saml_attribute_value_type":
            return self._verdict(
                VerdictType.UNEXPECTED, "MEDIUM",
                "SAML attribute with non-string xsi:type accepted. "
                "Check if type annotation affects attribute processing.",
                {},
                cve_pattern="CVE-2024-5798",
                requires_manual_review=True,
            )

        # --- URL canonicalization checks ---
        # If bound_issuer is not configured, issuer mutations are expected to pass —
        # the platform has no issuer constraint to enforce.
        if mt.startswith("i1_iss_"):
            role_config = (context or {}).get("role_config", {})
            bound_issuer = role_config.get("bound_issuer") or ""
            if not bound_issuer:
                return self._verdict(
                    VerdictType.BY_DESIGN, "HIGH",
                    f"Issuer mutation {mt} accepted, but bound_issuer is not "
                    f"configured on the role. Without an issuer constraint, "
                    f"any issuer value is accepted — this is a configuration choice, "
                    f"not a vulnerability.",
                    {"mutation_type": mt, "bound_issuer": bound_issuer},
                )

        if mt == "i1_iss_trailing_slash":
            return self._verdict(
                VerdictType.UNEXPECTED, "MEDIUM",
                "Token with trailing slash in iss accepted. The iss does not match "
                "bound_issuer literally. Either the platform normalizes URLs "
                "(potentially intended) or the iss check has a canonicalization flaw.",
                {},
                requires_manual_review=True,
            )

        if mt == "i1_iss_case_variation":
            return self._verdict(
                VerdictType.UNEXPECTED, "MEDIUM",
                "Token with case-varied iss accepted. DNS is case-insensitive "
                "but iss comparison should be case-sensitive per RFC 7519 "
                "Section 4.1.1 (StringOrURI value, compared as-is).",
                {},
                spec_reference="RFC 7519 Section 4.1.1",
                requires_manual_review=True,
            )

        if mt == "i1_iss_unicode_homoglyph":
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "Token with unicode homoglyph in iss accepted and signed with "
                "attacker key. The platform accepted a token from a visually "
                "similar but different issuer, validated against attacker-controlled keys.",
                {},
                cve_pattern="URL confusion",
            )

        if mt == "i1_iss_port_variation":
            return self._verdict(
                VerdictType.UNEXPECTED, "MEDIUM",
                "Token with explicit default port in iss accepted. "
                "http://host:80 and http://host should be equivalent per URL spec "
                "but string comparison would reject.",
                {},
                requires_manual_review=True,
            )

        if mt == "i1_iss_path_traversal":
            return self._verdict(
                VerdictType.UNEXPECTED, "MEDIUM",
                "Token with path traversal in iss accepted. The iss contains "
                "/../ sequences that may be resolved differently by different parsers.",
                {},
                requires_manual_review=True,
            )

        # --- HTTP header injection ---
        if mt.startswith("i1_http_header_injection"):
            return self._check_header_injection(mutation, auth_result, context)

        # --- SAML Issuer validation ---
        if mt == "i1_saml_issuer_mismatch":
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "SAML assertion with untrusted Issuer entity ID accepted. "
                "Platform failed to validate the assertion's Issuer against the "
                "configured trusted IdP entity ID.",
                {},
                spec_reference="SAML Core 2.0 Section 2.3.3",
            )

        if mt == "i1_saml_issuer_empty":
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "SAML assertion with empty Issuer accepted. Platform must require "
                "a non-empty Issuer matching the trusted IdP.",
                {},
                spec_reference="SAML Core 2.0 Section 2.3.3",
            )

        # --- SAML spurious/detached signature ---
        if mt == "i1_saml_spurious_signature":
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "SAML Response accepted with Signature covering only the Response "
                "envelope while the assertion itself is unsigned. A conformant SP "
                "must verify assertion-level integrity, not just that a Signature "
                "element exists somewhere in the document.",
                {},
            )

        return self._verdict(
            VerdictType.ERROR, "LOW",
            f"Unhandled I1 mutation: {mt}", {},
        )

    # ------------------------------------------------------------------
    # Canonicalization divergence helpers
    # ------------------------------------------------------------------

    def _check_comment_in_nameid(
        self, mutation: MutationRecord, auth_result: AuthResult, context: dict | None,
    ) -> Verdict:
        downstream_identity = (context or {}).get("downstream_identity", "")

        if "<!--" in downstream_identity:
            return self._verdict(
                VerdictType.BY_DESIGN, "HIGH",
                "Comment preserved in downstream identity. The platform passed "
                "through the comment as part of the NameID value.",
                {"downstream_identity": downstream_identity},
            )

        # Comment was stripped — canonicalization divergence
        return self._verdict(
            VerdictType.VIOLATION, "MEDIUM",
            "SAML NameID comment stripped after signature validation. "
            "Signed content included comment, consumed content did not. "
            "Canonicalization divergence between signature verification "
            "and identity extraction.",
            {"downstream_identity": downstream_identity},
            requires_manual_review=True,
        )

    def _check_whitespace_in_nameid(
        self, mutation: MutationRecord, auth_result: AuthResult, context: dict | None,
    ) -> Verdict:
        downstream_identity = (context or {}).get("downstream_identity", "")

        if downstream_identity and downstream_identity != downstream_identity.strip():
            return self._verdict(
                VerdictType.BY_DESIGN, "HIGH",
                "Whitespace preserved in downstream identity.",
                {"downstream_identity": downstream_identity},
            )

        return self._verdict(
            VerdictType.UNEXPECTED, "MEDIUM",
            "Whitespace stripped from NameID after signature validation. "
            "The consumed identity differs from the signed identity.",
            {"downstream_identity": downstream_identity},
            requires_manual_review=True,
        )

    # ------------------------------------------------------------------
    # HTTP header injection
    # ------------------------------------------------------------------

    def _check_header_injection(
        self, mutation: MutationRecord, auth_result: AuthResult, context: dict | None,
    ) -> Verdict:
        """Check if the platform actually used injected HTTP proxy headers
        for identity determination, or if it simply authenticated via the
        JWT/SAML credential (ignoring the headers).

        If the granted identity matches the JWT subject (not the injected
        header values), the headers were irrelevant — the platform
        authenticated via the credential, not the headers.
        """
        # If auth_context is JWT_BEARER or SAML_BEARER, proxy headers are
        # irrelevant — the platform authenticates via the credential, not headers.
        # Check this FIRST to avoid false VIOLATION when header values can't
        # be extracted from the mutation record.
        auth_context_str = (context or {}).get("auth_context", "")
        if auth_context_str in ("JWT_BEARER", "SAML_BEARER"):
            return self._verdict(
                VerdictType.BY_DESIGN, "HIGH",
                f"HTTP proxy headers injected alongside a valid {auth_context_str} "
                f"credential. The platform authenticates via the credential, not "
                f"proxy headers. X-Remote-User/X-Forwarded-User are only relevant "
                f"for proxy-based auth backends.",
                {"auth_context": auth_context_str, "mutation_type": mutation.mutation_type},
            )

        # Extract the injected identity from mutation headers
        injected_headers = {}
        if hasattr(mutation, 'mutated') and mutation.mutated:
            injected_headers = getattr(mutation.mutated, 'headers', {}) or {}

        injected_identity = (
            injected_headers.get("X-Remote-User")
            or injected_headers.get("X-Forwarded-User")
            or injected_headers.get("X-Remote-Email")
            or injected_headers.get("X-Forwarded-Email")
            or ""
        )

        # Extract the JWT subject from the credential
        jwt_sub = ""
        if hasattr(mutation, 'mutated') and mutation.mutated:
            claims = getattr(mutation.mutated, 'claims', {}) or {}
            jwt_sub = str(claims.get("sub", ""))

        # Extract the granted identity from downstream
        granted_id = ""
        if auth_result.downstream_claims:
            granted_id = str(
                auth_result.downstream_claims.get("entity_name", "")
                or auth_result.downstream_claims.get("display_name", "")
                or auth_result.downstream_claims.get("entity_id", "")
                or ""
            )

        # If we have both an injected identity and a JWT sub, compare
        if injected_identity and jwt_sub:
            # Normalize for comparison
            injected_lower = injected_identity.lower()
            jwt_sub_lower = jwt_sub.lower()

            # If granted identity does NOT match the injected header but
            # does match the JWT sub, headers were ignored — BY_DESIGN.
            if granted_id:
                granted_lower = granted_id.lower()
                if injected_lower not in granted_lower and (
                    jwt_sub_lower in granted_lower or granted_lower in jwt_sub_lower
                ):
                    return self._verdict(
                        VerdictType.BY_DESIGN, "HIGH",
                        f"HTTP proxy headers were injected (X-Remote-User={injected_identity}) "
                        f"but the platform authenticated via the JWT credential "
                        f"(sub={jwt_sub}), not the headers. The granted identity "
                        f"matches the JWT subject, indicating the platform does not "
                        f"trust proxy headers for identity determination.",
                        {"injected_identity": injected_identity,
                         "jwt_sub": jwt_sub, "granted_id": granted_id},
                    )

            # Even without granted_id: if the platform is JWT-based and login
            # succeeded with a valid JWT, the headers are likely irrelevant.
            # The JWT was validly signed and the platform authenticated it.
            auth_context_str = (context or {}).get("auth_context", "")
            if auth_context_str in ("JWT_BEARER", "SAML_BEARER"):
                return self._verdict(
                    VerdictType.BY_DESIGN, "HIGH",
                    f"HTTP proxy headers were injected alongside a valid "
                    f"{auth_context_str} credential. The platform authenticated "
                    f"via the credential (not proxy headers). Headers like "
                    f"X-Remote-User are only relevant for proxy-based auth "
                    f"backends, not JWT/SAML login endpoints.",
                    {"injected_identity": injected_identity,
                     "jwt_sub": jwt_sub, "auth_context": auth_context_str},
                )

        # Fallback: cannot determine — flag for review
        return self._verdict(
            VerdictType.VIOLATION, "HIGH",
            "Platform accepted identity from injected HTTP proxy headers "
            "(X-Remote-User, X-Forwarded-User, X-Remote-Group, etc.). "
            "These headers should only be trusted from authenticated upstream "
            "proxies, not from direct client connections. An attacker can "
            "impersonate any user by setting these headers.",
            {"injected_headers": injected_headers},
        )
