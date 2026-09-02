# Per-variant triage prompt template (2026-04-16)

> **Provenance note.** This is the exact historical agent-triage template. Absolute `/home/ubuntu/broker` paths refer to the original analysis checkout (including a separate platform-source tree) and are retained to document the method. For a new analysis, substitute the current checkout paths; do not execute these paths blindly.

Used to generate the 9 triage files in this directory via 9 parallel Claude Code subagents. One agent per `(variant, run)` pair. Each instance receives the template below with `{VARIANT}`, `{RUN}`, and the 13 file paths filled in.

## Agent prompt

```
Manually triage findings from LLM-judge ablation run "{VARIANT} / {RUN}"
against the paper's 33 ground-truth flaws.

## Input
Read all 13 of these unique_findings.json files:
{13 absolute paths, one per platform × protocol for this (variant, run)}

## Ground truth: 33 flaws (platform, invariant, keywords, protocol)
ZT-1   zitadel I5 "aud/audience/jwt" (oidc)
ZT-2   zitadel I5 "audience/saml/audiencerestriction" (saml)
ZT-3   zitadel I2 "exp/iat/temporal/expir/freshness" (oidc)
CD-1   casdoor I2 "replay/assertion" (saml)
CD-2   casdoor I2 "notonorafter/expir/time/temporal" (saml)
CD-3   casdoor I5 "audience/audiencerestriction" (saml)
CD-4   casdoor I5 "token exchange/cross-org/cross-tenant/organization" (oidc)
CD-5   casdoor I2 "revok/token exchange/revocation" (oidc)
CD-6   casdoor I1 "cert/certificate/trust anchor/saml" (saml)
CD-7   casdoor I3 "mfa/multi-factor/bypass/federation" (saml)
CD-8   casdoor I3 "unsolicited/flow/idp-initiated" (saml)
CD-9   casdoor I4 "email/identity/collision/confusion/binding" (saml)
DX-1   dex I5 "conditions/audience/optional" (saml)
DX-2   dex I2 "replay/assertion" (saml)
DX-3   dex I2 "notonorafter/expir/time/conditions" (saml)
DX-4   dex I3 "non-atomic/connector/stale/config/lifecycle" (saml)
DX-5   dex I3 "unsolicited/inresponseto/flow" (saml)
KC-1   keycloak I1 "alg=none/alg/request object/unsigned" (oidc)
KC-3   keycloak I2 "onetimeuse/replay/assertion" (saml)
KC-4   keycloak I5 "conditions/missing/null/absent" (saml)
KC-5   keycloak I5 "audience/wrong/saml" (saml)
KC-6   keycloak I3 "non-atomic/config/stale" (saml)
AK-1   authentik I2 "notonorafter/expir/time/temporal/replay" (saml)
AK-3   authentik I1 "issuer/iss/verify_iss" (oidc)
AK-5   authentik I5 "audience/conditions/saml" (saml)
AK-6   authentik I2 "exp/jwt/temporal/expir/client assertion" (oidc)
AK-7   authentik I3 "stale/non-atomic/config/jwks" (saml)
LG-1   logto I2 "nonce/bypass/oidc" (oidc)
LG-2   logto I4 "email/auto-link/linking/unverified" (oidc)
LG-3   logto I5 "conditions/saml/missing/absent" (saml)
LG-5   logto I3 "mfa/bypass/saml/federation" (saml)
LG-6   logto I4 "collision/case/unicode/whitespace/identity" (oidc)
VT-5/6 vault I4 "collision/case/email/identity/alias" (oidc)

## Classification rules

For EACH finding (UNEXPECTED *and* VIOLATION):

1. **If verdict_type = VIOLATION**:
   a. Speculative hedging (`suggests?`, `\bmay\b`, `appears?`, `cannot confirm`,
      `ambiguous`, `potentially`, `unclear`, `might`, `could indicate`,
      `possible`) → `FP:speculative`
   b. Setup failure (`no session token`, `409 already exists`,
      `invalid_client`, `setup fail`, `control.*fail`, `baseline.*fail`,
      `401 unauthorized`, `404 not found`) → `FP:setup-failure`
   c. Match against 33 flaws by platform + invariant + description
      semantics. Read platform source at /home/ubuntu/broker/platform/<platform>/
      if ambiguous. If matches → `TP:<flaw_id>`. If no match → `FP:not-in-33`.

2. **If verdict_type = UNEXPECTED**: default `FP:unexpected-not-violation`.
   Rescue ONLY if ALL of: (a) confidence is HIGH, (b) description is
   non-speculative and non-setup-failure, (c) evidence clearly describes a
   concrete flaw matching one of 33 — then `TP:<flaw_id>`. Be conservative;
   most UNEXPECTED should stay FP.

## Output

Write a Python file at
`/home/ubuntu/broker/fuzzer/results/ablation/analysis/manual_triage_2026/{VARIANT}_{RUN}_triage.py`
with this exact structure:

    """Manual triage for llm_judge ({VARIANT}) / {RUN}. Agent-generated 2026-04-16."""
    RUN = "{VARIANT}_{RUN}"
    FINDINGS_ROOT = "/home/ubuntu/broker/fuzzer/results/ablation/{run_dir}"

    TRIAGE = {
        ("authentik", "oidc_jwt", 1): {
            "verdict": "UNEXPECTED"|"VIOLATION",
            "conf": "HIGH"|"MEDIUM"|"LOW",
            "invariant": "I1".."I5",
            "label": "TP"|"FP",
            "reason": "<flaw_id>|speculative|setup-failure|not-in-33|unexpected-not-violation",
            "desc_snippet": "<first 100 chars of description>"
        },
        # ... one entry per finding in every file
    }

Key: (platform, protocol, idx) with 1-based idx.

After writing, print summary (<200 words):
- Total findings triaged
- VIOLATION count (TP/FP split, FP broken down by reason)
- UNEXPECTED count (total, rescued-as-TP count if any)
- Distinct flaws found: comma-separated flaw IDs
- By confidence: TP@HIGH, TP@MEDIUM, TP@LOW
```

## Variant → run_dir mapping

| Variant | run | run_dir |
|---|---|---|
| no_context | r1 | `llm_judge_r1` |
| no_context | r2 | `llm_judge_r2` |
| no_context | r3 | `llm_judge_r3` |
| profile | r1 | `llm_judge_profile_r1` |
| profile | r2 | `llm_judge_profile_r2` |
| profile | r3 | `llm_judge_profile_r3` |
| invariant | r1 | `llm_judge_invariant_r1` |
| invariant | r2 | `llm_judge_invariant_r2` |
| invariant | r3 | `llm_judge_invariant_r3` |

## Post-processing

After all 9 triage files are written:

```bash
cd /home/ubuntu/broker/fuzzer/results/ablation/analysis
python3 aggregate_triage.py
```

Produces `aggregate_results.json` and `aggregate_results.md` in this dir.
