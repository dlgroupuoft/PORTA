#!/bin/bash
# Keycloak VALENCE Campaign Runner
# Runs OIDC JWT and SAML campaigns against Keycloak, with resource cleanup.
#
# Prerequisites:
#   - Keycloak running on http://localhost:8080 (docker: valence-keycloak)
#   - OPENAI_API_KEY set in environment or ~/.bashrc
#   - Python dependencies installed (pip install -r requirements.txt)
#
# Usage:
#   bash scripts/run_keycloak_campaign.sh [oidc|saml|both] [seq_per_invariant]
#
# Examples:
#   bash scripts/run_keycloak_campaign.sh both 2    # 10 seq each (default)
#   bash scripts/run_keycloak_campaign.sh oidc 4    # 20 OIDC sequences only

set -euo pipefail
cd "$(dirname "$0")/.."

MODE="${1:-both}"
SEQ_PER_INV="${2:-2}"

# Load API key
if [ -z "${OPENAI_API_KEY:-}" ]; then
    source ~/.bashrc 2>/dev/null || true
fi
if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "ERROR: OPENAI_API_KEY not set"
    exit 1
fi

KC_URL="http://localhost:8080"
OIDC_PROFILE="src/profiles/keycloak_oidc_jwt_extracted_20260325_163713.json"
SAML_PROFILE="src/profiles/keycloak_saml_extracted_20260325_163711.json"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# ── Verify Keycloak is running ──
echo "[pre-flight] Checking Keycloak at $KC_URL..."
if ! curl -sf -o /dev/null "$KC_URL/realms/master"; then
    echo "ERROR: Keycloak not responding at $KC_URL"
    echo "Start it with: docker start valence-keycloak"
    exit 1
fi
echo "[pre-flight] Keycloak OK"

# ── Obtain admin token ──
get_admin_token() {
    curl -sf -X POST "$KC_URL/realms/master/protocol/openid-connect/token" \
        -d "grant_type=client_credentials&client_id=admin-cli&client_secret=admin" 2>/dev/null \
    | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])" 2>/dev/null \
    || curl -sf -X POST "$KC_URL/realms/master/protocol/openid-connect/token" \
        -d "grant_type=password&client_id=admin-cli&username=admin&password=admin" 2>/dev/null \
    | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])" 2>/dev/null
}

# ── Cleanup test realms ──
cleanup_keycloak() {
    echo "[cleanup] Removing test realms..."
    TOKEN=$(get_admin_token)
    if [ -z "$TOKEN" ]; then
        echo "[cleanup] WARNING: Could not get admin token, skipping cleanup"
        return
    fi
    REALMS=$(curl -sf -H "Authorization: Bearer $TOKEN" "$KC_URL/admin/realms" \
        | python3 -c "import json,sys; [print(r['realm']) for r in json.load(sys.stdin) if r['realm'] != 'master']" 2>/dev/null)
    for realm in $REALMS; do
        echo "  Deleting realm: $realm"
        curl -sf -X DELETE -H "Authorization: Bearer $TOKEN" "$KC_URL/admin/realms/$realm" || true
    done
    echo "[cleanup] Done"
}

# ── Run campaign ──
run_campaign() {
    local PROFILE="$1"
    local TAG="$2"
    local LOG="results/kc_${TAG}/campaign_${TIMESTAMP}.log"

    mkdir -p "results/kc_${TAG}"

    echo ""
    echo "========================================"
    echo "  Campaign: $TAG"
    echo "  Profile:  $PROFILE"
    echo "  Seqs:     $((SEQ_PER_INV * 5)) (${SEQ_PER_INV}/invariant)"
    echo "========================================"

    cleanup_keycloak

    python3 -m src.stateful.campaign_runner \
        --profile "$PROFILE" \
        --invariants I1,I2,I3,I4,I5 \
        --sequences-per-invariant "$SEQ_PER_INV" \
        --output-dir "results/kc_${TAG}" \
        2>&1 | tee "$LOG"

    echo ""
    echo "[$TAG] Results:"
    grep -E "Sequences executed|Completed|Login failed|Unique findings" "$LOG" 2>/dev/null
    echo ""
}

# ── Main ──
echo "VALENCE Keycloak Campaign — $(date)"
echo "Mode: $MODE, Sequences per invariant: $SEQ_PER_INV"

if [ "$MODE" = "oidc" ] || [ "$MODE" = "both" ]; then
    run_campaign "$OIDC_PROFILE" "oidc"
fi

if [ "$MODE" = "saml" ] || [ "$MODE" = "both" ]; then
    run_campaign "$SAML_PROFILE" "saml"
fi

# Final cleanup
cleanup_keycloak

echo ""
echo "=== ALL CAMPAIGNS COMPLETE ==="
