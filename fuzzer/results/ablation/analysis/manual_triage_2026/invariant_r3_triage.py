"""Manual triage for llm_judge_invariant_r3 / r3. Agent-generated 2026-04-16.

Classification rules:
  VIOLATION:
    a. Speculative hedging -> FP:speculative
    b. Setup failure -> FP:setup-failure
    c. Match to 33 flaws -> TP:<flaw_id>, else FP:not-in-33
  UNEXPECTED:
    default FP:unexpected-not-violation; rescue only if HIGH conf + clear flaw match.
"""
from collections import defaultdict

RUN = "invariant_r3"
FINDINGS_ROOT = "/home/ubuntu/broker/fuzzer/results/ablation/llm_judge_invariant_r3"

# Ground-truth 33 flaws
GROUND_TRUTH = {
    "ZT-1", "ZT-2", "ZT-3",
    "CD-1", "CD-2", "CD-3", "CD-4", "CD-5", "CD-6", "CD-7", "CD-8", "CD-9",
    "DX-1", "DX-2", "DX-3", "DX-4", "DX-5",
    "KC-1", "KC-3", "KC-4", "KC-5", "KC-6",
    "AK-1", "AK-3", "AK-5", "AK-6", "AK-7",
    "LG-1", "LG-2", "LG-3", "LG-5", "LG-6",
    "VT-5/6",
}

# Keys: (platform, protocol, finding_index_1based)
# Values: dict with verdict, conf, invariant, label (TP/FP), reason/flaw, desc_snippet
TRIAGE = {
    # =========================================================================
    # authentik/oidc_jwt  (28 findings: 3 VIOLATION, 25 UNEXPECTED)
    # =========================================================================
    ("authentik", "oidc_jwt", 1):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "kid header confusion - attacker JWT login 200"},
    ("authentik", "oidc_jwt", 2):  {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "same downstream entity_id control vs attacker"},
    ("authentik", "oidc_jwt", 3):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "session tokens not usable at /userinfo (403)"},
    ("authentik", "oidc_jwt", 4):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "JWT claim smuggling - no access token captured"},
    ("authentik", "oidc_jwt", 5):  {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "issuer-mismatch flag but login succeeded"},
    ("authentik", "oidc_jwt", 6):  {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I2", "label": "TP", "reason": "AK-6", "desc_snippet": "Expired JWT accepted - no exp enforcement"},
    ("authentik", "oidc_jwt", 7):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "missing session token prevents principal verif"},
    ("authentik", "oidc_jwt", 8):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection 200 but no token - setup incoherent"},
    ("authentik", "oidc_jwt", 9):  {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection post-revoke 200 but no token"},
    ("authentik", "oidc_jwt", 10): {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I2", "label": "TP", "reason": "AK-6", "desc_snippet": "JWT exp=now accepted - strict future violated"},
    ("authentik", "oidc_jwt", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session token - principal verif unreliable"},
    ("authentik", "oidc_jwt", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "password grant failed - revoke test incoherent"},
    ("authentik", "oidc_jwt", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "source update failed but old JWT still works"},
    ("authentik", "oidc_jwt", 14): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session token - can't verify principal"},
    ("authentik", "oidc_jwt", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "source update failed - config-change test invalid"},
    ("authentik", "oidc_jwt", 16): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session token for UserInfo verif"},
    ("authentik", "oidc_jwt", 17): {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I3", "label": "TP", "reason": "AK-6", "desc_snippet": "Expired JWT accepted in M2M flow"},
    ("authentik", "oidc_jwt", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "/userinfo 403 for control session"},
    ("authentik", "oidc_jwt", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "attack login 200 but no session token"},
    ("authentik", "oidc_jwt", 20): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "issuer-mismatch flag but both logins succeeded"},
    ("authentik", "oidc_jwt", 21): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session tokens - can't eval I4"},
    ("authentik", "oidc_jwt", 22): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cross-aud JWT: 200 but no token - inconclusive"},
    ("authentik", "oidc_jwt", 23): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "aud test client_id collisions"},
    ("authentik", "oidc_jwt", 24): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "policy-enforcement provider still accepts"},
    ("authentik", "oidc_jwt", 25): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session/access token for UserInfo"},
    ("authentik", "oidc_jwt", 26): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "numeric claim type coercion - MEDIUM, unclear"},
    ("authentik", "oidc_jwt", 27): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "can't verify downstream identity"},
    ("authentik", "oidc_jwt", 28): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection 200 but no token - test mis-bound"},

    # =========================================================================
    # authentik/saml  (22 findings: 1 VIOLATION, 21 UNEXPECTED)
    # =========================================================================
    ("authentik", "saml", 1):  {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cross-source RelayState ACS 200, no tokens"},
    ("authentik", "saml", 2):  {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "OneTimeUse replay - no session to verify"},
    ("authentik", "saml", 3):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML success but no usable token"},
    ("authentik", "saml", 4):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "revocation invalid_client - not exercised"},
    ("authentik", "saml", 5):  {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection inactive immediately after login"},
    ("authentik", "saml", 6):  {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I2", "label": "FP", "reason": "not-in-33", "desc_snippet": "revoke-user principal maps to other user's entity_id - I4 mislabeled as I2; not a matching flaw in 33 for authentik saml"},
    ("authentik", "saml", 7):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "expired assertion replay - unverifiable"},
    ("authentik", "saml", 8):  {"verdict": "UNEXPECTED", "conf": "HIGH",   "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session token after SAML logins - setup issue"},
    ("authentik", "saml", 9):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "replay accepted but no token to confirm"},
    ("authentik", "saml", 10): {"verdict": "UNEXPECTED", "conf": "HIGH",   "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token/session handling broken (setup)"},
    ("authentik", "saml", 11): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "replay accepted but revocation failed"},
    ("authentik", "saml", 12): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cross-session splice inconclusive"},
    ("authentik", "saml", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "unsolicited SAML 200 but identity verif failed"},
    ("authentik", "saml", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML providers failed to create"},
    ("authentik", "saml", 15): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session after SAML login"},
    ("authentik", "saml", 16): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "empty NameID SAML 200 but no session"},
    ("authentik", "saml", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no-conditions SAML - no token established"},
    ("authentik", "saml", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "expired assertion still grants session - inconclusive"},
    ("authentik", "saml", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection inactive yet entity_id present"},
    ("authentik", "saml", 20): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "OneTimeUse replay - no usable token"},
    ("authentik", "saml", 21): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "issuer-confusion - no session established"},
    ("authentik", "saml", 22): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "provider creation failed but login succeeded"},

    # =========================================================================
    # casdoor/oidc  (20 findings: 3 VIOLATION, 17 UNEXPECTED)
    # =========================================================================
    ("casdoor", "oidc", 1):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "forged SAML in oidc campaign - 200 but no token"},
    ("casdoor", "oidc", 2):  {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "'admin' as forged email - suspicious"},
    ("casdoor", "oidc", 3):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "missing conditions - token non-existent"},
    ("casdoor", "oidc", 4):  {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "conflicting principal identifiers"},
    ("casdoor", "oidc", 5):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login - token not in DB"},
    ("casdoor", "oidc", 6):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "replay test - broken token persistence"},
    ("casdoor", "oidc", 7):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "expired SAML and control both fail userinfo"},
    ("casdoor", "oidc", 8):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "state splice - token not found"},
    ("casdoor", "oidc", 9):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "IdP issuer splice - token not recognized"},
    ("casdoor", "oidc", 10): {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I4", "label": "FP", "reason": "not-in-33", "desc_snippet": "Case-variant username collision (local, not SAML/email flaw); CD-9 is saml email-binding specifically - not a match"},
    ("casdoor", "oidc", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cross-protocol merge test - token not in DB"},
    ("casdoor", "oidc", 12): {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I5", "label": "TP", "reason": "CD-4", "desc_snippet": "Cross-org token exchange succeeded"},
    ("casdoor", "oidc", 13): {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I5", "label": "FP", "reason": "not-in-33", "desc_snippet": "App tag restriction via token exchange - not in 33"},
    ("casdoor", "oidc", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "OneTimeUse replay - non-persisted tokens"},
    ("casdoor", "oidc", 15): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "OneTimeUse - no valid token"},
    ("casdoor", "oidc", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token-exchange - inconsistent validation"},
    ("casdoor", "oidc", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection invalid_request"},
    ("casdoor", "oidc", 18): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "auth-code invalid_client but token exchange succeeds"},
    ("casdoor", "oidc", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "group policy - token not in DB"},
    ("casdoor", "oidc", 20): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection invalid_request"},

    # =========================================================================
    # casdoor/saml  (36 findings: 1 VIOLATION, 35 UNEXPECTED)
    # =========================================================================
    ("casdoor", "saml", 1):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "backend SQL schema error - broken path"},
    ("casdoor", "saml", 2):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "missing conditions - no usable token"},
    ("casdoor", "saml", 3):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "signature toggle - token not recognized"},
    ("casdoor", "saml", 4):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "RelayState confusion - token unknown"},
    ("casdoor", "saml", 5):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "issuer trailing slash - broken binding"},
    ("casdoor", "saml", 6):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "metadata trust anchor poisoning - no token"},
    ("casdoor", "saml", 7):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "signature wrapping - token not recognized"},
    ("casdoor", "saml", 8):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "expired assertion - no token found"},
    ("casdoor", "saml", 9):  {"verdict": "UNEXPECTED", "conf": "HIGH",   "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "backend SQL error (setup)"},
    ("casdoor", "saml", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "session persistence broken"},
    ("casdoor", "saml", 11): {"verdict": "UNEXPECTED", "conf": "HIGH",   "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "expired after TTL change - no session"},
    ("casdoor", "saml", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "session token confusion"},
    ("casdoor", "saml", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "replay after logout - broken flow"},
    ("casdoor", "saml", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "replay with OneTimeUse - broken"},
    ("casdoor", "saml", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cross-realm splice - incoherent"},
    ("casdoor", "saml", 16): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection invalid_request"},
    ("casdoor", "saml", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML ACS out-of-context accepted 200"},
    ("casdoor", "saml", 18): {"verdict": "UNEXPECTED", "conf": "HIGH",   "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "redirect_uri change - token not recognized"},
    ("casdoor", "saml", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "same symptom regardless - mis-bound flow"},
    ("casdoor", "saml", 20): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "state reuse - token not usable"},
    ("casdoor", "saml", 21): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "both map to 'admin' - test setup issue"},
    ("casdoor", "saml", 22): {"verdict": "UNEXPECTED", "conf": "HIGH",   "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token storage broken/confusion"},
    ("casdoor", "saml", 23): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token collision across logins"},
    ("casdoor", "saml", 24): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cross-client splice - broken"},
    ("casdoor", "saml", 25): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "app creation failed - cannot determine"},
    ("casdoor", "saml", 26): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "email-binding collision - token not in DB"},
    ("casdoor", "saml", 27): {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I4", "label": "FP", "reason": "not-in-33", "desc_snippet": "Case-variant username collision in casdoor SAML - not in 33; CD-9 is email/identity-binding specifically"},
    ("casdoor", "saml", 28): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cross-provider same-subject - broken"},
    ("casdoor", "saml", 29): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection invalid_request"},
    ("casdoor", "saml", 30): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "password login still succeeds - policy may not apply"},
    ("casdoor", "saml", 31): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "expired still grants - broken token"},
    ("casdoor", "saml", 32): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "expired - no verifiable session"},
    ("casdoor", "saml", 33): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token exchange ignores revocation (UNEXPECTED not VIOLATION)"},
    ("casdoor", "saml", 34): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection invalid_request"},
    ("casdoor", "saml", 35): {"verdict": "UNEXPECTED", "conf": "HIGH",   "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "issuer confusion - broken flow"},
    ("casdoor", "saml", 36): {"verdict": "UNEXPECTED", "conf": "HIGH",   "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SQL error 'Unknown column saml' (setup)"},

    # =========================================================================
    # dex/oidc_jwt  (5 findings: 1 VIOLATION, 4 UNEXPECTED)
    # =========================================================================
    ("dex", "oidc_jwt", 1): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "insecure connector couldn't be enabled"},
    ("dex", "oidc_jwt", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "control code redemption failed"},
    ("dex", "oidc_jwt", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "code invalidated after wrong redirect_uri"},
    ("dex", "oidc_jwt", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "UserInfo succeeded despite code exchange failed"},
    ("dex", "oidc_jwt", 5): {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I4", "label": "FP", "reason": "not-in-33", "desc_snippet": "Empty-sub vs named principal collapse in dex oidc - no matching flaw in 33 for dex"},

    # =========================================================================
    # dex/saml  (25 findings: 2 VIOLATION, 23 UNEXPECTED)
    # =========================================================================
    ("dex", "saml", 1):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cert substitution - userinfo 'Invalid bearer'"},
    ("dex", "saml", 2):  {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "CreateConnector unsupported - precondition not applied"},
    ("dex", "saml", 3):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "unsigned assertion envelope - no token"},
    ("dex", "saml", 4):  {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "issuer mismatch - no usable session"},
    ("dex", "saml", 5):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "signature toggle reauth - no session"},
    ("dex", "saml", 6):  {"verdict": "UNEXPECTED", "conf": "HIGH",   "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "CreateConnector unsupported - config change did not occur"},
    ("dex", "saml", 7):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "OneTimeUse replay - Invalid bearer token"},
    ("dex", "saml", 8):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "expired assertion replay - downstream failed"},
    ("dex", "saml", 9):  {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "replay started new flow - not true replay"},
    ("dex", "saml", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "replay across config - userinfo 403"},
    ("dex", "saml", 11): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "connector reconfig failed - not meaningfully tested"},
    ("dex", "saml", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "RelayState replay - no OneTimeUse enforcement? but UNEXPECTED"},
    ("dex", "saml", 13): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 403 after 'success'"},
    ("dex", "saml", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cross-flow splice relay_state - UNEXPECTED"},
    ("dex", "saml", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "HTTP 500 on wrong connector"},
    ("dex", "saml", 16): {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I3", "label": "TP", "reason": "DX-5", "desc_snippet": "SAML callback accepted unsolicited response - InResponseTo/state missing"},
    ("dex", "saml", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 403 after unsolicited login"},
    ("dex", "saml", 18): {"verdict": "VIOLATION",  "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "not-in-33", "desc_snippet": "Cross-connector state confusion - not in 33 (DX-4/5 are specific)"},
    ("dex", "saml", 19): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "post-login userinfo failed"},
    ("dex", "saml", 20): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "double-complete same flow - atomicity"},
    ("dex", "saml", 21): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 403 after 'success'"},
    ("dex", "saml", 22): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "empty NameID - invalid_grant on code exchange"},
    ("dex", "saml", 23): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "attacker-signed accepted in secure mode"},
    ("dex", "saml", 24): {"verdict": "UNEXPECTED", "conf": "HIGH",   "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "CreateConnector unsupported - setup failure"},
    ("dex", "saml", 25): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "invalid bearer token post-login"},

    # =========================================================================
    # keycloak/oidc  (8 findings: 0 VIOLATION, 8 UNEXPECTED)
    # =========================================================================
    ("keycloak", "oidc", 1): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "alg=none request object 200 but client creation failed"},
    ("keycloak", "oidc", 2): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "alg=none before/after - client not created"},
    ("keycloak", "oidc", 3): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "request_uri injection - client creation failed"},
    ("keycloak", "oidc", 4): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "scope injection - client creation failed"},
    ("keycloak", "oidc", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "alg=none after PKCE - hardening didn't apply"},
    ("keycloak", "oidc", 6): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "PKCE enforce didn't actually apply"},
    ("keycloak", "oidc", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "alg=none redirect_uri override - hedged"},
    ("keycloak", "oidc", 8): {"verdict": "UNEXPECTED", "conf": "HIGH",   "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "client config failed - not reliable"},

    # =========================================================================
    # keycloak/saml  (34 findings: 1 VIOLATION, 33 UNEXPECTED)
    # =========================================================================
    ("keycloak", "saml", 1):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cert substitution - no session"},
    ("keycloak", "saml", 2):  {"verdict": "UNEXPECTED", "conf": "HIGH",   "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "broken verify - test didn't complete"},
    ("keycloak", "saml", 3):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "signature enforcement - no token"},
    ("keycloak", "saml", 4):  {"verdict": "UNEXPECTED", "conf": "HIGH",   "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "create_provider 409 - update didn't happen"},
    ("keycloak", "saml", 5):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "issuer mismatch - rejected when pinned"},
    ("keycloak", "saml", 6):  {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 401 - test not completed"},
    ("keycloak", "saml", 7):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no authenticated OIDC session established"},
    ("keycloak", "saml", 8):  {"verdict": "UNEXPECTED", "conf": "HIGH",   "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "create_provider 409 - invalidates results"},
    ("keycloak", "saml", 9):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "OneTimeUse replay - userinfo 401"},
    ("keycloak", "saml", 10): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "replay 200 but can't confirm"},
    ("keycloak", "saml", 11): {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I2", "label": "FP", "reason": "not-in-33", "desc_snippet": "Expired SAML (NotOnOrAfter) accepted in keycloak - not in 33; KC-3 is onetimeuse/replay, this is expiry"},
    ("keycloak", "saml", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "control login also no usable token"},
    ("keycloak", "saml", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "replay inconclusive"},
    ("keycloak", "saml", 14): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "realm lifespan change didn't apply"},
    ("keycloak", "saml", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "expired assertion accepted - inconclusive"},
    ("keycloak", "saml", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "replay same id 200 - can't confirm"},
    ("keycloak", "saml", 17): {"verdict": "UNEXPECTED", "conf": "HIGH",   "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 401 undermines oracle"},
    ("keycloak", "saml", 18): {"verdict": "UNEXPECTED", "conf": "HIGH",   "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "broken flow coherence"},
    ("keycloak", "saml", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "disable toggle didn't happen"},
    ("keycloak", "saml", 20): {"verdict": "UNEXPECTED", "conf": "HIGH",   "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "admin logout path normalization failed"},
    ("keycloak", "saml", 21): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no usable session token"},
    ("keycloak", "saml", 22): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "principal switch - flow inc."},
    ("keycloak", "saml", 23): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cross-realm splice - inconclusive"},
    ("keycloak", "saml", 24): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "linkOnly toggle - inconsistent setup"},
    ("keycloak", "saml", 25): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "IdP toggle didn't happen"},
    ("keycloak", "saml", 26): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "case-confusion NameID - no session"},
    ("keycloak", "saml", 27): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "case-confusion can't be evaluated"},
    ("keycloak", "saml", 28): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "empty NameID - no session"},
    ("keycloak", "saml", 29): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "linkOnly collision - unobservable"},
    ("keycloak", "saml", 30): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "provider creation already exists"},
    ("keycloak", "saml", 31): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "client UUID captured as HTTP status"},
    ("keycloak", "saml", 32): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML 200 but no session token"},
    ("keycloak", "saml", 33): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "trustEmail unverified linking - no token"},
    ("keycloak", "saml", 34): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "missingNormalization - no oracle"},

    # =========================================================================
    # logto/oidc_jwt  (17 findings: 3 VIOLATION, 14 UNEXPECTED)
    # =========================================================================
    ("logto", "oidc_jwt", 1):  {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "unsigned envelope-only accepted - hedged"},
    ("logto", "oidc_jwt", 2):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "forged JWT accepted - but no session"},
    ("logto", "oidc_jwt", 3):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "invalid_connector_id - setup"},
    ("logto", "oidc_jwt", 4):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "OIDC auth endpoint 404 - not exercised"},
    ("logto", "oidc_jwt", 5):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "refresh revoke - exchange failed upfront"},
    ("logto", "oidc_jwt", 6):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "revoke invalid_client"},
    ("logto", "oidc_jwt", 7):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "revoke invalid_client prevents exercise"},
    ("logto", "oidc_jwt", 8):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "invalid_connector_id drift"},
    ("logto", "oidc_jwt", 9):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "code exchange invalid_grant upfront"},
    ("logto", "oidc_jwt", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "OIDC /oidc/auth 404 - not exercised"},
    ("logto", "oidc_jwt", 11): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "session labeling inconsistent"},
    ("logto", "oidc_jwt", 12): {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I4", "label": "TP", "reason": "LG-2", "desc_snippet": "SAML NameID collision same verified email - principals collapse"},
    ("logto", "oidc_jwt", 13): {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I4", "label": "TP", "reason": "LG-2", "desc_snippet": "Cross-protocol password-vs-SAML same-email takeover"},
    ("logto", "oidc_jwt", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "case-fold email merge - MEDIUM conf, not rescued"},
    ("logto", "oidc_jwt", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "org context omission - same token"},
    ("logto", "oidc_jwt", 16): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection active=false"},
    ("logto", "oidc_jwt", 17): {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I5", "label": "TP", "reason": "LG-3", "desc_snippet": "SAML missing Conditions accepted - over-broad authz"},

    # =========================================================================
    # logto/saml  (9 findings: 4 VIOLATION, 5 UNEXPECTED)
    # =========================================================================
    ("logto", "saml", 1): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "failed OIDC but identity_id captured"},
    ("logto", "saml", 2): {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "Attacker-signed SAML accepted - SAML signature-wrapping not in logto's 33 (similar to removed LG-4)"},
    ("logto", "saml", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "OIDC auth step 404 - not executed"},
    ("logto", "saml", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "MFA not enabled - inconclusive"},
    ("logto", "saml", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "unverified-email linking - MEDIUM, hedged"},
    ("logto", "saml", 6): {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I4", "label": "TP", "reason": "LG-2", "desc_snippet": "Unverified-email SAML SSO linked to existing account - takeover"},
    ("logto", "saml", 7): {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I4", "label": "TP", "reason": "LG-6", "desc_snippet": "Empty/missing upstream subject collapses principals"},
    ("logto", "saml", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "sub change same email - MEDIUM hedged"},
    ("logto", "saml", 9): {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I4", "label": "TP", "reason": "LG-2", "desc_snippet": "Account takeover via email-based SSO linking (verified toggle)"},

    # =========================================================================
    # vault/oidc_jwt  (13 findings: 9 VIOLATION, 4 UNEXPECTED)
    # =========================================================================
    ("vault", "oidc_jwt", 1):  {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "kid injection - not in 33 for vault"},
    ("vault", "oidc_jwt", 2):  {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "old-key JWT after rotation + re-signed (stale trust, removed VT-1)"},
    ("vault", "oidc_jwt", 3):  {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "re-signed untrusted key accepted - not in 33"},
    ("vault", "oidc_jwt", 4):  {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "admin swapped jwks_url (test-setup config change)"},
    ("vault", "oidc_jwt", 5):  {"verdict": "UNEXPECTED", "conf": "HIGH",   "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "revocation failed - 'no namespace' 500"},
    ("vault", "oidc_jwt", 6):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no effective revocation - broken path"},
    ("vault", "oidc_jwt", 7):  {"verdict": "VIOLATION",  "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "not-in-33", "desc_snippet": "iat future-skew bypass - not in 33"},
    ("vault", "oidc_jwt", 8):  {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "admin verif failed"},
    ("vault", "oidc_jwt", 9):  {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I3", "label": "FP", "reason": "not-in-33", "desc_snippet": "key rotation pubkeys stale (VT-1 removed) - not in 33"},
    ("vault", "oidc_jwt", 10): {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I4", "label": "TP", "reason": "VT-5/6", "desc_snippet": "Case-variant Admin/admin sub collapse"},
    ("vault", "oidc_jwt", 11): {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I4", "label": "TP", "reason": "VT-5/6", "desc_snippet": "Email-claim cross-user collision"},
    ("vault", "oidc_jwt", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "empty sub HTTP 500 - DoS"},
    ("vault", "oidc_jwt", 13): {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I4", "label": "TP", "reason": "VT-5/6", "desc_snippet": "identity_claim rebinding collapses principals"},

    # =========================================================================
    # zitadel/oidc_jwt  (15 findings: 4 VIOLATION, 11 UNEXPECTED)
    # =========================================================================
    ("zitadel", "oidc_jwt", 1):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "wrong-aud JWT IdP login succeeded - UNEXPECTED/hedged"},
    ("zitadel", "oidc_jwt", 2):  {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "kid injection - kid actually identical"},
    ("zitadel", "oidc_jwt", 3):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "alg=none HTTP 500 on both"},
    ("zitadel", "oidc_jwt", 4):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "intent-token collision - flow splicing"},
    ("zitadel", "oidc_jwt", 5):  {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "stale IdP user data after failed login"},
    ("zitadel", "oidc_jwt", 6):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "malformed JWT parsing error"},
    ("zitadel", "oidc_jwt", 7):  {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cleanup 404 - lifecycle"},
    ("zitadel", "oidc_jwt", 8):  {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I2", "label": "TP", "reason": "ZT-3", "desc_snippet": "JWT IdP accepted missing-exp assertion"},
    ("zitadel", "oidc_jwt", 9):  {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I2", "label": "TP", "reason": "ZT-3", "desc_snippet": "Same no-exp JWT accepted again - replay"},
    ("zitadel", "oidc_jwt", 10): {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I2", "label": "FP", "reason": "not-in-33", "desc_snippet": "IdP intent-token replay - not in 33"},
    ("zitadel", "oidc_jwt", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "replay - same admin context limits conclusion"},
    ("zitadel", "oidc_jwt", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cross-intent splice possible - UNEXPECTED"},
    ("zitadel", "oidc_jwt", 13): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "control inconsistency"},
    ("zitadel", "oidc_jwt", 14): {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I5", "label": "FP", "reason": "not-in-33", "desc_snippet": "External IdP after policy toggle - not in 33"},
    ("zitadel", "oidc_jwt", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "policy precondition unclear"},

    # =========================================================================
    # zitadel/saml  (22 findings: 2 VIOLATION, 20 UNEXPECTED)
    # =========================================================================
    ("zitadel", "saml", 1):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "wrong-aud JWT IdP 200 - hedged"},
    ("zitadel", "saml", 2):  {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no downstream user_id"},
    ("zitadel", "saml", 3):  {"verdict": "UNEXPECTED", "conf": "HIGH",   "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML HTTP 500 on missing Conditions - DoS, not ZT-2"},
    ("zitadel", "saml", 4):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "flow incoherence - userinfo works despite failures"},
    ("zitadel", "saml", 5):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "intent id collision"},
    ("zitadel", "saml", 6):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "idp_intent_token reused"},
    ("zitadel", "saml", 7):  {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I2", "label": "TP", "reason": "ZT-3", "desc_snippet": "JWT IdP accepted missing-exp - freshness failure"},
    ("zitadel", "saml", 8):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "control+attack same attrs - setup"},
    ("zitadel", "saml", 9):  {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "HTTP 500 - robustness"},
    ("zitadel", "saml", 10): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cleanup 404"},
    ("zitadel", "saml", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "HTTP 500 input handling"},
    ("zitadel", "saml", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 200 despite code failed - setup"},
    ("zitadel", "saml", 13): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "principal-binding inconsistent"},
    ("zitadel", "saml", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 200 despite code failed"},
    ("zitadel", "saml", 15): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cleanup 404 - id mismatch"},
    ("zitadel", "saml", 16): {"verdict": "VIOLATION",  "conf": "HIGH",   "invariant": "I5", "label": "FP", "reason": "setup-failure", "desc_snippet": "SAML login failed (400/500), userinfo 200 - flow incoherence/harness not a real violation"},
    ("zitadel", "saml", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "HTTP 500 on missing Conditions"},
    ("zitadel", "saml", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 200 despite upstream failures"},
    ("zitadel", "saml", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "scope escalation but no subject token"},
    ("zitadel", "saml", 20): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "exchange w/o subject token minted"},
    ("zitadel", "saml", 21): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection unauthorized_client"},
    ("zitadel", "saml", 22): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "control flow failed"},
}


def main():
    total = len(TRIAGE)
    violation_total = 0
    unexpected_total = 0
    tp_count = 0
    fp_count = 0
    fp_reasons = defaultdict(int)
    tp_flaws = set()
    tp_by_conf = defaultdict(int)  # conf -> count of TPs
    rescued_from_unexpected = 0

    for key, rec in TRIAGE.items():
        if rec["verdict"] == "VIOLATION":
            violation_total += 1
        else:
            unexpected_total += 1

        if rec["label"] == "TP":
            tp_count += 1
            tp_flaws.add(rec["reason"])
            tp_by_conf[rec["conf"]] += 1
            if rec["verdict"] == "UNEXPECTED":
                rescued_from_unexpected += 1
        else:
            fp_count += 1
            fp_reasons[rec["reason"]] += 1

    print(f"===== Manual triage for {RUN} =====")
    print(f"Total findings triaged:  {total}")
    print(f"  VIOLATION:             {violation_total}")
    print(f"  UNEXPECTED:            {unexpected_total}")
    print()
    print(f"TP total:                {tp_count}")
    print(f"FP total:                {fp_count}")
    print()
    print("FP reason breakdown:")
    for reason, count in sorted(fp_reasons.items(), key=lambda x: -x[1]):
        print(f"  {reason:40s} {count}")
    print()
    print(f"Distinct flaws found: {sorted(tp_flaws)} ({len(tp_flaws)}/33)")
    missed = sorted(GROUND_TRUTH - tp_flaws)
    print(f"Missed flaws ({len(missed)}/33): {missed}")
    print()
    print("TP by confidence:")
    for c in ["HIGH", "MEDIUM", "LOW"]:
        print(f"  {c:8s} {tp_by_conf[c]}")
    print()
    print(f"UNEXPECTED rescued to TP: {rescued_from_unexpected}")

    # VIOLATION-only breakdown (precision among VIOLATION)
    v_tp = sum(1 for r in TRIAGE.values() if r["verdict"] == "VIOLATION" and r["label"] == "TP")
    v_fp = sum(1 for r in TRIAGE.values() if r["verdict"] == "VIOLATION" and r["label"] == "FP")
    prec_violation = v_tp / (v_tp + v_fp) if (v_tp + v_fp) else 0
    print()
    print(f"Among VIOLATION ({violation_total}): TP={v_tp}, FP={v_fp}, precision={prec_violation:.1%}")


if __name__ == "__main__":
    main()
