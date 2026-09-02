"""Manual triage for llm_judge (no_context) / r1. Agent-generated 2026-04-16.

Triage of all 221 unique findings across 13 campaign files against the 33
ground-truth flaws defined in the paper.

Classification rules:
  1. VIOLATION:
     a. Speculative hedging language -> FP:speculative
     b. Test-infrastructure failure -> FP:setup-failure
     c. Match a ground-truth flaw semantically -> TP:<flaw_id>
     d. Otherwise -> FP:not-in-33
  2. UNEXPECTED: default FP:unexpected-not-violation; rescue only if HIGH
     confidence, non-speculative, non-setup-failure, clearly describes a
     concrete flaw match.
"""
from collections import defaultdict

RUN = "no_context_r1"
FINDINGS_ROOT = "/home/ubuntu/broker/fuzzer/results/ablation/llm_judge"

# Key format: (platform, protocol, idx) -- idx is 1-based position in unique_findings.json
TRIAGE = {
    # ==================== authentik / oidc_jwt (10) ====================
    ("authentik", "oidc_jwt", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Control JWT signed with the expected/trusted key was rejected (invalid_grant), so the test cannot v"},
    ("authentik", "oidc_jwt", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Control (supposed-valid) JWT M2M login was rejected with invalid_grant, so the test cannot confirm"},
    ("authentik", "oidc_jwt", 3): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "TP", "reason": "AK-6", "desc_snippet": "Expired external JWT was accepted (HTTP 200) when it should have been rejected, indicating missing"},
    ("authentik", "oidc_jwt", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Successful JWT logins did not yield a session token, preventing identity verification and suggesti"},
    ("authentik", "oidc_jwt", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Control token exchange for client B failed with invalid_grant, indicating the authorization code f"},
    ("authentik", "oidc_jwt", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "JWT login reports success (HTTP 200) but no session token is issued, preventing identity verificat"},
    ("authentik", "oidc_jwt", 7): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "After the supposed JWKS rotation step, a login using the old key still returns HTTP 200 (success),"},
    ("authentik", "oidc_jwt", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "JWT audience-mismatch login attempt returned HTTP 200/success instead of being rejected, suggestin"},
    ("authentik", "oidc_jwt", 9): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Both successful login_with_jwt calls returned no session token, preventing identity verification a"},
    ("authentik", "oidc_jwt", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Token introspection succeeded (HTTP 200) despite no authenticated session/token being available, s"},

    # ==================== authentik / saml (15) ====================
    ("authentik", "saml", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML OneTimeUse replay test is inconclusive because the replayed SAML login returned HTTP 200 succ"},
    ("authentik", "saml", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login reports success (HTTP 200) but no session token is issued, preventing identity verifica"},
    ("authentik", "saml", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Session revocation endpoint returns invalid_client (401) when called with a session token, suggest"},
    ("authentik", "saml", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login reports success (HTTP 200) but no session token is issued, preventing identity verifica"},
    ("authentik", "saml", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Session revocation attempt fails with invalid_client (401), suggesting misconfigured/unauthenticat"},
    ("authentik", "saml", 6): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login reports success (HTTP 200) but no session token is issued/available, causing identity v"},
    ("authentik", "saml", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Token introspection indicates the session is inactive immediately after a successful SAML login, s"},
    ("authentik", "saml", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Session revocation fails with invalid_client (401), indicating the revocation endpoint/client auth"},
    ("authentik", "saml", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login with a mismatched Issuer was accepted (HTTP 200/success=True) both before and after the"},
    ("authentik", "saml", 10): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Post-login identity verification failed due to missing session tokens, preventing confirmation whe"},
    ("authentik", "saml", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Session revocation step failed with invalid_client (401), indicating the test did not actually rev"},
    ("authentik", "saml", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login reports success (HTTP 200) but no authenticated session/token is established, suggestin"},
    ("authentik", "saml", 13): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "cleanup_auth_method endpoint returned HTTP 405 (method not allowed), preventing the intended mid-f"},
    ("authentik", "saml", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login reports success (HTTP 200) but no session token is issued/available afterward, preventi"},
    ("authentik", "saml", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "All SAML logins report success (HTTP 200) but no session token is issued/available afterward, prev"},

    # ==================== casdoor / oidc (27) ====================
    ("casdoor", "oidc", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Forged SAML login returned HTTP 200/success=True but no valid session/access token was created (to"},
    ("casdoor", "oidc", 2): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Session token value for the forged SAML flow matches the victim's session token, suggesting possib"},
    ("casdoor", "oidc", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login reports success (HTTP 200) but no access token/session is persisted, preventing verific"},
    ("casdoor", "oidc", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Freshly obtained access token is immediately rejected as non-existent/invalid, preventing meaningf"},
    ("casdoor", "oidc", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login reports success (HTTP 200) but no access token is persisted/recognized, indicating a po"},
    ("casdoor", "oidc", 6): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Session token collision/reuse observed between different auth contexts (replay-after-logout sessio"},
    ("casdoor", "oidc", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login reports success (HTTP 200) but no access token/session is persisted, causing immediate"},
    ("casdoor", "oidc", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "After revoking user A, the identity verification response for A contains user B's email, suggestin"},
    ("casdoor", "oidc", 9): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Revoked token is reported as 'expired' with an expireTime equal to the token creation time, which"},
    ("casdoor", "oidc", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Expired SAML login flow reports success (HTTP 200, success=True) but no access token is issued/rec"},
    ("casdoor", "oidc", 11): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "not-in-33", "desc_snippet": "Token exchange succeeded using the application's old client_secret after secret rotation, indicati"},
    ("casdoor", "oidc", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login reports success but no access token is persisted/recognized, indicating a potentially b"},
    ("casdoor", "oidc", 13): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "User creation fails with 'Phone already exists' while subsequent password logins say 'the user doe"},
    ("casdoor", "oidc", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login reports success (HTTP 200) but the resulting session/access token is not recognized by"},
    ("casdoor", "oidc", 15): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML flows return an email value even though identity verification fails and no downstream identit"},
    ("casdoor", "oidc", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Global uniqueness constraint on phone number prevents creating same username across orgs, undermin"},
    ("casdoor", "oidc", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "User existence is disclosed via OAuth error_description ('the user does not exist'), enabling acco"},
    ("casdoor", "oidc", 18): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "verify_granted_identity returns HTTP 200 with an error body ('Access token doesn't exist in databa"},
    ("casdoor", "oidc", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Token exchange succeeded even though the initial OIDC code-to-token step failed with invalid_clien"},
    ("casdoor", "oidc", 20): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Introspection returned invalid_request (HTTP 400) and did not provide token metadata, preventing v"},
    ("casdoor", "oidc", 21): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "not-in-33", "desc_snippet": "Application tag restriction appears bypassed: a non-admin user without the required tag successful"},
    ("casdoor", "oidc", 22): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "TP", "reason": "CD-4", "desc_snippet": "Token exchange appears to ignore resource/audience binding: a token obtained for service-A was suc"},
    ("casdoor", "oidc", 23): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Introspection fails with HTTP 400 invalid_request for both original and exchanged tokens, preventi"},
    ("casdoor", "oidc", 24): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Successful password logins yield session/JWT-like tokens that the platform then reports as non-exi"},
    ("casdoor", "oidc", 25): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Access tokens issued at login appear not to be persisted/recognized by the broker ('Access token d"},
    ("casdoor", "oidc", 26): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Token introspection fails with invalid_request (HTTP 400) after session revocation, suggesting the"},
    ("casdoor", "oidc", 27): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Token exchange attempt fails due to invalid_client (client_id invalid), so the test cannot determi"},

    # ==================== casdoor / saml (26) ====================
    ("casdoor", "saml", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login flow returned HTTP 200/success=True but no access token/session was persisted, indicati"},
    ("casdoor", "saml", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Both the initial and replayed SAML logins returned HTTP 200/success=True, but no access token was"},
    ("casdoor", "saml", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login reports success (HTTP 200) but no access token is persisted/recognized, preventing veri"},
    ("casdoor", "saml", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login reports success (HTTP 200) but no access token/session is persisted, causing immediate"},
    ("casdoor", "saml", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Expired SAML assertion appears to be accepted (HTTP 200 success) instead of being rejected, sugges"},
    ("casdoor", "saml", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "All SAML logins (including control and second identity) report success but no access token is pers"},
    ("casdoor", "saml", 7): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Second 'different upstream identity' did not result in a different granted identity (all captured"},
    ("casdoor", "saml", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login reports success (HTTP 200) but no access token is issued/recognized, preventing verific"},
    ("casdoor", "saml", 9): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Provider metadata update step failed due to duplicate provider primary key, so the intended 'metad"},
    ("casdoor", "saml", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "MFA bypass test is inconclusive because MFA enablement failed, yet the victim could still password"},
    ("casdoor", "saml", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login reports success (HTTP 200) but results in a non-existent/invalid access token, indicati"},
    ("casdoor", "saml", 12): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login attempt triggers a backend SQL/schema error that is returned to the client, indicating"},
    ("casdoor", "saml", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login flow reports success (HTTP 200) but no usable access token/session is created, causing"},
    ("casdoor", "saml", 14): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Second SAML login (intended state/RelayState reuse) appears to succeed and yields a session token,"},
    ("casdoor", "saml", 15): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login against the newly created provider fails with a backend SQL schema error, indicating a"},
    ("casdoor", "saml", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login reports success but no access token/session is usable afterward, suggesting inconsisten"},
    ("casdoor", "saml", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML completion endpoint appears to return HTTP 200/success even though no access token/session is"},
    ("casdoor", "saml", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login flow returned success (HTTP 200 / success=True) but no valid access token was issued/re"},
    ("casdoor", "saml", 19): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Captured SAML collision entity_id shows 'admin' while identity fields are null, suggesting possibl"},
    ("casdoor", "saml", 20): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Token exchange test could not validate audience-binding because the exchange failed earlier with i"},
    ("casdoor", "saml", 21): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "RFC8693 token exchange succeeded even though the platform could not validate the subject/access to"},
    ("casdoor", "saml", 22): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "not-in-33", "desc_snippet": "Password login was expected to be rejected after disabling password login, but it still succeeded"},
    ("casdoor", "saml", 23): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login returned HTTP 200/success but no access token exists in the database, indicating incons"},
    ("casdoor", "saml", 24): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login appears to map/attribute the authenticated user as 'admin' (email/entity_id), suggestin"},
    ("casdoor", "saml", 25): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Token introspection endpoint returns generic 400 invalid_request for a seemingly valid logged-in s"},
    ("casdoor", "saml", 26): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Token exchange attempt fails at client authentication (401 invalid_client: client_id is invalid),"},

    # ==================== dex / oidc_jwt (10) ====================
    ("dex", "oidc_jwt", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Token exchange trust-anchor substitution test could not be validated because the control path fail"},
    ("dex", "oidc_jwt", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Attack attempt returned HTTP 404 (Not Found) rather than an explicit OIDC error response, which ma"},
    ("dex", "oidc_jwt", 3): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Attacker session verification captured an email value despite no session token, suggesting possibl"},
    ("dex", "oidc_jwt", 4): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "Token exchange accepted a JWT subject_token signed with an untrusted key, resulting in a valid ses"},
    ("dex", "oidc_jwt", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Control password login failed with unsupported_grant_type, preventing a valid baseline token excha"},
    ("dex", "oidc_jwt", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Two distinct auth attempts (user_A and user_B) resulted in the same downstream subject/entity_id,"},
    ("dex", "oidc_jwt", 7): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Password login step failed with unsupported_grant_type yet identities were still granted/verified,"},
    ("dex", "oidc_jwt", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Token exchange succeeded and produced the same subject/identity for two different principals (user"},
    ("dex", "oidc_jwt", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Token exchange succeeded and returned expanded identity attributes (groups/policies/display_name)"},
    ("dex", "oidc_jwt", 10): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "not-in-33", "desc_snippet": "Token exchange accepted a subject_token while claiming a different connector_id (issuer/connector"},

    # ==================== dex / saml (13) ====================
    ("dex", "saml", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Admin attempt to enable/configure the auth method failed (unsupported CREATECONNECTOR), so the tes"},
    ("dex", "saml", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Post-login identity verification fails with 'Invalid bearer token' for both users, suggesting the"},
    ("dex", "saml", 3): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Admin setup step to enable the auth method failed ('Unsupported method: CREATECONNECTOR'), so the"},
    ("dex", "saml", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login flow returns HTTP 200/success but the resulting session cannot be used (Invalid bearer"},
    ("dex", "saml", 5): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Admin attempt to toggle connector configuration failed (Unsupported method: CREATECONNECTOR), so t"},
    ("dex", "saml", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Session revocation step failed (404), so the test could not validate OneTimeUse replay protection"},
    ("dex", "saml", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Successful SAML logins produced sessions whose bearer tokens were immediately rejected as invalid"},
    ("dex", "saml", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Session issued after successful SAML login appears invalid (bearer token rejected), preventing ver"},
    ("dex", "saml", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Session revocation endpoint returned 404 (not found), so the test could not validate whether revoc"},
    ("dex", "saml", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Posting a SAMLResponse to the wrong connector callback caused an HTTP 500 (server error) instead o"},
    ("dex", "saml", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Unsolicited/step-skipped SAML POST to the ACS/callback returned HTTP 200 (appears accepted) even t"},
    ("dex", "saml", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Post-login identity verification fails with 'Invalid bearer token' (403) for both users, preventin"},
    ("dex", "saml", 13): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Admin connector management endpoints appear unsupported/misrouted (CREATECONNECTOR unsupported; cl"},

    # ==================== keycloak / oidc (4) ====================
    ("keycloak", "oidc", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Unsigned OIDC request object (alg=none) appears to be accepted (HTTP 200), which can enable author"},
    ("keycloak", "oidc", 2): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "TP", "reason": "KC-1", "desc_snippet": "OIDC authorization endpoint accepted a request object with alg=none (unsigned JWT), which should b"},
    ("keycloak", "oidc", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Attempted enforcement via client policy failed to apply (policy creation error), yet the platform"},
    ("keycloak", "oidc", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Unsigned OIDC request object (alg=none) appears to be accepted (HTTP 200), which may allow scope/p"},

    # ==================== keycloak / saml (24) ====================
    ("keycloak", "saml", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Admin IdP configuration change (intended trustEmail toggle) failed with HTTP 500, preventing valid"},
    ("keycloak", "saml", 2): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login returned HTTP 200 but no session token was established for the brokered user, suggestin"},
    ("keycloak", "saml", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML logins report HTTP 200/success but no session token is issued, preventing verification and ob"},
    ("keycloak", "saml", 4): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Provider creation failed with 'already exists', suggesting the intended config change (issuer pinn"},
    ("keycloak", "saml", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Replay attempt succeeded (HTTP 200) even though the initial use of the same SAML assertion flow fa"},
    ("keycloak", "saml", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login returns HTTP 200 success but the resulting session cannot access protected identity end"},
    ("keycloak", "saml", 7): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Admin session revocation failed due to 'missingNormalization', which may indicate an input/path no"},
    ("keycloak", "saml", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Both initial and replay SAML logins returned HTTP 200 but the resulting sessions could not access"},
    ("keycloak", "saml", 9): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "The intended IdP configuration change did not occur (create_provider returned 409 already exists),"},
    ("keycloak", "saml", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login reports HTTP 200/success but the resulting session cannot access verify_granted_identit"},
    ("keycloak", "saml", 11): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Attempt to 'tighten realm session/token lifetimes' appears not to have been applied because create"},
    ("keycloak", "saml", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login returned HTTP 200 twice, but the resulting session could not access protected identity"},
    ("keycloak", "saml", 13): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "User disable step failed (HTTP 405 Method Not Allowed), so the test did not actually disable the u"},
    ("keycloak", "saml", 14): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "A user record for the SAML principal appears to exist/was created even though the flow did not re"},
    ("keycloak", "saml", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Post-login session/identity verification fails with 401 despite SAML login returning HTTP 200 succ"},
    ("keycloak", "saml", 16): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Attempt to toggle IdP to linkOnly=true fails with HTTP 500 unknown_error, preventing enforcement o"},
    ("keycloak", "saml", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "IdP configuration change intended to toggle trustEmail failed (HTTP 500), so the test cannot valid"},
    ("keycloak", "saml", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Post-login session handling is inconsistent: verify_granted_identity reports no session token, yet"},
    ("keycloak", "saml", 19): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Protected resource seeding and subsequent authorization check fail with 'Could not find client' (H"},
    ("keycloak", "saml", 20): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "not-in-33", "desc_snippet": "Token exchange request was rejected (HTTP 400) but an access token was still issued and introspect"},
    ("keycloak", "saml", 21): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "The 'exchanged' access token appears identical/prefix-matching to the original limited token, sugg"},
    ("keycloak", "saml", 22): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Test could not validate privilege-inheritance behavior because post-login session/identity was nev"},
    ("keycloak", "saml", 23): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Protected resource seeding failed ('Could not find client'), preventing any meaningful authorizati"},
    ("keycloak", "saml", 24): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "IdP reconfiguration step failed with HTTP 500, so the intended trustEmail false-to-true toggle may"},

    # ==================== logto / oidc_jwt (20) ====================
    ("logto", "oidc_jwt", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Control client_credentials flow failed with invalid_client (401), so the test cannot confirm wheth"},
    ("logto", "oidc_jwt", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Replay attempt failed due to 'invalid_connector_id' (connector not found) rather than an assertion"},
    ("logto", "oidc_jwt", 3): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "TP", "reason": "LG-2", "desc_snippet": "SSO login was linked/mapped to an existing local user based on matching email/display name, allowi"},
    ("logto", "oidc_jwt", 4): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "SAML signature validation bypass: login succeeded with a SAMLResponse where only the outer Respons"},
    ("logto", "oidc_jwt", 5): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "TP", "reason": "LG-1", "desc_snippet": "OIDC nonce not enforced: authentication succeeds even when RP sent a nonce but IdP omits nonce in"},
    ("logto", "oidc_jwt", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Potential replay acceptance: a second OIDC auth attempt also succeeds under the same missing-nonce"},
    ("logto", "oidc_jwt", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Replay attempt failed due to an invalid/missing SAML connector reference rather than an explicit S"},
    ("logto", "oidc_jwt", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Password login fails with HTTP 422 'Experience verification' for both users, preventing token iss"},
    ("logto", "oidc_jwt", 9): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Revocation endpoint returns 401 invalid_client, suggesting client authentication is required/fail"},
    ("logto", "oidc_jwt", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Expired SAML assertion test did not reach assertion validation; login failed instead with an inval"},
    ("logto", "oidc_jwt", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "After token exchange was re-enabled, token_exchange still failed with invalid_client, suggesting t"},
    ("logto", "oidc_jwt", 12): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "A session/access token value was captured even though token_exchange returned 401 invalid_client,"},
    ("logto", "oidc_jwt", 13): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-2", "desc_snippet": "SSO login appears to have linked/collapsed into an existing local user identity based on email, e"},
    ("logto", "oidc_jwt", 14): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-6", "desc_snippet": "Two distinct SAML principals were mapped to the same downstream user (account merge/collision), b"},
    ("logto", "oidc_jwt", 15): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-6", "desc_snippet": "Empty OIDC/SAML subject identifier (sub='') collides and maps to an existing user, enabling accoun"},
    ("logto", "oidc_jwt", 16): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-2", "desc_snippet": "SSO login (SAML) with the same email was merged/collapsed into an existing local password account"},
    ("logto", "oidc_jwt", 17): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-6", "desc_snippet": "Cross-connector identity collision: the same upstream subject was accepted as the same local ident"},
    ("logto", "oidc_jwt", 18): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-2", "desc_snippet": "Account takeover via SSO auto-linking: a SAML login with email_verified=true was mapped to an exis"},
    ("logto", "oidc_jwt", 19): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Inconsistent identity resolution across two SAML logins suggests email_verified flipping changes w"},
    ("logto", "oidc_jwt", 20): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "TP", "reason": "LG-3", "desc_snippet": "SAML assertion missing the entire Conditions element was accepted and resulted in an authenticated"},

    # ==================== logto / saml (19) ====================
    ("logto", "saml", 1): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "The sequence labeled as OIDC kid/header key-confusion injection actually performed a SAML login an"},
    ("logto", "saml", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SSO login produced an identity whose display name matches the victim user while the email is atta"},
    ("logto", "saml", 3): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "SAML login succeeded even though the attempted SAML connector creation failed due to an invalid Id"},
    ("logto", "saml", 4): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "The sequence intended to validate rejection of OIDC kid/header injection, but the observed login p"},
    ("logto", "saml", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "After an application configuration change (enable token exchange), a nonce-less SSO login still su"},
    ("logto", "saml", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Replay attempt was not evaluated for SAML OneTimeUse anti-replay because the flow failed earlier w"},
    ("logto", "saml", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Test intended to verify OIDC nonce-less id_token rejection after config change, but the executed f"},
    ("logto", "saml", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Token introspection appears to return an entity_id for an inactive/invalid token, and the reported"},
    ("logto", "saml", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SSO login produced a new user with the victim's email; if the IdP claim had email_verified=false,"},
    ("logto", "saml", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML SSO login produced a new user identity with the victim's email/display name, suggesting emai"},
    ("logto", "saml", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SSO login with empty upstream subject ('sub'='') was accepted and provisioned a new principal, whi"},
    ("logto", "saml", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SSO user with empty subject inherited the same display name and email as an existing local user_B"},
    ("logto", "saml", 13): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-2", "desc_snippet": "SSO login with an unverified email claim (email_verified=false) was accepted and resulted in a ses"},
    ("logto", "saml", 14): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-2", "desc_snippet": "Distinct upstream principals (different attacker entity/sub) were both mapped to the same local ac"},
    ("logto", "saml", 15): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "LG-2", "desc_snippet": "SAML SSO logins with different upstream principals were merged into an existing local password ac"},
    ("logto", "saml", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SSO user created with a Unicode-homoglyph email and the same display name as an existing local vic"},
    ("logto", "saml", 17): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Identity verification step shows a display_name for Bob even though Alice login failed and no sess"},
    ("logto", "saml", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Test could not validate revocation enforcement because initial user login failed and revocation/in"},
    ("logto", "saml", 19): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Identity verification shows a display_name for 'alice' sessions as 'i5rev_bob' despite no session"},

    # ==================== vault / oidc_jwt (12) ====================
    ("vault", "oidc_jwt", 1): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "JWT auth accepted an attacker token using alg=none (unsigned JWT), resulting in a valid session to"},
    ("vault", "oidc_jwt", 2): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "JWT login succeeded for the attacker-crafted token intended to exploit kid header injection (untru"},
    ("vault", "oidc_jwt", 3): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "setup-failure", "desc_snippet": "Trust anchor substitution: after switching jwt_validation jwks_url to an attacker-controlled JWKS"},
    ("vault", "oidc_jwt", 4): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "FP", "reason": "not-in-33", "desc_snippet": "JWTs re-signed with an untrusted/attacker key were accepted (signature/key trust not enforced), al"},
    ("vault", "oidc_jwt", 5): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Unsigned OIDC request object (alg=none) probe did not yield an explicit accept/reject signal; both"},
    ("vault", "oidc_jwt", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Session revocation failed with a server-side error ('no namespace'), preventing validation that re"},
    ("vault", "oidc_jwt", 7): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "not-in-33", "desc_snippet": "JWTs with an iat far in the future are still accepted even after clock_skew_leeway was tightened/d"},
    ("vault", "oidc_jwt", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Role config readback shows clock_skew_leeway as null/None after modification, suggesting the tight"},
    ("vault", "oidc_jwt", 9): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "not-in-33", "desc_snippet": "JWT signing key rotation did not take effect immediately: a token signed with the old key (key-A)"},
    ("vault", "oidc_jwt", 10): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "VT-5/6", "desc_snippet": "Case-variant JWT subjects ('Admin' vs 'admin') are mapped to the same canonical entity, indicating"},
    ("vault", "oidc_jwt", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "JWT login with empty subject/alias fails with HTTP 500 (server error) instead of a clean client-si"},
    ("vault", "oidc_jwt", 12): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "TP", "reason": "VT-5/6", "desc_snippet": "Identity alias collision: changing identity_claim to a nested JSON pointer (/user/id) allows two d"},

    # ==================== zitadel / oidc_jwt (26) ====================
    ("zitadel", "oidc_jwt", 1): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Attack JWT with wrong audience appears to be accepted (HTTP 200) instead of being rejected, sugges"},
    ("zitadel", "oidc_jwt", 2): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Post-login intent retrieval shows no mapped/created user (user_id=None) despite successful control"},
    ("zitadel", "oidc_jwt", 3): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Attack attempt to send an unsigned OIDC request object (alg=none) did not yield an explicit accept"},
    ("zitadel", "oidc_jwt", 4): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Attack case was not actually executed as described (the minted 'attack' JWT still contains a kid h"},
    ("zitadel", "oidc_jwt", 5): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Potential intent/session mix-up: both start_idp_intent calls returned the same intent_id, which is"},
    ("zitadel", "oidc_jwt", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I1", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "JWT IdP login succeeded (HTTP 200) even when the asserted JWT omitted the exp claim, suggesting mi"},
    ("zitadel", "oidc_jwt", 7): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "JWT bearer login returns HTTP 500 (internal error) for both fresh and expired assertions, indicati"},
    ("zitadel", "oidc_jwt", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "JWT bearer login fails with generic HTTP 500 (server_error) for both fresh and stale assertions, i"},
    ("zitadel", "oidc_jwt", 9): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "TP", "reason": "ZT-3", "desc_snippet": "JWT IdP accepted an upstream JWT assertion that omitted the required exp claim, indicating expiry"},
    ("zitadel", "oidc_jwt", 10): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "IdP intent ID appears to be reused across separate start_idp_intent calls, which could indicate in"},
    ("zitadel", "oidc_jwt", 11): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Both intent tokens (including the correct, non-crossed ones) were rejected as CRYPTO invalid on re"},
    ("zitadel", "oidc_jwt", 12): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Two separate start_idp_intent calls returned the same intent ID, suggesting intent ID collision/re"},
    ("zitadel", "oidc_jwt", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Mid-intent IdP deletion was not actually performed (cleanup returned 404), so the test did not val"},
    ("zitadel", "oidc_jwt", 14): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Intent completion succeeded (HTTP 200) but subsequent intent retrieval failed with 'Intent Token i"},
    ("zitadel", "oidc_jwt", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "After a successful JWT IdP login, the issued idp_intent_token cannot be retrieved even once (403 C"},
    ("zitadel", "oidc_jwt", 16): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Baseline JWT IdP login failed before any key rotation, so the test cannot validate stale-key-cache"},
    ("zitadel", "oidc_jwt", 17): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Cleanup of both IdP configurations returned 404 'doesn't exist' despite successful creation/enabli"},
    ("zitadel", "oidc_jwt", 18): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "JWT IdP login completes successfully even when the JWT subject is an empty string (sub=''), sugges"},
    ("zitadel", "oidc_jwt", 19): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Unable to determine whether empty-subject identities collide with normal subjects because no downs"},
    ("zitadel", "oidc_jwt", 20): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "JWT IdP login fails due to key retrieval/validation error, preventing the intended email case-fold"},
    ("zitadel", "oidc_jwt", 21): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Cleanup reports IdP configuration not found (404) despite earlier successful creation/enabling, su"},
    ("zitadel", "oidc_jwt", 22): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I4", "label": "FP", "reason": "not-in-33", "desc_snippet": "IdP intent token appears reusable across different intents/users, indicating missing binding of th"},
    ("zitadel", "oidc_jwt", 23): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Null-byte/Unicode-escape in JWT 'sub' triggers a backend SQLSTATE 22P05 parsing error, suggesting"},
    ("zitadel", "oidc_jwt", 24): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "After failed login, retrieve_idp_intent returns an idp_user_id resembling the victim ('sub'='nul-v"},
    ("zitadel", "oidc_jwt", 25): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I5", "label": "TP", "reason": "ZT-1", "desc_snippet": "JWT IdP login accepted a JWT with a wrong audience (aud) claim, indicating missing/incorrect audie"},
    ("zitadel", "oidc_jwt", 26): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Post-login intent retrieval returned no resolved user identity (user_id=None) despite successful l"},

    # ==================== zitadel / saml (15) ====================
    ("zitadel", "saml", 1): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I1", "label": "TP", "reason": "ZT-1", "desc_snippet": "JWT IdP login accepted a token with an incorrect/attacker-controlled audience (aud), indicating mi"},
    ("zitadel", "saml", 2): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "TP", "reason": "ZT-3", "desc_snippet": "JWT IdP accepts assertions without an exp claim, enabling potentially indefinite token validity (m"},
    ("zitadel", "saml", 3): {"verdict": "VIOLATION", "conf": "HIGH", "invariant": "I2", "label": "TP", "reason": "ZT-3", "desc_snippet": "JWT IdP accepted an assertion missing the required 'iat' claim, indicating issuance-time freshness"},
    ("zitadel", "saml", 4): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login fails on the first attempt (HTTP 400) so the OneTimeUse replay protection is not actual"},
    ("zitadel", "saml", 5): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Cleanup of the IdP auth method returns 404 'configuration doesn't exist' after successful creation"},
    ("zitadel", "saml", 6): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "After a successful control JWT login, retrieving the IdP intent fails with 'Intent Token is invali"},
    ("zitadel", "saml", 7): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Replay test is inconclusive because the control SAML login failed; the broker never accepted a bas"},
    ("zitadel", "saml", 8): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I2", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML replay attempt triggered an Internal Server Error (500), suggesting a robustness issue and po"},
    ("zitadel", "saml", 9): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "SAML login appears to fail (HTTP 400) yet an identity/session is still granted/verified, suggestin"},
    ("zitadel", "saml", 10): {"verdict": "UNEXPECTED", "conf": "LOW", "invariant": "I3", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Policy toggle race condition could not be validated because enabling external IdP login policy did"},
    ("zitadel", "saml", 11): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "JWT IdP login completes (HTTP 200) but subsequent intent retrieval fails with CRYPTO-CRYPTO invali"},
    ("zitadel", "saml", 12): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I4", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Potential identity mix-up: user_B token parsing/capture indicates user_A subject despite failed lo"},
    ("zitadel", "saml", 13): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Identity appears to be granted/created despite SAML login failing and no OIDC tokens being minted,"},
    ("zitadel", "saml", 14): {"verdict": "UNEXPECTED", "conf": "HIGH", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "RFC8693 token exchange succeeded and returned expanded scopes (including profile) even though the"},
    ("zitadel", "saml", 15): {"verdict": "UNEXPECTED", "conf": "MEDIUM", "invariant": "I5", "label": "FP", "reason": "unexpected-not-violation", "desc_snippet": "Token exchange succeeded and produced a valid session for the same subject even though the control"},
}


def main():
    by_verdict = defaultdict(int)
    fp_reasons = defaultdict(int)
    tp_flaws = set()
    tp_conf = defaultdict(int)  # by confidence
    violation_tp = 0
    violation_fp = 0
    violation_fp_reasons = defaultdict(int)
    unexpected_total = 0
    unexpected_rescued = 0

    for key, rec in TRIAGE.items():
        by_verdict[rec["verdict"]] += 1
        if rec["verdict"] == "VIOLATION":
            if rec["label"] == "TP":
                violation_tp += 1
                tp_flaws.add(rec["reason"])
                tp_conf[rec["conf"]] += 1
            else:
                violation_fp += 1
                violation_fp_reasons[rec["reason"]] += 1
        else:  # UNEXPECTED
            unexpected_total += 1
            if rec["label"] == "TP":
                unexpected_rescued += 1
                tp_flaws.add(rec["reason"])
                tp_conf[rec["conf"]] += 1

    total = len(TRIAGE)
    print(f"Total findings triaged: {total}")
    print(f"  VIOLATION: {by_verdict['VIOLATION']} (TP={violation_tp}, FP={violation_fp})")
    print(f"    FP reasons: {dict(violation_fp_reasons)}")
    print(f"  UNEXPECTED: {unexpected_total} (rescued-as-TP={unexpected_rescued})")
    print(f"Distinct flaws found ({len(tp_flaws)}): {', '.join(sorted(tp_flaws))}")
    print(f"By confidence: TP@HIGH={tp_conf['HIGH']}, TP@MEDIUM={tp_conf['MEDIUM']}, TP@LOW={tp_conf['LOW']}")


if __name__ == "__main__":
    main()
