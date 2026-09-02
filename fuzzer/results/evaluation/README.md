# Evaluation Experiment Data Sources & Results

This directory is the **primary paper evaluation**, not an obsolete precursor to Recall. The checked-in April campaigns, profiles, sequences, findings, and analyses are the source of record. [`../../Recall/`](../../Recall/README.md) is a later supplemental known-CVE benchmark.

All paths in this document are relative to the `fuzzer/` directory. Exact historical execution uses the saved profile and `sequences.json`; regenerating a profile invokes an LLM and constitutes a new method run rather than a byte-identical reconstruction.

## Experiment Configuration

- **Runs**: 3 independent runs (exp1, exp2, exp3)
- **Platforms**: 7 (Zitadel, Casdoor, Dex, Keycloak, Authentik, Vault, Logto)
- **Protocols per platform**: OIDC/JWT + SAML (Vault: OIDC/JWT only)
- **Campaigns per run**: 13
- **Sequences per invariant**: 10
- **Invariants**: I1 (Proof Integrity), I2 (Temporal Validity), I3 (Flow Coherence), I4 (Identity Binding), I5 (Authorization Scope)

## Input Profiles

Each experiment uses a distinct set of LLM-generated platform profiles containing API mappings, known behaviors, and constraints.

| Exp | Platform | Protocol | Profile |
|-----|----------|----------|---------|
| exp1 | zitadel | oidc_jwt | `src/profiles/zitadel_oidc_jwt_evaluation-exp1_20260403_012338.json` |
| exp1 | zitadel | saml | `src/profiles/zitadel_saml_evaluation-exp1_20260403_012622.json` |
| exp1 | casdoor | oidc | `src/profiles/casdoor_oidc_jwt_evaluation-exp1_20260403_011205.json` |
| exp1 | casdoor | saml | `src/profiles/casdoor_saml_evaluation-exp1_20260403_011546.json` |
| exp1 | dex | oidc_jwt | `src/profiles/dex_oidc_jwt_evaluation-exp1_20260403_011835.json` |
| exp1 | dex | saml | `src/profiles/dex_saml_evaluation-exp1_20260403_012038.json` |
| exp1 | keycloak | oidc | `src/profiles/keycloak_oidc_jwt_evaluation-exp1_20260403_010530.json` |
| exp1 | keycloak | saml | `src/profiles/keycloak_saml_evaluation-exp1_20260403_010954.json` |
| exp1 | authentik | oidc_jwt | `src/profiles/authentik_oidc_jwt_evaluation-exp1_20260403_004306.json` |
| exp1 | authentik | saml | `src/profiles/authentik_saml_evaluation-exp1_20260403_004541.json` |
| exp1 | vault | oidc_jwt | `src/profiles/vault_oidc_jwt_evaluation-exp1_20260403_005023.json` |
| exp1 | logto | oidc_jwt | `src/profiles/logto_oidc_jwt_evaluation-exp1_20260403_005614.json` |
| exp1 | logto | saml | `src/profiles/logto_saml_evaluation-exp1_20260403_005948.json` |
| exp2 | zitadel | oidc_jwt | `src/profiles/zitadel_oidc_jwt_evaluation-exp2_20260403_020818.json` |
| exp2 | zitadel | saml | `src/profiles/zitadel_saml_evaluation-exp2_20260403_021032.json` |
| exp2 | casdoor | oidc | `src/profiles/casdoor_oidc_jwt_evaluation-exp2_20260403_015717.json` |
| exp2 | casdoor | saml | `src/profiles/casdoor_saml_evaluation-exp2_20260403_015938.json` |
| exp2 | dex | oidc_jwt | `src/profiles/dex_oidc_jwt_evaluation-exp2_20260403_020245.json` |
| exp2 | dex | saml | `src/profiles/dex_saml_evaluation-exp2_20260403_020526.json` |
| exp2 | keycloak | oidc | `src/profiles/keycloak_oidc_jwt_evaluation-exp2_20260403_015117.json` |
| exp2 | keycloak | saml | `src/profiles/keycloak_saml_evaluation-exp2_20260403_015503.json` |
| exp2 | authentik | oidc_jwt | `src/profiles/authentik_oidc_jwt_evaluation-exp2_20260403_012954.json` |
| exp2 | authentik | saml | `src/profiles/authentik_saml_evaluation-exp2_20260403_013321.json` |
| exp2 | vault | oidc_jwt | `src/profiles/vault_oidc_jwt_evaluation-exp2_20260403_013758.json` |
| exp2 | logto | oidc_jwt | `src/profiles/logto_oidc_jwt_evaluation-exp2_20260403_014427.json` |
| exp2 | logto | saml | `src/profiles/logto_saml_evaluation-exp2_20260403_014715.json` |
| exp3 | zitadel | oidc_jwt | `src/profiles/zitadel_oidc_jwt_evaluation-exp3_20260403_024734.json` |
| exp3 | zitadel | saml | `src/profiles/zitadel_saml_evaluation-exp3_20260403_025005.json` |
| exp3 | casdoor | oidc | `src/profiles/casdoor_oidc_jwt_evaluation-exp3_20260403_023812.json` |
| exp3 | casdoor | saml | `src/profiles/casdoor_saml_evaluation-exp3_20260403_024111.json` |
| exp3 | dex | oidc_jwt | `src/profiles/dex_oidc_jwt_evaluation-exp3_20260403_024324.json` |
| exp3 | dex | saml | `src/profiles/dex_saml_evaluation-exp3_20260403_024527.json` |
| exp3 | keycloak | oidc | `src/profiles/keycloak_oidc_jwt_evaluation-exp3_20260403_023241.json` |
| exp3 | keycloak | saml | `src/profiles/keycloak_saml_evaluation-exp3_20260403_023620.json` |
| exp3 | authentik | oidc_jwt | `src/profiles/authentik_oidc_jwt_evaluation-exp3_20260403_021330.json` |
| exp3 | authentik | saml | `src/profiles/authentik_saml_evaluation-exp3_20260403_021624.json` |
| exp3 | vault | oidc_jwt | `src/profiles/vault_oidc_jwt_evaluation-exp3_20260403_022046.json` |
| exp3 | logto | oidc_jwt | `src/profiles/logto_oidc_jwt_evaluation-exp3_20260403_022637.json` |
| exp3 | logto | saml | `src/profiles/logto_saml_evaluation-exp3_20260403_022932.json` |

## Data Sources (Result Directories)

| Exp | Platform | Protocol | Campaign Directory | Summary | Unique Findings |
|-----|----------|----------|--------------------|---------|-----------------|
| exp1 | zitadel | oidc_jwt | `results/evaluation/exp1/zitadel/oidc_jwt/full/campaign_20260403_195436/` | Y | Y |
| exp1 | zitadel | saml | `results/evaluation/exp1/zitadel/saml/full/campaign_20260403_200649/` | Y | Y |
| exp1 | casdoor | oidc | `results/evaluation/exp1/casdoor/oidc/full/campaign_20260403_203622/` | Y | Y |
| exp1 | casdoor | saml | `results/evaluation/exp1/casdoor/saml/full/campaign_20260403_202252/` | Y | Y |
| exp1 | dex | oidc_jwt | `results/evaluation/exp1/dex/oidc_jwt/full/campaign_20260403_204713/` | Y | Y |
| exp1 | dex | saml | `results/evaluation/exp1/dex/saml/full/campaign_20260403_205611/` | Y | Y |
| exp1 | keycloak | oidc | `results/evaluation/exp1/keycloak/oidc/full/campaign_20260403_210746/` | Y | Y |
| exp1 | keycloak | saml | `results/evaluation/exp1/keycloak/saml/full/campaign_20260403_212204/` | Y | Y |
| exp1 | authentik | oidc_jwt | `results/evaluation/exp1/authentik/oidc_jwt/full/campaign_20260403_215753/` | Y | Y |
| exp1 | authentik | saml | `results/evaluation/exp1/authentik/saml/full/campaign_20260403_214241/` | Y | Y |
| exp1 | vault | oidc_jwt | `results/evaluation/exp1/vault/oidc_jwt/full/campaign_20260403_222006/` | Y | Y |
| exp1 | logto | oidc_jwt | `results/evaluation/exp1/logto/oidc_jwt/full/campaign_20260405_001004/` | Y | Y |
| exp1 | logto | saml | `results/evaluation/exp1/logto/saml/full/campaign_20260403_224056/` | Y | Y |
| exp2 | zitadel | oidc_jwt | `results/evaluation/exp2/zitadel/oidc_jwt/full/campaign_20260403_225157/` | Y | Y |
| exp2 | zitadel | saml | `results/evaluation/exp2/zitadel/saml/full/campaign_20260403_230341/` | Y | Y |
| exp2 | casdoor | oidc | `results/evaluation/exp2/casdoor/oidc/full/campaign_20260405_002127/` | Y | Y |
| exp2 | casdoor | saml | `results/evaluation/exp2/casdoor/saml/full/campaign_20260403_231801/` | Y | Y |
| exp2 | dex | oidc_jwt | `results/evaluation/exp2/dex/oidc_jwt/full/campaign_20260403_234103/` | Y | Y |
| exp2 | dex | saml | `results/evaluation/exp2/dex/saml/full/campaign_20260403_234841/` | Y | Y |
| exp2 | keycloak | oidc | `results/evaluation/exp2/keycloak/oidc/full/campaign_20260404_000055/` | Y | Y |
| exp2 | keycloak | saml | `results/evaluation/exp2/keycloak/saml/full/campaign_20260404_001757/` | Y | Y |
| exp2 | authentik | oidc_jwt | `results/evaluation/exp2/authentik/oidc_jwt/full/campaign_20260404_005559/` | Y | Y |
| exp2 | authentik | saml | `results/evaluation/exp2/authentik/saml/full/campaign_20260404_003836/` | Y | Y |
| exp2 | vault | oidc_jwt | `results/evaluation/exp2/vault/oidc_jwt/full/campaign_20260404_010847/` | Y | Y |
| exp2 | logto | oidc_jwt | `results/evaluation/exp2/logto/oidc_jwt/full/campaign_20260404_012104/` | Y | Y |
| exp2 | logto | saml | `results/evaluation/exp2/logto/saml/full/campaign_20260404_013129/` | Y | Y |
| exp3 | zitadel | oidc_jwt | `results/evaluation/exp3/zitadel/oidc_jwt/full/campaign_20260404_014344/` | Y | Y |
| exp3 | zitadel | saml | `results/evaluation/exp3/zitadel/saml/full/campaign_20260404_015455/` | Y | Y |
| exp3 | casdoor | oidc | `results/evaluation/exp3/casdoor/oidc/full/campaign_20260404_022450/` | Y | Y |
| exp3 | casdoor | saml | `results/evaluation/exp3/casdoor/saml/full/campaign_20260404_021043/` | Y | Y |
| exp3 | dex | oidc_jwt | `results/evaluation/exp3/dex/oidc_jwt/full/campaign_20260404_023627/` | Y | Y |
| exp3 | dex | saml | `results/evaluation/exp3/dex/saml/full/campaign_20260404_024421/` | Y | Y |
| exp3 | keycloak | oidc | `results/evaluation/exp3/keycloak/oidc/full/campaign_20260404_025650/` | Y | Y |
| exp3 | keycloak | saml | `results/evaluation/exp3/keycloak/saml/full/campaign_20260404_031037/` | Y | Y |
| exp3 | authentik | oidc_jwt | `results/evaluation/exp3/authentik/oidc_jwt/full/campaign_20260404_034325/` | Y | Y |
| exp3 | authentik | saml | `results/evaluation/exp3/authentik/saml/full/campaign_20260404_032820/` | Y | Y |
| exp3 | vault | oidc_jwt | `results/evaluation/exp3/vault/oidc_jwt/full/campaign_20260404_035751/` | Y | Y |
| exp3 | logto | oidc_jwt | `results/evaluation/exp3/logto/oidc_jwt/full/campaign_20260404_041036/` | Y | Y |
| exp3 | logto | saml | `results/evaluation/exp3/logto/saml/full/campaign_20260404_042132/` | Y | Y |

## Results Table

```
Campaign               |         Exp1         |         Exp2         |         Exp3         |     μ ± σ
                       |  Seq  SR%  UF  L3 Sw L2 L1 |  Seq  SR%  UF  L3 Sw L2 L1 |  Seq  SR%  UF  L3 Sw L2 L1 |   SR%    UF    L3
----------------------------------------------------------------------------------------------------------------------------------
zitadel/oidc_jwt       |   40   82   0   0  0  0  0 |   42   92   1   1  0  0  0 |   38   92   0   0  0  0  0 |  89± 6  0.3±0.6  0.3±0.6
zitadel/saml           |   40   35   5   5  0  0  0 |   39   69  10   7  3  0  0 |   42  100   0   0  0  0  0 |  68±33  5.0±5.0  4.0±3.6
casdoor/oidc           |   35   74   7   7  0  0  0 |   34   73   0   0  0  0  0 |   40   95  17   9  0  8  0 |  81±12  8.0±8.5  5.3±4.7
casdoor/saml           |   40   95   4   3  0  1  0 |   39   92  14  12  0  2  0 |   34   97  14  13  0  1  0 |  95± 3 10.7±5.8  9.3±5.5
dex/oidc_jwt           |   32   59   0   0  0  0  0 |   35   28   0   0  0  0  0 |   36   44   0   0  0  0  0 |  44±16  0.0±0.0  0.0±0.0
dex/saml               |   33   72   8   5  3  0  0 |   31  100  21  17  3  0  1 |   31   96  20  16  3  0  1 |  89±15 16.3±7.2 12.7±6.7
keycloak/oidc          |   41   19   2   2  0  0  0 |   45   28   3   3  0  0  0 |   42   33   6   6  0  0  0 |  27± 7  3.7±2.1  3.7±2.1
keycloak/saml          |   32   90   2   1  0  1  0 |   39   56  11  11  0  0  0 |   40   80  21  21  0  0  0 |  75±17 11.3±9.5 11.0±10.0
authentik/oidc_jwt     |   38   55   8   7  0  0  1 |   42   45   4   3  0  0  1 |   42   21   0   0  0  0  0 |  40±17  4.0±4.0  3.3±3.5
authentik/saml         |   34   94   3   3  0  0  0 |   41   87   9   8  0  1  0 |   35   97   4   4  0  0  0 |  93± 5  5.3±3.2  5.0±2.6
vault/oidc_jwt         |   41   92   7   6  0  0  1 |   39   82  15  10  0  5  0 |   40   87   9   7  0  2  0 |  87± 5 10.3±4.2  7.7±2.1
logto/oidc_jwt         |   43   88   0   0  0  0  0 |   43   86   0   0  0  0  0 |   40   75   4   4  0  0  0 |  83± 7  1.3±2.3  1.3±2.3
logto/saml             |   43   83   8   7  0  0  1 |   46   67   8   6  0  0  2 |   35   80   7   6  0  0  1 |  77± 9  7.7±0.6  6.3±0.6
----------------------------------------------------------------------------------------------------------------------------------
TOTAL exp1             |  492   72  54  46  3  2  3 | (sweep w/dup: 144)
TOTAL exp2             |  515   69  96  78  6  8  4 | (sweep w/dup: 348)
TOTAL exp3             |  495   75 102  86  3 11  2 | (sweep w/dup: 180)
```

Legend: Seq=sequences, SR%=success rate, UF=unique findings, L3=assertion oracle, Sw=mutation sweep, L2=platform verifier, L1=syntactic

## Aggregate Statistics (μ ± σ, n=3)

| Metric | Exp1 | Exp2 | Exp3 | μ ± σ |
|--------|------|------|------|-------|
| Sequences | 492 | 515 | 495 | $500.7 \pm 12.5$ |
| Completed | 356 | 358 | 376 | $363.3 \pm 11.0$ |
| Execution Success Rate | 72.4% | 69.5% | 76.0% | $72.6 \pm 3.2$% |
| Unique Findings | 54 | 96 | 102 | $84.0 \pm 26.2$ |
|   L3 Assertion Oracle | 46 | 78 | 86 | $70.0 \pm 21.2$ |
|   Mutation Sweep | 3 | 6 | 3 | $4.0 \pm 1.7$ |
|   L2 Platform Verifier | 2 | 8 | 11 | $7.0 \pm 4.6$ |
|   L1 Syntactic | 3 | 4 | 2 | $3.0 \pm 1.0$ |
| Total Findings (w/dup) | 206 | 439 | 281 | $308.7 \pm 118.9$ |
|   Sweep (w/dup) | 144 | 348 | 180 | $224.0 \pm 108.9$ |

## Statistical units and catalog classification

Three units must not be mixed:

1. **Raw findings** are all emitted reports before within-campaign deduplication: 926 across the three runs.
2. **Campaign-unique findings** are the `unique_findings.json` entries, summed across campaigns/runs: 252. The same underlying flaw can appear in more than one campaign or run. Manual finding-level triage classifies these as 226 TP and 26 FP.
3. **Distinct flaws** are semantic root causes after cross-run/manual consolidation: 33 in [`finding_catalog.md`](finding_catalog.md), classified as 18 known and 15 novel in [`finding_catalog_annotated.md`](finding_catalog_annotated.md).

The pooled campaign-unique precision is therefore 226/252 = 89.7%. The paper table reports the unweighted mean of the three per-run precisions below, 88.5% ± 6.1%. These are different aggregation conventions, not conflicting result sets.

## TP/FP at Finding Level (per run)

| Metric | Exp1 | Exp2 | Exp3 | μ ± σ |
|--------|------|------|------|-------|
| True Positives | 44 | 89 | 93 | $75.3 \pm 27.2$ |
| False Positives | 10 | 7 | 9 | $8.7 \pm 1.5$ |
| Precision | 81.5% | 92.7% | 91.2% | $88.5 \pm 6.1$% |

## Recomputing checked-in analyses

From `fuzzer/results/evaluation/`:

```bash
python3 count_findings.py
python3 dedup_breakdown.py
python3 compute_kappa.py
```

`count_findings.py` recomputes 926 raw and 252 campaign-unique findings. `dedup_breakdown.py` separates the 672 → 12 mutation-sweep and 254 → 240 sequence-level deduplication counts. `compute_kappa.py` recomputes Cohen's κ = 0.888 on the 33 catalogued pattern codes. These scripts are read-only with respect to the recorded campaign directories.

## File Index

| File | Description |
|------|-------------|
| `results/evaluation/exp{1,2,3}/` | Per-experiment result directories |
| `results/evaluation/exp{1,2,3}/run_script_*.sh` | Preserved historical launch commands |
| `results/evaluation/exp{1,2,3}/{platform}/{protocol}/full/campaign_*/summary.json` | Campaign summaries |
| `results/evaluation/exp{1,2,3}/{platform}/{protocol}/full/campaign_*/unique_findings.json` | Deduplicated findings |
| `results/evaluation/exp{1,2,3}/{platform}/{protocol}/full/campaign_*/sequences.json` | Generated test sequences |
| `results/evaluation/exp{1,2,3}/metrics.json` | Preserved per-run analysis snapshots; use the reconciled tables in this README for cross-run totals |
| `results/evaluation/finding_catalog.md` | Canonical 33-flaw semantic catalog |
| `results/evaluation/finding_catalog_annotated.md` | Known/novel annotation and source evidence |
| `results/evaluation/FP.md` | False-positive analysis |
| `results/evaluation/invariant_data.md` | Invariant-level supporting data |
| `results/evaluation/{count_findings.py,dedup_breakdown.py}` | Raw/unique and branch-specific deduplication counts |
| `results/evaluation/compute_kappa.py` | Inter-rater agreement for 33 pattern codes |
| `scripts/run_evaluation.sh` | Evaluation launcher script |
| `scripts/run_all_experiments.sh` | Unified experiment runner |
| `scripts/analyze_evaluation.py` | Statistics computation script |
| `docker/platform-images.yml` | Platform container definitions; broker/database images use explicit version tags |

No `exp*/logs/run_*.log` files are present in the artifact. Consequently `compute_runtime.py` cannot reconstruct wall-clock runtime from logs and should not be cited as producing a measured zero-runtime result. Campaign JSON remains complete for sequence/finding statistics; runtime is simply unavailable from the checked-in files.
