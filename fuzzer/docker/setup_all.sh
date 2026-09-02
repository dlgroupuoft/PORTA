#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMEOUT=120

echo "============================================"
echo "  VALENCE — Starting all platform services"
echo "============================================"

cd "${SCRIPT_DIR}"
docker compose up -d

echo "[*] Waiting for services to become healthy (timeout=${TIMEOUT}s)..."

wait_for() {
  local name=$1 url=$2
  local start=$SECONDS
  while (( SECONDS - start < TIMEOUT )); do
    if curl -sf "${url}" > /dev/null 2>&1; then
      echo "[+] ${name} is ready"
      return 0
    fi
    sleep 2
  done
  echo "[-] ${name} failed health check at ${url}"
  return 1
}

wait_for "Vault"    "http://localhost:8200/v1/sys/health"
wait_for "Keycloak" "http://localhost:8080/health/ready"
wait_for "Dex"      "http://localhost:5556/healthz"
wait_for "Mock IdP" "http://localhost:9090/health"

echo ""
echo "[*] Running platform setup scripts..."

bash "${SCRIPT_DIR}/vault/setup.sh"
bash "${SCRIPT_DIR}/keycloak/setup.sh"
bash "${SCRIPT_DIR}/dex/setup.sh"

echo ""
echo "============================================"
echo "  All services ready"
echo "============================================"
echo "  Vault:    http://localhost:8200"
echo "  Keycloak: http://localhost:8080"
echo "  Dex:      http://localhost:5556"
echo "  OpenLDAP: ldap://localhost:389"
echo "  Mock IdP: http://localhost:9090"
echo "============================================"
