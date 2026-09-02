#!/usr/bin/env bash
set -euo pipefail

KC_URL="${KC_URL:-http://localhost:8080}"
ADMIN_USER="${ADMIN_USER:-admin}"
ADMIN_PASS="${ADMIN_PASS:-admin}"

echo "[*] Configuring Keycloak at ${KC_URL}"

# Get admin token
TOKEN=$(curl -s -X POST "${KC_URL}/realms/master/protocol/openid-connect/token" \
  -d "grant_type=password&client_id=admin-cli&username=${ADMIN_USER}&password=${ADMIN_PASS}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Create test realm
curl -s -X POST "${KC_URL}/admin/realms" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"realm":"valence-test","enabled":true}' || true

# Create OIDC client in test realm
curl -s -X POST "${KC_URL}/admin/realms/valence-test/clients" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId":"valence-client",
    "enabled":true,
    "protocol":"openid-connect",
    "publicClient":false,
    "secret":"valence-secret",
    "redirectUris":["http://localhost:9090/callback","*"],
    "directAccessGrantsEnabled":true
  }' || true

echo "[+] Keycloak setup complete"
