#!/usr/bin/env bash
# =============================================================================
# Evaluation Extraction — Run profile extraction 3 times for stability analysis
#
# Generates profiles tagged evaluation-exp1, evaluation-exp2, evaluation-exp3
# for all 7 platforms × 2 protocols = 42 profiles total.
#
# Usage:
#   export OPENAI_API_KEY='sk-...'
#   bash scripts/run_evaluation_extraction.sh
#
# Output:
#   src/profiles/{platform}_{protocol}_evaluation-exp{1,2,3}_{timestamp}.json
#   results/evaluation_extraction_{timestamp}.log
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FUZZER_DIR="$(dirname "$SCRIPT_DIR")"
cd "$FUZZER_DIR"

# --- Configuration ---
PLATFORMS="authentik vault logto keycloak casdoor dex zitadel"
PROTOCOLS="oidc_jwt saml"
RUNS=3
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOGFILE="results/evaluation_extraction_${TIMESTAMP}.log"

if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "ERROR: OPENAI_API_KEY not set. Export it before running."
    exit 1
fi

mkdir -p results

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOGFILE"; }

log "=== Evaluation Extraction Pipeline ==="
log "Platforms: $PLATFORMS"
log "Protocols: $PROTOCOLS"
log "Runs: $RUNS"
log ""

total=0
for run in $(seq 1 $RUNS); do
    log "============================================"
    log "=== Run $run/$RUNS (evaluation-exp${run}) ==="
    log "============================================"

    for platform in $PLATFORMS; do
        for proto in $PROTOCOLS; do
            tag="evaluation-exp${run}"
            log "--- $platform/$proto [$tag] ---"
            total=$((total + 1))

            python3 -m src.extraction.run_pipeline \
                --platform "$platform" \
                --protocol "$proto" \
                --no-merge \
                --tag "$tag" \
                2>&1 | tee -a "$LOGFILE" | grep -E "(Merged|Operations|Pipeline complete)"

            echo | tee -a "$LOGFILE"
        done
    done

    log "=== Run $run/$RUNS complete ==="
    log ""
done

log ""
log "=== All $RUNS runs complete ($total extractions) ==="
log ""

# Quality report
log "=== Quality Report ==="
for run in $(seq 1 $RUNS); do
    log "--- evaluation-exp${run} ---"
    python3 -m src.extraction.quality_report "src/profiles/*_evaluation-exp${run}_*.json" 2>&1 | tee -a "$LOGFILE"
    log ""
done

# Stability comparison
log "=== Stability Analysis (exp1 vs exp2 vs exp3) ==="
python3 -c "
import json, glob

platforms = '$PLATFORMS'.split()
protocols = '$PROTOCOLS'.split()

print(f'{\"Platform/Protocol\":<30s} {\"exp1\":>5s} {\"exp2\":>5s} {\"exp3\":>5s} {\"Stable\":>6s}')
print('-' * 55)

stable_count = 0
total_count = 0

for p in platforms:
    for proto in protocols:
        ops_per_run = []
        for run in range(1, 4):
            files = sorted(glob.glob(f'src/profiles/{p}_{proto}_evaluation-exp{run}_*.json'))
            if files:
                with open(files[-1]) as f:
                    d = json.load(f)
                ops = set(d.get('api_mapping', {}).get(proto, {}).keys())
                ops_per_run.append(ops)
            else:
                ops_per_run.append(set())

        counts = [len(o) for o in ops_per_run]

        if len(ops_per_run) == 3 and all(ops_per_run):
            common = ops_per_run[0] & ops_per_run[1] & ops_per_run[2]
            union = ops_per_run[0] | ops_per_run[1] | ops_per_run[2]
            stability = len(common) / len(union) * 100 if union else 100
        else:
            stability = 0

        total_count += 1
        if stability >= 90:
            stable_count += 1

        name = f'{p}/{proto}'
        print(f'{name:<30s} {counts[0]:5d} {counts[1]:5d} {counts[2]:5d} {stability:5.0f}%')

print(f'\nStability >= 90%: {stable_count}/{total_count}')
" 2>&1 | tee -a "$LOGFILE"

log ""
log "Log saved to: $LOGFILE"
log "DONE"
