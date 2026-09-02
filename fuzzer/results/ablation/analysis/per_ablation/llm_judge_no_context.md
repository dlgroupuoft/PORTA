# LLM-Judge (no context) — TP/FP Analysis

- **eval-mode**: `llm_judge`
- **Generation pipeline**: invariant + CVE examples (identical to Full)
- **Verdict layer**: single LLM call (gpt-5.2, temperature 0.01)
- **Runs analyzed**: 3 — `llm_judge_r1, llm_judge_r2, llm_judge_r3`
- **Triage**: per-finding manual triage (2026-04-16), see [../manual_triage_2026/](../manual_triage_2026/)

Pure LLM-as-judge with only the captured HTTP trace. No platform profile, no invariant taxonomy in the judge prompt. Generation pipeline matches Full (invariant + examples).

## Per-run results by confidence threshold

Findings are filtered by the confidence field the LLM attached to each finding. *ALL* = all findings (same denominator as Full). *HIGH+MED* = exclude findings the LLM itself flagged as low-confidence. *HIGH* = only findings the LLM marked high-confidence (the most favorable reading for the LLM-judge).

| Run | Findings@HIGH | TP@HIGH | Prec@HIGH | Findings@HIGH+MED | TP@HIGH+MED | Prec@HIGH+MED | Findings@ALL | TP@ALL | Prec@ALL |
|---|---|---|---|---|---|---|---|---|---|
| no_context_r1 | 44 | 22 | 50.0% | 175 | 22 | 12.6% | 221 | 22 | 10.0% |
| no_context_r2 | 63 | 21 | 33.3% | 205 | 21 | 10.2% | 249 | 21 | 8.4% |
| no_context_r3 | 51 | 16 | 31.4% | 204 | 18 | 8.8% | 266 | 18 | 6.8% |
| **mean±std** | **52.7±9.6** | **19.7±3.2** | **38.2%±10.2%** | **194.7±17.0** | **20.3±2.1** | **10.5%±1.9%** | **245.3±22.7** | **20.3±2.1** | **8.4%±1.6%** |

## Flaws recovered (union of 3 runs)

| Threshold | Distinct flaws | IDs |
|---|---|---|
| HIGH      | 12/33 | AK-6, CD-4, CD-5, KC-1, LG-1, LG-2, LG-3, LG-5, LG-6, VT-5/6, ZT-1, ZT-3 |
| HIGH+MED  | 12/33 | AK-6, CD-4, CD-5, KC-1, LG-1, LG-2, LG-3, LG-5, LG-6, VT-5/6, ZT-1, ZT-3 |
| ALL       | 12/33 | AK-6, CD-4, CD-5, KC-1, LG-1, LG-2, LG-3, LG-5, LG-6, VT-5/6, ZT-1, ZT-3 |

**Never found across any run/threshold** (21/33): AK-1, AK-3, AK-5, AK-7, CD-1, CD-2, CD-3, CD-6, CD-7, CD-8, CD-9, DX-1, DX-2, DX-3, DX-4, DX-5, KC-3, KC-4, KC-5, KC-6, ZT-2

## FP root-cause breakdown

Each FP is categorized by the *quality of the finding description*, independent of the LLM's verdict field. Categories:

- **`fabricated`** — description commits to a concrete attack/behavior that does not match any of the 33 ground-truth flaws (either a made-up attack narrative or a real-but-out-of-scope platform behavior)
- **`hedged`** — description uses speculative language (*suggests*, *may*, *appears*, *cannot confirm*) or declines to commit to a specific violation claim; the output is not a concrete assertion a reviewer can evaluate
- **`setup-artifact`** — description is about control/baseline test-infrastructure failure (missing session token, `invalid_client`, 409 already-exists, etc.) rather than a security behavior
- **`wrong-classif`** — concrete violation but labeled with the wrong invariant axis

| Threshold | fabricated | hedged | setup-artifact | wrong-classif | Total FP |
|---|---|---|---|---|---|
| HIGH | 62 | 34 | 3 | 0 | 99 |
| HIGH+MED | 62 | 458 | 3 | 0 | 523 |
| ALL | 62 | 610 | 3 | 0 | 675 |

## Per platform × protocol (HIGH threshold, 3-run aggregate)

| platform / protocol | Findings | TP | FP | Precision |
|---|---|---|---|---|
| logto / oidc_jwt | 20 | 15 | 5 | 75.0% |
| keycloak / oidc | 5 | 3 | 2 | 60.0% |
| authentik / oidc_jwt | 7 | 4 | 3 | 57.1% |
| logto / saml | 21 | 9 | 12 | 42.9% |
| zitadel / saml | 21 | 9 | 12 | 42.9% |
| vault / oidc_jwt | 32 | 10 | 22 | 31.2% |
| zitadel / oidc_jwt | 14 | 4 | 10 | 28.6% |
| casdoor / saml | 15 | 4 | 11 | 26.7% |
| casdoor / oidc | 9 | 1 | 8 | 11.1% |
| authentik / saml | 3 | 0 | 3 | 0.0% |
| dex / oidc_jwt | 7 | 0 | 7 | 0.0% |
| keycloak / saml | 3 | 0 | 3 | 0.0% |
| dex / saml | 1 | 0 | 1 | 0.0% |

## Example FPs at HIGH confidence

These are findings the LLM itself marked HIGH-confidence yet are still false positives. They illustrate the judgment-quality floor: extra prompt context does not fix this class of error.


### no_context_r1

**`fabricated`** (12 total at HIGH, 2 shown):
- `casdoor/oidc` #11 (inv=I3): Token exchange succeeded using the application's old client_secret after secret rotation, indicati
- `casdoor/oidc` #21 (inv=I5): Application tag restriction appears bypassed: a non-admin user without the required tag successful

**`hedged`** (8 total at HIGH, 2 shown):
- `authentik/saml` #6 (inv=I2): SAML login reports success (HTTP 200) but no session token is issued/available, causing identity v
- `casdoor/saml` #12 (inv=I3): SAML login attempt triggers a backend SQL/schema error that is returned to the client, indicating

**`setup-artifact`** (2 total at HIGH, 2 shown):
- `logto/saml` #3 (inv=I1): SAML login succeeded even though the attempted SAML connector creation failed due to an invalid Id
- `vault/oidc_jwt` #3 (inv=I1): Trust anchor substitution: after switching jwt_validation jwks_url to an attacker-controlled JWKS


### no_context_r2

**`fabricated`** (25 total at HIGH, 2 shown):
- `authentik/oidc_jwt` #1 (inv=I1): Attacker re-signed JWT accepted; JWT trust-anchor (no AK I1-JWT flaw in 33)
- `casdoor/saml` #20 (inv=I3): Backend SQL error: info-disclosure/DoS not in 33

**`hedged`** (16 total at HIGH, 2 shown):
- `authentik/saml` #4 (inv=I2): All SAML logins 200 but no session; harness issue
- `authentik/saml` #16 (inv=I5): Provider creation failed; replay test invalid

**`setup-artifact`** (1 total at HIGH, 2 shown):
- `authentik/oidc_jwt` #12 (inv=I2): Login failed 400 but session token issued; contradictory


### no_context_r3

**`fabricated`** (25 total at HIGH, 2 shown):
- `authentik/oidc_jwt` #16 (inv=I4): Homoglyph sub collision (authentik I4 not in 33)
- `casdoor/oidc` #15 (inv=I3): Token exchange succeeded with wrong client_secret (not in 33)

**`hedged`** (10 total at HIGH, 2 shown):
- `casdoor/oidc` #24 (inv=I4): SAML 200 but session token not validated (speculative setup failure)
- `casdoor/oidc` #28 (inv=I5): App tag restriction bypass (casdoor tag restriction not in 33)

## Reproducibility

- **Raw findings**: `FINDINGS_ROOT` in each triage file — one campaign per platform × protocol per run.
- **Per-finding labels**: [`../manual_triage_2026/`](../manual_triage_2026/) (9 Python files, one per variant × run).
- **Aggregator**: [`../aggregate_triage.py`](../aggregate_triage.py) regenerates aggregate_results from the triage files.
- **Re-run raw campaigns**: see the current eval-mode mapping in [`../README.md`](../README.md) §3; use `--eval-mode llm_judge` and a new output root.
- **Regenerate this doc**: `python3 ../scripts_gen_per_ablation.py`.
