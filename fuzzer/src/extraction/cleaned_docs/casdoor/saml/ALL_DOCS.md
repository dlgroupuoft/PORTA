

================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/oauth.md
================================================================================

---
title: OAuth 2.0
description: Obtain, verify, and use access tokens with Casdoor’s OAuth 2.0 endpoints.
keywords: [OAuth 2.0, access token, refresh token, grant types]
authors: [nomeguy]
---

Casdoor issues **access tokens** for authenticating clients. This page describes how to get a token via the API, verify it, and use it. Alternatively use [Casdoor SDKs](/docs/how-to-connect/sdk) to handle the flow.

**Supported grant types:** [Authorization Code](https://datatracker.ietf.org/doc/html/rfc6749#section-4.1), [Implicit](https://datatracker.ietf.org/doc/html/rfc6749#section-4.2), [Resource Owner Password](https://datatracker.ietf.org/doc/html/rfc6749#section-4.3), [Client Credentials](https://datatracker.ietf.org/doc/html/rfc6749#section-4.4), [Refresh Token](https://datatracker.ietf.org/doc/html/rfc6749#section-6), [Device Authorization](https://datatracker.ietf.org/doc/html/rfc8628), [Token Exchange](https://datatracker.ietf.org/doc/html/rfc8693).

Authorization code is enabled by default for security. Enable other grant types on the application edit page if needed.

![Grant Types](/img/how-to-connect/oauth/accesstoken_grant_types.png)

### Authorization code grant <span id="1"></span>

Redirect the user to:

```url
https://<CASDOOR_HOST>/login/oauth/authorize?
client_id=CLIENT_ID&
redirect_uri=REDIRECT_URI&
response_type=code&
scope=openid&
state=STATE
```

#### Scopes

| Scope | Description |
|-------|-------------|
| openid (default) | `sub`, `iss`, `aud` |
| profile | name, displayName, avatar |
| email | email address |
| address | address (OIDC object in **JWT-Standard**; see [OIDC address claim](/docs/token/overview#oidc-address-claim)) |
| phone | phone number |

:::info
Request scopes in the authorize URL. Separate multiple scopes with `%20`:

```text
https://<CASDOOR_HOST>/login/oauth/authorize?
client_id=...&
scope=openid%20email
```

See the [OIDC spec](https://openid.net/specs/openid-connect-core-1_0.html#UserInfoResponse) for details.
:::

After the user signs in, Casdoor redirects to:

```url
https://REDIRECT_URI?code=CODE&state=STATE
```

Exchange the code for tokens with a POST to:

```url
https://<CASDOOR_HOST>/api/login/oauth/access_token
```

Request body:

```json
{
    "grant_type": "authorization_code",
    "client_id": ClientId,
    "client_secret": ClientSecret,
    "code": Code,
}
```

Example response:

```json
{
    "access_token": "eyJhb...",
    "id_token": "eyJhb...",
    "refresh_token": "eyJhb...",
    "token_type": "Bearer",
    "expires_in": 10080,
    "scope": "openid"
}
```

:::note

Casdoor supports [PKCE](https://datatracker.ietf.org/doc/html/rfc7636) (Proof Key for Code Exchange) for enhanced security. To enable PKCE, add two parameters when requesting the authorization code:

```url
&code_challenge_method=S256&code_challenge=YOUR_CHALLENGE
```

The code challenge should be a Base64-URL-encoded SHA-256 hash of your randomly generated code verifier (43-128 characters). When requesting the token, include the original `code_verifier` parameter. With PKCE enabled, `client_secret` becomes optional, but if provided, it must be correct.

For OAuth providers configured in Casdoor (like Twitter and custom providers with PKCE enabled), Casdoor automatically generates unique code verifiers for each authentication flow, so you don't need to manually implement PKCE.

:::

#### Binding Tokens to Specific Services

When your application needs to call multiple backend services, you might want tokens that are explicitly bound to a specific service. This prevents security issues where a token meant for one service could accidentally be used with another.

Casdoor supports RFC 8707 Resource Indicators, which lets you specify the intended service when requesting authorization. Add the `resource` parameter with an absolute URI identifying your service:

```url
https://<CASDOOR_HOST>/login/oauth/authorize?
client_id=CLIENT_ID&
redirect_uri=REDIRECT_URI&
response_type=code&
scope=openid&
state=STATE&
resource=https://api.example.com
```

When you exchange the authorization code for tokens, include the same `resource` parameter:

```json
{
    "grant_type": "authorization_code",
    "client_id": ClientId,
    "client_secret": ClientSecret,
    "code": Code,
    "resource": "https://api.example.com"
}
```

The resulting access token will have its `aud` (audience) claim set to your resource URI instead of the client ID. Your backend service can then verify that tokens were issued specifically for it by checking the audience claim. The resource must match exactly between the authorization and token requests.

#### Signup Flow with OAuth

When users sign up through the OAuth authorization flow, they are automatically redirected to your application's callback URL with the authorization code, just like the sign-in flow. Previously, users had to manually click through intermediate pages after creating their account. Now the signup process matches the streamlined experience of signing in—once registration completes, Casdoor immediately generates the authorization code and redirects to your `redirect_uri`.

Your application doesn't need any changes to support this. The authorization parameters (`client_id`, `response_type`, `redirect_uri`, etc.) are automatically passed through the signup process when users choose to create a new account during OAuth authorization.

### Implicit Grant

For apps without a backend, use **Implicit Grant**. Enable it on the application, then redirect users to:

```url
https://<CASDOOR_HOST>/login/oauth/authorize?client_id=CLIENT_ID&redirect_uri=REDIRECT_URI&response_type=token&scope=openid&state=STATE
```

After your user has authenticated with Casdoor, Casdoor will redirect them to:

```url
https://REDIRECT_URI/#access_token=ACCESS_TOKEN
```

Casdoor also supports the [id_token](https://openid.net/specs/oauth-v2-multiple-response-types-1_0.html#id_token) as `response_type`, which is a feature of OpenID.

### Device Grant

For devices with limited input or no browser, use **Device Grant**. Enable it on the application, request `device_authorization_endpoint` from OIDC discovery, then show `verification_uri` (e.g. via QR or text) so the user can complete login.

Second, you should request `token endpoint` to get Access Token with parameter define in [rfc8628](https://datatracker.ietf.org/doc/html/rfc8628#section-3.4).

### Resource Owner Password Credentials Grant

If your application doesn't have a frontend that redirects users to Casdoor, then you may need this.

Enable **Password Credentials Grant** on the application, then send a POST request to:

```url
https://<CASDOOR_HOST>/api/login/oauth/access_token
```

```json
{
    "grant_type": "password",
    "client_id": ClientId,
    "client_secret": ClientSecret,
    "username": Username,
    "password": Password,
}
```

Example response:

```json
{
    "access_token": "eyJhb...",
    "id_token": "eyJhb...",
    "refresh_token": "eyJhb...",
    "token_type": "Bearer",
    "expires_in": 10080,
    "scope": "openid"
}
```

### Client Credentials Grant

Use Client Credentials Grant when the application has no frontend.

Enable **Client Credentials Grant** on the application and send a POST request to `https://<CASDOOR_HOST>/api/login/oauth/access_token`:

```json
{
    "grant_type": "client_credentials",
    "client_id": ClientId,
    "client_secret": ClientSecret,
}
```

Example response:

```json
{
    "access_token": "eyJhb...",
    "id_token": "eyJhb...",
    "refresh_token": "eyJhb...",
    "token_type": "Bearer",
    "expires_in": 10080,
    "scope": "openid"
}
```

It is important to note that the AccessToken obtained in this way differs from the first three in that it corresponds to the application rather than to the user.

### Refresh Token

To refresh the access token, use the `refreshToken` obtained above.

Set the **Refresh Token** expiration in the application (default 0 hours), then send a POST request to `https://<CASDOOR_HOST>/api/login/oauth/refresh_token`

```json
{
    "grant_type": "refresh_token",
    "refresh_token": REFRESH_TOKEN,
    "scope": SCOPE,
    "client_id": ClientId,
    "client_secret": ClientSecret,
}
```

Example response:

```json
{
    "access_token": "eyJhb...",
    "id_token": "eyJhb...",
    "refresh_token": "eyJhb...",
    "token_type": "Bearer",
    "expires_in": 10080,
    "scope": "openid"
}
```

### Token Exchange Grant

Token Exchange (RFC 8693) lets you swap an existing token for a new one with different characteristics—particularly useful when one service needs to call another on behalf of a user, or to narrow a token's scope for a specific downstream service.

To exchange a token, send a POST request to `https://<CASDOOR_HOST>/api/login/oauth/access_token`:

```json
{
    "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
    "client_id": ClientId,
    "client_secret": ClientSecret,
    "subject_token": SubjectToken,
    "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
    "scope": "openid email"
}
```

The `subject_token` is the token you want to exchange—typically an access token or JWT you already have. If you want to narrow the permissions in the new token, specify a `scope` that's a subset of the original token's scope. When you omit `scope`, the new token inherits the same scope as the subject token.

Casdoor supports three token types for `subject_token_type`:

- `urn:ietf:params:oauth:token-type:access_token` (default)
- `urn:ietf:params:oauth:token-type:jwt`
- `urn:ietf:params:oauth:token-type:id_token`

The response returns a new token tied to the same user as your subject token:

```json
{
    "access_token": "eyJhb...",
    "id_token": "eyJhb...",
    "refresh_token": "eyJhb...",
    "token_type": "Bearer",
    "expires_in": 10080,
    "scope": "openid email"
}
```

For example, an API gateway might exchange a broad-scoped access token for a narrower one before forwarding requests to a downstream microservice. This pattern—called scope downscoping—ensures each service gets only the permissions it needs, rather than inheriting full access from the original token.

## How to Verify Access Token

Casdoor currently supports the [token introspection](https://datatracker.ietf.org/doc/html/rfc7662) endpoint. This endpoint is protected by Basic Authentication (ClientId:ClientSecret).

```http
POST /api/login/oauth/introspect HTTP/1.1
Host: CASDOOR_HOST
Accept: application/json
Content-Type: application/x-www-form-urlencoded
Authorization: Basic Y2xpZW50X2lkOmNsaWVudF9zZWNyZXQ=

token=ACCESS_TOKEN&token_type_hint=access_token
```

Example response:

```json
{
    "active": true,
    "client_id": "c58c...",
    "username": "admin",
    "token_type": "Bearer",
    "exp": 1647138242,
    "iat": 1646533442,
    "nbf": 1646533442,
    "sub": "7a6b4a8a-b731-48da-bc44-36ae27338817",
    "aud": [
        "c58c..."
    ],
    "iss": "http://localhost:8000"
}
```

## How to Use `AccessToken`

Use the access token to call Casdoor APIs that require authentication.

For example, there are two different ways to request `/api/userinfo`.

Type 1: Query parameter

`https://CASDOOR_HOST/api/userinfo?accessToken=your_access_token`

Type 2: HTTP Bearer token

`https://CASDOOR_HOST/api/userinfo` with the header: "Authorization: Bearer `your_access_token`"

Casdoor will parse the access_token and return corresponding user information according to the `scope`.
The response has the same shape:

```json
{
    "sub": "7a6b4a8a-b731-48da-bc44-36ae27338817",
    "iss": "http://localhost:8000",
    "aud": "c58c..."
}
```

If you expect more user information, add `scope` when obtaining the AccessToken in step [Authorization code grant](#authorization-code-grant).

## Accessing OAuth Provider Tokens

When users sign in via OAuth providers (GitHub, Google, etc.), the provider's access token is available to call the third-party API on their behalf; it is stored in the user's `originalToken` field.

The token is available through the `/api/get-account` endpoint:

```json
{
  "status": "ok",
  "data": {
    "name": "user123",
    "originalToken": "ya29.a0AfH6SMBx...",
    ...
  }
}
```

The `originalToken` is visible only when the user requests their own account or when the requester is an admin. For other requests, it is masked for privacy.

This allows your application to interact with third-party APIs (e.g., GitHub API, Google Drive API) using the provider's access token without requiring additional OAuth flows.

## Differences between the `userinfo` and `get-account` APIs

- `/api/userinfo`: This API returns user information as part of the OIDC protocol. It provides limited information, including only the basic information defined in OIDC standards. For a list of available scopes supported by Casdoor, see the [Scopes](#scopes) section.

- `/api/get-account`: This API retrieves the user object for the currently logged-in account. It is a Casdoor-specific API that allows you to obtain all the information of the [user](/docs/basic/core-concepts#user) in Casdoor, including the OAuth provider's access token when applicable.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/saml/keycloak.md
================================================================================

---
title: Keycloak (SAML)
description: Use Casdoor as SAML IdP in Keycloak.
keywords: [SAML, IdP, Keycloak]
authors: [seriouszyx]
---

This guide configures Casdoor as a SAML v2.0 identity provider in **Keycloak**.

## Add the SAML IdP in Keycloak

1. In the Keycloak admin console, go to **Identity providers** and add **SAML v2.0**.
2. On the IdP configuration page, set **Alias** and paste the Casdoor metadata URL into **Import from URL** (you can copy this from the Casdoor application edit page).
3. Click **Import** so Keycloak fills the SAML settings.
4. Note the **Service Provider Entity ID** and save.

![saml_keycloak_idp_create](/img/how-to-connect/saml/saml_keycloak_idp_create.png)
![saml_keycloak_idp_edit](/img/how-to-connect/saml/saml_keycloak_idp_edit.png)

:::info
See [Keycloak SAML Identity Providers](https://www.keycloak.org/docs/latest/server_admin/#saml-v2-0-identity-providers) for full options.
:::

## Configure the application in Casdoor

In the Casdoor application edit page:

- Add a **Redirect URL** that matches the **Service Provider Entity ID** from Keycloak.
- Enable **SAML compress** for Keycloak.

![saml_keycloak_compress](/img/how-to-connect/saml/saml_keycloak_compress.png)

## Sign in with Casdoor SAML

On the Keycloak login page, use the button for the Casdoor SAML provider. You will be redirected to Casdoor to sign in, then back to Keycloak. Assign users to the application as needed.

![saml_keycloak_login](/img/how-to-connect/saml/saml_keycloak_login.png)
![saml_keycloak_success](/img/how-to-connect/saml/saml_keycloak_success.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/saml/aws.md
================================================================================

---
title: AWS Client VPN (SAML)
description: Use Casdoor as SAML IdP for AWS Client VPN.
keywords: [SAML, IdP, AWS, VPN]
authors: [UsherFall]
---

This guide configures Casdoor as a SAML identity provider for **AWS Client VPN**.

## Prerequisites

- AWS account with permission to configure the service
- Amazon VPC with an EC2 instance ([VPC setup](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-getting-started.html), [EC2](https://docs.aws.amazon.com/ec2/latest/userGuide/EC2_GetStarted.html)); in the instance security group, allow ICMP from the VPC CIDR for testing
- A private certificate in [AWS Certificate Manager (ACM)](https://aws.amazon.com/certificate-manager/) ([import guide](https://docs.aws.amazon.com/vpn/latest/clientvpn-admin/what-is.html))
- Windows or Mac with [AWS Client VPN](https://aws.amazon.com/vpn/client-vpn-download/) installed

## Configure the SAML application in Casdoor

- Set **Redirect URL** to `urn:amazon:webservices:clientvpn`.

![saml_aws_redirect_url.png](/img/how-to-connect/saml/saml_aws_redirect_url.png)

- Set **SAML reply URL** to `http://127.0.0.1:35001`.

![saml_aws_reply_url.png](/img/how-to-connect/saml/saml_aws_reply_url.png)

- Save the **SAML metadata** as an XML file for the next step.

![saml_aws_metadata.png](/img/how-to-connect/saml/saml_aws_metadata.png)

## Configure AWS

### Add Casdoor as an identity provider

1. In the **IAM** console, open **Identity providers** → **Create provider**.
2. Choose **SAML**, give the provider a name, and upload the metadata file from Casdoor.
3. Click **Next step** → **Create**.

![saml_aws_create.png](/img/how-to-connect/saml/saml_aws_create.png)
![saml_aws_choose_metadata.png](/img/how-to-connect/saml/saml_aws_choose_metadata.png)

### Create a Client VPN endpoint

1. In **VPC** → **Client VPN Endpoints** → **Create Client VPN Endpoint**.
2. Set **Client IPv4 CIDR** for remote users.
3. Select your **Server certificate** (from ACM).
4. Under **Authentication**, choose **User-based authentication** → **Federated authentication**.
5. Select the SAML identity provider you created.
6. Click **Create Client VPN Endpoint**.

![saml_aws_vpn_endpoint.png](/img/how-to-connect/saml/saml_aws_vpn_endpoint.png)
![saml_aws_create_vpn.png](/img/how-to-connect/saml/saml_aws_create_vpn.png)

### Associate the VPN with a VPC

1. In the endpoint, open **Target network associations** → **Associate target network**.
2. Select the VPC and subnet.

![saml_aws_target_network.png](/img/how-to-connect/saml/saml_aws_target_network.png)

### Authorization rules (optional)

1. Open **Authorization rules** → **Add authorize rule**.
2. Set **Destination network** (e.g. `172.31.16.0/20` for your EC2).
3. Under **Grant access to**, choose **Allow access to users in a specific access group** and enter the group name (e.g. `casdoor`).
4. Add the rule.

![saml_aws_rule.png](/img/how-to-connect/saml/saml_aws_rule.png)

## Connect to Client VPN

1. Select the endpoint (state: Available) → **Download Client Configuration**.
2. In the AWS Client VPN app: **File** → **Manage Profiles** → **Add Profile** → select the downloaded file.
3. Select the profile and click **Connect**.

![saml_aws_download.png](/img/how-to-connect/saml/saml_aws_download.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/saml/tencent-cloud.md
================================================================================

---
title: Tencent Cloud (SAML)
description: Use Casdoor as SAML IdP for Tencent Cloud CAM.
keywords: [SAML, IdP, Tencent Cloud]
authors: [Songjf-ttk]
---

This guide configures Casdoor as a SAML identity provider for **Tencent Cloud** (CAM).

## Get SAML metadata from Casdoor

1. In Casdoor, add an X.509 certificate (RSA).
2. Copy the **SAML metadata** from the application (or metadata URL).

![Add cert](/img/how-to-connect/saml/saml_tencent-cloud_cert.png)
![Copy Saml metadata](/img/how-to-connect/saml/saml_tencent-cloud_metadata.png)

## Add SAML IdP and role in Tencent Cloud

1. Log in to Tencent Cloud and open **Access Management** (CAM).
2. Create a new **Identity provider** and upload the Casdoor SAML metadata.
3. Create a new **Role** and select that identity provider.

![Login Access Management](/img/how-to-connect/saml/saml_tencent-cloud_access_management.png)
![Saml idp create](/img/how-to-connect/saml/saml_tencent-cloud_idp_create.png)
![Saml role create](/img/how-to-connect/saml/saml_tencent-cloud_create_role.png)

## Configure the application in Casdoor

1. On the application edit page, select the certificate and add the Tencent Cloud domain to **Redirect URLs**.
2. Set the **ACS URL** and configure **SAML attributes** as follows:

![Select cert and add redirect URLs](/img/how-to-connect/saml/saml_tencent-cloud_app.png)
![Add acs url and configure saml attribute](/img/how-to-connect/saml/saml_tencent-cloud_acs.png)

| Name | Name Format | Value |
|------|-------------|-------|
| `https://cloud.tencent.com/SAML/Attributes/Role` | Unspecified | `qcs::cam::uin/{'{'}AccountID{'}'}:roleName/{'{'}RoleName1{'}'};qcs::cam::uin/{'{'}AccountID{'}'}:roleName/{'{'}RoleName2{'}'},qcs::cam::uin/{'{'}AccountID{'}'}:saml-provider/{'{'}ProviderName{'}'}` |
| `https://cloud.tencent.com/SAML/Attributes/RoleSessionName` | Unspecified | `casdoor` |

:::info
Replace placeholders using:
- **{'{'}AccountID{'}'}**: Tencent Cloud account ID — [Account Information](https://console.cloud.tencent.com/developer)
- **{'{'}RoleName{'}'}**: Role name — [Roles](https://console.cloud.tencent.com/cam/role)
- **{'{'}ProviderName{'}'}**: SAML identity provider name — [Identity Providers](https://console.cloud.tencent.com/cam/idp)

See [Tencent Cloud SAML IdP documentation](https://cloud.tencent.com/document/product/598/38058).
:::

## Log in via SAML

Flow: User → Tencent Cloud (unauthenticated) → redirect to Casdoor → sign in → Tencent Cloud (authenticated). The initial redirect URL can be built from SAML metadata and IdP SSO URL. Example (Go) that fetches metadata, builds the auth URL, and prints it:

```go
func main() {
    res, err := http.Get("your casdoor application saml metadata url")
    if err != nil {
        panic(err)
    }

    rawMetadata, err := ioutil.ReadAll(res.Body)
    if err != nil {
        panic(err)
    }

    metadata := &types.EntityDescriptor{}
    err = xml.Unmarshal(rawMetadata, metadata)
    if err != nil {
        panic(err)
    }

    certStore := dsig.MemoryX509CertificateStore{
        Roots: []*x509.Certificate{},
    }

    for _, kd := range metadata.IDPSSODescriptor.KeyDescriptors {
        for idx, xcert := range kd.KeyInfo.X509Data.X509Certificates {
            if xcert.Data == "" {
                panic(fmt.Errorf("metadata certificate(%d) must not be empty", idx))
            }
            certData, err := base64.StdEncoding.DecodeString(xcert.Data)
            if err != nil {
                panic(err)
            }

            idpCert, err := x509.ParseCertificate(certData)
            if err != nil {
                panic(err)
            }

            certStore.Roots = append(certStore.Roots, idpCert)
        }
    }

    randomKeyStore := dsig.RandomKeyStoreForTest()

    sp := &saml2.SAMLServiceProvider{
        IdentityProviderSSOURL:      metadata.IDPSSODescriptor.SingleSignOnServices[0].Location,
        IdentityProviderIssuer:      metadata.EntityID,
        ServiceProviderIssuer:       "https://cloud.tencent.com",
        AssertionConsumerServiceURL: "https://cloud.tencent.com/login/saml",
        SignAuthnRequests:           true,
        AudienceURI:                 "https://cloud.tencent.com",
        IDPCertificateStore:         &certStore,
        SPKeyStore:                  randomKeyStore,
    }

    println("Visit this URL To Authenticate:")
    authURL, err := sp.BuildAuthURL("")
    if err != nil {
        panic(err)
    }

    println(authURL)
}
```

After running the code, open the printed URL to test login.

![Final result](/img/how-to-connect/saml/saml_tencent-cloud_login_test.gif)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/saml/appgate.md
================================================================================

---
title: Appgate (SAML POST)
description: Use Casdoor as SAML IdP for Appgate SDP (POST SAMLResponse).
keywords: [SAML, IdP, Appgate]
authors: [leo220yuyaodog]
---

**Appgate** accepts `SAMLResponse` via POST. This guide applies when using Casdoor as the SAML IdP for Appgate (and for other SPs that support POST).

## Casdoor configuration

Create or edit the application in Casdoor and set:

| Setting | Value |
|--------|--------|
| **Redirect URL** | Unique identifier (Audience/Entity ID in the SP). Use the value from the table below. |
| **Reply URL** | ACS URL that receives and verifies the SAML response. |

| Use case | Redirect URL | SAML Reply URL |
|----------|--------------|----------------|
| Administrator auth | `AppGate` | `https://mycontroller.your-site-url.com/admin/saml` |
| User auth | `AppGate Client` | `https://redirectserver.your-site-url.com/saml` |

![Entity ID](/img/how-to-connect/saml/saml_entityId.png)
![Reply URL](/img/how-to-connect/saml/saml_replyURL.png)

Download the **SAML metadata** (copy the metadata URL and open it in a browser to save the XML).

![metadata](/img/how-to-connect/saml/saml_metadata_url.png)

## Add SAML IdP in Appgate

1. In **AppGate SDP Console** → **System** → **Identity Providers**, create a new provider and choose **SAML**.
2. Set **Name** (e.g. "Casdoor SAML Admin"). For **Single Sign-on URL**, **Issuer**, and **Public Certificate**, upload the metadata file so they are filled automatically.
3. Set **Audience** to the **Redirect URL** you configured in Casdoor.

Upload the metadata via **Choose a file** to autocomplete Single Sign-On URL, Issuer, and Public Certificate.

## Map attributes

Map the **Name** attribute to **username**.

![map_attribute](/img/how-to-connect/saml/saml_map_attribute.png)

## Test

1. Log out of the AppGate admin UI.
2. Sign in with **Identity Provider** set to your Casdoor IdP and **Sign in with browser**.
3. A message like "You don't have any administration rights" indicates the IdP authenticated the user; adjust Appgate roles/policies as needed.

## Access policy

Update the **Builtin Administrator Policy** (or equivalent) so administrators can sign in via the SAML IdP.

![appgate_policy.png](/img/how-to-connect/saml/saml_appgate_policy.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/saml/overview.md
================================================================================

---
title: SAML IdP overview
description: Use Casdoor as a SAML 2.0 identity provider.
keywords: [SAML, IdP]
---

Casdoor can act as a **SAML 2.0 IdP**. This page covers SP configuration, Casdoor IdP settings, and SAML attributes.

### Configuration in the SP (service provider)

The SP typically needs **Single Sign-On URL**, **Issuer**, and **Public Certificate**. Most SPs can fill these from the Casdoor **XML Metadata URL** or by uploading the metadata file.

Casdoor metadata URL format: `<casdoor-endpoint>/api/saml/metadata?application=admin/<application-name>`

Example: if Casdoor is at `https://door.casdoor.com` and the application is `app-built-in`:

```text
https://door.casdoor.com/api/saml/metadata?application=admin/app-built-in
```

The metadata URL is also on the application edit page; copy it and open in a browser to download the XML.

![metadata](/img/how-to-connect/saml/saml_metadata.png)

### Configuration in Casdoor IdP

Casdoor supports both GET and POST `SAMLResponse`. Configure the application in Casdoor to match the `SAMLResponse` binding (GET or POST) that your SP supports.

When integrating Casdoor as a SAML IdP with external identity providers (like Azure AD), the `/api/acs` endpoint receives SAML responses. This endpoint is configured to accept cross-origin POST requests, allowing IdPs from different domains to send authentication data.

:::info

If you fill in the `Reply URL`, Casdoor will send the `SAMLResponse` by **POST** Request. If the Reply URL is empty, Casdoor will use **GET** request. You might wonder how Casdoor knows the `Reply URL` of the SP if the `Reply URL` is empty. Actually, Casdoor can get the URL called `AssertionConsumerServiceURL` by parsing the `SAMLRequest` and send the request with `SAMLResponse` to `AssertionConsumerServiceURL`. The `Reply URL` will overwrite the `AssertionConsumerServiceURL` in `SAMLRequest`.

:::

- **Reply URL**: Type in the URL of the ACS verifying the SAML response.
  
  ![Reply URL](/img/how-to-connect/saml/saml_replyURL.png)

- **Redirect URL**: Type in a unique name. This may be called `Audience` or `Entity ID` in your SP. Make sure you fill the same `Redirect URL` here as in your SP.
  
  ![Entity ID](/img/how-to-connect/saml/saml_entityId.png)

### SAML attributes

If the SP requires extra attributes in the SAML response, add them in the SAML attributes table and map user fields as needed.

If the service provider only needs NameID and not extra user attributes (Email, Name, DisplayName, Roles), enable **Disable SAML attributes** in the application settings. When enabled, Casdoor will omit these attributes from the SAML response, which can help avoid XML namespace issues with certain SPs that have strict validation requirements.

### Assertion signature control

SAML responses from Casdoor are always signed to ensure authenticity. However, some service providers may not support or require signed assertions within the response itself. Starting from version 2.81.0, Casdoor added assertion signatures following SAML 2.0 best practices, but this caused compatibility issues with certain SPs like Sentry.

If a service provider does not handle signed assertions correctly, disable assertion signing while keeping the response envelope signed. Toggle the **Enable SAML assertion signature** option in your application settings to control this behavior. When disabled, Casdoor will sign only the SAML response envelope, which maintains security while ensuring compatibility with a wider range of service providers.

For example

| Name |  Name format   | Value|
|:------------------:|:-------------:| :-------------:|
|       `https://www.aliyun.com/SAML-Role/Attributes/RoleSessionName`        |     Unspecified     |  `$user.name`  |
|    `https://www.aliyun.com/SAML-Role/Attributes/Role`     |  Unspecified  |  `acs:ram::1879818006829152:role/$user.roles,acs:ram::1879818006829152:saml-provider/testa`    |

will generate response with external `saml:Attribute`

```xml
```

:::info

We only support insert `$user.owner`,`$user.name`,`$user.email`,`$user.id`,`$user.phone`,`$user.roles`,`$user.permissions`,`$user.groups`

:::

### User profile

After successfully logging in, the user profile in the returned `SAMLResponse` from Casdoor has three fields. The attributes in the XML and the attributes of the user in Casdoor are mapped as follows:

| XML Attribute Name |  User field   |
|:------------------:|:-------------:|
|       Email        |     email     |
|    DisplayName     |  displayName  |
|        Name        |     name      |

See `https://en.wikipedia.org/wiki/SAML_2.0` for more information about SAML and its different versions.

### An example

[gosaml2](https://github.com/russellhaering/gosaml2) is a SAML 2.0 implementation for Service Providers based on etree and goxmldsig, a pure Go implementation of XML digital signatures. We use this library to test the SAML 2.0 in Casdoor as shown below.

Example: Casdoor at `http://localhost:7001/`, application `app-built-in` in org `built-in`. Add `http://localhost:6900/acs/example` and `http://localhost:6900/saml/acs/example` to **Redirect URLs** in `app-built-in`.

```go
    "crypto/x509"
    "fmt"
    "net/http"

    "io/ioutil"

    "encoding/base64"
    "encoding/xml"

    saml2 "github.com/russellhaering/gosaml2"
    "github.com/russellhaering/gosaml2/types"
    dsig "github.com/russellhaering/goxmldsig"
)

func main() {
    res, err := http.Get("http://localhost:7001/api/saml/metadata?application=admin/app-built-in")
    if err != nil {
        panic(err)
    }

    rawMetadata, err := ioutil.ReadAll(res.Body)
    if err != nil {
        panic(err)
    }

    metadata := &types.EntityDescriptor{}
    err = xml.Unmarshal(rawMetadata, metadata)
    if err != nil {
        panic(err)
    }

    certStore := dsig.MemoryX509CertificateStore{
        Roots: []*x509.Certificate{},
    }

    for _, kd := range metadata.IDPSSODescriptor.KeyDescriptors {
        for idx, xcert := range kd.KeyInfo.X509Data.X509Certificates {
            if xcert.Data == "" {
                panic(fmt.Errorf("metadata certificate(%d) must not be empty", idx))
            }
            certData, err := base64.StdEncoding.DecodeString(xcert.Data)
            if err != nil {
                panic(err)
            }

            idpCert, err := x509.ParseCertificate(certData)
            if err != nil {
                panic(err)
            }

            certStore.Roots = append(certStore.Roots, idpCert)
        }
    }

    randomKeyStore := dsig.RandomKeyStoreForTest()

    sp := &saml2.SAMLServiceProvider{
        IdentityProviderSSOURL:      metadata.IDPSSODescriptor.SingleSignOnServices[0].Location,
        IdentityProviderIssuer:      metadata.EntityID,
        ServiceProviderIssuer:       "http://localhost:6900/acs/example",
        AssertionConsumerServiceURL: "http://localhost:6900/v1/_saml_callback",
        SignAuthnRequests:           true,
        AudienceURI:                 "http://localhost:6900/saml/acs/example",
        IDPCertificateStore:         &certStore,
        SPKeyStore:                  randomKeyStore,
    }

    http.HandleFunc("/v1/_saml_callback", func(rw http.ResponseWriter, req *http.Request) {
        err := req.ParseForm()
        if err != nil {
            rw.WriteHeader(http.StatusBadRequest)
            return
        }
        samlReponse := req.URL.Query().Get("SAMLResponse")
        assertionInfo, err := sp.RetrieveAssertionInfo(samlReponse)
        if err != nil {
            fmt.Println(err)
            rw.WriteHeader(http.StatusForbidden)
            return
        }
        fmt.Println(assertionInfo)
        if assertionInfo.WarningInfo.InvalidTime {
            fmt.Println("here12:", assertionInfo.WarningInfo.InvalidTime)
            rw.WriteHeader(http.StatusForbidden)
            return
        }

        if assertionInfo.WarningInfo.NotInAudience {
            fmt.Println(assertionInfo)
            fmt.Println("here13:", assertionInfo.WarningInfo.NotInAudience)
            rw.WriteHeader(http.StatusForbidden)
            return
        }

        fmt.Fprintf(rw, "NameID: %s\n", assertionInfo.NameID)

        fmt.Fprintf(rw, "Assertions:\n")

        for key, val := range assertionInfo.Values {
            fmt.Fprintf(rw, "  %s: %+v\n", key, val)
        }
        fmt.Println(assertionInfo.Values.Get("FirstName"))
        fmt.Fprintf(rw, "\n")

        fmt.Fprintf(rw, "Warnings:\n")
        fmt.Fprintf(rw, "%+v\n", assertionInfo.WarningInfo)
    })

    println("Visit this URL To Authenticate:")
    authURL, err := sp.BuildAuthURL("")
    if err != nil {
        panic(err)
    }

    println(authURL)

    println("Supply:")
    fmt.Printf("  SP ACS URL      : %s\n", sp.AssertionConsumerServiceURL)

    err = http.ListenAndServe(":6900", nil)
    if err != nil {
        panic(err)
    }
}
```

Run the above code, and the console will display the following message.

```text
Visit this URL To Authenticate:
http://localhost:7001/login/saml/authorize/admin/app-built-in?SAMLRequest=lFVbk6K8Fv0rFvNo2QR...
Supply:
  SP ACS URL      : http://localhost:6900/v1/_saml_callback
```

Click the URL to authenticate, and the login page of Casdoor will be displayed.

![login](/img/how-to-connect/saml/saml_login.png)

After authentication, the response looks like the examples below.

![response](/img/how-to-connect/saml/saml_response.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/saml/google-workspace.md
================================================================================

---
title: Google Workspace (SAML)
description: Use Casdoor as SAML IdP for Google Workspace SSO.
keywords: [SAML, IdP, Google Workspace]
authors: [UsherFall]
---

This guide configures Casdoor as a SAML identity provider for **Google Workspace** single sign-on.

## Add a certificate in Casdoor

Create an X.509 certificate with RSA in Casdoor and download it.

![Add cert](/img/how-to-connect/saml/saml_google-workspace_cert.png)

## Configure the SAML application in Casdoor

1. On the application edit page, select the certificate and add your Google domain (e.g. `google.com`) to **Redirect URLs**.
2. Set **SAML reply URL** to `https://www.google.com/a/<your-domain>/acs`. See [SSO assertion requirements](https://support.google.com/a/answer/6330801) for the ACS URL.
3. Copy the **Sign-in page URL** for the next step.

![Select cert and add redirect URLs](/img/how-to-connect/saml/saml_google-workspace_app.png)
![Enter the SAML reply URL field](/img/how-to-connect/saml/saml_google-workspace_acs.png)
![Copy the sign-in page URL](/img/how-to-connect/saml/saml_google-workspace_login.png)

## Add third-party SAML IdP in Google Workspace

1. In **Google Workspace Admin** → **Security** → **Overview**, find **SSO with third-party IdP**.
2. Click **Add SSO profile** and enable **Set up SSO with third-party identity provider**.
3. Paste the Casdoor sign-in page URL into **Sign-in page URL** and **Sign-out page URL**.
4. Upload the certificate you downloaded from Casdoor and save.

![Configure Google Workspace](/img/how-to-connect/saml/saml_google-workspace_conf.png)

## Test with a user

1. In Google Workspace, create a user (e.g. username `test`).
2. In Casdoor, create a user with the same username in the correct organization and set their email.

![Add a user in Google Workspace](/img/how-to-connect/saml/saml_google-workspace_user.png)
![Add a user in Casdoor](/img/how-to-connect/saml/saml_google-workspace_test.png)

Sign-in flow: open the Google app (e.g. google.com) → sign in with the user’s email → redirect to Casdoor → enter Casdoor credentials → redirect back to Google when successful.

![Final result](/img/how-to-connect/saml/saml_google-workspace_test_gif.gif)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/CustomProvider.md
================================================================================

---
title: Custom OAuth provider
description: Integrate any OAuth 2.0–compliant IdP (Custom through Custom10).
keywords: [Custom Provider, OAuth, Casdoor]
authors: [halozhy]
---

:::note
Custom providers must use standard 3-legged OAuth. Responses from **Token URL** and **UserInfo URL** must match the formats below.
:::

Use **Custom** OAuth to connect Casdoor to any OAuth 2.0–compliant service: internal IdPs, self-hosted auth, or third-party services not yet built-in. You can add up to **10** custom providers: **Custom**, **Custom2**, … **Custom10**, each with its own config.

## Create a custom provider

In Casdoor **Providers** → **Add**, set **Type** to one of Custom, Custom2, … Custom10. Fill in **Client ID**, **Client Secret**, **Auth URL**, **Scope**, **Token URL**, **UserInfo URL**, and **Favicon**.

![image-20220418100744005](/img/providers/OAuth/customprovider.png)

- **Auth URL** — OAuth authorization endpoint. Example: with `https://door.casdoor.com/login/oauth/authorize`, the browser is sent to

  ```url
  https://door.casdoor.com/login/oauth/authorize?client_id={ClientID}&redirect_uri=https://{your-casdoor-hostname}/callback&state={State_generated_by_Casdoor}&response_type=code&scope={Scope}` 
  ```

  With **Enable PKCE** on, Casdoor adds:

  ```url
  &code_challenge={code_challenge}&code_challenge_method=S256
  ```

  The IdP must then redirect to

  ```url
  https://{your-casdoor-hostname}/callback?code={code}
  ```

  After this step, Casdoor will recognize the code parameter in the URL.

- **Scope** — Scope string sent to the Auth URL (per your IdP’s docs).

- **Enable PKCE** — When on, Casdoor sends `code_challenge`/`code_challenge_method=S256` in the auth request and `code_verifier` in the token request. Enable if your IdP requires or supports PKCE.

- **Token URL** — Token endpoint. Casdoor calls it with the code to get an access token. Example:

  ```bash
  curl -X POST -u "{ClientID}:{ClientSecret}" --data-binary "code={code}&grant_type=authorization_code&redirect_uri=https://{your-casdoor-hostname}/callback" https://door.casdoor.com/api/login/oauth/access_token
  ```

  When PKCE is enabled, the request includes the code verifier:

  ```bash
  curl -X POST -u "{ClientID}:{ClientSecret}" --data-binary "code={code}&grant_type=authorization_code&redirect_uri=https://{your-casdoor-hostname}/callback&code_verifier={code_verifier}" https://door.casdoor.com/api/login/oauth/access_token
  ```

  Response must include at least:

  ```json
  {
    "access_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6Ixxxxxxxxxxxxxx",
    "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6xxxxxxxxxxxxxx",
    "token_type": "Bearer",
    "expires_in": 10080,
    "scope": "openid profile email"
  }
  ```

- **UserInfo URL** — API to get user info with the access token. Casdoor calls it like:

  ```bash
  curl -X GET -H "Authorization: Bearer {accessToken}" https://door.casdoor.com/api/userinfo
  ```

  Response must include at least:

  ```json
  {
    "name": "admin",
    "preferred_username": "Admin",
    "email": "admin@example.com",
    "picture": "https://casbin.org/img/casbin.svg",
    "phone": "+1234567890"
  }
  ```

  `phone` is optional; if present, it is stored as the user’s phone in Casdoor.

- **Favicon** — URL of the provider logo shown on the Casdoor login page.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/weCom.md
================================================================================

---
title: WeCom OAuth
description: Add WeCom (WeChat Work) as an OAuth provider for internal or third-party apps.
keywords: [WeCom, OAuth, WeChat Work]
authors: [leo220yuyaodog]
---

WeCom supports OAuth so users can sign in from the WeCom client. You can use **internal** or **third-party** applications.

| Casdoor field   | Description |
|-----------------|-------------|
| Sub type        | Internal or Third-party |
| Method          | Silent or Normal |
| Client ID       | Enterprise **CorpID** |
| Client secret   | Enterprise **CorpSecret** |
| Agent ID        | Application **AgentId** |

:::info
- **Silent:** User clicks the link and is redirected to `redirect_URI?code=CODE&state=STATE`.
- **Normal:** A consent page is shown; after the user authorizes, redirect to `redirect_uri?code=CODE&state=STATE`.

See [WeCom OAuth](https://developer.work.weixin.qq.com/document/path/91119).
:::

**Internal apps:** [Internal Application](https://developer.work.weixin.qq.com/document/path/91022).  
**Third-party apps:** [Third-Party Application](https://developer.work.weixin.qq.com/document/path/91120).



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/gitee.md
================================================================================

---
title: Gitee OAuth
description: Add Gitee as an OAuth provider.
keywords: [Gitee, OAuth]
authors: [ErikQQY]
---

1. Go to [Gitee OAuth applications](https://gitee.com/oauth/applications) and create an application (or open an existing one).

![Gitee Workbench](/img/providers/OAuth/giteebench.png)
![Gitee](/img/providers/OAuth/gitee.png)

Set **name**, **description**, **homepage**, and **authorization callback URL**. The callback URL must be **Casdoor’s callback URL**. In Casdoor, the application **Redirect URL** is your application’s callback URL. See [Application config](/docs/application/config#how-the-flow-works). Grant the permissions you need; enable **email** so Casdoor can read the user’s email.

:::info
**Callback URL:** In Gitee use Casdoor’s callback URL; in Casdoor use your application’s redirect URL.
:::

2. After creating the app, copy **Client ID** and **Client Secret**.

![Gitee Client](/img/providers/OAuth/giteeclient.png)

3. In Casdoor add an **OAuth** provider, set **Type** to **Gitee**, and enter **Client ID** and **Client secret**.

![Gitee Provider](/img/providers/OAuth/giteeprovider.png)

:::caution
Enable the **email** scope in the Gitee app; otherwise scope authorization may fail.
:::

![Gitee scope](/img/giteescope.jpg)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/github.md
================================================================================

---
title: GitHub OAuth
description: Add GitHub as an OAuth provider (web or device flow).
keywords: [GitHub, OAuth]
authors: [ErikQQY]
---

GitHub OAuth supports both the web application flow and the device flow. Use a **GitHub App** (not a legacy OAuth App) so you can configure multiple redirect URIs for test and production. See [GitHub: Migrating OAuth Apps to GitHub Apps](https://docs.github.com/en/developers/apps/getting-started-with-apps/migrating-oauth-apps-to-github-apps).

## Register a GitHub App

1. Go to [GitHub Developer Settings](https://github.com/settings/apps/new) and create a new **GitHub App**.
2. Set **GitHub App name**, **Homepage URL**, **Description**, and **Callback URL**.

![GitHub](/img/providers/OAuth/github.png)

:::info
In the GitHub App, **Callback URL** must be **Casdoor’s callback URL**. In Casdoor, the application **Redirect URL** is your app’s callback URL. See [Application config](/docs/application/config#how-the-flow-works).
:::

3. After creating the app, generate the **Client secret** (under the app settings).

![GitHub Client ID](/img/providers/OAuth/githubclient.png)

## Add the provider in Casdoor

Create an **OAuth** provider, set **Type** to **GitHub**, and enter the **Client ID** and **Client Secret** from the GitHub App.

![Github Provider](/img/providers/OAuth/githubprovider.png)

![githubapps](/img/providers/OAuth/githubapps.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/user-mapping.md
================================================================================

---
title: OAuth user mapping
description: Map OAuth provider claims to Casdoor user fields.
keywords: [OAuth, user mapping, claims, IDP, identity provider]
authors: [nomeguy]
---

Casdoor captures basic profile data (username, email, avatar) from OAuth sign-in. **User mapping** lets you map additional IdP claims to Casdoor user fields (phone, name, region, etc.).

## Supported Fields

Supported user fields for mapping:

- **phone** - Phone number
- **countryCode** - Country calling code
- **firstName** - First name
- **lastName** - Last name
- **region** - Geographic region
- **location** - Full location or address
- **affiliation** - Organization or company affiliation
- **title** - Job title or position
- **homepage** - Personal website URL
- **bio** - Biography or description
- **tag** - Custom tag or category
- **language** - Preferred language
- **gender** - Gender identity
- **birthday** - Date of birth
- **education** - Educational background
- **idCard** - ID card number
- **idCardType** - Type of ID card

Standard fields (id, username, displayName, email, avatarUrl) are handled automatically and don't need mapping configuration.

## Configuration

To configure user mapping:

1. Open **Providers** and select or create an OAuth provider (e.g. Okta, Azure AD B2C, Google).
2. Scroll to **User mapping** and add entries:
   - **User field**: The Casdoor user field you want to populate
   - **Claim name**: The exact claim name from your OAuth provider's response

For example, if your identity provider returns a claim named `given_name` and you want to map it to the user's first name in Casdoor:

- User field: `firstName`
- Claim name: `given_name`

## Provider-Specific Examples

### Okta

Okta returns claims like `given_name`, `family_name`, and `locale`. You might configure:

- `firstName` → `given_name`
- `lastName` → `family_name`
- `language` → `locale`

### Azure AD B2C

Azure AD B2C can return custom claims configured in your user flows. For instance:

- `phone` → `extension_PhoneNumber`
- `title` → `jobTitle`
- `location` → `city`

### Generic OAuth Providers

Most OAuth providers following standard protocols return claims in their userinfo endpoint. Check your provider's documentation to find available claim names.

## Behavior

The mapping works with these characteristics:

- **Non-destructive**: Existing user field values are preserved. Mapping only updates empty fields.
- **Automatic sync**: When users sign in via OAuth, the mapping is applied automatically.
- **Flexible**: Each provider can have its own unique mapping configuration.
- **Extra claims**: All claims from the provider are stored in the user's extra data, even if not explicitly mapped.

## Common Scenarios

### Enterprise SSO

When integrating with enterprise identity providers like Okta or Azure AD, you often want to sync organizational data:

```text
title → jobTitle
affiliation → companyName
region → officeLocation
```

### Social Login Enhancement

Social providers (e.g. Google, Facebook) provide basic profile data; additional details can be captured as follows:

```text
location → location
homepage → website
bio → about_me
```

### Multi-Provider Setup

Different providers may use different claim names for the same data. Configure each provider independently:

**Google OAuth**:

- `firstName` → `given_name`
- `lastName` → `family_name`

**GitHub OAuth**:

- `location` → `location`
- `homepage` → `blog`
- `bio` → `bio`

## Technical Details

When a user authenticates through OAuth:

1. Casdoor receives the OAuth token and fetches user info from the provider
2. The provider response includes standard fields plus extra claims
3. Standard fields (username, email, etc.) are processed first
4. User mapping rules are applied to populate additional fields from extra claims
5. All raw claims are stored in the user's OAuth extra data for reference

This ensures that user profiles in Casdoor stay synchronized with your identity provider while maintaining flexibility in how data is structured.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/google.md
================================================================================

---
title: Google OAuth
description: Add Google as an OAuth provider.
keywords: [Google, OAuth]
authors: [ErikQQY]
---

Configure Google OAuth in the [Google API Console](https://console.developers.google.com).

## Configure in Google Cloud

1. Create or select a project. Open **APIs & Services** → **OAuth consent screen** and configure the consent screen.
2. Go to **Credentials** → **Create credentials** → **OAuth client ID**. Choose application type (e.g. Web application) and set **Authorized redirect URIs**.

![Setting up the project](/img/providers/OAuth/googlenewproject.png)
![Configure consent](/img/providers/OAuth/oauthconsentscreen.png)
![Registering the app](/img/providers/OAuth/appregistration.png)
![Credentials](/img/providers/OAuth/credential.png)
![Creating a credential](/img/providers/OAuth/createcredential.png)

:::info
**Authorized redirect URIs** in Google must be **Casdoor’s callback URL**. In Casdoor, the application **Redirect URL** is your application’s callback URL. See [Application config](/docs/application/config#how-the-flow-works).
:::

3. After creating the client, copy the **Client ID** and **Client Secret**.

![Client](/img/providers/OAuth/googleclient.png)

## Add the provider in Casdoor

Create an **OAuth** provider, set **Type** to **Google**, and enter the **Client ID** and **Client Secret**.

![Google Provider](/img/providers/OAuth/googleprovider.png)

### Optional: phone number scope

If you enable **Get password** (or need the user’s phone number), enable the [Google People API](https://console.cloud.google.com/apis/library/people.googleapis.com) and add the scope `https://www.googleapis.com/auth/user.phonenumbers.read` to the provider.

![Google People Api](/img/providers/OAuth/googleproviderpeopleapi.png)
![Google Provider Scope](/img/providers/OAuth/googleproviderscope.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/linkedin.md
================================================================================

---
title: LinkedIn OAuth
description: Add LinkedIn as an OAuth provider.
keywords: [LinkedIn, OAuth]
authors: [ErikQQY]
---

1. Create an app at [LinkedIn Developers](https://www.linkedin.com/developers/apps/new).

![LinkedIn](/img/providers/OAuth/linkedin.png)

2. Verify the LinkedIn page linked to the app. Only a company page admin can verify and grant permissions.

![LinkedIn Verify](/img/providers/OAuth/linkedin-verify.png)

:::note
Verification must be done by the company page administrator.
:::

3. In the app, enable **Sign In with LinkedIn** and add **Authorized redirect URLs**: use **Casdoor’s callback URL**. In Casdoor, set the application **Redirect URL** to your application’s callback URL. See [Application config](/docs/application/config#how-the-flow-works).

![LinkedIn sign in](/img/providers/OAuth/linkedinsignin.png)
![LinkedIn Redirect](/img/providers/OAuth/linkedinredirecturl.png)

4. Copy **Client ID** and **Client Secret** from the app.

![LinkedIn Client](/img/providers/OAuth/linkedinclient.png)

5. In Casdoor add an **OAuth** provider, set **Type** to **LinkedIn**, and enter **Client ID** and **Client secret**.

![LinkedIn Provider](/img/providers/OAuth/linkedinprovider.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/Weibo.md
================================================================================

---
title: Weibo OAuth
description: Add Weibo as an OAuth provider.
keywords: [Weibo, OAuth]
authors: [Marvelousp4]
---

Apply at the [Weibo Open Platform](https://open.weibo.com/developers/basicinfo): complete basic info and submit for review. Approval often takes about 2–3 days. After approval you receive **Client ID** and **Client Secret**. Create an **OAuth** provider in Casdoor, set **Type** to **Weibo**, and enter these values. Set the application’s **Redirect URL** in Casdoor to your app’s callback URL; in Weibo, the authorization callback URL must be Casdoor’s callback URL (see [Application config](/docs/application/config#how-the-flow-works)).



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/Tencent.md
================================================================================

---
title: Tencent QQ OAuth
description: Add Tencent QQ as an OAuth provider.
keywords: [Tencent QQ, OAuth]
authors: [Marvelousp4]
---

1. Apply to [become a QQ Connect developer](https://wiki.connect.qq.com/%E6%88%90%E4%B8%BA%E5%BC%80%E5%8F%91%E8%80%85). After approval, open [Connect QQ](https://connect.qq.com/manage.html#/) and create an application.
2. Note the **Client ID** and **Client Secret** from the application.
3. In Casdoor add an **OAuth** provider, set **Type** to **Tencent QQ**, and enter **Client ID** and **Client secret**. Set the application **Redirect URL** in Casdoor to your app’s callback URL; in QQ Connect, the authorization callback URL must be Casdoor’s callback URL. See [Application config](/docs/application/config#how-the-flow-works).



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/azureAD.md
================================================================================

---
title: Azure AD OAuth
description: Add Microsoft Azure Active Directory as an OAuth provider.
keywords: [Azure AD, Azure, OAuth]
authors: [leo220yuyaodog]
---

**Azure Active Directory (Azure AD)** provides a single identity for cloud and on-premises apps. Use it as an OAuth provider in Casdoor so users can sign in with their Microsoft accounts.

## Register an application

1. [Register an application](https://portal.azure.com/#view/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/~/RegisteredApps) in Azure AD and choose the account type (e.g. single tenant).

![azuread_register.png](/img/providers/OAuth/azuread_register.png)

2. Create a **client secret** and save the value (it is shown only once).

![azuread_secret.png](/img/providers/OAuth/azuread_secret.png)

3. Under **Authentication**, add **Redirect URIs** for Casdoor (e.g. `https://your-casdoor.com/callback`).

![azuread_uri.png](/img/providers/OAuth/azuread_uri.png)

4. Under **API permissions**, add the scopes you need (e.g. `User.Read`). Click **Grant admin consent**.

![azuread_permission.png](/img/providers/OAuth/azuread_permission.png)

5. In Casdoor, create an **OAuth** provider, set **Type** to **Azure AD**, and enter the **Client ID** and **Client Secret** from the Azure app.

![azuread_casdoor.png](/img/providers/OAuth/azuread_casdoor.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/lark.md
================================================================================

---
title: Lark OAuth
description: Add Lark (Feishu) as an OAuth provider.
keywords: [Lark, OAuth, Feishu]
authors: [Chinoholo0807]
---

## 1. Create a Lark application

On the [Lark Open Platform](https://open.feishu.cn/), create an application and enable it. In the app’s basic information, note **App ID** and **App Secret**. In security settings, add the redirect URL: `<your-casdoor-domain>/callback` (e.g. `https://door.example.com/callback`).

![create a new app](/img/providers/OAuth/lark_create_app.png)
![add redirect URL](/img/providers/OAuth/lark_redirect_url.png)

## 2. Create the provider in Casdoor

**Providers** → **Add**. Set **Category** to **OAuth**, **Type** to **Lark**. Map:

| Casdoor       | Lark        |
|---------------|-------------|
| Client ID     | App ID      |
| Client secret | App Secret  |

![create a Lark OAuth provider](/img/providers/OAuth/lark_provider_conf_detail.png)

## Username handling

Casdoor chooses the username from Lark’s response in this order: **UserId** (preferred), **UnionId** (links users across Lark orgs), **OpenId** (fallback, always present). This keeps sign-in working even when some fields are missing.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/adfs.md
================================================================================

---
title: AD FS OAuth
description: Add AD FS (Active Directory Federation Services) as an OAuth provider.
keywords: [AD FS, ADFS, Active Directory Federation Services]
authors: [ComradeProgrammer]
---

You need a working AD FS server. See the [AD FS documentation](https://docs.microsoft.com/en-us/windows-server/identity/active-directory-federation-services) and [AD FS deployment guide](https://docs.microsoft.com/en-us/windows-server/identity/ad-fs/deployment/ad-fs-deployment-guide).

## Enable OAuth confidential client in AD FS

Follow [Enabling OAuth Confidential Clients with AD FS](https://docs.microsoft.com/en-us/windows-server/identity/ad-fs/development/enabling-oauth-confidential-clients-with-ad-fs) to register an app and obtain a **client ID** and **client secret**.

![AD FS confidential client](/img/providers/OAuth/adfsconfidential1.png)
![AD FS confidential client](/img/providers/OAuth/adfsconfidential2.png)

Use the client identifier as **Client ID** and the secret as **Client secret** in Casdoor.

## Add the provider in Casdoor

**Providers** → **Add**. Set **Category** to **OAuth**, **Type** to **AD FS**. Enter the **Client ID** and **Client secret** from AD FS.

![AD FS provider in Casdoor](/img/providers/OAuth/adfscasdoor.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/okta.md
================================================================================

---
title: Okta OAuth
description: Add Okta as an OIDC/OAuth provider.
keywords: [Okta, OAuth, OIDC]
authors: [greenhandatsjtu]
---

1. Sign up at [Okta Developer](https://developer.okta.com/signup/).
2. **Applications** → **Applications** → **Create App Integration**. Choose **OIDC - OpenID Connect**, **Web Application**, then **Next**.
3. Set **Sign-in redirect URIs** to your Casdoor callback URL (e.g. `https://door.casdoor.com/callback`). In **Assignments** set **Controlled access**, then **Save**.
4. Copy **Client ID**, **Client secret**, and **Okta domain** from the app.

![Create an app integration](/img/providers/OAuth/oktacreateapp.png)
![Enter redirect URL](/img/providers/OAuth/oktasetredirecturl.png)
![Okta OIDC settings](/img/providers/OAuth/oktasettings.png)

In Casdoor add an **OAuth** provider, set **Type** to **Okta**, and enter **Client ID**, **Client secret**, and **Domain**. **Domain** must include the auth server path: use `https://<okta-domain>/oauth2/default` (not just the Okta domain). See [Okta authorization servers](https://developer.okta.com/docs/concepts/auth-servers/).

![Add Okta in Casdoor](/img/providers/OAuth/oktacasdoor.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/Twitter.md
================================================================================

---
title: Twitter OAuth
description: Add Twitter (X) as an OAuth provider (developer account required).
keywords: [Twitter, OAuth, X]
authors: [Marvelousp4]
---

:::caution
Twitter’s developer signup and app review can be strict. Approval may take time.
:::

1. Go to the [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard) and create or open a project and app.
2. In **Authentication settings**:
   - Enable **3-legged OAuth** (required for “Sign in with Twitter” and posting on behalf of users).
   - Enable **Request email address from users** if you need email.
3. Set the **Callback URL** to your Casdoor callback URL and save.

Casdoor uses **PKCE** (Proof Key for Code Exchange) for Twitter OAuth: a code verifier is generated per flow and sent during token exchange to reduce authorization-code interception risks.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/Steam.md
================================================================================

---
title: Steam OAuth
description: Add Steam as an OAuth provider (API key only).
keywords: [Steam, OAuth]
authors: [Marvelousp4]
---

1. Sign in at [Steam Web API Key](https://steamcommunity.com/dev/revokekey) and register an API key for your Casdoor domain or IP.
2. In Casdoor add an **OAuth** provider, set **Type** to **Steam**. Put the API key in **Client secret**. Leave **Client ID** empty.
3. Your Steam account must have at least one game to obtain an API key.

See [Steam Web API](https://steamcommunity.com/dev).



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/apple.md
================================================================================

---
title: Sign in with Apple
description: Add Apple as an OAuth provider (Sign in with Apple).
keywords: [Apple, OAuth, Sign in with Apple]
authors: [People257]
---

You need an [Apple Developer](https://developer.apple.com/account) account and an **Apple Developer Program** membership.

### Step 1: Configure App ID

Create a new App ID or configure an existing one, and ensure **Sign in with Apple** is enabled for it.

![Enable Sign in with Apple for App ID](/img/providers/OAuth/appledashboard.png)

### Step 2: Create a Services ID

Next, create a new identifier, making sure to select the **Services IDs** type. (The `Identifier` you set here will be your **Client ID** in Casdoor).

![Register Services ID](/img/providers/OAuth/appleregisterserviceid.png)

Then, configure this Services ID. Enable **Sign in with Apple** and click **Configure**.

![Edit Services ID Configuration](/img/providers/OAuth/appleeditserviceconfig.png)

### Step 3: Configure Redirect URLs

In the configuration screen, set up the **Return URLs** (callback URLs). You need to enter the **Redirect URL shown on the Casdoor provider page** here.

![Configure Callback URLs](/img/providers/OAuth/applecallbackconfig.png)

:::info Set Return URLs Correctly
The `Return URLs` on Apple **must** exactly match the `Redirect URL` shown on your Casdoor Apple provider configuration page (e.g., `https://your-casdoor-domain.com/callback`).
:::

### Step 4: Create a Key

After configuring the Services ID, create a **Key**.
When creating the Key, enable **Sign in with Apple** and associate it with your App ID.

![Configure Key Association](/img/providers/OAuth/applekeyconfig.png)

After registering the Key, note down the **Key ID** and **download the `.p8` file immediately**. (This file can only be downloaded once, save it securely!)

![Get Key ID and Download .p8 File](/img/providers/OAuth/applegetkeyid.png)

**Important:** Find and note down your **Team ID** from the **Membership** page on the Apple Developer Portal.

### Step 5: Add the provider in Casdoor

1. **Client ID** — The **Services ID** (Identifier) you created in Step 2.
2. **Team ID**: Enter your Apple **Team ID** (found on the Membership page).
3. **Key ID**: Enter the Apple **Key ID** you noted down.
4. **Key Text**: Open the downloaded `.p8` file with a text editor. Copy its **entire content** (including the `-----BEGIN...` and `-----END...` lines) and paste it here.
5. **Check Redirect URL**: Verify that the `Redirect URL` shown here in Casdoor has been correctly added to the **Return URLs** in your Apple Services ID configuration.

![Configure Casdoor Provider](/img/providers/OAuth/appleconfigcasdoor.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/facebook.md
================================================================================

---
title: Facebook OAuth
description: Add Facebook as an OAuth provider.
keywords: [Facebook, OAuth]
authors: [ErikQQY]
---

## Create a Facebook app

Go to [Facebook Developers](https://developers.facebook.com/apps/) and create a new app. Choose the app type (e.g. Consumer).

![Facebook select](/img/providers/OAuth/facebookselect.png)

After entering your name and contact email, you will be taken to the Facebook Developer dashboard.

![Dashboard](/img/providers/OAuth/dashboard.png)

Next, set up Facebook login:

![Facebook login](/img/providers/OAuth/facebooklogin.png)

Choose the Web platform for this app:

![Facebook web](/img/providers/OAuth/facebookweb.png)

Under **Facebook Login** → **Settings**, set **Valid OAuth Redirect URIs** to **Casdoor’s callback URL**. In Casdoor, the application **Redirect URL** is your application’s callback URL. See [Application config](/docs/application/config#how-the-flow-works).

![Redirect URIs](/img/providers/OAuth/facebookredirecturl.png)

Switch the app from **In development** to **Live** in the dashboard top bar.

![Top bar](/img/providers/OAuth/facebooktopbar.png)

Copy **App ID** and **App Secret** from **Settings** → **Basic**.

![Facebook app](/img/providers/OAuth/facebookappclient.png)

## Add the provider in Casdoor

Create an **OAuth** provider, set **Type** to **Facebook**, and enter **App ID** as **Client ID** and **App Secret** as **Client Secret**.

![Facebook Client](/img/providers/OAuth/facebookclient.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/telegram.md
================================================================================

---
title: Telegram
description: Add Telegram OAuth provider to your application
keywords: [Telegram, OAuth]
authors: [hsluoyz,oxkrypton]
---

Telegram Login Widget provides a secure way to authenticate users through their Telegram accounts. Unlike traditional OAuth providers, Telegram uses a widget-based approach with cryptographic verification.

## Create a Telegram Bot

Create a bot via [@BotFather](https://t.me/BotFather):

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts to create your bot
![Create Telegram Bot](/img/providers/OAuth/telegrambot.png)
3. After creation, BotFather will provide you with a **bot token** - save this securely
![Telegram client](/img/providers/OAuth/telegramclient.png)
4. Send `/setdomain` to BotFather and provide your domain (e.g., `example.com`)
![Telegram Setdomain](/img/providers/OAuth/telegramdomain.png)

:::tip

The bot token is sensitive information. Never share it publicly or commit it to version control.

:::

## Add Telegram Provider in Casdoor

1. Navigate to **Providers** in Casdoor's admin panel
2. Click **Add** to create a new provider
3. Set **Category** to `OAuth` and **Type** to `Telegram`
4. Configure the provider:
   - **Client ID**: Your bot's username (e.g. `casdoor_telegram_bot` no need @)
   - **Client Secret**: The bot token provided by BotFather
![Telegram provider](/img/providers/OAuth/telegramprovider.png)

:::note Domain Verification

Authentication will only work from the domain you registered with BotFather using the `/setdomain` command. Make sure your Casdoor instance is accessible from this domain.

:::

## Logging In with Telegram

With the setup completed, users can now log in with Telegram.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/DingTalk.md
================================================================================

---
title: DingTalk OAuth
description: Add DingTalk as an OAuth provider.
keywords: [DingTalk, OAuth]
authors: [Marvelousp4]
---

Configure DingTalk at the [DingTalk Open Platform](https://open-dev.dingtalk.com/). Create or open an app and note **AppKey** and **AppSecret** (these map to **Client ID** and **Client secret** in Casdoor).

| Casdoor       | DingTalk  |
|---------------|-----------|
| Client ID     | AppKey    |
| Client secret | AppSecret |

![DingTalk](/img/providers/OAuth/dingtalkapp.png)

Add the **Redirect Domain**: your Casdoor domain (e.g. `https://your-casdoor.com`).

![DingTalk](/img/providers/OAuth/dingtalkredirect.png)

## Required permission

Enable **Contact.User.Read** in your DingTalk app (used for `/v1.0/contact/users/me`). Without it, Casdoor cannot fetch user info and sign-in will fail. Enable it under **Permissions Management**.

![DingTalk](/img/providers/OAuth/dingtalkpermission.png)

:::caution
**Contact.User.Read** must be enabled in the DingTalk application.
:::

## Username mapping

Casdoor uses DingTalk’s **unionid** as the username. This keeps the same user mapped across your DingTalk org even when other details change.

## Add the provider in Casdoor

Create an **OAuth** provider, set **Type** to **DingTalk**, and enter **AppKey** as **Client ID** and **AppSecret** as **Client secret**.

![DingTalk](/img/providers/OAuth/dingtalkprovider.png)

See [DingTalk developer docs](https://open.dingtalk.com/document/orgapp-server/tutorial-obtaining-user-personal-information).



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/gitlab.md
================================================================================

---
title: GitLab OAuth
description: Add GitLab (or self-hosted GitLab) as an OAuth provider.
keywords: [GitLab, OAuth]
authors: [hsluoyz]
---

Use the [GitLab Applications](https://gitlab.com/-/profile/applications) page (or `https://<your-gitlab>/-/profile/applications` for self-hosted) to create an OAuth application.

## Create the GitLab application

1. Click **Add new application**.
2. Set **Name** (e.g. "Casdoor"), **Redirect URI**, and **Scopes**.

:::caution
Enable scopes **read_user** and **profile**. Without them, authentication can fail.
:::

:::info
In GitLab, **Redirect URI** must be **Casdoor’s callback URL**. In Casdoor, the application **Redirect URL** is your application’s callback URL. See [Application config](/docs/application/config#how-the-flow-works).
:::

3. After creating the app, copy **Application ID** and **Secret** from the app details.

## Add the provider in Casdoor

Create an **OAuth** provider, set **Type** to **GitLab**, and enter **Application ID** as **Client ID** and **Secret** as **Client Secret**.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/Wechat.md
================================================================================

---
title: WeChat OAuth
description: Add WeChat as an OAuth provider (PC QR code or in-app browser).
keywords: [WeChat, OAuth]
authors: [Marvelousp4]
---

Add **WeChat** as an OAuth provider for PC (QR code) or mobile (WeChat in-app browser) sign-in.

## Get credentials

1. Register at the [WeChat Open Platform](https://open.weixin.qq.com/).
2. After your app is approved, you receive **App ID** and **App Secret**.

![wechat](/img/providers/OAuth/wechat.png)

## SubTypes

When configuring the WeChat provider, choose a **SubType**:

| SubType | Use case |
|--------|----------|
| **Web** (default) | PC browser: user scans QR code with WeChat app to sign in. |
| **Mobile** | WeChat built-in browser: OAuth inside the WeChat app. |

Use the same credentials; endpoints differ. For both PC and mobile, create two WeChat providers (one Web, one Mobile).

## Two keypairs (optional)

- **Client ID / Client Secret** — From **WeChat Open Platform (微信开放平台)** for PC QR-code login.
- **Client ID 2 / Client Secret 2** + **Access Token** — From **WeChat Media Platform (微信公众平台)** for in-WeChat-app login. **Access Token** is the value you set in the WeChat public account’s server configuration. WeChat only allows in-app login from the WeChat browser, not from other mobile browsers or apps.

If you set both keypairs and **Access Token**, enable **Enable QR code**: on PC, users can sign in with the Open Platform QR code or be prompted to follow the official account and then scan the Open Platform QR code. This flow is for PC only (mobile cannot scan its own QR code).

## Enable WeChat on the login page

Add the WeChat provider to your application and add WeChat to **Signin methods**. The login page will show a **WeChat** tab. QR code flow:

1. User selects the WeChat tab; a QR code is shown.
2. User scans with the WeChat app and authorizes.
3. Use **Refresh** below the QR code if it expires.

![set-wechat](/img/providers/OAuth/set-wechat.png)
![wechat-login](/img/providers/OAuth/wechat-login.png)

:::tip
Link your WeChat Open Platform and WeChat Media Platform accounts in the Open Platform so the same user is recognized when signing in from PC and from the WeChat app.
:::

:::note
WeChat does not support sign-in from third-party mobile apps or from mobile browsers outside the WeChat app. In-app login must happen inside WeChat.
:::

See [WeChat Open Platform – WeChat Login](https://developers.weixin.qq.com/doc/oplatform/en/Website_App/WeChat_Login/Wechat_Login.html).



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/googleonetap.md
================================================================================

---
title: Google One Tap
description: Learn how to add Google One Tap support to your application
keywords: [Google, Google One Tap, OAuth]
authors: [Chinoholo0807]
---

## Step 1: Configure Your Application

Add the [Google OAuth provider](./google.md) to your application first.

On the application edit page, add the Google OAuth provider and set its **Rule** from **Default** to **One Tap**.

![Switch rule from "Default" to "One Tap".](/img/providers/OAuth/googleonetap_rule_conf.png)

## Step 2: Logging In with Google One Tap

With the setup completed, users can now log in with Google One Tap.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/overview.md
================================================================================

---
title: Overview
description: Add OAuth providers so users can sign in with Google, GitHub, and other identity providers.
keywords: [OAuth, identity provider, sign-in]
authors: [ErikQQY]
---

Casdoor can use external OAuth applications as sign-in methods. After adding a provider, its icon appears on the login and sign-up pages. Supported OAuth providers:

| Provider      | Logo                                                                           | Provider    | Logo                                                                       | Provider     | Logo                                                                      | Provider     | Logo                                                                        |
|:--------------|:-------------------------------------------------------------------------------|:------------|:---------------------------------------------------------------------------|:-------------|:--------------------------------------------------------------------------|:-------------|:----------------------------------------------------------------------------|
| ADFS          | <img src="https://cdn.casbin.org/img/social_adfs.png" width="40" />            | Alipay      | <img src="https://cdn.casbin.org/img/social_alipay.png" width="40" />      | Amazon       | <img src="https://cdn.casbin.org/img/social_amazon.png" width="40" />     | Apple        | <img src="https://cdn.casbin.org/img/social_apple.png" width="40" />        |
| Auth0         | <img src="https://cdn.casbin.org/img/social_auth0.png" width="40" />           | Azure AD    | <img src="https://cdn.casbin.org/img/social_azuread.png" width="40" />     | Azure AD B2C | <img src="https://cdn.casbin.org/img/social_azureadb2c.png" width="40" /> | Baidu        | <img src="https://cdn.casbin.org/img/social_baidu.png" width="40" />        |
| Bilibili      | <img src="https://cdn.casbin.org/img/social_bilibili.png" width="40" />        | Bitbucket   | <img src="https://cdn.casbin.org/img/social_bitbucket.png" width="40" />   | Box          | <img src="https://cdn.casbin.org/img/social_box.png" width="40" />        | Casdoor      | <img src="https://cdn.casbin.org/img/social_casdoor.png" width="40" />      |
| Cloud Foundry | <img src="https://cdn.casbin.org/img/social_cloudfoundry.png" width="40" />    | Dailymotion | <img src="https://cdn.casbin.org/img/social_dailymotion.png" width="40" /> | Deezer       | <img src="https://cdn.casbin.org/img/social_deezer.png" width="40" />     | DigitalOcean | <img src="https://cdn.casbin.org/img/social_digitalocean.png" width="40" /> |
| DingTalk      | <img src="https://cdn.casbin.org/img/social_dingtalk.png" width="40" />        | Discord     | <img src="https://cdn.casbin.org/img/social_discord.png" width="40" />     | Tiktok       | <img src="https://cdn.casbin.org/img/social_douyin.png" width="40" />     | Dropbox      | <img src="https://cdn.casbin.org/img/social_dropbox.png" width="40" />      |
| Eve Online    | <img src="https://cdn.casbin.org/img/social_eveonline.png" width="40" />       | Facebook    | <img src="https://cdn.casbin.org/img/social_facebook.png" width="40" />    | Fitbit       | <img src="https://cdn.casbin.org/img/social_fitbit.png" width="40" />     | Gitea        | <img src="https://cdn.casbin.org/img/social_gitea.png" width="40" />        |
| Gitee         | <img src="https://cdn.casbin.org/img/social_gitee.png" width="40" />           | GitHub      | <img src="https://cdn.casbin.org/img/social_github.png" width="40" />      | GitLab       | <img src="https://cdn.casbin.org/img/social_gitlab.png" width="40" />     | Google       | <img src="https://cdn.casbin.org/img/social_google.png" width="40" />       |
| Heroku        | <img src="https://cdn.casbin.org/img/social_heroku.png" width="40" />          | InfluxCloud | <img src="https://cdn.casbin.org/img/social_influxcloud.png" width="40" /> | Infoflow     | <img src="https://cdn.casbin.org/img/social_infoflow.png" width="40" />   | Instagram    | <img src="https://cdn.casbin.org/img/social_instagram.png" width="40" />    |
| Intercom      | <img src="https://cdn.casbin.org/img/social_intercom.png" width="40" />        | Kakao       | <img src="https://cdn.casbin.org/img/social_kakao.png" width="40" />       | Lark         | <img src="https://cdn.casbin.org/img/social_lark.png" width="40" />       | Lastfm       | <img src="https://cdn.casbin.org/img/social_lastfm.png" width="40" />       |
| Line          | <img src="https://cdn.casbin.org/img/social_line.png" width="40" />            | LinkedIn    | <img src="https://cdn.casbin.org/img/social_linkedin.png" width="40" />    | Mailru       | <img src="https://cdn.casbin.org/img/social_mailru.png" width="40" />     | Meetup       | <img src="https://cdn.casbin.org/img/social_meetup.png" width="40" />       |
| Microsoft     | <img src="https://cdn.casbin.org/img/social_microsoftonline.png" width="40" /> | Naver       | <img src="https://cdn.casbin.org/img/social_naver.png" width="40" />       | Nextcloud    | <img src="https://cdn.casbin.org/img/social_nextcloud.png" width="40" />  | Okta         | <img src="https://cdn.casbin.org/img/social_okta.png" width="40" />         |
| OneDrive      | <img src="https://cdn.casbin.org/img/social_onedrive.png" width="40" />        | Oura        | <img src="https://cdn.casbin.org/img/social_oura.png" width="40" />        | Patreon      | <img src="https://cdn.casbin.org/img/social_patreon.png" width="40" />    | PayPal       | <img src="https://cdn.casbin.org/img/social_paypal.png" width="40" />       |
| QQ            | <img src="https://cdn.casbin.org/img/social_qq.png" width="40" />              | Salesforce  | <img src="https://cdn.casbin.org/img/social_salesforce.png" width="40" />  | Shopify      | <img src="https://cdn.casbin.org/img/social_shopify.png" width="40" />    | Slack        | <img src="https://cdn.casbin.org/img/social_slack.png" width="40" />        |
| SoundCloud    | <img src="https://cdn.casbin.org/img/social_soundcloud.png" width="40" />      | Spotify     | <img src="https://cdn.casbin.org/img/social_spotify.png" width="40" />     | Steam        | <img src="https://cdn.casbin.org/img/social_steam.png" width="40" />      | Strava       | <img src="https://cdn.casbin.org/img/social_strava.png" width="40" />       |
| Stripe        | <img src="https://cdn.casbin.org/img/social_stripe.png" width="40" />          | Telegram    | <img src="https://cdn.casbin.org/img/social_telegram.png" width="40" />    | TikTok       | <img src="https://cdn.casbin.org/img/social_tiktok.png" width="40" />     | Tumblr       | <img src="https://cdn.casbin.org/img/social_tumblr.png" width="40" />       |
| Twitch        | <img src="https://cdn.casbin.org/img/social_twitch.png" width="40" />          | Twitter     | <img src="https://cdn.casbin.org/img/social_twitter.png" width="40" />     | Typetalk     | <img src="https://cdn.casbin.org/img/social_typetalk.png" width="40" />   | Uber         | <img src="https://cdn.casbin.org/img/social_uber.png" width="40" />         |
| VK            | <img src="https://cdn.casbin.org/img/social_vk.png" width="40" />              | WeChat      | <img src="https://cdn.casbin.org/img/social_wechat.png" width="40" />      | WeCom        | <img src="https://cdn.casbin.org/img/social_wecom.png" width="40" />      | Weibo        | <img src="https://cdn.casbin.org/img/social_weibo.png" width="40" />        |
| WePay         | <img src="https://cdn.casbin.org/img/social_wepay.png" width="40" />           | Xero        | <img src="https://cdn.casbin.org/img/social_xero.png" width="40" />        | Yahoo        | <img src="https://cdn.casbin.org/img/social_yahoo.png" width="40" />      | Yammer       | <img src="https://cdn.casbin.org/img/social_yammer.png" width="40" />       |
| Yandex        | <img src="https://cdn.casbin.org/img/social_yandex.png" width="40" />          | Zoom        | <img src="https://cdn.casbin.org/img/social_zoom.png" width="40" />        | Email        | <img src="https://cdn.casbin.org/img/social_mail.png" width="40" />       | SMS          | <img src="https://cdn.casbin.org/img/social_msg.png" width="40" />          |
| Battle.net    | <img src="https://cdn.casbin.org/img/social_battlenet.png" width="40" />       |             |                                                                             |              |                                                                            |              |                                                                              |

## Registering with a third-party OAuth service

You need a **redirect URL** (your app’s URL after login, e.g. `https://forum.casbin.com/`), **scopes** (what you request from the user), and **Client ID / Client Secret** from the provider. Keep the client secret private.

## Adding an OAuth provider in Casdoor

1. Open **Providers** in the sidebar and click **Add**.
2. Set **Category** to **OAuth** and choose the **Type** (e.g. Google, GitHub).
3. Enter **Client ID** and **Client Secret** from the provider’s developer console.

## User field mapping

Use [User mapping](/docs/provider/oauth/user-mapping) to map OAuth claims (e.g. from Okta, Azure AD) to Casdoor user fields.

## Automatic account linking

Casdoor can link OAuth logins to existing users by OAuth identity, email/phone (if enabled), or username (case-insensitive). That lets you add OAuth without manual linking.

## Using the provider’s access token

After OAuth sign-in, Casdoor stores the provider’s access token on the user. Your app can read it via `/api/get-account` and call the provider’s API (e.g. GitHub, Google Drive) on behalf of the user. Only the user and org admins can see the token. See [OAuth docs](/docs/how-to-connect/oauth#accessing-oauth-provider-tokens).

## Attaching the provider to an application

1. Open **Applications**, edit the application.
2. Add the provider and set its rules (e.g. enable for login, signup, unbind).
3. Save.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/baidu.md
================================================================================

---
title: Baidu OAuth
description: Add Baidu as an OAuth provider.
keywords: [Baidu, Baidu OAuth]
authors: [Steve0x2a]
---

1. Read [Baidu Open Auth](https://openauth.baidu.com/doc/regdevelopers.html?qq-pf-to=pcqq.c2c) and [create an application](http://developer.baidu.com/console#app/create).

![Create Baidu APP](/img/providers/OAuth/baiduapp.png)

2. Set the redirect URL in the app settings. **Add your Casdoor domain in the domain setting**, not in the callback URL field — Baidu’s callback URL validation often fails if you put the full URL there, and only one domain or URL is allowed (unlike the docs).

![Baidu URL Setting](/img/providers/OAuth/baidusetting.png)
![Redirect URL Setting](/img/providers/OAuth/baidudomain.png)

:::caution
- Use the **domain** setting for your Casdoor domain; adding the full callback URL in the callback URL field often fails validation and breaks login.
- Only one URL or domain can be added.
:::

3. Copy **Client ID** and **Client Secret** from the app.

![Baidu Client](/img/providers/OAuth/baiduclient.png)

4. In Casdoor add an **OAuth** provider, set **Type** to **Baidu**, and enter **Client ID** and **Client secret**.

![Baidu Provider](/img/providers/OAuth/baiduprovider.png)

:::info Troubleshooting
- If Baidu reports an incorrect redirect URL: add your domain in the correct place, then reset the Secret (Baidu may show an error but the secret updates after refresh). If it still fails, delete the app and create a new one, and set the domain first.
- Baidu returns a masked username; Casdoor uses that masked value as the username.
:::



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/Alipay.md
================================================================================

---
title: Alipay OAuth
description: Add Alipay as an OAuth provider (certificate-based).
keywords: [Alipay, OAuth]
authors: [hsluoyz]
---

You need an [Alipay Open Platform](https://open.alipay.com/) developer account. See [preparation before access](https://opendocs.alipay.com/open/270/01didh).

## 1. Get APPID and certificates

### APPID

[Create an application](https://opendocs.alipay.com/open/200/105310) in the Alipay Open Platform console and note the **APPID**. See [APPID query guide](https://opendocs.alipay.com/common/02nebp).

### Certificates

Generate an RSA2 key pair per [Alipay docs](https://opendocs.alipay.com/common/056zub?pathHash=91c49771). You get `appPrivateKey.txt` and `appPublicKey.txt`. Upload the app certificate in the Alipay app and download: `alipayRootCert.crt`, `appCertPublicKey.crt`, `alipayCertPublicKey.crt`.

In Casdoor **Certs**, create two certs:

**App Cert**

| Casdoor field | Value |
|---------------|--------|
| Type | `x509` |
| Certificate | content of `appCertPublicKey.crt` |
| Private key | content of `appPrivateKey.txt` |

**Root Cert**

| Casdoor field | Value |
|---------------|--------|
| Type | `x509` |
| Certificate | content of `alipayCertPublicKey.crt` |
| Private key | content of `alipayRootCert.crt` |

:::info
In Alipay, the callback URL must be **Casdoor’s callback URL**. In Casdoor, the application **Redirect URL** is your application’s callback URL. See [Application config](/docs/application/config#how-the-flow-works).
:::

## 2. Create the Alipay OAuth provider in Casdoor

**Providers** → **Add**. Set **Category** to **OAuth**, **Type** to **Alipay**. Fill **Client ID** with the APPID and select the **App Cert** and **Root Cert** you created.

## Troubleshooting

If you see "asn1: syntax error: sequence truncated" or login failures:

1. App Cert: **Certificate** = `appCertPublicKey.crt`, **Private key** = `appPrivateKey.txt`.
2. Root Cert: **Certificate** = `alipayCertPublicKey.crt`, **Private key** = `alipayRootCert.crt`.
3. APPID matches the Alipay application.
4. Callback URL is set correctly in both Alipay and Casdoor.

See [Alipay Open Platform](https://opendocs.alipay.com/).



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/azureADb2c.md
================================================================================

---
title: Azure AD B2C OAuth
description: Add Azure AD B2C as an OAuth provider.
keywords: [Azure AD B2C, OAuth]
authors: [nomeguy]
---

Azure AD B2C is a customer identity platform supporting OpenID Connect, OAuth 2.0, and SAML. Use it as an OAuth provider so users can sign in with B2C accounts.

## 1. Create a B2C tenant

Create a B2C tenant in the [Azure Portal](https://portal.azure.com/).

## 2. Register an application

In the B2C tenant, register an application and note the **Application (client) ID**.

![azuread_register.png](/img/providers/OAuth/azuread_register.png)

## 3. Create a client secret

Create a **client secret** for the app and copy its value (it is shown only once).

![azuread_secret.png](/img/providers/OAuth/azuread_secret.png)

## 4. Add redirect URIs

In the app registration, add the **Redirect URIs** (e.g. your Casdoor callback URL).

![azuread_uri.png](/img/providers/OAuth/azuread_uri.png)

## 5. Define user flows

In B2C, define user flows for sign-up, sign-in, and profile management as needed.

## 6. Add the provider in Casdoor

**Providers** → **Add**. Set **Category** to **OAuth**, **Type** to **Azure AD B2C**. Enter the **Client ID** and **Client secret** from the B2C app.

![azuread_casdoor.png](/img/providers/OAuth/azuread_casdoor.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/oauth/infoflow.md
================================================================================

---
title: Infoflow OAuth
description: Add Baidu Infoflow as an OAuth provider.
keywords: [Infoflow, OAuth, Baidu]
authors: [Steve0x2a]
---

1. Log in at [Infoflow](http://id.qy.baidu.com/static/ge/login.html#/) and open [Infoflow applications](http://qy.baidu.com/index.html#applist).
2. Register an application and note the **AgentID**.
3. In the **Setting** tab, create a management group. In address book permissions, add your structure and grant the app the needed permissions; add the app to the specified location. Add the required sensitive interface permissions.
4. On the same page, copy **CorpID** and **Secret**.

![Create APP](/img/providers/OAuth/infoflowapp1.png)
![Create APP](/img/providers/OAuth/infoflowapp2.png)
![AgentID](/img/providers/OAuth/infoflowagentid.png)
![Setting](/img/providers/OAuth/infoflowsetting.png)
![Permission](/img/providers/OAuth/infoflowpermission1.png)
![Permission](/img/providers/OAuth/infoflowpermission2.png)
![Permission](/img/providers/OAuth/infoflowsecret.png)

5. In Casdoor add an **OAuth** provider, set **Type** to **Infoflow**, and fill in:

| Casdoor       | Infoflow   |
|---------------|------------|
| Client ID     | CorpID     |
| Client secret | Secret     |
| Agent ID      | AgentID    |

![Infoflow Provider](/img/providers/OAuth/infoflowprovider.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/saml/keycloak.md
================================================================================

---
title: Keycloak SAML
description: Use Keycloak as a SAML IdP for Casdoor sign-in.
keywords: [Keycloak, SAML]
authors: [seriouszyx]
---

[Keycloak](https://www.keycloak.org/) is an open-source IdP that supports SAML and OpenID Connect and can broker LDAP or other SAML IdPs. This guide configures a Keycloak SAML client and Casdoor so Keycloak users can sign in to Casdoor.

## Configure Keycloak

Example assumptions:

- Casdoor: UI at `http://localhost:7001`, API at `http://localhost:8000`. Adjust for your deployment.
- Keycloak: UI at `http://localhost:8080/auth`.
- SP ACS URL and Entity ID: `http://localhost:8000/api/acs`.

:::note

The `/api/acs` endpoint only accepts POST requests. Ensure Keycloak is configured to use HTTP POST binding for SAML responses.

:::

Use the default realm or create a new one.

![Add Keycloak realm](/img/providers/SAML/keycloak_realm_add.png)

![Keycloak realm](/img/providers/SAML/keycloak_realm.png)

## Add a client entry in Keycloak

:::info
See [Keycloak client SAML configuration](https://www.keycloak.org/docs/latest/server_admin/index.html#_client-saml-configuration).
:::

Click **Clients** in the menu and then click **Create** to go to the **Add Client** page. Fill in the fields as follows:

- **Client ID**: `http://localhost:8000/api/acs` - This will be the SP Entity ID used in the Casdoor configuration later.
- **Client Protocol**: `saml`.
- **Client SAML Endpoint**: `http://localhost:8000/api/acs` - This URL is where you want the Keycloak server to send SAML requests and responses. Generally, applications have one URL for processing SAML requests. Multiple URLs can be set in the Settings tab of the client.

![Add Keycloak client](/img/providers/SAML/keycloak_client_add.png)

Click **Save**. This action creates the client and brings you to the **Settings** tab.

The following are part of the settings:

1. **Name** — e.g. `Casdoor`; any friendly name for the Keycloak UI.
2. **Enabled** - Select `on`.
3. **Include Authn Statement** - Select `on`.
4. **Sign Documents** - Select `on`.
5. **Sign Assertions** - Select `off`.
6. **Encrypt Assertions** - Select `off`.
7. **Client Signature Required** - Select `off`.
8. **Force Name ID Format** - Select `on`.
9. **Name ID Format** - Select `username`.
10. **Valid Redirect URIs** - Add `http://localhost:8000/api/acs`.
11. **Master SAML Processing URL** - `http://localhost:8000/api/acs`.
12. Fine Grain SAML Endpoint Configuration
    1. **Assertion Consumer Service POST Binding URL** - `http://localhost:8000/api/acs`.
    2. **Assertion Consumer Service Redirect Binding URL** - `http://localhost:8000/api/acs`.

Save the configuration.

![Configure Keycloak client](/img/providers/SAML/keycloak_client_configure.png)

:::tip

To sign the authn request: enable **Client Signature Required** and upload your certificate. Casdoor’s private key and certificate (`token_jwt_key.key`, `token_jwt_key.pem`) are in the **object** directory. In Keycloak open **Keys** → **Import** → **Archive Format** → **Certificate PEM** and upload the certificate.

:::

Click **Installation** tab.

For Keycloak `<=` 5.0.0, select Format Option - **SAML Metadata IDPSSODescriptor** and copy the metadata.

For Keycloak 6.0.0+, select Format Option - **Mod Auth Mellon files** and click **Download**. Unzip the downloaded.zip, locate `idp-metadata.xml`, and copy the metadata.

![Download metadata](/img/providers/SAML/keycloak_client_install.png)

![Copy metadata](/img/providers/SAML/keycloak_client_copy.png)

## Configure in Casdoor

Create a new provider in Casdoor.

Select category as **SAML**, type as **Keycloak**. Copy the content of metadata and paste it into the **Metadata** field. The values of **Endpoint**, **IdP**, and **Issuer URL** will be generated automatically after clicking the **Parse** button. Finally, click the **Save** button.

:::tip

If **Client Signature Required** is enabled in Keycloak and you uploaded a certificate, enable **Sign request** in Casdoor.

:::

![Casdoor provider](/img/providers/SAML/keycloak_casdoor_provider.png)

Edit the application you want to configure in Casdoor. Select the provider you just added and click the **Save** button.

![Add provider for app](/img/providers/SAML/keycloak_casdoor_app.png)

## Test

Open the application’s login page; a Keycloak option appears. Click it to sign in via Keycloak; after success you are logged into Casdoor.

![Casdoor login](/img/providers/SAML/keycloak_casdoor_login.gif)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/saml/custom.md
================================================================================

---
title: Custom SAML
description: Connect any SAML 2.0 IdP to Casdoor as the SP.
keywords: [SAML, Custom]
authors: [Chinoholo0807]
---

Casdoor can act as a Service Provider (SP) and connect to any SAML 2.0 Identity Provider (IdP).

## 1. Configure your IdP

In your IdP (e.g. Google Workspace, Azure AD, Okta), register Casdoor as an SP with:

- **ACS URL**: `https://<your-casdoor-domain>/api/acs` (e.g. `https://door.example.com/api/acs`). This endpoint accepts **POST** only.
- **Entity ID (SP Entity ID)**: use the same URL as the ACS URL.

Replace `<your-casdoor-domain>` with your Casdoor host (e.g. `http://localhost:8000` → `http://localhost:8000/api/acs`).

## 2. Get IdP metadata

From your IdP, obtain the metadata XML (EntityID, SSO endpoint, etc.). Some IdPs (e.g. [Keycloak](/docs/provider/saml/keycloak)) need SP details before providing metadata.

## 3. Configure the SAML Custom provider in Casdoor

**Providers** → **Add**. Set **Category** to **SAML**, **Type** to **Custom**. Set **Favicon URL** (IdP logo) and paste the IdP **Metadata**. Click **Parse** to fill **Endpoint**, **IdP**, **Issuer URL**, **SP ACS URL**, and **SP Entity ID**. Save.

| Field       | Description        |
|------------|--------------------|
| Category   | SAML               |
| Type       | Custom             |
| Favicon URL| IdP logo URL       |
| Metadata   | IdP metadata XML   |

![configure saml custom provider](/img/providers/SAML/custom_provider.png)

Add the SAML provider to the application’s **Providers** list.

![add saml custom provider to application](/img/providers/SAML/custom_provider_add.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/saml/overview.md
================================================================================

---
title: SAML provider overview
description: Sign in with external SAML 2.0 identity providers (Casdoor as SP).
keywords: [SAML, Keycloak, Alibaba Cloud IDaaS]
authors: [seriouszyx]
---

Casdoor can act as a **SAML 2.0 Service Provider (SP)** so users sign in with an external Identity Provider (IdP). Casdoor does not store user credentials; authentication is handled by the IdP.

Supported SAML providers: **Alibaba Cloud IDaaS**, **Keycloak**, **Custom**. After adding a provider, its icon appears on the login page.

| Alibaba Cloud IDaaS | Keycloak | Custom |
| :----------: | :------: | :-----: |
| <img src="https://cdn.casbin.org/img/social_aliyun.png" width="40"></img> | <img src="https://cdn.casbin.org/img/social_keycloak.png" width="40"></img> | <img src="https://cdn.casbin.org/img/social_custom.png" width="40"></img> |
|      ✅      |    ✅    |    ✅    |

## Terms

- **Identity Provider (IdP)** — The service that holds identities and authenticates users (e.g. Keycloak, Azure AD).
- **Service Provider (SP)** — The application that protects resources; here, Casdoor.
- **Assertion Consumer Service (ACS)** — The endpoint that receives SAML assertions from the IdP.

## Configuring the external IdP (Casdoor as SP)

When you set up the external IdP (e.g. Google Workspace, Azure AD), use these values for Casdoor:

- **ACS URL (Assertion Consumer Service URL)**: This is the endpoint where the IdP will send SAML assertions. For Casdoor, use: `https://<your-casdoor-domain>/api/acs` (replace `<your-casdoor-domain>` with your actual Casdoor domain, e.g., `https://door.example.com/api/acs`)

- **Entity ID (SP Entity ID)**: This uniquely identifies your Casdoor instance as a Service Provider. Use the same URL as the ACS URL: `https://<your-casdoor-domain>/api/acs`

- **Request Method**: The `/api/acs` endpoint only accepts POST requests. Ensure your IdP is configured to send SAML responses via HTTP POST binding.

## User Attribute Mapping

When a user authenticates through SAML, Casdoor extracts user information from the SAML assertion based on your provider's attribute mapping configuration. The username field is particularly important as it's required for user identification and creation in Casdoor.

If your IdP doesn't explicitly provide a username mapping or the username field comes back empty, Casdoor automatically applies a fallback strategy:

1. First, it attempts to use the **email address** from the SAML assertion as the username
2. If no email is available, it falls back to the **NameID** (unique identifier) from the assertion

This fallback mechanism ensures smooth authentication even when username attributes aren't explicitly configured in your IdP, which is common with providers like Azure AD where the default attribute claims might not include a separate username field.

## Login Behavior

Unlike OAuth providers which auto-redirect when configured as the sole authentication method, SAML providers always display their button on the login page. This design ensures users explicitly choose to authenticate via SAML before being redirected to their identity provider. Even with a single SAML provider configured, clicking the provider button is required to initiate the login flow.

This behavior prevents unexpected redirects and gives users clear control over the authentication method they're using, which is particularly important in enterprise environments where SAML is often one of multiple authentication options.

## How SAML integration works

When using SAML SSO, users log into Casdoor via the identity provider without ever passing credentials to Casdoor. The progress is shown in the following diagram.

![SAML](/img/providers/SAML/SAML.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/saml/aliyun.md
================================================================================

---
title: Alibaba Cloud IDaaS SAML
description: Use Alibaba Cloud IDaaS (EIAM) as a SAML IdP for Casdoor.
keywords: [Alibaba Cloud IDaaS, SAML, EIAM]
authors: [seriouszyx]
---

## Create SAML application in Alibaba Cloud IDaaS

Login to the [Alibaba Cloud management console](https://account.aliyun.com/), search and go to the Application Indentity Service (IDentity-as-a-Service, IDaaS).

![Alibaba Cloud IDaaS](/img/providers/SAML/aliyun.png)

Click **EIAM Instance List** and open the free version.

![Alibaba Cloud EIAM](/img/providers/SAML/aliyun_eiam.png)

An instance will be created and run automatically after opening. Click on the instance name or the **Manage** button to enter the IDaaS management console.

![Alibaba Cloud EIAM List](/img/providers/SAML/aliyun_eiam_list.png)

After entering the IDaaS management console, click **Add Application**, search for **SAML**, and click **Add Application**.

![Add Alibaba Cloud SAML](/img/providers/SAML/aliyun_saml_add.png)

Click **Add SigningKey**.

![Add Signing Key](/img/providers/SAML/aliyun_saml_signingkey.png)

Fill in all required information and submit.

![Fill in Signing Key](/img/providers/SAML/aliyun_saml_signingkey_input.png)

Select the added SigningKey.

![Select added Signing Key](/img/providers/SAML/aliyun_saml_signingkey_select.png)

Fill in all the required information below and submit.

- IDP IdentityId: Keep the same as Issuer URL in Casdoor.
- SP Entity ID & SP ACS URL (SSO Location): Use placeholders for now; after configuring Casdoor, set both to `https://<your-casdoor-domain>/api/acs`.
- Assertion Attribute: Directly fill in as username.
- Account Association Mode: Account Association

:::note

The ACS URL (`/api/acs`) only accepts POST requests. Ensure your IdP is configured to use HTTP POST binding.

:::

![Update information of Signing Key](/img/providers/SAML/aliyun_saml_signingkey_update.png)

## Account authorization & association

After the application is successfully added, an authorization prompt will pop up. Do not authorize it now, add an account and then authorize it.

Go to **Organizations and Groups** and click on **New Account**.

![Add account](/img/providers/SAML/aliyun_account.png)

Fill in all required information and submit.

![Fill in account information](/img/providers/SAML/aliyun_account_add.png)

Go to **Application Authorization**, select the accounts you want to authorize and click **Save**.

![Account authorizationn](/img/providers/SAML/aliyun_account_authorization.png)

Go to the **Application List**, click **View application sub-accounts**, and then click **Add account association**.

![View sub-account](/img/providers/SAML/aliyun_subaccount_view.png)
![Add sub-account](/img/providers/SAML/aliyun_subaccount_add.png)

Fill in the primary and sub accounts that need to be associated and click **Save**.

The primary account exists in IDaaS, and the sub account is the ID of the user in Casdoor.

![Associate](/img/providers/SAML/aliyun_subaccount_input.png)

## Export IDaaS Metadata

Go to the **Application List**, click **View Application Details** and click **Export IDaaS SAML Metadata**.

![Export](/img/providers/SAML/aliyun_saml_metadata.png)

## Configure in Casdoor

Create a new provider in Casdoor.

Set **Category** to **SAML**, **Type** to **Alibaba Cloud IDaaS**. Copy the content of metadata and paste it to the **Metadata** input. The values of **Endpoint**, **IdP** and **Issuer URL** will be generated automatically after clicking the **Parse** button.

![Casdoor provider](/img/providers/SAML/aliyun_casdoor.png)

Copy the **SP ACS URL** and the **SP Entity ID** and click the **Save** button.

Edit the application you want to configure in Casdoor. Select the provider just added and click the button **Save**.

![Add provider for app](/img/providers/SAML/aliyun_casdoor_provider.png)

## Modify SAML application in Alibaba Cloud IDaaS

Disable the application and then click **Modify Application**.

![Modify SAML app](/img/providers/SAML/aliyun_saml_modify.png)

Fill in **SP Entity ID** and **SP ACS URL(SSO Location)** with the content copied in Casdoor. Submit and enable application.

![Modify SAML app](/img/providers/SAML/aliyun_saml_modify_input.png)

## Test

Open the application’s login page; an IDaaS icon appears. Click it to sign in via Alibaba Cloud IDaaS; after success you are logged into Casdoor.

![Casdoor login](/img/providers/SAML/aliyun_casdoor_login.gif)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/saml/google-workspace.md
================================================================================

---
title: Google Workspace
description: Using Google Workspace as SAML IdP
keywords: [Google Workspace, SAML]
authors: [nomeguy]
---

Configure Google Workspace as a SAML IdP so users can sign in with their Google Workspace accounts.

## Configure SAML App in Google Workspace

Access the Google Admin Console (admin.google.com) and navigate to **Apps** > **Web and mobile apps**.

Click **Add App** > **Add custom SAML app**.

### Basic Information

Enter an **App name** (e.g., "Casdoor") and optionally upload an app icon. Click **Continue**.

### Google Identity Provider Details

Download the metadata or note the following values provided by Google:

- **SSO URL**
- **Entity ID**
- **Certificate**

Click **Continue**.

### Service Provider Details

Configure Casdoor as the Service Provider with the following values:

- **ACS URL**: `https://<your-casdoor-domain>/api/acs`
  - Example: `https://door.example.com/api/acs`
- **Entity ID**: `https://<your-casdoor-domain>/api/acs`
  - Use the same URL as ACS URL
- **Name ID format**: `EMAIL`
- **Name ID**: `Basic Information > Primary email`

:::note

The `/api/acs` endpoint only accepts POST requests. Google Workspace uses POST binding by default.

:::

Click **Continue**.

### Attribute Mapping

Configure attribute mapping (optional):

- **email** → **Primary email**
- **displayName** → **First name** and **Last name**

Click **Finish**.

### Enable the App

After creating the app, make sure to turn it **ON** for your organization or specific organizational units.

## Configure SAML Provider in Casdoor

In the Casdoor admin console, navigate to **Providers** and click **Add**.

Select the following:

- **Category**: `SAML`
- **Type**: `Custom`
- **Metadata**: Paste the metadata downloaded from Google Workspace, or manually enter the SSO URL, Entity ID, and certificate.

Click **Parse** to automatically fill in the fields, then click **Save**.

Copy the generated **SP ACS URL** and **SP Entity ID** values (they should match `https://<your-casdoor-domain>/api/acs`).

## Add Provider to Application

Edit your Casdoor application and add the Google Workspace SAML provider to the **Providers** list. Click **Save**.

## Test the Integration

Navigate to your Casdoor application's login page. You should see a Google Workspace login option. Click it to test the SAML authentication flow.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/saml/azure-ad.md
================================================================================

---
title: Azure AD
description: Using Azure AD as SAML IdP
keywords: [Azure AD, SAML, Microsoft Entra]
authors: [nomeguy]
---

Configure Azure AD (Microsoft Entra ID) as a SAML IdP so users can sign in with their Azure AD accounts.

## Create Enterprise Application in Azure AD

Sign in to the [Azure Portal](https://portal.azure.com/) and navigate to **Azure Active Directory** > **Enterprise applications**.

Click **New application** > **Create your own application**.

Enter a name (e.g., "Casdoor") and select **Integrate any other application you don't find in the gallery (Non-gallery)**. Click **Create**.

## Configure Single Sign-On

In your new enterprise application, navigate to **Single sign-on** and select **SAML**.

### Basic SAML Configuration

Click **Edit** on the Basic SAML Configuration section and enter:

- **Identifier (Entity ID)**: `https://<your-casdoor-domain>/api/acs`
  - Example: `https://door.example.com/api/acs`
- **Reply URL (Assertion Consumer Service URL)**: `https://<your-casdoor-domain>/api/acs`
  - Use the same URL as Entity ID

:::note

The `/api/acs` endpoint only accepts POST requests. Azure AD uses POST binding by default for SAML responses.

:::

Click **Save**.

### Attributes & Claims

The default attributes configuration is typically sufficient:

- **Unique User Identifier**: `user.userprincipalname`
- **emailaddress**: `user.mail`
- **name**: `user.userprincipalname`

You can customize these mappings if needed. When the username attribute is not explicitly mapped, Casdoor will automatically fall back to using the email address or NameID from the SAML assertion to populate the username field.

### SAML Certificates

Download the **Certificate (Base64)** from the SAML Certificates section.

### Set up Casdoor

Note the following URLs from the **Set up Casdoor** section:

- **Login URL**
- **Azure AD Identifier**
- **Logout URL**

## Configure SAML Provider in Casdoor

In the Casdoor admin console, navigate to **Providers** and click **Add**.

Select the following:

- **Category**: `SAML`
- **Type**: `Custom`
- **Metadata**: You can either:
  - Download the **Federation Metadata XML** from Azure AD and paste it here, or
  - Manually configure using the Login URL, Azure AD Identifier, and Certificate

Click **Parse** to automatically fill in the fields, then click **Save**.

## Assign Users

Back in Azure AD, navigate to **Users and groups** in your enterprise application and assign users or groups who should have access to Casdoor.

## Add Provider to Application

Edit your Casdoor application and add the Azure AD SAML provider to the **Providers** list. Click **Save**.

## Test the Integration

Navigate to your Casdoor application's login page. You should see an Azure AD login option. Click it to test the SAML authentication flow.

You can also use the **Test** button in Azure AD's SAML configuration to verify the setup.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/guest-auth.md
================================================================================

---
title: Guest authentication
description: Create temporary users without credentials and upgrade them later.
keywords: [guest, authentication, temporary users, passwordless]
authors: [nomeguy]
---

**Guest authentication** creates temporary users with no username or password. Users can use the app immediately; require full registration later if needed.

## Creating a guest user

POST to the token endpoint with the special code `guest-user`:

```bash
POST https://<CASDOOR_HOST>/api/login/oauth/access_token
```

**Request Body:**

```json
{
    "grant_type": "authorization_code",
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "code": "guest-user"
}
```

:::note
The code `"guest-user"` is a Casdoor extension that creates a guest user instead of completing the normal OAuth code flow.
:::

**Response:**

```json
{
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "id_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 10080,
    "scope": "openid"
}
```

Casdoor creates a user with: username `guest_<uuid>`, a random password, and tag `guest-user`.

## Upgrading to a normal user

When the user sets or changes their username (to something not starting with `guest_`) or sets a password via the user update API, they are upgraded: the tag becomes `normal-user` and they can use normal sign-in.

## Restrictions

Guest users cannot sign in via the normal login page until they upgrade (set a real username or password).

## Example Integration

```javascript
// Create a guest user
async function createGuestUser() {
  const response = await fetch('https://your-casdoor-host/api/login/oauth/access_token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      grant_type: 'authorization_code',
      client_id: 'your_client_id',
      client_secret: 'your_client_secret',
      code: 'guest-user'
    })
  });
  
  const data = await response.json();
  return data.access_token;
}

// Later, upgrade the guest user
async function upgradeGuestUser(accessToken, newUsername, newPassword) {
  const response = await fetch('https://your-casdoor-host/api/update-user', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({
      name: newUsername,
      password: newPassword
    })
  });
  
  return response.json();
}
```

## Related Documentation

- [OAuth 2.0](/docs/how-to-connect/oauth) - Standard OAuth flows
- [User Tags](/docs/user/overview#user-tags) - Understanding user tags
- [Application Tags](/docs/application/tags) - Restricting access by tags



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/totp-authenticator-app.md
================================================================================

---
title: Casdoor authenticator app
description: TOTP authenticator app for iOS and Android, synced with Casdoor.
keywords: [authenticator, 2fa, TOTP, MFA]
authors: [IZUMI-Zu]
---

**Casdoor Authenticator** ([app.casdoor.org](https://app.casdoor.org/)) is an open-source TOTP app ([GitHub](https://github.com/casdoor/casdoor-authenticator)) similar to Google Authenticator or Microsoft Authenticator. It provides MFA with time-based one-time passwords (TOTP) on iOS and Android and can sync accounts with Casdoor.

### Features

- **MFA** — Generate TOTP codes for 2FA.
- **Offline** — Codes work without internet.
- **Sync** — Accounts sync across devices via Casdoor.
- **Privacy** — Data encrypted and stored securely.
- **UI** — Simple, intuitive interface.

| Android | iOS |
|---------|-----|
| ![android](/img/totp-authenticator-app/android.png) | ![ios](/img/totp-authenticator-app/ios.png) |

## What is TOTP?

**TOTP** (Time-based One-Time Password) is a standard 2FA method. Codes are generated from a shared secret and the current time ([RFC 6238](https://tools.ietf.org/html/rfc6238)): they change every 30 seconds, work offline, and are widely supported.

## Using the app

### Step 0: Install

- **Android**: [Releases](https://github.com/casdoor/casdoor-authenticator/releases) or [app.casdoor.org](https://app.casdoor.org).
- **iOS**: See [app.casdoor.org](https://app.casdoor.org) and the [repo](https://github.com/casdoor/casdoor-authenticator).
- **Build from source**: [Casdoor Authenticator – Building from source](https://github.com/casdoor/casdoor-authenticator#building-from-source).

### Step 1: Enable MFA account storage (optional)

To store TOTP accounts in Casdoor, enable the **MFA accounts** setting on the Casdoor server.

![Mfa account setting](/img/totp-authenticator-app/mfa-account-setting.png)

### Step 2: Connect to Casdoor

After installing the app (and enabling MFA accounts if you use sync), connect in one of these ways:

| Method | Steps |
|--------|--------|
| **Manual** | Tap **Enter Server Manually**, enter server URL, client ID, and organization name, then sign in. |
| **QR code** | Tap **Scan QR Code**, scan the QR from **My Account** → **MFA accounts** on the Casdoor server. |
| **Demo** | Tap **Try Demo Server** to use the preconfigured demo instance. |

![Login](/img/totp-authenticator-app/login.png)

You can then view TOTP codes and manage 2FA accounts in the app.

## Migration from other authenticators

### From Google Authenticator

In Google Authenticator: **Menu** → **Transfer accounts** → select accounts → **Export** (QR code). In Casdoor Authenticator, scan that QR to import.

![Export TOTP data](/img/totp-authenticator-app/google-export.png)
![Import TOTP data from Google Authenticator](/img/totp-authenticator-app/import-totp-google.gif)

### From Microsoft Authenticator (Android, root required)

1. On the device with Microsoft Authenticator, the app data is under `/data/data/com.azure.authenticator/databases/`. Root access is required to read it.
2. Copy the `PhoneFactor` database file.
3. In Casdoor Authenticator: import → **Import from Microsoft Authenticator** → select the `PhoneFactor` file.
4. The app imports the TOTP accounts.

![Import TOTP data from Microsoft Authenticator](/img/totp-authenticator-app/import-totp-microsoft.gif)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/webauthn.md
================================================================================

---
title: WebAuthn
description: Sign in with WebAuthn (passkeys, fingerprint, face, security keys).
keywords: [webauthn, passkey, FIDO]
authors: [ComradeProgrammer]
---

Casdoor supports **WebAuthn** so users can sign in with built-in authenticators (fingerprint, face, Windows Hello) or security keys (e.g. YubiKey) instead of (or in addition to) a password.

## What is WebAuthn?

WebAuthn (Web Authentication API) is a W3C/FIDO standard that uses public-key cryptography for registration and sign-in. The server stores a public key; the private key stays on the user’s device. Sign-in works by proving possession of the private key (e.g. via biometrics or a security key). Credentials are bound to the user, the authenticator, and the site origin.

For more detail: [webauthn.guide](https://webauthn.guide/).

## Enable WebAuthn in Casdoor

### Step 0: Configuration

1. In `conf/app.conf`, set **origin** to the exact URL of your Casdoor site:

   ```ini
   origin = "http://localhost:8000"
   ```

   :::caution
   WebAuthn requires **HTTPS** in production; `localhost` is allowed for development.
   :::

2. As an admin, open the application edit page and turn on **Enable WebAuthn signin** (off by default).

### Step 1: Register a credential

Go to **My Account**. Use **Add WebAuthn Credential** and follow your device’s prompt to register a new credential. You can delete credentials from the list.

![WebAuthn1](/img/webauthn/webauthn.png)

### Step 2: Sign in with WebAuthn

Sign out, then on the login page select the WebAuthn method, enter your username, and click sign in. Complete the authenticator step (e.g. fingerprint or Windows Hello).

![WebAuthn2](/img/webauthn/login_webauthn.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/mcp/authorization.md
================================================================================

---
title: MCP authorization and scopes
description: Scope-based access control for MCP tools.
keywords: [MCP, OAuth, scopes, authorization, permissions]
authors: [hsluoyz]
---

The MCP server enforces fine-grained authorization through OAuth scopes. When you authenticate with an access token, the tools you can access depend on the scopes included in that token. This allows you to create tokens with limited permissions for specific automation tasks, following the principle of least privilege.

Session-based authentication (using cookies) bypasses scope checking and grants full access to all tools. This maintains backward compatibility with existing integrations while encouraging the adoption of scope-based authorization for better security.

## Scope-Based Tool Access

Each MCP tool requires a specific OAuth scope. For application management tools, the mapping is straightforward:

- `read:application` grants access to `get_applications` and `get_application`
- `write:application` grants access to `add_application`, `update_application`, and `delete_application`

When you request a token from Casdoor, include the scopes you need in your authorization request. The MCP server filters available tools based on these granted scopes, ensuring that automated processes can only perform actions they're explicitly authorized for.

If you call `tools/list` with a scoped token, the response only includes tools your token can access. Unauthenticated requests still receive the full tool list to enable discovery, but any attempt to actually call a tool without proper authentication will fail.

## Scope Validation Errors

When you try to use a tool without the required scope, the server responds with an `insufficient_scope` error:

```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "error": {
    "code": -32001,
    "message": "insufficient_scope",
    "data": {
      "tool": "add_application",
      "granted_scopes": ["read:application"],
      "required_scope": "write:application"
    }
  }
}
```

This error tells you exactly which scope you need to request a new token with the appropriate permissions. The `granted_scopes` field shows what your current token has, and `required_scope` indicates what's needed for the operation.

## Creating Scoped Tokens

When obtaining an OAuth token for MCP access, specify the scopes in your authorization request. For example, to get a token that can only read applications but not modify them:

```bash
curl -X POST https://your-casdoor.com/api/login/oauth/access_token \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "scope=read:application"
```

For automation that needs to create and update applications, request the write scope:

```bash
curl -X POST https://your-casdoor.com/api/login/oauth/access_token \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "scope=write:application"
```

You can request multiple scopes by separating them with spaces: `scope=read:application write:application` (or `scope=read:application%20write:application` when URL-encoded). The token will then have access to all tools covered by those scopes.

Some operations have additional requirements beyond scope authorization. Creating applications checks against your organization's application quota. IP whitelist validation runs for applications with restricted access. Demo mode applies additional constraints to prevent modifications to the demonstration instance.

## Complete Scope Reference

Casdoor's built-in MCP server supports scopes across multiple resource types. Each scope follows the `resource:action` pattern, where `resource` identifies the entity type and `action` specifies the operation level.

### Application Scopes

| Scope | Mapped Tools | Description |
|-------|-------------|-------------|
| `read:application` | `get_applications`, `get_application` | View application configurations and settings |
| `write:application` | `add_application`, `update_application`, `delete_application` | Create, modify, and delete applications |

### User Scopes

| Scope | Mapped Tools | Description |
|-------|-------------|-------------|
| `read:user` | `get_users`, `get_user` | View user profiles and information |
| `write:user` | `add_user`, `update_user`, `delete_user` | Create, modify, and delete user accounts |

### Organization Scopes

| Scope | Mapped Tools | Description |
|-------|-------------|-------------|
| `read:organization` | `get_organizations`, `get_organization` | View organization details and settings |
| `write:organization` | `add_organization`, `update_organization`, `delete_organization` | Create, modify, and delete organizations |

### Role Scopes

| Scope | Mapped Tools | Description |
|-------|-------------|-------------|
| `read:role` | `get_roles`, `get_role` | View role definitions and assignments |
| `write:role` | `add_role`, `update_role`, `delete_role` | Create, modify, and delete roles |

### Permission Scopes

| Scope | Mapped Tools | Description |
|-------|-------------|-------------|
| `read:permission` | `get_permissions`, `get_permission` | View permission configurations |
| `write:permission` | `add_permission`, `update_permission`, `delete_permission` | Create, modify, and delete permissions |

### Provider Scopes

| Scope | Mapped Tools | Description |
|-------|-------------|-------------|
| `read:provider` | `get_providers`, `get_provider` | View OAuth, SMS, email, and other provider configurations |
| `write:provider` | `add_provider`, `update_provider`, `delete_provider` | Create, modify, and delete provider integrations |

### Token Scopes

| Scope | Mapped Tools | Description |
|-------|-------------|-------------|
| `read:token` | `get_tokens`, `get_token` | View access tokens and their metadata |
| `write:token` | `refresh_token`, `revoke_token` | Refresh and revoke access tokens |

## Custom Scopes for Third-Party MCP Servers

When building your own MCP server with Casdoor as the OAuth provider, you can define custom scopes to match your server's capabilities. This allows fine-grained authorization beyond the built-in Casdoor scopes.

To configure custom scopes:

1. Set your application's **Category** to "Agent" in the Casdoor admin panel
2. Add custom scopes in the application configuration with Name, Display Name, and Description
3. Your MCP server validates these scopes from the access token's `scope` claim
4. The scopes appear in the OIDC discovery endpoint and consent screen

See [Custom scopes](/docs/application/scopes) for configuration.

**Example custom scopes for a file management MCP server:**

| Name | Display Name | Description |
|------|--------------|-------------|
| `files:read` | Read Files | View and download files from storage |
| `files:write` | Write Files | Create, modify, and delete files |
| `metadata:read` | Read Metadata | View file metadata and properties |

## Consent Screen Configuration

When users authorize an MCP client, Casdoor displays a consent screen showing the requested scopes. The consent screen uses the **Display Name** and **Description** fields you configure for each scope.

To control when the consent screen appears:

1. Navigate to your application configuration in Casdoor
2. Set the **Consent Policy** field:
   - **Always**: Show consent screen on every authorization request
   - **Once**: Show consent screen only on first authorization
   - **Never**: Skip consent screen (not recommended for third-party clients)

The consent screen lists all requested scopes with their display names and descriptions, allowing users to understand what permissions they're granting before approving the request.

## Fine-Grained Authorization with Casbin

For authorization requirements beyond simple scopes, Casdoor integrates with Casbin to provide fine-grained access control. Casbin policies can enforce complex rules based on:

- User attributes (organization, role, department)
- Resource properties (owner, sensitivity level)
- Environmental factors (time, location, IP address)
- Relationships (user is owner, user is team member)

To use Casbin with your MCP server:

1. Define a Casbin model in Casdoor that describes your authorization rules
2. Create a permission resource linking your application to the Casbin model
3. Configure policies that map users, roles, and scopes to specific actions
4. Your MCP server enforces these policies by checking permissions after validating scopes

Casbin authorization runs in addition to scope validation. A request must pass both scope checking and Casbin policy enforcement to succeed. See [Permissions](/docs/permission/overview) for Casbin integration.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/mcp/authentication.md
================================================================================

---
title: MCP authentication
description: OAuth discovery and authentication methods for the MCP server.
keywords: [MCP, authentication, OAuth, access token]
authors: [hsluoyz]
---

## OAuth discovery

Casdoor supports [RFC 9728](https://datatracker.ietf.org/doc/html/rfc9728) OAuth 2.0 Protected Resource Metadata so MCP clients can discover auth requirements. Query the well-known endpoint:

```bash
curl https://your-casdoor.com/.well-known/oauth-protected-resource
```

The response indicates which OAuth authorization server protects the MCP resource:

```json
{
  "resource": "https://your-casdoor.com",
  "authorization_servers": ["https://your-casdoor.com"],
  "bearer_methods_supported": ["header"],
  "scopes_supported": ["openid", "profile", "email"]
}
```

For application-specific discovery, append the application name:

```bash
curl https://your-casdoor.com/.well-known/my-app/oauth-protected-resource
```

This returns metadata scoped to that specific application, useful when different applications have different authorization requirements.

## Authentication Methods

MCP requests must use one of the auth methods in [Public API authentication](/docs/basic/public-api). The authentication method you choose affects which tools you can access.

**Using an access token with scopes** (recommended for automation):

```bash
curl -X POST https://your-casdoor.com/api/mcp \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

Access tokens enforce scope-based authorization. The tools you can use depend on the scopes granted when the token was issued. This approach lets you create tokens with limited permissions for specific tasks.

**Using client credentials** (for service accounts):

```bash
curl -X POST https://your-casdoor.com/api/mcp \
  -u "CLIENT_ID:CLIENT_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

**Using session authentication** (for interactive use):

Session-based authentication through browser cookies grants access to all tools without scope restrictions. This method is intended for interactive use and maintains compatibility with existing workflows.

## Handling Unauthenticated Requests

Unauthenticated requests receive a JSON-RPC error response with a `WWW-Authenticate` header pointing to the OAuth protected resource metadata:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32001,
    "message": "Unauthorized",
    "data": "Unauthorized operation"
  }
}
```

The response includes a `WWW-Authenticate: Bearer realm="/.well-known/oauth-protected-resource"` header, allowing compliant OAuth clients to automatically discover the authorization server configuration.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/sms/alibabaCloud.md
================================================================================

---
title: Alibaba Cloud SMS
description: Use Alibaba Cloud as an SMS provider for verification codes.
keywords: [Alibaba Cloud, SMS, provider]
authors: [UsherFall]
---

Create a **SMS** provider in Casdoor and set **Type** to **Alibaba Cloud**. Map fields as follows:

| Casdoor field   | Alibaba Cloud   | Required |
|-----------------|-----------------|----------|
| Client ID       | AccessKey ID    | Yes      |
| Client secret   | AccessKey Secret| Yes      |
| Sign Name       | Signature       | Yes      |
| Template code   | Template code   | Yes      |

## Get credentials in Alibaba Cloud

- **AccessKey ID / AccessKey Secret** — In the [Alibaba Cloud console](https://ram.console.aliyun.com/manage/ak), create or copy an AccessKey.

![Alibaba Cloud workbench](/img/providers/sms/aliyunsms.png)
![AccessKey](/img/providers/sms/accesskey.png)

- **Signature** — Configure in the SMS service console.

![Alibaba Signature](/img/providers/sms/alibabaSign.png)

- **Template code** — Create or select an SMS template and use its code.

![Alibaba Template Code](/img/providers/sms/alibabaCode.png)

## Configure and test in Casdoor

Fill in the provider fields and use **SMS Test** with a phone number to verify.

![Alibaba Provider Configuration](/img/providers/sms/alibabaProvider.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/application/scopes.md
================================================================================

---
title: Custom scopes
description: Define custom OAuth scopes for Agent applications (e.g. MCP servers).
keywords: [scopes, OAuth, OIDC, agent, MCP, permissions]
authors: [hsluoyz]
---

**Custom scopes** let Agent applications define permissions or capabilities exposed via OAuth. They are added to the app’s OIDC discovery and used alongside standard OIDC scopes.

## When to use custom scopes

Available for applications with category **Agent**. Useful for:

- MCP servers that need to define granular permissions for different resources
- API services that want to control access to specific endpoints or features
- Applications implementing fine-grained authorization models

Default (non-Agent) applications use only standard OIDC scopes and do not need custom scopes.

## Configuring scopes

On the application edit page, add scopes. Each has:

- **Name** — Scope identifier in OAuth (e.g. `files:read`, `messages:write`).
- **Display name** — Shown to the user during consent (e.g. “Read files”).
- **Description** — What the scope allows (e.g. “Allow reading your files”).

## How scopes work

When you configure custom scopes for an Agent application:

1. The scopes are stored with the application configuration
2. They're merged with standard OIDC scopes in the discovery endpoint
3. Client applications can request these scopes during OAuth flows
4. The scopes appear in the OIDC discovery document at `/.well-known/openid-configuration`

Standard OIDC scopes are always available regardless of your custom scopes configuration. Your custom scopes extend rather than replace the defaults.

## Example

Here's a practical example for an MCP server that manages files and databases:

| Name | Display Name | Description |
|------|--------------|-------------|
| `files:read` | Read Files | View and download files from your storage |
| `files:write` | Write Files | Create, modify, and delete files in your storage |
| `db:query` | Query Database | Execute read-only database queries |
| `db:modify` | Modify Database | Create, update, and delete database records |

When clients connect to this MCP server, they can request specific scopes based on what operations they need to perform, following the principle of least privilege.

## Adding Scopes

From the application edit page:

1. Ensure your application Category is set to "Agent"
2. Scroll to the Scopes section
3. Click "Add" to create a new scope
4. Fill in the Name, Display Name, and Description
5. Use the up/down arrows to reorder scopes
6. Click the delete button to remove unwanted scopes
7. Save your application

The scopes are immediately available after saving and will appear in your OIDC discovery endpoint.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/user/multi-factor-authentication.md
================================================================================

---
title: MFA / 2FA
description: Secure your account with MFA / 2FA
keywords: [MFA, 2FA, Authentication, Security, SMS, TOTP, Email, RADIUS]
authors: [leo220yuyaodog]
---

## About multi-factor authentication

MFA (Multi-Factor Authentication) is a security measure that can enhance the security of users and systems. It requires users to provide two or more factors of authentication to verify their identity when logging in or performing sensitive operations.

Casdoor supports multiple second-factor authentication methods including SMS codes, email codes, TOTP authenticator apps, and RADIUS authentication.

Once you enable MFA, Casdoor requires an authentication code every time someone attempts to sign in to your account. The only way someone can sign in to your account is if they know both your password and have access to the authentication code.

## Configuring MFA

1. On the user profile page, open the multi-factor authentication section. If it is missing, ensure the organization has added the MFA item in the account items table.

   ![mfa_config](/img/user/mfa/mfa_config.png)

2. Click the "setup" button.

   ![mfa_setup](/img/user/mfa/mfa_setup.png)

3. Type your password and click "Next Step".

   ![mfa_check_password](/img/user/mfa/mfa_check_password.png)

### Configuring multi-factor authentication using a TOTP mobile app

A time-based one-time password (TOTP) application automatically generates an authentication code that changes after a certain period of time. We recommend using:

- [Google Authenticator](https://play.google.com/store/apps/details?id=com.google.android.apps.authenticator2&hl=en_US&gl=US)
- [Microsoft Authenticator](https://play.google.com/store/apps/details?id=com.azure.authenticator&hl=en_US&gl=US).

:::tip

To configure authentication via TOTP on multiple devices, during setup, scan the QR code using each device at the same time. If 2FA is already enabled, and you want to add another device, you must reconfigure your TOTP app from the user profile page.

:::

![totp](/img/user/mfa/mfa_totp.png)

When you add your account to an authenticator app, the account name will show the organization's display name (or organization name if no display name is set). This helps you identify which organization the TOTP code belongs to when managing multiple accounts.

1. In the "Verify Code" step, do one of the following:

   - Scan the QR code with your mobile device's app. After scanning, the app displays a six-digit code that you can enter on Casdoor.
   - If the QR code cannot be scanned, copy the secret and enter it manually in the TOTP app.

2. The TOTP mobile application saves your account on Casdoor and generates a new authentication code every few seconds. On Casdoor, type the code into the "Passcode" field and click "Next Step".

3. Above the "Enable" button, copy your recovery codes and save them to your device. Save them to a secure location because your recovery codes can help you regain access to your account if you lose access.

   ![mfa_enable](/img/user/mfa/mfa_enable.png)

:::caution

Each recovery code can only be used once. If you use a recovery code to sign in, it will become invalid.

:::

### Configuring multi-factor authentication using text messages

If you have added your mobile phone number, Casdoor will use it to send you a text message.

![mfa_bound](/img/user/mfa/mfa_bound.png)

If you have not added your mobile phone number, add it in your account first.

![mfa_binding](/img/user/mfa/mfa_binding.png)

1. Select your country code and enter your mobile phone number.

2. Check if your information is correct and click "Send Code".

3. Enter the security code from the text message in **Enter your code** and click **Next Step**.

4. Above the "Enable" button, copy your recovery codes and save them to your device. Save them to a secure location because your recovery codes can help you regain access to your account if you lose access.

### Configuring multi-factor authentication using email

Configuring email as your multi-factor authentication method is similar to using text messages.

1. Use your current email or enter your email address and click "Send Code".

2. Then enter the code into the "Enter your code" field and click "Next Step".

3. Above the "Enable" button, copy your recovery codes and save them to your device. Save them to a secure location because your recovery codes can help you regain access to your account if you lose access.

### Configuring multi-factor authentication using RADIUS

RADIUS MFA allows you to authenticate against an external RADIUS server for the second authentication factor. This is useful when integrating with existing authentication infrastructure.

Before using RADIUS MFA, your administrator must configure a RADIUS provider in the application. Once configured:

1. Enter your RADIUS username when prompted during setup.

2. Enter your RADIUS password to verify the setup. This password will be verified against the configured RADIUS server. During subsequent logins, you'll enter this same RADIUS password as your second factor.

3. Above the "Enable" button, copy your recovery codes and save them to your device. Save them to a secure location because your recovery codes can help you regain access to your account if you lose access.

:::note

The RADIUS authentication communicates with the external RADIUS server configured by your administrator. Make sure you have the correct username and password for your RADIUS account.

:::

## Changing your preferred MFA method

Multiple MFA methods can be added; only the preferred one is used at sign-in.

If you want to set a preferred MFA method, click the "Set preferred" button.

![preferred_mfa_method](/img/user/mfa/mfa_preferred_method.png)

A "Preferred" label will be displayed on your preferred method.

## Disabling multi-factor authentication

If you want to disable multi-factor authentication, click the "Disable" button. All your multi-factor authentication settings will be deleted.

![disable_mfa](/img/user/mfa/mfa_disable.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/basic/core-concepts.md
================================================================================

---
title: Core concepts
description: Organizations, users, applications, and providers—the main building blocks of Casdoor.
keywords: [core concepts, organization, user, application, provider]
authors: [hsluoyz]
---

Casdoor is built around four core concepts: **Organization**, **User**, **Application**, and **Provider**. Understanding these will help you configure and operate Casdoor effectively.

```mermaid
flowchart LR;
    subgraph Organization-1;
        Applications-1;
        Users-1;
    end;
    
    subgraph Organization-2;
        Applications-2;
        Users-2;
    end;
    
    subgraph Users-1;
        Resources-1;
        Permissions-1;
    end;
    
    subgraph Users-2;
        Resources-2;
        Permissions-2;
    end;
    
    subgraph Providers;
        SMS;
        OAuth;
        SAML;
        Email;
    end;
    
    subgraph SMS;
        Twilio\nAmazon-SNS\n...;
    end;
    
    subgraph OAuth;
        Google\nGithub\nFacebook\nAzureAD\nCustomOAuth\n...;
    end;
    
    subgraph SAML;
        CustomSAML\nKeycloak\n...;
    end;
    
    subgraph Email;
        Default\nSendGrid\nAzureACS\n...;
    end;
    
    subgraph Applications-1;
        Forum;
        CMS;
    end;
    
    subgraph Applications-2;
        OA;
    end;
    
    Organization-1 --> Applications-1;
    Applications-1<-->Providers;
    Applications-2<-->Providers;
```

:::tip
Examples in this section use the demo site `https://door.casdoor.com`.
:::

## Organization

An **organization** is a container for users and applications—for example, a company’s employees or a product’s customers. The `Organization` struct in code looks like this:

```go
type Organization struct {
    Owner       string `xorm:"varchar(100) notnull pk" json:"owner"`
    Name        string `xorm:"varchar(100) notnull pk" json:"name"`
    CreatedTime string `xorm:"varchar(100)" json:"createdTime"`

    DisplayName        string   `xorm:"varchar(100)" json:"displayName"`
    WebsiteUrl         string   `xorm:"varchar(100)" json:"websiteUrl"`
    Favicon            string   `xorm:"varchar(100)" json:"favicon"`
    PasswordType       string   `xorm:"varchar(100)" json:"passwordType"`
    PasswordSalt       string   `xorm:"varchar(100)" json:"passwordSalt"`
    PhonePrefix        string   `xorm:"varchar(10)"  json:"phonePrefix"`
    DefaultAvatar      string   `xorm:"varchar(100)" json:"defaultAvatar"`
    Tags               []string `xorm:"mediumtext" json:"tags"`
    MasterPassword     string   `xorm:"varchar(100)" json:"masterPassword"`
    EnableSoftDeletion bool     `json:"enableSoftDeletion"`
    IsProfilePublic    bool     `json:"isProfilePublic"`

    AccountItems []*AccountItem `xorm:"varchar(2000)" json:"accountItems"`
}
```

## User

A **user** can sign in to applications. Each user belongs to exactly one organization but can sign in to any application in that organization. Casdoor has two user types:

- **Built-in users** (e.g. `built-in/admin`): Global administrators with full control over the Casdoor instance.
- **Organization users** (e.g. `my-company/alice`): Regular users who can sign up, sign in, sign out, and manage their own profile.

In the API, a user is identified as `<organization_name>/<username>`. The default admin is `built-in/admin`. The `User` struct also has an `id` field (a UUID such as `d835a48f-2e88-4c1f-b907-60ac6b6c1b40`) that applications can use as a stable user ID.

:::tip
For single-organization applications, use `<username>` instead of `<organization_name>/<username>` as the user ID to keep things simple.
:::

The `User` struct:

```go
type User struct {
    Owner       string `xorm:"varchar(100) notnull pk" json:"owner"`
    Name        string `xorm:"varchar(100) notnull pk" json:"name"`
    CreatedTime string `xorm:"varchar(100)" json:"createdTime"`
    UpdatedTime string `xorm:"varchar(100)" json:"updatedTime"`

    Id                string   `xorm:"varchar(100)" json:"id"`
    Type              string   `xorm:"varchar(100)" json:"type"`
    Password          string   `xorm:"varchar(100)" json:"password"`
    PasswordSalt      string   `xorm:"varchar(100)" json:"passwordSalt"`
    DisplayName       string   `xorm:"varchar(100)" json:"displayName"`
    Avatar            string   `xorm:"varchar(500)" json:"avatar"`
    PermanentAvatar   string   `xorm:"varchar(500)" json:"permanentAvatar"`
    Email             string   `xorm:"varchar(100) index" json:"email"`
    Phone             string   `xorm:"varchar(100) index" json:"phone"`
    Location          string   `xorm:"varchar(100)" json:"location"`
    Address           []string `json:"address"`
    Affiliation       string   `xorm:"varchar(100)" json:"affiliation"`
    Title             string   `xorm:"varchar(100)" json:"title"`
    IdCardType        string   `xorm:"varchar(100)" json:"idCardType"`
    IdCard            string   `xorm:"varchar(100) index" json:"idCard"`
    Homepage          string   `xorm:"varchar(100)" json:"homepage"`
    Bio               string   `xorm:"varchar(100)" json:"bio"`
    Tag               string   `xorm:"varchar(100)" json:"tag"`
    Region            string   `xorm:"varchar(100)" json:"region"`
    Language          string   `xorm:"varchar(100)" json:"language"`
    Gender            string   `xorm:"varchar(100)" json:"gender"`
    Birthday          string   `xorm:"varchar(100)" json:"birthday"`
    Education         string   `xorm:"varchar(100)" json:"education"`
    Score             int      `json:"score"`
    Ranking           int      `json:"ranking"`
    IsDefaultAvatar   bool     `json:"isDefaultAvatar"`
    IsOnline          bool     `json:"isOnline"`
    IsAdmin           bool     `json:"isAdmin"`
    IsGlobalAdmin     bool     `json:"isGlobalAdmin"`
    IsForbidden       bool     `json:"isForbidden"`
    IsDeleted         bool     `json:"isDeleted"`
    SignupApplication string   `xorm:"varchar(100)" json:"signupApplication"`
    Hash              string   `xorm:"varchar(100)" json:"hash"`
    PreHash           string   `xorm:"varchar(100)" json:"preHash"`

    CreatedIp      string `xorm:"varchar(100)" json:"createdIp"`
    LastSigninTime string `xorm:"varchar(100)" json:"lastSigninTime"`
    LastSigninIp   string `xorm:"varchar(100)" json:"lastSigninIp"`

    Github   string `xorm:"varchar(100)" json:"github"`
    Google   string `xorm:"varchar(100)" json:"google"`
    QQ       string `xorm:"qq varchar(100)" json:"qq"`
    WeChat   string `xorm:"wechat varchar(100)" json:"wechat"`
    Facebook string `xorm:"facebook varchar(100)" json:"facebook"`
    DingTalk string `xorm:"dingtalk varchar(100)" json:"dingtalk"`
    Weibo    string `xorm:"weibo varchar(100)" json:"weibo"`
    Gitee    string `xorm:"gitee varchar(100)" json:"gitee"`
    LinkedIn string `xorm:"linkedin varchar(100)" json:"linkedin"`
    Wecom    string `xorm:"wecom varchar(100)" json:"wecom"`
    Lark     string `xorm:"lark varchar(100)" json:"lark"`
    Gitlab   string `xorm:"gitlab varchar(100)" json:"gitlab"`
    Apple    string `xorm:"apple varchar(100)" json:"apple"`
    AzureAD  string `xorm:"azuread varchar(100)" json:"azuread"`
    Slack    string `xorm:"slack varchar(100)" json:"slack"`

    Ldap       string            `xorm:"ldap varchar(100)" json:"ldap"`
    Properties map[string]string `json:"properties"`
}
```

:::tip
The `Properties` field is a key-value map for custom user attributes. See [User overview](/docs/user/overview#using-the-properties-field) for usage and best practices.
:::

## Application

An **application** is a web service that uses Casdoor for authentication—for example, a forum, an internal OA system, or a CRM.

```go
type Application struct {
    Owner               string          `xorm:"varchar(100) notnull pk" json:"owner"`
    Name                string          `xorm:"varchar(100) notnull pk" json:"name"`
    CreatedTime         string          `xorm:"varchar(100)" json:"createdTime"`
    DisplayName         string          `xorm:"varchar(100)" json:"displayName"`
    Logo                string          `xorm:"varchar(100)" json:"logo"`
    HomepageUrl         string          `xorm:"varchar(100)" json:"homepageUrl"`
    Description         string          `xorm:"varchar(100)" json:"description"`
    Organization        string          `xorm:"varchar(100)" json:"organization"`
    Cert                string          `xorm:"varchar(100)" json:"cert"`
    EnablePassword      bool            `json:"enablePassword"`
    EnableSignUp        bool            `json:"enableSignUp"`
    EnableSigninSession bool            `json:"enableSigninSession"`
    EnableCodeSignin    bool            `json:"enableCodeSignin"`
    Providers           []*ProviderItem `xorm:"mediumtext" json:"providers"`
    SignupItems         []*SignupItem   `xorm:"varchar(1000)" json:"signupItems"`
    OrganizationObj     *Organization   `xorm:"-" json:"organizationObj"`
    ClientId             string         `xorm:"varchar(100)" json:"clientId"`
    ClientSecret         string         `xorm:"varchar(100)" json:"clientSecret"`
    RedirectUris         []string       `xorm:"varchar(1000)" json:"redirectUris"`
    TokenFormat          string         `xorm:"varchar(100)" json:"tokenFormat"`
    ExpireInHours        int            `json:"expireInHours"`
    RefreshExpireInHours int            `json:"refreshExpireInHours"`
    SignupUrl            string         `xorm:"varchar(200)" json:"signupUrl"`
    SigninUrl            string         `xorm:"varchar(200)" json:"signinUrl"`
    ForgetUrl            string         `xorm:"varchar(200)" json:"forgetUrl"`
    AffiliationUrl       string         `xorm:"varchar(100)" json:"affiliationUrl"`
    TermsOfUse           string         `xorm:"varchar(100)" json:"termsOfUse"`
    SignupHtml           string         `xorm:"mediumtext" json:"signupHtml"`
    SigninHtml           string         `xorm:"mediumtext" json:"signinHtml"`
}
```

Each application can have its own sign-up and sign-in pages. The root path `/login` (e.g. `https://door.casdoor.com/login`) is the sign-in page for Casdoor’s built-in application, `app-built-in`.

An application is the entry point through which users sign in to Casdoor; users always sign in via an application’s sign-in page.

| Application   | Sign-up page URL                           | Sign-in page URL                                                                                                                                                                      |
|---------------|--------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| app-built-in  | `https://door.casdoor.com/signup`           | `https://door.casdoor.com/login`                                                                                                                                                         |
| app-casnode   | `https://door.casdoor.com/signup/app-casnode`| `https://door.casdoor.com/login/oauth/authorize?client_id=014ae4bd048734ca2dea&response_type=code&redirect_uri=http://localhost:9000/callback&scope=read&state=casdoor` |
| app-casbin-oa | `https://door.casdoor.com/signup/app-casbin-oa` | `https://door.casdoor.com/login/oauth/authorize?client_id=0ba528121ea87b3eb54d&response_type=code&redirect_uri=http://localhost:9000/callback&scope=read&state=casdoor`  |

### Login URLs

Signing in via the built-in application is straightforward: open the Casdoor server URL (e.g. `https://door.casdoor.com`) and you are redirected to `/login`. For other applications, build sign-in and sign-up URLs in two ways:

#### 1. Build URLs manually

- **Sign-up**
  - By application: `<casdoor-host>/signup/<application-name>`
  - By OAuth: `<casdoor-host>/signup/oauth/authorize?client_id=<client-id>&response_type=code&redirect_uri=<redirect-uri>&scope=read&state=casdoor`
  - Auto sign-up: `<casdoor-host>/auto-signup/oauth/authorize?client_id=<client-id>&response_type=code&redirect_uri=<redirect-uri>&scope=read&state=casdoor`
- **Sign-in**
  - By organization: `<casdoor-host>/login/<organization-name>`
  - By OAuth: `<casdoor-host>/login/oauth/authorize?client_id=<client-id>&response_type=code&redirect_uri=<redirect-uri>&scope=read&state=casdoor`

#### 2. Frontend SDK (React, Vue, Angular)

Use `getSignupUrl()` and `getSigninUrl()` from [casdoor-js-sdk](https://github.com/casdoor/casdoor-js-sdk/blob/3d08d726bcd5f62d6444b820596e2d8472f67d97/src/sdk.ts#L50-L63).

#### 3. Backend SDK (Go, Java, etc.)

Use `GetSignupUrl()` and `GetSigninUrl()` from [casdoor-go-sdk](https://github.com/casdoor/casdoor-go-sdk/blob/f3ef1adff792e9a06af5682e0a3af9436ed24ed3/auth/url.go#L23-L39).

## Provider

Casdoor acts as a federated SSO platform: it supports multiple identity providers (OIDC, OAuth, SAML) and can send verification codes and notifications via email or SMS. All such integrations are represented as **providers**.

See **[Providers overview](/docs/provider/overview)** for the full list of supported provider types.

```go
type Provider struct {
    Owner       string `xorm:"varchar(100) notnull pk" json:"owner"`
    Name        string `xorm:"varchar(100) notnull pk" json:"name"`
    CreatedTime string `xorm:"varchar(100)" json:"createdTime"`

    DisplayName   string `xorm:"varchar(100)" json:"displayName"`
    Category      string `xorm:"varchar(100)" json:"category"`
    Type          string `xorm:"varchar(100)" json:"type"`
    Method        string `xorm:"varchar(100)" json:"method"`
    ClientId      string `xorm:"varchar(100)" json:"clientId"`
    ClientSecret  string `xorm:"varchar(100)" json:"clientSecret"`
    ClientId2     string `xorm:"varchar(100)" json:"clientId2"`
    ClientSecret2 string `xorm:"varchar(100)" json:"clientSecret2"`

    Host    string `xorm:"varchar(100)" json:"host"`
    Port    int    `json:"port"`
    Title   string `xorm:"varchar(100)" json:"title"`
    Content string `xorm:"varchar(1000)" json:"content"`

    RegionId     string `xorm:"varchar(100)" json:"regionId"`
    SignName     string `xorm:"varchar(100)" json:"signName"`
    TemplateCode string `xorm:"varchar(100)" json:"templateCode"`
    AppId        string `xorm:"varchar(100)" json:"appId"`

    Endpoint         string `xorm:"varchar(1000)" json:"endpoint"`
    IntranetEndpoint string `xorm:"varchar(100)" json:"intranetEndpoint"`
    Domain           string `xorm:"varchar(100)" json:"domain"`
    Bucket           string `xorm:"varchar(100)" json:"bucket"`

    Metadata               string `xorm:"mediumtext" json:"metadata"`
    IdP                    string `xorm:"mediumtext" json:"idP"`
    IssuerUrl              string `xorm:"varchar(100)" json:"issuerUrl"`
    EnableSignAuthnRequest bool   `json:"enableSignAuthnRequest"`

    ProviderUrl string `xorm:"varchar(200)" json:"providerUrl"`
}
```

## How Casdoor manages itself

On first run, Casdoor creates default objects:

- **Organization:** `built-in`
- **User:** `admin` in `built-in`
- **Application:** `app-built-in` (the Casdoor UI), owned by `built-in`

All users in the `built-in` organization (including `admin`) have full admin rights. For multiple admins, create additional accounts under `built-in`, or disable sign-up for `app-built-in` to avoid unwanted accounts.

:::caution
The built-in organization, `admin` user, and `app-built-in` application **cannot be renamed or deleted** via the UI or API. Their names are hardcoded; changing or removing them in the database can break the system.
:::



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/basic/public-api.md
================================================================================

---
title: Public API
description: Authenticate and call the Casdoor REST API from your apps and scripts.
keywords: [API, REST, authentication, OAuth, M2M]
authors: [hsluoyz]
---

The Casdoor web UI is a React [SPA](https://developer.mozilla.org/en-US/docs/Glossary/SPA) that talks to the same REST API as your code. That API is the **Casdoor Public API**: anything the UI does can be done via HTTP. It is used by:

- The Casdoor frontend
- Casdoor SDKs (e.g. casdoor-go-sdk)
- Your own applications and scripts

**API reference:** [https://door.casdoor.com/swagger](https://door.casdoor.com/swagger). To regenerate the Swagger spec, see [Developer guide – Swagger](/docs/developer-guide/swagger#generate-swagger-files).

## Response language

Responses can be localized. Send the `Accept-Language` header to get error messages and other text in that language:

```bash
# Example: Get error messages in French
curl -X GET https://door.casdoor.com/api/get-account \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept-Language: fr"
```

Supported codes include `en`, `zh`, `es`, `fr`, `de`, `ja`, `ko`, and others. See [Internationalization](/docs/internationalization) for the full list.

## Machine-to-machine (M2M) authentication

M2M authentication is for services or scripts that call the API **without a user present**. Use it for:

- Backend services calling Casdoor programmatically
- CLI tools using access tokens
- B2B: per-organization apps with their own client credentials
- Scheduled jobs, sync, and system integrations
- Service-to-service auth

Casdoor supports M2M via:

1. **Client Credentials Grant (OAuth 2.0)** — Recommended. Use [Client ID and Client Secret](/docs/how-to-connect/oauth#client-credentials-grant) to obtain an access token.
2. **Client ID + Client Secret on each request** — Pass credentials directly (see method #2 below).

### Typical M2M use cases

- **Per-organization API access:** One application per organization; client credentials give that org’s admin-level access.
- **Tokens for downstream services:** Use Client Credentials to get tokens for CLIs or other services.
- **Service-to-service:** Backend calls the API as the application (org-admin equivalent).

## How to authenticate

### 1. Access token (user context)

Use the access token obtained after a user signs in (e.g. from the OAuth code exchange). API calls run with that user’s permissions.

#### Getting the token

The app receives the token at the end of the OAuth login flow (code + state). Issued tokens are also visible in the Casdoor UI (**Tokens** page, e.g. `https://door.casdoor.com/tokens`).

Example (Go, casdoor-go-sdk):

```go
func (c *ApiController) Signin() {
    code := c.Input().Get("code")
    state := c.Input().Get("state")

    token, err := casdoorsdk.GetOAuthToken(code, state)
    if err != nil {
        c.ResponseError(err.Error())
        return
    }

    claims, err := casdoorsdk.ParseJwtToken(token.AccessToken)
    if err != nil {
        c.ResponseError(err.Error())
        return
    }

    if !claims.IsAdmin {
        claims.Type = "chat-user"
    }

    err = c.addInitialChat(&claims.User)
    if err != nil {
        c.ResponseError(err.Error())
        return
    }

    claims.AccessToken = token.AccessToken
    c.SetSessionClaims(claims)

    c.ResponseOk(claims)
}
```

#### Sending the token

1. **Query parameter:**

    ```shell
    /page?access_token=<The access token>
    ```

    Demo site example: `https://door.casdoor.com/api/get-global-providers?access_token=eyJhbGciOiJSUzI1NiIs`

2. **Bearer header:**

    ```shell
    Authorization: Bearer <The access token>
    ```

### 2. Client ID and Client Secret (M2M)

Use this for **machine-to-machine** calls (no user). Permissions are those of the application (equivalent to the organization admin).

#### Getting credentials

On the application edit page (e.g. `https://door.casdoor.com/applications/casbin/app-vue-python-example`) you’ll see **Client ID** and **Client Secret**.

#### Use cases

- **Service authentication**: Backend services calling Casdoor APIs programmatically
- **Organization management**: In B2B scenarios, create an application per organization to enable them to manage users and generate tokens independently
- **Token generation**: Obtain access tokens via the [OAuth Client Credentials Grant](/docs/how-to-connect/oauth#client-credentials-grant) flow for distribution to CLI tools or other services

#### Sending credentials

1. **Query parameters:** `/page?clientId=<clientId>&clientSecret=<clientSecret>`

2. **HTTP Basic Auth** — Header:

    ```shell
    Authorization: Basic <The Base64 encoding of client ID and client secret joined by a single colon ":">
    ```

Use any standard library for Base64-encoding `clientId:clientSecret`.

#### Getting an access token (Client Credentials flow)

To use a Bearer token instead of sending client ID/secret on every request, use the **Client Credentials Grant**:

1. Make a POST request to `https://<CASDOOR_HOST>/api/login/oauth/access_token` with:

    ```json
    {
        "grant_type": "client_credentials",
        "client_id": "YOUR_CLIENT_ID",
        "client_secret": "YOUR_CLIENT_SECRET"
    }
    ```

2. The response contains an access token:

    ```json
    {
        "access_token": "eyJhb...",
        "token_type": "Bearer",
        "expires_in": 10080,
        "scope": "openid"
    }
    ```

3. Call the API with the `access_token` as a Bearer token (same as method #1).

See [Client Credentials Grant](/docs/how-to-connect/oauth#client-credentials-grant) for full details.

:::info

**For B2B**: Create separate Casdoor applications per customer organization. Each application has its own `client_id` and `client_secret`, which your customers can use to:

- Authenticate as their organization (with admin privileges)
- Generate access tokens for their users or services
- Manage their organization's users and permissions independently
- Integrate your APIs into their systems without UI-based login flows

This approach allows you to delegate organization management to your customers while maintaining security and isolation between different organizations.

:::

### 3. Access key and Access secret (user context)

A user can have an **access key** and **access secret** (set in the account settings by the user or an admin, or via the `update-user` API). Requests using them run as that user.

#### Setup

Create a key pair on the user’s account settings page.

#### Sending them

**Query parameters:**

    ```shell
    /page?accessKey=<The user's access key>&accessSecret=<the user's access secret>"
    ```

Example: `https://door.casdoor.com/api/get-global-providers?accessKey=...&accessSecret=...`

![User Api Key](/img/basic/user_api_key.png)

```bash
curl --location 'http://door.casdoor.com/api/user?accessKey=b86db9dc-6bd7-4997-935c-af480dd2c796&accessSecret=79911517-fc36-4093-b115-65a9741f6b14'
```

### 4. Username and password

:::caution
**Not recommended.** Credentials are sent as query parameters and may be logged or visible on the network. Use only for compatibility or local demos. Prefer access token, client credentials, or access key/secret.
:::

Username format: `<organization>/<username>`. API calls run as that user.

**Query parameters:**

    ```shell
    /page?username=<The user's organization name>/<The user name>&password=<the user's password>"
    ```

## SSO logout

The `/api/sso-logout` endpoint logs a user out from all applications or only the current session, depending on `logoutAll`.

### Endpoint

```http
GET or POST /api/sso-logout?logoutAll=<true|false>
```

### Parameters

- **logoutAll** (optional): `true`, `1`, or omit → logout from all sessions and expire all tokens. `false` or `0` → current session only.

### Behavior

**Full SSO logout** (default):

- Deletes all active sessions for the user across all applications
- Expires all access tokens issued to the user
- Sends logout notifications with all session IDs and token hashes

**Session-only logout**:

- Deletes only the current session
- Preserves other active sessions and tokens
- Sends logout notification with only the current session ID

Use session-only logout when users should sign out from one device but stay signed in elsewhere.

### Authentication

The user must be authenticated. Use any of the [authentication methods](#how-to-authenticate) above.

### Example Request

```bash
# Full SSO logout (all sessions)
curl -X POST https://door.casdoor.com/api/sso-logout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Session-level logout (current session only)
curl -X POST "https://door.casdoor.com/api/sso-logout?logoutAll=false" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Using session cookie
curl -X POST https://door.casdoor.com/api/sso-logout \
  --cookie "casdoor_session_id=abc123def456"
```

### Response

```json
{
  "status": "ok",
  "msg": "",
  "data": ""
}
```

## CORS

Casdoor sets CORS headers so browsers can call the API from your frontend. Allowed origins include:

- Your application’s **Redirect URIs**
- The Casdoor server hostname
- Configured origin in Casdoor settings
- Special cases: `/api/login/oauth/access_token`, `/api/userinfo`, and origin `appleid.apple.com`

The server checks the request `Origin` against these; if it matches, it adds the appropriate `Access-Control-Allow-*` headers. For `OPTIONS` preflight, allowed methods include `GET`, `POST`, `OPTIONS`, `DELETE`, with credentials supported.

**To allow your app:** Add your frontend origin to the application’s **Redirect URIs** in the Casdoor admin.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/basic/server-installation.mdx
================================================================================

---
title: Server installation
description: Install and configure the Casdoor server from source or pre-built binaries.
keywords: [Casdoor server, installation, configuration]
authors: [hsluoyz]
---

## Requirements

### Operating system

Windows, Linux, and macOS are supported.

### Build environment

- [Go 1.21+](https://go.dev/dl/)
- [Node.js LTS (20)](https://nodejs.org)
- [Yarn 1.x](https://classic.yarnpkg.com/en/docs/install)

:::info
Use **Yarn 1.x** for the frontend; NPM can cause UI styling issues ([casdoor#294](https://github.com/casdoor/casdoor/issues/294)).
:::

:::caution
If Go dependencies fail to download, set **GOPROXY** (e.g. `https://goproxy.cn/`).
:::

### Database

Casdoor uses [XORM](https://xorm.io/) and supports these databases ([Xorm drivers](https://xorm.io/docs/chapter-01/readme/)):

- `MySQL`
- `MariaDB`
- `PostgreSQL`
- `CockroachDB`
- `SQL Server`
- `Oracle`
- `SQLite 3`
- `TiDB`

## Download

### Pre-built binaries

[GitHub Releases](https://github.com/casdoor/casdoor/releases) provide binaries for Linux (x86_64, arm64), macOS (x86_64, arm64), and Windows (x86_64, arm64). Extract the archive and run the `casdoor` binary. It includes the web frontend and a sample `conf/app.conf`; set the database connection before first run (see [Configure database](#configure-database)).

:::tip Quick start with binaries

```bash
# Linux/macOS example
tar -xzf casdoor_Linux_x86_64.tar.gz
cd casdoor_Linux_x86_64
# Edit conf/app.conf with your database settings
./casdoor
```

:::

### Build from source

Repository: `https://github.com/casdoor/casdoor` (backend and frontend in one repo).

| Part      | Description        | Stack                 |
|-----------|--------------------|------------------------|
| Frontend  | Web UI             | JavaScript + React    |
| Backend   | REST API           | Go + Beego + XORM     |

Clone the repo (Go Modules are used):

```shell
cd path/to/folder
git clone https://github.com/casdoor/casdoor
```

## Configuration

### Configure database

Casdoor supports MySQL, MariaDB, PostgreSQL, CockroachDB, SQL Server, Oracle, SQLite3, and TiDB. Default config uses MySQL.

#### MySQL

Create a database named `casdoor` if it does not exist. Set the connection in `conf/app.conf` (see [app.conf](https://github.com/casdoor/casdoor/blob/master/conf/app.conf)):

```ini
driverName = mysql
dataSourceName = root:123456@tcp(localhost:3306)/
dbName = casdoor
```

#### PostgreSQL

Create a database (e.g. `casdoor`) before running; xorm requires it in the connection string. Example `app.conf`:

```ini
driverName = postgres
dataSourceName = user=postgres password=postgres host=localhost port=5432 sslmode=disable dbname=casdoor
dbName = casdoor
```

:::info
For PostgreSQL, ensure that `dataSourceName` has a non-empty `dbName` and also [duplicate](https://github.com/casdoor/casdoor/issues/2127) the database name for the `dbname` field as shown in the example above.
:::

#### CockroachDB

CockroachDB can also be used with the PostgreSQL driver and has the same configuration as PostgreSQL.

```ini
driverName = postgres
dataSourceName = user=postgres password=postgres host=localhost port=5432 sslmode=disable dbname=casdoor serial_normalization=virtual_sequence
dbName = casdoor
```

:::info
For CockroachDB, remember to add `serial_normalization=virtual_sequence` to the `dataSourceName` as shown in the example above. Otherwise, you will get an error regarding an existing database whenever the service starts or restarts. Note that this must be added before the database is created.
:::

#### SQLite3

To configure SQLite3, you should specify `app.conf` like this:

```ini
driverName = sqlite
dataSourceName = file:casdoor.db?cache=shared
dbName = casdoor
```

### Config files

Backend and frontend options are documented in [Configuration](/docs/basic/configuration). For a minimal setup, set `driverName` and `dataSourceName` in [conf/app.conf](https://github.com/casdoor/casdoor/blob/master/conf/app.conf) (see [Configure database](#configure-database)).

## Run

### Development mode

#### Backend

Start the Go backend (default port 8000):

```bash
go run main.go
```

Then start the frontend.

#### Frontend <span id="frontend-1"></span>

The frontend is a [Create React App](https://create-react-app.dev/) project and runs on port 7001 by default:

```bash
cd web
yarn install
yarn start
```

Open [http://localhost:7001](http://localhost:7001) and sign in as **built-in/admin** / **123**.

### Production mode <span id="production-mode"></span>

#### Backend

Build and run the binary:

For Linux:

```bash
go build
./casdoor
```

For Windows:

```bash
go build
casdoor.exe
```

#### Frontend

Build static assets:

```bash
cd web
yarn install
yarn build
```

Open [http://localhost:8000](http://localhost:8000) and sign in as **built-in/admin** / **123**.

:::tip
To use a different port, set `httpport` in `conf/app.conf` and restart the backend.
:::

:::info Ports and URLs
- **Dev:** Frontend runs on port 7001 (`yarn start`). Point apps at **http://localhost:7001** for the Casdoor login page.
- **Prod:** Frontend is built and served by the backend on port 8000. Use **https://your-casdoor-domain** (or your reverse proxy URL).
:::

**Example:** [Casnode](https://casnode.org) uses Casdoor. In dev, set `serverUrl` to `http://localhost:7001`; in prod, set it to `https://door.casdoor.com`.

![Casnode Example](/img/basic/server-installation/casnodeexample.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/basic/try-with-helm.md
================================================================================

---
title: Try with Helm
description: Deploy Casdoor on Kubernetes using Helm for manageable, scalable deployments.
keywords: [Casdoor, Helm, Kubernetes, K8s]
authors: [nomeguy]
---

This page describes how to deploy Casdoor on Kubernetes using Helm.

## Prerequisites

- A running Kubernetes cluster
- Helm v3

## Installation

### Step 1: Install the Casdoor chart

Install the Casdoor [Helm chart](https://hub.docker.com/r/casbin/casdoor-helm-charts/tags):

```shell
helm install casdoor oci://registry-1.docker.io/casbin/casdoor-helm-charts --version v1.702.0
```

### Step 2: Access Casdoor

After installation, use the service URL provided by your cluster to access Casdoor.

### Customization

Override [values.yaml](https://github.com/casdoor/casdoor-helm/blob/master/charts/casdoor/values.yaml) to customize the deployment. Key parameters:

| Parameter                                    | Description                                                                                 | Default Value                                                                                      |
|----------------------------------------------|---------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| `replicaCount`                               | Number of replicas of the Casdoor application to run.                                       | `1`                                                                                                |
| `image.repository`                           | Repository for the Casdoor Docker image.                                                    | `casbin`                                                                                           |
| `image.name`                                 | Name of the Casdoor Docker image.                                                           | `casdoor`                                                                                          |
| `image.pullPolicy`                           | Pull policy for the Casdoor Docker image.                                                   | `IfNotPresent`                                                                                     |
| `image.tag`                                  | Tag for the Casdoor Docker image.                                                           | `""`                                                                                               |
| `config`                                     | Configuration settings for the Casdoor application.                                         | See [config](https://github.com/casdoor/casdoor-helm/blob/master/charts/casdoor/values.yaml) field |
| `database.driver`                            | Database driver to use (supports mysql, postgres, cockroachdb, sqlite3).                    | `sqlite3`                                                                                          |
| `database.user`                              | Database username.                                                                          | `""`                                                                                               |
| `database.password`                          | Database password.                                                                          | `""`                                                                                               |
| `database.host`                              | Database host.                                                                              | `""`                                                                                               |
| `database.port`                              | Database port.                                                                              | `""`                                                                                               |
| `database.databaseName`                      | Name of the database used by Casdoor.                                                       | `casdoor`                                                                                          |
| `database.sslMode`                           | SSL mode for the database connection.                                                       | `disable`                                                                                          |
| `service.type`                               | Type of Kubernetes service to create for Casdoor (ClusterIP, NodePort, LoadBalancer, etc.). | `ClusterIP`                                                                                        |
| `service.port`                               | Port number for the Casdoor service.                                                        | `8000`                                                                                             |
| `ingress.enabled`                            | Whether to enable Ingress for Casdoor.                                                      | `false`                                                                                            |
| `ingress.annotations`                        | Annotations for the Ingress resource.                                                       | `\{\}`                                                                                             |
| `ingress.hosts`                              | Hostnames for the Ingress resource.                                                         | `[]`                                                                                               |
| `resources`                                  | Resource requests and limits for the Casdoor container.                                     | `\{\}`                                                                                             |
| `autoscaling.enabled`                        | Whether to enable Horizontal Pod Autoscaler for Casdoor.                                    | `false`                                                                                            |
| `autoscaling.minReplicas`                    | Minimum number of replicas for Horizontal Pod Autoscaler.                                   | `1`                                                                                                |
| `autoscaling.maxReplicas`                    | Maximum number of replicas for Horizontal Pod Autoscaler.                                   | `100`                                                                                              |
| `autoscaling.targetCPUUtilizationPercentage` | Target CPU utilization percentage for Horizontal Pod Autoscaler.                            | `80`                                                                                               |
| `nodeSelector`                               | Node labels for pod assignment.                                                             | `\{\}`                                                                                             |
| `tolerations`                                | Toleration labels for pod assignment.                                                       | `[]`                                                                                               |
| `affinity`                                   | Affinity settings for pod assignment.                                                       | `\{\}`                                                                                             |
| `extraContainersEnabled`                     | Whether to enable additional sidecar containers.                                            | `false`                                                                                            |
| `extraContainers`                            | Additional sidecar containers.                                                              | `""`                                                                                               |
| `extraVolumeMounts`                          | Additional volume mounts for the Casdoor container.                                         | `[]`                                                                                               |
| `extraVolumes`                               | Additional volumes for the Casdoor container.                                               | `[]`                                                                                               |
| `envFromSecret`                              | Provide Environment variable from secret.                                                   | `[\{name:"",secretName:"",key:""\}]`                                                               |
| `envFromConfigmap`                           | Provide Environment variable from configmap.                                                | `[\{name:"",configmapName:"",key:""\}]`                                                            |
| `envFrom`                                    | Provide Environment variable from entire secret or configmap.                               | `[\{name:"",type:"configmap \| secret"\}]`                                                        |

### Managing the deployment

Upgrade:

```shell
helm upgrade casdoor oci://registry-1.docker.io/casbin/casdoor-helm-charts --version <version>
```

Uninstall:

```shell
helm uninstall casdoor
```

For more options, see the [Helm](https://helm.sh/docs/) and [Kubernetes](https://kubernetes.io/docs/) documentation.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/basic/tutorials.md
================================================================================

---
title: Tutorials
description: Third-party product docs and articles that use Casdoor for SSO or auth.
keywords: [tutorial, integration, SSO, OAuth]
authors: [nomeguy]
---

## Product documentation

| Product | Stack | Documentation |
|--------|--------|----------------|
| [Dashboard](https://github.com/pingcap/tidb-dashboard) of [PingCAP TiDB](https://www.pingcap.com/tidb/) | React + TypeScript + Go + Gin   | [Use Casdoor for TiDB Dashboard SSO sign-in](https://docs.pingcap.com/tidb/stable/dashboard-session-sso#example-3-use-casdoor-for-tidb-dashboard-sso-sign-in) (other languages: [Chinese](https://docs.pingcap.com/zh/tidb/stable/dashboard-session-sso#%E7%A4%BA%E4%BE%8B%E4%B8%89%E4%BD%BF%E7%94%A8-casdoor-%E8%BF%9B%E8%A1%8C-tidb-dashboard-sso-%E7%99%BB%E5%BD%95%E8%AE%A4%E8%AF%81)) |
| [GitLab](https://about.gitlab.com/)                                                                     | Vue + Ruby + Rails              | [OpenID Connect OmniAuth provider](https://docs.gitlab.com/ee/administration/auth/oidc.html#casdoor)                                                                                                                                                                                                                                                                                                                                                                                                                       |
| [Apache Shenyu](https://shenyu.apache.org/)                                                             | Java                            | [Casdoor Plugin](https://shenyu.apache.org/docs/next/plugin-center/security/casdoor/) (other languages: [Chinese](https://shenyu.apache.org/zh/docs/next/plugin-center/security/casdoor/))                                                                                                                                                                                                                                                                                                                                 |
| [Alist](https://alist-doc.nn.ci/)                                                                       | TypeScript + SolidJS + Go + Gin | [Casdoor SSO](https://alist-doc.nn.ci/en/docs/setting/casdoor/) (other languages: [Chinese](https://alist-doc.nn.ci/docs/setting/casdoor/))                                                                                                                                                                                                                                                                                                                                                                                |
| [BookStack](https://www.bookstack.cn/)                                                                  | jQuery + Bootstrap + Go + Beego | [Casdoor integrates registration and login](https://www.bookstack.cn/read/help/Casdoor.md)                                                                                                                                                                                                                                                                                                                                                                                                                                 |

## Articles

| Technologies                                                      | Language | Title                                                                                                                                                                                                                                                                         |
|-------------------------------------------------------------------|----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ASP.NET Core 6                                                    | English  | [ASP.NET Core .NET 6 Demo Authentication Project using local Casdoor Docker Container on Windows Subsystem for Linux](https://blog.kenaro.com/2022/02/18/asp-net-core-net-6-demo-authentication-project-using-local-casdoor-docker-container-on-windows-subsystem-for-linux/) |
| [OAuth2 Proxy (Go)](https://github.com/oauth2-proxy/oauth2-proxy) | Chinese  | [Use Casdoor + OAuth-Proxy to protect web applications on public networks](https://studygolang.com/topics/15475)                                                                                                                                                              |
| [Casnode (JavaScript + React + Go + Beego)](https://casnode.org/) | Chinese  | [Use Lighthouse to set up a forum like V2ex](https://www.jianshu.com/p/e08ef8501a4d)                                                                                                                                                                                          |
| [Cloudreve (Go)](https://github.com/cloudreve/Cloudreve)          | Chinese  | [Modify Cloudreve to support Casdoor](https://www.epis2048.net/2022/modify-cloudreve-to-support-casdoor/index.html)                                                                                                                                                           |
| [KodExplorer (PHP)](https://github.com/kalcaddle/KodExplorer)     | Chinese  | [Modify KodExplorer to support Casdoor](https://www.epis2048.net/2022/modify-kodexplorer-to-support-casdoor/index.html)                                                                                                                                                       |



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/basic/try-with-docker.md
================================================================================

---
title: Try with Docker
description: Run Casdoor using Docker or Docker Compose for quick testing or production.
keywords: [Casdoor, Docker, docker-compose]
authors: [hsluoyz]
---

## Requirements

### Hardware

- **Building the image:** At least **2 GB** RAM. The frontend is a React (npm) project and the build can fail with less memory.
- **Running the pre-built image:** At least **100 MB** RAM.

### OS

Linux, Windows, and macOS are supported.

### Docker

- **Docker:** Use [Docker](https://docs.docker.com/get-docker/) (engine **≥ 17.05** on Linux) or **Docker Desktop** on Windows/macOS. Version 17.05+ is required for multi-stage builds used in the project (see [Docker multi-stage build](https://docs.docker.com/develop/develop-images/multistage-build/)).
- **Docker Compose:** If you use Compose, install **docker-compose v2.2+**. On Linux, Compose is installed separately from the Docker engine.

## Choosing an image

Two images are available on Docker Hub:

| Image | Contents | Use case |
|-------|----------|----------|
| [casdoor-all-in-one](https://hub.docker.com/r/casbin/casdoor-all-in-one) | Casdoor + embedded MySQL | Quick try-out only; **not for production** |
| [casdoor](https://hub.docker.com/r/casbin/casdoor) | Casdoor only | Connect to your own database; suitable for production |

**casdoor-all-in-one** includes the Casdoor binary, a MySQL database, and default config so Casdoor can be run with one or two commands. Use it only for testing.

### Option 1: All-in-one (toy database)

Expose port `8000` and run the all-in-one image. It will be pulled automatically if missing.

```shell
docker run -p 8000:8000 casbin/casdoor-all-in-one
```

Open [**http://localhost:8000**](http://localhost:8000) and sign in with the default admin: **built-in/admin** / **123**.

### Option 2: Standard image with your config

:::tip
Pass configuration via environment variables instead of mounting a config file.

```bash title="example"

docker run \
  -e driverName=mysql \
  -e dataSourceName='user:password@tcp(x.x.x.x:3306)/' \
  -p 8000:8000 \
  casbin/casdoor:latest

```

:::

Create `conf/app.conf` (copy from [conf/app.conf](https://github.com/casdoor/casdoor/blob/master/conf/app.conf)); see [Config files](/docs/basic/server-installation#config-files) for options. Then run:

```bash
docker run -p 8000:8000 -v /folder/of/app.conf:/conf casbin/casdoor:latest
```

:::note
Casdoor runs as uid/gid 1000. When using volume mounts (e.g. for SQLite or other file-based storage), ensure the mounted path is writable by uid 1000 to avoid `permission denied` errors.
:::

In short: **mount your `app.conf` at `/conf/app.conf`** and start the container. Then open [**http://localhost:8000**](http://localhost:8000) and sign in as **built-in/admin** / **123**.

### Option 3: Docker Compose

Place `app.conf` in a `conf/` directory next to `docker-compose.yml` (copy from [app.conf](https://github.com/casdoor/casdoor/blob/master/conf/app.conf); see [Config files](/docs/basic/server-installation#config-files)). Start Casdoor and the database with:

```bash
docker-compose up
```

Then open [**http://localhost:8000**](http://localhost:8000) and sign in as **built-in/admin** / **123**.

:::note
The `RUNNING_IN_DOCKER` environment variable in `docker-compose.yml` is used because the database service is reachable at `localhost` on the host but not inside the Casdoor container. When `RUNNING_IN_DOCKER` is set, Casdoor uses `host.docker.internal` so it can connect to the database without editing `app.conf`.
:::



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/basic/configuration.md
================================================================================

---
title: Configuration
description: Configure the Casdoor backend and frontend via app.conf and Conf.js.
keywords: [Casdoor, configuration, app.conf, Conf.js, backend, frontend]
authors: [hsluoyz]
---

Casdoor is configured through separate files for the backend and frontend. This page documents all supported options.

## Backend configuration (app.conf)

The backend reads a single config file: [**conf/app.conf**](https://github.com/casdoor/casdoor/blob/master/conf/app.conf). For a minimal setup, set `driverName` and `dataSourceName` for your database (see [Configure database](/docs/basic/server-installation#configure-database)). The table below lists every option.

| Parameter                   | Default Value                                                                        | Description                                                                                                                                          |
|-----------------------------|--------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| `appname`                   | `casdoor`                                                                            | Application name (currently has no practical use)                                                                                                    |
| `httpport`                  | `8000`                                                                               | Port that the backend application listens on                                                                                                         |
| `runmode`                   | `dev`                                                                                | Running mode: `dev` or `prod`                                                                                                                        |
| `copyrequestbody`           | `true`                                                                               | Whether to copy request body for later use                                                                                                           |
| `driverName`                | `mysql`                                                                              | Database driver (e.g., `mysql`, `postgres`, `sqlite`). See [Configure Database](/docs/basic/server-installation#configure-database)                  |
| `dataSourceName`            | `root:123456@tcp(localhost:3306)/`                                                   | Database connection string. See [Configure Database](/docs/basic/server-installation#configure-database)                                             |
| `dbName`                    | `casdoor`                                                                            | Database name used by Casdoor                                                                                                                        |
| `tableNamePrefix`           | (empty)                                                                              | Prefix for table names when using an adapter                                                                                                         |
| `showSql`                   | `false`                                                                              | Show SQL statements in logger when log level is greater than INFO                                                                                    |
| `redisEndpoint`             | (empty)                                                                              | Redis endpoint for session storage (e.g., `localhost:6379`). If empty, sessions are stored locally in `./tmp`. For password: `host:port,db,password` |
| `defaultStorageProvider`    | (empty)                                                                              | Default storage provider name for file uploads (e.g., avatars). See [storage](/docs/provider/storage/overview)                                       |
| `isCloudIntranet`           | `false`                                                                              | Whether provider endpoints use intranet addresses                                                                                                    |
| `authState`                 | `"casdoor"`                                                                          | Authorization application name checked during login                                                                                                  |
| `socks5Proxy`               | `"127.0.0.1:10808"`                                                                  | SOCKS5 proxy address for OAuth providers (Google, GitHub, etc.) that may be blocked                                                                  |
| `verificationCodeTimeout`   | `10`                                                                                 | Verification code expiration time in minutes                                                                                                         |
| `initScore`                 | `0`                                                                                  | Initial score assigned to new users (used by Casnode, not Casdoor)                                                                                   |
| `logPostOnly`               | `true`                                                                               | Whether to log only POST requests                                                                                                                    |
| `isUsernameLowered`         | `false`                                                                              | Whether to convert usernames to lowercase                                                                                                            |
| `origin`                    | (empty)                                                                              | Backend origin URL (e.g., `https://door.casdoor.com`)                                                                                                |
| `originFrontend`            | (empty)                                                                              | Frontend origin URL if different from backend                                                                                                        |
| `staticBaseUrl`             | `"https://cdn.casbin.org"`                                                           | CDN URL for static assets used during database initialization                                                                                        |
| `isDemoMode`                | `false`                                                                              | Enable demo mode restrictions                                                                                                                        |
| `batchSize`                 | `100`                                                                                | Batch size for bulk operations                                                                                                                       |
| `enableErrorMask`           | `false`                                                                              | Whether to mask detailed error messages                                                                                                              |
| `enableGzip`                | `true`                                                                               | Accept and respond with gzip encoding when client supports it                                                                                        |
| `inactiveTimeoutMinutes`    | (empty)                                                                              | Auto-logout timeout in minutes. Empty or ≤0 means no timeout                                                                                         |
| `ldapServerPort`            | `389`                                                                                | Port for LDAP server                                                                                                                                 |
| `ldapsCertId`               | `""`                                                                                 | Certificate ID for LDAPS connections                                                                                                                 |
| `ldapsServerPort`           | `636`                                                                                | Port for LDAPS (LDAP over SSL) server                                                                                                                |
| `radiusServerPort`          | `1812`                                                                               | Port for RADIUS server                                                                                                                               |
| `radiusDefaultOrganization` | `"built-in"`                                                                         | Default organization for RADIUS authentication                                                                                                       |
| `radiusSecret`              | `"secret"`                                                                           | Shared secret for RADIUS authentication                                                                                                              |
| `quota`                     | `{"organization": -1, "user": -1, "application": -1, "provider": -1}`                | Resource quotas (-1 means unlimited)                                                                                                                 |
| `logConfig`                 | `{"adapter":"file", "filename": "logs/casdoor.log", "maxdays":99999, "perm":"0770"}` | Logging configuration (adapter, file path, rotation, permissions)                                                                                    |
| `initDataNewOnly`           | `false`                                                                              | Whether to initialize data only for new installations                                                                                                |
| `initDataFile`              | `"./init_data.json"`                                                                 | Path to data initialization file. See [Data Initialization](/docs/deployment/data-initialization)                                                    |
| `frontendBaseDir`           | `"../cc_0"`                                                                          | Base directory for frontend files (only for development)                                                                                             |

### Environment variables

Every Casdoor option in `app.conf` can be overridden with an environment variable of the same name. Some Beego options (e.g. `httpport`, `appname`) are also supported.

Example: starting Casdoor with config passed via environment variables:

```shell
appname=casbin go run main.go
```

Variables can also be `export`ed in the shell. Variable names must match the `app.conf` key names exactly.

:::note
Environment variables override values in `app.conf`.
:::

## Frontend configuration (Conf.js)

The frontend is configured in [**web/src/Conf.js**](https://github.com/casdoor/casdoor/blob/master/web/src/Conf.js). These options control the Casdoor web UI behavior and appearance.

| Parameter               | Default Value                                                                                     | Description                                                                                                                                 |
|-------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| `DefaultApplication`    | `"app-built-in"`                                                                                  | The default application used for login when none is specified                                                                               |
| `CasvisorUrl`           | `""`                                                                                              | URL for Casvisor integration. Leave empty to disable                                                                                        |
| `ShowGithubCorner`      | `false`                                                                                           | Whether to show a GitHub corner link in the UI                                                                                              |
| `IsDemoMode`            | `false`                                                                                           | Whether to run the frontend in demo mode with restrictions                                                                                  |
| `ForceLanguage`         | `""`                                                                                              | Force a specific language for all users. Leave empty to allow user selection                                                                |
| `DefaultLanguage`       | `"en"`                                                                                            | Default language for the UI when no user preference is set                                                                                  |
| `InitThemeAlgorithm`    | `true`                                                                                            | Whether to enable the theme algorithm for UI styling                                                                                        |
| `ThemeDefault`          | `{themeType: "default", colorPrimary: "#5734d3", borderRadius: 6, isCompact: false}`              | Default theme settings including theme type, primary color, border radius, and compact mode                                                 |
| `CustomFooter`          | `null`                                                                                            | Custom footer content. Set to `null` to use the default footer                                                                              |
| `AiAssistantUrl`        | `"https://ai.casbin.com"`                                                                         | URL for the AI Assistant feature. Set to blank or `null` to hide the AI Assistant button                                                    |
| `MaxItemsForFlatMenu`   | `7`                                                                                               | Maximum number of navbar items before switching from a flat menu to a grouped/dropdown menu                                                 |

### Theme options

The `ThemeDefault` object supports:

| Property        | Type      | Description                                                              |
|-----------------|-----------|--------------------------------------------------------------------------|
| `themeType`     | `string`  | Theme type: `"default"`, `"dark"`, or `"compact"`                        |
| `colorPrimary`  | `string`  | Primary color in hex format (e.g., `"#5734d3"`)                          |
| `borderRadius`  | `number`  | Border radius in pixels for UI elements                                  |
| `isCompact`     | `boolean` | Whether to use compact mode for denser UI                                |

### Applying changes

1. Edit `web/src/Conf.js` in your Casdoor tree.
2. Adjust the values as needed.
3. Rebuild the frontend: run `yarn build` in the `web` directory.

:::tip
In development, restart the dev server (`yarn start` in `web`) for `Conf.js` changes to apply.
:::



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/cli.md
================================================================================

﻿---
title: Casdoor CLI
description: Using Casdoor's official command-line interface for managing users, groups, and permissions
keywords: [CLI, command-line, terminal, bash, shell, user management, groups, permissions, OAuth2]
authors: [hsluoyz]
---

**Casdoor CLI** is the official command-line interface for [Casdoor](https://casdoor.org), providing a powerful and intuitive way to manage your Casdoor identity and access management system directly from the terminal.

GitHub repository: `https://github.com/casdoor/casdoor-cli`

## Features

### OAuth2 Browser-Based Authentication

The CLI uses a secure browser-based OAuth2 flow for authentication, ensuring your credentials are protected through Casdoor's standard authentication mechanism.

### Secure Token Storage

Credentials are safely stored using your system's keyring interface (GNOME Keyring on Linux, Keychain on macOS), ensuring tokens never touch disk in plaintext.

### User Management

Create, update, and delete users with ease directly from the command line.

### Permission Management

Control user permissions through Casdoor's group feature with built-in roles:

- `lector`: Read-only access
- `editor`: Can create users, with limited modification rights
- `administrator`: Full control over user creation, modification, and deletion

### Group Management

Create, modify, and delete user groups to organize users and manage permissions efficiently.

## Installation

### Prerequisites

- Go 1.22.0 or higher
- macOS or Linux operating system
- GNOME Keyring (Linux) or Keychain (macOS) for secure credential storage

:::caution

**Platform Support**: Currently supports macOS and Linux (tested on Debian 12 and macOS Sonoma). Windows support via WSL is not available as the CLI requires GNOME's Secret Service DBus interface (GNOME Keyring) for secure credential storage.

:::

### macOS

```bash
make build TARGET_OS=darwin && make install TARGET_OS=darwin
```

### Linux

```bash
make build TARGET_OS=linux && make install TARGET_OS=linux
```

### Configure Your Shell

After installation, add `casdoor-cli` to your `PATH`:

**For Bash users:**

```bash
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**For Zsh users:**

```bash
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Verify the installation:

```bash
casdoor --help
```

## Configuration

### Casdoor server

You need a Casdoor application for the CLI:

1. **Bootstrap data** — Use the repo’s `init_data.json` and follow [Data initialization](/docs/deployment/data-initialization).
2. **Manual** — Create and configure an application in the Casdoor admin panel.

### CLI Configuration

On first run, the CLI prompts for a `config.yaml` with your Casdoor connection details. Use the repo’s `config.yaml.example` as a template.

**Required configuration fields:**

```yaml
application_name: your-app-name
casdoor_endpoint: https://your-casdoor-instance.com
certificate: |
  -----BEGIN CERTIFICATE-----
  Your certificate content here
  -----END CERTIFICATE-----
client_id: your-client-id
client_secret: your-client-secret
organization_name: your-organization
redirect_uri: http://localhost:9000/callback
```

Your configuration will be securely stored in `~/.casdoor-cli/config.yaml` (base64 encoded) for subsequent use.

## Usage

### Available Commands

```bash
Usage:
  casdoor [command]

Available Commands:
  completion  Generate the autocompletion script for the specified shell
  groups      Manage Casdoor permissions
  help        Help about any command
  login       Login to your Casdoor account
  logout      Logout from your Casdoor account
  users       Manage Casdoor users

Flags:
  -d, --debug   verbose logging
  -h, --help    help for casdoor
```

### Login

To authenticate with your Casdoor instance:

```bash
casdoor login
```

This will open your default browser for OAuth2 authentication.

### Managing Users

```bash
# List users
casdoor users list

# Create a user
casdoor users create

# Update a user
casdoor users update

# Delete a user
casdoor users delete
```

### Managing Groups

```bash
# List groups
casdoor groups list

# Create a group
casdoor groups create

# Update a group
casdoor groups update

# Delete a group
casdoor groups delete
```

### Logout

To logout from your Casdoor account:

```bash
casdoor logout
```

## Development

### Local Development Environment

A Docker Compose environment is provided in the repository for local testing and development:

```bash
docker compose up -d
```

:::note

Allow a few moments for the Casdoor container to fully initialize. The container will restart multiple times as it sets up the database.

:::

### Development Configuration

Create a `config.yaml` file from the provided `config.yaml.example` template at the repository root with your local development settings.

### Testing the CLI

Test the login functionality with the default development credentials provided in the repository documentation.

**Run directly with Go:**

```bash
go run main.go login
```

**Or build and install first:**

```bash
make build TARGET_OS=darwin && make install TARGET_OS=darwin  # For macOS
# OR
make build TARGET_OS=linux && make install TARGET_OS=linux    # For Linux

casdoor login
```



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/chrome-extension.md
================================================================================

---
title: Chrome extension
description: Integrate Casdoor OAuth in a Chrome extension.
keywords: [chrome extension, browser extension, oauth]
authors: [hsluoyz]
---

The [casdoor-chrome-extension](https://github.com/casdoor/casdoor-chrome-extension) repo shows how to integrate Casdoor in a Chrome extension. Summary of steps:

## Step 1: Deploy Casdoor

Deploy Casdoor in [production mode](/docs/basic/server-installation). Confirm the login page at `http://localhost:8000` works (e.g. sign in with `admin` / `123` in dev).

## Step 2: Configure the application

1. In Casdoor, go to **Applications** and create or edit an application.
2. Add **Redirect URLs** for the extension (e.g. `https://<extension-id>.chromiumapp.org/` or `http://localhost:3000/callback` for dev).
3. Note the **Client ID** and **Client Secret** and enable the OAuth options you need.

## Step 3: Set Up Chrome Extension

### 1. Create Manifest File

Create a `manifest.json` file in your Chrome extension project with the necessary permissions:

```json
{
  "manifest_version": 3,
  "name": "Casdoor Chrome Extension",
  "version": "1.0.0",
  "description": "Chrome extension integrated with Casdoor",
  "permissions": [
    "identity",
    "storage"
  ],
  "host_permissions": [
    "http://localhost:8000/*",
    "https://door.casdoor.com/*"
  ],
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "background": {
    "service_worker": "background.js"
  }
}
```

### 2. Configure Extension Identity

In the `manifest.json`, you may need to add OAuth2 configuration if using Chrome's identity API:

```json
{
  "oauth2": {
    "client_id": "your-client-id.apps.googleusercontent.com",
    "scopes": ["openid", "profile", "email"]
  }
}
```

:::caution

Replace the configuration values with your own Casdoor instance, especially the `client_id` and the host permissions URLs.

:::

## Step 4: Implement Authentication Flow

### 1. Create Background Script

Create a `background.js` file to handle the authentication:

```javascript
const CASDOOR_ENDPOINT = "http://localhost:8000";
const CLIENT_ID = "your-client-id";
const CLIENT_SECRET = "your-client-secret";
const ORGANIZATION_NAME = "built-in";
const APPLICATION_NAME = "app-built-in";
const REDIRECT_URI = chrome.identity.getRedirectURL();

// Generate the authorization URL
function getAuthUrl() {
  const state = Math.random().toString(36).substring(7);
  const authUrl = `${CASDOOR_ENDPOINT}/login/oauth/authorize?client_id=${CLIENT_ID}&response_type=code&redirect_uri=${encodeURIComponent(REDIRECT_URI)}&scope=openid%20profile%20email&state=${state}`;
  
  chrome.storage.local.set({ oauthState: state });
  
  return authUrl;
}

// Handle OAuth callback
async function handleOAuthCallback(redirectUrl) {
  const url = new URL(redirectUrl);
  const code = url.searchParams.get('code');
  const state = url.searchParams.get('state');
  
  // Verify state
  const { oauthState } = await chrome.storage.local.get('oauthState');
  if (state !== oauthState) {
    throw new Error('Invalid state parameter');
  }
  
  // Exchange code for token
  const tokenResponse = await fetch(`${CASDOOR_ENDPOINT}/api/login/oauth/access_token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      grant_type: 'authorization_code',
      client_id: CLIENT_ID,
      client_secret: CLIENT_SECRET,
      code: code,
      redirect_uri: REDIRECT_URI,
    }),
  });
  
  const tokenData = await tokenResponse.json();
  return tokenData;
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'login') {
    chrome.identity.launchWebAuthFlow(
      {
        url: getAuthUrl(),
        interactive: true,
      },
      async (redirectUrl) => {
        if (chrome.runtime.lastError || !redirectUrl) {
          sendResponse({ error: chrome.runtime.lastError?.message });
          return;
        }
        
        try {
          const tokenData = await handleOAuthCallback(redirectUrl);
          await chrome.storage.local.set({ user: tokenData });
          sendResponse({ success: true, data: tokenData });
        } catch (error) {
          sendResponse({ error: error.message });
        }
      }
    );
    return true; // Keep the message channel open for async response
  }
  
  if (request.action === 'logout') {
    chrome.storage.local.remove(['user', 'oauthState'], () => {
      sendResponse({ success: true });
    });
    return true;
  }
  
  if (request.action === 'getUser') {
    chrome.storage.local.get('user', (result) => {
      sendResponse({ user: result.user });
    });
    return true;
  }
});
```

### 2. Create Popup HTML

Create a `popup.html` file for the extension popup:

```html
  
  
```

### 3. Create Popup Script

Create a `popup.js` file to handle user interactions:

```javascript
document.addEventListener('DOMContentLoaded', () => {
  const loginSection = document.getElementById('login-section');
  const userSection = document.getElementById('user-section');
  const loginBtn = document.getElementById('login-btn');
  const logoutBtn = document.getElementById('logout-btn');
  const userInfo = document.getElementById('user-info');
  
  // Check if user is already logged in
  chrome.runtime.sendMessage({ action: 'getUser' }, (response) => {
    if (response.user) {
      showUserSection(response.user);
    } else {
      showLoginSection();
    }
  });
  
  loginBtn.addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: 'login' }, (response) => {
      if (response.error) {
        alert('Login failed: ' + response.error);
      } else if (response.success) {
        showUserSection(response.data);
      }
    });
  });
  
  logoutBtn.addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: 'logout' }, (response) => {
      if (response.success) {
        showLoginSection();
      }
    });
  });
  
  function showLoginSection() {
    loginSection.style.display = 'block';
    userSection.style.display = 'none';
  }
  
  function showUserSection(user) {
    loginSection.style.display = 'none';
    userSection.style.display = 'block';
    
    // Parse JWT token to get user info
    if (user.access_token) {
      try {
        const payload = JSON.parse(atob(user.access_token.split('.')[1]));
        userInfo.innerHTML = `


================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/face-id.md
================================================================================

---
title: Face ID
description: Sign in with Face ID using face-api.js.
keywords: [face id, signin, biometric]
authors: [HGZ-20]
---

Casdoor supports **Face ID** sign-in using face-api.js. Users register facial data in their account and can sign in by scanning their face on the login page.

## Enable Face ID

### 1. Add Face ID to account items

**User Management** → **Organizations** → select organization → **Account items** → add **Face ID**.

![Face ID](/img/application/face-id/organization-face-id.png)

### 2. Let users add facial data

**User Management** → **Users** → select user → **Face Ids**. Users can add up to 5 face entries and give each a name.

![Face ID](/img/application/face-id/user-face-id.png)

### 3. Add Face ID to sign-in methods

**Identity** → **Applications** → select application → **Signin methods** → add **Face ID**.

![Face ID](/img/application/face-id/signin-methods-face-id.png)

### 4. Sign in with Face ID

1. On the login page, choose the **Face ID** method.
2. Enter the username and click **Sign in with Face ID**.
3. Allow camera access when prompted, then complete face verification.

![Face ID](/img/application/face-id/face-id-signin.png)
![Face ID](/img/application/face-id/face-recognition.png)

Demo video:



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/nuxt.md
================================================================================

---
title: Nuxt
description: Integrate Casdoor in a Nuxt app with middleware and the JS SDK.
keywords: [nuxt, SDK, middleware]
authors: [xiao-kong-long]
---

The [nuxt-auth](https://github.com/casdoor/nuxt-auth) repo demonstrates Casdoor integration in Nuxt. The flow is similar to the [Next.js](/docs/how-to-connect/nextjs) example.

## Step 1: Deploy Casdoor

Deploy Casdoor in [production mode](/docs/basic/server-installation). Confirm the login page works (e.g. at `http://localhost:8000` with `admin` / `123` in dev).

## Step 2: Add middleware

Create a `.js` or `.ts` file in the `middleware` directory. The filename becomes the middleware name (e.g. `myMiddleware.js` → `myMiddleware`). Reference it in `nuxt.config.js`.

Example:

```js
const protectedRoutes = ["/profile"];

  if (protectedRoutes.includes(route.path)) {
    redirect('/login');
  }
}
```

Enable in `nuxt.config.js`:

```js
  router: {
    middleware: ['myMiddleware']  // your middleware name
  },
}
```

See [Nuxt middleware](https://nuxt.com/docs/guide/directory-structure/middleware).

## Step 3: Use Casdoor SDK

### Install

```shell
npm install casdoor-js-sdk
# or: yarn add casdoor-js-sdk
```

### Initialize

Provide these six string parameters:

| Parameter | Required | Description |
|-----------|----------|-------------|
| **serverUrl** | Yes | Casdoor server URL (e.g. `http://localhost:8000`). |
| **clientId** | Yes | Application client ID. |
| **clientSecret** | Yes | Application client secret. |
| **organizationName** | Yes | Organization name. |
| **appName** | Yes | Application name. |
| **redirectPath** | Yes | Callback path (e.g. `/callback`). |

Example:

```js
const sdkConfig = {
  serverUrl: "https://door.casdoor.com",
  clientId: "294b09fbc17f95daf2fe",
  clientSecret: "dd8982f7046ccba1bbd7851d5c1ece4e52bf039d",
  organizationName: "casbin",
  appName: "app-vue-python-example",
  redirectPath: "/callback",
};
```

:::caution
Replace with your own Casdoor instance: `serverUrl`, `clientId`, and `clientSecret`.
:::

Add the callback URL (e.g. `http://localhost:8080/callback`) in the application’s Redirect URLs.

### Redirect to sign-in and handle callback

```js
const CasdoorSDK = new Sdk(sdkConfig);
CasdoorSDK.signin_redirect();
```

After sign-in, exchange the code for a token and optionally store the user in a cookie:

```js
CasdoorSDK.exchangeForAccessToken()
  .then((res) => {
    if (res && res.access_token) {
      return CasdoorSDK.getUserInfo(res.access_token);
    }
  })
  .then((res) => {
    Cookies.set("casdoorUser", JSON.stringify(res));
  });
```

See [How to use Casdoor SDK](/docs/how-to-connect/sdk).

## Step 4: Protect routes in middleware

Check the Casdoor user cookie and redirect unauthenticated users from protected routes:

```js

const protectedRoutes = ["/profile"];

  const casdoorUserCookie = Cookies.get('casdoorUser');
  const isAuthenticated = !!casdoorUserCookie;

  if (!isAuthenticated && protectedRoutes.includes(route.path)) {
    redirect('/login');
  }
}
```



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/sdk.md
================================================================================

---
title: Casdoor SDKs
description: Use Casdoor SDKs for frontend and backend integration with user management and more.
keywords: [SDK, frontend, backend, OIDC]
authors: [nomeguy]
---

## Overview

Casdoor SDKs extend standard OIDC with user management, resource uploads, and other features. They take a bit more setup than a generic OIDC client but give you the full Casdoor API.

**Frontend SDKs** — For web (JavaScript, React, Vue, etc.) and mobile (Android, iOS, React Native, Flutter).  
**Backend SDKs** — For Go, Java, Node.js, Python, PHP, .NET, Rust, C++, and more.

:::tip
For a frontend/backend split, use a frontend SDK (e.g. `casdoor-js-sdk`, `casdoor-react-sdk`, `casdoor-vue-sdk`) in the UI and a backend SDK for token validation and API calls. For a traditional server-rendered app (JSP, PHP), a backend SDK may be enough. Example: [casdoor-python-vue-sdk-example](https://github.com/casdoor/casdoor-python-vue-sdk-example).
:::

| Mobile SDK       | Description                     | SDK code                                                                        | Example code                                                                            |
|------------------|---------------------------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| Android SDK      | For Android apps                | [casdoor-android-sdk](https://github.com/casdoor/casdoor-android-sdk)           | [casdoor-android-example](https://github.com/casdoor/casdoor-android-example)           |
| iOS SDK          | For iOS apps                    | [casdoor-ios-sdk](https://github.com/casdoor/casdoor-ios-sdk)                   | [casdoor-ios-example](https://github.com/casdoor/casdoor-ios-example)                   |
| React Native SDK | For React Native apps           | [casdoor-react-native-sdk](https://github.com/casdoor/casdoor-react-native-sdk) | [casdoor-react-native-example](https://github.com/casdoor/casdoor-react-native-example) |
| Flutter SDK      | For Flutter apps                | [casdoor-flutter-sdk](https://github.com/casdoor/casdoor-flutter-sdk)           | [casdoor-flutter-example](https://github.com/casdoor/casdoor-flutter-example)           |
| Firebase SDK     | For Google Firebase apps        |                                                                                 | [casdoor-firebase-example](https://github.com/casdoor/casdoor-firebase-example)         |
| Unity Games SDK  | For Unity 2D/3D PC/Mobile games | [casdoor-dotnet-sdk](https://github.com/casdoor/casdoor-dotnet-sdk)             | [casdoor-unity-example](https://github.com/casdoor/casdoor-unity-example)               |
| uni-app SDK      | For uni-app apps                | [casdoor-uniapp-sdk](https://github.com/casdoor/casdoor-uniapp-sdk)             | [casdoor-uniapp-example](https://github.com/casdoor/casdoor-uniapp-example)             |

| Desktop SDK      | Description            | SDK code                                                            | Example code                                                                                                                                                                                                                                                                                                                                               |
|------------------|------------------------|---------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Electron SDK     | For Electron apps      | [casdoor-js-sdk](https://github.com/casdoor/casdoor-js-sdk)         | [casdoor-electron-example](https://github.com/casdoor/casdoor-electron-example)                                                                                                                                                                                                                                                                            |
| .NET Desktop SDK | For .NET desktop apps  | [casdoor-dotnet-sdk](https://github.com/casdoor/casdoor-dotnet-sdk) | WPF: [casdoor-dotnet-desktop-example](https://github.com/casdoor/casdoor-dotnet-desktop-example)<br />WinForms: [casdoor-dotnet-winform-example](https://github.com/casdoor/casdoor-dotnet-winform-example)<br />[Avalonia UI](https://avaloniaui.net/): [casdoor-dotnet-avalonia-example](https://github.com/RVShershnev/casdoor-dotnet-avalonia-example) |
| C/C++ SDK        | For C/C++ desktop apps | [casdoor-cpp-sdk](https://github.com/casdoor/casdoor-cpp-sdk)       | [casdoor-cpp-qt-example](https://github.com/casdoor/casdoor-cpp-qt-example)                                                                                                                                                                                                                                                                                |

| Web frontend SDK  | Description                      | SDK code                                                          | Example code                                                                                                                                                                                                                         |
|-------------------|----------------------------------|-------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Javascript SDK    | For traditional non-SPA websites | [casdoor-js-sdk](https://github.com/casdoor/casdoor-js-sdk)       | Nodejs backend: [casdoor-raw-js-example](https://github.com/casdoor/casdoor-raw-js-example)<br />Go backend: [casdoor-go-react-sdk-example](https://github.com/casdoor/casdoor-go-react-sdk-example)                                 |
| Frontend-only SDK | For frontend-only SPA websites   | [casdoor-js-sdk](https://github.com/casdoor/casdoor-js-sdk)       | [casdoor-react-only-example](https://github.com/casdoor/casdoor-react-only-example)                                                                                                                                                  |
| React SDK         | For React websites               | [casdoor-react-sdk](https://github.com/casdoor/casdoor-react-sdk) | Nodejs backend: [casdoor-nodejs-react-example](https://github.com/casdoor/casdoor-nodejs-react-example)<br />Java backend: [casdoor-spring-security-react-example](https://github.com/casdoor/casdoor-spring-security-react-example) |
| Next.js SDK       | For Next.js websites             |                                                                   | [nextjs-auth](https://github.com/casdoor/nextjs-auth)                                                                                                                                                                                |
| Nuxt SDK          | For Nuxt websites                |                                                                   | [nuxt-auth](https://github.com/casdoor/nuxt-auth)                                                                                                                                                                                    |
| Vue SDK           | For Vue websites                 | [casdoor-vue-sdk](https://github.com/casdoor/casdoor-vue-sdk)                                       | [casdoor-python-vue-sdk-example](https://github.com/casdoor/casdoor-python-vue-sdk-example)                                                                                                                                          |
| Angular SDK       | For Angular websites             | [casdoor-angular-sdk](https://github.com/casdoor/casdoor-angular-sdk)                               | [casdoor-nodejs-angular-example](https://github.com/casdoor/casdoor-nodejs-angular-example)                                                                                                                                          |
| Flutter SDK       | For Flutter Web websites         | [casdoor-flutter-sdk](https://github.com/casdoor/casdoor-flutter-sdk)                               | [casdoor-flutter-example](https://github.com/casdoor/casdoor-flutter-example)                                                                                                                                                        |
| ASP.NET SDK       | For ASP.NET Blazor WASM websites | [Blazor.BFF.OpenIDConnect.Template](https://github.com/damienbod/Blazor.BFF.OpenIDConnect.Template) | [casdoor-dotnet-blazorwasm-oidc-example](https://github.com/RVShershnev/casdoor-dotnet-blazorwasm-oidc-example)                                                                                                                      |
| Firebase SDK      | For Google Firebase apps         |                                                                                                     | [casdoor-firebase-example](https://github.com/casdoor/casdoor-firebase-example)                                                                                                                                                      |

Pair the frontend with a backend SDK in your server’s language:

| Web backend SDK | Description          | Sdk code                                                            | Example code                                                                                                                                                                                                                                                                                                         |
|-----------------|----------------------|---------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Go SDK          | For Go backends      | [casdoor-go-sdk](https://github.com/casdoor/casdoor-go-sdk)         | [casdoor-go-react-sdk-example](https://github.com/casdoor/casdoor-go-react-sdk-example)                                                                                                                                                                                                                              |
| Java SDK        | For Java backends    | [casdoor-java-sdk](https://github.com/casdoor/casdoor-java-sdk)     | [casdoor-spring-boot-starter](https://github.com/casdoor/casdoor-spring-boot-starter), [casdoor-spring-boot-example](https://github.com/casdoor/casdoor-spring-boot-example), [casdoor-spring-security-react-example](https://github.com/casdoor/casdoor-spring-security-react-example)                              |
| Node.js SDK     | For Node.js backends | [casdoor-nodejs-sdk](https://github.com/casdoor/casdoor-nodejs-sdk) | [casdoor-nodejs-react-example](https://github.com/casdoor/casdoor-nodejs-react-example)                                                                                                                                                                                                                              |
| Python SDK      | For Python backends  | [casdoor-python-sdk](https://github.com/casdoor/casdoor-python-sdk) | Flask: [casdoor-python-vue-sdk-example](https://github.com/casdoor/casdoor-python-vue-sdk-example)<br />Django: [casdoor-django-js-sdk-example](https://github.com/casdoor/casdoor-django-vue-sdk-example)<br />FastAPI: [casdoor-fastapi-js-sdk-example](https://github.com/casdoor/casdoor-fastapi-js-sdk-example) |
| PHP SDK         | For PHP backends     | [casdoor-php-sdk](https://github.com/casdoor/casdoor-php-sdk)       | [wordpress-casdoor-plugin](https://github.com/casdoor/wordpress-casdoor-plugin)                                                                                                                                                                                                                                      |
| .NET SDK        | For ASP.NET backends | [casdoor-dotnet-sdk](https://github.com/casdoor/casdoor-dotnet-sdk) | [casdoor-dotnet-sdk-example](https://github.com/casdoor/casdoor-dotnet-sdk-example)                                                                                                                                                                                                                                  |
| Rust SDK        | For Rust backends    | [casdoor-rust-sdk](https://github.com/casdoor/casdoor-rust-sdk)     | [casdoor-rust-example](https://github.com/casdoor/casdoor-rust-example)                                                                                                                                                                                                                                              |
| C/C++ SDK       | For C/C++ backends   | [casdoor-cpp-sdk](https://github.com/casdoor/casdoor-cpp-sdk)       | [casdoor-cpp-qt-example](https://github.com/casdoor/casdoor-cpp-qt-example)                                                                                                                                                                                                                                          |
| Dart SDK        | For Dart backends    | [casdoor-dart-sdk](https://github.com/casdoor/casdoor-dart-sdk)     |                                                                                                                                                                                                                                                                                                                      |
| Ruby SDK        | For Ruby backends    | [casdoor-ruby-sdk](https://github.com/casdoor/casdoor-ruby-sdk)     |                                                                                                                                                                                                                                                                                                                      |

**All official SDKs:** `https://github.com/orgs/casdoor/repositories?q=sdk&type=all&language=&sort=`.

## Using the SDK

### 1. Backend SDK configuration

On startup, call the SDK’s init function with your Casdoor endpoint, client ID, client secret, and (for JWT validation) the public key. Example with **casdoor-go-sdk**: `https://github.com/casbin/casnode/blob/6d4c55f5c9a3c4bd8c85f2493abad3553b9c7ac0/controllers/account.go#L51-L64`

```go
var CasdoorEndpoint = "https://door.casdoor.com"
var ClientId = "541738959670d221d59d"
var ClientSecret = "66863369a64a5863827cf949bab70ed560ba24bf"
var CasdoorOrganization = "casbin"
var CasdoorApplication = "app-casnode"

//go:embed token_jwt_key.pem
var JwtPublicKey string

func init() {
    auth.InitConfig(CasdoorEndpoint, ClientId, ClientSecret, JwtPublicKey, CasdoorOrganization, CasdoorApplication)
}
```

All the parameters for `InitConfig()` are explained as follows:

| Parameter        | Must | Description                                                                    |
|------------------|------|--------------------------------------------------------------------------------|
| endpoint         | Yes  | Casdoor Server URL, like `https://door.casdoor.com` or `http://localhost:8000` |
| clientId         | Yes  | Client ID for the Casdoor application                                          |
| clientSecret     | Yes  | Client secret for the Casdoor application                                      |
| jwtPublicKey     | Yes  | The public key for the Casdoor application's cert                              |
| organizationName | Yes  | The name for the Casdoor organization                                          |
| applicationName  | No   | The name for the Casdoor application                                           |

:::tip

The `jwtPublicKey` can be managed in the `Certs` page as below.

![Certs Management](/img/how-to-connect/sdk/howto_cert_list.png)

Copy or download the public key from the certificate edit page for use in the SDK.

![Certs Edit](/img/how-to-connect/sdk/howto_cert_edit.png)

Then select the cert on the application edit page.

![Certs Select](/img/how-to-connect/sdk/howto_cert_select.png)

:::

### 2. Frontend configuration

First, install `casdoor-js-sdk` via NPM or Yarn:

```shell
npm install casdoor-js-sdk
```

Or:

```shell
yarn add casdoor-js-sdk
```

Then define the following utility functions (better in a global JS file like `Setting.js`):

```js

  CasdoorSdk = new Sdk(config);
}

  return CasdoorSdk.getSignupUrl();
}

  return CasdoorSdk.getSigninUrl();
}

  return CasdoorSdk.getUserProfileUrl(userName, account);
}

  return CasdoorSdk.getMyProfileUrl(account);
}

  return CasdoorSdk.getMyProfileUrl(account).replace("/account?", "/resources?");
}

  return CasdoorSdk.signin(ServerUrl);
}

  if (type === "") {
    return;
  } else if (type === "success") {
    message.success(text);
  } else if (type === "error") {
    message.error(text);
  }
}

  window.location.href = link;
}
```

In your frontend entry file (e.g. `index.js` or `app.js` in React), initialize the `casdoor-js-sdk` by calling `InitConfig()` with the required parameters. The first 4 parameters should use the same value as the Casdoor backend SDK. The last parameter `redirectPath` is relative path for the redirected URL, returned from Casdoor's login page.

```js
const config = {
  serverUrl: "https://door.casdoor.com",
  clientId: "014ae4bd048734ca2dea",
  organizationName: "casbin",
  appName: "app-casnode",
  redirectPath: "/callback",
};

xxx.initCasdoorSdk(config);
```

**(Optional)** This example uses React; the `/callback` route is handled by the component below, which forwards the call to the backend. Skip this if your callback goes directly to the backend (e.g. JSP or PHP).

```js

class AuthCallback extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      classes: props,
      msg: null,
    };
  }

  componentWillMount() {
    this.login();
  }

  login() {
    Setting.signin().then((res) => {
      if (res.status === "ok") {
        Setting.showMessage("success", `Logged in successfully`);
        Setting.goToLink("/");
      } else {
        this.setState({
          msg: res.msg,
        });
      }
    });
  }

  render() {
    return (
        )}
    );
  }
}

```

### 3. Get login URLs

Show "Sign up" and "Sign in" buttons or links to users; URLs can be obtained from the frontend or backend. See [Login URLs](/docs/basic/core-concepts#login-urls).

### 4. Get and verify access token

Here are the steps:

1. The user clicks the login URL and is redirected to Casdoor's login page,
   like: `https://door.casdoor.com/login/oauth/authorize?client_id=014ae4bd048734ca2dea&response_type=code&redirect_uri=https%3A%2F%2Fforum.casbin.com%2Fcallback&scope=read&state=app-casnode`
2. The user enters username & password and clicks `Sign In` (or just click the third-party login button
   like `Sign in with GitHub`).
3. The user is redirected back to your application with the authorization code issued by Casdoor (
   like: `https://forum.casbin.com?code=xxx&state=yyy`), your application's backend needs to exchange the authorization code with the access token and verify that the access token is valid and issued by Casdoor. The functions `GetOAuthToken()` and `ParseJwtToken()` are provided by Casdoor backend SDK.

The following code shows how to get and verify the access token. For a real example of Casnode (a forum website written in Go), see: `https://github.com/casbin/casnode/blob/6d4c55f5c9a3c4bd8c85f2493abad3553b9c7ac0/controllers/account.go#L51-L64`

```go
// get code and state from the GET parameters of the redirected URL
code := c.Input().Get("code")
state := c.Input().Get("state")

// exchange the access token with code and state
token, err := auth.GetOAuthToken(code, state)
if err != nil {
    panic(err)
}

// verify the access token
claims, err := auth.ParseJwtToken(token.AccessToken)
if err != nil {
    panic(err)
}
```

If `ParseJwtToken()` finishes with no error, then the user has successfully logged into the application. The
returned `claims` can be used to identity the user later.

### 4. Identify user with access token

:::info

This part is actually your application's own business logic and not part of OIDC, OAuth or Casdoor. We just provide good practices as a lot of people don't know what to do for the next step.

:::

In Casdoor, access token is usually identical as ID token. They are the same thing. So the access token contains all information for the logged-in user.

The variable `claims` returned by `ParseJwtToken()` is defined as:

```go
type Claims struct {
    User
    AccessToken string `json:"accessToken"`
    jwt.RegisteredClaims
}
```

1. `User`: the User object, containing all information for the logged-in user, see definition
   at: **[/docs/basic/core-concepts#user](/docs/basic/core-concepts#user)**
2. `AccessToken`: the access token string.
3. `jwt.RegisteredClaims`: some other values required by JWT.

At this moment, the application usually has two ways to remember the user session: `session` and `JWT`.

#### Session

The Method to set session varies greatly depending on the language and web framework. E.g., Casnode
uses [Beego web framework](https://github.com/beego/beego/) and set session by calling: `c.SetSessionUser()`.

```go
token, err := auth.GetOAuthToken(code, state)
if err != nil {
    panic(err)
}

claims, err := auth.ParseJwtToken(token.AccessToken)
if err != nil {
    panic(err)
}

claims.AccessToken = token.AccessToken
c.SetSessionUser(claims) // set session
```

#### JWT

The `accessToken` returned by Casdoor is actually a JWT. So if your application uses JWT to keep user session, just use the access token directly for it:

1. Send the access token to frontend, save it in places like localStorage of the browser.
2. Let the browser send the access token to backend for every request.
3. Call `ParseJwtToken()` or your own function to verify the access token and get logged-in user information in your backend.

### 5. **(Optional)** Interact with the User table

:::info

This part is provided by `Casdoor Public API` and not part of the OIDC or OAuth.

:::

Casdoor Backend SDK provides a lot of helper functions, not limited to:

- `GetUser(name string)`: get a user by username.
- `GetUsers()`: get all users.
- `AddUser()`: add a user.
- `UpdateUser()`: update a user.
- `DeleteUser()`: delete a user.
- `CheckUserPassword(auth.User)`: check user's password.

These functions are implemented by making RESTful calls against `Casdoor Public API`. If a function is not in the Casdoor Backend SDK, call the [Public API](/docs/basic/public-api) directly.

### 6. **(Optional)** Manage Applications via SDK

Casdoor SDKs also provide functions to manage applications programmatically:

- `AddApplication()`: create a new application.
- `GetApplication(name string)`: get an application by name.
- `GetApplications()`: get all applications.
- `UpdateApplication()`: update an application.
- `DeleteApplication()`: delete an application.

When creating applications via SDK using `AddApplication()`, Casdoor automatically initializes essential fields with sensible defaults. This includes signup items (ID, Username, Display name, Password, Confirm password, Email, Phone, Agreement), signin items, and signin methods. This ensures applications created programmatically work correctly in the UI without requiring manual configuration of these basic settings.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/vue-sdk.md
================================================================================

---
title: Vue SDK
description: Use Casdoor in Vue 2 or Vue 3 with the official Vue SDK.
keywords: [Vue, SDK]
authors: [Nekotoxin]
---

The **Casdoor Vue SDK** works with Vue 2 and Vue 3 and wraps [casdoor-js-sdk](/docs/how-to-connect/sdk) for easier integration. For more control, use the JS SDK directly.

:::note
This plugin is still in development. Questions or suggestions: [open an issue](https://github.com/casdoor/casdoor-vue-sdk/issues).
:::

Full example (Vue frontend + Python backend): [casdoor-python-vue-sdk-example](https://github.com/casdoor/casdoor-python-vue-sdk-example).

## Installation

```shell
# NPM
npm install casdoor-vue-sdk

# Yarn
yarn add casdoor-vue-sdk
```

## Initialization

Provide these parameters (all strings):

| Parameter | Required | Description |
|-----------|----------|-------------|
| **serverUrl** | Yes | Casdoor server URL. |
| **clientId** | Yes | Application client ID. |
| **appName** | Yes | Application name. |
| **organizationName** | Yes | Organization name. |
| **redirectPath** | No | Callback path; default `/callback`. |

**Vue 3:**

```javascript
// main.js

const config = {
  serverUrl: "http://localhost:8000",
  clientId: "4262bea2b293539fe45e",
  organizationName: "casbin",
  appName: "app-casnode",
  redirectPath: "/callback",
};

const app = createApp(App)
app.use(Casdoor, config)
```

**Vue 2:**

```javascript
// main.js

const config = {
  serverUrl: "http://localhost:8000",
  clientId: "4262bea2b293539fe45e",
  organizationName: "casbin",
  appName: "app-casnode",
  redirectPath: "/callback",
};

Vue.use(VueCompositionAPI)
Vue.use(Casdoor, config)

new Vue({
  render: h => h(App),
}).$mount('#app')
```

## Usage example

```vue
```

## Redirect / Vue version issues

If the `postinstall` hook did not run or you changed the Vue version, fix redirect behavior with:

```shell
npx vue-demi-fix
```

See [vue-demi](https://github.com/vueuse/vue-demi) for switching between Vue 2 and Vue 3.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/oidc-client.md
================================================================================

---
title: Standard OIDC client
description: Connect to Casdoor with any OIDC client using discovery endpoints.
keywords: [OIDC, discovery, client, migration]
authors: [nomeguy]
---

## OIDC discovery

Casdoor is a full OIDC implementation. If your app already uses a standard OIDC client against another IdP, you can switch to Casdoor by pointing the client at Casdoor’s discovery URL.

### Discovery endpoints

Casdoor exposes metadata at both OpenID Connect and OAuth 2.0 discovery URLs. Most clients use these to auto-configure endpoints and capabilities.

#### OpenID Connect discovery

```url


================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/overview.md
================================================================================

---
title: Overview
description: Connect your application to Casdoor using OAuth 2.0, OIDC, SAML, or CAS.
keywords: [OAuth, OAuth 2.0, OIDC, SAML, CAS, integration]
authors: [nomeguy]
---

This section describes how to connect your application to Casdoor.

**When Casdoor acts as a Service Provider (SP)**, it supports:

- OAuth 2.0 (OIDC)
- SAML

**When Casdoor acts as an Identity Provider (IdP)**, it supports:

- OAuth 2.0
- OIDC
- SAML
- CAS 1.0, 2.0, and 3.0

## OAuth 2.0 (OIDC)


Casdoor’s authorization flow is based on OAuth 2.0. We recommend OAuth 2.0 (OIDC) because it is straightforward to implement, covers many use cases, and is widely supported.

Your application can integrate with Casdoor in three main ways:

### Standard OIDC client

**[Standard OIDC client](/docs/how-to-connect/oidc-client)** — Use any standard OIDC client library available for your language or framework.


Casdoor is fully OIDC-compliant. If you already use another OIDC identity provider with a standard client library, switching to Casdoor is typically a configuration change (e.g. discovery URL and credentials).

### Casdoor SDKs

**[Casdoor SDKs](/docs/how-to-connect/sdk)** — Casdoor provides SDKs for many languages, built on OIDC and adding Casdoor-specific features (e.g. user management, file upload).

Using an SDK takes a bit more setup than a generic OIDC client but gives you the most flexibility and the full Casdoor API.

### Casdoor plugin

**[Casdoor plugin](/docs/how-to-connect/plugin)** — If your app runs on a supported platform (e.g. Spring Boot, WordPress), use the official or community plugin or middleware. Plugins are the fastest way to add Casdoor to that platform.

**Plugins:**

- [Jenkins plugin](/docs/integration/java/jenkins-plugin)
- [APISIX plugin](/docs/integration/lua/apisix#connect-casdoor-via-apisixs-casdoor-plugin)

**Middleware:**

- [Spring Boot](https://github.com/casdoor/casdoor-spring-boot-starter)
- [Django](https://github.com/casdoor/django-casdoor-auth)

## SAML


Casdoor can act as a **SAML 2.0 IdP** and supports the main SAML 2.0 features. See **[SAML](/docs/how-to-connect/saml/overview)** for details.

**Example:** [Casdoor as a SAML IdP in Keycloak](/docs/how-to-connect/saml/keycloak#add-the-saml-idp-in-keycloak)

**When to use SAML:** SAML is mature and widely used in enterprise SSO, but the protocol is large and has many optional parts. For new applications, OAuth 2.0 / OIDC is usually simpler; choose SAML when you must interoperate with existing SAML-based systems.

## CAS


Casdoor supports **CAS 1.0, 2.0, and 3.0**. See **[CAS](/docs/how-to-connect/cas)** for setup.

**Note:** CAS is lightweight but limited in scope. Trust between the CAS client and server is established by interface calls rather than cryptographic signatures. For new projects, OAuth 2.0 / OIDC is generally preferred.

## Integrations

For step-by-step examples of connecting specific applications to Casdoor, see the [Integrations](/docs/category/integrations) section.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/cas.md
================================================================================

---
title: Casdoor as a CAS server
description: Use Casdoor as a Central Authentication Service (CAS) server for CAS 1.0, 2.0, and 3.0.
keywords: [CAS, server, SSO]
authors: [ComradeProgrammer]
---

## Overview

Casdoor can act as a **CAS server** and supports CAS 1.0, 2.0, and 3.0.

The CAS URL prefix is: `<casdoor-host>/cas/<organization>/<application>`. Example for `https://door.casdoor.com`, org `casbin`, app `cas-java-app`:

- `/login` endpoint: `https://door.casdoor.com/cas/casbin/cas-java-app/login`
- `/logout` endpoint: `https://door.casdoor.com/cas/casbin/cas-java-app/logout`
- `/serviceValidate` endpoint: `https://door.casdoor.com/cas/casbin/cas-java-app/serviceValidate`
- `/proxyValidate` endpoint: `https://door.casdoor.com/cas/casbin/cas-java-app/proxyValidate`
- `/proxy` endpoint: `https://door.casdoor.com/cas/casbin/cas-java-app/proxy`
- `/validate` endpoint: `https://door.casdoor.com/cas/casbin/cas-java-app/validate`
- `/p3/serviceValidate` endpoint: `https://door.casdoor.com/cas/casbin/cas-java-app/p3/serviceValidate`
- `/p3/proxyValidate` endpoint: `https://door.casdoor.com/cas/casbin/cas-java-app/p3/proxyValidate`
- `/samlValidate` endpoint: `https://door.casdoor.com/cas/casbin/cas-java-app/samlValidate`

See the [CAS protocol specification](https://apereo.github.io/cas/7.1.x/protocol/CAS-Protocol-Specification.html) for parameters and versions.

### Example

The [Apereo CAS sample Java webapp](https://github.com/apereo/cas-sample-java-webapp) and [Java CAS client](https://github.com/apereo/java-cas-client) work with Casdoor. Point the client at your Casdoor CAS base URL.

The CAS configuration is located in `src/main/webapp/WEB-INF/web.yml`.

By default, this app uses CAS 3.0, which is specified by the following configurations:

```xml


================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/plugin.md
================================================================================

---
title: Plugins and middlewares
description: Official Casdoor plugins for Spring Boot, WordPress, Odoo, Django, and Chrome.
keywords: [plugin, middleware, Spring Boot, WordPress, Odoo, Django]
authors: [hsluoyz]
---

Casdoor provides plugins or middlewares for popular platforms. For CLI usage, see [Casdoor CLI](/docs/how-to-connect/cli).

| Plugin | Language | Repository |
|--------|----------|------------|
| Spring Boot | Java | [casdoor-spring-boot-starter](https://github.com/casdoor/casdoor-spring-boot-starter) |
| Spring Boot example | Java | [casdoor-spring-boot-example](https://github.com/casdoor/casdoor-spring-boot-example) |
| WordPress | PHP | [wordpress-casdoor-plugin](https://github.com/casdoor/wordpress-casdoor-plugin) |
| Odoo | Python | [odoo-casdoor-oauth](https://github.com/casdoor/odoo-casdoor-oauth) |
| Django | Python | [django-casdoor-auth](https://github.com/casdoor/django-casdoor-auth) |
| Chrome extension | JavaScript | [casdoor-chrome-extension](https://github.com/casdoor/casdoor-chrome-extension) |

More official integrations: [Casdoor repositories](https://github.com/orgs/casdoor/repositories?q=sdk+in%3Areadme&type=all&language=&sort=).



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/nextjs.md
================================================================================

---
title: Next.js
description: Integrate Casdoor in a Next.js app with middleware and the JS SDK.
keywords: [nextjs, SDK, middleware]
authors: [SamYSF]
---

The [nextjs-auth](https://github.com/casdoor/nextjs-auth) repo demonstrates Casdoor integration in Next.js. Steps below.

## Step 1: Deploy Casdoor

Deploy Casdoor in [production mode](/docs/basic/server-installation). Confirm the login page works (e.g. at `http://localhost:8000` with `admin` / `123` in dev).

## Step 2: Add middleware

Put `middleware.ts` (or `.js`) at the project root (same level as `pages` or `app`, or inside `src`). Middleware runs before the request completes and can redirect or modify the response.

Example:

```js
const protectedRoutes = ["/profile"];

  if (protectedRoutes.includes(req.nextUrl.pathname)) {
    return NextResponse.redirect(new URL("/login", req.url));
  }
}
```

See [Next.js middleware](https://nextjs.org/docs/app/building-your-application/routing/middleware).

## Step 3: Use Casdoor SDK

### Install

```shell
npm install casdoor-js-sdk
# or: yarn add casdoor-js-sdk
```

### Initialize

Provide these six string parameters:

| Parameter | Required | Description |
|-----------|----------|-------------|
| **serverUrl** | Yes | Casdoor server URL (e.g. `http://localhost:8000`). |
| **clientId** | Yes | Application client ID. |
| **clientSecret** | Yes | Application client secret. |
| **organizationName** | Yes | Organization name. |
| **appName** | Yes | Application name. |
| **redirectPath** | Yes | Callback path (e.g. `/callback`). |

Example:

```js
const sdkConfig = {
  serverUrl: "https://door.casdoor.com",
  clientId: "294b09fbc17f95daf2fe",
  clientSecret: "dd8982f7046ccba1bbd7851d5c1ece4e52bf039d",
  organizationName: "casbin",
  appName: "app-vue-python-example",
  redirectPath: "/callback",
};
```

:::caution
Replace with your own Casdoor instance: `serverUrl`, `clientId`, and `clientSecret`.
:::

Add the callback URL (e.g. `http://localhost:8080/callback`) in the application’s Redirect URLs.

### Redirect to sign-in and handle callback

```js
const CasdoorSDK = new Sdk(sdkConfig);
CasdoorSDK.signin_redirect();
```

After sign-in, Casdoor redirects back with a code. Exchange for a token and optionally store the user in a cookie:

```js
CasdoorSDK.exchangeForAccessToken()
  .then((res) => {
    if (res && res.access_token) {
      return CasdoorSDK.getUserInfo(res.access_token);
    }
  })
  .then((res) => {
    Cookies.set("casdoorUser", JSON.stringify(res));
  });
```

See [How to use Casdoor SDK](/docs/how-to-connect/sdk).

## Step 4: Protect routes in middleware

In middleware, treat the presence of the Casdoor user cookie as authenticated and redirect unauthenticated users away from protected routes:

```js
const protectedRoutes = ["/profile"];
const casdoorUserCookie = req.cookies.get("casdoorUser");
const isAuthenticated = !!casdoorUserCookie;

if (!isAuthenticated && protectedRoutes.includes(req.nextUrl.pathname)) {
  return NextResponse.redirect(new URL("/login", req.url));
}
```



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/desktop-sdks/electron-app.md
================================================================================

---
title: Electron app
description: Integrate Casdoor in an Electron app with OAuth and a custom protocol.
keywords: [electron, SDK, Casdoor]
authors: [Resulte]
---

The [casdoor-electron-example](https://github.com/casdoor/casdoor-electron-example) shows Casdoor sign-in in an Electron app (custom protocol + browser OAuth).

## Run the example

### Initialization

Set these 6 string parameters:

| Name                 | Description                                                                                      | Path                   |
| -------------------- | ------------------------------------------------------------------------------------------------ | ---------------------- |
| serverUrl            | Your Casdoor server URL                                                                          | `src/App.js`         |
| clientId             | The Client ID of your Casdoor application                                                        | `src/App.js`         |
| appName              | The name of your Casdoor application                                                             | `src/App.js`         |
| redirectPath         | The path of the redirect URL for your Casdoor application, will be `/callback` if not provided | `src/App.js`         |
| clientSecret         | The Client Secret of your Casdoor application                                                   | `src/App.js`         |
| casdoorServiceDomain | Your Casdoor server URL                                                                          | `public/electron.js` |

Defaults: [Casdoor demo](https://door.casdoor.com/) and [app-casnode](https://door.casdoor.com/applications/app-casnode) if not set.

### Commands

In the project directory:

#### `npm run dev` or `yarn dev`

Builds the electron app and runs this app.

#### `npm run make` or `yarn make`

Packages and distributes your application. It will create the `out` folder where your package will be located:

```bash
// Example for macOS out/  
├── out/make/zip/darwin/x64/casdoor-electron-example-darwin-x64-1.0.0.zip  
├── ...  
└── out/casdoor-electron-example-darwin-x64/casdoor-electron-example.app/Contents/MacOS/casdoor-electron-example
```

### Preview

![Electron Login](/img/how-to-connect/desktop-sdks/electron-app/login.png)

Running the app opens a window. Click **Login with Casdoor** to open the Casdoor login page in your browser.

![Browser View](/img/how-to-connect/desktop-sdks/electron-app/browser.png)

After sign-in, the app opens and shows your username.

![Electron Logout](/img/how-to-connect/desktop-sdks/electron-app/logout.png)
![Electron Preview Gif](/img/how-to-connect/desktop-sdks/electron-app/preview.gif)

## Integration steps

### 1. Set the custom protocol

Register the `casdoor` custom protocol:

```javascript
const protocol = "casdoor";

if (process.defaultApp) {
  if (process.argv.length >= 2) {
    app.setAsDefaultProtocolClient(protocol, process.execPath, [
      path.resolve(process.argv[1]),
    ]);
  }
} else {
  app.setAsDefaultProtocolClient(protocol);
}
```

The browser can then open your app and pass the auth code via the protocol.

### 2. Open the login URL in the browser

```javascript
const serverUrl = "https://door.casdoor.com";
const appName = "app-casnode";
const redirectPath = "/callback";
const clientId = "014ae4bd048734ca2dea";
const clientSecret = "f26a4115725867b7bb7b668c81e1f8f7fae1544d";

const redirectUrl = "casdoor://localhost:3000" + redirectPath;

const signinUrl = `${serverUrl}/login/oauth/authorize?client_id=${clientId}&response_type=code&redirect_uri=${encodeURIComponent(redirectUrl)}&scope=profile&state=${appName}&noRedirect=true`;

shell.openExternal(signinUrl); //Open the login url in the browser
```

Adjust the first five variables for your Casdoor instance.

### 3. Listen for the app being opened

After sign-in in the browser, the browser opens your app via the custom protocol. Listen for that event:

```javascript
const gotTheLock = app.requestSingleInstanceLock();
const ProtocolRegExp = new RegExp(`^${protocol}://`);

if (!gotTheLock) {
  app.quit();
} else {
  app.on("second-instance", (event, commandLine, workingDirectory) => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
      commandLine.forEach((str) => {
        if (ProtocolRegExp.test(str)) {
          const params = url.parse(str, true).query;
          if (params && params.code) {
            store.set("casdoor_code", params.code);
            mainWindow.webContents.send("receiveCode", params.code);
          }
        }
      });
    }
  });
  app.whenReady().then(createWindow);

  app.on("open-url", (event, openUrl) => {
    const isProtocol = ProtocolRegExp.test(openUrl);
    if (isProtocol) {
      const params = url.parse(openUrl, true).query;
      if (params && params.code) {
        store.set("casdoor_code", params.code);
        mainWindow.webContents.send("receiveCode", params.code);
      }
    }
  });
}
```

The auth code is in `casdoor_code` or `params.code`.

### 4. Exchange the code for user info

```javascript
async function getUserInfo(clientId, clientSecret, code) {
  const { data } = await axios({
    method: "post",
    url: authCodeUrl,
    headers: {
      "content-type": "application/json",
    },
    data: JSON.stringify({
      grant_type: "authorization_code",
      client_id: clientId,
      client_secret: clientSecret,
      code: code,
    }),
  });
  const resp = await axios({
    method: "get",
    url: `${getUserInfoUrl}?accessToken=${data.access_token}`,
  });
  return resp.data;
}

ipcMain.handle("getUserInfo", async (event, clientId, clientSecret) => {
  const code = store.get("casdoor_code");
  const userInfo = await getUserInfo(clientId, clientSecret, code);
  store.set("userInfo", userInfo);
  return userInfo;
});
```

See [OAuth](/docs/how-to-connect/oauth) for the full flow.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/desktop-sdks/maui-app.md
================================================================================

---
title: .NET MAUI app
description: Integrate Casdoor in a .NET MAUI app (Android, Windows, etc.) with OpenID Connect.
keywords: [.NET, MAUI, SDK]
authors: [RVShershnev]
---

The [casdoor-dotnet-maui-example](https://github.com/RVShershnev/casdoor-dotnet-maui-example) includes a .NET MAUI app and library for Casdoor authentication via OpenID Connect.

## Demo

### Android

![Android](/img/how-to-connect/desktop-sdks/maui-app/android.gif)

### Windows

![Windows](/img/how-to-connect/desktop-sdks/maui-app/windows.gif)

## Requirements

- [.NET 7 SDK](https://dotnet.microsoft.com/download/dotnet/7.0)
- Target platform assets — see [MAUI first app](https://docs.microsoft.com/en-us/dotnet/maui/get-started/first-app)
- Visual Studio 2022 (Windows 17.3 or Mac 17.4) optional

## Get started

### 1. Create a MAUI app

Create a [MAUI application](https://docs.microsoft.com/en-us/dotnet/maui/get-started/first-app).

### 2. Add reference

Add a reference to `Casdoor.MauiOidcClient`.

### 3. Register the Casdoor client

Add `CasdoorClient` as a singleton in the services.

```csharp
builder.Services.AddSingleton(new CasdoorClient(new()
{
    Domain = "<your domain>",
    ClientId = "<your client>",
    Scope = "openid profile email",

#if WINDOWS
    RedirectUri = "http://localhost/callback"
#else
    RedirectUri = "casdoor://callback"
#endif
}));
```

### 4. UI (MainPage)

**MainPage.xaml**

```xml


```

**MainPage.cs**

```csharp
namespace Casdoor.MauiOidcClient.Example
{
    public partial class MainPage : ContentPage
    {
        int count = 0;
        private readonly CasdoorClient client;
        private string accessToken;
        public MainPage(CasdoorClient client)
        {
            InitializeComponent();
            this.client = client;

#if WINDOWS
    client.Browser = new WebViewBrowserAuthenticator(WebViewInstance);
#endif
        }

        private void OnCounterClicked(object sender, EventArgs e)
        {
            count++;

            if (count == 1)
                CounterBtn.Text = $"Clicked {count} time";
            else
                CounterBtn.Text = $"Clicked {count} times";

            SemanticScreenReader.Announce(CounterBtn.Text);
        }

        private async void OnLoginClicked(object sender, EventArgs e)
        {
            var loginResult = await client.LoginAsync();
            accessToken = loginResult.AccessToken;
            if (!loginResult.IsError)
            {
                NameLabel.Text = loginResult.User.Identity.Name;
                EmailLabel.Text = loginResult.User.Claims.FirstOrDefault(c => c.Type == "email")?.Value;            

                LoginView.IsVisible = false;
                HomeView.IsVisible = true;
            }
            else
            {
                await DisplayAlert("Error", loginResult.ErrorDescription, "OK");
            }
        }

        private async void OnLogoutClicked(object sender, EventArgs e)
        {
            var logoutResult = await client.LogoutAsync(accessToken);


            if (!logoutResult.IsError)
            {
                HomeView.IsVisible = false;
                LoginView.IsVisible = true;
                this.Focus();
            }
            else
            {
                await DisplayAlert("Error", logoutResult.ErrorDescription, "OK");
            }
        }
    }
}
```

### Step 5: Support the Android Platform

Modify the `AndroidManifest.xml` file.

```xml
```

### Step 6: Launch the Application

**Visual Studio:** Press Ctrl + F5 to start.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/desktop-sdks/qt-app.md
================================================================================

---
title: Qt desktop app
description: Integrate Casdoor in a Qt (C++) desktop app with WebEngine.
keywords: [qt, sdk, C++]
authors: [cs1137195420]
---

The [casdoor-cpp-qt-example](https://github.com/casdoor/casdoor-cpp-qt-example) shows Casdoor sign-in in a Qt desktop app.

## Run the example

### Prerequisites

- [Qt 6](https://www.qt.io/download)
- [OpenSSL](https://www.openssl.org/source/)

### Initialization

Set these 7 string parameters:

| Name           | Description                                                                                             | File                  |
| -------------- | ------------------------------------------------------------------------------------------------------- | --------------------- |
| endpoint       | Your Casdoor server host/domain                                                                         | `mainwindow.h` |
| client_id      | The Client ID of your Casdoor application                                                               | `mainwindow.h` |
| client_secret  | The Client Secret of your Casdoor application                                                           | `mainwindow.h` |
| certificate    | The public key for the Casdoor application's cert                                                       | `mainwindow.h` |
| org_name       | The name of your Casdoor organization                                                                    | `mainwindow.h` |
| app_name       | The name of your Casdoor application                                                                    | `mainwindow.h` |
| redirect_url   | The path of the callback URL for your Casdoor application, will be `http://localhost:8080/callback` if not provided | `mainwindow.h` |

Default endpoint: `http://localhost:8000` if not set.

### Running

**Qt Creator**

1. Open `casdoor-cpp-qt-example.pro`
2. Set the `INCLUDEPATH` of OpenSSL in `casdoor-cpp-qt-example.pro`
3. Press `Ctrl + R` to start

### Preview

![index](/img/how-to-connect/desktop-sdks/qt-app/index.png)

Click **Sign In** to open the login window. After sign-in, the user profile is shown.

![login](/img/how-to-connect/desktop-sdks/qt-app/login.png)
![user profile](/img/how-to-connect/desktop-sdks/qt-app/userprofile.png)
![preview gif](/img/how-to-connect/desktop-sdks/qt-app/preview.gif)

## Integration

### Open the login window

```cpp
// Load and display the login page of Casdoor
m_webview->page()->load(*m_signin_url);
m_webview->show();
```

### Listen for the callback (TCP)

```cpp
// Initialize the TcpServer object and listen on port 8080
m_tcpserver = new QTcpServer(this);
if (!m_tcpserver->listen(QHostAddress::LocalHost, 8080)) {
    qDebug() << m_tcpserver->errorString();
    close();
}
connect(m_tcpserver, SIGNAL(newConnection()), this, SLOT(on_tcp_connected()));
```

### Using Auth Code to Get the User Info

```cpp
// Get the token and parse it with the JWT library
std::string token = m_casdoor->GetOAuthToken(code.toStdString());
auto decoded = m_casdoor->ParseJwtToken(token);
```



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/desktop-sdks/dotnet-app.md
================================================================================

---
title: .NET desktop app
description: Integrate Casdoor in a .NET desktop app with WebView2.
keywords: [dotNET, SDK]
authors: [zh6335901]
---

The [casdoor-dotnet-desktop-example](https://github.com/casdoor/casdoor-dotnet-desktop-example) shows Casdoor sign-in in a .NET desktop app using WebView2.

## Run the example

### Prerequisites

- [.NET 6 SDK](https://dotnet.microsoft.com/en-us/download)
- [WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/#download-section) (usually preinstalled on Windows)

### Initialization

Set these 5 string parameters:

| Name         | Description                                                                                             | File                  |
| ------------ | ------------------------------------------------------------------------------------------------------- | --------------------- |
| Domain       | The host/domain of your Casdoor server                                                                  | `CasdoorVariables.cs` |
| ClientId     | The Client ID of your Casdoor application                                                               | `CasdoorVariables.cs` |
| AppName      | The name of your Casdoor application                                                                    | `CasdoorVariables.cs` |
| CallbackUrl  | The path of the callback URL for your Casdoor application. If not provided, it will be `casdoor://callback` | `CasdoorVariables.cs` |
| ClientSecret | The Client Secret of your Casdoor application                                                           | `CasdoorVariables.cs` |

Defaults: [Casdoor demo](https://door.casdoor.com) and [app-casnode](https://door.casdoor.com/applications/app-casnode) if not set.

### Running

**Visual Studio**

1. Open `casdoor-dotnet-desktop-example.sln`
2. Press `Ctrl + F5` to start

**Command line**

1. `cd src/DesktopApp`
2. `dotnet run`

### Preview

![index](/img/how-to-connect/desktop-sdks/dotnet-app/index.png)

Click **Casdoor Login** to open the login window. After sign-in, the user profile is shown.

![login](/img/how-to-connect/desktop-sdks/dotnet-app/login.png)
![user profile](/img/how-to-connect/desktop-sdks/dotnet-app/userprofile.png)
![preview gif](/img/how-to-connect/desktop-sdks/dotnet-app/preview.gif)

## Integration

### Open the login window

```csharp
var login = new Login();
// Triggered when login succeeds, you will receive an auth code in the event handler
login.CodeReceived += Login_CodeReceived;
login.ShowDialog();
```

### Exchange the auth code for user info

```csharp
public async Task<string?> RequestToken(string clientId, string clientSecret, string code)
{
    var body = new
    {
        grant_type = "authorization_code",
        client_id = clientId,
        client_secret = clientSecret,
        code
    };

    var req = new RestRequest(_requestTokenUrl).AddJsonBody(body);
    var token = await _client.PostAsync<TokenDto>(req);

    return token?.AccessToken;
}

public async Task<UserDto?> GetUserInfo(string token)
{
    var req = new RestRequest(_getUserInfoUrl).AddQueryParameter("accessToken", token);

    return await _client.GetAsync<UserDto>(req);
}

...

var token = await _casdoorApi.RequestToken(
    CasdoorVariables.ClientId,
    CasdoorVariables.ClientSecret,
    authCode,
);

var user = await _casdoorApi.GetUserInfo(token);
```



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/mobile-sdks/react-native-app.md
================================================================================

---
title: React Native app
description: Integrate Casdoor in a React Native app with the official SDK.
keywords: [React Native, sdk]
authors: [cwp0]
---

The [casdoor-react-native-example](https://github.com/casdoor/casdoor-react-native-example) and [casdoor-react-native-sdk](https://github.com/casdoor/casdoor-react-native-sdk) show how to use Casdoor in React Native.

## Run the example

### Quick start

```bash
git clone git@github.com:casdoor/casdoor-react-native-example.git
cd casdoor-react-native-example
yarn install
cd ios/ && pod install && cd ..
```

**iOS:** `react-native start` then `react-native run-ios`  
**Android:** `react-native start` then `react-native run-android`

Start an emulator or connect a device before running.

### Preview

|                                                 **iOS**                                                  |                                                   **Android**                                                    |
|:--------------------------------------------------------------------------------------------------------:|:----------------------------------------------------------------------------------------------------------------:|
| <img src="/img/how-to-connect/mobile-sdks/react-native-app/iOS-login.png" alt="iOS-login" width="250" /> | <img src="/img/how-to-connect/mobile-sdks/react-native-app/Android-login.png" alt="Android-login" width="250" /> |

Click **Login with Casdoor** to open the Casdoor login screen.

|                                                         **iOS**                                                          |                                                           **Android**                                                            |
|:------------------------------------------------------------------------------------------------------------------------:|:--------------------------------------------------------------------------------------------------------------------------------:|
| <img src="/img/how-to-connect/mobile-sdks/react-native-app/iOS-casdoor-login.png" alt="iOS-casdoor-login" width="250" /> | <img src="/img/how-to-connect/mobile-sdks/react-native-app/Android-casdoor-login.png" alt="Android-casdoor-login" width="250" /> |

After sign-in, the user profile is shown.

|                                                       **iOS**                                                       |                                                           **Android**                                                            |
|:-------------------------------------------------------------------------------------------------------------------:|:--------------------------------------------------------------------------------------------------------------------------------:|
| <img src="/img/how-to-connect/mobile-sdks/react-native-app/iOS-userInfo.png" alt="iOS-userInfo" width="250" /> | <img src="/img/how-to-connect/mobile-sdks/react-native-app/Android-userInfo.png" alt="Android-userInfo" width="250" /> |


|                                                             **iOS**                                                              |                                 **Android**                                                                                              |
|:--------------------------------------------------------------------------------------------------------------------------------:|:----------------------------------------------------------------------------------------------------------------------------------------:|
| <img src="https://github.com/casdoor/casdoor-react-native-example/blob/master/iOS-gif.gif?raw=true" alt="iOS-gif" width="250" /> | <img src="https://github.com/casdoor/casdoor-react-native-example/blob/master/Android-gif.gif?raw=true" alt="Android-gif" width="250" /> |

## Integration

The example uses [casdoor-react-native-sdk](https://github.com/casdoor/casdoor-react-native-sdk). To use it in your own project:

### 1. Install the SDK

```shell script
# NPM
npm i casdoor-react-native-sdk

# Yarn
yarn add casdoor-react-native-sdk
```

### 2. Initialize

Set these 7 string parameters (all required except `redirectPath` and `signinPath`):

| Name (in order)  | Must | Description                                                                                    |
|------------------|------|------------------------------------------------------------------------------------------------|
| serverUrl        | Yes  | your Casdoor server URL                                                                        |
| clientId         | Yes  | the Client ID of your Casdoor application                                                      |
| appName          | Yes  | the name of your Casdoor application                                                           |
| organizationName | Yes  | the name of the Casdoor organization connected with your Casdoor application                   |
| redirectPath     | No   | the path of the redirect URL for your Casdoor application, will be `/callback` if not provided |
| signinPath       | No   | the path of the signin URL for your Casdoor application                                        |

```javascript

const sdkConfig = {
  serverUrl: 'https://door.casdoor.com',
  clientId: 'b800a86702dd4d29ec4d',
  appName: 'app-example',
  organizationName: 'casbin',
  redirectPath: 'http://localhost:5000/callback',
  signinPath: '/api/signin',
};
const sdk = new SDK(sdkConfig)
```

### 3. Use the SDK

Typical flow:

```javascript

// get the signin url
getSigninUrl()

// get Access Token
getAccessToken(redirectUrl); // http://localhost:5000/callback?code=b75bc5c5ac65ffa516e5&state=gjmfdgqf498

// decode jwt token to get user info
JwtDecode(jwtToken) 
```

See [casdoor-react-native-sdk](https://github.com/casdoor/casdoor-react-native-sdk) for the full API.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/mcp/connect-claude-desktop.md
================================================================================

---
title: Connect Claude Desktop to MCP
description: Connect Claude Desktop to Casdoor’s MCP server with OAuth.
keywords: [MCP, Claude Desktop, OAuth, PKCE]
authors: [hsluoyz]
---

Connect Claude Desktop to Casdoor’s MCP server so Claude can manage your applications, users, and resources via natural language.

## Prerequisites

- A running Casdoor instance (accessible via HTTPS recommended for production)
- [Claude Desktop](https://claude.ai/download) installed on your computer
- Admin access to your Casdoor instance to create applications

## Step 1: Create an application in Casdoor

Create a Casdoor application for Claude Desktop’s OAuth:

1. Log in to your Casdoor admin panel
2. Navigate to **Applications** and click **Add**
3. Configure the application with these settings:

   - **Name**: `claude-desktop-mcp` (or your preferred name)
   - **Display Name**: `Claude Desktop MCP Client`
   - **Organization**: Select your organization
   - **Redirect URIs**: Add these OAuth callback URLs:

     ```text
     http://127.0.0.1:*/callback
     http://localhost:*/callback
     ```

     :::tip
     The wildcard `*` allows Claude Desktop to use any available port for the OAuth callback.
     :::

4. **Grant Types**: Enable `Authorization Code` and optionally `Refresh Token`
5. **Enable PKCE**: Check this option for enhanced security
6. **Token Format**: `JWT` (recommended)
7. **(Optional) Application Type**: Set to `Agent`
8. **(Optional) Category**: Set to `MCP` for better organization

   :::info
   See [Application categories](/docs/application/categories) for Category and Type options.
   :::

9. Click **Save** and note the **Client ID** for the next step.

## Step 2: Configure Claude Desktop

Claude Desktop stores MCP server configurations in a JSON file. The location depends on your operating system:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

Open this file in a text editor and add your Casdoor MCP server configuration:

```json
{
  "mcpServers": {
    "casdoor": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-oauth",
        "https://your-casdoor.com/api/mcp"
      ],
      "env": {
        "OAUTH_CLIENT_ID": "your-client-id",
        "OAUTH_SCOPES": "read:application write:application openid profile email"
      }
    }
  }
}
```

Replace the following placeholders:

- `your-casdoor.com` → Your Casdoor instance domain
- `your-client-id` → The Client ID from Step 1

:::note
The `@modelcontextprotocol/server-oauth` package handles OAuth flows automatically. Claude Desktop will open your browser to complete authentication.
:::

### Configuring Scopes

The `OAUTH_SCOPES` environment variable controls what permissions Claude has. Common scopes include:

- `read:application` - View applications
- `write:application` - Create, update, delete applications
- `read:user` - View users
- `write:user` - Create, update, delete users
- `openid profile email` - Basic user information (required for OAuth)

See [Authorization and Scopes](/docs/how-to-connect/mcp/authorization) for the complete list of available scopes.

## Step 3: Restart Claude Desktop

After saving the configuration file:

1. Completely quit Claude Desktop (don't just close the window)
2. Relaunch Claude Desktop

Claude will automatically detect the new MCP server configuration.

## Step 4: Complete the OAuth Flow

The first time Claude Desktop connects to your Casdoor MCP server:

1. Claude Desktop will automatically open your default web browser
2. You'll see the Casdoor login page (if not already logged in)
3. After logging in, you'll see a **Consent Screen** asking you to authorize Claude Desktop
4. The consent screen shows the requested scopes (permissions)
5. Click **Authorize** to grant access
6. Your browser will redirect to `http://127.0.0.1:<port>/callback` and show a success message
7. Return to Claude Desktop - the connection is now established

:::tip
The OAuth token is securely stored by the MCP OAuth helper. You won't need to re-authorize unless you revoke the token or change scopes.
:::

## Step 5: Verify the Connection

Test the connection by asking Claude to interact with Casdoor:

**Example prompts to try:**

- "List all applications in Casdoor"
- "Show me details about the application named 'my-app'"
- "Create a new application called 'test-app' in organization 'my-org'"

Claude will use the MCP tools to execute these commands. You should see responses with data from your Casdoor instance.

**Expected output for "List all applications":**

```text
I found the following applications in your Casdoor instance:

1. claude-desktop-mcp (Claude Desktop MCP Client)
2. app-built-in (Casdoor)
...
```

## Troubleshooting

### Issue: "Unable to connect to MCP server"

**Cause**: The MCP server URL might be incorrect or unreachable.

**Solution**:

- Verify the URL in your `claude_desktop_config.json` is correct
- Ensure your Casdoor instance is running and accessible
- Check for HTTPS/HTTP mismatch (use HTTPS in production)

### Issue: "Redirect URI mismatch" error during OAuth

**Cause**: The callback URL doesn't match the configured Redirect URI in Casdoor.

**Solution**:

- In Casdoor, ensure your application has these redirect URIs:

  ```text
  http://127.0.0.1:*/callback
  http://localhost:*/callback
  ```

- The wildcard `*` is crucial - it allows any port

### Issue: "CORS error" in browser console

**Cause**: Cross-Origin Resource Sharing (CORS) restrictions.

**Solution**:

- Casdoor's MCP endpoint should automatically handle CORS for localhost origins
- If you're using a custom domain, ensure CORS is properly configured in Casdoor

### Issue: "insufficient_scope" error

**Cause**: The requested operation requires a scope that wasn't granted.

**Solution**:

- Update the `OAUTH_SCOPES` in your `claude_desktop_config.json` to include the required scope
- Example: Add `write:application` if you want to create/modify applications
- Restart Claude Desktop and re-authorize to get a new token with updated scopes

### Issue: OAuth token expired

**Cause**: Access tokens expire after a certain time.

**Solution**:

- If you enabled `Refresh Token` grant type in Step 1, the MCP OAuth helper will automatically refresh expired tokens
- Otherwise, you'll need to re-authorize by restarting Claude Desktop

### Issue: HTTPS requirement in production

**Cause**: OAuth best practices require HTTPS for production environments.

**Solution**:

- Use HTTPS for your Casdoor instance in production
- For local development/testing, HTTP with localhost is acceptable
- Configure SSL certificates or use a reverse proxy like Nginx

## Security Considerations

- **PKCE (Proof Key for Code Exchange)**: Always enable PKCE in your Casdoor application for enhanced security
- **Scopes**: Follow the principle of least privilege - only grant scopes that Claude actually needs
- **Token Storage**: The MCP OAuth helper stores tokens securely in your system's keychain
- **HTTPS**: Always use HTTPS for production Casdoor instances to protect OAuth flows
- **Token Revocation**: You can revoke access tokens in Casdoor's admin panel under **Tokens**

## Next Steps

Now that Claude Desktop is connected to Casdoor:

- Explore available [MCP Tools](/docs/how-to-connect/mcp/tools) that Claude can use
- Learn about [Authentication](/docs/how-to-connect/mcp/authentication) methods
- Understand [Error Handling](/docs/how-to-connect/mcp/error-handling) for better debugging
- Check out the [Integration Example](/docs/how-to-connect/mcp/integration) for programmatic access

## Related Resources

- [MCP Server Overview](/docs/how-to-connect/mcp/overview)
- [Authorization and Scopes](/docs/how-to-connect/mcp/authorization)
- [Application Categories](/docs/application/categories)
- [Claude.ai](https://claude.ai)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/mcp/troubleshooting.md
================================================================================

---
title: MCP troubleshooting
description: Common MCP and OAuth issues and how to debug them.
keywords: [MCP, OAuth, troubleshooting, debugging, errors]
authors: [hsluoyz]
---

This page covers common problems when using Casdoor’s built-in MCP server or when Casdoor is the OAuth provider for your own MCP server.

## Common Errors

### 401 Unauthorized from MCP Server

**Symptom**: MCP server rejects requests with `401 Unauthorized` status code.

**Causes**:

- Access token has expired
- Token's `aud` (audience) claim doesn't match the MCP server's resource URI
- Missing `Authorization: Bearer` header in requests
- Token was issued for a different resource

**Fix**:

1. Decode your token at [jwt.io](https://jwt.io) and check the `exp` claim for expiration
2. Verify the `aud` claim matches your MCP server's URI exactly (including scheme, host, and port)
3. Ensure requests include the header: `Authorization: Bearer YOUR_TOKEN`
4. If using the `resource` parameter during OAuth, confirm it matches the MCP server URI

```bash
# Example: Check token claims
curl -X GET https://your-mcp-server.com/api/mcp \
  -H "Authorization: Bearer YOUR_TOKEN"

# If 401, inspect token at jwt.io:
# - exp: 1735689600 (must be in future)
# - aud: "https://your-mcp-server.com" (must match server URI)
# - scope: "read:application" (must include required scopes)
```

### CORS Errors in Browser

**Symptom**: Browser console shows CORS errors when MCP client attempts to connect to Casdoor.

**Causes**:

- Casdoor CORS settings don't include the MCP client's origin
- Preflight requests are being blocked
- Wildcard CORS is disabled for security

**Fix**:

1. Log into Casdoor admin panel
2. Navigate to your application configuration
3. Add the MCP client's origin to the **CORS Allowed Origins** field
4. Include the full origin: `https://client-domain.com` (with scheme and port if non-standard)
5. For local development, add `http://localhost:PORT`

```text
# Example CORS configuration:
https://claude.ai
https://cursor.sh
http://localhost:3000
```

### Redirect URI Mismatch

**Symptom**: OAuth flow fails with `redirect_uri_mismatch` error.

**Causes**:

- The `redirect_uri` in the authorization request doesn't exactly match the application configuration
- Scheme mismatch (`http` vs `https`)
- Port number missing or incorrect
- Trailing slash mismatch

**Fix**:

1. Copy the exact `redirect_uri` from your authorization request
2. In Casdoor, edit the application configuration
3. Add the exact URI to **Redirect URLs** field (must match character-for-character)
4. Ensure scheme, host, port, and path all match exactly

```bash
# These are all different redirect URIs:
http://localhost:3000/callback
https://localhost:3000/callback  # Different scheme
http://localhost:3000/callback/  # Trailing slash
http://localhost:3001/callback   # Different port
```

### Discovery Endpoint 404

**Symptom**: Attempting to fetch `.well-known` discovery document returns 404.

**Causes**:

- Using wrong discovery path for your use case
- Casdoor configuration doesn't expose discovery endpoints
- Application not configured as OIDC provider

**Fix**:

Try these discovery endpoints in order:

1. **OAuth Authorization Server Metadata** (RFC 8414):

   ```bash
   curl https://your-casdoor.com/.well-known/oauth-authorization-server
   ```

2. **OpenID Connect Discovery**:

   ```bash
   curl https://your-casdoor.com/.well-known/openid-configuration
   ```

3. **OAuth Protected Resource Metadata** (RFC 9470):

   ```bash
   curl https://your-casdoor.com/.well-known/oauth-protected-resource
   ```

For MCP servers acting as resource servers, use the `oauth-protected-resource` endpoint to advertise OAuth requirements.

### DCR Registration Rejected

**Symptom**: Dynamic Client Registration (DCR) request fails with error.

**Causes**:

- Organization has DCR disabled in settings
- Registration request missing required fields
- Software statement rejected or invalid
- Rate limiting on registration endpoint

**Fix**:

1. Navigate to your organization settings in Casdoor
2. Enable **Dynamic Client Registration** toggle
3. Configure **Allowed Redirect URI Patterns** to restrict client URIs
4. For registration requests, include all required metadata:

   ```json
   {
     "client_name": "My MCP Client",
     "redirect_uris": ["https://client.example.com/callback"],
     "grant_types": ["authorization_code"],
     "token_endpoint_auth_method": "client_secret_basic"
   }
   ```

See [Dynamic client registration](/docs/application/dynamic-client-registration) for details.

### Consent Screen Not Showing

**Symptom**: OAuth flow completes without showing user consent screen.

**Causes**:

- Application's **Consent Policy** is set to "Never"
- User has previously granted consent and policy is "Once"
- Session authentication bypasses consent

**Fix**:

1. Edit your application in Casdoor admin panel
2. Set **Consent Policy** to:
   - **Always**: Show consent on every authorization request
   - **Once**: Show consent only on first authorization (recommended)
3. Save the application configuration
4. Clear user's previous consent if testing (revoke application access)

The consent screen displays requested scopes with their display names and descriptions from your scope configuration.

### insufficient_scope Error

**Symptom**: MCP tool calls fail with `insufficient_scope` JSON-RPC error.

**Causes**:

- Access token doesn't include the scope required by the tool
- Token was requested with incorrect scopes
- Scope names don't match server expectations

**Fix**:

1. Check the error response for `required_scope` and `granted_scopes`:

   ```json
   {
     "error": {
       "code": -32001,
       "message": "insufficient_scope",
       "data": {
         "tool": "add_application",
         "granted_scopes": ["read:application"],
         "required_scope": "write:application"
       }
     }
   }
   ```

2. Request a new token with the required scope:

   ```bash
   curl -X POST https://your-casdoor.com/api/login/oauth/access_token \
     -d "grant_type=client_credentials" \
     -d "client_id=YOUR_CLIENT_ID" \
     -d "client_secret=YOUR_CLIENT_SECRET" \
     -d "scope=read:application write:application"
   ```

See [Authorization and scopes](/docs/how-to-connect/mcp/authorization) for the scope reference.

### invalid_target / Resource Error

**Symptom**: Authorization request fails with `invalid_target` or `invalid_resource` error.

**Causes**:

- `resource` parameter is not a valid URI (RFC 8707)
- Resource URI missing scheme (`http://` or `https://`)
- Resource parameter conflicts with token audience

**Fix**:

1. Ensure `resource` parameter is a full URL:

   ```bash
   # Correct:
   resource=https://your-server.com
   resource=https://api.example.com:8080

   # Incorrect:
   resource=your-server.com        # Missing scheme
   resource=localhost:3000         # Missing scheme
   ```

2. The `resource` value becomes the `aud` claim in the access token
3. Resource must match the MCP server's expected audience exactly

### Claude Desktop / Cursor Connection Failures

**Symptom**: Claude Desktop or Cursor IDE fails to connect to MCP server with OAuth errors.

**Causes**:

- MCP server not returning valid Protected Resource Metadata (PRM)
- `WWW-Authenticate` header malformed or missing
- Discovery endpoint not accessible
- Token validation failing

**Fix**:

1. **Verify PRM endpoint** returns valid JSON:

   ```bash
   curl https://your-mcp-server.com/.well-known/oauth-protected-resource
   ```

   Expected response:

   ```json
   {
     "resource": "https://your-mcp-server.com",
     "authorization_servers": [
       "https://your-casdoor.com"
     ]
   }
   ```

2. **Check WWW-Authenticate header** on unauthorized requests:

   ```bash
   curl -v https://your-mcp-server.com/api/mcp
   ```

   Expected header:

   ```http
   WWW-Authenticate: Bearer realm="mcp-server",
     authorization_uri="https://your-casdoor.com/login/oauth/authorize",
     scope="read:application write:application"
   ```

3. **Test complete OAuth flow** with curl:

   ```bash
   # 1. Get authorization code (requires browser)
   # 2. Exchange for token
   curl -X POST https://your-casdoor.com/api/login/oauth/access_token \
     -d "grant_type=authorization_code" \
     -d "code=AUTH_CODE" \
     -d "redirect_uri=YOUR_REDIRECT_URI" \
     -d "client_id=YOUR_CLIENT_ID" \
     -d "client_secret=YOUR_CLIENT_SECRET"
   
   # 3. Test MCP endpoint with token
   curl https://your-mcp-server.com/api/mcp \
     -H "Authorization: Bearer ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
   ```

## Debugging Tools

### MCP Inspector

The official MCP Inspector helps test MCP connections interactively:

```bash
npx @modelcontextprotocol/inspector
```

Features:

- Interactive tool browser and testing
- Real-time JSON-RPC request/response viewer
- OAuth flow testing
- Connection diagnostics

### Testing Discovery Endpoints

Verify each discovery endpoint returns valid JSON:

```bash
# OAuth Authorization Server
curl -s https://your-casdoor.com/.well-known/oauth-authorization-server | jq

# OIDC Configuration
curl -s https://your-casdoor.com/.well-known/openid-configuration | jq

# Protected Resource (for MCP resource servers)
curl -s https://your-mcp-server.com/.well-known/oauth-protected-resource | jq
```

### Inspecting JWT Tokens

Use [jwt.io](https://jwt.io) to decode access tokens and verify claims:

**Key claims to check**:

- `aud` (audience): Must match MCP server URI
- `scope`: Must include required scopes for tools
- `exp` (expiration): Must be in the future (Unix timestamp)
- `iss` (issuer): Should match Casdoor's authorization server URL
- `sub` (subject): User identifier
- `client_id`: Application/client that received the token

```bash
# Alternative: Decode token with jq
echo "YOUR_JWT_TOKEN" | cut -d. -f2 | base64 -d | jq
```

### Token Introspection Endpoint

Casdoor provides a token introspection endpoint (RFC 7662) to validate and inspect tokens:

```bash
curl -X POST https://your-casdoor.com/api/login/oauth/introspect \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -u "CLIENT_ID:CLIENT_SECRET" \
  -d "token=ACCESS_TOKEN"
```

Response includes:

```json
{
  "active": true,
  "scope": "read:application write:application",
  "client_id": "your-client-id",
  "username": "admin",
  "exp": 1735689600,
  "iat": 1735603200,
  "aud": "https://your-mcp-server.com"
}
```

### Testing with curl

Manual OAuth flow testing with curl:

```bash
# 1. Test authorization endpoint (requires browser)
# Open in browser:
https://your-casdoor.com/login/oauth/authorize?
  client_id=YOUR_CLIENT_ID&
  redirect_uri=http://localhost:8080/callback&
  response_type=code&
  scope=read:application&
  state=random-state

# 2. Exchange authorization code for token
curl -X POST https://your-casdoor.com/api/login/oauth/access_token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code=AUTHORIZATION_CODE" \
  -d "redirect_uri=http://localhost:8080/callback" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET"

# 3. Use access token with MCP server
curl https://your-mcp-server.com/api/mcp \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### Debug Logging

Enable debug logging in your MCP client or server to see detailed OAuth flows:

**For MCP clients**:

- Check client configuration for debug/verbose mode
- Review client logs for OAuth redirect, token exchange, and API calls
- Capture network traffic with browser DevTools or mitmproxy

**For MCP servers**:

- Enable server debug logging to see incoming requests
- Log token validation results (success/failure and reasons)
- Monitor authorization checks and scope validation

### Network Debugging

Use browser DevTools or network analysis tools:

1. **Browser DevTools (F12)**:
   - Network tab shows all OAuth redirects and API calls
   - Console tab displays JavaScript errors
   - Application tab shows stored tokens and cookies

2. **mitmproxy** for CLI clients:

   ```bash
   mitmproxy -p 8080
   # Configure client to use proxy: http://localhost:8080
   ```

3. **Wireshark** for low-level packet analysis

## See also

- [Authorization and scopes](/docs/how-to-connect/mcp/authorization) — Scope reference
- [Error handling](/docs/how-to-connect/mcp/error-handling) — JSON-RPC error codes
- [Authentication](/docs/how-to-connect/mcp/authentication) — OAuth and tokens
- [Custom scopes](/docs/application/scopes) — Agent application scopes
- [Dynamic client registration](/docs/application/dynamic-client-registration) — DCR setup



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/mcp/connect-cursor.md
================================================================================

---
title: Connect Cursor to MCP
description: Connect Cursor IDE to Casdoor’s MCP server with OAuth.
keywords: [MCP, Cursor, IDE, OAuth, PKCE]
authors: [hsluoyz]
---

Connect Cursor IDE to Casdoor’s MCP server so you can manage applications, users, and resources from the editor.

## Prerequisites

- A running Casdoor instance (HTTPS recommended for production)
- [Cursor IDE](https://cursor.sh/) installed on your computer
- Admin access to your Casdoor instance to create applications

## Step 1: Create an application in Casdoor

Create a Casdoor application for Cursor’s OAuth:

1. Log in to your Casdoor admin panel
2. Navigate to **Applications** and click **Add**
3. Configure the application with these settings:

   - **Name**: `cursor-mcp` (or your preferred name)
   - **Display Name**: `Cursor IDE MCP Client`
   - **Organization**: Select your organization
   - **Redirect URIs**: Add these OAuth callback URLs:

     ```text
     http://127.0.0.1:*/callback
     http://localhost:*/callback
     ```

     :::tip
     The wildcard `*` allows Cursor to use any available port for the OAuth callback.
     :::

4. **Grant Types**: Enable `Authorization Code` and optionally `Refresh Token`
5. **Enable PKCE**: Check this option for enhanced security
6. **Token Format**: `JWT` (recommended)
7. **(Optional) Application Type**: Set to `Agent`
8. **(Optional) Category**: Set to `MCP` for better organization

   :::info
   See [Application categories](/docs/application/categories) for Category and Type options.
   :::

9. Click **Save** and note the **Client ID** for the next step.

## Step 2: Configure Cursor MCP settings

Cursor supports MCP server configuration through its settings. You can configure it either through the UI or by directly editing the configuration file.

### Option A: Using Cursor Settings UI

1. Open Cursor IDE
2. Go to **Settings** (Cmd+, on macOS or Ctrl+, on Windows/Linux)
3. Search for "MCP" in the settings search bar
4. Click **Edit in settings.json** to open the MCP configuration file

### Option B: Direct File Edit

The MCP configuration file location depends on your operating system:

- **macOS**: `~/Library/Application Support/Cursor/User/mcp.json`
- **Windows**: `%APPDATA%\Cursor\User\mcp.json`
- **Linux**: `~/.config/Cursor/User/mcp.json`

Add your Casdoor MCP server configuration:

```json
{
  "mcpServers": {
    "casdoor": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-oauth",
        "https://your-casdoor.com/api/mcp"
      ],
      "env": {
        "OAUTH_CLIENT_ID": "your-client-id",
        "OAUTH_SCOPES": "read:application write:application openid profile email"
      }
    }
  }
}
```

Replace the following placeholders:

- `your-casdoor.com` → Your Casdoor instance domain
- `your-client-id` → The Client ID from Step 1

:::note
The `@modelcontextprotocol/server-oauth` package handles OAuth flows automatically. Cursor will open your browser to complete authentication.
:::

### Configuring Scopes

The `OAUTH_SCOPES` environment variable controls what permissions Cursor's AI has. Common scopes include:

- `read:application` - View applications
- `write:application` - Create, update, delete applications
- `read:user` - View users
- `write:user` - Create, update, delete users
- `openid profile email` - Basic user information (required for OAuth)

See [Authorization and Scopes](/docs/how-to-connect/mcp/authorization) for the complete list of available scopes.

## Step 3: Reload Cursor

After saving the configuration:

1. Reload Cursor IDE (Cmd+Shift+P or Ctrl+Shift+P → "Developer: Reload Window")
2. Alternatively, restart Cursor completely

Cursor will automatically detect and load the new MCP server configuration.

## Step 4: Complete the OAuth Flow

When Cursor first connects to your Casdoor MCP server:

1. Cursor will automatically open your default web browser
2. You'll see the Casdoor login page (if not already logged in)
3. After logging in, you'll see a **Consent Screen** asking you to authorize Cursor
4. The consent screen displays the requested scopes (permissions)
5. Click **Authorize** to grant access
6. Your browser will redirect to `http://127.0.0.1:<port>/callback` and show a success message
7. Return to Cursor - the connection is now established

:::tip
The OAuth token is securely stored by the MCP OAuth helper. You won't need to re-authorize unless you revoke the token or change scopes.
:::

## Step 5: Verify the Connection

Test the connection by using Cursor's AI features to interact with Casdoor:

**Example prompts to try in Cursor's chat:**

- "Using the Casdoor MCP server, list all applications"
- "Show me details about the application named 'my-app' from Casdoor"
- "Create a new Casdoor application called 'test-app' in organization 'my-org'"

Cursor's AI will use the MCP tools to execute these commands. You should see responses with data from your Casdoor instance.

**Expected output:**

```text
I've queried the Casdoor MCP server and found the following applications:

1. cursor-mcp (Cursor IDE MCP Client)
2. app-built-in (Casdoor)
...
```

## Troubleshooting

### Issue: "MCP server not found" in Cursor

**Cause**: The configuration file might not be in the correct location or has syntax errors.

**Solution**:

- Verify the file path for your operating system
- Check that the JSON is valid (no trailing commas, proper quotes)
- Reload Cursor after making changes

### Issue: "Unable to connect to MCP server"

**Cause**: The MCP server URL might be incorrect or unreachable.

**Solution**:

- Verify the URL in your `mcp.json` is correct
- Ensure your Casdoor instance is running and accessible
- Check for HTTPS/HTTP mismatch (use HTTPS in production)

### Issue: "Redirect URI mismatch" error during OAuth

**Cause**: The callback URL doesn't match the configured Redirect URI in Casdoor.

**Solution**:

- In Casdoor, ensure your application has these redirect URIs:

  ```text
  http://127.0.0.1:*/callback
  http://localhost:*/callback
  ```

- The wildcard `*` is crucial - it allows any port

### Issue: "CORS error" in browser console

**Cause**: Cross-Origin Resource Sharing (CORS) restrictions.

**Solution**:

- Casdoor's MCP endpoint should automatically handle CORS for localhost origins
- If you're using a custom domain, ensure CORS is properly configured in Casdoor

### Issue: "insufficient_scope" error when using AI features

**Cause**: The requested operation requires a scope that wasn't granted.

**Solution**:

- Update the `OAUTH_SCOPES` in your `mcp.json` to include the required scope
- Example: Add `write:application` if you want to create/modify applications
- Reload Cursor and re-authorize to get a new token with updated scopes

### Issue: OAuth token expired

**Cause**: Access tokens expire after a certain time.

**Solution**:

- If you enabled `Refresh Token` grant type in Step 1, the MCP OAuth helper will automatically refresh expired tokens
- Otherwise, you'll need to re-authorize by reloading Cursor

### Issue: MCP tools not available in Cursor's AI

**Cause**: Cursor might not have loaded the MCP server or OAuth hasn't completed.

**Solution**:

- Check Cursor's developer console (Help → Toggle Developer Tools) for errors
- Try explicitly mentioning "using Casdoor MCP server" in your prompts
- Ensure you've completed the OAuth flow in Step 4

## Security Considerations

- **PKCE (Proof Key for Code Exchange)**: Always enable PKCE in your Casdoor application for enhanced security
- **Scopes**: Follow the principle of least privilege - only grant scopes that Cursor actually needs
- **Token Storage**: The MCP OAuth helper stores tokens securely in your system's keychain
- **HTTPS**: Always use HTTPS for production Casdoor instances to protect OAuth flows
- **Token Revocation**: You can revoke access tokens in Casdoor's admin panel under **Tokens**
- **Code Review**: Always review AI-generated code that interacts with Casdoor before executing it

## Use Cases

With Cursor connected to Casdoor's MCP server, you can:

- **Generate configuration code**: Ask Cursor to generate application setup code based on existing Casdoor apps
- **Automate user management**: Create scripts to bulk-create users or update permissions
- **Documentation**: Generate documentation for your Casdoor setup automatically
- **Testing**: Create test applications and clean them up programmatically
- **Migration scripts**: Build scripts to migrate configurations between Casdoor instances

## Next Steps

Now that Cursor is connected to Casdoor:

- Explore available [MCP Tools](/docs/how-to-connect/mcp/tools) that Cursor can use
- Learn about [Authentication](/docs/how-to-connect/mcp/authentication) methods
- Understand [Error Handling](/docs/how-to-connect/mcp/error-handling) for better debugging
- Check out the [Integration Example](/docs/how-to-connect/mcp/integration) for programmatic access

## Related Resources

- [MCP Server Overview](/docs/how-to-connect/mcp/overview)
- [Authorization and Scopes](/docs/how-to-connect/mcp/authorization)
- [Application Categories](/docs/application/categories)
- [Cursor Documentation](https://cursor.sh/docs)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/mcp/integration.md
================================================================================

---
title: MCP integration example
description: "Python example: scoped token and MCP tool calls."
keywords: [MCP, integration, Python, example]
authors: [hsluoyz]
---

Example: obtain a scoped token, connect to the MCP server, and call tools (with scope error handling):

```python

# Server configuration
server_url = "https://your-casdoor.com/api/mcp"
token_url = "https://your-casdoor.com/api/login/oauth/access_token"
client_id = "your-client-id"
client_secret = "your-client-secret"

# Get a scoped token for application management
token_response = requests.post(token_url, data={
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_secret": client_secret,
    "scope": "read:application write:application"
})
access_token = token_response.json()["access_token"]

# Create a session with the token
session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
})

# Initialize the connection
init_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "python-client", "version": "1.0.0"}
    }
}
response = session.post(server_url, json=init_request)
print("Initialize:", response.json())

# Send initialized notification
notify_request = {
    "jsonrpc": "2.0",
    "method": "notifications/initialized"
}
session.post(server_url, json=notify_request)

# List available tools (filtered by scopes)
list_tools_request = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list"
}
response = session.post(server_url, json=list_tools_request)
print("Available tools:", response.json())

# Create a new application (requires write:application scope)
create_app_request = {
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
        "name": "add_application",
        "arguments": {
            "application": {
                "owner": "my-org",
                "name": "automated-app",
                "displayName": "Automated Application",
                "organization": "my-org"
            }
        }
    }
}
response = session.post(server_url, json=create_app_request)
result = response.json()

if "error" in result:
    error = result["error"]
    if error.get("code") == -32001 and error.get("message") == "insufficient_scope":
        # Handle insufficient scope error
        error_data = error.get("data", {})
        print(f"Need scope: {error_data.get('required_scope', 'unknown')}")
        print(f"Have scopes: {error_data.get('granted_scopes', [])}")
    else:
        print(f"Error: {error.get('message', 'Unknown error')}")
else:
    print("Created application:", result)
```

This example demonstrates obtaining a scoped token, using it to authenticate with the MCP server, and handling potential scope-related errors. The token includes both read and write scopes, allowing full application management.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/mcp/overview.md
================================================================================

---
title: MCP server overview
description: Use Casdoor’s MCP server for programmatic access via JSON-RPC 2.0.
keywords: [MCP, Model Context Protocol, API, automation, JSON-RPC]
authors: [hsluoyz]
---

Casdoor exposes a **Model Context Protocol (MCP)** server at `/api/mcp`. Clients (e.g. AI assistants or automation tools) can call it over JSON-RPC 2.0 to manage applications, users, and other resources without using Casdoor’s REST API directly.

## What is MCP?

MCP is a JSON-RPC 2.0 protocol for discovering and calling tools provided by a server. Casdoor’s MCP server exposes tools so clients can manage Casdoor resources in a standard way.

## Getting Started

The MCP endpoint is available at `/api/mcp` and accepts POST requests with JSON-RPC 2.0 payloads. Before making tool calls, clients must complete the initialization handshake:

```json
POST /api/mcp
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "my-client",
      "version": "1.0.0"
    }
  }
}
```

The server responds with its capabilities:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {
        "listChanged": true
      }
    },
    "serverInfo": {
      "name": "Casdoor MCP Server",
      "version": "1.0.0"
    }
  }
}
```

After initialization, send a notification to indicate the client is ready:

```json
POST /api/mcp
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/mcp/error-handling.md
================================================================================

---
title: MCP error handling
description: JSON-RPC error codes and responses from the MCP server.
keywords: [MCP, errors, JSON-RPC, troubleshooting]
authors: [hsluoyz]
---

## Error codes

The MCP server uses standard JSON-RPC 2.0 error codes:

- **-32700**: Parse error - Invalid JSON
- **-32600**: Invalid Request - Missing required fields
- **-32601**: Method not found - Unknown method name
- **-32602**: Invalid params - Malformed parameters
- **-32001**: Unauthorized or Insufficient scope

The `-32001` error code covers both authentication failures and authorization issues. When you lack the required scope for a tool, the error includes details about what scope you need:

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "error": {
    "code": -32001,
    "message": "insufficient_scope",
    "data": {
      "tool": "add_application",
      "granted_scopes": ["read:application"],
      "required_scope": "write:application"
    }
  }
}
```

## Common Error Examples

Invalid JSON triggers a parse error:

```json
{
  "jsonrpc": "2.0",
  "id": null,
  "error": {
    "code": -32700,
    "message": "Parse error",
    "data": "unexpected character at position 12"
  }
}
```

Unknown methods return method not found:

```json
{
  "jsonrpc": "2.0",
  "id": 8,
  "error": {
    "code": -32601,
    "message": "Method not found",
    "data": "Method 'unknown_method' not found"
  }
}
```

## Additional Features

The MCP server implements the full JSON-RPC 2.0 specification including notifications (requests without an `id` field) and batch requests. The `ping` method provides a simple health check:

```json
{
  "jsonrpc": "2.0",
  "id": 9,
  "method": "ping"
}
```

When running in demo mode, the server restricts write operations to protect the demonstration instance while allowing all read operations and authentication flows.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/mcp/tools.md
================================================================================

---
title: MCP tools reference
description: List and call MCP tools (applications and more).
keywords: [MCP, tools, API, application management]
authors: [hsluoyz]
---

## List tools

Call `tools/list` to discover tools:

```json
POST /api/mcp
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list"
}
```

The response depends on auth: unauthenticated requests see all tools (for discovery); session auth returns the full list; a scoped token returns only tools allowed by that token’s scopes.

The server returns tool definitions with input schemas:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "get_applications",
        "description": "Get all applications for a specific owner",
        "inputSchema": {
          "type": "object",
          "properties": {
            "owner": {
              "type": "string",
              "description": "The owner of applications"
            }
          },
          "required": ["owner"]
        }
      }
    ]
  }
}
```

## Application Management Tools

The MCP server currently provides these application management tools:

**get_applications** - Retrieve all applications for an organization:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "get_applications",
    "arguments": {
      "owner": "my-org"
    }
  }
}
```

**get_application** - Get details of a specific application:

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "get_application",
    "arguments": {
      "id": "my-org/my-app"
    }
  }
}
```

**add_application** - Create a new application:

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "tools/call",
  "params": {
    "name": "add_application",
    "arguments": {
      "application": {
        "owner": "my-org",
        "name": "new-app",
        "displayName": "New Application",
        "organization": "my-org"
      }
    }
  }
}
```

**update_application** - Modify an existing application:

```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "tools/call",
  "params": {
    "name": "update_application",
    "arguments": {
      "id": "my-org/my-app",
      "application": {
        "owner": "my-org",
        "name": "my-app",
        "displayName": "Updated Name"
      }
    }
  }
}
```

**delete_application** - Remove an application:

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "tools/call",
  "params": {
    "name": "delete_application",
    "arguments": {
      "application": {
        "owner": "my-org",
        "name": "old-app"
      }
    }
  }
}
```

## Response Format

Tool calls return results in a structured format:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "[{\"name\":\"app1\",\"displayName\":\"App 1\"}]"
      }
    ]
  }
}
```

When errors occur during tool execution, the response includes an `isError` flag:

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "application quota is exceeded"
      }
    ],
    "isError": true
  }
}
```



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/how-to-connect/mcp/connect-chatgpt.md
================================================================================

---
title: Connect ChatGPT to MCP
description: Connect ChatGPT to Casdoor’s MCP server with OAuth.
keywords: [MCP, ChatGPT, OpenAI, OAuth, PKCE]
authors: [hsluoyz]
---

Connect ChatGPT to Casdoor’s MCP server so you can manage applications, users, and resources from ChatGPT. Requires ChatGPT Plus or Enterprise with MCP support ([OpenAI docs](https://openai.com/chatgpt)).

## Prerequisites

- A running Casdoor instance (HTTPS required for ChatGPT integration)
- A ChatGPT Plus or Enterprise account with MCP support
- Admin access to your Casdoor instance to create applications

## Step 1: Create an application in Casdoor

Create a Casdoor application for ChatGPT’s OAuth:

1. Log in to your Casdoor admin panel
2. Navigate to **Applications** and click **Add**
3. Configure the application with these settings:

   - **Name**: `chatgpt-mcp` (or your preferred name)
   - **Display Name**: `ChatGPT MCP Client`
   - **Organization**: Select your organization
   - **Redirect URIs**: Add the ChatGPT OAuth callback URL:

     ```text
     https://chat.openai.com/auth/callback
     ```

     :::warning
     ChatGPT requires HTTPS for OAuth callbacks. Ensure your Casdoor instance is accessible via HTTPS.
     :::

4. **Grant Types**: Enable `Authorization Code` and `Refresh Token`
5. **Enable PKCE**: Check this option for enhanced security
6. **Token Format**: `JWT` (recommended)
7. **(Optional) Application Type**: Set to `Agent`
8. **(Optional) Category**: Set to `MCP` for better organization

   :::info
   See [Application categories](/docs/application/categories) for Category and Type options.
   :::

9. Click **Save** and note the **Client ID** and **Client Secret** for the next step.

## Step 2: Configure ChatGPT MCP Connection

ChatGPT supports connecting to MCP servers through its settings interface.

### Access MCP Settings

1. Log in to [ChatGPT](https://chat.openai.com)
2. Click on your profile icon in the bottom left
3. Go to **Settings** → **Beta Features**
4. Enable **Model Context Protocol** (if not already enabled)
5. Navigate to **Settings** → **MCP Servers**

### Add Casdoor MCP Server

1. Click **Add Server** or **+ New Server**
2. Fill in the server details:

   - **Server Name**: `Casdoor` (or your preferred name)
   - **Server URL**: `https://your-casdoor.com/api/mcp`
   - **Authentication Type**: Select `OAuth 2.0`
   - **Client ID**: Your Client ID from Step 1
   - **Client Secret**: Your Client Secret from Step 1
   - **Authorization URL**: `https://your-casdoor.com/api/login/oauth/authorize`
   - **Token URL**: `https://your-casdoor.com/api/login/oauth/access_token`
   - **Scopes**: `read:application write:application openid profile email`

3. Click **Save** or **Connect**

:::note
The exact UI and field names may vary depending on ChatGPT's current interface. Refer to ChatGPT's help documentation for the most up-to-date instructions.
:::

### Configuring Scopes

The scopes you configure control what permissions ChatGPT has. Common scopes include:

- `read:application` - View applications
- `write:application` - Create, update, delete applications
- `read:user` - View users
- `write:user` - Create, update, delete users
- `openid profile email` - Basic user information (required for OAuth)

See [Authorization and Scopes](/docs/how-to-connect/mcp/authorization) for the complete list of available scopes.

## Step 3: Complete the OAuth Flow

After adding the server configuration:

1. ChatGPT will automatically initiate the OAuth flow
2. You'll be redirected to the Casdoor login page (if not already logged in)
3. After logging in, you'll see a **Consent Screen** asking you to authorize ChatGPT
4. The consent screen displays the requested scopes (permissions)
5. Click **Authorize** to grant access
6. You'll be redirected back to ChatGPT with a success message
7. The connection is now established

:::tip
The OAuth token is securely stored by ChatGPT. You won't need to re-authorize unless you revoke the token or change scopes.
:::

## Step 4: Verify the Connection

Test the connection by asking ChatGPT to interact with Casdoor in a new conversation:

**Example prompts to try:**

- "Using Casdoor, list all applications"
- "Show me details about the application named 'my-app' from Casdoor"
- "Create a new application in Casdoor called 'test-app' in organization 'my-org'"

ChatGPT will use the MCP tools to execute these commands. You should see responses with data from your Casdoor instance.

**Expected output for "List all applications":**

```text
I've connected to your Casdoor instance and found the following applications:

1. chatgpt-mcp (ChatGPT MCP Client)
   - Organization: my-org
   - Created: 2024-01-15

2. app-built-in (Casdoor)
   - Organization: built-in
   - Default application

...
```

## Alternative: Using MCP Proxy (Advanced)

If ChatGPT doesn't support direct MCP server connections or you need more control, you can use an MCP proxy service:

### Using a Cloud MCP Proxy

1. Deploy an MCP proxy service (e.g., using the `@modelcontextprotocol/server-oauth` package) on a cloud platform
2. Configure the proxy to connect to your Casdoor instance
3. Add the proxy URL to ChatGPT instead of the direct Casdoor URL

### Example: Deploying MCP Proxy on Vercel

```bash
# Install the MCP OAuth server
npm install -g @modelcontextprotocol/server-oauth

# Create a simple server wrapper
cat > server.js << 'EOF'
const { createServer } = require('@modelcontextprotocol/server-oauth');

const server = createServer({
  targetUrl: process.env.CASDOOR_URL + '/api/mcp',
  clientId: process.env.OAUTH_CLIENT_ID,
  clientSecret: process.env.OAUTH_CLIENT_SECRET,
  scopes: process.env.OAUTH_SCOPES.split(' ')
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`MCP proxy listening on port ${PORT}`);
});
EOF

# Deploy to your preferred platform
```

Set environment variables:

- `CASDOOR_URL`: Your Casdoor instance URL
- `OAUTH_CLIENT_ID`: Your Client ID
- `OAUTH_CLIENT_SECRET`: Your Client Secret
- `OAUTH_SCOPES`: Space-separated list of scopes

## Troubleshooting

### Issue: "Unable to connect to MCP server"

**Cause**: The MCP server URL might be incorrect or unreachable.

**Solution**:

- Verify the URL in ChatGPT settings is correct
- Ensure your Casdoor instance is publicly accessible via HTTPS
- Test the MCP endpoint manually: `curl https://your-casdoor.com/api/mcp`

### Issue: "Redirect URI mismatch" error during OAuth

**Cause**: The callback URL doesn't match the configured Redirect URI in Casdoor.

**Solution**:

- In Casdoor, ensure your application has the correct redirect URI:

  ```text
  https://chat.openai.com/auth/callback
  ```

- Check ChatGPT's documentation for the current callback URL

### Issue: "HTTPS required" error

**Cause**: ChatGPT requires HTTPS for OAuth flows.

**Solution**:

- Ensure your Casdoor instance uses HTTPS
- Configure SSL certificates for your domain
- Use a reverse proxy (Nginx, Caddy) with automatic HTTPS
- For development, consider using ngrok or similar tunneling services

### Issue: "CORS error" during OAuth flow

**Cause**: Cross-Origin Resource Sharing (CORS) restrictions.

**Solution**:

- Casdoor should automatically allow CORS for OAuth endpoints
- If using a reverse proxy, ensure CORS headers are properly forwarded
- Check your Casdoor CORS configuration for ChatGPT's domain

### Issue: "insufficient_scope" error

**Cause**: The requested operation requires a scope that wasn't granted.

**Solution**:

- Update the scopes in ChatGPT's MCP server settings
- Example: Add `write:application` if you want to create/modify applications
- Reconnect the server to get a new token with updated scopes

### Issue: OAuth token expired in long conversations

**Cause**: Access tokens expire after a certain time.

**Solution**:

- Ensure `Refresh Token` grant type is enabled in your Casdoor application (Step 1)
- ChatGPT should automatically refresh tokens, but you may need to reconnect if refresh fails

### Issue: MCP server not available in conversation

**Cause**: The server might not be properly connected or recognized.

**Solution**:

- Verify the connection in ChatGPT settings
- Try explicitly mentioning "using Casdoor MCP server" in your prompts
- Start a new conversation to ensure fresh initialization

## Security Considerations

- **HTTPS Only**: Always use HTTPS for production Casdoor instances when integrating with ChatGPT
- **PKCE (Proof Key for Code Exchange)**: Always enable PKCE in your Casdoor application
- **Scopes**: Follow the principle of least privilege - only grant scopes that ChatGPT needs
- **Token Storage**: ChatGPT stores tokens securely on OpenAI's infrastructure
- **Client Secret**: Keep your Client Secret confidential - don't share it in conversations
- **Token Revocation**: You can revoke access tokens in Casdoor's admin panel under **Tokens**
- **Audit Logs**: Monitor Casdoor's audit logs for actions performed by ChatGPT

## Privacy Considerations

:::warning
When using ChatGPT with Casdoor MCP server, be aware that:

- Data from your Casdoor instance may be processed by OpenAI
- Avoid sharing sensitive user information, passwords, or secrets
- Review OpenAI's privacy policy and terms of service
- Consider using data masking or filtering for sensitive fields
:::

## Use Cases

With ChatGPT connected to Casdoor's MCP server, you can:

- **Natural language queries**: "Show me all users created last week"
- **Bulk operations**: "Create 5 test applications for development"
- **Configuration assistance**: "What's the current OAuth configuration for app-xyz?"
- **Troubleshooting**: "Why isn't user John able to log in?"
- **Documentation**: "Explain the setup for our authentication system"
- **Reporting**: "Generate a summary of all active applications"

## Next Steps

Now that ChatGPT is connected to Casdoor:

- Explore available [MCP Tools](/docs/how-to-connect/mcp/tools) that ChatGPT can use
- Learn about [Authentication](/docs/how-to-connect/mcp/authentication) methods
- Understand [Error Handling](/docs/how-to-connect/mcp/error-handling) for better debugging
- Check out the [Integration Example](/docs/how-to-connect/mcp/integration) for programmatic access

## Related Resources

- [MCP Server Overview](/docs/how-to-connect/mcp/overview)
- [Authorization and Scopes](/docs/how-to-connect/mcp/authorization)
- [Application Categories](/docs/application/categories)
- [ChatGPT Documentation](https://help.openai.com/en/collections/3742473-chatgpt)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/overview.md
================================================================================

---
title: Overview
description: Configure third-party providers for OAuth, SMS, email, storage, payment, captcha, and more.
keywords: [provider, OAuth, SMS, storage, email, payment, captcha, MFA]
authors: [kininaru]
---

**Providers** in Casdoor are connectors to third-party services. This section describes the provider types and how to add and use them.

## Provider types

Casdoor supports the following provider types:

| Type | Purpose |
|------|--------|
| **OAuth** | Sign-in via external identity providers (e.g. GitHub, Google, QQ). See [OAuth](/docs/provider/oauth/overview). |
| **SMS** | Send SMS verification codes for phone number verification. |
| **Email** | Send email (e.g. verification codes, notifications). |
| **Storage** | Store files on the local filesystem or cloud object storage (e.g. S3, OSS). |
| **Payment** | Accept payments (e.g. Alipay, WeChat Pay, PayPal). Used for products and subscriptions. |
| **Captcha** | Protect sign-in and sign-up with captcha (Default, reCAPTCHA, hCaptcha, Cloudflare Turnstile, Alibaba Cloud, etc.). |
| **Identity verification** | Verify user identity via third-party services (e.g. Jumio) using ID documents. |
| **MFA** | Second-factor authentication (e.g. RADIUS) for multi-factor authentication. |

## Scope and permissions

Only administrators can add and configure providers. Visibility of providers depends on who created them:

- **Global administrators**: Users in the `built-in` organization or with `IsGlobalAdmin` enabled. Providers they create can be used by **all** applications.
- **Organization administrators**: Users with `IsAdmin` enabled. Providers they create can be used **only** by applications in the same organization (behavior may evolve in future releases).

## Adding a provider to an application

A provider must be added to an application before it can be used. Steps:

1. Open the application edit page and add a new provider row.

   ![provider_overview_add](/img/providers/provider_overview_add.png)

2. Choose the provider to attach. The list shows all providers available to that application.

   ![provider_overview_select](/img/providers/provider_overview_select.png)

3. For **OAuth** and **Captcha** providers, further configure how they are used. See [OAuth](/docs/provider/oauth/overview#attaching-the-provider-to-an-application) and [Captcha](/docs/provider/captcha/default#configure-in-casdoor).

   ![provider_overview_config](/img/providers/provider_overview_config.png)

4. **Save** the application. The provider is now available for that application.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/notification/googleChat.md
================================================================================

---
title: Google Chat notification
description: Use Google Chat as a notification provider via a service account.
keywords: [Google Chat, notification, provider]
authors: [UsherFall]
---

Google Chat notifications use **Application Default Credentials** (service account JSON). See [How Application Default Credentials work](https://cloud.google.com/docs/authentication/application-default-credentials).

The credential JSON has this shape:

```json
{
  "type": "service_account",
  "project_id": "",
  "private_key_id": "",
  "private_key": "",
  "client_email": "",
  "client_id": "",
  "auth_uri": "",
  "token_uri": "",
  "auth_provider_x509_cert_url": "",
  "client_x509_cert_url": ""
}
```

## Configure the provider in Casdoor

**Providers** → **Add**. Set **Category** to **Notification**, **Type** to **Google Chat**. Paste the full service account JSON into the **Application credential** / metadata field (as required by the provider form).

![google_chat_provider](/img/providers/notification/google_chat_provider.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/notification/telegram.md
================================================================================

---
title: Telegram notification
description: Send Casdoor notifications to Telegram.
keywords: [telegram, notification, provider]
authors: [UsherFall]
---

## 1. Get bot API token

Create a [Telegram](https://web.telegram.org/) account, then open [@BotFather](https://telegram.me/BotFather) and send `/newbot`. Set the bot name and username; BotFather returns an **API Token**.

![telegram_bot](/img/providers/notification/telegram_bot.png)

## 2. Get chat ID

Use [@RawDataBot](https://t.me/raw_info_bot) in Telegram: start a chat and it will show your **Chat ID**.

![telegram_chat_id](/img/providers/notification/telegram_chat_id.png)

## 3. Configure the provider in Casdoor

Create a **Notification** provider, set **Type** to **Telegram**, and fill in:

| Casdoor field | Value     |
|---------------|-----------|
| Secret key    | API Token |
| Chat ID       | Chat ID   |
| Content       | Message template (optional) |

![telegram_provider](/img/providers/notification/telegram_provider.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/notification/twitter.md
================================================================================

---
title: Twitter (X) notification
description: Use Twitter (X) as a notification provider.
keywords: [Twitter, notification, provider, X]
authors: [UsherFall]
---

## 1. Get Twitter app credentials

Sign up for a [Twitter developer account](https://developer.twitter.com/) and create an app. See [API Key and Secret](https://developer.twitter.com/en/docs/authentication/oauth-1-0a/api-key-and-secret). Copy **API Key**, **API Secret**, **Access Token**, and **Access Token Secret**.

![twitter_items](/img/providers/notification/twitter_items.png)

## 2. Get Twitter ID

The **Twitter ID** (numeric user ID) is not shown in the app UI; use [TweeterID](https://tweeterid.com/) or [Twiteridfinder](https://twiteridfinder.com/) to get it.

## 3. Configure the provider in Casdoor

**Providers** → **Add**. Set **Category** to **Notification**, **Type** to **Twitter**. Map:

| Casdoor       | Twitter           |
|---------------|-------------------|
| Client ID     | API Key           |
| Client secret | API Secret        |
| Client ID 2   | Access Token      |
| Client secret 2 | Access Token Secret |
| Chat ID       | Twitter ID        |

![twitter_provider](/img/providers/notification/twitter_provider.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/notification/slack.md
================================================================================

---
title: Slack notification
description: Send Casdoor notifications to a Slack channel.
keywords: [Slack, notification, provider]
authors: [UsherFall]
---

## 1. Create a Slack app

At [Slack API](https://api.slack.com/apps), create an app and add the OAuth scopes **chat:write** and **chat:write.public** for the bot.

![slack_app](/img/providers/notification/slack_app.png)

## 2. Get token and channel ID

- Copy the **Bot User OAuth Access Token** from **OAuth & Permissions**.
- Get the **Channel ID**: right-click the channel in Slack and choose **Copy link** (or “copy name”); the ID is in the URL or you can use Slack’s channel details.

![slack_token](/img/providers/notification/slack_token.png)
![slack_channel](/img/providers/notification/slack_channel.png)

## 3. Configure the provider in Casdoor

Create a **Notification** provider, set **Type** to **Slack**, and fill in:

| Casdoor field | Value        |
|---------------|--------------|
| Secret key    | Access Token |
| Chat ID       | Channel ID   |
| Content       | Message template (optional) |

![slack_provider](/img/providers/notification/slack_provider.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/notification/overview.md
================================================================================

---
title: Notification provider overview
description: Send notifications via Telegram, Slack, Discord, and other channels.
keywords: [Notification, Telegram, Slack, Discord]
authors: [UsherFall]
---

Casdoor can send notification messages through **Notification** providers. Add a provider and attach it to your application to enable notifications.

Supported providers:

| Provider | |
|----------|---|
| Telegram | <img src="https://cdn.casbin.org/img/social_telegram.png" width="40" /> |
| Custom HTTP | <img src="https://cdn.casbin.org/img/email_default.png" width="40" /> |
| Slack | <img src="https://cdn.casbin.org/img/social_slack.png" width="40" /> |
| Google Chat | <img src="https://cdn.casbin.org/img/social_google_chat.png" width="40" /> |
| Twitter | <img src="https://cdn.casbin.org/img/social_twitter.png" width="40" /> |
| Discord | <img src="https://cdn.casbin.org/img/social_discord.png" width="40" /> |
| Bark | <img src="https://cdn.casbin.org/img/social_bark.png" width="40" /> |
| DingTalk | <img src="https://cdn.casbin.org/img/social_dingtalk.png" width="40" /> |
| Lark | <img src="https://cdn.casbin.org/img/social_lark.png" width="40" /> |
| Line | <img src="https://cdn.casbin.org/img/social_line.png" width="40" /> |
| Matrix | <img src="https://cdn.casbin.org/img/social_matrix.png" width="40" /> |
| Microsoft Teams | <img src="https://cdn.casbin.org/img/social_teams.png" width="40" /> |
| WeCom | <img src="https://cdn.casbin.org/img/social_wecom.png" width="40" /> |
| Pushbullet | <img src="https://cdn.casbin.org/img/social_pushbullet.png" width="40" /> |
| Pushover | <img src="https://cdn.casbin.org/img/social_pushover.png" width="40" /> |
| Reddit | <img src="https://cdn.casbin.org/img/social_reddit.png" width="40" /> |
| Rocket Chat | <img src="https://cdn.casbin.org/img/social_rocket_chat.png" width="40" /> |
| Viber | <img src="https://cdn.casbin.org/img/social_viber.png" width="40" /> |
| Webpush | <img src="https://cdn.casbin.org/img/email_default.png" width="40" /> |

See the provider subpages for configuration details per channel.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/notification/wecom.md
================================================================================

---
title: WeCom notification
description: Use WeCom (WeChat Work) group bot webhooks for notifications.
keywords: [WeCom, WeChat Work, notification, provider]
authors: [hsluoyz]
---

WeCom can send notifications to a group via a bot webhook.

## 1. Create a group bot

In WeCom, create a group chat and add a bot in the group settings. Copy the **webhook URL** (format: `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY`). See [WeCom webhook docs](https://developer.work.weixin.qq.com/document/path/90236).

## 2. Configure the provider in Casdoor

**Providers** → **Add**. Set **Category** to **Notification**, **Type** to **WeCom**. Paste the webhook URL into **Endpoint**. Optionally set **Content** as a message template for notifications.

| Casdoor | WeCom      |
|---------|------------|
| Endpoint| Webhook URL|



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/notification/customHttp.md
================================================================================

---
title: Custom HTTP notification
description: Send notifications to an arbitrary HTTP endpoint.
keywords: [custom, notification, provider, HTTP]
authors: [UsherFall]
---

The **Custom HTTP** provider sends notification payloads to a URL you specify (GET or POST).

## Configure the provider

**Providers** → **Add**. Set **Category** to **Notification**, **Type** to **Custom HTTP**. Fill in:

| Field           | Description |
|-----------------|-------------|
| Method          | `GET` or `POST` |
| Parameter name  | Query (GET) or body (POST) parameter name for the message |
| Content         | Message content or template |
| Endpoint        | Full HTTP(S) URL to call |
| Chat ID         | Optional identifier |

![custom_http_provider](/img/providers/notification/custom_http_provider.png)

When you use **Send Notification Message**, Casdoor sends a request to **Endpoint** with the message in the chosen parameter. Example:

![custom_http_request](/img/providers/notification/custom_http_request.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/notification/discord.md
================================================================================

---
title: Discord notification
description: Use Discord as a notification provider (webhook-style).
keywords: [Discord, notification, provider]
authors: [UsherFall]
---

## 1. Get bot token

In the [Discord Developer Portal](https://discord.com/developers/applications), create an application and open the **Bot** tab. Create or copy the bot **token**.

![discord_token](/img/providers/notification/discord_token.png)

## 2. Get channel ID

In Discord, right-click the channel where messages should be sent and choose **Copy Channel ID**.

![discord_channel](/img/providers/notification/discord_channel.png)

## 3. Configure the provider in Casdoor

**Providers** → **Add**. Set **Category** to **Notification**, **Type** to **Discord**. Map:

| Casdoor    | Discord     |
|------------|-------------|
| Secret key | Bot token   |
| Chat ID    | Channel ID  |
| Content    | (optional)  |

![discord_provider](/img/providers/notification/discord_provider.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/web3/web3onboard.md
================================================================================

---
title: Web3-Onboard
description: Use Web3-Onboard to support multiple wallets for Web3 sign-in.
keywords: [Web3-Onboard, Web3, provider]
authors: [Chinoholo0807]
---

[Web3-Onboard](https://onboard.blocknative.com/) lets users pick from multiple wallets for Web3 login. Casdoor can use it as a Web3 identity provider.

![web3-onboard](/img/providers/web3/web3onboard.png)

## 1. Create the provider in Casdoor

**Providers** → **Add**. Set **Category** to **Web3**, **Type** to **Web3-Onboard**. In **Wallets**, select which wallets are allowed for sign-in. **Injected** covers browser wallets such as MetaMask and Coinbase Wallet.

![create a web3-onboard web3 provider](/img/providers/web3/web3onboard_provider_conf.png)

## 2. Add to your application

Add the Web3-Onboard provider to the application’s provider list.

![add the web3-onboard web3 provider to your application](/img/providers/web3/web3onboard_app_add.png)

## 3. Sign in with Web3-Onboard

Users choose a wallet and sign in. Demo:



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/web3/metamask.md
================================================================================

---
title: MetaMask Web3
description: Use MetaMask as a Web3 sign-in provider.
keywords: [MetaMask, Web3, provider]
authors: [Chinoholo0807]
---

[MetaMask](https://metamask.io/) is a wallet and gateway to dApps. Casdoor can use it as a Web3 identity provider for “Sign in with MetaMask”.

## 1. Create the provider in Casdoor

**Providers** → **Add**. Set **Category** to **Web3**, **Type** to **MetaMask**. No API keys required.

![Create a MetaMask Web3 provider](/img/providers/web3/metamask_provider_conf.png)

## 2. Add to your application

Add the MetaMask provider to the application’s provider list.

![Add the MetaMask Web3 provider to your application](/img/providers/web3/metamask_app_add.png)

## 3. Sign in with MetaMask

Users can sign in with MetaMask. Demo:



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/mfa/push.md
================================================================================

---
title: Push notification
description: Configure push notification provider for MFA
keywords: [Push Notification, MFA, provider, authentication]
authors: [nomeguy]
---

Push notification MFA enables users to receive verification codes through mobile push services during authentication. This method leverages Casdoor's existing notification provider infrastructure, supporting services like Duo, Pushover, Telegram, and 20+ other providers.

## Configure Notification Provider

Push notification MFA uses notification providers to send verification codes. To add a notification provider:

1. **Providers** → **Add**.
2. Set **Category** to **Notification** and **Type** to your preferred service (e.g. Telegram, Pushover, Custom HTTP).
3. Fill in the provider’s required settings.
4. Save.

## Use in Application

After creating the notification provider, add it to your application:

1. Edit the application and add the notification provider to its **Providers** list.
2. Users can then choose push notification as their MFA method.

## User Setup Flow

During MFA setup, users will:

1. Select "Use Push Notification" as their MFA method.

2. Enter their push notification receiver (device token or user ID).

3. Select the notification provider from the configured options.

4. Receive a verification code via push notification.

5. Enter the verification code to complete setup and receive recovery codes.

## Authentication Flow

When push notification MFA is enabled, users will receive a verification code via push notification during login. They must enter this code to complete authentication.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/mfa/radius.md
================================================================================

---
title: RADIUS MFA
description: Use an external RADIUS server as an MFA provider.
keywords: [RADIUS, MFA, provider, authentication]
authors: []
---

**RADIUS** (Remote Authentication Dial-In User Service) providers let Casdoor verify a second factor against your RADIUS server during MFA.

## Configure the provider

1. **Providers** → **Add**.
2. Set **Category** to **MFA**, **Type** to **RADIUS**.
3. Fill in:
   - **Host** — RADIUS server IP or hostname (e.g. `10.10.10.10`)
   - **Port** — RADIUS port (default `1812`)
   - **Client Secret** — Shared secret configured on the RADIUS server
4. Save.

## Use in an application

Add the RADIUS provider to your application’s provider list. Users can then choose RADIUS as their MFA method. During setup and sign-in, they enter their RADIUS username and password; Casdoor forwards the check to your RADIUS server.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/faceid/alibaba_cloud_facebody.md
================================================================================

---
title: Alibaba Cloud FaceBody
description: Use Alibaba Cloud FaceBody for face verification.
keywords: [Alibaba Cloud FaceBody, faceid]
authors: [dacongda]
---

Alibaba Cloud FaceBody provides face detection, comparison, and human-body detection via API. It is used for scenarios such as face AR, biometric auth, and photo management.

## 1. Register and enable FaceBody

Sign in at [Alibaba Cloud FaceBody](https://vision.aliyun.com/facebody) and open the service.

![alibaba_cloud_faceid_register.png](/img/providers/faceid/alibaba_cloud_faceid_register.png)

## 2. Purchase CompareFace resource pack

On the [Face Body console](https://vision.console.aliyun.com/cn-shanghai/detail/facebody), purchase a **CompareFace** resource pack.

## 3. Create AccessKey

In the Alibaba Cloud console, create an **AccessKey** and **AccessSecret**. Save both.

![alibaba_cloud_faceid_accesskey.png](/img/providers/faceid/alibaba_cloud_faceid_accesskey.png)
![alibaba_cloud_faceid_accesskey.png](/img/providers/faceid/alibaba_cloud_faceid_create_accesskey.png)

## 4. Get endpoint

Find the endpoint for your region in [Aliyun FaceBody docs](https://help.aliyun.com/document_detail/40654.html). Example: region `cn-shanghai` → endpoint `facebody.cn-shanghai.aliyuncs.com`.

## 5. Create the provider in Casdoor

**Providers** → **Add**. Set **Category** to **Face ID**, **Type** to **Alibaba Cloud FaceBody**. Enter **Client ID** (AccessKey ID), **Client Secret** (AccessSecret), and **Endpoint**. Save and add the provider to your application.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/faceid/overview.md
================================================================================

---
title: Face ID overview
description: Use Face ID as a sign-in method.
keywords: [faceid]
authors: [dacongda]
---

Casdoor supports Face ID as a sign-in method. Only enable it when you can ensure the hardware and requests are trusted and not tampered with.

## Add a Face ID provider

1. Open the Casdoor admin UI → **Providers** → **Add**.
2. Set **Category** to **Face ID**.
3. Choose the **Type** (e.g. Alibaba Cloud FaceBody).
4. Fill in the required fields (e.g. **Client ID**, **Client Secret**, **Endpoint** as needed) and save.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/email/azureACS.md
================================================================================

---
title: Azure Communication Services email
description: Use Azure Communication Services (ACS) as the email provider.
keywords: [email, Azure ACS, Communication Services]
authors: [UsherFall]
---

Use [Azure Communication Services](https://learn.microsoft.com/en-us/azure/communication-services/) for sending email. Complete:

- [Create and manage Email Communication Service](https://learn.microsoft.com/en-us/azure/communication-services/quickstarts/email/create-email-communication-resource)
- [Get a free Azure managed domain](https://learn.microsoft.com/en-us/azure/communication-services/quickstarts/email/add-azure-managed-domains) or [Add a custom domain](https://learn.microsoft.com/en-us/azure/communication-services/quickstarts/email/add-custom-verified-domains)
- [Connect domain](https://learn.microsoft.com/en-us/azure/communication-services/quickstarts/email/connect-email-communication-resource?pivots=azure-portal)

Copy your **Endpoint** and **Private Key** from the resource.

![azureACS_info](/img/providers/azureACS_info.png)

## Configure the provider in Casdoor

**Providers** → **Add**. Set **Category** to **Email**, **Type** to the option for Azure ACS. Map:

| Casdoor     | Azure ACS   |
|-------------|-------------|
| From Address| Verified sender (must use a verified domain) |
| Secret key  | Private Key  |
| Host        | Endpoint    |

:::note
**From Address** must use a verified email domain in ACS.
:::

![azureACS_provider](/img/providers/azureACS_provider.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/email/mailhog.md
================================================================================

---
title: MailHog email
description: Use MailHog as a local SMTP server for testing.
keywords: [email, mailhog]
authors: [Chinoholo0807]
---

[MailHog](https://github.com/mailhog/MailHog) is a test SMTP server that captures outgoing mail. Use your MailHog host and port (e.g. `192.168.24.128:1025`).

### 1. Run MailHog

Start the MailHog service so the SMTP server is reachable from Casdoor (e.g. `192.168.24.128`, port `1025`).

![MailHog configuration](/img/providers/mailhog_conf.png)

### 2. Create the email provider in Casdoor

**Providers** → **Add**. Set **Category** to **Email** and the type to the appropriate SMTP option. Set **Host** and **Port** to your MailHog address. No auth by default. Save.

![MailHog email provider](/img/providers/mailhog_email_provider_conf.png)

### 3. Test

Use **Test SMTP Connection**; you should see “SMTP connected successfully”. Use **Send Testing Email**; you should see “Email sent successfully” and the message in MailHog’s UI.

![Sending a test email using MailHog](/img/providers/mailhog_send_test_email.png)

![Receiving a test email using MailHog](/img/providers/mailhog_recv_test_email.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/email/mailpit.md
================================================================================

---
title: Mailpit email
description: Use Mailpit as a local SMTP server for testing.
keywords: [email, mailpit]
authors: [Attack825]
---

[Mailpit](https://github.com/axllent/mailpit) is a test SMTP server that catches outgoing mail. By default it listens on `127.0.0.1:1025` with no TLS or auth.

## 1. Run Mailpit

Start the Mailpit service so the SMTP server is available at `127.0.0.1:1025` (or your configured host/port).

![Mailpit configuration](/img/providers/mailpit_conf.png)

## 2. Create the email provider in Casdoor

**Providers** → **Add**. Set **Category** to **Email**, **Type** to the appropriate SMTP option. Set **Host** and **Port** to match Mailpit (e.g. `127.0.0.1`, `1025`). Leave **Username** and **Password** empty if Mailpit has no auth. Save.

![Mailpit email provider](/img/providers/mailpit_email_provider_conf.png)

## 3. Test

Use **Test SMTP Connection**; you should see “SMTP connected successfully”. Use **Send Testing Email**; you should see “Email sent successfully” and the message in Mailpit’s UI.

![Sending a test email using Mailpit](/img/providers/mailpit_send_test_email.png)
![Receiving a test email using Mailpit](/img/providers/mailpit_recv_test_email.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/email/brevo.md
================================================================================

---
title: Brevo email
description: Use Brevo (Sendinblue) as the SMTP provider for Casdoor.
keywords: [email, Brevo, SMTP]
authors: [UsherFall]
---

## 1. Enable Brevo SMTP

Activate SMTP for your Brevo account. See [Send transactional emails using Brevo SMTP](https://help.brevo.com/hc/en-us/articles/7924908994450). You may need to request activation via support.

![brevo_smtp](/img/providers/brevo_smtp.png)

## 2. Get SMTP settings

In the Brevo dashboard, open **SMTP & API** and note:

- **SMTP Server**
- **Port**
- **Login**
- **SMTP key** (password)

![brevo_conf](/img/providers/brevo_conf.png)

## 3. Configure the provider in Casdoor

Create an **Email** provider, set **Type** to the appropriate SMTP option, and enter **Host**, **Port**, **Username**, and **Password** (SMTP key). Set **From** to your verified sender.

![brevo_provider](/img/providers/brevo_provider.png)

- Use **Test SMTP Connection**; you should see “SMTP connected successfully”.
- Use **Send Testing Email**; you should see “Email sent successfully” and receive the test at the **Test Email** address.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/email/overview.md
================================================================================

---
title: Email provider overview
description: Configure SMTP for verification emails and password reset.
keywords: [email, SMTP, verification]
authors: [kininaru]
---

## Add an email provider

1. Click **Add** and choose **Email** under **Category**.
2. Enter **Username**, **Password**, **Host**, and **Port** for your SMTP server.
3. Set **Email Title** and **Email Content** (templates), then save.

![Email provider](/img/providers/emailprovider.png)
![Email Config](/img/providers/emailconfig.png)

## Proxy

If the Casdoor server cannot reach the SMTP server directly (e.g. Gmail from a restricted network), enable **Enable proxy**. Email is then sent via the SOCKS5 proxy defined in Casdoor’s config.

## Email content and placeholders

Templates support placeholders and the `<reset-link>` block for password reset.

| Placeholder | Description |
|-------------|-------------|
| **%{'{'}user.friendlyName{'}'}** | User’s display or friendly name. |
| **%s** | Verification code (for auth emails). |
| **%link** | Password reset URL. Use only inside `<reset-link>...</reset-link>`. |

### Password reset link

To let users reset the password by clicking a link in the email:

1. Put the link text and `%link` inside `<reset-link>` tags.
2. The block is shown only in password-reset emails; it is removed for signup/login verification.

**Plain text example:**

```text
You have requested a verification code at Casdoor. Here is your code: %s, please enter in 5 minutes. <reset-link>Or click %link to reset</reset-link>
```

**HTML example:**

```html
```

![Html template](/img/providers/email/email-template.png)

The `<reset-link>` block is omitted for non–password-reset emails (signup, login verification).



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/email/sendgrid.md
================================================================================

---
title: SendGrid email
description: Use SendGrid as an email provider for verification and notifications.
keywords: [email, SendGrid]
authors: [UsherFall]
---

## 1. Create an API key

In the [SendGrid](https://sendgrid.com/) dashboard, go to **Settings** → **API Keys**. Click **Create API Key** and set the permissions you need.

![sendgrid_apikey](/img/providers/sendgrid_apikey.png)

## 2. Verify sender

Verify your sender via **Single Sender Verification** or **Domain Authentication**. See [Sender Identity](https://docs.sendgrid.com/for-developers/sending-email/sender-identity).

## 3. Configure the provider in Casdoor

Create an **Email** provider, set **Type** to **SendGrid**, and fill in:

**Required**

| Field         | Description                    |
|---------------|--------------------------------|
| Secret Key    | Your SendGrid API key          |
| From Address  | Verified sender email or domain |

**Defaults** (can override)

| Field    | Default                     |
|----------|-----------------------------|
| Endpoint | `/v3/mail/send`             |
| Host     | `https://api.sendgrid.com`  |

**Optional**

| Field          | Description                    |
|----------------|--------------------------------|
| From Name      | Sender display name            |
| Email Title    | Subject                        |
| Email Content  | Body (HTML supported)          |
| Test Email     | Recipient for **Send Testing Email** |

![sendgrid_email_provider_fields](/img/providers/sendgrid_email_provider_fields.png)

Use **Send Testing Email** and check the **Test Email** inbox to confirm delivery.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/storage/synology-nas.md
================================================================================

---
title: Synology NAS storage
description: Use Synology NAS as a storage provider (S3-compatible).
keywords: [Synology, NAS, storage, provider]
authors: [xiao-kong-long]
---

Configure Synology NAS (or its S3-compatible API) as the backend. You need **Client ID**, **Client secret**, and **Endpoint** at minimum.

| Casdoor field | Synology / meaning | Required |
|---------------|--------------------|----------|
| Client ID     | SecretId (access key) | Yes   |
| Client secret | SecretKey          | Yes      |
| Endpoint      | S3 API endpoint    | Yes      |
| Bucket        | Bucket name        | No       |
| Path prefix   | Path prefix        | No       |
| Domain        | Custom domain      | No       |
| Region ID     | Region             | No       |

See [Synology developer documentation](https://www.synology.cn/zh-cn/support/developer#tool) for creating and configuring the S3-compatible endpoint and keys.

![synologyConfig.png](/img/providers/storage/synologyConfig.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/storage/azure.md
================================================================================

---
title: Azure Blob storage
description: Use Azure Blob Storage as a storage provider.
keywords: [Azure Blob, storage, provider]
authors: [sh1luo]
---

You need an [Azure Storage account](https://docs.microsoft.com/azure/storage/common/storage-account-create?tabs=azure-portal).

## 1. Select Azure Blob

In Casdoor **Providers** → **Add**, set **Category** to **Storage**, **Type** to **Azure Blob**.

![azureSelect.png](/img/providers/storage/azureSelect.png)

## 2. Map fields

| Casdoor field        | Azure / meaning        | Required |
|----------------------|------------------------|----------|
| Client ID            | AccountName            | Yes      |
| Client secret        | AccountKey             | Yes      |
| Endpoint             | ContainerUrl           | Yes      |
| Endpoint (intranet)  | PrivateEndpoint        | No       |
| Bucket               | ContainerName          | Yes      |
| Path prefix          | Path prefix            | No       |
| Domain               | Custom domain (e.g. CDN)| No      |

- **AccountName** — Storage account name.
- **AccountKey** — From Azure Portal → your storage account → **Access keys**.
- **ContainerUrl** — From the container’s properties.
- **PrivateEndpoint** — Optional; for [Azure Private Endpoint](https://learn.microsoft.com/azure/private-link/tutorial-private-endpoint-storage-portal).
- **ContainerName** — Container name (e.g. `default`).
- **Domain** — Optional custom domain (e.g. Azure CDN).

![azureKey.png](/img/providers/storage/azureKey.png)
![azureUrl.png](/img/providers/storage/azureUrl.png)
![azureContainer.png](/img/providers/storage/azureContainer.png)
![azureCDN.png](/img/providers/storage/azureCDN.png)

## 3. Save

Save the provider. Your application can use Azure Blob for file storage.

![azureResult.png](/img/providers/storage/azureResult.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/storage/minio.md
================================================================================

---
title: MinIO storage
description: Use MinIO as a Casdoor storage provider.
keywords: [MinIO, storage, provider, S3]
authors: [Chinoholo0807]
---

[MinIO](https://github.com/minio/minio) is S3-compatible object storage. Use it as a Casdoor storage provider for file uploads (e.g. avatars).

## 1. Deploy MinIO

Deploy MinIO with TLS enabled. From the MinIO console note the **API address**, create an **Access Key** and **Secret Key**, and create a **Bucket**.

![Deploy service](/img/providers/storage/minio_deploy.png)
![Create access key](/img/providers/storage/minio_create_key.png)
![Create bucket](/img/providers/storage/minio_create_bucket.png)

## 2. Add the provider in Casdoor

Create a **Storage** provider, set **Type** to **MinIO**, and fill in:

| Casdoor field   | Value from MinIO   |
|-----------------|--------------------|
| Client ID       | Access Key         |
| Client secret   | Secret Key         |
| Endpoint        | API address        |
| Bucket          | Bucket name        |

![Create a MinIO provider](/img/providers/storage/minio_provider_conf_detail.png)

## 3. Use in your application

Attach the provider to your application; uploads will go to MinIO.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/storage/tencentCloudCOS.md
================================================================================

---
title: Tencent Cloud COS
description: Use Tencent Cloud COS as a Casdoor storage provider.
keywords: [Tencent Cloud COS, storage, provider]
authors: [UsherFall]
---

## Field mapping

| Casdoor field   | Tencent Cloud     | Required |
|-----------------|-------------------|----------|
| Client ID       | SecretId          | Yes      |
| Client secret   | SecretKey         | Yes      |
| Endpoint        | Endpoint          | Yes      |
| Bucket          | BucketName        | Yes      |
| Region ID       | Region            | Yes      |
| Path prefix     | —                 | No       |
| Domain          | CDN domain        | No       |

Get **SecretId** and **SecretKey** from the [Tencent Cloud API Key](https://console.cloud.tencent.com/cam/capi) page. Get **Endpoint**, **BucketName**, and **Region** from your COS bucket settings.

![tencentKey.png](/img/providers/storage/tencentKey.png)
![tencentConfig.png](/img/providers/storage/tencentConfig.png)

Optional: use a custom CDN domain — see [Tencent COS CDN configuration](https://cloud.tencent.com/document/product/436/18670).

## Configure in Casdoor

Create a **Storage** provider, set **Type** to **Tencent Cloud COS**, and fill in the fields above.

![tencentResult.png](/img/providers/storage/tencentResult.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/storage/amazon-s3.md
================================================================================

---
title: Amazon S3 storage
description: Use Amazon S3 as a Casdoor storage provider.
keywords: [Amazon S3, storage, provider]
authors: [UsherFall]
---

Configure Casdoor to store files (e.g. avatars) in **Amazon S3**.

## 1. Create credentials

Create and save an **access key** and **secret access key** in the AWS console. See [Managing access keys](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html).

## 2. Configure the bucket

- In the bucket **Permissions**, turn off “Block all public access” (or configure a policy that allows Casdoor) and save.
- In **Object Ownership**, enable **ACLs** and set ownership as needed.

![uncheck block](/img/providers/storage/amazonNoBlock.png)
![check ACLs enabled](/img/providers/storage/amazonOwnership.png)

## 3. Add the provider in Casdoor

| Casdoor field    | In AWS / S3      | Required |
|------------------|-------------------|----------|
| Client ID        | Access key        | Yes      |
| Client secret    | Secret access key | Yes      |
| Endpoint         | Endpoint          | Yes      |
| Endpoint (intranet) | VPC endpoint   | No       |
| Bucket           | Bucket name       | Yes      |
| Path prefix      | —                 | No       |
| Domain           | CloudFront domain | No       |
| Region ID        | AWS region        | Yes      |

Endpoint format: [Website endpoints](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteEndpoints.html).

![Amazon S3 provider](/img/providers/storage/amazonProvider.png)

## Optional

- **VPC access**: [Access AWS services through AWS PrivateLink](https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-access-aws-services.html).
- **CloudFront**: [Create a distribution](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/GettingStarted.SimpleDistribution.html), then set **Domain** in the provider to the distribution domain.

![domain](/img/providers/storage/amazonCloudFront.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/storage/overview.md
================================================================================

---
title: Storage provider overview
description: Configure local or cloud storage for file uploads (e.g. avatars).
keywords: [storage, provider, S3, OSS, MinIO]
authors: [leo220yuyaodog]
---

Use a **Storage** provider when you need file storage (e.g. avatar uploads). Add the provider and attach it to your application. Casdoor supports **Local** (filesystem) and **Cloud** (object storage) types.

## Provider fields

| Field | Description |
|-------|-------------|
| **Client ID** | Identifier from the cloud storage provider. |
| **Client secret** | Secret shared with the storage service. |
| **Endpoint** | Public URL/domain of the storage service. |
| **Endpoint (Intranet)** | Internal/private URL for same-datacenter access. |
| **Path prefix** | Prefix for object keys (default `/`). With prefix `abcd/xxxx`, a file is stored at e.g. `https://cdn.example.com/abcd/xxxx/casdoor/avatar.png`. |
| **Bucket** | Bucket/container name. |
| **Domain** | Custom CDN domain for serving files. |
| **Region ID** | Data center region (for cloud providers). |

## Local storage

Files are stored on the server’s local filesystem.

## Cloud storage

Supported: **AWS S3**, **Azure Blob Storage**, **MinIO**, **Alibaba Cloud OSS**, **Tencent Cloud COS**. More providers may be added over time.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/storage/aliyun-oss.md
================================================================================

---
title: Alibaba Cloud OSS
description: Use Alibaba Cloud OSS as a Casdoor storage provider (static credentials or RRSA).
keywords: [Alibaba Cloud OSS, storage, RRSA, RAM]
authors: [leo220yuyaodog]
---

Casdoor supports **Alibaba Cloud OSS** with two auth options: **static credentials** (AccessKey) or **RRSA** (RAM Roles for Service Accounts) for environments that provide OIDC tokens (e.g. Alibaba Cloud ACK).

## Static credentials

1. Create an AccessKey in the [Alibaba Cloud console](https://help.aliyun.com/document_detail/53045.html).
2. In Casdoor, create a **Storage** provider, set **Type** to **Alibaba Cloud OSS**, and fill **Client ID** (AccessKey ID), **Client secret** (AccessKey Secret), **Endpoint**, **Bucket**, and **Region** as needed.

![Create OSS](/img/providers/createaliyunoss.png)
![OSS](/img/providers/storage/oss.png)

## RRSA (no long-term credentials)

In environments that provide OIDC tokens (e.g. ACK with RRSA), set these environment variables from your [RAM console](https://ram.console.aliyun.com/):

```bash
ALIBABA_CLOUD_ROLE_ARN=acs:ram::YOUR_ACCOUNT_ID:role/YOUR_ROLE_NAME
ALIBABA_CLOUD_OIDC_PROVIDER_ARN=acs:ram::YOUR_ACCOUNT_ID:oidc-provider/YOUR_PROVIDER_NAME
ALIBABA_CLOUD_OIDC_TOKEN_FILE=/var/run/secrets/tokens/oidc-token
```

In the Casdoor storage provider, leave **Client ID** and **Client secret** empty. Casdoor will use the OIDC token to obtain temporary credentials. If RRSA is unavailable, it falls back to static credentials.

:::tip
For production on Alibaba Cloud ACK, RRSA is recommended: no stored secrets and short-lived tokens.
:::



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/storage/localFileSystem.md
================================================================================

---
title: Local file system storage
description: Store uploaded files on the Casdoor server’s filesystem.
keywords: [Local File System, storage, provider]
authors: [UsherFall]
---

The **Local File System** provider stores uploads in the Casdoor `files` directory. For example, if Casdoor is at `/home/user/casdoor`, files are stored under `/home/user/casdoor/files`.

## Configure the provider

![Local File configuration](/img/providers/storage/localFileConfig.png)

**Path prefix** — Optional prefix for object paths. With a prefix, files are stored under that subpath.

### With prefix

![With prefix configuration](/img/providers/storage/localFileWithPre.png)
![Files with prefix](/img/providers/storage/localFileWithResult.png)

### Without prefix

![Without prefix configuration](/img/providers/storage/localFileWithoutPre.png)
![Files without prefix](/img/providers/storage/localFileWithoutResult.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/storage/google-cloudstorage.md
================================================================================

---
title: Google Cloud Storage
description: Use Google Cloud Storage as a storage provider.
keywords: [Google Cloud Storage, storage, provider]
authors: [sp71]
---

## 1. Create credentials in GCP

Create a [service account](https://cloud.google.com/iam/docs/keys-create-delete) with [IAM permissions](https://cloud.google.com/storage/docs/access-control/iam-permissions) for your bucket. See [Cloud Storage authentication](https://cloud.google.com/storage/docs/authentication?hl=en#service_accounts). Download the **service account key** (JSON).

## 2. Configure the provider in Casdoor

**Providers** → **Add**. Set **Category** to **Storage**, **Type** to **Google Cloud Storage**. Fill in:

| Casdoor field       | GCP / meaning       | Required |
|---------------------|---------------------|----------|
| Service Account JSON| Service account key (JSON content) | Yes |
| Endpoint            | Endpoint (optional) | No       |
| Bucket              | Bucket name         | Yes      |

![Google Cloud Storage provider](/img/providers/storage/googleProvider.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/payment/paypal.md
================================================================================

---
title: PayPal payment
description: Use PayPal as a payment provider in Casdoor.
keywords: [PayPal, payment]
authors: [Chinoholo0807]
---

## 1. Create a PayPal app

You need a **PayPal business account**. [Create one](https://www.paypal.com/in/webapps/mpp/account-selection?pros=2) if needed, then sign in to the [Developer Dashboard](https://developer.paypal.com/dashboard/applications/sandbox) and click **Create App** under **Apps & Credentials**.

Copy the **Client ID** and **Secret** from the app’s basic information.

![create a PayPal application](/img/providers/payment/paypal_create_app.png)
![PayPal application details](/img/providers/payment/paypal_app_detail.png)

## 2. Create the provider in Casdoor

Add a **Payment** provider, set **Type** to **PayPal**, and enter the **Client ID** and **Secret** (Client secret).

## 3. Attach to your product

Add the PayPal provider to your product so users can pay with PayPal.

![add PayPal payment provider for product](/img/providers/payment/paypal_product.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/payment/dummy.md
================================================================================

---
title: Dummy payment
description: Mock payment provider for testing and development.
keywords: [Dummy, payment, testing, development]
authors: [hsluoyz]
---

The **Dummy** provider simulates payment: no real gateway is called. Use it to test the purchase flow before going live.

**Behavior:** A purchase with Dummy is marked successful immediately and the user is redirected to the result page. No money is charged.

## Create the provider

**Providers** → **Add**. Set **Category** to **Payment**, **Type** to **Dummy**. No API keys or secrets are required.

## Use in a product

Add the Dummy provider to the product so test users can complete “purchases.” For production, replace it with a real provider (e.g. Stripe or PayPal).



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/payment/WeChatPay.md
================================================================================

---
title: WeChat Pay
description: Use WeChat Pay as a payment provider in Casdoor.
keywords: [WeChat Pay, payment]
authors: [Wrapping-2000, Chinoholo0807]
---

You need a [WeChat Merchant](https://pay.weixin.qq.com/index.php/public/wechatpay_en) account. See [preparation before access](https://pay.weixin.qq.com/docs/merchant/products/native-payment/preparation.html).

## 1. Get credentials

### API Key v3

In WeChat Merchant Platform: **Account Settings** → **API Security** → **Set APIv3 Secret**. Copy the **API Key v3**. See [APIv3 Key Settings](https://kf.qq.com/faq/180830E36vyQ180830AZFZvu.html).

![wechat api key v3](/img/providers/payment/wechat_apikey_v3.png)

### Merchant certificate

**Account Settings** → **API Security** → **API Certificate** → download the certificate. Get the [Certificate Serial Number](https://pay.weixin.qq.com/wiki/doc/apiv3/wechatpay/wechatpay7_0.shtml#part-5) and [Private Key](https://pay.weixin.qq.com/wiki/doc/apiv3/wechatpay/wechatpay3_1.shtml). In Casdoor, create a **Cert** and fill in the certificate details.

![wechat merchant certificate](/img/providers/payment/wechat_mch_cert.png)
![wechat_cert](/img/providers/payment/wechat_cert.png)

### Merchant ID and App ID

- [Merchant ID](https://kf.qq.com/faq/200729EZ7fEj200729aumYR7.html)
- [App ID](https://pay.weixin.qq.com/static/pay_setting/appid_protocol.shtml)

## 2. Create the provider in Casdoor

Add a **Payment** provider, set **Type** to **WeChat Pay**, and fill in:

| Casdoor field   | Value           |
|-----------------|-----------------|
| Client ID       | Merchant ID     |
| Client secret   | API Key v3      |
| App ID          | App ID          |
| Cert            | The Cert above  |

![wechat pay provider](/img/providers/payment/wechat_payment_provider.png)

## 3. Attach to your product

Add the WeChat Pay provider to your product so users can pay with WeChat Pay.

![add wechat pay payment provider for product](/img/providers/payment/wechat_product.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/payment/Balance.md
================================================================================

---
title: Balance payment
description: Let users pay with their Casdoor account balance (wallet).
keywords: [Balance, payment, wallet]
authors: [hsluoyz]
---

The **Balance** payment provider lets users pay for products from their account balance instead of an external gateway. Casdoor deducts the price from the user’s balance; no redirect to a third party.

Users need sufficient balance before they can pay. Create a **recharge** product (enable **Is recharge**) and attach external providers (e.g. Stripe, PayPal). When users buy that product, the amount is added to their balance. Then they can use **Balance** to pay for other products.

## Create the provider

In Casdoor **Providers** → **Add**:

| Field    | Value        |
|----------|--------------|
| Category | **Payment**  |
| Type     | **Balance**  |

No Client ID or secret; Balance uses the built-in user balance.

## Use in products

Add the Balance provider to your product’s payment provider list. Users will see “Balance” at checkout when they have enough funds.

Typical setup: one recharge product (Stripe/PayPal) so users can top up, and regular products that accept Balance so users can pay from their wallet without re-entering payment details.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/payment/stripe.md
================================================================================

---
title: Stripe payment
description: Use Stripe as a payment provider in Casdoor.
keywords: [Stripe, payment]
authors: [Chinoholo0807]
---

## 1. Get API keys

Create an account at [Stripe](https://www.stripe.com/) and open the [Developer Dashboard](https://dashboard.stripe.com/test/apikeys). Under **API keys**, copy the **Publishable key** and **Secret key**.

![Stripe API keys](/img/providers/payment/stripe_api_keys.png)

## 2. Create the provider in Casdoor

Add a **Payment** provider, set **Type** to **Stripe**, and fill in:

| Casdoor field   | Value              |
|-----------------|--------------------|
| Client ID       | Publishable key    |
| Client secret   | Secret key         |

![Stripe provider](/img/providers/payment/stripe_provider.png)

## 3. Attach to your product

Add the Stripe provider to your product so users can pay with Stripe.

![Add Stripe payment provider for product](/img/providers/payment/stripe_product.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/payment/Adyen.md
================================================================================

---
title: Adyen
description: Use Adyen as a payment provider for online, mobile, and in-store.
keywords: [Adyen, payment]
authors: [hsluoyz]
---

[Adyen](https://www.adyen.com/) provides a unified payment platform with fraud protection and global acquiring.

## 1. Get credentials

Sign in to the [Adyen Customer Area](https://www.adyen.com/). Under **Developers** → **API credentials**, create a web service API credential and generate an API key with payment permissions. Note your **merchant account name** (from the credential or dashboard). Copy the API key and merchant account name.

## 2. Create the provider in Casdoor

**Providers** → **Add**. Set **Category** to **Payment**, **Type** to **Adyen**. Map:

| Casdoor        | Adyen                |
|----------------|----------------------|
| Client ID 2    | Merchant account name|
| Client secret  | API key              |

**Client ID** is not used for Adyen.

## 3. Attach to a product

Add the Adyen provider to the product in Casdoor. Checkout redirects users to Adyen’s hosted page. Payments are created dynamically; Adyen supports cards, digital wallets, and local methods based on your account.

:::note
Test vs live is determined by Casdoor’s `runmode` in `conf/app.conf`. Use test API credentials in development.
:::



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/payment/Polar.md
================================================================================

---
title: Polar
description: Use Polar as a payment provider for digital products and subscriptions.
keywords: [Polar, payment]
authors: [hsluoyz]
---

[Polar](https://polar.sh/) provides checkout for developers and creators, with subscriptions, one-time payments, and licensing.

## 1. Get access token

Sign in at [Polar](https://polar.sh/). Open **Settings** → [Personal Access Tokens](https://polar.sh/settings) and create a token with permissions for checkouts and payments. Copy the token.

## 2. Create the provider in Casdoor

**Providers** → **Add**. Set **Category** to **Payment**, **Type** to **Polar**. Put the access token in **Client secret**. **Client ID** is not used for Polar.

## 3. Attach to a product

Add the Polar provider to the product in Casdoor. Users are redirected to Polar for checkout and returned to your app when payment completes or is cancelled.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/payment/AirWallex.md
================================================================================

---
title: AirWallex
description: Use AirWallex as a payment provider.
keywords: [AirWallex, payment]
authors: [Cutsin]
---

## 1. Get credentials

Create an account at [AirWallex](https://www.airwallex.com/) and sign in to the [Developer Dashboard](https://www.airwallex.com/app/account/apiKeys). Under **API Keys**, copy **CLIENT ID** and **API KEY** (or create a new custom permission key).

![AirWallex API Keys](/img/providers/payment/airwallex_api_keys.png)

## 2. Create the provider in Casdoor

**Providers** → **Add**. Set **Category** to **Payment**, **Type** to **AirWallex**. Map:

| Casdoor       | AirWallex   |
|---------------|-------------|
| Client ID     | CLIENT ID   |
| Client secret | API KEY     |

![AirWallex provider](/img/providers/payment/airwallex_provider.png)

## 3. Attach to a product

Add the AirWallex provider to the product so users can pay with AirWallex.

![Add AirWallex payment provider for product](/img/providers/payment/airwallex_product.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/payment/Paddle.md
================================================================================

---
title: Paddle
description: Use Paddle as a payment provider for digital products and subscriptions.
keywords: [Paddle, payment]
authors: [hsluoyz]
---

[Paddle](https://www.paddle.com/) handles payments, tax, and subscriptions for digital products.

## 1. Get API key

Sign in at [Paddle](https://www.paddle.com/). In [Developer Tools → Authentication](https://sandbox-vendors.paddle.com/authentication-v2), create an API key with permission to create transactions. Copy the key.

## 2. Create the provider in Casdoor

**Providers** → **Add**. Set **Category** to **Payment**, **Type** to **Paddle**. Put the API key in **Client secret**. **Client ID** is not used for Paddle.

## 3. Attach to a product

Add the Paddle provider to the product in Casdoor. Checkout redirects users to Paddle. Paddle creates transactions dynamically; you do not need to pre-create products in Paddle.

:::note
Sandbox vs production is determined by Casdoor’s `runmode` in `conf/app.conf`.
:::



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/payment/overview.md
================================================================================

---
title: Payment provider overview
description: Add payment providers so users can pay for products.
keywords: [Payment, product]
authors: [Chinoholo0807]
---

To accept payments in Casdoor, create **Payment** providers and attach them to your [products](/docs/products/product). Users can then choose a payment method when purchasing.

![Add payment provider](/img/providers/payment/add_payment_provider.png)

After configuring a product, add one or more Payment providers to it so users can complete purchases through those providers.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/payment/LemonSqueezy.md
================================================================================

---
title: Lemon Squeezy
description: Use Lemon Squeezy as a payment provider for subscriptions and one-time purchases.
keywords: [Lemon Squeezy, payment]
authors: [hsluoyz]
---

[Lemon Squeezy](https://www.lemonsqueezy.com/) handles payments, subscriptions, and tax for software and digital products.

## 1. Get credentials

In the [Lemon Squeezy](https://www.lemonsqueezy.com/) dashboard: **Settings** → **API** to create an **API key**. In store settings, note your **Store ID**. Keep both for the next step.

## 2. Create the provider in Casdoor

**Providers** → **Add**. Set **Category** to **Payment**, **Type** to **Lemon Squeezy**. Map:

| Casdoor       | Lemon Squeezy |
|---------------|----------------|
| Client ID     | Store ID       |
| Client secret | API Key        |

## 3. Attach to a product

Add this provider to the product in Casdoor. Set the product’s **name** (or identifier) to the **Variant ID** from the Lemon Squeezy product. Checkout redirects users to Lemon Squeezy.

:::tip
Configure webhooks in the Lemon Squeezy dashboard for reliable payment status. Without webhooks, status is inferred from checkout expiry.
:::



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/payment/Alipay.md
================================================================================

---
title: Alipay
description: Add Alipay payment provider to your application
keywords: [Alipay, payment]
authors: [Chinoholo0807]
---

## Step 1. Preparation

You need a merchant account at [Alipay Open Platform](https://open.alipay.com/).

Before accessing the Alipay, there are some preparations that need to be done.

See [preparation before access](https://opendocs.alipay.com/open/270/01didh).

### 1.1 Get APPID

Login the Alipay Open Platform Console and [create an application](https://opendocs.alipay.com/open/200/105310).

How to get the `APPID` : [Alipay APPID Query Guide](https://opendocs.alipay.com/common/02nebp)

### 1.2 Configure Cert

Generate an RSA2 certificate per the [Alipay doc](https://opendocs.alipay.com/common/056zub?pathHash=91c49771) to obtain `appPrivateKey.txt` and `appPublicKey.txt`.

Upload the certificate to the application and download three files: `alipayRootCert.crt`, `appCertPublicKey.crt`, `alipayCertPublicKey.crt`.

Create a Cert named **App Cert** in Casdoor:

| Casdoor        | Value |
|----------------|--------|
| Type           | Payment (x509) |
| Certificate    | content of `appCertPublicKey.crt` |
| Private key    | content of `appPrivateKey.txt` |

![alipay app cert](/img/providers/payment/alipay_app_cert.png)

Create a Cert named **Root Cert** in Casdoor:

| Casdoor        | Value |
|----------------|--------|
| Type           | Payment (x509) |
| Certificate    | content of `alipayCertPublicKey.crt` |
| Private key    | content of `alipayRootCert.crt` |

![alipay root cert](/img/providers/payment/alipay_root_cert.png)

## Step 2.  Create an Alipay Payment provider

Next, create an Alipay Payment provider in Casdoor by filling in the necessary information.

| Casdoor   | Value |
|-----------|--------|
| Category  | Payment |
| Type      | Alipay |
| Client ID | APPID from step 1.1 |
| Cert      | App Cert from step 1.2 |
| Root Cert | Root Cert from step 1.2 |

![alipay provider](/img/providers/payment/alipay_provider.png)

## Step 3. Add the Alipay Pay Payment provider for your product

Finally, add the Alipay Payment provider for your product so that users can purchase the product using Alipay.

:::info Currency Requirement

Alipay only supports transactions in Chinese Yuan (CNY). When adding Alipay as a payment provider, ensure your product's currency is set to CNY. Products with other currencies will be rejected during creation or update to prevent payment failures.

:::

![add wechat pay payment provider for product](/img/providers/payment/alipay_product.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/payment/FastSpring.md
================================================================================

---
title: FastSpring
description: Use FastSpring as a payment provider for digital products and subscriptions.
keywords: [FastSpring, payment]
authors: [hsluoyz]
---

[FastSpring](https://fastspring.com/) handles payments, subscriptions, and tax for software and digital products.

## 1. Get credentials

Sign in at [FastSpring](https://fastspring.com/). Go to **Developer** → **API Credentials** and note your **API Username** and **API Password**. Note your storefront host (e.g. `yourcompany.onfastspring.com`).

## 2. Create the provider in Casdoor

**Providers** → **Add**. Set **Category** to **Payment**, **Type** to **FastSpring**. Fill in:

| Casdoor       | FastSpring        |
|---------------|-------------------|
| Client ID     | API Username      |
| Client secret | API Password      |
| Host          | Storefront host (e.g. `mycompany.onfastspring.com`) |

## 3. Attach to a product

Add the FastSpring provider to the product in Casdoor. Users are redirected to FastSpring for checkout and returned to your app after payment.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/idv/overview.md
================================================================================

---
title: ID verification provider overview
description: Verify user identity via third-party ID verification (KYC) providers.
keywords: [ID Verification, identity, verification, KYC]
authors: [hsluoyz]
---

**ID Verification** providers let users prove their identity (e.g. ID document + real name) through a third-party service. Once verified, the account is marked verified and sensitive fields are locked.

## How it works

1. Users fill in their ID card information (type and number) and real name in their account settings
2. They click the "Verify Identity" button to initiate verification
3. The configured ID Verification provider validates the submitted information
4. Upon successful verification, the user's account is marked as verified and sensitive fields are locked

Once verified, users cannot modify their real name, ID card type, ID card number, or related identity information, ensuring data integrity and preventing fraud.

## Add a provider

1. **Providers** → **Add**.
2. Set **Category** to **ID Verification**, choose the **Type**, enter credentials, and save.

After creating the provider, add it to your application's provider list so users can access the verification feature.

## Configuring Account Fields

For users to access verification, configure the relevant account fields in your organization:

1. Go to **Organizations** and edit your organization
2. In the **Account items** section, ensure these fields are properly configured:
   - **ID card type** - Should be visible so users can select their ID type
   - **ID card** - Should be visible for users to enter their ID number
   - **Real name** - Should be visible and modifiable by users before verification
   - **ID verification** - Controls who can see and use the verify button

The typical configuration sets these fields with "Public" view rule and "Self" modify rule, allowing users to manage their own identity information while keeping it visible to the system.

See [Account customization](/docs/organization/accountCustomization) for field configuration.

## User Verification

Users can verify their identity from their account page. The verification button appears when:

- The user has filled in their ID card type, ID card number, and real name
- The user hasn't been verified yet
- An ID Verification provider is configured in their application

After verification, these fields become read-only and a verification badge appears on their profile.

## API Integration

Identity verification is available through the `/api/verify-identification` endpoint. The API supports:

- Self-verification: Users can verify themselves without additional parameters
- Admin verification: Admins can verify other users by providing owner and name parameters
- Provider selection: Optionally specify which provider to use for testing purposes

The verification status is reflected in the user's `isVerified` field and `realName` is included in JWT tokens and OIDC userinfo responses.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/idv/jumio.md
================================================================================

---
title: Jumio ID verification
description: Use Jumio as an ID verification (KYC) provider in Casdoor.
keywords: [Jumio, ID Verification, identity, KYC]
authors: [hsluoyz]
---

[Jumio](https://www.jumio.com/) verifies government-issued IDs and supports KYC flows. Configure it as an **ID Verification** provider in Casdoor.

## Prerequisites

You need:

- A Jumio account with API access
- API credentials (Client ID and Client Secret)
- Your Jumio API endpoint URL

If you don't have a Jumio account, visit [jumio.com](https://www.jumio.com/) to sign up.

## Configuration

### 1. Get Jumio credentials

In the Jumio dashboard, open the API credentials section. Note your **API Token** (Client ID), **API Secret** (Client Secret), and **API endpoint URL** (e.g. `https://api.jumio.com`).

### 2. Create the provider in Casdoor

**Providers** → **Add**. Set **Category** to **ID Verification**, **Type** to **Jumio**, and fill in:
- **Client ID** — Jumio API Token  
- **Client Secret** — Jumio API Secret  
- **Endpoint** — Jumio API URL  

Save the provider.

### 3. Add to your application

Edit the application, add the Jumio provider in the Providers section, and save.

## How Verification Works

When a user initiates identity verification:

1. Casdoor calls the Jumio API with the user's ID information
2. Jumio initiates a verification transaction and returns a transaction reference
3. The user completes the verification workflow (in production scenarios, this involves document upload and selfie capture)
4. Jumio validates the submitted documents against the provided information
5. Upon successful verification, the user's account is marked as verified in Casdoor

## Testing the Provider

You can test your Jumio configuration from the provider edit page:

1. Ensure you have ID card information and real name filled in your user profile
2. Navigate to the provider edit page
3. Use the test functionality to verify that the provider is properly configured
4. Check the response to confirm successful API communication

## Important Notes

- Verification is a one-time process per user. Once verified, users cannot modify their identity information
- The current implementation initiates the verification workflow through Jumio's API v4
- For production deployments, ensure your Jumio account has sufficient API call quotas
- All verification attempts are logged for audit purposes



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/idv/alibaba-cloud.md
================================================================================

---
title: Alibaba Cloud
description: Integrate Alibaba Cloud for ID card verification
keywords: [Alibaba Cloud, ID Verification, identity, KYC]
authors: [hsluoyz]
---

Alibaba Cloud (Aliyun) offers a financial-grade ID verification service that specializes in validating national ID cards. This service verifies whether the provided ID number matches the real name through government databases, making it ideal for applications serving users.

## Getting Started

You need an Alibaba Cloud account with the ID Verification (Real Person Verification) service enabled. Register at [aliyun.com](https://www.aliyun.com/) if needed.

To get credentials: log in to the Alibaba Cloud console → AccessKey management → create an AccessKey pair (Access Key ID and Secret Access Key). Enable the Real Person Verification service for your account.

The service uses the [Id2MetaVerify API](https://help.aliyun.com/zh/id-verification/financial-grade-id-verification/server-side-integration-2) to verify ID cards against government records.

## Configuration

Create a new provider in Casdoor:

1. Go to **Providers** and click **Add**
2. Set **Category** to "ID Verification"
3. Select **Type** as "Alibaba Cloud"
4. Fill in the credentials:
   - **Access key**: Your Alibaba Cloud Access Key ID
   - **Secret access key**: Your Alibaba Cloud Secret Access Key
   - **Endpoint**: Leave empty to use the default (`cloudauth.cn-shanghai.aliyuncs.com`) or specify a custom endpoint
5. Save and add the provider to your application

## Usage

When users verify their identity, Casdoor submits their ID card number and real name to Alibaba Cloud. The service checks whether these details match the records in national ID database.

Verification succeeds when:

- The ID card number format is valid
- The ID card exists in the government database  
- The provided name matches the registered name for that ID card

After successful verification, the user's identity fields are locked and cannot be changed.

## Requirements

- Users must have valid national ID cards (supports both 15-digit and 18-digit ID numbers)
- Both the ID card number and real name fields must be filled in before verification
- Your Alibaba Cloud account must have sufficient API call quotas

## Testing

Test your configuration from the provider edit page in Casdoor. Make sure to use valid test credentials provided by Alibaba Cloud to avoid consuming your production quota during development.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/captcha/default.md
================================================================================

---
title: Default captcha
description: Use Casdoor’s built-in image captcha (digit sequence).
keywords: [captcha, default]
authors: [Resulte]
---

The **Default** captcha type shows an image containing a sequence of digits (0–9), 5 characters long, and verifies the user’s answer.

## Configure in Casdoor

1. **Providers** → **Add** → set **Category** to **Captcha**, **Type** to **Default**.
2. Use **Preview** to check the captcha style.

![Default provider](/img/providers/captcha/default_provider.png)
![Default preview](/img/providers/captcha/default_preview.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/captcha/cloudflareTurnstile.md
================================================================================

---
title: Cloudflare Turnstile
description: Add Cloudflare Turnstile captcha to your application.
keywords: [Cloudflare Turnstile, captcha]
authors: [YiNNx]
---

[Cloudflare Turnstile](https://developers.cloudflare.com/turnstile/) is a privacy-friendly captcha alternative. Use it as a Casdoor captcha provider.

## Create a key pair

1. [Create a Cloudflare account](https://dash.cloudflare.com/?to=/:account/turnstile) and open the **Turnstile** tab.
2. Add a widget name and your site’s hostname, choose a widget type (e.g. **Managed**), and click **Create**.
3. Copy the **Site Key** and **Secret Key**.

![Cloudflare Turnstile preview](/img/providers/captcha/captcha_cloudflare1.png)
![Cloudflare Turnstile preview](/img/providers/captcha/captcha_cloudflare2.png)

## Configure in Casdoor

Create a **Captcha** provider, set **Type** to **Cloudflare Turnstile**, and enter the site key and secret key. Use **Preview** to check the captcha.

![Cloudflare Turnstile provider](/img/providers/captcha/captcha_cloudflare3.png)
![Cloudflare Turnstile preview](/img/providers/captcha/captcha_cloudflare4.png)

## Use in an application

Edit the application, add the Cloudflare Turnstile provider, and save.

![Cloudflare Turnstile provider app](/img/providers/captcha/captcha_cloudflare5.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/captcha/aliyunCaptcha.md
================================================================================

---
title: Alibaba Cloud Captcha
description: Add Alibaba Cloud Captcha to your application
keywords: [Alibaba Cloud Captcha]
authors: [Resulte]
---

Alibaba Cloud Captcha is a captcha service provided by Alibaba Cloud. It offers two ways to verify captcha: "Sliding Validation" and "Intelligent Validation". See [Alibaba Cloud Captcha](https://help.aliyun.com/product/28308.html) for details.

## Add Captcha Configuration in Alibaba Cloud

To add the Captcha configuration, log in to the [Alibaba Cloud management console](https://account.aliyun.com/), search for and go to the Captcha Service. Then, click on **Confirm Open** to enable the Captcha Service.

![Alibaba Cloud Captcha console open](/img/providers/captcha/aliyunCaptcha_console_open.png)

Once you have entered the Captcha management console, click on **Add configuration**.

![Alibaba Cloud Captcha console open](/img/providers/captcha/aliyunCaptcha_console_add.png)

Fill in all the required information and submit the form.

![Alibaba Cloud Captcha console open](/img/providers/captcha/aliyunCaptcha_console_add_form.png)

View the `Scene` and `App key` in your console.

![Alibaba Cloud Captcha console open](/img/providers/captcha/aliyunCaptcha_console_info.png)

![Alibaba Cloud Captcha console open](/img/providers/captcha/aliyunCaptcha_console_info2.png)

Also, the `Access key` and `Secret access key` can be found in your profile.

## Configure in Casdoor

Create a new provider in Casdoor.

Set **Category** to **Captcha**, **Type** to **Alibaba Cloud Captcha**. Choose the sub-type: "Sliding Validation" or "Intelligent Validation". Make sure to fill in the `Access key`, `Secret access key`, `Scene`, and `App key` that you created in the previous step.

![Alibaba Cloud Captcha provider](/img/providers/captcha/aliyunCaptcha_provider.png)

Use **Preview** to check the captcha style.

The following image shows the preview of "Sliding Validation":

![Alibaba Cloud Captcha preview](/img/providers/captcha/aliyunCaptcha_nc_preview.png)

And this image shows the preview of "Intelligent Validation":

![Alibaba Cloud Captcha preview](/img/providers/captcha/aliyunCaptcha_ic_preview.png)

## Application Integration

Edit the application in which you want to configure Casdoor. Select the newly added provider and click on the **Save** button.

![Alibaba Cloud Captcha provider app](/img/providers/captcha/aliyunCaptcha_provider_app.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/captcha/overview.md
================================================================================

---
title: Captcha provider overview
description: Add captcha to sign-in, sign-up, and password reset.
keywords: [captcha, reCAPTCHA, Turnstile, hCaptcha]
authors: [Resulte]
---

Casdoor can require a **captcha** before sending verification codes (sign-in, sign-up, forgot password). Add a captcha provider and attach it to your application; you can then choose when the captcha is shown.

Supported providers: **Default**, **Cloudflare Turnstile**, **reCAPTCHA**, **hCaptcha**, **Alibaba Cloud Captcha**, **Geetest**.

| Default | Cloudflare Turnstile | reCAPTCHA | hCaptcha | Alibaba Cloud | Geetest |
|---------|----------------------|-----------|----------|---------------|---------|
| <img src="https://cdn.casbin.org/img/social_default.png" width="40" /> | <img src="https://cdn.casbin.org/img/social_cloudflare.png" width="40" /> | <img src="https://cdn.casbin.org/img/social_recaptcha.png" width="40" /> | <img src="https://cdn.casbin.org/img/social_hcaptcha.png" width="40" /> | <img src="https://cdn.casbin.org/img/social_aliyun.png" width="40" /> | <img src="https://cdn.casbin.org/img/social_geetest.png" width="40" /> |

## Add a captcha provider

1. Go to **Providers** → **Add** → select the new provider.
2. Set **Category** to **Captcha** and **Type** to the provider you want.
3. Fill in the required fields (varies by provider) and save.

## Use in an application

1. Open **Applications** → select an application → add the captcha provider.
2. Set the **Provider rule** for when captcha is shown:
   - **None** — Captcha disabled (no verification).
   - **Dynamic** — Show captcha after 5 failed login attempts.
   - **Always** — Require captcha on every login.
   - **Internet-Only** — Show captcha only for requests from the public internet.

![Default provider app](/img/providers/captcha/default_provider_app.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/captcha/recaptcha.md
================================================================================

---
title: reCAPTCHA
description: Add Google reCAPTCHA v2 Checkbox to your application.
keywords: [reCAPTCHA, captcha]
authors: [Resulte]
---

Casdoor uses **reCAPTCHA v2 Checkbox** from Google. See [reCAPTCHA docs](https://developers.google.com/recaptcha) and [verify API](https://developers.google.com/recaptcha/docs/verify).

## Create an API key pair

1. [Register](http://www.google.com/recaptcha/admin) a reCAPTCHA key pair for your site (site key + secret key).
2. Choose the [reCAPTCHA type](https://developers.google.com/recaptcha/docs/versions) and add authorized domains or [package names](https://developer.android.com/guide/topics/manifest/manifest-element#package).
3. Accept the terms and click **Register** to get the **site key** and **secret key**.

![reCAPTCHA create apiKey](/img/providers/captcha/recaptcha_create_apiKey.png)
![reCAPTCHA apiKey](/img/providers/captcha/recaptcha_apikey.png)

## Configure in Casdoor

Create a **Captcha** provider, set **Type** to **reCAPTCHA**, and enter the site key and secret key. Use **Preview** to check the captcha.

![reCAPTCHA provider](/img/providers/captcha/recaptcha_provider.png)
![reCAPTCHA preview](/img/providers/captcha/recaptcha_preview.png)

## Use in an application

Edit the application, add the reCAPTCHA provider, and save.

![reCAPTCHA provider app](/img/providers/captcha/recaptcha_provider_app.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/captcha/geetest.md
================================================================================

---
title: Geetest captcha
description: Add Geetest CAPTCHA V4 to your application.
keywords: [Geetest, captcha]
authors: [leoil]
---

## 1. Get Geetest keys

1. Open [Geetest CAPTCHA V4](https://auth.geetest.com/product) and create a product/app.
2. Enter application name and address; add events and choose **web** as the device.
3. Copy the **ID** and **Key** (site key and secret key).

![Configure Geetest product](/img/providers/captcha/geetest_product.png)
![Geetest application](/img/providers/captcha/geetest_create_application.png)
![Geetest event](/img/providers/captcha/geetest_add_events.png)
![Configure Geetest key](/img/providers/captcha/geetest_key.png)

## 2. Configure Casdoor

**Providers** → **Add**. Set **Category** to **Captcha**, **Type** to **Geetest**. Enter the ID as **Site key** and the Key as **Secret key**. Use **Preview** to check the captcha style.

![Configure app provider](/img/providers/captcha/geetest_casdoor_configure.gif)

## 3. Apply to an application

Edit the application in Casdoor, add the Geetest provider to its provider list, and save.

![Configure app provider](/img/providers/captcha/geetest_app_provider.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/captcha/hcaptcha.md
================================================================================

---
title: hCaptcha
description: Add hCaptcha to your application as a captcha provider.
keywords: [hCaptcha, captcha]
authors: [Resulte]
---

[hCaptcha](https://www.hcaptcha.com/) is a captcha service similar to reCAPTCHA. Use it as a Casdoor captcha provider.

## Create a key pair

Sign up at hCaptcha and get a **site key** and **secret key** from your [dashboard](https://dashboard.hcaptcha.com/settings).

## Configure in Casdoor

Create a **Captcha** provider, set **Type** to **hCaptcha**, and enter the site key and secret key. Use **Preview** to check the captcha.

![hCaptcha provider](/img/providers/captcha/hcaptcha_provider.png)
![hCaptcha preview](/img/providers/captcha/hcaptcha_preview.png)

## Use in an application

Edit the application, add the hCaptcha provider, and save.

![hCaptcha provider app](/img/providers/captcha/hcaptcha_provider_app.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/sms/acs.md
================================================================================

---
title: Azure Communication Services SMS
description: Use Azure Communication Services (ACS) as an SMS provider.
keywords: [ACS, SMS, provider, Azure]
authors: [UsherFall]
---

Create a **SMS** provider in Casdoor and set **Type** to **Azure ACS**. You need: **Client secret**, **Sender number**, **Provider Url**, and **Template code**.

| Casdoor field   | Azure ACS / meaning      | Required |
|-----------------|--------------------------|----------|
| Client secret   | User Access Token (Communication Service) | Yes  |
| Sender number   | Phone number from Communication Service   | Yes  |
| Provider Url    | Communication Service endpoint            | Yes  |
| Template code   | Message template / body  | Yes  |

## Get credentials in Azure

- **Client secret** — In your Communication Service, create a **User Access Token** and use it as **Client secret** in Casdoor.

![azureToken.png](/img/providers/sms/azureToken.png)

- **Sender number** — Use a phone number provisioned in the Communication Service.

![azurePhone.png](/img/providers/sms/azurePhone.png)

- **Provider Url** — Use the Communication Service **endpoint** URL.

![azureUrl.png](/img/providers/sms/azureUrl.png)

## Configure and test in Casdoor

Fill in the provider fields. **Template code** is the message (or template) to send. Use **SMS Test** with a phone number to verify.

![azureProvider.png](/img/providers/sms/azureProvider.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/sms/amazonSns.md
================================================================================

---
title: Amazon SNS SMS
description: Use Amazon SNS as an SMS provider for verification codes.
keywords: [Amazon SNS, SMS, provider]
authors: [UsherFall]
---

Create a **SMS** provider in Casdoor and set **Type** to **Amazon SNS**. You need: **Access Key**, **Secret Access Key**, **Region**, and **Template code**.

| Casdoor field   | Amazon SNS / meaning     | Required |
|-----------------|--------------------------|----------|
| Client ID       | Access Key (IAM)         | Yes      |
| Client secret   | Secret Access Key (IAM)  | Yes      |
| Region          | AWS region for the topic | Yes      |
| Template code   | Message template / body | Yes      |

## Get credentials in AWS

- **Access Key / Secret Access Key** — In [IAM](https://console.aws.amazon.com/iam/), create or copy an access key for the user that can publish to SNS.

![amazonAccess.png](/img/providers/sms/amazonAccess.png)

- **Region** — Use the region where your SNS topic (or SMS is configured) lives.

![amazonRegion.png](/img/providers/sms/amazonRegion.png)

## Configure and test in Casdoor

Fill in the provider fields. **Template code** is the message content (or template ID) to send. Use **SMS Test** with a phone number to verify.

![amazonProvider.png](/img/providers/sms/amazonProvider.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/sms/overview.md
================================================================================

---
title: SMS provider overview
description: Configure SMS providers for verification codes using go-sms-sender.
keywords: [SMS, verification, Twilio, Alibaba, Tencent]
authors: [kininaru]
---

Casdoor sends SMS via [casdoor/go-sms-sender](https://github.com/casdoor/go-sms-sender). Supported providers include Twilio, Submail, SmsBao, Alibaba Cloud, Tencent Cloud, Huawei Cloud, and Volc. To add another provider, open an issue or submit a PR in that repo.

## Add an SMS provider

1. Click **Add** and select **SMS** under **Category**.
2. Choose the provider **Type** (e.g. Twilio, Alibaba Cloud).
3. Get credentials from the SMS provider and fill the required fields.

![Select Category](/img/providers/sms/selectCategory.png)
![Select Type](/img/providers/sms/selecttype.png)

## Proxy

For HTTP-based SMS providers (e.g. Custom HTTP SMS), you can enable **Enable proxy** so traffic goes through the SOCKS5 proxy set in Casdoor’s config. Useful when the server cannot reach the SMS API directly.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/provider/sms/twilio.md
================================================================================

---
title: Twilio SMS
description: Use Twilio as an SMS provider for verification codes.
keywords: [Twilio, SMS, provider]
authors: [UsherFall]
---

Configure a **SMS** provider in Casdoor with **Type** set to **Twilio**. Map Twilio values to Casdoor fields:

| Casdoor field   | Twilio              | Required |
|-----------------|---------------------|----------|
| Client ID       | Account SID         | Yes      |
| Client secret   | Auth Token         | Yes      |
| Sender number   | Twilio phone number | Yes      |
| Template code   | Your SMS template   | Yes      |

Get **Account SID**, **Auth Token**, and the **Twilio phone number** from the [Twilio Console](https://console.twilio.com/).

![twilioInfo.png](/img/providers/sms/twilioInfo.png)

Set the **Template code** to match your Twilio template, then use **SMS Test** with a phone number to verify.

![twilioProvider.png](/img/providers/sms/twilioProvider.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/application/invitation-code.md
================================================================================

---
title: Invitation codes
description: Restrict application sign-up to users with a valid invitation code.
keywords: [application, signup, invitation code]
authors: [leo220yuyaodog]
---

Invitation codes let you restrict who can sign up for an application. An admin creates one or more codes per application; each code can be used multiple times. Sign-up is allowed only when the user provides a valid code.

## Configuration

1. Add the **Invitation code** signup item to the [sign-up items table](/docs/application/signup-items-table).
2. On the application configuration page, add the invitation codes you want to allow.

![invitation code](/img/application/invitation-code/invitation_code_config.png)

:::tip
Once the application has invitation codes, sign-up requires a valid code. This applies even if the "Invitation code" signup item is hidden—users must still supply a valid code (e.g. in a hidden field or flow). Always add the Invitation code signup item when using this feature.
:::

Demo:

![invitation code demo](/img/application/invitation-code/invitation_demo.gif)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/application/config.md
================================================================================

---
title: Application configuration
description: Configure authentication and callback URLs for your Casdoor applications.
keywords: [config, application, redirect URL, callback]
authors: [ErikQQY]
---

```mdx-code-block
```

After deploying Casdoor and creating an organization, configure applications and their authentication settings.

This page explains how to configure application authentication using Casdoor.

:::note

**Example:** Configuring a forum application using [Casnode](https://casnode.org).

:::

Create an application and fill in the required configuration.

Select the organization you created so that users in that organization can access this application.

![Organization](/img/application/config/organization.png)

If your organization is named `my_organization`, select it from the drop-down menu.

![Select Organization](/img/application/config/selectorganization.png)

To allow users to authenticate via Casdoor when they sign up, set the **Redirect URL** to your application’s callback URL (e.g. **`https://your-site-url.com/callback`**).

:::caution

**Callback URL vs Redirect URL**

- The **callback URL** configured in the provider (e.g. GitHub, Google) must be Casdoor’s callback URL: **`http://your-casdoor-url.com/callback`**.
- The **Redirect URL** configured in Casdoor must be your application’s callback URL: **`http://your-site-url.com/callback`**.

:::

#### How the flow works

1. The user initiates sign-in and is sent to Casdoor.
2. Casdoor uses the application’s **Client ID** and **Client Secret** to authenticate with the provider (e.g. GitHub, Google).
3. After successful authentication, the provider redirects back to Casdoor. The provider’s **callback URL** must be Casdoor’s callback: **`http://your-casdoor-url.com/callback`**.
4. Casdoor then redirects to your application with the auth result. Casdoor’s **Redirect URL** must be your app’s callback: **`http://your-site-url.com/callback`**.

```mdx-code-block
```

## Verification Code Settings

Use **Code resend timeout** to control how long users must wait before requesting another verification code (email or SMS). The value is in seconds (default: 60) and sets the countdown shown on the login page. Set to `0` to use the global default.

:::tip

For finer control over sign-in methods (e.g. disabling or enabling specific methods), see **[Sign-in methods](./signin-methods.md)**.

:::



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/application/signin-items-table.md
================================================================================

---
title: Sign-in items table
description: Configure signin items to build a custom sign-in page.
keywords: [signin, items, table]
authors: [DacongDA]
---

On the application configuration page, use the **Sign-in items** table to define which elements appear on the sign-in page. Add, remove, or reorder items to customize the form.

![Signin Items Table](/img/application/signin-items-table/signin-items-table.png)

## Column reference

| Column | Values | Description |
|--------|--------|-------------|
| **Name** | — | Name of the signin item. |
| **Visible** | `True` / `False` | Show or hide on the sign-in page. |
| **Label HTML** | — | For custom items, HTML used as the field label. |
| **Custom CSS** | — | CSS for this signin item. |
| **Placeholder** | — | Placeholder text for the field. |
| **Rule** | Rule items | Rule that customizes this item (see below). |
| **Action** | — | Move up, move down, or delete. |

## Captcha rules

The **Captcha** item supports rules that control how verification is shown:

| Rule | Description |
|------|-------------|
| **Normal** | Captcha is shown in a modal when sending verification codes. |
| **Inline** | Captcha is shown directly on the sign-in page. |



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/application/signin-methods.md
================================================================================

---
title: Sign-in methods
description: Configure which sign-in methods are available and their order on the login page.
keywords: [signin, method, password, verification code, WebAuthn, LDAP]
authors: [HGZ-20]
---

On the application edit page, configure the **sign-in items** table: add, remove, and reorder methods. Supported methods: **Password**, **Verification code**, **WebAuthn**, and **LDAP**.

![Signin Methods](/img/application/signin-methods/signin-methods.png)

Field reference:

| Column       | Description |
|-------------|-------------|
| Name        | Sign-in method name. |
| DisplayName | Label shown to users. |
| Rule        | Rule that customizes this method (see table below). |
| Action      | Move up, move down, or delete. |

Rules are supported for **Password** and **Verification code** only.

| Method            | Rules | Description |
|-------------------|-------|-------------|
| Password          | `All` (default), `Non-LDAP` | `All` — LDAP users can sign in with password. `Non-LDAP` — LDAP users cannot use password sign-in. |
| Verification code | `All` (default), `Email only`, `Phone only` | Which channel to use for the code: both, email only, or phone only. |

:::note
**Example:** Prefer email sign-in, then password. Add **Verification code** first and **Password** second; set the verification code rule to **Email only** so the code is sent only by email. Optionally set a clear display name for the verification code method (e.g. “Email login”).
:::

![Signin Methods](/img/application/signin-methods/signin-methods-demo-config.png)

![Signin Methods](/img/application/signin-methods/signin-methods-demo-page.png)

:::tip
All methods except LDAP are available by default. At least one sign-in method must be configured.
:::

Here is a video of how the sign-in method works:



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/application/specify-login-organization.md
================================================================================

---
title: Specify login organization
description: Let users choose or enter the organization on the sign-in page.
keywords: [UI, login, application, organization]
authors: [leo220yuyaodog]
---

You can enable organization selection on the sign-in page so users pick or type the organization before signing in. For example, `/login` is the default page for the **built-in** organization; with this option enabled on **app-built-in**, users select an organization and are redirected to `/login/<organization>`.

## Configuration

On the application edit page, set **Org select mode**:

![mode_config](/img/application/specify-login-organization/mode_config.png)

| Mode | Behavior |
|------|----------|
| **None** | Organization selection is not shown. |
| **Input** | User types the organization name in an input. |
| **Select** | User chooses the organization from a dropdown. |

![mode_input](/img/application/specify-login-organization/mode_input.png)
![mode_select](/img/application/specify-login-organization/mode_select.png)

:::info
The organization selection page appears only when the route is `/login` or `<organization>/login`. The application must be set as the **default application** for the organization (or app-built-in).
:::

## Automatic redirect after session expiry

When a user’s session expires, Casdoor remembers the last-used organization (stored in the browser when visiting e.g. `/login/my-org`). On the next sign-in, they are redirected to that organization’s login page instead of the generic `/login` page.

If no organization is stored, the user is sent to `/login` and can choose an organization via the configured mode (Input or Select) if enabled.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/application/providers.md
================================================================================

---
title: Providers
description: Attach providers to your application and set rules (signup, login, forgot password, MFA, etc.).
keywords: [providers, OAuth, email, SMS, MFA]
authors: [zhuying]
---

```mdx-code-block
```

Add **providers** to your application so users can sign up or sign in with third-party identity, email, or SMS. For each provider you choose a **rule** that defines when it is used:

![Select providers](/img/application/config/selectproviders.png)

Rule reference:

| Rule | Use |
|------|-----|
| **Signup** | Send SMS/email templates during registration. |
| **Login** | Use this provider for sign-in. |
| **Forget Password** | Send reset links or codes. See [Email provider](/docs/provider/email/overview#password-reset-link) for reset links. |
| **Reset Password** | Use when the user resets their password. |
| **Set MFA** | Send codes during MFA setup. |
| **MFA Auth** | Use for MFA verification at login. See [MFA](/docs/user/multi-factor-authentication). |
| **all** | Use this provider for every scenario above. |

![Select rules](/img/application/providers/choose_providers.png)

![Select regions](/img/application/providers/choose_region.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/application/dynamic-client-registration.md
================================================================================

---
title: Dynamic client registration
description: Register OAuth clients programmatically via RFC 7591 (DCR).
keywords: [OAuth 2.0, DCR, dynamic registration, RFC 7591, MCP]
authors: [hsluoyz]
---

**Dynamic Client Registration (DCR)** lets your software register an OAuth client with Casdoor in one HTTP request instead of creating an application manually in the admin UI. That helps when you ship tools to end users: MCP clients, CLIs, or desktop apps can obtain client credentials at first run or install. Casdoor implements [RFC 7591](https://datatracker.ietf.org/doc/html/rfc7591).

## Registration endpoint

The endpoint is advertised in OIDC discovery. Request `/.well-known/openid-configuration`:

```bash
curl https://your-casdoor.com/.well-known/openid-configuration
```

Use the `registration_endpoint` value (e.g. `/api/oauth/register`) for registration:

```json
{
  "issuer": "https://your-casdoor.com",
  "authorization_endpoint": "https://your-casdoor.com/login/oauth/authorize",
  "token_endpoint": "https://your-casdoor.com/api/login/oauth/access_token",
  "registration_endpoint": "https://your-casdoor.com/api/oauth/register",
  ...
}
```

## Registering a client

POST to `/api/oauth/register` with JSON metadata:

```bash
curl -X POST https://your-casdoor.com/api/oauth/register \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Claude Desktop",
    "redirect_uris": ["http://localhost:3000/callback"],
    "grant_types": ["authorization_code", "refresh_token"],
    "token_endpoint_auth_method": "none",
    "application_type": "native"
  }'
```

Response includes the new client credentials:

```json
{
  "client_id": "a1b2c3d4e5f6",
  "client_secret": "secret_xyz789...",
  "client_id_issued_at": 1737799294,
  "client_secret_expires_at": 0,
  "redirect_uris": ["http://localhost:3000/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "token_endpoint_auth_method": "none",
  "application_type": "native"
}
```

Store the `client_id` and `client_secret` securely—you'll use them for all subsequent OAuth flows.

## Request Parameters

Your registration request needs at least one redirect URI. Everything else is optional, with Casdoor applying sensible defaults:

- **redirect_uris** (required): Array of allowed callback URLs where Casdoor redirects after authentication
- **client_name**: Display name for your application (auto-generated if omitted)
- **grant_types**: OAuth grant types your app will use—defaults to `["authorization_code"]`
- **token_endpoint_auth_method**: How your app authenticates at the token endpoint (`none`, `client_secret_post`, or `client_secret_basic`)
- **application_type**: Either `web` for server-side apps or `native` for desktop/mobile apps
- **logo_uri**: URL to your application's logo
- **client_uri**: URL to your application's homepage
- **scope**: Space-separated list of OAuth scopes your app requests

Applications created through DCR get a 7-day token expiration and are tagged with `dcr` for easy identification in the admin interface.

## Controlling DCR Per Organization

Organizations can control whether DCR is available through the `dcrPolicy` setting in the organization configuration page. When set to "disabled", registration requests will fail with an error. The default is "open", allowing anyone to register applications.

This gives you flexibility: enable DCR for developer-friendly organizations while keeping it locked down for production environments that require manual oversight.

## Security Model

DCR intentionally requires no authentication—this is by design for public clients like mobile apps and desktop tools that can't securely store credentials before registration. The model trades off unrestricted registration for the ability to support these client types.

Applications created through DCR belong to the organization's admin account and appear in your application list with a `dcr` tag. Client secrets never expire by default, but you can revoke any application through the admin interface at any time. For production deployments, consider whether your organization actually needs unauthenticated registration. Many scenarios work fine with manual app creation, and disabling DCR removes a potential abuse vector.

## Complete Example: MCP Client

Here's how an MCP client might implement DCR from scratch:

```javascript
// Discover the registration endpoint
const discovery = await fetch('https://your-casdoor.com/.well-known/openid-configuration')
  .then(r => r.json());

// Register the application
const registration = await fetch(discovery.registration_endpoint, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    client_name: 'MCP Client',
    redirect_uris: ['http://127.0.0.1:6437/callback'],
    grant_types: ['authorization_code', 'refresh_token'],
    token_endpoint_auth_method: 'none',
    application_type: 'native'
  })
}).then(r => r.json());

// Store credentials for OAuth flows
const { client_id, client_secret } = registration;
```

With these credentials, the client proceeds through the standard OAuth authorization code flow. The user authenticates in their browser, Casdoor redirects back to your callback URL with an authorization code, and you exchange it for access tokens.

## Handling Registration Failures

When something goes wrong, Casdoor returns RFC 7591 compliant errors with an `error` code and human-readable `error_description`. The most common issues: missing redirect URIs (`invalid_redirect_uri`), malformed parameters (`invalid_client_metadata`), or DCR being disabled for the organization (`access_denied`). Check the description field for specifics on what needs to be fixed.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/application/exclusive-signin.md
================================================================================

---
title: Exclusive sign-in
description: Allow only one active session per user per application.
keywords: [exclusive signin, session, single session]
authors: [hsluoyz]
---

**Exclusive sign-in** limits each user to one active session per application. A new sign-in from another device or browser ends all previous sessions for that user and application.

## Configuration

On the application edit page, enable **Enable exclusive signin**. The setting applies to all users of that application.

## Behavior

On sign-in with exclusive sign-in enabled:

- All existing sessions for that user and application are removed
- A new session is created for the current sign-in
- The user is effectively signed out everywhere else for this app

Example: user signs in on a laptop, then on a phone — the laptop session is terminated; only the phone session stays active.

## When to use it

Exclusive sign-in reduces the risk of concurrent use of the same account (e.g. after forgetting to sign out on a shared PC). It also limits concurrent sessions per user. Users who need to stay signed in on multiple devices will have to sign in again when they switch.

## How it works

For each sign-in with exclusive sign-in on: Casdoor finds all sessions for that user and application, deletes them, creates a new session, and keeps only that session ID. This is done per application.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/application/ui-customization.md
================================================================================

---
title: Login UI customization
description: "Customize the sign-in page: background, panel style, position, and side panel."
keywords: [UI, login, application, customization]
authors: [leo220yuyaodog]
---

This guide walks through customizing your application’s sign-in page: background image, login panel style, position, and optional side panel.

![step4_result2.png](/img/application/ui-customization/step4_result2.png)

## 1. Background image

The default background is white. Set **Background URL** to an image URL; the preview updates when the URL is valid.

![step1_start.png](/img/application/ui-customization/step1_start.png)
![step1_backgroune_url.gif](/img/application/ui-customization/step1_backgroune_url.gif)

## 2. Login panel style

Use **Form CSS** to style the login panel. Example:

```html
```

![step2_form_css.gif](/img/application/ui-customization/step2_form_css.gif)

:::tip
If **Form CSS** is empty, the editor may show a default; copy the content and paste it into the field, then save.
:::

![step2_end.png](/img/application/ui-customization/step2_end.png)

## 3. Panel position

Use the position buttons to place the panel on the **Left**, **Center**, or **Right**.

![step3_position.png](/img/application/ui-customization/step3_position.png)
![step3_end.png](/img/application/ui-customization/step3_end.png)

## 4. Side panel

Enable **Enable Side Panel** so the form is centered with a side area. Edit **Side panel HTML** for the side content; start from the default template or customize it.

![enable_side_panel.png](/img/application/ui-customization/step4_enable_side_panel.png)

Example **Side panel HTML**:

```html
```

Refine the layout with **Form CSS** (e.g. `.login-panel`, `.login-form`):

```html
```

![step4_modify_CSS.gif](/img/application/ui-customization/step4_modify_CSS.gif)

:::info
`.login-panel` and `.login-form` are the main container classes; target them in **Form CSS** for further customization.
:::

![step4_result2.png](/img/application/ui-customization/step4_result2.png)

## Summary

Set **Background URL**, style **Form CSS**, choose **panel position**, and optionally enable and style **Side panel HTML**. See also:

- [Customize theme](/docs/organization/customize-theme) — primary color and border radius
- [Sign-up items table](/docs/application/signup-items-table)
- [Application config](/docs/application/config)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/application/shared-application.md
================================================================================

---
title: Shared application
description: Use one application across multiple organizations with org-specific client IDs.
keywords: [shared, application, multi-tenant]
authors: [DacongDA]
---

A **shared application** can be used by multiple organizations. Only the **built-in** organization can create shared applications. Each organization uses the same application with an org-specific identifier: append `-org-<organizationName>` to the client ID or application name.

Example: application client ID `2dc94ccbec09612c04ac`, organization `casbin` → use client ID `2dc94ccbec09612c04ac-org-casbin`. OAuth authorize URL: `https://door.casdoor.com/login/oauth/authorize?client_id=2dc94ccbec09612c04ac-org-casbin&response_type=code&redirect_uri=...&scope=read&state=casdoor`.

## Configuration

1. Create the application.
2. Enable **Is Shared**.
3. Use `-org-<orgName>` when referring to the app (e.g. in client_id or login URLs).

![shared application field](/img/application/shared-application/shared_application_field.png)

![shared application login link](/img/application/shared-application/shared_application_login_link.png)

## Invitations

For [invitations](/docs/invitation/overview) with a shared application, Casdoor generates organization-specific links with the `-org-{orgName}` suffix so users register in the correct organization.

:::caution
Once an application is shared, it is available to all organizations and cannot be restricted to a subset.
:::

Here is a demo video that shows how to use shared application:



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/application/categories.md
================================================================================

---
title: Application categories
description: Default (user-facing) vs Agent (M2M) applications and their types.
keywords: [application, category, type, agent, MCP, A2A]
authors: [hsluoyz]
---

Casdoor uses **categories** and **types** to support both user-facing apps and machine-to-machine (M2M) apps. The category determines which protocol types and features are available.

## Categories

### Default

**Default** applications are for web or mobile apps where users sign in in a browser or client. Choose a protocol type:

- **All** — Multiple protocols
- **OIDC**, **OAuth**, **SAML**, **CAS** — Single protocol

### Agent

**Agent** applications are for M2M: services or tools that authenticate programmatically, without a user UI. Types:

- **MCP** — Model Context Protocol (e.g. AI agents and MCP tools)
- **A2A** — Application-to-application (service-to-service)

When a client registers via OAuth Dynamic Client Registration, Casdoor can assign the Agent category and MCP type by default.

## Changing category

Set or change the category on the application edit page. When you switch category, **Type** is updated automatically: Agent → **MCP**, Default → **All**.

## Custom scopes (Agent only)

Agent applications can define [custom scopes](./scopes.md). Default applications use only standard OAuth/OIDC scopes.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/application/overview.md
================================================================================

---
title: Overview
description: Learn how applications work in Casdoor and how to configure authentication for your services.
keywords: [application, authentication, OAuth, OIDC]
authors: [sh1luo]
---

In Casdoor, each protected service is an **application**. Applications are independent: deploy, configure, or disable any one without affecting others.

To use Casdoor as the identity provider for your web apps, register each app as a Casdoor application. Users who sign in to an organization can then access all applications in that organization without signing in again.

Application configuration is flexible:

- Enable or disable password-based login and third-party login
- Configure which identity providers (e.g., Google, GitHub) users can use to sign in
- Customize sign-up fields and sign-in options per application

This section walks you through creating and configuring your first application.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/application/tags.md
================================================================================

---
title: Application tags
description: Restrict sign-in to users whose tags match the application’s tags.
keywords: [tags, application, access control]
authors: [Chinoholo0807]
---

**Application tags** limit who can sign in: only users with at least one tag that matches the application’s tags can access it. Admins and global admins are not restricted.

Example: if the application has tags `dev` and `staging`, users must have `dev` or `staging` (or both). User tags are comma-separated (e.g. `"dev,qa,staging"`); Casdoor checks each tag and allows access if any match. The reserved tag `guest-user` is for [guest authentication](/docs/how-to-connect/guest-auth); those users become `normal-user` when they set credentials.

## Multiple tags per user

Assign several tags to one user (e.g. `"dev,staging"`) so they can access multiple apps or environments. Casdoor splits the user’s tags and matches against the application’s tags. Single-tag users (e.g. `"prod"`) behave as before.

## Configuration

On the application edit page, use the **Tags** section to add the tags that are allowed to sign in.

![configure_tags](/img/application/tags/configure_app_tags.png)

Here is a video demonstrating how application tags work:



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/application/terminology.md
================================================================================

---
title: Application terminology
description: Reference for application configuration fields and options.
keywords: [terminology, application, config]
authors: [ErikQQY]
---

## Basic information

- **Name** — Internal application name.
- **CreatedTime** — When the application was created.
- **DisplayName** — Name shown to users.
- **Category** — `Default` (web apps) or `Agent` (M2M, e.g. MCP servers, API clients).
- **Type** — For Default: `All`, `OIDC`, `OAuth`, `SAML`, `CAS`. For Agent: `MCP`, `A2A`.
- **Logo**, **Title**, **Favicon** — Branding on login/sign-up pages.
- **Order** — Sort order in lists.
- **HomepageUrl**, **Description** — App homepage and description.
- **Organization** — Owning organization.
- **Tags** — Only users with one of these tags can sign in.
- **IsShared** — Whether the app is shared across organizations.

## Authentication and sign-in

- **EnablePassword** — Password sign-in.
- **EnableSignUp** — Allow self sign-up; if off, only admins can create accounts.
- **DisableSignin** — Turn off sign-in for this app.
- **EnableSigninSession**, **EnableAutoSignin** — Session and auto sign-in.
- **EnableCodeSignin** — Email/SMS verification code sign-in.
- **EnableExclusiveSignin** — One active session per user.
- **EnableWebAuthn** — WebAuthn (passwordless).
- **EnableLinkWithEmail** — Account linking via email.
- **SigninMethods**, **SigninItems** — Sign-in method and UI config.
- **SignupItems** — Registration form fields.
- **OrgChoiceMode** — How users pick organization at sign-in.

## OAuth and token

- **ClientId**, **ClientSecret** — OAuth credentials.
- **RedirectUris** — Allowed post-login redirect URIs.
- **ForcedRedirectOrigin** — Force redirect to a given origin.
- **GrantTypes** — Allowed OAuth grant types.
- **Scopes** — Custom scopes for Agent apps (name, display name, description); appear in OIDC discovery.
- **TokenFormat** — `JWT`, `JWT-Empty`, `JWT-Custom` (see [Token overview](/docs/token/overview)).
- **TokenSigningMethod** — e.g. RS256, HS256.
- **TokenFields**, **TokenAttributes** — Custom token content.
- **ExpireInHours**, **RefreshExpireInHours** — Access and refresh token lifetime.
- **CookieExpireInHours** — Session cookie lifetime (default 720 h). Without “Remember me”, session is limited to 24 h. `0` = use default.

## SAML

- `Cert`: Certificate used for SAML signing.
- `EnableSamlCompress`: Enable compression for SAML requests and responses.
- `EnableSamlC14n10`: Enable C14N 1.0 canonicalization for SAML.
- `EnableSamlPostBinding`: Use POST binding instead of GET for SAML responses.
- `DisableSamlAttributes`: Disable sending user attributes in SAML responses (only sends NameID).
- `EnableSamlAssertionSignature`: Enable digital signatures for SAML assertions. When disabled, only the response envelope is signed while maintaining compatibility with service providers that don't support assertion signatures.
- `UseEmailAsSamlNameId`: Use user's email as the SAML NameID instead of username.
- `SamlReplyUrl`: The ACS (Assertion Consumer Service) URL for SAML responses.
- `SamlAttributes`: Custom SAML attributes to include in the response.
- `SamlHashAlgorithm`: Hash algorithm for SAML signatures (e.g., SHA256).

## Providers

- **Providers** — OAuth, email, SMS, and other providers attached to the application.

## UI customization

- **HeaderHtml**, **FooterHtml** — Custom header/footer on login/sign-up pages.
- **SignupHtml**, **SigninHtml** — Custom HTML for sign-up/sign-in pages.
- **FormCss**, **FormCssMobile** — CSS for the login form (desktop and mobile).
- **FormOffset** — Vertical offset of the form.
- **FormSideHtml** — HTML beside the form.
- **FormBackgroundUrl**, **FormBackgroundUrlMobile** — Login page background image.
- **ThemeData** — Theme/color config.

## Security and access control

- **DefaultGroup** — Default group for new users.
- **IpRestriction**, **IpWhitelist** — IP allowlist (see [IP allowlist](../ip-whitelist/ip-whitelist)).
- **FailedSigninLimit** — Failed attempts before lockout.
- **FailedSigninFrozenTime** — Lockout duration (seconds).

## External URLs

- **SigninUrl** — Custom sign-in URL for external auth.
- **SignupUrl** — External sign-up URL if not using Casdoor sign-up.
- **ForgetUrl** — Password recovery URL.
- **AffiliationUrl** — Affiliation or invitation URL.
- **TermsOfUse** — Terms of use URL or id.

## Other

- **CodeResendTimeout** — Seconds before another verification code can be requested (default: 60).



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/application/signup-items-table.md
================================================================================

---
title: Sign-up items table
description: Configure signup items to build a custom registration page.
keywords: [signup, items, table, registration]
authors: [Resulte]
---

On the application configuration page, use the **Sign-up items** table to define which fields appear on the registration page. Add, remove, or reorder items to customize the form.

![Signup Items Table](/img/application/signup-items-table/signup-items-table.png)

:::tip
Applications created via the Casdoor SDK get default signup items (ID, Username, Display name, Password, Confirm password, Email, Phone, Agreement). You can adjust them as needed.
:::

## Column reference

| Column | Values | Description |
|--------|--------|-------------|
| **Name** | — | Name of the signup item. |
| **Visible** | `True` / `False` | Show or hide on the registration page. |
| **Required** | `True` / `False` | Whether the field is mandatory. |
| **Prompted** | `True` / `False` | Whether to prompt the user if they leave it empty. |
| **Regex** | — | Optional regex for client-side validation. |
| **Label** | — | For items starting with `Text`, use HTML for the field; otherwise replaces the item label. |
| **Custom CSS** | — | CSS for this signup item. |
| **Rule** | Rule items | Rule that customizes this item (see table below). |
| **Action** | — | Move up, move down, or delete. |

Items that support **rules**: ID, Display name, Email, Agreement.

| Item | Rules | Description |
|------|-------|-------------|
| **ID** | `Random` / `Incremental` | User ID generation: random or incremental. |
| **Display name** | `None` / `Real name` / `First, last` | How to show the display name; `First, last` shows first and last name separately. |
| **Email** | `Normal` / `No verification` | `Normal` = require email verification; `No verification` = skip verification. |
| **Agreement** | `None` / `Signin` / `Signin (Default True)` | Terms of use: none, require confirmation, or default to confirmed. |

:::note
Example: to show an email field without verification, add the Email signup item and set its rule to **No verification**.
:::

![Signup Items Table](/img/application/signup-items-table/signup-items-table-demo-config.png)

![Signup Items Table](/img/application/signup-items-table/signup-items-table-demo-page.png)

:::note
If the organization has "Use email as username" enabled and the username field is hidden in signup items, the user’s email is used as their username.
:::

## Field validation

Use the **Regex** column to validate input on the client before submit:

1. Set **Regex** on the signup item (e.g. Username, Display name, or a custom field).
2. Enter a pattern (e.g. `^[a-zA-Z0-9_]+$` for alphanumeric usernames).
3. Users see an error when input does not match.

Works for standard fields (Username, Display name, First name, Last name, Affiliation) and custom fields.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/user/forms.md
================================================================================

---
title: Forms
description: Customize list-page columns and layout for core entities.
keywords: [forms, column management, list page]
authors: [Attack825]
---

**Forms** let admins customize how list pages for core entities (users, providers, etc.) are displayed: which columns appear, their order, labels, and widths.

## Overview

The Forms entry page lists all existing forms. Select a **Form type** (e.g. User list, Provider list) to edit the layout for that entity’s list page.

![Forms Inventory Overview](/img/user/forms.png)

![Form Type Selection](/img/user/form_type.png)

## Form items

- **Edit items** — Change **Label** (e.g. "User ID" → "Employee ID"), **Width**, and **Visible** (show/hide column).
- **Remove items** — Delete columns you don’t need.
- **Reorder** — Use "Move Up" / "Move Down" to set column order.

![Form Items Editor](/img/user/form_items.png)

## Preview

The preview matches the live list page so you can confirm column order, labels, widths, and visibility before saving.

![Form Preview Page](/img/user/form_preview.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/user/permissions.md
================================================================================

---
title: User permissions
description: Assign permissions to users and roles; use the Permissions API.
keywords: [user, permissions, Casbin, API]
authors: [Resulte]
---

Users can have multiple **permissions**. You see them on the user’s profile.

![permissions](/img/user/users_permissions.png)

## Permission properties

Each permission has: **Owner**, **Name**, **CreatedTime**, **DisplayName**, **IsEnabled**, **Model**, **Users**, **Roles**, **ResourceType**, **Resources**, **Actions**, **Effect**. **Users** and **Roles** list who gets this permission.

## Managing permissions

Permissions are separate resources. The user’s `Permissions` field is filled when you load the user. To assign or change permissions, use the **Permissions** API, not the User API.

- **Web UI:** **Permissions** page (e.g. `https://door.casdoor.com/permissions`).
- **API:** [Casdoor API reference](https://door.casdoor.com/swagger) — permission endpoints.

If a user is in a permission’s **Users** list or in a role that is in **Roles**, that permission appears in the user’s `Permissions` when you fetch the user.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/user/roles.md
================================================================================

---
title: User roles
description: Assign and manage roles for users; use roles with permission policies.
keywords: [user, roles, RBAC, API]
authors: [Resulte]
---

Users can have multiple **roles**. You see a user’s roles on their profile page.

![user roles](/img/user/users_roles.png)

## Role properties

Each role has:

- **Owner**, **Name**, **CreatedTime**, **DisplayName**, **IsEnabled**
- **Users** — list of users in this role
- **Roles** — list of child roles (for role hierarchy)

## Managing roles

Roles are separate resources. The user’s `Roles` field is filled when you load the user (it is not stored on the user record). To assign or change roles, use the **Roles** API, not the User API.

- **Web UI:** Open the **Roles** page (e.g. `https://door.casdoor.com/roles`).
- **API:** Use the role endpoints in the [Casdoor API reference](https://door.casdoor.com/swagger).

When you add a user to a role’s **Users** array, that role shows up in the user’s `Roles` when you fetch the user.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/user/impersonation.md
================================================================================

---
title: User impersonation
description: Sign in as another user for support and testing without knowing their password.
keywords: [impersonation, master password, admin, support]
---

**Impersonation** lets admins act as another user temporarily—useful for support, testing permissions, and debugging.

Casdoor supports two methods:

1. **Session-based** — One-click from the Users page (no password).
2. **Master password** — Sign in with an org-wide master password as any user.

Both give you the same access as the impersonated user.

## Session-based impersonation

Start from the **Users** page: each row has an **Impersonation** button. Click it to switch your session to that user; the UI and permissions match theirs.

![enter impersonation](/img/user/user_impersonation.png)

You stay in the impersonated user’s context until you exit. Casdoor tracks that you’re impersonating so it can restore your admin session.

### Exiting

Open the user menu (top right). Choose **Exit impersonation** (instead of Logout) to return to your admin session.

![exit impersonation](/img/user/exit_user_impersonation.png)

:::tip
Only administrators can impersonate; normal users do not see the impersonation button.
:::

## Master password

Impersonation is also available at login: set an organization **master password**; admins can then sign in as any user in that org by entering the master password instead of the user’s password.

### Behavior

On login, Casdoor checks the organization’s master password first, then the user’s password. If the master password matches, login succeeds for that user without their real password.

### Setting up master password

To configure this feature, open your Organization settings and locate the Master Password field. Enter a strong password and save. From then on, use this password at the login screen with any username in that organization to sign in as that user.

![master password](/img/user/master_password.png)

:::caution Handle with care

The master password grants access to any account in your organization. Treat it like a master key - share it only with trusted administrators, store it securely in a password manager, and rotate it immediately if you suspect it's been compromised.

:::

### Using master password

Navigate to your organization's login page at `/login/<organization_name>`. Enter the target user's username and the master password instead of their personal password. Casdoor authenticates you as that user, giving you their exact permissions and view of the system.

:::tip Example

For an organization called "my-company", visit `https://your-casdoor-domain.com/login/my-company`, enter the username you want to impersonate, and use the master password.

:::

## When to use impersonation

Impersonation becomes valuable when you need to see the system through a user's eyes. Support teams often use it to reproduce reported issues - seeing exactly what the user sees makes debugging much faster. Testing permission configurations also benefits from impersonation, letting you verify access controls work correctly for different roles without creating test accounts.

Emergency situations sometimes require immediate access to a user's data when they're unavailable. Similarly, investigating security concerns or unusual account activity becomes more effective when navigating the system in that user's context.

## Security considerations

Session-based impersonation requires admin privileges and creates an audit trail of who impersonated whom. The system tracks these sessions separately from normal logins, maintaining accountability.

Master password authentication doesn't distinguish between administrator impersonation and regular login in basic audit logs, since it uses the standard authentication flow. This makes session-based impersonation preferable for most scenarios.

Both methods respect multi-factor authentication settings. If a user has MFA enabled, you'll need to complete those verification steps even when impersonating.

## Disabling master password

To remove the master password option, clear the Master Password field in your Organization settings and save. This only affects password-based impersonation - the session-based method remains available to administrators regardless of master password configuration.

## Related configuration

Organizations can set a default password assigned to newly created users, which differs from the master password used for impersonation. Password complexity rules apply to all passwords including the master password, helping maintain security standards across your organization.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/user/overview.md
================================================================================

---
title: Overview
description: User model, properties, roles, permissions, and bulk import in Casdoor.
keywords: [user, properties, roles, permissions, import]
authors: [sh1luo]
---

## User properties

Casdoor manages user accounts. Each user has the following properties:

- `Owner`: The organization that owns the user
- `Name`: The unique username for the user (must be unique within the organization)
- `CreatedTime`: Timestamp when the user account was created
- `UpdatedTime`: Timestamp when the user account was last updated
- `Id`: Unique identifier (UUID) for each user
- `Type`: The type of user account (e.g., normal-user, guest-user)
- `Password`: The user's encrypted password
- `PasswordSalt`: Salt value used for password hashing
- `PasswordOptions`: Password complexity options
- `DisplayName`: The user's display name shown in the user interface
- `FirstName`: The user's first name (given name)
- `LastName`: The user's last name (family name)
- `Avatar`: URL or link to the user's current avatar image
- `PermanentAvatar`: URL to the user's permanently stored avatar (not affected by provider changes)
- `Email`: The user's email address (automatically normalized to lowercase)
- `Phone`: The user's phone number
- `Location`: The user's geographical location
- `Address`: An array of strings containing the user's address information (e.g., street address, city, state, postal code)
- `Affiliation`: The user's organization or institutional affiliation
- `Title`: The user's professional title or job position
- `IdCardType`: The type of ID card used for identity verification (e.g., passport, driver's license)
- `IdCard`: The ID card number (becomes read-only after verification)
- `RealName`: The user's verified real name (becomes read-only after identity verification)
- `IsVerified`: Indicates whether the user has completed identity verification through an ID Verification provider
- `Homepage`: URL to the user's personal homepage or website
- `Bio`: A short biography or description of the user
- `Tag`: Tags for categorizing users (can be multiple tags separated by commas)
- `Region`: The user's geographical region or area
- `Language`: The user's preferred language for the interface
- `Gender`: The user's gender
- `Birthday`: The user's date of birth
- `Education`: The user's education level or background
- `Balance`: The user's account balance (for applications with payment features)
- `Score`: Numerical score associated with the user (application-defined)
- `Karma`: Karma or reputation points for the user
- `Ranking`: The user's ranking position (application-defined)
- `IsDefaultAvatar`: Indicates whether the user is using the default avatar
- `IsOnline`: Indicates whether the user is currently online
- `IsAdmin`: Indicates whether the user is an administrator of their organization
- `IsGlobalAdmin`: Indicates whether the user has permission to manage Casdoor
- `IsForbidden`: Indicates whether the user account has been banned or restricted
- `IsDeleted`: When a user is soft-deleted (`IsDeleted = true`), they cannot sign in through any authentication method, including OAuth providers. This prevents deleted users from re-registering via third-party login.
- `SignupApplication`: The application through which the user signed up
- `Hash`: Hash value used for internal authentication mechanisms
- `PreHash`: Previous hash value (used during password migration)
- `CreatedIp`: The IP address from which the user account was created
- `LastSigninTime`: Timestamp of the user's last sign-in
- `LastSigninIp`: The IP address from the user's last sign-in
- `Roles`: An array of the user's roles (extended field, read-only via User API)
- `Permissions`: An array of the user's permissions (extended field, read-only via User API)

Unique IDs for social platform logins:

- `Github`: User's unique identifier from GitHub OAuth login
- `Google`: User's unique identifier from Google OAuth login
- `QQ`: User's unique identifier from QQ OAuth login
- `WeChat`: User's unique identifier from WeChat OAuth login
- `Facebook`: User's unique identifier from Facebook OAuth login
- `DingTalk`: User's unique identifier from DingTalk OAuth login
- `Weibo`: User's unique identifier from Weibo OAuth login
- `Gitee`: User's unique identifier from Gitee OAuth login
- `LinkedIn`: User's unique identifier from LinkedIn OAuth login
- `Wecom`: User's unique identifier from WeCom (WeChat Work) OAuth login
- `Lark`: User's unique identifier from Lark (Feishu) OAuth login
- `Gitlab`: User's unique identifier from GitLab OAuth login
- `Adfs`: User's unique identifier from ADFS authentication
- `Baidu`: User's unique identifier from Baidu OAuth login
- `Casdoor`: User's unique identifier from another Casdoor instance OAuth login
- `Infoflow`: User's unique identifier from Infoflow OAuth login
- `Apple`: User's unique identifier from Apple OAuth login
- `Azure AD`: User's unique identifier from Azure Active Directory OAuth login
- `Azure AD B2C`: User's unique identifier from Azure AD B2C OAuth login
- `Slack`: User's unique identifier from Slack OAuth login
- `Steam`: User's unique identifier from Steam OAuth login
- `Ldap`: User's unique identifier from LDAP authentication

## Organization admin privileges

Users with `IsAdmin` enabled are administrators of their organization:

- Full access to manage users, applications, and resources within their organization
- Access to verification code records sent to users in their organization
- Ability to configure organization-level settings and policies

Organization admins have elevated permissions but are scoped to their organization only. Global admins (`built-in` organization users) have full access across all organizations in the Casdoor instance.

## User tags

The `Tag` field categorizes users. Use a single tag or several comma-separated tags (e.g. `"developer,qa,reviewer"`). Application access checks evaluate each tag separately.

Reserved tag values:

- `normal-user`: Standard users with full authentication capabilities
- `guest-user`: Temporary users created through [guest authentication](/docs/how-to-connect/guest-auth) without initial credentials
  - Automatically upgrade to `normal-user` when they set a proper username or password
  - Cannot sign in directly until they upgrade their account

Custom tags can restrict application access. See [Application Tags](/docs/application/tags).

## Identity verification

Casdoor supports identity verification via ID Verification providers. Users can verify their identity by submitting their ID card information and real name, which gets validated through third-party services like Jumio.

When a user completes identity verification:

- The `IsVerified` field is set to `true`
- The `RealName`, `IdCardType`, `IdCard`, and related identity fields become read-only
- The verified status is included in JWT tokens and OIDC userinfo responses
- A verification badge appears on the user's profile

This feature is useful for applications that require KYC (Know Your Customer) compliance or need to ensure user identity authenticity. See [ID Verification Providers](/docs/provider/idv/overview) for more information on configuring identity verification.

## Email normalization

Casdoor normalizes all email addresses to lowercase for uniqueness and to avoid duplicate accounts. This means that `user@example.com`, `User@Example.com`, and `USER@EXAMPLE.COM` are treated as the same email address, complying with RFC 5321 standards.

This normalization happens automatically during:

- User signup and account creation
- User login and authentication
- Email duplicate checking

## Roles and permissions (extended fields)

The `Roles` and `Permissions` fields on the User object are **extended**: they are filled when user data is fetched, not stored on the User table. They are built from the Roles and Permissions resources via `ExtendUserWithRolesAndPermissions()`.

**Important:** You cannot change roles or permissions with `/api/update-user` (including via the `columns` parameter). Use the [Roles](/docs/user/roles#managing-roles) and [Permissions](/docs/user/permissions#managing-permissions) APIs and their management pages (e.g. **Roles** and **Permissions** in the sidebar) to assign and manage them.

## Using the Properties field

The `Properties` field is a key-value map (`map[string]string`) for custom user attributes not covered by the built-in schema. Use it to:

- Store organization-specific user attributes
- Add custom metadata that doesn't fit into standard fields
- Extend user profiles without modifying the core schema

## Importing users from XLSX

Add or update users by uploading an XLSX file.

### Getting started

On the **Users** page in the admin console you’ll see:

- **Download template**: Generates an XLSX template with all available user fields and their localized column headers
- **Upload (.xlsx)**: Opens the upload dialog to import users from your XLSX file

![Importing Users](/img/user/import_users.png)

The template file includes headers in the format `Display Name#field_name` (e.g., `Organization#owner`), where the display name is localized to your language and the field name after `#` is used for import mapping. The comment prefix (everything before `#`) is automatically removed during import.

### Upload process

After you choose an XLSX file, Casdoor shows a preview of the data. Review it and confirm to start the import. A [sample file](https://github.com/casdoor/casdoor/blob/master/xlsx/user_test.xlsx) (`xlsx/user_test.xlsx`) with 5 test users is available for reference.

![Import Successful](/img/user/import_success.png)

### Upload permissions

Who can upload depends on your role:

- **Global admins** (users in the `built-in` organization with `IsGlobalAdmin` set to true) can upload users to any organization. The target organization is determined by the `Owner` field in the XLSX file.
- **Organization admins** (users with `IsAdmin` set to true) can only upload users to their own organization. The system ensures that duplicate checking and user creation are scoped to the correct organization.

## Bypassing password encryption on import

When migrating users from another system, you may need to preserve existing password hashes instead of re-hashing with the organization’s default password type. Use the `passwordType` field during user import to tell Casdoor the format of the stored password.

:::note Example: bcrypt password
Example POST body for `/api/add-user`:

```json
{
  "owner": "organization",
    "signupApplication": "first-app",
    "email":"dev@dev.com",
    "name": "dev",
    "displayName": "developper",
    "password": "$2a$10$.o/iVyDE9Xk8ioywHDnQRu72RviOi6FPa1ujhusbSCZeg7VOa6MY6",
    "passwordType":"bcrypt",
}
```

The password is already bcrypt-hashed, so `passwordType` is set to `"bcrypt"` so Casdoor does not hash it again.

:::



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/session/single-sign-out.md
================================================================================

---
title: Single sign-out (SSO logout)
description: Log users out from all applications in the organization at once.
keywords: [SSO, single sign-out, logout, session]
authors: [leo220yuyaodog]
---

## Overview

**Single sign-out (SSO logout)** logs a user out from every application in the organization in one go. When they sign out from one app, all other apps in the same SSO setup are signed out as well.

Use it for:

- **Security incidents**: Immediately terminate all active sessions when a security breach is detected
- **Organization-wide logout policies**: Enforce logout across all services when users leave the organization or change roles
- **Compliance requirements**: Ensure users are completely logged out from all systems when required by regulations
- **User-initiated logout**: Allow users to log out from all applications with a single action

## How it works

The `logoutAll` parameter chooses the mode:

**Full SSO logout** (default, `logoutAll=true` or omitted):

1. **Delete all active sessions**: All active sessions for the user across all applications in the organization are terminated
2. **Expire all access tokens**: All access tokens that were issued to the user are immediately invalidated
3. **Clear the current session**: The user's current session and authentication state are cleared
4. **Send logout notifications**: Notification providers receive the logout event with all session IDs and token hashes

This ensures that the user is completely logged out from all integrated applications and cannot access any resources without re-authenticating.

**Session-only logout** (`logoutAll=false`):

1. **Delete current session**: Only the current session is terminated
2. **Clear current authentication state**: The user's current session and token are cleared
3. **Send targeted notification**: Notification providers receive the logout event with the current session ID and associated access token hashes

This allows users to logout from a specific device or browser while remaining logged in on other sessions. This is useful when users share accounts across multiple devices or have concurrent sessions they want to manage individually.

The access token hashes included in session-level logout notifications enable your subsystems to identify exactly which tokens need to be invalidated. When a user logs out from a specific browser or device, match the token hashes against active sessions and perform targeted invalidation without affecting other devices where the user remains logged in.

### Logout notifications

On SSO logout, Casdoor sends a request to each notification provider configured for the application the user signed up with. The notifications include session IDs, access token hashes, and cryptographic signatures for secure, synchronized logout across all integrated systems.

Each notification provider receives a POST request with the following payload:

```json
{
  "owner": "org-name",
  "name": "username",
  "displayName": "John Doe",
  "email": "user@example.com",
  "phone": "+1234567890",
  "id": "user-id",
  "event": "sso-logout",
  "sessionIds": ["session-123", "session-456"],
  "accessTokenHashes": ["hash-abc", "hash-def"],
  "nonce": "random-nonce-xyz",
  "timestamp": 1699900000,
  "signature": "hmac-sha256-signature"
}
```

**Notification fields:**

- `sessionIds`: List of session IDs being logged out (enables targeted session invalidation)
- `accessTokenHashes`: SHA-256 hashes of access tokens being invalidated. Both full SSO logout and session-level logout now include these hashes, allowing your subsystems to match them against active tokens and perform synchronized logout
- `nonce`: Random value for replay attack protection
- `timestamp`: Unix timestamp when the notification was generated
- `signature`: HMAC-SHA256 signature computed using the application's client secret

#### Verifying Logout Notifications

To prevent malicious logout requests, you should verify the signature of incoming logout notifications:

```go
// Example verification in Go
func verifyLogoutNotification(notification *SsoLogoutNotification, clientSecret string) bool {
    data := fmt.Sprintf("%s|%s|%s|%d|%s|%s",
        notification.Owner,
        notification.Name,
        notification.Nonce,
        notification.Timestamp,
        strings.Join(notification.SessionIds, ","),
        strings.Join(notification.AccessTokenHashes, ","))
    
    expectedSignature := hmacSHA256(clientSecret, data)
    return notification.Signature == expectedSignature
}
```

```javascript
// Example verification in JavaScript
const crypto = require('crypto');

function verifyLogoutNotification(notification, clientSecret) {
  const data = `${notification.owner}|${notification.name}|${notification.nonce}|${notification.timestamp}|${notification.sessionIds.join(',')}|${notification.accessTokenHashes.join(',')}`;
  
  const expectedSignature = crypto
    .createHmac('sha256', clientSecret)
    .update(data)
    .digest('hex');
  
  return notification.signature === expectedSignature;
}
```

#### Configuration

To receive logout notifications, configure a notification provider (such as Custom HTTP, Telegram, or Slack) in your Casdoor application's notification provider settings. For Custom HTTP providers:

- Set **Receiver** to your application's webhook endpoint (e.g., `https://app.example.com/api/logout-webhook`)
- Set **Method** to POST
- Set **Title** to `content` (the parameter name for the JSON payload)

Your application can then verify the signature, check the timestamp to prevent replay attacks, and use the session IDs and token hashes to perform targeted logout operations. For more details on configuring notification providers, see the [Notification Providers](/docs/provider/notification/overview) documentation.

## SSO Logout API

### Endpoint

```http
GET or POST /api/sso-logout?logoutAll=<true|false>
```

The SSO logout endpoint accepts both `GET` and `POST` requests, making it flexible for different integration scenarios.

### Parameters

- `logoutAll` (optional): Controls logout scope. Accepts `true`, `1`, or empty string (default: `true` for backward compatibility)
  - `true` or `1` or empty: Logout from all sessions across all applications
  - Any other value (e.g., `false`, `0`): Logout from current session only

### Authentication

This endpoint requires the user to be authenticated. Use any authentication method supported by Casdoor:

- **Access token**: Include the access token in the `Authorization` header
- **Session cookie**: Use the session cookie that was set during login
- **Client credentials**: Use the application's client ID and secret for machine-to-machine scenarios

For more details on authentication methods, see the [Casdoor Public API](/docs/basic/public-api#how-to-authenticate) documentation.

### Request Examples

#### Logout from All Sessions (Default)

```bash
curl -X POST https://door.casdoor.com/api/sso-logout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Or explicitly specify logoutAll=true
curl -X POST "https://door.casdoor.com/api/sso-logout?logoutAll=true" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Logout from Current Session Only

```bash
curl -X POST "https://door.casdoor.com/api/sso-logout?logoutAll=false" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Using Session Cookie

```bash
curl -X POST https://door.casdoor.com/api/sso-logout \
  --cookie "casdoor_session_id=abc123def456"
```

#### Using JavaScript Fetch API

```javascript
// Logout from all sessions
fetch('https://door.casdoor.com/api/sso-logout', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  },
  credentials: 'include'
})
  .then(response => response.json())
  .then(data => {
    console.log('Logout successful:', data);
    window.location.href = '/login';
  })
  .catch(error => {
    console.error('Logout failed:', error);
  });

// Logout from current session only
fetch('https://door.casdoor.com/api/sso-logout?logoutAll=false', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  },
  credentials: 'include'
})
  .then(response => response.json())
  .then(data => {
    console.log('Logged out from current session:', data);
    window.location.href = '/login';
  });
```

### Response

The API returns a standard Casdoor response:

```json
{
  "status": "ok",
  "msg": "",
  "data": ""
}
```

**Response Fields:**

- `status`: Indicates whether the operation was successful (`"ok"`) or failed (`"error"`)
- `msg`: Contains an error message if the operation failed, otherwise empty
- `data`: Additional data returned by the API, typically empty for logout operations

## Implementing SSO Logout in Your Application

### Using Casdoor SDKs

Most Casdoor SDKs provide built-in support for SSO logout. Here are examples for different platforms:

#### Go SDK

```go

func logout(w http.ResponseWriter, r *http.Request) {
    // Get the access token from the session or request
    token := getAccessTokenFromSession(r)
    
    // Call the SSO logout endpoint
    err := casdoorsdk.Logout(token)
    if err != nil {
        http.Error(w, "Logout failed", http.StatusInternalServerError)
        return
    }
    
    // Clear local session
    clearSession(w, r)
    
    // Redirect to login page
    http.Redirect(w, r, "/login", http.StatusFound)
}
```

#### JavaScript SDK

```javascript

const CasdoorSDK = new Sdk({
  serverUrl: "https://door.casdoor.com",
  clientId: "YOUR_CLIENT_ID",
  appName: "YOUR_APP_NAME",
  organizationName: "YOUR_ORG_NAME",
});

async function handleLogout() {
  try {
    // Call the SSO logout endpoint
    await CasdoorSDK.logout();
    
    // Clear local state
    localStorage.removeItem('casdoor_token');
    sessionStorage.clear();
    
    // Redirect to login page
    window.location.href = '/login';
  } catch (error) {
    console.error('Logout failed:', error);
  }
}
```

#### Python SDK

```python
from casdoor import CasdoorSDK

sdk = CasdoorSDK(
    endpoint="https://door.casdoor.com",
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    certificate="YOUR_CERT",
    org_name="YOUR_ORG_NAME",
    app_name="YOUR_APP_NAME",
)

def logout(access_token):
    try:
        # Call the SSO logout endpoint
        result = sdk.logout(access_token)
        
        if result['status'] == 'ok':
            # Clear local session
            clear_session()
            return True
        else:
            print(f"Logout failed: {result['msg']}")
            return False
    except Exception as e:
        print(f"Logout error: {e}")
        return False
```

### Manual Implementation

Without a Casdoor SDK, implement SSO logout by calling the logout endpoint:

```javascript
async function logout() {
  const accessToken = localStorage.getItem('access_token');
  
  try {
    // Use the full Casdoor server URL in your application
    const response = await fetch('https://door.casdoor.com/api/sso-logout', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      credentials: 'include'
    });
    
    const result = await response.json();
    
    if (result.status === 'ok') {
      // Clear local storage
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_info');
      sessionStorage.clear();
      
      // Redirect to login page
      window.location.href = '/login';
    } else {
      console.error('Logout failed:', result.msg);
    }
  } catch (error) {
    console.error('Logout error:', error);
  }
}
```

## Best Practices

### 1. Clear Local State

After calling the SSO logout endpoint, make sure to clear all local authentication state:

- Remove access tokens from local storage or session storage
- Clear any cached user information
- Invalidate any local session cookies
- Reset application state to the logged-out state

### 2. Handle Logout Errors Gracefully

Even if the SSO logout endpoint fails, you should still clear local authentication state to ensure the user appears logged out from your application:

```javascript
async function logout() {
  try {
    await callSSOLogout();
  } catch (error) {
    console.error('SSO logout failed, clearing local state anyway:', error);
  } finally {
    // Always clear local state
    clearLocalAuthenticationState();
    redirectToLogin();
  }
}
```

### 3. Provide User Feedback

Give users clear feedback about the logout process:

```javascript
async function logout() {
  // Show loading indicator
  showLoadingIndicator('Logging out...');
  
  try {
    await callSSOLogout();
    showSuccessMessage('Logged out successfully');
  } catch (error) {
    showErrorMessage('Logout failed, but you have been logged out locally');
  } finally {
    clearLocalAuthenticationState();
    // Redirect after a short delay to allow users to see the message
    setTimeout(() => redirectToLogin(), 1000);
  }
}
```

### 4. Implement Logout Timeout

Set a reasonable timeout for the logout request to prevent users from waiting indefinitely:

```javascript
async function logout() {
  const timeout = 5000; // 5 seconds
  
  try {
    await Promise.race([
      callSSOLogout(),
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Logout timeout')), timeout)
      )
    ]);
  } catch (error) {
    console.error('Logout error:', error);
  } finally {
    clearLocalAuthenticationState();
    redirectToLogin();
  }
}
```

## Security Considerations

### 1. Verify Logout Notification Signatures

Always verify the HMAC-SHA256 signature of logout notifications to prevent malicious logout requests. The signature is computed using your application's client secret and includes all critical fields (owner, name, nonce, timestamp, sessionIds, accessTokenHashes). Reject any notification with an invalid signature.

### 2. Check Notification Timestamp

Implement timestamp validation to prevent replay attacks. Reject notifications that are too old (e.g., more than 5 minutes old):

```javascript
function isNotificationValid(notification) {
  const maxAge = 5 * 60 * 1000; // 5 minutes in milliseconds
  const now = Date.now();
  const notificationTime = notification.timestamp * 1000; // Convert to milliseconds
  
  if (now - notificationTime > maxAge) {
    console.error('Notification is too old, possible replay attack');
    return false;
  }
  
  return verifyLogoutNotification(notification, clientSecret);
}
```

### 3. Secure Communication

Always use HTTPS when calling the SSO logout endpoint to prevent token interception:

```javascript
// ✅ Good: Uses HTTPS
const logoutUrl = 'https://door.casdoor.com/api/sso-logout';

// ❌ Bad: Uses HTTP (insecure)
const logoutUrl = 'http://door.casdoor.com/api/sso-logout';
```

### 4. Token Validation

Casdoor validates the access token before processing the logout request. Ensure your token is valid and has not expired before making the logout call.

### 5. CSRF Protection

When using session cookies for authentication, ensure CSRF protection is enabled to prevent unauthorized logout requests:

```javascript
// Include CSRF token in the request headers
// Replace with your actual Casdoor server URL
fetch('https://door.casdoor.com/api/sso-logout', {
  method: 'POST',
  headers: {
    'X-CSRF-Token': getCsrfToken()
  },
  credentials: 'include'
});
```

### 6. Protect Client Secrets

Keep your application's client secret secure. It's used to sign logout notifications, so if compromised, attackers could forge valid logout requests. Store it securely (e.g., in environment variables or secret management systems) and never expose it in client-side code.

### 7. Audit Logging

Consider logging logout events for security auditing and compliance:

```go
func logout(userID string, token string) error {
    // Call SSO logout
    err := casdoorsdk.Logout(token)
    
    // Log the logout event
    auditLog.Info(map[string]interface{}{
        "event": "sso_logout",
        "user_id": userID,
        "timestamp": time.Now(),
        "success": err == nil,
    })
    
    return err
}
```

## Troubleshooting

### Logout Not Working Across All Applications

If users remain logged in to some applications after SSO logout:

1. **Verify application integration**: Ensure all applications are properly integrated with Casdoor and use the same organization
2. **Check token validation**: Make sure all applications validate tokens on each request
3. **Review session management**: Applications should not rely solely on local sessions; they must validate tokens with Casdoor

### Token Still Valid After Logout

If access tokens or refresh tokens remain valid after logout:

1. **Verify the logout endpoint**: Ensure you're calling the correct endpoint (`/api/sso-logout`)
2. **Check authentication**: Make sure you're sending valid authentication credentials with the logout request
3. **Review token caching**: Ensure applications don't cache token validation results

After SSO logout, both access tokens and refresh tokens are invalidated. The token records remain in the database with `ExpiresIn` set to 0, but Casdoor's token introspection and refresh token endpoints will reject them. When a client attempts to use a refresh token after logout, they'll receive an `invalid_grant` error with the message "refresh token is invalid, expired or revoked". This ensures complete session termination and prevents token reuse even if the token hasn't reached its original expiration time.

### Logout Endpoint Returns Error

Common error scenarios:

- **401 Unauthorized**: The access token is invalid or expired. Clear local state and redirect to login.
- **403 Forbidden**: The user doesn't have permission to logout. This is rare and may indicate a configuration issue.
- **500 Internal Server Error**: Server-side error. Log the error and clear local state anyway.

```javascript
async function logout() {
  try {
    // Replace with your actual Casdoor server URL
    const response = await fetch('https://door.casdoor.com/api/sso-logout', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (!response.ok) {
      console.error(`Logout failed with status: ${response.status}`);
      // Clear local state anyway
    }
  } catch (error) {
    console.error('Logout error:', error);
  } finally {
    clearLocalAuthenticationState();
    redirectToLogin();
  }
}
```

## Related Documentation

- [Single Sign-On (SSO)](/docs/session/single-sign-on): Learn how to enable SSO for your applications
- [Casdoor Public API](/docs/basic/public-api): Complete API reference including authentication methods
- [Tokens](/docs/token/overview): Understand how Casdoor manages access tokens and sessions
- [OAuth 2.0](/docs/how-to-connect/oauth): Learn about OAuth 2.0 flows supported by Casdoor



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/session/management.md
================================================================================

---
title: Session management
description: View and terminate user sessions in the Casdoor admin panel.
keywords: [session, management, delete, multi-session, logout]
authors: [hsluoyz]
---

In the Casdoor admin panel, view active sessions and end them individually or in bulk. Admins and users can control which devices or browsers stay signed in.

## Viewing sessions

1. Open **Sessions** in the sidebar.
2. You’ll see all active sessions for the organization, with user, application, creation time, and session IDs.

Each row is one user–application pair; multiple session IDs in a row mean the user is signed in from more than one device or browser.

## Deleting a single session

Ending a specific session revokes access from that device or browser only. Use this to:

- Revoking access from a lost or stolen device
- Terminating a suspicious login from an unfamiliar location
- Managing sessions across multiple devices individually
- Logging out from specific browsers while staying logged in elsewhere

### Steps

On the Sessions list, each session’s IDs appear as tags. To remove one:

1. Find the session row.
2. Click the × on the session ID tag you want to end.
3. Confirm in the dialog.

That session is invalidated immediately; the user is signed out on that device or browser only.

### Current session protection

The session you are currently using cannot be deleted. Attempting to delete it shows:

> "session id {'{'}session-id{'}'} is the current session and cannot be deleted"

Use the normal logout flow to sign out of your current session.

## Deleting all sessions

When you delete a session record entirely (not just a single session ID), Casdoor handles it intelligently:

- If the session record has multiple session IDs, deleting one ID removes just that session
- If only one session ID remains and you delete it, the entire session record is removed
- Delete the entire session record with the row's delete button

Deleting all sessions for a user effectively logs them out from all devices and browsers simultaneously.

## API for Session Deletion

Developers can programmatically delete sessions using the Casdoor API:

### Delete a Specific Session ID

To delete a single session ID from a session record:

```bash
POST /api/delete-session?sessionId={'{'}session-id{'}'}
Content-Type: application/json

{
  "owner": "organization-name",
  "name": "username",
  "application": "app-name"
}
```

The `sessionId` parameter specifies which session ID to remove. If this is the last session ID for the record, the entire session record is deleted.

### Delete All Session IDs

To delete all session IDs for a user-application pair:

```bash
POST /api/delete-session
Content-Type: application/json

{
  "owner": "organization-name",
  "name": "username",
  "application": "app-name"
}
```

Omit the `sessionId` parameter to delete all sessions. The current active session cannot be deleted this way; the API returns an error.

## Session Cleanup

Casdoor automatically cleans up expired sessions based on your session timeout configuration. You don't need to manually delete expired sessions unless you want to revoke access immediately before the automatic expiration.

## Best Practices

**Use individual session deletion for security incidents**: If you detect suspicious activity from a specific device, delete just that session ID rather than logging the user out everywhere.

**Educate users on session management**: Users should know how to view their active sessions and remove ones they don't recognize. Consider adding a "My Sessions" page in your application that integrates with Casdoor's session API.

**Monitor session patterns**: Unusual numbers of concurrent sessions may indicate account sharing or credential compromise. Regular session audits can help identify security issues.

**Clean up old sessions regularly**: While Casdoor handles automatic expiration, periodically review and clean up abandoned sessions to maintain good hygiene in your session database.

## Related Documentation

- [Single Sign-Out](/docs/session/single-sign-out): Learn about SSO logout functionality
- [Session Overview](/docs/session/overview): Understand session concepts in Casdoor
- [Tokens](/docs/token/overview): How sessions relate to access tokens



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/session/single-sign-on.md
================================================================================

---
title: Single sign-on (SSO)
description: Let users sign in once and access all apps in the organization without signing in again.
keywords: [SSO, single sign-on, auto sign-in, silent sign-in]
authors: [leo220yuyaodog]
---

## Overview

With multiple applications in one organization, enable **single sign-on (SSO)** so users sign in once and are automatically signed in for other apps in the same org.

To enable SSO:

1. Set the **Home** URL (application home or login page).
2. Enable **Auto Sign-In** on the application.
3. Implement **Silent Sign-In** on your app’s home page so it can complete login when opened with the SSO link.

:::note
Without auto sign-in, users see a picker to choose the current user or another account. With auto sign-in, the already-signed-in user is used and the picker is skipped.
:::

## Configuration

1. Set **Home** to your application’s home page or login URL.

![sso_home.png](/img/how-to-connect/single-sign-on/sso_home.png)
2. Enable **Auto Sign-In**.

![sso_signin.png](/img/how-to-connect/single-sign-on/sso_signin.png)

## Silent sign-in

SSO works by opening your app’s home URL with a query parameter. Your app must detect that and trigger login. The [casdoor-react-sdk](https://github.com/casdoor/casdoor-react-sdk) provides a `SilentSignin` component; see [use-in-react](https://github.com/casdoor/casdoor-react-sdk#use-in-react).

:::info
**Flow:** The link to your home page includes `silentSignin=1`. On load, if `silentSignin === 1`, render the `SilentSignin` component so it starts the login; with auto sign-in enabled, the user is signed in without extra clicks. Silent sign-in only runs when the user’s organization matches the application, avoiding duplicate or wrong sign-ins.
:::

## Popup sign-in

**Popup sign-in** opens a small window for Casdoor login; after success it posts the auth result to the opener and closes. Use `popupSignin()` from [casdoor-js-sdk](https://github.com/casdoor/casdoor-js-sdk); demo: [casdoor-nodejs-react-example](https://github.com/casdoor/casdoor-nodejs-react-example). The home URL is called with `popup=1`; Casdoor sends `code` and `state` to the opener, and the main window exchanges them for a token via the SDK.

## Using SSO

The configuration is complete. Below, we will show you how to use auto login.

:::info

Make sure your application can redirect to the user's profile page. The [getMyProfileUrl(account, returnUrl)](https://github.com/casdoor/casdoor-js-sdk#get-my-profile-page-url) API is provided in our SDK for each language.

:::

Open the profile page and go to **Home** (`/`). The application list for the organization is shown there. It's worth noting that only users in organizations other than "built-in" can see the application list on the "Home" page. All the global administrators (those in the "built-in" organization) cannot see it.

![sso_homepage.png](/img/how-to-connect/single-sign-on/sso_homepage.png)

Click on a tile in the application list, and it will jump to the homepage URL of that application with the GET parameter `?silentSignin=1`. It will automatically log into the application if the application has integrated with Casdoor SSO (so it will recognize the `?silentSignin=1` parameter and perform a silent login in the background).

## SSO Logout

When using SSO, you might need to log a user out from all applications simultaneously. Casdoor provides an SSO logout endpoint that terminates all active sessions and expires all tokens for a user across all applications in the organization.

To implement SSO logout in your application, make a request to the `/api/sso-logout` endpoint. This endpoint will ensure the user is completely logged out from all integrated applications. For detailed information about the SSO logout API, including authentication methods and request examples, see the [Single Sign-Out](/docs/session/single-sign-out) documentation.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/session/overview.md
================================================================================

---
title: Overview
description: Understanding sessions in Casdoor
keywords: [session, authentication, token, login]
authors: [hsluoyz]
---

Casdoor manages authentication through sessions, which represent active login states across applications. Each session tracks a user's authenticated connection to one or more applications in an organization.

## What is a session?

A session represents an authenticated user state. When a user signs in to an application, Casdoor creates a session record that includes:

- **Session ID**: A unique identifier for each login instance
- **User information**: The authenticated user's identity
- **Application context**: Which application the user logged into
- **Creation time**: When the session was established
- **Expiration**: When the session will automatically terminate

Users can have multiple active sessions simultaneously - for example, logging in from different devices or browsers. Each session is tracked independently, allowing granular control over user access.

## Session lifecycle

Sessions move from creation to termination as follows:

**Creation**: When a user authenticates successfully (OAuth, SAML, username/password, etc.), Casdoor creates a new session and assigns a unique session ID.

**Active**: While active, the session grants access to protected resources without re-authenticating. Each request validates the session so expired or revoked sessions are rejected.

**Expiration**: Sessions expire after a configurable period of inactivity or at maximum lifetime. Casdoor cleans up expired sessions automatically.

**Termination**: Sessions can be ended by logout (user or admin). When terminated, all associated session IDs are invalidated immediately.

## Multi-session support

Casdoor supports multiple concurrent sessions per user. This is useful when:

- Users access applications from multiple devices (phone, tablet, desktop)
- Users maintain separate sessions in different browsers or private browsing windows
- Backend services need to manage sessions for different application instances

Each session is tracked separately with its own session ID. This allows users to selectively terminate specific sessions without affecting their other active logins - for example, logging out from a work computer while staying logged in on a mobile device.

## Session storage

Session data is stored in Casdoor's database and is associated with:

- The user who created the session
- The application through which they authenticated
- The organization context

Session IDs are stored as arrays, allowing a single session record to track multiple concurrent logins for the same user-application pair.

## Related topics

- [Session management](/docs/session/management): View and manage user sessions
- [Single sign-on](/docs/session/single-sign-on): SSO across multiple applications
- [Single sign-out](/docs/session/single-sign-out): Logout across all sessions
- [Tokens](/docs/token/overview): Sessions and access tokens



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/webhooks/overview.md
================================================================================

---
title: Webhooks
description: Send Casdoor events to your application via HTTP webhooks for real-time integration.
authors: [huang-yilong]
keywords: [webhook, event-driven, API, integration]
---

Casdoor can notify your application when events occur by sending HTTP `POST` requests with a JSON payload to a URL you configure. Use webhooks to react to sign-ups, logins, logouts, profile updates, and many other events.

## How webhooks work

When an event occurs in Casdoor:

1. Casdoor sends a `POST` request to the specified webhook URL.
2. The request contains a JSON payload with event details.
3. Your application processes the payload and executes relevant actions based on the event type.

### Supported events

Webhooks can be subscribed to a wide set of events, grouped by area:

#### Authentication & Session Events

- `signup`, `login`, `logout` - User authentication flows
- `sso-logout`, `unlink` - Single sign-on and account unlinking
- `new-user` - Custom event for new user creation

#### Resource Management Events

Standard CRUD operations (`add-*`, `update-*`, `delete-*`) are available for all core resources including organizations, groups, users, applications, providers, and certificates. Additional resources like roles, permissions, models, adapters, enforcers, sessions, tokens, products, payments, and pricing also support these operations. Webhooks can track changes to syncers, forms, invitations, LDAP configurations, orders, tickets, and transactions as well.

#### Specialized Operations

**User Management:** `add-user-keys`, `remove-user-from-group`, `upload-users`, `check-user-password`, `set-password`, `reset-email-or-phone`, `verify-identification`

**Bulk Operations:** `upload-groups`, `upload-roles`, `upload-permissions`, `upload-resource`

**Order Processing:** `place-order`, `cancel-order`, `pay-order`

**Payment Handling:** `invoice-payment`, `notify-payment`

**Invitations:** `send-invitation`, `verify-invitation`

**Support Systems:** `add-ticket-message`

**Synchronization:** `run-syncer`, `test-syncer-db`, `sync-ldap-users`

**Access Control:** `enforce`, `batch-enforce`, `add-policy`, `update-policy`, `remove-policy`, `add-record`

**Multi-Factor Authentication:** `delete-mfa`, `set-preferred-mfa`, `mfa/setup/initiate`, `mfa/setup/verify`, `mfa/setup/enable`

**WebAuthn:** `webauthn/signup/begin`, `webauthn/signup/finish`, `webauthn/signin/begin`, `webauthn/signin/finish`

**OAuth & Token Management:** `login/oauth/access_token`, `login/oauth/refresh_token`, `login/oauth/introspect`

**Verification & Communication:** `send-verification-code`, `verify-code`, `verify-captcha`, `send-email`, `send-sms`, `send-notification`

**SAML:** `acs`, `saml/metadata`

**System Operations:** `run-casbin-command`, `refresh-engines`, `health`, `metrics`, `callback`, `device-auth`, `faceid-signin-begin`, `user`, `userinfo`

Each event includes contextual information in the webhook payload, allowing you to implement custom logic based on the specific action that triggered the webhook.

## Setting up a webhook

1. In your Casdoor instance, go to **Settings** → **Webhooks**.
2. Click **Add Webhook**.
3. Enter the **Webhook URL** that will receive events.
4. Select one or more events to subscribe to.
5. (Optional) Add custom headers (e.g. for authentication).
6. Save. Casdoor will send events to the URL from then on.

## Filtering webhook payloads

When working with webhooks, you might not always need the complete record data. Casdoor allows you to filter the payload by configuring **ObjectFields** for each webhook. This feature is particularly valuable when you have privacy concerns, bandwidth constraints, or when your endpoint only processes specific fields.

The ObjectFields configuration accepts either "All" to receive the complete record, or a list of specific field names you want to include. When you specify field names, Casdoor will send only those fields in the webhook payload, reducing payload size and exposing only the data your application needs.

If you configure multiple webhooks with different ObjectFields settings, each webhook operates independently. For example, one webhook might receive only user IDs and timestamps, while another receives full user profiles. Casdoor ensures that the filtering applied to one webhook doesn't affect the data sent to others, even when they're triggered by the same event.

## Example payload

Example JSON sent to your webhook on login:

```json
{
  "event": "login",
  "timestamp": 1709452800,
  "user": {
    "id": "12345",
    "username": "johndoe",
    "email": "johndoe@example.com"
  }
}
```

Your application should parse this payload and perform necessary actions, such as logging the event or notifying another service.

## Testing webhooks

Before production, test with:

- **[Beeceptor](https://beeceptor.com/)** – Allows you to create a custom webhook URL and inspect incoming requests.
- **[Webhook.site](https://webhook.site/)** – Provides an instant webhook endpoint for testing.

### Example with Beeceptor

1. Create an endpoint at [Beeceptor](https://beeceptor.com/).
2. Copy the URL and set it as the webhook URL in Casdoor.
3. Trigger an event (e.g. sign in to Casdoor).
4. Inspect the request in Beeceptor’s dashboard.

## Handling webhooks in your application

Your server should be able to process incoming webhook requests. Below is a simple example in Node.js:

```javascript
const express = require('express');
const app = express();

app.use(express.json());

app.post('/webhook', (req, res) => {
  console.log('Received webhook:', req.body);
  res.status(200).send('Webhook received');
});

app.listen(3000, () => console.log('Server running on port 3000'));
```

Validate incoming webhook requests (e.g. signatures or shared secrets) and test with Beeceptor or Webhook.site before using webhooks in production.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/developer-guide/swagger.md
================================================================================

---
title: Generating Swagger docs
description: Generate Swagger/OpenAPI docs for Casdoor APIs using the modified bee tool.
keywords: [bee, swagger, API docs]
authors: [ComradeProgrammer]
---

Casdoor is built on **beego**, which uses the **bee** CLI to generate Swagger files. The default bee does not group APIs by tag; Casdoor uses a [modified bee](https://github.com/casbin/bee) that supports the `@Tag` label so APIs are grouped in the generated docs.

## Comment format

Use the same comment style as standard bee; the only extra requirement is **@Tag** so APIs are grouped. Example:

```go
// @Title Login
// @Tag Login API
// @Description login
// @Param   oAuthParams     query    string  true        "oAuth parameters"
// @Param   body    body   RequestForm  true        "Login information"
// @Success 200 {object} controllers.api_controller.Response The Response object
// @router /login [post]
func (c *ApiController) Login() {
```

APIs with the same `@Tag` appear in the same group in the Swagger output.

## Generate Swagger files

1. Add comments in the format above (including `@Tag`) to your API handlers.
2. Clone the modified bee: [https://github.com/casbin/bee](https://github.com/casbin/bee).
3. Build bee in the repo root:

   ```shell
   go build -o mybee .
   ```

4. Copy `mybee` into the Casdoor project root.
5. From the Casdoor root, run:

   ```bash
   mybee generate docs
   ```

6. (Optional) Generate docs for specific tags or APIs:

   ```bash
   mybee generate docs --tags "Adapter API"
   mybee generate docs --tags "Adapter API,Login API"
   mybee generate docs --apis "add-adapter"
   mybee generate docs --apis "add-adapter,delete-adapter"
   ```

   Use a comma `,` only when listing multiple tags or APIs.

Generated Swagger files will appear in the Casdoor project.



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/developer-guide/frontend.md
================================================================================

﻿---
title: Frontend
description: Casdoor web UI source layout and how to run or customize it.
keywords: [frontend, React, CRA, development]
authors: [hsluoyz]
---

The Casdoor web UI lives in the **`/web`** directory: `https://github.com/casdoor/casdoor/tree/master/web`. It is a [Create React App (CRA)](https://create-react-app.dev/) project with this layout:

| File/Directory   | Description |
|------------------|-------------|
| `public`         | Root HTML and static assets |
| `src`            | Application source code |
| `craco.config.js` | Craco config (e.g. theme; default primary is blue) |
| `crowdin.yml`    | Crowdin i18n config |
| `package.json`   | NPM/Yarn dependencies |
| `yarn.lock`      | Lock file |

Under **`/src`**:

| File/Directory          | Description |
|-------------------------|-------------|
| `account`               | “My profile” page for signed-in users |
| `auth`                  | Auth flows: OAuth, SAML, sign-up, sign-in, forgot password |
| `backend`               | Client for the Go API (all `fetch` calls) |
| `basic`                 | Dashboard (home) and card widgets |
| `common`                | Shared UI components |
| `locales`               | i18n JSON (synced with [Crowdin](https://crowdin.com/project/casdoor-site)) |
| `App.js`                | Root and routing |
| `Setting.js`            | Shared helpers |
| `*ListPage.js` / `*EditPage.js` | List and edit pages per resource (e.g. `OrganizationListPage.js`, `OrganizationEditPage.js`) |



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/organization/mfa-items.md
================================================================================

---
title: MFA items
description: Configure which MFA methods are available and whether they are optional or required.
keywords: [organization, MFA, multi-factor authentication, 2FA]
authors: [leo220yuyaodog]
---

Admins can add **MFA items** to the organization’s account settings. Users then enable and manage MFA on their profile.

![organization-items-mfa](/img/organization/mfa/organization-items-mfa.png)

## MFA rules

For each MFA method, set:

- **Optional** — Users may enable or skip this MFA method.
- **Prompt** — Users are prompted to enable it after sign-in if they haven’t yet.
- **Required** — Users must enable this method before they can complete sign-in.

![organization-mfa-table](/img/organization/mfa/organization-mfa-table.png)

Prompt shown when MFA is set to prompt:

![mfa prompt](/img/organization/mfa/mfa-prompt.png)

When set to required, users must complete MFA setup before finishing login:

![mfa prompt](/img/organization/mfa/mfa-required.gif)

## Remember MFA

Users can choose to have MFA “remembered” for a period so they are not asked again on the same device. Configure **MFA remember time** in the organization settings (e.g. 12 hours).

![mfa remember](/img/organization/mfa/mfa-remember.png)

![mfa remember time](/img/organization/mfa/mfa-remember-time.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/organization/passwordComplexity.md
================================================================================

---
title: Password complexity
description: Configure password strength rules per organization.
keywords: [password, complexity]
authors: [leoil]
---

Each organization can enforce password complexity rules for user passwords.

## Options

| Option | Requirement |
|--------|-------------|
| **AtLeast6** | At least 6 characters. |
| **AtLeast8** | At least 8 characters. |
| **Aa123** | At least one uppercase letter, one lowercase letter, and one digit. |
| **SpecialChar** | At least one special character. |
| **NoRepeat** | No repeated characters. |

Multiple options can be enabled; all selected rules apply.

## Configuration

1. Open the organization list and click **Edit** for the organization.
2. In **Password complexity options**, select the options to enforce.

![org edit](/img/organization/password_complexity/org_edit.png)
![option selection](/img/organization/password_complexity/select_password_option.png)

## Where validation applies

- **Sign-up page** — new passwords must satisfy the rules.
- **Forgot password page** — reset passwords must satisfy the rules.
- **User edit page** — password changes must satisfy the rules.

![signup page check](/img/organization/password_complexity/sign_up_demo.gif)
![forget page check](/img/organization/password_complexity/forget_demo.gif)
![user-edit page check](/img/organization/password_complexity/user_edit_demo.gif)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/organization/organization-tree.md
================================================================================

---
title: Organization tree
description: User groups and group hierarchy within an organization.
keywords: [user, group, organization, tree]
authors: [leo220yuyaodog]
---

**Groups** are collections of users in an organization. A user can be in multiple groups.

## Group properties

- **Owner** — Owning organization
- **Name** — Unique group name
- **DisplayName**, **CreatedTime**, **UpdatedTime**
- **Type** — `Physical` or `Virtual`. A user can be in only one Physical group but multiple Virtual groups.
- **ParentGroup** — Parent group (top-level groups use the organization as parent)

## Managing groups

Groups can be managed in two places:

1. **Groups list page** — View all groups in the organization.

   ![groups list](/img/organization/organization_tree/groups_list.png)

2. **Organization list** — Click **Groups** on an organization to open the group tree.

   ![organization list](/img/organization/organization_tree/organization_tree_entry.png)

   ![groups tree](/img/organization/organization_tree/groups_tree.png)

   ![groups tree page](/img/organization/organization_tree/groups_tree.gif)

You can also assign and edit groups from a user’s profile.

![groups user](/img/organization/organization_tree/groups_user.png)



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/organization/overview.md
================================================================================

---
title: Overview
description: Organizations are the core unit in Casdoor for managing users and applications.
keywords: [organization, users, applications]
authors: [sh1luo]
---

An **organization** is the primary unit in Casdoor for managing users and applications. Once a user signs in to an organization, they can access all applications in that organization without signing in again.

When configuring [applications](/docs/application/config) and [providers](/docs/provider/overview), the chosen organization determines which users can access the application and which providers apply.

The organization’s display name (or its name if no display name is set) is used as the issuer in TOTP authenticator apps, helping users distinguish accounts when they have multiple TOTP entries.

LDAP can be configured per organization. For details, see [LDAP](/docs/ldap/overview).

Casdoor supports multiple password storage algorithms, configurable on the organization edit page. New organizations use **bcrypt** by default for secure password hashing.

| Name        | Algorithm | Description | Typical use |
| :---------- | :-------- | ----------- | :---------- |
| plain       | —         | Passwords stored in cleartext. **Not recommended for production.** | — |
| salt        | [SHA-256](https://github.com/casdoor/casdoor/blob/master/cred/sha256-salt.go) | [SHA-256](https://www.n-able.com/blog/sha-256-encryption) is a cryptographic hash function that produces a 256-bit value. | — |
| md5-salt    | [MD5](https://github.com/casdoor/casdoor/blob/master/cred/md5-user-salt.go) | [MD5](https://en.wikipedia.org/wiki/MD5) is a widely used but cryptographically weak hash (128-bit). | [Discuz!](https://www.discuz.vip/) |
| bcrypt      | [bcrypt](https://github.com/casdoor/casdoor/blob/master/cred/bcrypt.go) | [bcrypt](https://en.wikipedia.org/wiki/Bcrypt) hashes and salts passwords securely. **Default for new organizations.** | [Spring Boot](https://spring.io/projects/spring-boot), [WordPress](https://stackoverflow.com/questions/1045988/what-type-of-hash-does-wordpress-use) |
| pbkdf2-salt | [SHA-256 and PBKDF2](https://github.com/casdoor/casdoor/blob/master/cred/pbkdf2-salt.go) | [PBKDF2](https://en.wikipedia.org/wiki/PBKDF2) is a key derivation function resistant to dictionary and rainbow-table attacks. Use when importing users via the Keycloak syncer. | [Keycloak](http://keycloak.org/) |

## Password Salt Configuration

For algorithms that use salts (`salt`, `md5-salt`, `pbkdf2-salt`), set the **Password salt** on the organization edit page:

- **Organization-level salt**: When **Password salt** is set, all users in the organization share the same salt. Use this when you need consistency (e.g. compatibility with another system).
- **Per-user random salt**: When **Password salt** is left empty, Casdoor generates a unique random salt per user. This improves security by limiting the impact of precomputed hash tables.

**Recommendation:** Use per-user salt for new deployments to strengthen protection against rainbow-table attacks. Salts are stored with the password hash and managed by Casdoor.

## Use email as username

Organizations can enable **Use email as username** so that the user’s email is used as their username when the username field is not shown at sign-up. This simplifies registration by avoiding a separate username.

When enabled:

- At sign-up, if the username field is hidden, the email is used as the username.
- If a user changes their email, their username is updated to match.
- Email and username stay in sync.

To enable it, check **Use email as username** on the organization edit page.

:::tip

Besides signing in through an application (which redirects to Casdoor for SSO), users can sign in directly on an organization’s login page: `/login/<organization_name>` (e.g. `https://door.casdoor.com/login/casbin` on the demo site).

If a user signs in via an organization-specific URL, Casdoor remembers that organization. When the session expires, they are redirected back to that organization’s login page for a simpler re-authentication flow.

:::



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/organization/accountCustomization.md
================================================================================

---
title: Account customization
description: Control visibility and edit permissions for each user account field.
keywords: [account customization, view rule, modify rule]
authors: [leo220yuyaodog]
---

You can customize **account items** per organization: whether each field is visible and who can view or modify it. These settings apply to every member’s profile/home page in that organization.

## Configuring account items

Each account item has four settings:

| Column Name | Selectable Value | Description |
| :---------: | :--------------: | ----------- |
|    Name     |        -         | Account item name. |
|   Visible   | `True` / `False` | Select whether this account item is visible on the user home page. |
|  ViewRule  |    Rule Items    | Select a rule to use when viewing the account item. Controls who can **view** this field. |
| ModifyRule |    Rule Items    | Select a rule to use when modifying the account item. Controls who can **edit** this field. |

### View rule and modify rule

- **View rule** — Who can see this field (e.g. email, phone).
- **Modify rule** — Who can edit this field.

This is separate from [Permissions](/docs/permission/overview), which control access to applications and resources; view/modify rules apply to individual profile fields.

### Steps

1. Navigate to **Organizations** in the Casdoor sidebar
2. Click on your organization to open the **Edit Organization** page
3. Scroll down to the **Account items** section

   ![account_customize.png](/img/organization/account_customize.png)

4. For each item you can:

   - **Set visibility** — Show or hide the field on the user home page.

   ![account_visible.png](/img/organization/account_visible.png)

   - **Set view and modify rules** — Who can view or edit the field.

   ![account_rule.png](/img/organization/account_rule.png)

### Rule options

- **Public** — Anyone can view or modify this field for any user.
- **Self** — Users can only view or modify their own value (matched by user ID, or by org + username if ID is missing).
- **Admin** — Only organization admins can view or modify this field.

### Example patterns

Here are some common configuration patterns:

| Field | View Rule | Modify Rule | Use Case |
|-------|-----------|-------------|----------|
| Name | Public | Self | Everyone can see names, but users can only change their own |
| Email | Self | Self | Users can only see and change their own email |
| Phone | Admin | Admin | Only admins can see and change phone numbers (for privacy) |
| Display name | Public | Self | Public profile name visible to all |
| Password | Self | Self | Users can only change their own password |

:::tip

Use **Admin** rules for sensitive fields like phone numbers, addresses, or internal identifiers that should only be managed by administrators.

:::

:::note

These field-level permissions work in conjunction with the broader [Permission system](/docs/permission/overview) in Casdoor. The Permission system controls access to applications and API resources, while View rule and Modify rule control access to specific user profile fields within the **Edit Organization** page configuration.

:::

## Account Table

Below are all the fields in the account item. For field descriptions, see [User](/docs/user/overview).

- `Organization`
- `ID`
- `Name`
- `Display name`
- `Avatar`
- `User type`
- `Password`
- `Email`
- `Phone`
- `Country code`
- `Country/Region`
- `Location`
- `Affiliation`
- `Title`
- `ID card type`
- `ID card`
- `Real name` - The user's verified real name (locked after ID verification)
- `ID verification` - Controls visibility and access to the verify identity button
- `Homepage`
- `Bio`
- `Tag`
- `Signup application`
- `Register type`
- `Register source`
- `Roles`
- `Permissions`
- `Groups`
- `3rd-party logins`
- `Properties`
- `Is admin`
- `Is forbidden`
- `Is deleted`
- `Multi-factor authentication`
- `WebAuthn credentials`
- `Managed accounts`
- `MFA accounts`



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/organization/passwordObfuscator.md
================================================================================

---
title: Password obfuscator
description: Encrypt password parameters in login and set-password APIs.
keywords: [password, obfuscator, AES, DES]
authors: [ZhaoYP-2001]
---

The **Password obfuscator** option encrypts password parameters for the login and set-password APIs before they are sent to the server. You choose the algorithm and (optionally) the key at the organization level.

## Configuration

On the organization edit page, set **Password obfuscator**:

![password_obfuscator](/img/organization/password_obfuscator/password_obfuscator.png)

| Option | Behavior |
|--------|----------|
| **Plain** | Passwords are sent in plain text. |
| **AES** | Passwords are encrypted with AES before transmission. |
| **DES** | Passwords are encrypted with DES before transmission. |

When you switch to AES or DES, Casdoor generates a key and fills **Password obf key**. You can override it with your own key:

![password_obf_key](/img/organization/password_obfuscator/password_obf_key.png)

:::note
If the key does not match the algorithm’s requirements, Casdoor shows an error with the expected key format (regex).
:::

## API support

| API | Encrypted fields |
|-----|------------------|
| **Login** (`/api/login`) | `password` |
| **Set password** (`/api/set-password`) | `oldPassword`, `newPassword` |

With obfuscation enabled, the Casdoor frontend encrypts these fields before sending; the backend decrypts with the configured key and algorithm, then processes them as usual.

### Backward compatibility

The set-password API accepts both obfuscated and plaintext passwords. If obfuscation is not configured or decryption fails, it falls back to plaintext. This keeps compatibility with:

- SDKs that do not yet support obfuscation
- Direct API calls using plaintext
- Existing integrations

Demo:



================================================================================
SOURCE: src/extraction/local-docs/casdoor-website/docs/organization/customize-theme.md
================================================================================

---
title: Customize theme
description: Set primary color and border radius at global, organization, or application level.
keywords: [theme, organization, application]
authors: [leo220yuyaodog]
---

Themes control primary color and border radius so you can match your brand. Casdoor supports three levels:

| Level | Where to set | Applies to |
|-------|----------------|------------|
| **Global** | In Casdoor source only (no UI). | Any org that uses the global theme. |
| **Organization** | Organization edit page. | All Casdoor after-login pages for that org, and entry pages (sign-in, sign-up, forgot password, etc.) of applications that follow the org theme. |
| **Application** | Application edit page. | Entry pages of that application only. |

## Organization theme

Edit the organization and use the theme controls (primary color, border radius, etc.). Changes apply to that organization’s pages and to applications following the org theme.

![edit theme](/img/organization/edit_theme.gif)

:::info
If you are editing the same organization you are logged in as, changes apply immediately. Otherwise, sign in to that organization to see the updated theme.
:::

## Application theme

Applications use the same theme editor. You can preview the theme in the application’s preview panel.

![preview](/img/organization/application_preview.png)
