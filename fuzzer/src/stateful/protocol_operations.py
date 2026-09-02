"""Protocol-level operation definitions for LLM sequence generation."""

# These are ABSTRACT operations — platform-independent.
# The LLM generates sequences using these names.
# The executor maps them to platform-specific APIs via PlatformProfile.
#
# NOTE: This is the MINIMUM set of operations every platform should support.
# Individual platform profiles (src/profiles/{platform}.json) may define additional
# platform-specific operations beyond this set.
# The sequence generator accepts both these operations AND any operations in the
# active platform's api_mapping.

PROTOCOL_OPERATIONS = {
    # === SETUP operations (admin, before testing) ===
    "create_tenant":            "Create a tenant/realm/organization if the platform requires one before any other setup (e.g., Keycloak realm, Casdoor organization). Skip if the platform uses a default tenant.",
    "enable_auth_method":       "Enable an auth method (JWT, OIDC, SAML, LDAP) on the platform",
    "configure_jwt_validation": "Configure how the platform validates JWTs (JWKS URL, static keys, OIDC discovery). Also used to create a JWT Identity Provider (JWT IdP) that accepts external JWTs for federated login. Include auto-linking options (auto_linking, is_linking_allowed, is_auto_creation) when the platform supports automatic account linking by email/username.",
    "create_auth_role":         "Create an authentication role with claim constraints and permission grants",
    "create_policy":            "Create an authorization policy that grants specific permissions",
    "create_identity_group":    "Create an identity group that can aggregate policies",
    "create_group_alias":       "Map an external group name (from JWT groups claim) to an internal group",
    "get_mount_accessor":       "Get the mount accessor ID needed for alias creation",
    "seed_protected_resource":  "Write test data to a protected path for access testing",

    # === AUTH operations (the actual login being tested) ===
    "start_oidc_auth":          "Initiate OIDC authorization code flow at the authorization endpoint (GET /authorize with client_id, redirect_uri, scope, response_type, and optional 'request' JWT request object per RFC 9101)",
    "login_with_jwt":           "Authenticate using a signed JWT token",
    "login_with_password":      "Authenticate using username + password (ROPC grant or direct login)",
    "saml_login":               "Authenticate via SAML — executor auto-generates forged SAMLResponse signed with attacker cert. Params: target_identity, email, provider, realm. Special params: remove_conditions=true (omit Conditions element), include_onetimeuse=true (add OneTimeUse condition), fixed_assertion_id=string (reuse same Assertion/@ID across calls — OneTimeUse replay test), idp_entity_id=string (set Issuer in assertion), expired_assertion=true (set NotOnOrAfter to 60 minutes in the past — tests time-bound enforcement per SAML Core 2.5.1.2; if login succeeds, SP does not check assertion expiry)",
    "exchange_code_for_token":  "Exchange auth code or subject_token for access token (supports token exchange grant_type)",
    "token_exchange":           "Exchange a subject_token for a new token via RFC 8693 token exchange (grant_type=urn:ietf:params:oauth:grant-type:token-exchange). Params: subject_token, subject_token_type, client_id, client_secret, audience",

    # === VERIFY operations (post-auth evidence collection) ===
    "verify_granted_identity":     "Check WHO the platform thinks is logged in (identity, display name, metadata)",
    "verify_entity_details":       "Look up the full identity entity record (aliases, groups, policies)",
    "verify_read_secret":          "Try to read a protected resource (positive/negative access test)",
    "read_role_config":            "Read back the role configuration to confirm settings",

    # === USER/APP/ORG management (test setup) ===
    "create_user":              "Create a test user account on the platform",
    "delete_user":              "Delete a test user account",
    "update_user":              "Update user attributes (e.g., enable MFA, change email, set roles, assign groups)",
    "create_application":       "Create/register an application or client (with audience, redirect URIs, etc.)",
    "update_application":       "Update application settings (e.g., audience restrictions, grant types, MFA requirements)",
    "delete_application":       "Delete an application or client",
    "create_organization":      "Create an organization or tenant for multi-tenancy testing",
    "create_provider":          "Create/register an identity provider (SAML IdP, OIDC provider, etc.)",
    "mfa_setup_enable":         "Enable or configure MFA (TOTP, WebAuthn) on a user account or application",
    "verify_entity_details_by_name": "Look up a user/entity by name or email",

    # === MODIFY operations (mid-test state changes) ===
    "modify_role_config":       "Change role settings mid-test (e.g., tighten policies)",
    "revoke_session":           "Revoke a token/session",
    "introspect_token":         "Introspect a token to check its claims, audience, and validity",

    # === CLEANUP ===
    "cleanup_auth_method":      "Remove the auth method after testing",
}

# Attack patterns per invariant (shared across all platforms)
CROSS_PLATFORM_ATTACK_PATTERNS = {
    "I1": [
        "alg_none: JWT with alg=none should be rejected",
        "resign_attacker_key: JWT signed with untrusted key should be rejected",
        "trust_anchor_substitution: Forged issuer with attacker JWKS should be rejected",
        "kid_injection: Attacker-controlled kid pointing to malicious key",
        "saml_cert_substitution: Forge SAMLResponse signed with attacker-generated cert — if platform does not validate signatures or extracts trust anchor from the response itself, attacker cert is accepted. The default saml_login already signs with attacker cert. To test insecure defaults: create SAML IdP with DEFAULT config (do NOT set validateSignature=true or wantAssertionsSigned=true in provider_config), then saml_login — if login succeeds, signature validation defaults are insecure",
        "saml_unsigned_assertion: Response envelope signed but assertion not individually signed — some SPs accept this",
        "saml_issuer_mismatch: SAML assertion with Issuer set to untrusted/unknown IdP entity ID — tests whether SP validates Issuer against configured trust. Use saml_login with idp_entity_id='https://wrong-issuer.example/idp'. For default-config test: create SAML IdP without setting idpEntityId in provider_config, then login — if accepted, issuer validation is skipped when idpEntityId is unset",
        "saml_spurious_signature: Response has a Signature element covering only the envelope, assertion itself unsigned — tests whether SP checks assertion-level integrity vs just detecting any Signature element. Configure a SAML IdP, then send a SAMLResponse where the Response envelope is signed but the Assertion is NOT individually signed",
        "saml_post_binding_unsigned_assertion: Configure SAML IdP with POST binding, send SAMLResponse where only the outer Response is signed with attacker cert but inner Assertion has no Signature — tests whether SP verifies assertion-level signatures independently of response-level signatures",
        "oidc_request_object_alg_none: [OIDC flow only] Send an unsigned JWT (alg=none) as the 'request' parameter to the authorization endpoint — tests whether the platform validates request object signatures. If the client's requestObjectSignatureAlg is not explicitly configured, some platforms accept alg=none request objects, allowing attackers to inject arbitrary authorization parameters (redirect_uri, scope, claims)",
        "http_header_injection: Inject identity via HTTP proxy headers (X-Remote-User, X-Forwarded-User, X-Remote-Group) — tests whether platform trusts proxy headers from untrusted clients",
    ],
    "I2": [
        "replay_same_token: Same JWT used twice — note: jti tracking is OPTIONAL per RFC 7519 Section 4.1.7; JWT bearer replay is BY_DESIGN for stateless verifiers. Only flag as violation for client_assertion (RFC 7523) or SAML contexts",
        "expired_token: JWT with exp in the past should be rejected",
        "future_token: JWT with nbf far in the future should be rejected",
        "stateless_jwt_no_jti: [HARDENING CHECK, not a vulnerability] JWT without jti claim submitted twice — jti is OPTIONAL per RFC 7519 Section 4.1.7. No major JWT auth system (AWS IAM, Google IAM, K8s OIDC) tracks jti. Stateless JWT verifiers are not expected to implement jti tracking",
        "saml_one_time_use_replay: SAML assertion with <OneTimeUse/> condition submitted twice — second must be rejected per SAML Core 2.5.1.5. Use TWO saml_login events with include_onetimeuse=true AND fixed_assertion_id='_replay_onetimeuse' (SAME value in both). First login should succeed; if second also succeeds, OneTimeUse is not enforced",
        "saml_assertion_id_replay: Same SAML assertion ID submitted twice — assertion ID tracking required by SAML spec. Use TWO saml_login events with fixed_assertion_id='_replay_test' (SAME value in both). If second login succeeds, assertion ID replay is not detected",
        "saml_expired_assertion: SAML assertion with NotOnOrAfter set 60 minutes in the past — tests time-bound enforcement per SAML Core 2.5.1.2. Use saml_login with expired_assertion=true. Include a CONTROL login WITHOUT expired_assertion=true first to confirm the flow works. If the expired login succeeds, the SP does not check NotOnOrAfter",
        "oidc_sso_nonce_bypass: [OIDC SSO] The mock IdP ALWAYS omits nonce from id_tokens by default. "
        "Use a saml_login event with connector_id={{oidc_sso_connector_id}} AND "
        "mutation_type='i2_oidc_sso_nonce_bypass' in params. "
        "Oracle: assert user_X_http_status >= 400 (RP must reject nonce-less id_token per OIDC Core 3.1.3.7 §11). "
        "If user_X_http_status == 200, nonce validation is bypassed — I2 VIOLATION. "
        "Example oracle_check: {\"check_id\": \"i2_nonce_absent_rejected\", \"invariant\": \"I2\", "
        "\"assertion\": \"user_X_http_status >= 400\", "
        "\"violation_description\": \"OIDC SSO accepted id_token without nonce (OIDC Core 3.1.3.7)\"}",
        "oidc_sso_audience_cross_tenant: [OIDC SSO] Configure two OIDC SSO connectors (IdP-A and IdP-B) with different client_ids. Obtain an id_token from IdP-A and present it to IdP-B's callback. If accepted, the RP does not validate the aud claim per OIDC Core 3.1.3.7 — I1/I5 violation",
    ],
    "I3": [
        # JWT bearer mode attacks — use login_with_jwt + configure_jwt_validation/create_auth_role/modify_role_config
        "jwt_role_config_tighten_reauth: Configure a role permissively, login successfully as baseline. Then tighten the role config (e.g. add a bound_claims restriction or tighten allowed_audiences). Re-login with the same JWT — must be rejected. Tests that role config changes take effect immediately with no stale cache.",
        "jwt_signing_key_rotation: Configure the auth method with trusted key-A. Login successfully (baseline). Rotate trust to key-B (update jwt_validation_pubkeys or jwks_url). Attempt login again with a JWT signed by key-A — must be rejected. Tests that trust anchor rotation propagates immediately.",
        "jwt_default_role_change: Configure the JWT auth mount with default_role=role-A. Login without specifying a role (uses default). Change default_role to role-B. Login again without explicit role — must now authenticate against role-B policies. Tests that default binding is coherent after config change.",
        "jwt_bound_issuer_enforce: Reconfigure the JWT auth method with a different bound_issuer. Tokens carrying the previous issuer value must be rejected after the reconfiguration. Tests issuer-validation coherence across config updates.",
        # OIDC redirect-flow attacks — only applicable when the profile includes start_oidc_auth / exchange_code_for_token operations
        "redirect_uri_mismatch: [OIDC flow only] Different redirect_uri at token endpoint vs authorize",
        "state_swap: [OIDC flow only] Exchange state parameter between sessions",
        "pkce_skip: [OIDC flow only, HARDENING CHECK, not a vulnerability] Skip code_verifier when code_challenge was sent — PKCE (RFC 7636) is OPTIONAL per RFC 6749. Not enforcing it is standard behavior. Assert that the code exchange returns an error status (non-200). Do NOT compare identities/emails; test the flow rejection via status codes",
        "pkce_not_required_public_client: [OIDC flow only, HARDENING CHECK, not a vulnerability] Register a public client (no client_secret), obtain auth code WITH code_challenge, then exchange WITHOUT code_verifier — PKCE (RFC 7636) is OPTIONAL per RFC 6749. Not enforcing it is standard behavior. Assert that code exchange WITHOUT code_verifier returns an error status (non-200 HTTP status). Do NOT compare identities or emails across users — test the flow rejection directly via status codes (e.g., assert exchange_without_verifier_http_status != 200)",
        "auth_code_no_client_auth: [OIDC flow only] Exchange auth code without client_secret AND without code_verifier — no binding of code to client at all",
        "code_injection: [OIDC flow only] Auth code from session A used in session B",
        # SAML attacks
        "saml_mfa_bypass_via_binding_rule: [SAML only] Enable MFA on victim user, verify password login requires MFA step (e.g., status returns MFA challenge), then attempt saml_login with same email — if login succeeds without MFA challenge, the alternate binding path skips MFA enforcement",
    ],
    "I4": [
        "cross_user_collision: Two different sub values map to same identity",
        "case_confusion: 'Admin' vs 'admin' — same or different identity?",
        "unicode_normalization: Different byte sequences for same visual string",
        "nfd_nfc_normalization: Same logical subject in NFC vs NFD Unicode forms — tests RFC 7613 string prep (e.g., 'caf\\u00e9' NFC vs 'cafe\\u0301' NFD)",
        "empty_sub: sub='' — what identity does it get?",
        "type_confusion_groups: groups='string' vs groups=['string'] — same mapping?",
        "cross_mount_collision: Same sub from different auth mounts — same identity?",
        "saml_email_binding_collision: SAML login with NameID=attacker but email=victim@example.com — if platform binds by email, attacker gets victim's account (use saml_login with target_identity=attacker_id and email=victim_email)",
        "unverified_email_account_linking: SSO login with email=victim@example.com but email_verified=false — platform must NOT auto-link to victim's account based on unverified email. Pattern: (1) create_user victim with email X, (2) set_idp_claims with sub=attacker, email=X, email_verified=false, (3) saml_login or OIDC SSO, (4) verify_granted_identity — assert attacker entity_id != victim entity_id. If they match, unverified email caused account takeover.",
        "cross_protocol_identity_merge: User created via password, then SAML login with same email but different NameID — should they merge or stay separate?",
    ],
    "I5": [
        "empty_audience: bound_audiences=[] or missing — does it accept any?",
        "audience_mismatch: JWT aud doesn't match role's bound_audiences",
        "empty_bound_claims: bound_claims={} — skip validation or deny all?",
        "glob_wildcard: bound_claims={'sub':'*'} with glob type — matches everything?",
        "bound_claim_numeric_type_coercion: Set numeric bound_claim as float (e.g., department_id=100.7 against bound 100) — tests RFC 7519 claim type handling",
        "group_policy_escalation: Groups claim maps to group with extra policies beyond role",
        "identity_policy_override: Entity has policies not granted by role",
        "cross_org_token_exchange: Login with type=code to get access token from org-A, then exchange_code_for_token at org-B app with grant_type=urn:ietf:params:oauth:grant-type:token-exchange and target_application=app-org-b — if shared signing cert (cert-built-in), exchange succeeds across org boundary",
        "shared_cert_token_exchange: Two applications share the same signing certificate — token from app-A is accepted by app-B token exchange endpoint",
        "token_exchange_wrong_audience: Exchange a token whose audience is service-A at service-B's token exchange endpoint — audience binding must be enforced (use token_exchange with subject_token from service-A login, audience=service-B client_id)",
        "token_exchange_ignore_audience: Obtain access token for client-A, then call token_exchange with that token as subject_token at client-B — some platforms skip audience validation on subject_token during token exchange (RFC 8693 Section 2.1 requires audience validation)",
        "token_exchange_scope_escalation: Login with limited scope (e.g., openid email), then call token_exchange with the access_token as subject_token but request EXPANDED scope (e.g., openid email groups profile federated:id). If the exchanged token includes claims (groups, name, federated_claims) not in the original scope, the platform fails to restrict token exchange scopes to the original authorization. Assert that the exchanged token does NOT contain claims beyond the original scope, or that the exchange is rejected",
        "saml_no_audience_restriction: SAML assertion without <AudienceRestriction> — tests whether SP enforces audience scoping per SAML Core 2.5.1.2",
        "saml_no_conditions: SAML assertion without <Conditions> element entirely — no audience or time bounds. Use saml_login with remove_conditions=true. If login succeeds, broker accepts assertions with no temporal/audience constraints",
        "saml_wrong_audience: SAML assertion with <Audience> set to different SP entity ID — tests audience validation",
        "cross_provider_jwt_audience: Create TWO OAuth2 providers (A and B) that share the same federated JWKS source (enable_auth_method with oidc_jwks_url pointing to mock-idp). Create applications for both. Mint a JWT with aud=provider-A-client-id, then use login_with_jwt with client_id=provider-B-client-id and the SAME JWT. If provider B accepts it, audience validation is missing (verify_aud:False). The oracle should assert the cross-provider login fails (status >= 400)",
    ],
}
