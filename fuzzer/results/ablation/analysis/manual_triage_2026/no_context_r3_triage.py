"""Manual triage for llm_judge_r3 (no_context) / r3. Agent-generated 2026-04-16.

Classification rules:
  VIOLATION: match against 33 ground-truth flaws.
    - Speculative hedging (suggests/may/appears/cannot confirm/etc) -> FP:speculative
    - Setup failure (no session token, 409 already exists, invalid_client, etc.) -> FP:setup-failure
    - Clear flaw match -> TP:<flaw_id>
    - Otherwise -> FP:not-in-33
  UNEXPECTED: default FP:unexpected-not-violation.
    Rescue ONLY if HIGH conf + non-speculative + clear flaw match.

Ground truth (33 flaws):
  ZT-1..3 zitadel; CD-1..9 casdoor; DX-1..5 dex; KC-1,3..6 keycloak;
  AK-1,3,5,6,7 authentik; LG-1..3,5,6 logto; VT-5/6 vault.
"""
from collections import defaultdict

RUN = "no_context_r3"
FINDINGS_ROOT = "/home/ubuntu/broker/fuzzer/results/ablation/llm_judge_r3"

# Total findings: 266 (42 VIOLATION + 224 UNEXPECTED)
# Per-file counts:
#   authentik/oidc_jwt: 23 (3V+20U)   authentik/saml: 17 (0V+17U)
#   casdoor/oidc: 34 (2V+32U)         casdoor/saml: 45 (2V+43U)
#   dex/oidc_jwt: 9 (1V+8U)           dex/saml: 10 (0V+10U)
#   keycloak/oidc: 5 (2V+3U)          keycloak/saml: 19 (0V+19U)
#   logto/oidc_jwt: 20 (3V+17U)       logto/saml: 27 (12V+15U)
#   vault/oidc_jwt: 17 (10V+7U)
#   zitadel/oidc_jwt: 19 (4V+15U)     zitadel/saml: 21 (3V+18U)

TRIAGE = {
    # ============================================================
    # authentik/oidc_jwt (23 findings: 3 VIOLATION + 20 UNEXPECTED)
    # ============================================================
    ("authentik", "oidc_jwt", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Request-object test 404 - endpoint routing issue (speculative)"},
    ("authentik", "oidc_jwt", 2): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "No session token established - cannot verify control"},
    ("authentik", "oidc_jwt", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "JWT login 200 for both control and attack but no session token issued"},
    ("authentik", "oidc_jwt", 4): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Trust-anchor change not applied (slug collision 400)"},
    ("authentik", "oidc_jwt", 5): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "TP", "reason": "AK-6",
        "desc_snippet": "Expired external JWT accepted with session token issued"},
    ("authentik", "oidc_jwt", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Control login succeeded but identity verification 403"},
    ("authentik", "oidc_jwt", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Attack success but inconsistent session token presence"},
    ("authentik", "oidc_jwt", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Future nbf JWT accepted (speculative - test harness issue)"},
    ("authentik", "oidc_jwt", 9): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "No session tokens captured for control/attack"},
    ("authentik", "oidc_jwt", 10): {"verdict": "VIOLATION", "conf": "MEDIUM", "invariant": "I2", "label": "TP", "reason": "AK-6",
        "desc_snippet": "JWT with exp==now accepted (boundary freshness violation)"},
    ("authentik", "oidc_jwt", 11): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "No session tokens captured for control/attack"},
    ("authentik", "oidc_jwt", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "JWKS rotation not applied (slug conflict 400)"},
    ("authentik", "oidc_jwt", 13): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "JWT 200 but no session token"},
    ("authentik", "oidc_jwt", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Issuer change not applied (update failed 400)"},
    ("authentik", "oidc_jwt", 15): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "No session token - auth result ambiguous"},
    ("authentik", "oidc_jwt", 16): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Homoglyph sub collision (authentik I4 not in 33)"},
    ("authentik", "oidc_jwt", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Cross-provider JWT aud confusion (speculative, no session token)"},
    ("authentik", "oidc_jwt", 18): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "No session token captured for cross-provider test"},
    ("authentik", "oidc_jwt", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection 200 despite failed login"},
    ("authentik", "oidc_jwt", 20): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Pre-revocation identity verification 403"},
    ("authentik", "oidc_jwt", 21): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Missing-aud JWT ambiguous without session tokens"},
    ("authentik", "oidc_jwt", 22): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "OIDC source issuer mismatch flag (speculative)"},
    ("authentik", "oidc_jwt", 23): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token exchange empty subject_token, introspection 200"},

    # ============================================================
    # authentik/saml (17 findings: 0 VIOLATION + 17 UNEXPECTED)
    # ============================================================
    ("authentik", "saml", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired SAML login 200 but no granted identity (speculative)"},
    ("authentik", "saml", 2): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "No session tokens - replay check inconclusive"},
    ("authentik", "saml", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML login 200 but no session token issued"},
    ("authentik", "saml", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Session revocation invalid_client - replay-after-revoke not tested"},
    ("authentik", "saml", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "OneTimeUse test inconclusive - no session tokens"},
    ("authentik", "saml", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML login 200 but no session token"},
    ("authentik", "saml", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML login 200 but no session token - replay not confirmed"},
    ("authentik", "saml", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Session revocation invalid_client 401"},
    ("authentik", "saml", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML source cleanup failed 405 - not exercised"},
    ("authentik", "saml", 10): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no session token"},
    ("authentik", "saml", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "MFA enable failed - MFA bypass test not exercised"},
    ("authentik", "saml", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Issuer change may not have applied (speculative)"},
    ("authentik", "saml", 13): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Identity verification failed - missing session tokens"},
    ("authentik", "saml", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML source cleanup 405 - stale-acceptance not validated"},
    ("authentik", "saml", 15): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML completion 200 but no session token"},
    ("authentik", "saml", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection contains entity_id despite inactive token"},
    ("authentik", "saml", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection leakage - inactive token contains entity_id"},

    # ============================================================
    # casdoor/oidc (34 findings: 2 VIOLATION + 32 UNEXPECTED)
    # ============================================================
    ("casdoor", "oidc", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML login 200 but access token not in DB"},
    ("casdoor", "oidc", 2): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Same login path for control/expired assertions"},
    ("casdoor", "oidc", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML login 200 but token not recognized"},
    ("casdoor", "oidc", 4): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Control and attack same entity_id (harness mix-up)"},
    ("casdoor", "oidc", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection invalid_request 400 (test harness issue)"},
    ("casdoor", "oidc", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML login 200 but no access token"},
    ("casdoor", "oidc", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Both control and expired SAML 200 but no access token"},
    ("casdoor", "oidc", 8): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Session token collision between expired and global"},
    ("casdoor", "oidc", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Revoke_session success despite failed login"},
    ("casdoor", "oidc", 10): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection invalid_request after 'token not exist'"},
    ("casdoor", "oidc", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired SAML accepted 200 (speculative; no token)"},
    ("casdoor", "oidc", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML login 200 but access token not persisted"},
    ("casdoor", "oidc", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML login 200 but no access token"},
    ("casdoor", "oidc", 14): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Replay inconclusive - verification fails"},
    ("casdoor", "oidc", 15): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Token exchange succeeded with wrong client_secret (not in 33)"},
    ("casdoor", "oidc", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML login 200 but no access token"},
    ("casdoor", "oidc", 17): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Both users resolve to 'admin' - harness mis-capture"},
    ("casdoor", "oidc", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no access token - state replay inconclusive"},
    ("casdoor", "oidc", 19): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "State-replay test inconclusive"},
    ("casdoor", "oidc", 20): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Case-variant username collision (casdoor/oidc I4 not in 33)"},
    ("casdoor", "oidc", 21): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection 400 invalid_request"},
    ("casdoor", "oidc", 22): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but token unknown - cross-protocol merge test broken"},
    ("casdoor", "oidc", 23): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML-attack entity_id mismatched (speculative)"},
    ("casdoor", "oidc", 24): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but session token not validated (speculative setup failure)"},
    ("casdoor", "oidc", 25): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Session token collision across contexts"},
    ("casdoor", "oidc", 26): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no access token usable"},
    ("casdoor", "oidc", 27): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection invalid_request; identity mismatch"},
    ("casdoor", "oidc", 28): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "App tag restriction bypass (casdoor tag restriction not in 33)"},
    ("casdoor", "oidc", 29): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Policy-change admin update failed - policy-gating not validated"},
    ("casdoor", "oidc", 30): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "App creation/configuration failed"},
    ("casdoor", "oidc", 31): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Access token not found in DB"},
    ("casdoor", "oidc", 32): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token exchange rejected due to malformed subject_token"},
    ("casdoor", "oidc", 33): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "User creation failed non-unique phone"},
    ("casdoor", "oidc", 34): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Non-standard status handling for missing tokens"},

    # ============================================================
    # casdoor/saml (45 findings: 2 VIOLATION + 43 UNEXPECTED)
    # ============================================================
    ("casdoor", "saml", 1): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Backend SQL error on SAML login (not one of the 33 flaws)"},
    ("casdoor", "saml", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Password login returns JWT but access token not in DB"},
    ("casdoor", "saml", 3): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Access token not in DB - session binding broken (setup failure)"},
    ("casdoor", "saml", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Mismatched Issuer forged SAML 200 (speculative)"},
    ("casdoor", "saml", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Session token collision attacker vs global"},
    ("casdoor", "saml", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no usable access token"},
    ("casdoor", "saml", 7): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Session token reuse across contexts"},
    ("casdoor", "saml", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no access token"},
    ("casdoor", "saml", 9): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Entity_id resolves to 'admin' with null identity fields"},
    ("casdoor", "saml", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no access token persisted"},
    ("casdoor", "saml", 11): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Attacker identity mapped to 'admin' - verification failed"},
    ("casdoor", "saml", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no access token - replay untestable"},
    ("casdoor", "saml", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no access token"},
    ("casdoor", "saml", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection 400 invalid_request (setup failure)"},
    ("casdoor", "saml", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no access token"},
    ("casdoor", "saml", 16): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Replay inconclusive - no assertion ID captured"},
    ("casdoor", "saml", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML login 200 but no access token"},
    ("casdoor", "saml", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection 400 invalid_request"},
    ("casdoor", "saml", 19): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no access token (setup failure, not violation)"},
    ("casdoor", "saml", 20): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired assertion 200 but enforcement cannot be confirmed (speculative)"},
    ("casdoor", "saml", 21): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection 400 invalid_request"},
    ("casdoor", "saml", 22): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no access token"},
    ("casdoor", "saml", 23): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "MFA enablement failed - MFA bypass test inconclusive"},
    ("casdoor", "saml", 24): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no access token"},
    ("casdoor", "saml", 25): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Both users resolve to 'admin' - mis-attribution"},
    ("casdoor", "saml", 26): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no session token"},
    ("casdoor", "saml", 27): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Inconsistent captured identity"},
    ("casdoor", "saml", 28): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no access token"},
    ("casdoor", "saml", 29): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Provider still returns success after config change (speculative)"},
    ("casdoor", "saml", 30): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no access token (setup failure)"},
    ("casdoor", "saml", 31): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML identity fields show 'admin' - mis-attribution"},
    ("casdoor", "saml", 32): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no access token"},
    ("casdoor", "saml", 33): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Anomalous entity_id 'admin' with null identity fields"},
    ("casdoor", "saml", 34): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no access token"},
    ("casdoor", "saml", 35): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token exchange across clients succeeded (speculative, intro failed)"},
    ("casdoor", "saml", 36): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Token exchange across audience/resource (not in 33 for saml campaign)"},
    ("casdoor", "saml", 37): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection 400 invalid_request"},
    ("casdoor", "saml", 38): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no access token"},
    ("casdoor", "saml", 39): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Identity fields show 'admin'"},
    ("casdoor", "saml", 40): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no access token"},
    ("casdoor", "saml", 41): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired assertion accepted but downstream broken (speculative)"},
    ("casdoor", "saml", 42): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token exchange succeeded with wrong audience (speculative)"},
    ("casdoor", "saml", 43): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection 400 invalid_request"},
    ("casdoor", "saml", 44): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no access token"},
    ("casdoor", "saml", 45): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Replay inconclusive - no access tokens"},

    # ============================================================
    # dex/oidc_jwt (9 findings: 1 VIOLATION + 8 UNEXPECTED)
    # ============================================================
    ("dex", "oidc_jwt", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token exchange 200 for attacker flow, control no token (speculative)"},
    ("dex", "oidc_jwt", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Password login unsupported_grant_type - test not run"},
    ("dex", "oidc_jwt", 3): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Revocation endpoint 404 - feature missing"},
    ("dex", "oidc_jwt", 4): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Future-nbf subject_token accepted in token exchange (not in 33)"},
    ("dex", "oidc_jwt", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Session granted despite failed code exchange (speculative)"},
    ("dex", "oidc_jwt", 6): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Password grant disabled - cross-protocol merge test unavailable"},
    ("dex", "oidc_jwt", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token exchange succeeded even without prior grant (speculative)"},
    ("dex", "oidc_jwt", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token exchange 200 despite failed auth-code exchange (speculative)"},
    ("dex", "oidc_jwt", 9): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Alice/Bob resolved to same entity_id (mock connector issue)"},

    # ============================================================
    # dex/saml (10 findings: 0 VIOLATION + 10 UNEXPECTED)
    # ============================================================
    ("dex", "saml", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Invalid bearer token for userinfo - test broken"},
    ("dex", "saml", 2): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Admin CREATECONNECTOR unsupported - config not applied"},
    ("dex", "saml", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Both logins 200 but userinfo 'Invalid bearer token'"},
    ("dex", "saml", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired SAML 200 but userinfo invalid - inconclusive"},
    ("dex", "saml", 5): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Control SAML also unusable session"},
    ("dex", "saml", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Revoke endpoint 404 - revocation not exercised"},
    ("dex", "saml", 7): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no usable session"},
    ("dex", "saml", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Invalid bearer token prevents NameID-collision test"},
    ("dex", "saml", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Invalid bearer token - over-grant test inconclusive"},
    ("dex", "saml", 10): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Admin connector enablement failed"},

    # ============================================================
    # keycloak/oidc (5 findings: 2 VIOLATION + 3 UNEXPECTED)
    # ============================================================
    ("keycloak", "oidc", 1): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "TP", "reason": "KC-1",
        "desc_snippet": "Authorization endpoint accepted unsigned OIDC request object (alg=none)"},
    ("keycloak", "oidc", 2): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "OIDC client never created - invalid_client for all tests (setup failure)"},
    ("keycloak", "oidc", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Admin update returned 'User not found' - realm mismatch"},
    ("keycloak", "oidc", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Empty/missing sub accepted in request object (speculative)"},
    ("keycloak", "oidc", 5): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "TP", "reason": "KC-1",
        "desc_snippet": "Unsigned request object (alg=none) enabled scope injection"},

    # ============================================================
    # keycloak/saml (19 findings: 0 VIOLATION + 19 UNEXPECTED)
    # ============================================================
    ("keycloak", "saml", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Attacker SAML 200 but success misclassification (speculative)"},
    ("keycloak", "saml", 2): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Post-login 401 - no session established"},
    ("keycloak", "saml", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Wrong-issuer SAML 200 but no granted identity (speculative)"},
    ("keycloak", "saml", 4): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Provider change 409 already exists - setup failure"},
    ("keycloak", "saml", 5): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Wrong-issuer SAML 200 under no pin, no session"},
    ("keycloak", "saml", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Both SAML 200 but no auth session - OneTimeUse untestable"},
    ("keycloak", "saml", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but verify_granted_identity 401"},
    ("keycloak", "saml", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired assertion returns success but downstream 401 (speculative)"},
    ("keycloak", "saml", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Both SAML 200 but sessions not usable"},
    ("keycloak", "saml", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but 401 for identity - session broken"},
    ("keycloak", "saml", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Admin session revoke 404 - replay-after-logout not tested"},
    ("keycloak", "saml", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "IdP update 409 Already exists - disable not applied"},
    ("keycloak", "saml", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "401 for both baseline and after-change sessions"},
    ("keycloak", "saml", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no session token (speculative)"},
    ("keycloak", "saml", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Casefold email collision (speculative, session broken)"},
    ("keycloak", "saml", 16): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Post-login 401 - collision inconclusive"},
    ("keycloak", "saml", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but 401 for identity - broken flow"},
    ("keycloak", "saml", 18): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Cross-provider merge inconclusive"},
    ("keycloak", "saml", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection returned claims for inactive token"},

    # ============================================================
    # logto/oidc_jwt (20 findings: 3 VIOLATION + 17 UNEXPECTED)
    # ============================================================
    ("logto", "oidc_jwt", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Forged SAML failed invalid_connector_id (speculative, setup)"},
    ("logto", "oidc_jwt", 2): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Sequence ran SAML instead of OIDC - no OIDC evidence"},
    ("logto", "oidc_jwt", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML replay failed invalid_connector_id - not exercised"},
    ("logto", "oidc_jwt", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Revocation invalid_client - token not revoked"},
    ("logto", "oidc_jwt", 5): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "TP", "reason": "LG-1",
        "desc_snippet": "OIDC SSO login succeeded without nonce (nonce bypass)"},
    ("logto", "oidc_jwt", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Revocation invalid_client - not tested"},
    ("logto", "oidc_jwt", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Revocation invalid_client - refresh-token test broken"},
    ("logto", "oidc_jwt", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Auth-code exchange invalid_grant (speculative identity mix)"},
    ("logto", "oidc_jwt", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "M2M token 200 then 401 for verification (speculative)"},
    ("logto", "oidc_jwt", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection reports session inactive (speculative)"},
    ("logto", "oidc_jwt", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token exchange failed invalid_grant (speculative leak)"},
    ("logto", "oidc_jwt", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SSO attribute merge (speculative)"},
    ("logto", "oidc_jwt", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Unicode NFC/NFD resolves to two distinct identities (OK)"},
    ("logto", "oidc_jwt", 14): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Display name collision - UI concern only"},
    ("logto", "oidc_jwt", 15): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-2",
        "desc_snippet": "Two SSO principals mapped to same user via shared email"},
    ("logto", "oidc_jwt", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SSO display_name mismatch (speculative attribute assoc)"},
    ("logto", "oidc_jwt", 17): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-6",
        "desc_snippet": "Cross-connector collision by email collapses identities"},
    ("logto", "oidc_jwt", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Email_verified flip kept identities separate (safe)"},
    ("logto", "oidc_jwt", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML login without Conditions (speculative signature compensation)"},
    ("logto", "oidc_jwt", 20): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token exchange invalid_grant but token value retained (speculative)"},

    # ============================================================
    # logto/saml (27 findings: 12 VIOLATION + 15 UNEXPECTED)
    # ============================================================
    ("logto", "saml", 1): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "OIDC/SAML SSO accepted token with untrusted kid (not in 33)"},
    ("logto", "saml", 2): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "alg=none JWT accepted (logto alg=none not in 33)"},
    ("logto", "saml", 3): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Attacker-signed IdP token accepted (logto trust-anchor not in 33)"},
    ("logto", "saml", 4): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Forged SAML with wrong Issuer accepted (not in 33)"},
    ("logto", "saml", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Forged-signature test failed invalid_connector_id"},
    ("logto", "saml", 6): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Wrong-issuer SAML accepted (logto SAML issuer binding not in 33)"},
    ("logto", "saml", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Invalid cert rejected but preconfigured connector used"},
    ("logto", "saml", 8): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "TP", "reason": "LG-1",
        "desc_snippet": "RP accepted token without nonce (nonce bypass)"},
    ("logto", "saml", 9): {"verdict": "VIOLATION", "conf": "MEDIUM", "invariant": "I2", "label": "TP", "reason": "LG-1",
        "desc_snippet": "Second no-nonce auth succeeded - replay without nonce"},
    ("logto", "saml", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Session revocation invalid_client - not exercised"},
    ("logto", "saml", 11): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "TP", "reason": "LG-1",
        "desc_snippet": "Login succeeds without nonce in id_token (nonce bypass)"},
    ("logto", "saml", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "New identity on claim change (speculative swap risk)"},
    ("logto", "saml", 13): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Bob's exchanged token introspects as Alice (token confusion, not in 33)"},
    ("logto", "saml", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Session revocation 401 invalid_client"},
    ("logto", "saml", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "JWT reported inactive - introspection broken"},
    ("logto", "saml", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Replay failed invalid_connector_id - not exercised"},
    ("logto", "saml", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Identity matches attacker (speculative mix-up)"},
    ("logto", "saml", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "OIDC auth endpoint 404 - replay test inconclusive"},
    ("logto", "saml", 19): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token exchange invalid_client"},
    ("logto", "saml", 20): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Alice vs Bob identity mis-bind (speculative)"},
    ("logto", "saml", 21): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Password login fails at Experience init 400"},
    ("logto", "saml", 22): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Identity state inconsistent"},
    ("logto", "saml", 23): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "New token inactive per introspection (logto introspection not in 33)"},
    ("logto", "saml", 24): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Revocation invalid_client"},
    ("logto", "saml", 25): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "After failed revoke /oidc/me still succeeds"},
    ("logto", "saml", 26): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3", "label": "TP", "reason": "LG-5",
        "desc_snippet": "SSO bypasses MFA with email linking - account takeover"},
    ("logto", "saml", 27): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-6",
        "desc_snippet": "SSO linked via case-insensitive email - account takeover"},

    # ============================================================
    # vault/oidc_jwt (17 findings: 10 VIOLATION + 7 UNEXPECTED)
    # ============================================================
    ("vault", "oidc_jwt", 1): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "alg=none JWTs accepted (vault alg=none removed from 33)"},
    ("vault", "oidc_jwt", 2): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Stale key accepted after rotation (vault stale trust removed)"},
    ("vault", "oidc_jwt", 3): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Trust-anchor substitution via admin JWKS swap (by-design config change)"},
    ("vault", "oidc_jwt", 4): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "JWKS-URL with pubkey override accepted forged JWT (not in 33)"},
    ("vault", "oidc_jwt", 5): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Session revocation 500 'no namespace' - not exercised"},
    ("vault", "oidc_jwt", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Just-expired JWT accepted under default leeway"},
    ("vault", "oidc_jwt", 7): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Session revocation 500 'no namespace'"},
    ("vault", "oidc_jwt", 8): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Token/session collision across identities (not in 33)"},
    ("vault", "oidc_jwt", 9): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Future-iat JWT accepted (vault iat handling not in 33)"},
    ("vault", "oidc_jwt", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "clock_skew_leeway change had no effect (setup)"},
    ("vault", "oidc_jwt", 11): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Stale key accepted after rotation (vault stale trust removed from 33)"},
    ("vault", "oidc_jwt", 12): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "VT-5/6",
        "desc_snippet": "Case-variant Admin/admin mapped to same entity"},
    ("vault", "oidc_jwt", 13): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "VT-5/6",
        "desc_snippet": "Two subs merged via identity_claim=email"},
    ("vault", "oidc_jwt", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Empty-sub JWT 500 server error (DoS concern, not identity collapse)"},
    ("vault", "oidc_jwt", 15): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "VT-5/6",
        "desc_snippet": "Two subs mapped to same entity via identity_claim=email"},
    ("vault", "oidc_jwt", 16): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "VT-5/6",
        "desc_snippet": "Turkish dotted/dotless I Unicode subjects collide to same entity"},
    ("vault", "oidc_jwt", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "bound_audiences=[] still allowed login (not in 33)"},

    # ============================================================
    # zitadel/oidc_jwt (19 findings: 4 VIOLATION + 15 UNEXPECTED)
    # ============================================================
    ("zitadel", "oidc_jwt", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Wrong-aud JWT IdP accepted (speculative)"},
    ("zitadel", "oidc_jwt", 2): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Verification failed - missing session token"},
    ("zitadel", "oidc_jwt", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Cleanup 404 after successful create"},
    ("zitadel", "oidc_jwt", 4): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "IdP intent token replayable (intent artifact, not in 33)"},
    ("zitadel", "oidc_jwt", 5): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Cleanup 404 - not an auth bypass"},
    ("zitadel", "oidc_jwt", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "JWT without exp accepted and reused (speculative)"},
    ("zitadel", "oidc_jwt", 7): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Post-login verification failed - missing session token"},
    ("zitadel", "oidc_jwt", 8): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "JWT IdP login after policy disable (policy-cache, not in 33)"},
    ("zitadel", "oidc_jwt", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent ID reuse (speculative fixation)"},
    ("zitadel", "oidc_jwt", 10): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "JWKS fetch error details disclosed"},
    ("zitadel", "oidc_jwt", 11): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Replayable intent after completion (zitadel intent, not in 33)"},
    ("zitadel", "oidc_jwt", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "authRequestID/intentID mismatch"},
    ("zitadel", "oidc_jwt", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Post-login session not established - inconclusive"},
    ("zitadel", "oidc_jwt", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "JWKS key lookup 'not found' - test misconfig"},
    ("zitadel", "oidc_jwt", 15): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Same intent_id reused across calls"},
    ("zitadel", "oidc_jwt", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent retrieval CRYPTO-CRYPTO error"},
    ("zitadel", "oidc_jwt", 17): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Same intent_id across authRequestIDs"},
    ("zitadel", "oidc_jwt", 18): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "External IdP login after policy disabled (zitadel policy bypass not in 33)"},
    ("zitadel", "oidc_jwt", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent identifier reused across calls"},

    # ============================================================
    # zitadel/saml (21 findings: 3 VIOLATION + 18 UNEXPECTED)
    # ============================================================
    ("zitadel", "saml", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 400 but granted identity (speculative session fixation)"},
    ("zitadel", "saml", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Identity granted despite SAML 400 (speculative)"},
    ("zitadel", "saml", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Identity established despite SAML 400 (speculative)"},
    ("zitadel", "saml", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Baseline login never succeeded - replay untestable"},
    ("zitadel", "saml", 5): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Identity verification succeeded despite login failure (mix-up)"},
    ("zitadel", "saml", 6): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Control JWT rejected - exp handling mismatch (setup)"},
    ("zitadel", "saml", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent ID reused across start_idp_intent"},
    ("zitadel", "saml", 8): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "TP", "reason": "ZT-3",
        "desc_snippet": "JWT IdP accepted assertion without exp claim (replay risk)"},
    ("zitadel", "saml", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent mix-up between authRequestIDs"},
    ("zitadel", "saml", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Two start_idp_intent return same intent_id"},
    ("zitadel", "saml", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent token retrieval fails 'invalid' for own token"},
    ("zitadel", "saml", 12): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Both start_idp_intent return same intent_id"},
    ("zitadel", "saml", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 400 but OIDC still granted identity (speculative)"},
    ("zitadel", "saml", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Session granted after SAML 400 (speculative)"},
    ("zitadel", "saml", 15): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "not-in-33",
        "desc_snippet": "OIDC tokens granted despite SAML 400 (flow coherence, not in 33)"},
    ("zitadel", "saml", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML validation 500 (DoS risk, speculative)"},
    ("zitadel", "saml", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 500 (DoS risk)"},
    ("zitadel", "saml", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Granted identity despite SAML 400 (speculative)"},
    ("zitadel", "saml", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token exchange returned broad scopes (speculative)"},
    ("zitadel", "saml", 20): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "TP", "reason": "ZT-1",
        "desc_snippet": "JWT IdP accepted JWT with wrong aud (audience binding failure)"},
    ("zitadel", "saml", 21): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent mix-up control vs attack"},
}


def main():
    # Summary statistics
    total = len(TRIAGE)
    by_verdict = defaultdict(int)
    by_label = defaultdict(int)
    fp_reasons = defaultdict(int)
    tp_flaws = set()
    tp_by_conf = defaultdict(int)
    violation_tp = 0
    violation_fp = 0
    unexpected_total = 0
    unexpected_rescued = 0

    for key, entry in TRIAGE.items():
        by_verdict[entry["verdict"]] += 1
        by_label[entry["label"]] += 1
        if entry["verdict"] == "VIOLATION":
            if entry["label"] == "TP":
                violation_tp += 1
                tp_flaws.add(entry["reason"])
                tp_by_conf[entry["conf"]] += 1
            else:
                violation_fp += 1
                fp_reasons[entry["reason"]] += 1
        else:  # UNEXPECTED
            unexpected_total += 1
            if entry["label"] == "TP":
                unexpected_rescued += 1
                tp_flaws.add(entry["reason"])
                tp_by_conf[entry["conf"]] += 1
            else:
                fp_reasons[entry["reason"]] += 1

    print(f"=== {RUN} triage summary ===")
    print(f"Total findings: {total}")
    print(f"  VIOLATION: {by_verdict['VIOLATION']} "
          f"(TP={violation_tp}, FP={violation_fp})")
    print(f"  UNEXPECTED: {by_verdict['UNEXPECTED']} "
          f"(rescued TP={unexpected_rescued}, FP={unexpected_total - unexpected_rescued})")
    print()
    print(f"Overall TP: {by_label['TP']}")
    print(f"Overall FP: {by_label['FP']}")
    print()
    print("FP reason breakdown:")
    for reason, count in sorted(fp_reasons.items(), key=lambda x: -x[1]):
        print(f"  {reason}: {count}")
    print()
    print(f"Distinct flaws found: {sorted(tp_flaws)} ({len(tp_flaws)}/33)")
    print()
    print(f"TP by confidence:")
    for conf in ["HIGH", "MEDIUM", "LOW"]:
        print(f"  {conf}: {tp_by_conf[conf]}")


if __name__ == "__main__":
    main()
