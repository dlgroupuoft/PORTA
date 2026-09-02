#!/usr/bin/env bash
set -euo pipefail

FUZZER_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
cd "$FUZZER_ROOT"

OUTPUT_DIR=Recall/Results/images
IMAGES=(
  porta-recall-keycloak-cve-2018-14637-vuln:4.5.0.Final-src
  porta-recall-keycloak-cve-2018-14637-fixed:4.6.0.Final-src
  porta-recall-keycloak-cve-2022-1245-vuln:17.0.1-src
  porta-recall-keycloak-cve-2022-1245-fixed:18.0.0-src
  porta-recall-keycloak-cve-2023-0264-vuln:21.0.0-src
  porta-recall-keycloak-cve-2023-0264-fixed:21.0.1-src
  porta-recall-keycloak-cve-2023-0264-browser-adapter:local
  porta-recall-keycloak-cve-2023-2585-vuln:21.1.1-src
  porta-recall-keycloak-cve-2023-2585-fixed:21.1.2-src
  porta-recall-keycloak-cve-2023-6291-vuln:22.0.5-src
  porta-recall-keycloak-cve-2023-6291-fixed:22.0.10-src
  porta-recall-keycloak-cve-2024-8698-vuln:24.0.5-src
  porta-recall-keycloak-cve-2024-8698-fixed:25.0.6-src
  porta-recall-keycloak-cve-2023-6544-vuln:22.0.9-src
  porta-recall-keycloak-cve-2023-6544-fixed:22.0.10-src
  porta-recall-keycloak-cve-2025-1391-vuln:26.0.9-src
  porta-recall-keycloak-cve-2025-1391-fixed:26.0.10-src
  porta-recall-keycloak-browser-adapter:local
  porta-recall-keycloak-cve-2023-2422-vuln:21.1.1-src
  porta-recall-keycloak-cve-2023-2422-fixed:21.1.2-src
  porta-recall-keycloak-cve-2023-2422-certs:latest
  porta-recall-keycloak-cve-2023-2422-mtls-gateway:latest
  porta-recall-vault-cve-2024-5798-vuln:v1.15.6-src
  porta-recall-vault-cve-2024-5798-fixed:v1.17.0-src
  porta-recall-vault-cve-2025-3879-vuln:v0.20.1-src
  porta-recall-vault-cve-2025-3879-fixed:v0.21.0-src
  porta-recall-vault-cve-2025-3879-azure-mock:local
)

mkdir -p "$OUTPUT_DIR"

docker save "${IMAGES[@]}" \
  | gzip -1 > "$OUTPUT_DIR/qualified-cve-source-images.tar.gz"

sha256sum "$OUTPUT_DIR/qualified-cve-source-images.tar.gz" \
  > "$OUTPUT_DIR/qualified-cve-source-images.tar.gz.sha256"

for image in "${IMAGES[@]}"; do
  docker image inspect --format "$image {{.Id}} {{.Size}}" "$image"
done > "$OUTPUT_DIR/qualified-cve-source-images.manifest"
