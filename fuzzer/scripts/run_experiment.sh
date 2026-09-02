#!/usr/bin/env bash
# =============================================================================
# VALENCE Experiment Runner — Generic for all platforms
# =============================================================================
# Uses pre-built images from docker/platform-images.yml.
# Stop + rm container = clean state. No build step needed.
#
# Usage:
#   # Single platform:
#   bash scripts/run_experiment.sh casdoor
#
#   # All platforms (overnight run):
#   tmux new-session -d -s exp 'bash scripts/run_experiment.sh all'
#
#   # Specific experiment name:
#   EXP_NAME=final-exp3 bash scripts/run_experiment.sh keycloak vault
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FUZZER_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="${FUZZER_ROOT}/docker/platform-images.yml"

# ── Config ──────────────────────────────────────────────────────────────────
export OPENAI_API_KEY="${OPENAI_API_KEY:?Set OPENAI_API_KEY}"

EXP_NAME="${EXP_NAME:-final-exp3}"
INVARIANTS="${INVARIANTS:-I1,I2,I3,I4,I5}"
SEQ_PER_INV="${SEQ_PER_INV:-5}"
MUTATION_SWEEP="${MUTATION_SWEEP:---mutation-sweep}"  # set to "" to disable
HEALTH_TIMEOUT=120

RESULTS_ROOT="${FUZZER_ROOT}/results/${EXP_NAME}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOGDIR="${RESULTS_ROOT}/logs"

# Platform → profile mapping (protocol → profile path)
# Each platform can have SAML and/or OIDC profiles
declare -A PLATFORM_PORTS=(
    [vault]=8200
    [keycloak]=8080
    [dex]=5556
    [casdoor]=8000
    [logto]=3001
    [authentik]=9000
    [zitadel]=8085
)

# ── Helpers ─────────────────────────────────────────────────────────────────
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

find_profiles() {
    local platform="$1"
    ls "${FUZZER_ROOT}/src/profiles/${platform}_"*"_exp-1_"*.json 2>/dev/null || true
}

wait_for_health() {
    local platform="$1"
    local port="${PLATFORM_PORTS[$platform]}"
    log "Waiting for ${platform} on port ${port}..."
    local elapsed=0
    while [ $elapsed -lt $HEALTH_TIMEOUT ]; do
        if docker compose -f "$COMPOSE_FILE" --profile "$platform" ps --format json 2>/dev/null | grep -q '"Health":"healthy"'; then
            log "${platform} is healthy (${elapsed}s)"
            return 0
        fi
        # Fallback: simple HTTP check
        if curl -sf -o /dev/null "http://localhost:${port}/" 2>/dev/null || \
           curl -sf -o /dev/null "http://localhost:${port}/api/health" 2>/dev/null; then
            log "${platform} responding on port ${port} (${elapsed}s)"
            return 0
        fi
        sleep 3
        elapsed=$((elapsed + 3))
    done
    log "WARNING: ${platform} did not become healthy within ${HEALTH_TIMEOUT}s"
    return 1
}

teardown_platform() {
    local platform="$1"
    log "Tearing down ${platform}..."
    docker compose -f "$COMPOSE_FILE" --profile "$platform" down -v --remove-orphans 2>/dev/null || true
    sleep 2
    log "${platform} torn down"
}

startup_platform() {
    local platform="$1"
    log "Starting ${platform}..."
    docker compose -f "$COMPOSE_FILE" --profile "$platform" up -d 2>/dev/null
    wait_for_health "$platform"
    # Extra settle time for DB init
    sleep 5
    log "${platform} ready"
}

run_campaign() {
    local platform="$1"
    local protocol="$2"
    local profile="$3"
    local output_dir="$4"
    local logfile="$5"

    log "  Campaign: ${platform}/${protocol}"
    log "  Profile:  ${profile}"
    log "  Output:   ${output_dir}"

    cd "${FUZZER_ROOT}"
    python3 -m src.stateful.campaign_runner \
        --profile "${profile}" \
        --invariants "${INVARIANTS}" \
        --sequences-per-invariant "${SEQ_PER_INV}" \
        ${MUTATION_SWEEP} \
        --output-dir "${output_dir}" \
        2>&1 | tee "${logfile}"

    log "  Campaign ${platform}/${protocol} finished (exit: ${PIPESTATUS[0]})"
}

run_platform() {
    local platform="$1"
    log ""
    log "============================================================"
    log "Platform: ${platform}"
    log "============================================================"

    local profiles
    profiles=$(find_profiles "$platform")
    if [ -z "$profiles" ]; then
        log "SKIP: No exp-1 profiles found for ${platform}"
        return
    fi

    # Collect SAML and OIDC profiles
    local saml_profile="" oidc_profile=""
    for p in $profiles; do
        if echo "$p" | grep -q "_saml_"; then
            saml_profile="$p"
        elif echo "$p" | grep -q "_oidc_jwt_"; then
            oidc_profile="$p"
        fi
    done

    # Run each protocol with fresh container
    for proto_profile in "saml:${saml_profile}" "oidc:${oidc_profile}"; do
        local proto="${proto_profile%%:*}"
        local profile="${proto_profile#*:}"

        if [ -z "$profile" ]; then
            log "  SKIP: No ${proto} profile for ${platform}"
            continue
        fi

        log ""
        log "--- ${platform}/${proto} ---"

        # Fresh container for each protocol
        teardown_platform "$platform"
        startup_platform "$platform" || { log "  FAIL: ${platform} startup failed"; continue; }

        local output="${RESULTS_ROOT}/${platform}/${proto}"
        local logfile="${LOGDIR}/${platform}_${proto}_${TIMESTAMP}.log"

        run_campaign "$platform" "$proto" "$profile" "$output" "$logfile" || true

        # Save container logs
        local container_name
        container_name=$(docker compose -f "$COMPOSE_FILE" --profile "$platform" ps -q 2>/dev/null | head -1)
        if [ -n "$container_name" ]; then
            docker logs "$container_name" > "${LOGDIR}/${platform}_${proto}_${TIMESTAMP}.docker.log" 2>&1 || true
        fi
    done

    # Final teardown
    teardown_platform "$platform"
}

# ── Main ────────────────────────────────────────────────────────────────────
PLATFORMS=("$@")
if [ ${#PLATFORMS[@]} -eq 0 ] || [ "${PLATFORMS[0]}" = "all" ]; then
    PLATFORMS=(vault keycloak dex casdoor authentik logto zitadel)
fi

log "============================================================"
log "VALENCE Experiment: ${EXP_NAME}"
log "Platforms: ${PLATFORMS[*]}"
log "Invariants: ${INVARIANTS}"
log "Sequences/invariant: ${SEQ_PER_INV}"
log "Mutation sweep: ${MUTATION_SWEEP:-disabled}"
log "Timestamp: ${TIMESTAMP}"
log "============================================================"

mkdir -p "${LOGDIR}"

# Save this script for reproducibility
cp "$0" "${RESULTS_ROOT}/run_script_${TIMESTAMP}.sh" 2>/dev/null || true

for platform in "${PLATFORMS[@]}"; do
    run_platform "$platform"
done

# ── Summary ─────────────────────────────────────────────────────────────────
log ""
log "============================================================"
log "Experiment Summary"
log "============================================================"

cd "${FUZZER_ROOT}"
python3 -c "
import json, glob, os

root = '${RESULTS_ROOT}'
for platform_dir in sorted(glob.glob(os.path.join(root, '*/'))):
    platform = os.path.basename(platform_dir.rstrip('/'))
    if platform == 'logs':
        continue
    for proto in ['saml', 'oidc']:
        summaries = sorted(glob.glob(os.path.join(platform_dir, proto, 'full', 'campaign_*', 'summary.json')))
        if not summaries:
            continue
        with open(summaries[-1]) as f:
            d = json.load(f)
        completed = d['by_status'].get('COMPLETED', 0)
        total = d['total_sequences']
        findings = d['unique_findings']
        sweep = d.get('sweep_summary', {}).get('total_sweep_findings', 0)
        print(f'{platform}/{proto}: {completed}/{total} completed, {findings} findings, {sweep} sweep violations')
" 2>&1 | tee "${LOGDIR}/summary_${TIMESTAMP}.txt"

log "Results: ${RESULTS_ROOT}"
log "Done."
