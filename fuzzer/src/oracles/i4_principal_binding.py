"""I4 Principal Binding Oracle — identity claim validation and type confusion."""

from __future__ import annotations

from src.models.types import AuthResult, Invariant, MutationRecord, Verdict, VerdictType
from src.oracles.base import SecurityOracle


class I4PrincipalBindingOracle(SecurityOracle):

    def __init__(self, invariant: Invariant = Invariant.I4_PRINCIPAL_BINDING):
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

        # --- LDAP injection checks ---
        if mt == "i4_dn_injection":
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "LDAP DN injection succeeded. Special characters in the DN "
                "were not properly escaped.",
                {},
            )

        if mt == "i4_null_byte_injection":
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "Null byte injection succeeded. Null bytes in identity values "
                "indicate improper input sanitization.",
                {},
            )

        if mt == "i4_wildcard_filter":
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "Wildcard as username matched in LDAP filter. "
                "LDAP search filter must not allow wildcard matching for authentication.",
                {},
            )

        if mt == "i4_unicode_normalization":
            return self._verdict(
                VerdictType.UNEXPECTED, "MEDIUM",
                "Unicode confusable character accepted in LDAP authentication. "
                "Check if the platform normalizes Unicode before comparison.",
                {},
                requires_manual_review=True,
            )

        # --- Type confusion checks (delegate to same CVE-2024-5798 logic) ---
        if mt.startswith("i4_sub_type_") or mt.startswith("i4_groups_type_"):
            # groups_type_string is BY_DESIGN: normalizeList() (claims.go:171-187)
            # intentionally converts single strings to single-element lists for
            # IdP compatibility (Google, Azure AD return "group" instead of ["group"]
            # when list has one element). The resulting group alias is identical
            # regardless of string vs list input. No security impact.
            if mt == "i4_groups_type_string":
                return self._verdict(
                    VerdictType.BY_DESIGN, "HIGH",
                    f"Groups claim accepted as string instead of list. This is "
                    f"BY_DESIGN: normalizeList() (claims.go:171-187) converts "
                    f"single strings to single-element lists for IdP compatibility "
                    f"(many IdPs return a bare string when groups has one element). "
                    f"The resulting group alias is identical.",
                    {"mutation_type": mt, "reason": "normalizeList_idp_compat"},
                )
            # If the role has no groups_claim configured, group type mutations
            # are irrelevant — the platform ignores the groups claim entirely.
            if mt.startswith("i4_groups_type_"):
                role_config = (context or {}).get("role_config", {})
                groups_claim = role_config.get("groups_claim")
                if not groups_claim:
                    return self._verdict(
                        VerdictType.BY_DESIGN, "HIGH",
                        f"Groups type mutation {mt} accepted, but groups_claim is "
                        f"not configured on the role. Platform ignores groups claim "
                        f"entirely — acceptance is expected regardless of type.",
                        {"mutation_type": mt, "groups_claim": groups_claim},
                    )
            return self._check_type_confusion(mutation, auth_result, context)

        # --- Claim constraint precondition ---
        # If no bound_claims/claim_constraints are configured on the role,
        # the platform does not enforce claim-level restrictions. Any claim
        # mutation trivially passes — this is BY_DESIGN (no constraint to bypass).
        if mt.startswith("i4_bound_claims"):
            role_config = (context or {}).get("role_config", {})
            bound_claims = (role_config.get("bound_claims")
                            or role_config.get("claim_constraints")
                            or {})
            if not bound_claims:
                return self._verdict(
                    VerdictType.BY_DESIGN, "HIGH",
                    f"Claim mutation {mt} accepted, but no bound_claims are "
                    f"configured on the role. Without claim constraints, any "
                    f"claim value is accepted. This is a configuration choice, "
                    f"not a vulnerability.",
                    {"mutation_type": mt, "bound_claims": {}},
                )

            # Check if the mutated claim field is actually constrained by
            # bound_claims.  Mutations like i4_bound_claims_glob_star inject
            # a hardcoded claim (e.g. "department") that may not appear in
            # the role's bound_claims.  The platform only evaluates claims
            # listed in bound_claims — unlisted claims are ignored by design.
            mutated_field = self._extract_mutated_claim_field(mutation)
            if mutated_field and bound_claims:
                bc_keys = set(bound_claims.keys()) if isinstance(bound_claims, dict) else set()
                if bc_keys and mutated_field not in bc_keys:
                    return self._verdict(
                        VerdictType.BY_DESIGN, "HIGH",
                        f"Claim mutation {mt} accepted, but the mutated claim "
                        f"field '{mutated_field}' is not in the role's "
                        f"bound_claims ({sorted(bc_keys)}). The platform only "
                        f"evaluates claims listed in bound_claims — unlisted "
                        f"claims are ignored by design.",
                        {"mutation_type": mt, "mutated_field": mutated_field,
                         "bound_claims_keys": sorted(bc_keys)},
                    )

        # --- Glob injection checks ---
        if mt in ("i4_bound_claims_glob_star", "i4_bound_claims_glob_question",
                   "i4_bound_claims_glob_bracket"):
            role_config = (context or {}).get("role_config", {})
            bct = (role_config.get("bound_claims_type")
                   or role_config.get("claim_constraint_type")
                   or "")
            if bct == "glob":
                return self._verdict(
                    VerdictType.BY_DESIGN, "HIGH",
                    f"Glob wildcard {mt} accepted, but bound_claims_type='glob' "
                    f"is configured. Glob pattern matching is the admin-intended "
                    f"behavior for this role.",
                    {"mutation_type": mt, "bound_claims_type": "glob"},
                )
            return self._check_glob_injection(mutation, auth_result, context)

        if mt == "i4_bound_claims_empty_value":
            # Check the role's bound_claims config: if the bound value is also
            # empty string, this is an exact match ("" == ""), not a bypass.
            # Check both field names: bound_claims (native) and claim_constraints (profile)
            role_config = (context or {}).get("role_config", {})
            bound_claims = (role_config.get("bound_claims")
                            or role_config.get("claim_constraints")
                            or {})
            # If any bound claim value is empty string, empty-to-empty match is expected
            has_empty_bound = any(
                v == "" or v == [] for v in bound_claims.values()
            ) if bound_claims else False
            if has_empty_bound:
                return self._verdict(
                    VerdictType.BY_DESIGN, "HIGH",
                    "Empty string claim value matched bound_claims where the "
                    "configured bound value is also empty. Exact match of "
                    "empty-to-empty is correct behavior, not a bypass.",
                    {"bound_claims": bound_claims},
                )
            return self._verdict(
                VerdictType.UNEXPECTED, "HIGH",
                "Empty string claim value matched bound_claims. "
                "This might be intentional (exact match of empty to empty) "
                "or might indicate 'empty matches everything' (CVE-2024-7594 pattern).",
                {},
                cve_pattern="CVE-2024-7594",
                requires_manual_review=True,
            )

        # --- Config-change mutations ---
        if mt.endswith("_config") or mt == "i4_user_claim_nonexistent_field":
            return self._check_config_change(mutation, auth_result, context)

        # --- Identity comparison checks ---
        if mt in ("i4_sub_overwrite", "i4_email_overwrite", "i4_groups_escalation"):
            return self._check_identity_overwrite(mutation, auth_result, context)

        if mt == "i4_claim_in_header":
            return self._verdict(
                VerdictType.UNEXPECTED, "HIGH",
                "Token with identity claim in header accepted. "
                "Reviewer must verify whether the platform used the header or "
                "payload value for downstream identity. JWT headers are not "
                "integrity-protected in the same way as payload claims.",
                {},
                requires_manual_review=True,
            )

        if mt in ("i4_unicode_collision", "i4_case_confusion"):
            return self._verdict(
                VerdictType.UNEXPECTED, "MEDIUM",
                f"Identity mutation {mt} accepted. Check if the platform "
                f"normalized the identity or mapped it to a different entity.",
                {},
                requires_manual_review=True,
            )

        if mt == "i4_subject_nfd_nfc_normalization":
            return self._check_nfd_nfc(mutation, auth_result, context)

        # SAML-specific
        if mt == "i4_nameid_from_attribute":
            return self._verdict(
                VerdictType.UNEXPECTED, "MEDIUM",
                "NameID derived from SAML attribute accepted. "
                "Check attribute-to-identity mapping.",
                {},
                requires_manual_review=True,
            )

        if mt == "i4_dual_assertion_identity":
            return self._verdict(
                VerdictType.UNEXPECTED, "HIGH",
                "Dual assertion with conflicting identities accepted. "
                "Platform should reject or consistently pick one.",
                {},
                requires_manual_review=True,
            )

        return self._verdict(
            VerdictType.ERROR, "LOW",
            f"Unhandled I4 mutation: {mt}", {},
        )

    # ------------------------------------------------------------------
    # Type confusion (same CVE-2024-5798 pattern as I5)
    # ------------------------------------------------------------------

    def _check_type_confusion(
        self, mutation: MutationRecord, auth_result: AuthResult, context: dict | None,
    ) -> Verdict:
        claim_name = self._extract_confused_claim(mutation.mutation_type)
        claim_value = None
        if mutation.mutated and hasattr(mutation.mutated, "claims"):
            claim_value = mutation.mutated.claims.get(claim_name)
        claim_type = type(claim_value).__name__

        expected_types = {
            "sub": ["str"],
            "groups": ["list"],
        }
        valid_types = expected_types.get(claim_name, ["str"])

        if claim_type in valid_types:
            return self._verdict(
                VerdictType.BY_DESIGN, "HIGH",
                f"Claim '{claim_name}' accepted with expected type {claim_type}",
                {"claim": claim_name, "type": claim_type,
                 "value_repr": repr(claim_value)},
            )

        severity_map = {
            "NoneType": ("VIOLATION", "HIGH"),
            "bool": ("VIOLATION", "HIGH"),
            "int": ("VIOLATION", "HIGH"),
            "float": ("VIOLATION", "HIGH"),
            "dict": ("VIOLATION", "HIGH"),
        }
        verdict_type_str, confidence = severity_map.get(
            claim_type, ("UNEXPECTED", "MEDIUM"),
        )

        # Check list with non-string elements
        if claim_type == "list" and claim_value:
            non_string_elements = [v for v in claim_value if not isinstance(v, str)]
            if non_string_elements:
                return self._verdict(
                    VerdictType.VIOLATION, "HIGH",
                    f"Claim '{claim_name}' accepted as array containing non-string "
                    f"elements: {[type(v).__name__ for v in non_string_elements]}.",
                    {"claim": claim_name, "type": claim_type,
                     "value": repr(claim_value),
                     "non_string_types": [type(v).__name__ for v in non_string_elements]},
                    cve_pattern="CVE-2024-5798",
                )

        # String accepted for groups is a type confusion
        if claim_type == "str" and claim_name == "groups":
            verdict_type_str = "VIOLATION"
            confidence = "HIGH"

        return self._verdict(
            VerdictType(verdict_type_str), confidence,
            f"Claim '{claim_name}' accepted with non-standard type '{claim_type}'. "
            f"Expected types: {valid_types}. CVE-2024-5798 pattern.",
            {"claim": claim_name, "expected_types": valid_types,
             "actual_type": claim_type, "value_repr": repr(claim_value)},
            cve_pattern="CVE-2024-5798",
        )

    def _extract_confused_claim(self, mutation_type: str) -> str:
        if "sub" in mutation_type:
            return "sub"
        if "groups" in mutation_type:
            return "groups"
        return "unknown"

    # ------------------------------------------------------------------
    # Glob injection
    # ------------------------------------------------------------------

    def _check_glob_injection(
        self, mutation: MutationRecord, auth_result: AuthResult, context: dict | None,
    ) -> Verdict:
        return self._verdict(
            VerdictType.VIOLATION, "HIGH",
            f"Glob wildcard injection ({mutation.mutation_type}) accepted. "
            "The claim value contained a glob wildcard that matched the "
            "bound_claims pattern. This means matching logic treats claim "
            "values as patterns, not literals.",
            {},
            cve_pattern="CVE-2025-11621",
        )

    # ------------------------------------------------------------------
    # Config changes
    # ------------------------------------------------------------------

    def _check_config_change(
        self, mutation: MutationRecord, auth_result: AuthResult, context: dict | None,
    ) -> Verdict:
        config_change = mutation.metadata.get("config_change", {})

        for field_name, value in config_change.items():
            if value is None or value == [] or value == {} or value == "":
                return self._verdict(
                    VerdictType.UNEXPECTED, "HIGH",
                    f"Authentication succeeded with {field_name}={repr(value)} (empty/unset). "
                    f"CVE-2024-7594 pattern: empty config may mean 'allow all'.",
                    {"config_field": field_name, "config_value": repr(value)},
                    cve_pattern="CVE-2024-7594",
                    requires_manual_review=True,
                )

        return self._verdict(
            VerdictType.UNEXPECTED, "MEDIUM",
            f"Config-change mutation {mutation.mutation_type} accepted.",
            {"config_change": config_change},
            requires_manual_review=True,
        )

    # ------------------------------------------------------------------
    # NFC/NFD Unicode normalization
    # ------------------------------------------------------------------

    def _check_nfd_nfc(
        self, mutation: MutationRecord, auth_result: AuthResult, context: dict | None,
    ) -> Verdict:
        """Subject in NFD form accepted — check if it mapped to the same
        identity as the NFC baseline.

        Per RFC 7613 (PRECIS), identity strings should be normalized
        before comparison. If NFC and NFD forms map to different entities,
        this is a principal binding violation (same logical user gets
        two different identities).
        """
        baseline_captures = (context or {}).get("baseline_captures", {})
        mutation_captures = (context or {}).get("mutation_captures", {})
        baseline_entity = baseline_captures.get("entity_id")
        mutation_entity = mutation_captures.get("entity_id")

        if baseline_entity and mutation_entity:
            if baseline_entity == mutation_entity:
                return self._verdict(
                    VerdictType.BY_DESIGN, "HIGH",
                    "NFD-form subject mapped to same entity as NFC baseline. "
                    "Platform correctly normalizes Unicode before identity comparison.",
                    {"baseline_entity": baseline_entity, "mutation_entity": mutation_entity},
                    spec_reference="RFC 7613 (PRECIS Framework)",
                )
            else:
                return self._verdict(
                    VerdictType.UNEXPECTED, "HIGH",
                    "NFD-form subject mapped to DIFFERENT entity than NFC baseline. "
                    "Platform may not normalize Unicode before identity comparison, "
                    "allowing the same logical user to have multiple identities.",
                    {"baseline_entity": baseline_entity, "mutation_entity": mutation_entity},
                    spec_reference="RFC 7613 (PRECIS Framework)",
                    requires_manual_review=True,
                )

        return self._verdict(
            VerdictType.UNEXPECTED, "MEDIUM",
            "NFD-form subject accepted. Manual review needed to verify "
            "whether NFC and NFD forms map to the same or different identities.",
            {},
            spec_reference="RFC 7613 (PRECIS Framework)",
            requires_manual_review=True,
        )

    # ------------------------------------------------------------------
    # Identity overwrite
    # ------------------------------------------------------------------

    def _check_identity_overwrite(
        self, mutation: MutationRecord, auth_result: AuthResult, context: dict | None,
    ) -> Verdict:
        return self._verdict(
            VerdictType.BY_DESIGN, "HIGH",
            f"Identity mutation {mutation.mutation_type} accepted. "
            "The JWT is signed by the trusted IdP, which is the authority on "
            "identity claims. Only flag if downstream identity/permissions "
            "differ from what the platform's claim mapping should produce.",
            {},
            requires_manual_review=True,
        )

    # ------------------------------------------------------------------
    # Mutated claim field extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_mutated_claim_field(mutation: MutationRecord) -> str | None:
        """Determine which JWT claim field was actually mutated.

        Checks mutation metadata first, then inspects the mutated credential's
        claims to find the injected/changed field.  Falls back to well-known
        defaults for hardcoded mutation functions.
        """
        # 1. Explicit metadata (set by smarter engines)
        field = (mutation.metadata or {}).get("mutated_claim_field")
        if field:
            return field

        # 2. Compare baseline vs mutated claims if available
        if (mutation.baseline and mutation.mutated
                and hasattr(mutation.baseline, "claims")
                and hasattr(mutation.mutated, "claims")):
            baseline_claims = mutation.baseline.claims or {}
            mutated_claims = mutation.mutated.claims or {}
            # New fields not in baseline
            for k in mutated_claims:
                if k not in baseline_claims:
                    return k
            # Changed fields
            for k in mutated_claims:
                if k in baseline_claims and mutated_claims[k] != baseline_claims[k]:
                    # Skip standard JWT fields — mutations on these are identity mutations
                    if k in ("sub", "iss", "aud", "exp", "iat", "nbf", "jti", "nonce"):
                        continue
                    return k

        # 3. Well-known defaults for hardcoded mutations
        mt = mutation.mutation_type
        if mt in ("i4_bound_claims_glob_star", "i4_bound_claims_glob_question",
                   "i4_bound_claims_glob_bracket", "i4_bound_claims_empty_value"):
            return "department"
        if mt == "i5_bound_claim_numeric_type_coercion":
            return "department_id"

        return None
