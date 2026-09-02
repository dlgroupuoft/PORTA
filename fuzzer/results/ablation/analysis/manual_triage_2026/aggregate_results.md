# Manual Triage 2026 — Aggregate Results

Aggregated from 9 agent-generated triage files in `manual_triage_2026/`. Each variant × run file contains per-finding TP/FP labels.

Axis = **confidence threshold** (HIGH / HIGH+MEDIUM / ALL). Full counts all confidence levels as findings, so ALL is the apples-to-apples comparison. HIGH-only is the most favorable reading for each LLM-judge variant.

## Per-run counts (ALL threshold = all findings)

| Variant | Run | Findings | TP | FP | Precision | Flaws/run |
|---|---|---|---|---|---|---|
| no_context | no_context_r1 | 221 | 22 | 199 | 10.0% | 10 |
| no_context | no_context_r2 | 249 | 21 | 228 | 8.4% | 9 |
| no_context | no_context_r3 | 266 | 18 | 248 | 6.8% | 9 |
| profile | profile_r1 | 270 | 10 | 260 | 3.7% | 6 |
| profile | profile_r2 | 320 | 11 | 309 | 3.4% | 8 |
| profile | profile_r3 | 317 | 14 | 303 | 4.4% | 9 |
| invariant | invariant_r1 | 278 | 22 | 256 | 7.9% | 10 |
| invariant | invariant_r2 | 271 | 13 | 258 | 4.8% | 5 |
| invariant | invariant_r3 | 254 | 17 | 237 | 6.7% | 8 |

## HIGH only threshold

| Variant | Findings/run | TP/run | FP/run | Precision | Flaws (union) |
|---|---|---|---|---|---|
| no_context | 52.7±9.6 | 19.7±3.2 | 33.0±10.1 | 38.2%±10.2% | 12/33 |
| profile | 62.0±6.9 | 11.3±2.3 | 50.7±4.6 | 18.2%±1.6% | 12/33 |
| invariant | 55.3±4.5 | 17.0±4.0 | 38.3±4.0 | 30.7%±6.1% | 12/33 |

## HIGH + MEDIUM threshold

| Variant | Findings/run | TP/run | FP/run | Precision | Flaws (union) |
|---|---|---|---|---|---|
| no_context | 194.7±17.0 | 20.3±2.1 | 174.3±18.5 | 10.5%±1.9% | 12/33 |
| profile | 233.0±27.2 | 11.7±2.1 | 221.3±25.3 | 5.0%±0.4% | 12/33 |
| invariant | 205.0±12.3 | 17.3±4.5 | 187.7±12.1 | 8.5%±2.1% | 12/33 |

## ALL (HIGH + MEDIUM + LOW) threshold

| Variant | Findings/run | TP/run | FP/run | Precision | Flaws (union) |
|---|---|---|---|---|---|
| no_context | 245.3±22.7 | 20.3±2.1 | 225.0±24.6 | 8.4%±1.6% | 12/33 |
| profile | 302.3±28.0 | 11.7±2.1 | 290.7±26.7 | 3.9%±0.5% | 12/33 |
| invariant | 267.7±12.3 | 17.3±4.5 | 250.3±11.6 | 6.5%±1.6% | 12/33 |

## FP root-cause breakdown (ALL threshold, 3-run totals)

Each FP is categorized by the quality of the finding description, independent of the LLM's verdict field:

- **fabricated** — concrete description of an attack/behavior that does not match any of the 33 flaws (made-up or out-of-scope).
- **hedged** — speculative language (suggests/may/appears/...) or declines to commit to a specific violation.
- **setup-artifact** — test-infrastructure failure mistaken for a security behavior.
- **wrong-classif** — concrete violation labeled under the wrong invariant axis.

| Variant | fabricated | hedged | setup-artifact | wrong-classif | Total FP |
|---|---|---|---|---|---|
| no_context | 62 | 610 | 3 | 0 | 675 |
| profile | 40 | 648 | 183 | 1 | 872 |
| invariant | 40 | 709 | 2 | 0 | 751 |

## FP root-cause breakdown at HIGH confidence (3-run totals)

HIGH-confidence FPs reveal the LLM's judgment-quality floor — it selected these itself as high-confidence.

| Variant | fabricated | hedged | setup-artifact | wrong-classif | Total FP @ HIGH |
|---|---|---|---|---|---|
| no_context | 62 | 34 | 3 | 0 | 99 |
| profile | 36 | 85 | 30 | 1 | 152 |
| invariant | 38 | 75 | 2 | 0 | 115 |

## Flaws recovered by variant (union across 3 runs, ALL threshold)

- **no_context** (12/33): AK-6, CD-4, CD-5, KC-1, LG-1, LG-2, LG-3, LG-5, LG-6, VT-5/6, ZT-1, ZT-3
- **profile** (12/33): AK-3, AK-6, CD-4, CD-5, DX-3, LG-1, LG-2, LG-3, LG-6, VT-5/6, ZT-1, ZT-3
- **invariant** (12/33): AK-1, AK-6, CD-2, CD-4, DX-5, LG-1, LG-2, LG-3, LG-6, VT-5/6, ZT-1, ZT-3
