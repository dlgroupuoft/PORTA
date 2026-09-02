# Ablation Experiment Plan

> **Historical planning document.** This records the design process and contains obsolete prototype flags and the original `/home/ubuntu/broker` checkout path. It is not a current launcher. Use [`../README.md`](../README.md) and [`../results/ablation/analysis/README.md`](../results/ablation/analysis/README.md) for runnable commands; preserve this file as experiment provenance.

## Purpose

RQ4 asks: what does each component contribute?
We compare the full system against 3 ablations, each removing one component.

## Configurations

| Config | Name | Generation | Verdict | What's removed |
|--------|------|-----------|---------|----------------|
| **B** | Baseline | Blind (no invariant, no examples) | LLM-as-judge (no assertion oracle) | Everything |
| **A1** | +Invariants | Invariant-guided (no examples) | Assertion oracle | Attack-pattern examples |
| **A2** | +Examples | Invariant-guided + examples | Assertion oracle | Mutation sweep |
| **Full** | Full system | Invariant-guided + examples | All oracles + sweep | Nothing |

Note: "Full" is what we already ran 3 times. We only need to run B, A1, A2 once each.

## How to implement each config

### B: Baseline (blind generation, LLM-as-judge)

**Generation change**: Remove invariant definitions and attack examples from the LLM prompt.
The LLM only receives the Platform Profile and a generic instruction: "Generate test sequences
that probe the authentication and authorization logic of this platform."

**Verdict change**: Disable the assertion oracle (step 6). Instead, after execution,
send the captured HTTP responses + status codes to the LLM and ask "Does this behavior
indicate a security vulnerability?" (LLM-as-judge). Keep L1 syntactic and L2 identity
checks active (they are non-LLM).

**Implementation**:
```bash
python3 -m src.stateful.campaign_runner \
    --profile <profile> \
    --invariants I1,I2,I3,I4,I5 \
    --sequences-per-invariant 10 \
    --blind-generation \          # Flag to strip invariant+examples from prompt
    --llm-judge \                 # Flag to use LLM verdict instead of assertion oracle
    --no-mutation-sweep \         # Disable sweep
    --output-dir results/ablation/baseline/<platform>/<protocol>
```

If `--blind-generation` and `--llm-judge` flags don't exist yet, they need to be added to
`campaign_runner.py`. The changes are:
1. `--blind-generation`: In `generation_strategy.py`, skip the invariant definition block
   and attack-pattern examples in the prompt. Keep only the Platform Profile.
2. `--llm-judge`: In `sequence_executor.py`, after execution, instead of evaluating
   `oracle_checks` assertions, send a prompt to the LLM with captured values and ask
   for a vulnerability judgment.

### A1: +Invariants (no examples)

**Generation change**: Include invariant definitions in the prompt but remove attack-pattern
examples (the CVE-based few-shot examples).

**Verdict change**: Use the assertion oracle as normal. Disable mutation sweep.

**Implementation**:
```bash
python3 -m src.stateful.campaign_runner \
    --profile <profile> \
    --invariants I1,I2,I3,I4,I5 \
    --sequences-per-invariant 10 \
    --no-examples \               # Flag to remove few-shot attack examples
    --no-mutation-sweep \
    --output-dir results/ablation/a1_no_examples/<platform>/<protocol>
```

If `--no-examples` doesn't exist, add it to `generation_strategy.py` to skip the
attack-pattern examples block in the generation prompt.

### A2: +Examples (no sweep)

**Generation change**: Full generation (invariants + examples). Same as Full system.

**Verdict change**: Disable mutation sweep only.

**Implementation**:
```bash
python3 -m src.stateful.campaign_runner \
    --profile <profile> \
    --invariants I1,I2,I3,I4,I5 \
    --sequences-per-invariant 10 \
    --no-mutation-sweep \
    --output-dir results/ablation/a2_no_sweep/<platform>/<protocol>
```

`--no-mutation-sweep` likely already exists (check `campaign_runner.py` for sweep flags).

## Execution plan

Run each ablation config once across all 13 platform×protocol configurations.
Use the **evaluation-exp1** profiles (same as the first evaluation run) so results
are comparable.

```bash
# Create ablation results directory
mkdir -p results/ablation/{baseline,a1_no_examples,a2_no_sweep}

# Run each config using run_all_experiments.sh with appropriate flags
# Modify run_all_experiments.sh to accept --extra-flags parameter, or
# write a dedicated ablation launcher script.
```

### Launcher script structure

```bash
#!/usr/bin/env bash
# scripts/run_ablation.sh
export PATH=/usr/bin:/usr/local/bin:$PATH
cd /home/ubuntu/broker/fuzzer

PROFILES_EXP="evaluation-exp1"  # Use exp1 profiles for all ablations

for CONFIG in baseline a1_no_examples a2_no_sweep; do
    echo "=== Running ablation: $CONFIG ==="
    
    EXTRA_FLAGS=""
    case $CONFIG in
        baseline)
            EXTRA_FLAGS="--blind-generation --llm-judge --no-mutation-sweep" ;;
        a1_no_examples)
            EXTRA_FLAGS="--no-examples --no-mutation-sweep" ;;
        a2_no_sweep)
            EXTRA_FLAGS="--no-mutation-sweep" ;;
    esac
    
    bash scripts/run_all_experiments.sh \
        --exp-name "ablation/$CONFIG" \
        --seq-per-inv 10 \
        --profile zitadel:oidc=src/profiles/zitadel_oidc_jwt_${PROFILES_EXP}_*.json \
        ... (all 13 profile mappings) \
        $EXTRA_FLAGS
done
```

## What to measure

For each config, collect:
1. Total sequences generated
2. Execution success rate  
3. Unique findings
4. True positives (manual review or use existing metrics)
5. Precision

## Expected results (hypotheses)

| Metric | B (Baseline) | A1 (+Inv) | A2 (+Examples) | Full |
|--------|-------------|-----------|----------------|------|
| Findings | Low (~10-20) | Medium (~40-60) | High (~70-90) | Highest (~84) |
| Precision | Low (~50-60%) | Medium (~70-80%) | High (~85%) | Highest (~88%) |
| What it shows | Without invariants, LLM generates unfocused sequences | Invariants guide toward right bugs | Examples improve sequence quality | Sweep adds I5 findings |

Key expected insights:
- B→A1: Large jump in findings proves invariant guidance is critical for coverage
- A1→A2: Moderate jump proves attack-pattern examples improve sequence quality
- A2→Full: Small but significant jump in I5 findings from mutation sweep
- B precision < Full precision: Proves assertion oracle is more accurate than LLM-as-judge

## Implementation checklist

Before running:
- [ ] Add `--blind-generation` flag to campaign_runner.py
- [ ] Add `--llm-judge` flag to sequence_executor.py  
- [ ] Add `--no-examples` flag to generation_strategy.py
- [ ] Verify `--no-mutation-sweep` already works
- [ ] Write `scripts/run_ablation.sh`
- [ ] Test each config on one platform (e.g., keycloak/saml) before full run
