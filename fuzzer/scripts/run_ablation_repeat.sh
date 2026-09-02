#!/usr/bin/env bash
# =============================================================================
# Ablation Repeat Runner — run baseline and a1_no_examples two more times each
# Results go to: results/ablation/baseline_r2, baseline_r3, a1_no_examples_r2, a1_no_examples_r3
# =============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FUZZER_DIR="$(dirname "$SCRIPT_DIR")"
cd "$FUZZER_DIR"

SEQ_PER_INV=10
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

RUNS=(
    "baseline_r2:blind"
    "baseline_r3:blind"
    "a1_no_examples_r2:no_examples"
    "a1_no_examples_r3:no_examples"
)

TOTAL=${#RUNS[@]}
IDX=0

echo "================================================================="
echo "ABLATION REPEAT RUNS STARTED at $(date -Iseconds)"
echo "Runs: ${RUNS[*]}"
echo "================================================================="

for entry in "${RUNS[@]}"; do
    IDX=$((IDX + 1))
    NAME="${entry%%:*}"
    EVAL_MODE="${entry##*:}"

    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║ Run [$IDX/$TOTAL]: $NAME (--eval-mode $EVAL_MODE)"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""

    bash "$SCRIPT_DIR/run_all_experiments.sh" \
        --exp-name "ablation/$NAME" \
        --eval-mode "$EVAL_MODE" \
        --seq-per-inv "$SEQ_PER_INV"

    echo ""
    echo "[$(date -Iseconds)] Run '$NAME' completed."
    echo ""
done

echo "================================================================="
echo "ALL REPEAT RUNS COMPLETE at $(date -Iseconds)"
echo "================================================================="
