#!/usr/bin/env bash
# =============================================================================
# Vault Experiment 3 — OIDC JWT with mutation sweep
#
# Uses platform-images.yml for clean-state restarts.
# Vault dev mode = in-memory, so stop+rm+up = fully clean state.
# Mock-idp is auto-started with the vault profile.
#
# NOTE: Vault OSS (1.21.4) does NOT support SAML auth (Enterprise only).
#       Only OIDC JWT is tested.
#
# --setup-platform ensures:
#   - JWT auth method enabled
#   - Campaign's own public key injected into Vault JWT config
#     (so jwt_validation_pubkeys matches the key used by mint_custom_jwt)
#   - KV v2 engine enabled
#
# Usage:
#   tmux new-session -d -s vault-exp3 'bash /home/ubuntu/broker/fuzzer/scripts/run_vault_exp3.sh'
#   tmux attach -t vault-exp3   # to watch live
# =============================================================================
set -euo pipefail

export OPENAI_API_KEY="${OPENAI_API_KEY:?Set OPENAI_API_KEY env var before running}"

FUZZER_DIR="/home/ubuntu/broker/fuzzer"
COMPOSE_FILE="$FUZZER_DIR/docker/platform-images.yml"
RESULTS_DIR="$FUZZER_DIR/results/final-exp3/vault"
LOG_DIR="$RESULTS_DIR/logs"

PROFILE_OIDC="$FUZZER_DIR/src/profiles/vault_oidc_jwt_exp-1_20260330_212231.json"

mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUNLOG="$LOG_DIR/run_${TIMESTAMP}.log"
exec > >(tee -a "$RUNLOG") 2>&1

echo "================================================================="
echo "Vault Experiment 3 — started at $(date -Iseconds)"
echo "================================================================="
echo "COMPOSE_FILE=$COMPOSE_FILE"
echo "PROFILE_OIDC=$PROFILE_OIDC"
echo "RESULTS_DIR=$RESULTS_DIR"
echo "Sweep: enabled (--mutation-sweep)"
echo "Setup: enabled (--setup-platform)"
echo ""

# Save this script for reproducibility
cp "$0" "$RESULTS_DIR/run_script_${TIMESTAMP}.sh" 2>/dev/null || true

# ─────────────────────────────────────────────────────────────────────
# Helper: restart Vault from clean state
# Only restarts the vault container — leaves mock-idp untouched
# (mock-idp may be shared with other experiments like logto)
# Vault dev-mode = in-memory, so stop+rm+up = fully clean state.
# ─────────────────────────────────────────────────────────────────────
restart_vault() {
    echo ""
    echo ">>> Stopping vault container only (preserving mock-idp)..."
    docker compose -f "$COMPOSE_FILE" --profile vault stop vault --timeout 10 2>&1 || true
    docker compose -f "$COMPOSE_FILE" --profile vault rm -f vault 2>&1 || true
    sleep 2

    # Ensure mock-idp is running (start if not already up)
    echo ">>> Ensuring mock-idp is running..."
    docker compose -f "$COMPOSE_FILE" --profile vault up -d mock-idp 2>&1
    for i in $(seq 1 30); do
        if curl -sf http://localhost:9090/health > /dev/null 2>&1; then
            echo ">>> mock-idp ready after ~$((i * 2))s"
            break
        fi
        sleep 2
    done

    # Start fresh vault
    echo ">>> Starting fresh Vault container..."
    docker compose -f "$COMPOSE_FILE" --profile vault up -d vault 2>&1

    # Wait for Vault
    echo ">>> Waiting for Vault..."
    for i in $(seq 1 30); do
        if curl -sf http://localhost:8200/v1/sys/health > /dev/null 2>&1; then
            echo ">>> Vault ready after ~$((i * 2))s"
            break
        fi
        sleep 2
    done

    echo ">>> Vault restart complete (setup-platform will configure auth)"
}

# ─────────────────────────────────────────────────────────────────────
# Helper: print summary from campaign results
# ─────────────────────────────────────────────────────────────────────
print_summary() {
    local proto="$1"
    local dir="$RESULTS_DIR/$proto"
    local summary
    summary=$(find "$dir" -name "summary.json" -type f 2>/dev/null | sort | tail -1)
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
# Run: OIDC JWT (with sweep + setup-platform)
# ─────────────────────────────────────────────────────────────────────
echo ""
echo "================================================================="
echo "[1/1] OIDC JWT experiment (with sweep)"
echo "================================================================="

restart_vault

echo ">>> Running OIDC JWT campaign (--setup-platform --mutation-sweep)..."
cd "$FUZZER_DIR"
python3 -m src.stateful.campaign_runner \
    --profile "$PROFILE_OIDC" \
    --invariants I1,I2,I3,I4,I5 \
    --sequences-per-invariant 5 \
    --mutation-sweep \
    --setup-platform \
    --output-dir "$RESULTS_DIR/oidc_jwt" \
    2>&1 | tee "$LOG_DIR/oidc_jwt_${TIMESTAMP}.log" || true

OIDC_EXIT=${PIPESTATUS[0]}
echo ""
echo ">>> OIDC JWT campaign finished (exit=$OIDC_EXIT) at $(date -Iseconds)"

# Save Vault logs
docker compose -f "$COMPOSE_FILE" --profile vault logs vault > "$LOG_DIR/vault_oidc_${TIMESTAMP}.docker.log" 2>&1 || true

# ─────────────────────────────────────────────────────────────────────
# Final teardown (vault only — leave mock-idp for other experiments)
# ─────────────────────────────────────────────────────────────────────
echo ""
echo ">>> Final teardown (vault container only)..."
docker compose -f "$COMPOSE_FILE" --profile vault stop vault --timeout 10 2>&1 || true
docker compose -f "$COMPOSE_FILE" --profile vault rm -f vault 2>&1 || true

# ─────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────
echo ""
echo "================================================================="
echo "Experiment complete at $(date -Iseconds)"
echo "================================================================="
echo ""
echo "Results:"
echo "  OIDC JWT: $RESULTS_DIR/oidc_jwt/"
echo "  Logs:     $LOG_DIR/"
echo ""
echo "Note: Vault SAML skipped — not available in Vault OSS (requires Enterprise)"
echo ""

print_summary "oidc_jwt"

echo "Done."
