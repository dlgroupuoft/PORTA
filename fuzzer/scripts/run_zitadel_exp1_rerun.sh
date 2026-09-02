#!/usr/bin/env bash
# =============================================================================
# Zitadel Experiment 1 — Rerun after base_url fix (8080 -> 8085)
#
# Usage:
#   tmux new-session -d -s zitadel-exp1 'bash /home/ubuntu/broker/fuzzer/scripts/run_zitadel_exp1_rerun.sh'
#   tmux attach -t zitadel-exp1
# =============================================================================
set -euo pipefail

export OPENAI_API_KEY="${OPENAI_API_KEY:?Set OPENAI_API_KEY env var before running}"

FUZZER_DIR="/home/ubuntu/broker/fuzzer"
COMPOSE_FILE="$FUZZER_DIR/docker/platform-images.yml"
RESULTS_DIR="$FUZZER_DIR/results/final-exp1/zitadel"
LOG_DIR="$RESULTS_DIR/logs"

PROFILE_OIDC="$FUZZER_DIR/src/profiles/zitadel_oidc_jwt_exp-1_20260331_004400.json"
PROFILE_SAML="$FUZZER_DIR/src/profiles/zitadel_saml_exp-1_20260331_004714.json"

mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUNLOG="$LOG_DIR/run_${TIMESTAMP}.log"
exec > >(tee -a "$RUNLOG") 2>&1

echo "================================================================="
echo "Zitadel Experiment 1 (rerun) — started at $(date -Iseconds)"
echo "================================================================="
echo "FIX: base_url changed from localhost:8080 to localhost:8085"
echo "PROFILE_OIDC=$PROFILE_OIDC"
echo "PROFILE_SAML=$PROFILE_SAML"
echo "RESULTS_DIR=$RESULTS_DIR"
echo ""

# Verify fix
python3 -c "
import json
for f in ['$PROFILE_OIDC', '$PROFILE_SAML']:
    with open(f) as fh:
        p = json.load(fh)
    print(f'{f.split(\"/\")[-1]}: base_url={p[\"base_url\"]}')
"
echo ""

# ─────────────────────────────────────────────────────────────────────
# Helper: fresh Zitadel restart
# ─────────────────────────────────────────────────────────────────────
restart_zitadel() {
    echo ""
    echo ">>> Tearing down Zitadel..."
    docker compose -f "$COMPOSE_FILE" --profile zitadel down -v --remove-orphans --timeout 10 2>&1 || true
    sleep 2

    echo ">>> Starting fresh Zitadel..."
    docker compose -f "$COMPOSE_FILE" --profile zitadel up -d 2>&1

    echo ">>> Waiting for Zitadel to become ready..."
    for i in $(seq 1 60); do
        code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8085/debug/ready 2>/dev/null || echo "000")
        if [ "$code" = "200" ]; then
            echo ">>> Zitadel ready after ~$((i * 5))s"
            sleep 3
            return 0
        fi
        sleep 5
    done
    echo ">>> ERROR: Zitadel not ready within 5 minutes"
    docker compose -f "$COMPOSE_FILE" --profile zitadel logs --tail 20 2>&1
    return 1
}

# ─────────────────────────────────────────────────────────────────────
# Run 1: OIDC JWT
# ─────────────────────────────────────────────────────────────────────
echo ""
echo "================================================================="
echo "[1/2] OIDC JWT experiment"
echo "================================================================="

restart_zitadel

echo ">>> Running OIDC JWT campaign..."
cd "$FUZZER_DIR"
python3 -m src.stateful.campaign_runner \
    --profile "$PROFILE_OIDC" \
    --invariants I1,I2,I3,I4,I5 \
    --sequences-per-invariant 5 \
    --output-dir "$RESULTS_DIR/oidc_jwt" \
    2>&1 | tee "$LOG_DIR/oidc_jwt_${TIMESTAMP}.log"

OIDC_EXIT=${PIPESTATUS[0]}
echo ""
echo ">>> OIDC JWT campaign finished (exit=$OIDC_EXIT) at $(date -Iseconds)"

# Save docker logs
docker compose -f "$COMPOSE_FILE" --profile zitadel logs --no-color > "$LOG_DIR/oidc_jwt_${TIMESTAMP}.docker.log" 2>&1 || true

# ─────────────────────────────────────────────────────────────────────
# Run 2: SAML
# ─────────────────────────────────────────────────────────────────────
echo ""
echo "================================================================="
echo "[2/2] SAML experiment"
echo "================================================================="

restart_zitadel

echo ">>> Running SAML campaign..."
cd "$FUZZER_DIR"
python3 -m src.stateful.campaign_runner \
    --profile "$PROFILE_SAML" \
    --invariants I1,I2,I3,I4,I5 \
    --sequences-per-invariant 5 \
    --output-dir "$RESULTS_DIR/saml" \
    2>&1 | tee "$LOG_DIR/saml_${TIMESTAMP}.log"

SAML_EXIT=${PIPESTATUS[0]}
echo ""
echo ">>> SAML campaign finished (exit=$SAML_EXIT) at $(date -Iseconds)"

# Save docker logs
docker compose -f "$COMPOSE_FILE" --profile zitadel logs --no-color > "$LOG_DIR/saml_${TIMESTAMP}.docker.log" 2>&1 || true

# Final teardown
docker compose -f "$COMPOSE_FILE" --profile zitadel down -v --remove-orphans --timeout 10 2>&1 || true

# ─────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────
echo ""
echo "================================================================="
echo "All experiments complete at $(date -Iseconds)"
echo "================================================================="
echo ""

for proto in oidc_jwt saml; do
    summary=$(find "$RESULTS_DIR/$proto" -name "summary.json" -path "*/full/*" -not -path "*vault*" -type f 2>/dev/null | sort | tail -1)
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

echo "Results: $RESULTS_DIR/"
echo "Logs:    $LOG_DIR/"
echo "Done."
