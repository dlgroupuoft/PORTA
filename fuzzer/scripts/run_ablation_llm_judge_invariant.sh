#!/usr/bin/env bash
# =============================================================================
# LLM-as-Judge WITH Invariant Definitions — run 1 time
# Same generation as full system (invariants + examples), but verdict is LLM
# with I1-I5 invariant definitions + profile context in the judge prompt.
# Results: results/ablation/llm_judge_invariant_r1
# =============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FUZZER_DIR="$(dirname "$SCRIPT_DIR")"
cd "$FUZZER_DIR"

SEQ_PER_INV=10

NAME="llm_judge_invariant_r1"

echo "================================================================="
echo "LLM-JUDGE WITH INVARIANTS — STARTED at $(date -Iseconds)"
echo "Run: $NAME"
echo "================================================================="

bash "$SCRIPT_DIR/run_all_experiments.sh" \
    --exp-name "ablation/$NAME" \
    --eval-mode "llm_judge_invariant" \
    --seq-per-inv "$SEQ_PER_INV"

echo ""
echo "[$(date -Iseconds)] Run '$NAME' completed."
echo "================================================================="
echo "LLM-JUDGE WITH INVARIANTS — COMPLETE at $(date -Iseconds)"
echo "================================================================="
