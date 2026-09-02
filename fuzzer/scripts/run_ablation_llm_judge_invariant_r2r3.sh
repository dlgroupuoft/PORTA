#!/usr/bin/env bash
# =============================================================================
# LLM-as-Judge WITH Invariant + Profile — runs 2 and 3
# =============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FUZZER_DIR="$(dirname "$SCRIPT_DIR")"
cd "$FUZZER_DIR"

SEQ_PER_INV=10

RUNS=(
    "llm_judge_invariant_r2"
    "llm_judge_invariant_r3"
)

TOTAL=${#RUNS[@]}
IDX=0

echo "================================================================="
echo "LLM-JUDGE+INVARIANT RUNS 2-3 STARTED at $(date -Iseconds)"
echo "================================================================="

for NAME in "${RUNS[@]}"; do
    IDX=$((IDX + 1))
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║ Run [$IDX/$TOTAL]: $NAME (--eval-mode llm_judge_invariant)"
    echo "╚═══════════════════════════════════════════════════════════════╝"

    bash "$SCRIPT_DIR/run_all_experiments.sh" \
        --exp-name "ablation/$NAME" \
        --eval-mode "llm_judge_invariant" \
        --seq-per-inv "$SEQ_PER_INV"

    echo "[$(date -Iseconds)] Run '$NAME' completed."
done

echo "================================================================="
echo "ALL RUNS COMPLETE at $(date -Iseconds)"
echo "================================================================="
