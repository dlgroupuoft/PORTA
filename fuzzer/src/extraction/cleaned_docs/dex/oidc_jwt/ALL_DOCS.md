

================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/connectors/oauth.md
================================================================================

---
title: "Authentication Through an OAuth 2.0 Provider"
linkTitle: "OAuth 2.0"
description: ""
date: 2021-03-15
toc: true
weight: 2055
---

## Overview

Dex users can make use of this connector to work with standards-compliant [OAuth 2.0](https://oauth.net/2/) authorization providers, in case those authorization providers are not already in the Dex connectors list.

## Configuration

The following is an example of a configuration for using OAuth connector with Reddit.

```yaml
connectors:
- type: oauth
  # ID of OAuth 2.0 provider
  id: reddit
  # Name of OAuth 2.0 provider
  name: reddit
  config:
    # Connector config values starting with a "$" will read from the environment.
    clientID: $REDDIT_CLIENT_ID
    clientSecret: $REDDIT_CLIENT_SECRET
    redirectURI: http://127.0.0.1:5556/dex/callback

    tokenURL: https://www.reddit.com/api/v1/access_token
    authorizationURL: https://www.reddit.com/api/v1/authorize
    userInfoURL: https://www.reddit.com/api/v1/me

    # Optional: Some providers return claims without "email_verified", when they had no usage of emails verification in enrollment process
    # or if they are acting as a proxy for another IDP etc AWS Cognito with an upstream SAML IDP
    # This can be overridden with the below option
    # insecureSkipEmailVerified: true

    # Optional: Specify whether to communicate to Auth provider without
    # validating SSL certificates
    # insecureSkipVerify: false

    # Optional: The location of file containing SSL certificates to communicate
    # to Auth provider
    # rootCAs:
    # - /etc/ssl/reddit.pem

    # Optional: List of scopes to request Auth provider for access user account
    # scopes:
    #  - identity

    # Optional: Configurable keys for user ID look up
    # Default: id
    # userIDKey:

    # Auth providers return non-standard user identity profile
    # Use claimMapping to map those user informations to standard claims:
    claimMapping:
      # Optional: Configurable keys for user name look up
      # Default: user_name
      # userNameKey:

      # Optional: Configurable keys for preferred username look up
      # Default: preferred_username
      # preferredUsernameKey:

      # Optional: Configurable keys for user groups look up
      # Default: groups
      # groupsKey:

      # Optional: Configurable keys for email look up
      # Default: email
      # emailKey:

      # Optional: Configurable keys for email verified look up
      # Default: email_verified
      # emailVerifiedKey:
```



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/configuration/oauth2.md
================================================================================

---
title: "OAuth2"
description: "OAuth2 flow customization options"
date: 2024-01-05
draft: false
toc: true
weight: 1060
---
Dex provides a range of configurable options that empower you to fine-tune and personalize various aspects of the authentication and user flow.

## Flow Customization
Customize OAuth2 settings to align with your authentication requirements.

```yaml
oauth2:
  grantTypes: [ "authorization_code" ]
  responseTypes: [ "code" ]
  skipApprovalScreen: true
  alwaysShowLoginScreen: false
```

### Authentication flow
* `responseTypes` - allows you to configure the desired auth flow (`Authorization Code Flow`, `Implicit Flow`, or `Hybrid Flow`) based on different values. See the table below for valid configuration options.

| `responseTypes` value  | flow                    |
|------------------------|-------------------------|
| `code`                 | Authorization Code Flow |
| `id_token`             | Implicit Flow           |
| `id_token token`       | Implicit Flow           |
| `code id_token`        | Hybrid Flow             |
| `code token`           | Hybrid Flow             |
| `code id_token token`  | Hybrid Flow             |
Examples of the different flows and their behavior can be found in the [official openid spec](https://openid.net/specs/openid-connect-core-1_0.html#AuthorizationExamples).

### User flow

Customizing the user flow allows you to influence how users login into your application.

* `skipApprovalScreen` - controls the need for user approval before sharing data with connected applications. If enabled, users must approve data sharing with every auth flow.
  {{% alert color="info" %}}
  This setting is not applicable when the request has the `approval_prompt=force` parameter. In this case, the approval screen is always shown.
  {{% /alert %}}
* `alwaysShowLoginScreen` - whether to always display the login screen. If only one authentication method is enabled, the default behavior is to go directly to it. For connected IdPs, this redirects the browser away from the application to upstream provider, such as the Google login page.

## Configurable Grants

Dex supports various OAuth2 and OpenID Connect grant types. You can control which grant types are available by configuring the `grantTypes` setting.

```yaml
oauth2:
  grantTypes:
    - "authorization_code"
    - "refresh_token"
    - "urn:ietf:params:oauth:grant-type:token-exchange"
```

### Available grant types

The following grant types can be enabled or disabled:

| Grant Type | Description | Special Configuration |
|-----------|-------------|---------------------|
| `authorization_code` | Authorization Code Flow - recommended for web and mobile applications | - |
| `refresh_token` | Refresh Token Grant - allows clients to obtain new access tokens without user interaction | - |
| `password` | Resource Owner Password Credentials Flow - deprecated and less secure | **Requires `passwordConnector` to be set** |
| `client_credentials` | Client Credentials Flow - for server-to-server communication | **Requires feature flag:** `DEX_CLIENT_CREDENTIAL_GRANT_ENABLED_BY_DEFAULT=true` |
| `urn:ietf:params:oauth:grant-type:token-exchange` | Token Exchange Grant (RFC 8693) - allows clients to exchange tokens from external identity providers | - |
| `urn:ietf:params:oauth:grant-type:device_code` | Device Code Grant (RFC 8628) - for devices with limited input capabilities | - |

{{% alert color="warning" %}}
**Important Notes:**
- **Implicit Flow** is not configured via `grantTypes`. Instead, use the `responseTypes` setting (see [Authentication flow](#authentication-flow) section above).
- **Password Grant** will not work unless `passwordConnector` is configured (see [Password grants](#password-grants) section below).
- **Client Credentials Grant** requires the environment variable `DEX_CLIENT_CREDENTIAL_GRANT_ENABLED_BY_DEFAULT=true` to be set.
{{% /alert %}}

### Default behavior

If the `grantTypes` field is not specified, Dex enables these default grant types:
- `authorization_code`
- `refresh_token`
- `urn:ietf:params:oauth:grant-type:token-exchange`

{{% alert color="info" %}}
To use token exchange and device grants, the supported upstream connector must be properly configured. Token exchange works with OIDC connectors, while device code flow requires additional configuration.
{{% /alert %}}

### Examples

**Enable only Authorization Code flow:**
```yaml
oauth2:
  grantTypes: [ "authorization_code" ]
```

**Enable client credentials grant for server-to-server authentication:**

Set the required environment variable, client credentials grant is enabled by default:
```bash
```

**Enable password grant (not recommended):**
```yaml
oauth2:
  passwordConnector: local  # Required for password grant
```

Password grants involve clients directly sending a user's credentials (`username` and `password`) to the authorization server (dex), acquiring access tokens without the need for an intermediate authorization step.

**Enable Implicit Flow:**

Implicit flow is configured via `responseTypes`, not `grantTypes`:
```yaml
oauth2:
  responseTypes: [ "id_token", "token" ]
```

### Configuration options

* `grantTypes` - list of enabled grant types (see [Configurable Grants](#configurable-grants) section above). To enable password grants, ensure `"password"` is included in this list.
* `passwordConnector` - specifies the connector's id that is used for password grants

{{% alert title="Warning" color="warning" %}}
The password grant type is not recommended for use by the [OAuth 2.0 Security Best Current Practice](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics-13#section-3.4) because of serious security concerns.
Please see [oauth.net](https://oauth.net/2/grant-types/password/) for additional information.
{{% /alert %}}



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/openid-connect.md
================================================================================

---
title: "An Overview of OpenID Connect"
linkTitle: "Intro to OpenID Connect"
description: "Intro to OpenID Connect (basics)"
date: 2020-09-30
draft: false
toc: true
type: "docs"
weight: 1020
---

This document attempts to provide a general overview of the [OpenID Connect protocol](https://openid.net/connect/), a flavor of OAuth2 that dex implements. While this document isn't complete, we hope it provides enough information to get users up and running.

For an overview of custom claims, scopes, and client features implemented by dex, see [this document](/docs/configuration/custom-scopes-claims-clients).

## OAuth2

OAuth2 should be familiar to anyone who's used something similar to a "Login
with Google" button. In these cases an application has chosen to let an
outside provider, in this case Google, attest to your identity instead of
having you set a username and password with the app itself.

The general flow for server side apps is:

1. A new user visits an application.
1. The application redirects the user to Google.
1. The user logs into Google, then is asked if it's okay to let the
application view the user's profile, post on their behalf, etc.
1. If the user clicks okay, Google redirects the user back to the application
with a code.
1. The application redeems that code with provider for a token that can be used
to access the authorized actions, such as viewing a users profile or posting on
their wall.

In these cases, dex is acting as Google (called the "provider" in OpenID
Connect) while clients apps redirect to it for the end user's identity.

## ID Tokens

Unfortunately the access token applications get from OAuth2 providers is
completely opaque to the client and unique to the provider. The token you
receive from Google will be completely different from the one you'd get from
Twitter or GitHub.

OpenID Connect's primary extension of OAuth2 is an additional token returned in
the token response called the ID Token. This token is a [JSON Web Token](
https://tools.ietf.org/html/rfc7519) signed by the OpenID Connect server, with
well known fields for user ID, name, email, etc. A typical token response from
an OpenID Connect looks like (with less whitespace):

```json
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: no-store
Pragma: no-cache

{
 "access_token": "SlAV32hkKG",
 "token_type": "Bearer",
 "refresh_token": "8xLOxBtZp8",
 "expires_in": 3600,
 "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjFlOWdkazcifQ.ewogImlzcyI6ICJodHRwOi8vc2VydmVyLmV4YW1wbGUuY29tIiwKICJzdWIiOiAiMjQ4Mjg5NzYxMDAxIiwKICJhdWQiOiAiczZCaGRSa3F0MyIsCiAibm9uY2UiOiAibi0wUzZfV3pBMk1qIiwKICJleHAiOiAxMzExMjgxOTcwLAogImlhdCI6IDEzMTEyODA5NzAKfQ.ggW8hZ1EuVLuxNuuIJKX_V8a_OMXzR0EHR9R6jgdqrOOF4daGU96Sr_P6qJp6IcmD3HP99Obi1PRs-cwh3LO-p146waJ8IhehcwL7F09JdijmBqkvPeB2T9CJNqeGpe-gccMg4vfKjkM8FcGvnzZUN4_KSP0aAp1tOJ1zZwgjxqGByKHiOtX7TpdQyHE5lcMiKPXfEIQILVq0pc_E2DzL7emopWoaoZTF_m0_N0YzFC6g6EJbOEoRoSK5hoDalrcvRYLSrQAZZKflyuVCyixEoV9GfNQC3_osjzw2PAithfubEEBLuVVk4XUVrWOLrLl0nx7RkKU8NXNHq-rvKMzqg"
}
```

That ID Token is a JWT with three base64'd fields separated by dots. The first
is a header, the second is a payload, and the third is a signature of the first
two fields. When parsed we can see the payload of this value is.

```json
{
  "iss": "http://server.example.com",
  "sub": "248289761001",
  "aud": "s6BhdRkqt3",
  "nonce": "n-0S6_WzA2Mj",
  "exp": 1311281970,
  "iat": 1311280970
}
```

This has a few interesting fields such as

* The server that issued this token (`iss`).
* The token's subject (`sub`). In this case a unique ID of the end user.
* The token's audience (`aud`). The ID of the OAuth2 client this was issued for.

A real world token would have additional claims like the user's name, email, groups, etc.

```json
{
  "iss": "https://dex.example.com/",
  "sub": "R29vZCBqb2IhIEdpdmUgdXMgYSBzdGFyIG9uIGdpdGh1Yg",
  "aud": [
    "kubernetes",
    "kubeconfig-generator"
  ],
  "exp": 1712945837,
  "iat": 1712945237,
  "azp": "kubeconfig-generator",
  "at_hash": "OamCo8c60Zdj3dVho3Km5oxA",
  "c_hash": "HT04XtwtlUhfHvm7zf19qsGw",
  "email": "maksim.nabokikh@palark.com",
  "email_verified": true,
  "groups": [
    "administrators",
    "developers"
  ],
  "name": "Maksim Nabokikh",
  "preferred_username": "maksim.nabokikh"
}
```

## Discovery

OpenID Connect servers have a discovery mechanism for OAuth2 endpoints, scopes
supported, and indications of various other OpenID Connect features.

```bash
$ curl http://127.0.0.1:5556/dex/.well-known/openid-configuration
{
  "issuer": "http://127.0.0.1:5556",
  "authorization_endpoint": "http://127.0.0.1:5556/auth",
  "token_endpoint": "http://127.0.0.1:5556/token",
  "jwks_uri": "http://127.0.0.1:5556/keys",
  "response_types_supported": [
    "code"
  ],
  "subject_types_supported": [
    "public"
  ],
  "id_token_signing_alg_values_supported": [
    "RS256"
  ],
  "scopes_supported": [
    "openid",
    "email",
    "profile"
  ]
}
```

Importantly, we've discovered the authorization endpoint, token endpoint, and
the location of the server's public keys. OAuth2 clients should be able to use
the token and auth endpoints immediately, while a JOSE library can be used to
parse the keys. The keys endpoint returns a [JSON Web Key](
https://tools.ietf.org/html/rfc7517) Set of public keys that will look
something like this:

```bash
$ curl http://127.0.0.1:5556/dex/keys
{
  "keys": [
    {
      "use": "sig",
      "kty": "RSA",
      "kid": "5d19a0fde5547960f4edaa1e1e8293e5534169ba",
      "alg": "RS256",
      "n": "5TAXCxkAQqHEqO0InP81z5F59PUzCe5ZNaDsD1SXzFe54BtXKn_V2a3K-BUNVliqMKhC2LByWLuI-A5ZlA5kXkbRFT05G0rusiM0rbkN2uvRmRCia4QlywE02xJKzeZV3KH6PldYqV_Jd06q1NV3WNqtcHN6MhnwRBfvkEIm7qWdPZ_mVK7vayfEnOCFRa7EZqr-U_X84T0-50wWkHTa0AfnyVvSMK1eKL-4yc26OWkmjh5ALfQFtnsz30Y2TOJdXtEfn35Y_882dNBDYBxtJV4PaSjXCxhiaIuBHp5uRS1INyMXCx2ve22ASNx_ERorv6BlXQoMDqaML2bSiN9N8Q",
      "e": "AQAB"
    }
  ]
}
```



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/connectors/oidc.md
================================================================================

---
title: "Authentication Through an OpenID Connect Provider"
linkTitle: "OpenID Connect"
description: ""
date: 2020-09-30
draft: false
toc: true
weight: 2050
---

## Overview

Dex is able to use another OpenID Connect provider as an authentication source. When logging in, dex will redirect to the upstream provider and perform the necessary OAuth2 flows to determine the end users email, username, etc. More details on the OpenID Connect protocol can be found in [_An overview of OpenID Connect_](../openid-connect.md).

Prominent examples of OpenID Connect providers include Google Accounts, Salesforce, and Azure AD v2 ([not v1][azure-ad-v1]).

## Configuration

```yaml
connectors:
- type: oidc
  id: google
  name: Google
  config:
    # Canonical URL of the provider, also used for configuration discovery.
    # This value MUST match the value returned in the provider config discovery.
    #
    # See: https://openid.net/specs/openid-connect-discovery-1_0.html#ProviderConfig
    issuer: https://accounts.google.com

    # Some offspec providers like Azure, Oracle IDCS have oidc discovery url
    # different from issuer url which causes issuerValidation to fail
    # issuerAlias provides a way to override the Issuer url
    # from the .well-known/openid-configuration issuer
    # issuerAlias: https://accounts.google.com

    # Connector config values starting with a "$" will read from the environment.
    clientID: $GOOGLE_CLIENT_ID
    clientSecret: $GOOGLE_CLIENT_SECRET

    # Dex's issuer URL + "/callback"
    redirectURI: http://127.0.0.1:5556/dex/callback


    # Some providers require passing client_secret via POST parameters instead
    # of basic auth, despite the OAuth2 RFC discouraging it. Many of these
    # cases are caught internally, but some may need to uncomment the
    # following field.
    #
    # basicAuthUnsupported: true
    
    # List of additional scopes to request in token response
    # Default is profile and email
    # Full list at https://dexidp.io/docs/custom-scopes-claims-clients/
    # scopes:
    #  - profile
    #  - email
    #  - groups

    # Some providers return claims without "email_verified", when they had no usage of emails verification in enrollment process
    # or if they are acting as a proxy for another IDP etc AWS Cognito with an upstream SAML IDP
    # This can be overridden with the below option
    # insecureSkipEmailVerified: true 

    # Groups claims (like the rest of oidc claims through dex) only refresh when the id token is refreshed
    # meaning the regular refresh flow doesn't update the groups claim. As such by default the oidc connector
    # doesn't allow groups claims. If you are okay with having potentially stale group claims you can use
    # this option to enable groups claims through the oidc connector on a per-connector basis.
    # This can be overridden with the below option
    # insecureEnableGroups: true

    # Filter users based on membership in the given groups. Authentication will be successful it the user is a member in a least
    # one of the specified groups.
    # allowedGroups:
    #  - <value>

    # When enabled, the OpenID Connector will query the UserInfo endpoint for additional claims. UserInfo claims
    # take priority over claims returned by the IDToken. This option should be used when the IDToken doesn't contain
    # all the claims requested.
    # https://openid.net/specs/openid-connect-core-1_0.html#UserInfo
    # getUserInfo: true

    # The set claim is used as user id.
    # Claims list at https://openid.net/specs/openid-connect-core-1_0.html#Claims
    # Default: sub
    # userIDKey: nickname

    # The set claim is used as user name.
    # Default: name
    # userNameKey: nickname

    # The acr_values variable specifies the Authentication Context Class Values within
    # the Authentication Request that the Authorization Server is being requested to process
    # from this Client.
    # acrValues: 
    #  - <value>
    #  - <value>

    # For offline_access, the prompt parameter is set by default to "prompt=consent". 
    # However this is not supported by all OIDC providers, some of them support different
    # value for prompt, like "prompt=login" or "prompt=none"
    # promptType: consent

    # Some providers return non-standard claims (eg. mail).
    # Use claimMapping to map those claims to standard claims:
    # https://openid.net/specs/openid-connect-core-1_0.html#Claims
    # claimMapping can only map a non-standard claim to a standard one if it's not returned in the id_token.
    claimMapping:
      # The set claim is used as preferred username.
      # Default: preferred_username
      # preferred_username: other_user_name

      # The set claim is used as email.
      # Default: email
      # email: mail

      # The set claim is used as groups.
      # Default: groups
      # groups: "cognito:groups"

    # claimModifications can change claims during the login
    claimModifications:
      # newGroupFromClaims allows to create a new group, based on other claims
      # they are concatenated using the delimiter.
      # Currently only string claims are supported, and other claims are skipped
      # The new group name is added to the groups claims, passed to the clients.
      # For this example, the resulting group would be: `example::organization::email`
      # newGroupFromClaims:
      #   - prefix: example
      #     delimiter: "::"
      #     clearDelimiter: false
      #     claims:
      #       - organization
      #       - email

      # filterGroupClaims allows to filter the groups, using a regex.
      # The regex must conform to the RE2 regex specification used in go regexp.
      # Groups added using the newGroupFromClaims modification, are not passed through the filterGroupClaims
      # filterGroupClaims:
      #   groupsFilter: "<REGEX>"

      # modifyGroupNames allows to add a prefix or suffix to all groups
      # Either one, or both fields can be specified, and they will be pre-/appended directly to the group-name as provided by the oidc issuer
      # The modifications are applied to all groups, not filtered by filterGroupClaims, and before Groups from newGroupFromClaims are created
      # For example, if the connector provides a group called "regular-users",
      # this modification would convert it to "example-prefix-regular-usersexample-suffix"
      # modifyGroupNames:
      #   prefix: example-prefix- # note the delimiter at the end
      #   suffix: example-suffix


    # overrideClaimMapping will be used to override the options defined in claimMappings.
    # i.e. if there are 'email' and `preferred_email` claims available, by default Dex will always use the `email` claim independent of the claimMapping.email.
    # This setting allows you to override the default behavior of Dex and enforce the mappings defined in `claimMapping`.
    overrideClaimMapping: false

    # The section to override options discovered automatically from
    # the providers' discovery URL (.well-known/openid-configuration).
    providerDiscoveryOverrides:
      # tokenURL provides a way to user overwrite the token URL
      # from the .well-known/openid-configuration 'token_endpoint'.
      # tokenURL: ""
      #
      # authURL provides a way to user overwrite the authorization URL
      # from the .well-known/openid-configuration 'authorization_endpoint'.   
      # authURL: ""
```

[oidc-doc]: openid-connect.md
[issue-863]: https://github.com/dexidp/dex/issues/863
[azure-ad-v1]: https://github.com/coreos/go-oidc/issues/133



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/development/oidc-certification.md
================================================================================

---
title: "OpenID Connect Provider Certification"
description: ""
date: 2020-09-30
draft: false
toc: true
weight: 1100
---

The OpenID Foundation provides a set of [conformance test profiles](https://openid.net/wordpress-content/uploads/2018/06/OpenID-Connect-Conformance-Profiles.pdf) that test both Relying Party (RP)
and OpenID Provider (OP) OpenID Connect implementations.
Upon submission of [results](https://openid.net/certification/submission/) and an affirmative response,
the affirmed OP will be listed as a [certified OP](https://openid.net/developers/certified/) on the OpenID Connect website
and allowed to use the [certification mark](https://openid.net/certification/mark/) according to the certification [terms and conditions](https://openid.net/wordpress-content/uploads/2015/03/OpenID-Certification-Terms-and-Conditions.pdf), section 3(d).

Further details about the certification are available on the [OpenID Connect website](https://openid.net/certification/instructions/).

## Basic OpenID Provider profile

Dex is an OP that strives to implement the [mandatory set](https://openid.net/specs/openid-connect-core-1_0.html#ServerMTI) of OpenID Connect features,
and can be tested against the Basic OpenID Provider profile ([profile outline](https://openid.net/wordpress-content/uploads/2018/06/OpenID-Connect-Conformance-Profiles.pdf), section 2.1.1).
These tests ensure that all features required by a [basic client](https://openid.net/specs/openid-connect-basic-1_0.html) work as expected.

Unfortunately, Dex currently does not fully comply with the Basic profile at the moment.

The progress for getting Dex certified can be tracked here: https://github.com/orgs/dexidp/projects/3/views/1

### Configuring Dex

The Basic OP test suite doesn't require extensive configuration from Dex.
The suite needs the following:

- A public issuer URL
- At least two separate clients (with redirect URIs pointing to `https://www.certification.openid.net/test/a/YOUR_ALIAS/callback`).

`YOUR_ALIAS` is an arbitrary string that MUST be unique to avoid interference with other test runs.

The easiest way to run a public Dex instance is running one locally and exposing it using a [tunnel](https://github.com/anderspitman/awesome-tunneling).

The following instructions use [tunnelto.dev](https://tunnelto.dev/).

Here is a minimal configuration example for running Dex:

```yaml
issuer: https://dex.tunnelto.dev/dex

storage:
  type: memory

web:
  http: 0.0.0.0:5556

oauth2:
  # Automate some clicking
  # Note: this might actually make some tests pass that otherwise wouldn't.
  skipApprovalScreen: true

connectors:
  # Note: this might actually make some tests pass that otherwise wouldn't.
  - type: mockCallback
    id: mock
    name: Example

# Basic OP test suite requires two clients.
staticClients:
  - id: first_client
    secret: 89d6205220381728e85c4cf5
    redirectURIs:
      - https://www.certification.openid.net/test/a/dex/callback
    name: First client

  - id: second_client
    secret: 51c612288018fd384b05d6ad
    redirectURIs:
      - https://www.certification.openid.net/test/a/dex/callback
    name: Second client
```

Save it in a file (eg. `config.yaml`) then launch Dex:

```shell
dex serve config.yaml
```

Then launch the tunnel:

```shell
tunnelto --subdomain dex --port 5556
```

You can verify Dex running by checking the discovery endpoint:

```shell
curl https://dex.tunnelto.dev/dex/.well-known/openid-configuration
```

### Running tests

1. Open https://www.certification.openid.net/ in your browser
1. Login with your Google or GitLab account
1. Click _Create a new test plan_
1. Select _OpenID Connect Core: Basic Certification Profile Authorization server test_ as the test plan
1. _Server metadata location_ should be **discovery**
1. _Client registration type_ should be **static_client**
1. Choose an alias (that you used in the redirect URIs above)
1. Enter the discovery URL
1. Enter the first client details in the _Client_ and _Second client_ sections
1. Enter the second client details in the _Client for client_secret_post_ section
1. Hit _Create test plan_
1. Run through each test case, following all instructions given by individual cases.
    * In order to pass certain cases, screenshots of OP responses might be required.

### Last results

Dex does not fully pass the Basic profile test suite yet. The following table contains the current state of test results.

| Test Name                                                                    | Status      | Result  |
|------------------------------------------------------------------------------|-------------|---------|
| oidcc-server                                                                 | FINISHED    | PASSED  |
| oidcc-response-type-missing                                                  | FINISHED    | PASSED  |
| oidcc-userinfo-get                                                           | FINISHED    | PASSED  |
| oidcc-userinfo-post-header                                                   | FINISHED    | PASSED  |
| oidcc-userinfo-post-body                                                     | FINISHED    | WARNING |
| oidcc-ensure-request-without-nonce-succeeds-for-code-flow                    | FINISHED    | PASSED  |
| oidcc-scope-profile                                                          | FINISHED    | WARNING |
| oidcc-scope-email                                                            | FINISHED    | WARNING |
| oidcc-scope-address                                                          | FINISHED    | SKIPPED |
| oidcc-scope-phone                                                            | FINISHED    | SKIPPED |
| oidcc-scope-all                                                              | FINISHED    | SKIPPED |
| oidcc-ensure-other-scope-order-succeeds                                      | FINISHED    | WARNING |
| oidcc-display-page                                                           | FINISHED    | PASSED  |
| oidcc-display-popup                                                          | FINISHED    | PASSED  |
| oidcc-prompt-login                                                           | INTERRUPTED | UNKNOWN |
| oidcc-prompt-none-not-logged-in                                              | FINISHED    | FAILED  |
| oidcc-prompt-none-logged-in                                                  | FINISHED    | PASSED  |
| oidcc-max-age-1                                                              | INTERRUPTED | FAILED  |
| oidcc-max-age-10000                                                          | FINISHED    | FAILED  |
| oidcc-ensure-request-with-unknown-parameter-succeeds                         | FINISHED    | PASSED  |
| oidcc-id-token-hint                                                          | FINISHED    | PASSED  |
| oidcc-login-hint                                                             | FINISHED    | PASSED  |
| oidcc-ui-locales                                                             | FINISHED    | PASSED  |
| oidcc-claims-locales                                                         | FINISHED    | PASSED  |
| oidcc-ensure-request-with-acr-values-succeeds                                | FINISHED    | WARNING |
| oidcc-codereuse                                                              | FINISHED    | PASSED  |
| oidcc-codereuse-30seconds                                                    | FINISHED    | WARNING |
| oidcc-ensure-registered-redirect-uri                                         | INTERRUPTED | REVIEW  |
| oidcc-server-client-secret-post                                              | FINISHED    | PASSED  |
| oidcc-unsigned-request-object-supported-correctly-or-rejected-as-unsupported | INTERRUPTED | UNKNOWN |
| oidcc-claims-essential                                                       | FINISHED    | WARNING |
| oidcc-ensure-request-object-with-redirect-uri                                | INTERRUPTED | UNKNOWN |
| oidcc-refresh-token                                                          | INTERRUPTED | FAILED  |
| oidcc-ensure-request-with-valid-pkce-succeeds                                | FINISHED    | PASSED  |

> TODO: find a better place for test results.



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/connectors/authproxy.md
================================================================================

---
title: "Authenticating Proxy"
linkTitle: "AuthProxy"
description: ""
date: 2020-09-30
draft: false
toc: true
weight: 2090
---

NOTE: This connector is experimental and may change in the future.

## Overview

The `authproxy` connector returns identities based on authentication which your
front-end web server performs. Dex consumes the `X-Remote-User` header set by
the proxy, which is then used as the user's email address.

It also consumes the `X-Remote-Group` header to use as the user's group.

Header's names can be configured via the `userHeader` and `groupHeader` config.

Additional static groups can also be defined in the connector's configuration.

__The proxy MUST remove any `X-Remote-*` headers set by the client, for any URL
path, before the request is forwarded to dex.__

The connector does not support refresh tokens.

## Configuration

The `authproxy` connector is used by proxies to implement login strategies not
supported by dex. For example, a proxy could handle a different OAuth2 strategy
such as Slack:

```yaml
connectors:
# Slack login implemented by an authenticating proxy, not by dex.
- type: authproxy
  id: slack
  name: Slack 
```

The proxy only needs to authenticate the user when they attempt to visit the
callback URL path:

```
( dex issuer URL )/callback/( connector id )?( url query )
```

For example, if dex is running at `https://auth.example.com/dex` and the connector
ID is `slack`, the callback URL would look like:

```
https://auth.example.com/dex/callback/slack?state=xdg3z6quhrhwaueo5iysvliqf
``` 

The proxy should login the user then return them to the exact URL (including the
query), setting `X-Remote-User` to the user's email before proxying the request
to dex.

## Configuration example - Apache 2

The following is an example config file that can be used by the external
connector to authenticate a user.

```yaml
connectors:
- type: authproxy
  id: myBasicAuth
  name: HTTP Basic Auth
  config:
    userHeader: X-Forwarded-User # default is X-Remote-User
    groupHeader: X-Forwarded-Group # default is X-Remote-Group
    staticGroups:
    - default
```

The authproxy connector assumes that you configured your front-end web server
such that it performs authentication for the `/dex/callback/myBasicAuth`
location and provides the result in the HTTP headers.

In this example, the configured headers are `X-Forwarded-User` for the user's mail
and `X-Forwarded-Group` for the user's group.
Dex authproxy connector will return a list of groups containing both
configured `staticGroups` and return the group header.

The following configuration will work for Apache 2.4.10+:

```bash
    ProxyPass "http://localhost:5556/dex/"
    ProxyPassReverse "http://localhost:5556/dex/"

    # Strip the X-Remote-User header from all requests except for the ones
    # where we override it.
    RequestHeader unset X-Remote-User

```

## Full Apache2 setup

After installing your Linux distribution’s Apache2 package, place the following
virtual host configuration in e.g. `/etc/apache2/sites-available/sso.conf`:

```bash

```

Then, enable it using `a2ensite sso.conf`, followed by a restart of Apache2.



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/connectors/ldap.md
================================================================================

---
title: "Authentication Through LDAP"
linkTitle: "LDAP"
description: ""
date: 2020-09-30
draft: false
toc: true
weight: 2010
---

## Overview

The LDAP connector allows email/password based authentication, backed by a LDAP directory.

The connector executes two primary queries:

1. Finding the user based on the end user's credentials.
2. Searching for groups using the user entry.

## Getting started

The dex repo contains a basic LDAP setup using [OpenLDAP][openldap].

First start the LDAP server using docker-compose. This will run the OpenLDAP daemon in a Docker container, and seed it with an initial set of users.

```bash
cd examples/ldap
docker-compose up
```

This container is expected to print several warning messages which are normal. Once the server is up, run dex in another terminal.

```bash
./bin/dex serve examples/ldap/config-ldap.yaml
```

Then run the OAuth client in another terminal.

```bash
./bin/example-app
```

Go to [http://localhost:5555](http://localhost:5555), login and enter the username and password of the LDAP user: `janedoe@example.com`/`foo`. Add the "groups" scope as part of the initial redirect to add group information from the LDAP server.

## Security considerations

Dex attempts to bind with the backing LDAP server using the end user's _plain text password_. Though some LDAP implementations allow passing hashed passwords, dex doesn't support hashing and instead _strongly recommends that all administrators just use TLS_. This can often be achieved by using port 636 instead of 389, and administrators that choose 389 are actively leaking passwords.

Dex currently allows insecure connections because the project is still verifying that dex works with the wide variety of LDAP implementations. However, dex may remove this transport option, and _users who configure LDAP login using 389 are not covered by any compatibility guarantees with future releases._

## Configuration

User entries are expected to have an email attribute (configurable through `emailAttr`), and a display name attribute (configurable through `nameAttr`). `*Attr` attributes could be set to "DN" in situations where it is needed but not available elsewhere, and if "DN" attribute does not exist in the record.

For the purposes of configuring this connector, "DN" is case-sensitive and should always be capitalised.

The following is an example config file that can be used by the LDAP connector to authenticate a user.

```yaml
connectors:
- type: ldap
  # Required field for connector id.
  id: ldap
  # Required field for connector name.
  name: LDAP
  config:
    # Host and optional port of the LDAP server in the form "host:port".
    # If the port is not supplied, it will be guessed based on "insecureNoSSL",
    # and "startTLS" flags. 389 for insecure or StartTLS connections, 636
    # otherwise.
    host: ldap.example.com:636

    # Following field is required if the LDAP host is not using TLS (port 389).
    # Because this option inherently leaks passwords to anyone on the same network
    # as dex, THIS OPTION MAY BE REMOVED WITHOUT WARNING IN A FUTURE RELEASE.
    #
    # insecureNoSSL: true

    # If a custom certificate isn't provide, this option can be used to turn on
    # TLS certificate checks. As noted, it is insecure and shouldn't be used outside
    # of explorative phases.
    #
    # insecureSkipVerify: true

    # When connecting to the server, connect using the ldap:// protocol then issue
    # a StartTLS command. If unspecified, connections will use the ldaps:// protocol
    #
    # startTLS: true

    # Path to a trusted root certificate file. Default: use the host's root CA.
    rootCA: /etc/dex/ldap.ca

    # A raw certificate file can also be provided inline.
    # rootCAData: ( base64 encoded PEM file )

    # The DN and password for an application service account. The connector uses
    # these credentials to search for users and groups. Not required if the LDAP
    # server provides access for anonymous auth.
    # Please note that if the bind password contains a `$`, it has to be saved in an
    # environment variable which should be given as the value to `bindPW`.
    bindDN: uid=serviceaccount,cn=users,dc=example,dc=com
    bindPW: password

    # The attribute to display in the provided password prompt. If unset, will
    # display "Username"
    usernamePrompt: SSO Username

    # User search maps a username and password entered by a user to a LDAP entry.
    userSearch:
      # BaseDN to start the search from. It will translate to the query
      # "(&(objectClass=person)(uid=<username>))".
      baseDN: cn=users,dc=example,dc=com
      # Optional filter to apply when searching the directory.
      filter: "(objectClass=person)"

      # username attribute used for comparing user entries. This will be translated
      # and combined with the other filter as "(<attr>=<username>)".
      username: uid
      # The following three fields are direct mappings of attributes on the user entry.
      # String representation of the user.
      idAttr: uid
      # Required. Attribute to map to Email.
      emailAttr: mail
      # Maps to display name of users. No default value.
      nameAttr: name
      # Maps to preferred username of users. No default value.
      preferredUsernameAttr: uid

    # Group search queries for groups given a user entry.
    groupSearch:
      # BaseDN to start the search from. It will translate to the query
      # "(&(objectClass=group)(member=<user uid>))".
      baseDN: cn=groups,dc=freeipa,dc=example,dc=com
      # Optional filter to apply when searching the directory.
      filter: "(objectClass=group)"

      # Following list contains field pairs that are used to match a user to a group. It adds an additional
      # requirement to the filter that an attribute in the group must match the user's
      # attribute value.
      userMatchers:
      - userAttr: uid
        groupAttr: member

      # Represents group name.
      nameAttr: name
```

The LDAP connector first initializes a connection to the LDAP directory using the `bindDN` and `bindPW`. It then tries to search for the given `username` and bind as that user to verify their password.
Searches that return multiple entries are considered ambiguous and will return an error.

## Example: Mapping a schema to a search config

Writing a search configuration often involves mapping an existing LDAP schema to the various options dex provides. To query an existing LDAP schema install the OpenLDAP tool `ldapsearch`. For `rpm` based distros run:

```bash
sudo dnf install openldap-clients
```

For `apt-get`:

```bash
sudo apt-get install ldap-utils
```

For smaller user directories it may be practical to dump the entire contents and search by hand.

```bash
ldapsearch -x -H ldap://ldap.example.org -b 'dc=example,dc=org' | less
```

First, find a user entry. User entries declare users who can login to LDAP connector using username and password.

```bash
dn: uid=jdoe,cn=users,cn=compat,dc=example,dc=org
cn: Jane Doe
objectClass: posixAccount
objectClass: ipaOverrideTarget
objectClass: top
gidNumber: 200015
gecos: Jane Doe
uidNumber: 200015
loginShell: /bin/bash
homeDirectory: /home/jdoe
mail: jane.doe@example.com
uid: janedoe
```

Compose a user search which returns this user.

```yaml
userSearch:
  # The directory directly above the user entry.
  baseDN: cn=users,cn=compat,dc=example,dc=org
  filter: "(objectClass=posixAccount)"

  # Expect user to enter "janedoe" when logging in.
  username: uid

  # Use the full DN as an ID.
  idAttr: DN

  # When an email address is not available, use another value unique to the user, like uid.
  emailAttr: mail
  nameAttr: gecos
```

Second, find a group entry.

```bash
dn: cn=developers,cn=groups,cn=compat,dc=example,dc=org
memberUid: janedoe
memberUid: johndoe
gidNumber: 200115
objectClass: posixGroup
objectClass: ipaOverrideTarget
objectClass: top
cn: developers
```

Group searches must match a user attribute to a group attribute. In this example, the search returns users whose uid is found in the group's list of memberUid attributes.

```yaml
groupSearch:
  # The directory directly above the group entry.
  baseDN: cn=groups,cn=compat,dc=example,dc=org
  filter: "(objectClass=posixGroup)"

  # The group search needs to match the "uid" attribute on
  # the user with the "memberUid" attribute on the group.
  userMatchers:
  - userAttr: uid
    groupAttr: memberUid

  # Unique name of the group.
  nameAttr: cn
```
To extract group specific information the `DN` can be used in the `userAttr` field.

```bash
# Top level object example.coma in LDIF file.
dn: dc=example,dc=com
objectClass: top
objectClass: dcObject
objectClass: organization
dc: example
```

The following is an example of a group query would match any entry with member=<user DN>:

```yaml
groupSearch:
  # BaseDN to start the search from. It will translate to the query
  # "(&(objectClass=group)(member=<user DN>))".
  baseDN: cn=groups,cn=compat,dc=example,dc=com
  # Optional filter to apply when searching the directory.
  filter: "(objectClass=group)"

  userMatchers:
  - userAttr: DN # Use "DN" here not "uid"
    groupAttr: member

  nameAttr: name
```

There are cases when different types (objectClass) of groups use different attributes to keep a list of members. Below is an example of group query for such case:

```yaml
groupSearch:
  baseDN: cn=groups,cn=compat,dc=example,dc=com
  # Optional filter to search for different group types
  filter: "(|(objectClass=posixGroup)(objectClass=group))"

  # Use multiple user matchers so Dex will know which attribute names should be used to search for group members
  userMatchers:
  - userAttr: uid
    groupAttr: memberUid
  - userAttr: DN
    groupAttr: member

  nameAttr: name
```

## Example: Searching a FreeIPA server with groups

The following configuration will allow the LDAP connector to search a FreeIPA directory using an LDAP filter.

```yaml
connectors:
- type: ldap
  id: ldap
  name: LDAP
  config:
    # host and port of the LDAP server in form "host:port".
    host: freeipa.example.com:636
    # freeIPA server's CA
    rootCA: ca.crt
    userSearch:
      # Would translate to the query "(&(objectClass=posixAccount)(uid=<username>))".
      baseDN: cn=users,dc=freeipa,dc=example,dc=com
      filter: "(objectClass=posixAccount)"
      username: uid
      idAttr: uid
      # Required. Attribute to map to Email.
      emailAttr: mail
      # Entity attribute to map to display name of users.
    groupSearch:
      # Would translate to the query "(&(objectClass=group)(member=<user uid>))".
      baseDN: cn=groups,dc=freeipa,dc=example,dc=com
      filter: "(objectClass=group)"
      userMatchers:
      - userAttr: uid
        groupAttr: member
      nameAttr: name
```

If the search finds an entry, it will attempt to use the provided password to bind as that user entry.

[openldap]: https://www.openldap.org/

## Example: Searching a Active Directory server with groups

The following configuration will allow the LDAP connector to search a Active Directory using an LDAP filter.

```yaml
connectors:
- type: ldap
  name: ActiveDirectory
  id: ad
  config:
    host: ad.example.com:636

    insecureNoSSL: false
    insecureSkipVerify: true

    bindDN: cn=Administrator,cn=users,dc=example,dc=com
    bindPW: admin0!

    usernamePrompt: Email Address

    userSearch:
      baseDN: cn=Users,dc=example,dc=com
      filter: "(objectClass=person)"
      username: userPrincipalName
      idAttr: DN
      emailAttr: userPrincipalName
      nameAttr: cn

    groupSearch:
      baseDN: cn=Users,dc=example,dc=com
      filter: "(objectClass=group)"
      userMatchers:
      - userAttr: DN
        groupAttr: member
      nameAttr: cn
```

## Example: Searching a FreeIPA server for nested groups 

Some LDAP schemas support group nesting, where groups can contain other groups. Dex supports resolving these indirect group memberships using the `recursionGroupAttr` attribute within the `groupSearch.userMatchers` block. By defining this attribute, recursive group lookup will be enabled. 

You might want to use this if, for example, John is a member of the group `seniorAdmins`, and `seniorAdmins` is itself a member of the group `admins`. With recursive search enabled, John will be treated as a member of both `seniorAdmins` and `admins`, even though he’s only directly assigned to `seniorAdmins`.

The following is a `groupsearch` configuration that enables this functionality. 

```yaml
groupSearch:
  baseDN: cn=groups,dc=freeipa,dc=example,dc=com
  filter: "(objectClass=group)"
  userMatchers:
  - userAttr: uid
    groupAttr: member
    recursionGroupAttr: member
  nameAttr: name
```

In this example:

1. Dex looks for groups where the `member` attribute matches the user's `uid`.
2. Groups can also list other groups in the same `member` attribute, allowing nesting.
3. By specifying `recursionGroupAttr`, Dex will recursively search for parent groups that contain the matched groups. This attribute tells Dex which field to follow when tracing nested group links.
4. If `recursionGroupAttr` is not set, Dex performs only a single-level group lookup.

Dex includes built-in cycle detection to prevent infinite loops if group references form a cycle.



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/connectors/saml.md
================================================================================

---
title: "Authentication through SAML 2.0"
linkTitle: "SAML 2.0"
description: ""
date: 2020-09-30
draft: false
toc: true
weight: 2030
---

## WARNING

The SAML connector is unmaintained, likely vulnerable to authentication bypass vulnerabilities, and is under consideration for deprecation (see [#1884](https://github.com/dexidp/dex/discussions/1884)). Please consider switching to OpenID Connect, OAuth2, or LDAP for identity providers that support these protocols. If you have domain expertise in SAML/XMLDSig and would like to volunteer to maintain the connector please comment on the discussion.

## Overview

The SAML provider allows authentication through the SAML 2.0 HTTP POST binding. The connector maps attribute values in the SAML assertion to user info, such as username, email, and groups.

The connector uses the value of the `NameID` element as the user's unique identifier which dex assumes is both unique and never changes. Use the `nameIDPolicyFormat` to ensure this is set to a value which satisfies these requirements.

Unlike some clients which will process unprompted AuthnResponses, dex must send the initial AuthnRequest and validates the response's InResponseTo value.

## Caveats

__The connector doesn't support refresh tokens__ since the SAML 2.0 protocol doesn't provide a way to requery a provider without interaction. If the "offline_access" scope is requested, it will be ignored.

The connector doesn't support signed AuthnRequests or encrypted attributes.

## Group Filtering

The SAML Connector supports providing a whitelist of SAML Groups to filter access based on, and when the `groupsattr` is set with a scope including groups, Dex will check for membership based on configured groups in the `allowedGroups` config setting for the SAML connector.

If `filterGroups` is set to true, any groups _not_ part of `allowedGroups` will be excluded.

## Configuration

```yaml
connectors:
- type: saml
  # Required field for connector id.
  id: saml
  # Required field for connector name.
  name: SAML
  config:
    # SSO URL used for POST value.
    ssoURL: https://saml.example.com/sso

    # CA to use when validating the signature of the SAML response.
    ca: /path/to/ca.pem

    # Dex's callback URL.
    #
    # If the response assertion status value contains a Destination element, it
    # must match this value exactly.
    #
    # This is also used as the expected audience for AudienceRestriction elements
    # if entityIssuer isn't specified.
    redirectURI: https://dex.example.com/callback

    # Name of attributes in the returned assertions to map to ID token claims.
    usernameAttr: name
    emailAttr: email
    groupsAttr: groups # optional

    # List of groups to filter access based on membership
    # allowedGroups
    #   - Admins

    # CA's can also be provided inline as a base64'd blob.
    #
    # caData: ( RAW base64'd PEM encoded CA )

    # To skip signature validation, uncomment the following field. This should
    # only be used during testing and may be removed in the future.
    #
    # insecureSkipSignatureValidation: true

    # Optional: Manually specify dex's Issuer value.
    #
    # When provided dex will include this as the Issuer value during AuthnRequest.
    # It will also override the redirectURI as the required audience when evaluating
    # AudienceRestriction elements in the response.
    entityIssuer: https://dex.example.com/callback

    # Optional: Issuer value expected in the SAML response.
    ssoIssuer: https://saml.example.com/sso

    # Optional: Delimiter for splitting groups returned as a single string.
    #
    # By default, multiple groups are assumed to be represented as multiple
    # attributes with the same name.
    #
    # If "groupsDelim" is provided groups are assumed to be represented as a
    # single attribute and the delimiter is used to split the attribute's value
    # into multiple groups.
    groupsDelim: ", "

    # Optional: Requested format of the NameID.
    #
    # The NameID value is is mapped to the user ID of the user. This can be an
    # abbreviated form of the full URI with just the last component. For example,
    # if this value is set to "emailAddress" the format will resolve to:
    #
    #     urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress
    #
    # If no value is specified, this value defaults to:
    #
    #     urn:oasis:names:tc:SAML:2.0:nameid-format:persistent
    #
    nameIDPolicyFormat: persistent
```

A minimal working configuration might look like:

```yaml
connectors:
- type: saml
  id: okta
  name: Okta
  config:
    ssoURL: https://dev-111102.oktapreview.com/app/foo/exk91cb99lKkKSYoy0h7/sso/saml
    ca: /etc/dex/saml-ca.pem
    redirectURI: http://127.0.0.1:5556/dex/callback
    usernameAttr: name
    emailAttr: email
    groupsAttr: groups
```



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/configuration/custom-scopes-claims-clients.md
================================================================================

---
title: "Scopes and Claims"
description: "Custom Scopes, Claims and Client Features"
date: 2020-09-30
draft: false
toc: true
weight: 1040
---

This document describes the set of OAuth2 and OpenID Connect features implemented by dex.

## Scopes

The following is the exhaustive list of scopes supported by dex:

| Name | Description |
| ---- | ------------|
| `openid` | Required scope for all login requests. |
| `email` | ID token claims should include the end user's email and if that email was verified by an upstream provider. |
| `profile` | ID token claims should include the username of the end user. |
| `groups` | ID token claims should include a list of groups the end user is a member of. |
| `federated:id` | ID token claims should include information from the ID provider. The token will contain the connector ID and the user ID assigned at the provider. |
| `offline_access` | Token response should include a refresh token. Doesn't work in combinations with some connectors, notability the [SAML connector](/docs/connectors/saml/) ignores this scope. |
| `audience:server:client_id:( client-id )` | Dynamic scope indicating that the ID token should be issued on behalf of another client. See the _"Cross-client trust and authorized party"_ section below. |

## Custom claims

Beyond the [required OpenID Connect claims][core-claims], and a handful of [standard claims][standard-claims], dex implements the following non-standard claims.

| Name | Description |
| ---- | ------------|
| `groups` | A list of strings representing the groups a user is a member of. |
| `federated_claims` | The connector ID and the user ID assigned to the user at the provider. |
| `email` | The email of the user. |
| `email_verified` | If the upstream provider has verified the email. |
| `name` | User's display name. |
| `preferred_username` | Shorthand name by which the End-User wishes to be referred to. |


The `federated_claims` claim has the following format:

```json
"federated_claims": {
  "connector_id": "github",
  "user_id": "110272483197731336751"
}
```

## Cross-client trust and authorized party

Dex has the ability to issue ID tokens to clients on behalf of other clients. In OpenID Connect terms, this means the ID token's `aud` (audience) claim being a different client ID than the client that performed the login.

For example, this feature could be used to allow a web app to generate an ID token on behalf of a command line tool:

```yaml
staticClients:
- id: web-app
  redirectURIs:
  - 'https://web-app.example.com/callback'
  name: 'Web app'
  secret: web-app-secret
  # It is also possible to fetch the secret from an injected environment variable
  # secretEnv: YOUR_INJECTED_SECRET

- id: cli-app
  redirectURIs:
  - 'https://cli-app.example.com/callback'
  name: 'Command line tool'
  secret: cli-app-secret
  # The command line tool lets the web app issue ID tokens on its behalf.
  trustedPeers:
  - web-app
```

Note that the command line tool must explicitly trust the web app using the `trustedPeers` field. The web app can then use the following scope to request an ID token that's issued for the command line tool.

```
audience:server:client_id:cli-app
```

The ID token claims will then include the following audience and authorized party:

```json
{
    "aud": "cli-app",
    "azp": "web-app",
    "email": "foo@bar.com",
    // other claims...
}
```

## Public clients

Public clients are inspired by Google's [_"Installed Applications"_][installed-apps] and are meant to impose restrictions on applications that don't intend to keep their client secret private. Clients can be declared as public using the `public` config option.

```yaml
staticClients:
- id: cli-app
  public: true
  name: 'CLI app'
  redirectURIs:
  - ...
```

If no `redirectURIs` are specified, public clients only support redirects that begin with "http://localhost" or a special "out-of-browser" URL "urn:ietf:wg:oauth:2.0:oob".
The latter triggers dex to display the OAuth2 code in the browser, prompting the end user to manually copy it to their app. It's the client's responsibility to either create a screen or a prompt to receive the code, then perform a code exchange for a token response.

When using the "out-of-browser" flow, an ID Token nonce is strongly recommended.

[core-claims]: https://openid.net/specs/openid-connect-core-1_0.html#IDToken
[standard-claims]: https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims
[installed-apps]: https://developers.google.com/api-client-library/python/auth/installed-app



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/connectors/atlassian-crowd.md
================================================================================

---
title: "Authentication Through Atlassian Crowd"
linkTitle: "Atlassian Crowd"
description: ""
date: 2020-09-30
draft: false
toc: true
weight: 2120
---

## Overview

Atlassian Crowd is a centralized identity management solution providing single sign-on and user identity.

Current connector uses request to [Crowd REST API](https://developer.atlassian.com/server/crowd/json-requests-and-responses/) endpoints:
* `/user` - to get user-info
* `/session` - to authenticate the user

Offline Access scope support provided with a new request to user authentication and user info endpoints. 

## Configuration
To start using the Atlassian Crowd connector, firstly you need to register an application in your Crowd like specified in the [docs](https://confluence.atlassian.com/crowd/adding-an-application-18579591.html).

The following is an example of a configuration for dex `examples/config-dev.yaml`:

```yaml
connectors:
- type: atlassian-crowd
  # Required field for connector id.
  id: crowd
  # Required field for connector name.
  name: Crowd
  config:
    # Required field to connect to Crowd.
    baseURL: https://crowd.example.com/crowd
    # Credentials can be string literals or pulled from the environment.
    clientID: $ATLASSIAN_CROWD_APPLICATION_ID
    clientSecret: $ATLASSIAN_CROWD_CLIENT_SECRET
    # Optional groups whitelist, communicated through the "groups" scope.
    # If `groups` is omitted, all of the user's Crowd groups are returned when the groups scope is present.
    # If `groups` is provided, this acts as a whitelist - only the user's Crowd groups that are in the configured `groups` below will go into the groups claim.  
    # Conversely, if the user is not in any of the configured `groups`, the user will not be authenticated.
    groups:
    - my-group
    # Prompt for username field.
    usernamePrompt: Login
    # Optionally set preferred_username claim.
    # If `preferredUsernameField` is omitted or contains an invalid option, the `preferred_username` claim will be empty.
    # If `preferredUsernameField` is set, the `preferred_username` claim will be set to the chosen Crowd user attribute value.
    # Possible choices are: "key", "name", "email"
    preferredUsernameField: name
```



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/connectors/_index.md
================================================================================

---
title: "Connectors"
description: "Documentation about configuration of Dex connectors"
date: 2020-01-07T14:59:38+01:00
draft: false
toc: true
weight: 2000
---

When a user logs in through Dex, the user's identity is usually stored in another user-management system: a LDAP directory, a GitHub org, etc. Dex acts as a shim between a client app and the upstream identity provider. The client only needs to understand OpenID Connect to query Dex, while Dex implements an array of protocols for querying other user-management systems.

![](/img/dex-flow.png)

A "connector" is a strategy used by Dex for authenticating a user against another identity provider. Dex implements connectors that target specific platforms such as GitHub, LinkedIn, and Microsoft as well as established protocols like LDAP and SAML.

Depending on the connectors limitations in protocols can prevent Dex from issuing [refresh tokens][scopes] or returning [group membership][scopes] claims. For example, because SAML doesn't provide a non-interactive way to refresh assertions, if a user logs in through the SAML connector Dex won't issue a refresh token to its client. Refresh token support is required for clients that require offline access, such as `kubectl`.

Dex implements the following connectors:

| Name | supports refresh tokens | supports groups claim | supports preferred_username claim | status | notes |
| ---- | ----------------------- | --------------------- | --------------------------------- | ------ | ----- |
| [LDAP](/docs/connectors/ldap/) | yes | yes | yes | stable | |
| [GitHub](/docs/connectors/github/) | yes | yes | yes | stable | |
| [SAML 2.0](/docs/connectors/saml/) | no | yes | no | stable |
| [GitLab](/docs/connectors/gitlab/) | yes | yes | yes | beta | |
| [OpenID Connect](/docs/connectors/oidc/) | yes | yes | yes | beta | Includes Salesforce, Azure, etc. |
| [OAuth 2.0](/docs/connectors/oauth/) | no | yes | yes | alpha |
| [Google](/docs/connectors/google/) | yes | yes | yes | alpha | |
| [LinkedIn](/docs/connectors/linkedin/) | yes | no | no | beta | |
| [Microsoft](/docs/connectors/microsoft/) | yes | yes | no | beta | |
| [AuthProxy](/docs/connectors/authproxy/) | no | no | no | alpha | Authentication proxies such as Apache2 mod_auth, etc. |
| [Bitbucket Cloud](/docs/connectors/bitbucketcloud/) | yes | yes | no | alpha | |
| [OpenShift](/docs/connectors/openshift/) | no | yes | no | stable | |
| [Atlassian Crowd](/docs/connectors/atlassian-crowd/) | yes | yes | yes * | beta | preferred_username claim must be configured through config |
| [Gitea](/docs/connectors/gitea/) | yes | no | yes | alpha | |
| [OpenStack Keystone](/docs/connectors/keystone/) | yes | yes | no | alpha |  |


Stable, beta, and alpha are defined as:

* Stable: well tested, in active use, and will not change in backward incompatible ways.
* Beta: tested and unlikely to change in backward incompatible ways.
* Alpha: may be untested by core maintainers and is subject to change in backward incompatible ways.

All changes or deprecations of connector features will be announced in the [release notes.][release-notes]

[scopes]: /docs/configuration/custom-scopes-claims-clients/#scopes
[release-notes]: https://github.com/dexidp/dex/releases



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/connectors/github.md
================================================================================

---
title: "Authentication Through GitHub"
linkTitle: "GitHub"
description: ""
date: 2020-09-30
draft: false
toc: true
weight: 2020
---

## Overview

One of the login options for dex uses the GitHub OAuth2 flow to identify the end user through their GitHub account.

When a client redeems a refresh token through dex, dex will re-query GitHub to update user information in the ID Token. To do this, __dex stores a readonly GitHub access token in its backing datastore.__ Users that reject dex's access through GitHub will also revoke all dex clients which authenticated them through GitHub.

## Caveats

* A user must explicitly [request][github-request-org-access] an [organization][github-orgs] give dex [resource access][github-approve-org-access]. Dex will not have the correct permissions to determine if the user is in that organization otherwise, and the user will not be able to log in. This request mechanism is a feature of the GitHub API.

## Configuration

Register a new application with [GitHub][github-oauth2] ensuring the callback URL is `(dex issuer)/callback`. For example if dex is listening at the non-root path `https://auth.example.com/dex` the callback would be `https://auth.example.com/dex/callback`.

The following is an example of a configuration for `examples/config-dev.yaml`:

```yaml
connectors:
- type: github
  # Required field for connector id.
  id: github
  # Required field for connector name.
  name: GitHub
  config:
    # Credentials can be string literals or pulled from the environment.
    clientID: $GITHUB_CLIENT_ID
    clientSecret: $GITHUB_CLIENT_SECRET
    redirectURI: http://127.0.0.1:5556/dex/callback

    # Legacy 'org' field.
    #  - A user MUST be a member of the following org to authenticate with dex.
    #  - Both 'org' and 'orgs' can NOT be used simultaneously.
    #org: my-organization

    # List of org and team names.
    #  - If specified, a user MUST be a member of at least ONE of these orgs
    #    and teams (if set) to authenticate with dex.
    #  - Dex queries the following organizations for group information if the
    #    "groups" scope is requested. Group claims are formatted as "(org):(team)".
    #    For example if a user is part of the "engineering" team of the "coreos" org,
    #    the group claim would include "coreos:engineering".
    #  - If teams are specified, dex only returns group claims for those teams.
    orgs:
    - name: my-organization
    - name: my-organization-with-teams
      teams:
      - red-team
      - blue-team

    # Flag which indicates that all the user's orgs and teams should be loaded.
    # Only works if neither 'org' nor 'orgs' are specified in the config.
    loadAllGroups: false

    # How the team names are formatted.
    #  - Options: 'name' (default), 'slug', 'both'.
    #  - Examples:
    #    - 'name': 'acme:Site Reliability Engineers'
    #    - 'slug': 'acme:site-reliability-engineers'
    #    - 'both': 'acme:Site Reliability Engineers', 'acme:site-reliability-engineers'
    teamNameField: slug

    # Flag which will switch from using the internal GitHub id to the users handle (@mention) as the user id.
    # It is possible for a user to change their own username, but it is very rare for them to do so
    useLoginAsID: false

    # A preferred email domain to use when returning the user's email.
    #  - If the user has a PUBLIC email, it is ALWAYS returned in the email claim,
    #    so this field would have NO effect (this may change in the future).
    #  - By default, if the user does NOT have a public email, their primary email is returned.
    #  - When 'preferredEmailDomain' is set, the first email matching this domain is returned,
    #    we fall back to the primary email if no match is found.
    #  - To allow multiple subdomains, you may specify a wildcard like "*.example.com"
    #    which will match "aaaa.example.com" and "bbbb.example.com", but NOT "example.com".
    #  - To return the user's no-reply email, set this field to "users.noreply.github.com",
    #    this is a mostly static email that GitHub assigns to the user. These emails
    #    are formatted like 'ID+USERNAME@users.noreply.github.com' for newer accounts
    #    and 'USERNAME@users.noreply.github.com' for older accounts.
    #preferredEmailDomain: "example.com"
```

## GitHub Enterprise

Users can use their GitHub Enterprise account to login to dex. The following configuration can be used to enable a GitHub Enterprise connector on dex:

```yaml
connectors:
- type: github
  # Required field for connector id.
  id: github
  # Required field for connector name.
  name: GitHub
  config:
    # Required fields. Dex must be pre-registered with GitHub Enterprise
    # to get the following values.
    # Credentials can be string literals or pulled from the environment.
    clientID: $GITHUB_CLIENT_ID
    clientSecret: $GITHUB_CLIENT_SECRET
    redirectURI: http://127.0.0.1:5556/dex/callback

    # List of org and team names.
    #  - If specified, a user MUST be a member of at least ONE of these orgs
    #    and teams (if set) to authenticate with dex.
    #  - Dex queries the following organizations for group information if the
    #    "groups" scope is requested. Group claims are formatted as "(org):(team)".
    #    For example if a user is part of the "engineering" team of the "coreos" org,
    #    the group claim would include "coreos:engineering".
    #  - If teams are specified, dex only returns group claims for those teams.
    orgs:
    - name: my-organization
    - name: my-organization-with-teams
      teams:
      - red-team
      - blue-team

    # Flag which indicates that all the user's orgs and teams should be loaded.
    # Only works if neither 'org' nor 'orgs' are specified in the config.
    loadAllGroups: false

    # How the team names are formatted
    #  - Options: 'name' (default), 'slug', 'both'.
    #  - Examples:
    #    - 'name': 'acme:Site Reliability Engineers'
    #    - 'slug': 'acme:site-reliability-engineers'
    #    - 'both': 'acme:Site Reliability Engineers', 'acme:site-reliability-engineers'
    teamNameField: slug

    # Required ONLY for GitHub Enterprise.
    # This is the Hostname of the GitHub Enterprise account listed on the
    # management console. Ensure this domain is routable on your network.
    hostName: git.example.com

    # ONLY for GitHub Enterprise. Optional field.
    # Used to support self-signed or untrusted CA root certificates.
    rootCA: /etc/dex/ca.crt
```

### Generate TLS assets

Running Dex with HTTPS enabled requires a valid SSL certificate, and the API server needs to trust the certificate of the signing CA using the `--oidc-ca-file` flag.

For our example use case, the TLS assets can be created using the following command:

```bash
$ ./examples/k8s/gencert.sh
```

This will generate several files under the `ssl` directory, the important ones being `cert.pem` ,`key.pem` and `ca.pem`. The generated SSL certificate is for 'dex.example.com', although you could change this by editing `gencert.sh` if required.

### Run example client app with GitHub config

```bash
./bin/example-app --issuer-root-ca examples/k8s/ssl/ca.pem
```

1. Open browser to http://127.0.0.1:5555
2. Click Login
3. Select Log in with GitHub and grant access to dex to view your profile

[github-oauth2]: https://github.com/settings/applications/new
[github-orgs]: https://developer.github.com/v3/orgs/
[github-request-org-access]: https://help.github.com/articles/requesting-organization-approval-for-oauth-apps/
[github-approve-org-access]: https://help.github.com/articles/approving-oauth-apps-for-your-organization/



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/connectors/google.md
================================================================================

---
title: "Authentication Through Google"
linkTitle: "Google"
description: ""
date: 2020-09-30
draft: false
toc: true
weight: 2060
---

## Overview

Dex is able to use Google's OpenID Connect provider as an authentication source.

The connector uses the same authentication flow as the OpenID Connect provider but adds Google specific features such as Hosted domain support and reading groups using a service account.

## Configuration

```yaml
connectors:
- type: google
  id: google
  name: Google
  config:

    # Connector config values starting with a "$" will read from the environment.
    clientID: $GOOGLE_CLIENT_ID
    clientSecret: $GOOGLE_CLIENT_SECRET

    # Dex's issuer URL + "/callback"
    redirectURI: http://127.0.0.1:5556/dex/callback

    # Set the value of `prompt` query parameter in the authorization request
    # The default value is "consent" when not set.
    # promptType: consent

    # Google supports whitelisting allowed domains when using G Suite
    # (Google Apps). The following field can be set to a list of domains
    # that can log in:
    #
    # hostedDomains:
    #  - example.com

    # The Google connector supports whitelisting allowed groups when using G Suite
    # (Google Apps). The following field can be set to a list of groups
    # that can log in:
    #
    # groups:
    #  - admins@example.com

    # Google does not support the OpenID Connect groups claim and only supports
    # fetching a user's group membership with a service account.
    # This service account requires an authentication JSON file and the email
    # of a G Suite admin to impersonate:
    #
    #serviceAccountFilePath: googleAuth.json
    #domainToAdminEmail:
    #  *: super-user@example.com
    #  my-domain.com: super-user@my-domain.com
```

## Fetching groups from Google

To allow Dex to fetch group information from Google, you will need to configure a service account for Dex to use.
This account needs Domain-Wide Delegation and permission to access the `https://www.googleapis.com/auth/admin.directory.group.readonly` API scope.

To get group fetching set up:

1. Follow the [instructions](https://developers.google.com/admin-sdk/directory/v1/guides/delegation) to set up a service account with Domain-Wide Delegation
  - During service account creation, a JSON key file will be created that contains authentication information for the service account. This needs storing in a location accessible by Dex and you will set the `serviceAccountFilePath` to point at it.
  - When delegating the API scopes to the service account, delegate the `https://www.googleapis.com/auth/admin.directory.group.readonly` scope and only this scope. If you delegate more scopes to the service account, it will not be able to access the API.
2. Enable the [Admin SDK](https://console.developers.google.com/apis/library/admin.googleapis.com/)
3. Add the `serviceAccountFilePath` and `domainToAdminEmail` configuration options to your Dex config.
  - `serviceAccountFilePath` should point to the location of the service account JSON key file
  - `domainToAdminEmail` should map the base domain to the email address of a Google Workspace user with a minimum of the `Groups Reader (BETA)` Role assigned. The service account you created earlier will impersonate this user when making calls to the admin API. A valid user should be able to retrieve a list of groups when [testing the API](https://developers.google.com/admin-sdk/directory/v1/reference/groups/list#try-it).

## Consent Screen

Dex will set `prompt=consent` by default when redirecting users to Google's
authorization endpoint. This will force users to see the consent screen every
time they log in.

To change this behavior, you can set the `promptType` field in config file to
any OIDC-supported value. To skip the consent screen for every authorization
request, set `promptType` to `""` (empty string) to fall back to Google's
default behavior.



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/connectors/linkedin.md
================================================================================

---
title: "Authentication Through LinkedIn"
linkTitle: "LinkedIn"
description: ""
date: 2020-09-30
draft: false
toc: true
weight: 2070
---

## Overview

One of the login options for dex uses the LinkedIn OAuth2 flow to identify the end user through their LinkedIn account.

When a client redeems a refresh token through dex, dex will re-query LinkedIn to update user information in the ID Token. To do this, __dex stores a readonly LinkedIn access token in its backing datastore.__ Users that reject dex's access through LinkedIn will also revoke all dex clients which authenticated them through LinkedIn.

## Configuration

Register a new application via `My Apps -> Create Application` ensuring the callback URL is `(dex issuer)/callback`. For example if dex is listening at the non-root path `https://auth.example.com/dex` the callback would be `https://auth.example.com/dex/callback`.

The following is an example of a configuration for `examples/config-dev.yaml`:

```yaml
connectors:
  - type: linkedin
    # Required field for connector id.
    id: linkedin
    # Required field for connector name.
    name: LinkedIn
    config:
      # Credentials can be string literals or pulled from the environment.
      clientID: $LINKEDIN_APPLICATION_ID
      clientSecret: $LINKEDIN_CLIENT_SECRET
      redirectURI: http://127.0.0.1:5556/dex/callback
```



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/connectors/gitea.md
================================================================================

---
title: "Authentication Through Gitea"
linkTitle: "Gitea"
description: ""
date: 2020-09-30
draft: false
toc: true
weight: 2130
---

## Overview

One of the login options for dex uses the Gitea OAuth2 flow to identify the end user through their Gitea account.

When a client redeems a refresh token through dex, dex will re-query Gitea to update user information in the ID Token. To do this, __dex stores a readonly Gitea access token in its backing datastore.__ Users that reject dex's access through Gitea will also revoke all dex clients which authenticated them through Gitea.

## Configuration

Register a new OAuth consumer with [Gitea](https://docs.gitea.com/next/development/oauth2-provider) ensuring the callback URL is `(dex issuer)/callback`. For example if dex is listening at the non-root path `https://auth.example.com/dex` the callback would be `https://auth.example.com/dex/callback`.

The following is an example of a configuration for `examples/config-dev.yaml`:

```yaml
connectors:
- type: gitea
  # Required field for connector id.
  id: gitea
  # Required field for connector name.
  name: Gitea
  config:
    # Credentials can be string literals or pulled from the environment.
    clientID: $GITEA_CLIENT_ID
    clientSecret: $GITEA_CLIENT_SECRET
    redirectURI: http://127.0.0.1:5556/dex/callback
    # optional, default = https://gitea.com
    baseURL: https://gitea.com
```



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/connectors/openshift.md
================================================================================

---
title: "Authentication using OpenShift"
linkTitle: "OpenShift"
description: ""
date: 2020-09-30
draft: false
toc: true
weight: 2110
---

## Overview

Dex can make use of users and groups defined within OpenShift by querying the platform provided OAuth server.

## Configuration


### Creating an OAuth Client

Two forms of OAuth Clients can be utilized:

* [Using a Service Account as an OAuth Client](https://docs.openshift.com/container-platform/latest/authentication/using-service-accounts-as-oauth-client.html) (Recommended)
* [Registering An Additional OAuth Client](https://docs.openshift.com/container-platform/latest/authentication/configuring-internal-oauth.html#oauth-register-additional-client_configuring-internal-oauth)

#### Using a Service Account as an OAuth Client

OpenShift Service Accounts can be used as a constrained form of OAuth client. Making use of a Service Account to represent an OAuth Client is the recommended option as it does not require elevated privileged within the OpenShift cluster. Create a new Service Account or make use of an existing Service Account.

Patch the Service Account to add an annotation for location of the Redirect URI

```bash
oc patch serviceaccount <name> --type='json' -p='[{"op": "add", "path": "/metadata/annotations/serviceaccounts.openshift.io~1oauth-redirecturi.dex", "value":"https://<dex_url>/callback"}]'
```

The Client ID for a Service Account representing an OAuth Client takes the form `system:serviceaccount:<namespace>:<service_account_name>`

The Client Secret for a Service Account representing an OAuth Client is the long lived OAuth Token that is configued for the Service Account. Execute the following command to retrieve the OAuth Token.

```bash
oc serviceaccounts get-token <name>
```

#### Registering An Additional OAuth Client

Instead of using a constrained form of Service Account to represent an OAuth Client, an additional OAuthClient resource can be created.

Create a new OAuthClient resource similar to the following:

```yaml
kind: OAuthClient
apiVersion: oauth.openshift.io/v1
metadata:
 name: dex
# The value that should be utilized as the `client_secret`
secret: "<clientSecret>" 
# List of valid addresses for the callback. Ensure one of the values that are provided is `(dex issuer)/callback` 
redirectURIs:
 - "https:///<dex_url>/callback" 
grantMethod: prompt
```

### Dex Configuration

The following is an example of a configuration for `examples/config-dev.yaml`:

```yaml
connectors:
  - type: openshift
    # Required field for connector id.
    id: openshift
    # Required field for connector name.
    name: OpenShift
    config:
      # OpenShift API
      issuer: https://api.mycluster.example.com:6443
      # Credentials can be string literals or pulled from the environment.
      clientID: $OPENSHIFT_OAUTH_CLIENT_ID
      clientSecret: $OPENSHIFT_OAUTH_CLIENT_SECRET
      redirectURI: http://127.0.0.1:5556/dex/
      # Optional: Specify whether to communicate to OpenShift without validating SSL certificates
      insecureCA: false
      # Optional: The location of file containing SSL certificates to communicate to OpenShift
      rootCA: /etc/ssl/openshift.pem
      # Optional list of required groups a user must be a member of
      groups:
        - users
```



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/connectors/bitbucketcloud.md
================================================================================

---
title: "Authentication Through Bitbucket Cloud"
linkTitle: "Bitbucket Cloud"
description: ""
date: 2020-09-30
draft: false
toc: true
weight: 2100
---

## Overview

One of the login options for dex uses the Bitbucket OAuth2 flow to identify the end user through their Bitbucket account.

When a client redeems a refresh token through dex, dex will re-query Bitbucket to update user information in the ID Token. To do this, __dex stores a readonly Bitbucket access token in its backing datastore.__ Users that reject dex's access through Bitbucket will also revoke all dex clients which authenticated them through Bitbucket.

## Configuration

Register a new OAuth consumer with [Bitbucket](https://confluence.atlassian.com/bitbucket/oauth-on-bitbucket-cloud-238027431.html) ensuring the callback URL is `(dex issuer)/callback`. For example if dex is listening at the non-root path `https://auth.example.com/dex` the callback would be `https://auth.example.com/dex/callback`.

There are several permissions required for an OAuth consumer to use it with Dex:
* `Account: Read` - required for extracting base information (email, username)
* `Workspace membership: Read` - only necessary to get user's teams

The following is an example of a configuration for `examples/config-dev.yaml`:

```yaml
connectors:
- type: bitbucket-cloud
  # Required field for connector id.
  id: bitbucket-cloud
  # Required field for connector name.
  name: Bitbucket Cloud
  config:
    # Credentials can be string literals or pulled from the environment.
    clientID: $BITBUCKET_CLIENT_ID
    clientSecret: $BITBUCKET_CLIENT_SECRET
    redirectURI: http://127.0.0.1:5556/dex/callback
    # Optional teams whitelist, communicated through the "groups" scope.
    # If `teams` is omitted, all of the user's Bitbucket teams are returned when the groups scope is present.
    # If `teams` is provided, this acts as a whitelist - only the user's Bitbucket teams that are in the configured `teams` below will go into the groups claim.  Conversely, if the user is not in any of the configured `teams`, the user will not be authenticated.
    teams:
    - my-team
    # Optional parameter to include team groups.
    # If enabled, the groups claim of dex id_token will looks like this:
    # ["my_team", "my_team/administrators", "my_team/members"]
    includeTeamGroups: true
```



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/connectors/microsoft.md
================================================================================

---
title: "Authentication Through Microsoft"
linkTitle: "Microsoft"
description: ""
date: 2020-09-30
draft: false
toc: true
weight: 2080
---

## Overview

One of the login options for dex uses the Microsoft OAuth2 flow to identify the
end user through their Microsoft account.

When a client redeems a refresh token through dex, dex will re-query Microsoft
to update user information in the ID Token. To do this, __dex stores a readonly
Microsoft access and refresh tokens in its backing datastore.__ Users that
reject dex's access through Microsoft will also revoke all dex clients which
authenticated them through Microsoft.

### Caveats

`groups` claim in dex is only supported when `tenant` is specified in Microsoft
connector config. Furthermore, `tenant` must also be configured to either 
`<tenant uuid>` or `<tenant name>` (see [Configuration](#configuration)). In 
order for dex to be able to list groups on behalf of logged in user, an 
explicit organization administrator consent is required. To obtain the 
consent do the following:

  - when registering dex application on https://apps.dev.microsoft.com add
    an explicit `Directory.Read.All` permission to the list of __Delegated
    Permissions__
  - open the following link in your browser and log in under organization
    administrator account:

`https://login.microsoftonline.com/<tenant>/adminconsent?client_id=<dex client id>`

## Configuration

Register a new application on https://apps.dev.microsoft.com via `Add an app`
ensuring the callback URL is `(dex issuer)/callback`. For example if dex
is listening at the non-root path `https://auth.example.com/dex` the callback
would be `https://auth.example.com/dex/callback`.

The following is an example of a configuration for `examples/config-dev.yaml`:

```yaml
connectors:
  - type: microsoft
    # Required field for connector id.
    id: microsoft
    # Required field for connector name.
    name: Microsoft
    config:
      # Credentials can be string literals or pulled from the environment.
      clientID: $MICROSOFT_APPLICATION_ID
      clientSecret: $MICROSOFT_CLIENT_SECRET
      redirectURI: http://127.0.0.1:5556/dex/callback
```

`tenant` configuration parameter controls what kinds of accounts may be
authenticated in dex. By default, all types of Microsoft accounts (consumers
and organizations) can authenticate in dex via Microsoft. To change this, set
the `tenant` parameter to one of the following:

- `common`- both personal and business/school accounts can authenticate in dex
  via Microsoft (default)
- `consumers` - only personal accounts can authenticate in dex
- `organizations` - only business/school accounts can authenticate in dex
- `<tenant uuid>` or `<tenant name>` - only accounts belonging to specific
  tenant identified by either `<tenant uuid>` or `<tenant name>` can
  authenticate in dex

For example, the following snippet configures dex to only allow business/school
accounts:

```yaml
connectors:
  - type: microsoft
    # Required field for connector id.
    id: microsoft
    # Required field for connector name.
    name: Microsoft
    config:
      # Credentials can be string literals or pulled from the environment.
      clientID: $MICROSOFT_APPLICATION_ID
      clientSecret: $MICROSOFT_CLIENT_SECRET
      redirectURI: http://127.0.0.1:5556/dex/callback
      tenant: organizations
```

`domainHint` configuration parameter allows for a more streamlined login
experience when the email domain is common to all users of the connector.
By default, users with multiple Microsoft sessions will be prompted to choose
which account they want to use for login.  When `domainHint` is configured,
Microsoft will select the session with matching email without the interactive
prompt.

For example: user John Doe has 2 active Microsoft sessions:

- John.Doe@live.com (consumer)
- John.Doe@example.com (organization)

If Example Organization configures the `domainHint` parameter with its
organization's email suffix, John will not be prompted to select an account
from the active sessions.  Instead, the matching organization session is
selected automatically.

`scopes` configuration parameter controls what the initial scope(s) of the identity
token that dex requests from Microsoft. To change this initial set, configure
the `scopes` parameter to be a list of one or more valid scopes (as defined in
[Microsoft Documentation](https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-permissions-and-consent)).

The default scope (if one is not specified in the connector's configuration) is
`user.read`.

The scope list requested may also be appended by specifying [groups](#groups) or
requesting a new token through the use of a refresh token.

For example, the following snippet configures dex to request an OpenID token
with only getting the email address associated with the account and nothing else:

```yaml
connectors:
  - type: microsoft
    # Required field for connector id.
    id: microsoft
    # Required field for connector name.
    name: Microsoft
    config:
      # Credentials can be string literals or pulled from the environment.
      clientID: $MICROSOFT_APPLICATION_ID
      clientSecret: $MICROSOFT_CLIENT_SECRET
      redirectURI: http://127.0.0.1:5556/dex/callback
      tenant: example.onmicrosoft.com
      domainHint: example.com
      scopes:
        - openid
        - email
```

### Groups

When the `groups` claim is present in a request to dex __and__ `tenant` is
configured, dex will query Microsoft API to obtain a list of groups the user is
a member of. `onlySecurityGroups` configuration option restricts the list to
include only security groups. By default all groups (security, Office 365,
mailing lists) are included.

Please note that `tenant` must be configured to either `<tenant uuid>` or 
`<tenant name>` for this to work. For more details on `tenant` configuration,
see [Configuration](#configuration).

By default, dex resolve groups ids to groups names, to keep groups ids, you can
specify the configuration option `groupNameFormat: id`.

It is possible to require a user to be a member of a particular group in order
to be successfully authenticated in dex. For example, with the following
configuration file only the users who are members of at least one of the listed
groups will be able to successfully authenticate in dex:

```yaml
connectors:
  - type: microsoft
    # Required field for connector id.
    id: microsoft
    # Required field for connector name.
    name: Microsoft
    config:
      # Credentials can be string literals or pulled from the environment.
      clientID: $MICROSOFT_APPLICATION_ID
      clientSecret: $MICROSOFT_CLIENT_SECRET
      redirectURI: http://127.0.0.1:5556/dex/callback
      tenant: myorg.onmicrosoft.com
      groups:
        - developers
        - devops
```

Also, `useGroupsAsWhitelist` configuration option, can restrict the groups
claims to include only the user's groups that are in the configured `groups`.

You can use the emailToLowercase (boolean) configuration option to streamline 
UPNs (user email) from Active Directory before putting them into an id token.
Without this option, it can be tough to match the email claim because a client 
application doesn't know whether an email address has been added with 
capital- or lowercase letters.
For example, it is hard to bind Roles in Kubernetes using email as a user name 
(--oidc-username-claim=email flag) because user names are case sensitive.

```yaml
connectors:
  - type: microsoft
    # Required field for connector id.
    id: microsoft
    # Required field for connector name.
    name: Microsoft
    config:
      # Credentials can be string literals or pulled from the environment.
      clientID: $MICROSOFT_APPLICATION_ID
      clientSecret: $MICROSOFT_CLIENT_SECRET
      redirectURI: http://127.0.0.1:5556/dex/callback
      tenant: myorg.onmicrosoft.com
      groups:
        - developers
        - devops
      # All relevant E-Mail Addresses delivered by AD will transformed to
      # lowercase if config is TRUE
      emailToLowercase: true
```


================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/connectors/gitlab.md
================================================================================

---
title: "Authentication Through GitLab"
linkTitle: "GitLab"
description: ""
date: 2020-09-30
draft: false
toc: true
weight: 2040
---

## Overview

GitLab is a web-based Git repository manager with wiki and issue tracking features, using an open source license, developed by GitLab Inc. One of the login options for dex uses the GitLab OAuth2 flow to identify the end user through their GitLab account. You can use this option with [gitlab.com](https://gitlab.com), GitLab community or enterprise edition.

When a client redeems a refresh token through dex, dex will re-query GitLab to update user information in the ID Token. To do this, __dex stores a readonly GitLab access token in its backing datastore.__ Users that reject dex's access through GitLab will also revoke all dex clients which authenticated them through GitLab.

## Configuration

Register a new application via `User Settings -> Applications` ensuring the callback URL is `(dex issuer)/callback`. For example if dex is listening at the non-root path `https://auth.example.com/dex` the callback would be `https://auth.example.com/dex/callback`.

The application requires the user to grant the `read_user` and `openid` scopes. The latter is required only if group membership is a desired claim.

The following is an example of a configuration for `examples/config-dev.yaml`:

```yaml
connectors:
  - type: gitlab
    # Required field for connector id.
    id: gitlab
    # Required field for connector name.
    name: GitLab
    config:
      # optional, default = https://gitlab.com
      baseURL: https://gitlab.com
      # Credentials can be string literals or pulled from the environment.
      clientID: $GITLAB_APPLICATION_ID
      clientSecret: $GITLAB_CLIENT_SECRET
      redirectURI: http://127.0.0.1:5556/dex/callback
      # Optional groups whitelist, communicated through the "groups" scope.
      # If `groups` is omitted, all of the user's GitLab groups are returned when the groups scope is present.
      # If `groups` is provided, this acts as a whitelist - only the user's GitLab groups that are in the configured `groups` below will go into the groups claim.  Conversely, if the user is not in any of the configured `groups`, the user will not be authenticated.
      groups:
      - my-group
      # flag which will switch from using the internal GitLab id to the users handle (@mention) as the user id.
      # It is possible for a user to change their own user name but it is very rare for them to do so
      useLoginAsID: false
      # Flag to include user group permissions in the user groups.
      # For example, if the user has maintainer access to a GitLab group named "project/group1", 
      # the user's groups will reflect two entries: "project/group1" and "project/group1:maintainer".
      getGroupsPermission: false
```



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/connectors/keystone.md
================================================================================

---
title: "Authentication Through OpenStack Keystone"
linkTitle: "OpenStack Keystone"
description: ""
date: 2021-03-11
draft: false
toc: true
weight: 2135
---

## Overview

[Keystone](https://docs.openstack.org/keystone/latest/) is an OpenStack service that provides API client authentication, service discovery, and distributed multi-tenant authorization. 

OpenStack Keystone connector supports `offline_access` and `groups` scopes. To use this connector, create a domain and user with an admin role, then specify the credentials in the configuration file (see the example below).

OpenStack Keystone exposes the [Identity API v3](https://docs.openstack.org/api-ref/identity/v3/) to work with dex.


## Configuration

The following is an example of an OpenStack Keystone configuration for dex:

```yaml
connectors:
  - type: keystone
    # Required field for connector id.
    id: keystone
    # Required field for connector name.
    name: Keystone
    config:
      # Required, without v3 suffix.
      keystoneHost: http://example:5000
      # Required, admin user credentials to connect to keystone.
      domain: default
      keystoneUsername: demo 
      keystonePassword: DEMO_PASS
```



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/connectors/local.md
================================================================================

---
linkTitle: "BuiltIn (local)"
title: "Authentication Through the builtin connector"
description: ""
date: 2024-01-05
draft: false
toc: true
weight: 2110
---

## Overview
Dex comes with a built-in local connector, acting as a "virtual" identity provider within Dex's ecosystem, securely storing login credentials in the specified [storage](/docs/storage).
This local connector simplifies authentication workflows by managing and storing user credentials directly within Dex's infrastructure.


## Configuration
The local connector can be utilized by adding the following flag to the configuration.
```yaml
enablePasswordDB: true
```

### Creating Users

Once the local connector is enabled, users can be added in two ways: statically within the configuration file or dynamically through the [gRPC API](/docs/api).

#### Static configuration (config file)
```yaml
staticPasswords:
  - email: "admin@example.com"
    # bcrypt hash of the string "password": $(echo password | htpasswd -BinC 10 admin | cut -d: -f2)
    hash: "$2a$10$2b2cU8CPhOTaGrs1HRQuAueS7JTT5ZHsHSzYiFPm1leZck7Mc8T4W"
    username: "admin"
    userID: "08a8684b-db88-4b73-90a9-3cd1661f5466"
```

To specify users within the configuration file, the `staticPasswords` option can be used. It contains a list of predefined users, each defined by the following entities:

* `email`: The email address of the user (used as the main identifier).
* `hash`: The bcrypt hash of the user's password.
* `username`: The username associated with the user.
* `userID`: The unique identifier (ID) of the user.


#### Dynamic configuration (API)
Users can be dynamically managed via the gRPC API, offering a versatile method to handle user-related operations within the system.
This functionality enables seamless additions, updates, and removals of users, providing a flexible approach to user management.
For comprehensive information and detailed procedures, please refer to the specific [API documentation](/docs/api).

### Obtaining a token
Let's explore a sample configuration in dex that involves a public and private client along with a static user.
Both local users and password grants are enabled, allowing the exchange of a token for user credentials.

```yaml
issuer: http://localhost:8080/dex
storage:  # .. storage configuration
# Setup clients
staticClients:
  - id: public-client
    public: true
    name: 'Public Client'
    redirectURIs:
      - 'https://example.com/oidc/callback'
  - id: private-client
    secret: app-secret
    name: 'Private Client'
    redirectURIs:
      - 'https://example.com/oidc/callback'
# Set up an test user
staticPasswords:
  - email: "admin@example.com"
    # bcrypt hash of the string "password": $(echo password | htpasswd -BinC 10 admin | cut -d: -f2)
    hash: "$2a$10$2b2cU8CPhOTaGrs1HRQuAueS7JTT5ZHsHSzYiFPm1leZck7Mc8T4W"
    username: "admin"
    userID: "08a8684b-db88-4b73-90a9-3cd1661f5466"

# Enable local users
enablePasswordDB: true
# Allow password grants with local users
oauth2:
  passwordConnector: local
```

Depending on whether you use a public or a private client you need to either include the just `clientId` or the `clientId` and `clientPassword` in the authorization header.

**Public Client**
```shell
curl -L -X POST 'http://localhost:8080/dex/token' \
-H 'Authorization: Basic cHVibGljLWNsaWVudDo=' \ # base64 encoded: public-client:
-H 'Content-Type: application/x-www-form-urlencoded' \
--data-urlencode 'grant_type=password' \
--data-urlencode 'scope=openid profile' \
--data-urlencode 'username=admin@example.com' \
--data-urlencode 'password=password'
```


**Private Client**
```shell
curl -L -X POST 'http://localhost:8080/dex/token' \
-H 'Authorization: Basic cHJpdmF0ZS1jbGllbnQ6YXBwLXNlY3JldA==' \ # base64 encoded: private-client:app-secret
-H 'Content-Type: application/x-www-form-urlencoded' \
--data-urlencode 'grant_type=password' \
--data-urlencode 'scope=openid' \
--data-urlencode 'username=admin@example.com' \
--data-urlencode 'password=password'
```



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/configuration/tokens.md
================================================================================

---
title: "Tokens"
linkTitle: "Tokens"
description: "Types of tokens and expiration settings"
date: 2020-10-21
draft: false
toc: true
weight: 1013
---

## Overview

ID Tokens are an OAuth2 extension introduced by OpenID Connect and Dex's primary feature. ID Tokens are [JSON Web Tokens][jwt-io] (JWTs) signed by Dex and returned as part of the OAuth2 response that attest to the end user's identity. An example JWT might look like:

```bash
eyJhbGciOiJSUzI1NiIsImtpZCI6IjlkNDQ3NDFmNzczYjkzOGNmNjVkZDMyNjY4NWI4NjE4MGMzMjRkOTkifQ.eyJpc3MiOiJodHRwOi8vMTI3LjAuMC4xOjU1NTYvZGV4Iiwic3ViIjoiQ2djeU16UXlOelE1RWdabmFYUm9kV0kiLCJhdWQiOiJleGFtcGxlLWFwcCIsImV4cCI6MTQ5Mjg4MjA0MiwiaWF0IjoxNDkyNzk1NjQyLCJhdF9oYXNoIjoiYmk5NmdPWFpTaHZsV1l0YWw5RXFpdyIsImVtYWlsIjoiZXJpYy5jaGlhbmdAY29yZW9zLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJncm91cHMiOlsiYWRtaW5zIiwiZGV2ZWxvcGVycyJdLCJuYW1lIjoiRXJpYyBDaGlhbmcifQ.OhROPq_0eP-zsQRjg87KZ4wGkjiQGnTi5QuG877AdJDb3R2ZCOk2Vkf5SdP8cPyb3VMqL32G4hLDayniiv8f1_ZXAde0sKrayfQ10XAXFgZl_P1yilkLdknxn6nbhDRVllpWcB12ki9vmAxklAr0B1C4kr5nI3-BZLrFcUR5sQbxwJj4oW1OuG6jJCNGHXGNTBTNEaM28eD-9nhfBeuBTzzO7BKwPsojjj4C9ogU4JQhGvm_l4yfVi0boSx8c0FX3JsiB0yLa1ZdJVWVl9m90XmbWRSD85pNDQHcWZP9hR6CMgbvGkZsgjG32qeRwUL_eNkNowSBNWLrGNPoON1gMg
```

ID Tokens contains standard claims assert which client app logged the user in, when the token expires, and the identity of the user.

```json
{
  "iss": "http://127.0.0.1:5556/dex",
  "sub": "CgcyMzQyNzQ5EgZnaXRodWI",
  "aud": "example-app",
  "exp": 1492882042,
  "iat": 1492795642,
  "at_hash": "bi96gOXZShvlWYtal9Eqiw",
  "email": "jane.doe@coreos.com",
  "email_verified": true,
  "groups": [
    "admins",
    "developers"
  ],
  "name": "Jane Doe"
}
```

Because these tokens are signed by Dex and [contain standard-based claims][standard-claims] other services can consume them as service-to-service credentials. Systems that can already consume OpenID Connect ID Tokens issued by Dex include:

* [Kubernetes][kubernetes]
* [AWS STS][aws-sts]

For details on how to request or validate an ID Token, see [“_Writing apps that use Dex_.”][using-dex]

## Refresh tokens
Refresh tokens are credentials used to obtain access tokens. Refresh tokens are issued to the client by the authorization server and are used to obtain
a new id token when the current id token becomes invalid or expires. Issuing a refresh token is optional and is provided by passing `offline_access` scope to Dex server.

__NOTE__: Some connectors do not support `offline_access` scope. You can find out which connectors support refresh tokens by looking into the [_connectors list_][connectors].

Example of a server response with refresh token:
```json
{
 "access_token": "eyJhbGciOiJSUzI1N...",
 "token_type": "Bearer",
 "refresh_token": "lxzzsvasxho5exvwkfa5zhefl",
 "expires_in": 3600,
 "id_token": "eyJhbGciO..."
}
```

__NOTE__: For every refresh of an id token, Dex issues a new refresh token. This security measure is called _refresh token rotation_
and prevents someone stealing it. The idea is described in detail in the corresponding [RFC][rfc6819-5.2.2.3].

## Expiration and rotation settings

Dex has a section in the config file where you can specify expiration and rotation settings for id tokens and refresh tokens.
__NOTE__: All duration options should be set in the format: number + time unit (s, m, h), e.g., `10m`.

* `expiry` - section for various expiration settings, including token settings:
  * `idTokens` - the lifetime of if tokens. It is preferable to use short-lived id tokens, e.g., 10 minutes.
  * `authRequests` - the time frame in which users can exchange a code for an access or id token.
  * `deviceRequests` - the time frame in which users can authorize a device to receive an access or id token.
  * `signingKeys` - the period of time after which the signing keys are rotated. It is recommended to rotate keys regularly. If the `idTokens` lifetime exceeds, public parts of signing keys will be kept for validation for the extra time.
  * `refreshTokens` - section for various refresh token settings:
    * `validIfNotUsedFor` - invalidate a refresh token if it is not used for a specified amount of time.
    * `absoluteLifetime` - a stricter variant of the previous option, absolute lifetime of a refresh token. It forces users to reauthenticate and obtain a new refresh token.
    * `disableRotation` - completely disables every-request rotation. The user will also have to specify one of the previous refresh token options to keep refresh tokens secure when toggling this.
    * `reuseInterval` - allows getting the same refresh token from refresh endpoint within a specified interval, but only if the user's request contains the previous refresh token.

__NOTE__: `disableRotation` and `reuseInterval` options help effectively deal with network lags, concurrent requests, and so on in tradeoff for security. Use them with caution.

## Token signing configuration

Dex provides flexible token signing options through the `signer` configuration section. You can choose between a local signer or integrate with Vault-compatible APIs for centralized key management.

### Local signer

The local signer uses keys managed by Dex's storage backend with automatic rotation. This is the default option for simple deployments.

* `type` - set to `local` to use local signing
* `config` - configuration section for local signer:
  * `keysRotationPeriod` - (required) the period after which signing keys are rotated (e.g., `6h`, `24h`)

**Supported signing algorithms (not configurable):**

* `RS256` (RSA with SHA-256)

Example configuration:
```yaml
signer:
  type: local
  config:
    keysRotationPeriod: 6h
```

### Vault-compatible signer

For enhanced security and centralized key management. This allows you to use HashiCorp Vault or OpenBao for signing operations without storing keys locally.

* `type` - set to `vault` to use Vault-compatible API
* `config` - configuration section for Vault signer:
  * `keyName` - (required) the key identifier in Vault/OpenBao to use for signing (e.g., `dex/signing-key`)
  * `addr` - Vault/OpenBao server address (optional, can be set via `VAULT_ADDR` environment variable)
  * `token` - authentication token for Vault/OpenBao (optional, can be set via `VAULT_TOKEN` environment variable)

**Supported signing algorithms:**

* `RS256` (RSA with SHA-256)
* `ES256` (ECDSA with SHA-256)
* `ES384` (ECDSA with SHA-384)
* `ES512` (ECDSA with SHA-512)
* `EdDSA` (Edwards-curve Digital Signature Algorithm)

The signing algorithm is determined by the key type configured in Vault/OpenBao's Transit backend.

{{% alert title="Note" color="primary" %}}
Only the `keyName` parameter is required. The `addr` and `token` can be provided through environment variables, making it easier to manage sensitive credentials without exposing them in configuration files.
{{% /alert %}}

Example configuration:
```yaml
signer:
  type: vault
  config:
    keyName: dex/signing-key
    addr: http://localhost:8200
    token: test-token
```

Using environment variables:
```yaml
signer:
  type: vault
  config:
    keyName: dex/signing-key
```

With environment variables set:
```bash
```

This approach ensures that signing keys never leave your Vault/OpenBao server, providing better security and auditability of key operations.

{{% alert title="Note" color="primary" %}}
Dex supports Vault-compatible APIs through [OpenBao API v2 integration package](https://pkg.go.dev/github.com/openbao/openbao/api/v2).

Integration tests for Dex guarantee compatibility with Vault, but it may change in the future.
{{% /alert %}}

[aws-sts]: https://docs.aws.amazon.com/STS/latest/APIReference/Welcome.html
[connectors]: /docs/connectors
[jwt-io]: https://jwt.io/
[kubernetes]: https://kubernetes.io/docs/reference/access-authn-authz/authentication/#openid-connect-tokens
[openbao]: https://pkg.go.dev/github.com/openbao/openbao/api/v2
[rfc6819-5.2.2.3]: https://tools.ietf.org/html/rfc6819#section-5.2.2.3
[standard-claims]: https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims
[using-dex]: /docs/guides/using-dex



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/guides/token-exchange.md
================================================================================

---
title: "Machine Authentication to Dex"
linkTitle: "Authentication for Machines"
description: ""
date: 2023-07-01
draft: false
toc: true
weight: 1080
---

## Overview

Most Dex connectors redirect users to the upstream identity provider as part of the authentication flow.
While this works for human users,
it is much harder for machines and automated processes (e.g., CI pipelines) to complete this interactive flow.
This is where [OAuth2 Token Exchange][token-exchange] comes in:
it allows clients to exchange an access or ID token they already have
(obtained from their environment, through custom CLI commands, etc.)
for a token issued by dex.

This works like [GCP Workload Identity Federation][gcp-federation] and [AWS Web Identity Federation][aws-federation],
allowing processes running in trusted execution environments that issue OIDC tokens,
such as [Github Actions][gh-actions], [Buildkite][buildkite], [CircleCI][circleci], [GCP][gcp], and others,
to exchange them for a dex issued token to access protected resources.

The authentication flow looks like this:

1. Client independently obtains an access / id token from the upstream IDP.
2. Client exchanges the upstream token for a dex access / id token via the token exchange flow.
3. Use token to access dex protected resources.
4. Repeat these steps when the token expires.

## Configuring dex

Currently, only the [OIDC Connector][oidc-connector] supports token exchanges.
For this flow, `clientID`, `clientSecret`, and `redirectURI` aren't required.
`getUserInfo` is required if you want to exchange from access tokens to dex issued tokens.

As the user performing the token exchange will need the client secret,
we configure the client as a [public client](/docs/configuration/custom-scopes-claims-clients/#public-clients).
If you need to allow humans and machines to authenticate,
consider creating a dedicated public client for token exchange
and using [cross-client trust](/docs/configuration/custom-scopes-claims-clients/#cross-client-trust-and-authorized-party).

```yaml
issuer: https://dex.example.com
storage:
    type: sqlite3
    config:
        file: dex.db
web:
    http: 0.0.0.0:8001

oauth2:
  grantTypes:
    # ensure grantTypes includes the token-exchange grant (default)
    - "urn:ietf:params:oauth:grant-type:token-exchange"

connectors:
  - name: My Upstream
    type: oidc
    id: my-upstream
    config:
      # The client submitted subject token will be verified against the issuer given here.
      issuer: https://token.example.com
      # Additional scopes in token response, supported list at:
      # https://dexidp.io/docs/custom-scopes-claims-clients/#scopes
      scopes:
        - groups
        - federated:id
      # mapping of fields from the submitted token
      userNameKey: sub
      # Access tokens are generally considered opaque.
      # We check their validity by calling the user info endpoint if it's supported.
      # getUserInfo: true

staticClients:
  # dex issued tokens are bound to clients.
  # For the token exchange flow, the client id and secret pair must be submitted as the username:password
  # via Basic Authentication.
  - name: My App
    id: my-app
    secret: my-secret
    # We set public to indicate we don't intend to keep the client secret actually secret.
    # https://dexidp.io/docs/configuration/custom-scopes-claims-clients/#public-clients
    public: true
```

## Performing a token exchange

To exchange an upstream IDP token for a dex issued token,
perform an `application/x-www-form-urlencoded` `POST` request
to dex's `/token` endpoint following [RFC 8693 Section 2.1][token-exchange-2-1].
Additionally, dex requires the connector to be specified with the `connector_id` parameter
and a client id/secret to be included as the username/password via Basic Authentication.

```sh
$ export UPSTREAM_TOKEN=$(# get a token from the upstream IDP)

$ curl https://dex.example.com/token \
  --user my-app:my-secret \
  --data-urlencode connector_id=my-upstream \
  --data-urlencode grant_type=urn:ietf:params:oauth:grant-type:token-exchange \
  --data-urlencode scope="openid groups federated:id" \
  --data-urlencode requested_token_type=urn:ietf:params:oauth:token-type:access_token \
  --data-urlencode subject_token=$UPSTREAM_TOKEN \
  --data-urlencode subject_token_type=urn:ietf:params:oauth:token-type:access_token
```

Below is an example of a successful response.
Note that regardless of the `requested_token_type`,
the token will always be in the `access_token` field,
with the type indicated by the `issued_token_type` field.
See [RFC 8693 Section 2.2.1][token-exchange-2-2-1] for details.

```json
{
  "access_token":"eyJhbGciOi....aU5oA",
  "issued_token_type":"urn:ietf:params:oauth:token-type:access_token",
  "token_type":"bearer",
  "expires_in":86399
}
```

### Full example with GitHub Actions

Here is an example of running dex as a service during a Github Actions workflow
and getting an access token from it, exchanged from a Github Actions OIDC token.

Dex config:

```yaml
issuer: http://127.0.0.1:5556/
storage:
  type: sqlite3
  config:
    file: dex.db
web:
  http: 0.0.0.0:8080
connectors:
- type: oidc
  id: github-actions
  name: github-actions
  config:
    issuer: https://token.actions.githubusercontent.com
    scopes:
      - openid
      - groups
    userNameKey: sub
staticClients:
  - name: My app
    id: my-app
    secret: my-secret
    public: true
```

Github actions workflow.
Replace the service image with one that has the config included.

```yaml
name: workflow1

on: [push]

permissions:
  id-token: write # This is required for requesting the JWT

jobs:
  job:
    runs-on: ubuntu-latest
    services:
      dex:
        # replace with an image that has the config above
        image: ghcr.io/dexidp/dex:latest
        ports:
          - 80:8080
    steps:
      # Actions have access to two special environment variables ACTIONS_CACHE_URL and ACTIONS_RUNTIME_TOKEN.
      # Inline step scripts in workflows do not see these variables.
      - uses: actions/github-script@v6
        id: script
        timeout-minutes: 10
        with:
          debug: true
          script: |
            const token = process.env['ACTIONS_RUNTIME_TOKEN']
            const runtimeUrl = process.env['ACTIONS_ID_TOKEN_REQUEST_URL']
            core.setOutput('TOKEN', token.trim())
            core.setOutput('IDTOKENURL', runtimeUrl.trim())
      - run: |
          # get an token from github
          GH_TOKEN_RESPONSE=$(curl \
            "${{steps.script.outputs.IDTOKENURL}}" \
            -H "Authorization: bearer  ${{steps.script.outputs.TOKEN}}" \
            -H "Accept: application/json; api-version=2.0" \
            -H "Content-Type: application/json" \
            -d "{}" \
          )
          GH_TOKEN=$(jq -r .value <<< $GH_TOKEN_RESPONSE)

          # exchange it for a dex token
          DEX_TOKEN_RESPONSE=$(curl \
              http://127.0.0.1/token \
              --user my-app:my-secret \
              --data-urlencode "connector_id=github-actions" \
              --data-urlencode "grant_type=urn:ietf:params:oauth:grant-type:token-exchange" \
              --data-urlencode "scope=openid groups federated:id" \
              --data-urlencode "requested_token_type=urn:ietf:params:oauth:token-type:access_token" \
              --data-urlencode "subject_token=$GH_TOKEN" \
              --data-urlencode "subject_token_type=urn:ietf:params:oauth:token-type:access_token")
          DEX_TOKEN=$(jq -r .access_token <<< $DEX_TOKEN_RESPONSE)

          # use $DEX_TOKEN

        id: idtoken
```

[token-exchange]: https://www.rfc-editor.org/rfc/rfc8693.html
[token-exchange-2-1]: https://www.rfc-editor.org/rfc/rfc8693.html#name-request
[token-exchange-2-2-1]: https://www.rfc-editor.org/rfc/rfc8693.html#name-successful-response
[gcp-federation]: https://cloud.google.com/iam/docs/workload-identity-federation
[aws-federation]: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_oidc.html
[gh-actions]: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect
[buildkite]: https://buildkite.com/docs/agent/v3/cli-oidc
[circleci]: https://circleci.com/docs/openid-connect-tokens/
[gcp]: https://cloud.google.com/sdk/gcloud/reference/auth/print-access-token
[oidc-connector]: https://dexidp.io/docs/connectors/oidc/



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/archive/proposals/token-revocation.md
================================================================================

---
title: "Proposal: Design for Revoking Refresh Tokens"
linkTitle: "Design for Revoking Refresh Tokens"
description: ""
date: 2020-09-30
draft: true
toc: true
weight: 20
---

Refresh tokens are issued to the client by the authorization server and are used
to request a new access token when the current access token becomes invalid or expires.
It is a common usecase for the end users to revoke client access to their identity.
This proposal defines the changes needed in Dex v2 to support refresh token revocation.

## Motivation

1. Currently refresh tokens are not associated with the user. Need a new "session object" for this.
2. Need an API to list refresh tokens based on the UserID.
3. We need a way for users to login to dex and revoke a client.
4. Limit the number refresh tokens for each user-client pair to 1.

## Details

Currently in Dex when an end user successfully logs in via a connector and has the OfflineAccess
scope set to true, a refresh token is created and stored in the backing datastore. There is no
association between the end user and the refresh token. Hence if we want to support the functionality
of users being able to revoke refresh tokens, the first step is to have a structure in place that allows
us retrieve a list of refresh tokens depending on the authenticated user.

```go
// Reference object for RefreshToken containing only metadata.
type RefreshTokenRef struct {
	// ID of the RefreshToken
	ID string
	CreatedAt time.Time
	LastUsed  time.Time
}

// Session objects pertaining to users with refresh tokens.
//
// Will have to handle garbage collection i.e. if no refresh token exists for a user,
// this object must be cleaned up.
type OfflineSession struct {
        // UserID of an end user who has logged into the server.
        UserID        string
        // The ID of the connector used to login the user.
        ConnID     string
        // List of pointers to RefreshTokens issued for SessionID
        Refresh         []*RefreshTokenRef
}

// Retrieve OfflineSession obj for given userId and connID
func getOfflineSession (userId string, connID string)

```

### Changes in Dex CodeFlows

1. Client requests a refresh token:
   Try to retrieve the `OfflineSession` object for the User with the given `UserID + ConnID`.
   This leads to two possibilities:   
	* Object exists: This means a Refresh token already exists for the user.
          Update the existing `OfflineSession` object with the newly received token as follows:
		* CreateRefresh() will create a new `RefreshToken` obj in the storage.
		* Update the `Refresh` list with the new `RefreshToken` pointer.
		* Delete the old refresh token in storage.

	* No object found: This implies that this will be the first refresh token for the user.
 		* CreateRefresh() will create a new `RefreshToken` obj in the storage.
		* Create an OfflineSession for the user and add the new `RefreshToken` pointer to
		  the `Refresh` list.
                
2. Refresh token rotation:
   There will be no change to this codeflow. When the client refreshes a refresh token, the `TokenID`
   still remains intact and only the `RefreshToken` obj gets updated with a new nonce. We do not need
   any additional checks in the OfflineSession objects as the `RefreshToken` pointers still remain intact.

3. User revokes a refresh token (New functionality):
   A user that has been authenticated externally will have the ability to revoke their refresh tokens.
   Please note that Dex's API does not perform the authentication, this will have to be done by an
   external app.
   Steps involved:
	* Get `OfflineSession` obj with given UserID + ConnID. 
	* If a refresh token exists in `Refresh`, delete the `RefreshToken` (handle this in storage)
	  and its pointer value in `Refresh`. Clean up the OfflineSession object.
	* If there is no refresh token found, handle error case.

NOTE: To avoid race conditions between “requesting a refresh token” and “revoking a refresh token”, use
locking mechanism when updating an `OfflineSession` object.



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/_index.md
================================================================================

---
title: "Documentation"
description: ""
date: 2020-01-07T14:59:38+01:00
draft: false
toc: true
menu: { main: { weight: 10 } }
---

## Architecture

Dex is an identity service that uses OpenID Connect to drive authentication for other apps. Dex acts as a portal to other identity providers through "connectors." This lets Dex defer authentication to LDAP servers, SAML providers, or established identity providers like GitHub, Google, and Active Directory.



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/getting-started.md
================================================================================

---
title: "Getting Started"
description: "First touch with Dex"
date: 2020-09-30
draft: false
toc: true
weight: 1010
type: "docs"
---

## Container image

Dex is primarily distributed as a container image, published to the following locations:

- [ghcr.io/dexidp/dex](https://github.com/dexidp/dex/pkgs/container/dex)
- [docker.io/dexidp/dex](https://hub.docker.com/r/dexidp/dex/tags)

2 variants (`alpine` and `distroless`) of container images are provided
based on Alpine Linux and Distroless base images.

A reference Kubernetes Helm chart for dex can be found at [charts.dexidp.io](https://charts.dexidp.io).

## Building the dex binary

To build dex from source code, install a working Go environment with version 1.19 or greater according to the [official documentation][go-setup].
Then clone the repository and use `make` to compile the dex binary.

```bash
$ git clone https://github.com/dexidp/dex.git
$ cd dex/
$ make build
```

## Configuration

Dex exclusively pulls configuration options from a config file. Use the [example config][example-config] file found in the `examples/` directory to start an instance of dex with a sqlite3 data store, and a set of predefined OAuth2 clients.

```bash
./bin/dex serve examples/config-dev.yaml
```

The [example config][example-config] file documents many of the configuration options through inline comments. For extra config options, look at that file.

### Templated configuration

The default entrypoint for distributed container images utilize [gomplate][gomplate]
to pre-process configuration files (`.tpl`, `.tmpl`, `.yaml`) passed as arguments.
This enables templating any field from the environment, for example:

```yaml
secret: "{{ .Env.MY_SECRET_ENV }}"
```

See [gomplate docs][gomplate-docs] for templating syntax.

## Running a client

Dex operates like most other OAuth2 providers. Users are redirected from a client app to dex to login. Dex ships with an example client app (built with the `make examples` command), for testing and demos.

By default, the example client is configured with the same OAuth2 credentials defined in `examples/config-dev.yaml` to talk to dex. Running the example app will cause it to query dex's [discovery endpoint][oidc-discovery] and determine the OAuth2 endpoints.

```bash
./bin/example-app
```

Login to dex through the example app using the following steps.

1. Navigate to the example app at http://localhost:5555/ in your browser.
2. Hit "login" on the example app to be redirected to dex.
3. Choose an option to authenticate:
   - "Login with Example" to use mocked user data.
   - "Login with Email" to fill the form with static user credentials `admin@example.com` and `password`.
4. Approve the example app's request.
5. See the resulting token the example app claims from dex.

## Further reading

Dex is generally used as a building block to drive authentication for other apps. See [_"Writing apps that use Dex"_][using-dex] for an overview of instrumenting apps to work with dex.

For a primer on using LDAP to back dex's user store, see the OpenLDAP [_"Getting started"_](/docs/connectors/ldap/#getting-started) example.

Check out the Documentation directory for further reading on setting up different storages, interacting with the dex API, intros for OpenID Connect, and logging in through other identity providers such as Google, GitHub, or LDAP.

[go-setup]: https://golang.org/doc/install
[example-config]: https://github.com/dexidp/dex/blob/master/examples/config-dev.yaml
[gomplate]: https://github.com/hairyhenderson/gomplate
[gomplate-docs]: https://docs.gomplate.ca/
[oidc-discovery]: https://openid.net/specs/openid-connect-discovery-1_0-17.html#ProviderMetadata
[using-dex]: /docs//using-dex/



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/archive/_index.md
================================================================================

---
title: "Archive"
description: "The following documents are no longer maintained and are archived for reference purposes only"
date: 2020-01-07T14:59:38+01:00
draft: false
toc: true
weight: 9999
---




================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/archive/v2.md
================================================================================

---
title: "Dex v2"
linkTitle: "What's new in v2"
description: ""
date: 2020-09-30
draft: false
toc: true
weight: 1030
---

## Streamlined deployments

Many of the changes between v1 and v2 were aimed at making dex easier to deploy and manage, perhaps the biggest pain point for dex v1. Dex is now a single, scalable binary with a sole source of configuration. Many components which previously had to be set through the API, such as OAuth2 clients and IDP connectors can now be specified statically. The new architecture lacks a singleton component eliminating deployment ordering. There are no more special development modes; instructions for running dex on a workstation translate with minimal changes to a production system.

All of this results in a much simpler deployment story. Write a config file, run the dex binary, and that's it.

## More storage backends

Dex's internal storage interface has been improved to support multiple backing databases including Postgres, SQLite3, and the Kubernetes API through Third Party Resources. This allows dex to meet a more diverse set of use cases instead of insisting on one particular deployment pattern. For example, The Kubernetes API implementation, a [key value store][k8s-api-docs], allows dex to be run natively on top of a Kubernetes cluster with extremely little administrative overhead. Starting with support for multiple storage backends also should help ensure that the dex storage interface is actually pluggable, rather than being coupled too tightly with a single implementation.

A more in depth discussion of existing storage options and how to add new ones can be found [here][storage-docs].

## Additional improvements

The rewrite came with several, miscellaneous improvements including:

* More powerful connectors. For example the GitHub connector can now query for teams.
* Combined the two APIs into a single [gRPC API][api-docs] with no complex authorization rules.
* Expanded OAuth2 capabilities such as the implicit flow.
* Simplified codebase and improved testing.

## Rethinking registration

Dex v1 performed well when it could manage users. It provided features such as registration, email invites, password resets, administrative abilities, etc. However, login flows and APIs remain tightly coupled with concepts like registration and admin users even when v1 federated to an upstream identity provider (IDP) where it likely only had read only access to the actual user database.

Many of v2's use cases focus on federation to other IPDs rather than managing users itself. Because of this, options associated with registration, such as SMTP credentials, have been removed. We hope to add registration and user management back into the project through orthogonal applications using the [gRPC API][api-docs], but in a way that doesn't impact other use cases.

## Removed features

Dex v2 lacks certain features present in v1. For the most part _we aim to add most of these features back into v2_, but in a way that installations have to _opt in_ to a feature instead of burdening every deployment with extra configuration.

Notable missing features include:

* Registration flows.
* Local user management.
* SMTP configuration and email verification.
* Several of the login connectors that have yet to be ported.

## Support for dex v1

Dex v1 will continue to live under the `github.com/dexidp/dex` repo on a branch. Bug fixes and minor changes will continue to be accepted, but development of new features by the dex team will largely cease.

[k8s-api-docs]: http://kubernetes.io/docs/api/
[storage-docs]: /docs/configuration/storage
[api-docs]: /docs/configuration/api



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/archive/integrations.md
================================================================================

---
title: "Integrations"
description: ""
date: 2020-09-30
draft: false
toc: true
weight: 1100
---

This document tracks the libraries and tools that are compatible with dex. [Join the community](https://github.com/dexidp/dex/), and help us keep the list up-to-date.

## Tools

## Projects with a dex dependency



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/development/_index.md
================================================================================

---
title: "Development"
description: "Dev Environment Setup, Testing, and Contributing to Dex"
date: 2020-12-09
draft: false
toc: false
weight: 3000
---

This section explains how you can develop for the Dex project and documents what steps need to be done at each phase of development (setting up the development environment, running tests, submitting changes, releasing software, etc).

Dex is an open source software (licensed under the Apache-2.0 license) and contributions (of any kind) are more than welcome from anyone in the community.



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/development/releases.md
================================================================================

---
title: "Releases"
description: ""
date: 2020-09-30
draft: false
toc: true
weight: 3100
---

Releasing a new version of Dex can be done by one of the core maintainers with push access to the
[git repository](https://github.com/dexidp/dex).
It's usually good to have an extra pair of eyes ready when tagging a new release though,
so feel free to ask a peer to be ready in case anything goes wrong or you need a review.

The release process is semi-automated at the moment: artifacts are automatically built and published to
GitHub Container Registry (primary source of container images) and Docker Hub.

The GitHub release needs to be manually created (use past releases as templates).

> *Note:* this will hopefully be improved in the future.


## Tagging a new release

Make sure you've [uploaded your GPG key](https://github.com/settings/keys) and
configured git to [use that signing key](
https://git-scm.com/book/en/v2/Git-Tools-Signing-Your-Work) either globally or
for the Dex repo. Note that the email the key is issued for must be the email
you use for git.

```bash
git config [--global] user.signingkey "{{ GPG key ID }}"
git config [--global] user.email "{{ Email associated with key }}"
```

Create a signed tag at the commit you wish to release.

```bash
RELEASE_VERSION=v2.0.0
git tag -s -m "Release $RELEASE_VERSION" $RELEASE_VERSION # optionally: commit hash as the last argument
```

Push that tag to the Dex repo.

```bash
git push origin $RELEASE_VERSION
```

Draft releases on GitHub and summarize the changes since the last release.
See [previous releases](https://github.com/dexidp/dex/releases) for the expected format.


## Patch releases

Occasionally, patch releases might be necessary to fix an urgent bug or vulnerability.

First, check if there is a release branch for a minor release. Create one if necessary:

```bash
MINOR_RELEASE="v2.1.0"
RELEASE_BRANCH="v2.1.x"
git checkout -b $RELEASE_BRANCH tags/$MINOR_RELEASE
git push origin $RELEASE_BRANCH
```

If a patch version is needed (2.1.1, 2.1.2, etc.), checkout the desired release branch and cherry pick specific commits.

```bash
RELEASE_BRANCH="v2.1.x"
git checkout $RELEASE_BRANCH
git checkout -b "cherry-picked-change"
git cherry-pick (SHA of change)
git push origin "cherry-picked-change"
```

Open a PR onto `$RELEASE_BRANCH` to get the changes approved.

Continue with the regular release process.

## Dex API

If there are changes in the API, the API version should be bumped to appear correctly in
the [pkg.go.dev](https://pkg.go.dev/github.com/dexidp/dex/api/v2) and be able to
be pulled by tags (via go get or go modules).

Create a new tag with the `api/` path:
```bash
RELEASE_VERSION=v2.3.0
git tag -s -m "${RELEASE_VERSION} Dex API release" "api/${RELEASE_VERSION}"
```

Push that tag to the Dex repo.

```bash
git push origin "api/${RELEASE_VERSION}"
```



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/development/integration-tests.md
================================================================================

---
title: "Running Integration Tests"
description: ""
date: 2020-09-30
draft: false
toc: true
weight: 3100
---

## Postgres

Running database tests locally requires:

* Docker

To run the database integration tests:

- start a postgres container:

  ```bash
  docker run --name dex-postgres -e POSTGRES_USER=postgres -e POSTGRES_DB=dex -p 5432:5432 -d postgres:11
  ```

- export the required environment variables:

  ```bash
  ```

- run the storage/sql tests:

  ```bash
  $ # sqlite3 takes forever to compile, be sure to install test dependencies
  $ go test -v -i ./storage/sql
  $ go test -v ./storage/sql
  ```

- clean up the postgres container: 

  ```bash
  docker rm -f dex-postgres
  ```

## Etcd

These tests can also be executed using docker:

- start the container (where `NODE1` is set to the host IP address):

  ```bash
  $ export NODE1=0.0.0.0
  $ docker run --name dex-etcd -p 2379:2379 -p 2380:2380 gcr.io/etcd-development/etcd:v3.3.10 \
    /usr/local/bin/etcd --name node1 \
    --initial-advertise-peer-urls http://${NODE1}:2380 --listen-peer-urls http://${NODE1}:2380 \
    --advertise-client-urls http://${NODE1}:2379 --listen-client-urls http://${NODE1}:2379 \
    --initial-cluster node1=http://${NODE1}:2380
  ```

- run the tests, passing the correct endpoint for this etcd instance in `DEX_ETCD_ENDPOINTS`:

  ```bash
  DEX_ETCD_ENDPOINTS=http://localhost:2379 go test -v ./storage/etcd
  ```
- clean up the etcd container: `docker rm -f dex-etcd`

## Kubernetes

Running integration tests for Kubernetes storage requires the `DEX_KUBERNETES_CONFIG_PATH` environment variable
be set with the path to kubeconfig file of the existing cluster. For tests, it is ok to use "mini" Kubernetes distributive, e.g., [KinD][kind], [Microk8s][microk8s].

Example KinD cluster test run:

* Install KinD using the instructions from the [official website][kind-install].

* Run tests by executing the following commands:
  ```bash
  kind create cluster --kubeconfig "$DEX_KUBERNETES_CONFIG_PATH"

  go test -v ./storage/kubernetes
  ```
* To clean up, run:
  ```bash
  rm -f "$DEX_KUBERNETES_CONFIG_PATH"
  unset DEX_KUBERNETES_CONFIG_PATH
  
  kind delete cluster
  ```

## LDAP

The LDAP integration tests require [OpenLDAP][openldap] installed on the host machine. To run them, use `go test`:

```bash
go test -v ./connector/ldap/
```

To quickly stand up a LDAP server for development, see the LDAP [_"Getting started"_](/docs/connectors/ldap/#getting-started) example. This also requires OpenLDAP installed on the host.

To stand up a containerized LDAP server run the OpenLDAP docker image:

```bash
$ sudo docker run --hostname ldap.example.org --name openldap-container --detach osixia/openldap:1.1.6
```

By default TLS is enabled and a certificate is created with the container hostname, which in this case is "ldap.example.org". It will create an empty LDAP for the company Example Inc. and the domain example.org. By default the admin has the password admin.

Add new users and groups (sample .ldif file included at the end):

```bash
$ sudo docker exec openldap-container ldapadd -x -D "cn=admin,dc=example,dc=org" -w admin -f <path to .ldif> -h ldap.example.org -ZZ
```

Verify that the added entries are in your directory with ldapsearch :

```bash
$ sudo docker exec openldap-container ldapsearch -x -h localhost -b dc=example,dc=org -D "cn=admin,dc=example,dc=org" -w admin
```
The .ldif file should contain seed data. Example file contents:

```bash
dn: cn=Test1,dc=example,dc=org
objectClass: organizationalRole
cn: Test1

dn: cn=Test2,dc=example,dc=org
objectClass: organizationalRole
cn: Test2

dn: ou=groups,dc=example,dc=org
ou: groups
objectClass: top
objectClass: organizationalUnit

dn: cn=tstgrp,ou=groups,dc=example,dc=org
objectClass: top
objectClass: groupOfNames
member: cn=Test1,dc=example,dc=org
cn: tstgrp
```

## SAML

### Okta

The Okta identity provider supports free accounts for developers to test their implementation against. This document describes configuring an Okta application to test dex's SAML connector.

First, [sign up for a developer account][okta-sign-up]. Then, to create a SAML application:

* Go to the admin screen.
* Click "Add application"
* Click "Create New App"
* Choose "SAML 2.0" and press "Create"
* Configure SAML
  * Enter `http://127.0.0.1:5556/dex/callback` for "Single sign on URL"
  * Enter `http://127.0.0.1:5556/dex/callback` for "Audience URI (SP Entity ID)"
  * Under "ATTRIBUTE STATEMENTS (OPTIONAL)" add an "email" and "name" attribute. The values should be something like `user:email` and `user:firstName`, respectively.
  * Under "GROUP ATTRIBUTE STATEMENTS (OPTIONAL)" add a "groups" attribute. Use the "Regexp" filter `.*`.

After the application's created, assign yourself to the app.

* "Applications" > "Applications"
* Click on your application then under the "People" tab press the "Assign to People" button and add yourself.

At the app, go to the "Sign On" tab and then click "View Setup Instructions". Use those values to fill out the following connector in `examples/config-dev.yaml`.

```yaml
connectors:
- type: saml
  id: saml
  name: Okta
  config:
    ssoURL: ( "Identity Provider Single Sign-On URL" )
    caData: ( base64'd value of "X.509 Certificate" )
    redirectURI: http://127.0.0.1:5556/dex/callback
    usernameAttr: name
    emailAttr: email
    groupsAttr: groups
```

Start both dex and the example app, and try logging in (requires not requesting a refresh token).

[kind]: https://github.com/kubernetes-sigs/kind/
[kind-install]: https://kind.sigs.k8s.io/docs/user/quick-start/#installation
[microk8s]: https://github.com/ubuntu/microk8s
[okta-sign-up]: https://www.okta.com/developer/signup/
[openldap]: https://www.openldap.org/



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/configuration/_index.md
================================================================================

---
title: "Configuration"
description: "Configuring general settings for Dex"
date: 2020-01-07T14:59:38+01:00
draft: false
toc: true
weight: 2000
---



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/configuration/storage.md
================================================================================

---
title: "Storage"
description: "Configuration options for persistent data storage"
date: 2020-09-30
draft: false
toc: true
weight: 1050
---

Dex requires persisting state to perform various tasks such as track refresh tokens, preventing replays, and rotating keys. This document is a summary of the storage configurations supported by dex.

Storage breaches are serious as they can affect applications that rely on dex. Dex saves sensitive data in its backing storage, including signing keys and bcrypt'd passwords. As such, transport security and database ACLs should both be used, no matter which storage option is chosen.

## Etcd

Dex supports persisting state to [etcd v3](https://github.com/coreos/etcd).

An example etcd configuration is using these values:

```yaml
storage:
  type: etcd
  config:
    # list of etcd endpoints we should connect to
    endpoints:
      - http://localhost:2379
    namespace: my-etcd-namespace/
```

Etcd storage can be customized further using the following options:

* `endpoints`: list of etcd endpoints we should connect to
* `namespace`: etcd namespace to be set for the connection. All keys created by
  etcd storage will be prefixed with the namespace. This is useful when you
  share your etcd cluster amongst several applications. Another approach for
  setting namespace is to use [etcd proxy](https://coreos.com/etcd/docs/latest/op-guide/grpc_proxy.html#namespacing)
* `username`: username for etcd authentication
* `password`: password for etcd authentication
* `ssl`: ssl setup for etcd connection
  * `serverName`: ensures that the certificate matches the given hostname the
    client is connecting to.
  * `caFile`: path to the ca
  * `keyFile`: path to the private key
  * `certFile`: path to the certificate

## Kubernetes custom resource definitions (CRDs)

Kubernetes [custom resource definitions](https://kubernetes.io/docs/tasks/access-kubernetes-api/extend-api-custom-resource-definitions/) are a way for applications to create new resources types in the Kubernetes API.

The Custom Resource Definition (CRD) API object was introduced in Kubernetes version 1.7 to replace the Third Party Resource (TPR) extension. CRDs allow dex to run on top of an existing Kubernetes cluster without the need for an external database. While this storage may not be appropriate for a large number of users, it's extremely effective for many Kubernetes use cases.

The rest of this section will explore internal details of how dex uses CRDs. __Admins should not interact with these resources directly__, except while debugging. These resources are only designed to store state and aren't meant to be consumed by end users. For modifying dex's state dynamically see the [API documentation](/docs/api/).

The following is an example of the AuthCode resource managed by dex:

```yaml
apiVersion: apiextensions.k8s.io/v1beta1
kind: CustomResourceDefinition
metadata:
  creationTimestamp: 2017-09-13T19:56:28Z
  name: authcodes.dex.coreos.com
  resourceVersion: "288893"
  selfLink: /apis/apiextensions.k8s.io/v1beta1/customresourcedefinitions/authcodes.dex.coreos.com
  uid: a1cb72dc-98bd-11e7-8f6a-02d13336a01e
spec:
  group: dex.coreos.com
  names:
    kind: AuthCode
    listKind: AuthCodeList
    plural: authcodes
    singular: authcode
  scope: Namespaced
  version: v1
status:
  acceptedNames:
    kind: AuthCode
    listKind: AuthCodeList
    plural: authcodes
    singular: authcode
  conditions:
  - lastTransitionTime: null
    message: no conflicts found
    reason: NoConflicts
    status: "True"
    type: NamesAccepted
  - lastTransitionTime: 2017-09-13T19:56:28Z
    message: the initial names have been accepted
    reason: InitialNamesAccepted
    status: "True"
    type: Established
```

Once the `CustomResourceDefinition` is created, custom resources can be created and stored at a namespace level. The CRD type and the custom resources can be queried, deleted, and edited like any other resource using `kubectl`.

dex requires access to the non-namespaced `CustomResourceDefinition` type. For example, clusters using RBAC authorization would need to create the following roles and bindings:
```yaml
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRole
metadata:
  name: dex
rules:
- apiGroups: ["dex.coreos.com"] # API group created by dex
  resources: ["*"]
  verbs: ["*"]
- apiGroups: ["apiextensions.k8s.io"]
  resources: ["customresourcedefinitions"]
  verbs: ["create"] # To manage its own resources identity must be able to create customresourcedefinitions.
---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: dex
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: dex
subjects:
- kind: ServiceAccount
  name: dex                 # Service account assigned to the dex pod.
  namespace: dex-namespace  # The namespace dex is running in.
```


### Removed: Kubernetes third party resources(TPRs)

TPR support in dex has been removed.  The last version to support TPR
is [v2.17.0](https://github.com/dexidp/dex/tree/v2.17.0)

If you are currently running dex using TPRs, you will need to [migrate to CRDs](https://github.com/dexidp/dex/blob/v2.17.0/Documentation/storage.md#migrating-from-tprs-to-crds) before you upgrade to a post v2.17 dex.  The script mentioned in the instructions can be [found here](https://github.com/dexidp/dex/blob/v2.17.0/scripts/dump-tprs)

### Configuration

The storage configuration is extremely limited since installations running outside a Kubernetes cluster would likely prefer a different storage option. An example configuration for dex running inside Kubernetes:

```yaml
storage:
  type: kubernetes
  config:
    inCluster: true
```

Dex determines the namespace it's running in by parsing the service account token automatically mounted into its pod.

## SQL

Dex supports three flavors of SQL: SQLite3, Postgres and MySQL.

Migrations are performed automatically on the first connection to the SQL server (it does not support rolling back). Because of this dex requires privileges to add and alter the tables for its database.

__NOTE:__ Previous versions of dex required symmetric keys to encrypt certain values before sending them to the database. This feature has not yet been ported to dex v2. If it is added later there may not be a migration path for current v2 users.

### SQLite3

SQLite3 is the recommended storage for users who want to stand up dex quickly. It is __not__ appropriate for real workloads.

The SQLite3 configuration takes a single argument, the database file.

```yaml
storage:
  type: sqlite3
  config:
    file: /var/dex/dex.db
```

Because SQLite3 uses file locks to prevent race conditions, if the ":memory:" value is provided dex will automatically disable support for concurrent database queries.

### Postgres

When using Postgres, admins may want to dedicate a database to dex for the following reasons:

1. Dex requires privileged access to its database because it performs migrations.
2. Dex's database table names are not configurable; when shared with other applications there may be table name clashes.

```postgres
CREATE DATABASE dex_db;
CREATE USER dex WITH PASSWORD '66964843358242dbaaa7778d8477c288';
GRANT ALL PRIVILEGES ON DATABASE dex_db TO dex;
```

An example config for Postgres setup using these values:

```yaml
storage:
  type: postgres
  config:
    host: localhost
    port: 5432
    database: dex_db
    user: dex
    password: 66964843358242dbaaa7778d8477c288
    ssl:
      mode: verify-ca
      caFile: /etc/dex/postgres.ca
```

The SSL "mode" corresponds to the `github.com/lib/pq` package [connection options][psql-conn-options]. If unspecified, dex defaults to the strictest mode "verify-full".

### MySQL

Dex requires MySQL 5.7 or later version. When using MySQL, admins may want to dedicate a database to dex for the following reasons:

1. Dex requires privileged access to its database because it performs migrations.
2. Dex's database table names are not configurable; when shared with other applications there may be table name clashes.

```sql
CREATE DATABASE dex_db;
CREATE USER dex IDENTIFIED BY '66964843358242dbaaa7778d8477c288';
GRANT ALL PRIVILEGES ON dex_db.* TO dex;
```

An example config for MySQL setup using these values:

```yaml
storage:
  type: mysql
  config:
    database: dex_db
    user: dex
    password: 66964843358242dbaaa7778d8477c288
    ssl:
      mode: custom
      caFile: /etc/dex/mysql.ca
```

The SSL "mode" corresponds to the `github.com/go-sql-driver/mysql` package [connection options][mysql-conn-options]. If unspecified, dex defaults to the strictest mode "true".

## Adding a new storage options

Each storage implementation bears a large ongoing maintenance cost and needs to be updated every time a feature requires storing a new type. Bugs often require in depth knowledge of the backing software, and much of this work will be done by developers who are not the original author. Changes to dex which add new storage implementations require a strong use case to be considered for inclusion.

### New storage option references

Those who still want to construct a proposal for a new storage should review the following packages:

* `github.com/dexidp/dex/storage`: Interface definitions which the storage must implement. __NOTE:__ This package is not stable.
* `github.com/dexidp/dex/storage/conformance`: Conformance tests which storage implementations must pass.

### New storage option requirements

Any proposal to add a new implementation must address the following:

* Integration testing setups (Travis and developer workstations).
* Transactional requirements: atomic deletes, updates, etc.
* Is there an established and reasonable Go client?

[issues-transaction-tests]: https://github.com/dexidp/dex/issues/600
[k8s-api]: https://github.com/kubernetes/kubernetes/blob/master/docs/devel/api-conventions.md#concurrency-control-and-consistency
[psql-conn-options]: https://godoc.org/github.com/lib/pq#hdr-Connection_String_Parameters
[mysql-conn-options]: https://github.com/go-sql-driver/mysql#tls



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/configuration/api.md
================================================================================

---
title: "The Dex API"
linkTitle: "gRPC API"
description: "Configure Dex dynamically with the gRPC API"
date: 2020-09-30
draft: false
toc: true
weight: 1060
---

Dex provides a [gRPC](http://www.grpc.io/) service for programmatic modification of dex's state.
The API is intended to expose hooks for management applications and is not expected to be used by most installations.

This document is an overview of how to interact with the API.


## Configuration

Admins that wish to expose the gRPC service must add the following entry to the dex config file. This option is off by default.

```yaml
grpc:
  # Cannot be the same address as an HTTP(S) service.
  addr: 127.0.0.1:5557

  # Server certs. If TLS credentials aren't provided dex will run in plaintext (HTTP) mode.
  tlsCert: /etc/dex/grpc.crt
  tlsKey: /etc/dex/grpc.key

  # Client auth CA.
  tlsClientCA: /etc/dex/client.crt

  # enable reflection
  reflection: true
```


## Clients

gRPC is a suite of tools for generating client and server bindings from a common declarative language.
The canonical schema for Dex's API can be found in the source tree at [`api/v2/api.proto`](https://github.com/dexidp/dex/blob/master/api/v2/api.proto).
Go bindings are generated and maintained in the same directory for both public and internal use.


### Go

A Go project can import the API module directly, without having to import the entire project:

```bash
go get github.com/dexidp/dex/api/v2
```

The client then can be used as follows:

```go
package main

    "context"
    "fmt"
    "log"

    "github.com/dexidp/dex/api/v2"
    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials"
)

func newDexClient(hostAndPort, caPath string) (api.DexClient, error) {
    creds, err := credentials.NewClientTLSFromFile(caPath, "")
    if err != nil {
        return nil, fmt.Errorf("load dex cert: %v", err)
    }

    conn, err := grpc.Dial(hostAndPort, grpc.WithTransportCredentials(creds))
    if err != nil {
        return nil, fmt.Errorf("dial: %v", err)
    }
    return api.NewDexClient(conn), nil
}

func main() {
    client, err := newDexClient("127.0.0.1:5557", "/etc/dex/grpc.crt")
    if err != nil {
        log.Fatalf("failed creating dex client: %v ", err)
    }

    req := &api.CreateClientReq{
        Client: &api.Client{
            Id:           "example-app",
            Name:         "Example App",
            Secret:       "ZXhhbXBsZS1hcHAtc2VjcmV0",
            RedirectUris: []string{"http://127.0.0.1:5555/callback"},
        },
    }

    if _, err := client.CreateClient(context.TODO(), req); err != nil {
        log.Fatalf("failed creating oauth2 client: %v", err)
    }
}
```

A clear working example of the Dex gRPC client for Go can be found [here](https://github.com/dexidp/dex/tree/master/examples/grpc-client/README.md).


### Other languages

To generate a client for your own project install [`protoc`](https://github.com/google/protobuf/releases),
install a protobuf generator for your project's language, and download the `api.proto` file.

Here is an example:

```bash
# Download api.proto for a given version.
$ DEX_VERSION=v2.24.0
$ wget https://raw.githubusercontent.com/dexidp/dex/${DEX_VERSION}/api/v2/api.proto

# Generate the client bindings.
$ protoc [YOUR LANG PARAMS] api.proto
```

Client programs can then be written using the generated code.


## Authentication and access control

The Dex API does not provide any authentication or authorization beyond TLS client auth.

Projects that wish to add access controls on top of the existing API should build apps which perform such checks.
For example to provide a "Change password" screen, a client app could use Dex's OpenID Connect flow to authenticate an end user,
then call Dex's API to update that user's password.


## dexctl?

Dex does not ship with a command line tool for interacting with the API.
Command line tools are useful but hard to version, easy to design poorly,
and expose another interface which can never be changed in the name of compatibility.

While the Dex team would be open to re-implementing `dexctl` for v2 a majority of the work is writing a design document,
not the actual programming effort.


## Why not REST or gRPC Gateway?

Between v1 and v2, Dex switched from REST to gRPC. This largely stemmed from problems generating documentation,
client bindings, and server frameworks that adequately expressed REST semantics.
While [Google APIs](https://github.com/google/apis-client-generator), [Open API/Swagger](https://openapis.org/),
and [gRPC Gateway](https://github.com/grpc-ecosystem/grpc-gateway) were evaluated,
they often became clunky when trying to use specific HTTP error codes or complex request bodies.
As a result, v2's API is entirely gRPC.

Many arguments _against_ gRPC cite short term convenience rather than production use cases.
Though this is a recognized shortcoming, Dex already implements many features for developer convenience.
For instance, users who wish to manually edit clients during testing can use the `staticClients` config field instead of the API.



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/guides/_index.md
================================================================================

---
title: "Guides"
description: "Most common scenarios and how to solve them"
date: 2020-01-07T14:59:38+01:00
draft: false
toc: true
weight: 2000
---



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/guides/kubernetes.md
================================================================================

---
title: "Kubernetes Authentication Through Dex"
linkTitle: "Using Kubernetes with Dex"
description: ""
date: 2020-09-30
draft: false
toc: true
weight: 1070
---

## Overview

This document covers setting up the [Kubernetes OpenID Connect token authenticator plugin][k8s-oidc] with dex.
It also contains a worked example showing how the Dex server can be deployed within Kubernetes.

Token responses from OpenID Connect providers include a signed JWT called an ID Token. ID Tokens contain names, emails, unique identifiers, and in dex's case, a set of groups that can be used to identify the user. OpenID Connect providers, like dex, publish public keys; the Kubernetes API server understands how to use these to verify ID Tokens.

The authentication flow looks like:

1. OAuth2 client logs a user in through dex.
2. That client uses the returned ID Token as a bearer token when talking to the Kubernetes API.
3. Kubernetes uses dex's public keys to verify the ID Token.
4. A claim designated as the username (and optionally group information) will be associated with that request.

Username and group information can be combined with Kubernetes [authorization plugins][k8s-authz], such as role based access control (RBAC), to enforce policy.

## Configuring Kubernetes

Things to know before the start: 

* Dex has to be running on HTTPS.
  * Custom CA files must be accessible by the API server.
* Dex must be accessible to both your browser and the Kubernetes API server.
* The API server doesn't require dex to be available upfront.
  * Other authenticators, such as client certs, can still be used.
  * Dex doesn't need to be running when you start your API server.
* If a claim other than "email" is used for the username, for example, "sub", it will be prefixed by `"issuer-url"`. This is to namespace user-controlled claims which may be used for privilege escalation.
* The `/etc/ssl/certs/openid-ca.pem` used here is the CA from the [generated TLS assets](#generate-tls-assets), and is assumed to be present on the cluster nodes.

**Flow:** 

At the beginning, kube-apiserver will fetch Dex keys to validate signatures of bearer tokens. When there is a bearer token in the request, kube-apiserver:

1. Checks the token signature.
2. Makes an expiration check.
3. Validates claims (aud, iss).
4. Gets subject attributes from token claims.

Starting from Kubernetes v1.30.x, there are two options to connect Dex to your Kubernetes cluster:

### Using StructuredAuthenticationConfiguration

This is a structured configuration file that can be used to set up authenticator that will use Dex to validate incoming bearer tokens. You can find details about all the options and how the authenticator works by following [this link][structured-auth-config].

Steps to connect Dex:

1. Create a configuration file with the following content:

```yaml
# apiVersion can ends with the v1 / v1beta1 or v1alpha1 depending on your Kubernetes version
apiVersion: apiserver.config.k8s.io/v1beta1
kind: AuthenticationConfiguration
jwt:
- issuer:
    url: https://dex.example.com:32000
    audiences:
    - example-app
    # cat /etc/ssl/certs/openid-ca.pem | base64 -w0
    certificateAuthority: ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789
  claimMappings:
    username:
      claim: email
    groups:
      claim: groups
  userValidationRules:
  - expression: "!user.username.startsWith('system:')"
    message: "username cannot use reserved system: prefix"
```

2. Use the `--authentication-config=/path-to-your-config` flag for the `kube-apiserver` to apply the config.

### Using the OpenID Connect authenticator

Configuring the API server to use the OpenID Connect [authentication plugin][k8s-oidc] is possible for all Kubernetes versions.

Use the following flags to point your API server(s) at Dex. `dex.example.com` should be replaced by whatever DNS name or IP address Dex is running under.

```bash
--oidc-issuer-url=https://dex.example.com:32000
--oidc-client-id=example-app
--oidc-ca-file=/etc/ssl/certs/openid-ca.pem
--oidc-username-claim=email
--oidc-groups-claim=groups
```

Additional notes:
* Kubernetes configured with the `oidc` flags can only trusts ID Tokens issued to a single client.
  * As a workaround dex allows clients to [trust other clients][trusted-peers] to mint tokens on their behalf.

## Deploying dex on Kubernetes

The dex repo contains scripts for running dex on a Kubernetes cluster with authentication through GitHub. The dex service is exposed using a [node port][node-port] on port 32000. This likely requires a custom `/etc/hosts` entry pointed at one of the cluster's workers.

Because dex uses [CRDs](https://kubernetes.io/docs/tasks/access-kubernetes-api/custom-resources/custom-resource-definitions/) to store state, no external database is needed. For more details see the [storage documentation](/docs/configuration/storage/#kubernetes-custom-resource-definitions-crds).

There are many different ways to spin up a Kubernetes development cluster, each with different host requirements and support for API server reconfiguration. At this time, this guide does not have copy-pastable examples, but can recommend the following methods for spinning up a cluster:

* [coreos-kubernetes][coreos-kubernetes] repo for vagrant and VirtualBox users.
* [coreos-baremetal][coreos-baremetal] repo for Linux QEMU/KVM users.

To run dex on Kubernetes perform the following steps:

1. Generate TLS assets for dex.
2. Spin up a Kubernetes cluster with the appropriate flags and CA volume mount.
3. Create secrets for TLS and for your [GitHub OAuth2 client credentials][github-oauth2].
4. Deploy dex.

### Generate TLS assets

Running Dex with HTTPS enabled requires a valid SSL certificate, and the API server needs to trust the certificate of the signing CA using the `--oidc-ca-file` flag.

For our example use case, the TLS assets can be created using the following command:

```bash
$ cd examples/k8s
$ ./gencert.sh
```

This will generate several files under the `ssl` directory, the important ones being `cert.pem` ,`key.pem` and `ca.pem`. The generated SSL certificate is for 'dex.example.com', although you could change this by editing `gencert.sh` if required.

### Configure the API server

#### Ensure the CA certificate is available to the API server


The CA file which was used to sign the SSL certificates for Dex needs to be copied to a location where the API server can read it, and the API server configured to look for it with the flag `--oidc-ca-file`.

There are several options here but if you run your API server as a container probably the easiest method is to use a [hostPath](https://kubernetes.io/docs/concepts/storage/volumes/#hostpath) volume to mount the CA file directly from the host.

The example pod manifest below assumes that you copied the CA file into `/etc/ssl/certs`. Adjust as necessary:

```yaml
spec:
  containers:

    [...]

    volumeMounts:
    - mountPath: /etc/ssl/certs
      name: etc-ssl-certs
      readOnly: true

    [...]

  volumes:
   - name: ca-certs
     hostPath:
       path: /etc/ssl/certs
       type: DirectoryOrCreate
```

Depending on your installation you may also find that certain folders are already mounted in this way and that you can simply copy the CA file into an existing folder for the same effect.

#### Configure API server flags

Configure the API server as in [Configuring the OpenID Connect Plugin](#configuring-the-openid-connect-plugin) above.

Note that the `ca.pem` from above has been renamed to `openid-ca.pem` in this example - this is just to separate it from any other CA certificates that may be in use.

### Create cluster secrets

Once the cluster is up and correctly configured, use kubectl to add the serving certs as secrets.

```bash
$ kubectl -n dex create secret tls dex.example.com.tls --cert=ssl/cert.pem --key=ssl/key.pem
```

Then create a secret for the GitHub OAuth2 client.

```bash
$ kubectl -n dex create secret \
    generic github-client \
    --from-literal=client-id=$GITHUB_CLIENT_ID \
    --from-literal=client-secret=$GITHUB_CLIENT_SECRET
```

### Deploy the Dex server

Create the dex deployment, configmap, and node port service. This will also create RBAC bindings allowing the Dex pod access to manage [Custom Resource Definitions](/docs/configuration/storage/#kubernetes-custom-resource-definitions-crds) within Kubernetes.

```bash
$ kubectl create -f dex.yaml
```

## Logging into the cluster

The `example-app` can be used to log into the cluster and get an ID Token. To build the app, run the following commands:

```bash
cd examples/example-app
go install .
```

To build the `example-app` requires at least a 1.7 version of Go.

```bash
$ example-app --issuer https://dex.example.com:32000 --issuer-root-ca examples/k8s/ssl/ca.pem
```

Please note that the `example-app` will listen at http://127.0.0.1:5555 and can be changed with the `--listen` flag.

Once the example app is running, open a browser and go to http://127.0.0.1:5555

A page appears with fields such as scope and client-id. For the most basic case these are not required, so leave the form blank. Click login.

On the next page, choose the GitHub option and grant access to dex to view your profile.

The default redirect uri is http://127.0.0.1:5555/callback and can be changed with the `--redirect-uri` flag and should correspond with your configmap.

Please note the redirect uri is different from the one you filled when creating `GitHub OAuth2 client credentials`.
When you login, GitHub first redirects to dex (https://dex.example.com:32000/callback), then dex redirects to the redirect uri of example-app.

The printed "ID Token" can then be used as a bearer token to authenticate against the API server.

```bash
$ token='(id token)'
$ curl -H "Authorization: Bearer $token" -k https://( API server host ):443/api/v1/nodes
```

In the kubeconfig file ~/.kube/config, the format is:
```yaml
users:
- name: (USERNAME)
  user:
    token: (ID-TOKEN)
```

[k8s-authz]: https://kubernetes.io/docs/reference/access-authn-authz/authorization/
[k8s-oidc]: https://kubernetes.io/docs/reference/access-authn-authz/authentication/#openid-connect-tokens
[trusted-peers]: https://godoc.org/github.com/dexidp/dex/storage#Client
[coreos-kubernetes]: https://github.com/coreos/coreos-kubernetes/
[coreos-baremetal]: https://github.com/coreos/coreos-baremetal/
[github-oauth2]: https://github.com/settings/applications/new
[node-port]: https://kubernetes.io/docs/concepts/services-networking/service/#type-nodeport
[coreos-kubernetes]: https://github.com/coreos/coreos-kubernetes
[coreos-baremetal]: https://github.com/coreos/coreos-baremetal
[structured-auth-config]: https://kubernetes.io/docs/reference/access-authn-authz/authentication/#using-authentication-configuration



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/guides/templates.md
================================================================================

---
title: "Customizing Dex Templates"
description: ""
date: 2020-09-30
toc: true
weight: 1100
---

## Using your own templates

Dex supports using your own templates and passing arbitrary data to them to help customize your installation.

Steps:

1. Copy contents of the `web` directory over to a new directory.
1. Customize the templates as needed, be sure to retain all the existing variables so Dex continues working correctly.
  (Use the following syntax to render values from `frontend.extra` config: `{{ "your_key" | extra }}`)
1. Set the `frontend.dir` value to your own `web` directory (Alternatively, you can set the `DEX_FRONTEND_DIR` environment variable).
1. Add your custom data to the Dex configuration `frontend.extra`. (optional)
1. Change the issuer by setting the `frontend.issuer` config in order to modify the Dex title and the `Log in to <<dex>>` tag. (optional)
1. Create a custom theme for your templates in the `themes` directory. (optional)

Here is an example configuration:

```yaml
frontend:
  dir: /path/to/custom/web
  issuer: my-dex
  extra:
    tos_footer_link: "https://example.com/terms"
    client_logo_url: "../theme/client-logo.png"
    foo: "bar"
```

To test your templates simply run Dex with a valid configuration and go through a login flow.


## Customize the official container image

Dex is primarily distributed as a container image.
The above guide explains how to customize the templates for any Dex instance.

You can combine that with a custom `Dockerfile` to ease the deployment of those custom templates:

```dockerfile
FROM ghcr.io/dexidp/dex:latest

ENV DEX_FRONTEND_DIR=/srv/dex/web

COPY --chown=root:root web /srv/dex/web
```

Using the snippet above, you can avoid setting the `frontend.dir` config.



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/guides/using-dex.md
================================================================================

---
title: "Writing Apps That Use Dex"
description: ""
date: 2020-09-30
draft: false
toc: true
weight: 1017
---

Once you have dex up and running, the next step is to write applications that use dex to drive authentication. Apps that interact with dex generally fall into one of two categories:

1. Apps that request OpenID Connect ID tokens to authenticate users.
    * Used for authenticating an end user.
    * Must be web based.
2. Apps that consume ID tokens from other apps.
    * Needs to verify that a client is acting on behalf of a user.

The first category of apps are standard OAuth2 clients. Users show up at a website, and the application wants to authenticate those end users by pulling claims out of the ID token.

The second category of apps consume ID tokens as credentials. This lets another service handle OAuth2 flows, then use the ID token retrieved from dex to act on the end user's behalf with the app. An example of an app that falls into this category is the [Kubernetes API server][api-server].

## Requesting an ID token from dex

Apps that directly use dex to authenticate a user use OAuth2 code flows to request a token response. The exact steps taken are:

* User visits client app.
* Client app redirects user to dex with an OAuth2 request.
* Dex determines user's identity.
* Dex redirects user to client with a code.
* Client exchanges code with dex for an id_token.

![Dex flow](/img/dex-flow.png)

The dex repo contains a small [example app][example-app] as a working, self contained app that performs this flow.

The rest of this section explores the code sections which help explain how to implement this logic in your own app.

### Configuring your app

The example app uses the following Go packages to perform the code flow:

* [github.com/coreos/go-oidc][go-oidc]
* [golang.org/x/oauth2][go-oauth2]

First, client details should be present in the dex configuration. For example, we could register an app with dex with the following section:

```yaml
staticClients:
- id: example-app
  secret: example-app-secret
  name: 'Example App'
  # Where the app will be running.
  redirectURIs:
  - 'http://127.0.0.1:5555/callback'
```

In this case, the Go code would be configured as:

```go
// Initialize a provider by specifying dex's issuer URL.
provider, err := oidc.NewProvider(ctx, "https://dex-issuer-url.com")
if err != nil {
    // handle error
}

// Configure the OAuth2 config with the client values.
oauth2Config := oauth2.Config{
    // client_id and client_secret of the client.
    ClientID:     "example-app",
    ClientSecret: "example-app-secret",

    // The redirectURL.
    RedirectURL: "http://127.0.0.1:5555/callback",

    // Discovery returns the OAuth2 endpoints.
    Endpoint: provider.Endpoint(),

    // "openid" is a required scope for OpenID Connect flows.
    //
    // Other scopes, such as "groups" can be requested.
    Scopes: []string{oidc.ScopeOpenID, "profile", "email", "groups"},
}

// Create an ID token parser.
idTokenVerifier := provider.Verifier(&oidc.Config{ClientID: "example-app"})
```

The HTTP server should then redirect unauthenticated users to dex to initialize the OAuth2 flow.

```go
// handleRedirect is used to start an OAuth2 flow with the dex server.
func handleRedirect(w http.ResponseWriter, r *http.Request) {
    state := newState()
    http.Redirect(w, r, oauth2Config.AuthCodeURL(state), http.StatusFound)
}
```

After dex verifies the user's identity it redirects the user back to the client app with a code that can be exchanged for an ID token. The ID token can then be parsed by the verifier created above. This immediately 

```go
func handleOAuth2Callback(w http.ResponseWriter, r *http.Request) {
    state := r.URL.Query().Get("state")

    // Verify state.

    oauth2Token, err := oauth2Config.Exchange(ctx, r.URL.Query().Get("code"))
    if err != nil {
        // handle error
    }

    // Extract the ID Token from OAuth2 token.
    rawIDToken, ok := oauth2Token.Extra("id_token").(string)
    if !ok {
        // handle missing token
    }

    // Parse and verify ID Token payload.
    idToken, err := idTokenVerifier.Verify(ctx, rawIDToken)
    if err != nil {
        // handle error
    }

    // Extract custom claims.
    var claims struct {
        Email    string   `json:"email"`
        Verified bool     `json:"email_verified"`
        Groups   []string `json:"groups"`
    }
    if err := idToken.Claims(&claims); err != nil {
        // handle error
    }
}
```

### State tokens

The state parameter is an arbitrary string that dex will always return with the callback. It plays a security role, preventing certain kinds of OAuth2 attacks. Specifically it can be used by clients to ensure:

* The user who started the flow is the one who finished it, by linking the user's session with the state token. For example, by setting the state as an HTTP cookie, then comparing it when the user returns to the app.
* The request hasn't been replayed. This could be accomplished by associating some nonce in the state.

A more thorough discussion of these kinds of best practices can be found in the [_"OAuth 2.0 Threat Model and Security Considerations"_][oauth2-threat-model] RFC.

## Consuming ID tokens

Apps can also choose to consume ID tokens, letting other trusted clients handle the web flows for login. Clients pass along the ID tokens they receive from dex, usually as a bearer token, letting them act as the user to the backend service.

![Dex backend flow](/img/dex-backend-flow.png)

To accept ID tokens as user credentials, an app would construct an OpenID Connect verifier similarly to the above example. The verifier validates the ID token's signature, ensures it hasn't expired, etc. An important part of this code is that the verifier only trusts the example app's client. This ensures the example app is the one who's using the ID token, and not another, untrusted client.

```go
// Initialize a provider by specifying dex's issuer URL.
provider, err := oidc.NewProvider(ctx, "https://dex-issuer-url.com")
if err != nil {
    // handle error
}
// Create an ID token parser, but only trust ID tokens issued to "example-app"
idTokenVerifier := provider.Verifier(&oidc.Config{ClientID: "example-app"})
```

The verifier can then be used to pull user info out of tokens:

```go
type user struct {
    email  string
    groups []string
}

// authorize verifies a bearer token and pulls user information form the claims.
func authorize(ctx context.Context, bearerToken string) (*user, error) {
    idToken, err := idTokenVerifier.Verify(ctx, bearerToken)
    if err != nil {
        return nil, fmt.Errorf("could not verify bearer token: %v", err)
    }
    // Extract custom claims.
    var claims struct {
        Email    string   `json:"email"`
        Verified bool     `json:"email_verified"`
        Groups   []string `json:"groups"`
    }
    if err := idToken.Claims(&claims); err != nil {
        return nil, fmt.Errorf("failed to parse claims: %v", err)
    }
    if !claims.Verified {
        return nil, fmt.Errorf("email (%q) in returned claims was not verified", claims.Email)
    }
    return &user{claims.Email, claims.Groups}, nil
}
```

[api-server]: https://kubernetes.io/docs/reference/access-authn-authz/authentication/#openid-connect-tokens
[dex-flow]: img/dex-flow.png
[dex-backend-flow]: img/dex-backend-flow.png
[example-app]: https://github.com/dexidp/dex/tree/master/examples/example-app
[oauth2-threat-model]: https://tools.ietf.org/html/rfc6819
[go-oidc]: https://godoc.org/github.com/coreos/go-oidc
[go-oauth2]: https://godoc.org/golang.org/x/oauth2



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/guides/kubelogin-activedirectory.md
================================================================================

---
title: "Integration kubelogin and Active Directory"
linkTitle: "Integration kubelogin and Active Directory"
description: ""
date: 2020-09-30
draft: false
toc: true
weight: 2140
---

## Overview

kubelogin is helper tool for kubernetes and oidc integration.
It makes easy to login Open ID Provider.
This document describes how dex work with kubelogin and Active Directory.

examples/config-ad-kubelogin.yaml is sample configuration to integrate Active Directory and kubelogin.

## Precondition

1. Active Directory
You should have Active Directory or LDAP has Active Directory compatible schema such as samba ad.
You may have user objects and group objects in AD. Please ensure TLS is enabled.

2. Install kubelogin
Download kubelogin from https://github.com/int128/kubelogin/releases.
Install it to your terminal.

## Getting started

### Generate certificate and private key

Create OpenSSL conf req.conf as follow:

```bash
[req]
req_extensions = v3_req
distinguished_name = req_distinguished_name

[req_distinguished_name]

[ v3_req ]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = dex.example.com
```

Please replace dex.example.com to your favorite hostname.
Generate certificate and private key by following command.

```bash
$ openssl req -new -x509 -sha256 -days 3650 -newkey rsa:4096 -extensions v3_req -out openid-ca.pem -keyout openid-key.pem -config req.cnf -subj "/CN=kube-ca" -nodes
$ ls openid*
openid-ca.pem openid-key.pem
```

### Modify dex config

Modify following host, bindDN and bindPW in examples/config-ad-kubelogin.yaml.

```yaml
connectors:
- type: ldap
  name: OpenLDAP
  id: ldap
  config:
    host: ldap.example.com:636

    # No TLS for this setup.
    insecureNoSSL: false
    insecureSkipVerify: true

    # This would normally be a read-only user.
    bindDN: cn=Administrator,cn=users,dc=example,dc=com
    bindPW: admin0!
```

### Run dex

```bash
$ bin/dex serve examples/config-ad-kubelogin.yaml
```

### Configure kubernetes with oidc

Copy `openid-ca.pem` to `/etc/ssl/certs/openid-ca.pem` on master node.

Use the following flags to point your API server(s) at dex. `dex.example.com` should be replaced by whatever DNS name or IP address dex is running under.

```bash
--oidc-issuer-url=https://dex.example.com:32000/dex
--oidc-client-id=kubernetes
--oidc-ca-file=/etc/ssl/certs/openid-ca.pem
--oidc-username-claim=email
--oidc-groups-claim=groups
```

Then restart API server(s).


See https://kubernetes.io/docs/reference/access-authn-authz/authentication/ for more detail.

### Set up kubeconfig

Add a new user to the kubeconfig for dex authentication:

```bash
$ kubectl config set-credentials oidc \
    --exec-api-version=client.authentication.k8s.io/v1beta1 \
    --exec-command=kubectl \
    --exec-arg=oidc-login \
    --exec-arg=get-token \
    --exec-arg=--oidc-issuer-url=https://dex.example.com:32000/dex \
    --exec-arg=--oidc-client-id=kubernetes \
    --exec-arg=--oidc-client-secret=ZXhhbXBsZS1hcHAtc2VjcmV0 \
    --exec-arg=--oidc-extra-scope=profile \
    --exec-arg=--oidc-extra-scope=email \
    --exec-arg=--oidc-extra-scope=groups \
    --exec-arg=--certificate-authority-data=$(base64 -w 0 openid-ca.pem)
```

Please confirm `--oidc-issuer-url`, `--oidc-client-id`, `--oidc-client-secret` and `--certificate-authority-data` are same as values in config-ad-kubelogin.yaml.

Run the following command:

```bash
$ kubectl --user=oidc cluster-info
```

It launches the browser and navigates it to http://localhost:8000.
Please log in with your AD account (eg. test@example.com) and password.
After login and grant, you can access the cluster.

You can switch the current context to dex authentication.

```bash
$ kubectl config set-context --current --user=oidc
```



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/archive/proposals/_index.md
================================================================================

---
title: "Proposals"
description: "Proposals Index"
date: 2020-01-07T14:59:38+01:00
draft: true
toc: true
---



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/archive/proposals/user-object.md
================================================================================

---
title: "Proposal: User Objects for Revoking Refresh Tokens and Merging Accounts"
linkTitle: "User Objects for Revoking Refresh Tokens and Merging Accounts"
description: ""
date: 2020-09-30
draft: true
toc: true
weight: 20
---

Certain operations require tracking users the have logged in through the server
and storing them in the backend. Namely, allowing end users to revoke refresh
tokens and merging existing accounts with upstream providers.

While revoking refresh tokens is relatively easy, merging accounts is a
difficult problem. What if display names or emails are different? What happens
to a user with two remote identities with the same upstream service? Should
this be presented differently for a user with remote identities for different
upstream services? This proposal only covers a minimal merging implementation
by guaranteeing that merged accounts will always be presented to clients with
the same user ID.

This proposal defines the following objects and methods to be added to the
storage package to allow user information to be persisted.

```go
// User is an end user which has logged into the server.
//
// Users do not hold additional data, such as emails, because claim information
// is always supplied by an upstream provider during the auth flow. The ID is
// the only information from this object which overrides the claims produced by
// connectors.
//
// Clients which wish to associate additional data with a user must do so on
// their own. The server only guarantees that IDs will be constant for an end
// user, no matter what backend they use to login.
type User struct {
	// A string which uniquely identifies the user for the server. This overrides
	// the ID provided by the connector in the ID Token claims.
	ID string

	// A list of clients who have been issued refresh tokens for this user.
	//
	// When a refresh token is redeemed, the server will check this field to
	// ensure that the client is still on this list. To revoke a client,
	// remove it from here.
	AuthorizedClients []AuthorizedClient

	// A set of remote identities which are able to login as this user.
	RemoteIdentities []RemoteIdentity
}

// AuthorizedClient is a client that has a refresh token out for this user.
type AuthorizedClient struct {
	// The ID of the client.
	ClientID string
	// The last time a token was refreshed.
	LastRefreshed time.Time
}

// RemoteIdentity is the smallest amount of information that identifies a user
// with a remote service. It indicates which remote identities should be able
// to login as a specific user.
//
// RemoteIdentity contains an username so an end user can be displayed this
// object and reason about what upstream profile it represents. It is not used
// to cache claims, such as groups or emails, because these are always provided
// by the upstream identity system during login.
type RemoteIdentity struct {
	// The ID of the connector used to login the user.
	ConnectorID string
	// A string which uniquely identifies the user with the remote system.
	ConnectorUserID string

	// Optional, human readable name for this remote identity. Only used when
	// displaying the remote identity to the end user (e.g. when merging
	// accounts). NOT used for determining ID Token claims.
	Username string
}
```

`UserID` fields will be added to the `AuthRequest`, `AuthCode` and `RefreshToken`
structs. When a user logs in successfully through a connector
[here](https://github.com/dexidp/dex/blob/95a61454b522edd6643ced36b9d4b9baa8059556/server/handlers.go#L227),
the server will attempt to either get the user, or create one if none exists with
the remote identity.

`AuthorizedClients` serves two roles. First is makes displaying the set of
clients a user is logged into easy. Second, because we don't assume multi-object
transactions, we can't ensure deleting all refresh tokens a client has for a
user. Between listing the set of refresh tokens and deleting a token, a client
may have already redeemed the token and created a new one.

When an OAuth2 client exchanges a code for a token, the following steps are
taken to populate the `AuthorizedClients`:

1. Get token where the user has authorized the `offline_access` scope.
1. Update the user checking authorized clients. If client is not in the list,
add it.
1. Create a refresh token and return the token.

When a OAuth2 client attempts to renew a refresh token, the server ensures that
the token hasn't been revoked.

1. Check authorized clients and update the `LastRefreshed` timestamp. If client
isn't in list error out and delete the refresh token.
1. Continue renewing the refresh token.

When the end user revokes a client, the following steps are used to.

1. Update the authorized clients by removing the client from the list. This
atomic action causes any renew attempts to fail.
1. Iterate through list of refresh tokens and garbage collect any tokens issued
by the user for the client. This isn't atomic, but exists so a user can
re-authorize a client at a later time without authorizing old refresh tokens.

This is clunky due to the lack of multi-object transactions. E.g. we can't delete
all the refresh tokens at once because we don't have that guarantee.

Merging accounts becomes extremely simple. Just add another remote identity to
the user object.

We hope to provide a web interface that a user can login to to perform these
actions. Perhaps using a well known client issued exclusively for the server.

The new `User` object requires adding the following methods to the storage
interface, and (as a nice side effect) deleting the `ListRefreshTokens()` method.

```go
type Storage interface {
	// ...

	CreateUser(u User) error

	DeleteUser(id string) error

	GetUser(id string) error
	GetUserByRemoteIdentity(connectorID, connectorUserID string) (User, error)

	// Updates are assumed to be atomic.
	//
	// When a UpdateUser is called, if clients are removed from the
	// AuthorizedClients list, the underlying storage SHOULD clean up refresh
	// tokens issued for the removed clients. This allows backends with
	// multi-transactional capabilities to utilize them, while key-value stores
	// only guarantee best effort.
	UpdateUser(id string, updater func(old User) (User, error)) error
}
```

Importantly, this will be the first object which has a secondary index.
The Kubernetes client will simply list all the users in memory then iterate over
them to support this (possibly followed by a "watch" based optimization). SQL
implementations will have an easier time.



================================================================================
SOURCE: src/extraction/local-docs/dex/content/docs/archive/proposals/upstream-refreshing.md
================================================================================

---
title: "Proposal: Upstream Refreshing"
linkTitle: "Upstream Refreshing"
description: ""
date: 2020-09-30
draft: true
toc: true
weight: 20
---

## TL;DR

Today, if a user deletes their GitHub account, dex will keep allowing clients to
refresh tokens on that user's behalf because dex never checks back in with
GitHub.

This is a proposal to change the connector package so the dex can check back
in with GitHub.

## The problem

When dex is federating to an upstream identity provider (IDP), we want to ensure
claims being passed onto clients remain fresh. This includes data such as Google
accounts display names, LDAP group membership, account deactivations. Changes to
these on an upstream IDP should always be reflected in the claims dex passes to
its own clients.

Refresh tokens make this complicated. When refreshing a token, unlike normal
logins, dex doesn't have the opportunity to prompt for user interaction. For
example, if dex is proxying to a LDAP server, it won't have the user's username
and passwords.

Dex can't do this today because connectors have no concept of checking back in
with an upstream provider (with the sole exception of groups). They're only 
called during the initial login, and never consulted when dex needs to mint a
new refresh token for a client. Additionally, connectors aren't actually aware
of the scopes being requested by the client, so they don't know when they should
setup the ability to check back in and have to treat every request identically.

## Changes to the connector package

The biggest changes proposed impact the connector package and connector
implementations.

1. Connectors should be consulted when dex attempts to refresh a token.
2. Connectors should be aware of the scopes requested by the client.

The second bullet is important because of the first. If a client isn't
requesting a refresh token, the connector shouldn't do the extra work, such as
requesting additional upstream scopes.

to address the first point, a top level `Scopes` object will be added to the
connector package to express the scopes requested by the client. The
`CallbackConnector` and `PasswordConnector` will be updated accordingly.

```go
// Scopes represents additional data requested by the clients about the end user.
type Scopes struct{
	// The client has requested a refresh token from the server.
	OfflineAccess bool

	// The client has requested group information about the end user.
	Groups bool
}

// CallbackConnector is an interface implemented by connectors which use an OAuth
// style redirect flow to determine user information.
type CallbackConnector interface {
	// The initial URL to redirect the user to.
	//
	// OAuth2 implementations should request different scopes from the upstream
	// identity provider based on the scopes requested by the downstream client.
	// For example, if the downstream client requests a refresh token from the
	// server, the connector should also request a token from the provider.
	LoginURL(s Scopes, callbackURL, state string) (string, error)

	// Handle the callback to the server and return an identity.
	HandleCallback(s Scopes, r *http.Request) (identity Identity, state string, err error)
}

// PasswordConnector is an interface implemented by connectors which take a
// username and password.
type PasswordConnector interface {
	Login(s Scopes, username, password string) (identity Identity, validPassword bool, err error)
}
```

The existing `GroupsConnector` plays two roles.

1. The connector only attempts to grab groups when the downstream client requests it.
2. Allow group information to be refreshed.

The first issue is remedied by the added `Scopes` struct. This proposal also
hopes to generalize the need of the second role by adding a more general
`RefreshConnector`:

```go
type Identity struct {
	// Existing fields...

	// Groups are added to the identity object, since connectors are now told
	// if they're being requested.

	// The set of groups a user is a member of.
	Groups []string
}


// RefreshConnector is a connector that can update the client claims.
type RefreshConnector interface {
	// Refresh is called when a client attempts to claim a refresh token. The
	// connector should attempt to update the identity object to reflect any
	// changes since the token was last refreshed.
	Refresh(s Scopes, identity Identity) (Identity, error)

	// TODO(ericchiang): Should we allow connectors to indicate that the user has
	// been delete	or an upstream token has been revoked? This would allow us to
	// know when we should remove the downstream refresh token, and when there was
	// just a server error, but might be hard to determine for certain protocols.
	// Might be safer to always delete the downstream token if the Refresh()
	// method returns an error.
}
```

## Example changes to the "passwordDB" connector

The `passwordDB` connector is the internal connector maintained by the server. 
As an example, these are the changes to that connector if this change was
accepted.

```go
func (db passwordDB) Login(s connector.Scopes, username, password string) (connector.Identity, bool, error) {
	// No change to existing implementation. Scopes can be ignored since we'll
	// always have access to the password objects.

}

func (db passwordDB) Refresh(s connector.Scopes, identity connector.Identity) (connector.Identity, error) {
	// If the user has been deleted, the refresh token will be rejected.
	p, err := db.s.GetPassword(identity.Email)
	if err != nil {
		if err == storage.ErrNotFound {
			return connector.Identity{}, errors.New("user not found")
		}
		return connector.Identity{}, fmt.Errorf("get password: %v", err)
	}

	// User removed but a new user with the same email exists.
	if p.UserID != identity.UserID {
		return connector.Identity{}, errors.New("user not found")
	}

	// If a user has updated their username, that will be reflected in the
	// refreshed token.
	identity.Username = p.Username
	return identity, nil
}
```

## Caveats

Certain providers, such as Google, will only grant a single refresh token for each
client + end user pair. The second time one's requested, no refresh token is
returned. This means refresh tokens must be stored by dex as objects on an
upstream identity rather than part of a downstream refresh even.

Right now `ConnectorData` is too general for this since it is only stored with a
refresh token and can't be shared between sessions. This should be rethought in
combination with the [`user-object.md`](./user-object.md) proposal to see if
there are reasonable ways for us to do this.

This isn't a problem for providers like GitHub because they return the same
refresh token every time. We don't need to track a token per client.
