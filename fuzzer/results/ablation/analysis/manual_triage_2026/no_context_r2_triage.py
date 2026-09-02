"""Manual triage for llm_judge_r2 (no_context) / r2. Agent-generated 2026-04-16.

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

RUN = "no_context_r2"
FINDINGS_ROOT = "/home/ubuntu/broker/fuzzer/results/ablation/llm_judge_r2"

# Key: (platform, protocol, finding_1indexed)
# Value: dict(verdict, conf, invariant, label, reason, desc_snippet)
TRIAGE = {
    # =========================================================================
    # authentik / oidc_jwt  (20 findings)
    # =========================================================================
    ("authentik", "oidc_jwt", 1): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Attacker re-signed JWT accepted; JWT trust-anchor (no AK I1-JWT flaw in 33)",
    },
    ("authentik", "oidc_jwt", 2): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Control JWT login 200 but userinfo 403; inconsistent session",
    },
    ("authentik", "oidc_jwt", 3): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "JWT login 200/success but no session token; inconclusive",
    },
    ("authentik", "oidc_jwt", 4): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "JWKS staleness test inconclusive (no session token)",
    },
    ("authentik", "oidc_jwt", 5): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Issuer-mismatch flag speculative; cannot confirm",
    },
    ("authentik", "oidc_jwt", 6): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection 200 for failed login; harness artifact",
    },
    ("authentik", "oidc_jwt", 7): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2",
        "label": "TP", "reason": "AK-6",
        "desc_snippet": "Expired JWT accepted (200 success) - matches AK-6 exp/JWT",
    },
    ("authentik", "oidc_jwt", 8): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Successful login returned no session token; harness",
    },
    ("authentik", "oidc_jwt", 9): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection 200 despite no successful login; harness",
    },
    ("authentik", "oidc_jwt", 10): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2",
        "label": "TP", "reason": "AK-6",
        "desc_snippet": "JWT with exp=now accepted - matches AK-6 exp/JWT temporal",
    },
    ("authentik", "oidc_jwt", 11): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Successful JWT logins returned no session; harness",
    },
    ("authentik", "oidc_jwt", 12): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "setup-failure",
        "desc_snippet": "Login failed 400 but session token issued; contradictory",
    },
    ("authentik", "oidc_jwt", 13): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Replay test inconclusive; both rejected",
    },
    ("authentik", "oidc_jwt", 14): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Redirect-URI test returned invalid_client; setup",
    },
    ("authentik", "oidc_jwt", 15): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Code invalidated after earlier exchange; harness",
    },
    ("authentik", "oidc_jwt", 16): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "JWKS rotation test inconclusive (no session token)",
    },
    ("authentik", "oidc_jwt", 17): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Old-key JWT after rotation accepted (speculative)",
    },
    ("authentik", "oidc_jwt", 18): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Cross-provider aud confusion inconclusive",
    },
    ("authentik", "oidc_jwt", 19): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "aud-mismatch accepted; speculative - downstream denied",
    },
    ("authentik", "oidc_jwt", 20): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired token accepted; speculative",
    },

    # =========================================================================
    # authentik / saml  (16 findings)
    # =========================================================================
    ("authentik", "saml", 1): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML login 200 but no session; replay untestable",
    },
    ("authentik", "saml", 2): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Revocation 401 invalid_client; setup failure",
    },
    ("authentik", "saml", 3): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired SAML 200 success but no session; speculative",
    },
    ("authentik", "saml", 4): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "All SAML logins 200 but no session; harness issue",
    },
    ("authentik", "saml", 5): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired SAML reported success but no session; harness",
    },
    ("authentik", "saml", 6): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Control/fresh logins 200 without session; harness",
    },
    ("authentik", "saml", 7): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Replay-after-revocation test inconclusive",
    },
    ("authentik", "saml", 8): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Revocation failed 401; replay test invalid",
    },
    ("authentik", "saml", 9): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "OneTimeUse replay test inconclusive",
    },
    ("authentik", "saml", 10): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Source-disable mid-flow test inconclusive",
    },
    ("authentik", "saml", 11): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "User-disable step failed (setup); cannot interpret",
    },
    ("authentik", "saml", 12): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML without Conditions accepted; speculative hedge",
    },
    ("authentik", "saml", 13): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Post-login verify failed; harness",
    },
    ("authentik", "saml", 14): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "User disable step failed; cannot validate",
    },
    ("authentik", "saml", 15): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Post-login verify failed; harness",
    },
    ("authentik", "saml", 16): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Provider creation failed; replay test invalid",
    },

    # =========================================================================
    # casdoor / oidc  (25 findings)
    # =========================================================================
    ("casdoor", "oidc", 1): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML signature-wrapping: 200 but no session",
    },
    ("casdoor", "oidc", 2): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Identity fields conflict; speculative",
    },
    ("casdoor", "oidc", 3): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Trust-anchor substitution: token not in DB",
    },
    ("casdoor", "oidc", 4): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML replay: 200 but no session",
    },
    ("casdoor", "oidc", 5): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired SAML accepted but speculative (no session)",
    },
    ("casdoor", "oidc", 6): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Control/expired both 200 but no session",
    },
    ("casdoor", "oidc", 7): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Admin subject mapping speculative",
    },
    ("casdoor", "oidc", 8): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Missing Conditions test inconclusive",
    },
    ("casdoor", "oidc", 9): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Subject mapping speculative",
    },
    ("casdoor", "oidc", 10): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired SAML assertion test inconclusive",
    },
    ("casdoor", "oidc", 11): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Session token overlap speculative",
    },
    ("casdoor", "oidc", 12): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "OneTimeUse replay test inconclusive",
    },
    ("casdoor", "oidc", 13): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Replay second login 200 - suspicious but unconfirmed",
    },
    ("casdoor", "oidc", 14): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Logout broader than expected; not in 33",
    },
    ("casdoor", "oidc", 15): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Misleading expiry - not a real flaw",
    },
    ("casdoor", "oidc", 16): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token exchange 401 invalid_client; setup",
    },
    ("casdoor", "oidc", 17): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "JWT captured despite 401; speculative",
    },
    ("casdoor", "oidc", 18): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Cross-protocol identity merge: no session token",
    },
    ("casdoor", "oidc", 19): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Email collision password-vs-SAML: no session",
    },
    ("casdoor", "oidc", 20): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "NameID collision: no session",
    },
    ("casdoor", "oidc", 21): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Session token reuse speculative",
    },
    ("casdoor", "oidc", 22): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 200 but no session (harness); speculative",
    },
    ("casdoor", "oidc", 23): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Session token collision between principals; speculative",
    },
    ("casdoor", "oidc", 24): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML OneTimeUse test inconclusive",
    },
    ("casdoor", "oidc", 25): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Admin-mapping speculative",
    },

    # =========================================================================
    # casdoor / saml  (39 findings)
    # =========================================================================
    ("casdoor", "saml", 1): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Issuer mismatch: 200 but no session; speculative",
    },
    ("casdoor", "saml", 2): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Admin-subject mapping speculative",
    },
    ("casdoor", "saml", 3): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Forged SAML 200 maps to admin; speculative (no session)",
    },
    ("casdoor", "saml", 4): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Trust-anchor substitution: no session",
    },
    ("casdoor", "saml", 5): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Issuer confusion splice: no session",
    },
    ("casdoor", "saml", 6): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Sig policy confusion: no session",
    },
    ("casdoor", "saml", 7): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Remove-conditions: no session",
    },
    ("casdoor", "saml", 8): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Metadata trust-anchor: no session",
    },
    ("casdoor", "saml", 9): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Admin-subject speculative",
    },
    ("casdoor", "saml", 10): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "OneTimeUse replay: no session; inconclusive",
    },
    ("casdoor", "saml", 11): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Replay not rejected speculative",
    },
    ("casdoor", "saml", 12): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Cross-identity replay test inconclusive",
    },
    ("casdoor", "saml", 13): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token reuse speculative",
    },
    ("casdoor", "saml", 14): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired after rotation: no session",
    },
    ("casdoor", "saml", 15): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "NotOnOrAfter enforcement uncertain",
    },
    ("casdoor", "saml", 16): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Replay across two users: no session",
    },
    ("casdoor", "saml", 17): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "State-swap speculative (misleading success)",
    },
    ("casdoor", "saml", 18): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Completion after disable: no session",
    },
    ("casdoor", "saml", 19): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Admin identity speculative",
    },
    ("casdoor", "saml", 20): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Backend SQL error: info-disclosure/DoS not in 33",
    },
    ("casdoor", "saml", 21): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Provider-switch splice: no session",
    },
    ("casdoor", "saml", 22): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3",
        "label": "TP", "reason": "CD-5",
        "desc_snippet": "Token exchange after logout succeeds - matches CD-5 revok/token-exchange",
    },
    ("casdoor", "saml", 23): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Username case-confusion prevention; inverse flaw; not in 33",
    },
    ("casdoor", "saml", 24): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "IdP entity-id collision: no session",
    },
    ("casdoor", "saml", 25): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Admin entity-id speculative",
    },
    ("casdoor", "saml", 26): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Unicode homoglyph collision: no session",
    },
    ("casdoor", "saml", 27): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Mis-binding speculative",
    },
    ("casdoor", "saml", 28): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Empty-email collision: no session",
    },
    ("casdoor", "saml", 29): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Account-linking surface speculative",
    },
    ("casdoor", "saml", 30): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Control SAML: no session",
    },
    ("casdoor", "saml", 31): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5",
        "label": "TP", "reason": "CD-4",
        "desc_snippet": "Cross-client token exchange accepted - matches CD-4 token-exchange/cross-tenant",
    },
    ("casdoor", "saml", 32): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token exchange wrong audience; speculative",
    },
    ("casdoor", "saml", 33): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection fails; misconfig speculative",
    },
    ("casdoor", "saml", 34): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired SAML into token exchange: no session",
    },
    ("casdoor", "saml", 35): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Password-disable config not enforced; not in 33",
    },
    ("casdoor", "saml", 36): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML token not persisted; harness",
    },
    ("casdoor", "saml", 37): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5",
        "label": "TP", "reason": "CD-4",
        "desc_snippet": "Cross-client RFC8693 token exchange - matches CD-4",
    },
    ("casdoor", "saml", 38): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5",
        "label": "TP", "reason": "CD-4",
        "desc_snippet": "Cross-organization token exchange accepted - matches CD-4",
    },
    ("casdoor", "saml", 39): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection fails; setup",
    },

    # =========================================================================
    # dex / oidc_jwt  (21 findings)
    # =========================================================================
    ("dex", "oidc_jwt", 1): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Password login unsupported_grant_type; setup",
    },
    ("dex", "oidc_jwt", 2): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Admin endpoints 404; setup",
    },
    ("dex", "oidc_jwt", 3): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Authorize endpoint 404; setup",
    },
    ("dex", "oidc_jwt", 4): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired subject_token exchange; speculative",
    },
    ("dex", "oidc_jwt", 5): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Unsupported_grant_type setup",
    },
    ("dex", "oidc_jwt", 6): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Initial code exchange failure; harness issue, not a flaw match",
    },
    ("dex", "oidc_jwt", 7): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Alice/Bob identical identities; connector mix-up",
    },
    ("dex", "oidc_jwt", 8): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Future-nbf subject_token accepted; dex OIDC JWT nbf not in 33",
    },
    ("dex", "oidc_jwt", 9): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Inconsistent session after invalid_grant; harness",
    },
    ("dex", "oidc_jwt", 10): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Test harness state leakage speculative",
    },
    ("dex", "oidc_jwt", 11): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "State leakage speculative",
    },
    ("dex", "oidc_jwt", 12): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Password grant failure; setup",
    },
    ("dex", "oidc_jwt", 13): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Identity verification despite token exchange failure; harness",
    },
    ("dex", "oidc_jwt", 14): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "State leakage speculative",
    },
    ("dex", "oidc_jwt", 15): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Empty-sub vs normal-sub mapping same downstream; dex OIDC I4 not in 33",
    },
    ("dex", "oidc_jwt", 16): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "subject_token_type confusion; dex OIDC I4 not in 33",
    },
    ("dex", "oidc_jwt", 17): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Scope escalation speculative",
    },
    ("dex", "oidc_jwt", 18): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Wrong-audience exchange; speculative",
    },
    ("dex", "oidc_jwt", 19): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Cross-identity splicing inconclusive",
    },
    ("dex", "oidc_jwt", 20): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "invalid_grant but identity granted; harness",
    },
    ("dex", "oidc_jwt", 21): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Both principals resolve to same subject speculative",
    },

    # =========================================================================
    # dex / saml  (11 findings)
    # =========================================================================
    ("dex", "saml", 1): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Invalid bearer token on both flows; harness",
    },
    ("dex", "saml", 2): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Admin config step failed; setup",
    },
    ("dex", "saml", 3): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Provider creation failed; setup",
    },
    ("dex", "saml", 4): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Invalid bearer token after SAML; harness",
    },
    ("dex", "saml", 5): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Invalid bearer token; harness",
    },
    ("dex", "saml", 6): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Admin ops failed; setup",
    },
    ("dex", "saml", 7): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Expired SAML replay at ACS accepted; speculative hedge",
    },
    ("dex", "saml", 8): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Relaystate replay both 200 suspicious; no session",
    },
    ("dex", "saml", 9): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Wrong connector callback HTTP 500; robustness not in 33",
    },
    ("dex", "saml", 10): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Group gate bypass inconclusive",
    },
    ("dex", "saml", 11): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Admin CREATECONNECTOR unsupported; setup",
    },

    # =========================================================================
    # keycloak / oidc  (5 findings)
    # =========================================================================
    ("keycloak", "oidc", 1): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Unsigned request object (alg=none) appears accepted; UNEXPECTED/MEDIUM not rescued",
    },
    ("keycloak", "oidc", 2): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "request_uri injection with alg=none; UNEXPECTED/MEDIUM not rescued",
    },
    ("keycloak", "oidc", 3): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Client creation failed; setup",
    },
    ("keycloak", "oidc", 4): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Unsigned request object accepted; UNEXPECTED/MEDIUM not rescued",
    },
    ("keycloak", "oidc", 5): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Policy change not exercised; inconclusive",
    },

    # =========================================================================
    # keycloak / saml  (15 findings)
    # =========================================================================
    ("keycloak", "saml", 1): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Issuer-mismatch: 200 but no session; harness",
    },
    ("keycloak", "saml", 2): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "TrustEmail principal-collapse inconclusive",
    },
    ("keycloak", "saml", 3): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "OneTimeUse replay: no session",
    },
    ("keycloak", "saml", 4): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Admin revoke user-not-found; setup",
    },
    ("keycloak", "saml", 5): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Cross-mount collision: no session",
    },
    ("keycloak", "saml", 6): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Unverified-email linking: no session",
    },
    ("keycloak", "saml", 7): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Email casefold collision; KC I4 email-linking not in 33",
    },
    ("keycloak", "saml", 8): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Session verification failed; harness",
    },
    ("keycloak", "saml", 9): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "No-conditions test: no session",
    },
    ("keycloak", "saml", 10): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Client creation 500; setup",
    },
    ("keycloak", "saml", 11): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Group mapper 500; setup",
    },
    ("keycloak", "saml", 12): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Application 500; setup",
    },
    ("keycloak", "saml", 13): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Provider update 500; setup",
    },
    ("keycloak", "saml", 14): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "No session; harness",
    },
    ("keycloak", "saml", 15): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "OneTimeUse replay 200 but no session; inconclusive",
    },

    # =========================================================================
    # logto / oidc_jwt  (15 findings)
    # =========================================================================
    ("logto", "oidc_jwt", 1): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "SAML signature-wrapping envelope-only; logto I1-SAML not in 33",
    },
    ("logto", "oidc_jwt", 2): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "KID injection/attacker-minted JWT; not in 33",
    },
    ("logto", "oidc_jwt", 3): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "alg=none; speculative hedge",
    },
    ("logto", "oidc_jwt", 4): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection inactive; harness issue",
    },
    ("logto", "oidc_jwt", 5): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "alg_none token actually RS256; test invalid",
    },
    ("logto", "oidc_jwt", 6): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Invalid connector ID; setup",
    },
    ("logto", "oidc_jwt", 7): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "OneTimeUse invalid connector; setup",
    },
    ("logto", "oidc_jwt", 8): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2",
        "label": "TP", "reason": "LG-1",
        "desc_snippet": "OIDC SSO nonce bypass - matches LG-1",
    },
    ("logto", "oidc_jwt", 9): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Display name despite no session; state leak",
    },
    ("logto", "oidc_jwt", 10): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Unverified email linking; UNEXPECTED/MEDIUM not rescued",
    },
    ("logto", "oidc_jwt", 11): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Empty sub collision; UNEXPECTED/MEDIUM not rescued",
    },
    ("logto", "oidc_jwt", 12): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4",
        "label": "TP", "reason": "LG-2",
        "desc_snippet": "Cross-protocol identity merge verified email - matches LG-2 email auto-link",
    },
    ("logto", "oidc_jwt", 13): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4",
        "label": "TP", "reason": "LG-6",
        "desc_snippet": "OIDC SSO sub casefold collision - matches LG-6 collision/case/identity",
    },
    ("logto", "oidc_jwt", 14): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Issuer confusion same nameid; not a strong match",
    },
    ("logto", "oidc_jwt", 15): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Missing Conditions overgrant; UNEXPECTED/MEDIUM not rescued",
    },

    # =========================================================================
    # logto / saml  (20 findings)
    # =========================================================================
    ("logto", "saml", 1): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Forged SAMLResponse signature - not in 33 (logto I1-SAML)",
    },
    ("logto", "saml", 2): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Connector creation 400; setup",
    },
    ("logto", "saml", 3): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SSO display_name vs email mismatch; speculative",
    },
    ("logto", "saml", 4): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection inactive for new tokens; harness",
    },
    ("logto", "saml", 5): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection same entity_id speculative",
    },
    ("logto", "saml", 6): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Revoke invalid_client; setup",
    },
    ("logto", "saml", 7): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Revoke invalid_client; setup",
    },
    ("logto", "saml", 8): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Cross-user state leakage speculative",
    },
    ("logto", "saml", 9): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Identity mix-up speculative",
    },
    ("logto", "saml", 10): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "State bleed speculative",
    },
    ("logto", "saml", 11): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Introspection inconsistent speculative",
    },
    ("logto", "saml", 12): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Unverified-email linking speculative",
    },
    ("logto", "saml", 13): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4",
        "label": "TP", "reason": "LG-6",
        "desc_snippet": "Username case-confusion admin/Admin - matches LG-6 case/identity",
    },
    ("logto", "saml", 14): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Second login failed 422; harness confusion",
    },
    ("logto", "saml", 15): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Empty sub collision; not in 33 for logto",
    },
    ("logto", "saml", 16): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Issuer confusion same sub; not in 33 for logto",
    },
    ("logto", "saml", 17): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4",
        "label": "TP", "reason": "LG-2",
        "desc_snippet": "Cross-connector email-verified linking - matches LG-2 email auto-link",
    },
    ("logto", "saml", 18): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Revocation invalid_client; setup",
    },
    ("logto", "saml", 19): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "M2M introspection subject confusion speculative",
    },
    ("logto", "saml", 20): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Display name mix-up speculative",
    },

    # =========================================================================
    # vault / oidc_jwt  (17 findings)
    # =========================================================================
    ("vault", "oidc_jwt", 1): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Trust-anchor substitution Vault I1 not in 33",
    },
    ("vault", "oidc_jwt", 2): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "KID injection Vault I1 not in 33",
    },
    ("vault", "oidc_jwt", 3): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "num_uses=0 test setup issue",
    },
    ("vault", "oidc_jwt", 4): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Protected resource 403; setup",
    },
    ("vault", "oidc_jwt", 5): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Token accessor reuse cross-identity; Vault I2 not in 33",
    },
    ("vault", "oidc_jwt", 6): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Role TTL not enforced; Vault I2 not in 33",
    },
    ("vault", "oidc_jwt", 7): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Policy misbinding; setup",
    },
    ("vault", "oidc_jwt", 8): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Revocation 500 no namespace; setup",
    },
    ("vault", "oidc_jwt", 9): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Future-iat JWT bypass; Vault I2 not in 33",
    },
    ("vault", "oidc_jwt", 10): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "clock_skew_leeway ignored speculative",
    },
    ("vault", "oidc_jwt", 11): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "JWT key rotation stale trust; Vault I3 (VT-1 was removed)",
    },
    ("vault", "oidc_jwt", 12): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Role not found; setup",
    },
    ("vault", "oidc_jwt", 13): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4",
        "label": "TP", "reason": "VT-5/6",
        "desc_snippet": "Case-confusion sub (Admin vs admin) - matches VT-5/6 identity collision",
    },
    ("vault", "oidc_jwt", 14): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Empty sub 500 robustness; not in 33",
    },
    ("vault", "oidc_jwt", 15): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4",
        "label": "TP", "reason": "VT-5/6",
        "desc_snippet": "Literal-star sub collision - matches VT-5/6 identity alias collision",
    },
    ("vault", "oidc_jwt", 16): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4",
        "label": "TP", "reason": "VT-5/6",
        "desc_snippet": "Identity_claim switch email collision - matches VT-5/6",
    },
    ("vault", "oidc_jwt", 17): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4",
        "label": "TP", "reason": "VT-5/6",
        "desc_snippet": "Email identity_claim collision - matches VT-5/6",
    },

    # =========================================================================
    # zitadel / oidc_jwt  (17 findings)
    # =========================================================================
    ("zitadel", "oidc_jwt", 1): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "JWT IdP wrong aud accepted; UNEXPECTED/MEDIUM not rescued (I5 flaw)",
    },
    ("zitadel", "oidc_jwt", 2): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Missing kid test invalid; speculative",
    },
    ("zitadel", "oidc_jwt", 3): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token endpoint 500; robustness",
    },
    ("zitadel", "oidc_jwt", 4): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2",
        "label": "TP", "reason": "ZT-3",
        "desc_snippet": "JWT missing exp replay - matches ZT-3 exp/jwt/temporal",
    },
    ("zitadel", "oidc_jwt", 5): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "ctrl_user_id None; harness",
    },
    ("zitadel", "oidc_jwt", 6): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Missing iat bypass speculative hedge",
    },
    ("zitadel", "oidc_jwt", 7): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2",
        "label": "TP", "reason": "ZT-3",
        "desc_snippet": "Future-nbf accepted - matches ZT-3 temporal freshness",
    },
    ("zitadel", "oidc_jwt", 8): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent token CRYPTO-CRYPTO; setup",
    },
    ("zitadel", "oidc_jwt", 9): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Inconsistent intent IDs speculative",
    },
    ("zitadel", "oidc_jwt", 10): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "JWT IdP after disabled; Zitadel I3 not in 33",
    },
    ("zitadel", "oidc_jwt", 11): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Cleanup 404 inconsistent; setup",
    },
    ("zitadel", "oidc_jwt", 12): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent ID collision speculative",
    },
    ("zitadel", "oidc_jwt", 13): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Wrong aud accepted; UNEXPECTED/MEDIUM not rescued (speculative)",
    },
    ("zitadel", "oidc_jwt", 14): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "No linked user_id speculative",
    },
    ("zitadel", "oidc_jwt", 15): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Policy toggle bypass; not in 33",
    },
    ("zitadel", "oidc_jwt", 16): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Signature/JWKS not found; setup",
    },
    ("zitadel", "oidc_jwt", 17): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Cleanup 404 speculative",
    },

    # =========================================================================
    # zitadel / saml  (28 findings)
    # =========================================================================
    ("zitadel", "saml", 1): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1",
        "label": "TP", "reason": "ZT-1",
        "desc_snippet": "JWT IdP wrong audience accepted - matches ZT-1 aud/audience/jwt",
    },
    ("zitadel", "saml", 2): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML provider never created; setup",
    },
    ("zitadel", "saml", 3): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "500 for invalid IdpId; robustness",
    },
    ("zitadel", "saml", 4): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML failed but identity granted; harness",
    },
    ("zitadel", "saml", 5): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "IdP create failed; setup",
    },
    ("zitadel", "saml", 6): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2",
        "label": "TP", "reason": "ZT-3",
        "desc_snippet": "JWT IdP no exp reuse - matches ZT-3 exp/iat/temporal",
    },
    ("zitadel", "saml", 7): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2",
        "label": "TP", "reason": "ZT-3",
        "desc_snippet": "Replay same no-exp JWT - matches ZT-3 freshness",
    },
    ("zitadel", "saml", 8): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "SAML 400 but identity granted; harness",
    },
    ("zitadel", "saml", 9): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Both logins failed; replay untestable",
    },
    ("zitadel", "saml", 10): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent Token invalid; setup",
    },
    ("zitadel", "saml", 11): {
        "verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent IDs reused speculative",
    },
    ("zitadel", "saml", 12): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2",
        "label": "TP", "reason": "ZT-3",
        "desc_snippet": "Missing iat replay - matches ZT-3 iat/freshness",
    },
    ("zitadel", "saml", 13): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Policy toggle mid-flow stale; Zitadel I3 not in 33",
    },
    ("zitadel", "saml", 14): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "SAML IdP deleted mid-flow; Zitadel I3 not in 33",
    },
    ("zitadel", "saml", 15): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Identity granted despite SAML/OIDC failure; harness",
    },
    ("zitadel", "saml", 16): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "IdP cleanup 404 speculative",
    },
    ("zitadel", "saml", 17): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Session granted despite failures; Zitadel I3 not in 33",
    },
    ("zitadel", "saml", 18): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Policy update NotChanged; setup",
    },
    ("zitadel", "saml", 19): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent token invalid; setup",
    },
    ("zitadel", "saml", 20): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Inconsistent intent IDs speculative",
    },
    ("zitadel", "saml", 21): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Empty sub accepted; UNEXPECTED/MEDIUM not rescued",
    },
    ("zitadel", "saml", 22): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Missing session speculative",
    },
    ("zitadel", "saml", 23): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent token invalid 403; setup",
    },
    ("zitadel", "saml", 24): {
        "verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent ID reuse speculative",
    },
    ("zitadel", "saml", 25): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Token cross-session mix-up speculative",
    },
    ("zitadel", "saml", 26): {
        "verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5",
        "label": "FP", "reason": "not-in-33",
        "desc_snippet": "Attacker session granted despite 500; error-handling not in 33",
    },
    ("zitadel", "saml", 27): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Missing Conditions 500 robustness; not in 33",
    },
    ("zitadel", "saml", 28): {
        "verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5",
        "label": "FP", "reason": "unexpected-not-violation",
        "desc_snippet": "Intent Token invalid; setup",
    },
}


# =============================================================================
# Summary helpers
# =============================================================================

def summarize():
    total = len(TRIAGE)
    viol_tp = 0
    viol_fp_reasons = defaultdict(int)
    unex_total = 0
    unex_rescued_tp = 0
    flaws_found = defaultdict(int)
    tp_by_conf = defaultdict(int)
    for _, v in TRIAGE.items():
        if v["verdict"] == "VIOLATION":
            if v["label"] == "TP":
                viol_tp += 1
                flaws_found[v["reason"]] += 1
                tp_by_conf[v["conf"]] += 1
            else:
                viol_fp_reasons[v["reason"]] += 1
        else:  # UNEXPECTED
            unex_total += 1
            if v["label"] == "TP":
                unex_rescued_tp += 1
                flaws_found[v["reason"]] += 1
                tp_by_conf[v["conf"]] += 1
    violation_count = sum(1 for v in TRIAGE.values() if v["verdict"] == "VIOLATION")
    viol_fp_total = sum(viol_fp_reasons.values())
    tp_total = viol_tp + unex_rescued_tp

    print(f"=== {RUN} triage summary ===")
    print(f"Total findings: {total}")
    print(f"VIOLATION: {violation_count} (TP={viol_tp}, FP={viol_fp_total})")
    for reason, cnt in sorted(viol_fp_reasons.items()):
        print(f"    FP:{reason}: {cnt}")
    print(f"UNEXPECTED: {unex_total} (rescued-as-TP={unex_rescued_tp})")
    print(f"Total TPs: {tp_total}")
    print(f"Distinct flaws matched ({len(flaws_found)}):")
    for flaw, cnt in sorted(flaws_found.items()):
        print(f"    {flaw}: {cnt}")
    print(f"TP confidence distribution:")
    for conf in ("HIGH", "MEDIUM", "LOW"):
        print(f"    {conf}: {tp_by_conf.get(conf, 0)}")


if __name__ == "__main__":
    summarize()
