#!/usr/bin/env bash
# =============================================================================
# VALENCE Unified Experiment Runner
# =============================================================================
# Runs campaigns for selected platforms sequentially. Each platform gets fresh
# containers (image reload) between protocol runs. No port conflicts — each
# platform uses unique ports and runs one at a time.
#
# Usage:
#   # Run all platforms
#   bash scripts/run_all_experiments.sh
#
#   # Run specific platforms
#   bash scripts/run_all_experiments.sh zitadel vault logto
#
#   # Override experiment name (controls results directory)
#   bash scripts/run_all_experiments.sh --exp-name my-exp zitadel
#
#   # Override campaign profiles
#   bash scripts/run_all_experiments.sh --profile zitadel:oidc=/path/to/p.json zitadel
#
#   # Or via environment variables
#   ZITADEL_PROFILE_OIDC=/path/to/p.json bash scripts/run_all_experiments.sh zitadel
#
#   # Dry run — print config and exit
#   bash scripts/run_all_experiments.sh --dry-run zitadel vault
#
#   # Recommended: run in tmux
#   tmux new-session -d -s exp 'bash scripts/run_all_experiments.sh'
#
# Port Reference (no conflicts — each platform uses unique ports):
#   Vault        8200
#   Keycloak     8080
#   Dex          5556, 5557
#   Casdoor      8000
#   Logto        3001, 3002
#   Authentik    9000, 9443
#   Zitadel      8085
#   Mock-idp     9090  (shared by vault, dex, logto — managed per-platform)
# =============================================================================
set -uo pipefail  # no -e: campaign failures must not abort the whole run

export OPENAI_API_KEY="${OPENAI_API_KEY:?Set OPENAI_API_KEY env var before running}"

# ════════════════════════════════════════════════════════════════════════════
# Common paths
# ════════════════════════════════════════════════════════════════════════════
BROKER_ROOT="/home/ubuntu/broker"
FUZZER_DIR="$BROKER_ROOT/fuzzer"
COMPOSE_FILE="$FUZZER_DIR/docker/platform-images.yml"
CASDOOR_COMPOSE_DIR="$BROKER_ROOT/platform/casdoor"
AUTHENTIK_COMPOSE_DIR="$FUZZER_DIR/docker/authentik"
DOCKER_DEX_DIR="$FUZZER_DIR/docker/dex"

# ════════════════════════════════════════════════════════════════════════════
# Default campaign profiles (override via --profile flag or env vars)
# ════════════════════════════════════════════════════════════════════════════
: "${ZITADEL_PROFILE_OIDC:=$FUZZER_DIR/src/profiles/zitadel_oidc_jwt_exp-1_20260331_182000.json}"
: "${ZITADEL_PROFILE_SAML:=$FUZZER_DIR/src/profiles/zitadel_saml_exp-1_20260331_182253.json}"
: "${CASDOOR_PROFILE_OIDC:=$FUZZER_DIR/src/profiles/casdoor_oidc_jwt_exp-1_20260330_015452.json}"
: "${CASDOOR_PROFILE_SAML:=$FUZZER_DIR/src/profiles/casdoor_saml_exp-1_20260330_015701.json}"
: "${DEX_PROFILE_OIDC:=$FUZZER_DIR/src/profiles/dex_oidc_jwt_exp-1_20260331_011631.json}"
: "${DEX_PROFILE_SAML:=$FUZZER_DIR/src/profiles/dex_saml_exp-1_20260331_011840.json}"
: "${KEYCLOAK_PROFILE_OIDC:=$FUZZER_DIR/src/profiles/keycloak_oidc_jwt_exp-1_20260330_212955.json}"
: "${KEYCLOAK_PROFILE_SAML:=$FUZZER_DIR/src/profiles/keycloak_saml_exp-1_20260330_213350.json}"
: "${AUTHENTIK_PROFILE_OIDC:=$FUZZER_DIR/src/profiles/authentik_oidc_jwt_exp-1_20260331_012128.json}"
: "${AUTHENTIK_PROFILE_SAML:=$FUZZER_DIR/src/profiles/authentik_saml_exp-1_20260331_012344.json}"
: "${VAULT_PROFILE_OIDC:=$FUZZER_DIR/src/profiles/vault_oidc_jwt_exp-1_20260330_212231.json}"
: "${LOGTO_PROFILE_OIDC:=$FUZZER_DIR/src/profiles/logto_oidc_jwt_exp-1_20260331_012637.json}"
: "${LOGTO_PROFILE_SAML:=$FUZZER_DIR/src/profiles/logto_saml_exp-1_20260331_012921.json}"

# ════════════════════════════════════════════════════════════════════════════
# CLI argument parsing
# ════════════════════════════════════════════════════════════════════════════
ALL_PLATFORMS=(zitadel casdoor dex keycloak authentik vault logto)
SELECTED=()
EXP_NAME="unified"
DRY_RUN=false
SEQ_OVERRIDE=""  # if set, overrides per-platform --sequences-per-invariant

while [[ $# -gt 0 ]]; do
    case "$1" in
        --exp-name)
            EXP_NAME="$2"; shift 2 ;;
        --seq-per-inv)
            SEQ_OVERRIDE="$2"; shift 2 ;;
        --dry-run)
            DRY_RUN=true; shift ;;
        --profile)
            # Format: PLATFORM:PROTOCOL=PATH
            # e.g.  --profile zitadel:oidc=/path/to/profile.json
            _spec="$2"
            _plat="${_spec%%:*}"
            _rest="${_spec#*:}"
            _proto="${_rest%%=*}"
            _path="${_rest#*=}"
            # Convert relative paths to absolute (avoid cwd dependency later)
            [[ "$_path" != /* ]] && _path="$FUZZER_DIR/$_path"
            _var="${_plat^^}_PROFILE_${_proto^^}"
            printf -v "$_var" '%s' "$_path"
            shift 2 ;;
        -h|--help)
            cat <<'USAGE'
Usage: run_all_experiments.sh [OPTIONS] [PLATFORM...]

Platforms: zitadel casdoor dex keycloak authentik vault logto
  (default: all)

Options:
  --exp-name NAME              Experiment name for results dir (default: unified)
  --seq-per-inv N              Override sequences-per-invariant for ALL platforms
  --profile PLAT:PROTO=PATH    Override campaign profile file
  --dry-run                    Print config and exit without running
  -h, --help                   Show this help

Profile override examples:
  --profile zitadel:oidc=/path/to/profile.json
  --profile authentik:saml=/path/to/profile.json

Environment variable overrides (take precedence over defaults):
  ZITADEL_PROFILE_OIDC, ZITADEL_PROFILE_SAML
  CASDOOR_PROFILE_OIDC, CASDOOR_PROFILE_SAML
  DEX_PROFILE_OIDC, DEX_PROFILE_SAML
  KEYCLOAK_PROFILE_OIDC, KEYCLOAK_PROFILE_SAML
  AUTHENTIK_PROFILE_OIDC, AUTHENTIK_PROFILE_SAML
  VAULT_PROFILE_OIDC
  LOGTO_PROFILE_OIDC, LOGTO_PROFILE_SAML
USAGE
            exit 0 ;;
        *)
            # Validate platform name
            _found=false
            for p in "${ALL_PLATFORMS[@]}"; do
                [[ "$1" == "$p" ]] && _found=true && break
            done
            if $_found; then
                SELECTED+=("$1")
            else
                echo "ERROR: Unknown platform '$1'. Valid: ${ALL_PLATFORMS[*]}" >&2
                exit 1
            fi
            shift ;;
    esac
done

# Default: all platforms
if [ ${#SELECTED[@]} -eq 0 ]; then
    SELECTED=("${ALL_PLATFORMS[@]}")
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_BASE="$FUZZER_DIR/results/${EXP_NAME}"
MASTER_LOG_DIR="$RESULTS_BASE/logs"

# ════════════════════════════════════════════════════════════════════════════
# Logging
# ════════════════════════════════════════════════════════════════════════════
mkdir -p "$MASTER_LOG_DIR"
MASTER_LOG="$MASTER_LOG_DIR/run_${TIMESTAMP}.log"
exec > >(tee -a "$MASTER_LOG") 2>&1

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# Resolve sequences-per-invariant: global override wins, else per-platform default
seq_count() {
    local default="$1"
    echo "${SEQ_OVERRIDE:-$default}"
}

# ════════════════════════════════════════════════════════════════════════════
# Dry-run: print config and exit
# ════════════════════════════════════════════════════════════════════════════
if $DRY_RUN; then
    echo "================================================================="
    echo "DRY RUN — Configuration Summary"
    echo "================================================================="
    echo ""
    echo "Experiment name: $EXP_NAME"
    echo "Results base:    $RESULTS_BASE"
    echo "Compose file:    $COMPOSE_FILE"
    echo "Timestamp:       $TIMESTAMP"
    echo ""
    echo "Selected platforms: ${SELECTED[*]}"
    echo ""
    echo "Campaign profiles:"
    for p in "${SELECTED[@]}"; do
        case "$p" in
            zitadel)
                echo "  zitadel/oidc:  $ZITADEL_PROFILE_OIDC"
                echo "  zitadel/saml:  $ZITADEL_PROFILE_SAML" ;;
            casdoor)
                echo "  casdoor/saml:  $CASDOOR_PROFILE_SAML"
                echo "  casdoor/oidc:  $CASDOOR_PROFILE_OIDC" ;;
            dex)
                echo "  dex/oidc:      $DEX_PROFILE_OIDC"
                echo "  dex/saml:      $DEX_PROFILE_SAML" ;;
            keycloak)
                echo "  keycloak/oidc: $KEYCLOAK_PROFILE_OIDC"
                echo "  keycloak/saml: $KEYCLOAK_PROFILE_SAML" ;;
            authentik)
                echo "  authentik/saml: $AUTHENTIK_PROFILE_SAML"
                echo "  authentik/oidc: $AUTHENTIK_PROFILE_OIDC" ;;
            vault)
                echo "  vault/oidc:    $VAULT_PROFILE_OIDC"
                echo "  (vault has no SAML — Enterprise only)" ;;
            logto)
                echo "  logto/oidc:    $LOGTO_PROFILE_OIDC"
                echo "  logto/saml:    $LOGTO_PROFILE_SAML" ;;
        esac
    done
    echo ""
    if [ -n "$SEQ_OVERRIDE" ]; then
        echo "Sequences-per-invariant OVERRIDE: $SEQ_OVERRIDE (applies to ALL platforms)"
    fi
    echo ""
    echo "Per-platform settings (seq = sequences-per-invariant):"
    echo "  zitadel:   seq=$(seq_count 5),  --setup-platform"
    echo "  casdoor:   seq=$(seq_count 5)"
    echo "  dex:       seq=$(seq_count 5),  --mutation-sweep"
    echo "  keycloak:  seq=$(seq_count 5)"
    echo "  authentik: seq=$(seq_count 10), --mutation-sweep"
    echo "  vault:     seq=$(seq_count 5),  --setup-platform --mutation-sweep"
    echo "  logto:     seq=$(seq_count 10), --setup-platform --mutation-sweep --sweep-priority high"
    echo ""
    echo "Port allocations (all unique, sequential execution — no conflicts):"
    echo "  Vault=8200  Keycloak=8080  Dex=5556,5557  Casdoor=8000"
    echo "  Logto=3001,3002  Authentik=9000,9443  Zitadel=8085  Mock-idp=9090"
    echo ""
    echo "Compose modes:"
    echo "  platform-images.yml (profile): zitadel, dex, keycloak, vault, logto"
    echo "  standalone compose:            casdoor ($CASDOOR_COMPOSE_DIR)"
    echo "                                 authentik ($AUTHENTIK_COMPOSE_DIR)"
    echo ""
    echo "(dry-run complete — nothing executed)"
    exit 0
fi

# ════════════════════════════════════════════════════════════════════════════
# Global mock-idp lifecycle
# ════════════════════════════════════════════════════════════════════════════
# Mock-idp is needed by ALL platforms (SAML signing, JWT minting, OIDC IdP).
# The original individual scripts assumed it was already running via the main
# fuzzer/docker/docker-compose.yml. We start it here once and keep it alive
# throughout all experiments. This also creates the docker_valence-net network
# that authentik's standalone compose depends on (via external network).
# ════════════════════════════════════════════════════════════════════════════

start_global_mock_idp() {
    log ">>> Starting global mock-idp (shared by all platforms)..."
    docker compose -f "$COMPOSE_FILE" --profile mock-idp up -d 2>&1
    wait_for_url "http://localhost:9090/health" 60 2 "mock-idp"
    log ">>> mock-idp running on :9090, docker_valence-net created"
}

stop_global_mock_idp() {
    log ">>> Stopping global mock-idp..."
    docker compose -f "$COMPOSE_FILE" --profile mock-idp stop mock-idp --timeout 10 2>&1 || true
    docker compose -f "$COMPOSE_FILE" --profile mock-idp rm -f mock-idp 2>&1 || true
}

# ════════════════════════════════════════════════════════════════════════════
# Generic helpers
# ════════════════════════════════════════════════════════════════════════════

# Wait for an HTTP endpoint to return 200
wait_for_url() {
    local url="$1" timeout="${2:-300}" interval="${3:-5}" label="${4:-service}"
    local elapsed=0
    while [ $elapsed -lt $timeout ]; do
        local code
        code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
        if [ "$code" = "200" ]; then
            log "    $label ready after ${elapsed}s"
            return 0
        fi
        sleep "$interval"
        elapsed=$((elapsed + interval))
    done
    log "    ERROR: $label not ready within ${timeout}s (last HTTP $code)"
    return 1
}

# Run a single campaign
run_campaign() {
    local platform="$1" protocol="$2" profile="$3" output_dir="$4"
    shift 4
    local extra_flags=("$@")
    local log_dir
    log_dir="$(dirname "$output_dir")/logs"

    cd "$FUZZER_DIR"

    log "    Campaign: $platform / $protocol"
    log "    Profile:  $profile"
    log "    Output:   $output_dir"
    log "    Flags:    ${extra_flags[*]:-none}"

    if [ ! -f "$profile" ]; then
        log "    ERROR: Profile file not found: $profile"
        return 1
    fi
    python3 -m src.stateful.campaign_runner \
        --profile "$profile" \
        --invariants I1,I2,I3,I4,I5 \
        "${extra_flags[@]}" \
        --output-dir "$output_dir" \
        2>&1 | tee "$log_dir/${protocol}_${TIMESTAMP}.log"

    local exit_code=${PIPESTATUS[0]}
    log "    Campaign finished (exit=$exit_code) at $(date -Iseconds)"
    return 0  # don't abort on campaign failure
}

# Print summary from campaign results
print_summary() {
    local dir="$1" label="$2"
    local summary
    summary=$(find "$dir" -name "summary.json" -type f 2>/dev/null | sort | tail -1)
    if [ -n "$summary" ]; then
        echo "--- $label ---"
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


# ════════════════════════════════════════════════════════════════════════════
#  Platform: Zitadel
#  Compose: platform-images.yml --profile zitadel
#  Ports: 8085
#  Protocols: OIDC JWT + SAML
#  Flags: --setup-platform, seq=5
# ════════════════════════════════════════════════════════════════════════════
restart_zitadel() {
    log "  [zitadel] Tearing down (preserving mock-idp)..."
    docker compose -f "$COMPOSE_FILE" --profile zitadel stop zitadel zitadel-db --timeout 10 2>&1 || true
    docker compose -f "$COMPOSE_FILE" --profile zitadel rm -f zitadel zitadel-db 2>&1 || true
    docker volume rm docker_zitadel-pat 2>/dev/null || true
    sleep 2

    log "  [zitadel] Starting fresh containers..."
    docker compose -f "$COMPOSE_FILE" --profile zitadel up -d zitadel-db zitadel 2>&1
    wait_for_url "http://localhost:8085/debug/ready" 300 5 "Zitadel"
    sleep 3

    # Read PAT from container volume
    log "  [zitadel] Reading PAT from container..."
    export VALENCE_ADMIN_TOKEN=""
    for i in $(seq 1 10); do
        docker cp docker-zitadel-1:/data/pat/zitadel-admin.pat /tmp/_zitadel_pat 2>/dev/null || true
        PAT=$(cat /tmp/_zitadel_pat 2>/dev/null || true)
        if [ -n "$PAT" ]; then
            export VALENCE_ADMIN_TOKEN="$PAT"
            log "  [zitadel] PAT obtained: ${PAT:0:20}..."
            break
        fi
        sleep 2
    done

    if [ -z "$VALENCE_ADMIN_TOKEN" ]; then
        log "  [zitadel] ERROR: Could not obtain PAT"
        return 1
    fi

    # Verify PAT works
    local verify
    verify=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $VALENCE_ADMIN_TOKEN" \
        http://localhost:8085/management/v1/orgs/me 2>/dev/null || echo "000")
    log "  [zitadel] PAT verification: HTTP $verify"
}

teardown_zitadel() {
    docker compose -f "$COMPOSE_FILE" --profile zitadel stop zitadel zitadel-db --timeout 10 2>&1 || true
    docker compose -f "$COMPOSE_FILE" --profile zitadel rm -f zitadel zitadel-db 2>&1 || true
    docker volume rm docker_zitadel-pat 2>/dev/null || true
}

run_platform_zitadel() {
    local results="$RESULTS_BASE/zitadel"
    local log_dir="$results/logs"
    mkdir -p "$log_dir"

    log "═══════════════════════════════════════════════════════════════"
    log "Platform: Zitadel [1/2: OIDC JWT, 2/2: SAML]"
    log "═══════════════════════════════════════════════════════════════"

    # ── OIDC JWT ──
    log "  [zitadel 1/2] OIDC JWT"
    restart_zitadel
    run_campaign zitadel oidc_jwt "$ZITADEL_PROFILE_OIDC" "$results/oidc_jwt" \
        --sequences-per-invariant "$(seq_count 5)" --setup-platform || true
    docker compose -f "$COMPOSE_FILE" --profile zitadel logs --no-color \
        > "$log_dir/oidc_jwt_${TIMESTAMP}.docker.log" 2>&1 || true

    # ── SAML ──
    log "  [zitadel 2/2] SAML"
    restart_zitadel
    run_campaign zitadel saml "$ZITADEL_PROFILE_SAML" "$results/saml" \
        --sequences-per-invariant "$(seq_count 5)" --setup-platform || true
    docker compose -f "$COMPOSE_FILE" --profile zitadel logs --no-color \
        > "$log_dir/saml_${TIMESTAMP}.docker.log" 2>&1 || true

    teardown_zitadel

    log "  [zitadel] Results:"
    print_summary "$results/oidc_jwt" "zitadel/oidc_jwt"
    print_summary "$results/saml" "zitadel/saml"
}


# ════════════════════════════════════════════════════════════════════════════
#  Platform: Casdoor
#  Compose: standalone — $BROKER_ROOT/platform/casdoor/docker-compose.yml
#  Ports: 8000
#  Protocols: SAML + OIDC
#  Flags: seq=5 (no sweep, no setup-platform)
# ════════════════════════════════════════════════════════════════════════════
restart_casdoor() {
    log "  [casdoor] Tearing down..."
    cd "$CASDOOR_COMPOSE_DIR"
    docker compose down -v --remove-orphans 2>/dev/null || true
    docker volume rm casdoor_mysql_data 2>/dev/null || true
    sudo rm -rf /usr/local/docker/mysql/* 2>/dev/null || true
    sleep 2

    log "  [casdoor] Loading image & starting fresh containers..."
    docker compose up -d --build 2>/dev/null
    sleep 5
    wait_for_url "http://localhost:8000/api/health" 120 2 "Casdoor"
    sleep 5
}

teardown_casdoor() {
    cd "$CASDOOR_COMPOSE_DIR"
    docker compose down -v --remove-orphans 2>/dev/null || true
}

run_platform_casdoor() {
    local results="$RESULTS_BASE/casdoor"
    local log_dir="$results/logs"
    mkdir -p "$log_dir"

    log "═══════════════════════════════════════════════════════════════"
    log "Platform: Casdoor [1/2: SAML, 2/2: OIDC]"
    log "═══════════════════════════════════════════════════════════════"

    # ── SAML ──
    log "  [casdoor 1/2] SAML"
    restart_casdoor
    run_campaign casdoor saml "$CASDOOR_PROFILE_SAML" "$results/saml" \
        --sequences-per-invariant "$(seq_count 5)" || true
    docker logs casdoor-casdoor-1 \
        > "$log_dir/casdoor_saml_${TIMESTAMP}.docker.log" 2>&1 || true

    # ── OIDC ──
    log "  [casdoor 2/2] OIDC"
    restart_casdoor
    run_campaign casdoor oidc "$CASDOOR_PROFILE_OIDC" "$results/oidc" \
        --sequences-per-invariant "$(seq_count 5)" || true
    docker logs casdoor-casdoor-1 \
        > "$log_dir/casdoor_oidc_${TIMESTAMP}.docker.log" 2>&1 || true

    teardown_casdoor

    log "  [casdoor] Results:"
    print_summary "$results/saml" "casdoor/saml"
    print_summary "$results/oidc" "casdoor/oidc"
}


# ════════════════════════════════════════════════════════════════════════════
#  Platform: Dex
#  Compose: platform-images.yml --profile dex (includes mock-idp)
#  Ports: 5556, 5557  (mock-idp: 9090)
#  Protocols: OIDC JWT + SAML
#  Flags: --mutation-sweep, seq=5
#  Special: must sync mock-idp SAML cert before starting Dex
# ════════════════════════════════════════════════════════════════════════════
sync_mock_idp_cert() {
    log "  [dex] Syncing SAML IdP cert from mock-idp..."
    for i in $(seq 1 15); do
        if curl -sf http://localhost:9090/saml/key > /tmp/_mock_idp_key.json 2>/dev/null; then
            break
        fi
        sleep 2
    done
    if [ ! -s /tmp/_mock_idp_key.json ]; then
        log "  [dex] ERROR: could not fetch cert from mock-idp /saml/key"
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
print('  [dex] Cert + key written')
"
}

restart_dex() {
    log "  [dex] Stopping dex container..."
    docker compose -f "$COMPOSE_FILE" --profile dex stop dex --timeout 10 2>&1 || true
    docker compose -f "$COMPOSE_FILE" --profile dex rm -f dex 2>&1 || true
    sleep 2

    # Restart mock-idp to regenerate fresh SAML keypair
    log "  [dex] Restarting mock-idp (fresh keypair for cert sync)..."
    docker compose -f "$COMPOSE_FILE" --profile mock-idp stop mock-idp --timeout 10 2>&1 || true
    docker compose -f "$COMPOSE_FILE" --profile mock-idp rm -f mock-idp 2>&1 || true
    docker compose -f "$COMPOSE_FILE" --profile mock-idp up -d mock-idp 2>&1
    wait_for_url "http://localhost:9090/health" 60 2 "mock-idp"

    # Sync cert BEFORE starting Dex (Dex mounts it as read-only volume)
    sync_mock_idp_cert

    # Now start Dex
    log "  [dex] Starting Dex..."
    docker compose -f "$COMPOSE_FILE" --profile dex up -d dex 2>&1
    wait_for_url "http://localhost:5556/dex/healthz" 60 2 "Dex"
    docker compose -f "$COMPOSE_FILE" --profile dex logs dex 2>&1 \
        | grep -i 'error\|connector' | tail -5 || true
}

teardown_dex() {
    docker compose -f "$COMPOSE_FILE" --profile dex stop dex --timeout 10 2>&1 || true
    docker compose -f "$COMPOSE_FILE" --profile dex rm -f dex 2>&1 || true
    # mock-idp stays running (global lifecycle)
}

run_platform_dex() {
    local results="$RESULTS_BASE/dex"
    local log_dir="$results/logs"
    mkdir -p "$log_dir"

    log "═══════════════════════════════════════════════════════════════"
    log "Platform: Dex [1/2: OIDC JWT, 2/2: SAML] (with sweep)"
    log "═══════════════════════════════════════════════════════════════"

    # ── OIDC JWT ──
    log "  [dex 1/2] OIDC JWT"
    restart_dex
    run_campaign dex oidc_jwt "$DEX_PROFILE_OIDC" "$results/oidc_jwt" \
        --sequences-per-invariant "$(seq_count 5)" --mutation-sweep || true

    # ── SAML ──
    log "  [dex 2/2] SAML"
    restart_dex
    run_campaign dex saml "$DEX_PROFILE_SAML" "$results/saml" \
        --sequences-per-invariant "$(seq_count 5)" --mutation-sweep || true

    teardown_dex

    log "  [dex] Results:"
    print_summary "$results/oidc_jwt" "dex/oidc_jwt"
    print_summary "$results/saml" "dex/saml"
}


# ════════════════════════════════════════════════════════════════════════════
#  Platform: Keycloak
#  Compose: platform-images.yml --profile keycloak
#  Ports: 8080
#  Protocols: OIDC + SAML
#  Flags: seq=5 (no sweep, no setup-platform)
# ════════════════════════════════════════════════════════════════════════════
restart_keycloak() {
    log "  [keycloak] Tearing down..."
    docker compose -f "$COMPOSE_FILE" --profile keycloak stop 2>/dev/null || true
    docker compose -f "$COMPOSE_FILE" --profile keycloak rm -f 2>/dev/null || true
    sleep 2

    log "  [keycloak] Starting fresh container..."
    docker compose -f "$COMPOSE_FILE" --profile keycloak up -d 2>&1
    wait_for_url "http://localhost:8080/realms/master/.well-known/openid-configuration" 450 5 "Keycloak"
}

teardown_keycloak() {
    docker compose -f "$COMPOSE_FILE" --profile keycloak stop 2>/dev/null || true
    docker compose -f "$COMPOSE_FILE" --profile keycloak rm -f 2>/dev/null || true
}

run_platform_keycloak() {
    local results="$RESULTS_BASE/keycloak"
    local log_dir="$results/logs"
    mkdir -p "$log_dir"

    log "═══════════════════════════════════════════════════════════════"
    log "Platform: Keycloak [1/2: OIDC, 2/2: SAML]"
    log "═══════════════════════════════════════════════════════════════"

    # ── OIDC ──
    log "  [keycloak 1/2] OIDC"
    restart_keycloak
    run_campaign keycloak oidc "$KEYCLOAK_PROFILE_OIDC" "$results/oidc" \
        --sequences-per-invariant "$(seq_count 5)" || true

    # ── SAML ──
    log "  [keycloak 2/2] SAML"
    restart_keycloak
    run_campaign keycloak saml "$KEYCLOAK_PROFILE_SAML" "$results/saml" \
        --sequences-per-invariant "$(seq_count 5)" || true

    teardown_keycloak

    log "  [keycloak] Results:"
    print_summary "$results/oidc" "keycloak/oidc"
    print_summary "$results/saml" "keycloak/saml"
}


# ════════════════════════════════════════════════════════════════════════════
#  Platform: Authentik
#  Compose: standalone — $FUZZER_DIR/docker/authentik/docker-compose.yml
#           (includes worker service not in platform-images.yml)
#  Ports: 9000, 9443
#  Protocols: SAML + OIDC JWT
#  Flags: --mutation-sweep, seq=10
#  Special: VALENCE_ADMIN_TOKEN for API access
# ════════════════════════════════════════════════════════════════════════════
restart_authentik() {
    log "  [authentik] Tearing down..."
    cd "$AUTHENTIK_COMPOSE_DIR"
    docker compose down -v --remove-orphans --timeout 10 2>&1 || true
    sleep 2

    log "  [authentik] Loading image & starting fresh containers..."
    docker compose up -d 2>&1
    wait_for_url "http://localhost:9000/api/v3/root/config/" 300 5 "Authentik"
}

teardown_authentik() {
    cd "$AUTHENTIK_COMPOSE_DIR"
    docker compose down -v --remove-orphans --timeout 10 2>&1 || true
}

run_platform_authentik() {
    local results="$RESULTS_BASE/authentik"
    local log_dir="$results/logs"
    mkdir -p "$log_dir"

    export VALENCE_ADMIN_TOKEN='fuzzer-authentik-bootstrap-api-token'

    log "═══════════════════════════════════════════════════════════════"
    log "Platform: Authentik [1/2: SAML, 2/2: OIDC JWT] (with sweep)"
    log "═══════════════════════════════════════════════════════════════"

    # ── SAML ──
    log "  [authentik 1/2] SAML"
    restart_authentik
    run_campaign authentik saml "$AUTHENTIK_PROFILE_SAML" "$results/saml" \
        --sequences-per-invariant "$(seq_count 10)" --mutation-sweep || true

    # ── OIDC JWT ──
    log "  [authentik 2/2] OIDC JWT"
    restart_authentik
    run_campaign authentik oidc_jwt "$AUTHENTIK_PROFILE_OIDC" "$results/oidc_jwt" \
        --sequences-per-invariant "$(seq_count 10)" --mutation-sweep || true

    teardown_authentik

    log "  [authentik] Results:"
    print_summary "$results/saml" "authentik/saml"
    print_summary "$results/oidc_jwt" "authentik/oidc_jwt"
}


# ════════════════════════════════════════════════════════════════════════════
#  Platform: Vault
#  Compose: platform-images.yml --profile vault (includes mock-idp)
#  Ports: 8200  (mock-idp: 9090)
#  Protocols: OIDC JWT only (SAML requires Enterprise)
#  Flags: --setup-platform --mutation-sweep, seq=5
#  Special: dev mode = in-memory, stop+rm+up = fully clean state
# ════════════════════════════════════════════════════════════════════════════
restart_vault() {
    log "  [vault] Stopping vault container..."
    docker compose -f "$COMPOSE_FILE" --profile vault stop vault --timeout 10 2>&1 || true
    docker compose -f "$COMPOSE_FILE" --profile vault rm -f vault 2>&1 || true
    sleep 2

    # Start fresh vault (mock-idp already running globally)
    log "  [vault] Starting fresh Vault container..."
    docker compose -f "$COMPOSE_FILE" --profile vault up -d vault 2>&1
    wait_for_url "http://localhost:8200/v1/sys/health" 60 2 "Vault"
}

teardown_vault() {
    docker compose -f "$COMPOSE_FILE" --profile vault stop vault --timeout 10 2>&1 || true
    docker compose -f "$COMPOSE_FILE" --profile vault rm -f vault 2>&1 || true
    # mock-idp stays running (global lifecycle)
}

run_platform_vault() {
    local results="$RESULTS_BASE/vault"
    local log_dir="$results/logs"
    mkdir -p "$log_dir"

    log "═══════════════════════════════════════════════════════════════"
    log "Platform: Vault [1/1: OIDC JWT] (with sweep + setup-platform)"
    log "  Note: SAML skipped — not available in Vault OSS (Enterprise only)"
    log "═══════════════════════════════════════════════════════════════"

    # ── OIDC JWT ──
    log "  [vault 1/1] OIDC JWT"
    restart_vault
    run_campaign vault oidc_jwt "$VAULT_PROFILE_OIDC" "$results/oidc_jwt" \
        --sequences-per-invariant "$(seq_count 5)" --mutation-sweep --setup-platform || true
    docker compose -f "$COMPOSE_FILE" --profile vault logs vault \
        > "$log_dir/vault_oidc_${TIMESTAMP}.docker.log" 2>&1 || true

    teardown_vault

    log "  [vault] Results:"
    print_summary "$results/oidc_jwt" "vault/oidc_jwt"
}


# ════════════════════════════════════════════════════════════════════════════
#  Platform: Logto
#  Compose: platform-images.yml --profile logto (includes mock-idp)
#  Ports: 3001, 3002  (mock-idp: 9090)
#  Protocols: OIDC JWT + SAML
#  Flags: --setup-platform --mutation-sweep --sweep-priority high, seq=10
# ════════════════════════════════════════════════════════════════════════════
restart_logto() {
    log "  [logto] Stopping Logto containers (preserving mock-idp)..."
    docker compose -f "$COMPOSE_FILE" --profile logto stop logto logto-db --timeout 10 2>&1 || true
    docker compose -f "$COMPOSE_FILE" --profile logto rm -f logto logto-db 2>&1 || true
    sleep 2

    log "  [logto] Starting fresh Logto + DB..."
    docker compose -f "$COMPOSE_FILE" --profile logto up -d logto-db logto 2>&1
    wait_for_url "http://localhost:3001/oidc/.well-known/openid-configuration" 270 3 "Logto"
    # Extra settle time: Logto needs DB migrations + session store init
    sleep 8
}

teardown_logto() {
    docker compose -f "$COMPOSE_FILE" --profile logto stop logto logto-db --timeout 10 2>&1 || true
    docker compose -f "$COMPOSE_FILE" --profile logto rm -f logto logto-db 2>&1 || true
    # mock-idp stays running (global lifecycle)
}

run_platform_logto() {
    local results="$RESULTS_BASE/logto"
    local log_dir="$results/logs"
    mkdir -p "$log_dir"

    log "═══════════════════════════════════════════════════════════════"
    log "Platform: Logto [1/2: OIDC JWT, 2/2: SAML] (sweep + setup)"
    log "═══════════════════════════════════════════════════════════════"

    # ── OIDC JWT ──
    log "  [logto 1/2] OIDC JWT"
    restart_logto
    run_campaign logto oidc_jwt "$LOGTO_PROFILE_OIDC" "$results/oidc_jwt" \
        --sequences-per-invariant "$(seq_count 10)" --setup-platform \
        --mutation-sweep --sweep-priority high || true

    # ── SAML ──
    log "  [logto 2/2] SAML"
    restart_logto
    run_campaign logto saml "$LOGTO_PROFILE_SAML" "$results/saml" \
        --sequences-per-invariant "$(seq_count 10)" --setup-platform \
        --mutation-sweep --sweep-priority high || true

    teardown_logto

    log "  [logto] Results:"
    print_summary "$results/oidc_jwt" "logto/oidc_jwt"
    print_summary "$results/saml" "logto/saml"
}


# ════════════════════════════════════════════════════════════════════════════
# Main execution
# ════════════════════════════════════════════════════════════════════════════
log "================================================================="
log "VALENCE Unified Experiment Runner — started at $(date -Iseconds)"
log "================================================================="
log "Experiment:  $EXP_NAME"
log "Results:     $RESULTS_BASE"
log "Platforms:   ${SELECTED[*]}"
log "Timestamp:   $TIMESTAMP"
log ""

# Save this script for reproducibility
cp "$0" "$RESULTS_BASE/run_script_${TIMESTAMP}.sh" 2>/dev/null || true

# ── Start global mock-idp (needed by all platforms) ─────────────────────
start_global_mock_idp

PLATFORM_IDX=0
PLATFORM_TOTAL=${#SELECTED[@]}
FAILED_PLATFORMS=()

for platform in "${SELECTED[@]}"; do
    PLATFORM_IDX=$((PLATFORM_IDX + 1))

    # Reset VALENCE_ADMIN_TOKEN to prevent cross-platform contamination.
    # Each platform that needs it (zitadel, authentik) sets it in its own run function.
    unset VALENCE_ADMIN_TOKEN 2>/dev/null || true

    log ""
    log "╔═══════════════════════════════════════════════════════════════╗"
    log "║  Platform $PLATFORM_IDX/$PLATFORM_TOTAL: $platform"
    log "╚═══════════════════════════════════════════════════════════════╝"

    if ! run_platform_"$platform"; then
        log "  WARNING: $platform had errors (continuing with next platform)"
        FAILED_PLATFORMS+=("$platform")
    fi
done

# ── Stop global mock-idp ────────────────────────────────────────────────
stop_global_mock_idp

# ════════════════════════════════════════════════════════════════════════════
# Final summary
# ════════════════════════════════════════════════════════════════════════════
log ""
log "================================================================="
log "All experiments complete at $(date -Iseconds)"
log "================================================================="
log ""
log "Results directory: $RESULTS_BASE/"
log "Master log:        $MASTER_LOG"
log ""

if [ ${#FAILED_PLATFORMS[@]} -gt 0 ]; then
    log "Platforms with errors: ${FAILED_PLATFORMS[*]}"
    log ""
fi

# Print all summaries
for platform in "${SELECTED[@]}"; do
    results="$RESULTS_BASE/$platform"
    case "$platform" in
        vault)
            print_summary "$results/oidc_jwt" "$platform/oidc_jwt" ;;
        casdoor)
            print_summary "$results/saml" "$platform/saml"
            print_summary "$results/oidc" "$platform/oidc" ;;
        keycloak)
            print_summary "$results/oidc" "$platform/oidc"
            print_summary "$results/saml" "$platform/saml" ;;
        *)
            print_summary "$results/oidc_jwt" "$platform/oidc_jwt"
            print_summary "$results/saml" "$platform/saml" ;;
    esac
done

log "Done."
