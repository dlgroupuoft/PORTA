# Baseline B (blind) — TP/FP Analysis

## Configuration
- **eval-mode**: `blind`
- **Generation**: `coverage` strategy (no I1-I5 invariants, no attack examples)
- **Oracle**: full L1+L2+L3 + KBF (unchanged from Full)
- **Sweep**: disabled
- **Sequences/inv**: 10
- **Runs**: 3 (baseline, baseline_r2, baseline_r3)

## Aggregate

| Metric | Run 1 | Run 2 | Run 3 | μ ± σ |
|--------|:--:|:--:|:--:|:--:|
| Sequences | 635 | 637 | 636 | 636.0 ± 1.0 |
| Execution rate | 52.9% | 58.6% | 58.0% | 56.5 ± 3.1% |
| Total findings | 10 | 6 | 3 | 6.3 ± 3.5 |
| **TP** | **0** | **0** | **0** | **0.0** |
| **FP** | 10 | 6 | 3 | 6.3 ± 3.5 |
| **Precision** | **0%** | **0%** | **0%** | **0.0%** |
| Distinct vulns | 0 | 0 | 0 | 0 / 33 |

## All findings reviewed (19 total, all FP)

### Run 1 — 10 findings, 0 TP

| # | Platform/Protocol | Inv | Detection | Description | TP/FP | Reason |
|---|---|:--:|:--:|---|:--:|---|
| 1 | dex/saml | I1 | L1_syntactic | HTTP 500 on saml_login | **FP** | Server error, login rejected (not bypassed). `dex/server/handlers.go:507` returns 500 for any auth failure. |
| 2 | keycloak/saml | I4 | L2_platform | Case divergence: `userA` → `usera` | **FP** | Documented case normalization. `BrokeredIdentityContext.java:107`: `username.toLowerCase()`. Configurable. |
| 3 | keycloak/saml | I4 | L2_platform | Case divergence: `userB` → `userb` | **FP** | Same documented behavior. |
| 4-10 | keycloak/saml | I1 | L1_syntactic | HTTP 500 on saml_login (×7) | **FP** | All return `"unknown_error"`. RuntimeException in SAML parsing → 500. Login failed, not bypassed. |

### Run 2 — 6 findings, 0 TP

| # | Platform/Protocol | Inv | Detection | Description | TP/FP | Reason |
|---|---|:--:|:--:|---|:--:|---|
| 1 | authentik/oidc_jwt | I4 | L2_platform | Identity collision: `cov_alice`, `cov_bob` → same internal ID | **FP** | Test setup failure: blind sequence didn't differentiate sub claims via mock-idp; Authentik used `EMAIL_LINK` matching mode. |
| 2 | authentik/oidc_jwt | I4 | L2_platform | Identity collision: `alicia`, `alice` → same internal ID | **FP** | Same — test precondition invalid. |
| 3 | dex/saml | I1 | L1_syntactic | HTTP 500 on saml_login | **FP** | Same as Run 1 — server error. |
| 4-6 | keycloak/saml | I1 | L1_syntactic | HTTP 500 on saml_login (×3) | **FP** | Same as Run 1 — RuntimeException → 500. |

### Run 3 — 3 findings, 0 TP

| # | Platform/Protocol | Inv | Detection | Description | TP/FP | Reason |
|---|---|:--:|:--:|---|:--:|---|
| 1 | authentik/oidc_jwt | I4 | L2_platform | Identity collision: `alex`, `alex1` → same internal ID | **FP** | Same as Run 2 — test setup, EMAIL_LINK matching. |
| 2 | dex/saml | I1 | L1_syntactic | HTTP 500 on saml_login | **FP** | Server error. |
| 3 | keycloak/saml | I1 | L1_syntactic | HTTP 500 on saml_login | **FP** | RuntimeException → 500. |

## FP category breakdown

| Category | Count | % |
|---|:--:|:--:|
| HTTP 500 server error mislabeled as I1 | 14 | 73.7% |
| Documented case normalization | 2 | 10.5% |
| Test setup identity collision | 3 | 15.8% |
| **Total** | **19** | **100%** |

## Per-platform results (3 runs combined)

| Platform/Protocol | R1 | R2 | R3 | TP | All FP reason |
|---|:--:|:--:|:--:|:--:|---|
| dex/saml | 1 | 1 | 1 | **0** | HTTP 500 |
| keycloak/saml | 9 | 3 | 1 | **0** | HTTP 500 (11) + case norm (2) |
| authentik/oidc_jwt | 0 | 2 | 1 | **0** | Identity collision (test setup) |
| zitadel/oidc_jwt | 0 | 0 | 0 | 0 | — |
| zitadel/saml | 0 | 0 | 0 | 0 | — |
| casdoor/saml | 0 | 0 | 0 | 0 | — |
| casdoor/oidc | 0 | 0 | 0 | 0 | — |
| dex/oidc_jwt | 0 | 0 | 0 | 0 | — |
| keycloak/oidc | 0 | 0 | 0 | 0 | — |
| authentik/saml | 0 | 0 | 0 | 0 | — |
| vault/oidc_jwt | 0 | 0 | 0 | 0 | — |
| logto/oidc_jwt | 0 | 0 | 0 | 0 | — |
| logto/saml | 0 | 0 | 0 | 0 | — |

## Key observation

Without invariant guidance, the LLM in `coverage` mode generates sequences that:

1. **Cannot construct valid attack payloads** — execution rate drops to 56.5% (vs 72.6% for Full).
2. **Only trigger generic server errors** — all I1 findings are HTTP 500s, not real bypasses.
3. **Cover only I1 and I4 (and only as noise)** — completely miss I2 (replay/temporal), I3 (flow coherence), and I5 (audience). These three invariant classes account for 75% of all real vulnerabilities in the catalog.

**Result**: **0 reportable vulnerabilities across 3 runs**. Baseline B is fundamentally unable to find security bugs without invariant taxonomy.
