# PORTA Supplemental Recall Reproduction

Run all commands from the current checkout's `fuzzer/` directory. These commands create a new supplemental Recall run; they do not regenerate or replace the primary experiments under `results/`.

- Model: `gpt-5.2-2025-12-11`
- Invariants: I1-I5
- Requests per invariant: 10

## API

Use the official OpenAI API:

```bash
export OPENAI_API_KEY=<api-key>
unset OPENAI_BASE_URL
```

## Images

If the image archive is available:

```bash
bash scripts/prepare_artifact_keys.sh
sha256sum -c Recall/Results/images/qualified-cve-source-images.tar.gz.sha256
gzip -dc Recall/Results/images/qualified-cve-source-images.tar.gz | docker load
```

Otherwise, use the build command in the selected CVE's README.

## Run

Run one CVE with a new label:

```bash
PORTA_GENERATION_LABEL=replay-20260902 \
  Recall/Results/generation/run-qualified-cve-generation.sh CVE-2023-2422
```

Run all eleven CVEs three times with labels that do not already exist:

```bash
PORTA_GENERATION_LABEL=replay-r1-20260902 Recall/Results/generation/run-qualified-cve-generation.sh
PORTA_GENERATION_LABEL=replay-r2-20260902 Recall/Results/generation/run-qualified-cve-generation.sh
PORTA_GENERATION_LABEL=replay-r3-20260902 Recall/Results/generation/run-qualified-cve-generation.sh
```

Run the commands serially. Each command starts the vulnerable source build, generates ten sequences for each invariant, executes them, saves the result directory, and removes the runtime environment. `round1`, `round2`, and `round3` are the preserved published supplemental runs; the script refuses to overwrite an existing label.
