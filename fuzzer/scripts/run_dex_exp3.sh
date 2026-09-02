#!/usr/bin/env bash
# =============================================================================
# Dex Experiment 3 — Full run (OIDC JWT + SAML) with mutation sweep
#
# Usage:
#   tmux new-session -d -s dex-exp3 'bash /home/ubuntu/broker/fuzzer/scripts/run_dex_exp3.sh'
#   tmux attach -t dex-exp3   # to watch live
#
# Uses platform-images.yml for clean-state restarts from image snapshots.
# Each protocol run gets a fresh Dex instance (down + up = clean sqlite).
# =============================================================================
set -euo pipefail

export OPENAI_API_KEY="${OPENAI_API_KEY:?Set OPENAI_API_KEY env var before running}"

FUZZER_DIR="/home/ubuntu/broker/fuzzer"
COMPOSE_FILE="$FUZZER_DIR/docker/platform-images.yml"
DOCKER_DEX_DIR="$FUZZER_DIR/docker/dex"
RESULTS_DIR="$FUZZER_DIR/results/final-exp3/dex"
LOG_DIR="$RESULTS_DIR/logs"

PROFILE_OIDC="$FUZZER_DIR/src/profiles/dex_oidc_jwt_exp-1_20260331_011631.json"
PROFILE_SAML="$FUZZER_DIR/src/profiles/dex_saml_exp-1_20260331_011840.json"

mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUNLOG="$LOG_DIR/run_${TIMESTAMP}.log"

exec > >(tee -a "$RUNLOG") 2>&1

echo "================================================================="
echo "Dex Experiment 3 — started at $(date -Iseconds)"
echo "================================================================="
echo "COMPOSE_FILE=$COMPOSE_FILE"
echo "PROFILE_OIDC=$PROFILE_OIDC"
echo "PROFILE_SAML=$PROFILE_SAML"
echo "RESULTS_DIR=$RESULTS_DIR"
echo ""

# ─────────────────────────────────────────────────────────────────────
# Helper: sync mock-idp SAML cert to local file (before Dex starts)
# Mock-idp generates new key pair on each restart, so we must fetch it.
# ─────────────────────────────────────────────────────────────────────
sync_mock_idp_cert() {
    echo ">>> Syncing SAML IdP cert from mock-idp HTTP endpoint..."
    for i in $(seq 1 15); do
        if curl -sf http://localhost:9090/saml/key > /tmp/_mock_idp_key.json 2>/dev/null; then
            break
        fi
        sleep 2
    done
    if [ ! -s /tmp/_mock_idp_key.json ]; then
        echo ">>> ERROR: could not fetch cert from mock-idp /saml/key"
        return 1
    fi
    python3 -c "
import json
with open('/tmp/_mock_idp_key.json') as f:
    d = json.load(f)
with open('${DOCKER_DEX_DIR}/saml_idp_cert.pem', 'w') as f:
    f.write(d['cert_pem'])
with open('${DOCKER_DEX_DIR}/saml_idp_key.pem', 'w') as f:
    f.write(d['key_pem'])
print('>>> Cert + key written to ${DOCKER_DEX_DIR}/')
"
}

# ─────────────────────────────────────────────────────────────────────
# Helper: restart Dex (+ mock-idp) from clean image snapshot
# ─────────────────────────────────────────────────────────────────────
restart_dex() {
    echo ""
    echo ">>> Tearing down Dex + mock-idp..."
    docker compose -f "$COMPOSE_FILE" --profile dex down --timeout 10 2>&1 || true
    sleep 2

    # Start mock-idp only first (needs to be up before cert sync)
    # The "dex" profile includes mock-idp, so we use service name to start just mock-idp
    echo ">>> Starting mock-idp..."
    docker compose -f "$COMPOSE_FILE" --profile dex up -d mock-idp 2>&1
    echo ">>> Waiting for mock-idp..."
    for i in $(seq 1 30); do
        if curl -sf http://localhost:9090/health > /dev/null 2>&1; then
            echo ">>> mock-idp ready after ~$((i * 2))s"
            break
        fi
        sleep 2
    done

    # Sync the cert BEFORE starting Dex (Dex mounts it as read-only volume)
    sync_mock_idp_cert

    # Now start Dex (mock-idp already running, compose will just add dex)
    echo ">>> Starting Dex..."
    docker compose -f "$COMPOSE_FILE" --profile dex up -d dex 2>&1
    echo ">>> Waiting for Dex..."
    for i in $(seq 1 30); do
        if curl -sf http://localhost:5556/dex/healthz > /dev/null 2>&1; then
            echo ">>> Dex ready after ~$((i * 2))s"
            # Verify SAML connector loaded successfully
            docker compose -f "$COMPOSE_FILE" --profile dex logs dex 2>&1 | grep -i 'error\|connector' | tail -5
            return 0
        fi
        sleep 2
    done
    echo ">>> ERROR: Dex did not become ready"
    docker compose -f "$COMPOSE_FILE" --profile dex logs dex 2>&1 | tail -20
    return 1
}

# ─────────────────────────────────────────────────────────────────────
# Run 1: OIDC JWT
# ─────────────────────────────────────────────────────────────────────
echo ""
echo "================================================================="
echo "[1/2] OIDC JWT experiment (with sweep)"
echo "================================================================="

restart_dex

echo ">>> Running OIDC JWT campaign..."
cd "$FUZZER_DIR"
python3 -m src.stateful.campaign_runner \
    --profile "$PROFILE_OIDC" \
    --invariants I1,I2,I3,I4,I5 \
    --sequences-per-invariant 5 \
    --mutation-sweep \
    --output-dir "$RESULTS_DIR/oidc_jwt" \
    2>&1 | tee "$LOG_DIR/oidc_jwt_${TIMESTAMP}.log"

OIDC_EXIT=${PIPESTATUS[0]}
echo ""
echo ">>> OIDC JWT campaign finished (exit=$OIDC_EXIT) at $(date -Iseconds)"
echo ""

# ─────────────────────────────────────────────────────────────────────
# Run 2: SAML
# ─────────────────────────────────────────────────────────────────────
echo ""
echo "================================================================="
echo "[2/2] SAML experiment (with sweep)"
echo "================================================================="

restart_dex

echo ">>> Running SAML campaign..."
cd "$FUZZER_DIR"
python3 -m src.stateful.campaign_runner \
    --profile "$PROFILE_SAML" \
    --invariants I1,I2,I3,I4,I5 \
    --sequences-per-invariant 5 \
    --mutation-sweep \
    --output-dir "$RESULTS_DIR/saml" \
    2>&1 | tee "$LOG_DIR/saml_${TIMESTAMP}.log"

SAML_EXIT=${PIPESTATUS[0]}
echo ""
echo ">>> SAML campaign finished (exit=$SAML_EXIT) at $(date -Iseconds)"

# ─────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────
echo ""
echo "================================================================="
echo "All experiments complete at $(date -Iseconds)"
echo "================================================================="
echo ""
echo "Results:"
echo "  OIDC JWT: $RESULTS_DIR/oidc_jwt/"
echo "  SAML:     $RESULTS_DIR/saml/"
echo "  Logs:     $LOG_DIR/"
echo ""

for proto in oidc_jwt saml; do
    summary=$(find "$RESULTS_DIR/$proto" -name "summary.json" -type f 2>/dev/null | head -1)
    if [ -n "$summary" ]; then
        echo "--- $proto ---"
        python3 -c "
import json
with open('$summary') as f:
    d = json.load(f)
print(f'  Sequences: {d[\"total_sequences\"]}')
print(f'  Status: {d[\"by_status\"]}')
print(f'  Findings: {d[\"total_findings\"]} (unique: {d[\"unique_findings\"]})')
print(f'  By invariant: {d.get(\"findings_by_invariant\", {})}')
print(f'  Sweep findings: {d.get(\"sweep_summary\", {}).get(\"total_sweep_findings\", 0)}')
" 2>/dev/null || echo "  (could not parse summary)"
        echo ""
    fi
done

echo "Done."
