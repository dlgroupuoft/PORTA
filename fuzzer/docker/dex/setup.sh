#!/usr/bin/env bash
set -euo pipefail

DEX_URL="${DEX_URL:-http://localhost:5556}"

echo "[*] Verifying Dex at ${DEX_URL}"

# Check health
if curl -sf "${DEX_URL}/healthz" > /dev/null 2>&1; then
  echo "[+] Dex is healthy"
else
  echo "[-] Dex health check failed"
  exit 1
fi

# Verify OIDC discovery
curl -sf "${DEX_URL}/dex/.well-known/openid-configuration" > /dev/null 2>&1 && \
  echo "[+] OIDC discovery endpoint accessible" || \
  echo "[!] OIDC discovery not available yet"

echo "[+] Dex setup complete"
