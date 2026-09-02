#!/usr/bin/env bash
###############################################################################
# VALENCE Experiment 1 — Dex (OIDC JWT + SAML)
# Fully automated, reproducible experiment script
# Run in tmux to survive SSH disconnection
#
# Target bugs:
#   - f3-token-exchange-scope-escalation (I5): server/handlers.go:1388
#   - Dex-Saml (I1): XSW/signature bypass in unmaintained SAML connector
#
# Generated: 2026-03-30
###############################################################################
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FUZZER_DIR="$(dirname "$SCRIPT_DIR")"
PLATFORM_DIR="$(dirname "$FUZZER_DIR")/platform/dex"
DOCKER_DEX_DIR="${FUZZER_DIR}/docker/dex"
RESULTS_DIR="${FUZZER_DIR}/results/final-exp1"
LOG_DIR="${RESULTS_DIR}"

# API Key
export OPENAI_API_KEY="${OPENAI_API_KEY:?Set OPENAI_API_KEY env var before running}"

# Container / network names
DEX_CONTAINER="valence-dex"
MOCK_IDP_CONTAINER="valence-mock-idp"
DEX_IMAGE="ghcr.io/dexidp/dex:latest"
MOCK_IDP_IMAGE="docker-mock-idp"
NETWORK="docker_valence-net"

# Profiles
OIDC_PROFILE="${FUZZER_DIR}/src/profiles/dex_oidc_jwt_exp-1_20260330_015843.json"
SAML_PROFILE="${FUZZER_DIR}/src/profiles/dex_saml_exp-1_20260330_020036.json"

# Common flags
INVARIANTS="I1,I2,I3,I4,I5"
SEQ_PER_INV=5

###############################################################################
# Helper functions
###############################################################################
timestamp() { date '+%Y-%m-%d %H:%M:%S'; }
log()       { echo "[$(timestamp)] $*"; }

wait_for_dex() {
    log "Waiting for Dex to become healthy..."
    local retries=30
    for i in $(seq 1 $retries); do
        if curl -sf http://localhost:5556/dex/healthz > /dev/null 2>&1; then
            log "Dex is healthy (attempt $i/$retries)"
            return 0
        fi
        sleep 2
    done
    log "ERROR: Dex did not become healthy after $retries attempts"
    return 1
}

wait_for_mock_idp() {
    log "Waiting for Mock IdP to become healthy..."
    local retries=20
    for i in $(seq 1 $retries); do
        if curl -sf http://localhost:9090/health > /dev/null 2>&1 || \
           curl -sf http://localhost:9090/saml/metadata > /dev/null 2>&1; then
            log "Mock IdP is healthy (attempt $i/$retries)"
            return 0
        fi
        sleep 2
    done
    log "ERROR: Mock IdP did not become healthy after $retries attempts"
    return 1
}

ensure_network() {
    if ! docker network inspect "$NETWORK" > /dev/null 2>&1; then
        log "Creating Docker network: $NETWORK"
        docker network create "$NETWORK"
    fi
}

destroy_dex() {
    log "Destroying Dex container (if exists)..."
    docker rm -f "$DEX_CONTAINER" 2>/dev/null || true
    # Clean up any leftover SQLite state by removing volumes
    sleep 1
}

destroy_mock_idp() {
    log "Destroying Mock IdP container (if exists)..."
    docker rm -f "$MOCK_IDP_CONTAINER" 2>/dev/null || true
    sleep 1
}

start_mock_idp() {
    log "Starting Mock IdP container..."
    docker run -d \
        --name "$MOCK_IDP_CONTAINER" \
        --network "$NETWORK" \
        -p 9090:9090 \
        "$MOCK_IDP_IMAGE" \
        python3 server.py
    wait_for_mock_idp
}

start_dex() {
    log "Starting Dex container..."
    docker run -d \
        --name "$DEX_CONTAINER" \
        --network "$NETWORK" \
        -p 5556:5556 \
        -p 5557:5557 \
        -v "${DOCKER_DEX_DIR}/config.yaml:/etc/dex/config.yaml:ro" \
        -v "${DOCKER_DEX_DIR}/saml_idp_cert.pem:/tmp/saml_idp_cert.pem:ro" \
        "$DEX_IMAGE" \
        dex serve /etc/dex/config.yaml
    wait_for_dex
}

sync_saml_cert_to_local() {
    log "Syncing SAML IdP cert from Mock IdP to local mount path..."
    # Copy cert from mock IdP container to the local file that Dex volume-mounts
    docker cp "${MOCK_IDP_CONTAINER}:/app/certs/idp_cert.pem" "${DOCKER_DEX_DIR}/saml_idp_cert.pem" 2>/dev/null || true
    if [ -f "${DOCKER_DEX_DIR}/saml_idp_cert.pem" ]; then
        log "SAML cert synced: ${DOCKER_DEX_DIR}/saml_idp_cert.pem"
    else
        log "WARNING: Could not sync SAML cert from Mock IdP"
    fi
}

full_cleanup_and_rebuild() {
    log "========== FULL CLEANUP AND REBUILD =========="
    destroy_dex
    destroy_mock_idp
    ensure_network
    start_mock_idp
    sync_saml_cert_to_local
    start_dex
    log "========== REBUILD COMPLETE =========="
}

###############################################################################
# Main
###############################################################################
mkdir -p "$RESULTS_DIR"

log "============================================================"
log "VALENCE Experiment 1 — Dex Platform"
log "============================================================"
log "OIDC JWT Profile: $OIDC_PROFILE"
log "SAML Profile:     $SAML_PROFILE"
log "Invariants:       $INVARIANTS"
log "Seq/Invariant:    $SEQ_PER_INV"
log "Results dir:      $RESULTS_DIR"
log "============================================================"

# ─────────────────────────────────────────────────────────────────
# Phase 1: OIDC JWT experiment
# ─────────────────────────────────────────────────────────────────
log ""
log "############################################################"
log "# Phase 1: Dex OIDC JWT Experiment"
log "############################################################"

full_cleanup_and_rebuild

log "Running OIDC JWT campaign..."
cd "$FUZZER_DIR"
python3 -m src.stateful.campaign_runner \
    --profile "$OIDC_PROFILE" \
    --invariants "$INVARIANTS" \
    --sequences-per-invariant "$SEQ_PER_INV" \
    --output-dir "${RESULTS_DIR}/dex_oidc_jwt" \
    2>&1 | tee "${LOG_DIR}/dex_oidc_jwt_exp1.log"

OIDC_EXIT=${PIPESTATUS[0]}
log "OIDC JWT campaign finished with exit code: $OIDC_EXIT"

# ─────────────────────────────────────────────────────────────────
# Phase 2: Cleanup between protocols
# ─────────────────────────────────────────────────────────────────
log ""
log "############################################################"
log "# Cleanup: Rebuilding containers for SAML experiment"
log "############################################################"

full_cleanup_and_rebuild

# ─────────────────────────────────────────────────────────────────
# Phase 3: SAML experiment
# ─────────────────────────────────────────────────────────────────
log ""
log "############################################################"
log "# Phase 2: Dex SAML Experiment"
log "############################################################"

log "Running SAML campaign..."
cd "$FUZZER_DIR"
python3 -m src.stateful.campaign_runner \
    --profile "$SAML_PROFILE" \
    --invariants "$INVARIANTS" \
    --sequences-per-invariant "$SEQ_PER_INV" \
    --output-dir "${RESULTS_DIR}/dex_saml" \
    2>&1 | tee "${LOG_DIR}/dex_saml_exp1.log"

SAML_EXIT=${PIPESTATUS[0]}
log "SAML campaign finished with exit code: $SAML_EXIT"

# ─────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────
log ""
log "============================================================"
log "EXPERIMENT COMPLETE"
log "============================================================"
log "OIDC JWT exit code: $OIDC_EXIT"
log "SAML exit code:     $SAML_EXIT"
log "Results:            $RESULTS_DIR"
log "Logs:"
log "  OIDC JWT: ${LOG_DIR}/dex_oidc_jwt_exp1.log"
log "  SAML:     ${LOG_DIR}/dex_saml_exp1.log"
log "============================================================"
