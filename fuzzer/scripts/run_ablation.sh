#!/usr/bin/env bash
# =============================================================================
# Ablation Experiment Runner (RQ4)
# =============================================================================
# Runs three ablation configs (B, A1, A2) across all platforms using the
# existing run_all_experiments.sh infrastructure.
#
# Configs:
#   B  (baseline)      = --eval-mode blind        (no invariants, no examples, no sweep)
#   A1 (+invariants)   = --eval-mode no_examples  (invariants, no examples, no sweep)
#   A2 (+examples)     = --eval-mode oracle_gen   (invariants + examples, no sweep)
#
# "Full" is already run 3x in exp1. We only run B, A1, A2 once each.
#
# Usage:
#   bash scripts/run_ablation.sh                    # all configs, all platforms
#   bash scripts/run_ablation.sh --config baseline   # single config
#   bash scripts/run_ablation.sh --platforms zitadel vault  # subset of platforms
#   bash scripts/run_ablation.sh --dry-run           # print config, don't run
# =============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FUZZER_DIR="$(dirname "$SCRIPT_DIR")"

# ════════════════════════════════════════════════════════════════════════════
# Configuration
# ════════════════════════════════════════════════════════════════════════════

# Ablation configs: name -> eval-mode mapping
declare -A ABLATION_CONFIGS=(
    [baseline]="blind"
    [a1_no_examples]="no_examples"
    [a2_no_sweep]="oracle_gen"
)

# Order of execution
ABLATION_ORDER=(baseline a1_no_examples a2_no_sweep)

# Default: run all configs
SELECTED_CONFIGS=()
SELECTED_PLATFORMS=()
DRY_RUN=false
SEQ_PER_INV=10  # ablation plan specifies 10

# ════════════════════════════════════════════════════════════════════════════
# CLI argument parsing
# ════════════════════════════════════════════════════════════════════════════
while [[ $# -gt 0 ]]; do
    case "$1" in
        --config)
            SELECTED_CONFIGS+=("$2"); shift 2 ;;
        --platforms)
            shift
            while [[ $# -gt 0 && "$1" != --* ]]; do
                SELECTED_PLATFORMS+=("$1"); shift
            done ;;
        --seq-per-inv)
            SEQ_PER_INV="$2"; shift 2 ;;
        --dry-run)
            DRY_RUN=true; shift ;;
        -h|--help)
            cat <<'USAGE'
Usage: run_ablation.sh [OPTIONS]

Options:
  --config NAME         Run only this config (baseline, a1_no_examples, a2_no_sweep)
                        Can be repeated. Default: all three.
  --platforms P1 P2...  Run only these platforms (default: all)
  --seq-per-inv N       Sequences per invariant (default: 10)
  --dry-run             Print config and exit
  -h, --help            Show this help

Examples:
  bash scripts/run_ablation.sh
  bash scripts/run_ablation.sh --config baseline --platforms zitadel vault
  bash scripts/run_ablation.sh --dry-run
USAGE
            exit 0 ;;
        *)
            echo "ERROR: Unknown argument '$1'" >&2; exit 1 ;;
    esac
done

# Default: all configs
if [ ${#SELECTED_CONFIGS[@]} -eq 0 ]; then
    SELECTED_CONFIGS=("${ABLATION_ORDER[@]}")
fi

# Build platform args for run_all_experiments.sh
PLATFORM_ARGS=""
if [ ${#SELECTED_PLATFORMS[@]} -gt 0 ]; then
    PLATFORM_ARGS="${SELECTED_PLATFORMS[*]}"
fi

# ════════════════════════════════════════════════════════════════════════════
# Print plan
# ════════════════════════════════════════════════════════════════════════════
echo "================================================================="
echo "ABLATION EXPERIMENT PLAN (RQ4)"
echo "================================================================="
echo ""
echo "Configs to run:"
for cfg in "${SELECTED_CONFIGS[@]}"; do
    echo "  $cfg  ->  --eval-mode ${ABLATION_CONFIGS[$cfg]}"
done
echo ""
echo "Sequences per invariant: $SEQ_PER_INV"
echo "Platforms: ${PLATFORM_ARGS:-all}"
echo ""

if $DRY_RUN; then
    echo "(dry-run) Would call for each config:"
    for cfg in "${SELECTED_CONFIGS[@]}"; do
        echo "  bash scripts/run_all_experiments.sh \\"
        echo "    --exp-name ablation/$cfg \\"
        echo "    --eval-mode ${ABLATION_CONFIGS[$cfg]} \\"
        echo "    --seq-per-inv $SEQ_PER_INV \\"
        echo "    $PLATFORM_ARGS"
        echo ""
    done
    echo "(dry-run complete — nothing executed)"
    exit 0
fi

# ════════════════════════════════════════════════════════════════════════════
# Execute ablation configs
# ════════════════════════════════════════════════════════════════════════════
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ABLATION_LOG="$FUZZER_DIR/results/ablation/ablation_${TIMESTAMP}.log"
mkdir -p "$FUZZER_DIR/results/ablation"

{
echo "================================================================="
echo "ABLATION RUN STARTED at $(date -Iseconds)"
echo "================================================================="

TOTAL=${#SELECTED_CONFIGS[@]}
IDX=0

for cfg in "${SELECTED_CONFIGS[@]}"; do
    IDX=$((IDX + 1))
    EVAL_MODE="${ABLATION_CONFIGS[$cfg]}"

    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║ Ablation [$IDX/$TOTAL]: $cfg (--eval-mode $EVAL_MODE)"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""

    bash "$SCRIPT_DIR/run_all_experiments.sh" \
        --exp-name "ablation/$cfg" \
        --eval-mode "$EVAL_MODE" \
        --seq-per-inv "$SEQ_PER_INV" \
        $PLATFORM_ARGS

    echo ""
    echo "[$(date -Iseconds)] Ablation config '$cfg' completed."
    echo ""
done

echo "================================================================="
echo "ALL ABLATION CONFIGS COMPLETE at $(date -Iseconds)"
echo "================================================================="

} 2>&1 | tee "$ABLATION_LOG"
