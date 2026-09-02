"""Extract platform profile from cleaned documentation via LLM.

Reads cleaned docs (from fetch_docs.py), calls LLM once, produces:
  - src/profiles/{platform}.json   (PlatformProfile with api_mapping, constraints, etc.)

Usage:
    python -m src.extraction.extract_specs --platform vault --protocol oidc_jwt
    python -m src.extraction.extract_specs --platform vault --protocol oidc_jwt --dry-run
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Multi-run merge for stable enumeration
# ---------------------------------------------------------------------------


def _extract_key_terms(text: str, n: int = 6) -> str:
    """Extract first N non-stopword tokens from text for semantic fingerprinting."""
    import re as _re
    _stop = frozenset(
        "the a an is are was were be been being have has had do does did will "
        "would could should may might must shall can not no nor and or but if "
        "then than when where which who this that these those it its of for to "
        "in on at by from with as into through during before after same such "
        "only also any each every both few more most other some all per used "
        "vault auth method presented validates verifies documented".split()
    )
    words = _re.findall(r"[a-z_]+", text.lower())
    # Naive stemming: strip common suffixes for stable fingerprinting
    def _stem(w: str) -> str:
        for suffix in ("lessly", "ation", "ting", "ing", "ted", "tes", "es", "ed", "ly", "s"):
            if len(w) > len(suffix) + 2 and w.endswith(suffix):
                return w[:-len(suffix)]
                break
        return w
    stemmed = set(_stem(w) for w in words if w not in _stop and len(w) > 2)
    # Sort by length descending — longest (most specific) terms first
    key = sorted(stemmed, key=lambda w: (-len(w), w))
    return " ".join(key[:n])


def _dedup_behaviors(all_kbs: list, platform: str) -> list:
    """Deduplicate known_behaviors using Jaccard similarity of key terms.

    Within each invariant group, behaviors sharing >40% of key terms are
    considered paraphrases. The first occurrence is kept; duplicates are
    dropped. IDs are generated deterministically from content hash.
    """
    import hashlib

    # Group by invariant set
    groups: dict = {}
    for kb in all_kbs:
        inv_key = ",".join(sorted(kb.get("invariants", [])))
        terms = set(_extract_key_terms(kb.get("description", ""), n=20).split())
        groups.setdefault(inv_key, []).append((kb, terms))

    result = []
    for inv_key, items in groups.items():
        used = [False] * len(items)
        for i in range(len(items)):
            if used[i]:
                continue
            used[i] = True
            rep_kb = items[i][0]
            rep_terms = items[i][1]
            # Collect shared terms across cluster members for stable ID
            shared_terms = set(rep_terms)
            for j in range(i + 1, len(items)):
                if used[j]:
                    continue
                inter = rep_terms & items[j][1]
                union = rep_terms | items[j][1]
                if union and len(inter) / len(union) > 0.3:
                    used[j] = True
                    shared_terms &= items[j][1]
            # ID from invariants + shared terms (stable across paraphrases)
            id_terms = shared_terms if shared_terms else rep_terms
            content = f"{platform}|{inv_key}|{' '.join(sorted(id_terms))}"
            short_hash = hashlib.md5(content.encode()).hexdigest()[:8]
            inv_prefix = inv_key.lower().replace(",", "_") if inv_key else "gen"
            rep_kb["id"] = f"{platform}_{inv_prefix}_{short_hash}"
            result.append(rep_kb)

    return result


def _majority_vote_ops(outputs: list) -> list:
    """Majority-vote on input_operations across multiple LLM runs.

    For each operation name present in any run:
    - path: majority vote (most common path wins)
    - body_map: union of all keys across runs (completeness)
    - response_map: union of all keys across runs
    - auth/method: majority vote
    """
    from collections import Counter

    # Collect all ops by name across runs
    ops_by_name: dict = {}
    for output in outputs:
        for op in output.get("input_operations", []):
            name = op.get("operation_name")
            if not name:
                continue
            ops_by_name.setdefault(name, []).append(op)

    # Adaptive majority filter: for platforms with many ops (>10 avg per run),
    # require 2/3 appearance to filter hallucinations. For sparse platforms
    # (<=10 avg ops), keep all ops to avoid dropping legitimate ones.
    avg_ops = sum(len(o.get("input_operations", [])) for o in outputs) / len(outputs)
    if avg_ops > 10:
        min_appearances = max(1, (len(outputs) + 1) // 2)  # 2 of 3
    else:
        min_appearances = 1  # keep all for sparse docs

    merged_ops = []
    for name, variants in ops_by_name.items():
        if len(variants) < min_appearances:
            continue  # skip ops that don't pass majority threshold
        # Path: majority vote
        path_votes = Counter(v.get("path", "") for v in variants)
        best_path = path_votes.most_common(1)[0][0]

        # method/auth: majority vote
        method_votes = Counter(v.get("method", "POST") for v in variants)
        auth_votes = Counter(v.get("auth", "admin") for v in variants)

        # body_map: union across runs (more params = better coverage)
        # When the same abstract key appears with both flat and dot values,
        # prefer flat (e.g., "clientId" over "application.clientId")
        merged_body = {}
        for v in variants:
            for k, val in v.get("body_map", {}).items():
                if k not in merged_body:
                    merged_body[k] = val
                elif "." in merged_body[k] and "." not in val:
                    merged_body[k] = val  # prefer flat over dot-notation

        # response_map: union across runs
        merged_resp = {}
        for v in variants:
            for k, val in v.get("response_map", {}).items():
                if k not in merged_resp:
                    merged_resp[k] = val

        # content_type: majority vote (most common non-json wins if any)
        ct_votes = Counter(v.get("content_type", "json") for v in variants)
        best_ct = ct_votes.most_common(1)[0][0]

        # metadata: union across runs
        merged_meta = {}
        for v in variants:
            for k, val in v.get("metadata", {}).items():
                if k not in merged_meta:
                    merged_meta[k] = val

        # Preserve other fields from first variant
        base = dict(variants[0])
        base["path"] = best_path
        base["method"] = method_votes.most_common(1)[0][0]
        base["auth"] = auth_votes.most_common(1)[0][0]
        base["body_map"] = merged_body
        base["response_map"] = merged_resp
        if best_ct != "json":
            base["content_type"] = best_ct
        if merged_meta:
            base["metadata"] = merged_meta
        merged_ops.append(base)

    return merged_ops


def _merge_llm_outputs(outputs: list, platform: str) -> dict:
    """Merge multiple LLM extraction outputs.

    - input_operations: majority-vote on paths, union on body_map/response_map
    - verification_fields: from run 1 (stable)
    - api_constraints/known_behaviors: union with dedup
    """
    merged = {
        "input_operations": _majority_vote_ops(outputs),
        "verification_fields": outputs[0].get("verification_fields", {}),
    }

    # api_constraints: union with text-based dedup (first 100 chars normalized)
    seen_constraints: dict = {}
    for output in outputs:
        for c in output.get("api_constraints", []):
            text = c.get("constraint", c) if isinstance(c, dict) else str(c)
            key = text.lower().strip()[:100]
            if key not in seen_constraints:
                seen_constraints[key] = c
    merged["api_constraints"] = list(seen_constraints.values())

    # known_behaviors: collect all, then dedup by Jaccard similarity
    all_kbs = []
    for output in outputs:
        all_kbs.extend(output.get("known_behaviors", []))
    merged["known_behaviors"] = _dedup_behaviors(all_kbs, platform)

    return merged


# ---------------------------------------------------------------------------
# Platform defaults (non-extractable config)
# ---------------------------------------------------------------------------

PLATFORM_DEFAULTS = {
    "vault": {
        "base_url": "http://localhost:8200",
        "admin_auth": {"header": "X-Vault-Token", "value": "root"},
        "environment_defaults": {
            "mount": "jwt",
            "engine": "secret",
        },
        "verification_fields": {
            "identity_field": "entity_id",
            "identity_name_field": "entity_alias.name",
            "policies_field": "policies",
            "identity_policies_field": "identity_policies",
            "groups_field": "group_ids",
        },
    },
    "keycloak": {
        "base_url": "http://localhost:8080",
        "admin_auth": {"header": "Authorization", "value": "Bearer {admin_token}"},
        "environment_defaults": {
            "realm_prefix": "valence-",
            "client_id": "valence-test-client",
            "client_secret": "valence-test-secret",
            "redirect_uri": "http://localhost:8080/callback",
            "idp_sso_url": "http://fake-idp.valence.local/saml/sso",
            "isolation_strategy": "Each test sequence MUST create its own realm using create_tenant with a unique name (e.g., valence-i1-test). Do NOT create IdPs in the master realm — use enable_auth_method in the new realm. This prevents alias conflicts (409) between concurrent sequences.",
            "idp_fields_warning": "Do NOT include syncMode in enable_auth_method params — older Keycloak versions reject it as an unrecognized field. Also do NOT include caseSensitiveOriginalUsername at the top level — it belongs inside the config object.",
        },
        "verification_fields": {
            "identity_field": "sub",
            "identity_name_field": "preferred_username",
            "policies_field": "realm_access.roles",
            "groups_field": "groups",
        },
    },
    "dex": {
        "base_url": "http://localhost:5556/dex",
        "admin_auth": {"header": "Authorization", "value": "Bearer {admin_token}"},
        "environment_defaults": {
            "client_id": "valence-test-client",
            "client_secret": "valence-test-secret",
            "redirect_uri": "http://localhost:8080/callback",
            "connector_id": "mock",
            "saml_connector_id": "test-saml",
            "saml_idp_key_path": "docker/dex/saml_idp_key.pem",
            "saml_idp_cert_path": "docker/dex/saml_idp_cert.pem",
            "saml_sp_acs_url": "http://localhost:5556/dex/callback",
        },
        "verification_fields": {
            "identity_field": "sub",
            "identity_name_field": "email",
            "policies_field": "groups",
            "groups_field": "groups",
        },
    },
    "casdoor": {
        "base_url": "http://localhost:8000",
        "admin_auth": {"header": "Authorization", "value": "Basic {admin_token}"},
        "session_auth_method": "cookie",
        "environment_defaults": {
            "organization": "test-org",
            "application": "app-test",
            "admin_owner": "admin",
            "user_owner": "test-org",
            "redirect_uri": "http://localhost:8000/callback",
            "provider_name": "provider-saml-test",
            "isolation_strategy": (
                "A pre-configured test environment exists: organization 'test-org', "
                "application 'app-test' (query clientId/clientSecret via "
                "GET /api/get-application?id=admin/app-test), and SAML provider "
                "'provider-saml-test' already linked to app-test. "
                "For MOST tests, REUSE these resources instead of creating new ones. "
                "Only create new organizations/applications when the attack specifically "
                "requires distinct tenants (e.g., I5 cross-org token exchange). "
                "OWNERSHIP RULES: Applications and providers MUST use owner='admin'. "
                "Users MUST use owner=<organization_name> (e.g., 'test-org'). "
                "NEVER use 'built-in' as organization for create_user — "
                "the built-in org forbids user creation. "
                "GRANT TYPES: When creating applications, ALWAYS include "
                "grantTypes=['password','authorization_code','urn:ietf:params:oauth:grant-type:token-exchange'] "
                "and enablePassword=true and cert='cert-built-in' unless the test specifically requires otherwise. "
                "MULTI-APP SEQUENCES: When a test needs two separate applications "
                "(e.g., token exchange between different clients/audiences), use 'app-test' "
                "as the SOURCE application (already exists) and create ONE new application "
                "as the TARGET. Create users with signupApplication matching the app they will "
                "login to. For login_with_password, the executor auto-resolves client_id from "
                "the user's signupApplication — so set signupApplication correctly in create_user."
            ),
        },
        "cookie_login": {
            "path": "/api/login",
            "body": {
                "type": "login",
                "application": "app-built-in",
                "organization": "built-in",
                "username": "admin",
                "password": "123",
            },
        },
        "identity_carrying_types": ["jwt", "password", "saml", "ldap", "cert"],
        # Verified endpoint definitions — injected when LLM extraction misses them.
        # These override nothing (only fill gaps), but provide correct body_maps
        # for endpoints the LLM frequently gets wrong.
        "extra_operations": {
            "mfa_setup_enable": {
                "method": "POST",
                "path": "/api/mfa/setup/enable",
                "body_map": {
                    "owner": "owner",
                    "username": "name",
                    "mfa_type": "mfaType",
                    "secret": "secret",
                    "recovery_codes": "recoveryCodes",
                },
                "response_map": {"status": "status"},
                "auth": "admin",
                "content_type": "form",
            },
            "saml_login": {
                "method": "POST",
                "path": "/api/login",
                "body_map": {
                    "saml_response": "samlResponse",
                    "type": "type",
                    "method": "method",
                    "application": "application",
                    "organization": "organization",
                    "provider": "provider",
                    "state": "state",
                    "redirect_uri": "redirectUri",
                },
                "response_map": {
                    "session_token": "data",
                    "http_status": "_http_status",
                },
                "auth": "none",
                "content_type": "json",
                "default_params": {
                    "type": "code",
                    "method": "signup",
                    "state": "casdoor",
                },
                "metadata": {
                    "casdoor_saml_via_login_api": True,
                    "acs_url": "/api/acs",
                },
            },
            "login_with_password": {
                "method": "POST",
                "path": "/api/login/oauth/access_token",
                "body_map": {
                    "grant_type": "grant_type",
                    "client_id": "client_id",
                    "client_secret": "client_secret",
                    "username": "username",
                    "password": "password",
                    "scope": "scope",
                },
                "response_map": {
                    "session_token": "access_token",
                    "metadata": "id_token",
                    "http_status": "_http_status",
                },
                "auth": "none",
            },
            "verify_granted_identity": {
                "method": "GET",
                "path": "/api/userinfo",
                "body_map": {"session_token": "accessToken"},
                "response_map": {
                    "identity_id": "sub",
                    "identity_name": "preferred_username",
                    "display_name": "name",
                    "email": "email",
                    "metadata": "$",
                    "http_status": "_http_status",
                },
                "auth": "session",
                "content_type": "query",
                "metadata": {"accepts_bearer_header": True},
            },
        },
        # Force-override operations: always replace LLM-generated definitions.
        # Used for endpoints where LLM consistently generates wrong body_maps.
        "force_extra_operations": {
            "create_application": {
                "method": "POST",
                "path": "/api/add-application",
                "body_map": {
                    "owner": "owner", "name": "name", "display_name": "displayName",
                    "organization": "organization", "client_id": "clientId",
                    "client_secret": "clientSecret", "redirect_uris": "redirectUris",
                    "grant_types": "grantTypes", "token_format": "tokenFormat",
                    "cert": "cert", "enable_password": "enablePassword",
                    "enable_sign_up": "enableSignUp", "enable_signin_session": "enableSigninSession",
                    "providers": "providers", "expire_in_hours": "expireInHours",
                    "refresh_expire_in_hours": "refreshExpireInHours",
                    "signin_methods": "signinMethods", "signup_items": "signupItems",
                    "saml_reply_url": "samlReplyUrl",
                    "enable_saml_compress": "enableSamlCompress",
                },
                "response_map": {},
                "auth": "admin",
                "default_params": {"owner": "admin", "cert": "cert-built-in"},
            },
            "create_provider": {
                "method": "POST",
                "path": "/api/add-provider",
                "body_map": {
                    "owner": "owner", "name": "name", "display_name": "displayName",
                    "category": "category", "type": "type",
                    "endpoint": "endpoint", "metadata": "metadata",
                    "idp": "idP", "issuer_url": "issuerUrl",
                    "enable_sign_authn_request": "enableSignAuthnRequest",
                    "client_id": "clientId", "client_secret": "clientSecret",
                },
                "response_map": {},
                "auth": "admin",
                "default_params": {"owner": "admin"},
            },
            "create_user": {
                "method": "POST",
                "path": "/api/add-user",
                "body_map": {
                    "owner": "owner", "name": "name", "display_name": "displayName",
                    "password": "password", "email": "email", "phone": "phone",
                    "type": "type", "is_admin": "isAdmin",
                    "signup_application": "signupApplication",
                },
                "response_map": {},
                "auth": "admin",
            },
            "create_organization": {
                "method": "POST",
                "path": "/api/add-organization",
                "body_map": {
                    "owner": "owner", "name": "name", "display_name": "displayName",
                    "website_url": "websiteUrl", "password_type": "passwordType",
                },
                "response_map": {},
                "auth": "admin",
                "default_params": {"owner": "admin", "password_type": "bcrypt"},
            },
        },
        "cleanup_rules": [
            {"resource_type": "user", "list_path": "/api/get-users?owner=test-org&pageSize=500&p=1",
             "list_response_path": "data", "name_field": "name", "name_pattern": ".",
             "name_exclude_pattern": "^(admin|test-user|test)$",
             "delete_method": "POST", "delete_path": "/api/delete-user",
             "delete_body_fields": ["owner", "name"]},
            {"resource_type": "application", "list_path": "/api/get-applications?owner=admin&pageSize=500&p=1",
             "list_response_path": "data", "name_field": "name", "name_pattern": ".",
             "name_exclude_pattern": "^(app-test|app-built-in|app-casdoor)$",
             "delete_method": "POST", "delete_path": "/api/delete-application",
             "delete_body_fields": ["owner", "name"]},
            {"resource_type": "organization", "list_path": "/api/get-organizations?owner=admin&pageSize=500&p=1",
             "list_response_path": "data", "name_field": "name", "name_pattern": ".",
             "name_exclude_pattern": "^(built-in|test-org)$",
             "delete_method": "POST", "delete_path": "/api/delete-organization",
             "delete_body_fields": ["owner", "name"]},
        ],
        "verification_fields": {
            "identity_field": "data.id",
            "identity_name_field": "data.name",
            "identity_prefix_pattern": "{sent}@.*",
            "policies_field": "data.roles",
            "groups_field": "data.groups",
        },
    },
    "authentik": {
        "base_url": "http://localhost:9000",
        "admin_auth": {"header": "Authorization", "value": "Bearer {admin_token}"},
        "environment_defaults": {
            "api_pattern": "authentik REST API follows /api/v3/{app}/{model}/ pattern. All CRUD operations use this pattern with standard HTTP methods (GET/POST/PUT/PATCH/DELETE).",
        },
        "extra_operations": {
            "create_user": {
                "method": "POST",
                "path": "/api/v3/core/users/",
                "body_map": {
                    "username": "username",
                    "email": "email",
                    "name": "name",
                    "password": "password",
                    "is_active": "is_active",
                    "groups": "groups",
                },
                "response_map": {"identity_id": "pk", "username": "username", "http_status": "_http_status"},
                "auth": "admin",
            },
            "create_application": {
                "method": "POST",
                "path": "/api/v3/core/applications/",
                "body_map": {
                    "name": "name",
                    "slug": "slug",
                    "provider": "provider",
                    "group": "group",
                },
                "response_map": {"app_id": "pk", "slug": "slug", "http_status": "_http_status"},
                "auth": "admin",
            },
            "create_provider": {
                "method": "POST",
                "path": "/api/v3/providers/saml/",
                "body_map": {
                    "name": "name",
                    "authorization_flow": "authorization_flow",
                    "acs_url": "acs_url",
                    "issuer": "issuer",
                    "audience": "audience",
                    "sp_binding": "sp_binding",
                    "signing_kp": "signing_kp",
                    "verification_kp": "verification_kp",
                },
                "response_map": {"provider_id": "pk", "http_status": "_http_status"},
                "auth": "admin",
            },
            "create_organization": {
                "method": "POST",
                "path": "/api/v3/providers/oauth2/",
                "body_map": {
                    "name": "name",
                    "authorization_flow": "authorization_flow",
                    "client_type": "client_type",
                    "client_id": "client_id",
                    "client_secret": "client_secret",
                    "redirect_uris": "redirect_uris",
                    "signing_key": "signing_key",
                    "sub_mode": "sub_mode",
                    "issuer_mode": "issuer_mode",
                    "jwks_sources": "jwks_sources",
                },
                "response_map": {"provider_id": "pk", "http_status": "_http_status"},
                "auth": "admin",
                "note": "Creates an OAuth2/OIDC provider (not an organization). Mapped to create_organization for compatibility with the canonical ops vocabulary.",
            },
            "enable_auth_method": {
                "method": "POST",
                "path": "/api/v3/sources/oauth/",
                "body_map": {
                    "name": "name",
                    "slug": "slug",
                    "provider_type": "provider_type",
                    "consumer_key": "consumer_key",
                    "consumer_secret": "consumer_secret",
                    "authorization_url": "authorization_url",
                    "access_token_url": "access_token_url",
                    "profile_url": "profile_url",
                    "oidc_well_known_url": "oidc_well_known_url",
                    "oidc_jwks_url": "oidc_jwks_url",
                },
                "response_map": {"source_id": "pk", "slug": "slug", "http_status": "_http_status"},
                "auth": "admin",
                "note": "Creates an OAuth/OIDC source (external IdP). Also used for SAML sources via /api/v3/sources/saml/.",
            },
            "verify_granted_identity": {
                "method": "GET",
                "path": "/application/o/userinfo/",
                "body_map": {},
                "response_map": {
                    "identity_id": "sub",
                    "display_name": "name",
                    "email": "email",
                    "groups": "groups",
                    "http_status": "_http_status",
                },
                "auth": "session",
            },
            "exchange_code_for_token": {
                "method": "POST",
                "path": "/application/o/token/",
                "body_map": {
                    "grant_type": "grant_type",
                    "code": "code",
                    "redirect_uri": "redirect_uri",
                    "client_id": "client_id",
                    "client_secret": "client_secret",
                },
                "response_map": {"session_token": "access_token", "http_status": "_http_status"},
                "auth": "none",
                "content_type": "form",
            },
        },
        "verification_fields": {
            "identity_field": "sub",
            "identity_name_field": "preferred_username",
            "policies_field": "groups",
            "groups_field": "groups",
        },
    },
    "zitadel": {
        "base_url": "http://localhost:8085",
        "admin_auth": {"header": "Authorization", "value": "Bearer {admin_token}"},
        "environment_defaults": {
            "project_id": "valence-project",
            "client_id": "valence-test-client",
            "redirect_uri": "http://localhost:8085/callback",
            "saml_metadata_url": "http://mock-idp:9090/saml/metadata",
            "mock_idp_entity_id": "http://mock-idp:9090",
            "isolation_strategy": "Zitadel management API uses REST gateway paths under /management/v1/ (org-scoped). Do NOT use gRPC Connect paths. For IdP setup: create_provider creates the IdP, enable_auth_method adds it to the login policy with ownerType='IDP_OWNER_TYPE_ORG' (NOT 'ORG' or 'OWNER_TYPE_ORG'). Both are needed before IdP login works. SAML login is brokered — saml_login is NOT directly callable as a standalone POST. It is handled internally by the executor's ZITADEL-LOGIN flow triggered via start_oidc_auth with scope containing urn:zitadel:iam:org:idp:id:{idp_id}.",
        },
        "extra_operations": {
            "create_user": {
                "method": "POST",
                "path": "/v2/users/human",
                "body_map": {
                    "username": "username",
                    "email": "profile.email.email",
                    "first_name": "profile.givenName",
                    "last_name": "profile.familyName",
                    "display_name": "profile.displayName",
                    "password": "password.password",
                },
                "response_map": {"identity_id": "userId", "http_status": "_http_status"},
                "auth": "admin",
            },
            "create_organization": {
                "method": "POST",
                "path": "/v2/organizations",
                "body_map": {
                    "name": "name",
                },
                "response_map": {"organization_id": "organizationId", "http_status": "_http_status"},
                "auth": "admin",
            },
            "configure_jwt_validation": {
                "method": "POST",
                "path": "/management/v1/idps/generic_jwt",
                "body_map": {
                    "name": "name",
                    "issuer": "issuer",
                    "jwt_endpoint": "jwtEndpoint",
                    "keys_endpoint": "keysEndpoint",
                    "header_name": "headerName",
                    "auto_linking": "providerOptions.autoLinking",
                    "is_linking_allowed": "providerOptions.isLinkingAllowed",
                    "is_auto_creation": "providerOptions.isAutoCreation",
                },
                "response_map": {"provider_id": "id", "http_status": "_http_status"},
                "auth": "admin",
            },
            "create_provider": {
                "method": "POST",
                "path": "/management/v1/idps/saml",
                "body_map": {
                    "name": "name",
                    "metadata_url": "metadataUrl",
                    "metadata_xml_base64": "metadataXml",
                    "binding": "binding",
                    "with_signed_request": "withSignedRequest",
                    "auto_linking": "providerOptions.autoLinking",
                    "is_linking_allowed": "providerOptions.isLinkingAllowed",
                    "is_auto_creation": "providerOptions.isAutoCreation",
                },
                "response_map": {"provider_id": "id", "http_status": "_http_status"},
                "auth": "admin",
                "note": "metadataXml is a proto bytes field — value MUST be base64-encoded. Use metadataUrl as simpler alternative. For mock-idp: metadataUrl MUST be 'http://mock-idp:9090/saml/metadata' (NOT /metadata).",
            },
            "enable_auth_method": {
                "method": "POST",
                "path": "/management/v1/policies/login/idps",
                "body_map": {
                    "idp_id": "idpId",
                    "owner_type": "ownerType",
                },
                "response_map": {"http_status": "_http_status"},
                "auth": "admin",
                "note": "ownerType MUST be exactly 'IDP_OWNER_TYPE_ORG' (protobuf enum). NOT 'ORG', 'OWNER_TYPE_ORG', or 'org'. Requires org-level login policy to exist first.",
            },
            "create_application": {
                "method": "POST",
                "path": "/management/v1/projects/{project_id}/apps/saml",
                "body_map": {
                    "name": "name",
                    "metadata_url": "metadataUrl",
                },
                "response_map": {"app_id": "appId", "http_status": "_http_status"},
                "auth": "admin",
            },
            "update_application": {
                "method": "PUT",
                "path": "/management/v1/policies/login",
                "body_map": {
                    "allow_external_idp": "allowExternalIdp",
                    "allow_register": "allowRegister",
                    "allow_username_password": "allowUsernamePassword",
                },
                "response_map": {"http_status": "_http_status"},
                "auth": "admin",
                "note": "Updates the org-level login policy. Use this to enable external IdP login (allowExternalIdp=true).",
            },
            "cleanup_auth_method": {
                "method": "DELETE",
                "path": "/management/v1/idps/{idp_id}",
                "body_map": {},
                "response_map": {"http_status": "_http_status"},
                "auth": "admin",
            },
        },
        "verification_fields": {
            "identity_field": "sub",
            "identity_name_field": "preferred_username",
            "policies_field": "urn:zitadel:iam:org:project:roles",
            "groups_field": "urn:zitadel:iam:org:project:roles",
        },
    },
    "logto": {
        "base_url": "http://localhost:3001",
        "admin_auth": {"header": "Authorization", "value": "Bearer {admin_token}"},
        "environment_defaults": {
            "api_pattern": "Logto Management API uses /api/ prefix. User CRUD: /api/users. SSO connectors: /api/sso-connectors. Applications: /api/applications.",
            "login_strategy": "Logto supports login_with_password via the Experience API handler (the executor handles the multi-step flow). For M2M service login, use login_with_jwt with client_credentials grant.",
            "app_types": "Logto application types: Native, SPA, Traditional, MachineToMachine, Protected, SAML. Do NOT use TraditionalWeb or WebApp — use 'Traditional'.",
            "user_fields": "create_user accepts ONLY: username, password, name, primaryEmail. Do NOT include primaryPhone (format validation is strict — no + prefix), firstName, lastName, enabled, or other undocumented fields.",
        },
        "extra_operations": {
            "create_user": {
                "method": "POST",
                "path": "/api/users",
                "body_map": {
                    "username": "username",
                    "password": "password",
                    "name": "name",
                    "primary_email": "primaryEmail",
                },
                "response_map": {"identity_id": "id", "username": "username", "http_status": "_http_status"},
                "auth": "admin",
            },
            "create_provider": {
                "method": "POST",
                "path": "/api/sso-connectors",
                "body_map": {
                    "provider_name": "providerName",
                    "connector_name": "connectorName",
                    "domains": "domains",
                    "config": "config",
                },
                "response_map": {"connector_id": "id", "http_status": "_http_status"},
                "auth": "admin",
                "note": "Creates an enterprise SSO connector (SAML or OIDC). providerName: 'SAML' or 'OIDC'. config contains IdP metadata/endpoints.",
            },
            "create_application": {
                "method": "POST",
                "path": "/api/applications",
                "body_map": {
                    "name": "name",
                    "type": "type",
                    "description": "description",
                    "redirect_uris": "oidcClientMetadata.redirectUris",
                    "post_logout_redirect_uris": "oidcClientMetadata.postLogoutRedirectUris",
                },
                "response_map": {"app_id": "id", "client_id": "id", "http_status": "_http_status"},
                "auth": "admin",
                "note": "type MUST be one of: Native, SPA, Traditional, MachineToMachine, Protected, SAML. postLogoutRedirectUris MUST be an array (can be empty []).",
            },
            "update_application": {
                "method": "PATCH",
                "path": "/api/applications/{app_id}",
                "body_map": {
                    "name": "name",
                    "description": "description",
                    "redirect_uris": "oidcClientMetadata.redirectUris",
                    "allow_token_exchange": "customClientMetadata.allowTokenExchange",
                },
                "response_map": {"http_status": "_http_status"},
                "auth": "admin",
                "note": "customClientMetadata is a TOP-LEVEL field, NOT nested inside oidcClientMetadata. app_id in path must match the captured id from create_application.",
            },
            "login_with_password": {
                "method": "POST",
                "path": "/api/experience/sign-in",
                "body_map": {
                    "username": "identifier",
                    "password": "password",
                },
                "response_map": {"session_token": "access_token", "http_status": "_http_status"},
                "auth": "none",
                "metadata": {"absent_canonical_login": True},
                "note": "Logto uses the Experience API for password login. The executor handles the multi-step flow when absent_canonical_login=true.",
            },
            "verify_granted_identity": {
                "method": "GET",
                "path": "/oidc/me",
                "body_map": {},
                "response_map": {
                    "identity_id": "sub",
                    "display_name": "username",
                    "email": "email",
                    "groups": "organizations",
                    "http_status": "_http_status",
                },
                "auth": "session",
                "content_type": "query",
            },
            "saml_login": {
                "method": "POST",
                "path": "/api/authn/saml/{connector_id}",
                "body_map": {
                    "saml_response": "SAMLResponse",
                    "relay_state": "RelayState",
                },
                "response_map": {"session_token": "access_token", "http_status": "_http_status"},
                "auth": "none",
                "content_type": "form",
                "metadata": {"initiate_saml_flow": True},
                "note": "connector_id MUST be a valid SSO connector ID from create_provider response. Use the captured connector_id, not a placeholder.",
            },
            "login_with_jwt": {
                "method": "POST",
                "path": "/oidc/token",
                "body_map": {
                    "grant_type": "grant_type",
                    "client_id": "client_id",
                    "client_secret": "client_secret",
                    "scope": "scope",
                    "resource": "resource",
                },
                "response_map": {"session_token": "access_token", "http_status": "_http_status"},
                "auth": "none",
                "content_type": "form",
                "note": "M2M client_credentials grant. grant_type MUST be 'client_credentials'. Requires a MachineToMachine application.",
            },
        },
        "verification_fields": {
            "identity_field": "sub",
            "identity_name_field": "username",
            "policies_field": "roles",
            "groups_field": "organizations",
        },
    },
}

# ---------------------------------------------------------------------------
# LLM Prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert security researcher extracting API specifications \
from identity broker documentation for a security testing tool (VALENCE).

VALENCE tests identity brokers using 5 security invariants:
- I1 Proof Integrity: The broker must verify the exact proof it consumes (e.g., signature on correct element)
- I2 Freshness/Anti-Replay: Credentials must not be reusable beyond their lifetime
- I3 Flow Coherence: Multi-step auth flows must be atomic and session-bound
- I4 Principal Binding: Different upstream identities must not collapse into the same downstream identity
- I5 Authorization Binding: Granted permissions must not exceed upstream intent ∩ broker policy

You must extract TWO categories of API operations and additional metadata.

OUTPUT ONLY VALID JSON — no markdown fences, no explanations."""


def build_user_prompt(platform: str, protocol: str, docs_text: str,
                      existing_profile: Optional[dict] = None) -> str:
    """Build the LLM extraction prompt."""
    from src.stateful.protocol_operations import PROTOCOL_OPERATIONS, CROSS_PLATFORM_ATTACK_PATTERNS
    ops_reference = "\n".join(f"  {k}: {v}" for k, v in PROTOCOL_OPERATIONS.items())

    # Filter attack patterns to exclude patterns tagged for other protocols
    exclude_tags = []
    if protocol != "oidc_jwt":
        exclude_tags.extend(["OIDC flow only", "OIDC redirect", "OIDC callback"])
    if protocol != "saml":
        exclude_tags.extend(["SAML only", "SAML assertion", "SAMLResponse", "saml_login"])
    filtered_patterns = {}
    for inv, pats in CROSS_PLATFORM_ATTACK_PATTERNS.items():
        filtered = [p for p in pats if not any(tag in p for tag in exclude_tags)]
        if filtered:
            filtered_patterns[inv] = filtered

    attack_patterns_text = "\n".join(
        f"  {inv}:\n" + "\n".join(f"    - {p}" for p in patterns)
        for inv, patterns in filtered_patterns.items()
    )

    example_snippet = """
Example input_operation (admin setup):
  "create_auth_role": {
    "method": "POST",
    "path": "/v1/auth/{mount}/role/{role_name}",
    "body_map": {
      "identity_claim": "user_claim",
      "audience_restriction": "bound_audiences",
      "claim_constraints": "bound_claims",
      "claim_constraint_type": "bound_claims_type",
      "groups_claim": "groups_claim",
      "granted_policies": "token_policies",
      "bound_subject": "bound_subject",
      "token_ttl": "token_ttl"
    },
    "response_map": {},
    "auth": "admin"
  }

Example input_operation (login — note the COMPLETE response_map):
  "login_with_jwt": {
    "method": "POST",
    "path": "/v1/auth/{mount}/login",
    "body_map": {
      "role": "role",
      "token": "jwt"
    },
    "response_map": {
      "session_token": "auth.client_token",
      "identity_id": "auth.entity_id",
      "granted_policies": "auth.policies",
      "identity_policies": "auth.identity_policies",
      "metadata": "auth.metadata",
      "token_accessor": "auth.accessor"
    },
    "auth": "none"
  }

Example input_operation (policy creation — NOTE: use CURRENT path, not legacy):
  "create_policy": {
    "method": "POST",
    "path": "/v1/sys/policies/acl/{name}",
    "body_map": {
      "policy_document": "policy"
    },
    "response_map": {},
    "auth": "admin"
  }
  (NOT /v1/sys/policy/{name} — that is the pre-0.9 legacy endpoint)

Example input_operation (session revocation — NOTE: explicit token in body, admin auth):
  "revoke_session": {
    "method": "POST",
    "path": "/v1/auth/token/revoke",
    "body_map": {
      "session_token": "token"
    },
    "response_map": {},
    "auth": "admin"
  }
  (NOT /v1/auth/token/revoke-self — that self-revokes the calling token)

Key conventions:
- body_map keys are ABSTRACT names (platform-independent), values are PLATFORM-SPECIFIC parameter names.
- Paths MUST include the full prefix as used in real HTTP requests (e.g., /v1/ for Vault).
- Configurable path segments (mount points, realm names, plugin paths) MUST use {placeholders}, not hardcoded defaults. Write /v1/auth/{mount}/login, NOT /v1/auth/jwt/login.
"""

    return f"""## Task
Extract ALL security-relevant API operations from the {platform} documentation below.
Target protocol: {protocol}

## Fuzzer Execution Context

The fuzzer executes test sequences as ordered event lists. A typical sequence is:
  0. Tenant:  create_tenant (if platform requires realm/org creation before any setup)
  1. Setup:   enable_auth_method → configure_* → create_auth_role → create_policy → seed_protected_resource
  2. Login:   login_with_jwt / login_with_password / etc.  →  yields session_token
  3. Verify:  verify_granted_identity (token self-lookup) → verify_read_secret (access a resource)
  4. Cleanup: revoke_session / cleanup_auth_method

Use this when writing api_constraints about session/token resource limits:
  - Any platform parameter that limits how many times a session or token can be used
    counts EVERY API call made with that session, including step-3 verification calls.
    Example: if num_uses=1, calling verify_granted_identity exhausts the budget before
    verify_read_secret runs — the access test returns 403 for the wrong reason.
    Emit a CRITICAL constraint flagging this for each such parameter.

## JWT Claim Template Variables

The fuzzer constructs JWT claims using these template variables. Use them when writing
timing-related api_constraints instead of hardcoded integers:
  {{{{now_epoch}}}}            — current Unix timestamp (seconds)
  {{{{now_epoch_plus_N}}}}    — current time + N seconds  (e.g. {{{{now_epoch_plus_3600}}}})
  {{{{now_epoch_minus_N}}}}   — current time − N seconds  (e.g. {{{{now_epoch_minus_7200}}}})
  {{{{jwt_sub}}}}              — the subject claim value for the current test identity

## Output Schema

Return a single JSON object with these top-level keys:

{{
  "input_operations": [...],           // Operations for setting up test scenarios
  "api_constraints": [...],            // Platform rules/limitations
  "known_behaviors": [...],            // By-design behaviors that look like bugs
  "verification_fields": {{...}}       // Identity display-name patterns (see section 4)
}}

### 1. input_operations (→ goes into profiles/{platform}.json api_mapping)

These are operations that appear as EVENTS in test sequences. Include ALL operations that:
- Set up the test environment (AUTH_CONFIG, IDENTITY_MGMT, AUTHZ_CONFIG, RESOURCE_MGMT)
- Perform login / authentication (AUTH_LOGIN)
- Inspect the authenticated session's own state within a sequence (SESSION_INSPECT) —
  e.g. token self-lookup, entity lookup by id, reading a secret with the session token.
  These are called in the "verify phase" of a sequence, NOT out-of-band audit ops.
- Manage session lifecycle (SESSION_MGMT)

IMPORTANT: token lookup-self, entity/identity lookup, secret read-with-session-token are
ALL input_operations — they appear as events inside test sequences and must be in this list.

NOTE on "Target protocol": Extract ONLY operations, api_constraints, and known_behaviors
relevant to the target protocol ({protocol}). Do NOT extract configuration or login
operations for other auth methods (e.g., if target is oidc_jwt, omit SAML/LDAP/userpass
config and login operations). Other protocols are extracted in separate --protocol runs.

Shared/infrastructure operations needed by ALL protocols — enable_auth_method, create_policy,
revoke_session, cleanup_auth_method, verify_granted_identity, verify_entity_details,
verify_entity_details_by_name, verify_read_secret, seed_protected_resource,
create_identity_group, create_group_alias, get_mount_accessor — belong under the target
protocol.

COMPLETENESS RULES:
1. Multi-path lookups: For any resource that has GET endpoints with DIFFERENT path templates
   (e.g., GET /entity/id/{{id}} AND GET /entity/name/{{name}}), extract EACH path as a
   SEPARATE operation with its own operation_name. Do not merge different URL shapes into
   one operation. The fuzzer uses different lookup paths to cross-reference identities and
   detect collision or confusion.
3. When in doubt, include: a missing operation causes a runtime failure; an extra operation
   that goes unused is harmless. Always err on the side of extracting more operations.

Classify each operation into one of these categories:
- AUTH_CONFIG: Configure authentication methods (enable JWT auth, set JWKS URL, etc.)
- AUTH_LOGIN: Execute authentication (JWT login, OIDC callback, SAML assertion, password, etc.)
- IDENTITY_MGMT: Manage identity objects (create entities, aliases, groups, group-aliases)
- AUTHZ_CONFIG: Configure authorization policies (create ACL policies, role policies)
- RESOURCE_MGMT: Manage protected resources (create secrets, seed test data)
- SESSION_MGMT: Manage sessions/tokens (revoke, renew)
- SESSION_INSPECT: Inspect own session state (token lookup-self, read secret, entity lookup)

For EACH operation, extract:
{{
  "operation_name": "abstract_name",
  "category": "AUTH_CONFIG|AUTH_LOGIN|IDENTITY_MGMT|AUTHZ_CONFIG|RESOURCE_MGMT|SESSION_MGMT|SESSION_INSPECT",
  "method": "GET|POST|PUT|DELETE|LIST",
  "path": "/exact/api/path/with/{{placeholders}}",
  "path_params": ["mount", "role_name"],
  "body_map": {{"abstract_param": "platform_param"}},
  "response_map": {{"abstract_field": "data.field.path"}},
  "auth": "admin|session|none",
  "content_type": "json|form|query",
  "metadata": {{}},
  "description": "one-line description",
  "invariant_relevance": ["I4", "I5"],
  "dependencies": ["other_operation_name"]
}}

### 2. api_constraints (→ goes into profiles/{platform}.json api_constraints)

Two types of constraints are needed:

**Type A — API setup constraints**: Platform-specific rules NOT obvious from the API signature.
Examples:
- "External groups cannot have member_entity_ids set manually — use group aliases instead"
- "Every JWT role requires at least one bound constraint (bound_audiences, bound_claims, or bound_subject)"

**Numeric sentinel analysis (part of Type A):** For every numeric configuration parameter
(TTL, leeway, num_uses, expiry, count), check:
- Does the value 0 mean literal zero, OR does it select a platform-default nonzero value?
- Is there a special sentinel (e.g. -1, -1s, "0s") that means "disable" or "strict"?
If yes to either, emit a CRITICAL constraint naming both sentinels and their exact meanings.
Example: "value 0 = use default (~150s); value -1 = strict with no extra buffer but the
underlying check is still enforced; never assume -1 disables the underlying validation."

**Session-use budget analysis (part of Type A):** For every parameter that limits the
number of times a session or token can be used (num_uses, max_uses, one_time, etc.):
Emit a CRITICAL constraint stating that verification calls made with the session token
BEFORE the target access test (see Fuzzer Execution Context above) consume uses.
Give the minimum safe value if the fuzzer needs both a verification step and an access test.

**Type B — Testing strategy constraints**: Cross-reference the ATTACK PATTERNS below with the platform documentation. For each attack pattern that targets this platform, identify platform-specific behaviors that would cause false positives, incorrect test setup, or misinterpreted results. These constraints tell the fuzzer HOW to test correctly on this platform.

For each testing strategy constraint, reason as follows:
1. What does the attack pattern try to test? (e.g., I1 issuer validation)
2. What does the platform documentation say about the relevant behavior? (e.g., bound_issuer is optional; omitting it skips issuer comparison)
3. What would go wrong if the fuzzer doesn't know this? (e.g., test passes trivially because issuer check was never configured)
4. Write the constraint as a CRITICAL instruction: what the fuzzer MUST or MUST NOT do.

**Parameter matching semantics analysis (important for Type B):**
For each parameter that constrains authentication (subject restrictions, claim constraints, audience restrictions, attribute restrictions), determine:
- What matching mode does it support? (exact string only, glob/wildcard, regex, list-membership)
- Does it have a companion parameter that controls the matching mode? (e.g., a _type suffix parameter toggling between exact and glob)
- If NO companion _type parameter exists, the parameter almost certainly supports exact match ONLY — wildcards like * will be treated as literal characters.
- CRITICAL consequence for multi-identity tests (I4): if the fuzzer needs multiple different values to pass the same constraint, an exact-match-only parameter MUST be OMITTED entirely, NOT set to a wildcard pattern. Setting an exact-match parameter to '*' means only the literal string '*' will match.
Emit a CRITICAL constraint for EACH constraint parameter, stating its matching semantics and what the fuzzer must do for multi-identity scenarios.

**Claim value type analysis (important for Type B — I5):**
For each parameter that binds/constrains claim VALUES (e.g., bound_claims, bound_attributes):
- What value types does the documentation say are accepted? (string, integer, boolean, list)
- Does a companion matching-mode parameter (e.g., bound_claims_type) affect how non-string
  types are handled? When the default mode says values are "treated as literals" or "must
  match exactly", it typically means string comparison — non-string types (integer, boolean)
  in the JWT claim will be rejected because they are not strings. A glob/wildcard mode often
  coerces values to strings first, which lets non-string types pass through to matching.
  If this applies, the constraint MUST state: "For I5 numeric coercion tests, set
  bound_claims_type to glob (not the default string) so that numeric claim values are
  coerced to strings rather than rejected outright."
- If the docs do NOT specify cross-type behavior, emit a CRITICAL constraint noting that the
  fuzzer SHOULD test numeric type coercion: set a bound value as integer N, then send a JWT
  with float N+0.7 — if the platform truncates the float, it silently matches (I5 violation).
  State which parameter(s) accept numeric values, AND which matching mode (if any) must be
  set for the platform to accept numeric claims without rejecting them outright.

Example testing strategy constraints:
- "CRITICAL: When testing I1 issuer validation, configure_jwt_validation MUST include bound_issuer. Without it, the platform skips issuer comparison entirely."
- "CRITICAL for I3 config-change sequences: when an admin changes config, NEW logins operating under the updated config are BY DESIGN. A valid I3 test must show the SAME request being evaluated inconsistently, NOT that an admin action legitimately changed behavior."
- "CRITICAL: For I5 tightening tests, modify_role_config must NARROW permissions. Do NOT empty claim constraints — that BROADENS access."
- "CRITICAL: bound_subject supports EXACT string match only — no glob, no wildcards. For I4 multi-user tests, OMIT bound_subject entirely so different sub values can authenticate to the same role."
- "CRITICAL: For I2 token-freshness tests (expired_token, future_token, nbf), the sequence MUST include a CONTROL login using a valid token (exp={{{{now_epoch_plus_3600}}}}, iat={{{{now_epoch}}}}) alongside the ATTACK login. Without a control, LOGIN_FAILED on the attack token cannot be distinguished from a broken test setup."

### Attack Patterns Reference (for generating Type B constraints)
{attack_patterns_text}

### 3. known_behaviors

Platform behaviors that LOOK like security bugs but are BY DESIGN.
Format:
[
  {{
    "id": "{platform}_descriptive_name",
    "description": "What the behavior is",
    "invariants": ["I4"],
    "conditions": {{"field.path": "expected_value"}},
    "source": "documentation reference",
    "note": "Why this matters for testing"
  }}
]

In addition to platform-specific behaviors from the documentation, include these RFC/spec-valid
behaviors as known_behaviors when the platform implements them per spec:

- **nbf is OPTIONAL** (RFC 7519 §4.1.5): If the platform does not check the `nbf` (not before) claim,
  this is spec-compliant. `nbf` is OPTIONAL — brokers are not required to enforce it. Do NOT flag
  acceptance of JWTs without `nbf` or with future `nbf` as a vulnerability.
- **Bearer token reuse is by design**: A valid, unexpired bearer JWT can be used across multiple sessions
  and API calls. This is the fundamental bearer token contract (RFC 6750). Only flag replay if the
  platform explicitly uses `jti`-based replay tracking or the token is a one-time artifact.
- **Lookup artifacts are idempotent**: If the platform issues lookup/intent tokens (e.g., IdP intent tokens,
  authorization references) that are designed for idempotent retrieval, re-fetching the same artifact
  is BY DESIGN, not a replay vulnerability. Only flag if the artifact is documented as single-use.
- **JWKS cache TTL**: After admin rotates signing keys (JWKS URL change, key rotation), the old key
  may remain accepted until the JWKS cache TTL expires. This is standard JWKS caching behavior
  (RFC 7517), not a trust anchor violation. Only flag if the old key is accepted AFTER cache expiry.
- **Admin-authorized trust anchor changes**: When an admin explicitly reconfigures the JWKS URL, issuer,
  or signing key, the platform accepting tokens from the new trust anchor is BY DESIGN. The admin
  authorized the change. Do NOT flag this as I1/I3 — it is not an attacker substituting a trust anchor.

### 4. verification_fields

Extract identity display-name patterns used by the auth platform.

The fuzzer compares the identity it SENT (e.g. the JWT sub claim "victim-user") against
the identity the platform GRANTED (e.g. the display_name from token lookup-self). If these
differ, it flags an I4 violation — UNLESS the difference is just a platform-added prefix.

To find the pattern, examine:
1. Token lookup / self-lookup response EXAMPLES in the docs — look at the display_name
   field. Does it contain a prefix before the username? (e.g. "ldap2-tesla" where "tesla"
   is the user and "ldap2" is the auth mount path)
2. Entity alias naming docs — how does the platform construct alias names?
3. The user_claim / identity_claim parameter — what claim value becomes the alias name?

If the display_name follows a pattern like "{{mount_path}}-{{user_claim_value}}", extract:
{{
  "identity_prefix_pattern": ".*-{{sent}}$"
}}

The {{sent}} placeholder represents the identity value the fuzzer sent. The oracle will
regex-match ".*-{{sent}}$" against the granted display_name. If it matches, the prefix is
treated as platform metadata, not an identity mismatch.

If display_name equals the user claim exactly (no prefix), return {{}}.

Also check if the platform returns a DERIVED form of the identity instead of the exact value sent.
Common derivation patterns:
- Email derivation: username "alice" → "alice@org.local" (platform auto-generates email from username)
- Lowercase normalization: "Alice" → "alice" (case-insensitive platforms)
- Display name vs username: verify_granted_identity returns display_name but the fuzzer sends username

If the platform derives the identity (e.g., appends an email domain to the username), extract:
{{
  "identity_prefix_pattern": "{{sent}}@.*"
}}
This matches "alice@org.local" when sent="alice", preventing false I4 violations from email derivation.

For admin-authorized configuration changes: If the platform allows admins to change trust anchors (JWKS URLs, signing keys, issuer bindings) and the new configuration is expected to take effect immediately, document this in a known_behavior. Admin-initiated trust anchor rotation is BY DESIGN, not a vulnerability. The oracle should not flag a login that succeeds because an admin changed the JWKS URL — that is the admin authorizing a new trust anchor. Only flag if the OLD (pre-rotation) key/issuer is accepted AFTER the admin explicitly rotated to a new one AND the cache TTL has expired.

## Required Canonical Operation Names

The following operations are REQUIRED in input_operations if the platform supports them.
You MUST use these EXACT names — do not add suffixes (_v1, _v2, _by_id, _by_name, etc.).
If multiple API variants exist for one operation (e.g. KV v1 vs v2, lookup by id vs name),
pick the most appropriate single variant and map it to the canonical name.
Additional variants may be extracted under distinct names, but the PRIMARY variant MUST use
the canonical name below.

If you cannot find a platform API for a canonical operation, still note it is absent —
do NOT silently skip it, as a missing operation causes runtime failures.

{ops_reference}

## Format Example
{example_snippet}

## RULES
1. Extract ONLY operations that are explicitly documented in the provided documentation. If the documentation does not describe an endpoint, do NOT invent it from general knowledge of other platforms. For example, if the docs have no admin API for creating policies or reading secrets, do NOT add create_policy or seed_protected_resource operations. It is far better to return fewer operations that are accurate than many operations that are hallucinated. Completeness means extracting everything FROM THE DOCS, not filling gaps from other platforms.
2. Use exact API paths from documentation — do not guess or invent paths. Each path must correspond to exactly ONE documented endpoint. Do NOT concatenate path segments from different endpoints (e.g., if docs show /broker/{{alias}}/endpoint and separately /clients/{{id}}, the callback is /broker/{{alias}}/endpoint — NOT /broker/{{alias}}/endpoint/clients/{{id}}). When unsure, prefer the shorter documented path.
3. body_map keys MUST be abstract/platform-independent names. Values are platform-specific parameter names that appear in the documentation's request body/parameters section for THAT endpoint. Do NOT include parameters from other endpoints, deprecated API versions, or general knowledge.
4. response_map keys MUST be abstract names. Values are JSON dot-paths in the actual response.
5. For AUTH_LOGIN operations, response_map MUST be COMPLETE — include ALL of these fields when the platform returns them: session_token (the credential), identity_id (entity/user ID assigned by the platform), granted_policies (policies/roles/permissions list), identity_policies (inherited/identity-system policies), metadata (user metadata or claims), token_accessor (token reference/accessor ID). A login response_map with only session_token is INCOMPLETE.
    CRITICAL: "session_token" MUST map to the credential used for subsequent API calls (Bearer token). For OIDC token endpoints that return both access_token and id_token, session_token MUST map to "access_token" (the API credential), NOT "id_token" (the client-side identity assertion). The fuzzer uses session_token as a Bearer token for /userinfo and other API calls — id_token cannot be used for this purpose.
6. For parameters that appear in the URL path, list them in path_params.
7. Include dependency information — which operations must succeed before this one.
8. Tag EVERY operation with invariant_relevance.
9. Extract ALL constraints — missing constraints cause test setup failures.
10. For known_behaviors, conditions must be matchable by KnownBehaviorFilter.
11. API paths MUST include the full path prefix as used in actual HTTP requests (e.g., /v1/ for Vault, /admin/realms/ for Keycloak). Do NOT strip version or API prefixes.
12. Configurable path segments — such as auth method mount points, realm names, engine paths, or plugin names — MUST use {{placeholders}} like {{mount}}, {{realm}}, {{engine}}. Do NOT hardcode default values like "jwt", "oidc", "userpass", "secret". For example: /v1/auth/{{mount}}/login, NOT /auth/jwt/login.
13. Extract ALL parameters documented for each endpoint into body_map, not just the most common ones. Include optional parameters, token tuning parameters (TTL, num_uses, max_ttl, type, bound_cidrs), matching-mode parameters, and advanced configuration options. Completeness of body_map is critical — missing parameters mean the fuzzer cannot test those attack surfaces.
14. Use consistent abstract names across operations. The same semantic concept must always use the same abstract key: e.g., always "granted_policies" (not sometimes "policies" and sometimes "token_policies"), always "identity_claim" (not sometimes "user_claim_field").
15. Parameters already encoded as {{param}} in the path template MUST NOT also appear in body_map. Path params are resolved by the executor from the event params dict; duplicating them in body_map sends the value twice and breaks execution.
16. For operations where the API response is a map keyed by a dynamic value (e.g., the mount path, realm name, or other runtime variable), encode the dynamic key in response_map using the same placeholder as in the path template. Example: if GET /v1/sys/auth returns {{"jwt/": {{"accessor": "auth_jwt_xxx"}}, "kubernetes/": {{...}}}}, write response_map as {{"mount_accessor": "{{mount}}/.accessor"}} — the placeholder mirrors {{mount}} from the path, followed by the subfield.
17. CURRENT vs LEGACY parameter names: When a platform's API docs show both deprecated/legacy field names (e.g., "policies", "ttl", "num_uses" without prefix) AND current names (e.g., "token_policies", "token_ttl", "token_num_uses" with a prefix), ALWAYS use the CURRENT names in body_map values. Legacy names typically appear in old response examples or compatibility notes; current names appear in the Parameters/Request Body table. Using legacy names silently sends wrong fields and breaks test setup.
    Similarly, prefer the CURRENT versioned API path over a legacy shorter path when both exist. Example: use /v1/sys/policies/acl/{{name}} (current) not /v1/sys/policy/{{name}} (legacy pre-0.9). Use /v1/sys/policies/acl for policy management if the platform is Vault 0.9+.
    Abstract key names in body_map MUST follow the canonical vocabulary from the Required Canonical Operation Names section above — e.g., always use "granted_policies" (abstract) → "token_policies" (platform), never "token_policies" → "token_policies". The abstract key is platform-independent; the value is platform-specific.
18. For `revoke_session` and any token/session revocation operation: use the endpoint that accepts an EXPLICIT token value in the request body and uses admin authentication (e.g., POST /revoke with body {{"token": "<value>"}}).  Do NOT use a self-revoke endpoint (e.g., /revoke-self) which revokes the calling token. The fuzzer uses admin credentials for cleanup and must specify which session token to revoke — using self-revoke with admin auth would destroy the admin token.
19. For `exchange_code_for_token`: this maps to the AUTH METHOD's OIDC callback endpoint (the URL that receives the authorization code from the IdP, e.g., /auth/{{mount}}/oidc/callback), NOT to any identity provider token-exchange endpoint. It completes the browser-based OIDC authorization code flow started by `start_oidc_auth`.
25. Standard OIDC endpoints MUST be extracted for any OIDC-based platform. These are well-known endpoints defined by the OpenID Connect specification and are present on all compliant platforms:
    - Authorization endpoint (e.g., /auth, /authorize) → `start_oidc_auth` — set content_type="query" and metadata={{"follow_redirects": false}} (auth endpoints return 302 redirects; the executor must NOT follow them)
    - Token endpoint (e.g., /token) → `exchange_code_for_token` — set content_type="form" (OAuth2 RFC 6749 requires application/x-www-form-urlencoded for token requests)
    - Token exchange endpoint (if same as token endpoint) → `token_exchange` — set content_type="form"
    - Token revocation endpoint (e.g., /token/revoke) → `revoke_session` — set content_type="form"
    - UserInfo endpoint (e.g., /userinfo) → `verify_granted_identity` (auth=session, returns identity claims: sub, email, groups, etc.)
    If the documentation mentions OIDC Discovery (/.well-known/openid-configuration), extract ALL endpoints listed there.
    For platforms where SAML is an upstream connector but the token/userinfo flow is still OIDC (e.g., Dex SAML connector, Keycloak SAML broker), the SAML profile MUST also include `exchange_code_for_token` and `verify_granted_identity` since the SAML assertion is exchanged for an OIDC token.
26. SAML Assertion Consumer Service (ACS) endpoints — the `saml_login` operation — MUST use:
    - method: POST (SAML HTTP POST binding — the IdP POSTs the signed assertion to the SP)
    - content_type: "form" (the SAMLResponse is sent as application/x-www-form-urlencoded)
    - body_map MUST include: {{"saml_response": "SAMLResponse", "relay_state": "RelayState"}}
    - metadata MUST include: {{"initiate_saml_flow": true}}
    The executor uses the initiate_saml_flow flag to start the SP-initiated SAML flow before building the SAMLResponse. This is required for ALL SAML platforms because the SP (Dex, Keycloak, Authentik, etc.) issues an AuthnRequest first, and the SAMLResponse must include a matching InResponseTo attribute. Without this flag, the executor sends a fabricated SAMLResponse that the SP will reject.
    Do NOT use GET for SAML callbacks. The SAML HTTP POST binding is a form submission, not a redirect.
27. SAML profiles MUST also include `login_with_password` if the platform supports it. The fuzzer uses password-based admin login to establish an admin session for test setup (creating providers, users, applications). Without `login_with_password`, the admin session cannot be established and all SAML test setup fails.
28. User and application management APIs MUST be extracted when documented. The fuzzer needs these for test setup:
    - `create_user` / `delete_user` / `update_user` — create test users, enable MFA, set roles
    - `create_application` / `update_application` — register OAuth/SAML apps, set audience, redirect URIs
    - `create_organization` — create tenants for multi-tenancy testing
    - `create_provider` — register identity providers (SAML IdP, OIDC provider)
    - `mfa_setup_enable` — enable MFA on a user (if documented as an API endpoint)
    If the documentation describes a data model (e.g., User properties, Application settings) but also mentions API CRUD patterns (e.g., /api/add-user, POST to create), extract the CRUD endpoints. Even if the docs focus on UI workflows, look for REST API examples, curl commands, or Swagger/OpenAPI references that reveal the endpoint paths.
    IMPORTANT for body_map: Extract the resource's documented data model fields individually. Check the documentation or API examples to determine if the request body is FLAT (fields at the top level, e.g., {{"name": "x", "clientId": "y"}}) or WRAPPED in a resource key (e.g., {{"application": {{"name": "x", "clientId": "y"}}}}). Use the format the API actually expects:
    - FLAT body (most REST APIs): body_map values are flat field names, e.g., {{"client_id": "clientId", "name": "name"}}
    - WRAPPED body (some APIs nest under a resource key): body_map values use dot-notation, e.g., {{"client_id": "config.clientId"}}
    When in doubt (no curl examples or request body samples in docs), prefer FLAT format — it is more common and the executor handles both.
33. OIDC SSO id_token validation constraints: When a platform acts as a relying party (RP) consuming id_tokens from external OIDC identity providers (SSO connectors, social login sources), emit Type B constraints about the expected validation checks per the OIDC Core specification (Section 3.1.3.7). Key validation requirements:
    - nonce: The id_token MUST contain a nonce claim matching the value sent in the authorization request. Missing or mismatched nonce enables replay attacks (I2).
    - aud: The id_token audience MUST match the client_id of the RP. Accepting tokens for other audiences breaks tenant isolation (I1/I5).
    - iss: The id_token issuer MUST match the configured IdP issuer URL. Skipping issuer validation enables cross-IdP token injection (I1).
    - exp: The id_token MUST NOT be expired. Missing exp check enables infinite-lifetime tokens (I2).
    If the documentation mentions nonce generation, id_token verification config, or references to OIDC Core validation steps, emit constraints about which checks are performed and which may be missing.
32. For platforms using gRPC with REST/JSON gateway (e.g., proto-defined APIs): when a proto field is defined as `bytes` type, the JSON representation MUST be base64-encoded. Common examples: SAML metadata XML (`metadataXml`), certificates, binary keys. If the body_map includes a field documented as `bytes` in the proto definition, emit a CRITICAL api_constraint: "Field X requires base64-encoded value in JSON requests (proto bytes type). Raw strings will be rejected with 'invalid value for bytes field'."
31. Resource creation APIs that return 201 with NO response body (e.g., Keycloak POST /admin/realms returns 201 empty, Vault POST /sys/auth returns 204 empty): the response_map for these operations should ONLY contain {{"http_status": "_http_status"}}. Do NOT try to capture resource names or IDs from the response — they are not there. The resource name/ID comes from the INPUT params (e.g., the realm name you sent in the request body). When generating Type B constraints, include: "create_tenant returns 201 with no body — the realm/tenant name is the value you provided in params, not a response field. Do NOT use captures for the resource name; reference the params value directly in subsequent events."
30. CREATE vs UPDATE endpoints: When a platform has separate POST (create) and PUT (update) endpoints for the same resource type (e.g., identity providers, clients), `enable_auth_method` MUST use POST (create a new resource). If the docs show both POST and PUT for the same resource path, extract `enable_auth_method` with POST (create) and `configure_jwt_validation` or `modify_role_config` with PUT (update). Using PUT on a non-existent resource returns 404. The fuzzer always creates fresh resources in test setup, so creation endpoints MUST use POST.
29. Resource ownership in multi-tenant platforms: Many platforms use an "owner" field to control which tenant owns a resource. IMPORTANT: different resource types may have DIFFERENT owner semantics. For example, users might be owned by an organization ("owner": "org-name"), while applications and providers might be owned by the admin account ("owner": "admin"). If the documentation shows examples of creating resources with specific owner values, or if API examples show different owner values for different resource types, extract this as a Type B constraint (e.g., "Applications and providers MUST set owner='admin', while users set owner=organization_name"). This prevents the fuzzer from using the wrong owner value in API calls.
    For MFA/2FA: if the docs describe MFA setup (TOTP, SMS, email codes), look for a REST API endpoint to programmatically enable MFA on a user. IMPORTANT: if the documentation lists webhook event names or action names like "mfa/setup/initiate", "mfa/setup/verify", "mfa/setup/enable", "delete-mfa", "set-preferred-mfa" — these ARE REST API paths (prefixed with /api/). Extract `mfa_setup_enable` as POST /api/mfa/setup/enable with body params: owner, name (username), mfaType (e.g., "app" for TOTP), secret (TOTP base32 secret). Similarly extract the initiate/verify steps if listed. If MFA is enabled through the user update API (e.g., setting preferredMfaType field), document this in `update_user`'s body_map instead.
22. For `verify_entity_details`: use the DIRECT GET endpoint that accepts an entity ID as a path parameter (e.g., /identity/entity/id/{{identity_id}}), NOT the lookup/search endpoint (e.g., /identity/lookup/entity). The fuzzer obtains the entity_id from the login response and does a direct GET — it does not search by name or alias.
23. For `verify_read_secret` on KV v2 platforms: the read path MUST include the /data/ segment (e.g., /v1/{{engine}}/data/{{path}} or /v1/secret/data/{{path}}). Omitting /data/ hits the KV v1 endpoint which does not exist on KV v2 mounts and returns 404.
24. For `create_identity_group`: use the generic POST endpoint without a name in the path (e.g., POST /v1/identity/group with name in the body), NOT the by-name variant (e.g., /v1/identity/group/name/{{name}}). The generic endpoint returns the created group's ID in the response, which is needed for subsequent alias creation.
20. In response_map, include {{"http_status": "_http_status"}} for every operation where a 2xx vs 4xx outcome is security-relevant: login operations, access/read tests (verify_read_secret), and session revocation. The special key "_http_status" is populated by the executor with the actual HTTP response status code and is critical for detecting permission-denied vs success outcomes.
21. For token/session self-lookup operations (verify_granted_identity), the response_map MUST include all time and usage fields: ttl, creation_ttl, expire_time, num_uses, and identity fields: identity_id, display_name, granted_policies, identity_policies, metadata. These fields are required for I2 freshness tests and I4/I5 identity tests.

## DOCUMENTATION ({platform} / {protocol})

{docs_text}
"""


# ---------------------------------------------------------------------------
# Post-processing: split LLM output into profile.json + api_spec.json
# ---------------------------------------------------------------------------

def split_and_save(
    llm_output: dict,
    platform: str,
    protocol: str,
    model_name: str = "unknown",
    profile_path: Optional[str] = None,
    no_merge: bool = False,
    tag: str = None,
) -> dict:
    """Save LLM extraction output as a platform profile JSON.

    When no_merge=True the existing profile is ignored; output is written to
    a timestamped file so successive runs can be compared without clobbering
    each other or the hand-written profile.

    Returns dict with profile path and extraction stats.
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    tag_part = f"_{tag}" if tag else ""
    if no_merge:
        profile_path = f"src/profiles/{platform}_{protocol}{tag_part}_{ts}.json"
    else:
        profile_path = profile_path or f"src/profiles/{platform}.json"

    # ── 1. Build / update profiles/{platform}.json ──────────────────────────
    if not no_merge and os.path.exists(profile_path):
        with open(profile_path) as f:
            profile = json.load(f)
    else:
        defaults = PLATFORM_DEFAULTS.get(platform, {})
        profile = {
            "name": platform,
            "base_url": defaults.get("base_url", f"http://localhost:8080"),
            "admin_auth": defaults.get("admin_auth", {"header": "Authorization", "value": ""}),
            "supported_protocols": [],
            "api_mapping": {},
            "known_behaviors": {},
            "verification_fields": defaults.get("verification_fields", {}),
            "api_constraints": {},
        }
        # Copy optional deployment config from PLATFORM_DEFAULTS
        for opt_key in ("environment_defaults", "session_auth_method", "cookie_login",
                         "init_hooks", "identity_carrying_types", "cleanup_rules"):
            val = defaults.get(opt_key)
            if val is not None:
                profile[opt_key] = val

    # Build api_mapping for target protocol from input_operations.
    # When no_merge=True start empty so we see exactly what the LLM produced.
    existing_ops = {} if no_merge else profile.get("api_mapping", {}).get(protocol, {})
    api_mapping: dict = dict(existing_ops)
    total_ops = 0

    for op in llm_output.get("input_operations", []):
        name = op.get("operation_name")
        if not name:
            continue

        method = op.get("method", "POST")
        path = op.get("path", "")

        # Skip ops with empty/invalid paths or placeholder methods (LLM couldn't find them)
        if not path or method.upper() in ("ABSENT", "UNKNOWN", "N/A", "NONE") \
                or path.upper() in ("ABSENT", "UNKNOWN", "N/A", "NONE", "NOT_DOCUMENTED"):
            continue

        # Strip analysis-only fields that don't belong in the profile
        endpoint = {
            "method": method,
            "path": path,
            "body_map": op.get("body_map", {}),
            "response_map": op.get("response_map", {}),
            "auth": op.get("auth", "admin"),
        }
        # Preserve optional fields if present
        ct = op.get("content_type")
        if ct and ct != "json":
            endpoint["content_type"] = ct
        meta = op.get("metadata")
        if meta and isinstance(meta, dict):
            endpoint["metadata"] = meta
        # Auto-flatten wrapper body_maps: if ALL body_map values share a common
        # single-segment prefix (e.g., "application.name", "application.clientId"),
        # strip it — the API likely accepts flat bodies, not wrapped ones.
        bm = endpoint.get("body_map", {})
        if len(bm) >= 3:
            prefixes = set()
            for v in bm.values():
                if "." in v:
                    prefixes.add(v.split(".")[0])
                else:
                    prefixes = set()  # mixed flat + dot = don't touch
                    break
            if len(prefixes) == 1:
                prefix = prefixes.pop() + "."
                endpoint["body_map"] = {
                    k: v[len(prefix):] if v.startswith(prefix) else v
                    for k, v in bm.items()
                }

        api_mapping[name] = endpoint
        total_ops += 1

    # Inject extra_operations from PLATFORM_DEFAULTS (verified endpoints).
    # These ALWAYS override LLM-extracted ops — they contain verified REST paths,
    # correct body_maps, and proper content_types. LLM extractions from proto files
    # often produce wrong paths (gRPC Connect instead of REST gateway).
    defaults = PLATFORM_DEFAULTS.get(platform, {})
    extra_ops = defaults.get("extra_operations", {})
    for op_name, op_def in extra_ops.items():
        was_missing = op_name not in api_mapping
        api_mapping[op_name] = dict(op_def)
        if was_missing:
            total_ops += 1

    profile["api_mapping"][protocol] = api_mapping

    # Backfill missing ops from sibling protocol profiles.
    # Many ops are protocol-independent (user/app management, auth setup, verification).
    # If the OIDC extraction found these ops but the SAML extraction missed them
    # (due to doc coverage or LLM inconsistency), backfill from the sibling.
    # Only protocol-specific ops (saml_login, login_with_jwt) are excluded from backfill
    # since they're meaningfully different per protocol.
    PROTOCOL_SPECIFIC_OPS = {
        "saml_login", "login_with_jwt", "configure_jwt_validation",
    }
    all_current_ops = set(api_mapping.keys())
    # Collect all ops from sibling profiles that are missing from current
    missing_mgmt = set()  # will be populated from sibling ops
    _sibling_ops_pool = {}  # op_name -> endpoint dict
    def _is_valid_op(ep: dict) -> bool:
        """Check if an endpoint has a real path and method."""
        p = ep.get("path", "")
        m = ep.get("method", "")
        invalid = ("ABSENT", "UNKNOWN", "N/A", "NONE", "NOT_DOCUMENTED", "")
        return bool(p) and p.upper() not in invalid and m.upper() not in invalid

    # Collect valid ops from sibling profiles (same platform, different protocol or older runs)
    import glob
    sibling_pattern = f"src/profiles/{platform}_*_extracted_*.json"
    for sib_path in sorted(glob.glob(sibling_pattern), reverse=True):
        if sib_path == profile_path:
            continue
        try:
            with open(sib_path) as sf:
                sib = json.load(sf)
            for sib_proto, sib_ops in sib.get("api_mapping", {}).items():
                for op_name, op_ep in sib_ops.items():
                    if op_name not in _sibling_ops_pool and _is_valid_op(op_ep):
                        _sibling_ops_pool[op_name] = dict(op_ep)
        except Exception:
            continue

    # Also check other protocol sections already in this profile
    for other_proto, other_ops in profile.get("api_mapping", {}).items():
        if other_proto == protocol:
            continue
        for op_name, op_ep in other_ops.items():
            if op_name not in _sibling_ops_pool and _is_valid_op(op_ep):
                _sibling_ops_pool[op_name] = dict(op_ep)

    # Backfill: add ops from siblings that are missing from current extraction
    # Skip protocol-specific ops that shouldn't cross protocols
    for op_name, op_ep in _sibling_ops_pool.items():
        if op_name not in all_current_ops and op_name not in PROTOCOL_SPECIFIC_OPS:
            api_mapping[op_name] = op_ep
            total_ops += 1

    profile["api_mapping"][protocol] = api_mapping

    if protocol not in profile.get("supported_protocols", []):
        profile.setdefault("supported_protocols", []).append(protocol)

    # api_constraints: store per-protocol
    existing_ac = profile.get("api_constraints", {})
    if isinstance(existing_ac, list):
        # Backward compat: migrate flat list to dict under "_legacy" key
        existing_ac = {"_legacy": existing_ac} if existing_ac else {}
    if no_merge:
        existing_ac[protocol] = llm_output.get("api_constraints", [])
    else:
        proto_ac = list(existing_ac.get(protocol, []))
        existing_texts = {
            (c.get("constraint", "") if isinstance(c, dict) else c)
            for c in proto_ac
        }
        for c in llm_output.get("api_constraints", []):
            text = c.get("constraint", "") if isinstance(c, dict) else c
            if text not in existing_texts:
                proto_ac.append(c)
                existing_texts.add(text)
        existing_ac[protocol] = proto_ac
    profile["api_constraints"] = existing_ac

    # known_behaviors: store per-protocol
    existing_kb = profile.get("known_behaviors", {})
    if isinstance(existing_kb, list):
        existing_kb = {"_legacy": existing_kb} if existing_kb else {}
    if no_merge:
        existing_kb[protocol] = llm_output.get("known_behaviors", [])
    else:
        proto_kb = list(existing_kb.get(protocol, []))
        existing_ids = {kb["id"] for kb in proto_kb if isinstance(kb, dict)}
        for kb in llm_output.get("known_behaviors", []):
            if kb.get("id") and kb["id"] not in existing_ids:
                proto_kb.append(kb)
                existing_ids.add(kb["id"])
        existing_kb[protocol] = proto_kb
    profile["known_behaviors"] = existing_kb

    # verification_fields: merge LLM-extracted fields (e.g. identity_prefix_pattern)
    extracted_vf = llm_output.get("verification_fields")
    if extracted_vf and isinstance(extracted_vf, dict):
        existing_vf = profile.get("verification_fields", {})
        existing_vf.update(extracted_vf)
        profile["verification_fields"] = existing_vf

    Path(profile_path).parent.mkdir(parents=True, exist_ok=True)
    with open(profile_path, "w") as f:
        json.dump(profile, f, indent=2)
    print(f"Saved: {profile_path}")

    return {
        "profile_path": profile_path,
        "ops_extracted": total_ops,
    }


# ---------------------------------------------------------------------------
# Main extraction pipeline
# ---------------------------------------------------------------------------

def extract_platform_specs(
    platform: str,
    protocol: str = "oidc_jwt",
    docs_dir: str = "src/extraction/cleaned_docs",
    model: str = "gpt-5.2",
    dry_run: bool = False,
    max_doc_chars: int = 500_000,
    regenerate_profile: bool = False,
    no_merge: bool = False,
    tag: str = None,
) -> dict:
    """Run full extraction pipeline for a platform/protocol.

    Reads ALL_DOCS.md produced by fetch_docs.py.

    Args:
        platform: e.g. "vault", "keycloak"
        protocol: e.g. "oidc_jwt", "ldap"
        docs_dir: Root dir with cleaned docs (expects {docs_dir}/{platform}/{protocol}/ALL_DOCS.md)
        model: LLM model name
        dry_run: If True, print the prompt but don't call LLM
        max_doc_chars: Truncate docs to this many chars to stay within LLM context
        regenerate_profile: If True, delete existing profile and start fresh

    Returns:
        Dict with paths to saved files (or empty dict on dry_run)
    """
    all_docs_path = Path(docs_dir) / platform / protocol / "ALL_DOCS.md"
    if not all_docs_path.exists():
        raise FileNotFoundError(
            f"{all_docs_path} not found. Run fetch_docs.py first:\n"
            f"  python -m src.extraction.fetch_docs --platform {platform} --protocol {protocol}"
        )

    docs_text = all_docs_path.read_text(encoding="utf-8")

    if len(docs_text) > max_doc_chars:
        logger.warning(f"Docs are {len(docs_text)} chars, truncating to {max_doc_chars}")
        docs_text = docs_text[:max_doc_chars]

    approx_tokens = len(docs_text) // 4
    print(f"Input: {all_docs_path} ({approx_tokens:,} approx tokens)")

    if dry_run:
        prompt = build_user_prompt(platform, protocol, docs_text)
        print(f"\n{'='*60}\nSYSTEM PROMPT ({len(SYSTEM_PROMPT)} chars):\n{'='*60}")
        print(SYSTEM_PROMPT[:500] + "...")
        print(f"\n{'='*60}\nUSER PROMPT ({len(prompt)} chars):\n{'='*60}")
        print(prompt[:2000] + "...")
        return {"dry_run": True, "prompt_chars": len(prompt)}

    # Optionally delete existing profile to regenerate from scratch
    if regenerate_profile:
        profile_path = f"src/profiles/{platform}.json"
        if os.path.exists(profile_path):
            import shutil
            backup = f"{profile_path}.bak"
            shutil.copy2(profile_path, backup)
            os.remove(profile_path)
            print(f"  Backed up and removed existing profile: {profile_path}")

    user_prompt = build_user_prompt(platform, protocol, docs_text)

    # Call LLM multiple times for stable enumeration of constraints/behaviors
    from src.llm.client import LLMClient
    llm = LLMClient(model=model)

    n_runs = 3
    outputs = []
    for i in range(n_runs):
        print(f"  LLM run {i + 1}/{n_runs}...")
        result = llm.generate_json(SYSTEM_PROMPT, user_prompt)
        if result:
            outputs.append(result)
            ops_n = len(result.get("input_operations", []))
            ac_n = len(result.get("api_constraints", []))
            kb_n = len(result.get("known_behaviors", []))
            print(f"    ops={ops_n}  constraints={ac_n}  behaviors={kb_n}")

    if not outputs:
        raise ValueError("All LLM runs returned empty responses")

    # Merge: stable fields from run 1, union for enumerable fields
    llm_output = _merge_llm_outputs(outputs, platform)
    ac_merged = len(llm_output.get("api_constraints", []))
    kb_merged = len(llm_output.get("known_behaviors", []))
    print(f"  Merged: constraints={ac_merged}  behaviors={kb_merged}")

    # Save results
    return split_and_save(llm_output, platform, protocol, model_name=model, no_merge=no_merge, tag=tag)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Extract API specs from platform documentation using LLM"
    )
    parser.add_argument("--platform", required=True,
                        choices=["vault", "keycloak", "dex", "casdoor", "authentik", "zitadel", "logto"],
                        help="Target platform")
    parser.add_argument("--protocol", default="oidc_jwt",
                        help="Protocol variant (default: oidc_jwt)")
    parser.add_argument("--docs-dir", default="src/extraction/cleaned_docs",
                        help="Directory containing cleaned docs")
    parser.add_argument("--model", default=None,
                        help="LLM model (default: from env or gpt-5.2)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print prompt without calling LLM")
    parser.add_argument("--max-chars", type=int, default=500_000,
                        help="Max doc chars to send to LLM (default: 500000)")
    parser.add_argument("--regenerate-profile", action="store_true",
                        help="Delete existing profile and regenerate from scratch "
                             "(default: merge into existing)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    model = args.model or os.getenv("VALENCE_LLM_MODEL", "gpt-5.2")

    extract_platform_specs(
        platform=args.platform,
        protocol=args.protocol,
        docs_dir=args.docs_dir,
        model=model,
        dry_run=args.dry_run,
        max_doc_chars=args.max_chars,
        regenerate_profile=args.regenerate_profile,
    )


if __name__ == "__main__":
    main()
