# Ablation — Reproduction & Analysis Guide

This directory contains all analysis artifacts for the paper's ablation study (§5) and the reproduction instructions for every ablation configuration.

These are primary experiment artifacts under `results/`; they are not superseded by the supplemental [`../../../Recall/`](../../../Recall/README.md) benchmark. Existing result directories and recorded scripts are preserved evidence and must not be overwritten.

---

## 1. Configurations

| Tag | Directory prefix | Generation | Verdict | Description |
|---|---|---|---|---|
| **Full** | `evaluation/exp1`, `evaluation/exp2`, `evaluation/exp3` | invariant + examples | deterministic oracle (I1–I5) + KBF + sweep | The published system |
| **A1** (no_examples) | `a1_no_examples*` | invariant only | deterministic | Removes CVE attack examples |
| **B** (blind) | `baseline*` | generic prompt (no invariants, no examples) | deterministic | Worst-case generation |
| **A2** (no_sweep) | `a2_no_sweep*` | invariant + examples | deterministic, no mutation sweep | Removes the I5-sweep net |
| **LLM-Judge** | `llm_judge_r1`, `llm_judge_r2`, `llm_judge_r3` | invariant + examples (same as Full) | pure LLM judge, no context in judge prompt | Replaces verdict layer |
| **LLM-Judge + profile** | `llm_judge_profile_r1-r3` | invariant + examples | LLM judge, sanitized platform profile in judge prompt | Tests whether profile helps judge |
| **LLM-Judge + invariant** | `llm_judge_invariant_r1-r3` | invariant + examples | LLM judge, I1–I5 definitions in judge prompt | Tests whether invariant defs help judge |

Each configuration × run produces `13` campaign directories (one per platform × protocol), each with `unique_findings.json` + `sequences.json` + `summary.json`.

---

## 2. Prerequisites for reproduction

1. Set `OPENAI_API_KEY` — every runner script expects this via environment variable. Scripts no longer contain hard-coded keys (scrubbed 2026-04-16); they will fail loudly with `OPENAI_API_KEY: parameter null or not set` if unset.

   ```bash
   export OPENAI_API_KEY="sk-proj-..."
   ```

2. Platform services must be runnable. See [`../../../docker/platform-images.yml`](../../../docker/platform-images.yml) for the current pinned Compose definitions and the top-level [`../../../README.md`](../../../README.md) for validated start/replay commands.

3. Python dependencies, from `fuzzer/`: `python3 -m pip install -r requirements.txt`.

4. Working directory for campaign commands: the current checkout's `fuzzer/` directory.

---

## 3. Re-running each configuration

Results go to `results/ablation/<exp-name>/<platform>/<protocol>/<eval-mode>/campaign_<ts>/`.

The `results/**/run_script_*.sh` files are exact historical provenance and intentionally retain the original `/home/ubuntu/broker` checkout path. `scripts/run_evaluation.sh` and `scripts/run_all_experiments.sh` also contain that path. On a machine with another checkout there, running them unchanged can execute the wrong clone. For a current run, use the direct campaign interface documented in [`../../../README.md`](../../../README.md), pass the matching saved `evaluation-exp1` profile explicitly, select the eval mode below, and write to a new `artifacts/` directory. Only use a recorded orchestrator after reviewing/making its checkout root portable.

Single-campaign template:

```bash
python3 -m src.stateful.campaign_runner \
  --platform <platform> \
  --protocol <oidc_jwt-or-saml> \
  --profile src/profiles/<evaluation-exp1-profile>.json \
  --eval-mode <mode> \
  --setup-platform \
  --output-dir artifacts/ablation-reproduction/<run-name>/<platform>/<protocol>
```

### 3.1 Current eval-mode mapping

Use the single-campaign template above with this mapping, repeating it for the 13 profile/platform/protocol pairs and three fresh run roots where the study has three rounds:

| Configuration | Current `--eval-mode` | Recorded data |
|---|---|---|
| Full | `full` | [`../../evaluation/`](../../evaluation/) |
| A1 (no examples) | `no_examples` | [`../a1_no_examples/`](../a1_no_examples/) and `a1_no_examples_r2/r3` |
| B (blind) | `blind` | [`../baseline/`](../baseline/) and `baseline_r2/r3` |
| A2 (no sweep) | `oracle_gen` | [`../a2_no_sweep/`](../a2_no_sweep/) |
| LLM-Judge | `llm_judge` | [`../llm_judge_r1/`](../llm_judge_r1/) through `r3` |
| LLM-Judge + profile | `llm_judge_profile` | [`../llm_judge_profile_r1/`](../llm_judge_profile_r1/) through `r3` |
| LLM-Judge + invariant | `llm_judge_invariant` | [`../llm_judge_invariant_r1/`](../llm_judge_invariant_r1/) through `r3` |

`oracle_gen` is the current named mode for invariant/example-guided generation with deterministic oracle and no mutation sweep. The old prototype `--no-sweep` flag appearing in planning/provenance files is not a current CLI option.

Historical wrapper names are `scripts/run_evaluation.sh`, `scripts/run_ablation*.sh`, and the `run_script_*.sh` files linked above. They document the original orchestration but, as noted above, are not portable until their checkout root is reviewed.

---

## 4. Analysis pipeline

Once all `unique_findings.json` files exist, analysis runs in two stages:

### 4.1 Per-finding TP/FP triage (manual, agent-assisted)

The three LLM-judge variants are re-triaged together for method consistency. Output: one Python file per (variant × run) under `manual_triage_2026/`:

- `no_context_{r1,r2,r3}_triage.py`
- `profile_{r1,r2,r3}_triage.py`
- `invariant_{r1,r2,r3}_triage.py`

Each file contains a `TRIAGE` dict mapping `(platform, protocol, idx) → {verdict, conf, invariant, label, reason, desc_snippet}`.

**To regenerate from scratch**, launch 9 agents with the triage prompt skeleton used for the 2026-04-16 run. The prompt template is recorded in `manual_triage_2026/triage_prompt_template.md` (see below). Each agent reads the 13 `unique_findings.json` files for its variant × run and classifies every finding against the 33 ground-truth flaws, writing its output file directly.

### 4.2 Aggregation

```bash
cd results/ablation/analysis
python3 aggregate_triage.py
```

Reads all 9 triage files and produces:

- `manual_triage_2026/aggregate_results.json` — structured data (per run × per threshold: HIGH, HIGH+MEDIUM, ALL)
- `manual_triage_2026/aggregate_results.md` — human-readable tables (per-run counts, cross-variant comparison at each confidence threshold, FP root-cause breakdown, union flaws)

### 4.3 Per-ablation TP/FP reports

One human-readable MD per ablation, in [`per_ablation/`](per_ablation/):

- [`per_ablation/blind.md`](per_ablation/blind.md) — Blind, all 19 findings reviewed (hand-written, 2026-04-08)
- [`per_ablation/no_examples.md`](per_ablation/no_examples.md) — A1 no-examples, all ~171 findings reviewed (hand-written)
- [`per_ablation/llm_judge_no_context.md`](per_ablation/llm_judge_no_context.md) — LLM-judge plain, agent-triaged 2026-04-16
- [`per_ablation/llm_judge_profile.md`](per_ablation/llm_judge_profile.md) — LLM-judge + profile, agent-triaged 2026-04-16
- [`per_ablation/llm_judge_invariant.md`](per_ablation/llm_judge_invariant.md) — LLM-judge + invariant definitions, agent-triaged 2026-04-16

The three LLM-judge docs are regenerated from [`manual_triage_2026/`](manual_triage_2026/) by [`scripts_gen_per_ablation.py`](scripts_gen_per_ablation.py): edit the triage dicts to correct a label, then re-run the generator to rebuild all three docs in a consistent format.

### 4.4 Cross-variant comparison

[`cross_variant_analysis.md`](cross_variant_analysis.md) — 2026-04-16 comparison of the three LLM-judge variants at HIGH / HIGH+MEDIUM / ALL confidence thresholds, with the structural FP explanation (typed-state oracle vs text classification).

---

## 5. Key aggregate numbers

Produced by `aggregate_triage.py` on 2026-04-16; canonical source for all downstream consumers (paper table, variant comparison).

### ALL (HIGH+MEDIUM+LOW) — apples-to-apples with Full

| Variant | Findings/run | TP/run | Precision | Flaws (union) |
|---|---|---|---|---|
| Full | 84.0 ± 26.2 | 75.3 ± 27.2 | 88.5% | 33/33 |
| LLM-Judge (no context) | 245.3 ± 22.7 | 20.3 ± 2.1 | 8.4% ± 1.6% | 12/33 |
| LLM-Judge + profile | 302.3 ± 28.0 | 11.7 ± 2.1 | 3.9% ± 0.5% | 12/33 |
| LLM-Judge + invariant | 267.7 ± 12.3 | 17.3 ± 4.5 | 6.5% ± 1.6% | 12/33 |

### HIGH only (excludes LOW/MEDIUM confidence)

| Variant | Findings/run | TP/run | Precision | Flaws (union) |
|---|---|---|---|---|
| LLM-Judge (no context) | 52.7 ± 9.6 | 19.7 ± 3.2 | 38.2% ± 10.2% | 12/33 |
| LLM-Judge + profile | 62.0 ± 6.9 | 11.3 ± 2.3 | 18.2% ± 1.6% | 12/33 |
| LLM-Judge + invariant | 55.3 ± 4.5 | 17.0 ± 4.0 | 30.7% ± 6.1% | 12/33 |

### HIGH + MEDIUM

| Variant | Findings/run | TP/run | Precision | Flaws (union) |
|---|---|---|---|---|
| LLM-Judge (no context) | 194.7 ± 17.0 | 20.3 ± 2.1 | 10.5% ± 1.9% | 12/33 |
| LLM-Judge + profile | 233.0 ± 27.2 | 11.7 ± 2.1 | 5.0% ± 0.4% | 12/33 |
| LLM-Judge + invariant | 205.0 ± 12.3 | 17.3 ± 4.5 | 8.5% ± 2.1% | 12/33 |

See [`cross_variant_analysis.md`](cross_variant_analysis.md) §3–§5 for the FP root-cause breakdown (fabricated / hedged / setup-artifact) and the structural explanation of why adding profile/invariant context does not close the gap to Full.

---

## 6. File map

```
analysis/
├── README.md                               ← this file — reproduction guide for every config
├── ABLATION_SUMMARY.md                     ← top-level results table + component-contribution ranking
├── cross_variant_analysis.md               ← 3-way LLM-judge comparison + FP structural explanation
├── aggregate_triage.py                     ← reads manual_triage_2026/ → aggregate_results.{json,md}
├── scripts_gen_per_ablation.py             ← regenerates per_ablation/llm_judge_*.md from triage dicts
├── per_ablation/                           ← one TP/FP doc per ablation
│   ├── blind.md                            ← Blind configuration
│   ├── no_examples.md                      ← A1 no-examples configuration
│   ├── llm_judge_no_context.md             ← plain LLM judge
│   ├── llm_judge_profile.md                ← LLM judge + platform profile
│   └── llm_judge_invariant.md              ← LLM judge + I1–I5 invariant defs
└── manual_triage_2026/                     ← per-finding raw labels (source of truth for LLM-judge docs)
    ├── triage_prompt_template.md           ← prompt used for 9 parallel agents
    ├── {no_context,profile,invariant}_r{1,2,3}_triage.py   (9 files: key = (platform, protocol, idx))
    ├── aggregate_results.json              ← structured aggregate (per run × threshold)
    └── aggregate_results.md                ← human-readable aggregate tables
```

---

## 7. Notes on data integrity

- All run scripts in `results/ablation/*/run_script_*.sh` and `fuzzer/scripts/run_*.sh` had their hard-coded `OPENAI_API_KEY` values replaced with `${OPENAI_API_KEY:?Set OPENAI_API_KEY env var before running}` on 2026-04-16. Re-runs require the env var to be set.
- The 9 triage files in `manual_triage_2026/` were produced by 9 parallel Claude Code subagents, each given the same ground-truth table and classification rules. Labels are deterministic given the rules; any agent-agent variance is in borderline `fabricated` vs `hedged` vs `setup-artifact` calls on FP descriptions (see `aggregate_triage.py:FP_MAP` for how the raw per-agent reason strings are normalized into the 4-bucket FP taxonomy used in all analysis outputs).
- A prior 2026-04-10 LLM-judge review (since deleted) reported 19.7 TP / 13 flaws for the no-context variant. The 2026-04-16 retriage gives 20.3 TP / 12 flaws; the 1-TP and 1-flaw delta comes from LG-4 being removed from the 33-flaw ground truth between the two analyses. The current `per_ablation/llm_judge_no_context.md` numbers are canonical.
