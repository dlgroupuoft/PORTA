#!/bin/bash
set -e

cd /home/ubuntu/broker/fuzzer

export OPENAI_API_KEY="${OPENAI_API_KEY:?Set OPENAI_API_KEY env var before running}"
export VALENCE_LLM_MODEL="gpt-5.2-2025-12-11"
ROUND=1

echo "=========================================="
echo "Keycloak remaining experiments — $(date)"
echo "=========================================="

# ─── E3: Keycloak SAML (full) ───
echo "=== E3: Keycloak SAML (full) ==="
docker compose -f docker/docker-compose.yml restart keycloak
sleep 40
python3 -m src.stateful.campaign_runner \
  --platform keycloak \
  --protocol saml \
  --eval-mode full \
  --invariants I1,I2,I3,I4,I5 \
  --sequences-per-invariant 6 \
  --setup-platform \
  --output-dir results/round${ROUND}/E3_keycloak_saml \
  2>&1 | tee results/round${ROUND}/E3_keycloak_saml.log
echo "E3 done at $(date)"

# ─── Ablation: Keycloak OIDC blind ───
echo "=== Ablation: Keycloak OIDC blind ==="
docker compose -f docker/docker-compose.yml restart keycloak
sleep 40
python3 -m src.stateful.campaign_runner \
  --platform keycloak \
  --protocol oidc_jwt \
  --eval-mode blind \
  --invariants I1,I2,I3,I4,I5 \
  --sequences-per-invariant 6 \
  --setup-platform \
  --output-dir results/round${ROUND}/ablation_keycloak_oidc_blind \
  2>&1 | tee results/round${ROUND}/ablation_keycloak_oidc_blind.log
echo "Ablation blind done at $(date)"

# ─── Ablation: Keycloak OIDC no_examples ───
echo "=== Ablation: Keycloak OIDC no_examples ==="
docker compose -f docker/docker-compose.yml restart keycloak
sleep 40
python3 -m src.stateful.campaign_runner \
  --platform keycloak \
  --protocol oidc_jwt \
  --eval-mode no_examples \
  --invariants I1,I2,I3,I4,I5 \
  --sequences-per-invariant 6 \
  --setup-platform \
  --output-dir results/round${ROUND}/ablation_keycloak_oidc_no_examples \
  2>&1 | tee results/round${ROUND}/ablation_keycloak_oidc_no_examples.log
echo "Ablation no_examples done at $(date)"

# ─── Ablation: Keycloak OIDC oracle_gen ───
echo "=== Ablation: Keycloak OIDC oracle_gen ==="
docker compose -f docker/docker-compose.yml restart keycloak
sleep 40
python3 -m src.stateful.campaign_runner \
  --platform keycloak \
  --protocol oidc_jwt \
  --eval-mode oracle_gen \
  --invariants I1,I2,I3,I4,I5 \
  --sequences-per-invariant 6 \
  --setup-platform \
  --output-dir results/round${ROUND}/ablation_keycloak_oidc_oracle_gen \
  2>&1 | tee results/round${ROUND}/ablation_keycloak_oidc_oracle_gen.log
echo "Ablation oracle_gen done at $(date)"

echo "=========================================="
echo "All 4 Keycloak experiments done at $(date)"
echo "=========================================="
