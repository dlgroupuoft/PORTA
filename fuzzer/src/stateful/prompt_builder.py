"""Builds LLM prompts for event sequence generation.

Shared between CoverageStrategy and AttackStrategy.
Parameterized by PlatformProfile and example configuration
for clean ablation experiments.
"""

import json
import logging
import os
import re as _re

from src.stateful.generation_strategy import GenerationConfig, INVARIANT_DEFINITIONS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy-loaded protocol abstractions
# ---------------------------------------------------------------------------
_PROTOCOL_OPERATIONS = None
_CROSS_PLATFORM_ATTACK_PATTERNS = None


def _load_abstractions():
    global _PROTOCOL_OPERATIONS, _CROSS_PLATFORM_ATTACK_PATTERNS
    if _PROTOCOL_OPERATIONS is None:
        from src.stateful.protocol_operations import (
            PROTOCOL_OPERATIONS as PO,
            CROSS_PLATFORM_ATTACK_PATTERNS as CPAP,
        )
        _PROTOCOL_OPERATIONS = PO
        _CROSS_PLATFORM_ATTACK_PATTERNS = CPAP


# ---------------------------------------------------------------------------
# Few-shot examples (kept here as prompt-building data)
# ---------------------------------------------------------------------------

PROFILE_FEW_SHOT_EXAMPLES = [
    {
        "id": "example_i4_entity_collision",
        "description": "Two different JWT sub values login to same role — do they get different identities?",
        "invariant_hypothesis": "I4: Different upstream principals must map to different downstream identities",
        "primary_invariant": "I4",
        "cve_analog": "none",
        "events": [
            {"event_type": "create_policy", "params": {"policy_name": "test-policy", "policy_document": "path \"secret/data/*\" { capabilities = [\"read\"] }"}, "auth_as": "admin"},
            {"event_type": "create_auth_role", "params": {"role_name": "collision-role", "identity_claim": "sub", "audience_restriction": ["vault"], "granted_policies": ["test-policy"], "role_type": "jwt"}, "auth_as": "admin"},
            {"event_type": "login_with_jwt", "params": {"role": "collision-role", "jwt_claims": {"sub": "alice", "aud": "vault"}}, "auth_as": "user_A", "captures": {"user_a_entity": "auth.entity_id"}},
            {"event_type": "login_with_jwt", "params": {"role": "collision-role", "jwt_claims": {"sub": "bob", "aud": "vault"}}, "auth_as": "user_B", "captures": {"user_b_entity": "auth.entity_id"}},
            {"event_type": "verify_granted_identity", "params": {}, "auth_as": "session_user_A"},
            {"event_type": "verify_granted_identity", "params": {}, "auth_as": "session_user_B"}
        ],
        "oracle_checks": [
            {"check_id": "i4_collision", "invariant": "I4", "assertion": "user_a_entity != user_b_entity",
             "violation_description": "Two distinct sub values mapped to same entity — identity collision"}
        ]
    },
    {
        "id": "example_i5_group_policy_escalation",
        "description": "Login with groups claim mapped to privileged identity group",
        "invariant_hypothesis": "I5: Group claim mapping should not grant policies beyond role's granted_policies",
        "primary_invariant": "I5",
        "cve_analog": "CVE-2025-1391",
        "events": [
            {"event_type": "create_policy", "params": {"policy_name": "admin-secrets", "policy_document": "path \"secret/data/admin/*\" { capabilities = [\"read\", \"list\"] }"}, "auth_as": "admin"},
            {"event_type": "create_policy", "params": {"policy_name": "user-secrets", "policy_document": "path \"secret/data/users/*\" { capabilities = [\"read\"] }"}, "auth_as": "admin"},
            {"event_type": "create_identity_group", "params": {"name": "vault-admins", "policies": ["admin-secrets"], "type": "external"}, "auth_as": "admin", "captures": {"admin_group_id": "data.id"}},
            {"event_type": "seed_protected_resource", "params": {"secret_path": "admin/flag", "data": {"flag": "admin-only"}}, "auth_as": "admin"},
            {"event_type": "get_mount_accessor", "params": {}, "auth_as": "admin", "captures": {"jwt_accessor": "jwt/.accessor"}},
            {"event_type": "create_group_alias", "params": {"name": "privileged-group", "mount_accessor": "{{jwt_accessor}}", "canonical_id": "{{admin_group_id}}"}, "auth_as": "admin"},
            {"event_type": "create_auth_role", "params": {"role_name": "group-test-role", "identity_claim": "sub", "groups_claim": "groups", "audience_restriction": ["vault"], "granted_policies": ["user-secrets"]}, "auth_as": "admin"},
            {"event_type": "login_with_jwt", "params": {"role": "group-test-role", "jwt_claims": {"sub": "regular-user", "aud": "vault", "groups": ["privileged-group"]}}, "auth_as": "user_A"},
            {"event_type": "verify_granted_identity", "params": {}, "auth_as": "session_user_A", "captures": {"user_a_policies": "data.policies", "user_a_identity_policies": "data.identity_policies"}},
            {"event_type": "verify_read_secret", "params": {"secret_path": "admin/flag"}, "auth_as": "session_user_A", "captures": {"admin_access_status": "http_status"}}
        ],
        "oracle_checks": [
            {"check_id": "i5_group_escalation", "invariant": "I5", "assertion": "admin_access_status == 403",
             "violation_description": "User with granted_policies=['user-secrets'] accessed admin secrets via group claim mapping",
             "cve_analog": "CVE-2025-1391"}
        ]
    },
    {
        "id": "example_i5_correct_policy_chain",
        "description": "Correct policy→role→login→access chain: create policy granting read on test path, create role referencing that policy, login, verify access succeeds",
        "invariant_hypothesis": "I5: Token should only have access granted by role's token_policies",
        "primary_invariant": "I5",
        "cve_analog": "",
        "events": [
            {"event_type": "create_policy", "params": {"policy_name": "test-read", "policy_document": "path \"secret/data/test/*\" { capabilities = [\"read\", \"list\"] }"}, "auth_as": "admin"},
            {"event_type": "seed_protected_resource", "params": {"secret_path": "test/allowed-data", "data": {"value": "test-secret"}}, "auth_as": "admin"},
            {"event_type": "seed_protected_resource", "params": {"secret_path": "admin/forbidden-data", "data": {"value": "admin-only"}}, "auth_as": "admin"},
            {"event_type": "create_auth_role", "params": {"role_name": "policy-test-role", "identity_claim": "sub", "audience_restriction": ["vault"], "granted_policies": ["test-read"], "role_type": "jwt"}, "auth_as": "admin"},
            {"event_type": "login_with_jwt", "params": {"role": "policy-test-role", "jwt_claims": {"sub": "policy-tester", "aud": "vault"}}, "auth_as": "user_A"},
            {"event_type": "verify_read_secret", "params": {"secret_path": "test/allowed-data"}, "auth_as": "session_user_A", "captures": {"allowed_read_status": "_http_status"}},
            {"event_type": "verify_read_secret", "params": {"secret_path": "admin/forbidden-data"}, "auth_as": "session_user_A", "captures": {"forbidden_read_status": "_http_status"}}
        ],
        "oracle_checks": [
            {"check_id": "i5_positive_access", "invariant": "I5", "assertion": "allowed_read_status == 200", "violation_description": "Token with test-read policy should be able to read test/* path"},
            {"check_id": "i5_negative_access", "invariant": "I5", "assertion": "forbidden_read_status == 403", "violation_description": "Token without admin policy should NOT access admin/* path — if it can, authorization binding is violated"}
        ]
    }
]

KEYCLOAK_UMA_FEW_SHOT = {
    "id": "seq_kc_i5_uma_scope_escalation",
    "description": "Register a resource with read scope, create policy granting only read, request RPT with write scope, verify RPT does not contain write",
    "invariant_hypothesis": "I5: RPT permissions must not exceed granted scopes from policy",
    "primary_invariant": "I5",
    "cve_analog": "none",
    "events": [
        {"event_type": "create_realm", "params": {"realm": "uma-test", "enabled": True}, "auth_as": "admin", "phase": "setup"},
        {"event_type": "create_client", "params": {
            "realm": "uma-test", "client_id": "resource-server", "client_secret": "rs-secret",
            "enabled": True, "public_client": False, "direct_access_grants": True,
            "standard_flow": True, "authorization_services_enabled": True,
        }, "auth_as": "admin", "phase": "setup"},
        {"event_type": "create_user", "params": {
            "realm": "uma-test", "username": "resource-owner", "enabled": True,
            "email": "owner@test.local", "firstName": "Owner", "lastName": "User",
            "credentials": [{"type": "password", "value": "owner-pass", "temporary": False}]
        }, "auth_as": "admin", "phase": "setup"},
        {"event_type": "create_user", "params": {
            "realm": "uma-test", "username": "requester", "enabled": True,
            "email": "req@test.local", "firstName": "Req", "lastName": "User",
            "credentials": [{"type": "password", "value": "req-pass", "temporary": False}]
        }, "auth_as": "admin", "phase": "setup"},
        {"event_type": "obtain_pat_client_credentials", "params": {
            "realm": "uma-test", "grant_type": "client_credentials",
            "client_id": "resource-server", "client_secret": "rs-secret", "scope": "openid"
        }, "auth_as": "pat_client", "phase": "setup", "captures": {"pat_token": "session_token"}},
        {"event_type": "create_protected_resource", "params": {
            "realm": "uma-test", "name": "Document A",
            "resource_scopes": ["read", "write"], "owner": "resource-owner", "owner_managed_access": True
        }, "auth_as": "session_pat_client", "phase": "setup", "captures": {"resource_id": "resource_id"}},
        {"event_type": "create_uma_policy_permission_for_resource", "params": {
            "realm": "uma-test", "resource_id": "{{resource_id}}", "name": "read-only-policy",
            "scopes": ["read"], "roles": [], "groups": [], "clients": []
        }, "auth_as": "session_pat_client", "phase": "setup"},
        {"event_type": "login_with_password", "params": {
            "realm": "uma-test", "username": "requester", "password": "req-pass",
            "client_id": "resource-server", "client_secret": "rs-secret",
            "grant_type": "password", "scope": "openid"
        }, "auth_as": "user_requester", "phase": "login"},
        {"event_type": "obtain_rpt_uma_ticket", "params": {
            "realm": "uma-test", "grant_type": "urn:ietf:params:oauth:grant-type:uma-ticket",
            "audience": "resource-server", "permission": "{{resource_id}}#write", "response_mode": "permissions"
        }, "auth_as": "session_user_requester", "phase": "login", "captures": {"rpt_token": "session_token"}},
        {"event_type": "introspect_token", "params": {
            "realm": "uma-test", "token": "{{rpt_token}}",
            "client_id": "resource-server", "client_secret": "rs-secret"
        }, "auth_as": "admin", "phase": "verify",
         "captures": {"rpt_active": "active", "rpt_permissions": "permissions", "rpt_scope": "scope"}},
    ],
    "oracle_checks": [
        {"check_id": "i5_uma_no_write", "invariant": "I5",
         "assertion": "rpt_permissions does not contain write scope when policy only grants read",
         "violation_description": "RPT contains write permission despite policy only granting read — scope escalation"}
    ]
}

KEYCLOAK_OIDC_REQUEST_OBJECT_EXAMPLE = {
    "id": "seq_kc_i1_request_object_alg_none",
    "description": "I1: Test if OIDC auth endpoint accepts unsigned request objects (alg=none). A public client without requestObjectSignatureAlg should reject alg=none JWTs.",
    "invariant_hypothesis": "I1: Authorization endpoint must reject unsigned request objects",
    "primary_invariant": "I1",
    "cve_analog": "CVE-2022-24720",
    "events": [
        {"event_type": "create_tenant", "params": {"realm": "kc-i1-reqobj-test"}, "auth_as": "admin", "phase": "setup"},
        {"event_type": "create_client", "params": {
            "realm": "kc-i1-reqobj-test", "clientId": "reqobj-test-client",
            "publicClient": True, "enabled": True,
            "redirectUris": ["http://localhost:8080/realms/kc-i1-reqobj-test/account/*"],
            "standardFlowEnabled": True
        }, "auth_as": "admin", "phase": "setup"},
        {"event_type": "test_request_object", "params": {
            "realm": "kc-i1-reqobj-test", "client_id": "reqobj-test-client",
            "redirect_uri": "http://localhost:8080/realms/kc-i1-reqobj-test/account/",
            "request_object_alg": "none"
        }, "auth_as": "admin", "phase": "login",
         "captures": {"reqobj_accepted": "accepted", "reqobj_status": "http_status"}}
    ],
    "oracle_checks": [
        {"check_id": "i1_alg_none_rejected", "invariant": "I1",
         "assertion": "reqobj_accepted != True",
         "violation_description": "Auth endpoint accepted unsigned request object (alg=none) — attacker can inject arbitrary authorization parameters without cryptographic verification"}
    ]
}

KEYCLOAK_FEW_SHOT_EXAMPLES = [
    {
        "id": "seq_kc_i4_case_collision",
        "description": "Test if Keycloak case-insensitive usernames cause role leakage",
        "invariant_hypothesis": "I4: Case-different usernames should not share roles",
        "primary_invariant": "I4",
        "cve_analog": "none",
        "events": [
            {"event_type": "create_realm", "params": {"realm": "valence-i4-case", "enabled": True}, "auth_as": "admin"},
            {"event_type": "create_client", "params": {
                "realm": "valence-i4-case", "client_id": "test-client", "client_secret": "test-secret",
                "enabled": True, "direct_access_grants": True, "public_client": False
            }, "auth_as": "admin"},
            {"event_type": "create_user", "params": {
                "realm": "valence-i4-case", "username": "Admin", "enabled": True,
                "email": "admin@test.local",
                "credentials": [{"type": "password", "value": "admin-pass", "temporary": False}]
            }, "auth_as": "admin", "captures": {"admin_user_id": "user_id"}},
            {"event_type": "create_policy", "params": {"realm": "valence-i4-case", "role_name": "super-admin"}, "auth_as": "admin"},
            {"event_type": "login_with_password", "params": {
                "realm": "valence-i4-case", "username": "Admin", "password": "admin-pass",
                "client_id": "test-client", "client_secret": "test-secret",
                "grant_type": "password", "scope": "openid"
            }, "auth_as": "user_Admin"},
            {"event_type": "verify_granted_identity", "params": {"realm": "valence-i4-case"},
             "auth_as": "session_user_Admin",
             "captures": {"admin_username": "display_name", "admin_sub": "identity_id", "admin_roles": "granted_policies"}},
        ],
        "oracle_checks": [
            {"check_id": "kc_case_roles", "invariant": "I4",
             "assertion": "admin_roles does not include unexpected roles from case-variant user",
             "violation_description": "Case-insensitive username collision caused role leakage"}
        ]
    }
]

CASDOOR_FEW_SHOT_EXAMPLES = [
    {
        "id": "seq_casdoor_i4_two_user_identity_check",
        "description": "Create two users in test-org, login as each, verify they map to distinct identities",
        "invariant_hypothesis": "I4: Different upstream principals must map to different downstream identities",
        "primary_invariant": "I4",
        "cve_analog": "none",
        "events": [
            {"event_type": "create_identity_user", "params": {
                "owner": "test-org", "name": "user_alpha", "displayName": "Alpha User",
                "password": "Alpha123456", "email": "alpha@test.local", "type": "normal-user",
                "signupApplication": "app-test"
            }, "auth_as": "admin", "phase": "setup"},
            {"event_type": "create_identity_user", "params": {
                "owner": "test-org", "name": "user_beta", "displayName": "Beta User",
                "password": "Beta123456", "email": "beta@test.local", "type": "normal-user",
                "signupApplication": "app-test"
            }, "auth_as": "admin", "phase": "setup"},
            {"event_type": "login_with_password", "params": {
                "application": "app-test", "organization": "test-org",
                "username": "user_alpha", "password": "Alpha123456", "type": "login"
            }, "auth_as": "user_A", "phase": "login"},
            {"event_type": "verify_granted_identity", "params": {}, "auth_as": "session_user_A", "phase": "verify"},
            {"event_type": "login_with_password", "params": {
                "application": "app-test", "organization": "test-org",
                "username": "user_beta", "password": "Beta123456", "type": "login"
            }, "auth_as": "user_B", "phase": "login"},
            {"event_type": "verify_granted_identity", "params": {}, "auth_as": "session_user_B", "phase": "verify"},
        ],
        "oracle_checks": [
            {"check_id": "i4_distinct_ids", "invariant": "I4",
             "assertion": "user_A_entity_id != user_B_entity_id",
             "violation_description": "Two different users mapped to same identity — I4 principal binding violation"}
        ]
    },
    {
        "id": "seq_casdoor_i5_token_exchange_cross_client",
        "description": "Obtain a token for app-test (source), then attempt token exchange at a different application (target) to test audience/client binding",
        "invariant_hypothesis": "I5: Token exchange must not allow a token minted for one client to be accepted by a different client without explicit audience delegation",
        "primary_invariant": "I5",
        "cve_analog": "none",
        "events": [
            {"event_type": "create_application", "params": {
                "owner": "admin", "name": "app-target-i5", "displayName": "I5 Target App",
                "organization": "test-org",
                "clientId": "target_i5_cid", "clientSecret": "target_i5_sec",
                "grantTypes": ["authorization_code", "password", "urn:ietf:params:oauth:grant-type:token-exchange"],
                "enablePassword": True, "cert": "cert-built-in", "tokenFormat": "JWT",
                "redirectUris": ["http://localhost:8000/callback"], "expireInHours": 168
            }, "auth_as": "admin", "phase": "setup"},
            {"event_type": "create_user", "params": {
                "owner": "test-org", "name": "i5_exchange_user", "displayName": "I5 User",
                "password": "I5ExchPwd123456", "email": "i5exch@test.local",
                "type": "normal-user", "signupApplication": "app-test"
            }, "auth_as": "admin", "phase": "setup"},
            {"event_type": "login_with_password", "params": {
                "grant_type": "password",
                "username": "i5_exchange_user", "password": "I5ExchPwd123456",
                "scope": "openid profile email"
            }, "auth_as": "user_source", "phase": "login"},
            {"event_type": "verify_granted_identity", "params": {}, "auth_as": "session_user_source", "phase": "verify"},
            {"event_type": "token_exchange", "params": {
                "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
                "scope": "openid profile email"
            }, "auth_as": "user_exchanged_target", "phase": "login",
             "note": "Exchange source token at target app — executor auto-resolves subject_token and client_id"},
            {"event_type": "verify_granted_identity", "params": {}, "auth_as": "session_user_exchanged_target", "phase": "verify"},
        ],
        "oracle_checks": [
            {"check_id": "i5_source_login_ok", "invariant": "I5",
             "assertion": "user_source_login_status < 400",
             "violation_description": "Source password login failed — cannot test token exchange"},
            {"check_id": "i5_cross_client_exchange_rejected", "invariant": "I5",
             "assertion": "user_exchanged_target_login_status >= 400",
             "violation_description": "Token exchange accepted a subject token from a different client — audience/client binding violation"}
        ]
    },
]


ZITADEL_JWT_IDP_FEW_SHOT = [
    {
        "id": "example_i2_missing_required_claim_bypass",
        "description": "Freshness: if a required temporal claim is absent from the token, does the broker skip the check or reject?",
        "invariant_hypothesis": "I2: Tokens missing mandatory freshness claims (e.g. exp, iat, nbf) must be rejected, not silently accepted with no time bound.",
        "primary_invariant": "I2",
        "cve_analog": "none",
        "events": [
            {"event_type": "mint_custom_jwt", "params": {"sub": "control-user", "iss": "{{mock_idp_issuer}}", "exp": "{{now_epoch_plus_3600}}", "iat": "{{now_epoch}}", "email": "control@test.local"}, "auth_as": "admin", "captures": {"control_jwt": "minted_token"}, "phase": "setup"},
            {"event_type": "mint_custom_jwt", "params": {"sub": "attack-user", "iss": "{{mock_idp_issuer}}", "iat": "{{now_epoch}}", "email": "attack@test.local"}, "auth_as": "admin", "captures": {"attack_jwt_no_exp": "minted_token"}, "phase": "setup",
             "note": "Deliberately omit exp — if the broker skips expiry check when exp is absent, this token lives forever"},
            {"event_type": "start_idp_intent", "params": {"idp_id": "{{jwt_idp_id}}", "success_url": "http://localhost:8085/idp/success", "failure_url": "http://localhost:8085/idp/failure"}, "auth_as": "admin", "captures": {"control_auth_url": "auth_url"}, "phase": "login"},
            {"event_type": "complete_jwt_idp_login", "params": {"auth_request_id": "{{control_auth_url_authRequestID}}", "user_agent_id": "{{control_auth_url_userAgentID}}", "jwt_token": "{{control_jwt}}"}, "auth_as": "user_control", "captures": {"control_status": "http_status"}, "phase": "login"},
            {"event_type": "start_idp_intent", "params": {"idp_id": "{{jwt_idp_id}}", "success_url": "http://localhost:8085/idp/success", "failure_url": "http://localhost:8085/idp/failure"}, "auth_as": "admin", "captures": {"attack_auth_url": "auth_url"}, "phase": "login"},
            {"event_type": "complete_jwt_idp_login", "params": {"auth_request_id": "{{attack_auth_url_authRequestID}}", "user_agent_id": "{{attack_auth_url_userAgentID}}", "jwt_token": "{{attack_jwt_no_exp}}"}, "auth_as": "user_attack", "captures": {"attack_status": "http_status"}, "phase": "login"},
        ],
        "oracle_checks": [
            {"check_id": "i2_control_accepted", "invariant": "I2", "assertion": "control_status == 200",
             "violation_description": "Control token with all required claims should be accepted"},
            {"check_id": "i2_missing_exp_rejected", "invariant": "I2", "assertion": "attack_status >= 400",
             "violation_description": "Token missing exp was accepted — the broker skips the expiry check when exp is absent, allowing indefinite token validity"},
        ],
    },
    {
        "id": "example_i2_missing_iat_bypass",
        "description": "Freshness: does the broker enforce iat presence or silently skip issuance-time freshness when iat is missing?",
        "invariant_hypothesis": "I2: A token with valid signature and issuer but missing iat must be rejected; silent acceptance means the 1-hour freshness window is bypassed.",
        "primary_invariant": "I2",
        "cve_analog": "none",
        "events": [
            {"event_type": "mint_custom_jwt", "params": {"sub": "iat-ctrl", "iss": "{{mock_idp_issuer}}", "exp": "{{now_epoch_plus_3600}}", "iat": "{{now_epoch}}", "email": "iat-ctrl@test.local"}, "auth_as": "admin", "captures": {"ctrl_jwt": "minted_token"}, "phase": "setup"},
            {"event_type": "mint_custom_jwt", "params": {"sub": "iat-atk", "iss": "{{mock_idp_issuer}}", "exp": "{{now_epoch_plus_3600}}", "email": "iat-atk@test.local"}, "auth_as": "admin", "captures": {"atk_jwt_no_iat": "minted_token"}, "phase": "setup",
             "note": "Deliberately omit iat — if the broker skips freshness check when iat is absent, stale tokens are accepted forever"},
            {"event_type": "start_idp_intent", "params": {"idp_id": "{{jwt_idp_id}}", "success_url": "http://localhost:8085/idp/success", "failure_url": "http://localhost:8085/idp/failure"}, "auth_as": "admin", "captures": {"ctrl_auth_url": "auth_url"}, "phase": "login"},
            {"event_type": "complete_jwt_idp_login", "params": {"auth_request_id": "{{ctrl_auth_url_authRequestID}}", "user_agent_id": "{{ctrl_auth_url_userAgentID}}", "jwt_token": "{{ctrl_jwt}}"}, "auth_as": "user_ctrl", "captures": {"ctrl_login_status": "http_status"}, "phase": "login"},
            {"event_type": "start_idp_intent", "params": {"idp_id": "{{jwt_idp_id}}", "success_url": "http://localhost:8085/idp/success", "failure_url": "http://localhost:8085/idp/failure"}, "auth_as": "admin", "captures": {"atk_auth_url": "auth_url"}, "phase": "login"},
            {"event_type": "complete_jwt_idp_login", "params": {"auth_request_id": "{{atk_auth_url_authRequestID}}", "user_agent_id": "{{atk_auth_url_userAgentID}}", "jwt_token": "{{atk_jwt_no_iat}}"}, "auth_as": "user_atk", "captures": {"atk_login_status": "http_status"}, "phase": "login"},
        ],
        "oracle_checks": [
            {"check_id": "i2_iat_control_ok", "invariant": "I2", "assertion": "ctrl_login_status == 200",
             "violation_description": "Control token with all required claims should be accepted"},
            {"check_id": "i2_missing_iat_rejected", "invariant": "I2", "assertion": "atk_login_status >= 400",
             "violation_description": "Token missing iat was accepted — the broker skips the issuance-time freshness check when iat is absent"},
        ],
    },
]


def _get_examples_for_profile(profile, proto_ops: dict) -> list:
    """Select appropriate few-shot examples based on platform."""
    if profile is None:
        return PROFILE_FEW_SHOT_EXAMPLES

    if profile.name == "keycloak":
        uma_ops = {"obtain_rpt_uma_ticket", "create_protected_resource", "create_permission_ticket"}
        has_uma = bool(uma_ops & set(proto_ops.keys()))
        has_reqobj = "test_request_object" in proto_ops
        base = list(KEYCLOAK_FEW_SHOT_EXAMPLES)
        if has_reqobj:
            base.append(KEYCLOAK_OIDC_REQUEST_OBJECT_EXAMPLE)
        if has_uma:
            return [KEYCLOAK_UMA_FEW_SHOT] + base
        return base
    elif profile.name == "casdoor":
        return CASDOOR_FEW_SHOT_EXAMPLES
    elif profile.name == "zitadel":
        has_jwt_idp = "complete_jwt_idp_login" in proto_ops
        base = list(PROFILE_FEW_SHOT_EXAMPLES)
        if has_jwt_idp:
            base.extend(ZITADEL_JWT_IDP_FEW_SHOT)
        return base
    else:
        return PROFILE_FEW_SHOT_EXAMPLES


def _get_capture_suffix(op_name: str, abstract_key: str) -> str:
    """Map abstract response_map key to the capture variable suffix.

    Must match the abstract_to_suffix mappings in
    SequenceExecutor._ensure_verify_captures.
    """
    SUFFIX_MAP = {
        "verify_granted_identity": {
            "identity_id": "entity_id",
            "identity_name": "identity_name",
            "display_name": "display_name",
            "granted_policies": "policies",
            "identity_policies": "identity_policies",
            "metadata": "meta",
            "num_uses": "num_uses",
            "email": "email",
            "groups": "groups",
        },
        "verify_entity_details": {
            "entity_name": "entity_name",
            "entity_id": "entity_id",
            "entity_aliases": "entity_aliases",
            "entity_policies": "entity_policies",
            "entity_group_ids": "entity_group_ids",
            "email": "email",
            "enabled": "enabled",
            "entity_groups": "entity_groups",
        },
        "introspect_token": {
            "active": "active",
            "identity_id": "entity_id",
            "granted_policies": "policies",
            "client_roles": "client_roles",
            "scope": "scope",
            "username": "username",
        },
        "session_token_inspect": {
            "active": "active",
            "identity_id": "entity_id",
            "scope": "scope",
            "token_type": "token_type",
            "exp": "exp",
            "iat": "iat",
            "aud": "aud",
            "iss": "iss",
        },
        "enforce_permission": {
            "allowed": "allowed",
            "status": "status",
        },
        "access_test": {
            "tools": "tools",
            "error_code": "error_code",
            "error_message": "error_message",
            "required_scope": "required_scope",
            "granted_scopes": "granted_scopes",
        },
    }
    op_map = SUFFIX_MAP.get(op_name, {})
    return op_map.get(abstract_key, abstract_key)


class PromptBuilder:
    """Builds LLM prompts for event sequence generation.

    Shared between CoverageStrategy and AttackStrategy.
    Parameterized by PlatformProfile and example configuration
    for clean ablation experiments.
    """

    def __init__(self, profile, protocol: str = "oidc_jwt"):
        self.profile = profile
        self.protocol = protocol

    def _build_env_defaults_section(self) -> str:
        """Build environment defaults section from profile.

        Tells the LLM what actual deployment values to use for client_id,
        redirect_uri, connector_id, etc. Without these, the LLM invents
        values that don't match the running platform.
        """
        env = getattr(self.profile, 'environment_defaults', None)
        if not env:
            # Try dict-style access
            try:
                env = self.profile.environment_defaults
            except (AttributeError, KeyError):
                return ""
        if not env:
            return ""

        lines = [
            "\n## Environment Configuration (USE THESE VALUES)",
            "The test environment has these pre-configured values.",
            "You MUST use these exact values in your sequences — do NOT invent your own:",
        ]
        for k, v in env.items():
            lines.append(f"  {k}: {json.dumps(v)}")
        lines.append("")
        return "\n".join(lines)

    def build_system_prompt(self, use_examples: bool = True,
                            max_examples: int = -1,
                            use_invariants: bool = True) -> str:
        """Build the platform-aware system prompt.

        This contains: platform operations, invariant definitions,
        assertion syntax, capture naming rules, and optionally examples.

        Args:
            use_examples: When False, omit the Few-Shot Examples section entirely.
            max_examples: When > 0, include only the first N examples.
            use_invariants: When False, omit the I1-I5 invariant definitions section
                (used for G_blind baseline in RQ1 ablation).
        """
        if self.profile:
            return self._build_profile_prompt(use_examples, max_examples, use_invariants)
        else:
            return self._build_legacy_prompt(use_examples, max_examples, use_invariants)

    def _build_profile_prompt(self, use_examples: bool, max_examples: int,
                              use_invariants: bool = True) -> str:
        """Build protocol-abstracted prompt from PlatformProfile."""
        _load_abstractions()
        protocol = self.protocol

        invariant_text = "\n".join(
            f"  {k}: {v}" for k, v in INVARIANT_DEFINITIONS.items()
        )

        proto_ops = self.profile.api_mapping.get(protocol, {})

        # Build ops text — only show ops in profile
        profile_op_names = set(proto_ops.keys())
        ops_text = "\n".join(
            f"  {name}: {desc}"
            for name, desc in _PROTOCOL_OPERATIONS.items()
            if name in profile_op_names
        )
        for op_name in profile_op_names:
            if op_name not in _PROTOCOL_OPERATIONS:
                ops_text += f"\n  {op_name}: (platform-specific operation)"

        # Inject virtual operations as synthetic APIEndpoints so they appear in
        # the same format as real operations (LLM follows api_mapping structure).
        if protocol in ("oidc_jwt", "oidc"):
            from src.models.platform_profile import APIEndpoint as _AE
            _virtual_ep = _AE(
                method="GET",
                path="/realms/{realm}/protocol/openid-connect/auth",
                body_map={
                    "client_id": "client_id",
                    "redirect_uri": "redirect_uri",
                    "scope": "scope",
                    "response_type": "response_type",
                    "request_object_alg": "request_object_alg",
                },
                response_map={"accepted": "accepted", "rejected": "rejected", "http_status": "http_status"},
                auth="none",
                note="SPECIAL: executor builds a JWT with specified alg (default 'none') and sends as 'request' query param. For I1: create PUBLIC client WITHOUT requestObjectSignatureAlg, then test_request_object with request_object_alg='none'. Assertion: 'f1_accepted != True'.",
            )
            proto_ops["test_request_object"] = _virtual_ep
            ops_text += "\n  test_request_object: Send unsigned JWT (alg=none) to OIDC auth endpoint — tests request object bypass (I1)"

        # Build detailed parameter guide
        ops_detail_lines = []
        for op_name, endpoint in proto_ops.items():
            content_type = getattr(endpoint, "content_type", "json")
            path_params = _re.findall(r"\{(\w+)\}", endpoint.path)
            body_keys = list(endpoint.body_map.keys()) if endpoint.body_map else []
            resp_keys = list(endpoint.response_map.keys()) if endpoint.response_map else []

            line = f"  {op_name}:\n"
            line += f"    HTTP: {endpoint.method} {endpoint.path}\n"
            if content_type != "json":
                line += f"    Content-Type: {content_type}\n"
            if path_params:
                line += f"    Path params (MUST include in params): {path_params}\n"
            if body_keys:
                line += f"    Body params: {body_keys}\n"
            if resp_keys:
                line += f"    Response captures: {resp_keys}\n"

            if op_name.startswith("login_"):
                if "username" in body_keys and "password" in body_keys:
                    line += f"    ⚠️ This is a PASSWORD login. Params: username, password, client_id, grant_type='password'\n"
                    line += f"    ⚠️ Do NOT use jwt_claims. Send username/password directly in params.\n"
                elif "token" in body_keys or "jwt" in (endpoint.body_map or {}).values():
                    line += f"    ⚠️ This is a JWT login. Provide jwt_claims in params — executor builds the JWT.\n"

            ops_detail_lines.append(line)

        # (Virtual operations like test_request_object are already in proto_ops
        #  and rendered by the loop above — no duplicate injection needed.)

        ops_params_guide = "\n".join(ops_detail_lines) if ops_detail_lines else "  (none)"

        # Load verification API spec
        verify_guide = ""
        spec_path = os.path.join(
            os.path.dirname(__file__), "..", "llm", "platform_apis",
            f"{self.profile.name}_api_spec.json"
        )
        try:
            with open(spec_path) as f:
                spec = json.load(f)

            profile_ops = set(proto_ops.keys())
            verify_guide = "\n## MANDATORY Verification Operations\n"
            verify_guide += "After EVERY login event, you MUST include verify events.\n"
            verify_guide += "These verify operations are available on this platform:\n\n"

            for cat_name, endpoints in spec.get("verification_apis", {}).items():
                if not endpoints:
                    continue
                verify_guide += f"### {cat_name}\n"
                for ep in endpoints[:5]:
                    ep_name = ep.get("name", "")
                    if ep_name not in profile_ops:
                        continue
                    fields = list(ep.get("response_fields", {}).keys())[:6]
                    verify_guide += (
                        f"  - {ep_name}: {ep.get('method', 'GET')} {ep.get('path', '?')}\n"
                        f"    Captures: {', '.join(fields)}\n"
                        f"    Relevant to: {', '.join(ep.get('invariant_relevance', []))}\n"
                    )
                verify_guide += "\n"

            recipes = spec.get("verification_recipes", {})
            if recipes:
                verify_guide += "### Verification Recipes (recommended sequences)\n"
                for name, recipe in list(recipes.items())[:3]:
                    steps = recipe.get("api_sequence", [])
                    valid_steps = [s for s in steps if s in profile_ops]
                    if not valid_steps:
                        continue
                    verify_guide += f"  - {name}: {recipe.get('description', '')}\n"
                    verify_guide += f"    Steps: {' → '.join(valid_steps)}\n"

        except Exception:
            verify_guide = "\n(Verification API spec not available — include verify_granted_identity after login)\n"

        constraints = self.profile.get_constraints_text(include_security_hints=use_invariants) or "(none)"

        # Build login instruction
        login_ops = [op for op in proto_ops if op.startswith("login_")]
        login_instructions = []
        for lop in login_ops:
            ep = proto_ops[lop]
            body_keys = list(ep.body_map.keys()) if ep.body_map else []
            if "username" in body_keys:
                login_instructions.append(
                    f"For {lop}: provide username, password, client_id, grant_type in params (NOT jwt_claims)"
                )
            elif "token" in body_keys or "jwt" in (ep.body_map or {}).values():
                login_instructions.append(
                    f"For {lop}: provide jwt_claims dict in params — the executor builds the JWT"
                )
        login_rule = "\n".join(f"5. {instr}" for instr in login_instructions) if login_instructions else \
            "5. For login events, provide the required params as shown in the operation reference above"

        # UMA guide (Keycloak-specific)
        uma_guide = ""
        if self.profile.name == "keycloak":
            uma_guide = """
## UMA Authorization Flow (Multi-Step)
For UMA testing, sequences MUST follow this flow:
1. create_realm → create_client (with authorization_services_enabled=true)
2. create_user(s) — resource owner + requester
3. obtain_pat_client_credentials — get PAT (Protection API Token)
4. create_protected_resource — register resource with scopes
5. create_uma_policy_permission_for_resource — set access rules
6. login_with_password — requester gets access token
7. obtain_rpt_uma_ticket — exchange for RPT (Requesting Party Token)
8. introspect_token — verify what permissions RPT contains

Key params for obtain_rpt_uma_ticket:
  grant_type: "urn:ietf:params:oauth:grant-type:uma-ticket"
  audience: client_id of resource server
  permission: "RESOURCE_ID#SCOPE" (can repeat)
  response_mode: "permissions" (to see granted permissions) or "decision" (boolean)

CRITICAL UMA setup requirements:
- Client MUST have: service_accounts_enabled=true (for client_credentials grant)
- Client MUST have: authorization_services_enabled=true
- PAT scope MUST include: uma_protection
- PAT grant_type: "client_credentials" (NOT "password")

PAT auth: use session token from obtain_pat_client_credentials
RPT auth: use session token from requester's login_with_password

## Token Exchange Flow (for I5 audience binding testing)
Keycloak supports RFC 8693 token exchange. To test audience binding:
1. create_realm → create TWO clients (client-A and client-B)
2. create_user → login_with_password (for client-A) → get access_token
3. token_exchange: subject_token={access_token_from_client_A}, audience=client-B, client_id=client-B, client_secret=client-B-secret
4. If exchange succeeds, introspect the exchanged token to check audience
This tests whether the broker ignores audience validation on subject_token during token exchange.

## SAML I2 Freshness Testing (preferred over UMA for replay tests)
For I2 SAML assertion replay and OneTimeUse, use saml_login — NOT UMA RPT flows:
### OneTimeUse replay:
1. create_tenant → enable_auth_method (SAML IdP)
2. saml_login with include_onetimeuse=true, fixed_assertion_id="_replay_onetimeuse" (first — should succeed)
3. saml_login with include_onetimeuse=true, fixed_assertion_id="_replay_onetimeuse" (SAME ID — should be REJECTED)
4. verify: if second login also succeeds, OneTimeUse is NOT enforced (I2 violation)
### Assertion ID replay:
1. create_tenant → enable_auth_method (SAML IdP)
2. saml_login with fixed_assertion_id="_replay_id_test" (first — should succeed)
3. saml_login with fixed_assertion_id="_replay_id_test" (SAME ID — should be REJECTED)
4. verify: if second login succeeds, assertion ID replay is not detected
### Missing Conditions (also tests I5):
1. create_tenant → enable_auth_method (SAML IdP)
2. saml_login with remove_conditions=true — if accepted, no temporal or audience constraints (I2/I5 violation)
UMA flows have complex multi-step setup that often fails. SAML assertion replay
directly tests I2 freshness without UMA infrastructure.

## SAML saml_login Special Parameters
The executor auto-generates a forged SAMLResponse signed with an attacker cert.
You can control assertion content with these EXTRA params (add to saml_login params):
- remove_conditions: true → omit the <Conditions> element entirely (no audience or time bounds)
- include_onetimeuse: true → add <OneTimeUse/> inside <Conditions> (replay of OneTimeUse assertions)
- fixed_assertion_id: string → use this EXACT string as the Assertion/@ID instead of random UUID.
  For replay testing, use the SAME fixed_assertion_id in TWO saml_login events.
  Example: both saml_login events use fixed_assertion_id="_replay_test" to reuse the same assertion ID.
- idp_entity_id: string → override the Issuer in the assertion (tests issuer mismatch)

## SAML I1 Insecure Default Testing
To test whether SAML broker defaults are insecure:
1. create_tenant (realm)
2. enable_auth_method with providerId="saml" — do NOT set validateSignature, wantAssertionsSigned, or idpEntityId in provider_config. Only set the minimum: singleSignOnServiceUrl (MUST use https:// URL, e.g. "https://fake-idp.invalid/sso" — Keycloak rejects http:// for SSO URLs)
3. saml_login — the executor signs with attacker cert.
4. Oracle: check login_status, NOT identity_id. Brokered SAML login may not complete user
   creation even when the SP accepts the assertion. The acceptance itself is the vulnerability.
   Correct assertion: "user_attacker_login_status == 200" (SP accepted the forged assertion)
   Wrong assertion: "user_attacker_identity_id is not None" (user creation may not complete)

## OIDC Request Object alg=none Testing (I1)
To test if the OIDC auth endpoint accepts unsigned request objects:
1. create_tenant (realm)
2. create_client with publicClient=true, NO requestObjectSignatureAlg configured
3. test_request_object with realm, client_id, request_object_alg="none"
   The executor builds a JWT with alg=none (no signature) and sends it to the auth endpoint.
   response.accepted=true means the auth endpoint silently accepted the unsigned JWT (I1 violation).
   response.rejected=true means the auth endpoint correctly rejected it (secure).
4. Oracle: "f1_accepted != True" (expected: auth endpoint REJECTS the unsigned JWT)
   violation_description: "Auth endpoint accepted alg=none request object without verification"
   captures: {"f1_accepted": "accepted", "f1_status": "http_status"}
   → FAILS when f1_accepted=True → UNEXPECTED → finding!

## IMPORTANT: SAML IdP singleSignOnServiceUrl MUST be https://
Keycloak rejects http:// URLs for singleSignOnServiceUrl with "requires secure connections".
ALWAYS use https:// for provider_config.singleSignOnServiceUrl, e.g. "https://fake-idp.invalid/sso".
"""

        # Build capture variable guide
        capture_guide = "\n## Available Capture Variables\n"
        capture_guide += "When writing oracle_checks assertions, use EXACTLY these variable names.\n"
        capture_guide += "Derivation rule: strip 'session_' from auth_as → that string is the prefix.\n\n"

        # Document login operation captures (http_status, login_success)
        capture_guide += "### After LOGIN events (login_with_password, login_with_jwt, saml_login):\n"
        capture_guide += "Every login event automatically captures these variables:\n"
        capture_guide += "  - {auth_as}_login_success  (bool: True if login HTTP status 2xx/3xx)\n"
        capture_guide += "  - {auth_as}_login_status   (int: HTTP status code of login response)\n"
        capture_guide += "Example: saml_login with auth_as='user_attacker' →\n"
        capture_guide += "  - user_attacker_login_success = True/False\n"
        capture_guide += "  - user_attacker_login_status  = 200/400/403\n\n"
        capture_guide += """\
### CRITICAL: Assertion Polarity Convention

Assertions describe EXPECTED SECURE BEHAVIOR. When the assertion FAILS, it is a
VIOLATION. When the assertion HOLDS, it is BY_DESIGN (secure, no finding).

WRONG: "user_attacker_login_status == 200"  ← describes attack success → HOLDS when vulnerable → BY_DESIGN (no finding!)
RIGHT: "user_attacker_login_status >= 400"  ← describes expected rejection → FAILS when 200 → UNEXPECTED (finding!)

### SAML/Brokered Login Assertion Strategy

For SAML brokered login tests (especially I1 trust-anchor violations):
- The SP accepting a forged/unsigned SAML assertion IS the vulnerability signal.
- Use `login_status` to detect acceptance — do NOT rely only on identity_id from
  verify events, because brokered flows may not complete user creation.

Correct I1 SAML assertion patterns:
  "assertion": "user_attacker_login_status >= 400"
  violation_description: "SP accepted attacker-signed assertion (login should have been rejected)"
  → FAILS when status=200 → UNEXPECTED → finding!

  "assertion": "user_attacker_login_status != 200"
  violation_description: "SP accepted forged assertion without signature validation"
  → FAILS when status=200 → UNEXPECTED → finding!

For I2 replay/missing-conditions tests:
  "assertion": "attacker_replay_login_status >= 400"
  violation_description: "SP accepted replayed/expired assertion"

For I5 over-grant with missing conditions:
  "assertion": "attacker_nocond_login_status >= 400"
  violation_description: "SP accepted assertion without Conditions element"

"""

        capture_guide += "### After VERIFY events:\n"
        verify_ops = {name: ep for name, ep in proto_ops.items()
                      if name.startswith("verify_") or name == "introspect_token"}

        for op_name, endpoint in verify_ops.items():
            if not endpoint.response_map:
                continue
            capture_guide += f"After {op_name} with auth_as='session_user_X':\n"
            for abstract_key in endpoint.response_map:
                suffix = _get_capture_suffix(op_name, abstract_key)
                capture_guide += f"  - user_X_{suffix}  (from response field: {abstract_key})\n"
            capture_guide += "\n"

        capture_guide += """\
## CRITICAL: Oracle Assertion Variable Naming Rule
Capture variable names are formed by: strip 'session_' from the event's auth_as value,
then append the abstract suffix.

Examples — derive the prefix from auth_as EXACTLY, never abbreviate:
  auth_as='session_user_alice'         → prefix='user_alice'
                                         variable: user_alice_entity_id  ✓
  auth_as='session_user_attacker_pwd'  → prefix='user_attacker_pwd'
                                         variable: user_attacker_pwd_entity_id  ✓
                                         NOT attacker_entity_id            ✗  (abbreviated)
                                         NOT attacker_pwd_entity_id        ✗  (missing 'user_')
  auth_as='session_appA'               → prefix='appA'
                                         variable: appA_entity_id          ✓

Before writing any oracle_checks assertion, trace back to the verify event that captured
the variable, read its auth_as, strip 'session_', and use THAT full string as the prefix.
You MUST NOT shorten, truncate, or abbreviate a multi-word prefix.

Correct assertions:
  user_attacker_pwd_entity_id != user_victim_entity_id   ✓
  user_alice_policies contains 'admin-role'               ✓
Wrong — abbreviated names:
  attacker_entity_id != victim_entity_id                  ✗
  alice_username != bob_username  (wrong suffix — use display_name, not username)  ✗
"""

        # Examples section (conditional)
        examples_section = ""
        if use_examples:
            example_list = _get_examples_for_profile(self.profile, proto_ops)
            if max_examples > 0:
                example_list = example_list[:max_examples]
            examples_section = f"\n## Few-Shot Examples\n{json.dumps(example_list, indent=2)}\n"

        invariants_section = ""
        if use_invariants:
            invariants_section = f"\n## The 5 Security Invariants\n{invariant_text}\n"

        return f"""You are generating multi-step test event sequences for a security fuzzer \
targeting {self.profile.name}'s {protocol} authentication.
{invariants_section}
## Available Operations on {self.profile.name} (ONLY these are supported)
{ops_text}

CRITICAL: You MUST ONLY use the operations listed above. Do NOT use operations from other
platforms (e.g. enable_auth_method, configure_jwt_validation, create_policy,
seed_protected_resource are Vault-specific and NOT available on {self.profile.name}).
Any sequence using an unsupported operation will be rejected.

## Operation Parameter Names (REQUIRED — use exactly these key names in params)
Params listed under "path:" MUST be included in the event's params dict so the executor
can substitute them into the API path. Params under "body:" are sent in the request body.
{ops_params_guide}

{self._build_env_defaults_section()}
## Platform: {self.profile.name}
### Platform-Specific Constraints (MUST FOLLOW)
{constraints}

{verify_guide}

{capture_guide}

{uma_guide}

## Event Phases
Every event MUST have a "phase" field:
  - "setup": Create resources, configure auth, create users/roles/groups (runs as admin)
  - "login": Authenticate as a test identity (runs as test user)
  - "verify": Query platform to check what identity/permissions were granted (runs as session or admin)

Sequence structure MUST be: setup* → login+ → verify+
The verify phase MUST include at least verify_granted_identity.

## Rules for Generating Sequences
1. Use ONLY the operation names from "Available Operations" — NOT raw API paths
2. Every sequence MUST have: setup ops → login op → verify ops
3. Every sequence MUST have oracle_checks with concrete assertions
4. Use {{{{variable}}}} syntax to capture and reference values across events
{login_rule}
6. For verify events, specify what fields to capture and what to assert
7. Every event MUST include a "phase" field ("setup", "login", or "verify")
8. NAMING RULE: oracle assertion variable names MUST exactly match the key you declared
   in the event's "captures" dict. Derive from auth_as: strip 'session_', keep the rest
   verbatim as the prefix. Never abbreviate (e.g. auth_as='session_user_attacker_pwd'
   → oracle must use user_attacker_pwd_entity_id, NOT attacker_entity_id).

## Assertion Syntax (STRICT)
Assertions must use ONLY these operators:
  ==, !=, >, <, >=, <=, in, not in, contains, is None, is not None
  AND, OR for combining comparisons

Allowed: alice_sub != bob_sub
Allowed: active == true AND scope != null
Allowed: "admin" in roles
Allowed: status == 403

FORBIDDEN: "is not 200" (use != 200)
FORBIDDEN: "should be" (use ==)
FORBIDDEN: "equals" (use ==)
FORBIDDEN: "greater than" (use >)
FORBIDDEN: natural language descriptions as assertions
FORBIDDEN: abbreviated capture names — if auth_as='session_user_attacker_pwd',
  attacker_entity_id is FORBIDDEN; you MUST write user_attacker_pwd_entity_id

Boolean literals: use true/false (not True/False)
Null literal: use null (not None)
String literals: use quotes ("admin", 'admin')
{examples_section}
## Output Format
Return ONLY valid JSON:
{{
  "sequences": [
    {{
      "id": "seq_XXX",
      "description": "...",
      "invariant_hypothesis": "I4: ...",
      "primary_invariant": "I4",
      "cve_analog": "CVE-XXXX-XXXX or 'none'",
      "events": [...],
      "oracle_checks": [...]
    }}
  ]
}}
"""

    def _build_legacy_prompt(self, use_examples: bool, max_examples: int,
                             use_invariants: bool = True) -> str:
        """DEPRECATED: Build the legacy (non-profile) Vault-specific system prompt."""
        from src.stateful.vault_event_types import get_event_types_json

        spec_path = os.path.join(
            os.path.dirname(__file__), "..", "llm", "platform_apis", "vault_api_spec.json"
        )
        api_summary = ""
        try:
            with open(spec_path) as f:
                spec = json.load(f)
            for cat_name, endpoints in spec.get("verification_apis", {}).items():
                api_summary += f"\n  {cat_name}:\n"
                for ep in endpoints[:4]:
                    fields = ", ".join(list(ep.get("response_fields", {}).keys())[:5])
                    api_summary += f"    - {ep['name']}: {ep['method']} {ep['path']} → {fields}\n"
            api_summary += "\n  Verification Recipes:\n"
            for recipe_name, recipe in spec.get("verification_recipes", {}).items():
                api_summary += f"    - {recipe_name}: {recipe['description'][:100]}\n"
                api_summary += f"      API sequence: {recipe.get('api_sequence', [])}\n"
        except Exception as e:
            logger.warning(f"Could not load API spec: {e}")
            api_summary = "(API spec not available — use general Vault knowledge)"

        invariant_text = "\n".join(
            f"  {k}: {v}" for k, v in INVARIANT_DEFINITIONS.items()
        )
        event_types = json.dumps(get_event_types_json(), indent=2)

        examples_section = ""
        if use_examples:
            # Use the legacy FEW_SHOT_EXAMPLES from sequence_generator for backward compat
            try:
                from src.stateful.sequence_generator import FEW_SHOT_EXAMPLES
                example_list = list(FEW_SHOT_EXAMPLES)
            except ImportError:
                example_list = []
            if max_examples > 0:
                example_list = example_list[:max_examples]
            if example_list:
                examples_section = f"\n## Few-Shot Examples\n{json.dumps(example_list, indent=2)}\n"

        invariants_section = ""
        if use_invariants:
            invariants_section = f"\n## The 5 Security Invariants\n{invariant_text}\n"

        return f"""You are generating multi-step test event sequences for a security fuzzer \
targeting HashiCorp Vault's JWT authentication.
{invariants_section}
## Available Event Types (Vault API operations)
{event_types}

## Vault Verification API Summary (from vault_api_spec.json)
{api_summary}

## Key Vault Concepts for Testing
- Each JWT login creates/uses an Identity Entity with aliases
- Entity aliases link auth mount + claim value to an entity
- Policies come from: (1) role's token_policies, (2) entity's policies, (3) group's policies
- Groups can have aliases mapping external group names (from JWT groups claim) to internal groups
- The user_claim role parameter controls which JWT claim becomes the entity alias name
- bound_audiences, bound_claims, bound_subject restrict which JWTs are accepted
- An empty bound_audiences list may or may not mean "accept any audience" depending on implementation

## Rules for Generating Sequences

1. Every sequence MUST contain at least one "login_jwt" event
2. Every sequence MUST end with "verify_*" events that collect evidence
3. Every sequence MUST have oracle_checks with concrete assertions
4. Use CONCRETE Vault field names from the event registry
5. Use {{{{variable}}}} syntax to reference captured values from earlier events
6. Use jwt_claims dict (not raw jwt string) for login events — the executor builds the JWT
7. Focus on MULTI-STEP interactions: cross-user, cross-config, cross-role
8. DO NOT generate sequences that only test single JWT mutations (we have those already)
9. auth_as for login_jwt should be descriptive: "user_A", "user_B", "attacker"
10. auth_as for verify events after login: "session_user_A", "session_attacker" etc.
11. Include mount accessor retrieval (setup_get_mount_accessor) when creating aliases

## Assertion Syntax (STRICT)
Assertions must use ONLY these operators:
  ==, !=, >, <, >=, <=, in, not in, contains, is None, is not None
  AND, OR for combining comparisons

Allowed: alice_sub != bob_sub
Allowed: active == true AND scope != null
Allowed: "admin" in roles
Allowed: status == 403

FORBIDDEN: "is not 200" (use != 200)
FORBIDDEN: "should be" (use ==)
FORBIDDEN: "equals" (use ==)
FORBIDDEN: "greater than" (use >)
FORBIDDEN: natural language descriptions as assertions
FORBIDDEN: abbreviated capture names — if auth_as='session_user_attacker_pwd',
  attacker_entity_id is FORBIDDEN; you MUST write user_attacker_pwd_entity_id

Boolean literals: use true/false (not True/False)
Null literal: use null (not None)
String literals: use quotes ("admin", 'admin')
{examples_section}
## Output Format
Return ONLY valid JSON:
{{
  "sequences": [
    {{
      "id": "seq_XXX",
      "description": "...",
      "invariant_hypothesis": "I4: ...",
      "primary_invariant": "I4",
      "cve_analog": "CVE-XXXX-XXXX or 'none'",
      "events": [...],
      "oracle_checks": [...]
    }}
  ]
}}
"""

    def build_user_prompt(self, mode_instruction: str,
                          config: GenerationConfig) -> str:
        """Build the user prompt with mode-specific instructions.

        Args:
            mode_instruction: The mode-specific block from the strategy
            config: Generation configuration
        """
        _load_abstractions()

        dedup = ""
        if config.previously_generated:
            dedup = "ALREADY GENERATED (do NOT repeat):\n" + \
                    "\n".join(f"  - {d}" for d in config.previously_generated[-10:])

        # Only include invariant focus when invariants are enabled.
        # When use_invariants=False (blind mode), omit to avoid contaminating G_blind baseline.
        if config.use_invariants:
            invariant_block = f"""Focus invariant: {config.invariant_focus}
Definition: {INVARIANT_DEFINITIONS.get(config.invariant_focus, '')}"""
        else:
            invariant_block = ""

        # Only include attack pattern hints when invariants are enabled.
        # These patterns contain invariant-specific descriptions and must not leak
        # into the blind baseline (use_invariants=False).
        if config.use_invariants:
            hints = config.custom_hints
            if not hints and _CROSS_PLATFORM_ATTACK_PATTERNS:
                raw_hints = _CROSS_PLATFORM_ATTACK_PATTERNS.get(config.invariant_focus, [])
                # Filter out patterns tagged for other protocols
                _exclude = []
                if self.protocol != "oidc_jwt":
                    _exclude.extend(["OIDC flow only", "OIDC redirect", "OIDC callback"])
                if self.protocol != "saml":
                    _exclude.extend(["SAML only", "SAML assertion", "SAMLResponse", "saml_login"])
                hints = [h for h in raw_hints if not any(t in h for t in _exclude)]
            hints_text = "\n".join(f"  - {h}" for h in hints)
            if hints_text.strip():
                # Some patterns describe OIDC authorization code flow mechanics
                # (state parameter, redirect_uri, auth code, PKCE). When the current
                # platform protocol uses direct credential/assertion login (no redirect
                # flow), those ops won't exist in Available Operations. Instruct the LLM
                # to translate the abstract security property to available equivalents.
                translation_note = (
                    "\nNOTE — Protocol translation: Some patterns above may reference "
                    "OIDC authorization code flow concepts (redirect_uri, state parameter, "
                    "auth code exchange, PKCE code_challenge/code_verifier). If those "
                    "operations are NOT listed in Available Operations for this platform, "
                    "translate the abstract security property to an equivalent test using "
                    "the available operations. The invariant property matters, not the "
                    "OIDC-specific mechanism. Examples:\n"
                    "  - 'state_swap / code_injection' (I3 session binding) → role "
                    "confusion: present a JWT obtained for role-A to role-B login, or "
                    "use a token from mount-A on mount-B\n"
                    "  - 'redirect_uri mismatch' (I3) → audience mismatch: JWT with "
                    "wrong aud claim for the configured bound_audiences\n"
                    "  - 'nonce replay / OIDC callback replay' (I2): if oidc_sso_connector_id "
                    "is in environment_defaults, use a saml_login event with "
                    "connector_id={{oidc_sso_connector_id}} and "
                    "mutation_type='i2_oidc_sso_nonce_bypass' — mock IdP omits nonce by default, "
                    "assert user_X_http_status >= 400 (rejection expected). "
                    "Otherwise → JWT replay: submit the same JWT token twice"
                )
                hints_block = f"Mutation patterns to explore:\n{hints_text}{translation_note}"
            else:
                hints_block = ""
        else:
            hints_block = ""

        coverage_text = ""
        if config.coverage_gaps:
            coverage_text = "\nUNCOVERED TEST SPACE (prioritize these):\n" + \
                            "\n".join(f"  - {g}" for g in config.coverage_gaps[:10])

        # Build mode-aware requirements: blind/coverage mode must not mention
        # invariants, attack angles, or assertions (prompt contamination guard).
        if config.use_invariants:
            requirements = """Requirements:
- Each sequence must involve >=2 identities OR >=1 config change + re-auth
- Include setup_get_mount_accessor when you need to create entity/group aliases
- For each verify event, specify what to capture in the "captures" field
- Assertions must reference captured variable names exactly
- Make sequences diverse — different attack angles for the same invariant
- Every event MUST include a "phase" field ("setup", "login", or "verify")
"""
            # Soft diversity hint: nudge LLM to cover different operation types
            # when the platform has specialized operations available.
            if (config.invariant_focus == "I1"
                    and self.protocol in ("oidc_jwt", "oidc")):
                requirements += (
                    "- Diversity: cover BOTH brokered-flow attacks AND direct-endpoint "
                    "attacks (e.g., test_request_object for request object bypass). "
                    "Do not generate 4 brokered-flow sequences — vary the attack surface.\n"
                )
        else:
            requirements = """Requirements:
- Each sequence must involve >=2 identities OR >=1 config change + re-auth
- For each verify event, specify what to capture in the "captures" field
- Make sequences diverse — exercise different API combinations
- Every event MUST include a "phase" field ("setup", "login", or "verify")
"""

        return f"""Generate exactly {config.num_sequences} NEW event sequences.

{mode_instruction}

{invariant_block}

{hints_block}

{dedup}
{coverage_text}

{requirements}"""
