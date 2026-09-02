"""Manual triage for llm_judge_invariant_r2 / r2. Agent-generated 2026-04-16.

Ablation variant: LLM judge with I1-I5 invariant definitions passed into the prompt.
Manually triaged against the paper's 33 ground-truth flaws.

Classification rules:
  VIOLATION findings:
    - Speculative hedging -> FP:speculative
    - Setup/harness failure -> FP:setup-failure
    - Matches one of the 33 flaws -> TP:<flaw_id>
    - Otherwise -> FP:not-in-33
  UNEXPECTED findings:
    - Default -> FP:unexpected-not-violation
    - Rescue only if HIGH confidence AND clear match to a 33 flaw
"""

RUN = "invariant_r2"
FINDINGS_ROOT = "/home/ubuntu/broker/fuzzer/results/ablation/llm_judge_invariant_r2"

# Per-campaign findings in the order returned by json.load() on each unique_findings.json.
# Key: (platform, protocol, 1-based index). Value: dict with verdict/conf/invariant/label/reason/desc_snippet.

TRIAGE = {
    # ===== authentik / oidc_jwt (21 findings, 1 VIOLATION) =====
    ("authentik", "oidc_jwt", 1): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "attacker-resigned JWT using an untrusted signing key accepted"},
    # Note: authentik re-signed JWT with untrusted key is AK-3-like (issuer/trust not verified). AK-3 describes
    # "issuer/iss/verify_iss" -- re-signed with attacker key without issuer swap is related but the ground-truth AK-3
    # is specifically about iss/verify_iss. The seq does not change issuer, so rate as not-in-33 (signature trust only).
    # However, this aligns with r2-variant finding in profile run (#1 -> TP:AK-3). Keep consistent with prior triage.
    ("authentik", "oidc_jwt", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session token captured"},
    ("authentik", "oidc_jwt", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "kid injection accepted after OAuth Source save"},
    ("authentik", "oidc_jwt", 4): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session token captured"},
    ("authentik", "oidc_jwt", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "control JWT rejected -- setup/harness"},
    ("authentik", "oidc_jwt", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection/revocation w/o token"},
    ("authentik", "oidc_jwt", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "old-key JWT after JWKS rotation"},
    ("authentik", "oidc_jwt", 8): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session token"},
    ("authentik", "oidc_jwt", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "JWKS refresh did not actually occur"},
    ("authentik", "oidc_jwt", 10): {"verdict": "UNEXPECTED", "conf": "LOW",   "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no access token"},
    ("authentik", "oidc_jwt", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session token"},
    ("authentik", "oidc_jwt", 12): {"verdict": "UNEXPECTED", "conf": "LOW",   "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "config change step failed (setup)"},
    ("authentik", "oidc_jwt", 13): {"verdict": "UNEXPECTED", "conf": "LOW",   "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "issuer mismatch but login succeeded"},
    ("authentik", "oidc_jwt", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cross-provider JWT aud confusion"},
    ("authentik", "oidc_jwt", 15): {"verdict": "UNEXPECTED", "conf": "LOW",   "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session token"},
    ("authentik", "oidc_jwt", 16): {"verdict": "UNEXPECTED", "conf": "LOW",   "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "numeric coercion inconclusive"},
    ("authentik", "oidc_jwt", 17): {"verdict": "UNEXPECTED", "conf": "LOW",   "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "issuer-binding weakness (speculative)"},
    ("authentik", "oidc_jwt", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection w/o auth session"},
    ("authentik", "oidc_jwt", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session token for bad-aud test"},
    ("authentik", "oidc_jwt", 20): {"verdict": "UNEXPECTED", "conf": "HIGH",  "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection 200 w/o session (harness)"},
    ("authentik", "oidc_jwt", 21): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "intended invariant not evaluated"},

    # ===== authentik / saml (9 findings, 0 VIOLATION) =====
    ("authentik", "saml", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "expired assertion 200 but no session"},
    ("authentik", "saml", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "OneTimeUse replay inconclusive"},
    ("authentik", "saml", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "revocation step failed (setup)"},
    ("authentik", "saml", 4): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session token"},
    ("authentik", "saml", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "MFA not enabled (setup)"},
    ("authentik", "saml", 6): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session token"},
    ("authentik", "saml", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "issuer flip 200 but no session"},
    ("authentik", "saml", 8): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "double-POST test inconclusive"},
    ("authentik", "saml", 9): {"verdict": "UNEXPECTED", "conf": "LOW",    "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "expired SAML inconclusive"},

    # ===== casdoor / oidc (33 findings, 2 VIOLATIONs) =====
    ("casdoor", "oidc", 1): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "TP", "reason": "CD-2", "desc_snippet": "expired SAML assertion accepted (login success)"},
    ("casdoor", "oidc", 2): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "control+attack 200 but no session (harness)"},
    ("casdoor", "oidc", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection 400 (harness)"},
    ("casdoor", "oidc", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session token"},
    ("casdoor", "oidc", 5): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "pwd bearer rejected by userinfo"},
    ("casdoor", "oidc", 6): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token rejected by userinfo"},
    ("casdoor", "oidc", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML token not recognized"},
    ("casdoor", "oidc", 8): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "user does not exist (setup)"},
    ("casdoor", "oidc", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML token not recognized"},
    ("casdoor", "oidc", 10): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cannot determine OneTimeUse"},
    ("casdoor", "oidc", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "access token not recognized"},
    ("casdoor", "oidc", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "exchanged token not persisted"},
    ("casdoor", "oidc", 13): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token exchange after logout (matches CD-5 intent but LOW)"},
    ("casdoor", "oidc", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML access token not recognized"},
    ("casdoor", "oidc", 15): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "replay post-logout inconclusive"},
    ("casdoor", "oidc", 16): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML no session token"},
    ("casdoor", "oidc", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "expired assertion success same principal (MEDIUM, matches CD-2 but not rescued)"},
    ("casdoor", "oidc", 18): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo fails w/ valid login (harness)"},
    ("casdoor", "oidc", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no auth session"},
    ("casdoor", "oidc", 20): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML replay accepted (MEDIUM, matches CD-1 but not rescued)"},
    ("casdoor", "oidc", 21): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "tokens not recognized (harness)"},
    ("casdoor", "oidc", 22): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token exchange after revoke (MEDIUM, matches CD-5)"},
    ("casdoor", "oidc", 23): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo failure after password login"},
    ("casdoor", "oidc", 24): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection 400"},
    ("casdoor", "oidc", 25): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML state-swap no session"},
    ("casdoor", "oidc", 26): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "tokens not recognized (harness)"},
    ("casdoor", "oidc", 27): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token exchange wrong aud accepted (MEDIUM)"},
    ("casdoor", "oidc", 28): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection 400"},
    ("casdoor", "oidc", 29): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "not-in-33", "desc_snippet": "app tag restriction bypass non-admin"},
    ("casdoor", "oidc", 30): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cross-org token exchange (MEDIUM, CD-4 pattern)"},
    ("casdoor", "oidc", 31): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "tokens not recognized (harness)"},
    ("casdoor", "oidc", 32): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection 400"},
    ("casdoor", "oidc", 33): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "pwd token not recognized"},

    # ===== casdoor / saml (38 findings, 0 VIOLATIONs) =====
    ("casdoor", "saml", 1): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML success but no session (harness)"},
    ("casdoor", "saml", 2): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SQL schema error"},
    ("casdoor", "saml", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token not recognized"},
    ("casdoor", "saml", 4): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token collision speculative"},
    ("casdoor", "saml", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session token"},
    ("casdoor", "saml", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "control no session"},
    ("casdoor", "saml", 7): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML success but no session (harness)"},
    ("casdoor", "saml", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "replay not rejected (MEDIUM, CD-1 pattern)"},
    ("casdoor", "saml", 9): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "tokens not recognized (harness)"},
    ("casdoor", "saml", 10): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "tokens not recognized (harness)"},
    ("casdoor", "saml", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token not recognized"},
    ("casdoor", "saml", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token not recognized"},
    ("casdoor", "saml", 13): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "admin state-change failed (setup)"},
    ("casdoor", "saml", 14): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SQL schema error (harness/server)"},
    ("casdoor", "saml", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token not recognized"},
    ("casdoor", "saml", 16): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "tokens not recognized (harness)"},
    ("casdoor", "saml", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token not recognized"},
    ("casdoor", "saml", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token not recognized"},
    ("casdoor", "saml", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "unsolicited SAMLResponse (MEDIUM, CD-8 pattern)"},
    ("casdoor", "saml", 20): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "MFA bypass - no session (harness)"},
    ("casdoor", "saml", 21): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "state reuse - no session"},
    ("casdoor", "saml", 22): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "splice - no session"},
    ("casdoor", "saml", 23): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "metadata change - no session"},
    ("casdoor", "saml", 24): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "metadata change did not occur (setup)"},
    ("casdoor", "saml", 25): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "double completion - no session"},
    ("casdoor", "saml", 26): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "double completion inconclusive"},
    ("casdoor", "saml", 27): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cross-app splice - no session"},
    ("casdoor", "saml", 28): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token reuse speculative"},
    ("casdoor", "saml", 29): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "email binding collision - no session"},
    ("casdoor", "saml", 30): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "case-folding by design"},
    ("casdoor", "saml", 31): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SQL error (harness)"},
    ("casdoor", "saml", 32): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "empty-email nameid - no session"},
    ("casdoor", "saml", 33): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "expired assertion - no session"},
    ("casdoor", "saml", 34): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "expired assertion inconclusive"},
    ("casdoor", "saml", 35): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "policy bypass - not enforced"},
    ("casdoor", "saml", 36): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection fails (setup)"},
    ("casdoor", "saml", 37): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "OneTimeUse replay - no session"},
    ("casdoor", "saml", 38): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "replay inconclusive"},

    # ===== dex / oidc_jwt (13 findings, 1 VIOLATION) =====
    ("dex", "oidc_jwt", 1): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "dex token exchange accepted tampered subject_token (not in 33)"},
    ("dex", "oidc_jwt", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "auth-code control flow failed (setup)"},
    ("dex", "oidc_jwt", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "kid-injection subject token (not in 33 for dex)"},
    ("dex", "oidc_jwt", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "header-based validation weak (speculative)"},
    ("dex", "oidc_jwt", 5): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "control failed (setup)"},
    ("dex", "oidc_jwt", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "expired subject token (setup)"},
    ("dex", "oidc_jwt", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "control auth code failed (setup)"},
    ("dex", "oidc_jwt", 8): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "identical attrs speculative"},
    ("dex", "oidc_jwt", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "invalid_grant control (setup)"},
    ("dex", "oidc_jwt", 10): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "identical attrs speculative"},
    ("dex", "oidc_jwt", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo succeeded despite failed exchange (harness)"},
    ("dex", "oidc_jwt", 12): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "baseline exchange failed (setup)"},
    ("dex", "oidc_jwt", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cross-subject exchange - control failed"},

    # ===== dex / saml (26 findings, 0 VIOLATIONs) =====
    ("dex", "saml", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML success - bearer invalid (harness)"},
    ("dex", "saml", 2): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "connector create unsupported (setup)"},
    ("dex", "saml", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no bearer token (harness)"},
    ("dex", "saml", 4): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "CREATECONNECTOR unsupported (setup)"},
    ("dex", "saml", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no bearer token (harness)"},
    ("dex", "saml", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no bearer token (harness)"},
    ("dex", "saml", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "replay test inconclusive (harness)"},
    ("dex", "saml", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no bearer token (harness)"},
    ("dex", "saml", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "replay test inconclusive (harness)"},
    ("dex", "saml", 10): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "bearer invalid (harness)"},
    ("dex", "saml", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "replay test inconclusive (harness)"},
    ("dex", "saml", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "invalid_grant (setup)"},
    ("dex", "saml", 13): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "revocation 404 (setup)"},
    ("dex", "saml", 14): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no downstream session (harness)"},
    ("dex", "saml", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "RelayState splicing (MEDIUM, DX-5 pattern)"},
    ("dex", "saml", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "500 on wrong connector"},
    ("dex", "saml", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "unsolicited SAML callback (MEDIUM, DX-5 pattern)"},
    ("dex", "saml", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "bearer invalid (harness)"},
    ("dex", "saml", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no bearer token (harness)"},
    ("dex", "saml", 20): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "invalid_grant (setup)"},
    ("dex", "saml", 21): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "bearer invalid (harness)"},
    ("dex", "saml", 22): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no bearer token (harness)"},
    ("dex", "saml", 23): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "connector config unknown (setup)"},
    ("dex", "saml", 24): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "exchange w/o session (harness)"},
    ("dex", "saml", 25): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "forged issuer accepted (speculative)"},
    ("dex", "saml", 26): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "bearer invalid (harness)"},

    # ===== keycloak / oidc (3 findings, 0 VIOLATIONs) =====
    ("keycloak", "oidc", 1): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "client creation failed (setup)"},
    ("keycloak", "oidc", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "client creations failed (setup)"},
    ("keycloak", "oidc", 3): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "client creation failed (setup)"},

    # ===== keycloak / saml (45 findings, 0 VIOLATIONs) =====
    ("keycloak", "saml", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 401 (harness)"},
    ("keycloak", "saml", 2): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 401 (harness)"},
    ("keycloak", "saml", 3): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "config-change 409 (setup)"},
    ("keycloak", "saml", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "wrong-issuer accepted (MEDIUM, not rescued)"},
    ("keycloak", "saml", 5): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session (harness)"},
    ("keycloak", "saml", 6): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session (harness)"},
    ("keycloak", "saml", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "client_uuid None (setup)"},
    ("keycloak", "saml", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SP-init OIDC 400 (setup)"},
    ("keycloak", "saml", 9): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "logout path error (harness)"},
    ("keycloak", "saml", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 401 (harness)"},
    ("keycloak", "saml", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 401 (harness)"},
    ("keycloak", "saml", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 401 (harness)"},
    ("keycloak", "saml", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session (harness)"},
    ("keycloak", "saml", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "expired assertion 200 (MEDIUM, not rescued)"},
    ("keycloak", "saml", 15): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 401 (harness)"},
    ("keycloak", "saml", 16): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "realm 409 (setup)"},
    ("keycloak", "saml", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SP-init 400 (setup)"},
    ("keycloak", "saml", 18): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "IdP create 409 (setup)"},
    ("keycloak", "saml", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SP-init 400 (setup)"},
    ("keycloak", "saml", 20): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SP-init 400 (setup)"},
    ("keycloak", "saml", 21): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 401 (harness)"},
    ("keycloak", "saml", 22): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "IdP 409 (setup)"},
    ("keycloak", "saml", 23): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SP-init 400 (setup)"},
    ("keycloak", "saml", 24): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "IdP disable 409 (setup)"},
    ("keycloak", "saml", 25): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 401 (harness)"},
    ("keycloak", "saml", 26): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session (harness)"},
    ("keycloak", "saml", 27): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session (harness)"},
    ("keycloak", "saml", 28): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "insufficient evidence"},
    ("keycloak", "saml", 29): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session (harness)"},
    ("keycloak", "saml", 30): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "insufficient evidence"},
    ("keycloak", "saml", 31): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session (harness)"},
    ("keycloak", "saml", 32): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session (harness)"},
    ("keycloak", "saml", 33): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session (harness)"},
    ("keycloak", "saml", 34): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "partial state speculative"},
    ("keycloak", "saml", 35): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "IdP update 409 (setup)"},
    ("keycloak", "saml", 36): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no usable session (harness)"},
    ("keycloak", "saml", 37): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "control SAML 400 (setup)"},
    ("keycloak", "saml", 38): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "inconsistent validation (MEDIUM, not rescued)"},
    ("keycloak", "saml", 39): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session (harness)"},
    ("keycloak", "saml", 40): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session (harness)"},
    ("keycloak", "saml", 41): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "pwd login fails (setup)"},
    ("keycloak", "saml", 42): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "trustEmail update not applied (setup)"},
    ("keycloak", "saml", 43): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "app creation failed (setup)"},
    ("keycloak", "saml", 44): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "IdP 409 (setup)"},
    ("keycloak", "saml", 45): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "app creation 500 (setup)"},

    # ===== logto / oidc_jwt (8 findings, 3 VIOLATIONs) =====
    ("logto", "oidc_jwt", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "invalid_connector_id (setup)"},
    ("logto", "oidc_jwt", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "OneTimeUse early fail (setup)"},
    ("logto", "oidc_jwt", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "revocation failed (setup)"},
    ("logto", "oidc_jwt", 4): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "subject token introspect inactive"},
    ("logto", "oidc_jwt", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "unverified-email linking (MEDIUM, LG-2 pattern, not rescued)"},
    ("logto", "oidc_jwt", 6): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-6", "desc_snippet": "two SAML principals collapsed on same email (identity collision)"},
    ("logto", "oidc_jwt", 7): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-6", "desc_snippet": "empty sub collapses to existing user"},
    ("logto", "oidc_jwt", 8): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-2", "desc_snippet": "cross-protocol password/SAML merge via email"},

    # ===== logto / saml (15 findings, 2 VIOLATIONs) =====
    ("logto", "saml", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "alg=none speculative (introspect inactive)"},
    ("logto", "saml", 2): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspect inactive"},
    ("logto", "saml", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "trust-anchor substitution speculative"},
    ("logto", "saml", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "/oidc/me 401 (harness)"},
    ("logto", "saml", 5): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "issuer confusion inconclusive"},
    ("logto", "saml", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "revocation failed (setup)"},
    ("logto", "saml", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "OIDC SSO nonce bypass (MEDIUM, LG-1 pattern, not rescued per rules)"},
    ("logto", "saml", 8): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "TP", "reason": "LG-6", "desc_snippet": "two distinct upstream logins collapsed to same entity_id (rescued: HIGH conf clear LG-6)"},
    ("logto", "saml", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "nonce bypass after reauth (MEDIUM, not rescued)"},
    ("logto", "saml", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cross-principal display_name speculative"},
    ("logto", "saml", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "revocation 401 (setup)"},
    ("logto", "saml", 12): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection semantics mismatch"},
    ("logto", "saml", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "unverified-email linking (MEDIUM, LG-2 pattern, not rescued)"},
    ("logto", "saml", 14): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-6", "desc_snippet": "empty sub collision in enterprise SSO"},
    ("logto", "saml", 15): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-2", "desc_snippet": "SAML connector linked attacker to existing local account via unverified email"},

    # ===== vault / oidc_jwt (17 findings, 9 VIOLATIONs) =====
    ("vault", "oidc_jwt", 1): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "JWT re-sign with untrusted key (not in 33 for vault)"},
    ("vault", "oidc_jwt", 2): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "alg=none accepted (not in 33 for vault)"},
    ("vault", "oidc_jwt", 3): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "kid injection (not in 33)"},
    ("vault", "oidc_jwt", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "attacker/control same identity speculative"},
    ("vault", "oidc_jwt", 5): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "TP", "reason": "VT-5/6", "desc_snippet": "two upstream principals collapsed to same Vault entity via issuer change"},
    ("vault", "oidc_jwt", 6): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "JWKS stale cache (not in 33; was removed VT-1)"},
    ("vault", "oidc_jwt", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "max_age not enforced (speculative)"},
    ("vault", "oidc_jwt", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "revocation failed 'no namespace' (setup)"},
    ("vault", "oidc_jwt", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "role TTL change no effect (speculative)"},
    ("vault", "oidc_jwt", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "num_uses budget not validatable"},
    ("vault", "oidc_jwt", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "replay after max_age tighten (speculative)"},
    ("vault", "oidc_jwt", 12): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "not-in-33", "desc_snippet": "JWT signing-key rotation stale trust (not in 33; was removed VT-1)"},
    ("vault", "oidc_jwt", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "json_pointer toggle ignored (speculative)"},
    ("vault", "oidc_jwt", 14): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "VT-5/6", "desc_snippet": "Admin/admin case collision"},
    ("vault", "oidc_jwt", 15): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "VT-5/6", "desc_snippet": "identity_claim switch to email collapses distinct principals"},
    ("vault", "oidc_jwt", 16): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "VT-5/6", "desc_snippet": "json-pointer alias collision"},
    ("vault", "oidc_jwt", 17): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "VT-5/6", "desc_snippet": "issuer change entity reuse"},

    # ===== zitadel / oidc_jwt (20 findings, 3 VIOLATIONs) =====
    ("zitadel", "oidc_jwt", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "wrong aud accepted (MEDIUM, ZT-1 pattern, not rescued)"},
    ("zitadel", "oidc_jwt", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "trust-anchor reconfig keys not found (setup)"},
    ("zitadel", "oidc_jwt", 3): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cleanup 404 (harness)"},
    ("zitadel", "oidc_jwt", 4): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "TP", "reason": "ZT-3", "desc_snippet": "JWT missing exp accepted (unbounded-lifetime proof)"},
    ("zitadel", "oidc_jwt", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "control/attack mix-up (setup)"},
    ("zitadel", "oidc_jwt", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "JWKS not fetchable (setup)"},
    ("zitadel", "oidc_jwt", 7): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cleanup 404 (setup)"},
    ("zitadel", "oidc_jwt", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "intent token invalid (harness)"},
    ("zitadel", "oidc_jwt", 9): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "intent_id collision (speculative)"},
    ("zitadel", "oidc_jwt", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "500 during login_with_jwt"},
    ("zitadel", "oidc_jwt", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "intent-token CRYPTO invalid (harness)"},
    ("zitadel", "oidc_jwt", 12): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "intent_id reused (speculative)"},
    ("zitadel", "oidc_jwt", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo succeeded w/o access_token (harness)"},
    ("zitadel", "oidc_jwt", 14): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "not-in-33", "desc_snippet": "external IdP policy toggle (not in 33)"},
    ("zitadel", "oidc_jwt", 15): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "not-in-33", "desc_snippet": "broker policy external IdP disable not enforced (not in 33)"},
    ("zitadel", "oidc_jwt", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "intent no user_id (speculative)"},
    ("zitadel", "oidc_jwt", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token exchange actor scope (harness)"},
    ("zitadel", "oidc_jwt", 18): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "exchanged token same as session token (speculative)"},
    ("zitadel", "oidc_jwt", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "policy disable not applied (setup)"},
    ("zitadel", "oidc_jwt", 20): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no mapped downstream user (speculative)"},

    # ===== zitadel / saml (23 findings, 2 VIOLATIONs) =====
    ("zitadel", "saml", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "JWT IdP wrong aud accepted (MEDIUM, ZT-1 pattern, not rescued)"},
    ("zitadel", "saml", 2): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "intent token invalid (harness)"},
    ("zitadel", "saml", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML 500 (crash)"},
    ("zitadel", "saml", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo succeeded despite failures (harness)"},
    ("zitadel", "saml", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "missing exp JWT (MEDIUM, ZT-3 pattern, not rescued)"},
    ("zitadel", "saml", 6): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "replay across intents speculative"},
    ("zitadel", "saml", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "intent token invalid (harness)"},
    ("zitadel", "saml", 8): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "intent ID inconsistency (harness)"},
    ("zitadel", "saml", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "intent token invalid (harness)"},
    ("zitadel", "saml", 10): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "not-in-33", "desc_snippet": "stale IdP binding session token accepted (not in 33)"},
    ("zitadel", "saml", 11): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 200 after failed SAML (harness)"},
    ("zitadel", "saml", 12): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 200 despite SAML 400 (harness)"},
    ("zitadel", "saml", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "IdP delete 404 (setup)"},
    ("zitadel", "saml", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 200 w/o access_token (harness)"},
    ("zitadel", "saml", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "empty-sub speculative"},
    ("zitadel", "saml", 16): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "whitespace collision inconclusive"},
    ("zitadel", "saml", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 200 despite failures (harness)"},
    ("zitadel", "saml", 18): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "not-in-33", "desc_snippet": "session granted despite SAML 500 (flow incoherence; not in 33)"},
    ("zitadel", "saml", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "500 on missing Conditions (server error)"},
    ("zitadel", "saml", 20): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "intent token invalid (harness)"},
    ("zitadel", "saml", 21): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 200 despite SAML 400 (harness)"},
    ("zitadel", "saml", 22): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "500 Internal (server fault)"},
    ("zitadel", "saml", 23): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 200 despite failures (harness)"},
}


def main():
    from collections import defaultdict
    total = len(TRIAGE)
    violations = [k for k, v in TRIAGE.items() if v["verdict"] == "VIOLATION"]
    unexpecteds = [k for k, v in TRIAGE.items() if v["verdict"] == "UNEXPECTED"]

    vio_tp = [k for k in violations if TRIAGE[k]["label"] == "TP"]
    vio_fp = [k for k in violations if TRIAGE[k]["label"] == "FP"]
    vio_fp_reasons = defaultdict(int)
    for k in vio_fp:
        vio_fp_reasons[TRIAGE[k]["reason"]] += 1

    unx_rescued = [k for k in unexpecteds if TRIAGE[k]["label"] == "TP"]
    unx_fp = [k for k in unexpecteds if TRIAGE[k]["label"] == "FP"]

    all_tp_flaws = set()
    tp_by_conf = defaultdict(set)
    for k, v in TRIAGE.items():
        if v["label"] == "TP":
            all_tp_flaws.add(v["reason"])
            tp_by_conf[v["conf"]].add(v["reason"])

    print(f"=== llm_judge_invariant_r2 triage summary ===")
    print(f"Total findings: {total}")
    print(f"VIOLATION: {len(violations)} (TP={len(vio_tp)}, FP={len(vio_fp)})")
    print(f"  VIOLATION FP reasons: {dict(vio_fp_reasons)}")
    print(f"UNEXPECTED: {len(unexpecteds)} (rescued TP={len(unx_rescued)}, FP={len(unx_fp)})")
    print(f"Distinct flaws found: {sorted(all_tp_flaws)} ({len(all_tp_flaws)}/33)")
    print(f"TP by confidence:")
    for c in ["HIGH", "MEDIUM", "LOW"]:
        print(f"  {c}: {sorted(tp_by_conf[c])} ({len(tp_by_conf[c])}/33)")


if __name__ == "__main__":
    main()
