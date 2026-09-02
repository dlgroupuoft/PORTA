#!/usr/bin/env bash
set -euo pipefail

FUZZER_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

require_openssl() {
  if ! command -v openssl >/dev/null 2>&1; then
    echo "openssl is required to generate local test certificates" >&2
    exit 1
  fi
}

generate_pair() {
  local key_path=$1
  local cert_path=$2
  local subject=$3
  local san=$4

  if [ -s "$key_path" ] && [ -s "$cert_path" ]; then
    return 0
  fi

  mkdir -p "$(dirname "$key_path")" "$(dirname "$cert_path")"
  openssl req \
    -x509 \
    -newkey rsa:2048 \
    -nodes \
    -sha256 \
    -days 3650 \
    -keyout "$key_path" \
    -out "$cert_path" \
    -subj "$subject" \
    -addext "$san" \
    >/dev/null 2>&1
  chmod 600 "$key_path"
  chmod 644 "$cert_path"
}

require_openssl

generate_pair \
  "$FUZZER_ROOT/docker/dex/saml_idp_key.pem" \
  "$FUZZER_ROOT/docker/dex/saml_idp_cert.pem" \
  "/C=US/O=PORTA/CN=porta-dex-test-idp" \
  "subjectAltName=DNS:mock-idp,DNS:localhost,IP:127.0.0.1"

generate_pair \
  "$FUZZER_ROOT/Recall/Results/Keycloak/CVE-2024-8698/idp.key" \
  "$FUZZER_ROOT/Recall/Results/Keycloak/CVE-2024-8698/idp.crt" \
  "/C=US/O=PORTA/CN=porta-recall-cve-2024-8698-idp" \
  "subjectAltName=DNS:localhost,IP:127.0.0.1"

echo "Generated local test certificates where needed."
