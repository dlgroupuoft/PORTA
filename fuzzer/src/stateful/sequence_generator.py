"""LLM-powered event sequence generator.

This module is now a facade over CoverageStrategy and AttackStrategy.
All shared prompt logic lives in PromptBuilder.
All shared parse/validate logic lives in GenerationStrategy base class.
"""
import json
import logging
import os
from typing import Optional

from src.llm.client import LLMClient
from src.stateful.models import Event, EventSequence, OracleCheck
# Re-export INVARIANT_DEFINITIONS from generation_strategy for backward compat
from src.stateful.generation_strategy import INVARIANT_DEFINITIONS, GenerationConfig
from src.stateful.prompt_builder import (
    PromptBuilder,
    PROFILE_FEW_SHOT_EXAMPLES,
    KEYCLOAK_FEW_SHOT_EXAMPLES,
    KEYCLOAK_UMA_FEW_SHOT,
    CASDOOR_FEW_SHOT_EXAMPLES,
)
from src.stateful.strategies.coverage_strategy import CoverageStrategy
from src.stateful.strategies.attack_strategy import AttackStrategy

logger = logging.getLogger(__name__)

# Lazy import to avoid circular dependency
_PlatformProfile = None
_PROTOCOL_OPERATIONS = None
_CROSS_PLATFORM_ATTACK_PATTERNS = None


def _load_protocol_abstractions():
    global _PlatformProfile, _PROTOCOL_OPERATIONS, _CROSS_PLATFORM_ATTACK_PATTERNS
    if _PlatformProfile is None:
        from src.models.platform_profile import PlatformProfile as PP
        from src.stateful.protocol_operations import (
            PROTOCOL_OPERATIONS as PO,
            CROSS_PLATFORM_ATTACK_PATTERNS as CPAP,
        )
        _PlatformProfile = PP
        _PROTOCOL_OPERATIONS = PO
        _CROSS_PLATFORM_ATTACK_PATTERNS = CPAP

# ---------------------------------------------------------------------------
# Few-shot examples
# ---------------------------------------------------------------------------
FEW_SHOT_EXAMPLES = [
    {
        "id": "example_i4_entity_collision",
        "description": "Two users with different sub (trailing space) both login and check if they map to same entity",
        "invariant_hypothesis": "I4: Two security-distinct principals (different sub values) should map to different entities",
        "primary_invariant": "I4",
        "cve_analog": "CVE-2021-41802",
        "events": [
            {"event_type": "setup_jwt_role", "params": {"role_name": "collision-role", "user_claim": "sub", "groups_claim": "groups", "bound_audiences": ["vault"], "token_policies": ["default"]}, "auth_as": "admin"},
            {"event_type": "login_jwt", "params": {"role": "collision-role", "jwt_claims": {"sub": "alice@corp.com", "aud": "vault", "groups": ["devs"]}}, "auth_as": "user_A", "captures": {"user_a_token": "auth.client_token", "user_a_entity": "auth.entity_id"}},
            {"event_type": "login_jwt", "params": {"role": "collision-role", "jwt_claims": {"sub": "alice@corp.com ", "aud": "vault", "groups": ["admins"]}}, "auth_as": "user_B", "captures": {"user_b_token": "auth.client_token", "user_b_entity": "auth.entity_id"}},
            {"event_type": "verify_token_self", "params": {}, "auth_as": "session_user_A", "captures": {"user_a_policies": "data.policies", "user_a_identity_policies": "data.identity_policies"}},
            {"event_type": "verify_token_self", "params": {}, "auth_as": "session_user_B", "captures": {"user_b_policies": "data.policies", "user_b_identity_policies": "data.identity_policies"}},
            {"event_type": "verify_entity", "params": {"entity_id": "{{user_a_entity}}"}, "auth_as": "admin", "captures": {"user_a_entity_name": "data.name", "user_a_aliases": "data.aliases"}},
            {"event_type": "verify_entity", "params": {"entity_id": "{{user_b_entity}}"}, "auth_as": "admin", "captures": {"user_b_entity_name": "data.name", "user_b_aliases": "data.aliases"}}
        ],
        "oracle_checks": [
            {"check_id": "i4_entity_distinct", "invariant": "I4", "assertion": "user_a_entity != user_b_entity", "violation_description": "Two users with different sub values (one has trailing space) collapsed to same Vault entity — principal binding violation", "cve_analog": "CVE-2021-41802"}
        ]
    },
    {
        "id": "example_i5_empty_bound_audiences",
        "description": "Set bound_audiences to empty list and verify if any audience is accepted",
        "invariant_hypothesis": "I5: Empty bound_audiences should deny all (not allow all)",
        "primary_invariant": "I5",
        "cve_analog": "CVE-2024-7594",
        "events": [
            {"event_type": "setup_policy", "params": {"policy_name": "sensitive-policy", "policy": "path \"secret/data/sensitive/*\" { capabilities = [\"read\"] }"}, "auth_as": "admin"},
            {"event_type": "setup_secret", "params": {"secret_path": "sensitive/test", "data": {"secret": "classified"}}, "auth_as": "admin"},
            {"event_type": "setup_jwt_role", "params": {"role_name": "aud-test-role", "user_claim": "sub", "bound_audiences": [], "token_policies": ["sensitive-policy"]}, "auth_as": "admin"},
            {"event_type": "login_jwt", "params": {"role": "aud-test-role", "jwt_claims": {"sub": "attacker", "aud": "completely-wrong-audience"}}, "auth_as": "attacker", "captures": {"attacker_token": "auth.client_token", "attacker_login_status": "http_status"}, "expected_outcome": "any"},
            {"event_type": "verify_read_secret", "params": {"secret_path": "sensitive/test"}, "auth_as": "session_attacker", "captures": {"attacker_access_status": "http_status"}}
        ],
        "oracle_checks": [
            {"check_id": "i5_empty_aud", "invariant": "I5", "assertion": "attacker_login_success == False", "violation_description": "Empty bound_audiences accepted login with arbitrary audience — authorization bypass. Should deny all when no audiences are bound.", "cve_analog": "CVE-2024-7594"}
        ]
    },
    {
        "id": "example_i5_group_policy_escalation",
        "description": "Login with groups claim mapped to privileged identity group",
        "invariant_hypothesis": "I5: Group claim mapping should not grant policies beyond role's token_policies",
        "primary_invariant": "I5",
        "cve_analog": "CVE-2025-1391",
        "events": [
            {"event_type": "setup_policy", "params": {"policy_name": "admin-secrets", "policy": "path \"secret/data/admin/*\" { capabilities = [\"read\", \"list\"] }"}, "auth_as": "admin"},
            {"event_type": "setup_policy", "params": {"policy_name": "user-secrets", "policy": "path \"secret/data/users/*\" { capabilities = [\"read\"] }"}, "auth_as": "admin"},
            {"event_type": "setup_group", "params": {"name": "vault-admins", "policies": ["admin-secrets"]}, "auth_as": "admin", "captures": {"admin_group_id": "data.id"}},
            {"event_type": "setup_secret", "params": {"secret_path": "admin/flag", "data": {"flag": "admin-only-data"}}, "auth_as": "admin"},
            {"event_type": "setup_get_mount_accessor", "params": {}, "auth_as": "admin", "captures": {"jwt_accessor": "jwt/.accessor"}},
            {"event_type": "setup_group_alias", "params": {"name": "privileged-group", "mount_accessor": "{{jwt_accessor}}", "canonical_id": "{{admin_group_id}}"}, "auth_as": "admin"},
            {"event_type": "setup_jwt_role", "params": {"role_name": "group-test-role", "user_claim": "sub", "groups_claim": "groups", "bound_audiences": ["vault"], "token_policies": ["user-secrets"]}, "auth_as": "admin"},
            {"event_type": "login_jwt", "params": {"role": "group-test-role", "jwt_claims": {"sub": "regular-user", "aud": "vault", "groups": ["privileged-group"]}}, "auth_as": "user_A", "captures": {"user_a_token": "auth.client_token", "user_a_entity": "auth.entity_id"}},
            {"event_type": "verify_token_self", "params": {}, "auth_as": "session_user_A", "captures": {"user_a_policies": "data.policies", "user_a_identity_policies": "data.identity_policies"}},
            {"event_type": "verify_read_secret", "params": {"secret_path": "admin/flag"}, "auth_as": "session_user_A", "captures": {"admin_access_status": "http_status"}}
        ],
        "oracle_checks": [
            {"check_id": "i5_group_escalation", "invariant": "I5", "assertion": "admin_access_status == 403", "violation_description": "User with token_policies=['user-secrets'] accessed admin secrets via group claim mapping — authorization binding violation. Group-based policy escalation.", "cve_analog": "CVE-2025-1391"}
        ]
    }
]

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
    },
    {
        "id": "example_i5_token_exchange_scope_escalation",
        "description": "Login with limited scope, then token exchange with expanded scope — tests whether platform validates scope against original authorization",
        "invariant_hypothesis": "I5: Token exchange must not grant broader scope than original authorization",
        "primary_invariant": "I5",
        "cve_analog": "none",
        "events": [
            {"event_type": "login_with_mock", "params": {"scope": "openid email", "connector_id": "mock"}, "auth_as": "user_limited", "captures": {"limited_access_token": "access_token"}},
            {"event_type": "token_exchange", "params": {
                "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                "subject_token": "{{limited_access_token}}",
                "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
                "connector_id": "mock",
                "scope": "openid email groups profile federated:id",
                "requested_token_type": "urn:ietf:params:oauth:token-type:id_token"
            }, "auth_as": "user_escalated", "captures": {"escalated_token": "access_token"}}
        ],
        "oracle_checks": [
            {"check_id": "i5_scope_escalation_baseline", "invariant": "I5",
             "assertion": "user_limited_session_token is not None",
             "violation_description": "Baseline: limited-scope login must succeed"},
            {"check_id": "i5_scope_escalation", "invariant": "I5",
             "assertion": "user_escalated_session_token is None OR user_escalated_http_status != 200",
             "violation_description": "Token exchange with expanded scope should be rejected or return limited claims. If accepted with expanded claims, scope escalation occurred (RFC 8693 violation)."}
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
        # Phase: setup — create realm, client with authz enabled, users
        {"event_type": "create_realm", "params": {"realm": "uma-test", "enabled": True}, "auth_as": "admin", "phase": "setup"},
        {"event_type": "create_client", "params": {
            "realm": "uma-test",
            "client_id": "resource-server",
            "client_secret": "rs-secret",
            "enabled": True,
            "public_client": False,
            "direct_access_grants": True,
            "standard_flow": True,
            "authorization_services_enabled": True,
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

        # Phase: setup — obtain PAT and register resource
        {"event_type": "obtain_pat_client_credentials", "params": {
            "realm": "uma-test",
            "grant_type": "client_credentials",
            "client_id": "resource-server",
            "client_secret": "rs-secret",
            "scope": "openid"
        }, "auth_as": "pat_client", "phase": "setup",
         "captures": {"pat_token": "session_token"}},

        {"event_type": "create_protected_resource", "params": {
            "realm": "uma-test",
            "name": "Document A",
            "resource_scopes": ["read", "write"],
            "owner": "resource-owner",
            "owner_managed_access": True
        }, "auth_as": "session_pat_client", "phase": "setup",
         "captures": {"resource_id": "resource_id"}},

        # Phase: setup — create UMA policy (only read scope for requester)
        {"event_type": "create_uma_policy_permission_for_resource", "params": {
            "realm": "uma-test",
            "resource_id": "{{resource_id}}",
            "name": "read-only-policy",
            "scopes": ["read"],
            "roles": [],
            "groups": [],
            "clients": []
        }, "auth_as": "session_pat_client", "phase": "setup"},

        # Phase: login — requester gets access token
        {"event_type": "login_with_password", "params": {
            "realm": "uma-test",
            "username": "requester",
            "password": "req-pass",
            "client_id": "resource-server",
            "client_secret": "rs-secret",
            "grant_type": "password",
            "scope": "openid"
        }, "auth_as": "user_requester", "phase": "login"},

        # Phase: login — request RPT with WRITE scope (should be denied or limited to read)
        {"event_type": "obtain_rpt_uma_ticket", "params": {
            "realm": "uma-test",
            "grant_type": "urn:ietf:params:oauth:grant-type:uma-ticket",
            "audience": "resource-server",
            "permission": "{{resource_id}}#write",
            "response_mode": "permissions"
        }, "auth_as": "session_user_requester", "phase": "login",
         "captures": {"rpt_token": "session_token"}},

        # Phase: verify — introspect RPT to check what permissions were granted
        {"event_type": "introspect_token", "params": {
            "realm": "uma-test",
            "token": "{{rpt_token}}",
            "client_id": "resource-server",
            "client_secret": "rs-secret"
        }, "auth_as": "admin", "phase": "verify",
         "captures": {
             "rpt_active": "active",
             "rpt_permissions": "permissions",
             "rpt_scope": "scope"
         }},
    ],
    "oracle_checks": [
        {"check_id": "i5_uma_no_write", "invariant": "I5",
         "assertion": "rpt_permissions does not contain write scope when policy only grants read",
         "violation_description": "RPT contains write permission despite policy only granting read — scope escalation"}
    ]
}


CASDOOR_FEW_SHOT_EXAMPLES = [
    # Example 1: Shows how to create a user, do password login, capture auth code,
    # exchange for token, and verify identity — the basic Casdoor operation chain.
    {
        "id": "seq_casdoor_i4_two_user_identity_check",
        "description": "Create two users in test-org, login as each, verify they map to distinct identities",
        "invariant_hypothesis": "I4: Different upstream principals must map to different downstream identities",
        "primary_invariant": "I4",
        "cve_analog": "none",
        "events": [
            {"event_type": "create_identity_user", "params": {
                "owner": "test-org", "name": "user_alpha",
                "displayName": "Alpha User", "password": "Alpha123456",
                "email": "alpha@test.local", "type": "normal-user",
                "signupApplication": "app-test"
            }, "auth_as": "admin", "phase": "setup"},
            {"event_type": "create_identity_user", "params": {
                "owner": "test-org", "name": "user_beta",
                "displayName": "Beta User", "password": "Beta123456",
                "email": "beta@test.local", "type": "normal-user",
                "signupApplication": "app-test"
            }, "auth_as": "admin", "phase": "setup"},
            {"event_type": "login_with_password", "params": {
                "application": "app-test", "organization": "test-org",
                "username": "user_alpha", "password": "Alpha123456",
                "type": "login"
            }, "auth_as": "user_A", "phase": "login"},
            {"event_type": "verify_granted_identity", "params": {},
             "auth_as": "session_user_A", "phase": "verify"},
            {"event_type": "login_with_password", "params": {
                "application": "app-test", "organization": "test-org",
                "username": "user_beta", "password": "Beta123456",
                "type": "login"
            }, "auth_as": "user_B", "phase": "login"},
            {"event_type": "verify_granted_identity", "params": {},
             "auth_as": "session_user_B", "phase": "verify"},
        ],
        "oracle_checks": [
            {"check_id": "i4_distinct_ids", "invariant": "I4",
             "assertion": "user_A_entity_id != user_B_entity_id",
             "violation_description": "Two different users mapped to same identity — I4 principal binding violation"}
        ]
    },
    # Example 2: Shows SAML login operation — executor auto-generates attacker SAMLResponse.
    # The LLM only specifies target_identity and email; the executor handles cert generation.
    {
        "id": "seq_casdoor_i1_saml_forged_login",
        "description": "SAML login with forged response — verify if platform rejects untrusted cert",
        "invariant_hypothesis": "I1: Platform must reject SAMLResponse signed by untrusted certificate",
        "primary_invariant": "I1",
        "cve_analog": "none",
        "events": [
            {"event_type": "saml_login", "params": {
                "type": "code", "method": "signup",
                "application": "app-built-in", "organization": "built-in",
                "provider": "provider-saml-test",
                "target_identity": "test_user", "email": "test@test.local",
                "state": "casdoor", "redirectUri": "http://localhost:8000/callback"
            }, "auth_as": "user_attacker", "phase": "login",
             "captures": {"saml_login_status": "status", "saml_login_data": "session_token"}},
            {"event_type": "verify_granted_identity", "params": {},
             "auth_as": "session_user_attacker", "phase": "verify"},
        ],
        "oracle_checks": [
            {"check_id": "i1_reject_forged", "invariant": "I1",
             "assertion": "saml_login_status != \"ok\"",
             "violation_description": "Platform accepted SAMLResponse signed with untrusted attacker cert — I1 proof integrity violation"}
        ]
    },
    # Example 3: Shows cross-context token exchange — login in one context, use token in another.
    # Demonstrates value chaining with {{captured_variable}} syntax.
    # login_with_password type=code → auto-exchanged for access_token → use as subject_token
    {
        "id": "seq_casdoor_i5_token_exchange_boundary",
        "description": "Login to get access token (type=code + auto-exchange), attempt token exchange at different application — verify authorization boundary",
        "invariant_hypothesis": "I5: Token exchange must validate that subject_token is authorized for the target application",
        "primary_invariant": "I5",
        "cve_analog": "none",
        "events": [
            {"event_type": "login_with_password", "params": {
                "application": "app-built-in", "organization": "built-in",
                "username": "admin", "password": "123",
                "type": "code",
                "redirectUri": "http://localhost:8000/callback"
            }, "auth_as": "user_source", "phase": "login",
             "captures": {"source_access_token": "session_token"}},
            {"event_type": "exchange_code_for_token", "params": {
                "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                "subject_token": "{{source_access_token}}",
                "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
                "target_application": "app-org-b"
            }, "auth_as": "user_exchange", "phase": "login",
             "captures": {"exchanged_token": "session_token"}},
            {"event_type": "verify_granted_identity", "params": {},
             "auth_as": "session_user_exchange", "phase": "verify"},
        ],
        "oracle_checks": [
            {"check_id": "i5_cross_boundary", "invariant": "I5",
             "assertion": "exchanged_token == null",
             "violation_description": "Token exchange accepted token from different organization/application context — I5 authorization boundary violation"}
        ]
    },
    # Example 4: MFA bypass via SAML binding-rule path 
    {
        "id": "seq_casdoor_i3_saml_mfa_bypass_binding_rule",
        "description": "Enable MFA on user via /api/mfa/setup/enable, verify password login requires MFA, then attempt SAML login via binding-rule path to bypass MFA",
        "invariant_hypothesis": "I3: MFA step must not be skippable by using alternative login path",
        "primary_invariant": "I3",
        "cve_analog": "CVE-2024-45042",
        "events": [
            {"event_type": "create_identity_user", "params": {
                "owner": "test-org", "name": "mfa_victim_seq",
                "displayName": "MFA Victim", "password": "Victim123456",
                "email": "mfa_victim_seq@test.local", "type": "normal-user",
                "signupApplication": "app-test"
            }, "auth_as": "admin", "phase": "setup"},
            {"event_type": "mfa_setup_enable", "params": {
                "owner": "test-org", "name": "mfa_victim_seq",
                "mfaType": "app", "secret": "JBSWY3DPEHPK3PXP",
                "recoveryCodes": "RC1"
            }, "auth_as": "admin", "phase": "setup"},
            {"event_type": "login_with_password", "params": {
                "application": "app-test", "organization": "test-org",
                "username": "mfa_victim_seq", "password": "Victim123456",
                "type": "login"
            }, "auth_as": "user_pwd", "phase": "login",
             "captures": {"pwd_login_data": "data"}},
            {"event_type": "saml_login", "params": {
                "target_identity": "attacker_mfa_seq",
                "email": "mfa_victim_seq@test.local",
                "provider": "provider-saml-test",
                "application": "app-test",
                "organization": "test-org"
            }, "auth_as": "user_saml", "phase": "login",
             "captures": {"saml_login_data": "data", "saml_status": "status"}},
            {"event_type": "verify_granted_identity", "params": {},
             "auth_as": "session_user_saml", "phase": "verify"},
        ],
        "oracle_checks": [
            {"check_id": "i3_mfa_enforced_pwd", "invariant": "I3",
             "assertion": "pwd_login_data == 'NextMfa'",
             "violation_description": "Password login did not trigger MFA — baseline check failed"},
            {"check_id": "i3_mfa_bypassed_saml", "invariant": "I3",
             "assertion": "saml_status != 'ok' OR saml_login_data == 'NextMfa'",
             "violation_description": "SAML binding-rule login bypassed MFA — I3 flow coherence violation"}
        ]
    },
    # Example 5: Cross-org token exchange 
    {
        "id": "seq_casdoor_i5_cross_org_token_exchange",
        "description": "Get access token in org-A (built-in), exchange at org-B application — verify organization boundary",
        "invariant_hypothesis": "I5: Token exchange must validate subject_token organization matches target application",
        "primary_invariant": "I5",
        "cve_analog": "none",
        "events": [
            {"event_type": "create_organization", "params": {
                "owner": "admin", "name": "org-b-seq",
                "displayName": "Org B Test",
                "passwordType": "bcrypt",
                "passwordOptions": ["AtLeast6"],
                "countryCodes": ["US"], "languages": ["en"]
            }, "auth_as": "admin", "phase": "setup"},
            {"event_type": "create_application", "params": {
                "owner": "admin", "name": "app-org-b-seq",
                "displayName": "Org B App",
                "organization": "org-b-seq",
                "redirectUris": ["http://localhost:8000/callback"],
                "grantTypes": ["authorization_code", "urn:ietf:params:oauth:grant-type:token-exchange"],
                "tokenFormat": "JWT", "cert": "cert-built-in",
                "enablePassword": True, "enableSignUp": True
            }, "auth_as": "admin", "phase": "setup"},
            {"event_type": "configure_application", "params": {
                "application_id": "admin/app-built-in",
                "application_object": {
                    "grantTypes": ["authorization_code", "urn:ietf:params:oauth:grant-type:token-exchange"],
                    "redirectUris": ["http://localhost:8000/callback"]
                }
            }, "auth_as": "admin", "phase": "setup"},
            {"event_type": "login_with_password", "params": {
                "application": "app-built-in", "organization": "built-in",
                "username": "admin", "password": "123", "type": "code",
                "redirectUri": "http://localhost:8000/callback"
            }, "auth_as": "user_orgA", "phase": "login",
             "captures": {"orgA_token": "session_token"}},
            {"event_type": "exchange_code_for_token", "params": {
                "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                "subject_token": "{{orgA_token}}",
                "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
                "target_application": "app-org-b-seq"
            }, "auth_as": "user_exchange", "phase": "login",
             "captures": {"exchanged_token": "session_token"}},
            {"event_type": "verify_granted_identity", "params": {},
             "auth_as": "session_user_exchange", "phase": "verify"},
        ],
        "oracle_checks": [
            {"check_id": "i5_cross_org_blocked", "invariant": "I5",
             "assertion": "exchanged_token is None",
             "violation_description": "Token exchange succeeded across organization boundary — I5 authorization binding violation"}
        ]
    },
    # Example 6: Casbin permission enforcement verification
    {
        "id": "seq_casdoor_i5_casbin_permission_enforcement",
        "description": "Create role + permission, assign to user, verify via enforce API",
        "invariant_hypothesis": "I5: Casbin enforcement must accurately reflect assigned permissions",
        "primary_invariant": "I5",
        "cve_analog": "none",
        "events": [
            {"event_type": "create_identity_user", "params": {
                "owner": "test-org", "name": "perm_user_seq",
                "displayName": "Perm User", "password": "PermUser123456",
                "email": "perm_user_seq@test.local", "type": "normal-user",
                "signupApplication": "app-test"
            }, "auth_as": "admin", "phase": "setup"},
            {"event_type": "create_auth_role", "params": {
                "role_object": {
                    "owner": "test-org", "name": "role_seq_admin",
                    "displayName": "Seq Admin Role"
                }
            }, "auth_as": "admin", "phase": "setup"},
            {"event_type": "create_policy", "params": {
                "permission_object": {
                    "owner": "test-org", "name": "perm_seq_admin",
                    "displayName": "Seq Admin Permission",
                    "actions": ["Read", "Write"],
                    "resources": ["resource_seq_*"],
                    "effect": "Allow",
                    "roles": ["test-org/role_seq_admin"]
                }
            }, "auth_as": "admin", "phase": "setup"},
            {"event_type": "assign_role_to_user", "params": {
                "owner": "test-org", "name": "perm_user_seq",
                "roles": [{"owner": "test-org", "name": "role_seq_admin"}]
            }, "auth_as": "admin", "phase": "setup"},
            {"event_type": "login_with_password", "params": {
                "application": "app-test", "organization": "test-org",
                "username": "perm_user_seq", "password": "PermUser123456",
                "type": "login"
            }, "auth_as": "user_A", "phase": "login"},
            {"event_type": "verify_granted_identity", "params": {},
             "auth_as": "session_user_A", "phase": "verify",
             "captures": {"user_A_policies": "granted_policies"}},
            {"event_type": "enforce_permission", "params": {
                "id": "test-org/perm_seq_admin",
                "v0": "test-org/perm_user_seq",
                "v1": "resource_seq_test",
                "v2": "Read"
            }, "auth_as": "admin", "phase": "verify",
             "captures": {"enforce_allowed": "allowed"}},
        ],
        "oracle_checks": [
            {"check_id": "i5_role_assigned", "invariant": "I5",
             "assertion": "user_A_policies is not None and len(user_A_policies) > 0",
             "violation_description": "User has no roles after assignment — role binding failed"},
            {"check_id": "i5_enforce_allowed", "invariant": "I5",
             "assertion": "enforce_allowed == true",
             "violation_description": "Casbin enforcement denied permission that should be granted — I5 permission enforcement violation"}
        ]
    },
]


KEYCLOAK_FEW_SHOT_EXAMPLES = [
    {
        "id": "seq_kc_i4_case_collision",
        "description": "Test if Keycloak case-insensitive usernames cause role leakage",
        "invariant_hypothesis": "I4: Case-different usernames should not share roles",
        "primary_invariant": "I4",
        "cve_analog": "none",
        "events": [
            {
                "event_type": "create_realm",
                "params": {"realm": "valence-i4-case", "enabled": True},
                "auth_as": "admin"
            },
            {
                "event_type": "create_client",
                "params": {
                    "realm": "valence-i4-case",
                    "client_id": "test-client",
                    "client_secret": "test-secret",
                    "enabled": True,
                    "direct_access_grants": True,
                    "public_client": False
                },
                "auth_as": "admin"
            },
            {
                "event_type": "create_user",
                "params": {
                    "realm": "valence-i4-case",
                    "username": "Admin",
                    "enabled": True,
                    "email": "admin@test.local",
                    "credentials": [{"type": "password", "value": "admin-pass", "temporary": False}]
                },
                "auth_as": "admin",
                "captures": {"admin_user_id": "user_id"}
            },
            {
                "event_type": "create_policy",
                "params": {"realm": "valence-i4-case", "role_name": "super-admin"},
                "auth_as": "admin"
            },
            {
                "event_type": "login_with_password",
                "params": {
                    "realm": "valence-i4-case",
                    "username": "Admin",
                    "password": "admin-pass",
                    "client_id": "test-client",
                    "client_secret": "test-secret",
                    "grant_type": "password",
                    "scope": "openid"
                },
                "auth_as": "user_Admin"
            },
            {
                "event_type": "verify_granted_identity",
                "params": {"realm": "valence-i4-case"},
                "auth_as": "session_user_Admin",
                "captures": {
                    "admin_username": "display_name",
                    "admin_sub": "identity_id",
                    "admin_roles": "granted_policies"
                }
            }
        ],
        "oracle_checks": [
            {
                "check_id": "kc_case_roles",
                "invariant": "I4",
                "assertion": "admin_roles does not include unexpected roles from case-variant user",
                "violation_description": "Case-insensitive username collision caused role leakage"
            }
        ]
    }
]


class SequenceGenerator:
    """Facade that delegates to CoverageStrategy or AttackStrategy.

    Preserves the original generate() interface for backward compatibility
    with campaign_runner.py and existing tests.
    """

    def __init__(self, llm_client: LLMClient, profile=None, **kwargs):
        self.llm = llm_client
        self.profile = profile

        # Build strategy objects — reuse same PromptBuilder for efficiency
        self.prompt_builder = PromptBuilder(profile)
        self.coverage_strategy = CoverageStrategy(llm_client, profile, self.prompt_builder)
        self.attack_strategy = AttackStrategy(llm_client, profile, self.prompt_builder)

    def generate(self,
                 invariant_focus: str = "I4",
                 num_sequences: int = 3,
                 previously_generated: list[str] = None,
                 custom_hints: list[str] = None,
                 protocol: str = "oidc_jwt",
                 coverage_gaps: list[str] = None,
                 mode: str = "attack",
                 use_examples: bool = True,
                 max_examples: int = -1,
                 use_invariants: bool = True) -> list[EventSequence]:
        """Generate event sequences. Delegates to the appropriate strategy.

        Args:
            invariant_focus: Which invariant to target (I1-I5)
            num_sequences: How many sequences to generate
            previously_generated: Descriptions of already-generated sequences (for dedup)
            custom_hints: Additional attack pattern hints
            protocol: Which protocol surface to test
            coverage_gaps: Uncovered test space cells (from CoverageTracker)
            mode: 'coverage' or 'attack'
            use_examples: Include few-shot examples in the prompt (ablation control)
            max_examples: Max number of examples to include (-1 = all)
            use_invariants: Include I1-I5 definitions in the prompt (ablation control)
        """
        # Update prompt_builder protocol if changed
        self.prompt_builder.protocol = protocol

        config = GenerationConfig(
            invariant_focus=invariant_focus,
            num_sequences=num_sequences,
            previously_generated=previously_generated or [],
            custom_hints=custom_hints or [],
            coverage_gaps=coverage_gaps or [],
            use_examples=use_examples,
            max_examples=max_examples,
            use_invariants=use_invariants,
        )

        logger.info(f"Generating {num_sequences} sequences for {invariant_focus} (mode={mode})...")

        if mode == "coverage":
            return self.coverage_strategy.generate(config)
        else:
            return self.attack_strategy.generate(config)

    # ------------------------------------------------------------------
    # DEPRECATED — called by tests only. Remove when tests are updated.
    # ------------------------------------------------------------------

    def _build_system_prompt_v2(self, protocol: str = "oidc_jwt") -> str:
        """Delegate to PromptBuilder. Kept for backward compat with tests."""
        self.prompt_builder.protocol = protocol
        return self.prompt_builder.build_system_prompt(use_examples=True, max_examples=-1)

    def _build_system_prompt(self) -> str:
        """Delegate to PromptBuilder legacy path. Kept for backward compat."""
        return self.prompt_builder._build_legacy_prompt(use_examples=True, max_examples=-1)

    def _build_user_prompt(self, invariant_focus, num_sequences,
                           previously_generated, hints,
                           coverage_gaps=None, mode="attack") -> str:
        """Delegate to PromptBuilder. Kept for backward compat."""
        from src.stateful.generation_strategy import GenerationConfig as GC
        if mode == "coverage":
            mode_instruction = self.coverage_strategy.build_mode_instruction(
                GC(invariant_focus=invariant_focus)
            )
        else:
            mode_instruction = self.attack_strategy.build_mode_instruction(
                GC(invariant_focus=invariant_focus)
            )
        config = GC(
            invariant_focus=invariant_focus,
            num_sequences=num_sequences,
            previously_generated=previously_generated,
            custom_hints=hints,
            coverage_gaps=coverage_gaps or [],
        )
        return self.prompt_builder.build_user_prompt(mode_instruction, config)

    def _parse_sequence(self, data: dict) -> EventSequence:
        """Delegate to strategy base. Kept for backward compat."""
        return self.attack_strategy._parse_sequence(data)

    def _validate_sequence(self, seq: EventSequence, protocol: str = "oidc_jwt") -> bool:
        """Delegate to strategy base. Kept for backward compat."""
        # Temporarily use attack strategy (validates oracle_checks exist)
        return self.attack_strategy._validate_sequence(seq, protocol=protocol)

    def _get_capture_suffix(self, op_name: str, abstract_key: str) -> str:
        """Delegate to prompt_builder util. Kept for backward compat."""
        from src.stateful.prompt_builder import _get_capture_suffix
        return _get_capture_suffix(op_name, abstract_key)

