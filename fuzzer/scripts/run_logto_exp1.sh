#!/usr/bin/env bash
# =============================================================================
# Logto Experiment 1 — Full run (OIDC JWT + SAML)
#
# Usage:
#   tmux new-session -d -s logto-exp1 'bash /home/ubuntu/broker/fuzzer/scripts/run_logto_exp1.sh'
#   tmux attach -t logto-exp1   # to watch live
#
# This script is fully unattended — no confirmation prompts.
# Each protocol run gets a fresh Logto database (docker-compose down -v + up).
# =============================================================================
set -euo pipefail

export OPENAI_API_KEY="${OPENAI_API_KEY:?Set OPENAI_API_KEY env var before running}"

FUZZER_DIR="/home/ubuntu/broker/fuzzer"
LOGTO_COMPOSE_DIR="/home/ubuntu/broker/platform/logto"
MOCKIDP_COMPOSE_DIR="$FUZZER_DIR/docker"
RESULTS_DIR="$FUZZER_DIR/results/final-exp1/logto"
LOG_DIR="$RESULTS_DIR/logs"
PROFILE_OIDC="$FUZZER_DIR/src/profiles/logto_oidc_jwt_exp-1_20260330_014157.json"
PROFILE_SAML="$FUZZER_DIR/src/profiles/logto_saml_exp-1_20260330_014426.json"

mkdir -p "$LOG_DIR"

# Record start time and environment
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUNLOG="$LOG_DIR/run_${TIMESTAMP}.log"

exec > >(tee -a "$RUNLOG") 2>&1

echo "================================================================="
echo "Logto Experiment 1 — started at $(date -Iseconds)"
echo "================================================================="
echo "FUZZER_DIR=$FUZZER_DIR"
echo "PROFILE_OIDC=$PROFILE_OIDC"
echo "PROFILE_SAML=$PROFILE_SAML"
echo "RESULTS_DIR=$RESULTS_DIR"
echo ""

# ─────────────────────────────────────────────────────────────────────
# Helper: ensure mock-idp is running (shared across all platforms)
# ─────────────────────────────────────────────────────────────────────
ensure_mock_idp() {
    echo ">>> Checking mock-idp..."
    if ! curl -sf http://localhost:9090/health > /dev/null 2>&1; then
        echo ">>> mock-idp not running, starting..."
        cd "$MOCKIDP_COMPOSE_DIR"
        docker compose up -d mock-idp 2>&1
        for i in $(seq 1 30); do
            if curl -sf http://localhost:9090/health > /dev/null 2>&1; then
                echo ">>> mock-idp ready after ~$((i * 2))s"
                return 0
            fi
            sleep 2
        done
        echo ">>> ERROR: mock-idp did not become ready"
        return 1
    fi
    echo ">>> mock-idp OK"
}

# ─────────────────────────────────────────────────────────────────────
# Helper: restart Logto with fresh database
# Postgres has NO persistent volume, so down -v wipes everything.
# ─────────────────────────────────────────────────────────────────────
restart_logto() {
    echo ""
    echo ">>> Restarting Logto with fresh database..."
    cd "$LOGTO_COMPOSE_DIR"
    docker compose down -v --timeout 10 2>&1 || true
    sleep 3

    # Reset mock-idp state (nonce mode, claims, signing key)
    echo ">>> Resetting mock-idp state..."
    curl -sf -X POST http://localhost:9090/admin/set-nonce-mode \
         -H 'Content-Type: application/json' \
         -d '{"omit_nonce": true}' > /dev/null 2>&1 || true
    curl -sf -X POST http://localhost:9090/admin/set-claims \
         -H 'Content-Type: application/json' \
         -d '{"sub": "default-user", "email": "default@mock.local", "name": "Default User", "groups": ["default"], "email_verified": true}' > /dev/null 2>&1 || true

    # Start Logto fresh
    docker compose up -d 2>&1

    # Ensure Logto is on the valence-net (for mock-idp connectivity)
    docker network connect docker_valence-net logto-app-1 2>/dev/null || true

    echo ">>> Waiting for Logto to become ready..."
    for i in $(seq 1 90); do
        code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/oidc/.well-known/openid-configuration 2>/dev/null || echo "000")
        if [ "$code" = "200" ]; then
            echo ">>> Logto ready after ~$((i * 3))s"
            return 0
        fi
        sleep 3
    done
    echo ">>> ERROR: Logto did not become ready within ~4.5 minutes"
    return 1
}

# ─────────────────────────────────────────────────────────────────────
# Run 1: OIDC JWT
# ─────────────────────────────────────────────────────────────────────
echo ""
echo "================================================================="
echo "[1/2] OIDC JWT experiment"
echo "================================================================="

ensure_mock_idp
restart_logto

echo ">>> Running OIDC JWT campaign..."
cd "$FUZZER_DIR"
python3 -m src.stateful.campaign_runner \
    --profile "$PROFILE_OIDC" \
    --invariants I1,I2,I3,I4,I5 \
    --sequences-per-invariant 5 \
    --output-dir "$RESULTS_DIR/oidc_jwt" \
    --setup-platform \
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
echo "[2/2] SAML experiment"
echo "================================================================="

restart_logto

echo ">>> Running SAML campaign..."
cd "$FUZZER_DIR"
python3 -m src.stateful.campaign_runner \
    --profile "$PROFILE_SAML" \
    --invariants I1,I2,I3,I4,I5 \
    --sequences-per-invariant 5 \
    --output-dir "$RESULTS_DIR/saml" \
    --setup-platform \
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

# Print quick summary from each result
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
" 2>/dev/null || echo "  (could not parse summary)"
        echo ""
    fi
done

echo "Done."
