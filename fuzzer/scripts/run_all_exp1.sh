#!/usr/bin/env bash
# =============================================================================
# VALENCE Experiment 1 — All 7 platforms, OIDC + SAML
# =============================================================================
# Runs all platforms sequentially with fresh containers between each protocol.
# Designed for unattended overnight execution in tmux.
#
# Usage:
#   tmux new-session -d -s exp1 'bash /home/ubuntu/broker/fuzzer/scripts/run_all_exp1.sh'
#   tmux attach -t exp1
# =============================================================================
set -euo pipefail

export OPENAI_API_KEY="${OPENAI_API_KEY:?Set OPENAI_API_KEY env var before running}"
export VALENCE_ADMIN_TOKEN='fuzzer-authentik-bootstrap-api-token'

FUZZER_DIR="/home/ubuntu/broker/fuzzer"
COMPOSE_FILE="$FUZZER_DIR/docker/platform-images.yml"
AUTHENTIK_COMPOSE_DIR="$FUZZER_DIR/docker/authentik"
DOCKER_DEX_DIR="$FUZZER_DIR/docker/dex"
RESULTS_BASE="$FUZZER_DIR/results/final-exp1"
LOG_DIR="$RESULTS_BASE/logs"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUNLOG="$LOG_DIR/run_all_${TIMESTAMP}.log"

mkdir -p "$LOG_DIR"
exec > >(tee -a "$RUNLOG") 2>&1

# ── Profile mappings (latest 03/31 profiles) ──────────────────────────
declare -A OIDC_PROFILES=(
    [vault]="$FUZZER_DIR/src/profiles/vault_oidc_jwt_exp-1_20260330_212231.json"
    [keycloak]="$FUZZER_DIR/src/profiles/keycloak_oidc_jwt_exp-1_20260330_212955.json"
    [dex]="$FUZZER_DIR/src/profiles/dex_oidc_jwt_exp-1_20260331_011631.json"
    [casdoor]="$FUZZER_DIR/src/profiles/casdoor_oidc_jwt_exp-1_20260331_003650.json"
    [logto]="$FUZZER_DIR/src/profiles/logto_oidc_jwt_exp-1_20260331_012637.json"
    [authentik]="$FUZZER_DIR/src/profiles/authentik_oidc_jwt_exp-1_20260331_012128.json"
    [zitadel]="$FUZZER_DIR/src/profiles/zitadel_oidc_jwt_exp-1_20260331_004400.json"
)

declare -A SAML_PROFILES=(
    [vault]="$FUZZER_DIR/src/profiles/vault_saml_exp-1_20260330_212541.json"
    [keycloak]="$FUZZER_DIR/src/profiles/keycloak_saml_exp-1_20260330_213350.json"
    [dex]="$FUZZER_DIR/src/profiles/dex_saml_exp-1_20260331_011840.json"
    [casdoor]="$FUZZER_DIR/src/profiles/casdoor_saml_exp-1_20260331_004052.json"
    [logto]="$FUZZER_DIR/src/profiles/logto_saml_exp-1_20260331_012921.json"
    [authentik]="$FUZZER_DIR/src/profiles/authentik_saml_exp-1_20260331_012344.json"
    [zitadel]="$FUZZER_DIR/src/profiles/zitadel_saml_exp-1_20260331_004714.json"
)

PLATFORMS=(vault keycloak dex casdoor logto authentik zitadel)

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# =============================================================================
# Docker lifecycle helpers
# =============================================================================

# Generic teardown via platform-images.yml (all platforms except authentik)
teardown_generic() {
    local platform="$1"
    log ">>> Tearing down $platform..."
    docker compose -f "$COMPOSE_FILE" --profile "$platform" down -v --remove-orphans --timeout 10 2>&1 || true
    sleep 2
    log ">>> $platform torn down"
}

# Generic startup via platform-images.yml
startup_generic() {
    local platform="$1"
    local port="$2"
    local health_url="$3"
    local max_wait="$4"

    log ">>> Starting $platform..."
    docker compose -f "$COMPOSE_FILE" --profile "$platform" up -d 2>&1

    log ">>> Waiting for $platform on $health_url..."
    for i in $(seq 1 "$max_wait"); do
        code=$(curl -s -o /dev/null -w "%{http_code}" "$health_url" 2>/dev/null || echo "000")
        if [ "$code" = "200" ] || [ "$code" = "204" ]; then
            log ">>> $platform ready after ~$((i * 5))s"
            sleep 3
            return 0
        fi
        sleep 5
    done
    log ">>> ERROR: $platform not ready within $((max_wait * 5))s"
    docker compose -f "$COMPOSE_FILE" --profile "$platform" logs --tail 20 2>&1 || true
    return 1
}

save_docker_logs() {
    local platform="$1"
    local proto="$2"
    local logfile="$LOG_DIR/${platform}_${proto}_${TIMESTAMP}.docker.log"

    if [ "$platform" = "authentik" ]; then
        cd "$AUTHENTIK_COMPOSE_DIR"
        docker compose logs --no-color > "$logfile" 2>&1 || true
        cd "$FUZZER_DIR"
    else
        docker compose -f "$COMPOSE_FILE" --profile "$platform" logs --no-color > "$logfile" 2>&1 || true
    fi
    log "    Docker logs saved: $logfile"
}

# ── Vault ────────────────────────────────────────────────────────────
teardown_vault()  { teardown_generic vault; }
startup_vault()   { startup_generic vault 8200 "http://localhost:8200/v1/sys/health" 60; }

# ── Keycloak ─────────────────────────────────────────────────────────
teardown_keycloak() { teardown_generic keycloak; }
startup_keycloak()  { startup_generic keycloak 8080 "http://localhost:8080/realms/master/.well-known/openid-configuration" 90; }

# ── Casdoor ──────────────────────────────────────────────────────────
teardown_casdoor() { teardown_generic casdoor; }
startup_casdoor()  { startup_generic casdoor 8000 "http://localhost:8000/api/health" 60; }

# ── Logto ────────────────────────────────────────────────────────────
teardown_logto() { teardown_generic logto; }
startup_logto()  { startup_generic logto 3001 "http://localhost:3001/oidc/.well-known/openid-configuration" 90; }

# ── Zitadel ──────────────────────────────────────────────────────────
teardown_zitadel() { teardown_generic zitadel; }
startup_zitadel()  { startup_generic zitadel 8085 "http://localhost:8085/debug/ready" 60; }

# ── Dex (special: mock-idp cert sync for SAML) ──────────────────────
teardown_dex() {
    log ">>> Tearing down Dex + mock-idp..."
    docker compose -f "$COMPOSE_FILE" --profile dex down --timeout 10 2>&1 || true
    sleep 2
    log ">>> Dex torn down"
}

sync_mock_idp_cert() {
    log ">>> Syncing SAML IdP cert from mock-idp..."
    for i in $(seq 1 15); do
        if curl -sf http://localhost:9090/saml/key > /tmp/_mock_idp_key.json 2>/dev/null; then
            break
        fi
        sleep 2
    done
    if [ ! -s /tmp/_mock_idp_key.json ]; then
        log ">>> ERROR: could not fetch cert from mock-idp"
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
print('>>> Cert + key written')
"
}

startup_dex() {
    log ">>> Starting mock-idp first..."
    docker compose -f "$COMPOSE_FILE" --profile dex up -d mock-idp 2>&1
    for i in $(seq 1 30); do
        if curl -sf http://localhost:9090/health > /dev/null 2>&1; then
            log ">>> mock-idp ready after ~$((i * 2))s"
            break
        fi
        sleep 2
    done

    sync_mock_idp_cert

    log ">>> Starting Dex..."
    docker compose -f "$COMPOSE_FILE" --profile dex up -d dex 2>&1
    for i in $(seq 1 30); do
        if curl -sf http://localhost:5556/dex/healthz > /dev/null 2>&1; then
            log ">>> Dex ready after ~$((i * 2))s"
            return 0
        fi
        sleep 2
    done
    log ">>> ERROR: Dex not ready"
    docker compose -f "$COMPOSE_FILE" --profile dex logs dex 2>&1 | tail -20
    return 1
}

# ── Authentik (uses its own docker-compose) ──────────────────────────
teardown_authentik() {
    log ">>> Tearing down Authentik (full volume cleanup)..."
    cd "$AUTHENTIK_COMPOSE_DIR"
    docker compose down -v --remove-orphans --timeout 10 2>&1 || true
    sleep 2
    cd "$FUZZER_DIR"
    log ">>> Authentik torn down"
}

startup_authentik() {
    log ">>> Starting Authentik..."
    cd "$AUTHENTIK_COMPOSE_DIR"
    docker compose up -d 2>&1
    cd "$FUZZER_DIR"

    log ">>> Waiting for Authentik..."
    for i in $(seq 1 60); do
        code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/api/v3/root/config/ 2>/dev/null || echo "000")
        if [ "$code" = "200" ]; then
            log ">>> Authentik ready after ~$((i * 5))s"
            sleep 3
            return 0
        fi
        sleep 5
    done
    log ">>> ERROR: Authentik not ready within 5min"
    cd "$AUTHENTIK_COMPOSE_DIR"
    docker compose logs --tail 20 2>&1
    cd "$FUZZER_DIR"
    return 1
}

# =============================================================================
# Campaign runner
# =============================================================================
run_campaign() {
    local platform="$1"
    local proto="$2"
    local profile="$3"
    local output_dir="$4"
    local campaign_log="$LOG_DIR/${platform}_${proto}_${TIMESTAMP}.log"

    log ""
    log "  Campaign: $platform / $proto"
    log "  Profile:  $profile"
    log "  Output:   $output_dir"

    cd "$FUZZER_DIR"
    python3 -m src.stateful.campaign_runner \
        --profile "$profile" \
        --invariants I1,I2,I3,I4,I5 \
        --sequences-per-invariant 5 \
        --output-dir "$output_dir" \
        2>&1 | tee "$campaign_log"

    local exit_code=${PIPESTATUS[0]}
    log "  Campaign $platform/$proto finished (exit=$exit_code)"
    return 0
}

# =============================================================================
# Per-platform runner
# =============================================================================
run_platform() {
    local platform="$1"

    log ""
    log "============================================================"
    log "PLATFORM: $platform"
    log "============================================================"

    # ── OIDC JWT ──
    local oidc_profile="${OIDC_PROFILES[$platform]}"
    if [ -n "$oidc_profile" ] && [ -f "$oidc_profile" ]; then
        log ""
        log "--- $platform / oidc_jwt ---"
        "teardown_${platform}"
        "startup_${platform}" || { log "  FAIL: $platform startup failed for oidc_jwt"; save_docker_logs "$platform" "oidc_jwt_FAIL"; true; }
        run_campaign "$platform" "oidc_jwt" "$oidc_profile" "$RESULTS_BASE/${platform}/oidc_jwt" || true
        save_docker_logs "$platform" "oidc_jwt"
    else
        log "  SKIP: No OIDC profile for $platform"
    fi

    # ── SAML ──
    local saml_profile="${SAML_PROFILES[$platform]}"
    if [ -n "$saml_profile" ] && [ -f "$saml_profile" ]; then
        log ""
        log "--- $platform / saml ---"
        "teardown_${platform}"
        "startup_${platform}" || { log "  FAIL: $platform startup failed for saml"; save_docker_logs "$platform" "saml_FAIL"; true; }
        run_campaign "$platform" "saml" "$saml_profile" "$RESULTS_BASE/${platform}/saml" || true
        save_docker_logs "$platform" "saml"
    else
        log "  SKIP: No SAML profile for $platform"
    fi

    # Final teardown to free resources
    "teardown_${platform}"
}

# =============================================================================
# Main
# =============================================================================
log "============================================================"
log "VALENCE Experiment 1 — All Platforms"
log "============================================================"
log "Timestamp:  $TIMESTAMP"
log "Platforms:  ${PLATFORMS[*]}"
log "Invariants: I1,I2,I3,I4,I5"
log "Seq/inv:    5"
log "Results:    $RESULTS_BASE"
log "Run log:    $RUNLOG"
log ""

# Verify all profiles exist
MISSING=0
for p in "${PLATFORMS[@]}"; do
    for f in "${OIDC_PROFILES[$p]}" "${SAML_PROFILES[$p]}"; do
        if [ ! -f "$f" ]; then
            log "WARNING: Profile missing: $f"
            MISSING=$((MISSING + 1))
        fi
    done
done
if [ $MISSING -gt 0 ]; then
    log "WARNING: $MISSING profiles missing, will skip those runs"
fi

# Save this script for reproducibility
cp "$0" "$RESULTS_BASE/run_all_exp1_${TIMESTAMP}.sh" 2>/dev/null || true

# Run all platforms
TOTAL_START=$(date +%s)

for platform in "${PLATFORMS[@]}"; do
    PLAT_START=$(date +%s)
    run_platform "$platform"
    PLAT_END=$(date +%s)
    log ">>> $platform total time: $(( (PLAT_END - PLAT_START) / 60 ))m $(( (PLAT_END - PLAT_START) % 60 ))s"
done

TOTAL_END=$(date +%s)

# =============================================================================
# Summary
# =============================================================================
log ""
log "============================================================"
log "EXPERIMENT SUMMARY"
log "============================================================"
log "Total time: $(( (TOTAL_END - TOTAL_START) / 60 ))m $(( (TOTAL_END - TOTAL_START) % 60 ))s"
log ""

cd "$FUZZER_DIR"
python3 -c "
import json, glob, os

root = '${RESULTS_BASE}'
for platform in sorted(os.listdir(root)):
    pdir = os.path.join(root, platform)
    if not os.path.isdir(pdir) or platform == 'logs':
        continue
    for proto in ['oidc_jwt', 'saml']:
        proto_dir = os.path.join(pdir, proto)
        if not os.path.isdir(proto_dir):
            continue
        summaries = sorted(glob.glob(os.path.join(proto_dir, 'full', 'campaign_*', 'summary.json')))
        summaries += sorted(glob.glob(os.path.join(proto_dir, 'campaign_*', 'summary.json')))
        if not summaries:
            print(f'{platform}/{proto}: NO SUMMARY FOUND')
            continue
        try:
            with open(summaries[-1]) as f:
                d = json.load(f)
            completed = d.get('by_status', {}).get('COMPLETED', 0)
            total = d.get('total_sequences', 0)
            findings = d.get('unique_findings', 0)
            print(f'{platform}/{proto}: {completed}/{total} completed, {findings} unique findings')
        except Exception as e:
            print(f'{platform}/{proto}: ERROR parsing summary: {e}')
" 2>&1 || true

log ""
log "Results: $RESULTS_BASE/"
log "Logs:    $LOG_DIR/"
log "Done at $(date -Iseconds)"
