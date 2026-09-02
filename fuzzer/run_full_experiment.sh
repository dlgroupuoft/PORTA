#!/bin/bash
# VALENCE Full-Mode Experiment — Single cell runner
# Usage: ./run_full_experiment.sh <run_number> <platform> <protocol>
set -euo pipefail

cd ~/broker/fuzzer
export OPENAI_API_KEY="${OPENAI_API_KEY:?Set OPENAI_API_KEY env var before running}"

BASE="results/experiment_full/raw"
INVARIANTS="I1,I2,I3,I4,I5"
SEQ=20
MODEL="gpt-5.2-2025-12-11"

RUN=${1:?Usage: $0 <run_number> <platform> <protocol>}
PLATFORM=${2:?Missing platform}
PROTOCOL=${3:?Missing protocol}

OUTDIR="${BASE}/R${RUN}/${PLATFORM}_${PROTOCOL}"
EXTRA=""
[ "$PLATFORM" = "keycloak" ] && EXTRA="--setup-platform"
[ "$PLATFORM" = "vault" ] && EXTRA="--setup-platform"

mkdir -p "${OUTDIR}"
echo "============================================"
echo "VALENCE R${RUN}: ${PLATFORM}/${PROTOCOL}"
echo "  Seq/Invariant: ${SEQ} × 4 = $((SEQ*4)) total"
echo "  Start: $(date -Iseconds)"
echo "============================================"

python3 -m src.stateful.campaign_runner \
    --platform "${PLATFORM}" \
    --protocol "${PROTOCOL}" \
    --invariants "${INVARIANTS}" \
    --sequences-per-invariant ${SEQ} \
    --eval-mode full \
    --llm-model "${MODEL}" \
    ${EXTRA} \
    --output-dir "${OUTDIR}" \
    2>&1 | tee "${OUTDIR}/run.log"

echo "[R${RUN}] ${PLATFORM}/${PROTOCOL} done at $(date -Iseconds)"
