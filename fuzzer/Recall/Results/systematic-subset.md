# Systematic 11-CVE Subset

The subset starts from all 60 rows in `../cves/identity_broker_logic_vulnerability_classification - identity_broker_logic_vulnerability_classification_v5.csv`.

A CVE is included when it affects Keycloak, Dex, or Vault; concerns OIDC/OAuth or SAML authentication or authorization; has source versions that can be executed; and its trigger can be expressed with PORTA's ordered operations.

| Stage | Retained | Excluded |
|---|---:|---:|
| All CSV rows | 60 | 0 |
| Keycloak, Dex, or Vault | 34 | 26 |
| OIDC/OAuth or SAML | 18 | 16 |
| Expressible with PORTA operations | 11 | 7 |


The seven operation exclusions are:

| CVE | Reason |
|---|---|
| CVE-2021-3827 | Requires SOAP/PAOS ECP transport and an MFA browser-flow comparison. |
| CVE-2023-6927 | Requires capture and browser submission of a JARM `form_post.jwt` response. |
| CVE-2025-3910 | Requires application-initiated-action form state and cancellation submission. |
| CVE-2025-7365 | Requires an upstream provider, email capture, two browser actors, and a victim verification-link action. |
| CVE-2020-26290 | Requires altered SAML response construction, ACS submission, connector callback, and subject observation as separate operations. |
| CVE-2020-27847 | Requires independent control of the signed SAML element, wrapper placement, ACS submission, and resulting identity. |
| CVE-2022-39222 | Requires concurrent victim and attacker actions around callback and approval. |

## Selected Results

| Platform | CVE | Surface | Detection frequency |
|---|---|---|---:|
| Keycloak | CVE-2018-14637 | SAML assertion freshness | 0/3 |
| Keycloak | CVE-2022-1245 | OAuth/OIDC token exchange | 2/3 |
| Keycloak | CVE-2023-0264 | OIDC authorization code | 3/3 |
| Keycloak | CVE-2023-2422 | OAuth/OIDC mTLS client authentication | 3/3 |
| Keycloak | CVE-2023-2585 | OAuth device authorization | 3/3 |
| Keycloak | CVE-2023-6291 | OIDC redirect URI binding | 2/3 |
| Keycloak | CVE-2023-6544 | OIDC dynamic client registration | 3/3 |
| Keycloak | CVE-2024-8698 | SAML signature integrity | 2/3 |
| Keycloak | CVE-2025-1391 | OIDC organization claims | 3/3 |
| Vault | CVE-2024-5798 | OIDC JWT audience binding | 1/3 |
| Vault | CVE-2025-3879 | OAuth bearer-token claim binding | 3/3 |

The three-run union is 10/11.
