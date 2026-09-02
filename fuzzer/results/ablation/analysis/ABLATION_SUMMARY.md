# Ablation Experiment Summary

## Purpose

RQ4: What does each component of the system contribute?

We compare the **Full** system (the published configuration) against three
core ablations and two LLM-judge context variants:

| Config | Removed components | Tests the importance of |
|--------|--------------------|--------------------------|
| **B** (blind) | invariants + examples + attack mode + sweep | Invariant taxonomy + attack-pattern guidance |
| **A1** (no_examples) | examples + sweep | Few-shot attack examples |
| **LLM-Judge** | all deterministic oracles + KBF + sweep | Deterministic verdict pipeline |
| **LLM-Judge + profile** | all deterministic oracles + KBF + sweep | Whether sanitized profile context improves the LLM judge |
| **LLM-Judge + invariant** | all deterministic oracles + KBF + sweep | Whether invariant definitions improve the LLM judge |

Each ablation runs 3 times across all 13 platform×protocol configurations
using the same `evaluation-exp1` profiles.

---

## Component matrix

| Component | **Full** | **A1** (no_examples) | **B** (blind) | **LLM-Judge** |
|-----------|:--:|:--:|:--:|:--:|
| Platform Profile in prompt                       | ✓ | ✓ | ✓ | ✓ |
| I1–I5 invariants in generation prompt            | ✓ | ✓ | **✗** | ✓ |
| CVE attack examples in generation prompt         | ✓ | **✗** | **✗** | ✓ |
| Generation strategy                              | `attack` | `attack` | **`coverage`** | `attack` |
| L1 syntactic oracle                              | ✓ | ✓ | ✓ | **✗** |
| L2 platform verifier                             | ✓ | ✓ | ✓ | **✗** |
| L3 assertion oracle (LLM-gen assertions)         | ✓ | ✓ | ✓ | **✗** |
| KnownBehaviorFilter (KBF)                        | ✓ | ✓ | ✓ | **✗** |
| Plain LLM-as-judge                               | ✗ | ✗ | ✗ | **✓** |
| LLM judge prompt: invariants/guidance            | — | — | — | **✗** (none) |
| Mutation sweep                                   | ✓ | **✗** | **✗** | **✗** |

---

## Aggregate results (3 runs)

| Metric | **Full** (exp1) | **A1** (no_examples) | **B** (blind) | **LLM-Judge** | **LLM-Judge + profile** | **LLM-Judge + invariant** |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|
| Sequences/run                       | 500.7 ± 12.5  | 492.0 ± 7.9   | 636.0 ± 1.0  | 475.3 ± 7.0  | ~475         | ~480          |
| Execution rate                      | 72.6 ± 3.3%   | 63.3 ± 1.7%   | 56.5 ± 3.1%  | 71.5 ± 2.2%  | ~71%         | ~72%          |
| Total findings/run                  | 84.0 ± 26.2   | 57.0 ± 3.6    | 6.3 ± 3.5    | 245.3 ± 22.7 | 302.3 ± 28.0 | 267.7 ± 12.3  |
| **TP/run**                          | **75.3 ± 27.2** | **43.0 ± 6.0** | **0.0**     | **20.3 ± 2.1**‡ | **11.7 ± 2.1** | **17.3 ± 4.5** |
| **FP/run**                          | **8.7 ± 1.5** | **14.0 ± 7.2** | **6.3 ± 3.5** | **225.0 ± 24.6** | **290.7 ± 26.7** | **250.3 ± 11.6** |
| **Precision** (ALL conf)            | **88.5 ± 6.1%** | **75.6±11.5 %**   | **0.0%**     | **8.4% ± 1.6%**‡ | **3.9% ± 0.5%** | **6.5% ± 1.6%** |
| **Precision @ HIGH conf only**§     | —             | —             | —            | **38.2% ± 10.2%** | **18.2% ± 1.6%** | **30.7% ± 6.1%** |
| Distinct vulns discovered (catalog 33) | **33 / 33** | **26 / 33**  | **0 / 33**   | **12 / 33** ‡ | **12 / 33** | **12 / 33** |

† B's I1 and I4 findings are noise (HTTP 500 server errors mislabeled as I1, identity-collision test setup failures mislabeled as I4) — no real coverage.
‡ Re-triaged from raw findings via 9 parallel agents (2026-04-16, see [`manual_triage_2026/`](manual_triage_2026/)); differs by ~1 TP / 1 flaw from a prior 2026-04-10 analysis (LG-4 was removed from the 33 flaws between analyses). All three LLM-judge rows use the same triage methodology for apples-to-apples comparison.
§ Precision computed on findings the LLM itself marked HIGH confidence only — the most favorable reading for each LLM-judge variant. Full's 88.5% is for ALL findings (Full does not attach a confidence field). See [cross_variant_analysis.md §2.1](cross_variant_analysis.md).

---

## Distinct vulnerabilities by platform (union across 3 runs)

| Platform (catalog count) | **Full** | **A1** | **B** | **LLM-Judge + Profile** | **LLM-Judge + Profile + Invariant** |
|--------------------------|:---:|:---:|:---:|:---:|:---:|
| Zitadel (3)              | 3  | 1  | 0 | 2  | 2  |
| Casdoor (9)              | 9  | 9  | 0 | 2  | 2  |
| Dex (5)                  | 5  | 5  | 0 | 0  | 1  |
| Keycloak (5)             | 5  | 4  | 0 | 1  | 0  |
| Authentik (5)            | 5  | 4  | 0 | 1  | 2  |
| Vault (1)                | 1  | 1  | 0 | 1  | 1  |
| Logto (6)                | 6  | 2  | 0 | 5  | 4  |
| **Total**                | **33** | **26** | **0** | **12** | **12** |

### LLM-Judge variants — which 12 flaws each finds (union of 3 runs)

| Variant | Flaws found |
|---|---|
| LLM-Judge + Profile              | AK-6, CD-4, CD-5, KC-1, LG-1, LG-2, LG-3, LG-5, LG-6, VT-5/6, ZT-1, ZT-3 |
| LLM-Judge + Profile + Invariant  | AK-1, AK-6, CD-2, CD-4, DX-5, LG-1, LG-2, LG-3, LG-6, VT-5/6, ZT-1, ZT-3 |
| **Intersection (common to both)** | AK-6, CD-4, LG-1, LG-2, LG-3, LG-6, VT-5/6, ZT-1, ZT-3 (9 flaws) |
| **Union (either variant)**        | AK-1, AK-6, CD-2, CD-4, CD-5, DX-5, KC-1, LG-1, LG-2, LG-3, LG-5, LG-6, VT-5/6, ZT-1, ZT-3 (15 flaws) |

Adding I1–I5 invariant definitions to the judge prompt does **not** expand coverage — both variants find 12/33 flaws, but swap 3 different flaws in/out. Extra taxonomy context affects *which* flaws the LLM latches onto, not *how many*.

---

## Vulnerabilities missed (never found across 3 runs)

| Config | Missed | List |
|--------|:--:|------|
| **Full** | 0 | — |
| **A1** | 7 | AK-6, KC-5, LG-2, LG-3, LG-6, ZT-1, ZT-2 |
| **B** | 33 | (all of them) |
| **LLM-Judge** | 21 | AK-1, AK-3, AK-5, AK-7, CD-1, CD-2, CD-3, CD-6, CD-7, CD-8, CD-9, DX-1, DX-2, DX-3, DX-4, DX-5, KC-3, KC-4, KC-5, KC-6, ZT-2 |

---

## FP type breakdown

### B (blind) — 19 FP across 3 runs

| FP Category | Count | % |
|---|:--:|:--:|
| HTTP 500 server error mislabeled as I1 | 14 | 74% |
| Documented case normalization (Keycloak) | 2 | 11% |
| Identity collision from test setup | 3 | 16% |

### A1 — 42 FP across 3 runs

| FP Category | Count |
|---|:--:|
| Vault `user_claim=email` admin-configured behavior | ~14 |
| Vault key rotation TTL grace period (by design) | ~3 |
| Control path / test setup failure | ~10 |
| Test precondition not validated | ~5 |
| HTTP 500 = rejection | ~2 |
| Invalid test premise (e.g., `*` not wildcard) | ~3 |
| Trivially identical input (NFC/NFD ASCII) | ~1 |
| Debatable design / admin config (MFA, callback) | ~4 |

### LLM-Judge variants — FP root-cause decomposition (3-run totals, 2026-04-16 retriage)

Re-classified via 9 parallel agents in [`manual_triage_2026/`](manual_triage_2026/) using the same rules for every variant. Each FP is categorized by the *quality of the finding description*, independent of any internal verdict field:

- **`fabricated`** — description commits to a concrete attack/behavior that does not match any of the 33 ground-truth flaws (made-up narrative or real-but-out-of-scope platform behavior)
- **`hedged`** — description uses speculative language (*suggests*, *may*, *appears*, *cannot confirm*) or declines to commit to a specific violation
- **`setup-artifact`** — description is about test-infrastructure failure (missing session token, `invalid_client`, 409 already-exists) rather than a security behavior
- **`wrong-classif`** — concrete violation but labeled with the wrong invariant axis

**At HIGH confidence only** — findings the LLM itself marked high-confidence:

| Variant | fabricated | hedged | setup-artifact | wrong-classif | Total HIGH FP |
|---|---|---|---|---|---|
| LLM-Judge (no context) | 62 (63%) | 34 (34%) | 3 (3%) | 0 | 99 |
| LLM-Judge + profile    | 36 (24%) | 85 (56%) | 30 (20%) | 1 | 152 |
| LLM-Judge + invariant  | 38 (33%) | 75 (65%) | 2 (2%)   | 0 | 115 |

**At ALL confidence** (apples-to-apples with Full's denominator):

| Variant | fabricated | hedged | setup-artifact | wrong-classif | Total FP |
|---|---|---|---|---|---|
| LLM-Judge (no context) | 62  | 610 | 3   | 0 | **675** |
| LLM-Judge + profile    | 40  | 648 | 183 | 1 | **872** |
| LLM-Judge + invariant  | 40  | 709 | 2   | 0 | **751** |

**Key observation about HIGH-confidence FPs** (why raising the confidence bar does not close the gap to Full):

- `fabricated` stays almost flat across confidence thresholds (62 / 40 / 40 in no_context; growth is tiny in the other variants). The LLM is equally willing to mark real and fabricated attacks as HIGH-confidence.
- In no_context, **63% of HIGH-conf FPs are `fabricated`** — the LLM confidently describes concrete attacks that are neither in the catalog nor real platform vulnerabilities (e.g., "intent-splicing", "application-tag bypass", "policy-toggle bypass").
- In `+ profile`, feeding the LLM the platform's normal-behavior profile makes `setup-artifact` at HIGH jump from 3 → 30 (20% of HIGH FPs) — the profile actively encourages the LLM to mark infrastructure anomalies as security violations.
- `+ invariant` cuts `fabricated` slightly (62 → 38) but `hedged` still dominates (65% of HIGH FPs) — giving invariant definitions doesn't stop descriptively-vague HIGH-confidence output.

This is why HIGH-only precision caps at 18–38%, even though the LLM selected these itself as its most-confident findings.

---

## A1 vs LLM-Judge: complementarity

| Set | Count | Type |
|-----|:--:|------|
| **Both found** | 7 | LG-1, LG-5, CD-4, CD-5, KC-1, VT-5/6, ZT-3 |
| **A1 only** | 19 | Mostly protocol-layer: replay, Conditions, MFA, unsolicited SAML, non-atomic config |
| **LLM-Judge only** | 5 | Mostly state-comparison: AK-6, LG-2, LG-3, LG-6, ZT-1 |

A1 is far broader (26 vs 12 flaws) but LLM-Judge finds 5 flaws A1 misses — these are state-comparison style findings (identity merging by email, audience comparison) that benefit from LLM semantic interpretation of captured state.

## Why extra context does not help LLM-judge (2026-04-16 analysis)

See [cross_variant_analysis.md](cross_variant_analysis.md) for the full write-up. In summary:

- Giving the LLM-judge the sanitized platform profile (`+ profile`) or I1–I5 invariant definitions (`+ invariant`) shifts *which* 12 flaws it latches onto but does **not** expand coverage beyond 12/33.
- At HIGH confidence only, precision is 18–38% across all three variants — a 2.4–4.9× gap to Full's ~90% remains.
- The dominant HIGH-confidence failure mode (24–63% of HIGH-conf FPs depending on variant) is `fabricated`: the LLM confidently describes concrete attacks that are neither in the catalog nor real platform vulnerabilities. Raising the confidence bar does not filter these out because the LLM is equally confident in real and fabricated attack descriptions.
- Full's oracle checks typed-state predicates (`entity_id == expected`, `token.aud ∈ allowed`, `assertion_id ∉ seen`), which cannot produce `fabricated` findings by construction — the assertion space is closed.

---

## Component contribution ranking

Removing each component degrades the system in a distinct way:

1. **Removing Invariants → 100% TP loss** (B vs A1: 0 vs 43 TP/run)
   Without I1–I5 guidance, the LLM cannot generate sequences that probe security boundaries. All findings become noise.

2. **Removing Oracle → 73% TP loss + 10.5× precision drop** (LLM-Judge vs Full: 20.3 vs 75.3 TP/run, 8.4% vs 88.5% precision)
   Even with the best generation, replacing deterministic verdicts with pure LLM judgment causes massive over-reporting (245 findings/run with only 8% precision) and misses 21/33 (64%) of the distinct catalogued flaws.

3. **Removing Examples → 43% TP loss + 13% precision drop** (A1 vs Full: 43 vs 75.3 TP/run, 75% vs 88.5% precision)
   Without attack-pattern examples, the LLM still finds most vulnerability classes (~80%) but produces lower-quality oracle assertions, increasing FP and missing some Cat-B findings.

4. **Removing Mutation sweep → mainly affects I5 coverage** (Full vs A2/A1)
   Sweep provides systematic credential mutations that cover I5 audience-restriction cases the LLM-generated sequences don't reach.

---

## Key takeaway

The Full system's three pillars are not interchangeable:

- **Invariant taxonomy** drives *what* to test (covers 5 invariant classes)
- **Attack examples** drive *how well* to test (sequence quality)
- **Deterministic oracle** drives *whether to trust* the verdict (precision)

LLM-as-judge can substitute for none of these. With the same generation pipeline as Full, replacing the oracle with LLM judgment reduces TP/run by 73%, misses 21/33 distinct flaws, and produces about 26× more false positives.

---

## Per-config detailed TP/FP analysis

Each config has its own detailed analysis file under [`per_ablation/`](per_ablation/):

- [`per_ablation/blind.md`](per_ablation/blind.md) — Blind configuration, all 19 findings reviewed
- [`per_ablation/no_examples.md`](per_ablation/no_examples.md) — A1 no-examples, all ~171 findings reviewed
- [`per_ablation/llm_judge_no_context.md`](per_ablation/llm_judge_no_context.md) — LLM-judge with only the trace (2026-04-16 retriage)
- [`per_ablation/llm_judge_profile.md`](per_ablation/llm_judge_profile.md) — LLM-judge + platform profile context
- [`per_ablation/llm_judge_invariant.md`](per_ablation/llm_judge_invariant.md) — LLM-judge + I1–I5 invariant definitions

Supporting material:

- [`cross_variant_analysis.md`](cross_variant_analysis.md) — cross-variant comparison of the three LLM-judge configurations at HIGH / HIGH+MEDIUM / ALL confidence thresholds, with the structural FP explanation
- [`manual_triage_2026/`](manual_triage_2026/) — per-finding agent-generated TP/FP labels for all 9 runs (3 variants × 3 runs) and the aggregated results table
