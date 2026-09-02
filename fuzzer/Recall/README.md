# PORTA Supplemental Recall Evaluation

This directory is a later, supplemental known-CVE recall benchmark: three generation/execution rounds over eleven selected Keycloak and Vault CVEs. Its three-run union detects 10/11 CVEs.

Recall does **not** replace the April primary experiments under [`../results/`](../results/). The primary evaluation and ablations remain the paper's main evidence; Recall adds a separate measurement of recovery on a systematic, executable CVE subset.

All commands run from the repository's `fuzzer/` directory and write inside the selected CVE directory. Existing `round1`, `round2`, and `round3` directories are recorded results and must not be overwritten. The runner refuses an existing output label, so every reproduction must set a fresh `PORTA_GENERATION_LABEL`, for example `replay-20260902`.

- [Results and finding links](Results/README.md)
- [Reproduction commands](Results/generation/README.md)
- [Subset-selection method](Results/systematic-subset.md)
