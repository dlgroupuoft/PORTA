# PORTA — Identity Broker Vulnerability Fuzzer

PORTA is the artifact accompanying the CCS 2026 paper *Vulnerabilities in Identity Brokers: From Systematic Detection to Lessons Learned*. It tests seven identity brokers—Keycloak, Vault, Dex, Casdoor, Authentik, Zitadel, and Logto—against five trust-translation invariants.


## What is authoritative

The repository contains two complementary experimental bodies:

- [`fuzzer/results/`](fuzzer/results/) contains the original, real experiments. In particular, [`results/evaluation/`](fuzzer/results/evaluation/README.md) is the three-run, 39-campaign primary evaluation and [`results/ablation/`](fuzzer/results/ablation/analysis/README.md) contains the ablation campaigns and analyses. These are the primary paper evidence.
- [`fuzzer/Recall/`](fuzzer/Recall/README.md) is a later supplemental known-CVE recall benchmark: 11 CVEs × 3 rounds. It supplements the primary experiments; it does not replace or invalidate anything under `results/`.

Profiles, saved sequences, raw results, analyses, run scripts, and extracted documentation snapshots are preserved research artifacts. Do not delete or overwrite them when reproducing a run. Use a new output directory and, for Recall, a new round label.

## Documentation map

| Document/data | Role |
|---|---|
| [`fuzzer/README.md`](fuzzer/README.md) | Current installation, extraction, campaign, replay, and output guide |
| [`fuzzer/src/extraction/README.md`](fuzzer/src/extraction/README.md) | How documentation becomes a platform profile |
| [`fuzzer/results/evaluation/README.md`](fuzzer/results/evaluation/README.md) | Primary evaluation configuration, inputs, statistics, and campaign index |
| [`fuzzer/results/ablation/analysis/README.md`](fuzzer/results/ablation/analysis/README.md) | Ablation reproduction and analysis guide |
| [`fuzzer/Recall/README.md`](fuzzer/Recall/README.md) | Supplemental Recall scope and entry points |
| `fuzzer/src/extraction/{local-docs,raw_docs,cleaned_docs}/` | Source snapshots and generated extraction caches, not user manuals |

## Fastest validated replay

The shortest path that does not call an LLM is to replay the saved Vault exp1 sequences with the exact saved profile. Run from this repository root:

```bash
cd fuzzer
python3 -m pip install -r requirements.txt

docker image inspect valence/mock-idp:latest >/dev/null 2>&1 || \
  docker build -t valence/mock-idp:latest docker/mock-idp

docker compose -f docker/platform-images.yml --profile vault up -d vault mock-idp

REPLAY_OUT="$(mktemp -d /tmp/porta-replay.XXXXXX)"
python3 -m src.stateful.campaign_runner \
  --platform vault \
  --protocol oidc_jwt \
  --profile src/profiles/vault_oidc_jwt_evaluation-exp1_20260403_005023.json \
  --eval-mode full \
  --setup-platform \
  --replay results/evaluation/exp1/vault/oidc_jwt/full/campaign_20260403_222006/sequences.json \
  --output-dir "$REPLAY_OUT"

docker compose -f docker/platform-images.yml --profile vault down
```

Replay skips LLM generation and verifies that the saved profile, sequence executor, platform setup, oracle pipeline, and report writer run together. The runner creates fresh runtime keys/tokens and initializes a fresh broker container; the April result directories remain the authoritative recorded outcomes.

For Recall reproduction and optional regeneration of new profiles/sequences, follow [`fuzzer/README.md`](fuzzer/README.md).
