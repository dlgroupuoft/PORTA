"""I5 Authorization Binding Oracle — type confusion and audience validation."""

from __future__ import annotations

from src.models.types import AuthResult, Invariant, MutationRecord, Verdict, VerdictType
from src.oracles.base import SecurityOracle


class I5AuthorizationBindingOracle(SecurityOracle):

    def __init__(self, invariant: Invariant = Invariant.I5_AUTHORIZATION_BINDING):
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
        if not auth_result.success:
            return self._rejected(mutation.mutation_type, auth_result.error_message)

        mutation_type = mutation.mutation_type

        # Type confusion mutations (CVE-2024-5798 pattern)
        if mutation_type.startswith("i5_aud_type_") or mutation_type.startswith("i4_groups_type_"):
            # groups_type_string is BY_DESIGN: normalizeList() compatibility
            if mutation_type == "i4_groups_type_string":
                return self._verdict(
                    VerdictType.BY_DESIGN, "HIGH",
                    f"Groups claim accepted as string instead of list. BY_DESIGN: "
                    f"normalizeList() converts strings to lists for IdP compatibility.",
                    {"mutation_type": mutation_type, "reason": "normalizeList_idp_compat"},
                )
            # If the role has no groups_claim configured, group type mutations
            # are irrelevant — the platform ignores the groups claim entirely.
            if mutation_type.startswith("i4_groups_type_"):
                role_config = (context or {}).get("role_config", {})
                groups_claim = role_config.get("groups_claim")
                if not groups_claim:
                    return self._verdict(
                        VerdictType.BY_DESIGN, "HIGH",
                        f"Groups type mutation {mutation_type} accepted, but "
                        f"groups_claim is not configured on the role. Platform "
                        f"ignores groups claim — acceptance is expected.",
                        {"mutation_type": mutation_type, "groups_claim": groups_claim},
                    )
            return self._check_type_confusion(mutation, auth_result, context)

        # Config semantics mutations (CVE-2024-7594 pattern)
        if mutation_type.endswith("_config"):
            return self._check_config_semantics(mutation, auth_result, context)

        # SAML audience/conditions mutations
        if mutation_type in ("i5_saml_no_conditions", "i5_saml_no_audience_restriction"):
            return self._check_saml_audience_missing(mutation, auth_result, context)

        if mutation_type == "i5_saml_wrong_audience":
            return self._check_saml_wrong_audience(mutation, auth_result, context)

        # Token exchange with wrong/missing audience
        if mutation_type in ("i5_token_exchange_wrong_audience",
                             "i5_token_exchange_no_audience"):
            return self._check_token_exchange_audience(mutation, auth_result, context)

        # Numeric type coercion on bound claims
        if mutation_type == "i5_bound_claim_numeric_type_coercion":
            # First check if the mutated claim is actually in bound_claims.
            # If not, the platform ignores it — acceptance is expected.
            mutated_field = self._extract_mutated_claim_field(mutation)
            if mutated_field:
                role_config = (context or {}).get("role_config", {})
                bound_claims = (role_config.get("bound_claims")
                                or role_config.get("claim_constraints")
                                or {})
                if bound_claims and isinstance(bound_claims, dict):
                    bc_keys = set(bound_claims.keys())
                    if mutated_field not in bc_keys:
                        return self._verdict(
                            VerdictType.BY_DESIGN, "HIGH",
                            f"Numeric type coercion mutation accepted, but the "
                            f"mutated claim field '{mutated_field}' is not in "
                            f"the role's bound_claims ({sorted(bc_keys)}). The "
                            f"platform only evaluates claims listed in "
                            f"bound_claims — unlisted claims are ignored.",
                            {"mutation_type": mutation_type,
                             "mutated_field": mutated_field,
                             "bound_claims_keys": sorted(bc_keys)},
                        )
            return self._check_numeric_type_coercion(mutation, auth_result, context)

        # Legacy audience checks
        if mutation_type in ("i5_aud_wrong", "i5_aud_empty", "i5_aud_missing"):
            return self._check_audience_legacy(mutation, auth_result, context)

        if mutation_type == "i5_aud_array_with_extra":
            return self._check_audience_array(mutation, auth_result, context)

        # Scope mutations
        if mutation_type in ("i5_scope_inflation", "i5_scope_empty"):
            return self._check_scope(mutation, auth_result, context)

        return self._verdict(
            VerdictType.ERROR, "LOW",
            f"Unhandled I5 mutation: {mutation_type}", {},
        )

    # ------------------------------------------------------------------
    # Type confusion (CVE-2024-5798 pattern)
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
            "aud": ["str", "list"],
            "groups": ["list"],
            "sub": ["str"],
        }
        valid_types = expected_types.get(claim_name, ["str"])

        # Check list with non-string elements BEFORE the valid_types check,
        # because list is a valid type for aud/groups but non-string elements are not.
        if claim_type == "list" and claim_value:
            non_string_elements = [v for v in claim_value if not isinstance(v, str)]
            if non_string_elements:
                return self._verdict(
                    VerdictType.VIOLATION, "HIGH",
                    f"Claim '{claim_name}' accepted as array containing non-string "
                    f"elements: {[type(v).__name__ for v in non_string_elements]}. "
                    f"This indicates incomplete type validation, similar to CVE-2024-5798 "
                    f"where string vs array handling was incomplete.",
                    {"claim": claim_name, "type": claim_type,
                     "value": repr(claim_value),
                     "non_string_types": [type(v).__name__ for v in non_string_elements]},
                    cve_pattern="CVE-2024-5798",
                    spec_reference="RFC 7519 Section 4.1.3 (aud must be StringOrURI)",
                )

        if claim_type in valid_types:
            return self._verdict(
                VerdictType.BY_DESIGN, "HIGH",
                f"Claim '{claim_name}' accepted with expected type {claim_type}",
                {"claim": claim_name, "type": claim_type,
                 "value_repr": repr(claim_value)},
            )

        # Accepted with UNEXPECTED type
        severity_map = {
            "NoneType": ("VIOLATION", "HIGH"),
            "bool": ("VIOLATION", "HIGH"),
            "int": ("VIOLATION", "HIGH"),
            "float": ("VIOLATION", "HIGH"),
            "dict": ("VIOLATION", "HIGH"),
            "str": ("VIOLATION", "HIGH"),  # string when list expected (groups)
        }
        verdict_type_str, confidence = severity_map.get(
            claim_type, ("UNEXPECTED", "MEDIUM"),
        )

        spec_ref = "RFC 7519 Section 4.1.3" if claim_name == "aud" else ""
        return self._verdict(
            VerdictType(verdict_type_str), confidence,
            f"Claim '{claim_name}' accepted with non-standard type '{claim_type}'. "
            f"Expected types: {valid_types}. This may indicate incomplete type "
            f"handling in claim validation (CVE-2024-5798 pattern).",
            {"claim": claim_name, "expected_types": valid_types,
             "actual_type": claim_type, "value_repr": repr(claim_value)},
            cve_pattern="CVE-2024-5798",
            spec_reference=spec_ref,
        )

    def _extract_confused_claim(self, mutation_type: str) -> str:
        if "aud" in mutation_type:
            return "aud"
        if "groups" in mutation_type:
            return "groups"
        if "sub" in mutation_type:
            return "sub"
        return "unknown"

    # ------------------------------------------------------------------
    # Config semantics (CVE-2024-7594 pattern)
    # ------------------------------------------------------------------

    def _check_config_semantics(
        self, mutation: MutationRecord, auth_result: AuthResult, context: dict | None,
    ) -> Verdict:
        config_change = mutation.metadata.get("config_change", {})

        for field_name, value in config_change.items():
            if value is None or value == [] or value == {} or value == "":
                return self._verdict(
                    VerdictType.UNEXPECTED, "HIGH",
                    f"Authentication succeeded with {field_name}={repr(value)} (empty/unset). "
                    f"This might mean empty config acts as 'allow all' rather than "
                    f"'deny all'. Similar to CVE-2024-7594 where empty valid_principals "
                    f"meant 'any principal'. Requires manual verification of intended behavior.",
                    {"config_field": field_name, "config_value": repr(value)},
                    cve_pattern="CVE-2024-7594",
                    requires_manual_review=True,
                )

        return self._verdict(
            VerdictType.BY_DESIGN, "HIGH",
            "Config change did not result in unexpected acceptance", {},
        )

    # ------------------------------------------------------------------
    # SAML audience/conditions
    # ------------------------------------------------------------------

    def _check_saml_audience_missing(
        self, mutation: MutationRecord, auth_result: AuthResult, context: dict | None,
    ) -> Verdict:
        """SAML assertion accepted without AudienceRestriction or Conditions.

        Per SAML Core 2.5.1.2, AudienceRestriction constrains which SPs
        may consume an assertion. Accepting assertions without audience
        scoping means any SP's assertion could be replayed here.
        """
        return self._verdict(
            VerdictType.VIOLATION, "HIGH",
            f"SAML assertion accepted without audience restriction "
            f"({mutation.mutation_type}). The SP does not enforce "
            f"AudienceRestriction, allowing assertions intended for other "
            f"services to be consumed.",
            {"mutation": mutation.mutation_type},
            spec_reference="SAML Core 2.0 Section 2.5.1.2",
        )

    def _check_saml_wrong_audience(
        self, mutation: MutationRecord, auth_result: AuthResult, context: dict | None,
    ) -> Verdict:
        """SAML assertion accepted with wrong <Audience> value."""
        return self._verdict(
            VerdictType.VIOLATION, "HIGH",
            "SAML assertion accepted with <Audience> set to a different SP. "
            "Platform failed to validate AudienceRestriction against its own "
            "entity ID.",
            {},
            spec_reference="SAML Core 2.0 Section 2.5.1.2",
        )

    # ------------------------------------------------------------------
    # Token exchange audience
    # ------------------------------------------------------------------

    def _check_token_exchange_audience(
        self, mutation: MutationRecord, auth_result: AuthResult, context: dict | None,
    ) -> Verdict:
        """Token exchange accepted a subject_token with wrong/missing audience.

        Per RFC 8693 Section 2.1, the authorization server should validate
        that the subject_token was intended for the entity performing the
        exchange. Accepting tokens minted for other audiences breaks
        authorization binding.
        """
        mt = mutation.mutation_type
        if "no_audience" in mt:
            return self._verdict(
                VerdictType.VIOLATION, "HIGH",
                "Token exchange accepted a subject_token with no audience claim. "
                "The exchange endpoint cannot verify the token was intended for it.",
                {},
                spec_reference="RFC 8693 Section 2.1",
            )
        return self._verdict(
            VerdictType.VIOLATION, "HIGH",
            "Token exchange accepted a subject_token whose audience is a "
            "different service. Audience binding was not enforced during "
            "token exchange.",
            {},
            spec_reference="RFC 8693 Section 2.1",
        )

    # ------------------------------------------------------------------
    # Numeric type coercion
    # ------------------------------------------------------------------

    def _check_numeric_type_coercion(
        self, mutation: MutationRecord, auth_result: AuthResult, context: dict | None,
    ) -> Verdict:
        """Numeric bound_claim accepted with float value (e.g., 100.7 vs bound 100).

        Per RFC 7519, claim values have specific JSON types. If the platform
        truncates or rounds a float claim to match an integer bound_claim,
        authorization binding is weakened (e.g., department_id=100.7 matches
        bound department_id=100).
        """
        return self._verdict(
            VerdictType.UNEXPECTED, "HIGH",
            "Numeric bound_claim accepted with float value (type coercion). "
            "The platform may be truncating or rounding float claim values to "
            "match integer bound_claims. This weakens claim-based authorization "
            "by allowing approximate matches where exact matching was intended.",
            {"mutation": mutation.mutation_type},
            spec_reference="RFC 7519 Section 4 (Claims)",
            requires_manual_review=True,
        )

    # ------------------------------------------------------------------
    # Legacy audience checks
    # ------------------------------------------------------------------

    def _check_audience_legacy(
        self, mutation: MutationRecord, auth_result: AuthResult, context: dict | None,
    ) -> Verdict:
        bound_audiences_configured = (context or {}).get("bound_audiences_configured", True)

        if not bound_audiences_configured:
            return self._verdict(
                VerdictType.BY_DESIGN, "HIGH",
                f"Audience mutation {mutation.mutation_type} accepted, but "
                f"bound_audiences is not configured. Admin chose not to enforce audience.",
                {},
            )

        return self._verdict(
            VerdictType.VIOLATION, "HIGH",
            f"Audience mutation {mutation.mutation_type} accepted despite "
            f"bound_audiences being configured. The platform failed to enforce "
            f"audience restriction.",
            {},
            spec_reference="RFC 7519 Section 4.1.3",
        )

    def _check_audience_array(
        self, mutation: MutationRecord, auth_result: AuthResult, context: dict | None,
    ) -> Verdict:
        return self._verdict(
            VerdictType.UNEXPECTED, "MEDIUM",
            "Token with extra audience values accepted. The aud array contains "
            "values beyond the expected audience. Check if the platform validates "
            "all array elements or just checks for membership.",
            {},
            spec_reference="RFC 7519 Section 4.1.3",
            requires_manual_review=True,
        )

    # ------------------------------------------------------------------
    # Scope
    # ------------------------------------------------------------------

    def _check_scope(
        self, mutation: MutationRecord, auth_result: AuthResult, context: dict | None,
    ) -> Verdict:
        if mutation.mutation_type == "i5_scope_inflation":
            return self._verdict(
                VerdictType.UNEXPECTED, "MEDIUM",
                "Token with inflated scope accepted. Check if the platform enforces "
                "scope boundaries.",
                {},
                requires_manual_review=True,
            )
        return self._verdict(
            VerdictType.UNEXPECTED, "MEDIUM",
            "Token with empty scope accepted.",
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
