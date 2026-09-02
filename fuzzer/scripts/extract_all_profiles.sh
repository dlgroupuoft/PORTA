#!/usr/bin/env bash
# =============================================================================
# Extract + Validate profiles for all platforms
#
# Usage:
#   bash scripts/extract_all_profiles.sh                  # extract only (no platform needed)
#   bash scripts/extract_all_profiles.sh --validate       # extract + validate (platforms must be running)
#   bash scripts/extract_all_profiles.sh --platform vault  # single platform
#   bash scripts/extract_all_profiles.sh --validate --start # auto-start platforms, extract, validate, stop
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FUZZER_DIR="$(dirname "$SCRIPT_DIR")"
cd "$FUZZER_DIR"

# --- Configuration ---
OPENAI_API_KEY="${OPENAI_API_KEY:-}"
ALL_PLATFORMS="vault keycloak dex casdoor authentik logto zitadel"
PROTOCOLS="oidc_jwt saml"
VALIDATE=""
START=""
SINGLE_PLATFORM=""
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOGFILE="results/extraction_${TIMESTAMP}.log"

mkdir -p results

# --- Parse args ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --validate) VALIDATE="--validate"; shift ;;
        --start) START="yes"; shift ;;
        --platform) SINGLE_PLATFORM="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

if [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: OPENAI_API_KEY not set"
    exit 1
fi

# When --start is used, always validate (catch version-specific field issues)
if [ -n "$START" ] && [ -z "$VALIDATE" ]; then
    VALIDATE="--validate"
fi

PLATFORMS="${SINGLE_PLATFORM:-$ALL_PLATFORMS}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOGFILE"; }

# --- Platform docker helpers ---
# Use existing docker-compose files for each platform
COMPOSE_CORE="docker/docker-compose.yml"

platform_compose() {
    local p="$1"
    case "$p" in
        vault|keycloak|dex) echo "-f $COMPOSE_CORE" ;;
        casdoor) echo "-f ../platform/casdoor/docker-compose.yml" ;;
        logto) echo "-f ../platform/logto/docker-compose.yml" ;;
        zitadel) echo "-f ../platform/zitadel/deploy/compose/docker-compose.yml" ;;
        authentik) echo "-f docker/authentik/docker-compose.yml" ;;
    esac
}

platform_services() {
    # Which services to start for each platform
    local p="$1"
    case "$p" in
        vault) echo "vault mock-idp" ;;
        keycloak) echo "keycloak" ;;
        dex) echo "dex mock-idp" ;;
        casdoor) echo "" ;;  # compose starts all services
        logto) echo "" ;;
        zitadel) echo "" ;;
        authentik) echo "" ;;
    esac
}

platform_health_url() {
    local p="$1"
    case "$p" in
        vault) echo "http://localhost:8200/v1/sys/health" ;;
        keycloak) echo "http://localhost:8080/realms/master/.well-known/openid-configuration" ;;
        dex) echo "http://localhost:5556/dex/healthz" ;;
        casdoor) echo "http://localhost:8000/api/health" ;;
        logto) echo "http://localhost:3001/oidc/.well-known/openid-configuration" ;;
        zitadel) echo "http://localhost:8085/debug/healthz" ;;
        authentik) echo "http://localhost:9000/api/v3/root/config/" ;;
    esac
}

wait_for_platform() {
    local platform="$1"
    local url
    url=$(platform_health_url "$platform")
    [ -z "$url" ] && return 0
    log "  Waiting for $platform..."
    for i in $(seq 1 90); do
        if curl -sf "$url" >/dev/null 2>&1; then
            log "  $platform ready (${i}×5s)"
            return 0
        fi
        sleep 5
    done
    log "  WARNING: $platform not ready after 7.5 min"
    return 1
}

start_platform() {
    local platform="$1"
    local compose services
    compose=$(platform_compose "$platform")
    services=$(platform_services "$platform")
    [ -z "$compose" ] && return 0
    log "  Starting $platform (from image)..."
    docker compose $compose up -d $services 2>&1 | tail -5
    wait_for_platform "$platform"

    # Platform-specific post-start: read auto-generated tokens
    if [ "$platform" = "zitadel" ]; then
        log "  Reading Zitadel admin PAT..."
        sleep 5  # Give time for PAT file to be written
        local container
        container=$(docker compose $compose ps -q zitadel 2>/dev/null)
        if [ -n "$container" ]; then
            local pat
            pat=$(docker exec "$container" cat /tmp/zitadel-admin.pat 2>/dev/null || true)
            if [ -n "$pat" ]; then
                export VALENCE_ADMIN_TOKEN="$pat"
                log "  Zitadel PAT acquired (${#pat} chars)"
            else
                log "  WARNING: Could not read Zitadel PAT"
            fi
        fi
    fi
}

stop_platform() {
    local platform="$1"
    local compose
    compose=$(platform_compose "$platform")
    [ -z "$compose" ] && return 0
    log "  Stopping $platform..."
    docker compose $compose down --remove-orphans 2>/dev/null || true
}

# --- Main ---
log "=== Profile Extraction Pipeline ==="
log "Platforms: $PLATFORMS"
log "Validate: ${VALIDATE:-no}"
log "Auto-start: ${START:-no}"

total=0
passed=0

for platform in $PLATFORMS; do
    log ""
    log "======== $platform ========"

    # Start platform if requested
    if [ -n "$START" ] && [ -n "$VALIDATE" ]; then
        start_platform "$platform"
    fi

    for proto in $PROTOCOLS; do
        log "--- $platform/$proto ---"
        total=$((total + 1))

        OPENAI_API_KEY="$OPENAI_API_KEY" python3 -m src.extraction.run_pipeline \
            --platform "$platform" \
            --protocol "$proto" \
            --no-merge \
            $VALIDATE \
            2>&1 | tee -a "$LOGFILE" | grep -E "(Merged|Operations|Pipeline complete|Fixed|validated)"

        # Quality check
        latest=$(ls -t src/profiles/${platform}_${proto}_exp-1_*.json 2>/dev/null | head -1)
        if [ -n "$latest" ]; then
            score=$(python3 -c "
from src.extraction.quality_report import check_profile
r = check_profile('$latest')
print(r['score'])
" 2>/dev/null || echo "0")
            grade=$(python3 -c "
s=$score
print('A' if s>=90 else 'B' if s>=75 else 'C' if s>=60 else 'F')
")
            log "  Quality: $grade ($score/100) — $latest"
            if [ "$score" -ge 75 ]; then
                passed=$((passed + 1))
            fi
        else
            log "  WARNING: No profile generated"
        fi
    done

    # Stop platform if we started it
    if [ -n "$START" ] && [ -n "$VALIDATE" ]; then
        stop_platform "$platform"
    fi
done

log ""
log "=== Summary: $passed/$total profiles passed (score >= 75) ==="
log "Log: $LOGFILE"
