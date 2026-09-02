#!/usr/bin/env bash
# =============================================================================
# Authentik Experiment 3 — Full run with sweep (SAML + OIDC JWT)
#
# Uses fresh docker containers per protocol to avoid resource conflicts.
# Sweep mode enabled for additional mutation-based findings.
#
# Usage:
#   tmux new-session -d -s ak-exp3 'bash /home/ubuntu/broker/fuzzer/scripts/run_authentik_exp3.sh'
#   tmux attach -t ak-exp3
# =============================================================================
set -euo pipefail

export OPENAI_API_KEY="${OPENAI_API_KEY:?Set OPENAI_API_KEY env var before running}"
export VALENCE_ADMIN_TOKEN='fuzzer-authentik-bootstrap-api-token'

FUZZER_DIR="/home/ubuntu/broker/fuzzer"
COMPOSE_DIR="$FUZZER_DIR/docker/authentik"
RESULTS_BASE="$FUZZER_DIR/results/final-exp3"
RESULTS_DIR="$RESULTS_BASE/authentik"
LOG_DIR="$RESULTS_DIR/logs"

PROFILE_SAML="$FUZZER_DIR/src/profiles/authentik_saml_exp-1_20260331_012344.json"
PROFILE_OIDC="$FUZZER_DIR/src/profiles/authentik_oidc_jwt_exp-1_20260331_012128.json"

mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUNLOG="$LOG_DIR/run_${TIMESTAMP}.log"
exec > >(tee -a "$RUNLOG") 2>&1

echo "================================================================="
echo "Authentik Experiment 3 — started at $(date -Iseconds)"
echo "================================================================="
echo "Profiles:"
echo "  SAML: $PROFILE_SAML"
echo "  OIDC: $PROFILE_OIDC"
echo "Output: $RESULTS_DIR"
echo "Sweep: enabled (--mutation-sweep)"
echo ""

# ─────────────────────────────────────────────────────────────────────
# Helper: destroy and recreate authentik from scratch
# ─────────────────────────────────────────────────────────────────────
fresh_authentik() {
    echo ""
    echo ">>> Destroying and recreating authentik (fresh image + DB)..."
    cd "$COMPOSE_DIR"

    # Full teardown: remove containers, volumes, orphans
    docker compose down -v --remove-orphans --timeout 10 2>&1 || true

    # Start fresh
    docker compose up -d 2>&1

    echo ">>> Waiting for authentik to become ready..."
    for i in $(seq 1 60); do
        code=$(curl -s -o /dev/null -w "%{http_code}" \
            http://localhost:9000/api/v3/root/config/ 2>/dev/null || echo "000")
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
# Helper: print quick summary from campaign results
# ─────────────────────────────────────────────────────────────────────
print_summary() {
    local proto="$1"
    local dir="$RESULTS_DIR/$proto"
    local summary
    summary=$(find "$dir" -name "summary.json" -path "*/full/*" -not -path "*vault*" -type f 2>/dev/null | head -1)
    if [ -n "$summary" ]; then
        echo "--- $proto results ---"
        python3 -c "
import json
with open('$summary') as f:
    d = json.load(f)
print(f'  Sequences: {d[\"total_sequences\"]}')
print(f'  Status: {d[\"by_status\"]}')
print(f'  Findings: {d[\"total_findings\"]} (unique: {d[\"unique_findings\"]})')
print(f'  By invariant: {d.get(\"findings_by_invariant\", {})}')
ss = d.get('sweep_summary', {})
if ss.get('total_sweep_findings', 0) > 0:
    print(f'  Sweep findings: {ss[\"total_sweep_findings\"]}')
" 2>/dev/null || echo "  (could not parse summary)"
        echo ""
    fi
}

# ─────────────────────────────────────────────────────────────────────
# Run 1: SAML
# ─────────────────────────────────────────────────────────────────────
echo "================================================================="
echo "[1/2] SAML experiment"
echo "================================================================="

fresh_authentik

echo ">>> Running SAML campaign (with sweep)..."
cd "$FUZZER_DIR"
python3 -m src.stateful.campaign_runner \
    --profile "$PROFILE_SAML" \
    --invariants I1,I2,I3,I4,I5 \
    --sequences-per-invariant 10 \
    --mutation-sweep \
    --output-dir "$RESULTS_DIR/saml" \
    2>&1 | tee "$LOG_DIR/saml_${TIMESTAMP}.log"

echo ">>> SAML campaign finished at $(date -Iseconds)"
print_summary "saml"

# ─────────────────────────────────────────────────────────────────────
# Run 2: OIDC JWT
# ─────────────────────────────────────────────────────────────────────
echo "================================================================="
echo "[2/2] OIDC JWT experiment"
echo "================================================================="

fresh_authentik

echo ">>> Running OIDC JWT campaign (with sweep)..."
cd "$FUZZER_DIR"
python3 -m src.stateful.campaign_runner \
    --profile "$PROFILE_OIDC" \
    --invariants I1,I2,I3,I4,I5 \
    --sequences-per-invariant 10 \
    --mutation-sweep \
    --output-dir "$RESULTS_DIR/oidc_jwt" \
    2>&1 | tee "$LOG_DIR/oidc_jwt_${TIMESTAMP}.log"

echo ">>> OIDC JWT campaign finished at $(date -Iseconds)"
print_summary "oidc_jwt"

# ─────────────────────────────────────────────────────────────────────
# Final summary
# ─────────────────────────────────────────────────────────────────────
echo ""
echo "================================================================="
echo "All experiments complete at $(date -Iseconds)"
echo "================================================================="
echo ""
echo "Results:  $RESULTS_DIR/"
echo "Logs:     $LOG_DIR/"
echo ""
print_summary "saml"
print_summary "oidc_jwt"
echo "Done."
