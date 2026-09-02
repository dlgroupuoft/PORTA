"""Manual triage for llm_judge_profile_r1 / r1. Agent-generated 2026-04-16.

Triages all 270 findings from the LLM-judge-with-profile ablation run R1
(platform profile passed as additional context to the LLM judge) against the
paper's 33 ground-truth flaws.

Rules:
  VIOLATION:
    - Speculative hedging in description -> FP:speculative
    - Setup failure (no session, 409, 401, 404, invalid_client, etc.) -> FP:setup-failure
    - Matches a ground-truth flaw by platform+invariant+keywords -> TP:<flaw_id>
    - Otherwise -> FP:not-in-33
  UNEXPECTED:
    - Default FP:unexpected-not-violation
    - Rescue only HIGH + non-speculative + clear flaw match
"""
RUN = "profile_r1"
FINDINGS_ROOT = "/home/ubuntu/broker/fuzzer/results/ablation/llm_judge_profile_r1"

# Key:   (platform, protocol, idx_1based)
# Value: dict with verdict, conf, invariant, label, reason, desc_snippet
TRIAGE = {
    # ================= authentik/oidc_jwt (18 findings, 0 VIOLATION) =================
    ("authentik", "oidc_jwt", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "speculative", "desc_snippet": "JWT M2M accepted wrong iss; 'indicating potential issuer confusion'"},
    ("authentik", "oidc_jwt", 2): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "no access/session token was captured"},
    ("authentik", "oidc_jwt", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "introspection 200 but no access token obtained (login failed)"},
    ("authentik", "oidc_jwt", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "speculative", "desc_snippet": "replay 'appears to be accepted', 'suggesting missing one-time-use'"},
    ("authentik", "oidc_jwt", 5): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "speculative", "desc_snippet": "unclear whether real OAuth token was issued"},
    ("authentik", "oidc_jwt", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "password grant failed, no token obtained"},
    ("authentik", "oidc_jwt", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "invalid_grant for control and test identities"},
    ("authentik", "oidc_jwt", 8): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "no access token ever issued"},
    ("authentik", "oidc_jwt", 9): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "no session/access token captured"},
    ("authentik", "oidc_jwt", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "config change re-save failed 400 slug already exists"},
    ("authentik", "oidc_jwt", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "provider A/B not created, client_id already exists"},
    ("authentik", "oidc_jwt", 12): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "no session token available for UserInfo"},
    ("authentik", "oidc_jwt", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "login failed, introspection 200 speculative"},
    ("authentik", "oidc_jwt", 14): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "providerA/B not created"},
    ("authentik", "oidc_jwt", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "no session/token for UserInfo"},
    ("authentik", "oidc_jwt", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "login failed, introspection 200 speculative"},
    ("authentik", "oidc_jwt", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "revoke 200 but no access/refresh token obtained (login failed)"},
    ("authentik", "oidc_jwt", 18): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "no access/session token captured"},

    # ================= authentik/saml (29 findings, 0 VIOLATION) =================
    ("authentik", "saml", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "no session token issued, unclear if forged accepted"},
    ("authentik", "saml", 2): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "SAML provider creation failed"},
    ("authentik", "saml", 3): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "no session token produced"},
    ("authentik", "saml", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "no session/access token issued"},
    ("authentik", "saml", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "no session/access token established"},
    ("authentik", "saml", 6): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "revoke failed invalid_client 401"},
    ("authentik", "saml", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "no authenticated session established"},
    ("authentik", "saml", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "speculative", "desc_snippet": "replay 'appears to be accepted' but cannot confirm"},
    ("authentik", "saml", 9): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "revocation invalid_client 401"},
    ("authentik", "saml", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "no authenticated session established"},
    ("authentik", "saml", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "revocation invalid_client"},
    ("authentik", "saml", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "no session/access token available"},
    ("authentik", "saml", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "speculative", "desc_snippet": "replay 'may be a false positive'"},
    ("authentik", "saml", 14): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "all verify_granted_identity steps failed, missing session token"},
    ("authentik", "saml", 15): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "no session/token to confirm MFA bypass"},
    ("authentik", "saml", 16): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "MFA not actually enabled"},
    ("authentik", "saml", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "cleanup step failed 405"},
    ("authentik", "saml", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "no session token for UserInfo"},
    ("authentik", "saml", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "cleanup call failed 405"},
    ("authentik", "saml", 20): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "no session token captured for UserInfo"},
    ("authentik", "saml", 21): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "speculative", "desc_snippet": "'could indicate' acceptance of unsolicited"},
    ("authentik", "saml", 22): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "revocation invalid_client 401, session not revoked"},
    ("authentik", "saml", 23): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "setup-failure", "desc_snippet": "no session/access token captured"},
    ("authentik", "saml", 24): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "speculative", "desc_snippet": "'possible false positive due to flow/state handling'"},
    ("authentik", "saml", 25): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "setup-failure", "desc_snippet": "no downstream session/access token established"},
    ("authentik", "saml", 26): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "setup-failure", "desc_snippet": "password grant invalid_grant for baseline users"},
    ("authentik", "saml", 27): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "SAML provider creation failed"},
    ("authentik", "saml", 28): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "no session token obtained"},
    ("authentik", "saml", 29): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "no post-login session/access token captured"},

    # ================= casdoor/oidc (31 findings, 2 VIOLATION) =================
    ("casdoor", "oidc", 1): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "speculative", "desc_snippet": "'may not be validating' signature/expiry"},
    ("casdoor", "oidc", 2): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "Access token doesn't exist in database"},
    ("casdoor", "oidc", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "token not persisted"},
    ("casdoor", "oidc", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting missing client auth enforcement'"},
    ("casdoor", "oidc", 5): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "tokens not recognized at /api/userinfo"},
    ("casdoor", "oidc", 6): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "token immediately rejected as non-existent"},
    ("casdoor", "oidc", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "introspection 400 invalid_request"},
    ("casdoor", "oidc", 8): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "Access token doesn't exist in database"},
    ("casdoor", "oidc", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "speculative", "desc_snippet": "expiry enforcement 'cannot be confirmed'"},
    ("casdoor", "oidc", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "token not in DB"},
    ("casdoor", "oidc", 11): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "no control userinfo succeeded"},
    ("casdoor", "oidc", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "token not recognized"},
    ("casdoor", "oidc", 13): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "both logins fail downstream token validation"},
    ("casdoor", "oidc", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "invalid_client client_id invalid"},
    ("casdoor", "oidc", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "Access token doesn't exist in database"},
    ("casdoor", "oidc", 16): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "token not recognized/trackable"},
    ("casdoor", "oidc", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "token not existing in database"},
    ("casdoor", "oidc", 18): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "PKCE code exchanges failed invalid_client"},
    ("casdoor", "oidc", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "token cannot be used at /api/userinfo"},
    ("casdoor", "oidc", 20): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "second application creation failed"},
    ("casdoor", "oidc", 21): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "Access token doesn't exist in database"},
    ("casdoor", "oidc", 22): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "second application creation failed"},
    ("casdoor", "oidc", 23): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "speculative", "desc_snippet": "'may be intentional policy'"},
    ("casdoor", "oidc", 24): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "setup-failure", "desc_snippet": "token not recognized by /api/userinfo"},
    ("casdoor", "oidc", 25): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "setup-failure", "desc_snippet": "both forged attempts used same email, intent not exercised"},
    ("casdoor", "oidc", 26): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "setup-failure", "desc_snippet": "token not recognized"},
    ("casdoor", "oidc", 27): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "TP", "reason": "CD-4", "desc_snippet": "Cross-organization token exchange succeeded: org-A subject_token minted org-B token"},
    ("casdoor", "oidc", 28): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "introspection fails invalid_request"},
    ("casdoor", "oidc", 29): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "not-in-33", "desc_snippet": "Application tag restriction not enforced (not in 33)"},
    ("casdoor", "oidc", 30): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting revocation surfaced as expiry'"},
    ("casdoor", "oidc", 31): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "introspection 400 invalid_request"},

    # ================= casdoor/saml (44 findings, 0 VIOLATION) =================
    ("casdoor", "saml", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "token not recognized by /api/userinfo"},
    ("casdoor", "saml", 2): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "introspection invalid_request 400"},
    ("casdoor", "saml", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "Access token doesn't exist in database"},
    ("casdoor", "saml", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "token not persisted/recognized"},
    ("casdoor", "saml", 5): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "introspection 400 invalid_request"},
    ("casdoor", "saml", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "token not recognized by /api/userinfo"},
    ("casdoor", "saml", 7): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "introspection invalid_request"},
    ("casdoor", "saml", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "token not recognized"},
    ("casdoor", "saml", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "token not recognized by /api/userinfo"},
    ("casdoor", "saml", 10): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "introspection invalid_request 400"},
    ("casdoor", "saml", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "Access token doesn't exist in database"},
    ("casdoor", "saml", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "Access token doesn't exist in database"},
    ("casdoor", "saml", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting session/token mix-up'"},
    ("casdoor", "saml", 14): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "introspection invalid_request"},
    ("casdoor", "saml", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "token not recognized"},
    ("casdoor", "saml", 16): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "token rejected immediately as non-existent"},
    ("casdoor", "saml", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "token not in DB"},
    ("casdoor", "saml", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "token not recognized"},
    ("casdoor", "saml", 19): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "application creation failed"},
    ("casdoor", "saml", 20): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "token not found during /api/userinfo"},
    ("casdoor", "saml", 21): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "token invalid/nonexistent"},
    ("casdoor", "saml", 22): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "token not in DB"},
    ("casdoor", "saml", 23): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "MFA enablement failed"},
    ("casdoor", "saml", 24): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "token not recognized"},
    ("casdoor", "saml", 25): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "token exchange failed invalid_client"},
    ("casdoor", "saml", 26): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "token not recognized"},
    ("casdoor", "saml", 27): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "tokens reported non-existent"},
    ("casdoor", "saml", 28): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "speculative", "desc_snippet": "'suspicious' state reuse, cannot confirm"},
    ("casdoor", "saml", 29): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "setup-failure", "desc_snippet": "token not recognized"},
    ("casdoor", "saml", 30): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting possible capture/parsing error'"},
    ("casdoor", "saml", 31): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "setup-failure", "desc_snippet": "token not persisted"},
    ("casdoor", "saml", 32): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting possible variable contamination'"},
    ("casdoor", "saml", 33): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "setup-failure", "desc_snippet": "token not recognized"},
    ("casdoor", "saml", 34): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting unintended attribute carryover'"},
    ("casdoor", "saml", 35): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "no usable access token, userinfo failed"},
    ("casdoor", "saml", 36): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "speculative", "desc_snippet": "cross-client exchange 'may indicate missing binding'"},
    ("casdoor", "saml", 37): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "introspection invalid_request"},
    ("casdoor", "saml", 38): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "Access token doesn't exist in database"},
    ("casdoor", "saml", 39): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "introspection invalid_request"},
    ("casdoor", "saml", 40): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "no usable OAuth access token; userinfo says token not in DB"},
    ("casdoor", "saml", 41): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "introspection invalid_request"},
    ("casdoor", "saml", 42): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "token not recognized"},
    ("casdoor", "saml", 43): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "speculative", "desc_snippet": "'may not be enforced' after policy change"},
    ("casdoor", "saml", 44): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "introspection invalid_request"},

    # ================= dex/oidc_jwt (9 findings, 0 VIOLATION) =================
    ("dex", "oidc_jwt", 1): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "control login failed, password grant unsupported"},
    ("dex", "oidc_jwt", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "invalid_grant on control"},
    ("dex", "oidc_jwt", 3): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I4", "label": "FP", "reason": "speculative", "desc_snippet": "'indicating possible principal confusion'"},
    ("dex", "oidc_jwt", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "setup-failure", "desc_snippet": "auth code invalid_grant"},
    ("dex", "oidc_jwt", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting identity mapping collision'"},
    ("dex", "oidc_jwt", 6): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "setup-failure", "desc_snippet": "password grant unsupported_grant_type"},
    ("dex", "oidc_jwt", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "control auth code flow failed"},
    ("dex", "oidc_jwt", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting subject_token_type confusion'"},
    ("dex", "oidc_jwt", 9): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "both control flows failed"},

    # ================= dex/saml (16 findings, 0 VIOLATION) =================
    ("dex", "saml", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "create_provider failed"},
    ("dex", "saml", 2): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "Invalid bearer token 403, no access_token obtained"},
    ("dex", "saml", 3): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "Invalid bearer token 403 after SAML login"},
    ("dex", "saml", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "speculative", "desc_snippet": "'cannot conclusively validate' replay protection"},
    ("dex", "saml", 5): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "Invalid bearer token 403 for both attempts"},
    ("dex", "saml", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "not-in-33", "desc_snippet": "HTTP 500 on wrong connector callback (DoS/robustness, not in 33)"},
    ("dex", "saml", 7): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "Invalid bearer token in /userinfo"},
    ("dex", "saml", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "Invalid bearer token 403"},
    ("dex", "saml", 9): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "client-B 404, no valid state"},
    ("dex", "saml", 10): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "CreateClient method unsupported"},
    ("dex", "saml", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "speculative", "desc_snippet": "unsolicited POST 'suspicious', cannot confirm"},
    ("dex", "saml", 12): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "Invalid bearer token"},
    ("dex", "saml", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "bearer token invalid; userinfo 403"},
    ("dex", "saml", 14): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "CreateConnector unsupported; inconclusive"},
    ("dex", "saml", 15): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "Invalid bearer token 403"},
    ("dex", "saml", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "Invalid bearer token after SAML login"},

    # ================= keycloak/oidc (3 findings, 0 VIOLATION) =================
    ("keycloak", "oidc", 1): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "client never successfully created"},
    ("keycloak", "oidc", 2): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "client/policy setup failed, client never created"},
    ("keycloak", "oidc", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "client never created, Admin API schema error"},

    # ================= keycloak/saml (35 findings, 0 VIOLATION) =================
    ("keycloak", "saml", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "no usable OIDC session, userinfo 401"},
    ("keycloak", "saml", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "no authenticated OIDC session (userinfo 401)"},
    ("keycloak", "saml", 3): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "create_provider 409 already exists"},
    ("keycloak", "saml", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "speculative", "desc_snippet": "'suggests the hardening step may not have been applied'"},
    ("keycloak", "saml", 5): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "409 IdP already exists"},
    ("keycloak", "saml", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "userinfo 401"},
    ("keycloak", "saml", 7): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "enable_auth_method 409 already exists"},
    ("keycloak", "saml", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "userinfo 401"},
    ("keycloak", "saml", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "speculative", "desc_snippet": "'cannot be confirmed and may be bypassed'"},
    ("keycloak", "saml", 10): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "Admin logout failed path-normalization"},
    ("keycloak", "saml", 11): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "userinfo 401, no session token"},
    ("keycloak", "saml", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "client_uuid captured as 201 status code"},
    ("keycloak", "saml", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "no OIDC session/token established"},
    ("keycloak", "saml", 14): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "enable_auth_method 409 already exists"},
    ("keycloak", "saml", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "userinfo 401"},
    ("keycloak", "saml", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "userinfo 401, no token"},
    ("keycloak", "saml", 17): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "control SAML login failed 400"},
    ("keycloak", "saml", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "userinfo 401"},
    ("keycloak", "saml", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "userinfo 401"},
    ("keycloak", "saml", 20): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "client update 404, client_uuid was 201"},
    ("keycloak", "saml", 21): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "userinfo 401"},
    ("keycloak", "saml", 22): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "SP-initiated OIDC auth 404"},
    ("keycloak", "saml", 23): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "userinfo verification failed 401"},
    ("keycloak", "saml", 24): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "setup-failure", "desc_snippet": "no session token established"},
    ("keycloak", "saml", 25): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "setup-failure", "desc_snippet": "user creation did not capture victim_user_id"},
    ("keycloak", "saml", 26): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I4", "label": "FP", "reason": "setup-failure", "desc_snippet": "userinfo verification 401, no session"},
    ("keycloak", "saml", 27): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "setup-failure", "desc_snippet": "no downstream session/token established"},
    ("keycloak", "saml", 28): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "setup-failure", "desc_snippet": "victim_user_id=None"},
    ("keycloak", "saml", 29): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "setup-failure", "desc_snippet": "no authenticated session"},
    ("keycloak", "saml", 30): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "setup-failure", "desc_snippet": "victim_user_id=None"},
    ("keycloak", "saml", 31): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting the test introspected wrong token'"},
    ("keycloak", "saml", 32): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "userinfo 401"},
    ("keycloak", "saml", 33): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "client_uuid=201 (HTTP status, not UUID)"},
    ("keycloak", "saml", 34): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "client UUID/user IDs captured as literal HTTP status 201"},
    ("keycloak", "saml", 35): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "no session token established for attacker"},

    # ================= logto/oidc_jwt (14 findings, 6 VIOLATION) =================
    ("logto", "oidc_jwt", 1): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "SAML trust-anchor forgery - SAML signature forgery in Logto not among 33"},
    ("logto", "oidc_jwt", 2): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "TP", "reason": "LG-1", "desc_snippet": "OIDC SSO nonce bypass: nonce omitted by IdP accepted"},
    ("logto", "oidc_jwt", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting inconsistent account-linking'"},
    ("logto", "oidc_jwt", 4): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "Partially signed SAMLResponse accepted (SAML sig wrapping - not in 33)"},
    ("logto", "oidc_jwt", 5): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "Attacker-minted JWT with arbitrary iss/kid accepted (not in 33 for logto)"},
    ("logto", "oidc_jwt", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "control M2M token 401 invalid_token at /oidc/me"},
    ("logto", "oidc_jwt", 7): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "not-in-33", "desc_snippet": "SAML assertion replay in Logto (not in 33)"},
    ("logto", "oidc_jwt", 8): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "TP", "reason": "LG-3", "desc_snippet": "SAML assertion without Conditions accepted"},
    ("logto", "oidc_jwt", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "speculative", "desc_snippet": "nonce-bypass 'appears to have succeeded'"},
    ("logto", "oidc_jwt", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting IdP-controlled profile fields may be applied without normalization'"},
    ("logto", "oidc_jwt", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "tokens introspect as inactive immediately - broken introspection"},
    ("logto", "oidc_jwt", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "revoke invalid_client 401"},
    ("logto", "oidc_jwt", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "speculative", "desc_snippet": "'could enable UI/account confusion'"},
    ("logto", "oidc_jwt", 14): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-2", "desc_snippet": "Cross-protocol account linking: SAML SSO merged with existing local password user by same verified email"},

    # ================= logto/saml (23 findings, 4 VIOLATION) =================
    ("logto", "saml", 1): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "TP", "reason": "LG-2", "desc_snippet": "OIDC SSO claim-based takeover: attacker claims mapped to victim account"},
    ("logto", "saml", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "OIDC auth 404, nonce initiation did not execute"},
    ("logto", "saml", 3): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "speculative", "desc_snippet": "'suggests test harness/endpoint mismatch'"},
    ("logto", "saml", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "Logto SAML apps IdP-only; test hit wrong surface"},
    ("logto", "saml", 5): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "speculative", "desc_snippet": "'could indicate bypass or more likely pre-existing connector'"},
    ("logto", "saml", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "attacker connector creation rejected invalid_certificate"},
    ("logto", "saml", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "speculative", "desc_snippet": "'may indicate missing nonce validation'"},
    ("logto", "saml", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting wrong token type introspected'"},
    ("logto", "saml", 9): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "revocation invalid_client 401"},
    ("logto", "saml", 10): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "not-in-33", "desc_snippet": "Expired attacker-minted JWT accepted (JWT exp in Logto not in 33)"},
    ("logto", "saml", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting session/variable contamination'"},
    ("logto", "saml", 12): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "speculative", "desc_snippet": "domain-tightening 'not exercised/validated'"},
    ("logto", "saml", 13): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "setup-failure", "desc_snippet": "wrong SAML endpoint used, not OIDC SSO"},
    ("logto", "saml", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "speculative", "desc_snippet": "'appears to succeed' with empty sub"},
    ("logto", "saml", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting potentially inconsistent account-linking'"},
    ("logto", "saml", 16): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-2", "desc_snippet": "SSO SAML connector linked attacker into victim account via unverified email"},
    ("logto", "saml", 17): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-2", "desc_snippet": "SAML SSO with attacker-controlled IdP claims linked to victim via email"},
    ("logto", "saml", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting retroactive email-based linking'"},
    ("logto", "saml", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "revocation invalid_client 401"},
    ("logto", "saml", 20): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting variable/session contamination'"},
    ("logto", "saml", 21): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting harness/state mix-up'"},
    ("logto", "saml", 22): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "password login 401 token exchange label, wrong endpoint"},
    ("logto", "saml", 23): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting a harness/state mix-up'"},

    # ================= vault/oidc_jwt (11 findings, 7 VIOLATION) =================
    ("vault", "oidc_jwt", 1): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "KID header injection (not in 33 for vault)"},
    ("vault", "oidc_jwt", 2): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "JWKS URL swap trust-anchor substitution (admin-driven config change, not in 33)"},
    ("vault", "oidc_jwt", 3): {"verdict": "VIOLATION", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "Alias collision from JWKS swap (same as #2)"},
    ("vault", "oidc_jwt", 4): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "Attacker-signed JWT re-signing (not in 33)"},
    ("vault", "oidc_jwt", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "revocation 500 'no namespace'"},
    ("vault", "oidc_jwt", 6): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "admin revoke 500 'no namespace'"},
    ("vault", "oidc_jwt", 7): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "not-in-33", "desc_snippet": "Stale JWKS/signing-key rotation (not in 33 for vault)"},
    ("vault", "oidc_jwt", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting token reuse/caching'"},
    ("vault", "oidc_jwt", 9): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "VT-5/6", "desc_snippet": "Case-confusable JWT subjects 'Admin'/'admin' mapped to same Vault entity"},
    ("vault", "oidc_jwt", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "not-in-33", "desc_snippet": "Empty-sub 500 input-validation DoS (not in 33)"},
    ("vault", "oidc_jwt", 11): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "VT-5/6", "desc_snippet": "Distinct principals mapped to same Vault entity via static alias"},

    # ================= zitadel/oidc_jwt (22 findings, 4 VIOLATION) =================
    ("zitadel", "oidc_jwt", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting missing aud validation'"},
    ("zitadel", "oidc_jwt", 2): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "ctrl_user_id=None, reduced observability"},
    ("zitadel", "oidc_jwt", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "IdP cleanup 404"},
    ("zitadel", "oidc_jwt", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting missing/ineffective kid enforcement'"},
    ("zitadel", "oidc_jwt", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "OIDC auth 404 for both control and attack"},
    ("zitadel", "oidc_jwt", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "speculative", "desc_snippet": "'may indicate acceptance of unsigned assertions'"},
    ("zitadel", "oidc_jwt", 7): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "Intent-splicing: JWT IdP proof not bound to intent (not in 33)"},
    ("zitadel", "oidc_jwt", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting intent identifier reuse'"},
    ("zitadel", "oidc_jwt", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting missing/insufficient expiry enforcement'"},
    ("zitadel", "oidc_jwt", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "speculative", "desc_snippet": "'indicating a potentially large replay window'"},
    ("zitadel", "oidc_jwt", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "speculative", "desc_snippet": "'potentially bypassing freshness requirement'"},
    ("zitadel", "oidc_jwt", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "key-fetch 'not found'"},
    ("zitadel", "oidc_jwt", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "setup-failure", "desc_snippet": "IdP cleanup 404"},
    ("zitadel", "oidc_jwt", 14): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "not-in-33", "desc_snippet": "Intent-token reuse across logins (not in 33)"},
    ("zitadel", "oidc_jwt", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting cross-session identity leakage'"},
    ("zitadel", "oidc_jwt", 16): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "not-in-33", "desc_snippet": "Login after policy disabled - login policy toggle (not in 33)"},
    ("zitadel", "oidc_jwt", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "control failed due to key-fetch not found"},
    ("zitadel", "oidc_jwt", 18): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "cleanup 404 after successful creation"},
    ("zitadel", "oidc_jwt", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "setup-failure", "desc_snippet": "no ZITADEL user_id resolved, cannot verify"},
    ("zitadel", "oidc_jwt", 20): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "external IdP disable step failed"},
    ("zitadel", "oidc_jwt", 21): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "not-in-33", "desc_snippet": "Policy toggle race - login policy toggle not in 33"},
    ("zitadel", "oidc_jwt", 22): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "broker_user_id=None, incomplete intent"},

    # ================= zitadel/saml (15 findings, 4 VIOLATION) =================
    ("zitadel", "saml", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting aud may not be enforced'"},
    ("zitadel", "saml", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "cannot fetch JWKS - setup issue"},
    ("zitadel", "saml", 3): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "speculative", "desc_snippet": "'could be a harness/capture bug'"},
    ("zitadel", "saml", 4): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "TP", "reason": "ZT-3", "desc_snippet": "JWT assertion without exp accepted and reused multiple times"},
    ("zitadel", "saml", 5): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "not-in-33", "desc_snippet": "idp_intent_token replay: one-time use bypass (not in 33)"},
    ("zitadel", "saml", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting missing nbf enforcement or test setup issue'"},
    ("zitadel", "saml", 7): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "not-in-33", "desc_snippet": "Stale SAML session after IdP disabled mid-flow (not in 33)"},
    ("zitadel", "saml", 8): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "not-in-33", "desc_snippet": "Session granted despite SAML completion 400 (not in 33)"},
    ("zitadel", "saml", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "IdP delete 404, provider not actually deleted"},
    ("zitadel", "saml", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "speculative", "desc_snippet": "'suggesting possible ID mix-up/correlation bug'"},
    ("zitadel", "saml", 11): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "setup-failure", "desc_snippet": "'Intent Token is invalid', different intent_id"},
    ("zitadel", "saml", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "not-in-33", "desc_snippet": "HTTP 500 on missing Conditions - DoS/robustness, not in 33"},
    ("zitadel", "saml", 13): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "control invalid code, reused existing session"},
    ("zitadel", "saml", 14): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "minimal-scope subject token never obtained (code exchange failed)"},
    ("zitadel", "saml", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "speculative", "desc_snippet": "'indicating possible client-auth/introspection misconfiguration'"},
}


def main():
    from collections import defaultdict
    total = len(TRIAGE)
    violations = [k for k, v in TRIAGE.items() if v["verdict"] == "VIOLATION"]
    unexpected = [k for k, v in TRIAGE.items() if v["verdict"] == "UNEXPECTED"]

    v_tp = [k for k in violations if TRIAGE[k]["label"] == "TP"]
    v_fp = [k for k in violations if TRIAGE[k]["label"] == "FP"]
    u_tp = [k for k in unexpected if TRIAGE[k]["label"] == "TP"]  # rescued
    u_fp = [k for k in unexpected if TRIAGE[k]["label"] == "FP"]

    fp_reasons = defaultdict(int)
    for k in v_fp:
        fp_reasons[TRIAGE[k]["reason"]] += 1

    all_tp_flaws = set()
    tp_high = set()
    tp_med = set()
    tp_low = set()
    for k in v_tp + u_tp:
        flaw = TRIAGE[k]["reason"]
        all_tp_flaws.add(flaw)
        conf = TRIAGE[k]["conf"]
        if conf == "HIGH":
            tp_high.add(flaw)
        elif conf == "MEDIUM":
            tp_med.add(flaw)
        else:
            tp_low.add(flaw)

    print(f"===== {RUN} manual triage =====")
    print(f"Total findings: {total}")
    print()
    print(f"VIOLATION: {len(violations)}")
    print(f"  TP (match 1 of 33): {len(v_tp)}")
    print(f"  FP: {len(v_fp)}")
    print(f"    FP reason breakdown: {dict(fp_reasons)}")
    print()
    print(f"UNEXPECTED: {len(unexpected)}")
    print(f"  Rescued TP: {len(u_tp)}")
    print(f"  FP (unexpected-not-violation): {len(u_fp)}")
    print()
    print(f"Distinct flaws found: {sorted(all_tp_flaws)} ({len(all_tp_flaws)}/33)")
    print(f"TP @ HIGH: {sorted(tp_high)} ({len(tp_high)})")
    print(f"TP @ MEDIUM: {sorted(tp_med)} ({len(tp_med)})")
    print(f"TP @ LOW: {sorted(tp_low)} ({len(tp_low)})")


if __name__ == "__main__":
    main()
