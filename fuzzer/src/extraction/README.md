# PORTA Platform-Profile Extraction

This pipeline converts broker documentation into the JSON platform profiles consumed by `src.stateful.campaign_runner`. Commands must be run from the repository's `fuzzer/` directory so relative source, cache, and output paths resolve correctly.

## Safe standalone extraction

```bash
export OPENAI_API_KEY="<your-openai-api-key>"
export PORTA_LLM_MODEL="<openai-chat-completions-model>"

python3 -m src.extraction.run_pipeline \
  --platform vault \
  --protocol oidc_jwt \
  --model "$PORTA_LLM_MODEL" \
  --no-merge \
  --tag my-run
```

The output path is printed at completion:

```text
src/profiles/vault_oidc_jwt_my-run_YYYYMMDD_HHMMSS.json
```

Pass that exact file to a campaign with `--profile`. `--no-merge` selects the standalone timestamped output instead of merging into the untagged default profile; `--tag` only changes the standalone filename. If `--no-merge` is omitted, the pipeline reads and updates `src/profiles/<platform>.json`, regardless of `--tag`.

The pipeline uses the OpenAI Python SDK chat-completions interface. For artifact evaluation, set a direct `OPENAI_API_KEY` and pass the chosen model explicitly with `--model`.

## Inputs and generated caches

Source configuration lives in `fetch_docs.py` as `PLATFORM_DOC_SOURCES`. A configured extraction may combine:

- upstream GitHub repositories and direct URLs;
- vendored snapshots under `local-docs/`;
- previously downloaded files under `raw_docs/` when their cache is accepted.

The fetch stage cleans and concatenates all selected material into:

```text
cleaned_docs/<platform>/<protocol>/ALL_DOCS.md
```

`local-docs/` is a preserved input corpus. `raw_docs/` and `cleaned_docs/` are generated extraction caches/LLM inputs. Their Markdown files are not run guides and should not be deleted merely because they look repetitive.

Remote discovery can require network access. Set `GITHUB_TOKEN` when GitHub rate limits apply. `--force-fetch` refreshes downloaded material; `--list-only` performs remote discovery and may also need GitHub access.

Extraction may refresh files under `raw_docs/` and `cleaned_docs/` as part of preparing the LLM input. Those directories are tracked reproducibility caches; if you are validating in a clean artifact checkout, either run in a disposable clone or restore cache diffs after the run. Exact replay does not run extraction and does not modify these caches.

## Pipeline behavior

1. **Fetch and clean:** resolve all configured remote and local inputs and write `ALL_DOCS.md`.
2. **Extract:** call the configured LLM three times, then merge the outputs for stability.
3. **Save:** write either a standalone timestamped profile (`--no-merge`) or update the untagged default profile.
4. **Validate, optional:** with `--validate`, probe a running broker and remove extracted fields that provoke HTTP 400 responses.

The three LLM calls are three extraction samples over the same documentation input; they are not three campaign executions. The merge uses majority agreement for endpoint method/path and combines compatible body/response mappings, constraints, and known behaviors. Platform defaults and verified extra operations in `extract_specs.py` are also applied.

## Flags

| Flag | Meaning |
|---|---|
| `--platform NAME` | Required broker: `vault`, `keycloak`, `dex`, `casdoor`, `authentik`, `zitadel`, or `logto` |
| `--protocol NAME` | Profile section, normally `oidc_jwt` or `saml` |
| `--model NAME` | Extraction model; see `--help` for the current default |
| `--no-merge` | Start from an empty profile and write `<platform>_<protocol>[_tag]_<timestamp>.json` |
| `--tag NAME` | Add a label to a standalone timestamped filename |
| `--force-fetch` | Ignore accepted download caches and refresh remote material |
| `--dry-run` | Build documentation input and print prompts without calling the LLM |
| `--list-only` | List remotely discoverable files, without extraction |
| `--validate` | Probe a running platform after extraction |
| `--regenerate` | Back up and remove `src/profiles/<platform>.json` before extraction |

`--regenerate` is unnecessary when `--no-merge` is used. It targets the untagged default profile and creates a `.bak`; do not use it when the intent is to preserve all existing inputs unchanged.

## Supported extraction pairs

Both `oidc_jwt` and `saml` sources are configured for all seven platforms. Vault SAML profiles can be extracted, but the primary paper evaluation intentionally runs Vault only with OIDC/JWT, giving 13 platform/protocol campaigns per round rather than 14.

To create a fresh 13-profile set without overwriting existing profiles:

```bash
for PLATFORM in keycloak dex casdoor authentik zitadel logto; do
  for PROTOCOL in oidc_jwt saml; do
    python3 -m src.extraction.run_pipeline \
      --platform "$PLATFORM" \
      --protocol "$PROTOCOL" \
      --model "$PORTA_LLM_MODEL" \
      --no-merge \
      --tag my-exp
  done
done

python3 -m src.extraction.run_pipeline \
  --platform vault \
  --protocol oidc_jwt \
  --model "$PORTA_LLM_MODEL" \
  --no-merge \
  --tag my-exp
```

This repeats the extraction method and therefore consumes API calls and can yield different profile content. To execute the recorded primary experiments, do not regenerate their profiles: use the exact `evaluation-exp1/2/3` files listed in [`../../results/evaluation/README.md`](../../results/evaluation/README.md).

## From profile to campaign

```bash
docker compose -f docker/platform-images.yml --profile vault up -d vault mock-idp

python3 -m src.stateful.campaign_runner \
  --platform vault \
  --protocol oidc_jwt \
  --profile src/profiles/vault_oidc_jwt_my-exp_YYYYMMDD_HHMMSS.json \
  --eval-mode full \
  --llm-model "$PORTA_LLM_MODEL" \
  --setup-platform \
  --output-dir artifacts/my-exp
```

Freshly generated profiles and sequences are new experiment artifacts and can vary with model output. The saved April profiles and campaign directories remain the recorded primary results. See the main [`../../README.md`](../../README.md) for replay, campaign commands, output layout, and the distinction between primary results and supplemental Recall.
