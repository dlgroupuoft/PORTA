#!/usr/bin/env bash
# =============================================================================
# Casdoor Experiment 1 — Full campaign (SAML + OIDC)
# =============================================================================
# Usage:
#   tmux new-session -d -s casdoor_exp1 'bash /home/ubuntu/broker/fuzzer/scripts/run_casdoor_exp1.sh'
#   tmux attach -t casdoor_exp1   # to watch progress
#
# This script:
#   1. Tears down and rebuilds Casdoor containers (clean state)
#   2. Waits for Casdoor to be healthy
#   3. Runs SAML campaign (I1-I5, 5 sequences per invariant)
#   4. Tears down and rebuilds Casdoor (clean state between protocols)
#   5. Runs OIDC campaign (I1-I5, 5 sequences per invariant)
#   6. Saves all logs and results
# =============================================================================

set -euo pipefail

# ── Config ──────────────────────────────────────────────────────────────────
OPENAI_API_KEY="${OPENAI_API_KEY:?Set OPENAI_API_KEY env var before running}"
export OPENAI_API_KEY

BROKER_ROOT="/home/ubuntu/broker"
FUZZER_ROOT="${BROKER_ROOT}/fuzzer"
CASDOOR_COMPOSE="${BROKER_ROOT}/platform/casdoor"
RESULTS_ROOT="${FUZZER_ROOT}/results/final-exp1/casdoor"

SAML_PROFILE="src/profiles/casdoor_saml_exp-1_20260330_015701.json"
OIDC_PROFILE="src/profiles/casdoor_oidc_jwt_exp-1_20260330_015452.json"

INVARIANTS="I1,I2,I3,I4,I5"
SEQ_PER_INV=5

CASDOOR_URL="http://localhost:8000"
HEALTH_TIMEOUT=120   # seconds to wait for Casdoor health

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOGDIR="${RESULTS_ROOT}/logs"

# ── Helpers ─────────────────────────────────────────────────────────────────
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

wait_for_casdoor() {
    log "Waiting for Casdoor to be healthy at ${CASDOOR_URL} ..."
    local elapsed=0
    while [ $elapsed -lt $HEALTH_TIMEOUT ]; do
        if curl -sf "${CASDOOR_URL}/api/health" >/dev/null 2>&1; then
            log "Casdoor is healthy (took ${elapsed}s)"
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done
    log "ERROR: Casdoor did not become healthy within ${HEALTH_TIMEOUT}s"
    return 1
}

teardown_casdoor() {
    log "Tearing down Casdoor containers..."
    cd "${CASDOOR_COMPOSE}"
    docker compose down -v --remove-orphans 2>/dev/null || docker-compose down -v --remove-orphans 2>/dev/null || true
    # Remove mysql data volume to ensure clean DB
    docker volume rm casdoor_mysql_data 2>/dev/null || true
    sudo rm -rf /usr/local/docker/mysql/* 2>/dev/null || true
    log "Casdoor teardown complete"
}

startup_casdoor() {
    log "Starting Casdoor containers..."
    cd "${CASDOOR_COMPOSE}"
    docker compose up -d --build 2>/dev/null || docker-compose up -d --build 2>/dev/null
    wait_for_casdoor
    # Give Casdoor a few more seconds for DB init
    sleep 5
    log "Casdoor startup complete"
}

run_campaign() {
    local protocol="$1"
    local profile="$2"
    local output_dir="$3"
    local logfile="$4"

    log "=== Starting ${protocol} campaign ==="
    log "  Profile: ${profile}"
    log "  Output:  ${output_dir}"
    log "  Log:     ${logfile}"

    cd "${FUZZER_ROOT}"
    python3 -m src.stateful.campaign_runner \
        --profile "${profile}" \
        --invariants "${INVARIANTS}" \
        --sequences-per-invariant "${SEQ_PER_INV}" \
        --output-dir "${output_dir}" \
        2>&1 | tee "${logfile}"

    local exit_code=${PIPESTATUS[0]}
    log "=== ${protocol} campaign finished (exit code: ${exit_code}) ==="
    return ${exit_code}
}

# ── Main ────────────────────────────────────────────────────────────────────
log "============================================================"
log "Casdoor Experiment 1 — Start"
log "Timestamp: ${TIMESTAMP}"
log "============================================================"

mkdir -p "${LOGDIR}"

# Save this script itself for reproducibility
cp "$0" "${RESULTS_ROOT}/run_script_${TIMESTAMP}.sh" 2>/dev/null || true

# ── Phase 1: SAML Campaign ─────────────────────────────────────────────────
log ""
log "============================================================"
log "Phase 1: SAML Campaign"
log "============================================================"

teardown_casdoor
startup_casdoor

SAML_OUTPUT="${RESULTS_ROOT}/saml"
SAML_LOG="${LOGDIR}/saml_${TIMESTAMP}.log"

run_campaign "saml" "${SAML_PROFILE}" "${SAML_OUTPUT}" "${SAML_LOG}" || true

# Save Casdoor logs
docker logs casdoor-casdoor-1 > "${LOGDIR}/casdoor_saml_${TIMESTAMP}.docker.log" 2>&1 || true

log "SAML campaign results saved to ${SAML_OUTPUT}"

# ── Phase 2: OIDC Campaign ─────────────────────────────────────────────────
log ""
log "============================================================"
log "Phase 2: OIDC Campaign"
log "============================================================"

teardown_casdoor
startup_casdoor

OIDC_OUTPUT="${RESULTS_ROOT}/oidc"
OIDC_LOG="${LOGDIR}/oidc_${TIMESTAMP}.log"

run_campaign "oidc" "${OIDC_PROFILE}" "${OIDC_OUTPUT}" "${OIDC_LOG}" || true

# Save Casdoor logs
docker logs casdoor-casdoor-1 > "${LOGDIR}/casdoor_oidc_${TIMESTAMP}.docker.log" 2>&1 || true

log "OIDC campaign results saved to ${OIDC_OUTPUT}"

# ── Summary ─────────────────────────────────────────────────────────────────
log ""
log "============================================================"
log "Experiment Complete"
log "============================================================"

cd "${FUZZER_ROOT}"
python3 -c "
import json, glob, os

root = '${RESULTS_ROOT}'
for proto in ['saml', 'oidc']:
    pattern = os.path.join(root, proto, 'full', 'campaign_*', 'summary.json')
    files = sorted(glob.glob(pattern))
    if files:
        with open(files[-1]) as f:
            d = json.load(f)
        print(f'{proto.upper()}:')
        print(f'  Sequences: {d[\"total_sequences\"]}')
        print(f'  Completed: {d[\"by_status\"].get(\"COMPLETED\",0)}')
        print(f'  Login failed: {d[\"by_status\"].get(\"LOGIN_FAILED\",0)}')
        print(f'  Findings: {d[\"total_findings\"]}')
        print(f'  Unique findings: {d[\"unique_findings\"]}')
        print()
    else:
        print(f'{proto.upper()}: No results found')
" 2>&1 | tee "${LOGDIR}/summary_${TIMESTAMP}.txt"

log "All logs saved to ${LOGDIR}"
log "Done."
