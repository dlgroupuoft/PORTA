#!/usr/bin/env bash
# =============================================================================
# Keycloak Experiment 1 — OIDC + SAML, 25 seqs each (5 per invariant × 5)
# Run in tmux for SSH resilience: tmux new -s exp1 'bash scripts/run_keycloak_exp1.sh'
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FUZZER_DIR="$(dirname "$SCRIPT_DIR")"
cd "$FUZZER_DIR"

# --- Configuration ---
export OPENAI_API_KEY="${OPENAI_API_KEY:?Set OPENAI_API_KEY env var before running}"
OIDC_PROFILE="src/profiles/keycloak_oidc_jwt_exp-1_20260330_014858.json"
SAML_PROFILE="src/profiles/keycloak_saml_exp-1_20260330_015238.json"
INVARIANTS="I1,I2,I3,I4,I5"
SEQ_PER_INV=5
OUTPUT_BASE="results/final-exp1"
DOCKER_COMPOSE="docker/docker-compose.yml"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOGFILE="${OUTPUT_BASE}/experiment_${TIMESTAMP}.log"

mkdir -p "$OUTPUT_BASE"

# --- Helper functions ---
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOGFILE"; }

wait_for_keycloak() {
    log "Waiting for Keycloak to be ready..."
    for i in $(seq 1 60); do
        if curl -sf http://localhost:8080/realms/master/.well-known/openid-configuration >/dev/null 2>&1; then
            log "Keycloak ready (attempt $i)"
            return 0
        fi
        sleep 5
    done
    log "ERROR: Keycloak failed to start after 5 minutes"
    return 1
}

restart_keycloak() {
    log "=== Restarting Keycloak container (clean state) ==="
    docker compose -f "$DOCKER_COMPOSE" stop keycloak 2>/dev/null || true
    docker compose -f "$DOCKER_COMPOSE" rm -f keycloak 2>/dev/null || true
    docker compose -f "$DOCKER_COMPOSE" up -d keycloak
    wait_for_keycloak
    log "Keycloak restarted with clean state"
}

cleanup_keycloak() {
    log "=== Cleaning Keycloak resources ==="
    python3 -c "
import requests, sys
base='http://localhost:8080'
try:
    r=requests.post(f'{base}/realms/master/protocol/openid-connect/token',
        data={'grant_type':'password','client_id':'admin-cli','username':'admin','password':'admin'}, timeout=15)
    t=r.json()['access_token'];h={'Authorization':f'Bearer {t}'}
    # Delete test realms
    realms=requests.get(f'{base}/admin/realms',headers=h,timeout=15).json()
    test=[r['realm'] for r in realms if r['realm']!='master']
    for rn in test: requests.delete(f'{base}/admin/realms/{rn}',headers=h,timeout=10)
    # Delete master IdPs
    idps=requests.get(f'{base}/admin/realms/master/identity-provider/instances',headers=h,timeout=15).json()
    for idp in idps: requests.delete(f'{base}/admin/realms/master/identity-provider/instances/{idp[\"alias\"]}',headers=h,timeout=10)
    # Delete test users from master (except admin)
    users=requests.get(f'{base}/admin/realms/master/users',headers=h,timeout=15).json()
    for u in users:
        if u.get('username') not in ('admin',):
            requests.delete(f'{base}/admin/realms/master/users/{u[\"id\"]}',headers=h,timeout=10)
    # Delete test clients from master (keep built-in)
    clients=requests.get(f'{base}/admin/realms/master/clients',headers=h,timeout=15).json()
    builtin={'account','account-console','admin-cli','broker','master-realm','security-admin-console'}
    for c in clients:
        if c.get('clientId') not in builtin:
            requests.delete(f'{base}/admin/realms/master/clients/{c[\"id\"]}',headers=h,timeout=10)
    print(f'Cleaned: {len(test)} realms, {len(idps)} IdPs')
except Exception as e:
    print(f'Cleanup error: {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1 | tee -a "$LOGFILE"
}

run_campaign() {
    local PROFILE="$1"
    local LABEL="$2"
    local OUTDIR="${OUTPUT_BASE}/${LABEL}"
    local CAMPAIGN_LOG="${OUTPUT_BASE}/${LABEL}.log"

    log "=========================================="
    log "Starting campaign: $LABEL"
    log "Profile: $PROFILE"
    log "Output: $OUTDIR"
    log "=========================================="

    python3 -m src.stateful.campaign_runner \
        --profile "$PROFILE" \
        --invariants "$INVARIANTS" \
        --sequences-per-invariant "$SEQ_PER_INV" \
        --output-dir "$OUTDIR" \
        2>&1 | tee "$CAMPAIGN_LOG" | tee -a "$LOGFILE"

    # Extract summary
    local FINDINGS=$(grep "^Findings:" "$CAMPAIGN_LOG" 2>/dev/null | tail -1 || echo "Findings: ?")
    local EXECUTED=$(grep "^Sequences executed:" "$CAMPAIGN_LOG" 2>/dev/null | tail -1 || echo "Sequences: ?")
    log "Result: $EXECUTED, $FINDINGS"
}

# =============================================================================
# MAIN EXPERIMENT
# =============================================================================
log "============================================================"
log "KEYCLOAK EXPERIMENT 1 — START"
log "OIDC profile: $OIDC_PROFILE"
log "SAML profile: $SAML_PROFILE"
log "Invariants: $INVARIANTS"
log "Sequences per invariant: $SEQ_PER_INV"
log "============================================================"

# --- Phase 1: OIDC campaign ---
restart_keycloak
run_campaign "$OIDC_PROFILE" "keycloak_oidc"

# --- Phase 2: SAML campaign (clean KC between protocols) ---
restart_keycloak
run_campaign "$SAML_PROFILE" "keycloak_saml"

# --- Final cleanup ---
cleanup_keycloak

# --- Summary ---
log ""
log "============================================================"
log "EXPERIMENT COMPLETE"
log "============================================================"

for LABEL in keycloak_oidc keycloak_saml; do
    CAMPAIGN_LOG="${OUTPUT_BASE}/${LABEL}.log"
    if [ -f "$CAMPAIGN_LOG" ]; then
        FINDINGS=$(grep "^Findings:" "$CAMPAIGN_LOG" 2>/dev/null | tail -1 || echo "?")
        EXECUTED=$(grep "^Sequences executed:" "$CAMPAIGN_LOG" 2>/dev/null | tail -1 || echo "?")
        UNIQUE=$(grep "Unique findings:" "$CAMPAIGN_LOG" 2>/dev/null | tail -1 || echo "?")
        log "  $LABEL: $EXECUTED | $FINDINGS | $UNIQUE"
    fi
done

log ""
log "Full logs: $LOGFILE"
log "Campaign outputs: $OUTPUT_BASE/keycloak_oidc/ and $OUTPUT_BASE/keycloak_saml/"
log "Done."
