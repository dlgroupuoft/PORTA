# 33 Finding Catalog with Code References

This is the supplementary catalog for the pattern-coding methodology
in §5.3.2 of the paper.  Each of the 33 included findings is listed
with: invariant, category (A or B), known/novel, dominant
implementation-assumption pattern, primary source-code location,
permalink to the inspected commit, and a one-sentence rationale for
the pattern assignment.

The pattern set converged after the first labeling pass to the eight
categories shown in Table 6 of the paper:

1. **silent-skip-on-absent-field**
2. **explicit-verification-disabled**
3. **no-persistent-anti-replay-state**
4. **branch-coverage-gap**
5. **stale-configuration-snapshot**
6. **trust-bootstrap-reflexivity**
7. **cross-namespace-identity-collapse**
8. **non-state-predicate**

Pinned commits used for the permalinks below:

| Platform  | Repository | Pinned commit |
|-----------|------------|---------------|
| Zitadel   | https://github.com/zitadel/zitadel | `f94e4065c2ff2c8c304845fa95e10f72b023af5b` |
| Casdoor   | https://github.com/casdoor/casdoor | `f6129b09c8ff483c05bff1b6513da04b43d56706` |
| Dex       | https://github.com/dexidp/dex | `11d2eeb52b42e1980e14cb91e69dd9e3faab2076` |
| Keycloak  | https://github.com/keycloak/keycloak | `7f8be2df2089c2cea85177f3548c9b220be7fdd3` |
| Authentik | https://github.com/goauthentik/authentik | `6aaebf6ad4109cc5c26de0eeba1eb18068ecd74d` |
| Vault JWT plugin | https://github.com/hashicorp/vault-plugin-auth-jwt | `c66034a72bdfc0aaed084cf7e6373b04fe4159e7` |
| Logto     | https://github.com/logto-io/logto | `69d3eb6bdaa6dd18c313da8a94487da294c1d9d4` |

---

## Category A (15 vulnerabilities)

### ZT-1 — JWT `aud` claim not validated
- Platform: Zitadel
- Invariant: I5 — Authorization Scope
- Known / Novel: **Known**
- Pattern: **explicit-verification-disabled**
- Source: `internal/idp/providers/jwt/session.go`, `validateToken()` (lines 74–106)
- Permalink: https://github.com/zitadel/zitadel/blob/f94e4065c2ff2c8c304845fa95e10f72b023af5b/internal/idp/providers/jwt/session.go#L74-L106
- Why this pattern: `validateToken()` calls `oidc.CheckIssuer`, `oidc.CheckSignature`, `oidc.CheckExpiration`, and `oidc.CheckIssuedAt`, but does not call `oidc.CheckAudience()` at all. The audience check is actively absent from the chain, not silently skipped on a missing field.
- Agreed

### ZT-2 — SAML `<AudienceRestriction>` not validated
- Platform: Zitadel
- Invariant: I5 — Authorization Scope
- Known / Novel: **Novel**
- Pattern: **explicit-verification-disabled**
- Source: `internal/idp/providers/saml/session.go`, `FetchUser()` (lines 65–113)
- Permalink: https://github.com/zitadel/zitadel/blob/f94e4065c2ff2c8c304845fa95e10f72b023af5b/internal/idp/providers/saml/session.go#L65-L113
- Why this pattern: After `ParseResponse()`, the code maps user attributes from `Assertion.AttributeStatements` and never inspects `Assertion.Conditions.AudienceRestriction`. The `crewjam/saml` library does not enforce AudienceRestriction by default; the SP must do so. Zitadel does not.
- Agreed, this means that the SAML for other SP can also be used on the Zitadel

### CD-1 — SAML assertion replay (no anti-replay cache)
- Platform: Casdoor
- Invariant: I2 — Temporal Validity
- Known / Novel: **Novel**
- Pattern: **no-persistent-anti-replay-state**
- Source: `object/saml_sp.go`, `ParseSamlResponse()` (lines 35–80)
- Permalink: https://github.com/casdoor/casdoor/blob/f6129b09c8ff483c05bff1b6513da04b43d56706/object/saml_sp.go#L35-L80
- Why this pattern: `ParseSamlResponse()` calls `sp.RetrieveAssertionInfo()` and immediately maps attributes to user info. There is no assertion-ID cache, no `OneTimeUse` enforcement, and no replay detection anywhere in the SAML SP code path.
- Agreed

### CD-2 — SAML `NotOnOrAfter` not enforced
- Platform: Casdoor
- Invariant: I2 — Temporal Validity
- Known / Novel: **Novel**
- Pattern: **silent-skip-on-absent-field**
- Source: `object/saml_sp.go`, `ParseSamlResponse()` (lines 35–80)
- Permalink: https://github.com/casdoor/casdoor/blob/f6129b09c8ff483c05bff1b6513da04b43d56706/object/saml_sp.go#L35-L80
- Why this pattern: The `gosaml2` library reports time-validation results in `assertionInfo.WarningInfo`, but Casdoor never inspects this field. Time bounds (NotOnOrAfter, NotBefore) are not enforced at all on the SP side.
- Agreed

### CD-3 — SAML `<AudienceRestriction>` not validated
- Platform: Casdoor
- Invariant: I5 — Authorization Scope
- Known / Novel: **Known**
- Pattern: **explicit-verification-disabled**
- Source: `object/saml_sp.go`, `ParseSamlResponse()` (lines 35–80)
- Permalink: https://github.com/casdoor/casdoor/blob/f6129b09c8ff483c05bff1b6513da04b43d56706/object/saml_sp.go#L35-L80
- Why this pattern: The SP issuer is set in `buildSp()` (`ServiceProviderIssuer: fmt.Sprintf("%s/api/acs", origin)`), but the audience extracted from the assertion is never compared against it. The check is structurally absent rather than guarded by a missing-field condition.
- Agreed

### CD-4 — Cross-organization token exchange
- Platform: Casdoor
- Invariant: I5 — Authorization Scope
- Known / Novel: **Known**so
- Pattern: **explicit-verification-disabled**
- Source: `object/token_oauth.go`, `GetTokenExchangeToken()` (lines 1248–1407)
- Permalink: https://github.com/casdoor/casdoor/blob/f6129b09c8ff483c05bff1b6513da04b43d56706/object/token_oauth.go#L1248-L1407
- Why this pattern: After parsing the subject token and looking up the user, the function never checks whether `user.Owner` (the user's organization) matches `application.Owner` (the requesting application's organization). The org-boundary check is absent.
- Agreed

### CD-6 — SAML verification cert extracted from response
- Platform: Casdoor
- Invariant: I1 — Proof Integrity
- Known / Novel: **Known**
- Pattern: **trust-bootstrap-reflexivity**
- Source: `object/saml_sp.go`, `buildSpCertificateStore()` (lines 155–215)
- Permalink: https://github.com/casdoor/casdoor/blob/f6129b09c8ff483c05bff1b6513da04b43d56706/object/saml_sp.go#L155-L215
- Why this pattern: When a SAML response is present, `buildSpCertificateStore()` extracts the verification certificate from the SAML response itself via `getCertificateFromSamlResponse()` rather than using the pre-configured trust anchor `provider.IdP`. The signing certificate is read from the same document being verified, which is the textbook trust-bootstrap reflexivity failure.
- Agreed

### CD-7 — MFA bypass via SAML federation path
- Platform: Casdoor
- Invariant: I3 — Flow Coherence
- Known / Novel: **Known**
- Pattern: **branch-coverage-gap**
- Source: `controllers/auth.go`, SAML branch around lines 237–248 (compare to OAuth branch around line 747 and signup branch around line 890)
- Permalink: https://github.com/casdoor/casdoor/blob/f6129b09c8ff483c05bff1b6513da04b43d56706/controllers/auth.go#L237-L248
- Why this pattern: The OAuth and signup branches both call `checkMfaEnable()`. The SAML branch returns the SAML response directly without ever calling `checkMfaEnable()`. The MFA check is present in some authentication branches and missing in the federation branch.
- Agreed

### DX-2 — SAML assertion replay (no cache)
- Platform: Dex
- Invariant: I2 — Temporal Validity
- Known / Novel: **Known**
- Pattern: **no-persistent-anti-replay-state**
- Source: `connector/saml/saml.go`, `HandlePOST()` (lines 295–451)
- Permalink: https://github.com/dexidp/dex/blob/11d2eeb52b42e1980e14cb91e69dd9e3faab2076/connector/saml/saml.go#L295-L451
- Why this pattern: `HandlePOST()` validates signature, subject, and conditions but never records or checks `assertion.ID`. There is no assertion-ID cache and no OneTimeUse handling anywhere in the connector.
- Agreed. since OneTimeUse is also an optional field, I think it can also be classified as silent skip.

### KC-3 — `<OneTimeUse>` not enforced (assertion replay)
- Platform: Keycloak
- Invariant: I2 — Temporal Validity
- Known / Novel: **Known**
- Pattern: **no-persistent-anti-replay-state**
- Source: `saml-core/src/main/java/org/keycloak/saml/validators/ConditionsValidator.java`, `validateOneTimeUse()` (lines 215–223)
- Permalink: https://github.com/keycloak/keycloak/blob/7f8be2df2089c2cea85177f3548c9b220be7fdd3/saml-core/src/main/java/org/keycloak/saml/validators/ConditionsValidator.java#L215-L223
- Why this pattern: `validateOneTimeUse()` only checks for *multiple* `<OneTimeUse>` conditions on the same assertion (a separate spec rule). It returns `Result.VALID` for a single OneTimeUse condition without recording the assertion ID anywhere. There is no persistent assertion-ID cache in the class.
- Agreed. but I feel it can also be categoried as silent-skip-on-absent-field

### AK-1 — SAML `NotOnOrAfter` not checked
- Platform: Authentik
- Invariant: I2 — Temporal Validity
- Known / Novel: **Known**
- Pattern: **silent-skip-on-absent-field**
- Source: `authentik/sources/saml/processors/response.py`, `parse()` (lines 75–97)
- Permalink: https://github.com/goauthentik/authentik/blob/6aaebf6ad4109cc5c26de0eeba1eb18068ecd74d/authentik/sources/saml/processors/response.py#L75-L97
- Why this pattern: `parse()` verifies signature, request ID, and status, then maps attributes. The strings `NotOnOrAfter`, `NotBefore`, and `Conditions` do not appear anywhere in `response.py`.
- Disagreed, I would categorized this as explicit-verification-disabled as no conditions have been verified

### AK-3 — OIDC issuer not verified
- Platform: Authentik
- Invariant: I1 — Proof Integrity
- Known / Novel: **Known**
- Pattern: **explicit-verification-disabled**
- Source: `authentik/sources/oauth/types/oidc.py`, `decode()` call (lines 56–57)
- Permalink: https://github.com/goauthentik/authentik/blob/6aaebf6ad4109cc5c26de0eeba1eb18068ecd74d/authentik/sources/oauth/types/oidc.py#L56-L57
- Why this pattern: The id_token decode call passes `options={"verify_iss": False}` directly into PyJWT. The issuer check is explicitly disabled at the configuration boundary.
- Agreed

### AK-5 — SAML `<Conditions>` and audience not enforced
- Platform: Authentik
- Invariant: I5 — Authorization Scope
- Known / Novel: **Novel**
- Pattern: **silent-skip-on-absent-field**
- Source: `authentik/sources/saml/processors/response.py`, `parse()` (lines 75–97)
- Permalink: https://github.com/goauthentik/authentik/blob/6aaebf6ad4109cc5c26de0eeba1eb18068ecd74d/authentik/sources/saml/processors/response.py#L75-L97
- Why this pattern: Same code path as AK-1: the parser never visits the `<Conditions>` or `<AudienceRestriction>` subtree. Every assertion that passes signature verification is accepted regardless of audience.
- Disagreed, I would categorized this to be **explicit-verification-disabled** because the codes checks for the conditions.

### AK-6 — JWT client assertion `exp` not enforced
- Platform: Authentik
- Invariant: I2 — Temporal Validity
- Known / Novel: **Novel**
- Pattern: **explicit-verification-disabled**
- Source: `authentik/providers/oauth2/views/token.py`, JWT bearer-assertion handler around lines 401–408 (and a parallel block around lines 432–440)
- Permalink: https://github.com/goauthentik/authentik/blob/6aaebf6ad4109cc5c26de0eeba1eb18068ecd74d/authentik/providers/oauth2/views/token.py#L401-L440
- Why this pattern: The decode call passes `options={"verify_aud": False}`, and the surrounding loop catches `PyJWTError` and continues to the next candidate key. In the runtime PoC observed by PORTA, an expired bearer assertion (`exp = now − 600`) is accepted with HTTP 200. The `exp` check is silently swallowed by the broad exception handler in the loop.
- Disagreed, from the code I didn't find how the `exp` check is skipped, but if it is true, I am leaning towards that these are separate vuls: one is explicit-verification-disabled and one is skip absent field.

### LG-1 — OIDC nonce bypass (predicate inversion)
- Platform: Logto
- Invariant: I2 — Temporal Validity (nonce binding)
- Known / Novel: **Known**
- Pattern: **non-state-predicate**
- Source: `packages/core/src/sso/OidcConnector/utils.ts` (lines 176–184)
- Permalink: https://github.com/logto-io/logto/blob/69d3eb6bdaa6dd18c313da8a94487da294c1d9d4/packages/core/src/sso/OidcConnector/utils.ts#L176-L184
- Why this pattern: The check is `if (data.nonce) { assert(data.nonce === nonceFromSession, ...) }`. The predicate inspects whether the *token* contains a nonce, not whether the *session* sent one. The two predicates collapse in the trusted-IdP case but diverge under attack.
- Agreed

---

## Category B (18 findings)

### ZT-3 — Missing `exp` / `iat` enforcement (JWT)
- Platform: Zitadel
- Invariant: I2 — Temporal Validity
- Known / Novel: **Known**
- Pattern: **silent-skip-on-absent-field**
- Source: `internal/idp/providers/jwt/session.go`, `validateToken()` (lines 95–105)
- Permalink: https://github.com/zitadel/zitadel/blob/f94e4065c2ff2c8c304845fa95e10f72b023af5b/internal/idp/providers/jwt/session.go#L95-L105
- Why this pattern: The check is `if !claims.GetExpiration().IsZero() { CheckExpiration(...) }`. When `exp` is absent, `GetExpiration()` returns zero, the predicate is true, and validation is skipped. The same shape applies to the `iat` block immediately below.
- Agreed

### CD-5 — Token exchange accepts revoked tokens
- Platform: Casdoor
- Invariant: I2 — Temporal Validity
- Known / Novel: **Novel**
- Pattern: **explicit-verification-disabled**
- Source: `object/token_oauth.go`, `GetTokenExchangeToken()` (lines 1248–1330)
- Permalink: https://github.com/casdoor/casdoor/blob/f6129b09c8ff483c05bff1b6513da04b43d56706/object/token_oauth.go#L1248-L1330
- Why this pattern: After validating the JWT signature and parsing claims, the function never queries the Token table to check whether the subject token has been revoked. Revocation lookup is structurally absent.

### CD-8 — Flow coherence / unsolicited SAML accepted
- Platform: Casdoor
- Invariant: I3 — Flow Coherence
- Known / Novel: **Novel**
- Pattern: **stale-configuration-snapshot**
- Source: `controllers/auth.go` around lines 800–806; `object/saml_sp.go`, `ParseSamlResponse()`
- Permalink: https://github.com/casdoor/casdoor/blob/f6129b09c8ff483c05bff1b6513da04b43d56706/controllers/auth.go#L800-L806
- Why this pattern: The handler accepts a SAML response without correlating it to a previously initiated AuthnRequest, and provider-config changes (disable, delete) do not invalidate in-flight assertions because there is no flow state to invalidate. The provider snapshot used during the response processing is whatever was loaded at the start of the handler.

### CD-9 — Identity confusion via email-based binding
- Platform: Casdoor
- Invariant: I4 — Principal Binding
- Known / Novel: **Known**
- Pattern: **cross-namespace-identity-collapse**
- Source: `object/saml_sp.go` (NameID assignment around line 55) and `controllers/auth.go` (user lookup around line 868)
- Permalink: https://github.com/casdoor/casdoor/blob/f6129b09c8ff483c05bff1b6513da04b43d56706/object/saml_sp.go#L55
- Why this pattern: The NameID from the SAML assertion is used directly as the identity key for `GetUserByFields()`, with no issuer scoping and no normalization. Two upstream IdPs sending the same NameID (e.g., the same email at different organizations) collide to the same Casdoor user.

### DX-1 — SAML `<Conditions>`/audience optional
- Platform: Dex
- Invariant: I5 — Authorization Scope
- Known / Novel: **Known**
- Pattern: **silent-skip-on-absent-field**
- Source: `connector/saml/saml.go` (lines 366–371)
- Permalink: https://github.com/dexidp/dex/blob/11d2eeb52b42e1980e14cb91e69dd9e3faab2076/connector/saml/saml.go#L366-L371
- Why this pattern: `if assertion.Conditions != nil { p.validateConditions(...) }`. When the `<Conditions>` element is absent, the entire conditions block is skipped, including audience validation. The textbook silent-skip pattern.
- Agreed

### DX-3 — SAML `NotOnOrAfter` not enforced
- Platform: Dex
- Invariant: I2 — Temporal Validity
- Known / Novel: **Novel**
- Pattern: **silent-skip-on-absent-field**
- Source: `connector/saml/saml.go` (lines 366–371; same `if Conditions != nil` block)
- Permalink: https://github.com/dexidp/dex/blob/11d2eeb52b42e1980e14cb91e69dd9e3faab2076/connector/saml/saml.go#L366-L371
- Why this pattern: Time validation lives inside `validateConditions()`. When `Conditions` is absent the check is skipped. Same code shape as DX-1, distinct security obligation.
- Agreed

### DX-4 — Non-atomic SAML connector lifecycle
- Platform: Dex
- Invariant: I3 — Flow Coherence
- Known / Novel: **Novel**
- Pattern: **stale-configuration-snapshot**
- Source: `connector/saml/saml.go`, `provider` struct loaded at `Open()` time; `HandlePOST()` (lines 295–451) does not re-validate the connector config
- Permalink: https://github.com/dexidp/dex/blob/11d2eeb52b42e1980e14cb91e69dd9e3faab2076/connector/saml/saml.go#L295-L451
- Why this pattern: The `provider` struct is initialized once at `Open()` time with CA certs, issuer, and attributes. If the Dex admin reconfigures the connector mid-flow, the in-flight callback continues to use the cached snapshot.
- Agreed

### DX-5 — Unsolicited SAMLResponse accepted
- Platform: Dex
- Invariant: I3 — Flow Coherence
- Known / Novel: **Novel**
- Pattern: **stale-configuration-snapshot**
- Source: `connector/saml/saml.go` (lines 328–331; `InResponseTo` check)
- Permalink: https://github.com/dexidp/dex/blob/11d2eeb52b42e1980e14cb91e69dd9e3faab2076/connector/saml/saml.go#L328-L331
- Why this pattern: The `InResponseTo` correlation depends on the `inResponseTo` parameter that the routing layer derives from RelayState. When the ACS endpoint is invoked without a prior `/auth` flow, the parameter is empty and the correlation degenerates.
- Not sure, I don't really understand the explanation and the code.

### KC-1 — `alg=none` request object accepted
- Platform: Keycloak
- Invariant: I1 — Proof Integrity
- Known / Novel: **Known**
- Pattern: **silent-skip-on-absent-field**
- Source: `services/src/main/java/org/keycloak/protocol/oidc/endpoints/request/AuthzEndpointRequestObjectParser.java` (lines 84–100)
- Permalink: https://github.com/keycloak/keycloak/blob/7f8be2df2089c2cea85177f3548c9b220be7fdd3/services/src/main/java/org/keycloak/protocol/oidc/endpoints/request/AuthzEndpointRequestObjectParser.java#L84-L100
- Why this pattern: The validator only enforces algorithm restrictions when `requestedSignatureAlgorithm` is non-null on the client. When the client does not configure a required algorithm, the predicate `requestedSignatureAlgorithm != null` is false, the algorithm check is skipped, and `alg=none` request objects are accepted.
- Agreed

### KC-4 — Missing `<Conditions>` element accepted
- Platform: Keycloak
- Invariant: I5 — Authorization Scope
- Known / Novel: **Known**
- Pattern: **silent-skip-on-absent-field**
- Source: `saml-core/src/main/java/org/keycloak/saml/validators/ConditionsValidator.java` (lines 117–119)
- Permalink: https://github.com/keycloak/keycloak/blob/7f8be2df2089c2cea85177f3548c9b220be7fdd3/saml-core/src/main/java/org/keycloak/saml/validators/ConditionsValidator.java#L117-L119
- Why this pattern: `isValid()` opens with `if (conditions == null) { return true; }`. Absence of the `<Conditions>` element returns valid before any audience, time, or OneTimeUse check runs. Canonical silent-skip on absent field.
- Agreed

### KC-5 — Wrong SAML audience accepted
- Platform: Keycloak
- Invariant: I5 — Authorization Scope
- Known / Novel: **Known**
- Pattern: **silent-skip-on-absent-field**
- Source: `saml-core/src/main/java/org/keycloak/saml/validators/ConditionsValidator.java` (lines 196–208)
- Permalink: https://github.com/keycloak/keycloak/blob/7f8be2df2089c2cea85177f3548c9b220be7fdd3/saml-core/src/main/java/org/keycloak/saml/validators/ConditionsValidator.java#L196-L208
- Why this pattern: `validateAudienceRestriction()` is correct in isolation, but it is reachable only when `<Conditions>` is present (otherwise KC-4 short-circuits to valid). The audience check is silent-skipped on the same absent-field path as KC-4.
- Agreed

### KC-6 — Flow coherence / non-atomic config
- Platform: Keycloak
- Invariant: I3 — Flow Coherence
- Known / Novel: **Novel**
- Pattern: **stale-configuration-snapshot**
- Source: `services/src/main/java/org/keycloak/broker/saml/SAMLIdentityProvider.java`; configuration loaded at provider initialization, persisted in authentication-session state
- Permalink: https://github.com/keycloak/keycloak/blob/7f8be2df2089c2cea85177f3548c9b220be7fdd3/services/src/main/java/org/keycloak/broker/saml/SAMLIdentityProvider.java
- \xiangyu{Permalink}: https://github.com/keycloak/keycloak/blob/7f8be2df2089c2cea85177f3548c9b220be7fdd3/services/src/main/java/org/keycloak/services/resources/IdentityBrokerService.java#L385-L431
- \xiangyu{Second link}: https://github.com/keycloak/keycloak/blob/7f8be2df2089c2cea85177f3548c9b220be7fdd3/model/infinispan/src/main/java/org/keycloak/models/cache/infinispan/idp/InfinispanIdentityProviderStorageProvider.java#L153-L173
- Why this pattern: Authentication sessions persist their IdP configuration state. Admin changes to the IdP broker (disable, certificate rotation, first-login flow modification) do not invalidate existing sessions.
- \Xiangyu{Why this Pattern}: The `performLogin` function gets the `IdentityProviderModel` based on the cached version( referred in the second link) and then uses it for login.
- Agreed

### AK-7 — Stale trust / non-atomic config update
- Platform: Authentik
- Invariant: I3 — Flow Coherence
- Known / Novel: **Novel**
- Pattern: **stale-configuration-snapshot**
- Source: `authentik/sources/saml/processors/response.py`, `__init__()` (lines 71–73): `self._source = source`
- Permalink: https://github.com/goauthentik/authentik/blob/6aaebf6ad4109cc5c26de0eeba1eb18068ecd74d/authentik/sources/saml/processors/response.py#L71-L73
- Why this pattern: The `ResponseProcessor` captures the `SAMLSource` model object at construction time. JWKS / certificate rotation and source-config changes do not invalidate in-flight processors that already hold a reference to the cached source object.
- Agreed

### VT-5/6 — Identity collision (case + email mapping)
- Platform: Vault (JWT auth plugin)
- Invariant: I4 — Principal Binding
- Known / Novel: **Novel** (combined: VT-5 case-collision is known, VT-6 email-collision is novel; we merge them as a single finding because both arise from the same alias-resolution code path)
- Pattern: **cross-namespace-identity-collapse**
- Source: `path_login.go` `Subject` matching (lines 148–150) and `createIdentity()` `user_claim` handling (lines 237–251)
- Permalink: https://github.com/hashicorp/vault-plugin-auth-jwt/blob/c66034a72bdfc0aaed084cf7e6373b04fe4159e7/path_login.go#L148-L251
- Why this pattern: Vault's identity-alias resolution does not normalize subject casing and accepts shared email addresses across IdPs as the same alias. Two principals from different upstream IdPs collapse into the same downstream entity.
- Agreed

### LG-2 — Unverified email auto-linking
- Platform: Logto
- Invariant: I4 — Principal Binding
- Known / Novel: **Known**
- Pattern: **cross-namespace-identity-collapse**
- Source: `packages/core/src/routes/interaction/utils/single-sign-on.ts` (lines 270–278)
- Permalink: https://github.com/logto-io/logto/blob/69d3eb6bdaa6dd18c313da8a94487da294c1d9d4/packages/core/src/routes/interaction/utils/single-sign-on.ts#L270-L278
- Why this pattern: When no SSO identity record matches, the code falls through to `findUserByEmail(userInfo.email)` and links the SSO identity to that local user without requiring `email_verified`. An attacker who controls an upstream IdP can set any email and merge into the matching local account.
- Agreed

### LG-3 — SAML missing `<Conditions>` accepted
- Platform: Logto
- Invariant: I5 — Authorization Scope
- Known / Novel: **Known**
- Pattern: **silent-skip-on-absent-field**
- Source: `packages/core/src/sso/SamlConnector/utils.ts` (lines 172–201); the underlying behavior is in `samlify`'s `flow.ts` `parseLoginResponse()`, which short-circuits all Conditions validation when the element is absent
- Permalink: https://github.com/logto-io/logto/blob/69d3eb6bdaa6dd18c313da8a94487da294c1d9d4/packages/core/src/sso/SamlConnector/utils.ts#L172-L201
- Why this pattern: Logto delegates SAML response parsing to `samlify`. `samlify` checks `extractedProperties.conditions && verifyTime(...)`; the short-circuit on a falsy `conditions` skips the conditions check entirely. Logto does not add a wrapper check.
- Agreed.

### LG-5 — SAML SSO bypasses MFA
- Platform: Logto
- Invariant: I3 — Flow Coherence
- Known / Novel: **Novel**
- Pattern: **branch-coverage-gap**
- Source: `packages/core/src/routes/interaction/utils/single-sign-on.ts` (`handleSsoAuthentication`, lines 246–289)
- Permalink: https://github.com/logto-io/logto/blob/69d3eb6bdaa6dd18c313da8a94487da294c1d9d4/packages/core/src/routes/interaction/utils/single-sign-on.ts#L246-L289
- Why this pattern: Both `signInWithSsoAuthentication` and `signInAndLinkWithSsoAuthentication` return a `userId` directly. There is no MFA enforcement on the SSO branch even when the user has local MFA configured. The local-login branch enforces MFA; the SSO branch does not.
- Agreed

### LG-6 — Identity collision (case / whitespace / unicode)
- Platform: Logto
- Invariant: I4 — Principal Binding
- Known / Novel: **Novel**
- Pattern: **cross-namespace-identity-collapse**
- Source: `packages/core/src/routes/interaction/utils/single-sign-on.ts` (lines 257–271)
- Permalink: https://github.com/logto-io/logto/blob/69d3eb6bdaa6dd18c313da8a94487da294c1d9d4/packages/core/src/routes/interaction/utils/single-sign-on.ts#L257-L271
- Why this pattern: SSO identity lookup uses `userInfo.id` directly without case normalization, whitespace trimming, or unicode normalization. Email lookup uses `userInfo.email` directly. Two upstream principals that differ only by casing or unicode form collide on the local namespace.
- Agreed

---

## Pattern roll-up

| Pattern | # findings |
|---|---|
| silent-skip-on-absent-field | 9 (CD-2, AK-1, AK-5, ZT-3, DX-1, DX-3, KC-1, KC-4, KC-5, LG-3)|
| explicit-verification-disabled | 8 (ZT-1, ZT-2, CD-3, CD-4, CD-5, AK-3, AK-6) |
| no-persistent-anti-replay-state | 3 (CD-1, DX-2, KC-3) |
| branch-coverage-gap | 2 (CD-7, LG-5) |
| stale-configuration-snapshot | 5 (CD-8, DX-4, DX-5, KC-6, AK-7) |
| trust-bootstrap-reflexivity | 1 (CD-6) |
| cross-namespace-identity-collapse | 4 (CD-9, VT-5/6, LG-2, LG-6) |
| non-state-predicate | 1 (LG-1) |

