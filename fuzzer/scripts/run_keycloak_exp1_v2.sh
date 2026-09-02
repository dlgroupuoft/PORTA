#!/usr/bin/env bash
# =============================================================================
# Keycloak Experiment 1 v2
# Usage: tmux new -s kc_exp1 'bash scripts/run_keycloak_exp1_v2.sh'
# Clean state: container rm + up = fresh KC, no resource cleanup needed
# =============================================================================
set -euo pipefail
cd /home/ubuntu/broker/fuzzer

export OPENAI_API_KEY="${OPENAI_API_KEY:?Set OPENAI_API_KEY env var before running}"
OIDC_PROFILE="src/profiles/keycloak_oidc_jwt_exp-1_20260330_212955.json"
SAML_PROFILE="src/profiles/keycloak_saml_exp-1_20260330_213350.json"
OUTPUT_BASE="results/final-exp1"
COMPOSE="docker/platform-images.yml"
TS=$(date +%Y%m%d_%H%M%S)
LOG="${OUTPUT_BASE}/kc_exp1v2_${TS}.log"
mkdir -p "$OUTPUT_BASE"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

fresh_kc() {
    log ">>> Destroying + recreating KC container (clean state)"
    docker compose -f "$COMPOSE" --profile keycloak stop   2>/dev/null || true
    docker compose -f "$COMPOSE" --profile keycloak rm -f   2>/dev/null || true
    docker compose -f "$COMPOSE" --profile keycloak up -d
    log "    Waiting for KC..."
    for i in $(seq 1 90); do
        if curl -sf http://localhost:8080/realms/master/.well-known/openid-configuration >/dev/null 2>&1; then
            log "    KC ready (${i}×5s)"
            return 0
        fi
        sleep 5
    done
    log "    ERROR: KC not ready after 450s"
    return 1
}

run() {
    local PROFILE="$1" LABEL="$2"
    local OUTDIR="${OUTPUT_BASE}/${LABEL}"
    local CLOG="${OUTPUT_BASE}/${LABEL}.log"
    log "=========================================="
    log "Campaign: $LABEL"
    log "Profile:  $PROFILE"
    log "=========================================="
    python3 -m src.stateful.campaign_runner \
        --profile "$PROFILE" \
        --invariants I1,I2,I3,I4,I5 \
        --sequences-per-invariant 5 \
        --output-dir "$OUTDIR" \
        2>&1 | tee "$CLOG" | tee -a "$LOG"
    log "Done: $LABEL ($(grep '^Findings:' "$CLOG" 2>/dev/null | tail -1))"
}

# ===================== MAIN =====================
log "============================================================"
log "KEYCLOAK EXP1 V2 — START"
log "OIDC: $OIDC_PROFILE"
log "SAML: $SAML_PROFILE"
log "============================================================"

fresh_kc
run "$OIDC_PROFILE" "keycloak_oidc_v2"

fresh_kc
run "$SAML_PROFILE" "keycloak_saml_v2"

log "============================================================"
log "KEYCLOAK EXP1 V2 — COMPLETE"
log "============================================================"
for L in keycloak_oidc_v2 keycloak_saml_v2; do
    F="${OUTPUT_BASE}/${L}.log"
    [ -f "$F" ] && log "  $L: $(grep '^Findings:' "$F" | tail -1), $(grep 'Unique findings:' "$F" | tail -1)"
done
log "Logs: $LOG"
