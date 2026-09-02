# LLM-Judge + profile — TP/FP Analysis

- **eval-mode**: `llm_judge_profile`
- **Generation pipeline**: invariant + CVE examples (identical to Full)
- **Verdict layer**: single LLM call (gpt-5.2, temperature 0.01)
- **Runs analyzed**: 3 — `llm_judge_profile_r1, llm_judge_profile_r2, llm_judge_profile_r3`
- **Triage**: per-finding manual triage (2026-04-16), see [../manual_triage_2026/](../manual_triage_2026/)

LLM-as-judge with the sanitized platform profile (API endpoints, constraints; invariant references stripped) added to the judge prompt. Generation pipeline matches Full.

## Per-run results by confidence threshold

Findings are filtered by the confidence field the LLM attached to each finding. *ALL* = all findings (same denominator as Full). *HIGH+MED* = exclude findings the LLM itself flagged as low-confidence. *HIGH* = only findings the LLM marked high-confidence (the most favorable reading for the LLM-judge).

| Run | Findings@HIGH | TP@HIGH | Prec@HIGH | Findings@HIGH+MED | TP@HIGH+MED | Prec@HIGH+MED | Findings@ALL | TP@ALL | Prec@ALL |
|---|---|---|---|---|---|---|---|---|---|
| profile_r1 | 58 | 10 | 17.2% | 204 | 10 | 4.9% | 270 | 10 | 3.7% |
| profile_r2 | 58 | 10 | 17.2% | 237 | 11 | 4.6% | 320 | 11 | 3.4% |
| profile_r3 | 70 | 14 | 20.0% | 258 | 14 | 5.4% | 317 | 14 | 4.4% |
| **mean±std** | **62.0±6.9** | **11.3±2.3** | **18.2%±1.6%** | **233.0±27.2** | **11.7±2.1** | **5.0%±0.4%** | **302.3±28.0** | **11.7±2.1** | **3.9%±0.5%** |

## Flaws recovered (union of 3 runs)

| Threshold | Distinct flaws | IDs |
|---|---|---|
| HIGH      | 12/33 | AK-3, AK-6, CD-4, CD-5, DX-3, LG-1, LG-2, LG-3, LG-6, VT-5/6, ZT-1, ZT-3 |
| HIGH+MED  | 12/33 | AK-3, AK-6, CD-4, CD-5, DX-3, LG-1, LG-2, LG-3, LG-6, VT-5/6, ZT-1, ZT-3 |
| ALL       | 12/33 | AK-3, AK-6, CD-4, CD-5, DX-3, LG-1, LG-2, LG-3, LG-6, VT-5/6, ZT-1, ZT-3 |

**Never found across any run/threshold** (21/33): AK-1, AK-5, AK-7, CD-1, CD-2, CD-3, CD-6, CD-7, CD-8, CD-9, DX-1, DX-2, DX-4, DX-5, KC-1, KC-3, KC-4, KC-5, KC-6, LG-5, ZT-2

## FP root-cause breakdown

Each FP is categorized by the *quality of the finding description*, independent of the LLM's verdict field. Categories:

- **`fabricated`** — description commits to a concrete attack/behavior that does not match any of the 33 ground-truth flaws (either a made-up attack narrative or a real-but-out-of-scope platform behavior)
- **`hedged`** — description uses speculative language (*suggests*, *may*, *appears*, *cannot confirm*) or declines to commit to a specific violation claim; the output is not a concrete assertion a reviewer can evaluate
- **`setup-artifact`** — description is about control/baseline test-infrastructure failure (missing session token, `invalid_client`, 409 already-exists, etc.) rather than a security behavior
- **`wrong-classif`** — concrete violation but labeled with the wrong invariant axis

| Threshold | fabricated | hedged | setup-artifact | wrong-classif | Total FP |
|---|---|---|---|---|---|
| HIGH | 36 | 85 | 30 | 1 | 152 |
| HIGH+MED | 40 | 493 | 130 | 1 | 664 |
| ALL | 40 | 648 | 183 | 1 | 872 |

## Per platform × protocol (HIGH threshold, 3-run aggregate)

| platform / protocol | Findings | TP | FP | Precision |
|---|---|---|---|---|
| logto / saml | 10 | 9 | 1 | 90.0% |
| logto / oidc_jwt | 15 | 7 | 8 | 46.7% |
| authentik / oidc_jwt | 14 | 4 | 10 | 28.6% |
| zitadel / saml | 13 | 3 | 10 | 23.1% |
| vault / oidc_jwt | 22 | 5 | 17 | 22.7% |
| zitadel / oidc_jwt | 10 | 2 | 8 | 20.0% |
| casdoor / oidc | 22 | 2 | 20 | 9.1% |
| dex / saml | 17 | 1 | 16 | 5.9% |
| casdoor / saml | 18 | 1 | 17 | 5.6% |
| authentik / saml | 6 | 0 | 6 | 0.0% |
| dex / oidc_jwt | 6 | 0 | 6 | 0.0% |
| keycloak / saml | 27 | 0 | 27 | 0.0% |
| keycloak / oidc | 6 | 0 | 6 | 0.0% |

## Example FPs at HIGH confidence

These are findings the LLM itself marked HIGH-confidence yet are still false positives. They illustrate the judgment-quality floor: extra prompt context does not fix this class of error.


### profile_r1

**`fabricated`** (17 total at HIGH, 2 shown):
- `casdoor/oidc` #29 (inv=I5): Application tag restriction not enforced (not in 33)
- `logto/oidc_jwt` #1 (inv=I1): SAML trust-anchor forgery - SAML signature forgery in Logto not among 33

**`hedged`** (2 total at HIGH, 2 shown):
- `casdoor/oidc` #1 (inv=I1): 'may not be validating' signature/expiry
- `dex/oidc_jwt` #3 (inv=I4): 'indicating possible principal confusion'

**`setup-artifact`** (29 total at HIGH, 2 shown):
- `authentik/oidc_jwt` #2 (inv=I1): no access/session token was captured
- `authentik/oidc_jwt` #9 (inv=I3): no session/access token captured


### profile_r2

**`fabricated`** (11 total at HIGH, 2 shown):
- `authentik/oidc_jwt` #5 (inv=I1): alg=none accepted in authentik JWT M2M (not in 33)
- `casdoor/oidc` #21 (inv=I3): Token exchange after grant-type removed (config enforcement, not in 33)

**`hedged`** (36 total at HIGH, 2 shown):
- `authentik/oidc_jwt` #7 (inv=I2): Control JWT login failed, nbf test inconclusive
- `authentik/oidc_jwt` #9 (inv=I2): No usable session/access token for UserInfo

**`setup-artifact`** (1 total at HIGH, 2 shown):
- `casdoor/saml` #8 (inv=I1): Password login token cannot be found at /api/userinfo (broken token persistence, test-harness artifact)


### profile_r3

**`fabricated`** (8 total at HIGH, 2 shown):
- `casdoor/oidc` #21 (inv=I3): Token exchange succeeded with wrong client_secret (not in 33)
- `dex/oidc_jwt` #1 (inv=I1): Dex token exchange accepted forged subject_token (not in 33)

**`hedged`** (47 total at HIGH, 2 shown):
- `authentik/oidc_jwt` #10 (inv=I2): UserInfo never executed - missing session tokens
- `authentik/oidc_jwt` #12 (inv=I3): JWKS rotation test not executed (OAuth Source save failed)

**`wrong-classif`** (1 total at HIGH, 2 shown):
- `vault/oidc_jwt` #6 (inv=I2): Two logins collapsed into same Vault identity (labeled I2 but is I4 alias collision)

## Reproducibility

- **Raw findings**: `FINDINGS_ROOT` in each triage file — one campaign per platform × protocol per run.
- **Per-finding labels**: [`../manual_triage_2026/`](../manual_triage_2026/) (9 Python files, one per variant × run).
- **Aggregator**: [`../aggregate_triage.py`](../aggregate_triage.py) regenerates aggregate_results from the triage files.
- **Re-run raw campaigns**: see [`../README.md`](../README.md) §3 (`bash scripts/run_ablation_llm_judge_profile.sh`).
- **Regenerate this doc**: `python3 ../scripts_gen_per_ablation.py`.
