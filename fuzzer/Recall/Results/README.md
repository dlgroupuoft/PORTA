# PORTA Supplemental 11-CVE Recall Results

All paths are relative to the current checkout's `fuzzer/` directory. These results supplement, and do not replace, the primary experiments under `results/`.

## Results

The three runs detected 10 of the 11 CVEs.

| Run | Result directory in each CVE folder | CVEs detected |
|---|---|---:|
| 1 | `round1` | 10/11 |
| 2 | `round2` | 7/11 |
| 3 | `round3` | 8/11 |
| Union | — | 10/11 |

| Platform | CVE | Round 1 | Round 2 | Round 3 | Evidence |
|---|---|:---:|:---:|:---:|---|
| Keycloak | CVE-2018-14637 | — | — | — | [Result](Keycloak/CVE-2018-14637/README.md) |
| Keycloak | CVE-2022-1245 | ✓ | — | ✓ | [Findings](Keycloak/CVE-2022-1245/README.md) |
| Keycloak | CVE-2023-0264 | ✓ | ✓ | ✓ | [Findings](Keycloak/CVE-2023-0264/README.md) |
| Keycloak | CVE-2023-2422 | ✓ | ✓ | ✓ | [Findings](Keycloak/CVE-2023-2422/README.md) |
| Keycloak | CVE-2023-2585 | ✓ | ✓ | ✓ | [Findings](Keycloak/CVE-2023-2585/README.md) |
| Keycloak | CVE-2023-6291 | ✓ | ✓ | — | [Findings](Keycloak/CVE-2023-6291/README.md) |
| Keycloak | CVE-2023-6544 | ✓ | ✓ | ✓ | [Findings](Keycloak/CVE-2023-6544/README.md) |
| Keycloak | CVE-2024-8698 | ✓ | — | ✓ | [Findings](Keycloak/CVE-2024-8698/README.md) |
| Keycloak | CVE-2025-1391 | ✓ | ✓ | ✓ | [Findings](Keycloak/CVE-2025-1391/README.md) |
| Vault | CVE-2024-5798 | ✓ | — | — | [Findings](Vault/CVE-2024-5798/README.md) |
| Vault | CVE-2025-3879 | ✓ | ✓ | ✓ | [Findings](Vault/CVE-2025-3879/README.md) |

## Reproduce

Configure the official OpenAI API and run one CVE:

```bash
export OPENAI_API_KEY=<api-key>
unset OPENAI_BASE_URL
PORTA_GENERATION_LABEL=replay-20260902 \
  Recall/Results/generation/run-qualified-cve-generation.sh CVE-2023-2422
```

Use a label that does not already exist; the runner refuses to overwrite a result directory. See [generation/README.md](generation/README.md) for image setup and three-run commands.
