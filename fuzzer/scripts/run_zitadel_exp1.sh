#!/usr/bin/env bash
# =============================================================================
# VALENCE Experiment 1 — Zitadel only (OIDC JWT + SAML)
# =============================================================================
# Fresh containers between each protocol. Unattended, no confirmation needed.
# Includes --setup-platform to auto-create project, OIDC client, JWT IdP.
# Reads PAT from container and injects as VALENCE_ADMIN_TOKEN.
#
# Usage:
#   tmux new-session -d -s zitadel-exp1 'bash /home/ubuntu/broker/fuzzer/scripts/run_zitadel_exp1.sh'
#   tmux attach -t zitadel-exp1
# =============================================================================
set -euo pipefail

export OPENAI_API_KEY="${OPENAI_API_KEY:?Set OPENAI_API_KEY env var before running}"

FUZZER_DIR="/home/ubuntu/broker/fuzzer"
COMPOSE_FILE="$FUZZER_DIR/docker/platform-images.yml"
RESULTS_DIR="$FUZZER_DIR/results/final-exp1/zitadel"
LOG_DIR="$RESULTS_DIR/logs"

PROFILE_OIDC="$FUZZER_DIR/src/profiles/zitadel_oidc_jwt_exp-1_20260331_182000.json"
PROFILE_SAML="$FUZZER_DIR/src/profiles/zitadel_saml_exp-1_20260331_182253.json"

mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUNLOG="$LOG_DIR/run_${TIMESTAMP}.log"
exec > >(tee -a "$RUNLOG") 2>&1

echo "================================================================="
echo "Zitadel Experiment 1 — started at $(date -Iseconds)"
echo "================================================================="
echo "COMPOSE_FILE=$COMPOSE_FILE"
echo "PROFILE_OIDC=$PROFILE_OIDC"
echo "PROFILE_SAML=$PROFILE_SAML"
echo "RESULTS_DIR=$RESULTS_DIR"
echo ""

# ─────────────────────────────────────────────────────────────────────
# Helper: destroy and recreate zitadel from scratch, read PAT
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
        code=$(curl -s -o /dev/null -w "%{http_code}" \
            http://localhost:8085/debug/ready 2>/dev/null || echo "000")
        if [ "$code" = "200" ]; then
            echo ">>> Zitadel ready after ~$((i * 5))s"
            sleep 3
            break
        fi
        sleep 5
    done

    if [ "$code" != "200" ]; then
        echo ">>> ERROR: Zitadel not ready within 5 minutes"
        docker compose -f "$COMPOSE_FILE" --profile zitadel logs --tail 30 2>&1
        return 1
    fi

    # Read PAT from container volume
    echo ">>> Reading PAT from container..."
    export VALENCE_ADMIN_TOKEN=""
    for i in $(seq 1 10); do
        docker cp docker-zitadel-1:/data/pat/zitadel-admin.pat /tmp/_zitadel_pat 2>/dev/null
        PAT=$(cat /tmp/_zitadel_pat 2>/dev/null)
        if [ -n "$PAT" ]; then
            export VALENCE_ADMIN_TOKEN="$PAT"
            echo ">>> PAT obtained: ${PAT:0:20}..."
            break
        fi
        sleep 2
    done

    if [ -z "$VALENCE_ADMIN_TOKEN" ]; then
        echo ">>> ERROR: Could not obtain PAT from container"
        return 1
    fi

    # Verify PAT works
    VERIFY=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $VALENCE_ADMIN_TOKEN" \
        http://localhost:8085/management/v1/orgs/me 2>/dev/null || echo "000")
    echo ">>> PAT verification: HTTP $VERIFY"
    if [ "$VERIFY" != "200" ]; then
        echo ">>> WARNING: PAT verification failed (HTTP $VERIFY)"
    fi

    return 0
}

# ─────────────────────────────────────────────────────────────────────
# Run 1: OIDC JWT
# ─────────────────────────────────────────────────────────────────────
echo ""
echo "================================================================="
echo "[1/2] OIDC JWT experiment"
echo "================================================================="

restart_zitadel

echo ">>> Running OIDC JWT campaign (with --setup-platform)..."
cd "$FUZZER_DIR"
python3 -m src.stateful.campaign_runner \
    --profile "$PROFILE_OIDC" \
    --invariants I1,I2,I3,I4,I5 \
    --sequences-per-invariant 5 \
    --setup-platform \
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

echo ">>> Running SAML campaign (with --setup-platform)..."
cd "$FUZZER_DIR"
python3 -m src.stateful.campaign_runner \
    --profile "$PROFILE_SAML" \
    --invariants I1,I2,I3,I4,I5 \
    --sequences-per-invariant 5 \
    --setup-platform \
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
echo "Results:"
echo "  OIDC JWT: $RESULTS_DIR/oidc_jwt/"
echo "  SAML:     $RESULTS_DIR/saml/"
echo "  Logs:     $LOG_DIR/"
echo ""

for proto in oidc_jwt saml; do
    summary=$(find "$RESULTS_DIR/$proto" -name "summary.json" -type f 2>/dev/null | sort | tail -1)
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
