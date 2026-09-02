#!/usr/bin/env bash
set -uo pipefail
export PATH=/usr/bin:/usr/local/bin:/usr/sbin:/sbin:$PATH
FUZZER_DIR="/home/ubuntu/broker/fuzzer"
cd "$FUZZER_DIR"

export OPENAI_API_KEY="${OPENAI_API_KEY:?Set OPENAI_API_KEY env var before running}"

echo "=== Rerunning 2 missing campaigns ==="

# 1. logto/oidc_jwt exp1
echo "[1/2] logto/oidc_jwt exp1"
docker compose -f docker/platform-images.yml --profile mock-idp up -d 2>&1 | tail -1
docker compose -f docker/platform-images.yml --profile logto up -d 2>&1 | tail -1
for i in $(seq 1 90); do
    [ "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3001/oidc/.well-known/openid-configuration 2>/dev/null)" = "200" ] && echo "Logto ready" && break
    sleep 3
done
sleep 8

python3 -m src.stateful.campaign_runner \
    --profile src/profiles/logto_oidc_jwt_evaluation-exp1_20260403_005614.json \
    --invariants I1,I2,I3,I4,I5 \
    --sequences-per-invariant 10 \
    --setup-platform \
    --mutation-sweep \
    --sweep-priority high \
    --output-dir results/evaluation/exp1/logto/oidc_jwt \
    2>&1 | tail -5

docker compose -f docker/platform-images.yml --profile logto stop logto logto-db --timeout 10 2>&1 | tail -1
docker compose -f docker/platform-images.yml --profile logto rm -f logto logto-db 2>&1 | tail -1

echo "[1/2] DONE"

# 2. casdoor/oidc exp2
echo "[2/2] casdoor/oidc exp2"
cd /home/ubuntu/broker/platform/casdoor
docker compose down -v --remove-orphans 2>/dev/null
docker compose up -d --build 2>/dev/null
cd "$FUZZER_DIR"
for i in $(seq 1 60); do
    [ "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/health 2>/dev/null)" = "200" ] && echo "Casdoor ready" && break
    sleep 2
done
sleep 5

python3 -m src.stateful.campaign_runner \
    --profile src/profiles/casdoor_oidc_jwt_evaluation-exp2_20260403_015717.json \
    --invariants I1,I2,I3,I4,I5 \
    --sequences-per-invariant 10 \
    --output-dir results/evaluation/exp2/casdoor/oidc \
    2>&1 | tail -5

cd /home/ubuntu/broker/platform/casdoor && docker compose down -v --remove-orphans 2>/dev/null
cd "$FUZZER_DIR"

echo "[2/2] DONE"

# Cleanup
docker compose -f docker/platform-images.yml --profile mock-idp down --timeout 10 2>&1 | tail -1
echo "=== All reruns complete ==="
