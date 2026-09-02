#!/usr/bin/env bash
set -euo pipefail

VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
VAULT_TOKEN="${VAULT_TOKEN:-root}"

echo "[*] Configuring Vault at ${VAULT_ADDR}"

# Enable JWT auth
curl -s -X POST "${VAULT_ADDR}/v1/sys/auth/jwt" \
  -H "X-Vault-Token: ${VAULT_TOKEN}" \
  -d '{"type":"jwt"}' || true

# Configure JWT auth with mock IdP
# Note: service name is "mock-idp" in docker compose (valence-net network)
curl -s -X POST "${VAULT_ADDR}/v1/auth/jwt/config" \
  -H "X-Vault-Token: ${VAULT_TOKEN}" \
  -d "{\"jwks_url\":\"http://mock-idp:9090/keys\",\"bound_issuer\":\"http://mock-idp:9090\"}"

# Create test role
curl -s -X POST "${VAULT_ADDR}/v1/auth/jwt/role/test-role" \
  -H "X-Vault-Token: ${VAULT_TOKEN}" \
  -d '{"role_type":"jwt","bound_audiences":["test"],"user_claim":"sub","token_policies":["default"],"token_ttl":"1h"}'

# Create test policy
curl -s -X PUT "${VAULT_ADDR}/v1/sys/policies/acl/test-policy" \
  -H "X-Vault-Token: ${VAULT_TOKEN}" \
  -d '{"policy":"path \"secret/*\" { capabilities = [\"read\",\"list\"] }"}'

echo "[+] Vault setup complete"
