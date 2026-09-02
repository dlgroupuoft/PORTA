# LLM-Judge + invariant — TP/FP Analysis

- **eval-mode**: `llm_judge_invariant`
- **Generation pipeline**: invariant + CVE examples (identical to Full)
- **Verdict layer**: single LLM call (gpt-5.2, temperature 0.01)
- **Runs analyzed**: 3 — `llm_judge_invariant_r1, llm_judge_invariant_r2, llm_judge_invariant_r3`
- **Triage**: per-finding manual triage (2026-04-16), see [../manual_triage_2026/](../manual_triage_2026/)

LLM-as-judge with the I1–I5 invariant definitions added to the judge prompt. Generation pipeline matches Full.

## Per-run results by confidence threshold

Findings are filtered by the confidence field the LLM attached to each finding. *ALL* = all findings (same denominator as Full). *HIGH+MED* = exclude findings the LLM itself flagged as low-confidence. *HIGH* = only findings the LLM marked high-confidence (the most favorable reading for the LLM-judge).

| Run | Findings@HIGH | TP@HIGH | Prec@HIGH | Findings@HIGH+MED | TP@HIGH+MED | Prec@HIGH+MED | Findings@ALL | TP@ALL | Prec@ALL |
|---|---|---|---|---|---|---|---|---|---|
| invariant_r1 | 60 | 21 | 35.0% | 214 | 22 | 10.3% | 278 | 22 | 7.9% |
| invariant_r2 | 55 | 13 | 23.6% | 210 | 13 | 6.2% | 271 | 13 | 4.8% |
| invariant_r3 | 51 | 17 | 33.3% | 191 | 17 | 8.9% | 254 | 17 | 6.7% |
| **mean±std** | **55.3±4.5** | **17.0±4.0** | **30.7%±6.1%** | **205.0±12.3** | **17.3±4.5** | **8.5%±2.1%** | **267.7±12.3** | **17.3±4.5** | **6.5%±1.6%** |

## Flaws recovered (union of 3 runs)

| Threshold | Distinct flaws | IDs |
|---|---|---|
| HIGH      | 12/33 | AK-1, AK-6, CD-2, CD-4, DX-5, LG-1, LG-2, LG-3, LG-6, VT-5/6, ZT-1, ZT-3 |
| HIGH+MED  | 12/33 | AK-1, AK-6, CD-2, CD-4, DX-5, LG-1, LG-2, LG-3, LG-6, VT-5/6, ZT-1, ZT-3 |
| ALL       | 12/33 | AK-1, AK-6, CD-2, CD-4, DX-5, LG-1, LG-2, LG-3, LG-6, VT-5/6, ZT-1, ZT-3 |

**Never found across any run/threshold** (21/33): AK-3, AK-5, AK-7, CD-1, CD-3, CD-5, CD-6, CD-7, CD-8, CD-9, DX-1, DX-2, DX-3, DX-4, KC-1, KC-3, KC-4, KC-5, KC-6, LG-5, ZT-2

## FP root-cause breakdown

Each FP is categorized by the *quality of the finding description*, independent of the LLM's verdict field. Categories:

- **`fabricated`** — description commits to a concrete attack/behavior that does not match any of the 33 ground-truth flaws (either a made-up attack narrative or a real-but-out-of-scope platform behavior)
- **`hedged`** — description uses speculative language (*suggests*, *may*, *appears*, *cannot confirm*) or declines to commit to a specific violation claim; the output is not a concrete assertion a reviewer can evaluate
- **`setup-artifact`** — description is about control/baseline test-infrastructure failure (missing session token, `invalid_client`, 409 already-exists, etc.) rather than a security behavior
- **`wrong-classif`** — concrete violation but labeled with the wrong invariant axis

| Threshold | fabricated | hedged | setup-artifact | wrong-classif | Total FP |
|---|---|---|---|---|---|
| HIGH | 38 | 75 | 2 | 0 | 115 |
| HIGH+MED | 40 | 521 | 2 | 0 | 563 |
| ALL | 40 | 709 | 2 | 0 | 751 |

## Per platform × protocol (HIGH threshold, 3-run aggregate)

| platform / protocol | Findings | TP | FP | Precision |
|---|---|---|---|---|
| logto / oidc_jwt | 11 | 11 | 0 | 100.0% |
| logto / saml | 11 | 10 | 1 | 90.9% |
| authentik / oidc_jwt | 7 | 4 | 3 | 57.1% |
| vault / oidc_jwt | 27 | 12 | 15 | 44.4% |
| zitadel / oidc_jwt | 12 | 5 | 7 | 41.7% |
| zitadel / saml | 10 | 4 | 6 | 40.0% |
| authentik / saml | 5 | 1 | 4 | 20.0% |
| casdoor / oidc | 22 | 3 | 19 | 13.6% |
| dex / saml | 10 | 1 | 9 | 10.0% |
| casdoor / saml | 20 | 0 | 20 | 0.0% |
| dex / oidc_jwt | 8 | 0 | 8 | 0.0% |
| keycloak / oidc | 2 | 0 | 2 | 0.0% |
| keycloak / saml | 21 | 0 | 21 | 0.0% |

## Example FPs at HIGH confidence

These are findings the LLM itself marked HIGH-confidence yet are still false positives. They illustrate the judgment-quality floor: extra prompt context does not fix this class of error.


### invariant_r1

**`fabricated`** (13 total at HIGH, 2 shown):
- `authentik/oidc_jwt` #4 (inv=I1): alg=none JWT accepted at authentik (not among 33)
- `casdoor/saml` #23 (inv=I3): password still succeeds after disable

**`hedged`** (26 total at HIGH, 2 shown):
- `authentik/saml` #12 (inv=I2): admin bootstrap invalid_client, prevents revocation test
- `casdoor/oidc` #5 (inv=I1): JWT rejected as not in DB, inconsistent acceptance


### invariant_r2

**`fabricated`** (12 total at HIGH, 2 shown):
- `authentik/oidc_jwt` #1 (inv=I1): attacker-resigned JWT using an untrusted signing key accepted
- `casdoor/oidc` #29 (inv=I5): app tag restriction bypass non-admin

**`hedged`** (30 total at HIGH, 2 shown):
- `authentik/oidc_jwt` #20 (inv=I5): introspection 200 w/o session (harness)
- `casdoor/oidc` #2 (inv=I1): control+attack 200 but no session (harness)


### invariant_r3

**`fabricated`** (13 total at HIGH, 2 shown):
- `authentik/saml` #6 (inv=I2): revoke-user principal maps to other user's entity_id - I4 mislabeled as I2; not a matching flaw in 33 for authentik saml
- `casdoor/oidc` #10 (inv=I4): Case-variant username collision (local, not SAML/email flaw); CD-9 is saml email-binding specifically - not a match

**`hedged`** (19 total at HIGH, 2 shown):
- `authentik/saml` #8 (inv=I2): no session token after SAML logins - setup issue
- `authentik/saml` #10 (inv=I2): token/session handling broken (setup)

**`setup-artifact`** (2 total at HIGH, 2 shown):
- `vault/oidc_jwt` #4 (inv=I1): admin swapped jwks_url (test-setup config change)
- `zitadel/saml` #16 (inv=I5): SAML login failed (400/500), userinfo 200 - flow incoherence/harness not a real violation

## Reproducibility

- **Raw findings**: `FINDINGS_ROOT` in each triage file — one campaign per platform × protocol per run.
- **Per-finding labels**: [`../manual_triage_2026/`](../manual_triage_2026/) (9 Python files, one per variant × run).
- **Aggregator**: [`../aggregate_triage.py`](../aggregate_triage.py) regenerates aggregate_results from the triage files.
- **Re-run raw campaigns**: see [`../README.md`](../README.md) §3 (`bash scripts/run_ablation_llm_judge_invariant.sh`).
- **Regenerate this doc**: `python3 ../scripts_gen_per_ablation.py`.
