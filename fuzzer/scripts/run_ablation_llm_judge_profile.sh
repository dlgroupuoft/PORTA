#!/usr/bin/env bash
# =============================================================================
# LLM-as-Judge WITH Profile Ablation — run 3 times
# Same generation as full system (invariants + examples), but verdict is LLM
# with sanitized profile context (API endpoints + constraints, invariant
# references stripped). Results: results/ablation/llm_judge_profile_r{1,2,3}
# =============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FUZZER_DIR="$(dirname "$SCRIPT_DIR")"
cd "$FUZZER_DIR"

SEQ_PER_INV=10

RUNS=(
    "llm_judge_profile_r1"
    "llm_judge_profile_r2"
    "llm_judge_profile_r3"
)

TOTAL=${#RUNS[@]}
IDX=0

echo "================================================================="
echo "LLM-JUDGE WITH PROFILE ABLATION STARTED at $(date -Iseconds)"
echo "Runs: ${RUNS[*]}"
echo "================================================================="

for NAME in "${RUNS[@]}"; do
    IDX=$((IDX + 1))

    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║ Run [$IDX/$TOTAL]: $NAME (--eval-mode llm_judge_profile)"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""

    bash "$SCRIPT_DIR/run_all_experiments.sh" \
        --exp-name "ablation/$NAME" \
        --eval-mode "llm_judge_profile" \
        --seq-per-inv "$SEQ_PER_INV"

    echo ""
    echo "[$(date -Iseconds)] Run '$NAME' completed."
    echo ""
done

echo "================================================================="
echo "ALL LLM-JUDGE-PROFILE RUNS COMPLETE at $(date -Iseconds)"
echo "================================================================="
