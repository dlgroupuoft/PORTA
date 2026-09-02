#!/usr/bin/env bash
# =============================================================================
# Authentik Experiment 1 — Full run (SAML + OIDC JWT)
#
# Usage:
#   tmux new-session -d -s authentik-exp1 'bash /home/ubuntu/broker/fuzzer/scripts/run_authentik_exp1.sh'
#   tmux attach -t authentik-exp1   # to watch live
#
# This script is fully unattended — no confirmation prompts.
# Each protocol run gets a fresh authentik database.
# =============================================================================
set -euo pipefail

export OPENAI_API_KEY="${OPENAI_API_KEY:?Set OPENAI_API_KEY env var before running}"
export VALENCE_ADMIN_TOKEN='fuzzer-authentik-bootstrap-api-token'

FUZZER_DIR="/home/ubuntu/broker/fuzzer"
COMPOSE_DIR="$FUZZER_DIR/docker/authentik"
RESULTS_DIR="$FUZZER_DIR/results/final-exp3/authentik"
LOG_DIR="$RESULTS_DIR/logs"
PROFILE_SAML="$FUZZER_DIR/src/profiles/authentik_saml_exp-1_20260330_013225.json"
PROFILE_OIDC="$FUZZER_DIR/src/profiles/authentik_oidc_jwt_exp-1_20260330_013002.json"

mkdir -p "$LOG_DIR"

# Record start time and environment
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUNLOG="$LOG_DIR/run_${TIMESTAMP}.log"

exec > >(tee -a "$RUNLOG") 2>&1

echo "================================================================="
echo "Authentik Experiment 1 — started at $(date -Iseconds)"
echo "================================================================="
echo "FUZZER_DIR=$FUZZER_DIR"
echo "PROFILE_SAML=$PROFILE_SAML"
echo "PROFILE_OIDC=$PROFILE_OIDC"
echo "RESULTS_DIR=$RESULTS_DIR"
echo ""

# ─────────────────────────────────────────────────────────────────────
# Helper: restart authentik with fresh database
# ─────────────────────────────────────────────────────────────────────
restart_authentik() {
    echo ""
    echo ">>> Restarting authentik with fresh database..."
    cd "$COMPOSE_DIR"
    docker compose down -v --timeout 10 2>&1 || true
    docker compose up -d 2>&1
    echo ">>> Waiting for authentik to become ready..."
    for i in $(seq 1 60); do
        code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/api/v3/root/config/ 2>/dev/null || echo "000")
        if [ "$code" = "200" ]; then
            echo ">>> Authentik ready after ~$((i * 5))s"
            return 0
        fi
        sleep 5
    done
    echo ">>> ERROR: Authentik did not become ready within 5 minutes"
    return 1
}

# ─────────────────────────────────────────────────────────────────────
# Run 1: SAML
# ─────────────────────────────────────────────────────────────────────
echo ""
echo "================================================================="
echo "[1/2] SAML experiment"
echo "================================================================="

restart_authentik

echo ">>> Running SAML campaign..."
cd "$FUZZER_DIR"
python3 -m src.stateful.campaign_runner \
    --profile "$PROFILE_SAML" \
    --invariants I1,I2,I3,I4,I5 \
    --sequences-per-invariant 10 \
    --output-dir "$RESULTS_DIR/saml" \
    2>&1 | tee "$LOG_DIR/saml_${TIMESTAMP}.log"

SAML_EXIT=$?
echo ""
echo ">>> SAML campaign finished (exit=$SAML_EXIT) at $(date -Iseconds)"
echo ""

# ─────────────────────────────────────────────────────────────────────
# Run 2: OIDC JWT
# ─────────────────────────────────────────────────────────────────────
echo ""
echo "================================================================="
echo "[2/2] OIDC JWT experiment"
echo "================================================================="

restart_authentik

echo ">>> Running OIDC JWT campaign..."
cd "$FUZZER_DIR"
python3 -m src.stateful.campaign_runner \
    --profile "$PROFILE_OIDC" \
    --invariants I1,I2,I3,I4,I5 \
    --sequences-per-invariant 10 \
    --output-dir "$RESULTS_DIR/oidc_jwt" \
    2>&1 | tee "$LOG_DIR/oidc_jwt_${TIMESTAMP}.log"

OIDC_EXIT=$?
echo ""
echo ">>> OIDC JWT campaign finished (exit=$OIDC_EXIT) at $(date -Iseconds)"

# ─────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────
echo ""
echo "================================================================="
echo "All experiments complete at $(date -Iseconds)"
echo "================================================================="
echo ""
echo "Results:"
echo "  SAML:     $RESULTS_DIR/saml/"
echo "  OIDC JWT: $RESULTS_DIR/oidc_jwt/"
echo "  Logs:     $LOG_DIR/"
echo ""

# Print quick summary from each result
for proto in saml oidc_jwt; do
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
