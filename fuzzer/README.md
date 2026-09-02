# PORTA Artifact Runbook

Run all commands in this file from the `fuzzer/` directory.

## What to run

| Goal | Command path | Data written |
|---|---|---|
| Reproduce a primary experiment execution | Replay a saved primary `sequences.json` | New `/tmp/porta-replay.*` directory |
| Reproduce supplemental Recall | Run the Recall script with a fresh label | New directory inside each selected CVE folder |
| Regenerate new material | Extract a new profile and generate new sequences | New `artifacts/<label>/` directory |

`results/` contains the preserved April primary experiments. `Recall/` contains the supplemental known-CVE recall benchmark. Do not overwrite either set of recorded result directories.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

python3 -m pytest -q tests/test_imports_clean.py tests/test_eval_modes.py
```

Build the local helper IdP image if it is not already present:

```bash
docker image inspect valence/mock-idp:latest >/dev/null 2>&1 || \
  docker build -t valence/mock-idp:latest docker/mock-idp
bash scripts/prepare_artifact_keys.sh
```

The broker and database images used by the main experiments are listed in `docker/platform-images.yml` with explicit version tags. `valence/mock-idp:latest` is the local helper image built from this repository.

## Reproduce a saved primary experiment by replay

Use the saved April profile and saved `sequences.json`. Replay does not call an LLM and writes only to the new output directory.

```bash
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

find "$REPLAY_OUT" -maxdepth 3 -type f -print
docker compose -f docker/platform-images.yml --profile vault down
```

Replay re-executes PORTA's saved abstract sequence against a fresh broker container. The saved April directories under `results/evaluation/` are the recorded primary results used for statistics.

## Reproduce supplemental Recall

Recall uses its own CVE-specific directories under `Recall/Results/`. The preserved published runs are `round1`, `round2`, and `round3`; use a new label for reproduction.

Set the API key:

```bash
export OPENAI_API_KEY="<your-openai-api-key>"
unset OPENAI_BASE_URL
```

If you have the Recall source image archive, place it at `Recall/Results/images/qualified-cve-source-images.tar.gz` and load it:

```bash
sha256sum -c Recall/Results/images/qualified-cve-source-images.tar.gz.sha256
gzip -dc Recall/Results/images/qualified-cve-source-images.tar.gz | docker load
```

Each CVE README also records the corresponding source-build command if the archive is not available.

Run one CVE:

```bash
PORTA_GENERATION_LABEL=ae-recall-1 \
  Recall/Results/generation/run-qualified-cve-generation.sh CVE-2023-2422
```

Run the full 11-CVE supplemental Recall experiment three times:

```bash
PORTA_GENERATION_LABEL=ae-recall-r1 Recall/Results/generation/run-qualified-cve-generation.sh
PORTA_GENERATION_LABEL=ae-recall-r2 Recall/Results/generation/run-qualified-cve-generation.sh
PORTA_GENERATION_LABEL=ae-recall-r3 Recall/Results/generation/run-qualified-cve-generation.sh
```

Run these commands serially. The script starts the selected vulnerable/fixed target environment, generates sequences for I1-I5, executes them, saves the labeled result directory, and tears down the runtime environment.

## Regenerate a new profile and new sequences

Set a direct OpenAI API key and choose the OpenAI chat-completions model to use for extraction and generation:

```bash
export OPENAI_API_KEY="<your-openai-api-key>"
export PORTA_LLM_MODEL="<openai-chat-completions-model>"
```

Generate a standalone Vault OIDC profile from the checked-in documentation corpus:

```bash
python3 -m src.extraction.run_pipeline \
  --platform vault \
  --protocol oidc_jwt \
  --model "$PORTA_LLM_MODEL" \
  --no-merge \
  --tag ae-run
```

The command prints a path like:

```text
src/profiles/vault_oidc_jwt_ae-run_YYYYMMDD_HHMMSS.json
```

Run a new `full` campaign with that profile:

```bash
docker compose -f docker/platform-images.yml --profile vault up -d vault mock-idp

python3 -m src.stateful.campaign_runner \
  --platform vault \
  --protocol oidc_jwt \
  --profile src/profiles/vault_oidc_jwt_ae-run_YYYYMMDD_HHMMSS.json \
  --eval-mode full \
  --invariants I1,I2,I3,I4,I5 \
  --sequences-per-invariant 10 \
  --llm-model "$PORTA_LLM_MODEL" \
  --setup-platform \
  --output-dir artifacts/ae-vault-oidc

docker compose -f docker/platform-images.yml --profile vault down
```

The structured output is under:

```text
artifacts/ae-vault-oidc/full/campaign_<timestamp>/
```

with `summary.json`, `sequences.json`, `findings.json`, `unique_findings.json`, and `unique_finding_sequences.json`.

The extractor performs three LLM extraction calls over the same documentation input and merges them into one profile. `--no-merge` is required for a standalone timestamped profile; without it, extraction updates `src/profiles/<platform>.json`. `--tag` only labels the standalone filename.

For a new full primary-style round, repeat the profile-generation and campaign commands for each platform/protocol pair. Vault is run for `oidc_jwt`; the other six brokers are run for both `oidc_jwt` and `saml`. Start the matching Compose profile from `docker/platform-images.yml`, pass the matching generated profile with `--profile`, and write to a fresh `artifacts/<round-label>/...` directory.

## Cleanup

Stop a main-experiment broker profile with:

```bash
docker compose -f docker/platform-images.yml --profile vault down
```

Replace `vault` with the profile you started. Do not run cleanup commands against `results/`, `Recall/`, `src/profiles/`, or `src/extraction/`.
