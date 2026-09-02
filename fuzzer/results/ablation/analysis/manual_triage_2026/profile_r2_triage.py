"""Manual triage for llm_judge_profile_r2 / r2. Agent-generated 2026-04-16.

Classifies every finding across all 13 campaigns against the 33 ground-truth
flaws using the rules specified by the triage driver:

  1. VIOLATION:
       a. speculative hedging -> FP:speculative
       b. setup failure       -> FP:setup-failure
       c. match to 33 flaws   -> TP:<flaw_id>   else FP:not-in-33
  2. UNEXPECTED:
       default FP:unexpected-not-violation; rescue ONLY if HIGH conf +
       non-speculative + clear flaw match (conservative).

Finding numbers are 1-indexed and correspond to the order in
unique_findings.json for each (platform, protocol) campaign.
"""
from collections import defaultdict

RUN = "profile_r2"
FINDINGS_ROOT = "/home/ubuntu/broker/fuzzer/results/ablation/llm_judge_profile_r2"

# Key: (platform, protocol, finding_1indexed)
# Value: dict(verdict, conf, invariant, label, reason, desc_snippet)
TRIAGE = {
    # =========================================================================
    # authentik / oidc_jwt  (28 findings)
    # =========================================================================
    ("authentik", "oidc_jwt", 1): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1",
        "label": "TP", "reason": "AK-3",
        "desc_snippet": "Attacker re-signed JWT accepted (trust/issuer bypass)",
    },
    ("authentik", "oidc_jwt", 2): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "UserInfo 403 for both logins (setup/harness)",
    },
    ("authentik", "oidc_jwt", 3): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Attacker-signed JWT after JWKS swap; speculative",
    },
    ("authentik", "oidc_jwt", 4): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Control JWT login 200 but no token captured",
    },
    ("authentik", "oidc_jwt", 5): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "alg=none accepted in authentik JWT M2M (not in 33)",
    },
    ("authentik", "oidc_jwt", 6): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "No session token captured",
    },
    ("authentik", "oidc_jwt", 7): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Control JWT login failed, nbf test inconclusive",
    },
    ("authentik", "oidc_jwt", 8): {
        "verdict": "VIOLATION", "conf": "MEDIUM", "invariant": "I2",
        "label": "TP", "reason": "AK-6",
        "desc_snippet": "JWT with exp=now-1s accepted (exp not enforced)",
    },
    ("authentik", "oidc_jwt", 9): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "No usable session/access token for UserInfo",
    },
    ("authentik", "oidc_jwt", 10): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "JWT with far-future nbf accepted; speculative",
    },
    ("authentik", "oidc_jwt", 11): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "No usable session/access token",
    },
    ("authentik", "oidc_jwt", 12): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "400 invalid_grant but captured JWT-like value",
    },
    ("authentik", "oidc_jwt", 13): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "UserInfo 403 on password-grant token",
    },
    ("authentik", "oidc_jwt", 14): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2",
        "label": "TP", "reason": "AK-6",
        "desc_snippet": "Expired JWT M2M authentication accepted",
    },
    ("authentik", "oidc_jwt", 15): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "UserInfo 403 after successful JWT login",
    },
    ("authentik", "oidc_jwt", 16): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "UserInfo 403 for both users",
    },
    ("authentik", "oidc_jwt", 17): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Alice/Bob same access_token — capture bug",
    },
    ("authentik", "oidc_jwt", 18): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "JWKS rotation step failed (slug-already-exists)",
    },
    ("authentik", "oidc_jwt", 19): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "200 but no session/access token captured",
    },
    ("authentik", "oidc_jwt", 20): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Trust-tightening step did not occur",
    },
    ("authentik", "oidc_jwt", 21): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "200 but no session/access token",
    },
    ("authentik", "oidc_jwt", 22): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "JWT login 200 success but no access token",
    },
    ("authentik", "oidc_jwt", 23): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection 200 even though no token minted",
    },
    ("authentik", "oidc_jwt", 24): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Provider creation failed (already exists)",
    },
    ("authentik", "oidc_jwt", 25): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "OIDC JWT login 200 but no access_token captured",
    },
    ("authentik", "oidc_jwt", 26): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Issuer mismatch flag unreliable; speculative",
    },
    ("authentik", "oidc_jwt", 27): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection 200 but token_exchange failed",
    },
    ("authentik", "oidc_jwt", 28): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection 200 but login failed",
    },

    # =========================================================================
    # authentik / saml  (27 findings, all UNEXPECTED)
    # =========================================================================
    ("authentik", "saml", 1): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Forged SAMLResponse 200 but no session token",
    },
    ("authentik", "saml", 2): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Issuer mismatch test — no post-login verification",
    },
    ("authentik", "saml", 3): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "OneTimeUse replay 200 — speculative, no verify",
    },
    ("authentik", "saml", 4): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Unable to verify session creation",
    },
    ("authentik", "saml", 5): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired SAML assertion — speculative",
    },
    ("authentik", "saml", 6): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Harness did not capture any session token",
    },
    ("authentik", "saml", 7): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Replay inconclusive — no post-login token",
    },
    ("authentik", "saml", 8): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML ACS 200 but no session",
    },
    ("authentik", "saml", 9): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token inactive post-login",
    },
    ("authentik", "saml", 10): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Revocation 401 invalid_client (setup failure)",
    },
    ("authentik", "saml", 11): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "RelayState splicing inconclusive",
    },
    ("authentik", "saml", 12): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Cross-source splicing — speculative",
    },
    ("authentik", "saml", 13): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Revocation 401 invalid_client",
    },
    ("authentik", "saml", 14): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Both SAML logins 200 but no session",
    },
    ("authentik", "saml", 15): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "MFA enablement failed — setup failure",
    },
    ("authentik", "saml", 16): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Admin MFA setup failed — no admin token",
    },
    ("authentik", "saml", 17): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "RelayState not captured",
    },
    ("authentik", "saml", 18): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Splice POST 200 but no session",
    },
    ("authentik", "saml", 19): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Cross-source confusion — unclear",
    },
    ("authentik", "saml", 20): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "ACS POST 200 but no RelayState captured",
    },
    ("authentik", "saml", 21): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Cleanup GET 405",
    },
    ("authentik", "saml", 22): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "ACS 200 but no session — inconclusive",
    },
    ("authentik", "saml", 23): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Password logins failed invalid_grant",
    },
    ("authentik", "saml", 24): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no access token captured",
    },
    ("authentik", "saml", 25): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Password tokens invalid_grant for baselines",
    },
    ("authentik", "saml", 26): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token exchange unsupported_grant_type",
    },
    ("authentik", "saml", 27): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "UserInfo 403 for valid token",
    },

    # =========================================================================
    # casdoor / oidc  (41 findings)
    # =========================================================================
    ("casdoor", "oidc", 1): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML success but userinfo 'token doesn't exist'",
    },
    ("casdoor", "oidc", 2): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Control+expired forged both produce same failure",
    },
    ("casdoor", "oidc", 3): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Password JWT rejected by /api/userinfo",
    },
    ("casdoor", "oidc", 4): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Tokens rejected by userinfo (harness issue)",
    },
    ("casdoor", "oidc", 5): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection 400 invalid_request",
    },
    ("casdoor", "oidc", 6): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML login no usable access token",
    },
    ("casdoor", "oidc", 7): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML SQL error 'Unknown column saml' (backend bug)",
    },
    ("casdoor", "oidc", 8): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Access tokens can't be used at /api/userinfo",
    },
    ("casdoor", "oidc", 9): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection 400 invalid_request",
    },
    ("casdoor", "oidc", 10): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML success but token not recognized",
    },
    ("casdoor", "oidc", 11): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Replay test inconclusive",
    },
    ("casdoor", "oidc", 12): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Control pwd + SAML both token-storage broken",
    },
    ("casdoor", "oidc", 13): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired SAML test inconclusive",
    },
    ("casdoor", "oidc", 14): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML success but token not in DB",
    },
    ("casdoor", "oidc", 15): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection 400 invalid_request",
    },
    ("casdoor", "oidc", 16): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token exchange after revocation — UNEXPECTED verdict",
    },
    ("casdoor", "oidc", 17): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Tokens not recognized by /api/userinfo",
    },
    ("casdoor", "oidc", 18): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection 400 invalid_request",
    },
    ("casdoor", "oidc", 19): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Password/token issuance mismatch",
    },
    ("casdoor", "oidc", 20): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Control JWT rejected by userinfo",
    },
    ("casdoor", "oidc", 21): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Token exchange after grant-type removed (config enforcement, not in 33)",
    },
    ("casdoor", "oidc", 22): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Access tokens fail at /api/userinfo",
    },
    ("casdoor", "oidc", 23): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but token not in DB",
    },
    ("casdoor", "oidc", 24): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Control+realm-splice same user — inconclusive",
    },
    ("casdoor", "oidc", 25): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Password JWT rejected by userinfo",
    },
    ("casdoor", "oidc", 26): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection 400 invalid_request",
    },
    ("casdoor", "oidc", 27): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but userinfo rejects token",
    },
    ("casdoor", "oidc", 28): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but token not recognized",
    },
    ("casdoor", "oidc", 29): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token collision — could be harness state leak",
    },
    ("casdoor", "oidc", 30): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but access token not recognized",
    },
    ("casdoor", "oidc", 31): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Two SAML logins same token — cannot confirm",
    },
    ("casdoor", "oidc", 32): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but token unusable",
    },
    ("casdoor", "oidc", 33): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Both SAML logins resolve to admin — inconclusive",
    },
    ("casdoor", "oidc", 34): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no usable token",
    },
    ("casdoor", "oidc", 35): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Session token reused across flows — speculative",
    },
    ("casdoor", "oidc", 36): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Cross-org token exchange UNEXPECTED; not rescued (not HIGH)",
    },
    ("casdoor", "oidc", 37): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Bearer token rejected by /api/userinfo",
    },
    ("casdoor", "oidc", 38): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection 400 invalid_request",
    },
    ("casdoor", "oidc", 39): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Control password token rejected by userinfo",
    },
    ("casdoor", "oidc", 40): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML accepted forged identity — speculative",
    },
    ("casdoor", "oidc", 41): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Inconsistent token format/handling",
    },

    # =========================================================================
    # casdoor / saml  (38 findings)
    # =========================================================================
    ("casdoor", "saml", 1): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no valid session (harness)",
    },
    ("casdoor", "saml", 2): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML success token not usable at userinfo",
    },
    ("casdoor", "saml", 3): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Issuer-mismatch test inconclusive",
    },
    ("casdoor", "saml", 4): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but token not recognized",
    },
    ("casdoor", "saml", 5): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection invalid_request",
    },
    ("casdoor", "saml", 6): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML success but broken flow",
    },
    ("casdoor", "saml", 7): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Config update JSON type mismatch (setup failure)",
    },
    ("casdoor", "saml", 8): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "setup-failure",
        "desc_snippet": "Password login token cannot be found at /api/userinfo (broken token persistence, test-harness artifact)",
    },
    ("casdoor", "saml", 9): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML SQL error 'Unknown column saml' (backend bug)",
    },
    ("casdoor", "saml", 10): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Replay test inconclusive (tokens not recognized)",
    },
    ("casdoor", "saml", 11): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection invalid_request",
    },
    ("casdoor", "saml", 12): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but token unusable",
    },
    ("casdoor", "saml", 13): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "All userinfo checks fail on password login",
    },
    ("casdoor", "saml", 14): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML OneTimeUse replay untestable",
    },
    ("casdoor", "saml", 15): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Control+attack both success; tokens not usable",
    },
    ("casdoor", "saml", 16): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired-assertion enforcement cannot be evaluated",
    },
    ("casdoor", "saml", 17): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "All logins 200 but tokens not recognized",
    },
    ("casdoor", "saml", 18): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but token not in DB",
    },
    ("casdoor", "saml", 19): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no usable token",
    },
    ("casdoor", "saml", 20): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection 400 invalid_request",
    },
    ("casdoor", "saml", 21): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Post-logout token rejected as 'expired'",
    },
    ("casdoor", "saml", 22): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but token not persisted",
    },
    ("casdoor", "saml", 23): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Unsolicited SAML 200 but no usable token",
    },
    ("casdoor", "saml", 24): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but token not recognized",
    },
    ("casdoor", "saml", 25): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "MFA bypass inconclusive (enablement failed)",
    },
    ("casdoor", "saml", 26): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but token unusable (harness)",
    },
    ("casdoor", "saml", 27): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Trust-anchor rotation failed (duplicate PK)",
    },
    ("casdoor", "saml", 28): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but token not recognized",
    },
    ("casdoor", "saml", 29): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but token not in DB",
    },
    ("casdoor", "saml", 30): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Password JWT rejected by userinfo",
    },
    ("casdoor", "saml", 31): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection 400 invalid_request",
    },
    ("casdoor", "saml", 32): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Control SAML 200 but no token",
    },
    ("casdoor", "saml", 33): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Access token unusable at /api/userinfo",
    },
    ("casdoor", "saml", 34): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token exchange wrong audience success; introspection failed",
    },
    ("casdoor", "saml", 35): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but token not usable",
    },
    ("casdoor", "saml", 36): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML login token not recognized",
    },
    ("casdoor", "saml", 37): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but token not recognized",
    },
    ("casdoor", "saml", 38): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection 400 invalid_request",
    },

    # =========================================================================
    # dex / oidc_jwt  (11 findings, all UNEXPECTED)
    # =========================================================================
    ("dex", "oidc_jwt", 1): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "400 but non-null tokens — harness state leak",
    },
    ("dex", "oidc_jwt", 2): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Identity value with 'No session token'",
    },
    ("dex", "oidc_jwt", 3): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Control failed, code rejected (setup failure)",
    },
    ("dex", "oidc_jwt", 4): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "UserInfo success without token — harness leak",
    },
    ("dex", "oidc_jwt", 5): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Stale variable reuse in captured state",
    },
    ("dex", "oidc_jwt", 6): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired-subject-token exchange — pwd grant unsupported",
    },
    ("dex", "oidc_jwt", 7): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Control code redemption failed invalid_grant",
    },
    ("dex", "oidc_jwt", 8): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "UserInfo succeeded despite exchange failure",
    },
    ("dex", "oidc_jwt", 9): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "UserInfo worked but no id_token captured",
    },
    ("dex", "oidc_jwt", 10): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Scope escalation not validated (invalid_grant)",
    },
    ("dex", "oidc_jwt", 11): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Control flow inconsistent (invalid_grant)",
    },

    # =========================================================================
    # dex / saml  (29 findings, all UNEXPECTED)
    # =========================================================================
    ("dex", "saml", 1): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Invalid bearer token — flow not completed",
    },
    ("dex", "saml", 2): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "CreateConnector unsupported (setup failure)",
    },
    ("dex", "saml", 3): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Invalid bearer token — flow not completed",
    },
    ("dex", "saml", 4): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "CreateConnector unsupported (setup failure)",
    },
    ("dex", "saml", 5): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Issuer test — invalid bearer token",
    },
    ("dex", "saml", 6): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "CreateConnector unsupported",
    },
    ("dex", "saml", 7): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Invalid bearer token after envelope signature test",
    },
    ("dex", "saml", 8): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Envelope-only signature — no token verification",
    },
    ("dex", "saml", 9): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "OneTimeUse untestable — invalid bearer",
    },
    ("dex", "saml", 10): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Replay POST 200 but no token-bound check",
    },
    ("dex", "saml", 11): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired test inconclusive — invalid bearer",
    },
    ("dex", "saml", 12): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Bearer unusable at /userinfo",
    },
    ("dex", "saml", 13): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Revocation endpoint missing (404)",
    },
    ("dex", "saml", 14): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "RelayState splicing inconclusive",
    },
    ("dex", "saml", 15): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Duplicate ACS completion — speculative",
    },
    ("dex", "saml", 16): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Invalid bearer token",
    },
    ("dex", "saml", 17): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Unsolicited SAMLResponse 200 — speculative",
    },
    ("dex", "saml", 18): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "RelayState swap incoherent (SP-init failed)",
    },
    ("dex", "saml", 19): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Duplicate callback accepted — speculative",
    },
    ("dex", "saml", 20): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Invalid bearer token",
    },
    ("dex", "saml", 21): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Invalid bearer token, replay conclusion unreliable",
    },
    ("dex", "saml", 22): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Invalid bearer token, identity-binding untestable",
    },
    ("dex", "saml", 23): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Post-login session unusable (Invalid bearer)",
    },
    ("dex", "saml", 24): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Invalid bearer — flow not completed",
    },
    ("dex", "saml", 25): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Connector provisioning failed (setup failure)",
    },
    ("dex", "saml", 26): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Auth code invalid_grant (setup failure)",
    },
    ("dex", "saml", 27): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "CreateConnector unsupported — no control applied",
    },
    ("dex", "saml", 28): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Invalid bearer — cannot validate allowedGroups",
    },
    ("dex", "saml", 29): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Connector enable failed (setup failure)",
    },

    # =========================================================================
    # keycloak / oidc  (6 findings, all UNEXPECTED)
    # =========================================================================
    ("keycloak", "oidc", 1): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "alg=none request object accepted — suspicious (not HIGH/rescue)",
    },
    ("keycloak", "oidc", 2): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Client creation failed (setup failure)",
    },
    ("keycloak", "oidc", 3): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "alg=none accepted but client not created — setup",
    },
    ("keycloak", "oidc", 4): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Client creation failed; 200 — speculative",
    },
    ("keycloak", "oidc", 5): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "alg=none accepted but control flow failed",
    },
    ("keycloak", "oidc", 6): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Client creation failed — results unreliable",
    },

    # =========================================================================
    # keycloak / saml  (35 findings, all UNEXPECTED)
    # =========================================================================
    ("keycloak", "saml", 1): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but userinfo 401 (flow did not complete)",
    },
    ("keycloak", "saml", 2): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Attacker-signed 200 but no session — speculative",
    },
    ("keycloak", "saml", 3): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "OIDC auth 404 (misrouted) — setup",
    },
    ("keycloak", "saml", 4): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Hardening 404 — setup failure",
    },
    ("keycloak", "saml", 5): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Both logins 200 but no session token",
    },
    ("keycloak", "saml", 6): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "OneTimeUse replay inconclusive",
    },
    ("keycloak", "saml", 7): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no session — speculative",
    },
    ("keycloak", "saml", 8): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Logout step failed (setup failure)",
    },
    ("keycloak", "saml", 9): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired assertion 200 but control failed (setup)",
    },
    ("keycloak", "saml", 10): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML broker HTML login page 400",
    },
    ("keycloak", "saml", 11): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no OIDC session (401 userinfo)",
    },
    ("keycloak", "saml", 12): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired-assertion after enable/disable — oracle broken",
    },
    ("keycloak", "saml", 13): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no OIDC session",
    },
    ("keycloak", "saml", 14): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Mid-flow config change 409 — test didn't actually execute",
    },
    ("keycloak", "saml", 15): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but OIDC auth failed — speculative",
    },
    ("keycloak", "saml", 16): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Admin client creation 500 (setup)",
    },
    ("keycloak", "saml", 17): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Config toggle 409 — no control applied",
    },
    ("keycloak", "saml", 18): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Both SAML logins no session",
    },
    ("keycloak", "saml", 19): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "OIDC init 400, userinfo 401 — no oracle",
    },
    ("keycloak", "saml", 20): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "IdP disable step missing (409) — not tested",
    },
    ("keycloak", "saml", 21): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Setup capture issue (client_uuid=201)",
    },
    ("keycloak", "saml", 22): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no session — userinfo fails",
    },
    ("keycloak", "saml", 23): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Only one user found — inconclusive",
    },
    ("keycloak", "saml", 24): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "OIDC client setup failed — cannot verify",
    },
    ("keycloak", "saml", 25): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token exchange failed but token captured — harness issue",
    },
    ("keycloak", "saml", 26): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "500 SAML after IdP mapper add — backend crash",
    },
    ("keycloak", "saml", 27): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Admin create_application 500 (setup)",
    },
    ("keycloak", "saml", 28): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no session",
    },
    ("keycloak", "saml", 29): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 500 (server error — potential DoS)",
    },
    ("keycloak", "saml", 30): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Resource seeding 404 (setup)",
    },
    ("keycloak", "saml", 31): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired 200 but control failed 400 — broken",
    },
    ("keycloak", "saml", 32): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Authz steps invalid (seeding failed)",
    },
    ("keycloak", "saml", 33): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token exchange rejected but active token — harness",
    },
    ("keycloak", "saml", 34): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Client creation 500 — invalid",
    },
    ("keycloak", "saml", 35): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no session token",
    },

    # =========================================================================
    # logto / oidc_jwt  (16 findings)
    # =========================================================================
    ("logto", "oidc_jwt", 1): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Endpoint 200 vs 404 differing — speculative",
    },
    ("logto", "oidc_jwt", 2): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "SAML signature wrapping (logto SAML wrapping not in 33)",
    },
    ("logto", "oidc_jwt", 3): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Forged JWT with attacker issuer accepted (logto JWT trust — not in 33)",
    },
    ("logto", "oidc_jwt", 4): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired-assertion test failed invalid_connector_id (setup)",
    },
    ("logto", "oidc_jwt", 5): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Spoofed Issuer 200 — speculative",
    },
    ("logto", "oidc_jwt", 6): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Attribute injection — speculative",
    },
    ("logto", "oidc_jwt", 7): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Replay not exercised (invalid connector id)",
    },
    ("logto", "oidc_jwt", 8): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2",
        "label": "TP", "reason": "LG-1",
        "desc_snippet": "OIDC SSO nonce enforcement bypassed",
    },
    ("logto", "oidc_jwt", 9): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML replay failed early (setup)",
    },
    ("logto", "oidc_jwt", 10): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Exchange invalid_grant with mixed-up identity",
    },
    ("logto", "oidc_jwt", 11): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Two SSO logins -> same user (not HIGH, not rescued)",
    },
    ("logto", "oidc_jwt", 12): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Admin/admin same user (not HIGH, not rescued)",
    },
    ("logto", "oidc_jwt", 13): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "display_name match — speculative",
    },
    ("logto", "oidc_jwt", 14): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Cross-protocol merge not evaluated",
    },
    ("logto", "oidc_jwt", 15): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4",
        "label": "TP", "reason": "LG-2",
        "desc_snippet": "SAML SSO different upstream sub merged to existing local user via email (LG-2)",
    },
    ("logto", "oidc_jwt", 16): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML missing Conditions — speculative",
    },

    # =========================================================================
    # logto / saml  (22 findings)
    # =========================================================================
    ("logto", "saml", 1): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Connector creation failed but SAML login succeeded",
    },
    ("logto", "saml", 2): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Attribute injection — speculative",
    },
    ("logto", "saml", 3): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "OneTimeUse not evaluated (setup)",
    },
    ("logto", "saml", 4): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "OIDC nonce omission — not HIGH, not rescued",
    },
    ("logto", "saml", 5): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Revocation invalid_client (setup failure)",
    },
    ("logto", "saml", 6): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "M2M token immediately inactive — speculative",
    },
    ("logto", "saml", 7): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Revocation invalid_client (setup failure)",
    },
    ("logto", "saml", 8): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired assertion test — connector id missing (setup)",
    },
    ("logto", "saml", 9): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "App config change 404 (setup failure)",
    },
    ("logto", "saml", 10): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "OIDC 404 — misrouted (setup failure)",
    },
    ("logto", "saml", 11): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token exchange invalid_client (setup failure)",
    },
    ("logto", "saml", 12): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Test identity mix-up — harness",
    },
    ("logto", "saml", 13): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Revocation invalid_client (setup failure)",
    },
    ("logto", "saml", 14): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "MFA-bypass inconclusive (enable failed)",
    },
    ("logto", "saml", 15): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Unverified-email test — no evidence of linking",
    },
    ("logto", "saml", 16): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Sequence mislabeled — unreliable",
    },
    ("logto", "saml", 17): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4",
        "label": "TP", "reason": "LG-2",
        "desc_snippet": "Unverified-email SAML SSO linked to local account (LG-2)",
    },
    ("logto", "saml", 18): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4",
        "label": "TP", "reason": "LG-6",
        "desc_snippet": "Empty upstream sub collapsed multiple logins to same identity (LG-6)",
    },
    ("logto", "saml", 19): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "display_name of existing user — speculative",
    },
    ("logto", "saml", 20): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "NFD vs NFC email normalization — not HIGH, not rescued",
    },
    ("logto", "saml", 21): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Attribute mapping confusion — speculative",
    },
    ("logto", "saml", 22): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Revocation invalid_client (setup failure)",
    },

    # =========================================================================
    # vault / oidc_jwt  (12 findings)
    # =========================================================================
    ("vault", "oidc_jwt", 1): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "alg=none accepted in vault — VT-2 removed from 33",
    },
    ("vault", "oidc_jwt", 2): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "JWKS URL swap — admin-driven config change, not in 33",
    },
    ("vault", "oidc_jwt", 3): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Policy/role binding mismatch (setup)",
    },
    ("vault", "oidc_jwt", 4): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "kid injection — not in 33",
    },
    ("vault", "oidc_jwt", 5): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Identical session tokens — capture mix-up",
    },
    ("vault", "oidc_jwt", 6): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Stale trust after key rotation — VT-1 removed from 33",
    },
    ("vault", "oidc_jwt", 7): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Revocation replay — speculative (not in 33 for vault)",
    },
    ("vault", "oidc_jwt", 8): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "iat future accepted — speculative",
    },
    ("vault", "oidc_jwt", 9): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Stale JWKS cache after rotation — VT-1 removed",
    },
    ("vault", "oidc_jwt", 10): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4",
        "label": "TP", "reason": "VT-5/6",
        "desc_snippet": "Case-confusable subjects collided (VT-5/6)",
    },
    ("vault", "oidc_jwt", 11): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4",
        "label": "TP", "reason": "VT-5/6",
        "desc_snippet": "identity_claim switch collapsed entities (VT-5/6)",
    },
    ("vault", "oidc_jwt", 12): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Admin entity verification failed (setup)",
    },

    # =========================================================================
    # zitadel / oidc_jwt  (22 findings)
    # =========================================================================
    ("zitadel", "oidc_jwt", 1): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Wrong-aud JWT accepted — speculative, no verify",
    },
    ("zitadel", "oidc_jwt", 2): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "JWKS fetch failure (setup)",
    },
    ("zitadel", "oidc_jwt", 3): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "IdP cleanup 404 (setup)",
    },
    ("zitadel", "oidc_jwt", 4): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Missing-kid attack still has kid — no demonstration",
    },
    ("zitadel", "oidc_jwt", 5): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Same intent_id — speculative (not in 33)",
    },
    ("zitadel", "oidc_jwt", 6): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "JWT missing exp accepted — speculative (not HIGH)",
    },
    ("zitadel", "oidc_jwt", 7): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Userinfo failed — cannot confirm",
    },
    ("zitadel", "oidc_jwt", 8): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Missing iat — speculative (not HIGH)",
    },
    ("zitadel", "oidc_jwt", 9): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent token replay — not in 33",
    },
    ("zitadel", "oidc_jwt", 10): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "nbf future accepted — speculative",
    },
    ("zitadel", "oidc_jwt", 11): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "No session token captured",
    },
    ("zitadel", "oidc_jwt", 12): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent re-use — not in 33",
    },
    ("zitadel", "oidc_jwt", 13): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Same intent ID — capture bug",
    },
    ("zitadel", "oidc_jwt", 14): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent token usable post-revocation — not in 33",
    },
    ("zitadel", "oidc_jwt", 15): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Stale intent reusable — not in 33",
    },
    ("zitadel", "oidc_jwt", 16): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Cross-intent swap inconclusive (setup)",
    },
    ("zitadel", "oidc_jwt", 17): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Inconsistent intent IDs — capture bug",
    },
    ("zitadel", "oidc_jwt", 18): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5",
        "label": "TP", "reason": "ZT-1",
        "desc_snippet": "JWT IdP login accepted wrong aud (ZT-1 aud bypass)",
    },
    ("zitadel", "oidc_jwt", 19): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Policy toggle not enforced (not in 33)",
    },
    ("zitadel", "oidc_jwt", 20): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "JWT IdP usable after policy disabled — BrokerPolicy (not in 33)",
    },
    ("zitadel", "oidc_jwt", 21): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Token-exchange scope escalation — not in 33",
    },
    ("zitadel", "oidc_jwt", 22): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection vs userinfo inconsistency — speculative",
    },

    # =========================================================================
    # zitadel / saml  (33 findings)
    # =========================================================================
    ("zitadel", "saml", 1): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "JWT wrong aud 200 — not HIGH, not rescued",
    },
    ("zitadel", "saml", 2): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent token invalid (harness/setup)",
    },
    ("zitadel", "saml", 3): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 400 but userinfo succeeded — harness leak",
    },
    ("zitadel", "saml", 4): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Login policy NotChanged (setup failure)",
    },
    ("zitadel", "saml", 5): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Session mix-up despite failed flows",
    },
    ("zitadel", "saml", 6): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2",
        "label": "TP", "reason": "ZT-3",
        "desc_snippet": "JWT IdP accepted assertion without exp (ZT-3)",
    },
    ("zitadel", "saml", 7): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 400 but userinfo 200 — test didn't validate replay",
    },
    ("zitadel", "saml", 8): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "nbf future accepted — speculative",
    },
    ("zitadel", "saml", 9): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "ctrl_user_id None — no confirmation",
    },
    ("zitadel", "saml", 10): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 500 (server crash — not in 33 security flaw)",
    },
    ("zitadel", "saml", 11): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 500 but userinfo success — harness leak",
    },
    ("zitadel", "saml", 12): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Cleanup 404 (setup)",
    },
    ("zitadel", "saml", 13): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Same intent ID — capture/collision",
    },
    ("zitadel", "saml", 14): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML failed before RelayState — not exercised",
    },
    ("zitadel", "saml", 15): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "IdP deletion 404 (setup)",
    },
    ("zitadel", "saml", 16): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Cross-session intent splice — not in 33",
    },
    ("zitadel", "saml", 17): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Same intent ID across sessions — speculative",
    },
    ("zitadel", "saml", 18): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent ID collision — speculative",
    },
    ("zitadel", "saml", 19): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Admin/admin collision inconclusive",
    },
    ("zitadel", "saml", 20): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent Token invalid — flow mismatch",
    },
    ("zitadel", "saml", 21): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Same intent ID — speculative (capture bug)",
    },
    ("zitadel", "saml", 22): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent Token invalid — flow mismatch",
    },
    ("zitadel", "saml", 23): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Same intent ID — speculative",
    },
    ("zitadel", "saml", 24): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Email case-folding — cannot confirm",
    },
    ("zitadel", "saml", 25): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Userinfo succeeded despite failed flow — harness",
    },
    ("zitadel", "saml", 26): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Variable contamination — harness",
    },
    ("zitadel", "saml", 27): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Forged SAML missing Conditions triggers 500 — not in 33",
    },
    ("zitadel", "saml", 28): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Control SAML fails — inconclusive",
    },
    ("zitadel", "saml", 29): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent identifiers inconsistent — capture bug",
    },
    ("zitadel", "saml", 30): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent Token invalid — flow mismatch",
    },
    ("zitadel", "saml", 31): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection invalid_client (setup)",
    },
    ("zitadel", "saml", 32): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Userinfo succeeded despite exchange failure — harness",
    },
    ("zitadel", "saml", 33): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Scope-escalation inconclusive (control not minted)",
    },
}


def main():
    total = len(TRIAGE)
    violation_tp = 0
    violation_fp_speculative = 0
    violation_fp_setup = 0
    violation_fp_not_in_33 = 0
    unexpected_total = 0
    unexpected_rescued = 0
    tp_flaws = set()
    tp_at_high = 0
    tp_at_medium = 0
    tp_at_low = 0
    fp_reason_counts = defaultdict(int)

    for key, entry in TRIAGE.items():
        verdict = entry["verdict"]
        label = entry["label"]
        reason = entry["reason"]
        conf = entry["conf"]
        if verdict == "VIOLATION":
            if label == "TP":
                violation_tp += 1
                tp_flaws.add(reason)
                if conf == "HIGH":
                    tp_at_high += 1
                elif conf == "MEDIUM":
                    tp_at_medium += 1
                else:
                    tp_at_low += 1
            else:
                if reason == "speculative":
                    violation_fp_speculative += 1
                elif reason == "setup-failure":
                    violation_fp_setup += 1
                elif reason == "not-in-33":
                    violation_fp_not_in_33 += 1
                fp_reason_counts[reason] += 1
        else:
            unexpected_total += 1
            if label == "TP":
                unexpected_rescued += 1
                tp_flaws.add(reason)
                if conf == "HIGH":
                    tp_at_high += 1
                elif conf == "MEDIUM":
                    tp_at_medium += 1
                else:
                    tp_at_low += 1

    violation_total = (violation_tp + violation_fp_speculative +
                       violation_fp_setup + violation_fp_not_in_33)

    print(f"===== {RUN} manual triage summary =====")
    print(f"Total findings: {total}")
    print(f"VIOLATION: {violation_total}")
    print(f"  TP: {violation_tp}")
    print(f"  FP:speculative    : {violation_fp_speculative}")
    print(f"  FP:setup-failure  : {violation_fp_setup}")
    print(f"  FP:not-in-33      : {violation_fp_not_in_33}")
    print(f"UNEXPECTED: {unexpected_total} (rescued to TP: {unexpected_rescued})")
    print(f"Distinct flaws matched: {sorted(tp_flaws)} ({len(tp_flaws)}/33)")
    print(f"TP@HIGH  : {tp_at_high}")
    print(f"TP@MEDIUM: {tp_at_medium}")
    print(f"TP@LOW   : {tp_at_low}")
    print(f"FP-by-reason (VIOLATION path): {dict(fp_reason_counts)}")


if __name__ == "__main__":
    main()
