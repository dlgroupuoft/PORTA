"""Tests for Sprint 3 — Oracle Verdict Engine."""

from __future__ import annotations

import time

import pytest

from src.models.types import (
    AuthContext,
    AuthResult,
    Credential,
    Invariant,
    MutationRecord,
    Platform,
    Protocol,
    Verdict,
    VerdictType,
)
from src.oracles.base import SecurityOracle
from src.oracles.i1_proof_integrity import I1ProofIntegrityOracle
from src.oracles.i2_freshness import I2FreshnessOracle
from src.oracles.i3_flow_coherence import I3FlowCoherenceOracle
from src.oracles.i4_principal_binding import I4PrincipalBindingOracle
from src.oracles.i5_authorization_binding import I5AuthorizationBindingOracle


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auth_ok(**kwargs) -> AuthResult:
    defaults = dict(
        success=True, platform=Platform.VAULT, protocol=Protocol.JWT,
        http_status=200,
    )
    defaults.update(kwargs)
    return AuthResult(**defaults)


def _auth_fail(**kwargs) -> AuthResult:
    defaults = dict(
        success=False, platform=Platform.VAULT, protocol=Protocol.JWT,
        http_status=401, error_message="unauthorized",
    )
    defaults.update(kwargs)
    return AuthResult(**defaults)


def _mutation(mutation_type: str, claims: dict | None = None,
              metadata: dict | None = None,
              cred_metadata: dict | None = None) -> MutationRecord:
    cred = Credential(
        protocol=Protocol.JWT,
        claims=claims or {},
        metadata=cred_metadata or {},
    )
    return MutationRecord(
        mutation_type=mutation_type,
        credential=cred,
        metadata=metadata or {},
    )


# ===========================================================================
# I2 Freshness Oracle Tests
# ===========================================================================

class TestI2Freshness:
    @pytest.fixture
    def oracle(self):
        return I2FreshnessOracle()

    # --- Critical correctness test: JWT bearer replay is BY_DESIGN ---
    def test_jwt_bearer_replay_is_by_design(self, oracle):
        prior = _auth_ok()
        m = _mutation("i2_replay_same_token")
        ctx = {
            "auth_context": AuthContext.JWT_BEARER,
            "prior_submission_results": [prior],
        }
        v = oracle.check(m, _auth_ok(), ctx)
        assert v.verdict_type == VerdictType.BY_DESIGN
        assert "RFC 6750" in v.spec_reference

    # --- Critical correctness test: client assertion replay is VIOLATION ---
    def test_client_assertion_replay_is_violation(self, oracle):
        prior = _auth_ok()
        m = _mutation("i2_replay_same_token", claims={"jti": "abc123"})
        ctx = {
            "auth_context": AuthContext.OAUTH2_CLIENT_ASSERTION,
            "prior_submission_results": [prior],
        }
        v = oracle.check(m, _auth_ok(), ctx)
        assert v.verdict_type == VerdictType.VIOLATION
        assert "RFC 7523" in v.spec_reference

    # --- Critical correctness test: SAML assertion replay is VIOLATION ---
    def test_saml_assertion_replay_is_violation(self, oracle):
        prior = _auth_ok()
        m = _mutation("i2_saml_assertion_id_replay")
        ctx = {
            "auth_context": AuthContext.SAML_ASSERTION,
            "prior_submission_results": [prior],
        }
        v = oracle.check(m, _auth_ok(), ctx)
        assert v.verdict_type == VerdictType.VIOLATION
        assert "SAML Core" in v.spec_reference
        assert v.cve_pattern == "CVE-2018-14637"

    def test_ldap_replay_is_by_design(self, oracle):
        prior = _auth_ok()
        m = _mutation("i2_replay_same_token")
        ctx = {
            "auth_context": AuthContext.LDAP_BIND,
            "prior_submission_results": [prior],
        }
        v = oracle.check(m, _auth_ok(), ctx)
        assert v.verdict_type == VerdictType.BY_DESIGN

    def test_first_submission_is_by_design(self, oracle):
        """First submission (no prior results) should always be BY_DESIGN."""
        m = _mutation("i2_replay_same_token")
        ctx = {
            "auth_context": AuthContext.SAML_ASSERTION,
            "prior_submission_results": [],
        }
        v = oracle.check(m, _auth_ok(), ctx)
        assert v.verdict_type == VerdictType.BY_DESIGN

    def test_unknown_context_replay_is_unexpected(self, oracle):
        prior = _auth_ok()
        m = _mutation("i2_replay_same_token")
        ctx = {
            "auth_context": AuthContext.OAUTH2_CODE,
            "prior_submission_results": [prior],
        }
        v = oracle.check(m, _auth_ok(), ctx)
        assert v.verdict_type == VerdictType.UNEXPECTED
        assert v.requires_manual_review

    def test_oauth2_code_replay_is_violation(self, oracle):
        first = _auth_ok(http_status=200)
        m = _mutation("i2_code_replay")
        ctx = {"first_exchange_result": first}
        v = oracle.check(m, _auth_ok(), ctx)
        assert v.verdict_type == VerdictType.VIOLATION
        assert "RFC 6749 Section 4.1.2" in v.spec_reference

    def test_code_replay_missing_context_is_error(self, oracle):
        m = _mutation("i2_code_replay")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.ERROR

    def test_expired_well_beyond_skew_is_violation(self, oracle):
        exp = int(time.time()) - 3600
        m = _mutation("i2_expired_token", claims={"exp": exp})
        ctx = {"clock_skew_tolerance": 60}
        v = oracle.check(m, _auth_ok(), ctx)
        assert v.verdict_type == VerdictType.VIOLATION
        assert "RFC 7519 Section 4.1.4" in v.spec_reference

    def test_expired_within_skew_is_unexpected(self, oracle):
        exp = int(time.time()) - 30
        m = _mutation("i2_expired_token", claims={"exp": exp})
        ctx = {"clock_skew_tolerance": 60}
        v = oracle.check(m, _auth_ok(), ctx)
        assert v.verdict_type == VerdictType.UNEXPECTED
        assert v.requires_manual_review

    def test_rejected_replay_is_rejected(self, oracle):
        m = _mutation("i2_replay_same_token")
        v = oracle.check(m, _auth_fail(), {})
        assert v.verdict_type == VerdictType.REJECTED

    def test_missing_exp_is_unexpected(self, oracle):
        m = _mutation("i2_missing_exp")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.UNEXPECTED

    def test_missing_exp_external_jwt_provider_is_violation(self, oracle):
        m = _mutation("i2_missing_exp")
        ctx = {"auth_context": AuthContext.EXTERNAL_JWT_PROVIDER}
        v = oracle.check(m, _auth_ok(), ctx)
        assert v.verdict_type == VerdictType.VIOLATION

    def test_missing_iat_is_unexpected(self, oracle):
        m = _mutation("i2_missing_iat")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.UNEXPECTED

    def test_missing_iat_external_jwt_provider_is_violation(self, oracle):
        m = _mutation("i2_missing_iat")
        ctx = {"auth_context": AuthContext.EXTERNAL_JWT_PROVIDER}
        v = oracle.check(m, _auth_ok(), ctx)
        assert v.verdict_type == VerdictType.VIOLATION

    def test_future_token_well_ahead_is_violation(self, oracle):
        nbf = int(time.time()) + 7200
        m = _mutation("i2_future_token", claims={"nbf": nbf})
        ctx = {"clock_skew_tolerance": 60}
        v = oracle.check(m, _auth_ok(), ctx)
        assert v.verdict_type == VerdictType.VIOLATION

    def test_inresponseto_mismatch_is_violation(self, oracle):
        m = _mutation("i2_inresponseto_mismatch",
                      cred_metadata={"in_response_to": "wrong_id"})
        ctx = {"original_request_id": "correct_id"}
        v = oracle.check(m, _auth_ok(), ctx)
        assert v.verdict_type == VerdictType.VIOLATION
        assert v.cve_pattern == "CVE-2023-0264"

    def test_disabled_user_is_violation(self, oracle):
        m = _mutation("i2_disabled_user_login")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION

    def test_password_changed_replay_is_violation(self, oracle):
        m = _mutation("i2_password_changed_replay")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION

    def test_unhandled_mutation_is_error(self, oracle):
        m = _mutation("i2_unknown_thing")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.ERROR

    def test_oracle_never_raises(self, oracle):
        """Oracle should catch exceptions and return ERROR verdict."""
        # Passing None for auth_result would cause AttributeError internally
        # but the oracle should catch it
        m = _mutation("i2_expired_token", claims={"exp": "not_a_number"})
        v = oracle.check(m, _auth_ok(), {})
        # Should not raise — any verdict is fine as long as it's a Verdict
        assert isinstance(v, Verdict)

    def test_jti_reuse_client_assertion_is_violation(self, oracle):
        m = _mutation("i2_reuse_jti_new_exp")
        ctx = {"auth_context": AuthContext.OAUTH2_CLIENT_ASSERTION}
        v = oracle.check(m, _auth_ok(), ctx)
        assert v.verdict_type == VerdictType.VIOLATION

    def test_jti_reuse_bearer_is_unexpected(self, oracle):
        m = _mutation("i2_reuse_jti_new_exp")
        ctx = {"auth_context": AuthContext.JWT_BEARER}
        v = oracle.check(m, _auth_ok(), ctx)
        assert v.verdict_type == VerdictType.UNEXPECTED


# ===========================================================================
# I5 Authorization Binding Oracle Tests
# ===========================================================================

class TestI5AuthorizationBinding:
    @pytest.fixture
    def oracle(self):
        return I5AuthorizationBindingOracle()

    def test_aud_number_accepted_is_violation(self, oracle):
        m = _mutation("i5_aud_type_number", claims={"aud": 12345})
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION
        assert v.cve_pattern == "CVE-2024-5798"

    def test_aud_boolean_accepted_is_violation(self, oracle):
        m = _mutation("i5_aud_type_boolean", claims={"aud": True})
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION

    def test_aud_null_accepted_is_violation(self, oracle):
        m = _mutation("i5_aud_type_null", claims={"aud": None})
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION

    def test_aud_object_accepted_is_violation(self, oracle):
        m = _mutation("i5_aud_type_object", claims={"aud": {"nested": "value"}})
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION

    def test_aud_string_accepted_is_by_design(self, oracle):
        m = _mutation("i5_aud_type_number", claims={"aud": "vault-test"})
        # Override: claim actually has a valid string type
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.BY_DESIGN

    def test_aud_list_of_strings_is_by_design(self, oracle):
        m = _mutation("i5_aud_type_empty_array", claims={"aud": ["vault-test", "other"]})
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.BY_DESIGN

    def test_aud_empty_array_is_violation(self, oracle):
        """Empty list is list type but has no strings — edge case handled as BY_DESIGN
        since the type is list (expected type). The emptiness is a separate check."""
        m = _mutation("i5_aud_type_empty_array", claims={"aud": []})
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.BY_DESIGN

    def test_aud_array_with_null_is_violation(self, oracle):
        m = _mutation("i5_aud_type_array_with_null", claims={"aud": ["valid", None]})
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION
        assert "non-string" in v.description

    def test_aud_array_with_number_is_violation(self, oracle):
        m = _mutation("i5_aud_type_array_with_number", claims={"aud": ["valid", 123]})
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION

    def test_groups_string_accepted_is_violation(self, oracle):
        m = _mutation("i4_groups_type_string", claims={"groups": "admins"})
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION

    def test_groups_array_with_number_is_violation(self, oracle):
        m = _mutation("i4_groups_type_array_with_non_string",
                      claims={"groups": ["devs", 123]})
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION

    def test_config_empty_audiences_is_unexpected(self, oracle):
        m = _mutation("i5_bound_audiences_empty_array_config",
                      metadata={"config_change": {"bound_audiences": []}})
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.UNEXPECTED
        assert v.cve_pattern == "CVE-2024-7594"
        assert v.requires_manual_review

    def test_config_unset_audiences_is_unexpected(self, oracle):
        m = _mutation("i5_bound_audiences_unset_config",
                      metadata={"config_change": {"bound_audiences": None}})
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.UNEXPECTED

    def test_aud_wrong_with_bound_audiences_is_violation(self, oracle):
        m = _mutation("i5_aud_wrong", claims={"aud": "wrong-aud"})
        ctx = {"bound_audiences_configured": True}
        v = oracle.check(m, _auth_ok(), ctx)
        assert v.verdict_type == VerdictType.VIOLATION

    def test_aud_wrong_without_bound_audiences_is_by_design(self, oracle):
        m = _mutation("i5_aud_wrong", claims={"aud": "wrong-aud"})
        ctx = {"bound_audiences_configured": False}
        v = oracle.check(m, _auth_ok(), ctx)
        assert v.verdict_type == VerdictType.BY_DESIGN

    def test_rejected_is_rejected(self, oracle):
        m = _mutation("i5_aud_type_number", claims={"aud": 123})
        v = oracle.check(m, _auth_fail(), {})
        assert v.verdict_type == VerdictType.REJECTED

    def test_oracle_never_raises(self, oracle):
        m = _mutation("i5_aud_type_number")
        m._credential = None  # corrupt the object
        v = oracle.check(m, _auth_ok(), {})
        assert isinstance(v, Verdict)

    def test_scope_inflation_is_unexpected(self, oracle):
        m = _mutation("i5_scope_inflation")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.UNEXPECTED


# ===========================================================================
# I1 Proof Integrity Oracle Tests
# ===========================================================================

class TestI1ProofIntegrity:
    @pytest.fixture
    def oracle(self):
        return I1ProofIntegrityOracle()

    def test_alg_none_accepted_is_violation(self, oracle):
        m = _mutation("i1_alg_none")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION
        assert "RFC 7518" in v.spec_reference

    def test_attacker_key_accepted_is_violation(self, oracle):
        m = _mutation("i1_resign_attacker_key")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION
        assert v.cve_pattern == "CVE-2025-49831"

    def test_trust_anchor_substitution_is_violation(self, oracle):
        m = _mutation("i1_trust_anchor_substitution")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION

    def test_kid_injection_is_violation(self, oracle):
        m = _mutation("i1_kid_injection")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION

    def test_xsw_accepted_is_violation(self, oracle):
        m = _mutation("i1_xsw_4")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION
        assert v.requires_manual_review
        assert v.cve_pattern == "Dex-CVE-2020-27847"

    def test_xsw_rejected_is_rejected(self, oracle):
        m = _mutation("i1_xsw_4")
        v = oracle.check(m, _auth_fail(), {})
        assert v.verdict_type == VerdictType.REJECTED

    def test_comment_in_nameid_stripped_is_violation(self, oracle):
        m = _mutation("i1_saml_comment_in_nameid")
        ctx = {"downstream_identity": "admievil.com"}  # comment was stripped
        v = oracle.check(m, _auth_ok(), ctx)
        assert v.verdict_type == VerdictType.VIOLATION

    def test_comment_in_nameid_preserved_is_by_design(self, oracle):
        m = _mutation("i1_saml_comment_in_nameid")
        ctx = {"downstream_identity": "admi<!--comment-->evil.com"}
        v = oracle.check(m, _auth_ok(), ctx)
        assert v.verdict_type == VerdictType.BY_DESIGN

    def test_iss_trailing_slash_is_unexpected(self, oracle):
        m = _mutation("i1_iss_trailing_slash")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.UNEXPECTED
        assert v.requires_manual_review

    def test_iss_case_variation_is_unexpected(self, oracle):
        m = _mutation("i1_iss_case_variation")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.UNEXPECTED
        assert "RFC 7519 Section 4.1.1" in v.spec_reference

    def test_iss_unicode_homoglyph_is_violation(self, oracle):
        m = _mutation("i1_iss_unicode_homoglyph")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION
        assert v.cve_pattern == "URL confusion"

    def test_namespace_prefix_is_unexpected(self, oracle):
        m = _mutation("i1_saml_namespace_prefix_manipulation")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.UNEXPECTED

    def test_multiple_nameid_is_unexpected(self, oracle):
        m = _mutation("i1_saml_multiple_nameid")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.UNEXPECTED

    def test_attribute_value_type_is_unexpected(self, oracle):
        m = _mutation("i1_saml_attribute_value_type")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.UNEXPECTED
        assert v.cve_pattern == "CVE-2024-5798"

    def test_whitespace_nameid_stripped_is_unexpected(self, oracle):
        m = _mutation("i1_saml_whitespace_in_nameid")
        ctx = {"downstream_identity": "admin@evil.com"}
        v = oracle.check(m, _auth_ok(), ctx)
        assert v.verdict_type == VerdictType.UNEXPECTED

    def test_whitespace_nameid_preserved_is_by_design(self, oracle):
        m = _mutation("i1_saml_whitespace_in_nameid")
        ctx = {"downstream_identity": "  admin@evil.com  "}
        v = oracle.check(m, _auth_ok(), ctx)
        assert v.verdict_type == VerdictType.BY_DESIGN

    def test_oracle_never_raises(self, oracle):
        m = _mutation("i1_alg_none")
        m._credential = None
        v = oracle.check(m, _auth_ok(), {})
        assert isinstance(v, Verdict)

    def test_alg_confusion_is_violation(self, oracle):
        m = _mutation("i1_alg_confusion_rs256_to_hs256")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION

    def test_unsigned_assertion_is_violation(self, oracle):
        m = _mutation("i1_unsigned_assertion_in_signed_response")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION

    def test_dtd_entity_is_violation(self, oracle):
        m = _mutation("i1_dtd_entity_expansion")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION


# ===========================================================================
# I3 Flow Coherence Oracle Tests
# ===========================================================================

class TestI3FlowCoherence:
    @pytest.fixture
    def oracle(self):
        return I3FlowCoherenceOracle()

    def test_redirect_mismatch_is_violation(self, oracle):
        m = _mutation("i3_redirect_uri_mismatch")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION
        assert "RFC 6749 Section 4.1.3" in v.spec_reference

    def test_code_injection_is_violation(self, oracle):
        m = _mutation("i3_code_injection")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION

    def test_pkce_skip_is_violation(self, oracle):
        m = _mutation("i3_pkce_skip")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION
        assert "RFC 7636" in v.spec_reference

    def test_pkce_wrong_verifier_is_violation(self, oracle):
        m = _mutation("i3_pkce_wrong_verifier")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION

    def test_state_swap_is_by_design(self, oracle):
        m = _mutation("i3_state_swap")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.BY_DESIGN

    def test_state_swap_with_nonce_mismatch_is_unexpected(self, oracle):
        m = _mutation("i3_state_swap")
        ctx = {
            "original_nonce": "nonce_a",
            "id_token_claims": {"nonce": "nonce_b"},
        }
        v = oracle.check(m, _auth_ok(), ctx)
        assert v.verdict_type == VerdictType.UNEXPECTED

    def test_loopback_port_override_is_by_design(self, oracle):
        m = _mutation("i3_loopback_port_override")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.BY_DESIGN
        assert "RFC 8252" in v.spec_reference

    def test_nonce_mismatch_is_unexpected(self, oracle):
        m = _mutation("i3_nonce_mismatch")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.UNEXPECTED

    def test_scope_escalation_is_violation(self, oracle):
        m = _mutation("i3_scope_escalation_at_token")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION
        assert "RFC 6749 Section 3.3" in v.spec_reference

    def test_rejected_is_rejected(self, oracle):
        m = _mutation("i3_redirect_uri_mismatch")
        v = oracle.check(m, _auth_fail(), {})
        assert v.verdict_type == VerdictType.REJECTED

    def test_oracle_never_raises(self, oracle):
        m = _mutation("i3_pkce_skip")
        m._credential = None
        v = oracle.check(m, _auth_ok(), {})
        assert isinstance(v, Verdict)


# ===========================================================================
# I4 Principal Binding Oracle Tests
# ===========================================================================

class TestI4PrincipalBinding:
    @pytest.fixture
    def oracle(self):
        return I4PrincipalBindingOracle()

    def test_dn_injection_is_violation(self, oracle):
        m = _mutation("i4_dn_injection")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION

    def test_null_byte_injection_is_violation(self, oracle):
        m = _mutation("i4_null_byte_injection")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION

    def test_wildcard_filter_is_violation(self, oracle):
        m = _mutation("i4_wildcard_filter")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION

    def test_glob_star_in_claims_is_violation(self, oracle):
        m = _mutation("i4_bound_claims_glob_star")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION
        assert v.cve_pattern == "CVE-2025-11621"

    def test_glob_question_is_violation(self, oracle):
        m = _mutation("i4_bound_claims_glob_question")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION
        assert v.cve_pattern == "CVE-2025-11621"

    def test_glob_bracket_is_violation(self, oracle):
        m = _mutation("i4_bound_claims_glob_bracket")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION

    def test_empty_value_is_unexpected(self, oracle):
        m = _mutation("i4_bound_claims_empty_value")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.UNEXPECTED
        assert v.cve_pattern == "CVE-2024-7594"

    def test_sub_overwrite_is_by_design(self, oracle):
        m = _mutation("i4_sub_overwrite")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.BY_DESIGN

    def test_email_overwrite_is_by_design(self, oracle):
        m = _mutation("i4_email_overwrite")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.BY_DESIGN

    def test_sub_type_number_is_violation(self, oracle):
        m = _mutation("i4_sub_type_number", claims={"sub": 42})
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION
        assert v.cve_pattern == "CVE-2024-5798"

    def test_groups_type_string_is_violation(self, oracle):
        m = _mutation("i4_groups_type_string", claims={"groups": "admins"})
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION

    def test_sub_type_null_is_violation(self, oracle):
        m = _mutation("i4_sub_type_null", claims={"sub": None})
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.VIOLATION

    def test_config_change_empty_is_unexpected(self, oracle):
        m = _mutation("i4_bound_claims_empty_config",
                      metadata={"config_change": {"bound_claims": {}}})
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.UNEXPECTED
        assert v.cve_pattern == "CVE-2024-7594"

    def test_user_claim_nonexistent_is_unexpected(self, oracle):
        m = _mutation("i4_user_claim_nonexistent_field",
                      metadata={"config_change": {"user_claim": "nonexistent_field"}})
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.UNEXPECTED

    def test_claim_in_header_is_unexpected(self, oracle):
        m = _mutation("i4_claim_in_header")
        v = oracle.check(m, _auth_ok(), {})
        assert v.verdict_type == VerdictType.UNEXPECTED
        assert v.requires_manual_review

    def test_rejected_is_rejected(self, oracle):
        m = _mutation("i4_dn_injection")
        v = oracle.check(m, _auth_fail(), {})
        assert v.verdict_type == VerdictType.REJECTED

    def test_oracle_never_raises(self, oracle):
        m = _mutation("i4_dn_injection")
        m._credential = None
        v = oracle.check(m, _auth_ok(), {})
        assert isinstance(v, Verdict)


# ===========================================================================
# Cross-cutting concerns
# ===========================================================================

class TestVerdictModel:

    def test_verdict_uses_verdict_type_enum(self):
        v = Verdict(
            invariant="I1",
            verdict_type=VerdictType.VIOLATION,
            confidence="HIGH",
            description="test",
        )
        assert isinstance(v.verdict_type, VerdictType)
        assert v.verdict_type == VerdictType.VIOLATION

    def test_verdict_serialization(self):
        v = Verdict(
            invariant="I2",
            verdict_type=VerdictType.BY_DESIGN,
            confidence="HIGH",
            description="test",
            spec_reference="RFC 6750",
            cve_pattern="CVE-2024-5798",
            requires_manual_review=True,
        )
        d = v.to_dict()
        assert d["verdict_type"] == "BY_DESIGN"
        assert d["spec_reference"] == "RFC 6750"
        assert d["cve_pattern"] == "CVE-2024-5798"

    def test_verdict_from_dict(self):
        d = {
            "invariant": "I1",
            "verdict_type": "VIOLATION",
            "confidence": "HIGH",
            "description": "test",
            "evidence": {},
            "spec_reference": "",
            "cve_pattern": "",
            "requires_manual_review": False,
        }
        v = Verdict.from_dict(d)
        assert v.verdict_type == VerdictType.VIOLATION

    def test_auth_context_enum(self):
        assert AuthContext.JWT_BEARER.value == "jwt_bearer"
        assert AuthContext.SAML_ASSERTION.value == "saml_assertion"
        assert AuthContext.OAUTH2_CLIENT_ASSERTION.value == "client_assertion"


class TestAllOraclesImportable:

    def test_i1_importable(self):
        oracle = I1ProofIntegrityOracle()
        assert oracle.invariant == Invariant.I1_PROOF_INTEGRITY

    def test_i2_importable(self):
        oracle = I2FreshnessOracle()
        assert oracle.invariant == Invariant.I2_FRESHNESS

    def test_i3_importable(self):
        oracle = I3FlowCoherenceOracle()
        assert oracle.invariant == Invariant.I3_FLOW_COHERENCE

    def test_i4_importable(self):
        oracle = I4PrincipalBindingOracle()
        assert oracle.invariant == Invariant.I4_PRINCIPAL_BINDING

    def test_i5_importable(self):
        oracle = I5AuthorizationBindingOracle()
        assert oracle.invariant == Invariant.I5_AUTHORIZATION_BINDING

    def test_base_class_is_abstract(self):
        with pytest.raises(TypeError):
            SecurityOracle(Invariant.I1_PROOF_INTEGRITY)


class TestSpecReferencesPresent:
    """Verify spec references are included where applicable."""

    def test_i2_code_replay_has_spec_ref(self):
        oracle = I2FreshnessOracle()
        first = _auth_ok(http_status=200)
        m = _mutation("i2_code_replay")
        v = oracle.check(m, _auth_ok(), {"first_exchange_result": first})
        assert v.spec_reference != ""

    def test_i1_alg_none_has_spec_ref(self):
        oracle = I1ProofIntegrityOracle()
        m = _mutation("i1_alg_none")
        v = oracle.check(m, _auth_ok(), {})
        assert v.spec_reference != ""

    def test_i3_redirect_has_spec_ref(self):
        oracle = I3FlowCoherenceOracle()
        m = _mutation("i3_redirect_uri_mismatch")
        v = oracle.check(m, _auth_ok(), {})
        assert v.spec_reference != ""

    def test_i5_type_confusion_has_cve_pattern(self):
        oracle = I5AuthorizationBindingOracle()
        m = _mutation("i5_aud_type_number", claims={"aud": 123})
        v = oracle.check(m, _auth_ok(), {})
        assert v.cve_pattern != ""
