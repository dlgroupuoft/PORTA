#!/usr/bin/env bash
# =============================================================================
# Logto Experiment 3 — Full run (OIDC JWT + SAML) with mutation sweep
#
# Uses platform-images.yml (pre-built images, no docker build).
# Each protocol run gets a fresh Logto by stopping + removing containers.
# Mutation sweep runs on completed sequences (findings tagged separately).
#
# Usage:
#   tmux new-session -d -s logto-exp3 'bash /home/ubuntu/broker/fuzzer/scripts/run_logto_exp3.sh'
#   tmux attach -t logto-exp3   # to watch live
#
# This script is fully unattended — no confirmation prompts.
# =============================================================================
set -uo pipefail  # no -e: campaign failures must not abort the script

export OPENAI_API_KEY="${OPENAI_API_KEY:?Set OPENAI_API_KEY env var before running}"

FUZZER_DIR="/home/ubuntu/broker/fuzzer"
COMPOSE_FILE="$FUZZER_DIR/docker/platform-images.yml"
RESULTS_DIR="$FUZZER_DIR/results/final-exp3/logto"
LOG_DIR="$RESULTS_DIR/logs"
PROFILE_OIDC="$FUZZER_DIR/src/profiles/logto_oidc_jwt_exp-1_20260331_012637.json"
PROFILE_SAML="$FUZZER_DIR/src/profiles/logto_saml_exp-1_20260331_012921.json"

mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUNLOG="$LOG_DIR/run_${TIMESTAMP}.log"

exec > >(tee -a "$RUNLOG") 2>&1

echo "================================================================="
echo "Logto Experiment 3 — started at $(date -Iseconds)"
echo "================================================================="
echo "FUZZER_DIR=$FUZZER_DIR"
echo "COMPOSE_FILE=$COMPOSE_FILE"
echo "PROFILE_OIDC=$PROFILE_OIDC"
echo "PROFILE_SAML=$PROFILE_SAML"
echo "RESULTS_DIR=$RESULTS_DIR"
echo ""

# ─────────────────────────────────────────────────────────────────────
# Helper: start fresh Logto + mock-idp via platform-images.yml
#   docker compose down removes containers (no volumes = clean DB)
#   docker compose up recreates with empty postgres
# ─────────────────────────────────────────────────────────────────────
restart_logto() {
    echo ""
    echo ">>> Stopping Logto + mock-idp containers..."
    docker compose -f "$COMPOSE_FILE" --profile logto down --timeout 10 2>&1 || true
    sleep 2

    echo ">>> Starting fresh Logto + mock-idp..."
    docker compose -f "$COMPOSE_FILE" --profile logto up -d 2>&1

    echo ">>> Waiting for Logto to become ready (HTTP check)..."
    for i in $(seq 1 90); do
        code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/oidc/.well-known/openid-configuration 2>/dev/null || echo "000")
        if [ "$code" = "200" ]; then
            echo ">>> Logto ready after ~$((i * 3))s (HTTP $code)"
            sleep 2  # brief settle
            return 0
        fi
        sleep 3
    done
    echo ">>> ERROR: Logto did not become ready within ~4.5 minutes"
    docker compose -f "$COMPOSE_FILE" --profile logto logs --tail 30 2>&1
    return 1
}

# ─────────────────────────────────────────────────────────────────────
# Run 1: OIDC JWT
# ─────────────────────────────────────────────────────────────────────
echo ""
echo "================================================================="
echo "[1/2] OIDC JWT experiment (with sweep)"
echo "================================================================="

restart_logto

echo ">>> Running OIDC JWT campaign..."
cd "$FUZZER_DIR"
python3 -m src.stateful.campaign_runner \
    --profile "$PROFILE_OIDC" \
    --invariants I1,I2,I3,I4,I5 \
    --sequences-per-invariant 10 \
    --output-dir "$RESULTS_DIR/oidc_jwt" \
    --setup-platform \
    --mutation-sweep \
    --sweep-priority high \
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

restart_logto

echo ">>> Running SAML campaign..."
cd "$FUZZER_DIR"
python3 -m src.stateful.campaign_runner \
    --profile "$PROFILE_SAML" \
    --invariants I1,I2,I3,I4,I5 \
    --sequences-per-invariant 10 \
    --output-dir "$RESULTS_DIR/saml" \
    --setup-platform \
    --mutation-sweep \
    --sweep-priority high \
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
sweep = d.get('sweep_summary', {})
if sweep:
    print(f'  Sweep: {sweep.get(\"total_sweep_findings\", 0)} findings from {len(sweep.get(\"by_mutation\", {}))} mutations')
" 2>/dev/null || echo "  (could not parse summary)"
        echo ""
    fi
done

echo "Done."
