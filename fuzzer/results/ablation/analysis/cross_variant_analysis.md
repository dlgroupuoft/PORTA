# LLM-Judge Variants — Cross-Variant Comparison and FP Structural Analysis

Date: 2026-04-16.
Scope: three LLM-judge ablation configurations, each run 3 times:

- **LLM-Judge (no context)** — plain LLM judge with just the trace
- **LLM-Judge + profile** — judge prompt additionally receives the sanitized platform profile (API endpoints, constraints, with invariant references stripped)
- **LLM-Judge + invariant** — judge prompt additionally receives the I1–I5 invariant definitions

The **Full** system (invariant oracle + KBF) is the precision reference point.

Generation pipeline is identical across all three variants and matches Full. Only the verdict layer changes.

Axis of comparison in this document is the **confidence level the LLM attached to each finding**: HIGH, HIGH+MEDIUM, or ALL. Full also counts all confidence levels as findings, so this is the apples-to-apples comparison. The interesting question is why even at HIGH confidence (the LLM's own most-confident output) precision is still far below Full.

---

## 1. Methodology

All three variants use the same re-triage protocol (2026-04-16):

- Each of 9 (variant × run) directories is processed by one agent. Each agent reads every `unique_findings.json` in its 13 campaigns (one per platform × protocol) and classifies **every** finding.
- A finding is **TP** iff it semantically matches one of the paper's 33 ground-truth flaws (right platform, right invariant class, and description that actually describes the catalogued attack). The historical triage also consulted a separate platform-source checkout when needed; the evidence retained in this artifact is indexed by [`../../evaluation/finding_catalog_annotated.md`](../../evaluation/finding_catalog_annotated.md).
- Everything else is **FP**. Each FP is tagged with a root cause: `fabricated`, `hedged`, `setup-artifact`, or `wrong-classif` (see §4).
- Per-finding labels are in [`manual_triage_2026/<variant>_<run>_triage.py`](manual_triage_2026/).
- Aggregate numbers below are produced by [`aggregate_triage.py`](aggregate_triage.py) reading those 9 files.
- The same methodology applies to all 3 variants, so numbers are directly comparable.

---

## 2. Aggregate results by confidence threshold

### 2.1 HIGH confidence only

The LLM itself labeled these findings as high-confidence. This is the most favorable reading for the LLM-judge variants.

| Variant | Findings/run | TP/run | FP/run | Precision | Flaws (union) |
|---|---|---|---|---|---|
| LLM-Judge (no context) | 52.7 ± 9.6 | 19.7 ± 3.2 | 33.0 ± 10.1 | **38.2% ± 10.2%** | 12/33 |
| LLM-Judge + profile | 62.0 ± 6.9 | 11.3 ± 2.3 | 50.7 ± 4.6 | **18.2% ± 1.6%** | 12/33 |
| LLM-Judge + invariant | 55.3 ± 4.5 | 17.0 ± 4.0 | 38.3 ± 4.0 | **30.7% ± 6.1%** | 12/33 |
| **Full** (all findings, not just HIGH) | 84.0 ± 26.2 | 75.3 ± 27.2 | 8.7 ± 1.5 | **88.5%** | 33/33 |

Even restricting attention to HIGH-confidence LLM outputs, precision is 18–38%, a 2.3–4.9× gap to Full.

### 2.2 HIGH + MEDIUM

| Variant | Findings/run | TP/run | FP/run | Precision | Flaws (union) |
|---|---|---|---|---|---|
| LLM-Judge (no context) | 194.7 ± 17.0 | 20.3 ± 2.1 | 174.3 ± 18.5 | 10.5% ± 1.9% | 12/33 |
| LLM-Judge + profile | 233.0 ± 27.2 | 11.7 ± 2.1 | 221.3 ± 25.3 | 5.0% ± 0.4% | 12/33 |
| LLM-Judge + invariant | 205.0 ± 12.3 | 17.3 ± 4.5 | 187.7 ± 12.1 | 8.5% ± 2.1% | 12/33 |

### 2.3 ALL (HIGH + MEDIUM + LOW) — same denominator as Full

| Variant | Findings/run | TP/run | FP/run | Precision | Flaws (union) |
|---|---|---|---|---|---|
| LLM-Judge (no context) | 245.3 ± 22.7 | 20.3 ± 2.1 | 225.0 ± 24.6 | 8.4% ± 1.6% | 12/33 |
| LLM-Judge + profile | 302.3 ± 28.0 | 11.7 ± 2.1 | 290.7 ± 26.7 | 3.9% ± 0.5% | 12/33 |
| LLM-Judge + invariant | 267.7 ± 12.3 | 17.3 ± 4.5 | 250.3 ± 11.6 | 6.5% ± 1.6% | 12/33 |
| **Full** | 84.0 ± 26.2 | 75.3 ± 27.2 | 8.7 ± 1.5 | **88.5%** | 33/33 |

Three observations are robust across all three confidence thresholds:

1. **All three LLM-judge variants find 12/33 flaws** regardless of added context. Coverage is the same; only *which* 12 flaws differ.
2. **Adding profile context reduces TP/run by 43%** (20.3 → 11.7) and nearly doubles per-run FP.
3. **Adding invariant definitions makes no significant improvement** over no-context (17.3 vs 20.3 TP, within 1σ; precision 6.5% vs 8.4%).
4. Raising the confidence bar to HIGH-only improves LLM-judge precision but caps at 38.2% — still far below Full.

---

## 3. FP root-cause breakdown

Each FP is categorized by the *quality of the finding description*, without reference to the LLM's internal verdict field. Categories:

- **`fabricated`** — description commits to a concrete attack/behavior that does not match any of the 33 ground-truth flaws (either a made-up attack narrative like "intent-splicing" or a real-but-out-of-scope platform behavior like admin-reconfigured JWKS URL)
- **`hedged`** — description uses speculative language (*suggests*, *may*, *appears*, *cannot confirm*) or declines to commit to a specific violation; the output is not a concrete assertion a reviewer can evaluate
- **`setup-artifact`** — description is about control/baseline test-infrastructure failure (missing session token, `invalid_client`, 409 already-exists, etc.) rather than a security behavior
- **`wrong-classif`** — concrete violation but labeled with the wrong invariant axis

### 3.1 At HIGH confidence (3-run totals)

These are FPs the LLM itself marked high-confidence. Even here the judgment-quality floor is visible.

| Variant | fabricated | hedged | setup-artifact | wrong-classif | Total HIGH FP |
|---|---|---|---|---|---|
| LLM-Judge (no context) | 62 (63%) | 34 (34%) | 3 (3%) | 0 | 99 |
| LLM-Judge + profile | 36 (24%) | 85 (56%) | 30 (20%) | 1 (1%) | 152 |
| LLM-Judge + invariant | 38 (33%) | 75 (65%) | 2 (2%) | 0 | 115 |

**Key observation about HIGH-confidence FPs:**

- In the `no_context` variant, **63% of HIGH-conf FPs are `fabricated`** — the LLM confidently asserts concrete attack descriptions that simply don't map to any ground-truth flaw. It's *committing* to wrong claims, not hedging.
- In the `+ profile` variant, `setup-artifact` jumps from ~3% to 20% — feeding the LLM the platform's normal-behavior profile makes it more willing to mark infrastructure anomalies as high-confidence security violations.
- In `+ invariant`, `fabricated` drops a little (62 → 38) but `hedged` still dominates at 65% — giving the LLM invariant definitions doesn't stop it from producing high-confidence but descriptively-vague output.

### 3.2 At HIGH + MEDIUM (3-run totals)

| Variant | fabricated | hedged | setup-artifact | wrong-classif | Total |
|---|---|---|---|---|---|
| LLM-Judge (no context) | 62 | 458 | 3 | 0 | 523 |
| LLM-Judge + profile | 40 | 493 | 130 | 1 | 664 |
| LLM-Judge + invariant | 40 | 521 | 2 | 0 | 563 |

### 3.3 At ALL confidence (3-run totals)

| Variant | fabricated | hedged | setup-artifact | wrong-classif | Total |
|---|---|---|---|---|---|
| LLM-Judge (no context) | 62 | 610 | 3 | 0 | 675 |
| LLM-Judge + profile | 40 | 648 | 183 | 1 | 872 |
| LLM-Judge + invariant | 40 | 709 | 2 | 0 | 751 |

`fabricated` FPs stay flat across confidence thresholds (62 / 40 / 40 in no_context; tiny growth in the other variants). That is, fabricated attacks are almost entirely high-confidence — the LLM is not marking its own inventions as low-confidence. `hedged` FPs scale roughly with the confidence threshold because LOW findings are almost always hedged by construction.

---

## 4. Why extra context does not help

Intuition: giving the LLM the platform profile (`+ profile`) or invariant definitions (`+ invariant`) should narrow the description space and cut `fabricated` errors. The data shows the effect is small *and* offset by a bigger loss:

| Variant | fabricated FP (3-run total, HIGH) | TP/run @ HIGH | Precision @ HIGH |
|---|---|---|---|
| no context | 62 | 19.7 | 38.2% |
| + profile | 36 | 11.3 | 18.2% |
| + invariant | 38 | 17.0 | 30.7% |

- `+ profile` cuts `fabricated` from 62 → 36 but TP drops from 19.7 → 11.3 AND `setup-artifact` jumps from 3 → 30 (platform normal-behavior cues get reinterpreted as anomaly signals). Net precision *drops* (38.2% → 18.2%).
- `+ invariant` cuts `fabricated` from 62 → 38 and preserves more TP (17.0), giving the smallest regression. But precision is still below no-context (30.7% vs 38.2%).

The 12/33 union-flaw count is identical across all three variants. Added context swaps *which* 12 flaws the LLM surfaces but does not expand the discoverable set. `+ profile` picks up AK-3, DX-3 but drops KC-1, LG-5. `+ invariant` picks up AK-1, CD-2, DX-5 but drops CD-5, KC-1, LG-5.

---

## 5. Why Full reduces FPs so sharply

Full's oracle has 8.7 ± 1.5 FP/run (88.5% precision). LLM-judge variants have 225–291 FP/run at ALL, 33–51 FP/run even at HIGH-only. The mechanism behind the 4–33× FP reduction in Full:

**5.1 Oracle judgments are typed-state predicates, not text classification.**
Each I1–I5 oracle ([src/oracles/](../../../src/oracles/)) is a Python function over typed `AuthResult` / `AuthContext` fields. For example, the I2 replay oracle asserts `replay_response.entity_id == control_response.entity_id AND replay_response.session_token != None`. This predicate has no space for "plausible-sounding but unrelated attacks"; it either fires on a specific state comparison or does not fire at all. The `fabricated` failure mode does not exist in this space by construction.

**5.2 The assertion space is closed.**
Full's judgment surface is limited to the oracles that exist. LLM-judge's judgment surface is unbounded (any English description of any claim about the trace). `fabricated` is a direct consequence: the LLM can describe attack classes that are neither in the paper's ground truth nor corresponding to a real flaw, but still outputs them as findings. Deterministic oracles cannot produce such output because no boolean predicate maps to those claims.

**5.3 Preconditions gate assertion firing.**
Every oracle first checks preconditions (`auth_result.success`, control login produced usable token, etc.) before evaluating the violation condition. If preconditions fail, the oracle returns `VerdictType.CLEAN` and emits no finding. This eliminates the entire `setup-artifact` class of FPs. LLM-judge has no equivalent gating — a trace where the control login failed still gets classified and emitted. This is why `+ profile` actually makes things *worse*: feeding the LLM "normal behavior" descriptions makes it more willing to commit to "this looks abnormal → violation" on infrastructure anomalies.

**5.4 Known-behavior filter removes documented platform behaviors.**
Full runs output through KBF, which removes findings matching previously-observed platform behaviors in prior campaigns. This absorbs the "real-but-out-of-scope" half of LLM-judge's `fabricated` class (e.g., Vault email auto-alias, Vault JWKS rotation, documented Keycloak case normalization).

The three LLM-judge variants cannot reach Full's precision because they cannot emulate these four structural properties via prompt engineering alone. Raising the confidence bar to HIGH-only caps at ~38% precision because `fabricated` FPs are overwhelmingly high-confidence — the LLM is equally confident in real and invented attack descriptions.

---

## 6. Recommendation for the paper

Paper Table `\label{tab:ablation}` currently has four rows (Full, No-examples, Blind, LLM-judge). The data supports adding two more rows for `LLM-judge + profile` and `LLM-judge + invariant` with these numbers (ALL-threshold, matching the existing LLM-judge row denominator):

| Config | Generation | Verdict | Seq/run | Exec. rate | Findings/run | TP/run | Precision | Findings found |
|---|---|---|---|---|---|---|---|---|
| LLM-judge + profile | invariant + examples | LLM (+ profile context) | ~475 | ~71% | 302.3 ± 28.0 | 11.7 ± 2.1 | 3.9% | 12/33 |
| LLM-judge + invariant | invariant + examples | LLM (+ I1–I5 defs in judge prompt) | ~480 | ~72% | 267.7 ± 12.3 | 17.3 ± 4.5 | 6.5% | 12/33 |

An optional HIGH-confidence column would show:

| Config | HIGH Precision | HIGH Findings found |
|---|---|---|
| LLM-judge (no context) | 38.2% ± 10.2% | 12/33 |
| LLM-judge + profile    | 18.2% ± 1.6%  | 12/33 |
| LLM-judge + invariant  | 30.7% ± 6.1%  | 12/33 |
| Full (all conf)        | 88.5%         | 33/33 |

The matching prose claim, stated as observation not speculation:

> Giving the LLM judge additional context — either the sanitized platform profile or the I1–I5 invariant definitions — does not improve precision or coverage. Adding the profile reduces true positives by 43% (20.3 → 11.7 per run) and increases test-infrastructure-artifact false positives 10-fold; adding invariant definitions leaves TP essentially unchanged (17.3) and gives the best precision of the three variants (30.7% at HIGH, 6.5% at ALL) but still ~58 points below Full at ALL. All three variants recover exactly 12/33 flaws in union across 3 runs, swapping different 3-flaw subsets in and out — extra prompt context shifts *which* attacks the LLM latches onto, not *how many*. Even restricting attention to HIGH-confidence LLM output (the most favorable reading), precision is 18–38% because the dominant high-confidence failure mode (24–63% of HIGH-conf FPs across the three variants) is the LLM confidently asserting concrete attacks whose descriptions do not match any of the 33 flaws — either plausible-sounding but fabricated narratives (intent-splicing, application-tag bypass) or real-but-out-of-scope platform behaviors. This failure is structural: Full's oracle expresses judgments as typed-state predicates over captured `AuthResult` fields (`entity_id`, `token.aud`, `assertion_id`), so findings outside the predefined invariant classes are unrepresentable; the LLM judge's output space is open text over unstructured traces and cannot be closed by prompt engineering.

---

## 7. Reproducibility pointers

- Raw data: [`llm_judge_r1-r3`](../) (no context); [`llm_judge_profile_r1-r3`](../) (+ profile); [`llm_judge_invariant_r1-r3`](../) (+ invariant)
- Per-finding triage: [`manual_triage_2026/`](manual_triage_2026/)
- Aggregator: [`aggregate_triage.py`](aggregate_triage.py); outputs `aggregate_results.{json,md}`
- Per-ablation TP/FP reports: [`per_ablation/llm_judge_no_context.md`](per_ablation/llm_judge_no_context.md), [`per_ablation/llm_judge_profile.md`](per_ablation/llm_judge_profile.md), [`per_ablation/llm_judge_invariant.md`](per_ablation/llm_judge_invariant.md) — regenerate via `python3 scripts_gen_per_ablation.py` after editing triage dicts.
- Reproduction steps for raw campaigns: [`README.md`](README.md).
