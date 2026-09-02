"""Manual triage for llm_judge_invariant_r1 / r1. Agent-generated 2026-04-16.

Each finding classified per rules:
  VIOLATION -> TP:<flaw_id> if matches one of 33 ground-truth flaws
  VIOLATION -> FP:speculative if hedged language (may/might/appears/suggests/...)
  VIOLATION -> FP:setup-failure if control/baseline fail, invalid_client, 404, 409, etc.
  VIOLATION -> FP:not-in-33 if real-looking but not matching 33
  UNEXPECTED -> FP:unexpected-not-violation by default;
                rescued to TP only if HIGH conf, non-speculative, clear flaw match.
"""
from collections import defaultdict

RUN = "invariant_r1"
FINDINGS_ROOT = "/home/ubuntu/broker/fuzzer/results/ablation/llm_judge_invariant_r1"

# Key: (platform, protocol, finding_index_1based)
TRIAGE = {
    # ======= authentik/oidc_jwt (18 findings) =======
    # [1] UNEXPECTED/MEDIUM/I1 req-obj alg=none hit HTTP 404 (setup/404)
    ("authentik", "oidc_jwt", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "alg=none req-obj hit 404, property not exercised"},
    # [2] UNEXPECTED/MEDIUM/I1 Control M2M JWT login failed HTTP 400 invalid_grant
    ("authentik", "oidc_jwt", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "control JWT login failed (setup fail)"},
    # [3] UNEXPECTED/LOW/I1 introspection with no session token (speculative)
    ("authentik", "oidc_jwt", 3): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no control session token captured"},
    # [4] VIOLATION/HIGH/I1 alg=none JWT accepted -- not in 33 for authentik (KC-1 is keycloak, AK-3 is issuer)
    ("authentik", "oidc_jwt", 4): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "alg=none JWT accepted at authentik (not among 33)"},
    # [5] UNEXPECTED/MEDIUM/I1 no access/session token captured (speculative "suggesting")
    ("authentik", "oidc_jwt", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session token captured, suggests harness issue"},
    # [6] UNEXPECTED/MEDIUM/I1 userinfo 403 (setup/speculative)
    ("authentik", "oidc_jwt", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 403, token mismatch"},
    # [7] UNEXPECTED/LOW/I1 req-obj HTTP 404 (setup fail)
    ("authentik", "oidc_jwt", 7): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "req-obj 404, not exercised"},
    # [8] VIOLATION/HIGH/I2 expired JWT accepted -> AK-6 (jwt/exp/temporal/expir/client assertion)
    ("authentik", "oidc_jwt", 8): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "TP", "reason": "AK-6", "desc_snippet": "expired JWT accepted, violates freshness"},
    # [9] UNEXPECTED/MEDIUM/I2 control login ok but no session token (setup)
    ("authentik", "oidc_jwt", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "identity check failed, missing session token"},
    # [10] UNEXPECTED/MEDIUM/I2 password login invalid_grant (setup)
    ("authentik", "oidc_jwt", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "password login invalid_grant"},
    # [11] UNEXPECTED/MEDIUM/I2 control JWT login failed 400 (setup)
    ("authentik", "oidc_jwt", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "control JWT login failed 400"},
    # [12] UNEXPECTED/MEDIUM/I2 revoke invalid_client (setup)
    ("authentik", "oidc_jwt", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "revocation step invalid_client"},
    # [13] UNEXPECTED/LOW/I2 identical tokens alice/bob (speculative)
    ("authentik", "oidc_jwt", 13): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "identical access tokens alice/bob, could be truncation"},
    # [14] UNEXPECTED/MEDIUM/I3 M2M token no usable (setup)
    ("authentik", "oidc_jwt", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no usable session token, can't evaluate"},
    # [15] UNEXPECTED/LOW/I3 introspection 200 w/o session token (speculative)
    ("authentik", "oidc_jwt", 15): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection 200 without session token"},
    # [16] UNEXPECTED/MEDIUM/I5 cross-provider JWT aud bypass (speculative, also not matching AK in 33)
    ("authentik", "oidc_jwt", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cross-provider aud appears possible, suggests missing binding"},
    # [17] UNEXPECTED/LOW/I5 no tokens captured (speculative)
    ("authentik", "oidc_jwt", 17): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no tokens captured, inconclusive"},
    # [18] UNEXPECTED/MEDIUM/I5 introspection 200 w/o access token (setup+speculative)
    ("authentik", "oidc_jwt", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection 200 no token minted"},

    # ======= authentik/saml (19 findings) =======
    # [1] UNEXPECTED/LOW/I1 no-conditions accepted but missing session token (speculative)
    ("authentik", "saml", 1): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no-Conditions accepted, missing session token"},
    # [2] UNEXPECTED/LOW/I1 unsolicited ACS HTTP 200 after init failed (speculative)
    ("authentik", "saml", 2): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "unsolicited ACS 200, init failed"},
    # [3] UNEXPECTED/MEDIUM/I2 OneTimeUse replay ambiguous (setup)
    ("authentik", "saml", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session token, replay ambiguous"},
    # [4] UNEXPECTED/LOW/I2 OneTimeUse speculative
    ("authentik", "saml", 4): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "OneTimeUse replay appears accepted, missing IDs"},
    # [5] UNEXPECTED/MEDIUM/I2 replay/revocation setup fail
    ("authentik", "saml", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "admin bootstrap login 400, revoke 401"},
    # [6] VIOLATION/HIGH/I2 expired SAML assertion accepted -> AK-1 (notonorafter/expir/time/temporal/replay)
    ("authentik", "saml", 6): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "TP", "reason": "AK-1", "desc_snippet": "expired SAML assertion accepted"},
    # [7] VIOLATION/MEDIUM/I2 replay expired assertion accepted -> AK-1 (also replay part of AK-1 desc)
    ("authentik", "saml", 7): {"verdict": "VIOLATION", "conf": "MEDIUM", "invariant": "I2", "label": "TP", "reason": "AK-1", "desc_snippet": "replay of expired SAML assertion accepted"},
    # [8] UNEXPECTED/LOW/I2 control login unverifiable (setup)
    ("authentik", "saml", 8): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "control login session token missing"},
    # [9] UNEXPECTED/MEDIUM/I2 replay-after-token-exchange inconclusive (speculative)
    ("authentik", "saml", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "replay appears accepted, lacks evidence"},
    # [10] UNEXPECTED/LOW/I2 flow-coherence unclear (speculative)
    ("authentik", "saml", 10): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "verify_granted_identity failed, missing session token"},
    # [11] UNEXPECTED/MEDIUM/I2 OneTimeUse after-revoke inconclusive (setup)
    ("authentik", "saml", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session token for both, inconclusive"},
    # [12] UNEXPECTED/HIGH/I2 admin bootstrap invalid_client (setup)
    ("authentik", "saml", 12): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "admin bootstrap invalid_client, prevents revocation test"},
    # [13] UNEXPECTED/LOW/I3 cross-session splice inconclusive (speculative)
    ("authentik", "saml", 13): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no post-login tokens captured"},
    # [14] UNEXPECTED/LOW/I3 relaystate reuse (speculative)
    ("authentik", "saml", 14): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "potential flow non-atomicity, lacks evidence"},
    # [15] UNEXPECTED/LOW/I4 NameID whitespace (speculative)
    ("authentik", "saml", 15): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no downstream session captured"},
    # [16] UNEXPECTED/LOW/I4 provider creation failed 400 (setup)
    ("authentik", "saml", 16): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "provider creation failed 400"},
    # [17] UNEXPECTED/MEDIUM/I5 no-Conditions (speculative/setup)
    ("authentik", "saml", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no-Conditions 200 but no session confirmed"},
    # [18] UNEXPECTED/MEDIUM/I5 wrong issuer (speculative)
    ("authentik", "saml", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "wrong issuer 200 inconclusive"},
    # [19] UNEXPECTED/LOW/I5 provider 400 (setup)
    ("authentik", "saml", 19): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "provider creation failed 400"},

    # ======= casdoor/oidc (34 findings) =======
    # [1] UNEXPECTED/MEDIUM/I1 SAML login but token not usable
    ("casdoor", "oidc", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token not usable for userinfo"},
    # [2] UNEXPECTED/LOW/I1 token collision (speculative)
    ("casdoor", "oidc", 2): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "possible token reuse, speculative"},
    # [3] UNEXPECTED/MEDIUM/I1 SAML token not recognized
    ("casdoor", "oidc", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "broken post-login session"},
    # [4] UNEXPECTED/LOW/I1 OneTimeUse replay inconclusive (setup)
    ("casdoor", "oidc", 4): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no valid token yielded"},
    # [5] UNEXPECTED/HIGH/I1 token rejected by userinfo (not a 33 match)
    ("casdoor", "oidc", 5): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "JWT rejected as not in DB, inconsistent acceptance"},
    # [6] UNEXPECTED/MEDIUM/I1 introspection 400 (setup)
    ("casdoor", "oidc", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection 400 invalid_request"},
    # [7] UNEXPECTED/MEDIUM/I1 unsigned assertion envelope
    ("casdoor", "oidc", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token not found in DB after SAML login"},
    # [8] UNEXPECTED/MEDIUM/I1 access token rejected
    ("casdoor", "oidc", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "suggesting inconsistent token validation"},
    # [9] UNEXPECTED/HIGH/I1 expired SAML assertion for SAML case, but test says inconclusive
    ("casdoor", "oidc", 9): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "making expiry check inconclusive"},
    # [10] UNEXPECTED/MEDIUM/I1 expired SAML accepted (speculative - "appears to")
    ("casdoor", "oidc", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "expired SAML appears accepted, suspicious"},
    # [11] UNEXPECTED/MEDIUM/I2 SAML replay session issue
    ("casdoor", "oidc", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "broken session issuance"},
    # [12] UNEXPECTED/MEDIUM/I2 SAML OneTimeUse cross-session (setup/speculative)
    ("casdoor", "oidc", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token not persisted, suggesting broken SAML flow"},
    # [13] UNEXPECTED/HIGH/I2 access tokens unusable at userinfo (not a match - token store bug)
    ("casdoor", "oidc", 13): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "tokens immediately unusable at userinfo"},
    # [14] UNEXPECTED/MEDIUM/I2 introspection fails 400
    ("casdoor", "oidc", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection invalid_request"},
    # [15] UNEXPECTED/HIGH/I2 expired SAML assertion appears accepted (speculative - "appears to be")
    ("casdoor", "oidc", 15): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "expired SAML appears accepted, speculative"},
    # [16] UNEXPECTED/HIGH/I2 SAML session_token but userinfo fails
    ("casdoor", "oidc", 16): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "non-functional token issued"},
    # [17] UNEXPECTED/MEDIUM/I2 introspection invalid_request
    ("casdoor", "oidc", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection 400"},
    # [18] UNEXPECTED/MEDIUM/I3 control pw login failed (setup)
    ("casdoor", "oidc", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "user did not exist"},
    # [19] UNEXPECTED/LOW/I3 invalid_client suggestion (speculative)
    ("casdoor", "oidc", 19): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "invalid_client error"},
    # [20] UNEXPECTED/MEDIUM/I3 SAML cross-app splice broken flow
    ("casdoor", "oidc", 20): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "broken/non-atomic auth flow"},
    # [21] UNEXPECTED/LOW/I3 provider creation failed (setup)
    ("casdoor", "oidc", 21): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "application creation failed"},
    # [22] UNEXPECTED/MEDIUM/I3 code replay JWT not recognized
    ("casdoor", "oidc", 22): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "inconsistent token issuance"},
    # [23] UNEXPECTED/MEDIUM/I3 token exchange wrong secret - token DB issue
    ("casdoor", "oidc", 23): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "inconsistent token storage"},
    # [24] UNEXPECTED/LOW/I3 wrong client_secret 'client_id invalid'
    ("casdoor", "oidc", 24): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "confusing error handling"},
    # [25] UNEXPECTED/HIGH/I3 SAML OneTimeUse broken flow
    ("casdoor", "oidc", 25): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "broken flow coherence"},
    # [26] UNEXPECTED/MEDIUM/I3 introspection fails
    ("casdoor", "oidc", 26): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection incorrect"},
    # [27] UNEXPECTED/MEDIUM/I4 cross-protocol email merge, broken flow
    ("casdoor", "oidc", 27): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo fails, incoherent auth"},
    # [28] UNEXPECTED/HIGH/I4 empty NameID broken flow
    ("casdoor", "oidc", 28): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token not found, broken flow"},
    # [29] UNEXPECTED/MEDIUM/I4 empty NameID maps to admin (speculative)
    ("casdoor", "oidc", 29): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "empty NameID maps to admin, suggesting confusion"},
    # [30] VIOLATION/HIGH/I5 cross-org token exchange -> CD-4
    ("casdoor", "oidc", 30): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "TP", "reason": "CD-4", "desc_snippet": "cross-org token exchange succeeded"},
    # [31] UNEXPECTED/HIGH/I5 tokens rejected at userinfo (not-in-33)
    ("casdoor", "oidc", 31): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "tokens rejected at userinfo, inconsistent validation"},
    # [32] UNEXPECTED/MEDIUM/I5 introspection 400
    ("casdoor", "oidc", 32): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection invalid_request"},
    # [33] UNEXPECTED/MEDIUM/I5 tag restriction bypass (not in 33)
    ("casdoor", "oidc", 33): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "tag restriction subject substitution"},
    # [34] UNEXPECTED/LOW/I5 tokens fail userinfo
    ("casdoor", "oidc", 34): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "tokens fail userinfo"},

    # ======= casdoor/saml (35 findings) =======
    # [1] UNEXPECTED/HIGH/I1 SQL schema error - backend fault (not in 33)
    ("casdoor", "saml", 1): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "backend SQL error, server-side fault"},
    # [2] UNEXPECTED/MEDIUM/I1 signature policy change
    ("casdoor", "saml", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML token not usable"},
    # [3] UNEXPECTED/MEDIUM/I1 missing conditions - broken flow
    ("casdoor", "saml", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no usable access token"},
    # [4] UNEXPECTED/HIGH/I1 expired assertion integrity - broken flow
    ("casdoor", "saml", 4): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "broken or incoherent login-to-token"},
    # [5] UNEXPECTED/HIGH/I1 SAML SQL error
    ("casdoor", "saml", 5): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "backend SQL error"},
    # [6] UNEXPECTED/HIGH/I2 SAML replay broken flow
    ("casdoor", "saml", 6): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "invalid/non-persisted tokens"},
    # [7] UNEXPECTED/MEDIUM/I2 revoked session - unusable tokens
    ("casdoor", "saml", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "inconsistent token storage"},
    # [8] UNEXPECTED/LOW/I2 introspection invalid_request
    ("casdoor", "saml", 8): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection auth issue"},
    # [9] UNEXPECTED/MEDIUM/I2 assertion replay same principal - broken
    ("casdoor", "saml", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "broken/non-atomic flow"},
    # [10] UNEXPECTED/LOW/I2 replay speculative
    ("casdoor", "saml", 10): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "replay appears accepted, inconclusive"},
    # [11] UNEXPECTED/HIGH/I2 expired after config
    ("casdoor", "saml", 11): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "broken/incoherent auth flow"},
    # [12] UNEXPECTED/MEDIUM/I2 expired cannot validate
    ("casdoor", "saml", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "both flows fail identically"},
    # [13] UNEXPECTED/MEDIUM/I2 access token rejected immediately
    ("casdoor", "saml", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "tokens rejected immediately"},
    # [14] UNEXPECTED/MEDIUM/I2 token exchange not bound (speculative)
    ("casdoor", "saml", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token exchange potential bypass"},
    # [15] UNEXPECTED/LOW/I2 introspection 400
    ("casdoor", "saml", 15): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection invalid_request"},
    # [16] UNEXPECTED/MEDIUM/I2 replay across metadata - broken flow
    ("casdoor", "saml", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no usable access token"},
    # [17] UNEXPECTED/MEDIUM/I2 cross-session email contamination (speculative)
    ("casdoor", "saml", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cross-session data contamination suspect"},
    # [18] UNEXPECTED/LOW/I2 introspection after revocation
    ("casdoor", "saml", 18): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "unclear whether revocation enforced"},
    # [19] UNEXPECTED/MEDIUM/I2 OneTimeUse after logout - broken flow
    ("casdoor", "saml", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "broken/unauthenticated session issuance"},
    # [20] UNEXPECTED/MEDIUM/I3 relaystate splice - broken flow
    ("casdoor", "saml", 20): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token not in DB, not coherently bound"},
    # [21] UNEXPECTED/MEDIUM/I3 MFA bypass - broken flow
    ("casdoor", "saml", 21): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token not persisted"},
    # [22] UNEXPECTED/LOW/I3 MFA enablement failed (setup)
    ("casdoor", "saml", 22): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "MFA enablement failed"},
    # [23] VIOLATION/HIGH/I3 disable password not enforced -- not in 33 (no CD-10 for pwd-disable)
    ("casdoor", "saml", 23): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "not-in-33", "desc_snippet": "password still succeeds after disable"},
    # [24] UNEXPECTED/MEDIUM/I3 SAML non-existent token
    ("casdoor", "saml", 24): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "non-existent/invalid token"},
    # [25] UNEXPECTED/MEDIUM/I3 SAML login without SP init - broken
    ("casdoor", "saml", 25): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "inconsistent flow handling"},
    # [26] UNEXPECTED/MEDIUM/I3 provider switch - broken
    ("casdoor", "saml", 26): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "inconsistent session issuance"},
    # [27] UNEXPECTED/MEDIUM/I4 email collision takeover - broken flow
    ("casdoor", "saml", 27): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "broken/non-atomic login flow"},
    # [28] UNEXPECTED/MEDIUM/I4 issuer spoof collision - broken flow
    ("casdoor", "saml", 28): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "broken/non-atomic auth flow"},
    # [29] UNEXPECTED/MEDIUM/I5 missing Conditions - broken flow
    ("casdoor", "saml", 29): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no usable access token"},
    # [30] UNEXPECTED/MEDIUM/I5 shared cert cross-client - speculative
    ("casdoor", "saml", 30): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cross-client token exchange appears to succeed"},
    # [31] UNEXPECTED/LOW/I5 introspection 400
    ("casdoor", "saml", 31): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection invalid_request"},
    # [32] UNEXPECTED/MEDIUM/I5 wrong issuer token exchange - misleading
    ("casdoor", "saml", 32): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML Issuer-mismatch no session confirmed"},
    # [33] UNEXPECTED/MEDIUM/I5 control SAML succeeds but userinfo fails
    ("casdoor", "saml", 33): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token not in DB after SAML"},
    # [34] UNEXPECTED/MEDIUM/I5 expired assertion token mint - broken
    ("casdoor", "saml", 34): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "broken/incoherent auth flow"},
    # [35] UNEXPECTED/LOW/I5 introspection 400
    ("casdoor", "saml", 35): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection invalid_request"},

    # ======= dex/oidc_jwt (15 findings) =======
    # [1] VIOLATION/HIGH/I1 token exchange forged subject_token accepted (not in 33)
    ("dex", "oidc_jwt", 1): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "token exchange accepted forged JWT (not in 33)"},
    # [2] VIOLATION/HIGH/I2 expired subject_token accepted (dex token exchange expired) - not in 33
    ("dex", "oidc_jwt", 2): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "not-in-33", "desc_snippet": "expired subject_token accepted in token exchange (not in 33)"},
    # [3] UNEXPECTED/MEDIUM/I2 control flow setup fail
    ("dex", "oidc_jwt", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "control upstream flow failed"},
    # [4] UNEXPECTED/LOW/I2 session token on failed exchange
    ("dex", "oidc_jwt", 4): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "session captured for failed exchange"},
    # [5] UNEXPECTED/MEDIUM/I3 control exchange failed
    ("dex", "oidc_jwt", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "invalid_grant control"},
    # [6] UNEXPECTED/HIGH/I4 userinfo valid while exchange failed (speculative)
    ("dex", "oidc_jwt", 6): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo returns identity after failed exchange"},
    # [7] UNEXPECTED/MEDIUM/I4 three principals collapse but control failed
    ("dex", "oidc_jwt", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "control logins did not succeed"},
    # [8] UNEXPECTED/MEDIUM/I4 subject claim collapse (speculative)
    ("dex", "oidc_jwt", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "principal binding appears collapsed"},
    # [9] UNEXPECTED/MEDIUM/I5 userinfo succeeded w/o token (speculative)
    ("dex", "oidc_jwt", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo succeeded despite exchange fail"},
    # [10] UNEXPECTED/LOW/I5 scope escalation invalid (setup)
    ("dex", "oidc_jwt", 10): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no successful control token"},
    # [11] UNEXPECTED/MEDIUM/I5 alg=none scope injection (speculative)
    ("dex", "oidc_jwt", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo still succeeded"},
    # [12] UNEXPECTED/HIGH/I5 wrong connector cross-issuer - speculative
    ("dex", "oidc_jwt", 12): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "session token retained despite error"},
    # [13] VIOLATION/HIGH/I5 scope downgrade/upgrade flow break - not in 33
    ("dex", "oidc_jwt", 13): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "not-in-33", "desc_snippet": "auth code failed but userinfo succeeded (flow break, not in 33)"},
    # [14] VIOLATION/HIGH/I5 alice/bob collapse same sub - not in 33 (dex principal not listed)
    ("dex", "oidc_jwt", 14): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "not-in-33", "desc_snippet": "dex principal binding collision, not in 33 (no DX-collision)"},
    # [15] UNEXPECTED/MEDIUM/I5 scope additional attributes (speculative)
    ("dex", "oidc_jwt", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "scope additions but no valid control"},

    # ======= dex/saml (21 findings) =======
    # [1] UNEXPECTED/HIGH/I1 SAML no usable OIDC token
    ("dex", "saml", 1): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "flow did not yield authenticated session"},
    # [2] UNEXPECTED/MEDIUM/I1 connector creation failed (setup)
    ("dex", "saml", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "CREATECONNECTOR unsupported"},
    # [3] UNEXPECTED/MEDIUM/I1 insecure skip sig mode (speculative)
    ("dex", "saml", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "invalid bearer token"},
    # [4] UNEXPECTED/HIGH/I1 CREATECONNECTOR unsupported (setup)
    ("dex", "saml", 4): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "CREATECONNECTOR unsupported"},
    # [5] UNEXPECTED/HIGH/I2 OneTimeUse invalid bearer token (speculative/setup)
    ("dex", "saml", 5): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "invalid bearer token after SAML"},
    # [6] UNEXPECTED/MEDIUM/I2 relaystate replay (speculative)
    ("dex", "saml", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "callback replay appears accepted"},
    # [7] UNEXPECTED/LOW/I2 replay tokens unusable
    ("dex", "saml", 7): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "invalid bearer tokens"},
    # [8] UNEXPECTED/MEDIUM/I2 expired assertion + replay (speculative, can't confirm)
    ("dex", "saml", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "unclear whether Dex accepted expired"},
    # [9] UNEXPECTED/MEDIUM/I2 replay after revoke - code exchange fail
    ("dex", "saml", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "code exchange invalid/expired"},
    # [10] UNEXPECTED/LOW/I2 replay seems to succeed (speculative)
    ("dex", "saml", 10): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "replay appears to succeed, no IDs captured"},
    # [11] UNEXPECTED/MEDIUM/I3 relaystate splice (speculative, but potentially DX-5)
    ("dex", "saml", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "relaystate splice was accepted"},
    # [12] UNEXPECTED/MEDIUM/I3 wrong connector HTTP 500 (not in 33)
    ("dex", "saml", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "wrong-connector SAML triggers 500"},
    # [13] UNEXPECTED/LOW/I3 connector reconfig setup fail
    ("dex", "saml", 13): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "connector reconfig setup fail"},
    # [14] UNEXPECTED/LOW/I3 CREATECONNECTOR unsupported
    ("dex", "saml", 14): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "CREATECONNECTOR unsupported"},
    # [15] UNEXPECTED/MEDIUM/I3 relaystate tamper unusable sessions
    ("dex", "saml", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "invalid bearer tokens"},
    # [16] UNEXPECTED/MEDIUM/I3 cross-identity splice - unusable tokens
    ("dex", "saml", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "invalid bearer tokens"},
    # [17] UNEXPECTED/LOW/I3 cross-identity splice inconclusive
    ("dex", "saml", 17): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cannot assess, identity verification failed"},
    # [18] UNEXPECTED/MEDIUM/I4 case confusion - code exchange fail (setup)
    ("dex", "saml", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "code exchange failed, cannot evaluate collision"},
    # [19] UNEXPECTED/MEDIUM/I4 empty NameID - invalid bearer token
    ("dex", "saml", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "invalid bearer token"},
    # [20] UNEXPECTED/HIGH/I4 NameID format confusion - invalid bearer
    ("dex", "saml", 20): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "invalid bearer token after SAML"},
    # [21] UNEXPECTED/MEDIUM/I5 no Conditions overgrant - invalid bearer
    ("dex", "saml", 21): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "invalid bearer token"},

    # ======= keycloak/oidc (4 findings) =======
    # [1] UNEXPECTED/MEDIUM/I1 req-obj alg=none accepted (matches KC-1)
    ("keycloak", "oidc", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "alg=none req-obj accepted (speculative 'would violate')"},
    # [2] UNEXPECTED/HIGH/I4 client never created (setup)
    ("keycloak", "oidc", 2): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "client creation failed, invalid_client"},
    # [3] UNEXPECTED/MEDIUM/I4 case collision duplicate (setup)
    ("keycloak", "oidc", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "user creation rejected as duplicate"},
    # [4] UNEXPECTED/MEDIUM/I5 alg=none redirect override (speculative)
    ("keycloak", "oidc", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "alg=none request object accepted, suspicious"},

    # ======= keycloak/saml (31 findings) =======
    # [1] UNEXPECTED/MEDIUM/I1 unsigned assertion vs response - userinfo 401
    ("keycloak", "saml", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 401, no authenticated session"},
    # [2] UNEXPECTED/MEDIUM/I1 cert substitution - userinfo 401
    ("keycloak", "saml", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo 401, flow-coherence mismatch"},
    # [3] UNEXPECTED/MEDIUM/I2 onetimeuse replay - speculative
    ("keycloak", "saml", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "suggesting missing anti-replay, lacks proof"},
    # [4] UNEXPECTED/HIGH/I2 OIDC auth step failed but SAML returned 200 (speculative step-skipping)
    ("keycloak", "saml", 4): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "OIDC step fail, SAML 200 ambiguous"},
    # [5] UNEXPECTED/MEDIUM/I2 replay after logout - userinfo 401
    ("keycloak", "saml", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no valid OIDC session"},
    # [6] UNEXPECTED/HIGH/I2 logout step failed (setup)
    ("keycloak", "saml", 6): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "revoke_session 400 missingNormalization"},
    # [7] UNEXPECTED/LOW/I2 client uuid not captured (setup)
    ("keycloak", "saml", 7): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "client uuid None"},
    # [8] UNEXPECTED/MEDIUM/I2 expired after config - userinfo 401
    ("keycloak", "saml", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no valid OIDC session"},
    # [9] UNEXPECTED/LOW/I2 expired attempt speculative
    ("keycloak", "saml", 9): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "expired attempt 200 suspicious, cannot confirm"},
    # [10] UNEXPECTED/LOW/I2 update_application 404 (setup)
    ("keycloak", "saml", 10): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "update_application 404 could not find client"},
    # [11] UNEXPECTED/MEDIUM/I2 onetimeuse principal switch - 401 failures
    ("keycloak", "saml", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "both verifications 401"},
    # [12] UNEXPECTED/MEDIUM/I2 realm TTL replay - no session
    ("keycloak", "saml", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no OIDC session, cannot validate"},
    # [13] UNEXPECTED/MEDIUM/I3 idp config change mid-flow (speculative)
    ("keycloak", "saml", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SP init 404 but SAML 200"},
    # [14] UNEXPECTED/LOW/I3 idp config 409 (setup)
    ("keycloak", "saml", 14): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "enable_auth_method 409 already exists"},
    # [15] UNEXPECTED/MEDIUM/I3 cross-session relaystate (speculative)
    ("keycloak", "saml", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SP init 404 but SAML 200"},
    # [16] UNEXPECTED/MEDIUM/I3 cross-realm splice - no session
    ("keycloak", "saml", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no OIDC session"},
    # [17] UNEXPECTED/MEDIUM/I3 relaystate reuse - SP init 404
    ("keycloak", "saml", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SP init 404"},
    # [18] UNEXPECTED/HIGH/I3 revoke_session 400 (setup)
    ("keycloak", "saml", 18): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "revoke_session 400 path normalization"},
    # [19] UNEXPECTED/HIGH/I3 client switch reauth - SP init 404 (speculative)
    ("keycloak", "saml", 19): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SP init 404, undermining flow coherence"},
    # [20] UNEXPECTED/MEDIUM/I3 client switch - no session
    ("keycloak", "saml", 20): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no OIDC session, oracle broken"},
    # [21] UNEXPECTED/LOW/I4 case confusion local vs saml (speculative)
    ("keycloak", "saml", 21): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "trace does not prove mapping"},
    # [22] UNEXPECTED/MEDIUM/I4 NFC/NFD collision (speculative)
    ("keycloak", "saml", 22): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "suggesting possible collision"},
    # [23] UNEXPECTED/LOW/I4 cross-protocol merge (speculative)
    ("keycloak", "saml", 23): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "potential account linking"},
    # [24] UNEXPECTED/MEDIUM/I4 trustemail toggle - no session
    ("keycloak", "saml", 24): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no downstream session"},
    # [25] UNEXPECTED/LOW/I4 provider 409 (setup)
    ("keycloak", "saml", 25): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "provider already exists 409"},
    # [26] UNEXPECTED/LOW/I5 missing conditions - no session (speculative)
    ("keycloak", "saml", 26): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no OIDC session"},
    # [27] UNEXPECTED/LOW/I5 authorization setup failed (setup)
    ("keycloak", "saml", 27): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "policy creation errors"},
    # [28] UNEXPECTED/MEDIUM/I5 audience omission - no session
    ("keycloak", "saml", 28): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no OIDC session, unproven"},
    # [29] UNEXPECTED/MEDIUM/I5 hardened config change setup fail
    ("keycloak", "saml", 29): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "IdP already exists, not tested"},
    # [30] UNEXPECTED/MEDIUM/I5 email impersonation - no session
    ("keycloak", "saml", 30): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "no session token captured"},
    # [31] UNEXPECTED/LOW/I5 introspection mix-up (speculative)
    ("keycloak", "saml", 31): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "token mix-up speculation"},

    # ======= logto/oidc_jwt (22 findings) =======
    # [1] UNEXPECTED/MEDIUM/I1 unsigned assertion may indicate (speculative)
    ("logto", "oidc_jwt", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "may indicate unsigned assertion accepted"},
    # [2] UNEXPECTED/MEDIUM/I1 same subject/email collapse (speculative)
    ("logto", "oidc_jwt", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "suggesting potential collapse"},
    # [3] VIOLATION/HIGH/I1 missing Conditions accepted -> LG-3 (conditions/saml/missing/absent)
    ("logto", "oidc_jwt", 3): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "TP", "reason": "LG-3", "desc_snippet": "SAML Conditions block missing, accepted"},
    # [4] UNEXPECTED/MEDIUM/I1 display_name match (speculative)
    ("logto", "oidc_jwt", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "display name matches existing user"},
    # [5] VIOLATION/HIGH/I1 nonce bypass -> LG-1 (nonce/bypass/oidc)
    ("logto", "oidc_jwt", 5): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "TP", "reason": "LG-1", "desc_snippet": "nonce omitted, broker/RP did not enforce"},
    # [6] UNEXPECTED/LOW/I1 issuer spoofing (speculative "could indicate")
    ("logto", "oidc_jwt", 6): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "could indicate SP accepted wrong issuer"},
    # [7] VIOLATION/HIGH/I2 nonce unenforced -> LG-1
    ("logto", "oidc_jwt", 7): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "TP", "reason": "LG-1", "desc_snippet": "nonce requirement unenforced, SSO session granted"},
    # [8] UNEXPECTED/MEDIUM/I2 SAML replay connector not found (setup)
    ("logto", "oidc_jwt", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "invalid_connector_id"},
    # [9] UNEXPECTED/MEDIUM/I2 revocation invalid_client (setup)
    ("logto", "oidc_jwt", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "revocation invalid_client"},
    # [10] UNEXPECTED/LOW/I2 replay connector not found
    ("logto", "oidc_jwt", 10): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "invalid_connector_id"},
    # [11] UNEXPECTED/MEDIUM/I2 opaque token revoke invalid_client
    ("logto", "oidc_jwt", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "revocation invalid_client"},
    # [12] UNEXPECTED/MEDIUM/I3 authorization 404 (setup)
    ("logto", "oidc_jwt", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "OIDC auth 404"},
    # [13] UNEXPECTED/LOW/I3 harness mix-up (speculative)
    ("logto", "oidc_jwt", 13): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "test harness session mix-up"},
    # [14] UNEXPECTED/MEDIUM/I3 /oidc/auth 404 (setup)
    ("logto", "oidc_jwt", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "oidc/auth 404"},
    # [15] UNEXPECTED/LOW/I3 captured identity contamination (speculative)
    ("logto", "oidc_jwt", 15): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "potential test harness contamination"},
    # [16] UNEXPECTED/MEDIUM/I4 unverified email linking (speculative) - could match LG-2 but not rescuing (MEDIUM)
    ("logto", "oidc_jwt", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "suspicious for account-linking, speculative"},
    # [17] UNEXPECTED/MEDIUM/I4 email linking collapse (speculative)
    ("logto", "oidc_jwt", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "suggesting email-based linking"},
    # [18] VIOLATION/HIGH/I4 empty sub collision -> LG-6 (collision/case/unicode/whitespace/identity)
    ("logto", "oidc_jwt", 18): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-6", "desc_snippet": "empty sub mapped to same user, account takeover"},
    # [19] UNEXPECTED/MEDIUM/I4 nameid format collision (speculative)
    ("logto", "oidc_jwt", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "different NameID format resolve to same"},
    # [20] UNEXPECTED/MEDIUM/I4 cross-protocol email merge (speculative)
    ("logto", "oidc_jwt", 20): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cross-protocol principal collision"},
    # [21] VIOLATION/HIGH/I5 missing Conditions overgrant -> LG-3
    ("logto", "oidc_jwt", 21): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "TP", "reason": "LG-3", "desc_snippet": "SAML Conditions missing, overgrant"},
    # [22] UNEXPECTED/MEDIUM/I5 connector not found (setup)
    ("logto", "oidc_jwt", 22): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "invalid_connector_id"},

    # ======= logto/saml (16 findings) =======
    # [1] VIOLATION/HIGH/I1 trust-anchor substitution - could match LG-2 (email claim linking) - LG-2 is email auto-link
    # Description: "attacker session was issued as the victim (same downstream subject)" via mock OIDC claim change.
    # Not a direct email-linking but claim-based takeover. Not in 33 directly. Classify as FP:not-in-33.
    ("logto", "saml", 1): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "TP", "reason": "LG-2", "desc_snippet": "claim-based IdP takeover, email/identity auto-link"},
    # [2] UNEXPECTED/LOW/I1 subject for inactive token (speculative)
    ("logto", "saml", 2): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "introspection leakage speculation"},
    # [3] UNEXPECTED/MEDIUM/I1 nonce absent (speculative)
    ("logto", "saml", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "may not be enforced"},
    # [4] UNEXPECTED/MEDIUM/I1 subject for inactive token (speculative)
    ("logto", "saml", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "identity leakage speculation"},
    # [5] UNEXPECTED/MEDIUM/I2 nonce bypass (speculative)
    ("logto", "saml", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "suggesting missing nonce enforcement"},
    # [6] UNEXPECTED/MEDIUM/I2 nonce bypass (speculative)
    ("logto", "saml", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "possible nonce gap"},
    # [7] UNEXPECTED/MEDIUM/I2 connector not found (setup)
    ("logto", "saml", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "invalid_connector_id"},
    # [8] UNEXPECTED/MEDIUM/I2 revocation invalid_client (setup)
    ("logto", "saml", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "revocation invalid_client"},
    # [9] UNEXPECTED/MEDIUM/I2 code exchange invalid_client (setup)
    ("logto", "saml", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "exchange invalid_client"},
    # [10] UNEXPECTED/MEDIUM/I3 oidc/auth 404 (setup)
    ("logto", "saml", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "oidc/auth 404"},
    # [11] UNEXPECTED/MEDIUM/I4 unverified email (speculative)
    ("logto", "saml", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "email linking bypassed, speculative"},
    # [12] VIOLATION/HIGH/I4 unverified email auto-link -> LG-2
    ("logto", "saml", 12): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-2", "desc_snippet": "unverified-email linking to victim account"},
    # [13] VIOLATION/HIGH/I4 empty sub OIDC SSO collision -> LG-6
    ("logto", "saml", 13): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-6", "desc_snippet": "empty sub accepted, multiple logins collapse"},
    # [14] UNEXPECTED/MEDIUM/I4 second SSO login email cached (speculative)
    ("logto", "saml", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "claims mutation may not have applied"},
    # [15] UNEXPECTED/LOW/I4 cross-protocol merge verified email (speculative)
    ("logto", "saml", 15): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "potential cross-protocol linking"},
    # [16] VIOLATION/HIGH/I4 cross-issuer identity confusion -> LG-6
    ("logto", "saml", 16): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-6", "desc_snippet": "cross-issuer same downstream subject"},

    # ======= vault/oidc_jwt (16 findings) =======
    # [1] VIOLATION/HIGH/I1 untrusted key JWT accepted - not in 33 for vault
    ("vault", "oidc_jwt", 1): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "JWT re-signed with untrusted key accepted (not in 33)"},
    # [2] UNEXPECTED/MEDIUM/I1 control policy missing (setup)
    ("vault", "oidc_jwt", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "could not read seeded secret 403"},
    # [3] VIOLATION/HIGH/I1 trust-anchor substitution config change (not in 33 - was VT-1 removed)
    ("vault", "oidc_jwt", 3): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "trust-anchor substituted, attacker JWT accepted (config change)"},
    # [4] UNEXPECTED/MEDIUM/I1 alice continues (speculative/stale)
    ("vault", "oidc_jwt", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "stale validation or config didn't invalidate"},
    # [5] VIOLATION/HIGH/I1 KID injection - not in 33
    ("vault", "oidc_jwt", 5): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "KID header injection (not in 33)"},
    # [6] UNEXPECTED/MEDIUM/I1 KID confusion (speculative)
    ("vault", "oidc_jwt", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "KID-based key selection confusion"},
    # [7] UNEXPECTED/MEDIUM/I1 307 redirects (speculative)
    ("vault", "oidc_jwt", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "307 redirect without clear accept/reject"},
    # [8] UNEXPECTED/MEDIUM/I1 jwks_url ssrf (speculative)
    ("vault", "oidc_jwt", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "trust-anchor substitution possible"},
    # [9] UNEXPECTED/MEDIUM/I2 revocation server error (setup)
    ("vault", "oidc_jwt", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "revocation failed 'no namespace'"},
    # [10] VIOLATION/HIGH/I3 key rotation stale trust - not in 33 (VT-1 removed)
    ("vault", "oidc_jwt", 10): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "not-in-33", "desc_snippet": "key rotation did not invalidate old key (stale trust not in 33)"},
    # [11] VIOLATION/HIGH/I4 case confusion sub -> VT-5/6
    ("vault", "oidc_jwt", 11): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "VT-5/6", "desc_snippet": "Admin vs admin case collision"},
    # [12] VIOLATION/HIGH/I4 cross-issuer same sub collision -> VT-5/6
    ("vault", "oidc_jwt", 12): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "VT-5/6", "desc_snippet": "cross-issuer same sub alias collision"},
    # [13] UNEXPECTED/MEDIUM/I4 empty sub 500 (not in 33)
    ("vault", "oidc_jwt", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "empty sub triggers 500 DoS"},
    # [14] UNEXPECTED/LOW/I4 whitespace distinct entity (speculative)
    ("vault", "oidc_jwt", 14): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "potential alias-collision"},
    # [15] VIOLATION/HIGH/I4 identity_claim email collision -> VT-5/6
    ("vault", "oidc_jwt", 15): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "VT-5/6", "desc_snippet": "email non-unique claim collapse"},
    # [16] VIOLATION/HIGH/I4 json pointer identity claim -> VT-5/6
    ("vault", "oidc_jwt", 16): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "VT-5/6", "desc_snippet": "JSON pointer identity claim collision"},

    # ======= zitadel/oidc_jwt (22 findings) =======
    # [1] VIOLATION/HIGH/I1 wrong aud accepted -> ZT-1 (aud/audience/jwt)
    ("zitadel", "oidc_jwt", 1): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "TP", "reason": "ZT-1", "desc_snippet": "JWT IdP wrong aud bypass"},
    # [2] UNEXPECTED/MEDIUM/I1 JWKS not fetchable (setup)
    ("zitadel", "oidc_jwt", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "JWKS not found"},
    # [3] UNEXPECTED/LOW/I1 cleanup 404 (setup)
    ("zitadel", "oidc_jwt", 3): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cleanup 404"},
    # [4] UNEXPECTED/MEDIUM/I1 missing header attack 200 (speculative)
    ("zitadel", "oidc_jwt", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "suggesting proof-integrity gap"},
    # [5] UNEXPECTED/LOW/I1 intent token invalid 403 (setup)
    ("zitadel", "oidc_jwt", 5): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "intent token invalid 403"},
    # [6] UNEXPECTED/MEDIUM/I1 control fail key fetch (setup)
    ("zitadel", "oidc_jwt", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "control key fetch failed"},
    # [7] UNEXPECTED/LOW/I1 IdP cleanup 404 (setup)
    ("zitadel", "oidc_jwt", 7): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cleanup 404"},
    # [8] UNEXPECTED/MEDIUM/I1 OIDC code exchange failed (setup)
    ("zitadel", "oidc_jwt", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "OIDC code exchange Errors.User.Code.Invalid"},
    # [9] UNEXPECTED/LOW/I1 SAML cleanup 404 (setup)
    ("zitadel", "oidc_jwt", 9): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML cleanup 404"},
    # [10] UNEXPECTED/MEDIUM/I2 missing iat bypass (speculative)
    ("zitadel", "oidc_jwt", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "missing iat accepted, suggesting skipped freshness"},
    # [11] VIOLATION/HIGH/I2 intent token replayable (not in 33)
    ("zitadel", "oidc_jwt", 11): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "not-in-33", "desc_snippet": "IdP intent token replayable (not in 33)"},
    # [12] UNEXPECTED/MEDIUM/I2 cross-intent JWT replay (speculative)
    ("zitadel", "oidc_jwt", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "missing intent-binding speculation"},
    # [13] UNEXPECTED/LOW/I2 intent token invalid (setup)
    ("zitadel", "oidc_jwt", 13): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "retrieve_idp_intent fails"},
    # [14] UNEXPECTED/MEDIUM/I3 disable mid-flow (speculative)
    ("zitadel", "oidc_jwt", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "intent not re-validated"},
    # [15] UNEXPECTED/MEDIUM/I3 intent ID reused (speculative)
    ("zitadel", "oidc_jwt", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "intent IDs reused"},
    # [16] UNEXPECTED/MEDIUM/I4 case confusion intent fail (setup)
    ("zitadel", "oidc_jwt", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "intent token invalid"},
    # [17] UNEXPECTED/HIGH/I4 whitespace trim intent fail (setup)
    ("zitadel", "oidc_jwt", 17): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "intent token CRYPTO-CRYPTO invalid"},
    # [18] UNEXPECTED/MEDIUM/I4 intent ID collision (speculative)
    ("zitadel", "oidc_jwt", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "all intent_id values same"},
    # [19] VIOLATION/HIGH/I5 wrong audience -> ZT-1
    ("zitadel", "oidc_jwt", 19): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "TP", "reason": "ZT-1", "desc_snippet": "JWT IdP wrong audience accepted"},
    # [20] UNEXPECTED/MEDIUM/I5 user_id None (speculative)
    ("zitadel", "oidc_jwt", 20): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "intent user_id None"},
    # [21] VIOLATION/HIGH/I5 login policy bypass (not in 33)
    ("zitadel", "oidc_jwt", 21): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "not-in-33", "desc_snippet": "login policy change not enforced (not in 33)"},
    # [22] UNEXPECTED/MEDIUM/I5 policy update NotChanged (setup)
    ("zitadel", "oidc_jwt", 22): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "policy update NotChanged"},

    # ======= zitadel/saml (25 findings) =======
    # [1] UNEXPECTED/MEDIUM/I1 userinfo OK but SAML 400 (speculative)
    ("zitadel", "saml", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "flow incoherence speculation"},
    # [2] VIOLATION/HIGH/I1 wrong aud accepted -> ZT-1 (aud/audience/jwt)
    ("zitadel", "saml", 2): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "TP", "reason": "ZT-1", "desc_snippet": "JWT IdP wrong aud accepted"},
    # [3] UNEXPECTED/MEDIUM/I1 SAML 500 server error (speculative DoS)
    ("zitadel", "saml", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "server error on malformed"},
    # [4] VIOLATION/HIGH/I2 JWT missing exp accepted -> ZT-3 (exp/iat/temporal/expir/freshness)
    ("zitadel", "saml", 4): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "TP", "reason": "ZT-3", "desc_snippet": "JWT missing exp claim accepted"},
    # [5] VIOLATION/HIGH/I2 no-exp JWT cross-intent replay -> ZT-3 (also freshness)
    ("zitadel", "saml", 5): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "TP", "reason": "ZT-3", "desc_snippet": "same no-exp JWT accepted in two intents"},
    # [6] UNEXPECTED/MEDIUM/I2 control SAML failed (setup)
    ("zitadel", "saml", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML 400, code exchange failed"},
    # [7] UNEXPECTED/LOW/I2 userinfo OK but no exchange (speculative)
    ("zitadel", "saml", 7): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "session token reuse speculation"},
    # [8] UNEXPECTED/MEDIUM/I2 same JWT across intents (speculative)
    ("zitadel", "saml", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "missing anti-replay binding"},
    # [9] UNEXPECTED/MEDIUM/I2 intent_token reuse (speculative)
    ("zitadel", "saml", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "intent_token reusable"},
    # [10] UNEXPECTED/MEDIUM/I3 userinfo after disable (speculative)
    ("zitadel", "saml", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "authenticated session when flow failed"},
    # [11] UNEXPECTED/MEDIUM/I3 userinfo after SAML fail (speculative)
    ("zitadel", "saml", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "flow splicing speculation"},
    # [12] UNEXPECTED/LOW/I3 idp deletion 404 (setup)
    ("zitadel", "saml", 12): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "idp deletion 404"},
    # [13] UNEXPECTED/MEDIUM/I3 intent splice control also fails (setup)
    ("zitadel", "saml", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "control retrieval invalid, test invalid"},
    # [14] UNEXPECTED/LOW/I3 same idp_intent_id (speculative)
    ("zitadel", "saml", 14): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "same intent id, atypical"},
    # [15] UNEXPECTED/LOW/I4 entity_id None (setup)
    ("zitadel", "saml", 15): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "entity_id None, cannot validate"},
    # [16] UNEXPECTED/MEDIUM/I4 empty sub risk (speculative)
    ("zitadel", "saml", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "empty sub accepted, risks collision"},
    # [17] VIOLATION/HIGH/I4 same idp_intent_token accepted diff authRequestID (not in 33)
    ("zitadel", "saml", 17): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "FP", "reason": "not-in-33", "desc_snippet": "intent token cross-session replay (not in 33)"},
    # [18] UNEXPECTED/MEDIUM/I4 stale intent state (speculative)
    ("zitadel", "saml", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "mis-associated intent state"},
    # [19] UNEXPECTED/MEDIUM/I5 flow coherence (speculative)
    ("zitadel", "saml", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo success despite SAML fail"},
    # [20] UNEXPECTED/LOW/I5 server 500 DoS (speculative)
    ("zitadel", "saml", 20): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "500 on malformed"},
    # [21] UNEXPECTED/MEDIUM/I5 missing AudienceRestriction 500 (speculative)
    ("zitadel", "saml", 21): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "HTTP 500 DoS speculation"},
    # [22] UNEXPECTED/LOW/I5 control fails downstream ok (speculative)
    ("zitadel", "saml", 22): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "flow incoherence"},
    # [23] UNEXPECTED/MEDIUM/I5 SAML 400 but userinfo ok (speculative)
    ("zitadel", "saml", 23): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "userinfo success despite SAML 400"},
    # [24] UNEXPECTED/LOW/I5 SAML cleanup 404 (setup)
    ("zitadel", "saml", 24): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cleanup 404"},
    # [25] UNEXPECTED/MEDIUM/I5 wrong aud appears accepted (speculative)
    # Could match ZT-1 but labeled UNEXPECTED and hedged ("appears to succeed")
    ("zitadel", "saml", 25): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "JWT IdP wrong aud appears accepted, speculative"},
}


def main():
    total = len(TRIAGE)
    violations = [v for v in TRIAGE.values() if v["verdict"] == "VIOLATION"]
    unexpected = [v for v in TRIAGE.values() if v["verdict"] == "UNEXPECTED"]

    v_tp = [v for v in violations if v["label"] == "TP"]
    v_fp = [v for v in violations if v["label"] == "FP"]
    u_tp = [v for v in unexpected if v["label"] == "TP"]
    u_fp = [v for v in unexpected if v["label"] == "FP"]

    all_tp = v_tp + u_tp

    # FP reason breakdown for VIOLATION
    v_fp_reasons = defaultdict(int)
    for v in v_fp:
        v_fp_reasons[v["reason"]] += 1

    # Distinct flaws found
    distinct_flaws = sorted({v["reason"] for v in all_tp})

    # TP by confidence
    tp_by_conf = defaultdict(int)
    for v in all_tp:
        tp_by_conf[v["conf"]] += 1

    print(f"===== {RUN} manual triage =====")
    print(f"Total findings: {total}")
    print(f"VIOLATION: {len(violations)}  (TP={len(v_tp)}, FP={len(v_fp)})")
    print(f"  VIOLATION FP breakdown: {dict(v_fp_reasons)}")
    print(f"UNEXPECTED: {len(unexpected)}  (rescued TP={len(u_tp)}, FP={len(u_fp)})")
    print(f"Total TP: {len(all_tp)}")
    print(f"Distinct flaws matched: {distinct_flaws}  ({len(distinct_flaws)}/33)")
    print(f"TP confidence: HIGH={tp_by_conf['HIGH']} MEDIUM={tp_by_conf['MEDIUM']} LOW={tp_by_conf['LOW']}")

    # Per-platform/protocol TP counts
    per_pp = defaultdict(lambda: {"tp": 0, "fp": 0, "total": 0})
    for (p, pr, idx), v in TRIAGE.items():
        k = f"{p}/{pr}"
        per_pp[k]["total"] += 1
        if v["label"] == "TP":
            per_pp[k]["tp"] += 1
        else:
            per_pp[k]["fp"] += 1
    print()
    print("Per platform/protocol:")
    for k in sorted(per_pp):
        s = per_pp[k]
        print(f"  {k}: total={s['total']} TP={s['tp']} FP={s['fp']}")


if __name__ == "__main__":
    main()
