# A1 (no_examples) — TP/FP Analysis

## Configuration
- **eval-mode**: `no_examples`
- **Generation**: `attack` strategy with I1-I5 invariants in prompt, **no CVE attack examples**
- **Oracle**: full L1+L2+L3 + KBF (unchanged from Full)
- **Sweep**: disabled
- **Sequences/inv**: 10
- **Runs**: 3 (a1_no_examples, a1_no_examples_r2, a1_no_examples_r3)

## Aggregate

| Metric | Run 1 | Run 2 | Run 3 | μ ± σ |
|--------|:--:|:--:|:--:|:--:|
| Sequences | 486 | 501 | 489 | 492.0 ± 7.9 |
| Execution rate | 63.6% | 61.5% | 64.8% | 63.3 ± 1.7% |
| Total findings | 58 | 53 | 60 | 57.0 ± 3.6 |
| **TP** | **50** | **41** | **38** | **43.0 ± 6.0** |
| **FP** | 8 | 12 | 22 | 14.0 ± 7.2 |
| **Precision** | **86.2%** | **77.4%** | **63.3%** | **75.6 ± 11.5%** |
| Distinct vulns/run | 22 | 14 | 14 | 16.7 ± 4.6 |
| **Distinct vulns (union 3 runs)** | | | | **26 / 33** |

## Distinct vulnerabilities discovered (3-run union)

| # | Vuln ID | Platform | Inv | Description | R1 | R2 | R3 |
|---|---|---|:--:|---|:--:|:--:|:--:|
| 1 | AK-1 | authentik | I2 | SAML assertion replay (no Assertion ID cache) | ✓ | ✓ | — |
| 2 | AK-1 | authentik | I2 | SAML NotOnOrAfter not validated (Conditions stripped) | ✓ | ✓ | — |
| 3 | AK-3 | authentik | I1 | OIDC issuer mismatch accepted | — | — | ✓ |
| 4 | AK-5 | authentik | I5 | SAML missing Conditions accepted | ✓ | ✓ | — |
| 5 | AK-7 | authentik | I3 | Source disable/removal stale config | ✓ | ✓ | — |
| 6 | CD-1 | casdoor | I2 | SAML assertion replay (no cache) | ✓ | ✓ | ✓ |
| 7 | CD-2 | casdoor | I2 | SAML NotOnOrAfter not enforced | ✓ | ✓ | ✓ |
| 8 | CD-3 | casdoor | I5 | SAML missing Conditions / audience | ✓ | ✓ | — |
| 9 | CD-4 | casdoor | I5 | Cross-org / app-tag bypass via token exchange | ✓ | — | ✓ |
| 10 | CD-5 | casdoor | I2 | Token exchange accepts revoked subject token | ✓ | ✓ | — |
| 11 | CD-6 | casdoor | I1/I3 | Cert from response / issuer mismatch | ✓ | — | ✓ |
| 12 | CD-7 | casdoor | I3 | MFA bypass via SAML federation path | ✓ | — | — |
| 13 | CD-8 | casdoor | I3 | Unsolicited SAML / direct ACS POST | ✓ | ✓ | ✓ |
| 14 | CD-9 | casdoor | I4 | Cross-IdP same NameID → same account | ✓ | — | — |
| 15 | DX-1 | dex | I5 | SAML missing Conditions / wrong audience accepted | ✓ | — | ✓ |
| 16 | DX-2 | dex | I2 | SAML assertion replay (no cache) | ✓ | ✓ | ✓ |
| 17 | DX-3 | dex | I2 | NotOnOrAfter via nil-Conditions path | ✓ | ✓ | ✓ |
| 18 | DX-4 | dex | I3 | Non-atomic connector / second SAMLResponse | — | ✓ | — |
| 19 | DX-5 | dex | I3 | Unsolicited SAMLResponse accepted | — | ✓ | — |
| 20 | KC-1 | keycloak | I1 | alg=none request object accepted | ✓ | — | ✓ |
| 21 | KC-3 | keycloak | I2 | OneTimeUse replay accepted | ✓ | ✓ | ✓ |
| 22 | KC-4 | keycloak | I5 | Missing Conditions accepted | ✓ | — | ✓ |
| 23 | KC-6 | keycloak | I3 | Flow coherence / non-atomic config change | ✓ | — | ✓ |
| 24 | LG-1 | logto | I2 | OIDC nonce bypass (inverted check) | ✓ | ✓ | ✓ |
| 25 | LG-5 | logto | I3 | SAML SSO bypasses MFA | ✓ | — | — |
| 26 | VT-5/6 | vault | I4 | Identity collision (Admin/admin case) | — | ✓ | — |
| 27 | ZT-3 | zitadel | I3 | Stale IdP intent: login completes after IdP removed | ✓ | — | — |

**Total distinct vulnerabilities discovered: 26 / 33**

### Vulnerabilities missed by A1 (7/33)

| Vuln ID | Platform | Inv | Description | Why missed |
|---|---|:--:|---|---|
| ZT-1 | zitadel | I5 | JWT aud not validated | No audience-mismatch sequences generated without examples |
| ZT-2 | zitadel | I5 | SAML AudienceRestriction not validated | Same |
| AK-6 | authentik | I2 | JWT temporal claims not enforced | No JWT-client-assertion sequences; OIDC JWT only had 2% exec rate |
| KC-5 | keycloak | I5 | Wrong SAML audience accepted | LLM generated nocond sequences (KC-4) but not audience-mutation |
| LG-2 | logto | I4 | Email auto-linking | Identity-merging sequences not generated |
| LG-3 | logto | I5 | SAML missing Conditions | Logto SAML not exercised by examples-free generation |
| LG-6 | logto | I4 | Identity collision (case/unicode) | Identity-collision sequences not generated |

## FP analysis

### Run 1 (8 FP)

| # | Platform/Protocol | Inv | Reason |
|---|---|:--:|---|
| 1 | dex/saml | I1 | HTTP 500 server error (login rejected) |
| 2 | dex/saml | I5 | `allowedGroups=['*']` test premise invalid (`*` not a wildcard in `dex/pkg/groups/groups.go`) |
| 3 | dex/saml | I5 | Same — `*` literal not glob |
| 4 | casdoor/oidc | I4 | Trivially identical NFC/NFD ASCII input (no real unicode difference) |
| 5 | authentik/saml | I3 | MFA per-flow design choice (debatable) |
| 6 | authentik/saml | I3 | Duplicate callback impact unclear |
| 7 | logto/saml | I3 | Compound assertion: SSO bypass MFA is documented design |
| 8 | vault/oidc_jwt | I3 | Vault key rotation TTL grace period (by design) |

### Run 2 (12 FP)

| # | Platform/Protocol | Inv | Reason |
|---|---|:--:|---|
| 1 | keycloak/saml | I3 | Cross-realm null capture (test precondition not validated) |
| 2 | logto/oidc_jwt | I4 | Empty-sub test failure (mock-idp didn't produce empty sub) |
| 3 | logto/saml | I1 | `victim_create == 201` got 200 (test setup) |
| 4 | logto/saml | I1 | `saml_app_create == 201` got 400 (test setup) |
| 5-9 | vault/oidc_jwt | I1/I3/I4 | `user_claim=email` admin-configured behavior (5 findings) |
| 10 | vault/oidc_jwt | I1 | alg=none — Vault rejects via cap library; 200 from different code path |
| 11 | vault/oidc_jwt | I1 | kid injection — JWKS URL is admin-configured, not bypassable |
| 12 | vault/oidc_jwt | I3 | Vault key rotation TTL grace period |

### Run 3 (~22 FP)

| Category | Count | Notes |
|---|:--:|---|
| Vault `user_claim=email` admin config | ~7 | Same root cause as R2 |
| Test precondition / control failures | ~6 | Various |
| Casdoor I4 identity match (admin config) | ~3 | Email-based linking documented |
| Other FP | ~6 | misc |

## FP category breakdown (3 runs aggregated)

| FP Category | Count |
|---|:--:|
| Vault `user_claim=email` admin-configured behavior | ~14 |
| Vault key rotation TTL grace period (by design) | ~3 |
| Control path / test setup failure | ~10 |
| Test precondition not validated (null capture) | ~5 |
| HTTP 500 = rejection | ~2 |
| Invalid test premise (e.g., `*` not wildcard) | ~3 |
| Trivially identical ASCII (NFC/NFD) | ~1 |
| Debatable design / admin config (MFA, callback) | ~4 |
| **Total** | **~42** |

## Per-platform breakdown (3 runs combined)

| Platform/Protocol | Findings | TP | FP | Precision |
|---|:--:|:--:|:--:|:--:|
| zitadel/oidc_jwt | 1 | 1 | 0 | 100% |
| zitadel/saml | 0 | 0 | 0 | — |
| casdoor/oidc | 21 | ~19 | ~2 | ~90% |
| casdoor/saml | 34 | ~33 | ~1 | ~97% |
| dex/oidc_jwt | 0 | 0 | 0 | — |
| dex/saml | 36 | ~33 | ~3 | ~92% |
| keycloak/oidc | 10 | 10 | 0 | 100% |
| keycloak/saml | 21 | ~18 | ~3 | ~86% |
| authentik/oidc_jwt | 2 | 2 | 0 | 100% |
| authentik/saml | 18 | ~16 | ~2 | ~89% |
| vault/oidc_jwt | 12 | 2 | ~10 | ~17% |
| logto/oidc_jwt | 6 | ~5 | ~1 | ~83% |
| logto/saml | 7 | ~3 | ~4 | ~43% |

## Key observations

1. **A1 still finds 26/33 vulnerabilities (79% coverage)** despite missing CVE attack examples — invariant guidance alone is sufficient for sequence generation in most cases.

2. **Per-vuln assertion accuracy degrades** — without examples, the LLM generates less precise oracle assertions (e.g., wrong field comparisons, missing precondition checks), causing some FPs.

3. **Vault is the dominant FP source** — without examples teaching the LLM about `user_claim` configuration, generated sequences keep testing email-based identity linking (which is admin-configured, not a vulnerability). This produces ~14/42 FPs.

4. **Logto SAML coverage drops** — A1 only finds LG-1 and LG-5; misses LG-2/3/6, which require state-comparison-style sequences that examples would have demonstrated.

5. **Compared to LLM-Judge**: A1 finds more than 2× as many distinct flaws (26 vs 12), with about 9× higher mean precision (75.6% vs 8.4%). This shows that **invariants + deterministic oracle** are more important than **examples + LLM judge**.
