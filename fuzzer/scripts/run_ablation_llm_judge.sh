#!/usr/bin/env bash
# =============================================================================
# LLM-as-Judge Ablation — run 3 times
# Full generation (invariants + examples) but LLM-as-judge verdict instead of
# assertion oracle. Results: results/ablation/llm_judge, llm_judge_r2, llm_judge_r3
# =============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FUZZER_DIR="$(dirname "$SCRIPT_DIR")"
cd "$FUZZER_DIR"

SEQ_PER_INV=10

RUNS=(
    "llm_judge"
    "llm_judge_r2"
    "llm_judge_r3"
)

TOTAL=${#RUNS[@]}
IDX=0

echo "================================================================="
echo "LLM-AS-JUDGE ABLATION STARTED at $(date -Iseconds)"
echo "Runs: ${RUNS[*]}"
echo "================================================================="

for NAME in "${RUNS[@]}"; do
    IDX=$((IDX + 1))

    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║ Run [$IDX/$TOTAL]: $NAME (--eval-mode llm_judge)"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""

    bash "$SCRIPT_DIR/run_all_experiments.sh" \
        --exp-name "ablation/$NAME" \
        --eval-mode "llm_judge" \
        --seq-per-inv "$SEQ_PER_INV"

    echo ""
    echo "[$(date -Iseconds)] Run '$NAME' completed."
    echo ""
done

echo "================================================================="
echo "ALL LLM-JUDGE RUNS COMPLETE at $(date -Iseconds)"
echo "================================================================="
