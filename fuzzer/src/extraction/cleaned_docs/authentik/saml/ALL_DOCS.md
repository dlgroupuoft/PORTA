

================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/userinfo-endpoint.mdx
================================================================================

---
title: UserInfo endpoint
sidebar_custom_props:
    termName: UserInfo endpoint
    tags:
        - OAuth2/OIDC
    shortDescription: OIDC endpoint returning user claims.
    longDescription: Returns standardized claims about the authenticated user when called with a valid access token.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/saml/index.md
================================================================================

---
title: SAML Provider
---

The SAML provider allows you to integrate with Service Providers using the SAML2 protocol. It supports [importing and exporting SAML metadata](#saml-metadata), [signed requests](#certificates) and uses [property mappings](../property-mappings/index.md#saml-property-mappings) to align, or "map", Service Provider and authentik attributes.

Refer to our documentation to learn how to [create a SAML provider](./create-saml-provider.md).

## SAML bindings and endpoints

Bindings define how SAML messages are exchanged between an Identity Provider (IdP) and a Service Provider (SP), typically a service or application. Both IdPs and SPs define various endpoints in their metadata, each associated with a specific SAML binding.

A binding defines how SAML messages are transported over network protocols. In authentik, you can select one of two SAML bindings: `HTTP Redirect` or `HTTP POST`.

Endpoint URLs specify where and how the messages are sent according to that binding. The table below shows the supported endpoints for each binding:

| Endpoint                  | URL                                                          |
| ------------------------- | ------------------------------------------------------------ |
| SSO (Redirect binding)    | `/application/saml/<application_slug>/sso/binding/redirect/` |
| SSO (POST binding)        | `/application/saml/<application_slug>/sso/binding/post/`     |
| SSO (IdP-initiated login) | `/application/saml/<application_slug>/sso/binding/init/`     |
| SLO (Redirect binding)    | `/application/saml/<application_slug>/slo/binding/redirect/` |
| SLO (POST binding)        | `/application/saml/<application_slug>/slo/binding/post/`     |
| Metadata Download         | `/application/saml/<application_slug>/metadata/`             |

## SAML metadata

SAML Metadata ensures that SAML single sign-on works reliably by exchanging and maintaining identity and connection information. SAML metadata is an XML document that defines how IdPs and SPs securely interact for authentication. It includes information such as endpoints, bindings, certificates, and unique identifiers.

### Importing SP SAML metadata

You can [import SP SAML metadata](./create-saml-provider.md#create-a-saml-provider-from-sp-metadata-import-sp-metadata) to automatically configure a SAML provider based on the requirements of an SP.

### Exporting authentik SAML metadata

You can [export SAML metadata from an authentik SAML provider](./create-saml-provider.md#export-authentik-saml-provider-metadata) to an SP to automatically provide important endpoint and certificate information to the SP.

## Certificates

Certificates are vital for trust and security during SAML authentication and are used for several purposes.

### Signing certificates

A signing certificate allows authentik to digitally sign SAML assertions and responses. This certificate contains a private key that creates a cryptographic signature, proving the authenticity and integrity of the transmitted data. The SP then uses the corresponding public key from this certificate to verify the signature. Ensuring the response was not tampered with and that it originated from authentik.

#### Signing algorithm

Signing algorithms (such as RSA-SHA256 or ECDSA-SHA256) define the cryptographic method used for creating and validating the signatures.

#### Digest algorithm

A digest algorithm is a cryptographic hash function used to create a fixed-size hash (digest) from the data in the SAML assertion or message. authentik computes a digest value using the chosen algorithm (such as SHA-1 or SHA-256), and it is included as part of the digital signature process. The SP uses the same digest algorithm to independently compare it with the received digest to validate the integrity of the received assertion or message.

### Verification certificates

A verification certificate in authentik acts as the public key used to verify digital signatures on SAML responses and assertions from an SP. When a SAML message is received, authentik validates it by comparing the signature against its configured verification certificate, ensuring that messages originated from the SP.

### Encryption certificates

An encryption certificate is a public key certificate used by authentik to encrypt sensitive data in SAML assertions before sending them to an SP. This ensures that sensitive data within the assertion, such as user attributes and authentication details, remain confidential and can only be decrypted by the SP possessing the corresponding private key.

## SAML property mappings

During a SAML authentication process, communication between the SP and the IdP relies on property mappings to align, or "map", user attributes values between the IdP and SP.

Each SAML property mapping includes the following fields:

    - **Name**: The name of the property mapping that's displayed in the authentik admin interface.
    - **SAML Attribute Name**: The label that maps IdP user information to SP expectations. Can be a URN OID, a schema reference, or any other string.
    - **Friendly Name**: A human-friendly identifier for a SAML attribute.
    - **Expression**: The Python expression that maps an authentik user attribute to a value that an SP is expecting.

### Default SAML property mappings

The following property mappings are automatically added when you create a new SAML provider and can be removed at will.

| Property Mapping Name                                         | SAML Attribute Name                                                          |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| authentik default SAML Mapping: Email                         | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress`         |
| authentik default SAML Mapping: Groups                        | `http://schemas.xmlsoap.org/claims/Group`                                    |
| authentik default SAML Mapping: Name                          | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name`                 |
| authentik default SAML Mapping: UPN                           | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/upn`                  |
| authentik default SAML Mapping: User ID                       | `http://schemas.goauthentik.io/2021/02/saml/uid`                             |
| authentik default SAML Mapping: Username                      | `http://schemas.goauthentik.io/2021/02/saml/username`                        |
| authentik default SAML Mapping: WindowsAccountName (Username) | `http://schemas.microsoft.com/ws/2008/06/identity/claims/windowsaccountname` |

The default SAML property mappings can be viewed on the **Property Mappings** page of the admin interface by disabling the **Hide managed mappings** toggle.

### Custom SAML property mappings

If there is not already a property mapping that maps the user attributes that your SP requires, you can [create a custom property mapping](../property-mappings/) or edit one of the existing mappings.

For example, some SPs require users' first name (givenname) and last name (surname) attributes to be provided separately. However, the `authentik default SAML Mapping: Name` property mapping returns both attributes as one string. The following custom property mappings can be useful in such cases:

#### `surname`

- SAML Attribute Name: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname`
- Expression:

    ```python
    return request.user.name.rsplit(" ", 1)[-1]
    ```

#### `givenname`

- SAML Attribute Name: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname`
- Expression:

    ```python
    return request.user.name.split(" ", 1)[0]
    ```

## NameID

The NameID attribute acts as a unique identifier for a user. While other attributes might change (givenname, email address, etc) the NameID attribute is persistent and should never change. When the IdP sends a SAML assertion to the SP, the NameID is the unique identifier used to represent a specific user in the assertion. It's not used for authentication itself, only for identification purposes in the assertion.

### NameID property mapping

In authentik, it's possible to configure which property mapping will be used to create the NameID value. The **NameID property mapping** field on a SAML provider can be set to any property mapping that's enabled on a SAML provider. When left empty, the NameID Policy of the incoming SP request will be respected.

### Default NameID policy

In authentik, it's also possible to configure the default SAML NameID policy used for IDP-initiated logins or when an incoming SP assertion doesn't specify a NameID policy (also applies when using a custom NameID Mapping). The following table outlines how NameID policies are handled:

| Default NameID policy                                                            | How authentik will handle the NameID                                                                                                                                                               |
| -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Persistent - `urn:oasis:names:tc:SAML:2.0:nameid-format:persistent`              | NameID will be set to the user's hashed ID.                                                                                                                                                        |
| x509 Subject - `urn:oasis:names:tc:SAML:2.0:nameid-format:X509SubjectName`       | NameID will be set to the user's `distinguishedName` attribute. This attribute is set by the LDAP source by default. If the attribute does not exist, it will fall back the persistent identifier. |
| Windows - `urn:oasis:names:tc:SAML:2.0:nameid-format:WindowsDomainQualifiedName` | NameID will be set to the user's UPN. This is also set by the LDAP source, and also falls back to the persistent identifier.                                                                       |
| Transient - `urn:oasis:names:tc:SAML:2.0:nameid-format:transient`                | NameID will be set based on the user's session ID.                                                                                                                                                 |
| Email address - `urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress`         | NameID will be set to the user's email address.                                                                                                                                                    |

:::warning Email based NameID attribute
By default, users are free to change their email addresses. Therefore, it is recommended to either: avoid using a user's email address as the NameID attribute or, if possible, disallow changing email addresses.
:::

## AuthnContextClassRef

The AuthnContextClassRef attribute appears in the SAML assertion and contains a URI that describes the assurance level, such as password, multi-factor, or smartcard authentication. SPs use this information to understand and verify how the user was authenticated by an IdP.

In authentik, it's possible to set the AuthnContextClassRef attribute to any property mapping that's enabled on a SAML provider. This is done via the **AuthnContextClassRef Property Mapping** on a SAML provider.

Alternatively, when the **AuthnContextClassRef Property Mapping** field is left unpopulated on a SAML provider, the AuthnContextClassRef will be set based on the method that the user authenticated with.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/saml/create-saml-provider.md
================================================================================

---
title: Create a SAML provider
---

authentik SAML providers can be created either from scratch or by using SAML metadata exported from the Service Provider (SP). Optionally, the metadata of an authentik SAML provider can be exported back to the SP. Note, however, that many SPs do not support exporting their metadata or importing Identity Provider (IdP) metadata.

## Create a SAML provider and application pair

To create a provider along with the corresponding application that uses it for authentication, navigate to **Applications** > **Applications** and click **Create with provider**. We recommend this combined approach for most common use cases. Alternatively, you can use the legacy method to solely create the provider by navigating to **Applications** > **Providers** and clicking **Create**.

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with provider** to create an application and provider pair.
3. On the **New application** page, define the application details, and then click **Next**.
4. Select **SAML Provider** as the **Provider Type**, and then click **Next**.
5. On the **Configure SAML Provider** page, provide the configuration settings and then click **Submit** to create both the application and the provider.

## Create a SAML provider from SP metadata (import SP metadata)

If you have exported SAML metadata from your SP, you can optionally create the authentik SAML provider by importing this metadata.

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click **Create** to create a provider.
3. Select **SAML Provider from Metadata** as the **Provider Type**, and then click **Next**.
4. On the **Create SAML Provider from Metadata** page, provide the configuration settings along with an SP metadata file and then click **Finish** to create the provider.
5. (Optional) Edit the created SAML provider and configure any further settings.

## Export authentik SAML provider metadata

After an authentik SAML provider has been created via any of the above methods, you can access its metadata in one of two ways:

### Download authentik metadata

To download the metadata of an authentik SAML provider, follow these steps:

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers**.
3. Click the name of the provider you want metadata from to open its overview tab.
4. In the **Related objects** section, under **Metadata** click on **Download**. This will download the metadata XML file for that provider.

### Access metadata tab

To view and optionally download the metadata of an authentik SAML provider, follow these steps:

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers**.
3. Click the name of the provider you want metadata from to open its overview tab.
4. Navigate to the **Metadata** tab.
5. The metadata for the provider will be shown in a codebox. You can optionally use the **Download** button to obtain the metadata as a file.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/saml/saml_single_logout.md
================================================================================

---
title: SAML Single Logout
authentik_version: "2025.10.0"
---

[Single Logout (SLO)](../single-logout/index.md) allows authentik to log out users from all configured providers simultaneously when they sign out of authentik. For SAML providers, this requires your service provider to support Single Logout via a Single Logout Service URL. Check your provider's documentation to confirm Single Logout support.

## Configure your SAML provider

To enable single logout, add a **Single Logout Service URL** to your SAML provider. The URL is the service provider’s endpoint to which authentik sends logout requests.

1. Log in to authentik as an administrator and open the authentik Admin interface
2. Navigate to **Applications** > **Providers**
3. Click the edit icon of the SAML provider that you want to configure for SLO
4. Set the **SLS URL** field to your service provider's logout endpoint
5. Select the appropriate **SLS Binding**:
    - **Redirect** - Uses HTTP redirects to send logout requests to the provider (front-channel only)
    - **POST** - Supports both front-channel and back-channel logout methods
6. Select the appropriate **Logout Method**:
    - **Front-channel iframe** - Performs parallel logout requests using hidden iframes. Supports both Redirect and POST bindings
    - **Front-channel native** - Uses the active browser tab to chain redirects and POST requests for sequential logout. Supports both Redirect and POST bindings
    - **Back-channel** - Performs server-to-server POST requests to log out the user. Requires POST SLS binding. Users are logged out even when their session is administratively terminated
7. (Optional) Enable **Sign Logout Request** to cryptographically sign SAML logout requests sent to the service provider
8. Click **Finish**

:::info
Back-channel logout ensures users are logged out even when their session is terminated administratively (e.g., when a user is deactivated or their session is deleted). This requires POST SLS binding.
:::

## SP-initiated Single Logout

SAML Service Providers can initiate logout by sending a SAML logout request to authentik. By default, only that Service Provider's session is ended while the authentik session remains active and the user stays logged in to other applications.

For instructions on how to trigger full Single Logout when a user logs out from a Service Provider, see [Enable full Single Logout for RP-initiated logout](../single-logout/index.md#enable-full-single-logout-for-rp-initiated-logout).

## How SAML Single Logout Works

When a user logs out of authentik through a logout flow, authentik initiates the single logout process for all SAML providers configured with an SLS URL and logout method.

### Front-channel iframe logout

With front-channel iframe logout, authentik injects an iframe logout stage into the logout flow. This stage loads all provider logout URLs simultaneously in hidden iframes within the browser, allowing parallel logout across multiple providers. After all iframes complete their requests, the user continues through the authentik logout flow.

### Front-channel native logout

With front-channel native logout, authentik chains logout requests sequentially using the active browser tab. For POST bindings, the browser automatically submits forms to each provider. For Redirect bindings, the browser follows redirect URLs. Each provider returns the user to authentik who redirects to the next provider. After all providers have been visited, the user completes the authentik logout flow.

### Back-channel logout

With back-channel logout, authentik sends SAML logout requests directly from the server to each provider's SLS URL via HTTP POST. This happens asynchronously and does not require browser interaction. Back-channel logout is also triggered automatically when:

    - A user's session is administratively deleted.
    - A user account is deactivated.

:::info
Back-channel logout requires POST SLS binding.
:::

## Binding Comparison

| Feature              | Redirect Binding      | POST Binding             |
| -------------------- | --------------------- | ------------------------ |
| Front-channel iframe | ✅ Supported          | ✅ Supported             |
| Front-channel native | ✅ Supported          | ✅ Supported             |
| Back-channel         | ❌ Not supported      | ✅ Supported             |
| Request sent via     | URL query parameters  | HTTP POST body           |
| Maximum data size    | Limited by URL length | Large requests supported |

## SAML session tracking

authentik tracks SAML sessions for each provider to support single logout. When a user successfully authenticates to a SAML provider, authentik creates a `SAMLSession` record containing:

    - The SAML `SessionIndex`
    - The `NameID` and `NameID format` used for the session
    - A link to the user's authenticated session

These session records are used to generate proper SAML logout requests with the correct `SessionIndex` and `NameID` values that the service provider expects.

## Resources

- [Single Logout (SLO) Overview](../single-logout/index.md)
- [User Logout Stage](../../flows-stages/stages/user_logout.md)
- [SAML Profiles 2.0 Specification](https://docs.oasis-open.org/security/saml/v2.0/saml-profiles-2.0-os.pdf)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/token-endpoint.mdx
================================================================================

---
title: Token endpoint
sidebar_custom_props:
    termName: Token endpoint
    tags:
        - Endpoints
    shortDescription: Exchanges codes or credentials for tokens.
    longDescription: Returns access, refresh, and optionally ID tokens depending on the grant type.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/saml-assertion.mdx
================================================================================

---
title: SAML assertion
sidebar_custom_props:
    termName: SAML assertion
    tags:
        - SAML
    shortDescription: SAML statement with authentication and attribute data.
    longDescription: Delivered to the service provider, typically via POST/Redirect binding, and consumed at the ACS URL.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/saml-binding.mdx
================================================================================

---
title: SAML binding
sidebar_custom_props:
    termName: SAML binding
    tags:
        - SAML
    shortDescription: Transport mechanism for SAML messages.
    longDescription: Defines how SAML messages are transported. Common bindings are HTTP-Redirect and HTTP-POST for SSO, and SOAP/Artifact for back-channel or large payloads.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/protocols/saml/index.md
================================================================================

---
title: SAML Source
---

This source allows authentik to act as a SAML Service Provider. Just like the [SAML provider](../../../../add-secure-apps/providers/saml/index.md), it supports signed requests. Vendor-specific documentation can be found in the Integrations section.

## Terminology

| Abbreviation | Name                       | Description                                                                                                                                 |
| ------------ | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| IDP          | Identity Provider          | The authoritative SAML authentication source that holds the user database                                                                   |
| SP           | Service Provider           | The client which is connected to an IDP, usually providing a service (e.g. a web application). In the current context, authentik is the SP. |
| -            | Assertion                  | A message sent by the IDP asserting that the user has been identified                                                                       |
| ACS          | Assertion Consumer Service | The service on the SP side that consumes the assertion sent from the IDP                                                                    |
| SSO URL      | Single Sign-On URL         | The URL on the IDP side which the SP calls to initiate an authentication process                                                            |
| SLO URL      | Single Log-Out URL         | The URL on the IDP side which the SP calls to invalidate a session and logout the user from the IDP as well as the SP                       |

## Example configuration

If you have the provider metadata, you should be able to extract all values you need from this. There is an example provided for a basic IDP metadata file below.

| Name                       | Example                          | Description                                                                                                                                                                                                                                                                    |
| -------------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Name                       | Company SAML                     | The name of the authentication source                                                                                                                                                                                                                                          |
| Slug                       | company-saml                     | The slug used in URLs for the source                                                                                                                                                                                                                                           |
| SSO URL                    | https://saml.company/login/saml  | The SingleSignOnService URL for the IDP, this can be found in the metadata or IDP documentation. There can be different URLs for different Binding Types (e.g. HTTP-Redirect and HTTP-POST), use the URL corresponding to the binding type you choose below                    |
| SLO URL                    | https://saml.company/logout/saml | The URL that is called when a user logs out of authentik, can be used to automatically log the user out of the SAML IDP after logging out of Authentik. Not supported by all IDPs, and not always wanted behaviour.                                                            |
| Issuer/Entity ID           | https://authentik.company        | The identifier for the authentik instance in the SAML federation, can be chosen freely. This is used to identify the SP on the IDP side, it usually makes sense to configure this to the URL of the SP or the path corresponding to the SP (e.g. `/source/saml/<source-slug>/` |
| Binding Type               | HTTP-POST                        | How authentik communicates with the SSO URL (302 redirect or POST request). This will depend on what the provider supports.                                                                                                                                                    |
| Allow IDP-Initiated Logins | False                            | Whether to allow the IDP to log users into authentik without any interaction. Activating this may constitute a security risk since this request is not verified, and could be utilized by an attacker to authenticate a user without interaction on their side.                |
| NameID Policy              | Persistent                       | Depending on what the IDP sends as persistent ID, some IDPs use the username or email address while others will use a random string/hashed value. If the user in authentik receives a random string as a username, try using Email address or Windows                          |
| Flow settings              | Default                          | If there are custom flows in your instance for external authentication, change to use them here                                                                                                                                                                                |

## Adding authentik as a server provider with your IDP

This will depend heavily on what software you are using for your IDP. On the Metadata tab in the SAML Federation Source you can download the metadata for the service provider, this should enable you to import this into most IDPs. If this does not work, the important parts are:

- Entity ID: Taken from the Issuer/Entity ID field above
- Return URL/ACS URL: `https://authentik.company/source/saml/<source-slug>/acs/`
- Certificate: If you have chosen to sign your outgoing requests, use the public side of the certificate that you specified in the settings

## Example IDP metadata

```xml
```

## SAML source property mappings

See the [overview](../../property-mappings/index.md) for information on how property mappings work.

### Expression data

The following variables are available to SAML source property mappings:

- `root`: An XML `ETree` object containing data from the source.
- `name_id`: An XML `Element` object identifying the user.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/authenticator_endpoint_gdtc/index.md
================================================================================

---
title: Google Chrome Device Trust Authenticator Stage
authentik_version: "2024.10"
authentik_enterprise: true
support_level: deprecated
---

:::warning Deprecated
This stage has been deprecated and is being replaced by the [Google Chrome connector](../../../../endpoint-devices/device-compliance/connectors/google-chrome.md) functionality included in the [Endpoint Devices](../../../../endpoint-devices/index.mdx) feature set.
:::

With this stage, authentik can validate users' Chrome browsers and ensure that users' devices are compliant and up-to-date.

Support for the Chrome Enterprise Device Trust connector allows organizations to integrate Chrome browsers and ChromeOS devices with authentik as the Identity Provider (IdP), to strengthen their overall security posture.

Device Trust is particularly important in environments with many different device types that are used by a large, remote workforce that might have a BYOD (Bring Your Own Device) policy, or have large teams of contractors, temporary workers, or volunteers.

With Device Trust you can enable "context-aware" access policies; for example a policy might require that a device has all security patches installed.

:::info
This stage only works with Google Chrome, as it relies on the [Chrome Verified Access API](https://developers.google.com/chrome/verified-access).
:::

## Configuration

The main steps to set up your Google workspace are as follows:

- [Configuration](#configuration)
    - [Create a Google cloud project](#create-a-google-cloud-project)
    - [Create a service account](#create-a-service-account)
    - [Set credentials for the service account](#set-credentials-for-the-service-account)
    - [Create the stage](#create-the-stage)

For detailed instructions, refer to Google documentation.

### Create a Google cloud project

1. Open the Google Cloud Console (https://cloud.google.com/cloud-console).
2. In upper left, click the drop-down box to open the **Select a project** box, and then select **New Project**.
3. Create a new project and give it a name like "authentik Chrome Device Trust".
4. Use the search bar at the top of your new project page to search for "API Library".
5. On the **API Library** page, use the search bar again to find "Chrome Verified Access API".
6. On the **Chrome Verified Access API** page, click **Enable**.

### Create a service account

1. After the new Chrome Verified Access API is enabled (it might take a few minutes), return to the Google Cloud console home page (click on **Google Cloud** in upper left).
2. Use the search bar to find and navigate to the **IAM** page.
3. On the **IAM** page, click **Service Accounts** in the left navigation pane.
4. At the top of the **Service Accounts** page, click **Create Service Account**.

- Under **Service account details** page, define the **Name** and **Description** for the new service account, and then click **Create and Continue**.
- Under **Grant this service account access to project** you do not need to define a role, so click **Continue**.
- Under **Grant users access to project** you do not need to define a role, so click **Done** to complete the creation of the service account.

### Set credentials for the service account

1. On the **Service accounts** page, click the account that you just created.
2. Click the **Keys** tab at top of the page, the click **Add Key > Create new key**.
3. In the Create box, select JSON as the key type, and then click **Create**.
   A pop-up displays with the private key, and the key is saved to your computer as a JSON file.
   Later, when you create the stage in authentik, you will add this key in the **Credentials** field.
4. On the service account page, click the **Details** tab, and expand the **Advanced settings** area.
5. Log in to the Admin Console, and then navigate to **Chrome browser > Connectors**.
6. Click on **New Provider Configuration**.
7. Under Universal Device Trust, click "Set up".
8. Enter a name.
9. Enter the URL: https://authentik.company/endpoint/gdtc/chrome/
10. Under Service accounts, enter the full name of the service account created above, for example `authentik-gdtc-docs@authentik-enterprise-dev.iam.gserviceaccount.com`.

### Create the stage

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows > Stages**.
3. Click **Create**, and select **Endpoint Authenticator Google Device Trust Connector Stage**, and in the **New stage** box, define the following fields:
    - **Name**: define a descriptive name, such as "chrome-device-trust".

    - **Google Verified Access API**
        - **Credentials**: paste the contents of the JSON file (the key) that you downloaded earlier.

4. Click **Finish**.

After creating the stage, it can be used in any flow. Compared to other Authenticator stages, this stage does not require enrollment. Instead of adding an [Authenticator Validation Stage](../authenticator_validate/index.mdx), this stage only verifies the user's browser.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/endpoint/index.md
================================================================================

---
title: Endpoint stage
---

This stage integrates with the [Endpoint Device](../../../../endpoint-devices/index.mdx) functionality and allows authentik to verify whether the device executing a flow is registered.

The Endpoint stage fetches [device facts](../../../../endpoint-devices/device-compliance/device-reporting.md#device-facts) via a configured [connector](../../../../endpoint-devices/device-compliance/connectors/index.mdx) and injects them into the flow context. These device facts can be used by other stages and policies to make device compliance decisions.

## Connector

Select the [connector](../../../../endpoint-devices/device-compliance/connectors/index.mdx) that the Endpoint stage will use to obtain device facts.

## Mode

Select whether the presence of a registered endpoint device is required for the stage to succeed.

- If the mode is set to required, and device verification fails, the user is not able to proceed with the flow.
- If the mode is set to optional, authentik will attempt to verify the device, and if it doesn't receive a response within the specified `challenge_idle_timeout`, authentik will continue without attaching a device to the flow.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/oauth2/github-compatibility.md
================================================================================

---
title: GitHub compatibility
---

The OAuth2 provider also exposes a GitHub-compatible endpoint. This endpoint can be used by applications, which support authenticating against GitHub Enterprise, but not generic OpenID Connect.

To use any of the GitHub Compatibility scopes, you have to use the GitHub Compatibility Endpoints.

| Endpoint        | URL                         |
| --------------- | --------------------------- |
| Authorization   | `/login/oauth/authorize`    |
| Token           | `/login/oauth/access_token` |
| User Info       | `/user`                     |
| User Teams Info | `/user/teams`               |

To access the user's email address, a scope of `user:email` is required. To access their groups, `read:org` is required. Because these scopes are handled by a different endpoint, they are not customisable as a Scope Mapping.

## Special scopes for GitHub compatibility

- `user`: No-op, is accepted for compatibility but does not give access to any resources
- `read:user`: Same as above
- `user:email`: Allows read-only access to `/user`, including email address
- `read:org`: Allows read-only access to `/user/teams`, listing all the user's groups as teams.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/oauth2/webfinger_support.mdx
================================================================================

---
title: WebFinger support
---

## About WebFinger

The [WebFinger protocol](https://webfinger.net/) allows for the discovery of information about individuals or entities on the Internet through standard HTTP methods. It enables the retrieval of information associated with a URI that might not be directly usable as a locator, such as those for accounts or email addresses.

## authentik WebFinger support

authentik provides a WebFinger endpoint when the **Default application** setting uses an OIDC provider. Instructions on how to set a **Default application** can be found in the [authentik Branding documentation](../../../sys-mgmt/brands/index.md#external-user-settings).

The WebFinger endpoint is available at: `https://authentik.company/.well-known/webfinger` (where authentik.company is the FQDN of your authentik instance)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/oauth2/machine_to_machine.mdx
================================================================================

---
title: Machine-to-Machine (M2M) authentication
sidebar_label: Machine-to-machine authentication
---

The OAuth 2.0 specification includes the client credentials grant which allows machine-to-machine (M2M) communication authentication, bypassing user involvement. In authentik, machine clients do not authenticate using the typical `client_id` + `client_secret`. This is due to OAuth providers only being able to have a single secret at any given time.

Hence identification is based on a username, and authentication is based on app password tokens.

```mermaid
sequenceDiagram
    participant Client
    participant authentik
    participant Resource

    Client->>+authentik: POST /application/o/token/<br><client_credentials_request>
    authentik->>-Client: 200 OK<br/><access_token>
    Client->>+Resource: GET /resource<br/><Authorization: Bearer token>
    Resource->>-Client: 200 OK<br/>Resource data

```

## Static authentication

All user account types; internal, external and service account, can be used for authentication. These can be created manually beforehand or [automatically during authentication](#automatic-service-account-creation).

authentik treats a grant type of `password` the same as `client_credentials` to support applications which rely on a password grant. Scopes, if required, must be defined in the request, and follow the same behaviour as other OAuth requests.

### Example request

An example request:

```http
POST /application/o/token/ HTTP/1.1
Host: authentik.company
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&
client_id=<client_id>&
username=<username>&
password=<app_password>&
scope=profile
```

This will return a JSON response with an `access_token`, which is a signed JWT token. This token can be sent along with requests to other hosts, which can then validate the JWT based on the signing key configured in authentik.

### Base64 encoded username and app password

It's also possible to encode the username and app password of the user to authenticate with, separated with a colon, into a base64 string and pass it as `client_secret` value, for example:

```http
POST /application/o/token/ HTTP/1.1
Host: authentik.company
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&
client_id=<client_id>&
client_secret=<base64(username:token)>&
scope=profile
```

### Automatic service account creation

Alternatively, it's possible to pass the configured `client_secret` value of an OAuth provider, in which case authentik will automatically generate a service account for which the JWT token will be issued, for example:

```http
POST /application/o/token/ HTTP/1.1
Host: authentik.company
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&
client_id=<client_id>&
client_secret=<client_secret>&
scope=profile
```

The automatically generated service account will follow this naming scheme: `ak-<provider_name>-client_credentials`. Currently the service account creation settings cannot be altered.

## JWT authentication

For both externally and authentik issued JWTs, authentik will create a service account which is based on the provider name and the subject claim of the token that authentik is given. You may end up with multiple service accounts depending on the tokens that are provided to authentik. These service accounts will expire and be deleted based on the expiry claim (if set) of the token that authentik is given.

### Externally issued JWTs

You can authenticate and get a token using an existing JWT. For readability we will refer to the JWT issued by the external issuer/platform as input JWT, and the resulting JWT from authentik as the output JWT.

To configure this, define a JWKS URL/raw JWKS data in OAuth Sources. If a JWKS URL is specified, authentik will fetch the data and store it in the source, and then select the source in the OAuth2 Provider that will be authenticated against.

With this configuration, any JWT issued by the configured sources' certificates can be used to authenticate:

```http
POST /application/o/token/ HTTP/1.1
Host: authentik.company
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&
client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer&
client_assertion=<inputJWT>&
client_id=<client_id>
```

Alternatively, you can set the `client_secret` parameter to `<inputJWT>`, for applications that can set the password from a file but not other parameters.

Input JWTs are checked to verify that they are signed by any of the selected _Federated OIDC Sources_, and that their `exp` attribute is not set as now or in the past.

To dynamically limit access based on the claims of the tokens, you can use [Expression policies](../../../customize/policies/expression.mdx), for example:

```python
return request.context["oauth_jwt"]["iss"] == "https://my.issuer"
```

Other information that's available in the policy expression context:

- `request.context["oauth_scopes"]` - list of scope names requested
- `request.context["oauth_grant_type"]` - the grant type
- `request.context["oauth_code_verifier"]` - a string or none

If you're authorizing with a JWT, then `request.context["oauth_jwt"]` is available which is the parsed JWT as a dictionary.

### authentik-issued JWTs

To allow federation between providers, modify the provider settings of the application (whose token will be used for authentication) to select the provider of the application to which you want to federate.

With this configuration, any JWT issued by the configured providers can be used to authenticate:

```http
POST /application/o/token/ HTTP/1.1
Host: authentik.company
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&
client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer&
client_assertion=<inputJWT>&
client_id=<client_id>
```

Alternatively, you can set the `client_secret` parameter to `<inputJWT>`, for applications which can set the password from a file but not other parameters.

Input JWTs must be valid access tokens issued by any of the configured _Federated OIDC Providers_, they must not have been revoked and must not have expired.

To dynamically limit access based on the claims of the tokens, you can use [Expression policies](../../../customize/policies/expression.mdx), for example:

```python
return request.context["oauth_jwt"]["iss"] == "https://my.issuer"
```

Other information that's available in the policy expression context:

- `request.context["oauth_scopes"]` - list of scope names requested
- `request.context["oauth_grant_type"]` - the grant type
- `request.context["oauth_code_verifier"]` - a string or none

If you're authorizing with a JWT, then `request.context["oauth_jwt"]` is available which is the parsed JWT as a dictionary.

## Troubleshooting

### More detailed error information

If you receive any error response from authentik it will only be a generic error, error description, and the `request_id`.

However, more detailed error information can be obtained from the [authentik server container logs](../../../troubleshooting/logs/logs.mdx) by searching for the `request_id` that you're experiencing issues with.

### OAuth introspection endpoint

To use the OAuth introspection endpoint to obtain more information on a token, you must first authenticate to it.

You are only able to introspect a token from the same provider that was used to authenticate, or you must exchange the token for a token from the provider as described above.

### Event logging

All of these authentication methods will create a login event in the event logs, rather than an authorization event. The event logs will contain different information depending on the scenario:

| Scenario                                                                                                      | Authentication Method | Authentication Arguments                     |
| ------------------------------------------------------------------------------------------------------------- | --------------------- | -------------------------------------------- |
| [Static authentication using credentials](#static-authentication)                                             | `token`               | Dictionary containing the token identifier   |
| [Static authentication and automatically generating the service account](#automatic-service-account-creation) | `oauth_client_secret` | N/A                                          |
| [JWT authentication](#jwt-authentication)                                                                     | `JWT`                 | Parsed JWT + reference to source or provider |



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/oauth2/device_code.md
================================================================================

---
title: Device code flow
---

The device code flow is also known as _device flow_ or _device authorization grant flow_. This type of authentication flow is useful for devices with limited input capabilities and/or devices without browsers. The Request for Comments (RFC) 8628) abstract for this flow states:

> The OAuth 2.0 device authorization grant is designed for Internet-connected devices that either lack a browser to perform a user-agent-based authorization or are input constrained to the extent that requiring the user to input text in order to authenticate during the authorization flow is impractical. It enables OAuth clients on such devices (like smart TVs, media consoles, digital picture frames, and printers) to obtain user authorization to access protected resources by using a user agent on a separate device.

### Requirements

This device flow is only possible if the active [brand](../../../sys-mgmt/brands/index.md) has a device code flow configured. This flow is run _after_ the user logs in, and before the user authenticates.

authentik does not include a default flow for this use case, so it is necessary to create a new one with a **Designation** of `Stage Configuration`.

### Device flow initiation

The flow is initiated by sending a POST request to the device authorization endpoint, `/application/o/device/`, with the following contents:

```http
POST /application/o/device/ HTTP/1.1
Host: authentik.company
Content-Type: application/x-www-form-urlencoded

client_id=application_client_id&
scope=openid email my-other-scope
```

Alternatively the client id may be sent via the HTTP Authorization header:

```http
POST /application/o/device/ HTTP/1.1
Host: authentik.company
Content-Type: application/x-www-form-urlencoded
Authorization: Bearer YXBwbGljYXRpb25fY2xpZW50X2lkOg==

scope=openid email my-other-scope
```

The response contains the following fields:

- `device_code`: Device code, which is the code kept on the device
- `verification_uri`: The URL to be shown to the enduser to input the code
- `verification_uri_complete`: The same URL as above except the code will be prefilled
- `user_code`: The raw code for the enduser to input
- `expires_in`: The total seconds after which this token will expire
- `interval`: The interval in seconds for how often the device should check the token status

With this response, the device can start checking the status of the token by sending requests to the token endpoint like this:

```http
POST /application/o/token/ HTTP/1.1
Host: authentik.company
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:device_code&
client_id=application_client_id&
device_code=device_code_from_above
```

If the user has not opened the link above yet, or has not finished the authentication and authorization yet, the response will contain an `error` element set to `authorization_pending`. The device should re-send the request in the interval set above.

If the user _has_ finished the authentication and authorization, the response will be similar to any other generic OAuth2 Token request, containing `access_token` and `id_token`.

### Create and apply a device code flow

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Flows** and click **Create**.
3. Set the following required configurations:
    - **Name**: provide a name (e.g. `default-device-code-flow`)
    - **Title**: provide a title (e.g. `Device code flow`)
    - **Slug**: provide a slug (e.g `default-device-code-flow`)
    - **Designation**: `Stage Configuration`
    - **Authentication**: `Require authentication`
4. Click **Create**.
5. Navigate to **System** > **Brands** and click the **Edit** icon on the default brand.
6. Set **Default code flow** to the newly created device code flow and click **Update**.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/oauth2/frontchannel_and_backchannel_logout.mdx
================================================================================

---
title: Front-channel and back-channel logout
description: Configure front-channel and back-channel logout for OAuth2/OpenID Connect providers
authentik_version: "2025.8.0"
authentik_preview: true
---

## Overview

OAuth2/OIDC logout is a security feature defined in the OpenID Connect specification. It allows an OIDC Provider (OP), such as authentik, to notify Relying Parties (RPs) when a user session ends. This ensures that all associated applications can properly terminate the user's session.

For more information about single logout across all providers, see the [Single Logout (SLO) Overview](../single-logout/index.md).

:::warning
Your OAuth application (Relying Party) must explicitly support OpenID Connect front-channel logout or back-channel logout to properly handle logout requests. Not all OAuth applications support these features, so compatibility should be verified.
:::

## Requirements

Your OAuth application (Relying Party) must:

    - **HTTPS**: Use HTTPS in production.
    - **Accessible**: Be reachable from authentik.
    - **Logout endpoint**: Have a defined endpoint to handle OP logout requests (front-channel, back-channel, or both).

## Configuration

### Set up single logout

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers**.
3. Edit or create an OAuth2 provider.
4. In the **Logout URI** field, enter the logout endpoint provided by your RP, if supported.
5. Select the **Logout Method** to choose **Front-channel** or **Back-channel** based on RP support.
6. Click **Finish** to save your changes.

:::info
Back-channel logout is the only way to ensure that users are logged out of the provider when their session is administratively terminated (e.g., when a user is deactivated or their session is deleted).
:::

### Logout URI format

The **Logout URI** should be a single URL provided by your Relying Party application, for example:

#### Back-channel

```
https://app.example.com/oauth/backchannel-logout
https://api.service.com/logout/backchannel
https://client.example.org/backchannel-logout
```

#### Front-channel

```
https://app.example.com/oauth/logout
https://api.service.com/logout
```

## RP-initiated Single Logout

OIDC Relying Parties can initiate logout by redirecting a user to authentik's `end_session` endpoint. By default, only that application's session is ended while the authentik session remains active and the user stays logged in to other applications.

For instructions on how to trigger full Single Logout when a user logs out from an application, see [Enable full Single Logout for RP-initiated logout](../single-logout/index.md#enable-full-single-logout-for-rp-initiated-logout).

## How OpenID Connect single logout works

### Back-channel logout

With back-channel logout, authentik sends logout requests directly from the server to the RP’s logout endpoint via HTTP POST. The logout request includes a signed JWT logout token that contains the following JWT claims:

    - `iss` (issuer): The authentik issuer URL
    - `sub` (subject): The user's unique identifier
    - `aud` (audience): The client ID
    - `iat` (issued at): Token creation timestamp
    - `jti` (JWT ID): Unique token identifier
    - `events`: Logout event claim
    - `sid` (session ID): The session identifier (if available)

Example back-channel logout request:

```http
POST /backchannel-logout HTTP/1.1
Host: client.example.org
Content-Type: application/x-www-form-urlencoded

logout_token=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

Back-channel logout is triggered when:

    - A user logs out through a logout flow
    - An administrator deletes a user's session
    - A user account is deactivated
    - A session expires or is revoked

### Front-channel logout

With front-channel logout, authentik injects an iframe logout stage into the logout flow. This stage loads the RP's (relying party) front-channel logout URL in a hidden iframe within the user's browser. The logout URL includes session information as query parameters, such as:

    - `iss`: The authentik issuer URL
    - `sid`: The session identifier

Example front-channel logout iframe:

```html


================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/oauth2/index.mdx
================================================================================

---
title: OAuth 2.0 provider
---

In authentik, you can [create](./create-oauth2-provider.md) an [OAuth 2.0](https://oauth.net/2/) provider that authentik uses to authenticate the user to the associated application. This provider supports both generic OAuth2 as well as OpenID Connect (OIDC).

## authentik and OAuth 2.0

It's important to understand how authentik works with and supports the OAuth 2.0 protocol, so before taking a [closer look at OAuth 2.0 protocol](#about-oauth-20-and-oidc) itself, let's cover a bit about authentik.

authentik can act either as the OP, (OpenID Provider, with authentik as the IdP), or as the RP (Relying Party, or the application that uses OAuth 2.0 to authenticate). If you want to configure authentik as an OP, then you create a provider, then use the OAuth 2.0 provider. If you want authentik to serve as the RP, then configure a [source](../../../users-sources/sources/index.md). Of course, authentik can serve as both the RP and OP, if you want to use the authentik OAuth provider and also use sources.

All standard OAuth 2.0 flows (authorization code, client_credentials, implicit, hybrid, device code) and grant types are supported in authentik, and we follow the [OIDC spec](https://openid.net/specs/openid-connect-core-1_0.html). OAuth 2.0 in authentik supports OAuth, PKCE, [Github compatibility](./github-compatibility.md) and the RP receives data from our scope mapping system.

The authentik OAuth 2.0 provider comes with all the standard functionality and features of OAuth 2.0, including the OAuth 2.0 security principles such as no cleartext storage of credentials, configurable encryption, configurable short expiration times, and the configuration of automatic rotation of refresh tokens. In short, our OAuth 2.0 protocol support provides full coverage.

## About OAuth 2.0 and OIDC

OAuth 2.0 is an authorization protocol that allows an application (the RP) to delegate authorization to an OP. OIDC is an authentication protocol built on top of OAuth2, which provides identity credentials and other data on top of OAuth2.

**OAuth 2.0** typically requires two requests (unlike the previous "three-legged" OAuth 1.0). The two "legs", or requests, for OAuth 2.0 are:

1. An authorization request is prepared by the RP and contains parameters for its implementation of OAuth and which data it requires, and then the User's browser is redirected to that URL.
2. The RP sends a request to authentik in the background to exchange the access code for an access token (and optionally a refresh token).

In detail, with OAuth2 when a user accesses the application (the RP) via their browser, the RP then prepares a URL with parameters for the OpenID Provider (OP), which the user's browser is redirected to. The OP authenticates the user and generates an authorization code. The OP then redirects the client (the user's browser) back to the RP, along with that authorization code. In the background, the RP then sends that same authorization code in a request authenticated by the `client_id` and `client_secret` to the OP. Finally, the OP responds by sending an Access Token saying this user has been authorized (the RP is recommended to validate this token using cryptography) and optionally a Refresh Token.

The image below shows a typical authorization code flow.

```mermaid
sequenceDiagram
    participant user as User
    participant rp as RP (Relying Party)
    participant op as OP (OpenID Provider)

    user->>rp: User accesses application
    rp->>user: RP prepares authorization request & redirects user to OP

    user->>op: User authentication & authorization occurs
    op->>rp: Redirect back to the RP with an authorization code

    rect

        rp->>op: Exchange authorization code
        op->>rp: RP receives Access token (optionally Refresh Token)
    end

    rp->>user: User is logged in
```

## OAuth2 endpoints and bindings

| Endpoint             | URL                                                                  |
| -------------------- | -------------------------------------------------------------------- |
| Authorization        | `/application/o/authorize/`                                          |
| Token                | `/application/o/token/`                                              |
| User Info            | `/application/o/userinfo/`                                           |
| Token Revoke         | `/application/o/revoke/`                                             |
| Token Introspection  | `/application/o/introspect/`                                         |
| Device Authorization | `/application/o/device/`                                             |
| End Session          | `/application/o/<application slug>/end-session/`                     |
| JWKS                 | `/application/o/<application slug>/jwks/`                            |
| OpenID Configuration | `/application/o/<application slug>/.well-known/openid-configuration` |

:::caution Reserved application slugs
Due to how the OAuth2 provider endpoints are structured, you cannot create applications that use the slugs `authorize`, `token`, `device`, `userinfo`, `introspect`, or `revoke` as these would conflict with the global OAuth2 endpoints.
:::

### Additional configuration options with Redirect URIs

When using an OAuth 2.0 provider in authentik, the OP must validate the provided redirect URI by the RP. An authentik admin can configure a list in the **Redirect URI** field on the Provider.

When you create a new OAuth 2.0 provider and app in authentik and you leave the **Redirect URI** field empty, then the first time a user opens that app, authentik uses that URL as the saved redirect URL.

For advanced use cases, an authentik admin can use regular expressions (regex) instead of a redirect URL. For example, if you want to list ten different applications, instead of listing them all individually, you can create an expression with wildcards. When using regex, be aware that authentik uses a dot as a separator in the URL, but in regex a dot means "one of any character", a wildcard. You should therefore escape the dot with `\.` to prevent its interpretation as a wildcard.

### OAuth2/OpenID Connect back-channel logout

Using back-channel logout (a server-to-server notification mechanism) allows an identity provider to notify connected OAuth2/OpenID clients whenever a user's session is terminated.

For more information, see our [OAuth2/OpenID Connect front-channel and back-channel logout](./frontchannel_and_backchannel_logout.mdx) documentation.

## OAuth 2.0 flows and grant types

There are three general flows of OAuth 2.0:

1. Web-based application authorization (Authorization code, Implicit, Refresh token)
2. Client credentials (Machine-to-machine)
3. Device code

Additionally, the [Refresh token](#refresh-token-grant) (grant type) is optionally used with any of the above flows, as well as the client credentials and device code flows.

### 1: Web-based application authorization

The flows and grant types used in this case are those used for a typical authorization process, with a user and an application:

- _Authorization code_ grant type
- _Implicit_ grant type (legacy)
- _Hybrid_ grant type

#### Authorization code

The authorization code is for environments with both a Client and a application server, where the back and forth happens between the client and an app server (the logic lives on app server). The RP needs to authorise itself to the OP. Client ID (public, identifies which app is talking to it) and client secret (the password) that the RP uses to authenticate.

If you configure authentik to use "Offline access" then during the initial auth the OP sends two tokens, an access token (short-lived, hours, can be customized) and a refresh token (typically longer validity, days or infinite). The RP (the app) saves both tokens. When the access token is about to expire, the RP sends the saved refresh token back to the OP, and requests a new access token. When the refresh token itself is about to expire, the RP can also ask for a new refresh token. This can all happen without user interaction if you configured the offline access.

:::info
Starting with authentik 2024.2, applications only receive an access token. To receive a refresh token, both applications and authentik must be configured to request the `offline_access` scope. In authentik this can be done by selecting the `offline_access` Scope mapping in the provider settings.
:::

The authorization code grant type is used to convert an authorization code to an access token (and optionally a refresh token). The authorization code is retrieved through the authentik [Authorization flow](../../flows-stages/flow/index.md), can only be used once, and expires quickly.

#### Implicit

:::info
The OAuth 2.0 [Security Best Current Practice document](https://tools.ietf.org/html/draft-ietf-oauth-security-topics) recommends against using the Implicit flow entirely, and OAuth 2.0 for Browser-Based Apps describes the technique of using the authorization code flow with PKCE instead. ([source](https://oauth.net/2/grant-types/implicit/))
:::

This flow is for more modern single page-applications, or ones you download, that are all client-side (all JS, no backend logic, etc) and have no server to make tokens. Because the secret cannot be stored on the client machine, the implicit flow is required in these architectures. With the implicit flow, the flow skips the second part of the two requests seen in the authorization flow; after the initial author request, the implicit flow receives a token, and then with cryptocracy and with PKCE, it can validate that it is the correct client, and that is safe to send a token. The RP (still called that with this implicit flow) can use cryptography to validate the token.

#### Hybrid

The Hybrid Flow is an OpenID Connect flow that incorporates traits of both the Implicit flow and the Authorization Code flow. It provides an application instant access to an ID token while ensuring secure and safe retrieval of access tokens and refresh tokens. This can be useful in situations where the application needs to quickly access information about the user, while in the background doing further processing to get additional tokens before gaining access to additional resources.

### 2. Client credentials

The client credentials flow and grant types are typically implemented for server-to-server scenarios, when code in a web application invokes a web API.

For more information, see [Machine-to-machine authentication](./machine_to_machine.mdx).

### 3. Device code

The device code flow is used in situations where there is no browser and limited options for text or data input from a client ("input-constrained devices"). For example, using a subscription TV program on a television, where you use a website on your mobile device to input a code displayed on the TV, authenticate, and then you are logged in to the TV.

For more information, see [Device code flow](./device_code.md).

#### Refresh token grant

Refresh tokens can be used as long-lived tokens to access user data, and further renew the refresh token down the road.

:::info
Starting with authentik 2024.2, the refresh token grant type requires the `offline_access` scope.
:::

## Scope mappings

Scopes can be configured using scope mappings, a type of [property mapping](../property-mappings/index.md#scope-mappings-with-oauth2).

## Scope authorization

By default, every user that has access to an application can request any of the configured scopes. Starting with authentik 2022.4, you can do additional checks for the scope in an expression policy (bound to the application):

```python
# There are additional fields set in the context, use `ak_logger.debug(request.context)` to see them.

if "my-admin-scope" in request.context["oauth_scopes"]:
    return ak_is_group_member(request.user, name="my-admin-group")
return True
```

## Default & special scopes

When a client does not request any scopes, authentik will treat the request as if all configured scopes were requested. Depending on the configured authorization flow, consent still needs to be given, and all scopes are listed there.

This does _not_ apply to special scopes, as those are not configurable in the provider.

### Default

- `openid`: A scope required by the OpenID Connect spec to specify that an OAuth interaction is OpenID Connect. Does not add any data to the token.
- `profile`: Include basic profile information, such as username, name and group membership.
- `email`: Include the users' email address.
- `entitlements`: Include application entitlement data.
- `offline_access`: An OAuth 2.0 scope which indicates that the application is requesting a refresh token.

### authentik

- `goauthentik.io/api`: This scope grants the refresh token access to the authentik API on behalf of the user

### GitHub compatibility

- `user`: No-op, is accepted for compatibility but does not give access to any resources
- `read:user`: Same as above
- `user:email`: Allows read-only access to `/user`, including email address
- `read:org`: Allows read-only access to `/user/teams`, listing all the user's groups as teams.

### Email scope verification

In authentik releases prior to 2025.10, the email scope always set the `email_verified` claim to `True`. Since authentik does not have a single authoritative source to determine whether a user's email is actually verified, asserting this claim could have security implications. As of 2025.10, `email_verified` now defaults to `False`.

Some applications require this claim to be `True` in order to authenticate users. In those cases, you can create a custom email scope mapping (**Customization** > **Property Mappings**) that always returns `email_verified` as `True`:

```python
return {
    "email": request.user.email,
    "email_verified": True
}
```

For greater security guarantees, verify users' email addresses and store the verification status as a user attribute (for example, `email_verified` set to `True` or `False`). You can then configure the scope mapping to return this value dynamically:

```python
return {
    "email": request.user.email,
    "email_verified": request.user.attributes.get("email_verified", False)
}
```

## Signing & Encryption

[JWTs](https://jwt.io/introduction) created by authentik will always be signed.

When a _Signing Key_ is selected in the provider, the JWT will be signed asymmetrically with the private key of the selected certificate, and can be verified using the public key of the certificate. The public key data of the signing key can be retrieved via the JWKS endpoint listed on the provider page.

When no _Signing Key_ is selected, the JWT will be signed symmetrically with the _Client secret_ of the provider, which can be seen in the provider settings.

### Encryption:ak-version

authentik can also encrypt JWTs (turning them into JWEs) it issues by selecting an _Encryption Key_ in the provider. When selected, all JWTs will be encrypted symmetrically using the selected certificate. authentik uses the `RSA-OAEP-256` algorithm with the `A256CBC-HS512` encryption method.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/oauth2/create-oauth2-provider.md
================================================================================

---
title: Create an OAuth2 provider
---

To create a provider along with the corresponding application that uses it for authentication, navigate to **Applications** > **Applications** and click **Create with provider**. We recommend this combined approach for most common use cases. Alternatively, you can use the legacy method to solely create the provider by navigating to **Applications** > **Providers** and clicking **Create**.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications > Applications** and click **Create with provider** to create an application and provider pair.
3. On the **New application** page, define the application settings, and then click **Next**.
4. Select **OAuth2/OIDC** as the **Provider Type**, and then click **Next**.
5. On the **Configure OAuth2/OpenId Provider** page, provide the configuration settings and then click **Submit** to create both the application and the provider.

:::info
Optionally, configure the provider with the `offline_access` scope mapping. By default, applications only receive an access token. To receive a refresh token, applications and authentik must be configured to request the `offline_access` scope. Do this in the Scope mapping area on the **Configure OAuth2/OpenId Provider** page.
:::



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/openid-provider.mdx
================================================================================

---
title: OpenID Provider (OP)
sidebar_custom_props:
    termName: OpenID Provider (OP)
    tags:
        - OAuth2/OIDC
    shortDescription: OIDC authority that authenticates users and issues tokens.
    longDescription: Authorization Server implementing OpenID Connect. Exposes discovery metadata, authorization, token, userinfo, JWKS, and end-session endpoints; authenticates users, issues ID/Access/Refresh tokens, and enforces consent and policy. In OAuth2 terminology, the OP is the Authorization Server (AS).
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/scim-endpoints.mdx
================================================================================

---
title: SCIM endpoints (Users, Groups)
sidebar_custom_props:
    termName: SCIM endpoints (Users, Groups)
    tags:
        - Provisioning
    shortDescription: RESTful endpoints for provisioning operations.
    longDescription: Key endpoints include /Users and /Groups supporting CRUD, filtering, and pagination. Implementations may also support bulk and search.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/authorization-endpoint.mdx
================================================================================

---
title: Authorization endpoint
sidebar_custom_props:
    termName: Authorization endpoint
    tags:
        - Endpoints
    shortDescription: Endpoint where users authenticate and consent.
    longDescription: Start of OAuth/OIDC flows; returns codes or tokens depending on the response type and client configuration.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/introspection-endpoint.mdx
================================================================================

---
title: Introspection endpoint
sidebar_custom_props:
    termName: Introspection endpoint
    tags:
        - OAuth2/OIDC
    shortDescription: Endpoint to validate opaque tokens.
    longDescription: RFC 7662 endpoint that returns whether a token is active along with subject, scopes, audience, and expiry. Typically requires client authentication and is used when tokens are opaque.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/revocation-endpoint.mdx
================================================================================

---
title: Revocation endpoint
sidebar_custom_props:
    termName: Revocation endpoint
    tags:
        - OAuth2/OIDC
    shortDescription: Endpoint to invalidate access or refresh tokens.
    longDescription: RFC 7009 endpoint that lets clients invalidate access or refresh tokens, immediately preventing further use.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/social-logins/entra-id/oauth/index.mdx
================================================================================

---
title: Entra ID OAuth authentication
sidebar_label: Entra ID OAuth
description: Authenticating to authentik with Entra ID credentials via the OAuth 2.0 protocol
tags:
    - source
    - entra
    - azure
    - oauth
---

Allows users to authenticate to authentik using their Entra ID credentials by configuring Entra ID as a federated identity provider via OAuth 2.0.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

## Entra ID configuration

To integrate Entra ID with authentik, you need to create an app registration in the Entra ID portal.

1. Log in to [Entra ID](https://entra.microsoft.com) using a [global administrator](https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference#global-administrator) account.
2. Navigate to **Applications** > **App registrations**.
3. Click **New registration** and set the following required configurations:
    - **Name**: provide a descriptive name (e.g. `authentik`).
    - Under **Supported account types**: select the account type that applies to your use case (e.g. `Accounts in this organizational directory only (Default Directory only - Single tenant)`).
    - Under **Redirect URI**:
        - **Platform**: `Web`
        - **URI**: `https://authentik.company/source/oauth/callback/entra-id/`

4. Click **Register**. When registration is complete, the **Overview** tab of the newly created app registration opens. Take note of the `Application (client) ID`. If you selected `Accounts in this organizational directory only (Default Directory only - Single tenant)` as the **Supported account types**, also note the `Directory (tenant) ID`. These values will be needed later when configuring authentik.
5. In the leftmost sidebar, navigate to **Certificates & secrets**.
6. Select the **Client secrets** tab and click **New Secret**. Configure the following required settings:
    - **Description**: provide a description for the secret (e.g. `authentik secret`).
    - **Expires**: choose an expiration period. As authentik does not yet support automatic secret rotation, either manual rotation or API-based updates are required. As a result, a duration of at least 12 months is recommended.
7. Copy the secret's value from the **Value** column.

:::info
The secret value is only displayed once at the time of creation. Make sure to copy and store it securely, as it cannot be retrieved later.
:::

8. In the sidebar, navigate to **API Permissions**, then click **Add a permission** and select **Microsoft Graph** as the API.
9. Select **Delegated permissions** as the permission type and assign the following permissions:
    - Under **OpenID Permissions**: select `email`, `profile`, and `openid`.
    - Under **User**: select `User.Read`.
    - Under **Group Member** _(optional)_: if you need authentik to sync group membership information from Entra ID, select the `GroupMember.Read.All` permission.
10. Click **Add permissions**.
11. Under **Configured permissions**, click **Grant admin consent for default directory**.

## authentik configuration

To support the integration of Entra ID with authentik, you need to create an Entra ID OAuth source in authentik.

### Create Entra ID OAuth source

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **Entra ID OAuth Source** as the source type.
    - **Create Entra ID OAuth Source**: provide a name, a slug which must match the slug used in the Entra ID `Redirect URI`, and the following required configurations:
        - Under **Protocol Settings**:
            - **Consumer key**: `Application (client) ID` from Entra ID.
            - **Consumer secret**: value of the secret created in Entra ID.
            - **Scopes** _(optional)_: if you need authentik to sync group membership information from Entra ID, add the `https://graph.microsoft.com/GroupMember.Read.All` scope.
        - Under **URL Settings**:
            - For **Single tenant** Entra ID applications:
                - **Authorization URL**: `https://login.microsoftonline.com/<directory_(tenant)_id>/oauth2/v2.0/authorize`
                - **Access token URL**: `https://login.microsoftonline.com/<directory_(tenant)_id>/oauth2/v2.0/token`
                - **Profile URL**: `https://graph.microsoft.com/v1.0/me`
                - **OIDC JWKS URL**: `https://login.microsoftonline.com/<directory_(tenant)_id>/discovery/v2.0/keys`
            - For **Multi tenant** Entra ID applications:
                - **Authorization URL**: `https://login.microsoftonline.com/common/oauth2/v2.0/authorize`
                - **Access token URL**: `https://login.microsoftonline.com/common/oauth2/v2.0/token`
                - **Profile URL**: `https://graph.microsoft.com/v1.0/me`
                - **OIDC JWKS URL**: `https://login.microsoftonline.com/common/discovery/v2.0/keys`

3. Click **Save**.

:::info Group Membership
When group membership information is synced from Entra ID, authentik creates all groups that a user is a member of. This sync process is carried out upon each user login, which can cause login delays for organizations with large numbers of groups.

For organizations with larger numbers of users and groups, we recommend using the [Entra ID SCIM integration](../scim/) to provision users and groups. These users are then automatically linked to matching users logging in via this Entra ID OAuth source.
:::

:::info Display new source on login screen
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../../add-secure-apps/flows-stages/stages/source).
:::

### Machine-to-machine authentication

If using [Machine-to-Machine](../../../../../add-secure-apps/providers/oauth2/machine_to_machine.mdx#jwt-authentication) authentication, some specific steps need to be considered.

When getting the JWT token from Entra ID, set the scope to the **Application ID URI**, and _not_ the Graph URL; otherwise the JWT will be in an invalid format.

```http
POST /<entra_tenant_id>/oauth2/v2.0/token/ HTTP/1.1
Host: login.microsoftonline.com
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&
client_id=<application_client_id>&
scope=api://<application_client_id>/.default&
client_secret=<application_client_secret>
```

The JWT returned from the request above can be used in authentik and exchanged for an [authentik JWT](../../../../../../add-secure-apps/providers/oauth2/machine_to_machine/#authentik-issued-jwts).

## Source property mappings

Source property mappings allow you to modify or gather extra information from sources. See the [overview](../../../property-mappings/index.md) for more information.

## Resources

- [Entra ID Documentation - Register an application in Microsoft Entra ID](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/protocols/oauth/index.mdx
================================================================================

---
title: OAuth Source
---

This source allows users to enroll themselves with an external OAuth-based Identity Provider. The generic provider expects the endpoint to return OpenID-Connect compatible information. Vendor-specific implementations have their own OAuth Source.

- Policies: Allow/Forbid users from linking their accounts with this provider.
- Request Token URL: This field is used for OAuth v1 implementations and will be provided by the provider.
- Authorization URL: This value will be provided by the provider.
- Access Token URL: This value will be provided by the provider.
- Profile URL: This URL is called by authentik to retrieve user information upon successful authentication.
- Consumer key/Consumer secret: These values will be provided by the provider.
- Scopes: Configure additional scopes to send to the provider.

    Starting with authentik 2022.10, the default scopes can be replaced by prefixing the value for scopes with `*`.

## OpenID Connect

### Well-known

Instead of configuring the URLs for a source manually, if the application you're configuring implements the [OpenID Connect Discovery Spec](https://openid.net/specs/openid-connect-discovery-1_0.html), you can configure the source with a single URL. The URL should always end with `.well-known/openid-configuration`. Many applications don't explicitly mention this URL, but for most of them it will be `https://application.company/.well-known/openid-configuration`.

This URL is fetched upon saving the source, and all the URLs will be replaced by the ones from the Discovery document. No automatic re-fetching is done.

### JWKS

To simplify machine-to-machine authentication, you can create an OAuth Source as a "trusted" source of JWTs. Create a source and configure either the Well-known URL or the OIDC JWKS URL, or you can manually enter the JWKS data if you so desire.

Afterwards, this source can be selected in one or multiple OAuth2 providers, and any JWT issued by any of the configured sources' JWKS will be able to authenticate. To learn more about this, see [JWT-authentication](../../../../add-secure-apps/providers/oauth2/machine_to_machine#jwt-authentication).

### `login_hint` parameter

If the OAuth authentication was started from within an authentik flow and the user has already identified themselves, authentik will set the `login_hint` parameter to the email address of the user. If the Identification stage has the **Pretend user exists** option enabled and a user could not be found, the `login_hint` value will be set to the identifier that the user entered.

## OAuth source property mappings

See the [overview](../../property-mappings/index.md) for information on how property mappings work.

### Expression data

The following variables are available to OAuth source property mappings:

- `info`: A Python dictionary containing OAuth claims. For example (values might differ depending on the source):
    ```python
    {
        "iss": "https://source.company",
        "sub": "f153e7da687eec8c8789c72b6cc6bb5197df7b48b263b3151f36908e1bc10691",
        "aud": "01e4DmQiG1d3kaewD3Mkz7E7kXknk9j43eZMkNaE",
        "aud": "a7809c1b1c4aaa50adfb68660a6273dd9c8d15e4",
        "email": "user@authentik.company",
        "email_verified": True,
        "name": "User",
        "given_name": "User",
        "preferred_username": "user",
        "nickname": "user",
    }
    ```
- `client`: An OAuth client object to make requests to the Source with authentication built-in.
- `token`: A Python dictionary containing OAuth tokens.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/identity-provider.mdx
================================================================================

---
title: Identity Provider (IdP)
sidebar_custom_props:
    termName: Identity Provider (IdP)
    tags:
        - Core Concepts
    shortDescription: Authority that authenticates users and issues assertions/tokens.
    longDescription: In SAML, the IdP issues assertions. In OIDC, this role is fulfilled by the OpenID Provider (OP), which is also the Authorization Server (AS) in OAuth2 terms; it authenticates users, obtains consent, and issues tokens.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/policy.mdx
================================================================================

---
title: Policy
sidebar_custom_props:
    termName: Policy
    tags:
        - Core Concepts
    shortDescription: A yes/no gate evaluated by type and settings.
    authentikSpecific: true
    longDescription: At a base level, a policy is a yes/no gate. It evaluates to True or False depending on the policy kind and settings. For example, a Group Membership policy evaluates to True if the user is a member of the specified group and False if not. Policies can conditionally apply stages, grant or deny access, and support other custom logic.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/policy.mdx
================================================================================

# Security Policy





================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/ldap/create-ldap-provider.mdx
================================================================================

---
title: Create an LDAP provider
---


Creating an authentik LDAP provider requires the following steps:

1. [Create an LDAP authentication flow _(optional)_](#create-an-ldap-authentication-flow-optional)
2. [Create an LDAP application and provider](#create-an-ldap-application-and-provider)
3. [Create a service account and assign the LDAP search permission](#create-a-service-account)
4. [Create an LDAP Outpost](#create-an-ldap-outpost)

## Create an LDAP authentication flow _(optional)_

The `default-authentication-flow` validates MFA by default. Duo, TOTP, and static authenticators are supported by the LDAP provider. WebAuthn and SMS are not supported.

If you plan to use only dedicated service accounts to bind to LDAP, or only use LDAP supported MFA authenticators, then you can use the default authentication flow and skip this section and continue with the [Create an LDAP application and provider](#create-an-ldap-application-and-provider) section.

Refer to [Code-Based MFA support](./index.md#code-based-mfa-support) for more information on LDAP and MFA.

### Create custom stages

You'll need to create the stages that make up the flow.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Stages**, and click **Create**.

#### Password Stage

First, you'll need to create a Password Stage.

3. Select **Password Stage** as the stage type, click **Next**, and set the following required configurations:
    - Provide a **Name** for the stage (e.g. `ldap-authentication-password-stage`).
    - For **Backends**, leave the default settings.
4. Click **Finish**

#### Identification Stage

Next, you'll need to create an Identification Stage.

5. On the **Stages** page, click **Create**.
6. Select **Identification Stage** as the stage type, click **Next**, and set the following required configurations:
    - Provide a **Name** for the stage (e.g. `ldap-identification-stage`).
    - For **User fields**, select `Username` and `Email` (and UPN if it is relevant to your setup).
    - Set **Password stage** to the Password Stage created in the previous section (e.g. `ldap-authentication-password-stage`)
7. Click **Finish**

#### User Login Stage

Finally, you'll need to create a User Login Stage.

8. On the **Stages** page, click **Create**.
9. Select **User Login Stage** as the stage type, click **Next**, and set the following required configurations:
    - Provide a **Name** for the stage (e.g. `ldap-authentication-login-stage`).
10. Click **Finish**

### Create an LDAP authentication flow

Now you'll need to create the LDAP authentication flow and bind the previously created stages.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Flows**, click **Create**, and set the following required configurations:
    - Provide a **Name**, **Title** and **Slug** for the flow (e.g. `ldap-authentication-flow`).
    - Set **Designation** to `Authentication`.
3. Click **Create**.
4. Click the name of the newly created flow, open the **Stage Bindings** tab, and click **Bind existing stage**.
5. Select the previously created LDAP Identification Stage (e.g.`ldap-identification-stage`), set the order to `10`, and click **Create**.
6. Click **Bind existing stage**.
7. Select the previously created LDAP User Login Stage (e.g.`ldap-authentication-login-stage`), set the order to `30`, and click **Create**.

## Create an LDAP application and provider

The LDAP application and provider can now be created.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications**, click **Create with Provider** to create an application and provider pair.
3. On the **New application** page, define the application details, and then click **Next**.
4. Select **LDAP Provider** as the **Provider Type**, and then click **Next**.
5. On the **Configure LDAP Provider** page, provide the configuration settings and then click **Submit** to create both the application and the provider.

:::info
If you followed the optional [Create an LDAP authentication flow](#create-an-ldap-authentication-flow-optional) section, ensure that you set **Bind flow** to newly created authentication flow (e.g. `ldap-authentication-flow`).
:::

## Create a service account

Create a service account to bind to LDAP with.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Users** and click **New User**.
3. Provide a name for the service account (e.g. `ldapservice`) and click **Create**.
4. Click the name of the newly created service account.
5. Under **Recovery**, click **Set password**, provide a secure password for the account, and click **Update password**.

:::info Default DN of service account
The default DN of this user will be `cn=ldapservice,ou=users,dc=ldap,dc=goauthentik,dc=io`
:::

### Assign the LDAP search permission to the service account

The service account needs permissions to search the LDAP directory. You'll need to create a role with the permission and assign the service account to that role.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Roles** and click **Create**.
3. Provide a name for the role (e.g. `LDAP search`) and then click **Create**.
4. Click on the newly created role and open the **Users** tab.
5. Click **Add existing user**, select the service account, and then click **Assign**.
6. Navigate to **Applications** > **Providers**.
7. Click on the name of the newly created LDAP provider and open the **Permissions** tab.
8. Click **Assign Object Permissions**.
9. Select the role that you created (e.g. `LDAP search`), enable the **Search full LDAP directory** permission, and then click **Assign**.

## Create an LDAP Outpost

The LDAP provider requires the deployment of an LDAP [Outpost](../../outposts/index.mdx).

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Outposts**, click **Create** and set the following required configurations:
    - Provide a **Name** for the outpost (e.g. `LDAP Outpost').
    - Set the **Type** as `LDAP`.
    - Set **Integration** to match your deployment method or manually deploy an outpost via [Docker-Compose](../../outposts/manual-deploy-docker-compose.md) or [Kubernetes](../../outposts/manual-deploy-kubernetes.md). For more information, refer to the [Outpost documentation](../../outposts/index.mdx).
    - Under **Applications**, select the LDAP application created in the previous section.
    - Under **Advanced settings**, set the required outpost configurations. For more information, refer to [Outpost Configuration](../../outposts/index.mdx#configuration)

3. Click **Create**.

:::warning Multiple LDAP providers
The LDAP Outpost selects different providers based on their Base DN. Adding multiple providers with the same Base DN will result in inconsistent access.
:::

## Configuration verification

You can test the LDAP provider by using the `ldapsearch` tool on Linux and macOS, or the `dsquery` tool on Windows.




================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/ldap/index.md
================================================================================

---
title: LDAP Provider
toc_max_heading_level: 5
---

The LDAP provider allows you to integrate with Service Providers using LDAP. It supports secure connections via LDAPS, code-based MFA authentication, basic LDAP schema compatibility, and can also be integrated with [SSSD](/integrations/services/sssd/) for authentication on Linux-based systems.

Refer to our documentation to learn how to [create a LDAP provider](./create-ldap-provider.mdx).

## LDAP directory

All users and groups in authentik's database are searchable via the LDAP directory served by the LDAP provider.

### Base DN

You can configure under which **Base DN** the LDAP directory should be available. The default is: `DC=ldap,DC=goauthentik,DC=io`

The setting is available under **Protocol settings** on the LDAP provider.

:::info Base DN when using multiple LDAP providers
When using multiple LDAP providers, each LDAP provider must have a unique Base DN. You can achieve this by prepending an application-specific OU or DC. e.g. `OU=appname,DC=ldap,DC=goauthentik,DC=io`
:::

### Users

Users are located under: `ou=users,<base DN>`

To aid compatibility, each user belongs to its own "virtual" group, as is standard on most Unix-like systems. This group does not exist in the authentik database, and is generated on the fly. These virtual groups are located under the `ou=virtual-groups,<base DN>` DN. They have the same attributes as groups but have an additional `objectClass`: `goauthentik.io/ldap/virtual-group`. The `gidNumber` attribute of each virtual group is equal to the `uidNumber` of the user.

The following attributes are returned for users:

| Attribute       | Description                                                                                                                                               |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cn`            | User's username                                                                                                                                           |
| `uid`           | Unique user identifier                                                                                                                                    |
| `uidNumber`     | A unique numeric identifier for the user                                                                                                                  |
| `name`          | User's name                                                                                                                                               |
| `displayName`   | User's display name                                                                                                                                       |
| `mail`          | User's email address                                                                                                                                      |
| `objectClass`   | List of these strings: "user", "organizationalPerson", "goauthentik.io/ldap/user"                                                                         |
| `memberOf`      | List of all DNs that the user is a member of                                                                                                              |
| `homeDirectory` | Default home directory path for the user, by default `/home/$username`. Can be overwritten by setting `homeDirectory` as an attribute on users or groups. |
| `ak-active`     | `true` if the account is active, otherwise `false`                                                                                                        |
| `ak-superuser`  | `true` if the account is part of a group with superuser permissions, otherwise `false`                                                                    |

:::info Custom attributes
Any custom attributes you set are also returned as LDAP attributes. Built-in attributes will be overwritten by custom attributes with matching names. Periods and slashes in custom attributes are sanitized.
:::

### Groups

Groups are located under: `ou=groups,<base DN>`

The following attributes are returned for groups:

| Attribute     | Description                                                                                          |
| ------------- | ---------------------------------------------------------------------------------------------------- |
| `cn`          | The group's name                                                                                     |
| `uid`         | Unique group identifier                                                                              |
| `gidNumber`   | Unique numeric identifier for the group                                                              |
| `member`      | List of all DNs of the group's members, including groups which have this group as their parent group |
| `memberOf`    | The DN of the parent group if this group has a parent group                                          |
| `objectClass` | List of these strings: "group", "goauthentik.io/ldap/group"                                          |

:::info Custom attributes
Any custom attributes you set are also returned as LDAP attributes. Built-in attributes will be overwritten by custom attributes with matching names. Periods and slashes in custom attributes are sanitized.
:::

## LDAPS via SSL or StartTLS

The LDAP provider supports secure connections via LDAPS using SSL or StartTLS.

You can configure SSL or StartTLS by configuring the **Certificate** and **TLS Server Name** settings on the provider.

The provider will pick the correct certificate based on the configured **TLS Server name** setting. The certificate is not picked based on the **Bind DN**, because the StartTLS operation should occur before the bind request to ensure that bind credentials are transmitted over TLS.

Configuring SSL or StartTLS enables you to bind on port 636 using LDAPS.

## Binding

Binding against the LDAP provider uses a flow in the background. This allows you to use the same policies and flows as you do for web-based logins.

The **Bind flow** determines the flow used for binding/authenticating users, and the **Unbind flow** determines the flow used when unbinding/de-authenticating users. Each is set under **Flow Settings** on the LDAP provider.

The following flow stages are supported by the LDAP provider:

- [Identification stage](../../flows-stages/stages/identification/index.mdx)
- [Password stage](../../flows-stages/stages/password/index.md)
- [Authenticator validation stage](../../flows-stages/stages/authenticator_validate/index.mdx)
- [User Logout stage](../../flows-stages/stages/user_logout.md)
- [User Login stage](../../flows-stages/stages/user_login/index.md)
- [Deny stage](../../flows-stages/stages/deny.md)

### Bind modes

The LDAP provider supports two different bind modes:

#### Direct bind

In this mode, the outpost will always execute the configured flow when a new bind request is received.

#### Cached bind

This mode uses the same logic as direct bind, however the result is cached for the entered credentials, and saved in memory for the standard session duration. Sessions are saved independently, meaning that revoking sessions does _not_ remove them from the outpost, and neither will changing a users credentials.

## Searching

Any user that is authorized to access the LDAP provider's application can search the LDAP directory. Without explicit permissions to do broader searches, a user's search request will return information about themselves, including user info, group info, and group membership.

[Users](../../../users-sources/user/index.mdx) and [roles](../../../users-sources/roles/index.md) can be assigned the permission `Search full LDAP directory` to allow them to search the full LDAP directory and retrieve information about all users in the authentik instance.

:::info
Up to authentik version 2024.8 this was managed using the LDAP provider's **Search group** setting, where users could be added to a group to grant them this permission. With authentik 2024.8 this is automatically migrated to the `Search full LDAP directory` permission, which can be assigned more flexibly.
:::

### Search modes

The LDAP provider supports two different search modes:

#### Direct search

In this mode, every LDAP search request will trigger one or more requests to the authentik core API. This will always return the latest data, however this has a performance hit due to all the layers the backend requests have to go through.

#### Cached search

In this mode, the outpost will periodically fetch all users and groups from the backend, hold them in memory, and respond to search queries directly. This means greatly improved performance but potentially returning old/invalid data.

## Code-based MFA support

:::info Authenticator support
Authenticator validation currently only supports DUO, TOTP and static authenticators. SMS-based authenticators are not supported as they require a code to be sent from authentik, which is not possible during the bind.
:::

The LDAP provider supports code-based MFA.

Code-based authenticators are only supported when the **Code-based MFA Support** setting is enabled on the provider and the configured **Bind flow** includes a [Authenticator Validation stage](../../flows-stages/stages/authenticator_validate/index.mdx).

When enabled, all users that bind to the LDAP provider should have a supported authenticator configured, as otherwise a password might be incorrectly rejected if it contains a semicolon.

For code-based authenticators, the code must be given as part of the bind/authentication password, separated by a semicolon.

For example, for the password `example-password` and the MFA code `123456`, the input must be `example-password;123456`.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/id-token.mdx
================================================================================

---
title: ID token
sidebar_custom_props:
    termName: ID token
    tags:
        - Tokens And Claims
    shortDescription: OIDC token describing the authenticated user.
    longDescription: JWT issued by the OpenID Provider describing the authentication event and the end-user (subject). RPs (Relying Party) validate issuer, audience, signature, expiry and the nonce; not intended for API authorization.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/scope.mdx
================================================================================

---
title: Scope
sidebar_custom_props:
    termName: Scope
    tags:
        - OAuth2/OIDC
    shortDescription: Permission strings requested by a client.
    longDescription: Define the level of access or claims requested; examples include `openid`, `email`, and `profile`.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/ldap-filter.mdx
================================================================================

---
title: LDAP search filter
sidebar_custom_props:
    termName: LDAP search filter
    tags:
        - Directory
    shortDescription: Expression selecting entries to return.
    longDescription: RFC 4515 filter syntax like `(objectClass=person)` or `(&(objectClass=user)(memberOf=...))` used to constrain LDAP queries.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/ldap-dn.mdx
================================================================================

---
title: Distinguished Name (DN)
sidebar_custom_props:
    termName: Distinguished Name (DN)
    tags:
        - Directory
    shortDescription: Unique path identifying an entry in LDAP.
    longDescription: Hierarchical identifier built from Relative Distinguished Names (RDNs), e.g., `uid=jane,ou=People,dc=example,dc=com`. Used to reference and bind to entries.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/ldap-base-dn.mdx
================================================================================

---
title: Base DN
sidebar_custom_props:
    termName: Base DN
    tags:
        - Directory
    shortDescription: Root DN (Distinguished Name) under which LDAP searches occur.
    longDescription: Starting point for LDAP queries and sync operations, typically the domain components such as `dc=example,dc=com` or an organizational unit.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/access-token.mdx
================================================================================

---
title: Access Token
sidebar_custom_props:
    termName: Access Token
    tags:
        - Tokens And Claims
    shortDescription: Bearer token used to access protected APIs.
    longDescription: >-
        Credential presented to resource servers to authorize requests. Often a JWT containing scopes, audience and expiry, but can be opaque and validated via introspection. Typically short-lived to reduce risk if leaked.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/refresh-token.mdx
================================================================================

---
title: Refresh token
sidebar_custom_props:
    termName: Refresh token
    tags:
        - Tokens And Claims
    shortDescription: Long-lived credential to obtain new access tokens.
    longDescription: Longer-lived credential used to obtain new access tokens without user interaction. Must be kept confidential, is commonly rotated on use, and can be revoked when compromised or no longer needed.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/claim.mdx
================================================================================

---
title: Claim
sidebar_custom_props:
    termName: Claim
    tags:
        - Tokens And Claims
    shortDescription: A piece of information about a subject.
    longDescription: Name-value pairs in tokens such as 'email', 'sub', or custom application attributes.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/entity-id.mdx
================================================================================

---
title: Entity ID
sidebar_custom_props:
    termName: Entity ID
    tags:
        - SAML
    shortDescription: Unique identifier for an IdP or Service Provider.
    longDescription: A URI/URL used in SAML metadata to uniquely identify a party in the federation.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/ldap.mdx
================================================================================

---
title: LDAP
sidebar_custom_props:
    termName: LDAP
    tags:
        - Directory
    shortDescription: Lightweight Directory Access Protocol for directory services.
    longDescription: Open protocol used to query and modify directory services like Active Directory or FreeIPA. Commonly used for user and group lookups and authentication binds.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/radius-shared-secret.mdx
================================================================================

---
title: RADIUS shared secret
sidebar_custom_props:
    termName: RADIUS shared secret
    tags:
        - Protocols
    shortDescription: Pre‑shared key between NAS and RADIUS server.
    longDescription: Used to compute request authenticators and validate responses. Must be unique per NAS and stored securely to prevent request forgery.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/ldap-bind-dn.mdx
================================================================================

---
title: Bind DN
sidebar_custom_props:
    termName: Bind DN
    tags:
        - Directory
    shortDescription: Account DN (Distinguished Name) used to authenticate to LDAP.
    longDescription: The DN of the service account used to perform searches or updates. Often paired with a bind password; may require least-privilege read access only.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/ldap-objectclass.mdx
================================================================================

---
title: ObjectClass
sidebar_custom_props:
    termName: ObjectClass
    tags:
        - Directory
    shortDescription: Schema class that defines required/allowed attributes.
    longDescription: LDAP entries declare one or more `objectClass` values (e.g., `inetOrgPerson`, `posixAccount`) that determine which attributes are valid.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/groups/group_ref.md
================================================================================

---
title: Group properties and attributes
---

## Object properties

The group object has the following properties:

- `name`: The group's display name.
- `is_superuser`: A boolean field that determines if the group's users are superusers.
- `parents`: The parent groups of this group.
- `roles`: The roles directly assigned to this group.
- `all_roles()`: Returns all roles for this group, including roles inherited from parent groups.
- `attributes`: Dynamic attributes, see [Attributes](#attributes).

## Examples

These are examples of how group objects can be used within authentik policies and property mappings.

### List all group members

Use the following examples to list all users that are members of a group:

```python title="Get all members of a group object"
group.users.all()
```

```python title="Specify a group object based on name and return all of its members"
from authentik.core.models import Group
Group.objects.get(name="name of group").users.all()
```

### List all roles for a group

Use the following examples to list roles assigned to a group:

```python title="Get directly assigned roles for a group object"
group.roles.all()
```

```python title="Get all roles including inherited from parent groups"
group.all_roles()
```

## Attributes

By default, authentik group objects are created with no attributes, however custom attributes can be set.

See [the user reference](../user/user_ref.mdx#attributes) for well-known attributes.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/groups/index.mdx
================================================================================

---
title: About groups
description: Learn about groups in authentik
---

For information about creating and editing groups refer to [Manage groups](./manage_groups.mdx).

## Hierarchy

Groups can be children of other groups. Members of children groups are effective members of the parent group.

When you bind a group to an application or flow, any members of any child group of the selected group will have access.

## Attributes

Attributes of groups are recursively merged, for all groups the user is a member of. For more information, see [Group properties and attributes](./group_ref.md).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/groups/manage_groups.mdx
================================================================================

---
title: Manage groups
description: "Learn how to work with groups in authentik."
---

A group is a collection of users. Refer to the following sections to learn how to create and manage groups, assign users and roles to groups, and how [permissions](../access-control/manage_permissions.md) work on a group level.

## Create a group

To create a new group, follow these steps:

1. In the Admin interface, navigate to **Directory > Groups**.
2. Click **Create** at the top of the Groups page.
3. In the Create box, define the following:
    - **Name** of the group
    - Whether or not users in that group will all be **super-users** (means anyone in that group has all permissions on everything)
    - Any **Parent** groups
    - Select **Roles** to apply to this group
    - Any custom attributes
4. Click **Create**.

:::info
To create a super-user, you need to add the user to a group that has super-user permissions. All members of that group are super-users.
:::

:::warning
Super-user permission is inherited by all descendant groups. Make sure you review every member of every descendant group to prevent accidentally granting super-user permission.
:::

## Modify a group

To edit the group's name, parent groups, whether the group grants superuser permissions, associated roles, and any custom attributes, click the Edit icon beside the role's name. Make the changes and then click **Update**.

Starting with authentik version 2025.2, the permission to change super-user status has been separated from the permission required to change the group. Now, the `Enable superuser status` and `Disable superuser status` permissions are explicitly required to enable and disable the super-user status.

To [add or remove users](../user/user_basic_operations.md#add-a-user-to-a-group) from the group, or to manage permissions assigned to the group, click on the name of the group to go to the group's detail page and then click on the **Permissions** tab.

## Delete a group

To delete a group, follow these steps:

1. In the Admin interface, navigate to **Directory > Groups**.
2. Select the checkbox beside the name of the group that you want to delete.
3. Click **Delete**.

## Assign a role to a group

You can assign a role to a group, and then all users in the group inherit the permissions assigned to that role. For instructions and more information, see [Assign a role to a group](../roles/manage_roles.md#assign-a-role-to-a-group).

:::info
Roles are inherited through group hierarchy. If a parent group has a role assigned, all child groups (and their users) automatically inherit that role's permissions. You can view both directly assigned and inherited roles on a group's detail page under the **Roles** tab.
:::

## Bind a group to an application

These bindings control which groups can access an application, and whether or not the application is visible in a group member's **My applications** page. If no bindings for an application are defined, this means that all users and groups can access the application.

For instructions refer to [Manage applications](../../add-secure-apps/applications/manage_apps.mdx#bind-a-user-or-group-to-an-application).

## Delegating group member management

To give a specific role or user the ability to manage group members, the following permissions need to be granted on the matching group object:

- Can view group
- Can add user to group
- Can remove user from group
- Can access admin interface (for managing a group's user within the authentik Admin interface)

In addition, the permission "Can view User" needs to be assigned, either globally or on specific users that should be manageable.

These permissions can be assigned to a [Role](../roles/index.md).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/protocols/ldap/index.md
================================================================================

---
title: LDAP Source
---

Sources allow you to connect authentik to an existing user directory. This source allows you to import users and groups from an LDAP server.

:::info
For Active Directory, follow the [Active Directory Integration](../../directory-sync/active-directory/index.md)

For FreeIPA, follow the [FreeIPA Integration](../../directory-sync/freeipa/index.md)
:::

## Configuration options for LDAP sources

To create or edit a source in authentik, open the Admin interface and navigate to **Directory > Federation and Social login**. There you can create a new LDAP source, or edit an existing one, using the following settings.

- **Enabled**: Toggle this option on to allow authentik to use the defined LDAP source.
- **Update internal password on login**: When the user logs in to authentik using the LDAP password backend, the password is stored as a hashed value in authentik. Toggle off (default setting) if you do not want to store the hashed passwords in authentik.
- **Sync users**: Enable or disable user synchronization between authentik and the LDAP source.
- **User password writeback**: Enable this option if you want to write password changes that are made in authentik back to LDAP.
- **Sync groups**: Enable/disable group synchronization between authentik and the LDAP source.
- **Delete Not Found Objects**: :ak-version[2025.6] This option synchronizes user and group deletions from LDAP sources to authentik. User deletion requires enabling **Sync users** and group deletion requires enabling **Sync groups**.

#### Connection settings

- **Server URI**: URI to your LDAP server/Domain Controller. You can specify multiple servers by separating URIs with a comma, like `ldap://ldap1.company,ldap://ldap2.company`. When using a DNS entry with multiple Records, authentik will select a random entry when first connecting.
    - **Enable StartTLS**: Enables StartTLS functionality. To use LDAPS instead, use port `636`.
    - **Use Server URI for SNI verification**: this setting is required for servers using TLS 1.3+

- **TLS Verification Certificate**: Specify a keypair to validate the remote certificate.
- **TLS Client authentication certificate**: Client certificate keypair to authenticate against the LDAP Server's Certificate.
- **Bind CN**: CN of the bind user. This can also be a UPN in the format of `user@domain.tld`.
- **Bind Password**: Password used during the bind process.
- **Base DN**: Base DN (distinguished name) used for all LDAP queries.

#### LDAP Attribute mapping

- **User Property Mappings** and **Group Property Mappings**: Define which LDAP properties map to which authentik properties. The default set of property mappings is generated for Active Directory. See also our documentation on [property mappings](#ldap-source-property-mappings).

    :::warning
    When the **Sync users** and/or the **Sync groups** options are enabled, their respective property mapping options must have at least one mapping selected, otherwise the sync will not start.
    :::

#### Additional Settings

- **Parent Group**: Parent group for all the groups imported from LDAP. An example use case would be to import Active Directory groups under a root `imported-from-ad` group.
- **User path**: Path template for all new users created.
- **Additional User DN**: Prepended to the base DN for user queries.
- **Additional Group DN**: Prepended to the base DN for group queries.
- **User object filter**: Consider objects matching this filter to be users.
- **Group object filter**: Consider objects matching this filter to be groups.
- **Lookup using a user attribute**: Acquire group membership from a User object attribute (`memberOf`) instead of a Group attribute (`member`). This works with directories with nested group memberships (Active Directory, RedHat IDM/FreeIPA), using `memberOf:1.2.840.113556.1.4.1941:` as the group membership field.
- **Group membership field**: The user object attribute or the group object attribute that determines the group membership for a user. If **Lookup using a user attribute** is set, this should be a user object attribute, otherwise a group object attribute.
- **User membership attribute**: Attribute name on authentik user objects which is checked against the **Group membership field**. Two common cases are:
    - If your groups have `member` attributes containing DNs, set this to `distinguishedName`. (The `distinguishedName` attribute for User objects in authentik is set automatically.)
    - If your groups have `memberUid` attributes containing `uid`s, set this to `uid`. Make sure that you've created a property mapping that creates an attribute called `uid`.
- **Object uniqueness field**: This field contains a unique identifier.

## LDAP source property mappings

See the [overview](../../property-mappings/index.md) for information on how property mappings work.

By default, authentik ships with [pre-configured mappings](#built-in-property-mappings) for the most common LDAP setups. These mappings can be found on the LDAP Source Configuration page in the Admin interface.

You can assign the value of a mapping to any user attribute. Keep in mind, though, data types from the LDAP server will be carried over. This means that with some implementations, where fields are stored as an array in LDAP, they will be saved as an array in authentik. To prevent this, use the built-in `list_flatten` function. Here is an example mapping for the user's username and a custom attribute for a phone number:

```python
return {
    "username": ldap.get("uid"), # list_flatten is automatically applied to top-level attributes
    "attributes": {
        "phone": list_flatten(ldap.get("phoneNumber")), # but not for attributes!
    },
}
```

### Built-in property mappings

LDAP property mappings are used when you define an LDAP source. These mappings define which LDAP property maps to which authentik property. By default, the following mappings are created:

- `authentik default Active Directory Mapping: givenName`
- `authentik default Active Directory Mapping: sAMAccountName`
- `authentik default Active Directory Mapping: sn`
- `authentik default Active Directory Mapping: userPrincipalName`
- `authentik default LDAP Mapping: mail`
- `authentik default LDAP Mapping: Name`
- `authentik default OpenLDAP Mapping: cn`
- `authentik default OpenLDAP Mapping: uid`

These are configured with most common LDAP setups.

### Expression data

The following variables are available to LDAP source property mappings:

- `ldap`: A Python dictionary containing data from LDAP.
- `dn`: The object DN.

### Additional expression semantics

If you need to skip synchronization for a specific object, you can raise the `SkipObject` exception. To do so, create or modify an LDAP property mapping to use an expression to define the object to skip.

**Example:**

```python
if ldap.get("cn") == "doNotSync":
    raise SkipObject
```

## Password login

By default, authentik doesn't update the password it stores for a user when they log in using their LDAP credentials. That means that if the LDAP server is not reachable by authentik, users will not be able to log in. This behavior can be turned on with the **Update internal password on login** setting on the LDAP source.

:::info
Sources created prior to the 2024.2 release have this setting turned on by default.
:::

Be aware of the following security considerations when turning on this functionality:

- Updating the LDAP password does not invalidate the password stored in authentik; however for LDAP Servers like FreeIPA and Active Directory, authentik will lock its internal password during the next LDAP sync. For other LDAP servers, the old passwords will still be valid indefinitely.
- Logging in via LDAP credentials overwrites the password stored in authentik if users have different passwords in LDAP and authentik.
- Custom security measures that are used to secure the password in LDAP may differ from the ones used in authentik. Depending on threat model and security requirements this could lead to unknowingly being non-compliant.

## Troubleshooting

To troubleshoot LDAP sources and their synchronization, see [LDAP Troubleshooting](../../../../troubleshooting/ldap_source.md).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/bindings-overview/index.md
================================================================================

---
title: authentik bindings
---

A binding is, simply put, a connection between two components. The use of a binding adds additional functionality to one the existing components; for example, a policy binding can cause a new stage to be presented within a flow to a specific user or group.

:::info
For information about creating and managing bindings, refer to [Work with bindings](./work-with-bindings.md).
:::

Bindings are an important part of authentik; the majority of configuration options are defined in bindings.

It's important to remember that bindings are instantiated objects themselves, and conceptually can be considered as a "connector" between two components. This is why you might read about "binding a binding", because technically, a binding is "spliced" into another binding, in order to intercept and enforce the criteria defined in the second binding. Note that stage-bindings are the only type of binding that you can add (or splice) another binding to.

## Relations with bindings

This diagram shows the relationships that bindings have between components. The primary components are _policy_, _user_, and _group_; these three objects can be bound to an application, application entitlement, flow, flow-stage binding, source, device, device access group, notification rule, or endpoint.

```mermaid

flowchart TD
    subgraph Directory
        user[User]
        group[Group]
    end

    subgraph Policy
        policy[Policy]
        policy_binding[Policy Binding]
    end

    subgraph Application
        application[Application]
        application_entitlement[Application Entitlement]
    end
    subgraph Sources
        source[Source]
    end
    subgraph Endpoint devices
        device[Device]
        device_access_group[Device Access Group]
    end
    subgraph Events
        notification_rule[Notification Rule]
    end
    subgraph RAC Provider
        endpoint[Endpoint]
    end
    subgraph Flows
        flow[Flow]
        flow_stage_binding[Flow Stage Binding]
        stage[Stage]
    end

    policy --> policy_binding
    user --> policy_binding
    group --> policy_binding

    policy_binding --> application
    policy_binding --> application_entitlement
    policy_binding --> source
    policy_binding --> device
    policy_binding --> device_access_group
    policy_binding --> notification_rule
    policy_binding --> flow
    policy_binding --> endpoint

    flow_stage_binding --> stage
    flow --> flow_stage_binding

    policy_binding --> flow_stage_binding
```

## Types of bindings

The two most common types of bindings in authentik are:

- policy bindings (which can also bind to users and groups)
- flow-stage bindings

### Policy bindings

A _policy binding_ connects a specific policy (a policy object) to a flow or flow-stage binding. With the policy binding, the flow (or specifically the stage within the flow) will now have additional content (i.e. the rules of the policy).

With policy bindings, you can also bind groups and users to another component (an application, a source, a flow, etc.). For example you can bind a group to an application, and then only that group (or other groups also bound to it), can access the application.

Bindings are also used for [Application Entitlements](../../add-secure-apps/applications/manage_apps.mdx#application-entitlements), where you can bind specific users or groups to an application as a way to manage who has access to certain areas _within an application_.

:::info
Be aware that policy bindings that are bound directly to the flow are evaluated _before_ the flow executes, so if the user is not authenticated, the flow will not start.
:::

### Flow-stage bindings

:::info
Be aware that depending on context, user and group policy bindings are not evaluated (i.e. ignored). For example, if you are not authenticated or if authentik has not yet identified the user, a policy binding that depends on knowing who the user is cannot be evaluated.
:::

Flow-stage bindings (also called stage bindings) are analyzed by authentik's Flow Plan, which starts with the flow, then assesses all of the bound policies, and then runs them in order to build out the plan.

A _flow-stage binding_ connects a stage to a flow in a specified order, so that the stage is executed at the desired point within the flow.

For example, you can create a binding for a specific group, and then [bind that to a stage binding](../flows-stages/stages/index.md#bind-users-and-groups-to-a-flows-stage-binding), with the result that everyone in that group now will see that stage (and any policies bound to that stage) as part of their flow. Or more specifically, and going one step deeper, you can also _bind a binding to a binding_.

Flow-stage bindings can have policy bindings bound to them; this can be used to conditionally run or skip stages within a flow. There are two settings in a flow-stage binding that configure _when_ these policies are executed:

- **Evaluate when flow is planned**
  Policies are evaluated when authentik creates a flow plan that contains a reference to all of the stages that the user will need to go through to complete the flow. In this case, user-specific attributes are only available if the user is already authenticated before beginning the flow.

- **Evaluate when the stage is run**
  Policies bound to a flow-stage binding are evaluated before the stage is run (i.e. after the flow has started but before the stage is reached in the flow). Therefore, the context with which policy bindings to the flow-stage binding are evaluated reflects the current state of the flow.

    For example, when configuring an authentication flow with an identification stage bound to it, and a user bound to a Captcha flow-stage binding, with this setting (**Evaluate when stage is run**) enabled authentik can check against the user who has identified themselves previously.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/bindings-overview/work-with-bindings.md
================================================================================

---
title: Work with bindings
---

As covered in the [overview](./index.md), bindings interact with many other components.

For instructions to create a binding, refer to the documentation for the specific components:

- [Bind a stage to a flow](../flows-stages/stages/index.md#bind-a-stage-to-a-flow)
- [Bind a policy to a flow, stage, application, or source](../../customize/policies/working_with_policies.md#bind-a-policy-to-a-flow-stage-application-or-source)
- [Bind users or groups to a specific application](../applications/manage_apps.mdx#use-bindings-to-control-access)
- [Bind users and groups to a stage binding, to define whether or not that stage is shown](../flows-stages/stages/index.md#bind-users-and-groups-to-a-flows-stage-binding)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/applications/index.md
================================================================================

---
title: Applications
---

Applications, as defined in authentik, are used to configure and separate the authorization/access control and the appearance of a specific software application in the **My applications** page.

When a user logs into authentik, they see a list of the applications for which authentik is configured to provide authentication and authorization (the applications that they are authorized to use).

Applications are the "other half" of providers. They typically exist in a 1-to-1 relationship; each application needs a provider and every provider can be used with one application. Applications can, however, use specific, additional providers to augment the functionality of the main provider. For more information, see [Backchannel providers](./manage_apps.mdx#backchannel-providers).

Furthermore, the [RAC (Remote Access Control)](../providers/rac/index.md) feature uses a single application and a single provider, but multiple "endpoints". An endpoint defines each remote machine.

:::info
For information about creating and managing applications, refer to [Manage applications](./manage_apps.mdx).
:::

## Appearance

Applications are displayed to users when:

- The user has access defined via policies (or the application has no policies bound)
- A valid Launch URL is configured/could be guessed, this consists of URLs starting with http:// and https://

The following options can be configured:

- _Name_: This is the name shown for the application card
- _Launch URL_: The URL that is opened when a user clicks on the application. When left empty, authentik tries to guess it based on the provider

    You can use placeholders in the launch url to build them dynamically based on the logged in user. For example, you can set the Launch URL to `https://goauthentik.io/%(username)s`, which will be replaced with the currently logged in user's username.

    For a reference of all fields available, see [the API schema for the User object](https://api.goauthentik.io/reference/core-users-retrieve/).

    Only applications whose launch URL starts with `http://` or `https://` or are relative URLs are shown on the users' **My applications** page. This can also be used to hide applications that shouldn't be visible on the **My applications** page but are still accessible by users, by setting the _Launch URL_ to `blank://blank`.

- _Icon (URL)_: Optionally configure an Icon for the application. You can select from files uploaded to the [Files](../../customize/files.md) library or enter an absolute URL.

- _Publisher_: Text shown in the application card's expandable kebab menu (⋮)
- _Description_: Text shown in the application card's expandable kebab menu (⋮)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/applications/manage_apps.mdx
================================================================================

---
title: Manage applications
---

Managing the applications that your team uses involves several tasks, from initially adding the application and provider, to controlling access and visibility of the application, to providing access URLs.

### Create an application and provider pair

To add an application to authentik and have it display on users' **My applications** page, follow these steps:

1. Log in to authentik as an administrator and open the authentik Admin interface.

2. Navigate to **Applications > Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create.)**

3. In the **New application** box, define the application details, the provider type and configuration settings, and bindings for the application.
    - **Application**: provide a name, an optional group for the type of application, the policy engine mode, and optional UI settings.

    - **Choose a Provider**: select the provider types for this application.

    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and any additional required configurations.

    - **Configure Bindings**: to manage which applications a user can view and access via their **My applications** page, you can optionally create a [binding](../bindings-overview/index.md) between the application and a specific policy, group, or user. Note that if you do not define any bindings, then all users have access to the application. For more information about user access, refer to our documentation about [policy-driven authorization](#policy-driven-authorization), [using application entitlements](../applications/manage_apps.mdx#create-an-application-entitlement) and [hiding an application](#hide-applications).

4. On the **Review and Submit Application** panel, review the configuration for the new application and its provider, and then click **Submit**.

## Use bindings to control access

By default, all users can access applications when no bindings are defined on the application.

You can bind policies, groups, and users to grant access to an application. When nothing is bound, everyone has access. Binding a policy restricts access to specific Users or Groups, or by other custom policies such as restriction to a set time-of-day or a geographic region.

When multiple policies/groups/users are attached, you can configure the _Policy engine mode_ to either:

- Require users to pass all policies or be member of all groups (ALL), or
- Require users to pass any single policy or be member of any group (ANY)

The most common ways to control access to an application by using bindings are:

1. [Create a policy binding](../../customize/policies/working_with_policies.md#bind-a-policy-to-an-application) in which a policy is used to determine whether or not a user can access an application.
2. [Bind a user or group to the application](#bind-a-user-or-group-to-an-application).

### Policy-driven authorization

To use a [policy](../../customize/policies/index.md) to control which users or groups can access an application, click on an application in the applications list, click the **Policy/Group/User Bindings** tab, and then select **Policy** from the **Policy/Group/User Bindings** options.

### Bind a user or group to an application

You can bind a user or group to an application either when you create a new application and provider or later, after the application is created.

#### When creating an application and provider

Follow the instructions for [creating a new application and provider](#create-an-application-and-provider-pair). On the **Policy/Group/User Bindings** tab at the top of the page, you can select **Group** or \*User\*\* to bind a specific group or userto the application.

#### Add binding to an existing application

To bind a user or group to an existing application, click on an application in the applications list, select **Group** or **User** from the **Policy/Group/User Bindings** options, and then select the group or user that you want to bind to the application.

## Application Entitlements


Application entitlements can be used through authentik to manage authorization _within an application_ (what areas of the app users or groups can access). Entitlements are scoped to a single application and can be bound to multiple users and/or groups (binding policies is not currently supported), giving them access to the entitlement. An application can either check for the name of the entitlement (via the `entitlements` scope), or via attributes stored in entitlements.

An authentik admin can create an entitlement [in the Admin interface](#create-an-application-entitlement) or using the [authentik API](/api).

Because entitlements exist within an application, names of entitlements must be unique within an application. This also means that entitlements are deleted when an application is deleted.

### Using entitlements

Entitlements to which a user has access can be retrieved using the `user.app_entitlements()` function in property mappings/policies. This function needs to be passed the specific application for which to get the entitlements. For example:

```python
entitlements = [entitlement.name for entitlement in request.user.app_entitlements(provider.application)]
return {
    "entitlements": entitlements,
}
```

### Attributes

Each entitlement can store attributes similar to user and group attributes. These attributes can be accessed in property mappings and passed to applications via `user.app_entitlements_attributes`. For example:

```python
attrs = request.user.app_entitlements_attributes(provider.application)
return {
    "my_attr": attrs.get("my_attr")
}
```

### Create an application entitlement

1. Open the Admin interface and navigate to **Applications > Applications**.
2. Click the name of the application for which you want to create an entitlement.
3. Click the **Application entitlements** tab at the top of the page, and then click **Create entitlement**. Provide a name for the entitlement, enter any optional **Attributes**, and then click **Create**.
4. In the list locate the entitlement to which you want to bind a user or group, and then **click the caret (>) to expand the entitlement details.**
5. In the expanded area, click **Bind existing Group/User**.
6. In the **Create Binding** box, select either the tab for **Group** or **User**, and then in the drop-down list, select the group or user.
7. Optionally, configure additional settings for the binding, and then click **Create** to create the binding and close the box.

## Hide applications

To hide an application without modifying its policy settings or removing it, you can simply set the _Launch URL_ to `blank://blank`, which will hide the application from users.

Keep in mind that users still have access, so they can still authorize access when the login process is started from the application.

## Launch URLs

To give users direct links to applications, you can now use a URL like `https://authentik.company/application/launch/<slug>/`. If the user is already logged in, they will be redirected to the application automatically. Otherwise, they'll be sent to the authentication flow and, if successful, forwarded to the application.

## Backchannel providers

Backchannel providers can augment the functionality of applications by using additional protocols. The main provider of an application provides the SSO protocol that is used for logging into the application. Then, additional backchannel providers can be used for protocols such as [SCIM](../providers/scim/index.md) and [LDAP](../providers/ldap/index.md) to provide directory syncing.

Note that any access restrictions that are configured on an application apply to all of its backchannel providers.

To create a backchannel provider and then add it to an existing application, follow these instructions:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click **Create**.

- **Choose a Provider type**: The protocol for a backchannel provider must be [SCIM](../providers/scim/index.md), [LDAP](../providers/ldap/index.md), [Google Workspace (GWS)](../providers/gws/index.md), [Microsoft Entra ID](../providers/entra/index.md), or [Shared Signals Framework (SSF)](../providers/ssf/index.md).
- **Configure the Provider**: Enter any required configurations.

3. Click **Finish** to save the provider.
4. Edit the application by going to **Applications** > **Applications**, and clicking the edit icon beside the application that you want to edit.
5. In the **Backchannel Providers** field, click the Add icon (**+**), select the backchannel provider that you just created, and click **Add**.
6. Click **Update**.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/outposts/manual-deploy-docker-compose.md
================================================================================

---
title: Manual Outpost deployment in Docker Compose
---

To deploy an outpost with Docker Compose, use the appropriate snippet from the options below and add it to your Compose file.

You can also run the outpost in a separate Compose project, you just have to ensure that the outpost container can reach your application container.

### Proxy outpost

```yaml
services:
    authentik_proxy:
        image: ghcr.io/goauthentik/proxy
        # Optionally specify the container's network, which must be able to reach the core authentik server.
        # networks:
        #   - foo
        ports:
            - 9000:9000
            - 9443:9443
        environment:
            AUTHENTIK_HOST: https://authentik.company
            AUTHENTIK_INSECURE: "false"
            AUTHENTIK_TOKEN: token-generated-by-authentik
            # Optional setting to be used when `authentik_host` for internal communication doesn't match the public URL.
            # AUTHENTIK_HOST_BROWSER: https://external-domain.tld
```

### LDAP outpost

```yaml
services:
    authentik_ldap:
        image: ghcr.io/goauthentik/ldap
        # Optionally specify the container's network, which must be able to reach the core authentik server.
        # networks:
        #   - foo
        ports:
            - 389:3389
            - 636:6636
        environment:
            AUTHENTIK_HOST: https://authentik.company
            AUTHENTIK_INSECURE: "false"
            AUTHENTIK_TOKEN: token-generated-by-authentik
```

### RAC outpost

```yaml
services:
    rac_outpost:
        image: ghcr.io/goauthentik/rac
        # Optionally specify the container's network, which must be able to reach the core authentik server.
        # networks:
        #   - foo
        environment:
            AUTHENTIK_HOST: https://authentik.company
            AUTHENTIK_INSECURE: "false"
            AUTHENTIK_TOKEN: token-generated-by-authentik
```

### RADIUS outpost

```yaml
services:
    radius_outpost:
        image: ghcr.io/goauthentik/radius
        # Optionally specify the container's network, which must be able to reach the core authentik server.
        # networks:
        #   - foo
        ports:
            - 1812:1812/udp
        environment:
            AUTHENTIK_HOST: https://authentik.company
            AUTHENTIK_INSECURE: "false"
            AUTHENTIK_TOKEN: token-generated-by-authentik
```



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/outposts/manual-deploy-kubernetes.md
================================================================================

---
title: Manual Outpost deployment on Kubernetes
---

Use the following manifest, replacing all values surrounded with `__`.

Afterwards, configure the proxy provider to connect to `<service name>.<namespace>.svc.cluster.local`, and update your Ingress to connect to the `authentik-outpost` service.

```yaml
apiVersion: v1
kind: Secret
metadata:
    labels:
        app.kubernetes.io/instance: __OUTPOST_NAME__
        app.kubernetes.io/name: authentik-outpost
    name: authentik-outpost-api
type: Opaque
stringData:
    AUTHENTIK_HOST: "__AUTHENTIK_URL__"
    AUTHENTIK_INSECURE: "true"
    AUTHENTIK_TOKEN: "__AUTHENTIK_TOKEN__"
---
apiVersion: v1
kind: Service
metadata:
    labels:
        app.kubernetes.io/instance: __OUTPOST_NAME__
        app.kubernetes.io/name: authentik-outpost
    name: authentik-outpost
spec:
    ports:
        - name: http
          port: 9000
          protocol: TCP
          targetPort: http
        - name: https
          port: 9443
          protocol: TCP
          targetPort: https
    type: ClusterIP
    selector:
        app.kubernetes.io/instance: __OUTPOST_NAME__
        app.kubernetes.io/name: authentik-outpost
---
apiVersion: apps/v1
kind: Deployment
metadata:
    labels:
        app.kubernetes.io/instance: __OUTPOST_NAME__
        app.kubernetes.io/name: authentik-outpost
    name: authentik-outpost
spec:
    selector:
        matchLabels:
            app.kubernetes.io/instance: __OUTPOST_NAME__
            app.kubernetes.io/name: authentik-outpost
    template:
        metadata:
            labels:
                app.kubernetes.io/instance: __OUTPOST_NAME__
                app.kubernetes.io/name: authentik-outpost
        spec:
            containers:
                - image: ghcr.io/goauthentik/proxy
                  name: proxy
                  ports:
                      - containerPort: 9000
                        name: http
                        protocol: TCP
                      - containerPort: 9443
                        name: https
                        protocol: TCP
                  envFrom:
                      - secretRef:
                            name: authentik-outpost-api
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
    annotations:
        # This example includes annotations for common ingress controllers,
        # remove annotations not used
        nginx.ingress.kubernetes.io/affinity: cookie
        nginx.ingress.kubernetes.io/proxy-buffer-size: 16k
        nginx.ingress.kubernetes.io/proxy-busy-buffers-size: 32k,
        nginx.ingress.kubernetes.io/proxy-buffers-number: "4"
        traefik.ingress.kubernetes.io/affinity: "true"
    labels:
        app.kubernetes.io/instance: __OUTPOST_NAME__
        app.kubernetes.io/name: authentik-outpost
    name: authentik-outpost
spec:
    ingressClassName: nginx
    rules:
        - host: __EXTERNAL_HOSTNAME__
          http:
              paths:
                  - path: /
                    pathType: Prefix
                    backend:
                        service:
                            name: authentik-outpost
                            port:
                                name: http
```



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/outposts/_config.md
================================================================================

```yaml
# Log level that the outpost will set
# Allowed levels: trace, debug, info, warning, error
# Applies to: non-embedded
log_level: debug
# Interval at which the outpost will refresh the providers
# from authentik. For caching outposts (such as LDAP), the
# cache will also be invalidated at that interval.
# (Format: hours=1;minutes=2;seconds=3).
refresh_interval: minutes=5
########################################
# The settings below are only relevant when using a managed outpost
########################################
# URL that the outpost uses to connect back to authentik
authentik_host: https://authentik.tld/
# Disable SSL Validation for the authentik connection
authentik_host_insecure: false
# Optionally specify a different URL used for user-facing interactions
# Applies to: proxy outposts
authentik_host_browser:
# Template used for objects created (deployments/containers, services, secrets, etc)
object_naming_template: ak-outpost-%(name)s
# Use a specific docker image for this outpost rather than the default. This also applies to Kubernetes
# outposts.
# Applies to: non-embedded
container_image:
########################################
# Docker outpost specific settings
########################################
# Network the outpost container should be connected to
# Applies to: non-embedded
docker_network: null
# Optionally disable mapping of ports to outpost container, may be useful when using docker networks
# (Available with 2021.9.4+)
# Applies to: non-embedded
docker_map_ports: true
# Optionally additional labels for docker containers
# (Available with 2022.1.2)
# Applies to: non-embedded
docker_labels: null
########################################
# Kubernetes outpost specific settings
########################################
# Replica count for the deployment of the outpost
# Applies to: non-embedded
kubernetes_replicas: 1
# Namespace to deploy in, defaults to the same namespace authentik is deployed in (if available)
kubernetes_namespace: authentik
# Any additional annotations to add to the ingress object, for example cert-manager
kubernetes_ingress_annotations: {}
# Name of the secret that is used for TLS connections, leave empty to disable TLS
kubernetes_ingress_secret_name: authentik-outpost-tls
# pathType to use on routes. Defaults to `Prefix`. Some ingress-nginx deployments need this to be set to `ImplementationSpecific`.
# Service kind created, can be set to LoadBalancer for LDAP outposts for example
kubernetes_service_type: ClusterIP
# Disable any components of the kubernetes integration, can be any of
# - 'secret'
# - 'deployment'
# - 'service'
# - 'prometheus servicemonitor'
# - 'ingress'
# - 'traefik middleware'
kubernetes_disabled_components: []
# If the above docker image is in a private repository, use these secrets to pull.
# NOTE: The secret must be created manually in the namespace first.
# Applies to: non-embedded
kubernetes_image_pull_secrets: []
# Optionally configure an ingress class name. If not set, the ingress will use the cluster's
# default ingress class
# (Available with 2022.11.0+)
# Applies to: proxy outposts
kubernetes_ingress_class_name: null
# Optionally apply an RFC 6902 compliant patch to the Kubernetes objects.
# For an understanding of how this works, refer to the link below:
# https://github.com/kubernetes-sigs/kustomize/blob/master/examples/jsonpatch.md
#
# This value expects a mapping where the key represents
# the Kubernetes component that shall be patched.
# It can be any of the same values supported by `kubernetes_disabled_components`.
#
# For example use this patch to add custom resource requests and limits
# to the outpost deployment:
#
# deployment:
#   - op: add
#     path: "/spec/template/spec/containers/0/resources"
#     value:
#       requests:
#         cpu: 2000m
#         memory: 2000Mi
#       limits:
#         cpu: 4000m
#         memory: 8000Mi
kubernetes_json_patches: null
```



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/outposts/index.mdx
================================================================================

---
title: Outposts
---

An outpost is a single deployment of an authentik component, essentially a service, that can be deployed anywhere that allows for a connection to the authentik API.

An outpost is required if you use any of the following types of providers with your application:

- [LDAP Provider](../providers/ldap/index.md)
- [Proxy Provider](../providers/proxy/index.md)
- [RADIUS Provider](../providers/radius/index.mdx)
- [RAC Provider](../providers/rac/index.md)

These types of providers use an outpost for increased flexibility and speed. Instead of the provider logic being implemented in authentik Core, these providers use an outpost to handle the logic, which provides improved performance.

An additional advantage of using an outpost is that outposts, like authentik itself, do not require access to the wider internet. Transactions between the application, the provider, and the outpost occur via the authentik API, and support single sign-on operations in firewalled or airgapped deployments and offline connections to remote machines that are not on the internet.

An outpost is given permissions to access the authentik API using a service account and token, both of which are auto-generated when you create a new outpost. The outpost is granted rights to only the application/provider pairs configured (and other necessary related objects such as certificates).

Any change made to the outpost's associated app or provider immediately triggers an event to update the configuration data stored on the outpost, via websockets. Websockets are used also by the outpost to send healthchecks to the authentik Core.

## Create and configure an outpost

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Outposts** and then click **Create**.

![](./outpost-create.png)

3. Set the following values:
    - **Name**: define a name for the outpost.
    - **Type**: select the outpost type (Proxy, LDAP, Radius, RAC).
    - **Integration**: select either Docker or Kubernetes, or optionally select `----` and [manually deploy the outpost](#outpost-integrations).
    - **Applications**: select the applications that you want the outpost to serve.
    - **Advanced settings (optional)**: for further optional configuration settings, refer to [Configuration](#configuration) below.

4. Click **Create**.

Upon creation, a service account and a token is generated. The service account only has permissions to read the outpost and provider configuration. This token is used by the outpost to connect to authentik.

## Outpost integrations

authentik can manage the deployment, updating, and general lifecycle of an outpost. To communicate with the underlying platforms on which the outpost is deployed, authentik has several built-in integrations.

- If you've deployed authentik on Docker Compose, authentik automatically creates an integration for the local docker socket (See [Docker](./integrations/docker.md)).
- If you've deployed authentik on Kubernetes, with `kubernetesIntegration` set to true (default), authentik automatically creates an integrations for the local Kubernetes Cluster (see [Kubernetes](./integrations/kubernetes.md)).

To deploy an outpost with these integrations, select them during the creation of an outpost. A background task is started, which creates the container/deployment. The outpost deployment can be monitored from the **Dashboards > System Tasks** page in the Admin interface.

To deploy an outpost manually, see:

- [Kubernetes](./manual-deploy-kubernetes.md)
- [Docker Compose](./manual-deploy-docker-compose.md)

## Configuration

Outposts fetch their configuration from authentik. Below are all the options you can set, and how they influence the outpost.



## Prometheus Metrics

Each authentik outpost has a Prometheus metrics endpoint accessible under port `:9300/metrics`. This endpoint is not mapped via Docker, as the endpoint doesn't have any authentication.

For the embedded outpost, the metrics of the outpost and the metrics of the core authentik server are both returned under the same endpoint.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/outposts/upgrading.md
================================================================================

---
title: Upgrading an Outpost
---

Outposts deployed using the [Docker](./integrations/docker.md) or [Kubernetes](./integrations/kubernetes.md) integrations are managed by authentik and are upgraded automatically. Outposts deployed manually via [Docker](./manual-deploy-docker-compose.md) or [Kubernetes](./manual-deploy-kubernetes.md) must be upgraded by updating the outpost's image tag to the new version.

To check if any outposts are out-of-date, navigate to **Applications** > **Outposts** and look for a message in the **Health and Version** column.

A red warning message will be shown on any outposts running outdated versions:

![](./outpost-upgrade.png)

An up-to-date outpost will show a green message indicating the last successful connection with authentik:

![](./outpost-upgrade2.png)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/index.mdx
================================================================================

---
title: Providers
slug: /providers
---


A Provider is an authentication method, a service that is used by authentik to authenticate the user for the associated application. Common Providers are OpenID Connect (OIDC)/OAuth2, LDAP, SAML, a generic proxy provider, and others.

Providers are the "other half" of [applications](../applications/index.md). They typically exist in a 1-to-1 relationship; each application needs a provider and every provider can be used with one application.

You can create a new provider in the Admin interface, or you can use the [**Create with Provider** option](../applications/manage_apps.mdx#create-an-application-and-provider-pair) to create a new application and its provider at the same time.

Applications can use additional providers to augment the functionality of the main provider. For more information, see [Backchannel providers](../applications/manage_apps.mdx#backchannel-providers).

When you create certain types of providers, you need to select specific [flows](../flows-stages/flow/index.md) to apply to users who access authentik via the provider. To learn more, refer to our [default flow documentation](../flows-stages/flow/examples/default_flows.md).

You can also create a SAML provider by uploading an SP metadata XML file that contains the service provider's configuration data. SAML metadata is used to share configuration information between the Identity Provider (IdP) and the Service Provider (SP). An SP metadata XML file typically contains the SP certificate, the entity ID, the Assertion Consumer Service URL (ACS URL), and a log out URL (SingleLogoutService).

To learn more about each provider type, refer to the documentation for each provider:




================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/outposts/embedded/embedded.mdx
================================================================================

---
title: Embedded Outpost
---

Starting with 2021.8.1, authentik comes with an embedded outpost. This has been added to simplify deployment for users using the Proxy provider.

The embedded outpost runs in the main `server` container, and is managed by authentik itself. The embedded outpost authenticates itself via the secret key.

You can access the embedded outpost on the same ports as authentik itself, 9000 and 9443.

If the embedded outpost doesn't make sense for your deployment, you can simply ignore it.

### Configuration

Since authentik doesn't know its own "primary" URL, there might be some configuration required.

By default, when opening the admin dashboard on a fresh install, authentik will automatically configure the outpost to use the same URL as was used to access authentik.

If this isn't correct, or needs to be changed, click the edit button on the right of the outpost, and set the value of `authentik_host` to the URL you want to log in with.
Make sure to set it to a full URL; only configuring a hostname or FQDN will not work.

Additionally, most of the other configuration options can be used as with any other outpost, except for items that are marked as "non-embedded".



### Routing

Routing is handled like this:

1. Paths starting with `/static`, `/media` and `/help` return packaged CSS/JS files, and user-uploaded media files.
2. Paths starting with `/outpost.goauthentik.io` are sent to the embedded outpost.
3. Any hosts configured in the providers assigned to the embedded outpost are sent to the outpost.
4. Everything remaining is sent to the authentik backend server.

### Differences

There are a few more differences between managed outposts and the embedded outpost, mainly due to the fact that authentik can't fully manage the containers.

1. (Docker-only) No automatic traefik labels are added to the server container.

    When you deploy a managed outpost on docker, the container has several labels to automatically configure traefik. This is not done for the embedded outpost.

2. (Kubernetes-only) An additional service is created.

    Since authentik does not know what the normal authentik Service is called, another one is created with a common set of labels that is always set.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/outposts/integrations/docker.md
================================================================================

---
title: Docker
---

The Docker integration automatically deploys and manages outpost containers using the Docker HTTP API.

This integration has the advantage over manual deployments of automatic updates that whenever authentik is upgraded to a later version, it also upgrades the outposts.

The following outpost settings are used:

- `object_naming_template`: Configures how the container is called.
- `container_image`: Optionally overwrites the standard container image (see [Configuration](../../../install-config/configuration/configuration.mdx#authentik_outposts) to configure the global default).
- `docker_network`: The Docker network the container should be added to. This needs to be modified if you plan to connect to authentik using the internal hostname.
- `docker_map_ports`: Enable/disable the mapping of ports. When using a proxy outpost with Traefik for example, you might not want to bind ports as they are routed through Traefik.
- `docker_labels`: Optional additional labels that can be applied to the container.

The container is created with the following hardcoded properties:

- Labels
    - `io.goauthentik.outpost-uuid`: Used by authentik to identify the container, and to allow for name changes.

    Additionally, the proxy outposts have the following extra labels to add themselves into Traefik automatically.
    - `traefik.enable`: "true"
    - `traefik.http.routers.ak-outpost-<outpost-name>-router.rule`: `Host(...)`
    - `traefik.http.routers.ak-outpost-<outpost-name>-router.service`: `ak-outpost-<outpost-name>-service`
    - `traefik.http.routers.ak-outpost-<outpost-name>-router.tls`: "true"
    - `traefik.http.services.ak-outpost-<outpost-name>-service.loadbalancer.healthcheck.path`: "/outpost.goauthentik.io/ping"
    - `traefik.http.services.ak-outpost-<outpost-name>-service.loadbalancer.healthcheck.port`: "9300"
    - `traefik.http.services.ak-outpost-<outpost-name>-service.loadbalancer.server.port`: "9000"

## Permissions

authentik requires the following permissions from the Docker API:

- Images/Pull: authentik tries to pre-pull the custom image if one is configured, otherwise falling back to the default image.
- Containers/Read: Gather infos about currently running container
- Containers/Create: Create new containers
- Containers/Kill: Cleanup during upgrades
- Containers/Remove: Removal of outposts
- System/Info: Gather information about the version of Docker running

## Docker Socket Proxy

Mounting the Docker socket to a container comes with some inherent security risks. Applications inside these containers have unfettered access to the full Docker API, which can be used to gain unauthorized access to sensitive Docker functions.

It can also result in possible root escalation on the host system.

To prevent this, many people use projects like [docker-socket-proxy](https://docs.linuxserver.io/images/docker-socket-proxy/), which limit access to the Docker socket by filtering and restricting API calls that these applications can make.

See [permissions](#permissions) for the list of APIs that authentik needs access to.

:::warning
Connections from authentik to Docker socket proxy must be made over HTTP, not TCP, e.g. `http://<docker-socket-proxy hostname or container name>:<port>`.
:::

## Remote hosts (TLS)

To connect remote hosts, follow this guide from Docker [Use TLS (HTTPS) to protect the Docker daemon socket](https://docs.docker.com/engine/security/protect-access/#use-tls-https-to-protect-the-docker-daemon-socket) to configure Docker.

Afterwards, create two certificate-keypairs in authentik:

- `Docker CA`, with the contents of `~/.docker/ca.pem` as Certificate
- `Docker Cert`, with the contents of `~/.docker/cert.pem` as the certificate and `~/.docker/key.pem` as the private key.

Create an integration with `Docker CA` as _TLS Verification Certificate_ and `Docker Cert` as _TLS Authentication Certificate_.

## Remote hosts (SSH)

authentik can connect to remote Docker hosts using SSH. To configure this, create a new SSH keypair using these commands:

```shell
# Generate the keypair itself, using RSA keys in the PEM format
ssh-keygen -t rsa -f authentik  -N "" -m pem
# Generate a certificate from the private key, required by authentik.
# The values that openssl prompts you for are not relevant
openssl req -x509 -sha256 -nodes -days 365 -out certificate.pem -key authentik
```

You'll end up with three files:

- `authentik.pub` is the public key, this should be added to the `~/.ssh/authorized_keys` file on the target host and user.
- `authentik` is the private key, which should be imported into a Keypair in authentik.
- `certificate.pem` is the matching certificate for the keypair above.

Modify/create a new Docker integration, and set your _Docker URL_ to `ssh://hostname`, and select the keypair you created above as _TLS Authentication Certificate/SSH Keypair_.

The _Docker URL_ field include a user, if none is specified authentik connects with the user `authentik`.

#### Advanced SSH config

With the above configuration, authentik will create and manage an `~/.ssh/config` file. If you need advanced configuration, for example SSH Certificates, you can mount a custom SSH Config file.

Mount the config file into `/authentik/.ssh/config`, and mount any other relevant files into a directory under `/opt`. Afterwards, create an integration using `ssh://hostname`, and don't select a keypair.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/outposts/integrations/kubernetes.md
================================================================================

---
title: Kubernetes
---

The kubernetes integration will automatically deploy outposts on any Kubernetes Cluster.

This integration has the advantage over manual deployments of automatic updates (whenever authentik is updated, it updates the outposts), and authentik can (in a future version) automatically rotate the token that the outpost uses to communicate with the core authentik server.

This integration creates the following objects:

- Deployment for the outpost container
- Service
- Secret to store the token
- Prometheus ServiceMonitor (if the Prometheus Operator is installed in the target cluster)
- Ingress (only Proxy outposts)
- HTTPRoute (only Proxy outposts, when the Gateway API resources are installed in the target cluster, and the `kubernetes_httproute_parent_refs` setting is set, see below)
- Traefik Middleware (only Proxy outposts with forward auth enabled)

The following outpost settings are used:

- `object_naming_template`: Configures how the container is called
- `container_image`: Optionally overwrites the standard container image (see [Configuration](../../../install-config/configuration/configuration.mdx) to configure the global default)
- `kubernetes_replicas`: Replica count for the deployment of the outpost
- `kubernetes_namespace`: Namespace to deploy in, defaults to the same namespace authentik is deployed in (if available)
- `kubernetes_ingress_annotations`: Any additional annotations to add to the ingress object, for example cert-manager
- `kubernetes_ingress_secret_name`: Name of the secret that is used for TLS connections, can be empty to disable TLS config
- `kubernetes_ingress_class_name`: Optionally set the ingress class used for the generated ingress, requires authentik 2022.11.0
- `kubernetes_httproute_parent_refs`: Define which Gateways the HTTPRoute wants to be attached to.
- `kubernetes_httproute_annotations`: Any additional annotations to add to the HTTPRoute object
- `kubernetes_service_type`: Service kind created, can be set to LoadBalancer for LDAP outposts for example
- `kubernetes_disabled_components`: Disable any components of the kubernetes integration, can be any of
    - 'secret'
    - 'deployment'
    - 'service'
    - 'prometheus servicemonitor'
    - 'ingress'
    - 'traefik middleware'
    - 'httproute'
- `kubernetes_image_pull_secrets`: If the above docker image is in a private repository, use these secrets to pull. (NOTE: The secret must be created manually in the namespace first.)
- `kubernetes_json_patches`: Applies an RFC 6902 compliant JSON patch to the Kubernetes objects.

## Permissions

The permissions required for this integration are documented in the helm chart. See [Cluster-level](https://github.com/goauthentik/helm/blob/main/charts/authentik-remote-cluster/templates/clusterrolebinding.yaml) and [Namespace-level](https://github.com/goauthentik/helm/blob/main/charts/authentik-remote-cluster/templates/rolebinding.yaml).

## Remote clusters

To add a remote cluster, you can simply install this helm chart in the target cluster and namespace: https://artifacthub.io/packages/helm/goauthentik/authentik-remote-cluster

After installation, the helm chart outputs an example kubeconfig file, that you can enter in authentik to connect to the cluster.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/flow/inspector.md
================================================================================

---
title: Flow Inspector
---

The flow inspector, introduced in 2021.10, allows administrators to visually determine how custom flows work, inspect the current [flow context](./context/index.mdx), and investigate issues.

As shown in the screenshot below, the flow inspector displays next to the selected flow (in this case, "Change Password"), with [information](#flow-inspector-details) about that specific flow and flow context.

![](./flow-inspector.png)

## Access the Flow Inspector

:::info
Be aware that when running a flow with the inspector enabled, the flow is still executed normally. This means that for example, a [User write](../stages/user_write.md) stage _will_ write user data.
:::

The inspector is accessible to users that have been granted the [permission](../../../users-sources/access-control/permissions.md) **Can inspect a Flow's execution**, either directly or through a role. Superusers can always inspect flow executions.

When developing authentik with the debug mode enabled, the inspector is enabled by default and can be accessed by both unauthenticated users and standard users. However, the debug mode should only be used for the development of authentik. So unless you are a developer and need the more verbose error information, the best practice for using the flow inspector is to assign the permission rather than use debug mode.

Starting with authentik 2025.2, for users with appropriate permissions to access the inspector, a button is shown in the top right of the [default flow executor](./executors/if-flow.md) which opens the flow inspector.

### Manually running a flow with the inspector

1. To access the inspector, open the Admin interface and navigate to **Flows and Stages > Flows**.

2. Select the specific flow that you want to inspect by clicking its name in the list.

3. On the Flow's detail page, on the left side under **Execute Flow**, click **with inspector**.

4. The selected flow will launch in a new browser tab, with the flow inspector displayed to the right.

Alternatively, a user with the correct permission can launch the inspector by adding the query parameter `?inspector` to the URL when the URL opens on a flow.

:::info
Troubleshooting:

- If the flow inspector does not launch and a "Bad request" error displays, this is likely either because you selected a flow that has a policy bound directly to it that prevents access (so the inspector won't open because the flow can't be executed) or because you do not have view permission on that specific flow.
  :::

### Flow Inspector Details

The following information is shown in the inspector:

#### Next stage

This is the currently planned next stage. If you have stage bindings configured to `Evaluate when flow is planned`\_`, then you will see the result here. If, however, you have them configured to re-evaluate (`Evaluate when stage is run`), then this will not show up here, since the results will vary based on your input.

The name and kind of the stage, as well as the unique ID, are shown.

#### Plan history

Here you can see an overview of which stages have run, which is currently active, and which is planned to come next. Same caveats as above apply.

#### Current plan context

This shows you the current context. This will contain fields depending on the same, after an identification stage for example you would see "pending_user" defined.

This data is not cleaned, so if your flow involves inputting a password, it will be shown here too.

#### Session ID

The unique ID for the currently used session. This can be used to debug issues with flows restarting/losing state.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/flow/index.md
================================================================================

---
title: Flows
---

Flows are a major component in authentik. In conjunction with stages and [policies](../../../customize/policies/index.md), flows are at the heart of our system of building blocks, used to define and execute the workflows of authentication, authorization, enrollment, and user settings.

There are over a dozen default, out-of-the-box flows available in authentik. Users can decide if they already have everything they need with the [default flows](../flow/examples/default_flows.md) or if they want to [create](#create-a-custom-flow) their own custom flow, using the Admin interface, Terraform, or via the API.

A flow is a method of describing a sequence of stages. A stage represents a single verification or logic step. By connecting a series of stages within a flow (and optionally attaching policies as needed) you can build a highly flexible process for authenticating users, enrolling them, and more.

For example a standard login flow would consist of the following stages:

- **Identification stage**: user identifies themselves via a username or email address
- **Password stage**: the user's password is checked against the hash in the database
- **Login stage**: this stage attaches a currently pending user to the current session

When these stages are successfully completed, authentik logs in the user.

![](./simple_stages.png)

By default, policies are evaluated dynamically, right before the stage (to which a policy is bound) is presented to the user. This flexibility allows the login process to continue, change, or stop, based on the success or failure of each policy.

This default behaviour can be altered by enabling the **Evaluate when flow is planned** option on the stage binding. With this setting a _flow plan_ containing all stages is generated upon flow execution. This means that all attached policies are evaluated upon execution. For more information about flow plans, read our [flow context documentation](./context/index.mdx).

## Policies and permissions

Flows can have [policies](../stages/index.md) assigned to them. These policies determine if the current user is allowed to see and use this flow.

Keep in mind that in certain circumstances, policies cannot match against users and groups as there is no authenticated user yet.

## Import or export a flow

Flows can be imported and exported (as [blueprints](../../../customize/blueprints/working_with_blueprints)) to share with other people, the community, and for troubleshooting.

Flows can be imported to add new functionality to existing flows, or to add a new custom flow.

You can download our [Example flows](./examples/flows.md) and then import them into your authentik instance, or create a new flow.

Starting with authentik 2022.8, flows are exported as YAML, but legacy JSON-based flows can still be imported.

:::warning Flow imports
Flow imports are blueprint files, which may contain objects other than flows (such as policies, users, groups, etc).

You should only import files from trusted sources and review blueprints before importing them.
:::

## Create a custom flow

To create a flow, follow these steps:

1. Log in to authentik as an administrator and open the Admin interface.
2. In the Admin interface, navigate to **Flows and Stages > Flows**.
3. Click **Create**, define the flow using the [configuration settings](#flow-configuration-options) described below, and then click **Finish**.

After creating the flow, you can then [bind specific stages](../stages/index.md#bind-a-stage-to-a-flow) to the flow and [bind policies](../../../customize/policies/working_with_policies.md) to the flow to further customize the user's log in and authentication process.

To determine which flow should be used, authentik will first check which default authentication flow is configured in the active [**Brand**](../../../sys-mgmt/brands/index.md). If no default is configured there, the policies in all flows with the matching designation are checked, and the first flow with matching policies sorted by `slug` will be used.

## Flow configuration options

When creating or editing a flow in the UI of the Admin interface, you can set the following configuration options.

![](./create-flow.png)

**Name**: Enter a descriptive name. This is the name that will appear on the list of flows in the Admin interface.

**Title**: This is the title that will appear on the flow as the end-user logs in and encounters the flow.

**Slug**: The slug will be used, and appear, in the URL when the flow is in use.

**Designation**: Flows are designated for a single purpose. This designation changes when a flow is used. The following designations are available:



**Authentication**: Using this option, you can configure whether the flow requires initial authentication or not, whether the user must be a superuser, if the flow can only be started after being redirected by a [Redirect stage](../stages/redirect/index.md), or if the flow requires an outpost.

**Behavior settings**:

- **Compatibility mode**: Toggle this option on to increase compatibility with password managers and mobile devices. Password managers like [1Password](https://1password.com/), for example, don't need this setting to be enabled when accessing the flow from a desktop browser. However, accessing the flow from a mobile device might necessitate this setting to be enabled.

    The technical reason for this setting's existence is the JavaScript libraries we're using for the default flow interface. These interfaces are implemented using [Lit](https://lit.dev/), which is a modern web development library. It uses a web standard called ["Shadow DOMs"](https://developer.mozilla.org/en-US/docs/Web/API/Web_components/Using_shadow_DOM), which makes encapsulating styles simpler. Due to differences in Browser APIs, many password managers are not compatible with this technology.

    When the compatibility mode is enabled, authentik uses a polyfill which emulates the Shadow DOM APIs without actually using the feature, and instead a traditional DOM is rendered. This increases support for password managers, especially on mobile devices.

- **Denied action**: Configure what happens when access to a flow is denied by a policy. By default, authentik will redirect to a `?next` parameter if set, and otherwise show an error message.
    - `MESSAGE_CONTINUE`: Show a message if no `?next` parameter is set, otherwise redirect.
    - `MESSAGE`: Always show error message.
    - `CONTINUE`: Always redirect, either to `?next` if set, otherwise to the default interface.

- **Policy engine mode**: Configure the flow to succeed in _any_ policy passes, or only if _all_ policies pass.

**Appearance Settings**:

- **Layout**: select how the UI displays the flow when it is executed; with stacked elements, content left or right, and sidebar left or right.

- **Background**: optionally, select a background image for the UI presentation of the flow. This overrides any default background image configured in the [Branding settings](../../../sys-mgmt/brands/index.md#branding-settings).

## Edit or delete a flow

- To edit a flow, navigate to **Flows and Stages > Flows** in the Admin interface, and then click **Edit** for the flow that you want to modify.

- To delete a flow, navigate to **Flows and Stages > Flows** in the Admin interface, select the checkbox in front of the flow that you want to delete, and then click **Delete**. You can retrieve and re-apply that flow by following the steps above to create a new flow.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/user_delete.md
================================================================================

---
title: User Delete stage
---

:::danger
This stage deletes the `pending_user` without any confirmation. You have to make sure the user is aware of this.
:::

The User Delete stage is intended for an unenrollment flow. It deletes the currently pending user.

The pending user is also removed from the current session.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/deny.md
================================================================================

---
title: Deny stage
---

This stage stops the execution of a flow. This can be used to conditionally deny users access to a flow,
even if they are not signed in (and permissions can't be checked via groups).

:::caution
To effectively use this stage, make sure _Evaluate when flow is planned_ is **disable** on the Stage binding.
:::



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/user_write.md
================================================================================

---
title: User Write stage
---

The User Write stage writes data from the current flow context to a user.

Newly created users can be created as inactive and can be assigned to a selected group.

### Dynamic groups

To add users to dynamic groups, set `groups` in the flow plan context before this stage is run. For example:

```python
from authentik.core.models import Group
group, _ = Group.objects.get_or_create(name="some-group")
# ["groups"] *must* be set to an array of Group objects, names alone are not enough.
request.context["flow_plan"].context["groups"] = [group]
return True
```

### User creation

By default, this stage will create a new user when none is present in the flow context.

To prevent users from creating new accounts without authorization, you can configure the User Write stage to not automatically create new users.

Alternatively, you can configure the stage to explicitly allow user creation, forbid it, or force user creation.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/user_logout.md
================================================================================

---
title: User Logout stage
---

The User Logout stage ends the user's session in authentik and, if configured, triggers [Single Logout (SLO)](../../providers/single-logout/index.md) for [SAML](../../providers/saml/saml_single_logout.md) and [OIDC](../../providers/oauth2/frontchannel_and_backchannel_logout.mdx) providers.

## When the User Logout stage is used

The User Logout stage is included in different default flows depending on how the logout is initiated:

- **`default-invalidation-flow`**: Used when a user logs out directly from authentik. This flow **includes** the User Logout stage, so the authentik session is ended and Single Logout is triggered for all connected applications.

- **`default-provider-invalidation-flow`**: Used when a user logs out from an application. This flow does **not** include the User Logout stage by default, so only that application's session is ended. The authentik session and other application sessions remain active.

This distinction exists because a user may want to sign out of a single application without ending their entire authentik session. To also end the authentik session when a user logs out from an application, you can add the User Logout stage to the `default-provider-invalidation-flow`. See [Enable full Single Logout for RP-initiated logout](../../providers/single-logout/index.md#enable-full-single-logout-for-rp-initiated-logout) for instructions.

## Logout flow injection

authentik dynamically injects logout stages into the user's current logout flow when provider sessions configured for Single Logout are detected:

1. The `flow_pre_user_logout` signal is triggered before the user is logged out
2. authentik queries for active provider sessions matching the user's authenticated session:
    - **SAML providers**: Queries active SAML sessions for providers with an SLS URL and logout method configured
    - **OIDC providers**: Queries for providers with front-channel or back-channel logout enabled
3. For each logout method with active sessions, the appropriate logout stage is injected:
    - **iframe logout stage**: Injected at index 1 (immediately after the logout stage) for front-channel iframe logout
    - **Native logout stage**: Injected at index 2 (after the iframe logout, if present) for front-channel native logout
    - **Back-channel logout**: Executed server-side without injecting additional stages
4. The user progresses through these injected stages before logout completes

This approach ensures that single logout happens automatically without requiring explicit flow configuration.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/index.md
================================================================================

---
title: Stages
---

Stages are one of the fundamental building blocks in authentik, along with [flows](../flow/index.md) and [policies](../../../customize/policies/index.md).

A stage represents a single verification or logic step within a flow. You can bind one or more stages to a flow to create a customized, flexible login and authentication process.

In the following diagram of the `default-authentication-flow`, you see multiple stages, or steps, in the authentication process for a user. Policies are bound to some stages; this provides for dynamic application of a specific stage _if_ the policy criteria is met.

```mermaid
graph TD
flow_pre[["Pre-flow policies"]]
flow_pre --Binding 10--> flow_policy_0{{"Policy (Event Matcher Policy)
default-match-update"}}
flow_policy_0 --Policy denied--> done[["End of the flow"]]
flow_policy_0 --> flow_start[["Flow
Welcome to authentik!"]]
stage_0_policy_0 --Policy passed--> stage_0(["Stage (Identification Stage)
default-authentication-identification"])
stage_1_policy_0 --Policy passed--> stage_1(["Stage (Password Stage)
default-authentication-password"])
--> stage_2(["Stage (Authenticator Validation Stage)
default-authentication-mfa-validation"])
--> stage_3(["Stage (User Login Stage)
default-authentication-login"])
flow_start --> stage_0_policy_0{{"Policy (Event Matcher Policy)
default-match-configuration-error"}}
stage_0 --> stage_1_policy_0{{"Policy (Expression Policy)
default-authentication-flow-password-stage"}}
stage_0_policy_0 --Policy denied--> stage_1(["Stage (Password Stage)
default-authentication-password"])
stage_1_policy_0 --Policy denied--> stage_2(["Stage (Authenticator Validation Stage)
default-authentication-mfa-validation"])
stage_3 --> done[["End of the flow"]]
```

## Create a Stage

To create a stage, follow these steps:

1. Log in as an admin to authentik, and go to the Admin interface.
2. In the Admin interface, navigate to **Flows and Stages > Stages**.
3. Click **Create**, define the stage using the configuration settings, and then click **Finish**.

After creating the stage, you can then use bindings to determine whether or not the stage will be implemented in the flow.

## Stage bindings

A _stage binding_ connects a stage to a flow. The "additional content" (i.e. the content in the stage) is now added to the flow.

You can use a binding to determine which exact [stages](../stages/index.md) (all of the _steps_ within a flow) are presented to a user (or a group).

For an overview about all the different types of bindings in authentik and how they are used, refer to [About authentik bindings](../../bindings-overview/index.md).

:::info
Be aware that some stages and flows do not allow user or group bindings, because in certain scenarios (authentication or enrollment), the flow plan doesn't yet know who the user or group is.
:::

### Bind a stage to a flow

To bind a stage to a flow (which adds the stage as a "step" in the flow), follow these steps:

1. Log in as an admin to authentik, and go to the Admin interface.
2. In the Admin interface, navigate to **Flows and Stages > Flows**.
3. In the list of flows, click the name of the flow to which you want to bind one or more stages.
4. On the Flow page, click the **Stage Bindings** tab at the top.
5. Here, you can decide if you want to create a new stage and bind it to the flow (**Create and bind Stage**), or if you want to select an existing stage and bind it to the flow (**Bind existing stage**).

### Control access to a stage

There are several ways use policy bindings to control access to a specific stage of a flow: - Bind a policy to a stage-binding. [See our policy documentation](../../../customize/policies/working_with_policies.md#bind-a-policy-to-a-stage-binding). - Bind a user or group to the stage. [See steps below](#bind-users-and-groups-to-a-flows-stage-binding).

### Bind users and groups to a flow's stage binding

You can use bindings to determine whether or not a stage is presented to a single user or any users within a group. You do this by binding the user or group to a stage binding within a specific flow. For example, if you have a flow that contains a stage that prompts the user for multi-factor authentication, but you only want certain users to see this stage (and fulfill the MFA prompt), then you would bind the appropriate group (or single user) to the stage binding for that flow.

To bind a user or a group to a stage binding for a specific flow, follow these steps:

1. Log in as an admin to authentik, and go to the Admin interface.
2. In the Admin interface, navigate to **Flows and Stages > Flows**.
3. In the list of flows, click the name of the flow to which you want to bind one or more stages.
4. On the Flow page, click the **Stage Bindings** tab at the top.
5. Locate the stage binding to which you want to bind a user or group, and then **click the caret (>) to expand the stage binding details.**

![](./edit_stage_binding.png)

6. In the expanded area, click **Bind existing policy/group/user**.
7. In the **Create Binding** box, select either the tab for **Group** or **User**.
8. In the drop-down list, select the group or user.
9. Optionally, configure additional settings for the binding, and then click **Create** to create the binding and close the box.

Learn more about the different types of [bindings](../../bindings-overview/index.md) in authentik and [working with them](../../bindings-overview/work-with-bindings.md).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/flow/executors/if-flow.md
================================================================================

---
title: Default
---

This is the default, web-based environment that flows are executed in. All stages are compatible with this environment and no limitations are imposed.

:::info
All flow executors use the same [API](/api/flow-executor/), which allows for the implementation of custom flow executors.
:::

## Layouts

Starting with authentik 2022.5, the layout of the default flow executor can be changed. Below are examples for the available options:

### Stacked (default)

![](../layouts/stacked.png)

### Content besides logo (left)

![](../layouts/content_left.png)

### Content besides logo (right)

![](../layouts/content_right.png)

### Sidebar (left)

![](../layouts/sidebar_left.png)

### Sidebar (right)

![](../layouts/sidebar_right.png)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/flow/executors/user-settings.md
================================================================================

---
title: User settings
---

The user interface (/if/user/) uses a specialized flow executor to allow individual users to customize their profile. A user's profile consists of key/value fields, so this executor only supports Prompt or User Write stages. If the configured flow contains another stage, a button will be shown to open the default executor.

Because the stages in a flow can change during its execution, be aware that configuring this executor to use any stage type other than Prompt or User Write will automatically trigger a redirect to the standard executor.

An admin can customize which fields can be changed by the user by updating the default-user-settings-flow, or copying it to create a new flow with a Prompt Stage and a User Write Stage. Different variants of your flow can be applied to different [Brands](../../../../sys-mgmt/brands/index.md) on the same authentik instance.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/flow/executors/sfe.md
================================================================================

---
title: Simplified flow executor
authentik_version: "2024.6.1"
---

A simplified web-based flow executor that authentik automatically uses for older browsers that do not support modern web technologies.

Currently this flow executor is automatically used for the following browsers:

- Internet Explorer
- Microsoft Edge (up to and including version 18)

The following stages are supported:

- [**Identification stage**](../../stages/identification/index.mdx)

    :::info
    Only user identifier and user identifier + password stage configurations are supported; sources and passwordless configurations are not supported.
    :::

- [**Password stage**](../../stages/password/index.md)
- [**Authenticator Validation Stage**](../../stages/authenticator_validate/index.mdx)

Compared to the [default flow executor](./if-flow.md), this flow executor does _not_ support the following features:

- Localization
- Theming (Dark / light themes)
- Theming (Custom CSS)
- Stages not listed above
- Flow inspector



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/flow/executors/headless.md
================================================================================

---
title: Headless
---

The headless flow executor is used by clients that don't have access to the web interface. It is currently used by the LDAP and Radius outposts to authenticate users.

The following stages are supported:

- [**Identification stage**](../../stages/identification/index.mdx)
- [**Password stage**](../../stages/password/index.md)
- [**Authenticator Validation Stage**](../../stages/authenticator_validate/index.mdx)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/flow/flow_list/_defaultflowlist.mdx
================================================================================

- **Authentication**: this option designates a flow to be used for authentication. The authentication flow should always contain a [**User Login**](../../stages/user_login/index.md) stage, which attaches the staged user to the current session.

- **Authorization**: designates a flow to be used for authorization of an application. Can be used to add additional verification steps before the user is allowed to access an application. This flow is defined per provider, when the provider is created, to state whether implicit or explicit authorization is required.

- **Enrollment**: designates a flow for enrollment. This flow can contain any amount of verification stages, such as [**Email**](../../stages/email/index.mdx) or **Captcha**. At the end, to create the user, you can use the [**User Write**](../../stages/user_write.md) stage, which either updates the currently staged user, or if none exists, creates a new one.

- **Invalidation**: designates a default flow to be used to invalidate a session. There are two default invalidation flows:
    - `default-invalidation-flow`: Used when a user logs out directly from authentik. This flow **includes** a [**User Logout**](../../stages/user_logout.md) stage, which ends the authentik session and triggers [Single Logout](../../../providers/single-logout/index.md) for all connected applications.

    - `default-provider-invalidation-flow`: Used when a user logs out from an application (OIDC, SAML, Proxy, or RAC providers). By default, this flow does **not** include a User Logout stage, meaning only the specific application session ends while the authentik session remains active. For instructions on how to also end the authentik session when a user logs out from an application, see the [Single Logout documentation](../../../providers/single-logout/index.md#enable-full-single-logout-for-rp-initiated-logout).

    You can also create custom invalidation flows with branded background images or different logout options.

- **Recovery**: designates a flow for recovery. This flow normally contains an [**Identification**](../../stages/identification/index.mdx) stage to find the user. It can also contain any amount of verification stages, such as [**Email**](../../stages/email/index.mdx) or [**CAPTCHA**](../../stages/captcha/index.md). Afterwards, use the [**Prompt**](../../stages/prompt/index.md) stage to ask the user for a new password and the [**User Write**](../../stages/user_write.md) stage to update the password.

- **Stage configuration**: designates a flow for general setup. This designation doesn't impose any constraints on what you can do. For example, by default this designation is used to configure authenticators, like changing a password and setting up TOTP.

- **Unenrollment**: designates a flow for unenrollment. This flow can contain any amount of verification stages, such as [**email**](../../stages/email/index.mdx) or [**Captcha**](../../stages/captcha/index.md). As a final stage, to delete the account, use the [**user_delete**](../../stages/user_delete.md) stage.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/flow/examples/default_flows.md
================================================================================

---
title: Default flows
---

When you create a new provider, you can select certain default flows that will be used with the provider and its associated application. For example, you can [create a custom flow](../index.md#create-a-custom-flow) that overrides the defaults configured on the brand.

If no default flow is selected when the provider is created, authentik will first check if there is a default flow configured in the active [**Brand**](../../../../sys-mgmt/brands/index.md). If no default is configured there, authentik will go through all flows with the matching designation, sorted by `slug`, evaluate policies bound directly to the flows, and pick the first flow whose policies allow access.





================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/flow/examples/flows.md
================================================================================

---
title: Example flows
---

:::info
You can apply these flows multiple times to stay updated, however this will discard all changes you've made.
:::

:::info
The example flows provided below will **override** the default flows, please review the contents of the example flow before importing and consider exporting the affected existing flows first.
:::

## Enrollment (2 Stage)

Flow: right-click [here](/blueprints/example/flows-enrollment-2-stage.yaml) and save the file.

Sign-up flow for new users, which prompts them for their username, email, password and name. No verification is done. Users are also immediately logged on after this flow.

## Enrollment with email verification

Flow: right-click [here](/blueprints/example/flows-enrollment-email-verification.yaml) and save the file.

Same flow as above, with an extra email verification stage.

You'll probably have to adjust the Email stage and set your connection details.

## Two-factor Login

Flow: right-click [here](/blueprints/example/flows-login-2fa.yaml) and save the file.

Login flow which follows the default pattern (username/email, then password), but also checks for the user's OTP token, if they have one configured.

You can force two-factor authentication by editing the _Not configured action_ in the Authenticator Validation Stage.

## Login with conditional Captcha

Flow: right-click [here](/blueprints/example/flows-login-conditional-captcha.yaml) and save the file.

Login flow which conditionally shows the users a captcha, based on the reputation of their IP and Username.

By default, the captcha test keys are used. You can get a proper key [here](https://www.google.com/recaptcha/intro/v3.html).

## Recovery with email verification

Flow: right-click [here](/blueprints/example/flows-recovery-email-verification.yaml) and save the file.

Recovery flow, the user is sent an email after they've identified themselves. After they click on the link in the email, they are prompted for a new password and immediately logged on.

## User deletion

Flow: right-click [here](/blueprints/example/flows-unenrollment.yaml) and save the file.

Flow for users to delete their account.

:::warning
This is done without any warning.
:::



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/flow/examples/snippets.mdx
================================================================================

---
title: Example policy snippets for flows
---

### Redirect current flow to another URL

```python
plan = request.context.get("flow_plan")
if not plan:
    return False
plan.redirect("https://foo.bar")
return False
```

This policy should be bound to the stage after your redirect should happen. For example, if you have an identification and a password stage, and you want to redirect after identification, bind the policy to the password stage. Make sure the stage binding's option _Evaluate when stage is run_ is enabled.

### Deny flow when user is authenticated

```python
return not request.user.is_authenticated
```

When used with authentik 2022.7 or later, set the flow _Denied action_ to _CONTINUE_. This will redirect already authenticated users to the default interface if they try to use the respective flow.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/flow/context/index.mdx
================================================================================

---
title: Flow Context
toc_max_heading_level: 5
---

Each flow execution has an independent _context_. This context holds all of the arbitrary data about that specific flow, data which can then be used and transformed by stages and policies.

## Managing data in a flow context

You create and manage the data for a context by configuring policies, stages, and bindings. As you plan your flow, and set up the required stages, etc. you are creating the context data for that flow.

For example, in the Identification Stage (part of the default login flow), you can define whether users will be prompted to enter an email address, a username, or both. All such information about the flow's configuration makes up the context.

Any data can be stored in the flow context, however there are some reserved keys in the context dictionary that are used by authentik stages.

To manage flow context on a more granular level, see [Setting flow context keys](../../../../customize/policies/expression/managing_flow_context_keys.md).

## Context dictionary and reserved keys

This section describes the data (the context) that are used in authentik, and provides a list of keys, what they are used for and when they are set.

:::warning
Keys prefixed with `goauthentik.io` are used internally by authentik and are subject to change without notice, and should not be modified in policies in most cases.
:::

{/* To update this file, search for `PLAN_CONTEXT_\w+\s=` in the workspace to find all definitions. */}

### Common keys

#### `pending_user` ([User object](../../../../users-sources/user/user_ref.mdx#object-properties))

`pending_user` is used by multiple stages. In the context of most flow executions, it represents the data of the user that is executing the flow. This value is not set automatically, it is set via the [Identification stage](../../stages/identification/index.mdx).

Stages that require a user, such as the [Password stage](../../stages/password/index.md), the [Authenticator validation stage](../../stages/authenticator_validate/index.mdx), and others will use this value if it is set, and fall back to the request's user when possible.

#### `prompt_data` (Dictionary)

`prompt_data` is primarily used by the [Prompt stage](../../stages/prompt/index.md). The value of any field within a prompt stage is written to the `prompt_data` dictionary. For example, given a field with the _Field key_ `email` that was submitted with the value `foo@bar.baz` will result in the following context:

```json
{
    "prompt_data": {
        "email": "foo@bar.baz"
    }
}
```

This data can be modified with policies. The data is also used by stages like [User write](../../stages/user_write.md), which takes data in `prompt_data` and writes it to `pending_user`.

#### `redirect` (string)

Stores the final redirect URL that the user's browser will be sent to after the flow is finished executing successfully. This is set when an un-authenticated user attempts to access a secured application, and when a user authenticates/enrolls with an external source.

#### `pending_user_identifier` (string)

If _Show matched user_ is disabled, this key will hold the user identifier entered by the user in the identification stage.

#### `application` (Application object)

When an unauthenticated user attempts to access a secured resource, they are redirected to an authentication flow. The application they attempted to access will be stored in the key attached to this object. For example: `application.github`, with `application` being the key and `github` the value.

#### `source` (Source object)

When a user authenticates/enrolls via an external source, this will be set to the source they are using.

#### `outpost` (dictionary)

When a flow is executed by an Outpost (for example the [LDAP](../../../providers/ldap/index.md) or [RADIUS](../../../providers/radius/index.mdx)), this will be set to a dictionary containing the Outpost instance under the key `"instance"`.

### Scenario-specific keys

#### `is_sso` (boolean)

This key is set to `True` when the flow is executed from an "SSO" context. For example, this is set when a flow is used during the authentication or enrollment via an external source, and if a flow is executed to authorize access to an application.

#### `is_restored` (Token object)

This key is set when a flow execution is continued from a token. This happens for example when an [Email stage](../../stages/email/index.mdx) is used and the user clicks on the link within the email. The token object contains the key that was used to restore the flow execution. This field is also used by the [Source stage](../../stages/source/index.md) when returning back to the initial flow the Source stage was run on.

#### `is_redirected` (Flow object)

This key is set when the current flow was reached through a [Redirect stage](../../stages/redirect/index.md) in Flow mode.

### Stage-specific keys

#### Autosubmit stage

The autosubmit stage is an internal stage type that is not configurable via the API/Web interface. It is used in certain situations, where a POST request is sent from the browser, such as with SAML POST bindings. This works by using an HTML form that is submitted automatically.

##### `title` (string)

Optional title of the form shown to the user. Automatically set when this stage is used by the backend.

##### `url` (string)

URL that the form will be submitted to.

##### `attrs` (dictionary)

Key-value pairs of the data that is included in the form and will be submitted to `url`.

#### Captcha stage:ak-version

##### `captcha` (dictionary)

When _Error on invalid score_ is set to false on a captcha stage, after the execution of the captcha stage, this object will be set in the flow context.

It contains two keys, `response` which is the raw response from the specified captcha verification URL, and `stage`, which is a reference to the captcha stage that executed the test.

#### `goauthentik.io/stages/captcha/site_key` (string):ak-version[2025.12]

#### `goauthentik.io/stages/captcha/private_key` (string):ak-version[2025.12]

Optionally set captcha site and private keys dynamically through a policy, for example when using E2E testing with a captcha stage bound.

#### Consent stage

##### `consent_header` (string)

The title of the consent prompt shown. Set automatically when the consent stage is used with a OAuth2, Proxy or SAML provider.

##### `consent_permissions` (List of PermissionDict)

An optional list of all permissions that will be given to the application by granting consent. Not supported with SAML. When used with an OAuth2 or Proxy provider, this will be set based on the configured scopes.

#### Deny stage

##### `deny_message` (string)

Optionally overwrite the deny message shown, has a higher priority than the message configured in the stage.

#### User write stage

##### `groups` (List of [Group objects](../../../../users-sources/groups/index.mdx))

See [Group](../../../../users-sources/groups/index.mdx). If set in the flow context, the `pending_user` will be added to all the groups in this list.

If set, this must be a list of group objects and not group names.

##### `user_path` (string)

Path the `pending_user` will be written to. If not set in the flow, falls back to the value set in the user_write stage, and otherwise to the `users` path.

##### `user_type` (string)

Type the `pending_user` will be created as. Must be one of `internal`, `external` or `service_account`.

#### Password stage

##### `user_backend` (string)

Set by the [Password stage](../../stages/password/index.md) after successfully authenticating the user. Contains a dot-notation to the authentication backend that was used to successfully authenticate the user.

##### `auth_method` (string)

Set by the [Password stage](../../stages/password/index.md), the [Authenticator validation stage](../../stages/authenticator_validate/index.mdx), the [OAuth2 Provider](../../../providers/oauth2/index.mdx), and the API authentication depending on which method was used to authenticate.

Possible options:

- `password` (Authenticated via the password in authentik's database)
- `token` (Authenticated via API token)
- `ldap` (Authenticated via LDAP bind from an LDAP source)
- `auth_mfa` (Authentication via MFA device without password)
- `auth_webauthn_pwl` (Passwordless authentication via WebAuthn with Passkeys)
- `jwt` ([M2M](../../../providers/oauth2/machine_to_machine.mdx) authentication via an existing JWT)
- `mtls` (Authentication via Certificate, see [Mutual TLS Stage](../../stages/mtls/index.md))

##### `auth_method_args` (dictionary)

Additional arguments used during the authentication. Value varies depending on `auth_method`.

Example:

```json
{
    // List of the MFA device objects used during authentication
    // applies for `auth_method` `auth_mfa`
    "mfa_devices": [],
    // MFA device used for passwordless authentication, applies to
    // `auth_method` `auth_webauthn_pwl`
    "device": null,
    // the token identifier when `auth_method` `token` was used
    "identifier": "",
    // JWT information when `auth_method` `jwt` was used
    "jwt": {},
    "source": null,
    "provider": null,
    // Certificate used for authentication
    // applies for `auth_method` `mtls`
    "certificate": {}
}
```

#### Email stage

##### `email_sent` (boolean)

Boolean set to true after the email form the email stage has been sent.

##### `email` (string)

Optionally override the email address that the email will be sent to. If not set, defaults to the email of `pending_user`.

#### Identification stage

##### `pending_user_identifier` (string)

If _Show matched user_ is disabled, this key will be set to the user identifier entered by the user in the identification stage.

#### Invitation stage

##### `invitation` (Invitation object)

The invitation used with the invitation stage. When **Continue flow without invitation** is enabled, this may be unset.

If the invitation was single-use, this object may hold a reference to an invitation that no longer exists in the database.

##### `invitation_in_effect` (boolean)

A boolean value that is `True` when an invitation has been used.

##### `token` (string)

This value can be set either via [Prompt data](#prompt_data-dictionary) or via policy to interactively/programmatically choose an invitation.

#### Redirect stage

##### `redirect_stage_target` (string)

[Set this key](../../../../customize/policies/expression/managing_flow_context_keys.md) in an Expression Policy to override [Redirect stage](../../stages/redirect/index.md) to force it to redirect to a certain URL or flow. This is useful when a flow requires that the redirection target be decided dynamically.

Use the format `ak-flow://{slug}` to use the Redirect stage in Flow mode. Any other format will result in the Redirect stage running in Static mode.

#### Mutual TLS Stage

##### `certificate` (dictionary):ak-version[2025.6]

This key is set by the Mutual TLS Stage during enrollment and contains data about the certificate supplied by the browser.

Example:

```json
{
    "serial_number": "1234",
    "subject": "CN=client",
    "issuer": "CN=authentik Test CA, O=authentik, OU=Self-signed",
    "fingerprint_sha256": "08:D4:A4:79:25:CA:C3:51:28:88:BB:30:C2:96:C3:44:5A:EB:18:07:84:CA:B4:75:27:74:61:19:8A:6A:AF:FC",
    "fingerprint_sha1": "5D:14:0D:5F:A2:7E:14:B0:F1:1D:6F:CD:E3:4B:81:68:71:24:1A:70",
    "raw": "-----BEGIN CERTIFICATE-----...."
}
```



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/password/index.md
================================================================================

---
title: Password stage
---

This is a generic password prompt which authenticates the current `pending_user`. This stage allows the selection of the source the user is authenticated against.

## Passwordless login

There are two different ways to configure passwordless authentication; you can follow the instructions [here](../authenticator_validate/index.mdx#passwordless-authentication) to allow users to directly authenticate with their authenticator (only supported for WebAuthn devices), or dynamically skip the password stage depending on the user's device, which is documented here.

If you want users to be able to pick a passkey from the browser's passkey/autofill UI without entering a username first, configure **Passkey autofill (WebAuthn conditional UI)** in the [Identification stage](../identification/index.mdx#passkey-autofill-webauthn-conditional-ui). This is separate from configuring a dedicated passwordless flow, and can be used alongside normal identification flows.

Depending on what kind of device you want to require the user to have:

#### WebAuthn

```python
from authentik.stages.authenticator_webauthn.models import WebAuthnDevice
return WebAuthnDevice.objects.filter(user=request.context['pending_user'], confirmed=True).exists()
```

#### Duo

```python
from authentik.stages.authenticator_duo.models import DuoDevice
return DuoDevice.objects.filter(user=request.context['pending_user'], confirmed=True).exists()
```

Afterwards, bind the policy you've created to the stage binding of the password stage.

Make sure to uncheck _Evaluate when flow is planned_ and check _Evaluate when stage is run_, otherwise an invalid result will be cached.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/redirect/index.md
================================================================================

---
title: Redirect stage
authentik_version: "2024.12"
---

This stage's main purpose is to redirect the user to a new Flow while keeping flow context. For convenience, it can also redirect the user to a static URL.

The redirection target can also be overwritten dynamically in an expression policy by setting the [redirect_stage_target](../../flow/context/#redirect_stage_target-string) key in the flow context.

## Redirect stage modes

### Static mode

When the user reaches this stage, they are redirected to a static URL.

### Flow mode

When the user reaches this stage, they are redirected to a specified flow, retaining all [flow context](../../flow/context/index.mdx).

Optionally, toggle the "Keep flow context" switch to "off". When this control is set to "off", all flow context is cleared with the exception of the [is_redirected](../../flow/context#is_redirected-flow-object) key.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/authenticator_static/index.md
================================================================================

---
title: Static Authenticator Setup stage
---

This stage configures static Tokens, which can be used as a backup method to time-based OTP tokens.

You can configure how many tokens are shown to the user.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/prompt/index.md
================================================================================

---
title: Prompt stage
---

This stage is used to show the user arbitrary prompts.

## Prompt

The prompt can be any of the following types:

| Type                  | Description                                                                                |
| --------------------- | ------------------------------------------------------------------------------------------ |
| Text                  | Arbitrary text. No client-side validation is done.                                         |
| Text (Read only)      | Same as above, but cannot be edited.                                                       |
| Text Area             | Arbitrary multiline text. No client-side validation is done.                               |
| Text Area (Read only) | Same as above, but cannot be edited.                                                       |
| Username              | Same as text, except the username is validated to be unique.                               |
| Email                 | Text input, ensures the value is an email address (validation is only done client-side).   |
| Password              | Same as text, shown as a password field client-side, and custom validation (see below).    |
| Number                | Numerical textbox.                                                                         |
| Checkbox              | Simple checkbox.                                                                           |
| Radio Button Group    | Similar to checkboxes, but allows selecting a value from a set of predefined values.       |
| Dropdown              | A simple dropdown menu filled with predefined values.                                      |
| Date                  | Same as text, except the client renders a date-picker                                      |
| Date-time             | Same as text, except the client renders a date-time-picker                                 |
| File                  | Allow users to upload a file, which will be available as base64-encoded data in the flow . |
| Separator             | Passive element to group surrounding elements                                              |
| Hidden                | Hidden input field. Allows for the pre-setting of default values.                          |
| Static                | Display arbitrary value as is                                                              |
| authentik: Locale     | Display a list of all locales authentik supports.                                          |

:::info
`TextArea`, `TextArea (Read only)`, `Radio Button Group` and `Dropdown` options require authentik 2023.4+
:::

Some types have special behaviors:

- _Username_: Input is validated against other usernames to ensure a unique value is provided.
- _Password_: All prompts with the type password within the same stage are compared and must be equal. If they are not equal, an error is shown
- _Hidden_ and _Static_: Their initial values are defaults and are not user-changeable.
- _Radio Button Group_ and _Dropdown_: Only allow the user to select one of a set of predefined values.

A prompt has the following attributes:

### `field_key`

The field name used for the prompt. This key is also used to later retrieve the data in expression policies:

```python
request.context.get('prompt_data').get('<field_key>')
```

### `label`

The label used to describe the field. Depending on the selected template, this may not be shown.

### `required`

A flag which decides whether or not this field is required.

### `placeholder`

A field placeholder, shown within the input field.

By default, the placeholder is interpreted as-is. If you enable _Interpret placeholder as expression_, the placeholder
will be evaluated as a Python expression. This happens in the same environment as [_Policies_](../../../../customize/policies/expression.mdx).

For `Radio Button Group` and `Dropdown` prompts, this field defines the available choices. When used as a plain string, it represents a single allowed value (the placeholder). When used as an expression, it can return a list of choices. For example, `return ["first option", 42, {"label": "another option", "value": "some value"}]` defines three possible values.

A choice can be a string (or any primitive that will be converted to a string) or an object with `value` and/or `label` properties. For example, `return ["Option 1"]` is equivalent to `return [{"label": "Option 1", "value": "Option 1"}]`.

You can access both the HTTP request and the user as with a mapping. Additionally, you can access `prompt_context`, which is a dictionary of the current state of the prompt stage's data.

For `Radio Button Group` and `Dropdown` prompts, if a key with the same name as the prompt's `field_key` and a suffix of `__choices` (`<field_key>__choices`) is present in the `prompt_context` dictionary, its value will be returned directly, even if _Interpret placeholder as expression_ is enabled.

### `initial_value`

The prompt's initial value. It can also be left empty, in which case the field will not have a pre-filled value.

With the `hidden` prompt, the initial value will also be the actual value, because the field is hidden to the user.

By default, the initial value is interpreted as-is. If you enable _Interpret initial value as expression_, the initial value
will be evaluated as a Python expression. This happens in the same environment as [_Policies_](../../../../customize/policies/expression.mdx).

In the case of `Radio Button Group` and `Dropdown` prompts, this field defines the default choice. When interpreted as-is, the default choice will be the initial value string. When interpreted as expression, the default choice will be the returned value. For example, `return 42` defines `42` as the default choice. When a choice is defined as an object `{"label": "Option", "value": "internal-value"}`, the initial value needs to be set to the value string `internal-value` in this case.

:::info
The default choice defined for any fixed choice field **must** be one of the valid choices specified in the prompt's placeholder.
:::

You can access both the HTTP request and the user as with a mapping. Additionally, you can access `prompt_context`, which is a dictionary of the current state of the prompt stage's data. If a key with the same name as the prompt's `field_key` is present in the `prompt_context` dictionary, its value will be returned directly, even if _Interpret initial value as expression_ is enabled.

### `order`

The numerical index of the prompt. This applies to all stages which this prompt is a part of.

# Validation

Further validation of prompts can be done using policies.

To validate that two password fields are identical, create the following expression policy:

```python
if request.context.get('prompt_data').get('password') == request.context.get('prompt_data').get('password_repeat'):
    return True

ak_message("Passwords don't match.")
return False
```

This policy expects you to have two password fields with `field_key` set to `password` and `password_repeat`.

Afterwards, bind this policy to the prompt stage you want to validate.

Before 2021.12, any policy was required to pass for the result to be considered valid. This has been changed, and now all policies are required to be valid.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/authenticator_duo/index.mdx
================================================================================

---
title: Duo Authenticator Setup stage
---

This stage configures a Duo authenticator. To get the API Credentials for this stage, open your Duo Admin dashboard.

Go to Applications, click on Protect an Application and search for "Auth API". Click on Protect.

Copy all of the integration key, secret key and API hostname, and paste them in the Stage form.

Devices created reference the stage they were created with, since the API credentials are needed to authenticate. This also means when the stage is deleted, all devices are removed.

## Importing users

:::info
Due to the way the Duo API works, authentik can only automatically import existing Duo users when a Duo MFA or higher license is active.
:::

To import a device, open the Stages list in the authentik Admin interface. On the right next to the import button you'll see an import button, with which you can import Duo devices to authentik users.

The Duo username can be found by navigating to your Duo Admin dashboard and selecting _Users_ in the sidebar. Optionally if you have multiple users with the same username, you can click on a User and copy their ID from the URL, and use that to import the device.

### Older versions

You can call the `/api/v3/stages/authenticator/duo/{stage_uuid}/import_devices/` endpoint ([see here](https://goauthentik.io/api/#post-/stages/authenticator/duo/-stage_uuid-/import_devices/)) using the following parameters:

- `duo_user_id`: The Duo User's ID. This can be found in the Duo Admin Portal, navigating to the user list and clicking on a single user. Their ID is shown in th URL.
- `username`: The authentik user's username to assign the device to.

Additionally, you need to pass `stage_uuid` which is the `authenticator_duo` stage, in which you entered your API credentials.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/identification/index.mdx
================================================================================

---
title: Identification stage
---

This stage provides a ready-to-go form for users to identify themselves.

## User Fields

Select which fields the user can use to identify themselves. Multiple fields can be selected. If no fields are selected, only sources will be shown.

- Username
- Email
- UPN

    UPN will attempt to identify the user based on the `upn` attribute, which can be imported with an [LDAP Source](../../../../users-sources/sources/protocols/ldap/index.md)

## Password stage

To prompt users for their password on the same step as identifying themselves, a Password stage can be selected here. If a Password stage is selected in the Identification stage, the Password stage should not be bound to the flow.

## CAPTCHA stage

:::warning
The CAPTCHA stage you use must be configured to use the "Invisible" mode, otherwise the widget will be rendered incorrectly.
:::

To run a CAPTCHA process in the background while the user is entering their identification, a CAPTCHA stage can be selected here. If a CAPTCHA stage is selected in the Identification stage, the CAPTCHA stage should not be bound to the flow.

## Passkey autofill (WebAuthn conditional UI):ak-version[2025.12]

When configured, the Identification stage can offer passkey login directly from the browser's passkey/autofill UI (also known as "conditional UI"). This allows a user to select a passkey without first typing their username.

authentik will automatically fall back to the normal identification flow when passkey autofill is not available.

### Requirements

- **HTTPS** is required for WebAuthn (except on `localhost`).
- **Browser support** for WebAuthn conditional mediation is required.
- Users must have a compatible **discoverable credential (aka resident key)** (most passkeys created by platform authenticators and password managers are discoverable).
- **Correct domain**: users must access authentik using the same hostname the passkey was created for.

### Configuration

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Stages** and either create or edit an [Authenticator validation stage](../authenticator_validate/index.mdx) that allows the **WebAuthn** device class.
3. Navigate to **Flows and Stages** > **Stages** and edit your Identification stage. Under **Passkey settings** set **WebAuthn Authenticator Validation Stage** to the Authenticator validation stage from step 2.
4. Click **Update** to save the changes.
5. Ensure users have enrolled a passkey/WebAuthn device (for example using the [WebAuthn / FIDO2 / Passkeys Authenticator setup stage](../authenticator_webauthn/index.mdx)).

### Notes

- The passkey prompt is triggered by the browser when the user focuses the username field.
- If a user has multiple passkeys, the browser will show a picker.
- If passkey login is used, the flow context will have `auth_method` set to `auth_webauthn_pwl`.
- In the default authentication flow blueprint, authentik skips the MFA validation stage after passkey login using an expression policy. If you want passkey login to still require an additional factor, disable or adjust that policy binding on the MFA stage.

### Troubleshooting

- **No passkey prompt appears**
    - Ensure the Identification stage has **WebAuthn Authenticator Validation Stage** set.
    - Ensure you're using **HTTPS** (except on `localhost`).
    - Check browser support for conditional UI.
    - Ensure the login page is not embedded in an iframe as some browsers block conditional UI outside top-level browsing contexts.

- **Passkey prompt appears, but login falls back to username/password**
    - Ensure the referenced Authenticator validation stage allows the **WebAuthn** device class.
    - Ensure the user has a valid, confirmed WebAuthn device enrolled.

## Enrollment/Recovery Flow

These fields specify if and which flows are linked on the form. The enrollment flow is linked as `Need an account? Sign up.`, and the recovery flow is linked as `Forgot username or password?`.

## Pretend user exists

When enabled, any user identifier will be accepted as valid (as long as they match the correct format, i.e. when [User fields](#user-fields) is set to only allow Emails, then the identifier still needs to be an Email). The stage will succeed and the flow will continue to the next stage. Stages like the [Password stage](../password/index.md) and [Email stage](../email/index.mdx) are aware of this "pretend" user and will behave the same as if the user would exist.

## Enable "Remember me on this device":ak-version[2025.4]

When enabled, users will be given the option at login of having their username stored on the device. If selected, on future logins this stage will automatically fill in the username and fast-forward to the password field. Users will still have the options of clicking "Not you?" and going back to provide a different username or disable this feature.

## Source settings

Some sources (like the [OAuth Source](../../../../users-sources/sources/protocols/oauth/index.mdx) and [SAML Source](../../../../users-sources/sources/protocols/saml/index.md)) require user interaction. To make these sources available to users, they can be selected in the Identification stage settings, which will show them below the selected [user field](#user-fields).

By default, sources are only shown with their icon, which can be changed with the _Show sources' labels_ option.

Furthermore, it is also possible to deselect any [user field option](#user-fields) for an Identification stage, which will result in users only being able to use currently configured sources.

:::info
Starting with authentik 2023.5, when no user fields are selected and only one source is selected, authentik will automatically redirect the user to that source. This only applies when the **Passwordless flow** option is _not_ configured.
:::

## Flow settings

### Passwordless flow

See [Passwordless authentication](../authenticator_validate/index.mdx#passwordless-authentication).

### Enrollment flow

Optionally can be set to a flow with the designation of _Enrollment_, which will allow users to sign up.

### Recovery flow

Optionally can be set to a flow with the designation of _Recovery_, which will allow users to recover their credentials.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/authenticator_email/index.md
================================================================================

---
title: Email Authenticator Setup stage
authentik_version: "2025.2"
---

This stage configures an email-based authenticator that sends a one-time code to a user's email address for authentication.

When a user goes through a flow that includes this stage, they are prompted for their email address (if not already set). The user then receives an email with a one-time code, which they enter into the authentik Login panel.

The email address will be saved and can be used with the [Authenticator validation](../authenticator_validate/index.mdx) stage for future authentications.

## Flow integration

To use the Email Authenticator Setup stage in a flow, follow these steps:

1. [Create](../../flow/index.md#create-a-custom-flow) a new flow or edit an existing one.
2. On the flow's **Stage Bindings** tab, click **Create and bind stage** to create and add the Email Authenticator Setup stage. (If the stage already exists, click **Bind existing stage**.)
3. Configure the stage settings as described below.
    - **Name**: provide a descriptive name, such as Email Authenticator Setup.
    - **Authenticator type name**: define the display name for this stage.
    - **Use global connection settings**: the stage can be configured in two ways: global settings or stage-specific settings.
        - Enable (toggle on) the **Use global connection settings** option to use authentik's global email configuration. Note that you must already have configured your environment variables to use the global settings. See instructions for [Docker Compose](../../../../install-config/install/docker-compose#email-configuration-optional-but-recommended) and for [Kubernetes](../../../../install-config/install/kubernetes#email-configuration-optional-but-recommended).

        - If you need different email settings for this stage, disable (toggle off) **Use global connection settings** and configure the following options:

        - **Connection settings**:
            - **SMTP Host**: SMTP server hostname (default: localhost)
            - **SMTP Port**: SMTP server port number(default: 25)
            - **SMTP Username**: SMTP authentication username (optional)
            - **SMTP Password**: SMTP authentication password (optional)
                - **Use TLS**: Enable TLS encryption
                - **Use SSL**: Enable SSL encryption
            - **Timeout**: Connection timeout in seconds (default: 10)
            - **From Address**: Email address that messages are sent from (default: system@authentik.local)

        - **Stage-specific settings**:
            - **Subject**: Email subject line (default: "authentik Sign-in code")
            - **Token Expiration**: Time in minutes that the sent token is valid (default: 30)
            - **Configuration flow**: select the flow to which you are binding this stage.

4. Click **Update** to complete the creation and binding of the stage to the flow.

The new Email Authenticator Setup stage now appears on the **Stage Bindings** tab for the flow.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/authenticator_sms/index.mdx
================================================================================

---
title: SMS Authenticator Setup stage
---

This stage configures an SMS-based authenticator using either Twilio, or a generic HTTP endpoint.

## Providers

### Twilio

Navigate to https://console.twilio.com/, and log in to your existing account, or create a new one.

In the sidebar, navigate to _Explore Products_, then _Messaging_, and _Services_ below that.

Click on _Create Messaging Service_ to create a new set of API credentials.

Give the service a Name, and select _Verify users_ as a use-case.

In the next step, add an address from your Sender Pool. Instructions on how to create numbers are not covered here, please check the Twilio documentation [here](https://www.twilio.com/docs).

The other two steps can be skipped using the _Skip setup_ button.

Navigate back to the root of your Twilio console, and copy the Auth token. This is the value for the _Twilio Auth Token_ field in authentik. Copy the value of **Account SID**. This is the value for the _Twilio Account SID_ field in authentik.

#### Custom SMS message :ak-version[2025.8]

Using a property mapping, it is possible to customize the SMS message sent via Twilio. The mapping should return a dictionary with the `message` key, which will be sent to the user. For example:

```python
return {
    "message": f"This is a custom message for {request.http_request.brand.branding_title} SMS authentication. The code is {token}."
}
```

Variables related to different objects can be used within the message:

    - The end user device, for example: `device.phone_number`
    - The stage sending the message, for example: `stage.from_number`
    - The request this verification code is being sent from, for example: `request.http_request.brand`

### Generic

For the generic provider, a POST request will be sent to the URL you have specified in the _External API URL_ field. The request payload looks like this

```json
{
    "From": "<value of the *From number* field>",
    "To": "<the phone number of the user's device>",
    "Body": "<the token that the user needs to authenticate>"
}
```

Authentication can either be done as HTTP Basic, or via a Bearer Token. Any response with status 400 or above is counted as failed, and will prevent the user from proceeding.

#### Custom SMS message

A custom webhook mapping can be used to customize the SMS message sent to users. For example:

```python
return {
    "from": stage.from_number,
    "to": device.phone_number,
    "body": f"foo bar baz {token}"
}
```

## Verify only

To only verify the validity of a user's phone number, without saving it in an easily accessible way, you can enable this option. Phone numbers from devices enrolled through this stage will only have their hashed phone number saved. These devices can also not be used with the [Authenticator validation](../authenticator_validate/index.mdx) stage.

## Limiting phone numbers

To limit phone numbers (for example to a specific region code), you can create an expression policy to validate the phone number, and use a prompt stage for input.

### Expression policy

Create an expression policy to check the phone number:

```python
# Trim all whitespace in and around the user input
phone_number = regex_replace(request.context["prompt_data"]["phone"], r'\s+', '')

# Only allow a specific region code
if phone_number.startswith("+1234"):
    return True
ak_message("Invalid phone number or missing region code")
return False
```

### Prompt stage

Create a text prompt field with the _field key_ set to `phone`. Make sure it is selected as a required field.

Create a prompt stage with the phone field you created above, and select the expression policy created above as validation policy.

### Flow

Create a new flow to enroll SMS devices. Bind the prompt stage created above as first stage, and create/bind a _SMS Authenticator Setup Stage_, and bind it to the flow as second stage. This stage will see the `phone` field in the flow's context's `prompt_data`, and not prompt the user for a phone number.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/invitation/index.md
================================================================================

---
title: Invitation stage
---

This stage can be used to invite users. You can use this to enroll users with preset values.

If the option `Continue Flow without Invitation` is enabled, this stage will continue even when no invitation token is present.

To check if a user has used an invitation within a policy, you can check `request.context.get("invitation_in_effect", False)`.

To use an invitation, use the URL `https://authentik.tld/if/flow/your-enrollment-flow/?itoken=invitation-token`.

You can also prompt the user for an invite by using the [_Prompt stage_](../prompt/index.md) by using a field with a field key of `token`.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/email/index.mdx
================================================================================

---
title: Email stage
---

This stage can be used for email verification. authentik's background worker will send an email using the specified connection details.

When an email can't be delivered, authentik automatically retries periodically.

You can also configure rate-limiting for emails requested by users. See the [configure rate limiting](#configure-rate-limiting-for-emails) section for more information.

For information about creating a stage, refer to our [documentation](../#create-a-stage).

## Behaviour

By default, the email is sent to the currently pending user. To override this, you can set `email` in the plan's context to another email address, which will override the user's email address (the user won't be changed).

For example, create this [expression policy](../../../../customize/policies/expression.mdx) and bind it to the email stage:

```python
request.context["flow_plan"].context["email"] = "foo@bar.baz"
# Or get it from a prompt
# request.context["flow_plan"].context["email"] = request.context["prompt_data"]["email"]
# Or another user attribute
# request.context["flow_plan"].context["email"] = request.context["pending_user"].attributes.get("otherEmail")
return True
```

## Configure rate limiting for emails

You can configure the Email stage with _a maximum number of emails_ that can be sent within _a specified time period_.

To configure the rate limiting for recovery emails use these two fields when you create or edit an Email stage:

- **Account Recovery Max Attempts**: set the maximum number of emails to send.
- **Account Recovery Cache Timeout**: specify the time window used to count recent recovery emails sent to the user (account recovery attempts).

## Custom Templates

You can also use custom email templates, to use your own design or layout.

:::info
Starting with authentik 2024.2, it is possible to create `.txt` files with the same name as the `.html` template. If a matching `.txt` file exists, the email sent will be a multipart email with both the text and HTML template.
:::



:::info
If you have added the line and created a file, and can't see it, check the worker logs using `docker compose logs -f worker` or `kubectl logs -f deployment/authentik-worker`.
:::

![](./custom_template.png)

### Example template

Templates are rendered using Django's templating engine. The following variables can be used:

- `url`: The full URL for the user to click on
- `user`: The pending user object.
- `expires`: The timestamp when the token expires.

{% endblock %}
```



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/source/index.md
================================================================================

---
title: Source stage
authentik_version: "2024.4"
authentik_enterprise: true
---

The source stage embeds an [OAuth](../../../../users-sources/sources/protocols/oauth/index.mdx) or [SAML](../../../../users-sources/sources/protocols/saml/index.md) source into the flow execution. This allows for additional user verification, or to dynamically access different sources for different user identifiers (username, email address, etc).

### Example use case

This stage can be used to leverage an external OAuth/SAML identity provider.

For example, you can authenticate users by routing them through a custom device-health solution.

Another use case is to route users to authenticate with your legacy (Okta, etc) IdP and then use the returned identity and attributes within authentik as part of an authorization flow, for example as part of an IdP migration. For authentication/enrollment this is also possible with an [OAuth](../../../../users-sources/sources/protocols/oauth/index.mdx)/[SAML](../../../../users-sources/sources/protocols/saml/index.md) source by itself.

### Considerations

It is very important that the configured source's authentication and enrollment flows (when set; they can be left unselected to prevent authentication or enrollment with the source) do **not** have a [User login stage](../user_login/index.md) bound to them.

This is because the Source stage works by appending a [dynamic in-memory](../../../../core/glossary?dynamic-in-memory-stage) stage to the source's flow, so having a [User login stage](../user_login/index.md) bound will cause the source's flow to not resume the original flow it was started from, and instead directly authenticating the pending user.

## Source stage workflow

```mermaid
sequenceDiagram
    participant u as User
    participant ak as authentik
    participant eidp as External IDP

    u->>ak: User initiates flow
    ak->>u: User reaches Source Stage

    u->>eidp: User is redirected to external IDP
    eidp->>ak: User has authenticated with external IDP

    alt User is connected to external IDP (auth)
        ak->>u: Source's authentication flow is started
        u->>ak: User finishes source's authentication flow
    else User has not been connected to external IDP (enroll)
        ak->>u: Source's enrollment flow is started
        u->>ak: User finishes source's enrollment flow
    end

    ak->>u: Execution of the previous flow is resumed
```

### Options

#### Source

The source the user is redirected to. Must be a web-based source, such as [OAuth](../../../../users-sources/sources/protocols/oauth/index.mdx) or [SAML](../../../../users-sources/sources/protocols/saml/index.md). Sources like [LDAP](../../../../users-sources/sources/protocols/ldap/index.md) are _not_ compatible.

#### Resume timeout

Because the execution of the current flow is suspended before the user is redirected to the configured source, this option configures how long the suspended flow is saved. If this timeout is exceeded, upon return from the configured source, the suspended flow will restart from the beginning.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/user_login/index.md
================================================================================

---
title: User Login stage
toc_max_heading_level: 4
---

The User Login stage attaches a currently pending user to the current session.

It can be used after `user_write` during an enrollment flow, or after a `password` stage during an authentication flow.

## User login stage configuration options

When creating or editing this stage in the Admin interface, you can define configuration options using the following fields.

#### Session duration

By default, the authentik session expires when you close your browser (_seconds=0_). Use the **Session duration** field to define a custom session length.

    :::warning
    Different browsers handle session cookies differently, and might not remove them even when the browser is closed. See [here](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie#expiresdate) for more info.
    :::

You can set the session to expire after any duration using the syntax of `hours=1,minutes=2,seconds=3`. The following keys are allowed:

    - Microseconds
    - Milliseconds
    - Seconds
    - Minutes
    - Hours
    - Days
    - Weeks

All values accept floating-point values.

#### Stay signed in offset

When the value in **Stay signed in offset** is set to a higher value than the default _seconds=0_, the user logging in is shown a prompt, allowing the user to choose if their session should be extended or not. The same syntax as for **Session duration** applies.

    ![](./stay_signed_in.png)

#### Remember device

If set to a duration above 0, a cookie is stored for the duration specified that informs authentik whether the user is signing in from a known or unknown (new) device.

If there's an existing authenticated user session for the user with the same IP address, authentik also classifies this as a known device. See [here](../../../../sys-mgmt/events/notification_rule_expression_policies.mdx#trigger-alert-when-user-logs-in-from-unknown-device) for an example of how an alert can be configured for logins from unknown devices.

#### Network binding and GeoIP binding

When configured, all sessions authenticated by this stage will be bound to the selected network and/or GeoIP criteria.

Sessions that break this binding will be terminated. The created [`logout`](../../../../sys-mgmt/events/event-actions#logout) event will contain additional data related to what caused the binding to be broken:

```json
{
    "asn": {
        "asn": 6805,
        "as_org": "Telefonica Germany",
        "network": "5.4.0.0/14"
    },
    "geo": {
        "lat": 51.2993,
        "city": "",
        "long": 9.491,
        "country": "DE",
        "continent": "EU"
    },
    "binding": {
        "reason": "network.missing",
        "new_value": {
            "asn": 6805,
            "as_org": "Telefonica Germany",
            "network": "5.4.0.0/14"
        },
        "previous_value": {}
    },
    "ip": {
        "previous": "1.2.3.4",
        "new": "5.6.7.8"
    },
    "http_request": {
        "args": {},
        "path": "/if/admin/",
        "method": "GET",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    },
    "logout_reason": "Session binding broken"
}
```

#### Terminate other sessions

When enabled, previous sessions of the same user are revoked. This has no affect on OAuth refresh tokens.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/authenticator_totp/index.md
================================================================================

---
title: TOTP Authenticator Setup stage
---

This stage configures a time-based OTP Device, such as Google Authenticator or Authy.

You can configure how many digits should be used for the OTP Token.

The Config URL's Issuer is set based on the currently active brand's branding title. The default setup can cause issues if the same username is used on multiple authentik issues within the same authenticator app, so changing the brand title is recommended.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/captcha/index.md
================================================================================

---
title: Captcha stage
---

This stage adds a form of verification using [Google's reCAPTCHA](https://www.google.com/recaptcha/intro/v3.html) or compatible services.

Currently supported implementations:

- [Google reCAPTCHA](#google-recaptcha)
- [hCaptcha](#hcaptcha)
- [Cloudflare Turnstile](#cloudflare-turnstile)

## Captcha provider configuration

### Google reCAPTCHA

This stage has two required fields: Public key and private key. These can both be acquired at https://www.google.com/recaptcha/admin.

![](./captcha-admin.png)

#### Configuration options

- Interactive: Enabled when using reCAPTCHA v3
- Score minimum threshold: `0.5`
- Score maximum threshold: `1`
- JS URL: `https://www.recaptcha.net/recaptcha/api.js`
- API URL: `https://www.recaptcha.net/recaptcha/api/siteverify`

### hCaptcha

See https://docs.hcaptcha.com/switch

#### Configuration options

- Interactive: Enabled
- JS URL: `https://js.hcaptcha.com/1/api.js`
- API URL: `https://api.hcaptcha.com/siteverify`

**Score options only apply to hCaptcha Enterprise**

- Score minimum threshold: `0`
- Score maximum threshold: `0.5`

### Cloudflare Turnstile

See https://developers.cloudflare.com/turnstile/get-started/migrating-from-recaptcha.

#### Configuration options

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Stages** and click **Create**.
3. Select **Captcha Stage** and click **Next**.
4. Provide a descriptive name for the stage (e.g. `authentication-captcha`) and configure the following required settings based on the values of your [Cloudflare Turnstile Widget](https://developers.cloudflare.com/turnstile/concepts/widget/):
    - Under **Stage-specific settings**:
        - **Public Key**: set to the **Turnstile Site Key** value from the widget.
        - **Private Key**: set to the **Turnstile Secret Key** value from the widget.
        - **Enable Interactive**: Enable this option if the Turnstile instance is configured as **Invisible** or **Managed**.
        - Leave both score thresholds at their default, as they are not supported for Turnstile.

- JS URL: `https://challenges.cloudflare.com/turnstile/v0/api.js`
- API URL: `https://challenges.cloudflare.com/turnstile/v0/siteverify`

**Score options do not apply when using with turnstile**



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/authenticator_webauthn/index.mdx
================================================================================

---
title: WebAuthn / FIDO2 / Passkeys Authenticator setup stage
---

This stage configures an authenticator stage for using WebAuthn, FIDO2, Passkeys. This stage supports:

- **Security Keys**: Physical devices like YubiKey, Google Titan, etc.
- **Platform Authenticators**: Built-in authenticators like Windows Hello, Touch ID, Face ID
- **Mobile Devices**: Using device biometrics or security keys via mobile browsers

### Options

#### User verification

Configure if authentik should require, prefer or discourage user verification for the authenticator. For example when using a virtual authenticator like Windows Hello, this setting controls if a PIN is required.

#### Resident key requirement

Configure if the created authenticator is stored in the encrypted memory on the device or in persistent memory. When configuring [passwordless login](../identification/index.mdx#passwordless-flow), this should be set to either _Preferred_ or _Required_, otherwise the authenticator cannot be used for passwordless authentication.

#### Authenticator Attachment

Configure if authentik will require either a removable device (like a YubiKey, Google Titan, etc) or a non-removable device (like Windows Hello, TouchID or password managers), or not send a requirement.

#### Device type restrictions

Optionally restrict the types of devices allowed to be enrolled. This option can be used to ensure users are only able to enroll FIPS-compliant devices for example.

When no restrictions are selected, all device types are allowed.

As authentik does not know of all possible device types, it is possible to select the special option `authentik: Unknown devices` to allow unknown devices.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/mtls/index.md
================================================================================

---
title: Mutual TLS stage
authentik_version: "2025.6"
authentik_preview: true
authentik_enterprise: true
toc_max_heading_level: 5
---

The Mutual TLS stage enables authentik to use client certificates to enroll and authenticate users. These certificates can be local to the device or available via PIV Smart Cards, Yubikeys, etc.

:::warning Use of trusted Certificate Authority

For mTLS, note that you should NOT use a globally known CA.

Using private PKI certificates that are trusted by the end-device is best practice. For example, using a Verisign certificate as a "known CA" means that ANYONE who has a certificate signed by them can authenticate via mTLS, and in addition you should implement [custom validation](../../flow/context/index.mdx#auth_method-string) to prevent unauthorized access.
:::

## Reverse-proxy configuration

Using the Mutual TLS stage requires special configuration of any reverse proxy that is used in front of authentik, because the reverse-proxy interacts directly with the browser.

- nginx
    - [Standalone nginx](#nginx-standalone)
    - [nginx kubernetes ingress](#nginx-ingress)
- Traefik
    - [Standalone Traefik](#traefik-standalone)
    - [Traefik kubernetes ingress](#traefik-ingress)
- [envoy](#envoy)
- [No reverse proxy](#no-reverse-proxy)

#### nginx Standalone

Add this configuration snippet in your authentik virtual host:

```nginx
# server {
    ssl_client_certificate /etc/ssl/path-to-my-ca.pem;
    ssl_verify_client on;

    # location / {
        proxy_set_header ssl-client-cert $ssl_client_escaped_cert;
    # }
# }
```

See [nginx documentation](https://nginx.org/en/docs/http/ngx_http_ssl_module.html#ssl_client_certificate) for reference.

#### nginx Ingress

Add these annotations to your authentik ingress object:

```yaml
nginx.ingress.kubernetes.io/auth-tls-pass-certificate-to-upstream: "true"
# This secret needs to contain `ca.crt` which is the certificate authority to validate against.
nginx.ingress.kubernetes.io/auth-tls-secret: namespace/secretName
```

See [ingress-nginx documentation](https://kubernetes.github.io/ingress-nginx/examples/auth/client-certs/) for reference.

#### Traefik Standalone

Add this snippet to your traefik configuration:

```yaml
tls:
    options:
        default:
            clientAuth:
                # in PEM format. each file can contain multiple CAs.
                caFiles:
                    - tests/clientca1.crt
                    - tests/clientca2.crt
                clientAuthType: RequireAndVerifyClientCert
```

See the [Traefik mTLS documentation](https://doc.traefik.io/traefik/https/tls/#client-authentication-mtls) for reference.

#### Traefik Ingress

Create a middleware object with these options:

```yaml
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
    name: test-passtlsclientcert
spec:
    passTLSClientCert:
        pem: true
```

See the [Traefik PassTLSClientCert documentation](https://doc.traefik.io/traefik/middlewares/http/passtlsclientcert/) for reference.

#### Envoy

See the [Envoy mTLS documentation](https://www.envoyproxy.io/docs/envoy/latest/start/quick-start/securing#use-mutual-tls-mtls-to-enforce-client-certificate-authentication) and [Envoy header documentation](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_conn_man/headers#x-forwarded-client-cert) for configuration.

#### No reverse proxy

When using authentik without a reverse proxy, select the certificate authorities in the corresponding [brand](../../../../sys-mgmt/brands/index.md#client-certificates) for the domain, under **Other global settings**.

## Stage configuration

1. Log in to authentik as an administrator and open the authentik Admin interface.

2. Navigate to **System** > **Certificates**, and either generate or add the certificate you’ll use as a certificate authority.

3. Then, navigate to **Flows and Stages** > **Stages** and click **Create**. Select **Mutual TLS Stage**, click **Next**, and set the following fields:
    - **Name**: provide a descriptive name, such as "chrome-device-trust".

    - **Stage-specific settings**:
        - **Mode**: Configure the mode this stage operates in.
            - **Certificate optional**: When no certificate is provided by the user or the reverse proxy, the flow will continue to the next stage.
            - **Certificate required**: When no certificate is provided, the flow ends with an error message.

        - **Certificate authorities**: Select the certificate authorities used to sign client certificates.

        - **Certificate attribute**: Select the attribute of the certificate to be used to find a user for authentication.

        - **User attribute**: Select the attribute of the user the certificate should be compared against.

4. Click **Finish**.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/flows-stages/stages/authenticator_validate/index.mdx
================================================================================

---
title: Authenticator Validation stage
---

This stage validates an already configured Authenticator Device. This device has to be configured using any of the other authenticator stages:

- [Duo authenticator stage](../authenticator_duo/index.mdx)
- [Email authenticator stage](../authenticator_email/index.md)
- [SMS authenticator stage](../authenticator_sms/index.mdx)
- [Static authenticator stage](../authenticator_static/index.md)
- [TOTP authenticator stage](../authenticator_totp/index.md)
- [WebAuthn authenticator stage](../authenticator_webauthn/index.mdx)

You can select which device classes are allowed.

Using the `Not configured action`, you can choose what happens when a user does not have any matching devices.

- Skip: Validation is skipped and the flow continues
- Deny: Access is denied, the flow execution ends
- Configure: This option requires a _Configuration stage_ to be set. The validation stage will be marked as successful, and the configuration stage will be injected into the flow.

By default, authenticator validation is required every time the flow containing this stage is executed. To only change this behavior, set _Last validation threshold_ to a non-zero value. (Requires authentik 2022.5)
Keep in mind that when using Code-based devices (TOTP, Static and SMS), values lower than `seconds=30` cannot be used, as with the way TOTP devices are saved, there is no exact timestamp.

### Options

#### Less-frequent validation

You can configure this stage to only ask for MFA validation if the user hasn't authenticated themselves within a defined time period. To configure this, set _Last validation threshold_ to any non-zero value. Any of the user's devices within the selected classes are checked.

#### Passwordless authentication

:::caution
Firefox has some known issues regarding TouchID (see https://bugzilla.mozilla.org/show_bug.cgi?id=1536482)
:::

Passwordless authentication currently only supports WebAuthn devices, which support passkeys, security keys, and biometrics. For an alternate passwordless setup, see [Password stage](../password/index.md#passwordless-login), which supports other types.

If you want users to authenticate with a passkey via the browser's built-in passkey/autofill UI on the **Identification** screen ("conditional UI" / passkey autofill), configure it in the [Identification stage](../identification/index.mdx#passkey-autofill-webauthn-conditional-ui). This requires a **discoverable credential (aka resident key)**.

To configure passwordless authentication, create a new Flow with the designation set to _Authentication_.

As the first stage, add an _Authenticator validation_ stage with the WebAuthn device class allowed.
After this stage you can bind any additional verification stages.
As the final stage, bind a _User login_ stage.

Users can either access this flow directly via its URL, or you can modify any Identification stage's _Passwordless flow_ setting to add a direct link to this flow.

#### Logging

Logins that used Passwordless authentication have the _auth_method_ context variable set to `auth_webauthn_pwl`, and the device used is saved in the arguments. Example:

```json
{
    "auth_method": "auth_webauthn_pwl",
    "http_request": {
        "args": {
            "query": ""
        },
        "path": "/api/v3/flows/executor/test/",
        "method": "GET"
    },
    "auth_method_args": {
        "device": {
            "pk": 1,
            "app": "authentik_stages_authenticator_webauthn",
            "name": "test device",
            "model_name": "webauthndevice"
        }
    }
}
```

#### WebAuthn Device type restrictions

Optionally restrict which WebAuthn device types can be used to authenticate.

When no restriction is set, all WebAuthn devices a user has registered are allowed.

These restrictions only apply to WebAuthn devices created with authentik 2024.4 or later.

#### Automatic device selection

If the user has more than one device, the user is prompted to select which device they want to use for validation. After the user successfully authenticates with a certain device, that device is marked as "last used". In subsequent prompts by the Authenticator validation stage, the last used device is automatically selected for the user. Should they wish to use another device, the user can return to the device selection screen.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/property-mappings/index.md
================================================================================

---
title: Provider property mappings
---

Property mappings allow you to pass information to external applications. For example, pass the current user's groups as a SAML parameter.

## SAML property mappings

SAML property mappings allow you embed information into the SAML authentication request. This information can then be used by the application to, for example, assign permissions to the object.

## Scope mappings with OAuth2

Scope mappings are used by the OAuth2 provider to map information from authentik to OAuth2/OIDC claims. Values returned by a scope mapping are added as custom claims to access and ID tokens.

:::info Default value for `email_verified`
By default, authentik sets the `email_verified` claim to `False`, since it has no way to confirm whether a user's email is verified. Setting this claim to `True` by default could introduce unintended security risks.

Be aware that some applications might require this claim to be true to successfully authenticate users. See [Email scope verification](../oauth2/index.mdx#email-scope-verification) for more information.
:::

## Skip objects during synchronization

To skip synchronization for a specific object, you can create a property mapping with an expression that triggers the `SkipObject` exception. This functionality is supported by the following providers: [**Google Workspace**](../gws/), [**Microsoft Entra ID**](../entra/), and [**SCIM**](../scim/).

**Example:**

```python
if request.user.username == "example_username":
	raise SkipObject
```



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/property-mappings/expression.mdx
================================================================================

---
title: Expressions
---

The property mapping should return a value that is expected by the provider. Supported types are documented in the individual provider. Returning `None` is always accepted and would simply skip the mapping for which `None` was returned.

## Available Functions



## Variables





- `request`: The current request. This may be `None` if there is no contextual request. See ([Django documentation](https://docs.djangoproject.com/en/3.0/ref/request-response/#httprequest-objects))
- Other arbitrary arguments given by the provider, this is documented on the provider.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/scim/index.md
================================================================================

---
title: SCIM Provider
---

SCIM (System for Cross-domain Identity Management) is a set of APIs to provision users and groups. The SCIM provider in authentik supports SCIM 2.0 and can be used to provision and sync users from authentik into other applications.

A SCIM provider requires a SCIM base URL for the endpoint and an authentication token. SCIM works via HTTP requests, so authentik must be able to reach the specified endpoint. This endpoint usually ends in `/v2`, which corresponds to the SCIM version supported.

SCIM providers in authentik always serve as [backchannel providers](../../applications/manage_apps.mdx#backchannel-providers), which are used in addition to the main provider that supplies SSO authentication. A backchannel provider is used for an application that requires backend authentication, directory synchronization, or other additional authentication needs.

For example, you can create an application and provider pair for Slack, creating Slack as the application and SAML as the provider. Say you then want to use SCIM for further authentication using a token. For this scenario use the following workflow:

1. [Create](../../applications/manage_apps.mdx#create-an-application-and-provider-pair) the application and provider pair.
2. [Create](../../applications/manage_apps.mdx#backchannel-providers) the SCIM backchannel provider.
3. Edit the application and in the **Backchannel Providers** field add the backchannel provider that you just created.

## Authentication mode options

In authentik, there are two options for how to configure authentication for a SCIM provider:

- **Static token** provided by the application (default)
- **OAuth token** authentik will retrieve an OAuth token from a specified source and use that token for authentication

When you create a new SCIM provider, select which **Authentication Mode** the application supports.

![Creating a SCIM provider](./scim_oauth.png)

Whichever mode you select, you'll need to enter a SCIM base **URL** for the endpoint.

### Default authentication method for a SCIM provider

With authentik's default mode, the token that you enter (provided by the application) is sent with all outgoing SCIM requests to authenticate each request.

### OAuth authentication for a SCIM provider :ak-enterprise :ak-version[2025.10]

Configuring your SCIM provider to use OAuth for authentication means that short-lived tokens are dynamically generated through an OAuth flow and sent to the SCIM endpoint. This offers improved security and control versus a static token.

You can also add additional token request parameters to the OAuth token, such as `grant_type`, `subject_token`, or `client_assertion`.

Some examples are:

- `grant_type: client_credentials`

- `grant_type: password`

:::info OAuth source required
To use OAuth authentication for your application, you will need to create and connect to an [OAuth source](../../../users-sources/sources/protocols/oauth/).
:::

### Syncing

Data is synchronized in multiple ways:

- When a user/group is created/modified/deleted, that action is sent to all SCIM providers
- Periodically (once an hour), all SCIM providers are fully synchronized

The actual synchronization process is run in the authentik worker. To allow this process to scale better, a task is started for each 100 users and groups, so when multiple workers are available the workload will be distributed.

### Attribute mapping

Attribute mapping from authentik to SCIM users is done via property mappings as with other providers. The default mappings for users and groups make some assumptions that should work for most setups, but it is also possible to define custom mappings to add fields.

All selected mappings are applied in the order of their name, and are deeply merged onto the final user data. The final data is then validated against the SCIM schema, and if the data is not valid, the sync is stopped.

#### Skipping objects during synchronization

To exclude specific users or groups from SCIM synchronization, you can create a property mapping that raises the `SkipObject` exception. When this exception is raised during the evaluation of a property mapping, the object is skipped and the sync continues with the next object.

For more information, refer to [Skip objects during synchronization](../property-mappings/#skip-objects-during-synchronization).

### Compatibility modes

By default, service accounts are excluded from being synchronized. This can be configured in the SCIM provider.

#### User Filtering

Users can be filtered using application policies.

Only users who can view the SCIM provider's application are synced by the SCIM provider.

#### Group Filters

Group Filters allow you to define the group syncing scope of a SCIM provider.

In its default configuration, with no group filters selected, the SCIM provider will sync all groups.

If group filters are selected, only selected groups will be synced.

Currently, changes to filter groups do _not_ remove previously synchronized groups and members.

Available compatibility modes:

- **Default**: Standard SCIM 2.0 implementation
- **AWS**: Disables PATCH operations for AWS Identity Center compatibility
- **Slack**: Enables filtering support for Slack's SCIM implementation
- **Salesforce**: Uses the non-standard `/ServiceProviderConfigs` endpoint
- **vCenter**: Skips the `ServiceProviderConfig` endpoint which is not implemented in VMware vCenter

To configure a compatibility mode, select the appropriate option in the **SCIM Compatibility Mode** field when creating or editing a SCIM provider.

### Filtering users

By default, service accounts are excluded from being synchronized. This can be configured in the SCIM provider. Additionally, an optional group can be configured to only synchronize the users that are members of the selected group. Changing this group selection does _not_ remove members outside of the group that might have been created previously.

### Supported options

SCIM defines several optional settings that allow clients to discover a service provider's supported features. In authentik, the [`ServiceProviderConfig`](https://datatracker.ietf.org/doc/html/rfc7644#section-4) endpoint provides support for the following options (if the option is supported by the service provider).

:::note
The `ServiceProviderConfig` is cached for 1 hour after it is fetched. The cache is automatically cleared when the SCIM provider is updated (such as when changing the compatibility mode).
:::

- Filtering

    When the remote system supports [filtering](https://datatracker.ietf.org/doc/html/rfc7644#section-3.4.2.2), authentik uses this operation to filter users and groups in the remote system to match them to existing authentik users and groups.

- Bulk

    The [`bulk`](https://datatracker.ietf.org/doc/html/rfc7644#section-3.7) configuration enables clients to send large collections of resource operations in a single request. If the remote system sets this attribute, authentik will respect the `maxOperations` value to determine the maximum number of individual operations a server can process within a single bulk request.

- Patch updates

    If the service provider supports [PATCH updates](https://datatracker.ietf.org/doc/html/rfc7644#section-3.5.2), authentik will use patch requests to add/remove members of groups. For all other updates, such as user updates and other group updates, PUT requests are used.

### Using in conjunction with other providers

A lot of applications support SCIM in conjunction with another SSO protocol like OAuth/OIDC or SAML. With default settings, the unique user IDs in SCIM and other protocols are identical, which should easily allow applications to link users that are provisioned with users that are logging in.

Applications can either match users on a unique ID sent by authentik called `externalId`, by their email or username.

#### OAuth/OIDC

The default provider configuration for the _Subject mode_ option of _Based on the User's hashed ID_ matches the `externalId` that's generated by default. If any other _Subject mode_ is selected, the `externalId` attribute can be customized via SCIM mappings.

#### SAML

The SAML NameID policy _urn:oasis:names:tc:SAML:2.0:nameid-format:persistent_ uses the same unique user identifier as the default `externalId` value used by the SCIM provider. If a SAML application does not send a NameID request, this value is also used as fallback.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/gws/configure-gws.md
================================================================================

---
title: Configure Google Workspace
authentik_enterprise: true
---

For more information about using a Google Workspace provider, see the [Overview](./index.md) documentation.

Your Google Workspace organization must be configured before you [create a Google Workspace provider](./create-gws-provider.md).

## Configure your Google Workspace Organization

The main steps to configure your Google Workspace organization are:

1. [Create a Google Cloud project](#create-a-google-cloud-project)
2. [Create a service account](#create-a-service-account)
3. [Configure service account key and scopes](#configure-service-account-key-and-scopes)
4. [Select a user for the Delegated Subject](#select-a-user-for-the-delegated-subject)

### Create a Google Cloud project

1. Open the [Google Cloud console](https://cloud.google.com/cloud-console).
2. In the upper left, click the drop-down box to open the **Select a project** box, then select **New Project**.
3. Create a new project and provide a name (e.g. `authentik GWS`).
4. Use the search bar at the top of your new project page to search for `API Library`.
5. On the **API Library** page, use the search bar again to find `Admin SDK API`.
6. On the **Admin SDK API** page, click **Enable**.

### Create a service account

1. After the new Admin SDK API is enabled (it might take a few minutes), return to the Google Cloud console home page by clicking on **Google Cloud** in the upper left.
2. Use the search bar to find and navigate to the **IAM** page.
3. On the **IAM** page, click **Service Accounts** in the left navigation pane.
4. At the top of the **Service Accounts** page, click **Create Service Account**.
    - Under **Service account details** page, define the **Name** and **Description** for the new service account, then click **Create and Continue**.
    - Under **Grant this service account access to project** you do not need to define a role, so click **Continue**.
    - Under **Grant users access to project** you do not need to define a role, so click **Done** to complete the creation of the service account.

### Configure service account key and scopes

1. On the **Service accounts** page, click the account that you just created.
2. Click the **Keys** tab at top of the page, then click **Add Key** > **Create new key**.
3. Select **JSON** as the key type, then click **Create**.
   A pop-up displays with the private key. The key can be saved to your computer as a JSON file. This key will be required when creating the Google Workspace provider in authentik.

    :::info Allow key creation
    By default, the Google Cloud organization policy `iam.disableServiceAccountKeyCreation` prevents creating service account keys. To allow key creation:
    1. Navigate to **IAM & Admin** > **Organization Policies** and select the **Disable service account key creation** policy.
    2. Click **Manage policy** and disable the policy.
    3. Click **Set policy** to save your changes.
       :::

4. On the service account page, click the **Details** tab, and expand the **Advanced settings** area.
5. Copy the **Client ID** (under **Domain-wide delegation**), and then click **View Google Workspace Admin Console**.
6. Log in to the Admin Console, and then navigate to **Security** > **Access and data control** > **API controls**.
7. On the **API controls** page, click **Manage Domain Wide Delegation**.
8. On the **Domain Wide Delegation** page, click **Add new**.
9. In the **Add a new client ID** box, paste in the Client ID that you copied from the Admin console earlier (the value from the downloaded JSON file) and paste in the following scope documents:
    - `https://www.googleapis.com/auth/admin.directory.user`
    - `https://www.googleapis.com/auth/admin.directory.group`
    - `https://www.googleapis.com/auth/admin.directory.group.member`
    - `https://www.googleapis.com/auth/admin.directory.domain.readonly`

### Select a user for the Delegated Subject

**Delegated Subject** is a required field when creating the Google Workspace provider in authentik. This field must be populated with the email address of a Google Workspace user with [suitable permissions](#delegated-subject-permissions).

1. In the sidebar navigate to **Directory** > **Users**.
2. Either select an existing user's email address or **Add new user** and define the user and email address to use as the Delegated Subject.
3. Take note of this email address as it will be required when creating the Google Workspace provider in authentik.

#### Delegated Subject permissions

:::warning
We do not recommend using an administrator account for the Delegated Subject user. A custom role should be used instead, see the [Google Admin console documentation](https://support.google.com/a/answer/2406043?hl=en) for more details.
:::

The Delagated Subject user requires the following permissions:

##### Admin console privileges

- Users
- Groups

##### Admin API privileges

- Domain management
- Users
- Groups

Now that you have configured your Google Workspace organization, you are ready to [create a Google Workspace provider](./create-gws-provider.md).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/gws/index.md
================================================================================

---
title: Google Workspace provider
authentik_enterprise: true
---

The Google Workspace provider allows you to integrate with your Google Workspace organization. It supports syncing users and groups from authentik to Google Workspace, allowing authentik to act as a source of truth for all users and groups.

- For instructions on configuring your Google Workspace organization in prepation for creating a Google Workspace provider, refer to the [Configure Google Workspace](./configure-gws.md) documentation.
- For instructions on creating a Google Workspace provider, refer to the [Create a Google Workspace provider](./create-gws-provider.md) documentation.

## Discovery

Upon creating the Google Workspace provider, it will run a discovery task to query your google workspace for all users and groups, and attempt to match them with their respective counterparts in authentik.

Users are matched on their email address. Groups are matched based on their names.

This discovery also takes into consideration any **User filtering** options configured in the provider, such as only linking to authentik users in a specific group or excluding service accounts. This discovery process occurs each time a full sync is initiated.

## Synchronization

There are two types of synchronization: direct sync and full sync.

### Direct sync

A direct sync occurs when a user or group is created, updated or deleted in authentik, or when a user is added to or removed from a group. When any of these events occur, the direct sync automatically syncs those changes to Google Workspace.

### Full sync

A full sync occurs when the provider is initially created and when it is saved. During a full sync, all users and groups that match the **User filtering** settings are processed and created or updated in Google Workspace. After the initial sync, authentik automatically performs a full sync every four hours to maintain consistency between users and groups.

During the full sync, if a user or group exists in both authentik and Google Workspace, authentik will automatically link them.

Additionally, any users or groups present in authentik but absent in Google Workspace will be created and linked.

## Error handling

When a property mapping has an invalid expression, it will cause a sync to stop to prevent excessive error messages.

To handle network interruptions, authentik detects transient request failures and retries sync tasks.

## Property mapping

There are several considerations regarding how authentik data is mapped to Google Workspace user and group data.

### Users

For users, authentik only saves the full display name, while Google requires the first (given) name and the family name separately, and as such authentik attempts to separate the full name automatically with the `authentik default Google Workspace Mapping: User` property mapping.

By default, authentik maps a user’s email address, name, and active status.

Refer to Google documentation for further details on which attributes can be mapped: [Google Workspace Reference - Resource: User](https://developers.google.com/admin-sdk/directory/reference/rest/v1/users#User)

### Groups

For groups, Google Workspace groups require an email address. Therefore the Google Workspace provider has an **Default group email domain** setting, which will be used in conjunction with the group’s name to generate an email address. This can be customized with a property mapping.

By default, authentik only maps a group's name.

Refer to Google documentation for further details on which attributes can be mapped: [Google Workspace Reference - Resource: Group](https://developers.google.com/admin-sdk/directory/reference/rest/v1/groups#Group)

### Skipping objects during synchronization

To exclude specific users or groups from Google Workspace synchronization, you can create a property mapping that raises the `SkipObject` exception. When this exception is raised during the evaluation of a property mapping, the object is skipped and the sync continues with the next object.

For more information, refer to [Skip objects during synchronization](../property-mappings/#skip-objects-during-synchronization).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/gws/create-gws-provider.md
================================================================================

---
title: Create a Google Workspace provider
authentik_enterprise: true
---

For more information about using a Google Workspace provider, see the [Overview](./index.md) documentation.

## Prerequisites

To create a Google Workspace provider in authentik, you must have already [configured Google Workspace](./configure-gws.md).

## Create a Google Workspace provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click **Create**.
3. Select **Google Workspace Provider** as the provider type, then click **Next**.
4. On the **Create Google Workspace Provider** page, set the following configurations:
    - **Name**: provide a descriptive name (e.g. `GWS provider`)
    - Under **Protocol settings**:
        - **Credentials**: paste the contents of the JSON file that you downloaded when [configuring Google Workspace](./configure-gws.md)
        - **Delegated Subject**: enter the email address of the Google Workspace user that all authentik actions will be delegated to
        - **Default group email domain**: enter a domain which will be used to generate the email address for groups synced from authentik to Google Workspace
        - **User deletion action**: determines what authentik will do when a user is deleted from authentik
        - **Group deletion action**: determines what authentik will do when a group is deleted from authentik
    - Under **User filtering**:
        - **Exclude service accounts**: choose whether to include or exclude service accounts
        - **Group**: select a group and only users within that group will be synced to Google Workspace
    - Under **Attribute mapping**:
        - **User Property Mappings**: select any property mappings, or use the default
        - **Group Property Mappings**: select any property mappings, or use the default

        :::info Skipping certain users or groups
        The `SkipObject` exception can be used within a property mapping to prevent specific objects from being synced. Refer to the [Provider property mappings documentation](../property-mappings/index.md#skip-objects-during-synchronization) for more details.
        :::

5. Click **Finish**.

## Create a Google Workspace application in authentik

:::info Backchannel Provider
If you have configured the [Google Workspace SAML integration](/integrations/services/google/) to enable authenticating to Google Workspace with authentik, you can add the provider created in the previous section as a backchannel provider to the existing application, instead of creating a new one.
:::

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications**, click **Create**, and set the following configurations:
    - **Name**: provide a name for the application (e.g. `GWS`)
    - **Slug**: enter the name that you want to appear in the URL
    - **Provider**: when _not_ used in conjunction with the [Google SAML configuration](/integrations/cloud-providers/google), this should be left empty.
    - **Backchannel Providers**: this field is required for Google Workspace. Select the name of the Google Workspace provider that you created in the previous section.
    - **UI settings**: leave these fields empty for Google Workspace.

3. Click **Create**.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/entra/index.md
================================================================================

---
title: Microsoft Entra ID provider
authentik_enterprise: true
---

The Entra ID provider allows you to integrate with your Entra ID tenant. It supports syncing users and groups from authentik to Entra ID, allowing authentik to act as a source of truth for all users and groups.

- For instructions on configuring your Entra ID tenant in prepation for creating an Entra ID provider, refer to [Configure Entra ID](./configure-entra.md).
- For instructions on creating an Entra ID provider, refer to [Create an Entra ID provider](./create-entra-provider.md).

## Discovery

Upon creating the Entra ID provider, it will run a discovery task to query your Entra ID tenant for all users and groups, and attempt to match them with their respective counterparts in authentik.

Users are matched on their email address. Groups are matched based on their names.

This discovery also takes into consideration any **User filtering** options configured in the provider, such as only linking to authentik users in a specific group or excluding service accounts. This discovery process occurs each time a [full sync](#full-sync) is initiated.

## Synchronization

There are two types of synchronization: direct sync and full sync.

### Direct sync

A direct sync occurs when a user or group is created, updated or deleted in authentik, or when a user is added to or removed from a group. When any of these events occur, the direct sync automatically syncs those changes to Entra ID.

### Full sync

A full sync occurs when the provider is initially created and when it is saved. During a full sync, all users and groups that match the **User filtering** settings are processed and created or updated in Entra ID. After the initial sync, authentik automatically performs a full sync every four hours by default to maintain consistency between users and groups.

During the full sync, if a user or group exists in both authentik and Entra ID, authentik will automatically link them.

Additionally, any users or groups present in authentik but absent in Entra ID will be created and linked.

## Error handling

When a property mapping has an invalid expression, it will cause a sync to stop to prevent excessive error messages.

To handle network interruptions, authentik detects transient request failures and retries sync tasks.

## Property mapping

There are several considerations regarding how authentik data is mapped to Entra ID user and group data.

### Users

For users, authentik only saves the full display name, not separate first and family names.

By default, authentik maps a user's email address, name, and whether the user is active.

Refer to the Entra ID documentation for further details on which attributes can be mapped: [Microsoft Graph - Create User](https://learn.microsoft.com/en-us/graph/api/user-post-users?view=graph-rest-1.0&tabs=http#request-body)

### Groups

By default, authentik only maps a group's name, `mail_enabled` status, `security_enabled` status and `mail_nickname` (equivalent to name).

Refer to the Entra ID documentation for further details on these attributes and which attributes can be mapped: [Microsoft Graph - Create Group](https://learn.microsoft.com/en-us/graph/api/group-post-groups?view=graph-rest-1.0&tabs=http#request-body)

### Skipping objects during synchronization

To exclude specific users or groups from Entra ID synchronization, you can create a property mapping that raises the `SkipObject` exception. When this exception is raised during the evaluation of a property mapping, the object is skipped and the sync continues with the next object.

For more information, refer to [Skip objects during synchronization](../property-mappings/#skip-objects-during-synchronization).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/entra/create-entra-provider.md
================================================================================

---
title: Create an Entra ID provider
authentik_enterprise: true
---

For more information about using an Entra ID provider, see the [Overview](./index.md) documentation.

## Prerequisites

To create an Entra ID provider in authentik, you must have already [configured Entra ID](./configure-entra.md).

## Create an Entra ID provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click **Create**.
3. Select **Microsoft Entra Provider** as the provider type, then click **Next**.
4. On the **Create Microsoft Entra Provider** page, set the following configurations:
    - **Name**: provide a descriptive name (e.g. `Entra ID provider`)
    - Under **Protocol settings**:
        - **Client ID**: the Client ID that you copied when [configuring Entra ID](./configure-entra.md)
        - **Client Secret**: the secret from Entra ID
        - **Tenant ID**: the Tenant ID from Entra ID
        - **User deletion action**: determines what authentik will do when a user is deleted from authentik
        - **Group deletion action**: determines what authentik will do when a group is deleted from authentik
    - Under **User filtering**:
        - **Exclude service accounts**: choose whether to include or exclude service accounts
        - **Group**: select a group and only users within that group will be synced to Entra ID
    - Under **Attribute mapping**:
        - **User Property Mappings**: select any property mappings, or use the default
        - **Group Property Mappings**: select any property mappings, or use the default

        :::info Skipping certain users or groups
        The `SkipObject` exception can be used within a property mapping to prevent specific objects from being synced. Refer to the [Provider property mappings documentation](../property-mappings/index.md#skip-objects-during-synchronization) for more details.
        :::

5. Click **Finish**.

## Create an Entra ID application in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications**, click **Create**, and set the following configurations:
    - **Name**: provide a name for the application (e.g. `Entra ID`)
    - **Slug**: enter the name that you want to appear in the URL
    - **Provider**: this field should be left empty
    - **Backchannel Providers**: this field is required for Entra ID. Select the name of the Entra ID provider that you created in the previous section.
    - **UI settings**: leave these fields empty for Entra ID.

3. Click **Create**.

## Email handling (_optional_) {#email-handling}

When the default `authentik default Microsoft Entra Mapping: User` property mapping is used, authentik checks whether each user's email domain is verified in your Entra ID tenant.

In which case, you must configure each user's email domain as a [verified custom domain in Entra ID](https://learn.microsoft.com/en-us/entra/identity/users/domains-manage#add-custom-domain-names-to-your-microsoft-entra-organization); otherwise, provisioning fails. The tenant's default `onmicrosoft.com` domain (e.g., `@<tenant name>.onmicrosoft.com`), is considered a verified domain.

### Email-verified-users

Alternatively, if you need to provision users with email domains that you don't control, you can provision users as "email-verified-users" in Entra ID.

These are limited access accounts that must use email for verification when logging in, refer to the [Microsoft documentation](https://learn.microsoft.com/en-us/entra/identity/users/directory-self-service-signup) for more information about the limitations of these accounts.

This is possible via a modified property mapping:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
3. Select **Microsoft Entra Provider Mapping** as the property mapping type and click **Next**.
4. Provide a **Name** for the property mapping and set the following **Expression**:

```python showLineNumbers
# Field reference: (note that keys have to converted to snake_case)
# https://learn.microsoft.com/en-us/graph/api/resources/user?view=graph-rest-1.0
from msgraph.generated.models.password_profile import PasswordProfile
from msgraph.generated.models.object_identity import ObjectIdentity

# Domains that are verified in Entra ID
verified_domains = {
    "company.com",
    "example.com",
    # add more domains here...
}

# Extract domain from email
email = request.user.email
domain = email.split("@", 1)[-1].lower()

if domain in verified_domains:
    # For users with verified domains
    user = {
        "display_name": request.user.name,
        "account_enabled": request.user.is_active,
        "mail_nickname": request.user.username,
        "user_principal_name": request.user.email,
    }
    if connection:
        # If there is a connection already made (discover or update), we can use
        # that connection's immutable_id...
        user["on_premises_immutable_id"] = connection.attributes.get("on_premises_immutable_id")
    else:
        user["password_profile"] = PasswordProfile(
            password=request.user.password
        )
        # ...otherwise we set an immutable ID based on the user's UID
        user["on_premises_immutable_id"] = request.user.uid
else:
    # For users with non-verified domains
    # e.g., email-verified-users
    # https://learn.microsoft.com/en-us/entra/identity/users/domains-manage#add-custom-domain-names-to-your-microsoft-entra-organization
    user = {
        "display_name": request.user.name,
        "mail": request.user.email,
        "password_policies": "DisablePasswordExpiration", # this setting is required by Entra ID
        "user_type": "member" # can be set to "guest" to limit a user's access to read user lists
    }

    # for other sign in types
    # refer to https://learn.microsoft.com/en-us/graph/api/resources/user?view=graph-rest-1.0
    user["identities"] = [
        ObjectIdentity(
          sign_in_type = "federated",
          issuer = "mail",
          issuer_assigned_id = request.user.email,
        )
    ]

    user["password_profile"] = PasswordProfile(
        password=request.user.password
    )

return user
```

5. Click **Finish**.
6. Navigate to **Applications** > **Providers** and open the Entra ID provider that you previously created.
7. Under **Attribute mapping**, remove the `authentik default Microsoft Entra Mapping: User` property mapping and add the property mapping that you just created.
8. Click **Update**.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/entra/configure-entra.md
================================================================================

---
title: Configure Entra ID
authentik_enterprise: true
---

For more information about using an Entra ID provider, see the [Entra ID Overview](./index.md) documentation.

Your Entra ID tenant must be configured before you [create a Entra ID provider](./create-entra-provider.md).

This involves creating an app registration, generating a secret, and configuring the required API permissions.

:::warning Email domains
When the default `authentik default Microsoft Entra Mapping: User` property mapping is used, authentik checks whether each user's email domain is verified in your Entra ID tenant.

In which case, you must configure each user's email domain as a [verified custom domain in Entra ID](https://learn.microsoft.com/en-us/entra/identity/users/domains-manage#add-custom-domain-names-to-your-microsoft-entra-organization); otherwise, provisioning fails. The tenant's default `onmicrosoft.com` domain (e.g., `@<tenant name>.onmicrosoft.com`), is considered a verified domain.

Alternatively, if you need to provision users with email domains that you don't control, refer to [Email handling](./create-entra-provider.md#email-handling) for more information.
:::

## Configuring you Entra ID tenant

1. Log in to the [Entra ID admin center](https://entra.microsoft.com).
2. Navigate to **App registrations**, click **New registration**, and set the following configurations:
    - Provide a **Name** for the app registration (e.g. `authentik Entra Provider`)
    - Under **Supported account types**, select **Accounts in this organizational directory only**
    - Leave **Redirect URI** empty
3. Click **Register**.
4. On the app detail page, take note of the **Application (client) ID** and **Directory (tenant) ID**. These values will be required when you [create the Entra ID provider](./create-entra-provider.md) in authentik.
5. Next, in the near-left navigation pane, click on **Certificates and Secrets**.
6. On the **Client secrets** tab, click **New client secret** and set the following configuration:
    - Provide a **Description** for the client secret
    - Set an expiry period for the secret. Please note that you will need to rotate the secret value in Entra ID and authentik upon expiry.
7. Click **Add**.
8. The **Value** of the client secret is shown only once. Take note of the value as it will be required when you [create the Entra ID provider](./create-entra-provider.md) in authentik.
9. Next, in the near-left navigation pane, click on **API permissions**.
10. Click **Add a permission** and select **Microsoft Graph** as the API.
11. Select **Application permissions** as the permission type and assign the following permissions:
    - `Group.Create`
    - `Group.ReadWrite.All`
    - `GroupMember.ReadWrite.All`
    - `User.ReadWrite.All`
12. Click **Add permissions**.
13. Under **Configured permissions**, click **Grant admin consent for default directory**.

Now that you have configured your Entra ID tenant, you are ready to [create an Entra ID provider](./create-entra-provider.md).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/single-logout/index.md
================================================================================

---
title: Single Logout (SLO)
authentik_version: "2025.10.0"
---

Single Logout (SLO) is a security feature that logs users out of all active applications when they log out of authentik. It uses the OAuth2/OpenID Connect front-channel and back-channel logout specifications in combination with SAML's Single Logout specification.

For example, if a user is concurrently logged into an OIDC application and two SAML applications, when the user logs out of authentik, they will automatically be logged out of all three applications. Without SLO configured, users with active sessions across multiple applications would need to manually log out of each one.

:::info
Check with your service provider to see if they support SAML Single Logout or OIDC front-channel/back-channel logout. Not all service providers support these features.
:::

## When Single Logout is triggered

Single Logout behavior depends on where the user initiates logout:

- **Logout from authentik**: When a user logs out directly from authentik, the `default-invalidation-flow` runs. This flow includes a [User Logout stage](../../flows-stages/stages/user_logout.md) that ends the user's authentik session and triggers Single Logout for all connected applications.

- **Logout from an application**: When a user logs out from an OIDC or SAML application, the `default-provider-invalidation-flow` runs. By default, this flow does **not** include a User Logout stage, so only that application's session is ended while the user's authentik session and other application sessions remain active.

For instructions on how to enable full Single Logout when a user logs out from an application, see [Enable full Single Logout for RP-initiated logout](#enable-full-single-logout-for-rp-initiated-logout) below.

## How Single Logout works in authentik

When a user logs out or their session is terminated in authentik, the following process occurs:

1. **Session Termination**: The user's session ends through one of the following:
    - User-initiated logout via a logout flow
    - Administrative action (session deletion or user deactivation)
    - Token revocation or expiration
2. **Provider Identification**: authentik identifies all OAuth2/OIDC and SAML providers with active sessions for the users who have SLO configured.
3. **Logout Request Dispatch**:
    - **Back-channel**: HTTP POST requests are sent directly from the authentik server to each back-channel provider's configured logout endpoint.
    - **Front-channel**: For user-initiated logouts, a logout stage is automatically injected into the flow that handles browser-based logout (typically via iframes or sequential redirects).
4. **Provider Processing**: Each provider processes the logout request, validates it, and terminates the user's active session.
5. **Completion**: After all providers have been notified, the user is redirected back to the authentik login screen.

## Front-channel vs. back-channel logout

authentik supports both front-channel (browser-based) and back-channel (server-to-server) logout methods, depending on how each provider is configured.

### Front-channel logout

Front-channel logout sends logout requests through the user's browser. authentik supports two front-channel modes:

#### iframe mode (default for OIDC)

- Loads all provider logout URLs simultaneously in hidden iframes
- Provides fast, parallel logout across multiple providers
- Required by the OIDC front-channel logout specification
- Most SAML providers also support iframe-based logout

#### Native Mode (SAML Only)

- Uses the active browser tab to chain redirects and POST requests sequentially
- Provides better compatibility with SAML providers that have iframe restrictions
- Each provider redirects the user back to authentik before proceeding to the next provider
- Not available for OIDC providers as the specification requires iframe support

:::info
Use native front-channel mode for SAML providers if you encounter iframe compatibility issues, such as Content Security Policy (CSP) restrictions or cookie handling problems.
:::

### Back-channel Logout

Back-channel logout sends logout requests directly from the authentik server to each provider's logout endpoint via HTTP POST.

- Does not require user browser interaction
- Works even when the user is offline or their browser is closed
- Is automatically triggered by administrators terminating a user session (user deactivation or session deletion)
- Requires the provider to accept server-to-server POST requests

**For SAML**: Requires POST SLS binding.
**For OIDC**: Requires a `logout_uri` configured for back-channel that accepts logout tokens.

## Enable full Single Logout for RP-initiated Logout

By default, when a user logs out from an application (RP-initiated logout), only that application's session is ended. To enable full Single Logout that also ends the user's authentik session and logs them out of all applications, add a User Logout stage to the `default-provider-invalidation-flow`:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Flows**.
3. Click `default-provider-invalidation-flow` to open the flow.
4. Click the **Stage Bindings** tab.
5. Click **Bind Existing Stage**.
6. In the **Stage** dropdown, select `default-invalidation-logout`.
7. Click **Create**.

After this change, when users log out from any application, they will be logged out of authentik and all other connected applications.

## Configure per-provider logout behavior

If you need different logout behaviors for different applications, you can create custom invalidation flows and assign them to specific providers:

1. Create a new flow with the **Invalidation** designation.
2. Add stages as needed:
    - Include a [User Logout stage](../../flows-stages/stages/user_logout.md) if you want full Single Logout.
    - Omit the User Logout stage if you only want to end the specific application session.
3. When configuring a provider, select your custom flow in the **Invalidation flow** field.

This allows you to configure full Single Logout only for sensitive applications while keeping the default behavior for others.

## Enable Single Logout

Enabling single logout requires configuring logout endpoints on your SAML or OIDC providers in authentik.

### SAML Providers

See the [SAML Single Logout documentation](../saml/saml_single_logout.md) for detailed instructions. You will need to:

1. Configure the **SLS URL** (Single Logout Service URL) - the provider's logout endpoint
2. Select the **SLS Binding** (Redirect or POST)
3. Choose a **Logout Method**; front-channel iframe, front-channel native, or back-channel
4. Optionally, enable **Sign Logout Request** for additional security

### OIDC providers

See the [OIDC Front-channel and Back-channel logout documentation](../oauth2/frontchannel_and_backchannel_logout.mdx) for detailed instructions. You will need to:

1. Configure the **logout URI** - the provider's logout endpoint
2. Enable the desired **Logout Method**; front-channel or back-channel
3. Optionally configure logout token signing for back-channel requests

## Session tracking

authentik tracks provider sessions to enable single logout:

- **SAML**: Creates `SAMLSession` records containing the `SessionIndex`, `NameID`, and `NameID format` for each successful authentication.
- **OIDC**: Tracks session identifiers (`sid`) and ID tokens required for logout requests.

These session records are automatically created during authentication and deleted after logout or expiration.

## Administrative session termination

Back-channel logout is always triggered when a user session is terminated via administrative actions:

- **Session Deletion**: When an administrator manually deletes a user's session through the Admin interface or API, authentik sends back-channel logout requests to all configured providers.
- **User Deactivation**: When a user account is deactivated, authentik automatically sends back-channel logout requests to terminate all active sessions across all providers.

These requests are processed asynchronously to avoid blocking administrative operations.

## Resources

- [SAML Single Logout](../saml/saml_single_logout.md)
- [OIDC Front-channel and Back-channel Logout](../oauth2/frontchannel_and_backchannel_logout.mdx)
- [User Logout Stage](../../flows-stages/stages/user_logout.md)
- [SAML Profiles 2.0 Specification](https://docs.oasis-open.org/security/saml/v2.0/saml-profiles-2.0-os.pdf)
- [OpenID Connect Front-Channel Logout 1.0](https://openid.net/specs/openid-connect-frontchannel-1_0.html)
- [OpenID Connect Back-Channel Logout 1.0](https://openid.net/specs/openid-connect-backchannel-1_0.html)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/wsfed/create-wsfed-provider.md
================================================================================

---
title: Create a WS-Federation provider
---

An authentik WS-Federation provider is typically created as part of an application/provider pair, using the steps below. You can also create a standalone provider, and then later assign an application to use it.

## Create a WS-Federation provider and application pair

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications > Applications** and click **Create with provider** to create an application and provider pair.
3. On the **New application** page, define the application details, and then click **Next**.
4. Select **WS-Federation Provider** as the **Provider Type**, and then click **Next**.
5. On the **Configure WS-Federation Provider** page, provide a name for the provider, select an authorization flow, and the two required configuration settings:
    - **Reply URL**: Enter the application callback URL, where the token should be sent. This is the specific endpoint on an RP (application) where an Identity Provider (STS) sends the security token and authentication response after a successful log in.
    - **Realm**: Enter the identifier (string) of the requesting realm; that is, the Relying Party (RP) or application receiving the token. Realm is similar to the SAML 2.0 Entity ID.
6. Click **Submit** to create both the application and the provider.

## Export authentik WS-Federation provider metadata

After an authentik WS-Federation provider has been created via any of the above methods, you can access its metadata in one of two ways:

### Download authentik metadata for a WS-Federation provider

To download the metadata of an authentik WS-Federation provider, follow these steps:

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications > Providers**.
3. Click the name of the provider you want metadata for.
4. On the **Overview** tab, in the **Related objects** section, click on **Download** under **Metadata**. This will download the metadata XML file for that provider.

### Access the Metadata tab for a WS-Federation provider

To view and optionally download the metadata of an authentik WS-Federation provider, follow these steps:

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications > Providers**.
3. Click the name of the provider you want metadata for, and then click the **Metadata** tab.
4. The metadata for the provider will be shown in a code box. You can optionally use the **Download** button to obtain the metadata as a file.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/wsfed/index.md
================================================================================

---
title: WS-Federation Provider
---

The WS-Federation provider is used to integrate with applications and service providers that use [WS-Federation protocol](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-adfsod/204de335-ea34-4f9b-ae73-8b7d4c8152d1). WS-Federation is an XML-based identity federation protocol that uses token exchange for federated Single Sign-On (SSO) and IdP authentication, specifically for Windows applications such as SharePoint.

There are similarities between WS-Federation and SAML protocols, but there are several key differences in terminology, most importantly:

- WS-Federation term: **STS (Security Token Service)**
- SAML term: **IdP (Identity Provider)**

:::info SAML2 token support
Note that we only support the SAML2 token type within WS-Federation providers, and that using the WS-Federation provider with Entra ID is not supported because Entra ID requires a SAML 1.0 token.
:::

## Supported URL request parameters

The following URL request parameters are supported in the authentik WS-Federation provider:

- **`wa`**: This is a required parameter that represents the action being requested, typically `wsignin1.0` for signing in. The parameter's value tells the Security Token Service (STS) which operation to execute.
- **`wtrealm`**: The unique identifier (realm) of the Relying Party (RP) or application requesting the security token, for example, urn:my-app:rp. It defines the trust relationship between the RP and the Identity Provider (IdP) and indicates which application is initiating the WS-Federation request. This is a required query parameter that tells the Security Token Service (STS) which relying party the token is intended for.
- **`wreply`**: The target URL to which the Identity Provider (IdP) sends the WS-Federation response containing the security token. This URL is supplied by the Service Provider (SP). authentik verifies that the received `wreply` parameter matches the URL configured by the administrator and stored in the database.
- **`wctx`**: A context value that is used to maintain state between the Relying Party (RP) and the Identity Provider (IdP) across redirects. It serves the same purpose as the `RelayState` parameter in SAML. The RP includes this value in the authentication request, and the IdP returns it unchanged in the response, allowing the RP to validate and restore the original session or request context.

## WS-Federation bindings and endpoints

_Bindings_ define how an Identity Provider (IdP) and the WS-Federation STS (Security Token Service), or IdP in SAML terms, communicate; how messages are transported over network protocols, specifying transport (like HTTP), encoding, and security detail that allow WS-Federation to facilitate secure identity sharing across systems. Both the IdP and STS define various endpoints in their metadata, each associated with a specific WS-Federation binding.

| Endpoint | URL                   |
| -------- | --------------------- |
| SSO/SLO  | `/application/wsfed/` |

## WS-Federation metadata

Using metadata ensures that WS-Federation single sign-on works reliably by exchanging and maintaining identity and connection information. WS-Federation metadata is an XML document that defines how IdPs and SPs securely interact for authentication. It includes information such as endpoints, bindings, certificates, and unique identifiers. The metadata is what you provide the application to configure it for authenticating with authentik.

You can [export WS-Federation metadata](./create-wsfed-provider.md#export-authentik-ws-federation-provider-metadata) from an authentik WS-Federation provider to an STS to automatically provide important endpoint and certificate information to the SP.

## Certificates

The certificates used with WS-Federation to sign Request Security Token Response (RSTR), which contains the assertion, are the same certificates that are used by SAML.

For details, refer to our [SAML certificates documentation](../saml/index.md#certificates).

## WS-Federation property mappings

Property mappings are used during the authentication process to align, or "map", user attributes values between the SP and STS (Security Token Service), the latter being the equivalent of SAML's IdP.

The same property mappings that are used in WS-Federation are used in SAML. For details, refer to our [SAML property mapping documentation](../saml/index.md#certificates).

## Attributes for WS-Federation

WS-Federation and SAML also share the use of the [NameID](../saml/index.md#nameid) and the [AuthnContextClassRef](../saml/index.md#authncontextclassref) attributes.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/rac/rac_credentials_prompt.md
================================================================================

---
title: RAC Credentials Prompt
---

## About the RAC credentials prompt

You can configure the RAC provider to prompt users for their credentials when connecting to RAC endpoints. This is particularly useful for establishing RDP connections to modern Windows systems that often require credentials to establish a connection.

After implementing this configuration, when connecting to an RAC endpoint users are prompted to enter their credentials which are then passed to the RAC endpoint. This means that static credentials do not need to be set in the RAC provider, property mapping, or endpoint.

This configurations requires:

1. Creating an authorization flow.
2. Creating two prompts.
3. Creating and binding a prompt stage.
4. Updating the RAC provider.

## Create a new authorization flow

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Flows**, click **Create**, and enter the following required settings:
    - **Name**: Enter a descriptive name for the flow.
    - **Title**: Enter a title for the flow. This will be displayed to users when they're prompted for their credentials.
    - **Slug**: Enter a slug for the flow. This will be displayed in the flow URL.
    - **Designation**: `Authorization`
    - **Authentication**: `Require authentication`
3. Click **Create**.

## Create prompts

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Prompts**, click **Create**, and enter the following required settings:
    - **Name**: Enter a descriptive name for the prompt (e.g. `username`).
    - **Field Key**: `connection_settings.username`
    - **Label**: Enter a label for the field which will be displayed above it.
    - **Type**: `Text`
    - **Required**: Toggled on.
    - **Order**: `0`
3. Click **Create** to save the prompt.
4. On the **Prompts** page, click **Create** again, and enter the following required settings:
    - **Name**: Enter a descriptive name for the prompt (e.g. `password`).
    - **Field Key**: `connection_settings.password`
    - **Label**: Enter a label for the field which will be displayed above it.
    - **Type**: `Password`
    - **Required**: Toggled.
    - **Order**: `1`
5. Click **Create** to save the prompt.

:::info
You can optionally add other prompt fields such as `domain` (e.g. `connection_settings.domain`), which can be useful for Windows based RDP. There is also the option of adding a `Text (read-only)` type prompt field that includes explanatory text for the user (e.g. `please enter your RDP credentials`).
:::

## Create and bind a prompt stage

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Flows**.
3. Click the name of the newly created authorization flow.
4. Click on **Stage bindings**, click **Create and bind stage**, and enter the following required settings:
    - **Select Type**: Select `Prompt stage` as the prompt type.
    - **Create Prompt Stage**:
        - **Name**: Enter a name for the prompt stage.
        - Under **Fields**:
            - Click the **x** icon to remove all selected fields.
            - Add the two newly created prompt fields (e.g.`username` and `password`) to selected fields.
        - Under **Validation Policies**:
            - Click the **x** icon to remove all selected validation policies.
    - **Create binding**:
        - Click **Finish**.

## Update the RAC provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers**.
3. Click the **Edit** icon of the RAC provider that you wish to add a credentials prompt to.
4. Change **Authorization flow** to the newly created authorization flow.
5. Click **Update** to save the change.

## Update the RAC endpoint _(sometimes required)_

Depending on the configuration of the RDP server that's being connected to, it is sometimes necessary to set the security type that's used for the connection. For many modern windows RDP servers, this often needs to be set to `tls`.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click the name of the RAC provider that you're using.
3. Under **Endpoints**, click the **Edit** icon of the endpoint that you're using.
4. Under **Advanced Settings** in the **Settings** box, enter `security: tls`
5. Click **Update** to save the change.

:::info
Other options for the connection security type are: `any`, `nla`, `nla-ext`, `vmconnect`, and `rdp`. For more information see the [Guacamole RDP Authentication and Security Documentation](https://guacamole.apache.org/doc/gug/configuring-guacamole.html#authentication-and-security).
:::

## Configuration verification

Log in to authentik with a user account that has the required privileges to access the RAC application. Open the User interface, and on the **My applications** page click the RAC application. You should then be redirected to the prompt stage and prompted for a username and password. Enter the credentials for the RAC endpoint and if the credentials are valid the RDP/SSH/VNC connection should be established.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/rac/index.md
================================================================================

---
title: Remote Access Control (RAC) Provider
---

The RAC provider allows users to access remote Windows, macOS, and Linux machines via [RDP](https://en.wikipedia.org/wiki/Remote_Desktop_Protocol)/[SSH](https://en.wikipedia.org/wiki/Secure_Shell)/[VNC](https://en.wikipedia.org/wiki/Virtual_Network_Computing). Just like other providers in authentik, the RAC provider is associated with an application that appears on a user's **My applications** page.

For instructions on creating a RAC provider, refer to the [Create a Remote Access Control (RAC) provider](./create-rac-provider.md) documentation. Alternatively, watch our ["Remote Access Control (RAC) in authentik" video on YouTube](https://www.youtube.com/watch?v=9wahIBRV6Ts).

## RAC components

A RAC provider uses several components:

```mermaid
architecture-beta
    service application(mdi:application-outline)[Application]
    service provider(mdi:application-cog-outline)[Provider]
    service endpoint(mdi:network-pos)[Endpoint Settings]
    service server(mdi:server)[authentik Server]
    service outpost(mdi:server-plus)[RAC Outpost]

    service machine(mdi:desktop-classic)[Remote Machine]

    application:R --> L:provider
    provider:B -- T:endpoint
    provider:R --> L:server
    server:R <--> L:outpost
    outpost:B <--> T:machine
```

When a user starts the RAC application, it communicates with the authentik server, which then connects to the RAC outpost and sends instructions (based on the endpoint data you defined) on how to connect to the remote machine.

After connecting to the remote machine, the outpost sends a message back to the authentik server (via WebSockets), and the web browser opens the WebSocket connection to the remote machine.

## Endpoints

Unlike other providers, where an application-provider pair is created for each resource you wish to access, RAC works differently. RAC uses a single application connected to one RAC provider. The RAC provider then has an _Endpoint_ object for each remote machine (computer/server) you want to connect to.

The _Endpoint_ object specifies:

- Hostname, IP address, and port of the remote machine
- Protocol to use: SSH, RDP, or VNC
- RDP connection settings
- [RAC Property mappings](#rac-property-mappings) to apply
- [Connection settings](#connection-settings) to apply

Additionally, it is possible to bind policies to _Endpoint_ objects to restrict user access. To connect to a remote machine, users must have access to both the application that the RAC provider is using and the corresponding endpoint.

## Connection management

A new connection is created every time an RAC application/endpoint is selected in the [User Interface](../../../customize/interfaces/user). After the user's authentik session expires, the connection is terminated. Additionally, you can configure connection expiry in the RAC provider, which applies even if the user is still authenticated. The connection can also be terminated manually from the **Connections** tab of the RAC provider.

## RAC Property Mappings

You can create RAC property mappings via **Customization** > **Property Mappings**.

RAC property mappings allow you to configure the following settings:

- **Username**: the username for the remote machine
- **Password**: the password for the remote machine
- **Ignore Server certificate**: set whether the validity of the returned RDP server certificate will be ignored
- **Enable wallpaper**: enable/disable the desktop wallpaper of the RDP server
- **Enable font-smoothing**: enable/disable font-smoothing (anti-aliasing) on the RDP server
- **Enable full window dragging**: enable/disable whether the full content of a window is visible while moving it on the RDP server
- **Advanced settings**: set [connection settings](#connection-settings) via a Python expression

## Connection settings

The RAC provider utilizes [Apache Guacamole](https://guacamole.apache.org/) for establishing SSH, RDP and VNC connections. RAC supports the use of Apache Guacamole connection configurations.

Connection settings can include `username`, `password`, `domain`, `private-key`, `security`, `enable-audio`, and more.

For a full list of possible connection settings, see the [Apache Guacamole connection configuration documentation](https://guacamole.apache.org/doc/gug/configuring-guacamole.html#configuring-connections).

RAC connection settings can be set via several methods and are all merged together when connecting:

1. Default settings
2. RAC Provider settings
3. RAC Endpoint settings
4. RAC Provider property mapping settings
5. RAC Endpoint property mapping settings
6. The `connection_settings` object in the flow plan

For examples of how to configure connection settings, see the [RAC SSH public key authentication](./rac-public-key.md) and [RAC Credentials Prompt](./rac_credentials_prompt.md) documentation.

## Capabilities

The following features are currently supported:

- Bi-directional clipboard
- Audio redirection (from remote machine to browser)
- Resizing



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/rac/create-rac-provider.md
================================================================================

---
title: Create a Remote Access Control (RAC) provider
---

For an overview of Remote Access Control (RAC), see the [RAC provider](./index.md) documentation.

You can also watch our video on YouTube for setting up RAC:



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/rac/rac-public-key.md
================================================================================

---
title: RAC SSH Public Key Authentication
---

## About RAC SSH public key authentication

The RAC provider supports SSH public key authentication. This allows for secure connections to SSH endpoints without the use of passwords.

SSH private keys can be configured via several methods:

## Apply a private key to an RAC provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers**.
3. Click the **Edit** icon on the RAC provider that requires public key authentication.
4. In the **Settings** codebox enter the private key of the endpoint, for example:
    ```yaml
    private-key: |
        REDACTED_TEST_PRIVATE_KEY
    ```
5. Click **Update**.

:::info
The pipe character (`|`) is required to preserve linebreaks in the YAML text. See the [YAML spec](https://yaml.org/spec/1.2.2/#literal-style) for more information.
:::

## Apply a private key to an RAC endpoint

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers**.
3. Click the name of the RAC provider that the endpoint belongs to.
4. Under **Endpoints**, click on the **Edit** icon next to the endpoint that requires public key authentication.
5. Under **Advanced settings**, in the **Settings** codebox enter the private key of the endpoint:
    ```yaml
    private-key: |
        REDACTED_TEST_PRIVATE_KEY
    ```
6. Click **Update**.

:::info
The pipe character (`|`) is required to preserve linebreaks in the YAML text. See the [YAML spec](https://yaml.org/spec/1.2.2/#literal-style) for more information.
:::

## Apply a private key to an RAC property mapping

1.  Log in to authentik as an administrator and open the authentik Admin interface.
2.  Navigate to **Customization** > **Property Mappings** and click **Create**, then create a **RAC Provider Property Mapping** with the following settings:
    - **Name**: Choose a descriptive name
    - Under **Advanced Settings**:
        - **Expression**:

    ```python

    private_key = textwrap.dedent("""
    REDACTED_TEST_PRIVATE_KEY
    """)

    return {
        "username": "<your_username>",
        "private-key": private_key
    }
    ```

3.  Click **Finish**.
4.  Navigate to **Applications** > **Providers**.
5.  Click the **Edit** icon on the RAC provider that requires public key authentication.
6.  Under **Protocol Settings** add the newly created property mapping to **Selected Property Mappings**.
7.  Click **Update**.

## Retrieve a private key from a user's attributes and apply it to an RAC property mapping

1.  Log in to authentik as an administrator and open the authentik Admin interface.
2.  Navigate to **Customization** > **Property Mappings** and click **Create**. Create a **RAC Provider Property Mapping** with the following settings:
    - **Name**: Choose a descriptive name
    - Under **Advanced Settings**:
        - **Expression**:
        ```python
        return {
        "private-key": request.user.attributes.get("<private-key-attribute-name>", "default"),
        }
        ```

3.  Click **Finish**.
4.  Navigate to **Applications** > **Providers**.
5.  Click the **Edit** icon on the RAC provider that requires public key authentication.
6.  Under **Protocol Settings**, add the newly created property mapping to **Selected Property Mappings**.
7.  Click **Update**.

:::info
For group attributes, the following expression can be used `request.user.group_attributes(request.http_request)`.
:::



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/radius/index.mdx
================================================================================

---
title: RADIUS Provider
---


You can configure a Radius provider for applications that don't support any other protocols or that require Radius.

:::info
This provider requires the deployment of a [RADIUS outpost](../../outposts/index.mdx).
:::

Currently, only authentication requests are supported.

### Authentication flow

Authentication requests against the Radius Server use a flow in the background. This allows you to use the same flows, stages, and policies as you do for web-based logins.

The following stages are supported:

    - [Identification](../../flows-stages/stages/identification/index.mdx)
    - [Password](../../flows-stages/stages/password/index.md)
    - [Authenticator validation](../../flows-stages/stages/authenticator_validate/index.mdx)

    :::info
    Authenticator validation currently only supports DUO, TOTP, and static authenticator.
    :::

    For code-based authenticators, the code must be given as part of the bind password, separated by a semicolon. For example for the password `example-password` and the MFA token `123456`, the input must be `example-password;123456`.

    SMS-based authenticators are not supported because they require a code to be sent from authentik, which is not possible during the bind.

- [User Logout](../../flows-stages/stages/user_logout.md)
- [User Login](../../flows-stages/stages/user_login/index.md)
- [Deny](../../flows-stages/stages/deny.md)
- [Mutual TLS stage](../../flows-stages/stages/mtls/index.md)

### Protocol support

The RADIUS provider supports EAP-TLS and [PAP](https://en.wikipedia.org/wiki/Password_Authentication_Protocol) (Password Authentication Protocol) protocol. For password-based authentication, only PAP protocol is supported due to other password hashing methods requiring reversible password hashes, which we don’t support for security reasons.


### EAP :ak-enterprise :ak-version[2025.10]

authentik supports EAP with TLS as the inner protocol, between the application and transport layers to encrypt and secure communications. To set this up, a certificate authority needs to be available and client certificates need to be installed on machines, the configuration of which is outside of the scope of this document.

#### EAP-TLS

Create an authentication flow with a [Mutual TLS stage](../../flows-stages/stages/mtls/index.md) as its first stage. This stage should be configured to use your CA's certificate. Afterwards a server certificate needs to be selected in the RADIUS provider (which serves as an outpost). Then, configure your RADIUS provider to use this authentication flow to enable EAP-TLS authentication. After the certificate and the authentication flow are configured in the provider, authentication via EAP-TLS is possible.

For certificates, ensure that you use a client certificate and a server certificate that are created by a certificate authority, not a self-generated certificate.

:::warning Use of trusted Certificate Authority

For EAP-TLS, note that you should NOT use a globally known CA.

Using private PKI certificates that are trusted by the end-device is best practice. For example, using a Verisign certificate as a "known CA" means that ANYONE who has a certificate signed by them can authenticate via EAP-TLS, and in addition you should implement [custom validation](../../flows-stages/flow/context/index.mdx#auth_method-string) to prevent unauthorized access.
:::

### RADIUS attributes

Starting with authentik 2024.8, you can create RADIUS provider property mappings, which make it possible to add custom attributes to the RADIUS response packets.

For example, to add the Cisco AV-Pair attribute, this snippet can be used:

```python
define_attribute(
    vendor_code=9,
    vendor_name="Cisco",
    attribute_name="AV-Pair",
    attribute_code=1,
    attribute_type="string",
)
packet["Cisco-AV-Pair"] = "shell:priv-lvl=15"
return packet
```

After creation, make sure to select the RADIUS property mapping in the RADIUS provider.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/proxy/_caddy_standalone.md
================================================================================

Use the following configuration:

```apacheconf
app.company {
    # directive execution order is only as stated if enclosed with route.
    route {
        # always forward outpost path to actual outpost
        reverse_proxy /outpost.goauthentik.io/* http://outpost.company:9000

        # forward authentication to outpost
        forward_auth http://outpost.company:9000 {
            uri /outpost.goauthentik.io/auth/caddy

            # capitalization of the headers is important, otherwise they will be empty
            copy_headers X-Authentik-Username X-Authentik-Groups X-Authentik-Entitlements X-Authentik-Email X-Authentik-Name X-Authentik-Uid X-Authentik-Jwt X-Authentik-Meta-Jwks X-Authentik-Meta-Outpost X-Authentik-Meta-Provider X-Authentik-Meta-App X-Authentik-Meta-Version

            # optional, in this config trust all private ranges, should probably be set to the outposts IP
            trusted_proxies private_ranges
        }

        # actual site configuration below, for example
        reverse_proxy localhost:1234
    }
}
```

If you're trying to proxy to an upstream over HTTPS, you need to set the `Host` header to the value they expect for it to work correctly.

```conf
reverse_proxy /outpost.goauthentik.io/* https://outpost.company {
    header_up Host {http.reverse_proxy.upstream.host}
}
```



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/proxy/_traefik_compose.md
================================================================================

```yaml
services:
    traefik:
        image: traefik:v3.0
        container_name: traefik
        volumes:
            - /var/run/docker.sock:/var/run/docker.sock
        ports:
            - 80:80
        command:
            - "--api"
            - "--providers.docker=true"
            - "--providers.docker.exposedByDefault=false"
            - "--entrypoints.web.address=:80"

    authentik-proxy:
        image: ghcr.io/goauthentik/proxy
        ports:
            - 9000:9000
            - 9443:9443
        environment:
            AUTHENTIK_HOST: https://your-authentik.tld
            AUTHENTIK_INSECURE: "false"
            AUTHENTIK_TOKEN: token-generated-by-authentik
            # Starting with 2021.9, you can optionally set this too
            # when authentik_host for internal communication doesn't match the public URL
            # AUTHENTIK_HOST_BROWSER: https://external-domain.tld
        labels:
            traefik.enable: true
            traefik.port: 9000
            traefik.http.routers.authentik.rule: Host(`app.company`) && PathPrefix(`/outpost.goauthentik.io/`)
            # `authentik-proxy` refers to the service name in the compose file.
            traefik.http.middlewares.authentik.forwardauth.address: http://authentik-proxy:9000/outpost.goauthentik.io/auth/traefik
            traefik.http.middlewares.authentik.forwardauth.trustForwardHeader: true
            traefik.http.middlewares.authentik.forwardauth.authResponseHeaders: X-authentik-username,X-authentik-groups,X-authentik-entitlements,X-authentik-email,X-authentik-name,X-authentik-uid,X-authentik-jwt,X-authentik-meta-jwks,X-authentik-meta-outpost,X-authentik-meta-provider,X-authentik-meta-app,X-authentik-meta-version
        restart: unless-stopped

    whoami:
        image: containous/whoami
        labels:
            traefik.enable: true
            traefik.http.routers.whoami.rule: Host(`app.company`)
            traefik.http.routers.whoami.middlewares: authentik@docker
        restart: unless-stopped
```



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/proxy/_traefik_ingress.md
================================================================================

Create a middleware:

```yaml
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
    name: authentik
spec:
    forwardAuth:
        # This address should point to the cluster endpoint provided by the kubernetes service, not the Ingress.
        address: http://outpost.company:9000/outpost.goauthentik.io/auth/traefik
        trustForwardHeader: true
        authResponseHeaders:
            - X-authentik-username
            - X-authentik-groups
            - X-authentik-entitlements
            - X-authentik-email
            - X-authentik-name
            - X-authentik-uid
            - X-authentik-jwt
            - X-authentik-meta-jwks
            - X-authentik-meta-outpost
            - X-authentik-meta-provider
            - X-authentik-meta-app
            - X-authentik-meta-version
```

:::info
Traefik changed the apiVersion of the middleware CRD in version 3.0, for older versions please substitute "apiVersion: traefik.containo.us/v1alpha1"
:::

Add the following settings to your IngressRoute

By default traefik does not allow cross-namespace references for middlewares:

See [here](https://doc.traefik.io/traefik/v2.4/providers/kubernetes-crd/#allowcrossnamespace) to enable it.

```yaml
spec:
    routes:
        - kind: Rule
          match: "Host(`app.company`)"
          middlewares:
              - name: authentik
                namespace: authentik
          priority: 10
          services: # Unchanged
        # This part is only required for single-app setups
        - kind: Rule
          match: "Host(`app.company`) && PathPrefix(`/outpost.goauthentik.io/`)"
          priority: 15
          services:
              - kind: Service
                # Or, to use an external Outpost, create an ExternalName service and reference that here.
                # See https://kubernetes.io/docs/concepts/services-networking/service/#externalname
                name: ak-outpost-example-outpost
                port: 9000
```



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/proxy/forward_auth.mdx
================================================================================

---
title: Forward auth
---

Using forward auth uses your existing reverse proxy to do the proxying, and only uses the authentik outpost to check authentication and authorization.

To use forward auth instead of proxying, you have to change a couple of settings.
In the Proxy Provider, make sure to use one of the Forward auth modes.

## Forward auth modes

The only configuration difference between single application mode and domain level mode is the host that you specify.

For single application, you'd use the domain that the application is running on, and only `/outpost.goauthentik.io` is redirected to the outpost.

For domain level, you'd use the same domain as authentik.

### Single application

Single application mode works for a single application hosted on its dedicated subdomain. This lets you keep per-application access policies in authentik.

### Domain level

To use forward auth instead of proxying, you have to change a couple of settings.
In the Proxy Provider, make sure to use the _Forward auth (domain level)_ mode.

This mode differs from the _Forward auth (single application)_ mode in the following points:

- You don't have to configure an application in authentik for each domain
- Users don't have to authorize multiple times

There are, however, also some downsides, mainly the fact that you **can't** restrict individual applications to different users.

## Configuration templates

For configuration templates for each web server, refer to the following:





================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/proxy/_nginx_ingress.md
================================================================================

Create a new ingress for the outpost

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
    name: authentik-outpost
spec:
    rules:
        - host: app.company
          http:
              paths:
                  - path: /outpost.goauthentik.io
                    pathType: Prefix
                    backend:
                        # Or, to use an external Outpost, create an ExternalName service and reference that here.
                        # See https://kubernetes.io/docs/concepts/services-networking/service/#externalname
                        service:
                            name: ak-outpost-example-outpost
                            port:
                                number: 9000
```

This ingress handles authentication requests, and the sign-in flow.

Add these annotations to the ingress you want to protect

:::warning
This configuration requires that you enable [`allow-snippet-annotations`](https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/configmap/#allow-snippet-annotations), for example by setting `controller.allowSnippetAnnotations` to `true` in your helm values for the ingress-nginx installation.
:::

```yaml
metadata:
    annotations:
        # This should be the in-cluster DNS name for the authentik outpost service
        # as when the external URL is specified here, nginx will overwrite some crucial headers
        nginx.ingress.kubernetes.io/auth-url: |-
            http://ak-outpost-example.authentik.svc.cluster.local:9000/outpost.goauthentik.io/auth/nginx
        # If you're using domain-level auth, use the authentication URL instead of the application URL
        nginx.ingress.kubernetes.io/auth-signin: |-
            https://app.company/outpost.goauthentik.io/start?rd=$scheme://$http_host$escaped_request_uri
        nginx.ingress.kubernetes.io/auth-response-headers: |-
            Set-Cookie,X-authentik-username,X-authentik-groups,X-authentik-entitlements,X-authentik-email,X-authentik-name,X-authentik-uid
        nginx.ingress.kubernetes.io/auth-snippet: |
            proxy_set_header X-Forwarded-Host $http_host;
```



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/proxy/server_caddy.mdx
================================================================================

---
title: Caddy
---



The configuration template shown below apply to both single-application and domain-level forward auth.





================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/proxy/_traefik_standalone.md
================================================================================

```yaml
http:
    middlewares:
        authentik:
            forwardAuth:
                address: http://outpost.company:9000/outpost.goauthentik.io/auth/traefik
                trustForwardHeader: true
                authResponseHeaders:
                    - X-authentik-username
                    - X-authentik-groups
                    - X-authentik-entitlements
                    - X-authentik-email
                    - X-authentik-name
                    - X-authentik-uid
                    - X-authentik-jwt
                    - X-authentik-meta-jwks
                    - X-authentik-meta-outpost
                    - X-authentik-meta-provider
                    - X-authentik-meta-app
                    - X-authentik-meta-version
    routers:
        default-router:
            rule: "Host(`app.company`)"
            middlewares:
                - authentik
            priority: 10
            service: app
        default-router-auth:
            rule: "Host(`app.company`) && PathPrefix(`/outpost.goauthentik.io/`)"
            priority: 15
            service: authentik
    services:
        app:
            loadBalancer:
                servers:
                    - url: http://ip.internal
        authentik:
            loadBalancer:
                servers:
                    - url: http://outpost.company:9000/outpost.goauthentik.io
```



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/proxy/_envoy_istio.md
================================================================================

Set the following settings on the _IstioOperator_ resource:

```yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
    name: istio
    namespace: istio-system
spec:
    meshConfig:
        extensionProviders:
            - name: "authentik"
              envoyExtAuthzHttp:
                  # Replace with <service-name>.<namespace>.svc.cluster.local
                  service: "ak-outpost-authentik-embedded-outpost.authentik.svc.cluster.local"
                  port: "9000"
                  pathPrefix: "/outpost.goauthentik.io/auth/envoy"
                  headersToDownstreamOnAllow:
                      - cookie
                  headersToUpstreamOnAllow:
                      - set-cookie
                      - x-authentik-*
                      # Add authorization headers to the allow list if you need proxy providers which
                      # send a custom HTTP-Basic Authentication header based on values from authentik
                      # - authorization
                  includeRequestHeadersInCheck:
                      - cookie
```

Afterwards, you can create _AuthorizationPolicy_ resources to protect your applications like this:

```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
    name: authentik-policy
    namespace: istio-system
spec:
    selector:
        matchLabels:
            istio: ingressgateway
    action: CUSTOM
    provider:
        name: "authentik"
    rules:
        - to:
              - operation:
                    hosts:
                        # You can create a single resource and list all Domain names here, or create multiple resources
                        - "app.company"
```



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/proxy/custom_headers.md
================================================================================

---
title: Custom headers
---

The proxy can send custom headers to your upstream application. These can be configured in one of two ways:

- Group attributes; this allows for inheritance, but only allows static values
- Property mappings; this allows for dynamic values

## Group attributes

Edit the group or user you wish the header to be set for, and set these attributes:

```yaml
additionalHeaders:
    X-My-Header: value
```

You can the add users to this group or override the field in users.

## Property Mappings

For dynamic Header values (for example, your application requires X-App-User to contain the username), property mappings can be used.

Create a new Scope mapping with a name and scope of your choice, and use an expression like this:

```python
return {
    "ak_proxy": {
        "user_attributes": {
            "additionalHeaders": {
                "X-App-User": request.user.username
            }
        }
    }
}
```

After you've created this Scope mapping, make sure to edit the proxy provider and select the mapping.

As you can see by the similar structure, this just overrides any static attributes, so both of these methods can be combined.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/proxy/_nginx_proxy_manager.md
================================================================================

```nginx
# Increase buffer size for large headers
# This is needed only if you get 'upstream sent too big header while reading response
# header from upstream' error when trying to access an application protected by goauthentik
proxy_buffers 8 16k;
proxy_buffer_size 32k;

# Make sure not to redirect traffic to a port 4443
port_in_redirect off;

location / {
    # Put your proxy_pass to your application here
    proxy_pass          $forward_scheme://$server:$port;
    # Set any other headers your application might need
    # proxy_set_header Host $host;
    # proxy_set_header ...
    # Support for websocket
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $http_connection;
    proxy_http_version 1.1;

    ##############################
    # authentik-specific config
    ##############################
    auth_request     /outpost.goauthentik.io/auth/nginx;
    error_page       401 = @goauthentik_proxy_signin;
    auth_request_set $auth_cookie $upstream_http_set_cookie;
    add_header       Set-Cookie $auth_cookie;

    # translate headers from the outposts back to the actual upstream
    auth_request_set $authentik_username $upstream_http_x_authentik_username;
    auth_request_set $authentik_groups $upstream_http_x_authentik_groups;
    auth_request_set $authentik_entitlements $upstream_http_x_authentik_entitlements;
    auth_request_set $authentik_email $upstream_http_x_authentik_email;
    auth_request_set $authentik_name $upstream_http_x_authentik_name;
    auth_request_set $authentik_uid $upstream_http_x_authentik_uid;

    proxy_set_header X-authentik-username $authentik_username;
    proxy_set_header X-authentik-groups $authentik_groups;
    proxy_set_header X-authentik-entitlements $authentik_entitlements;
    proxy_set_header X-authentik-email $authentik_email;
    proxy_set_header X-authentik-name $authentik_name;
    proxy_set_header X-authentik-uid $authentik_uid;

    # This section should be uncommented when the "Send HTTP Basic authentication" option
    # is enabled in the proxy provider
    # auth_request_set $authentik_auth $upstream_http_authorization;
    # proxy_set_header Authorization $authentik_auth;
}

# all requests to /outpost.goauthentik.io must be accessible without authentication
location /outpost.goauthentik.io {
    # When using the embedded outpost, use:
    proxy_pass              http://authentik.company:9000/outpost.goauthentik.io;
    # For manual outpost deployments:
    # proxy_pass              http://outpost.company:9000;

    # Note: ensure the Host header matches your external authentik URL:
    proxy_set_header        Host $host;

    proxy_set_header        X-Original-URL $scheme://$http_host$request_uri;
    add_header              Set-Cookie $auth_cookie;
    auth_request_set        $auth_cookie $upstream_http_set_cookie;
    proxy_pass_request_body off;
    proxy_set_header        Content-Length "";
}

# Special location for when the /auth endpoint returns a 401,
# redirect to the /start URL which initiates SSO
location @goauthentik_proxy_signin {
    internal;
    add_header Set-Cookie $auth_cookie;
    return 302 /outpost.goauthentik.io/start?rd=$scheme://$http_host$request_uri;
    # For domain level, use the below error_page to redirect to your authentik server with the full redirect path
    # return 302 https://authentik.company/outpost.goauthentik.io/start?rd=$scheme://$http_host$request_uri;
}
```



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/proxy/index.md
================================================================================

---
title: Proxy Provider
---

```mermaid
sequenceDiagram
    participant u as User accesses service
    participant rp as Reverse proxy
    participant ak as authentik
    participant s as Service

    u->>rp: Initial request
    rp->>ak: Checks authentication
    alt User is authenticated
        ak ->> rp: Successful response
        rp ->> s: Initial request is forwarded
    else User needs to be authenticated
        ak ->> rp: Redirect to the login page
        rp ->> u: Redirect is passed to enduser
    end
```

## Headers

The proxy outpost sets the following user-specific headers:

### `X-authentik-username`

Example value: `akadmin`

The username of the currently logged in user

### `X-authentik-groups`

Example value: `foo|bar|baz`

The groups the user is member of, separated by a pipe

### `X-authentik-entitlements`

Example value: `foo|bar|baz`

The entitlements on the application this user has access to, separated by a pipe

### `X-authentik-email`

Example value: `root@localhost`

The email address of the currently logged in user

### `X-authentik-name`

Example value: `authentik Default Admin`

Full name of the current user

### `X-authentik-uid`

Example value: `900347b8a29876b45ca6f75722635ecfedf0e931c6022e3a29a8aa13fb5516fb`

The hashed identifier of the currently logged in user.

Besides these user-specific headers, some application specific headers are also set:

### `X-authentik-meta-outpost`

Example value: `authentik Embedded Outpost`

The authentik outpost's name.

### `X-authentik-meta-provider`

Example value: `test`

The authentik provider's name.

### `X-authentik-meta-app`

Example value: `test`

The authentik application's slug.

### `X-authentik-meta-version`

Example value: `goauthentik.io/outpost/1.2.3`

The authentik outpost's version.

### `X-Forwarded-Host`

:::info
Only set in proxy mode
:::

The original Host header sent by the client. This is set as the `Host` header is set to the host of the configured backend.

### Additional headers

Additionally, you can set `additionalHeaders` attribute on groups or users to set additional headers:

```yaml
additionalHeaders:
    X-test-header: test-value
```

## HTTPS

The outpost listens on both 9000 for HTTP and 9443 for HTTPS.

:::info
If your upstream host is HTTPS, and you're not using forward auth, you need to access the outpost over HTTPS too.
:::

## Logging out

Login is done automatically when you visit the domain without a valid cookie.

When using single-application mode, navigate to `app.domain.tld/outpost.goauthentik.io/sign_out`.

When using domain-level mode, navigate to `auth.domain.tld/outpost.goauthentik.io/sign_out`, where auth.domain.tld is the external host configured for the provider.

To log out, navigate to `/outpost.goauthentik.io/sign_out`.

Starting with authentik 2023.2, when logging out of a provider, all the users sessions within the respective outpost are invalidated.

## Allowing unauthenticated requests

To allow un-authenticated requests to certain paths/URLs, you can use the _Unauthenticated URLs_ / _Unauthenticated Paths_ field.

Each new line is interpreted as a regular expression, and is compiled and checked using the standard Golang regex parser.

The behaviour of this field changes depending on which mode you're in.

### Proxy and Forward auth (single application)

In this mode, the regular expressions are matched against the Request's Path.

### Forward auth (domain level)

In this mode, the regular expressions are matched against the Request's full URL.

## Dynamic backend selection

You can configure the backend the proxy should access dynamically via scope mappings. To do this, create a scope mapping with a name and scope of your choice, and set the expression to:

```python
return {
    "ak_proxy": {
        "backend_override": f"http://foo.bar.baz/{request.user.username}"
    }
}
```

Afterwards, edit the proxy provider and add this new mapping. The expression is only evaluated when the user logs into the application.

## Host header:ak-version[2025.6.1]

By default, the proxy provider will use the forwarded host header received from the client. Starting with authentik 2025.6.1, it is possible to dynamically adjust the host header with a property mapping. To do this, create a scope mapping with a name and scope of your choice, and set the expression to:

```python
return {
    "ak_proxy": {
        "host_header": "my-internal-host-header"
    }
}
```

Afterwards, edit the proxy provider and add this new mapping. The expression is only evaluated when the user logs into the application.

### Dynamically setting host header

You can dynamically set the host header to match the **Internal host** value set on the proxy provider. To do this, create a scope mapping with a name and scope of your choice, and set the expression to:

```python
from urllib.parse import urlparse
parsed_url = urlparse(provider.proxyprovider.internal_host)
return {
    "ak_proxy": {
        "host_header": parsed_url.netloc
    }
}
```

Afterwards, edit the proxy provider and add this new mapping. The expression is only evaluated when the user logs into the application.

## Proxy authentication

When a user authenticates to the proxy, authentik uses the OAuth client credentials grant as described in the [Header authentication](./header_authentication.mdx) and [Machine-to-Machine](../oauth2/machine_to_machine.mdx) documentation.

## Troubleshooting

To obtain more detailed information on a failure, you can search the logs of the server container. You will need to search for the `client_id` of the proxy provider that you're experiencing issues with. The `client_id` of a proxy provider can be obtained from its **Authentication** tab.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/proxy/server_envoy.mdx
================================================================================

---
title: Envoy
---



The configuration template shown below apply to both single-application and domain-level forward auth.

:::info
If you are using Istio and Kubernetes, use the port number that is exposed for your cluster.
:::





================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/proxy/server_traefik.mdx
================================================================================


# Traefik

The configuration templates shown below apply to both single-application and domain-level forward auth.






================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/proxy/server_nginx.mdx
================================================================================


# nginx

The configuration templates shown below apply to both single-application and domain-level forward auth.






================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/proxy/__placeholders.md
================================================================================

:::info
_example-outpost_ is used as a placeholder for the outpost name.
_authentik.company_ is used as a placeholder for the authentik install.
_app.company_ is used as a placeholder for the external domain for the application.
_outpost.company_ is used as a placeholder for the outpost. When using the embedded outpost, this can be the same as _authentik.company_
:::



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/proxy/_nginx_standalone.md
================================================================================

```nginx
# Upgrade WebSocket if requested, otherwise use keepalive
map $http_upgrade $connection_upgrade_keepalive {
    default upgrade;
    ''      '';
}

server {
    # SSL and VHost configuration
    listen                  443 ssl http2;
    server_name             _;

    ssl_certificate         /etc/ssl/certs/ssl-cert-snakeoil.pem;
    ssl_certificate_key     /etc/ssl/private/ssl-cert-snakeoil.key;

    # Increase buffer size for large headers
    # This is needed only if you get 'upstream sent too big header while reading response
    # header from upstream' error when trying to access an application protected by goauthentik
    proxy_buffers 8 16k;
    proxy_buffer_size 32k;

    location / {
        # Put your proxy_pass to your application here, and all the other statements you'll need
        # proxy_pass http://localhost:5000;
        # proxy_set_header Host $host;
        # proxy_set_header ...
        # Support for websocket
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade_keepalive;

        ##############################
        # authentik-specific config
        ##############################
        auth_request     /outpost.goauthentik.io/auth/nginx;
        error_page       401 = @goauthentik_proxy_signin;
        auth_request_set $auth_cookie $upstream_http_set_cookie;
        add_header       Set-Cookie $auth_cookie;

        # translate headers from the outposts back to the actual upstream
        auth_request_set $authentik_username $upstream_http_x_authentik_username;
        auth_request_set $authentik_groups $upstream_http_x_authentik_groups;
        auth_request_set $authentik_entitlements $upstream_http_x_authentik_entitlements;
        auth_request_set $authentik_email $upstream_http_x_authentik_email;
        auth_request_set $authentik_name $upstream_http_x_authentik_name;
        auth_request_set $authentik_uid $upstream_http_x_authentik_uid;

        proxy_set_header X-authentik-username $authentik_username;
        proxy_set_header X-authentik-groups $authentik_groups;
        proxy_set_header X-authentik-entitlements $authentik_entitlements;
        proxy_set_header X-authentik-email $authentik_email;
        proxy_set_header X-authentik-name $authentik_name;
        proxy_set_header X-authentik-uid $authentik_uid;

        # This section should be uncommented when the "Send HTTP Basic authentication" option
        # is enabled in the proxy provider
        # auth_request_set $authentik_auth $upstream_http_authorization;
        # proxy_set_header Authorization $authentik_auth;
    }

    # all requests to /outpost.goauthentik.io must be accessible without authentication
    location /outpost.goauthentik.io {
        # When using the embedded outpost, use:
        proxy_pass              http://authentik.company:9000/outpost.goauthentik.io;
        # For manual outpost deployments:
        # proxy_pass              http://outpost.company:9000;

        # Note: ensure the Host header matches your external authentik URL:
        proxy_set_header        Host $host;

        proxy_set_header        X-Original-URL $scheme://$http_host$request_uri;
        add_header              Set-Cookie $auth_cookie;
        auth_request_set        $auth_cookie $upstream_http_set_cookie;
        proxy_pass_request_body off;
        proxy_set_header        Content-Length "";
    }

    # Special location for when the /auth endpoint returns a 401,
    # redirect to the /start URL which initiates SSO
    location @goauthentik_proxy_signin {
        internal;
        add_header Set-Cookie $auth_cookie;
        return 302 /outpost.goauthentik.io/start?rd=$scheme://$http_host$request_uri;
        # For domain level, use the below error_page to redirect to your authentik server with the full redirect path
        # return 302 https://authentik.company/outpost.goauthentik.io/start?rd=$scheme://$http_host$request_uri;
    }
}
```



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/proxy/header_authentication.mdx
================================================================================

---
title: Header authentication
---

## Sending authentication

### Send HTTP Basic authentication

Proxy providers have the option to _Send HTTP-Basic Authentication_ to the upstream application. When the option in the provider is enabled, two attributes must be specified. These attributes are the keys of values which can be saved on a user or group level that contain the credentials.

For example, with _HTTP-Basic Username Key_ set to `app_username` and _HTTP-Basic Password Key_ set to `app_password`, these attributes would have to be set either on a user or a group the user is member of:

```yaml
app_username: admin
app_password: admin-password
```

These credentials are only retrieved when the user authenticates to the proxy.

If the user does not have a matching attribute, authentik falls back to using the user's email address as username, and the password will be empty if not found.

## Receiving authentication

By default, when **Intercept header authentication** is enabled, authentik will intercept the authorization header. If the authorization header value is invalid, an error response will be shown with a 401 status code. Requests without an authorization header will still be redirected to the standard login flow.

If the proxied application requires usage of the "Authorization" header, the setting should be disabled. When this setting is disabled, authentik will still attempt to interpret the "Authorization" header, and fall back to the default behaviour if it can't.

### Receiving HTTP Basic authentication

Proxy providers can receive HTTP basic authentication credentials. The password is expected to be an _App password_, as the credentials are used internally with the [OAuth2 machine-to-machine authentication flow](../oauth2/machine_to_machine.mdx).

Access control is done with the policies bound to the application being accessed.

If the received credentials are invalid, a normal authentication flow is initiated. If the credentials are correct, the Authorization header is removed to prevent sending the credentials to the proxied application.

:::danger
It is **strongly** recommended that the client sending requests with HTTP-Basic authentication persists the cookies returned by the outpost. If this is not the case, every request must be authenticated independently, which will increase load on the authentik server and encounter a performance hit.
:::

Starting with authentik 2023.2, logging in with the reserved username `goauthentik.io/token` will behave as if a bearer token was used. All the same options as below apply. This is to allow token-based authentication for applications which might only support basic authentication.

### Receiving HTTP Bearer authentication

Proxy providers can receive HTTP bearer authentication credentials. The token is expected to be a JWT token issued for the proxy provider. This is described in the [OAuth2 machine-to-machine authentication flow](../oauth2/machine_to_machine.mdx) documentation, using the _client_id_ value shown in the admin interface. Both static and JWT authentication methods are supported.

Access control is done with the policies bound to the application being accessed.

If the received credentials are invalid, a normal authentication flow is initiated. If the credentials are correct, the Authorization header is removed to prevent sending the credentials to the proxied application.

:::caution
It is recommended that the client sending requests with HTTP-Bearer authentication persists the cookies returned by the outpost. For bearer authentication this has a smaller impact than for Basic authentication, but each request is still verified with the authentik server.
:::



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/ssf/create-ssf-provider.md
================================================================================

---
title: Configure an SSF provider
authentik_version: "2025.2.0"
description: "How to create and configure an SSF provider in authentik"
authentik_enterprise: true
authentik_preview: true
tags: [Shared Signals Framework, SSF, Apple Business Manager, backchannel]
---

Follow this workflow to create and configure an SSF provider for an application:

1. Create the SSF provider (which serves as the [backchannel provider](../../applications/manage_apps.mdx#backchannel-providers)).
2. Create an OIDC provider (which serves as the protocol provider for the application).
3. Create the application, and assign both the OIDC provider and the SSF provider.

## Create the SSF provider

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click **Create** to create a provider.
3. Select **Shared Signals Framework Provider** as the **Provider Type**, and then click **Next**.
4. On the **Create SSF Provider** page, provide the configuration settings. Be sure to select a **Signing Key**.
5. Click **Finish** to create the provider.

## Create the OIDC provider

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click **Create** to create a provider.
3. Select **OAuth2/OpenID Provider** as the **Provider Type**, and then click **Next**.
4. On the **Create OAuth2/OpenID Provider** page, provide the configuration settings and then click **Finish** to create the provider.

## Create the application

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create** to create an application.
3. Configure the following required settings for the application:
    - **Name**: provide a descriptive name of the application.
    - **Slug**: provide the application slug used in URLs.
    - **Provider**: select the OIDC provider that you created.
    - **Backchannel Providers**: select the SSF provider that you created.
4. Click **Create** to save the new application.

The new application, with its OIDC provider and the backchannel SSF provider, should now appear in your application list.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/add-secure-apps/providers/ssf/index.md
================================================================================

---
title: Shared Signals Framework (SSF) Provider
sidebar_label: SSF Provider
description: "Overview of SSF and the authentik SSF provider"
authentik_version: "2025.2.0"
authentik_enterprise: true
authentik_preview: true
tags: [Shared Signals Framework, SSF, Apple Business Manager]
---

The Shared Signals Framework (SSF) provider allows you to integrate applications with the Shared Signals Framework protocol.

SSF is a common standard for sharing asynchronous real-time security signals and events across multiple applications and an identity provider. The framework is a collection of standards and communication processes, documented in a [specification](https://openid.net/specs/openid-sharedsignals-framework-1_0-ID3.html). SSF leverages the APIs of the application and the IdP, using privacy-protected and secure webhooks.

The authentik SSF provider allows OIDC applications to subscribe to certain types of security signals (which are then translated into SETs, or Security Event Tokens) that are captured by authentik (the IdP), and then the application can respond to each event. In this scenario, authentik acts as the _transmitter_ and the application acts as the _receiver_ of the events.

Events in authentik that are tracked via SSF include when an MFA device is added or removed, logouts, sessions being revoked by Admin or user clicking logout, or credentials changed.

Refer to our documentation to learn how to [create a SSF provider](./create-ssf-provider.md).

## Example use cases

One important use case for SSF is to [integrate Apple Business Manager](https://integrations.goauthentik.io/device-management/apple/) or any of the Apple device management platforms with authentik, so that users can enroll their Apple devices using their authentik credentials. When a user signs in with their email address, Apple redirects them to authentik for authentication. Once authenticated, Apple enrolls the user's device and grants access to Apple services.

Another use case for SSF is when an administrator wants to know when a user logs out of authentik, so that the user is then also automatically logged out of all other work-focused applications.

Another example use case is when an application uses SSF to subscribe to authorization events because the application needs to know if a user changed their password in authentik. If a user did change their password, then the application receives a POST request to write the fact that the password was changed.

## Using the authentik SSF provider

The SSF provider serves as a [backchannel provider](../../applications/manage_apps#backchannel-providers). Backchannel providers are used to augment the functionality of the main provider for an application.

Therefore you still need to [create a typical OIDC application/provider pair](../../applications/manage_apps#create-an-application-and-provider-pair), and when creating the application, assign the SSF provider as a [backchannel provider](../../applications/manage_apps#backchannel-providers).

When an authentik administrator [creates an SSF provider](./create-ssf-provider), they need to configure both the application (the receiver) and authentik (the IdP and the transmitter).

### The application (the receiver)

Within the application, the administrator creates an SSF stream which lists all the signals that the application wants to subscribe to, and defines the audience (`aud`), which is the URL that identifies the stream. A stream is basically an API request to authentik, which asks for a POST of all events. How that request is sent varies from application to application. An application can also change or delete the stream.

authentik does not specify which events to subscribe to; instead the application defines which events they want to listen for.

### authentik (the transmitter)

To configure authentik as a shared signals transmitter, the authentik administrator [creates a new SSF provider](./create-ssf-provider), to serve as the backchannel provider for the application.

When creating the SSF provider you will need to select a signing key that is used to sign the Security Event Tokens (SET).

Optionally, you can specify an event retention time period, which determines how long events are stored for. If an event could not be sent correctly, and retries occur, the event's expiration is also increased by this duration.

:::note SET events
Be aware that the SET events are different events than those displayed in the authentik Admin interface under **Events**.
:::



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/architecture.md
================================================================================

---
title: Architecture
---

authentik consists of a handful of components, most of which are required for a functioning setup.

```mermaid
graph LR
    user(User) --> ak_server(authentik Server)
    ak_server --> ak_server_core(authentik Server Core)
    ak_server --> ak_outpost(Embedded outpost)
    ak_server_core --> db(PostgreSQL)
    ak_worker(Background Worker) --> db(PostgreSQL)
```

### Server

The server container consists of two sub-components, the actual server itself and the embedded outpost. Incoming requests to the server container(s) are routed by a lightweight router to either the _Core_ server or the embedded outpost. This router also handles requests for any static assets such as JavaScript and CSS files.

#### Core

The core sub-component handles most of authentik's logic, such as API requests, flow executions, any kind of SSO requests, etc.

#### Embedded outpost

Similar to [other outposts](../add-secure-apps/outposts/index.mdx), this outpost allows using [Proxy providers](../add-secure-apps/providers/proxy/index.md) without deploying a separate outpost.

#### Persistence

- `/data` is used to store uploaded files (icons, flow backgrounds, etc.) and CSV reports. If not mounted, authentik will allow you to set a URL to icons in place of a file upload. See [Files](../customize/files.md) for more information.

### Worker

This container executes background tasks, such as sending emails, the event notification system, and everything you can see on the _System Tasks_ page in the Admin interface.

#### Persistence

- `/certs` is used for authentik to import external certs, which in most cases shouldn't be used for SAML, but if you use authentik without a reverse proxy, this can be used, for example, for the [Let's Encrypt integration](../sys-mgmt/certificates.md#lets-encrypt-integration).
- `/templates` is used for [custom email templates](../add-secure-apps/flows-stages/stages/email/index.mdx#custom-templates), and as with the others is fully optional.

### PostgreSQL

authentik uses PostgreSQL to store all of its configuration and other data (excluding uploaded files).

#### Persistence

- `/var/lib/postgresql/data` is used to store the PostgreSQL database

On Kubernetes, with the default Helm chart and using the packaged PostgreSQL sub-chart, persistent data is stored in a PVC.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/index.mdx
================================================================================

---
title: Glossary
---


This glossary provides definitions for common terms used throughout the authentik documentation.




================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/dynamic-in-memory-stage.mdx
================================================================================

---
title: Dynamic in-memory stage
sidebar_custom_props:
    termName: Dynamic in-memory stage
    tags:
        - Flows
    shortDescription: Ephemeral stage appended at runtime; exists only in memory.
    authentikSpecific: true
    longDescription: Special stage added by authentik in specific contexts to alter control flow without persisting configuration. For example, the Source stage appends a dynamic in-memory stage to the source's flow to suspend the current flow, run the source's authentication or enrollment, and then resume. If a User login stage is bound in the source's flow, it will directly authenticate the pending user instead of resuming the original flow. Not configurable by administrators.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/radius-vsa.mdx
================================================================================

---
title: Vendor‑Specific Attribute (VSA)
sidebar_custom_props:
    termName: Vendor‑Specific Attribute (VSA)
    tags:
        - Protocols
    shortDescription: Attribute namespace for vendor extensions.
    longDescription: Allows vendors to convey proprietary settings (e.g., privilege levels, ACLs) beyond standard RADIUS attributes in Access‑Accept responses.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/scim.mdx
================================================================================

---
title: SCIM
sidebar_custom_props:
    termName: SCIM
    tags:
        - Provisioning
    shortDescription: System for Cross-domain Identity Management.
    longDescription: Open standard (RFC 7643/7644) for automating user and group provisioning across systems. Defines schemas, endpoints, and operations for lifecycle management.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/service-provider.mdx
================================================================================

---
title: Service Provider (SP)
sidebar_custom_props:
    termName: Service Provider (SP)
    tags:
        - Core Concepts
    shortDescription: Application that relies on the IdP to authenticate users.
    longDescription: In SAML, the SP consumes assertions. In OIDC, this role is called the Relying Party or Client.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/radius-messages.mdx
================================================================================

---
title: RADIUS messages
sidebar_custom_props:
    termName: RADIUS messages
    tags:
        - Protocols
    shortDescription: Access‑Request/Accept/Reject and Accounting messages.
    longDescription: Core flow - NAS sends Access‑Request; server replies Access‑Accept (optionally with attributes) or Access‑Reject. Accounting‑Start/Stop records session usage.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/redirect-uri.mdx
================================================================================

---
title: Redirect URI
sidebar_custom_props:
    termName: Redirect URI
    tags:
        - OAuth2/OIDC
    shortDescription: Callback URL the provider redirects to.
    longDescription: Registered callback URL where the OpenID Provider (OP) or Authorization Server (AS) returns the user after authorization. Must match exactly (including scheme and path), and pairs with `response_mode` (`query`, `fragment`, or `form_post`).
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/radius-nas.mdx
================================================================================

---
title: Network Access Server (NAS)
sidebar_custom_props:
    termName: Network Access Server (NAS)
    tags:
        - Protocols
    shortDescription: Device that sends RADIUS requests to the server.
    longDescription: Examples include VPN concentrators, Wi‑Fi controllers, firewalls, or switches. The NAS acts as the RADIUS client initiating Access‑Request and Accounting messages.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/subject.mdx
================================================================================

---
title: Subject (sub)
sidebar_custom_props:
    termName: Subject (sub)
    tags:
        - Tokens And Claims
    shortDescription: Unique identifier of the token's principal.
    longDescription: The 'sub' claim identifies the principal (end-user or client) represented by the token. In OIDC, 'sub' is stable per issuer and may be pairwise or public.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/issuer.mdx
================================================================================

---
title: Issuer (iss)
sidebar_custom_props:
    termName: Issuer (iss)
    tags:
        - Tokens And Claims
    shortDescription: Entity that issued the token.
    longDescription: The 'iss' claim identifies the authorization server or identity provider that created the token; RPs and APIs must verify it matches the expected issuer URL.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/front-channel-logout.mdx
================================================================================

---
title: Front-channel logout
sidebar_custom_props:
    termName: Front-channel logout
    tags:
        - Protocols
    shortDescription: Logout via browser redirects or iframes.
    longDescription: Relies on the user agent to propagate logout to clients or SPs; may be affected by third-party cookie and iframe restrictions.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/authorization-code.mdx
================================================================================

---
title: Authorization code
sidebar_custom_props:
    termName: Authorization code
    tags:
        - OAuth2/OIDC
    shortDescription: Short-lived code exchanged for tokens.
    longDescription: Returned to the client after user authorization and redeemed at the token endpoint for access, refresh, and optionally ID tokens.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/response-type.mdx
================================================================================

---
title: Response type
sidebar_custom_props:
    termName: Response type
    tags:
        - OAuth2/OIDC
    shortDescription: OAuth/OIDC response expected from the authorization endpoint.
    longDescription: Examples include `code`, `token`, and `id_token`; modern apps should use `code` with PKCE.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/audience.mdx
================================================================================

---
title: Audience (aud)
sidebar_custom_props:
    termName: Audience (aud)
    tags:
        - Tokens And Claims
    shortDescription: Intended recipient of a token.
    longDescription: The 'aud' claim limits where the token is valid, typically an API or application.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/blueprints.mdx
================================================================================

---
title: Blueprints
sidebar_custom_props:
    termName: Blueprints
    tags:
        - Configuration
    shortDescription: Declarative files to template and reconcile authentik config.
    authentikSpecific: true
    longDescription: YAML-based configuration files that are used to create and update objects (flows, providers, policies, etc.) as code. Blueprints can be applied from the filesystem, database, or OCI registries, support meta models for dependencies, and are reconciled periodically or on change.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/scim-resource.mdx
================================================================================

---
title: SCIM resource
sidebar_custom_props:
    termName: SCIM resource
    tags:
        - Provisioning
    shortDescription: Typed object like User or Group managed via SCIM.
    longDescription: Resources conform to schemas (core and extension) and are exposed at endpoints such as /Users and /Groups with standard attributes and metadata.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/sp-initiated-sso.mdx
================================================================================

---
title: SP-initiated SSO
sidebar_custom_props:
    termName: SP-initiated SSO
    tags:
        - SAML
    shortDescription: SSO flow started at the Service Provider.
    longDescription: User starts at the SP, which sends an AuthnRequest (often via Redirect) to the IdP. After authentication, the IdP posts the Response to the SP's ACS, optionally preserving RelayState.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/scim-lifecycle.mdx
================================================================================

---
title: SCIM provisioning lifecycle
sidebar_custom_props:
    termName: SCIM provisioning lifecycle
    tags:
        - Provisioning
    shortDescription: Create, update, deactivate, and delete user records.
    longDescription: SCIM automates onboarding/offboarding by creating accounts, updating attributes and entitlements, and deactivating or deleting users and group memberships.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/provider.mdx
================================================================================

---
title: Provider
sidebar_custom_props:
    termName: Provider
    tags:
        - Core Concepts
    shortDescription: A way for other applications to authenticate against authentik.
    authentikSpecific: true
    longDescription: A provider is a way for other applications to authenticate against authentik. Common providers in authentik are OpenID Connect (OIDC), OAuth2, SCIM, and SAML.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/jwt.mdx
================================================================================

---
title: JWT
sidebar_custom_props:
    termName: JWT
    tags:
        - Tokens And Claims
    shortDescription: Compact, signed JSON token format.
    longDescription: Compact token with header, payload, and signature. Usually a JWS (signed) and optionally a JWE (encrypted); includes claims such as `iss`, `sub`, `aud`, `exp`, `iat`, and custom fields.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/front-channel.mdx
================================================================================

---
title: Front-channel
sidebar_custom_props:
    termName: Front-channel
    tags:
        - Protocols
    shortDescription: Browser-mediated communication via the user's agent.
    longDescription: Interactions where data transits the user's browser, e.g., OAuth/OIDC authorization redirects and SAML HTTP-Redirect/POST bindings. Useful for user interaction and consent, but subject to browser policies, URL length/visibility, and referrer leakage if not carefully designed.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/nameid.mdx
================================================================================

---
title: NameID
sidebar_custom_props:
    termName: NameID
    tags:
        - SAML
    shortDescription: Primary identifier for a user in SAML.
    longDescription: Subject identifier in SAML Assertions. Common formats include `EmailAddress`, `Persistent` (stable pseudonymous), and `Transient` (one-time); chosen per service provider requirements.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/oidc-discovery.mdx
================================================================================

---
title: OIDC discovery document
sidebar_custom_props:
    termName: OIDC discovery document
    tags:
        - OAuth2/OIDC
    shortDescription: Provider metadata at the well-known URL.
    longDescription: JSON metadata at `/.well-known/openid-configuration` advertising issuer, endpoints (authorization, token, userinfo, jwks, end_session), supported scopes, response types, and algorithms for dynamic client configuration.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/radius.mdx
================================================================================

---
title: RADIUS
sidebar_custom_props:
    termName: RADIUS
    tags:
        - Protocols
    shortDescription: Remote Authentication Dial-In User Service protocol.
    longDescription: AAA protocol used by network devices (NAS) to authenticate and authorize users and to record accounting. Uses UDP and shared secrets for message integrity.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/brand.mdx
================================================================================

---
title: Brand
sidebar_custom_props:
    termName: Brand
    tags:
        - Customization
    shortDescription: Per-domain settings for UI, default flows, and behavior.
    authentikSpecific: true
    longDescription: A Brand applies visual identity and behavior to your authentik instance. Branding settings control title, logo, favicon, theme, default flows (authentication, logout, recovery, user settings, device code), default application redirects, and global attributes like locale.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/pkce.mdx
================================================================================

---
title: PKCE
sidebar_custom_props:
    termName: PKCE
    tags:
        - OAuth2/OIDC
    shortDescription: Proof Key for Code Exchange hardens the code flow.
    longDescription: Binds the authorization request to the token exchange using a one-time code verifier and a code challenge (typically `S256`). Prevents intercepted codes from being redeemed by attackers.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/back-channel-logout.mdx
================================================================================

---
title: Back-channel logout
sidebar_custom_props:
    termName: Back-channel logout
    tags:
        - Protocols
    shortDescription: Server-to-server logout notification.
    longDescription: Provider notifies clients directly without the user agent, offering more reliable session termination than front-channel logout.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/property-mappings.mdx
================================================================================

---
title: Property mappings
sidebar_custom_props:
    termName: Property mappings
    tags:
        - Configuration
    shortDescription: Define how data is exposed to apps and stored from sources.
    authentikSpecific: true
    longDescription: Property mappings allow you to make information available for external applications and to modify how information from sources is stored in authentik. For example, to log in to AWS you can set a user's roles in AWS based on their group memberships in authentik.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/grant-type.mdx
================================================================================

---
title: Grant type
sidebar_custom_props:
    termName: Grant type
    tags:
        - OAuth2/OIDC
    shortDescription: OAuth2 mechanism for obtaining tokens.
    longDescription: Examples include `authorization_code`, `client_credentials`, and `refresh_token`; PKCE strengthens `authorization_code` for public clients.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/jwk.mdx
================================================================================

---
title: JWK
sidebar_custom_props:
    termName: JWK
    tags:
        - Keys And Crypto
    shortDescription: JSON representation of a cryptographic key.
    longDescription: Describes key material and parameters for signing or encryption; individual entries make up a JWKS.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/outpost.mdx
================================================================================

---
title: Outpost
sidebar_custom_props:
    termName: Outpost
    tags:
        - Components
    shortDescription: Separate component providing services like reverse proxying, deployable anywhere.
    authentikSpecific: true
    longDescription: An outpost is a separate component of authentik, deployable anywhere regardless of the authentik deployment. It offers services not implemented directly in the core, such as reverse proxying.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/application.mdx
================================================================================

---
title: Application
sidebar_custom_props:
    termName: Application
    tags:
        - Core Concepts
    shortDescription: An application is what you authenticate into with authentik and is displayed on the "My applications" page in the User interface.
    authentikSpecific: true
    longDescription: An application is paired with a provider, and with defined policies and other configurations controls user access. It also holds information like UI name, icon, and more.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/jwks.mdx
================================================================================

---
title: JWKS
sidebar_custom_props:
    termName: JWKS
    tags:
        - Keys And Crypto
    shortDescription: JSON Web Key Set used to verify JWTs.
    longDescription: Set of public keys exposed by the provider so clients and resource servers can verify JWT signatures. Keys are identified by 'kid' and support rotation without downtime.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/passkey.mdx
================================================================================

---
title: Passkey
sidebar_custom_props:
    termName: Passkey
    tags:
        - Authentication
    shortDescription: Discoverable FIDO2 credential, often synced across devices for passwordless login.
    longDescription: A user‑friendly form of WebAuthn credential stored by a platform or password manager and typically synced via cloud. Passkeys allow username‑less and passwordless flows by discovering credentials on the device. All passkeys are WebAuthn, but not all WebAuthn credentials are passkeys (e.g., non‑resident).
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/system-tasks.mdx
================================================================================

---
title: System tasks
sidebar_custom_props:
    termName: System tasks
    tags:
        - Operations
    shortDescription: Longer-running background tasks in authentik.
    authentikSpecific: true
    longDescription: These are longer-running tasks which authentik runs in the background, such as syncing LDAP sources and other maintenance tasks.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/source.mdx
================================================================================

---
title: Source
sidebar_custom_props:
    termName: Source
    tags:
        - Core Concepts
    shortDescription: Location from which users and their attributes can be accessed by authentik.
    authentikSpecific: true
    longDescription: Sources are locations from which user data can be accessed by authentik, and either pulled into authentik or synced with authentik. For example, an LDAP connection to import users from Active Directory, or an OAuth2 connection to allow social logins.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/radius-auth-methods.mdx
================================================================================

---
title: RADIUS auth methods
sidebar_custom_props:
    termName: RADIUS auth methods
    tags:
        - Protocols
    shortDescription: PAP, CHAP, MS‑CHAPv2, and EAP methods.
    longDescription: RADIUS transports credential exchanges such as PAP (plaintext password), CHAP/MS‑CHAPv2 (challenge‑response), or EAP methods (e.g., PEAP, EAP‑TLS) terminated on the NAS or server.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/webauthn.mdx
================================================================================

---
title: WebAuthn
sidebar_custom_props:
    termName: WebAuthn
    tags:
        - Authentication
    shortDescription: W3C standard for phishing‑resistant authentication with FIDO2 authenticators.
    longDescription: Enables authentication with platform or roaming authenticators (e.g., Windows Hello, Touch ID, YubiKey). Supports user verification (biometrics/PIN), resident (discoverable) credentials for passwordless, and attestation/metadata. In authentik, exposed via the WebAuthn authenticator stages.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/relying-party.mdx
================================================================================

---
title: Relying Party (RP)
sidebar_custom_props:
    termName: Relying Party (RP)
    tags:
        - OAuth2/OIDC
    shortDescription: OIDC client that relies on the OP for identity.
    longDescription: Client application that registers redirect URIs, requests scopes, validates ID tokens (issuer, audience, signature, expiry, nonce), exchanges codes for tokens, and manages user sessions.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/acs.mdx
================================================================================

---
title: Assertion Consumer Service (ACS)
sidebar_custom_props:
    termName: Assertion Consumer Service (ACS)
    tags:
        - SAML
    shortDescription: Service Provider endpoint that receives SAML assertions.
    longDescription: Configured SP endpoint where the IdP delivers the SAML Response (typically via HTTP-POST). The SP validates signatures, issuer, audience, and time conditions before creating a session.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/single-logout.mdx
================================================================================

---
title: Single Logout (SLO)
sidebar_custom_props:
    termName: Single Logout (SLO)
    tags:
        - Protocols
    shortDescription: Terminates sessions across parties in a federation.
    longDescription: Coordinated logout that ends sessions at the Identity Provider (IdP) or OpenID Provider (OP) and participating Service Providers (SPs) or Relying Parties (RPs). Implemented via front-channel (browser) or back-channel (server) mechanisms depending on protocol support.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/scim-externalid.mdx
================================================================================

---
title: SCIM externalId
sidebar_custom_props:
    termName: SCIM externalId
    tags:
        - Provisioning
    shortDescription: Client-supplied stable identifier for correlation.
    longDescription: Optional, opaque identifier provided by the provisioning client to map SCIM resources to upstream records; distinct from server-generated 'id'.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/back-channel.mdx
================================================================================

---
title: Back-channel
sidebar_custom_props:
    termName: Back-channel
    tags:
        - Protocols
    shortDescription: Direct server-to-server communication.
    longDescription: Server-to-server interactions without user-agent involvement, e.g., token exchange at the token endpoint, introspection, revocation, or back-channel logout. More reliable for session coordination and avoids browser constraints.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/notification-rule.mdx
================================================================================

---
title: Notification rule
sidebar_custom_props:
    termName: Notification rule
    tags:
        - Events And Notifications
    shortDescription: Policy-filtered event triggers that send notifications via transports.
    authentikSpecific: true
    longDescription: Rules that evaluate events through the policy engine and, when matched, deliver notifications using a selected transport (local UI, email, webhook). Bind policies, groups, or users to scope recipients and control which events generate alerts.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/authorization-server.mdx
================================================================================

---
title: Authorization Server (AS)
sidebar_custom_props:
    termName: Authorization Server (AS)
    tags:
        - OAuth2/OIDC
    shortDescription: OAuth2 role that issues tokens and hosts authorization endpoints.
    longDescription: Server that authenticates resource owners, obtains consent, and issues access/refresh (and in OIDC, ID) tokens to clients. Provides authorization, token, introspection, revocation, and metadata (discovery) endpoints. In OIDC, the Authorization Server is called the OpenID Provider (OP).
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/flow.mdx
================================================================================

---
title: Flow
sidebar_custom_props:
    termName: Flow
    tags:
        - Flows
    shortDescription: An ordered sequence of stages.
    authentikSpecific: true
    longDescription: Flows are an ordered sequence of stages, potentially with policies bound to them. They define how a user authenticates, enrolls, and more.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/scim-patch.mdx
================================================================================

---
title: SCIM PATCH
sidebar_custom_props:
    termName: SCIM PATCH
    tags:
        - Provisioning
    shortDescription: Standardized partial update operation.
    longDescription: Supports add, remove, and replace path operations on resource attributes. Enables efficient updates without resending the full resource.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/stage.mdx
================================================================================

---
title: Stage
sidebar_custom_props:
    termName: Stage
    tags:
        - Flows
    shortDescription: A single verification or logic step within a flow.
    authentikSpecific: true
    longDescription: A stage represents a single verification or logic step. Stages are used to authenticate users, enroll users, and more, and can optionally be bound to a flow via policies.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/core/glossary/terms/idp-initiated-sso.mdx
================================================================================

---
title: IdP-initiated SSO
sidebar_custom_props:
    termName: IdP-initiated SSO
    tags:
        - SAML
    shortDescription: SSO flow started at the Identity Provider.
    longDescription: User launches from the IdP without an SP AuthnRequest. The IdP posts a response directly to the SP's ACS; simpler to start but offers fewer request-bound security guarantees.
---



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/developer-docs/index.mdx
================================================================================

---
title: Developer Documentation
description: Quick links and entry points for developers working on authentik.
---


We're thrilled you're here! 🎉 Thanks for jumping in to contribute to authentik; your ideas, fixes, and features make a real impact. Pick a topic below to dive in and have fun hacking! 🚀 Even small PRs and typo fixes are hugely appreciated.




================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/developer-docs/contributing.md
================================================================================

---
title: Contributing to authentik
description: Guidelines for contributing code, docs, and enhancements to authentik.
---

:+1::tada: Thanks for taking the time to contribute! :tada::+1:

The following is a set of guidelines for contributing to authentik and its components, which are hosted in the [goauthentik Organization](https://github.com/goauthentik) on GitHub. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

We appreciate contributions of code, documentation, enhancements, and bug fixes. Read more [below](#how-can-i-contribute) about the many ways to contribute.

## Code of conduct

We expect all contributors to act professionally and respectfully in all interactions. If there's something you dislike or think can be done better, tell us! We'd love to hear any suggestions for improvement.

## I don't want to read this whole thing I just have a question!!!

Either [create a question on GitHub](https://github.com/goauthentik/authentik/issues/new?assignees=&labels=question&template=question.md&title=) or join [the Discord server](https://goauthentik.io/discord?utm_source=developer-docs).

## What should I know before I get started?

### The components

authentik consists of a few larger components:

- _authentik_ — the actual application server, described below.
- _outpost-proxy_ — a Go application based on a forked version of oauth2_proxy, which does identity-aware reverse proxying.
- _outpost-ldap_ — a Go LDAP server that uses the _authentik_ application server as its backend.
- _outpost-radius_ — a Go RADIUS server that uses the _authentik_ application server as its backend.
- _web_ — the web frontend, both for administrating and using authentik. It is written in TypeScript using lit-html and the PatternFly CSS library.
- _website_ — the website/documentation, which uses Docusaurus.

### authentik's structure

authentik is at its very core a Django project. It consists of many individual Django applications. These applications are intended to separate concerns, and they may share code between each other.

These are the current packages:

```
authentik
├── admin - Administrative tasks and APIs, no models (Version updates, Metrics, system tasks)
├── api - General API Configuration (Routes, Schema and general API utilities)
├── blueprints - Handle managed models and their state.
├── core - Core authentik functionality, central routes, core Models
├── crypto - Cryptography, currently used to generate and hold Certificates and Private Keys
├── enterprise - Enterprise features, which are source available but not open source
├── events - Event Log, middleware and signals to generate signals
├── flows - Flows, the FlowPlanner and the FlowExecutor, used for all flows for authentication, authorization, etc
├── lib - Generic library of functions, few dependencies on other packages.
├── outposts - Configure and deploy outposts on Kubernetes and Docker.
├── policies - General PolicyEngine
│   ├── dummy - A Dummy policy used for testing
│   ├── event_matcher - Match events based on different criteria
│   ├── expiry - Check when a user's password was last set
│   ├── expression - Execute any arbitrary python code
│   ├── password - Check a password against several rules
│   └── reputation - Check the user's/client's reputation
├── providers
│   ├── ldap - Provide LDAP access to authentik users/groups using an outpost
│   ├── oauth2 - OIDC-compliant OAuth2 provider
│   ├── proxy - Provides an identity-aware proxy using an outpost
│   ├── radius - Provides a RADIUS server that authenticates using flows
│   ├── saml - SAML2 provider
│   └── scim - SCIM provider
├── recovery - Generate keys to use in case you lock yourself out
├── root - Root Django application, contains global settings and routes
├── sources
│   ├── kerberos - Sync Kerberos users into authentik
│   ├── ldap - Sync LDAP users from OpenLDAP or Active Directory into authentik
│   ├── oauth - OAuth1 and OAuth2 source
│   ├── plex - Plex source
│   ├── saml - SAML2 source
│   └── telegram - Telegram source
├── stages
│   ├── authenticator_duo - Configure a DUO authenticator
│   ├── authenticator_static - Configure TOTP backup keys
│   ├── authenticator_totp - Configure a TOTP authenticator
│   ├── authenticator_validate - Validate any authenticator
│   ├── authenticator_webauthn - Configure a WebAuthn / Passkeys authenticator
│   ├── captcha - Make the user pass a captcha
│   ├── consent - Let the user decide if they want to consent to an action
│   ├── deny - Static deny, can be used with policies
│   ├── dummy - Dummy stage to test
│   ├── email - Send the user an email and block execution until they click the link
│   ├── identification - Identify a user with any combination of fields
│   ├── invitation - Invitation system to limit flows to certain users
│   ├── password - Password authentication
│   ├── prompt - Arbitrary prompts
│   ├── user_delete - Delete the currently pending user
│   ├── user_login - Login the currently pending user
│   ├── user_logout - Logout the currently pending user
│   └── user_write - Write any currently pending data to the user.
├── tasks - Background tasks
└── tenants - Soft tenancy, configure defaults and branding per domain
```

This Django project is running in gunicorn, which spawns multiple workers and threads. Gunicorn is run from a lightweight Go application that reverse-proxies the application and handles static files.

There are also several background tasks that run in Dramatiq, via the `django-dramatiq-postgres` package, with some additional helpers in `authentik.tasks`.

## How can I contribute?

### Reporting bugs

This section guides you through submitting a bug report for authentik. Following these guidelines helps maintainers and the community understand your report, reproduce the behavior, and find related reports.

Whenever authentik encounters an error, it will be logged as an Event with the type `system_exception`. This event type has a button to directly open a pre-filled GitHub issue form.

This form will have the full stack trace of the error that occurred and shouldn't contain any sensitive data.

### Suggesting enhancements

This section guides you through submitting an enhancement suggestion for authentik, including completely new features and minor improvements to existing functionality. Following these guidelines helps maintainers and the community understand your suggestion and find related suggestions.

When you are creating an enhancement suggestion, please fill in [the template](https://github.com/goauthentik/authentik/issues/new?assignees=&labels=enhancement&template=feature_request.md&title=), including the steps that you imagine you would take if the feature you're requesting existed.

### Your first code contribution

#### Local development

authentik can be run locally, although depending on which part you want to work on, different prerequisites are required.

This is documented in the [developer docs](./setup/frontend-dev-environment.md).

### Help with the docs

Contributions to the technical documentation are greatly appreciated. Open a PR if you have improvements to make or new content to add. If you have questions or suggestions about the documentation, open an Issue. No contribution is too small.

Please be sure to refer to our [Style Guide](../developer-docs/docs/style-guide.mdx) for the docs, and use a [template](./docs/templates/index.md) to make it easier for you. The style guidelines are also used for any Integrations documentation, and we have a template for Integrations as well, in our [GitHub repo](https://github.com/goauthentik/authentik) at `/website/integrations/template/service.md`.

### Pull requests

The process described here has several goals:

- Maintain authentik's quality
- Fix problems that are important to users
- Engage the community in working toward the best possible authentik
- Enable a sustainable system for authentik's maintainers to review contributions

#### Always use feature branches

**DO NOT open pull requests from your `main` branch.** Always create a feature branch for your changes.

Here's one way to do it correctly (your own preferred git commands may differ):

```bash
# Create and switch to a new feature branch
git checkout -b feature/my-awesome-feature

# Make your changes, then commit and push
git add .
git commit -m "providers/oauth2: add awesome feature"
git push -u origin feature/my-awesome-feature
```

Then open your PR from the feature branch.

:::tip Accidentally made changes on main?
If you already started working on `main` (even if you've already made commits), you can still recover by creating a branch from your current state, then resetting `main`:

```bash
# Create a new branch with your current changes/commits
git checkout -b feature/my-awesome-feature

# Switch back to main and reset it to match origin
git checkout main
git reset --hard origin/main
```

Your changes are now safely on the feature branch, and `main` is back in sync with the remote.
:::

Please follow these steps to have your contribution considered by the maintainers:

1. Follow the [style guides](#style-guides)
2. After you submit your pull request, verify that all [status checks](https://help.github.com/articles/about-status-checks/) are passing <details><summary>What if the status checks are failing?</summary>If a status check is failing, and you believe that the failure is unrelated to your change, please leave a comment on the pull request explaining why you believe the failure is unrelated. A maintainer will re-run the status check for you. If we conclude that the failure was a false positive, then we will open an issue to track that problem with our status check suite.</details>
3. Ensure your code has tests. While it is not always possible to test every single case, the majority of the code should be tested.

While the prerequisites above must be satisfied prior to having your pull request reviewed, the reviewer(s) may ask you to complete additional design work, tests, or other changes before your pull request can be ultimately accepted.

## Style guides

### PR naming

- Use the format of `<package>: <verb> <description>`
    - See [here](#authentiks-structure) for `package`
    - Examples:
      `providers/saml2: fix parsing of requests`
      `website/docs: add config info for GWS`

### Git commit messages

- Use the format of `<package>: <verb> <description>`
    - See [here](#authentiks-structure) for `package`
    - Example: `providers/saml2: fix parsing of requests`
- Reference issues and pull requests liberally after the first line
- Naming of commits within a PR does not need to adhere to the guidelines as we squash merge PRs

### Python Style Guide

All Python code is linted with [black](https://black.readthedocs.io/en/stable/) and [Ruff](https://docs.astral.sh/ruff).

authentik runs on Python 3.14 at the time of writing this.

- Use native type-annotations wherever possible.
- Add meaningful docstrings when possible.
- Ensure any database migrations work properly from the last stable version (this is checked via CI)
- If your code changes central functions, make sure nothing else is broken.

### Documentation Style Guide

Refer to the full [Style Guide](../developer-docs/docs/style-guide.mdx) for details, but here are some important highlights:

- Our product name is authentik, with a lower-case "a" and a "k" on the end. Our company name is Authentik Security.

- We use sentence style case in our titles and headings.

- We use **bold** text to name UI components, and _italic_ text for variables.

- Use [MDX](https://mdxjs.com/) whenever appropriate. MDX, which uses React components, is useful for creating tabs, action buttons, and advanced content formatting.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/developer-docs/translation.md
================================================================================

---
title: Translations
---

Translations in authentik are handled in two places. Most of the text is defined in the frontend in `web/`, and a subset of messages is defined in the backend.

The frontend uses [@lit/localize](https://lit.dev/docs/localization/overview/), and the backend uses the built-in Django translation tools.

:::info
Please review the [Writing documentation](./docs/writing-documentation.md) guidelines as they apply to documentation too.
:::

## Online translation

To simplify translation you can use [Transifex](https://explore.transifex.com/authentik/authentik/), which has no local requirements.

## Local translation

### Prerequisites

- Node (any recent version should work, we use 16.x to build)
- Make (again, any recent version should work)
- Docker

### Frontend

Run `npm i` in the `/web` folder to install all dependencies.

Ensure the language code is in the `lit-localize.json` file in `web/`:

```json
    // [...]
    "targetLocales": [
        "en",
        "pseudo-LOCALE",
        "a-new-locale"
        // [...]
    ],
    // [...]
```

Afterwards, run `make web-i18n-extract` to generate a base .xlf file.

The .xlf files can be edited by any text editor, or using a tool such as [POEdit](https://poedit.net/).

To see the change, run `make web-watch` in the root directory of the repository.

### Backend

Backend translations are handled by `core-i18n-extract`.

Use Django's translation utility to declare the string, e.g.:

```python
from django.utils.translation import gettext as _

_("New text to be translated.")
```

Afterwards, run `make core-i18n-extract` to generate the updated translation files.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/developer-docs/releases/index.md
================================================================================

# Releasing authentik

### Creating a standard release

- Ensure a branch exists for the version family (for 2022.12.2 the branch would be `version-2022.12`)
- Merge all the commits that should be released on the version branch

    If backporting commits to a non-current version branch, cherry-pick the commits.

- Check if any of the changes merged to the branch make changes to the API schema, and if so update the package `@goauthentik/api` in `/web`
- Push the branch, which will run the CI pipeline to make sure all tests pass
- Create the version subdomain for the version branch ([see](https://github.com/goauthentik/terraform/commit/87792678ed525711be9c8c15dd4b931077dbaac2)) and add the subdomain in Netlify ([here](https://app.netlify.com/sites/authentik/settings/domain))
- Create/update the release notes

    #### For initial releases:
    - Copy `website/docs/releases/_template.md` to `website/docs/releases/v2022.12.md` and replace `xxxx.x` with the version that is being released

    - Fill in the section of `Breaking changes` and `New features`, or remove the headers if there's nothing applicable

    - Run `git log --pretty=format:'- %s' version/2022.11.3...version-2022.12`, where `version/2022.11.3` is the tag of the previous stable release. This will output a list of all commits since the previous release.

    - Paste the list of commits since the previous release under the `Minor changes/fixes` section.

        Run `make gen-changelog` and use the contents of `changelog.md`. Remove merged PRs from bumped dependencies unless they fix security issues or are otherwise notable. Remove merged PRs with the `website/` prefix.

    - Sort the list of commits alphabetically and remove all commits that have little importance, like dependency updates and linting fixes

    - Run `make gen-diff` and copy the contents of `diff.md` under `API Changes`

    - Update `website/sidebars.js` to include the new release notes, and move the oldest release into the `Previous versions` category.

        If the release notes are created in advance without a fixed date for the release, only add them to the sidebar once the release is published.

    - Run `make docs`

    #### For subsequent releases:
    - Paste the list of commits since the previous release into `website/docs/releases/v2022.12.md`, creating a new section called `## Fixed in 2022.12.2` underneath the `Minor changes/fixes` section

    - Run `make gen-changelog` and use the contents of `changelog.md`. Remove merged PRs from bumped dependencies unless they fix security issues or are otherwise notable. Remove merged PRs with the `website/` prefix.

    - Run `make gen-diff` and copy the contents of `diff.md` under `API Changes`, replacing the previous changes

    - Run `make docs`

- Run `bumpversion` on the version branch with the new version (i.e. `bumpversion --new-version 2022.12.2 minor --verbose`)
- Push the tag and commit
- A GitHub actions workflow will start to run a last test in container images and create a draft release on GitHub
- Edit the draft GitHub release
    - Make sure the title is formatted `Release 2022.12.0`
    - Add the following to the release notes

        ```
        See https://docs.goauthentik.io/releases/2022.12
        ```

        Or if creating a subsequent release

        ```
        See https://docs.goauthentik.io/releases/2022.12#fixed-in-2022121
        ```

    - Auto-generate the full release notes using the GitHub _Generate Release Notes_ feature

### Preparing a security release

- Create a draft GitHub Security advisory


- Request a CVE via the draft advisory
- If possible, add the original reporter in the advisory
- Implement a fix on a local branch `security/CVE-...`

    The fix must include unit tests to ensure the issue can't happen again in the future

    Update the release notes as specified above, making sure to address the CVE being fixed

    Create a new file `/website/docs/security/CVE-....md` with the same structure as the GitHub advisory

    Include the new file in the `/website/sidebars.js`

    Push the branch to https://github.com/goauthentik/authentik-internal for CI to run and for reviews

    An image with the fix is built under `ghcr.io/goauthentik/internal-server` which can be made accessible to the reporter for testing

- Check with the original reporter that the fix works as intended
- Wait for GitHub to assign a CVE
- Announce the release of the vulnerability via mailing list and Discord



### Creating a security release

- On the date specified in the announcement, retag the image from `authentik-internal` to the main image:

    ```
    docker buildx imagetools create -t ghcr.io/goauthentik/server:xxxx.x ghcr.io/goauthentik/internal-server:gh-cve-2022-xxx
    docker buildx imagetools create -t ghcr.io/goauthentik/server:xxxx.x.x ghcr.io/goauthentik/internal-server:gh-cve-2022-xxx
    ```

    Where xxxx.x is the version family and xxxx.x.x is the full version.

    This will make the fixed container image available instantly, while the full release is running on the main repository.

- Push the local `security/CVE-2022-xxxxx` branch into a PR, and squash merge it if the pipeline passes
- If the fix made any changes to the API schema, merge the PR to update the web API client
- Cherry-pick the merge commit onto the version branch
- If the fix made any changes to the API schema, manually install the latest version of the API client in `/web`
- Resume the instructions above, starting with the `bumpversion` step
- After the release has been published, update the Discord announcement and send another mail to the mailing list to point to the new releases





================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/developer-docs/docs/writing-documentation.md
================================================================================

---
title: Writing documentation
---


Writing documentation for authentik is a great way for both new and experienced users to improve and contribute to the project. We appreciate contributions to our documentation, from fixing typos and adding content to writing completely new topics.

The [technical documentation](https://docs.goauthentik.io) and our [integration guides](https://integrations.goauthentik.io/) are built, formatted, and tested using `npm`. The commands to build the content locally are defined in the `Makefile` in the root of the repository. Each command is prefixed with `docs-` or `integrations-` and corresponds to an NPM script within the `website` directory.

## Documentation subdomains

authentik documentation is deployed to different subdomains based on the git branch:

| Subdomain                                          | Git Branch       | Description                      |
| -------------------------------------------------- | ---------------- | -------------------------------- |
| [main.goauthentik.io](https://main.goauthentik.io) | `main`           | Latest changes and features      |
| [next.goauthentik.io](https://next.goauthentik.io) | `next`           | Upcoming release content         |
| [docs.goauthentik.io](https://docs.goauthentik.io) | Current release  | Official stable documentation    |
| version-YYYY-MM.goauthentik.io                     | Specific release | Historical version documentation |

## Guidelines

Adhering to the following guidelines will help us get your PRs merged more easily and quickly, with fewer edits needed.

- Ideally, when you are making contributions to the documentation, you should fork and clone our repo, then [build it locally](#set-up-your-local-build-tools), so that you can test the docs and run the required linting and spell checkers before pushing your PR. While you can do much of the writing and editing within the GitHub UI, you cannot run the required linters from the GitHub UI.

- After submitting a PR, you can view the Netlify Deploy Preview for the PR on GitHub, to check that your content rendered correctly, links work, etc. This is especially useful when using Docusaurus-specific features in your content.

- Please refer to our [Style Guide](./style-guide.mdx) for authentik documentation. Here you will learn important guidelines about not capitalizing authentik, how we format our titles and headers, and much more.

- Remember to use our templates when possible; they are already set up to follow our style guidelines, they make it a lot easier for you (no blank page frights!), and they keep the documentation structure and headings consistent.
    - [docs templates](./templates/index.md)
    - [integration guide template](https://integrations.goauthentik.io/applications#add-a-new-application)

## Setting up a docs development environment

### Prerequisites

- [Node.js](https://nodejs.org/en) (24 or later)
- [Make](https://www.gnu.org/software/make/) (3 or later)


### Clone and fork the authentik repository

```shell
git clone https://github.com/goauthentik/authentik
```

The documentation, integration guides, API docs, and the code are in the same [GitHub repo](https://github.com/goauthentik/authentik), so if you have cloned and forked the repo, you already have the docs and integration guides.

### Set up your local build tools

Run the following command to install or update the build tools for both the technical docs and integration guides.

```shell
make docs-install
```

This command installs or updates the build dependencies such as Docusaurus, Prettier, and ESLint. You should run this command when you are first setting up your writing environment, and also if you encounter build check fails either when you build locally or when you push your PR to the authentik repository. Running this command will grab any new dependencies that we might have added to our build tool package.

:::tip
If you have the [full development environment](../setup/full-dev-environment.mdx) installed you can run `make install` to get all of the latest build tools and dependencies, not just those for building documentation.
:::

## Writing or modifying technical docs

In addition to following the [Style Guide](./style-guide.mdx) please review the following guidelines about our technical documentation (https://docs.goauthentik.io/docs/):

- For new entries, make sure to add any new pages to the `/docs/sidebar.mjs` file.
  Otherwise, the new page will not appear in the table of contents to the left.

- Always be sure to run the `make docs` command on your local branch _before_ pushing the PR to the authentik repo. This command does important linting, and the build check in our repo will fail if the linting has not been done. In general, check on the health of your build before pushing to the authentik repo, and also check on the build status of your PR after you create it.

For our technical documentation (https://docs.goauthentik.io/docs/), the following commands are used:

### Build locally

```shell
make docs
```

This command is a combination of `make docs-lint-fix` and `make docs-build`. It is important to run this command before committing changes because linter errors will prevent the build checks from passing.

### Live editing

```shell
make docs-watch
```

Starts a local development server for the documentation site and opens a preview in your browser. This command will automatically rebuild your local documentation site in real time, as you write or make changes to the Markdown files in the `website/docs` directory.

## Writing or modifying integration guides

In addition to following the [Style Guide](./style-guide.mdx) please review the following guidelines about our integration guides (https://integrations.goauthentik.io/).

- For new integration documentation, please use the Integrations template in our [GitHub repo](https://github.com/goauthentik/authentik) at `/website/integrations/template/service.md`.

- For placeholder domains, use `authentik.company` and `app-name.company`, where `app-name` is the name of the application that you are writing documentation for.

- Make sure to create a directory for your service in a fitting category within [`/website/integrations/`](https://github.com/goauthentik/authentik/tree/main/website/integrations).

:::tip Sidebars and categories
You no longer need to modify the integrations sidebar file manually. This is now automatically generated from the categories in [`/website/integrations/categories.mjs`](https://github.com/goauthentik/authentik/blob/main/website/integrations/categories.mjs).
:::

When authoring integration guides, the following commands are used:

### Build locally

```shell
make integrations
```

This command is a combination of `make docs-lint-fix` and `make integrations-build`. This command should always be run on your local branch before committing your changes to a pull request to the authentik repo. It is important to run this command before committing changes because linter errors will prevent the build checks from passing.

### Live editing

```shell
make integrations-watch
```

Starts a local development server for the integrations site and opens a preview in your browser. This command will automatically rebuild your local integrations site in real time, as you write or make changes to the Markdown files in the `website/integrations` directory.

## Developing the glossary

The [authentik glossary](/core/glossary/) provides definitions for both industry-standard terms (like LDAP, OAuth2, SAML) and authentik-specific concepts (like Flows, Stages, Blueprints).

### Adding a new glossary term

1. Create a new `.mdx` file in `website/docs/core/glossary/terms/` (e.g., `my-term.mdx`).

2. Add frontmatter with the required metadata:

```mdx
---
title: My Term
sidebar_custom_props:
    termName: My Term
    tags:
        - Category Name
    authentikSpecific: true # Only for authentik-specific terms
    shortDescription: Brief one-line description.
    longDescription: Detailed explanation with context, use cases, and examples.
---
```

### Glossary metadata fields

- **`termName`** (required): The display name of the term
- **`tags`** (required): Array of category tags for organizing terms. Common tags include:
    - Core Concepts
    - Flows
    - OAuth2/OIDC
    - SAML
    - Directory
    - Configuration
    - Protocols
- **`authentikSpecific`** (optional): Set to `true` for authentik-specific terms. This displays an "authentik specific" badge next to the term name to distinguish it from industry-standard terminology. Omit this field for industry-standard terms.
- **`shortDescription`** (required): Concise one-line summary displayed in the main glossary view
- **`longDescription`** (optional): Detailed explanation shown when users expand the term

### Formatting guidelines

- Use backticks for inline code: \`application\`
- Keep `shortDescription` to one sentence
- In `longDescription`, you can use multiple paragraphs separated by blank lines

## Page routing and URLs

Every documentation page you see on our website starts as a simple Markdown file in our repository. When you create or edit these files, our build system automatically transforms them into web pages with predictable URLs.

### Converting file paths to URLs

Let's take a look at the file path of the [Style Guide page](https://docs.goauthentik.io/developer-docs/docs/style-guide/):

```text
/website/docs/developer-docs/docs/style-guide.mdx
```

Compared to the URL path of this page, there are a few differences:

- The `website/docs` prefix is dropped.
- File extensions are removed.
- A trailing slash is added.

This results in the following URL path:

```text
https://docs.goauthentik.io/developer-docs/docs/style-guide/
```

The final published URL is made possible with a combination of [Docusaurus's routing system](https://docusaurus.io/docs/advanced/routing) and [Netlify's redirects](https://docs.netlify.com/routing/redirects/).

### Sidebar files

The sidebar files define the navigation structure of the documentation pages.

- **Documentation**: [`website/docs/sidebar.mjs`](https://github.com/goauthentik/authentik/blob/main/website/docs/sidebar.mjs)
- **Integrations**: [`website/integrations/sidebar.mjs`](https://github.com/goauthentik/authentik/blob/main/website/integrations/sidebar.mjs)
    - Automatically generated from the categories in [`/website/integrations/categories.mjs`](https://github.com/goauthentik/authentik/blob/main/website/integrations/categories.mjs).
- **API Reference**: [`website/api/sidebar.mjs`](https://github.com/goauthentik/authentik/blob/main/website/api/sidebar.mjs)
    - Mostly automatically generated from authentik API schema.

### Redirects

Sometimes we need to move pages or change URLs. Instead of breaking bookmarks and links, we can define a redirect to automatically send readers from old URLs to new ones.

All our redirects are defined within three files:

- **Documentation**: [`website/docs/static/_redirects`](https://github.com/goauthentik/authentik/blob/main/website/docs/static/_redirects)
- **Integrations**: [`website/integrations/static/_redirects`](https://github.com/goauthentik/authentik/blob/main/website/integrations/static/_redirects)
- **API Reference**: [`website/api/static/_redirects`](https://github.com/goauthentik/authentik/blob/main/website/api/static/_redirects)

A `_redirects` file contains a list of rules that define how to handle requests, each of which has the following format:

1. The source URL path (i.e the old URL to match against).
2. The destination URL path (i.e. the new URL to redirect to).
3. The HTTP status code to use when redirecting, followed by an exclamation mark (`!`).

For example, if we moved our applications page:

```text title="website/docs/static/_redirects"
# Source URL Path  | Destination URL Path           | Status Code
/core/applications   /add-secure-apps/applications/   302!
```

Anyone visiting the old URL will automatically land on the new page using a combination of Netlify and Docusaurus.

#### Initial page loads (server-side)

When a reader first visits a documentation page or refreshes their browser:

1. Their browser requests the URL from our server (Netlify).
2. Netlify checks if that exact page exists.
3. If not, it checks our `_redirects` file for a matching rule.
4. The server sends back the correct page, or a 404 if no matching rule exists.

#### Navigating between pages (client-side)

When a reader clicks a link to another documentation page:

1. Docusaurus intercepts the click (no server request needed).
2. The URL in the browser's address bar changes.
3. Docusaurus router fetches the new page content without a full reload.

If Docusaurus's router attempts to render a page that does not exist, the `_redirects` file will be used to determine if a redirect rule should be applied, without a server request or a full reload.

Whether the reader is viewing a page for the first time or navigating between pages, this arrangement allows us to have a single source of truth for all URLs, ensuring that each page remains consistently accessible across authentik versions and throughout our three Docusaurus deployments (Topics, Integrations, and API).

### Updating a page's URL

:::danger[Every URL is a promise]

When someone bookmarks a page or shares a link, they expect it to keep working.

**Before changing any URL, ask yourself:**

- [x] Is this move absolutely necessary?
- [x] Could better organization be achieved without moving files?
- [x] Will this help or confuse readers migrating between authentik versions?

Remember, [Cool URIs don't change!](https://www.w3.org/Provider/Style/URI)
:::

Moving a documentation page to a new location requires updating a `sidebar.mjs` and `_redirects` file.

1. Take note of the page's current URL path in the browser's address bar.
2. Move the Markdown file to the new location.
3. Add a new redirect rule to the `_redirects` file in the respective [documentation directory](#redirects).
4. Update the `sidebar.mjs` file in the respective [documentation directory](#redirects).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/developer-docs/docs/style-guide.mdx
================================================================================

---
title: Style Guide
---

This Style Guide provides guidelines to ensure that the authentik documentation is consistent, clear, and easy to follow. It standardizes aspects like phrasing, formatting, tone, and structure across all documentation.

We appreciate all contributions to our documentation — whether it's fixing a typo, adding new content, or writing an entirely new topic. To help us review and merge your contributions more efficiently, please follow our [writing documentation](./writing-documentation.md) guidelines. If you notice any inconsistencies, feel free to open an [Issue](https://github.com/goauthentik/authentik/issues) or submit a [Pull Request](https://github.com/goauthentik/authentik/pulls) to fix them.

- [General Style Guidelines](#general-style-guidelines)
- [Terminology](#terminology)
- [Writing Style](#writing-style)
- [Word Choices](#word-choices)
- [Formatting Guidelines](#formatting-guidelines)
- [Component-Based Formatting](#component-based-formatting)
- [Error Message Formatting and Troubleshooting](#error-message-formatting-and-troubleshooting)
- [Accessibility Best Practices](#accessibility-best-practices)
- [Inclusive Language](#inclusive-language)
- [Images and Media](#images-and-media)
- [Document Structure and Metadata](#document-structure-and-metadata)

---

## General style guidelines

### Logical order

- Documentation should be structured to follow the natural order of tasks, making it easier for users to follow. Organize sections in a manner that reflects the actual workflow used to complete tasks.

- When writing procedural documentation (How Tos) the steps should follow the workflow in the UI, specifying the exact pages to navigate and the precise fields, tabs, etc., to select or complete. Present the UI components in the document in the same order they appear in the UI.

### Headings

Use headings (sub-titles) to break up large blocks of text, making it easier for users to navigate the content and find specific sections quickly.

### Look and feel of the docs

In general, the visual, aesthetics of the technical documentation is intended to be lean and clean. Both the content (shorter sentences, concise instructions, etc) and the layout strive to have a clean, uncluttered look, with restrained use of colors and large callouts or announcements. Relatedly, the colors used for our Info and Warning callouts, light blue and light yellow respectively, are reserved for those purposes only.

### Cross-references

Always include cross-references to related content. If a concept is referenced elsewhere in the documentation, link to the relevant section to provide users with additional context or instructions.

### Relative vs. absolute paths

Use relative paths when linking to other documentation files. This will ensure links are automatically updated if file paths change in the future. If you are linking between another authentik resource that is not in the same repository and our regular technical docs, then use an absolute path.

### Markdown file type

The standard file type for documentation is `.md`. Use `.mdx` only if React components, such as interactive elements, are required.

### OS-agnostic, clarify where needed

Try to write procedural (How To) docs generically enough that it does not endorse or force a specific operating system. If it is necessary to specify a specific OS be sure to label it clearly. Consider using tabs (with MDX) to show the different OSes.

---

## Terminology

### authentik product name and terms

- The product name **authentik** should always be written with a lowercase "a" and a "k" at the end, even if it begins a sentence.

- The company name is **Authentik Security, Inc.**, but for non-legal documentation, you may shorten it to **Authentik Security**.

- When referring to the authentik Admin interface, capitalize "Admin" like it is in the UI, but do not bold the phrase "Admin interface" unless in a sentence that explicitly says "Click on **Admin interface**". However, if you are referring to a user or role that is an administrator, or has administrative rights, then do not capitalize it and spell out the full word "administrator" or "administrative".

### Industry terms and technology names

- When referring to external tools or industry terms, always use the exact capitalization and naming conventions that the product or company uses. Refer to their website or official documentation for the proper formatting. For example, use "OAuth", "SAML", or "Docker" as per the official conventions.
- Avoid abbreviations unless they are well-known and widely recognized (e.g., SSO, MFA, RBAC).
- If an acronym is used less frequently, spell out its full meaning when first mentioned on the page, followed by the acronym in parentheses. In some cases the acronym can come first, followed by the full term in parentheses.

### Trademarks and legal terms

- Respect third-party trademarks. Use the correct symbols (™, ®) where applicable (e.g., "GitHub®", "Okta™") in the _first_ instance of the name.
- When mentioning third-party products, follow their branding guidelines (e.g., "GitHub", not "Github").
- Where appropriate, include required legal disclaimers when referencing external services or integrations.

---

## Writing style

### Tone

The tone of the authentik documentation should be friendly but professional. It should be approachable, yet not overly casual. When appropriate, address the reader directly using second-person pronouns (e.g., "Next, you need to configure the login settings").

### Language

The documentation uses **American English** spelling conventions (e.g., "customize" instead of "customise").

### Voice

Use **active voice** and **present tense** for clear, direct communication.

- **DON'T:** "The Applications page will be loaded."
- **DO:** "The Applications page displays."

### User-friendly phrasing

Avoid phrasing that blames the user. Be subjective and polite when providing instructions.

- **DON'T:** "Never modify the default file."
- **DO:** "We recommend that you do not modify the default file, as doing so may result in unexpected issues."

### Punctuation

For Ken's sake, and many others, try to not use too many commas (avoid commaitis). Use a comma when needed to separate clauses, or for "slowing the pace" or clarity. Please **do** use the [Serial comma](https://en.wikipedia.org/wiki/Serial_comma) (also known as the Oxford comma).

In [lists](#lists), add a period at the end of a bulleted item if it is a complete sentence. Try not to mix incomplete and complete sentences in the same list.

### Capitalization

#### Titles and headers

Titles and headers (H1, H2, H3, etc.) should follow **sentence case capitalization**, meaning only the first word is capitalized, except for proper nouns or product names. For more information, see [below](#titles-and-headers).

#### Following a colon

Whether to capitalize after a colon depends on the context. Typically, we do not capitalize the first word after a colon _unless_ it's a proper noun or if it is the start of a complete sentence. If the colon introduces a list, do not capitalize the first word unless it's a proper noun. In headings and titles, capitalize the first word after the colon.

---

## Word choices

### "May" versus "Might" versus "Can"

- Typically, avoid using the word "may" in technical writing, as it implies permission rather than ability to perform an action. Instead, use **"can"** to suggest possibility.
- **"Might"** should be used to indicate that something could happen under certain conditions, but use it sparingly. It implies unpredictability, which can be undesirable in software documentation.
    - **DON'T:** "You may use an Expression policy to enforce MFA adherence."
    - **DO:** "You can use an Expression policy to enforce MFA adherence."
    - **DO:** "Values might differ depending on the source of the property mappings."

### "Login", "Log in", and "Log in to"

- As a noun or descriptive term, use **login** (e.g., "The login panel").
- As a verb, use **"log in"** (e.g., "This stage prompts the user to log in").
- As a verb followed by the preposition **"to"**, use **"log in to"** (e.g., "Log in to the application").

### Use "that" as a conjunction

It's important to use "that" as a conjunction to introduce a dependent clause, or as a "connection" between a noun and a verb ("The provider that you created in Step 3."). Including "that" as a conjunction helps non-native English speakers more easily parse phrases, and improves output for translation tools.

- **DO:** "Ensure that the new user's password is valid."
- **DON'T:** "Ensure the new user's password is valid."

### "which" vs "that"

The easiest way to remember when to use "which" versus "that" is:

- If the second part (clause) of the sentence is required to understand the first part, use "that." If the second clause is only additional info, use "which".

For more information, see [this guide](https://www.grammarly.com/blog/which-vs-that/).

### "since" (time-based) vs "because" (causal)

When writing about a status or anything that is causal ("this happened because of that"), use the word "because". Use the word "since" for time-based topics (this will be rare in technical writing).

### Avoid using "once" (numeric) to mean "after" (time-based).

When writing out steps in a procedural topic, avoid starting with "Once...". Instead, you can say "After you have created the scope mapping...".

---

## Formatting guidelines

### Fonts and font styling

- When referring to internal components in authentik, like the policy engine, or blueprints, do not use any special formatting, and do not capitalize. Link to the relevant documentation when possible.

- When referring to authentik functionality and features, such as flows, stages, sources, or policies, do not capitalize and do not use bold or italic text. When possible link to the corresponding documentation.

- Use **bold** to highlight:
    - UI elements such as field names, labels, buttons, or options (e.g., **Save** button, **Username** field).
    - Key actions in instructions (e.g., **Click Next**).

- Use _italic_ for:
    - Emphasis, but sparingly, to avoid overuse. For example, you can use italics for important terms or concepts on first mention in a section. Do not use italics to indicate a variable or placeholder; instead use angle brackets as described under [Variables](#variables).

- Use `code formatting` for:
    - Commands (e.g., `kubectl get nodes`).
    - File paths, file names, and directory names (e.g., `/usr/local/bin/`).
    - Inline code snippets (e.g., `.env`).

### Lists

Add a period at the end of a bulleted item if it is a complete sentence. Try not to mix incomplete and complete sentences in the same list.

If there is a [colon](#following-a-colon) used in a bulleted list item, follow the capitalization rules.

### Notes and warnings

We use Info, Warning, and Danger boxes, to provide supplemental information. Info boxes can optionally have a title, but do not use a title with Warning or Danger boxes.

Use the following syntax for these components:

**Info**:

```md
::: info add-title-here
This is a tip or general note.
:::
```

**Warnings**:

```md
:::warning
This level is for more serious situations: an action cannot be undone, a process might be canceled, etc.
:::
```

**Critical warnings** (for irreversible actions):

```md
:::danger
This level is for extremely serious situations, such as an action permanently removing data.
:::
```

### URLs

- When mentioning URLs in text or within procedural instructions, omit code formatting. For instance: "In your browser, go to https://example.com."
- For URLs entered as values or defined in fields, enclose any variables inside angle brackets (`< >`) and use underscores between words. See more about variables below (#variables).

### Variables

To clearly indicate terms or values that are placeholders and require user input, enclose any variables inside angle brackets (`< >`) and use underscores between words to clearly indicate that these are placeholders that require user input.

Examples:

- `https://authentik.company/application/o/<slug>/.well-known/openid-configuration`
- "Add the configuration setting: `<first_name>`."

### Titles and headers

- Titles and headers (H1, H2, H3) should follow **sentence case capitalization**, meaning only the first word is capitalized, except for proper nouns or product names.
    - **DO:** "Configure the Google Workspace provider"
    - **DON'T:** "CONFIGURE THE GOOGLE WORKSPACE PROVIDER"
    - **DON'T:** "Configure The Google Workspace Provider"

- Ensure that titles and headers are descriptive and clearly convey the purpose of the section. Avoid vague titles like "Overview." Instead, opt for something more specific, like "About authentik policies."

- Use the **imperative verb form** in procedural topics, not gerunds. For example, use "Configure your instance" instead of "Configuring your instance."

### Examples

When you want to show an example (say, a code snippet), start on a new line, use bold text for the word "Example", and a colon, like this:

**Example**:

    This expression policy uses an expression based on the user's name:
    ```python
    if request.context["pending_user"].username == "marie":
        return True
    return False
    ```

### Code blocks

When you want to show sections of code use **Code blocks** to provide syntax highlighting, a copy button, line numbering and line highlighting:

```text
` ` ` yaml showLineNumbers {5} title="/etc/wazuh-indexer/opensearch-security/roles_mapping.yml"
all_access:
reserved: true
hidden: false
backend_roles:
    - "wazuh-admin"
    - "admin"
hosts: []
users: []
and_backend_roles: []
description: "Maps admin to all_access"
` ` `
```

Which is rendered as:

```yaml showLineNumbers {5} title="/etc/wazuh-indexer/opensearch-security/roles_mapping.yml"
all_access:
reserved: true
hidden: false
backend_roles:
    - "wazuh-admin"
    - "admin"
hosts: []
users: []
and_backend_roles: []
description: "Maps admin to all_access"
```

- ` ` ` `yaml `defines the language used for syntax highlighting. Other languages can be used such as`jsx`, `python`, `bash`, and `text`.

Optional configurations:

- `showLineNumbers`: enables line numbering.
- `title=" "`: defines the title displayed at the top (e.g., filenames).
- `{5}`: highlights specific lines. Ranges and lists are allowed (e.g., `{5, 7, 9-11}`).
- `// highlight-next-line`: highlights the next line within a code block.
- `// highlight-start` and `// highlight-end`: highlight multiple lines.

For more details, see the [Docusaurus code block documentation](https://docusaurus.io/docs/markdown-features/code-blocks).

### Tables

Use tables to compare options, list parameters, or summarize information. Ensure tables are concise and avoid nesting complex content. Only use a table when there are 4 or more items. For only 2 or 3 items, use a bullet list.

### Lists

- Use bullet points for unordered lists.
- Use numbered lists for sequential steps.
- Keep list items parallel in structure.

---

## Component-based formatting

### Tabs for multiple configurations

Use **Tabs** to display different configurations (e.g., setting up authentication with OIDC vs. SAML) to help users navigate between options. Default to the easier or more common option. For example:

```jsx

```

---

## Error message formatting and troubleshooting

When documenting errors, follow this structure:

1. **Error Message**: Display the error in a code block.
2. **Possible Causes**: List common reasons for the error.
3. **Solutions**: Provide step-by-step fixes or a work-around if there is one.

**Example**:

- **Error message**:

    ```sh
    Error: Authentication failed. Invalid credentials.
    ```

- **Possible causes**:
    - Incorrect username or password.
    - Account locked due to multiple failed attempts.

- **Solutions**:
    - Verify your credentials.
    - Reset your password using the **Forgot Password** link.
    - Contact your administrator if the account is locked.

---

## Accessibility best practices

- **Alt text for images**: Describe the purpose of the image, not just its appearance. For example, use "Screenshot of the login form" instead of "Image of a form."
- **Heading hierarchy**: Use headings in order (H1 → H2 → H3) to support screen readers.
- **Color usage**: Avoid using color as the sole method of conveying information (e.g., "Click the red button"). Instead, use descriptive labels to ensure accessibility.
- **Descriptive link text**: Provide descriptive link text. Avoid using generic terms like "Click here". Be specific about where the link will take the user.
    - **DON'T:** "Click here."
    - **DO:** "See the [Authentication Settings](/) for more details."

---

## Inclusive language

- Use **gender-neutral pronouns** like "they/them" instead of "he/she" (e.g., "The user should check their settings").
- Avoid **ableist terms** such as "dumb" or "lame"; use "non-functional" or "unavailable" instead.
- **Avoid idioms** that may not translate well (e.g., instead of "hit a home run" use "achieve success").

---

## Images and media

- **Screenshots**:
    - Use screenshots very sparingly, only for very complex UIs. If there are screenshots, update any existing ones if the UI changes.
    - Crop to focus on relevant elements, use red arrows or circles to call out the important element.
    - Add descriptive alt text (e.g., "Screenshot of the Provider configuration page").
- **Diagrams**:
    - Use [Mermaid](https://mermaid.js.org/) for creating diagrams directly in markdown. Mermaid is our preferred tool for documentation diagrams as it allows for version control and easy updates.
    - For more complex diagrams, you can use tools like [Draw.io](https://draw.io). Ensure high contrast and text descriptions.
- **authentik icons**:
    - For authentik icons in integration guides, reference assets from the user's own self-hosted instance to avoid external calls, for example: `https://authentik.company/static/dist/assets/icons/icon.svg`

---

## Document structure and metadata

- **Front matter**: Include a title and optional summary. You can also add badge metadata in the front matter:

    ```md
    ---
    title: Getting Started
    description: Install and configure authentik in 5 minutes.
    authentik_version: "2025.4" # Semantic version when feature was introduced (Optional)
    authentik_preview: true # For preview features (Optional)
    authentik_enterprise: true # For enterprise features (Optional)
    support_level: "authentik" # For integrations: Support level: "authentik" (tested by team) or "community" (community maintained)
    ---
    ```

    Note: Badges should be defined in the front matter, not in the markdown content. The system will automatically display the appropriate badges based on the front matter metadata.

- **Directives**: You can also use directives in your markdown content to add badges inline:
    - `:ak-version[2025.4]` - Shows when a feature was introduced (requires semantic version)
    - `:ak-preview` - Indicates preview features
    - `:ak-enterprise` - Indicates features in our Enterprise offering

    Example usage in a heading:

    ```md
    # New Feature :ak-version[2025.4] :ak-preview
    ```

    Note: When using directives, they should be placed at the end of the heading or paragraph where they apply.

- **SEO**: Use keywords in titles and headings to improve searchability. Include relevant terms that users might search for, but avoid keyword stuffing. Focus on natural, descriptive language that accurately represents the content.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/developer-docs/setup/full-dev-environment.mdx
================================================================================

---
title: Full development environment
sidebar_label: Full development
tags:
    - development
    - contributor
    - backend
    - frontend
    - docker
---


## Prerequisites

Before you begin, ensure you have the following tools installed. You can run the [provided script](#3-installing-platform-specific-dependencies) below in **Installing platform-specific dependencies** to install these required tools.

- [Python](https://www.python.org/) (3.14)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Latest stable release)
- [Rust](https://rust-lang.org/learn/get-started/) (We provide a `rust-toolchain.toml` file for the correct version, and we use the nightly toolchain to run formatting with rustfmt.)
- [Go](https://go.dev/) (1.26 or later)
- [Node.js](https://nodejs.org/en) (24 or later)
- [PostgreSQL](https://www.postgresql.org/) (16 or later)
- [Docker](https://www.docker.com/) (Latest Community Edition or Docker Desktop)
- [Docker Compose](https://docs.docker.com/compose/) (Compose v2)
- [Make](https://www.gnu.org/software/make/) (3 or later)

### Understanding the architecture

authentik is primarily a Django application running under gunicorn, proxied by a Go application that serves static files. Most functions and classes have type hints and docstrings. For better code navigation, we recommend installing a Python type-checking extension in your IDE.

## 1. Prepare your local working repository

Verify that you have a local working repository of authentik and that it is initialized and up-to-date with the [authentik repository](https://github.com/goauthentik/authentik).

Unless otherwise specified, all commands described below should be run from the project root of your local authentik repository.

## 2. Set up required services

authentik depends on several external services:

- [PostgreSQL](https://www.postgresql.org/) for database storage
- [Zenko CloudServer (S3)](https://www.zenko.io/cloudserver/) for object storage
- [Sentry Spotlight](https://spotlightjs.com/) for error tracking and visualization

The easiest way to set up these services is using the provided Docker Compose configuration:

```shell
docker compose -f scripts/compose.yml up -d
```

## 3. Installing platform-specific dependencies


## 4. Set up the backend

:::info
All `make` commands must be executed from the root directory of your local authentik Git repository.
:::

### Install dependencies

Install all required JavaScript and Python dependencies and create an isolated Python environment:

```shell
make install
```

### Generate development configuration

Create a local configuration file that uses the local databases for development:

```shell
make gen-dev-config
```

### Initialize the database

Run all migrations with the following command:

```shell
make migrate
```

:::info
If you ever want to start over, use `make dev-reset`, which drops and restores the authentik PostgreSQL database to the state it was in after you ran `make migrate`.
:::

## 5. Running authentik

Now that the backend has been set up and built, you can start authentik. In two different tabs in your terminal, run the following commands from the root of your installation directory:

```shell
make run-server
```

```shell
make run-worker
```

:::info
The very first time a worker runs, it might need some time to clear the initial task queue. Adjust [`AUTHENTIK_WORKER__THREADS`](../../../install-config/configuration/#authentik_worker__threads) as required.
:::

Both processes need to run to get a fully functioning authentik development environment.

### Initial setup

To set a password for the default admin user (**akadmin**):

1. Navigate to http://localhost:9000/if/flow/initial-setup/ in your browser.
2. Follow the prompts to set up your admin account.

From now on, you can access authentik at http://localhost:9000 using the credentials you defined in Step 2.

## 6. Build the frontend

Even if you're not planning to develop the UI, you need to build the frontend because no compiled bundle is included by default. Run the following command to build the authentik UI:

```shell
make web-build
```

For real-time feedback you can view the UI as you make changes. Run this command and then in your browser go to http://localhost:9000/.

```shell
make web-watch
```

### Hot-reloading

When `AUTHENTIK_DEBUG` is set to `true` (the default for the development environment), the authentik server automatically reloads whenever changes are made to the code. However, due to instabilities in the reloading process of the worker, that behavior is turned off for the worker. You can enable code reloading in the worker by manually running `uv run ak worker --watch`.

## Troubleshooting

### Recovery key

If you can no longer log in or the authentication flow repeats (perhaps due to an incorrectly configured stage or a failed flow import), you can create a recovery key by running this command in your terminal:

`uv run ak create_recovery_key 10 akadmin`

Copy the generated recovery key and paste it into the URL, after the domain. For example:

`http://localhost:9000/recovery/use-token/ChFk2nJKJKJKY9OdIc8yv6RCgpGYp5rdndBhR6qHoHoJoWDdlvLuvU/`

## End-to-End (E2E) Setup

Start the E2E test services with the following command:

```shell
docker compose -f tests/e2e/compose.yml up -d
```

You can then view the Selenium Chrome browser via http://localhost:7900/ using the password: `secret`.

Alternatively, you can connect directly via VNC on port `5900` using the password: `secret`.

:::info
When using Docker Desktop, host networking needs to be enabled via **Docker Settings** > **Resources** > **Network** > **Enable host networking**.
:::

## Contributing code

### Before submitting a pull request

Ensure your code meets our quality standards by running:

1. **Code linting**:

    ```shell
    make lint-fix
    make lint
    ```

2. **Generate updated API documentation**:

    ```shell
    make gen
    ```

3. **Format frontend code**:

    ```shell
    make web
    ```

4. **Run tests**:

    ```shell
    make test
    ```

You can run all these checks at once with:

```shell
make all
```

### Submitting your changes

After your code passes all checks, submit a pull request on [GitHub](https://github.com/goauthentik/authentik/pulls). Be sure to:

- Provide a clear description of your changes
- Reference any related issues
- Update any related documentation
- Follow our code and documentation [style guidelines](../../contributing/#style-guides)
- Include tests for your changes where appropriate

Thank you for contributing to authentik!



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/developer-docs/setup/index.mdx
================================================================================

---
title: Development environment
description: Choose how you want to run and work on authentik.
---


Pick the setup that fits your workflow: full stack, frontend-only, or just the docs and grab some debugging tips along the way.




================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/developer-docs/setup/debugging.md
================================================================================

---
title: Debugging authentik
---

This page describes how to debug different components of an authentik instance, running either in production or in a development setup. To learn more about the structure of authentik, refer to our [architecture documentation](../../core/architecture.md).

## authentik Server & Worker (Python)

The majority of the authentik codebase is in Python, running in Gunicorn for the server and Dramatiq for the worker. These instructions show how this code can be debugged or inspected. The local debugging setup requires the setup described in [Full development environment](./full-dev-environment.mdx).

Note that authentik uses [debugpy](https://github.com/microsoft/debugpy), which relies on the "Debug Adapter Protocol" (DAP). These instructions demonstrate debugging using [Visual Studio Code](https://code.visualstudio.com/), however they should be adaptable to other editors that support DAP.

To enable the debugging server, set the environment variable `AUTHENTIK_DEBUGGER` to `true`. This will launch the debugging server (by default on port _9901_).

With this setup in place, you can set Breakpoints in VS Code. To connect to the debugging server, run the command `> Debug: Start Debugging` in VS Code.

![](./debug_vscode.png)

:::info
Note that due to the Python debugger for VS Code, when a Python file in authentik is saved and the Django process restarts, you must manually reconnect the Debug session. Automatic re-connection is not supported for the Python debugger (see [here](https://github.com/microsoft/vscode-python/issues/19998) and [here](https://github.com/microsoft/vscode-python/issues/1182)).
:::

#### Debug the server or the worker

Whichever process is first started listens on port `9901`. Additional processes started after that will then try to listen on the same port, which will fail, and will simply not start the debugger in that case.

#### Debugging in containers

When debugging an authentik instance running in containers, there are some additional steps that need to be taken in addition to the steps above.

A local clone of the authentik repository is required to set breakpoints in the code. The locally checked out repository must be on the same version/commit as the authentik version running in the containers. To check out version 2024.12.3, for example, run `git checkout version/2024.12.3`.

The debug port needs to be accessible on the local machine. By default, this is port 9901. Additionally, the container being debugged must be started as `root`, because additional dependencies need to be installed on startup.

When running in Docker Compose, a file `compose.override.yml` can be created next to the authentik `compose.yml` file to expose the port, change the user, and enable debug mode.

```yaml
services:
    # Replace `server` with `worker` to debug the worker container.
    server:
        user: root
        healthcheck:
            disable: true
        environment:
            AUTHENTIK_DEBUGGER: "true"
            AUTHENTIK_LOG_LEVEL: "debug"
        ports:
            - 9901:9901
```

After re-creating the containers with `AUTHENTIK_DEBUGGER` set to `true` and the port mapped, the steps are identical to the steps above.

If the authentik instance is running on a remote server, the `.vscode/launch.json` file needs to be adjusted to point to the IP of the remote server. Alternatively, you can forward the debug port via an SSH tunnel, using `-L 9901:127.0.0.1:9901`.

## authentik Server / Outposts (Golang)

Outposts, as well as some auxiliary code of the authentik server, are written in Go. These components can be debugged using standard Golang tooling, such as [Delve](https://github.com/go-delve/delve).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/developer-docs/setup/frontend-dev-environment.md
================================================================================

---
title: Frontend development environment
sidebar_label: Frontend development
tags:
    - development
    - contributor
    - frontend
    - docker
---

If you're focusing solely on frontend development, you can create a minimal development environment using Docker and Node.js. This setup allows you to make and preview changes to the frontend in real-time, without needing to interact with the backend.

### Prerequisites

- [Node.js](https://nodejs.org/en) (24 or later)
- [Docker](https://www.docker.com/) (Latest Community Edition or Docker Desktop)
- [Docker Compose](https://docs.docker.com/compose/) (Compose v2)
- [Make](https://www.gnu.org/software/make/) (3 or later)

### Instructions

1. Clone the Git repo to your development machine and navigate to the authentik directory.

    ```shell
    git clone https://github.com/goauthentik/authentik
    cd authentik
    ```

2. Run the following to create a `.env` file in the `lifecycle/container` directory of the repository to configure the Docker Compose environment.

    ```shell
    echo "PG_PASS=$(openssl rand -base64 36 | tr -d '\n')" >> ./lifecycle/container/.env
    echo "AUTHENTIK_SECRET_KEY=$(openssl rand -base64 60 | tr -d '\n')" >> ./lifecycle/container/.env
    echo "AUTHENTIK_IMAGE=ghcr.io/goauthentik/dev-server" >> ./lifecycle/container/.env
    echo "AUTHENTIK_TAG=gh-next" >> ./lifecycle/container/.env
    echo "AUTHENTIK_OUTPOSTS__CONTAINER_IMAGE_BASE=ghcr.io/goauthentik/dev-%(type)s:gh-next" >> ./lifecycle/container/.env
    echo "AUTHENTIK_LOG_LEVEL=debug" >> ./lifecycle/container/.env
    echo 'GIT_BUILD_HASH="dev"' >> ./lifecycle/container/.env
    ```

3. Create a Docker Compose override file (`compose.override.yml`) in the root of the repository. This will override the volume configurations for the local configuration file (`local.env.yml`) and mount the directory for the frontend code (`web`) into the docker containers. Docker will automatically mount the web files generated by the build process. The `local.env.yml` mount is optional, but allows you to override the default configuration.

    ```yaml title="compose.override.yml"
    services:
        server:
            volumes:
                - ./web:/web
                - ./local.env.yml:/local.env.yml
    ```

4. From the repository root, run the frontend build script. This will install the npm packages needed to run the frontend project and start the project in watch mode.

    ```shell
    make node-install
    make web-watch
    ```

5. In a new terminal, navigate to the cloned repository root and start the backend containers with Docker Compose.

    ```shell
    docker compose -f lifecycle/container/compose.yml up -d
    ```

You can now access authentik on http://localhost:9000 (or https://localhost:9443).

You might also want to complete the initial setup under `/if/flow/initial-setup/`.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/developer-docs/hackathon/index.md
================================================================================

---
title: Hackathon 2023
---

![hackathon-image](./horizontal-brandon-frie-rdHeGGn7rwQ-unsplash.jpg)

**REGISTRATION NOW CLOSED. PLEASE JOIN US FOR A FUTURE AUTHENTIK HACKATHON.**

^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^

## Join us for our first authentik hackathon!

Everyone is welcome; we will work on code, docs, and anything else that looks interesting and challenging.

Moderators will be available for most US and European hours, so if participants have questions during the multi-day event, or if a PR needs a technical review, we are here for you.

Prizes? Why, Yes! We've got a total prize pool of $5000 and a bunch of cool authentik-branded socks and, indubitably, GitHub fame.

## When

July 26-30, 2023

- Kickoff meeting is on Wednesday, July 26th, at 8:00am Pacific USA (UTC -7), 5:00pm in Central Europe (UTC +2), and 8:30pm in Mumbai (UTC +5.30)
- Check-in calls on Thursday and Friday, for one hour, at the same times as above.
- Wrap-up and first demos on Saturday, starting at same times as above.
- Final demos, voting, and awards on Sunday! Yep, same times as above.

## Where

Online, in our [GitHub repo](https://github.com/goauthentik/authentik), and on Discord in our [#hackathon23 channel](https://discord.com/channels/809154715984199690/1110948434552299673) for our Kickoff call, check-ins, and the wrap-up and awards events. We will also use the #hackathon23 channel throughout the entire five days for questions and general chatting. Be sure to first visit our [welcome-info-rules channel](https://discord.com/channels/809154715984199690/813452440660606986) to review our code of conduct and see the latest posts about the hackathon.

## Take a look on GitHub

If you already know what you and/or your team want to work on, you can open an [Issue](https://github.com/goauthentik/authentik/issues) using our template for all hackathon Issues at any time (why not now?) and add the `hackathon` label. Then, when you register, enter the Issue number that you opened on your registration form. This way, on Kickoff Day we can easily match participants with their Issue of interest.

During the Kickoff call, there will be time to peruse existing Issues and add emotes to indicate your interest in working on it (or having it worked on!)

- 🚀 I want to work on this
- ❤️ I want to see this worked on

## Agenda

- **Wednesday, July 26th**: Kickoff, voting for topics to work on, teams formed, participants select the Issue/team they are going to work on, and get their environment set up. After the online kickoff, you can start your work at any time.

- **Thursday July 27th**: HackDay #1: participants working on their PRs, a one-hour Check-in call

- **Friday, July 28th**: HackDay #2: participants working on their PRs, a one-hour Check-in call

- **Saturday, July 29th**: an online “meeting” to do wrap-up, participants sign-up for demo slots (Saturday and Sunday slots available), then some demos

- **Sunday, July 30th**: rest of the demos, votes, and awards

## About that money...

Be aware that all prize money distributions will follow local/state/country laws regarding taxation, not providing funds to citizens of countries prohibited by US law, and all other legal requirements.

## Questions?

Chat with us on [Discord](https://discord.com/channels/809154715984199690/1110948434552299673) and email us at hackathon@goauthentik.io!

## Spread the word!

We would be grateful if you help us get the word out. Share this page and information wherever you hang out. Bring 'em all!



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/developer-docs/docs/templates/procedural.md
================================================================================

---
title: "Procedural topic"
---

:::info How to use this template
Start with the markdown version of the template, either by copying the [`procedural.tmpl.md`](https://github.com/goauthentik/authentik/tree/main/website/docs/developer-docs/docs/templates) file from our GitHub repo or downloading the template file using the following command:

```shell
wget https://raw.githubusercontent.com/goauthentik/authentik/main/website/docs/developer-docs/docs/templates/procedural.tmpl.md
```

Edit your markdown file as you work, reading this page for the descriptions of each section. You can build out a "stub file" with just headers, then gradually add content to each section. Use screenshots sparingly, only for complex UIs where it is difficult to describe a UI element with words. Refer to our [Style Guide](../style-guide.mdx) for writing tips and authentik-specific rules.
:::

For a procedural topic, use a title that focuses on the task you are writing about. For example, "Add a new Group" or "Edit user profiles". For procedural docs, there should be a verb in the title, and usually the noun (the component or object you are working on). For the title (and all headings) use the infinitive form of the verb (i.e. "add") not the gerund form (i.e. "adding").

In this first section, right after the title, write one or two sentences about the task. Keep it brief; if it goes on too long, then create a separate conceptual topic, in a separate `.md` file. We don't want readers to have to scroll through paragraphs of conceptual info before they get to Step 1.

## Prerequisites (optional section)

In this section, inform the reader of anything they need to do, or have configured or installed, before they start following the procedural instructions below.

## Overview of steps/workflow (optional section)

If the task is quite long or complex, it might be good to add a bullet list of the main steps, or even a diagram of the workflow, just so that the reader can first familiarize themselves with the 50,000 meter view before they dive into the detailed steps.

## First several group steps

If the task involves a lot of steps, try to group them into similar steps and have a Head3 or Head4 title for each group.

In this section, help the reader get oriented... where do they need to be (i.e. in the GUI, on a CLI, etc).

Have a separate paragraph for each step.

Start instructions with the desired goal, followed by the instructions. For example, in this sentence we first read the goal (to define a new port) and then we see the instructions: "To define a new port number, navigate to the Admin interface, and then to the **Settings** tab."

## Next step of grouped steps (if a second group is needed)

Continue with the steps...

Use screenshots sparingly, only for complex UIs where it is difficult to describe a UI element with words.

Provide as many code snippets and examples as needed.

## Verify the steps

Use a heading such as "Verify your installation" or "Verify successful configuration". Whenever possible, it is useful to add verification steps at the end of a procedural topic. For example, if the procedural was about installing a product, use this section to tell them how they can verify that the install was successful.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/developer-docs/docs/templates/conceptual.md
================================================================================

---
title: "Conceptual topic"
---

:::info How to use this template
Start with the markdown version of the template, either by copying the [`conceptual.tmpl.md`](https://github.com/goauthentik/authentik/tree/main/website/docs/developer-docs/docs/templates) file from our GitHub repo or downloading the template file using the following command:

```shell
wget https://raw.githubusercontent.com/goauthentik/authentik/main/website/docs/developer-docs/docs/templates/conceptual.tmpl.md
```

Edit your markdown file as you work, reading this page for the descriptions of each section. You can build out a "stub file" with just headers, then gradually add content to each section. Use screenshots sparingly, only for complex UIs where it is difficult to describe a UI element with words. Refer to our [Style Guide](../style-guide.mdx) for writing tips and authentik-specific rules.
:::

Use a title that focuses on the feature, component, or technology you are writing about... for example, "About authentik policies" or "Understanding outposts". For conceptual docs, the verb in the title should indicate a concept, such as "About" or "Overview" or "Understanding", followed by the noun (the component or object you are writing about).

In this first section, immediately after the title, write one or two sentences about the feature, component, or technology. The following sections can help break up the content.

## Common use cases (optional section)

In this optional section, provide some example use cases for the feature. Who would use it, WHY? If you mention HOW to use the feature, be sure to link off to the related procedural doc. Also share situations where users might NOT want to use the feature; for example, if the feature is intended for a specific environment.

## Overview of feature/component

Dive deeper into explaining the concepts behind the feature/component.

Write about the feature/functionality from the user's perspective. What is this feature used for, why should they use it, are there situations where they should **_not_** use it?

> Pro Tip: If you were writing the related procedural topic, and you found that you had a lot to say about the topic, this is exactly where that info would go (not crowded up at the top of the procedural topic!).

Cover anything the user needs to know about the feature. If there are Reference docs or a related procedural doc for this feature or component, be sure to link to them from this page.

## Important considerations

List anything that might be critical for the user to know, such as situations where this feature might not be ideal, or pre-configs that need to be set, etc.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/developer-docs/docs/templates/conceptual.tmpl.md
================================================================================

---
title: "Markdown template: conceptual"
---

Write a few sentences introducing the feature/component/technology.

:::info Add a title here
If needed, use this syntax to add a note (info) or warning (warning) anywhere in the document that is appropriate.
:::

## Common use cases

Provide a few use cases, with examples/scenarios when possible.

## About feature x

Provide more conceptual details.

## Important considerations

List anything users should know before implementing the feature/technology.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/developer-docs/docs/templates/combo.tmpl.md
================================================================================

---
title: "Markdown template: combo"
---

add brief description of the feature/functionality

## About feature XYZ

In this section, go into a deeper explanation of the feature, provide typical use cases, etc.

:::info Add a title here
If needed, use this syntax to add a note (info) or warning (warning) anywhere in the document that is appropriate.
:::

### More info about the feature, a sub-category of info

Use this section if there are several big topics or categories of info that the reader needs to know about the feature or task. Add as many of these sections as needed.

## Prerequisites

bullet list of pre-reqs

## Overview of steps/workflow (Optional, only if there are a lot of steps)

describe the 50,000 meter view before they dive into the detailed steps, using a bullet list of the main steps, or even a diagram of the workflow.

## first several group steps

1. first step

2. second step

3. third step

if you need a tabbed section to represent diff processes or code snippets for diff install environments, use an MDX tabbed component.

## next step of grouped steps, if needed

Continue with the steps...

## verify the steps

add verification steps



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/developer-docs/docs/templates/index.md
================================================================================

---
title: "Templates"
---

In technical documentation, there are document "types" (similar to how there are data types). We have templates for the different types, to make it super-easy to divide longer topics into separate pages (one for each content type) if needed. And templates in general make it easy for whomever wants to contribute some documentation!

The most common types are:

- [**Combo**](./combo.md): For most topics (unless they are very large and complex), we can combine the procedural and conceptual information into a single document. A handy guideline to follow is: "If the actual 1., 2., 3. steps are buried at the bottom, and a reader has to scroll multiple times to find them, then the combo approach is _not_ the right one. Use separate topics.".

- [**Procedural**](./procedural.md): these are How To docs, the HOW information, with step-by-step instructions for accomplishing a task. This is what most people are looking for when they open the docs... and best practice is to separate the procedural docs from long, lengthy conceptual or reference docs.

- [**Conceptual**](./conceptual.md): these docs provide the WHY information, and explain when to use a feature (or when not to!), and general concepts behind the feature or functionality.

- [**Reference**](./reference.md): this is typically tables or lists of reference information, such as configuration values, or functions, or most commonly APIs.

### Add a new integration

To add documentation for a new integration (with support level Community or Vendor), please use the integration templates [`service.md`](https://github.com/goauthentik/authentik/blob/main/website/integrations/template/service.md) from our GitHub repo. You can download the template using the following command:

```shell
wget https://raw.githubusercontent.com/goauthentik/authentik/main/website/integrations/template/service.md
```



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/developer-docs/docs/templates/procedural.tmpl.md
================================================================================

---
title: "Markdown template: procedural"
---

add brief description of the feature/functionality

:::info Add a title here
If needed, use this syntax to add a note (info) or warning (warning) anywhere in the document that is appropriate.
:::

## Prerequisites

bullet list of pre-reqs

## Overview of steps/workflow

describe the 50,000 meter view before they dive into the detailed steps, using a bullet list of the main steps, or even a diagram of the workflow.

## first several group steps

1. first step

2. second step

3. third step

if you need a tabbed section to represent diff processes or code snippets for diff install environments, use an MDX tabbed component.

## next step of grouped steps, if needed

Continue with the steps...

## verify the steps

add verification steps



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/developer-docs/docs/templates/combo.md
================================================================================

---
title: "Combination topic (most common)"
---

:::info How to use this template
Start with the markdown version of the template, either by copying the [`combo.tmpl.md`](https://github.com/goauthentik/authentik/tree/main/website/docs/developer-docs/docs/templates) file from our GitHub repo or downloading the template file using the following command:

```shell
wget https://raw.githubusercontent.com/goauthentik/authentik/main/website/docs/developer-docs/docs/templates/combo.tmpl.md
```

Edit your markdown file as you work, reading this page for the descriptions of each section. You can build out a "stub file" with just headers, then gradually add content to each section. Use screenshots sparingly, only for complex UIs where it is difficult to describe a UI element with words. Refer to our [Style Guide](../style-guide.mdx) for writing tips and authentik-specific rules.
:::

For a combo topic, the title is typically the name of the feature ("Branding" or "Remote Access Control").

In this first section, right after the title but with no header, write one or two sentences about the task. Keep it brief, just an overview.

## About feature XYZ

In this section, go into a deeper explanation of the feature, provide typical use cases, etc.

### More info about the feature, a sub-category of info

Use this section if there are several big topics or categories of info that the reader needs to know about the feature or task. Add as many of these sections as needed.

## Prerequisites (optional section)

In this section, inform the reader of anything they need to do, or have configured or installed, before they start following the procedural instructions below.

## Overview of steps/workflow (optional section)

If the task is quite long or complex, it might be good to add a bullet list of the main steps, or even a diagram of the workflow, just so that the reader can first familiarize themselves with the 50,000 meter view before they dive into the detailed steps.

## First several group steps

If the task involves a lot of steps, try to group them into similar steps and have a Head3 or Head4 title for each group.

In this section, help the reader get oriented... where do they need to be (i.e. in the GUI, on a CLI, etc).

Have a separate paragraph for each step.

_Start instructions with the desired goal_, followed by the instructions. For example, in this sentence: "To define a new port number, navigate to the Admin interface, and then to the **Settings** tab." we first read the goal (to define a new port) and then we see the instructions.

## Next step of grouped steps (if a second group is needed)

Continue with the steps...

Use screenshots sparingly, only for complex UIs where it is difficult to describe a UI element with words.

Provide as many code snippets and examples as needed.

## Verify the steps

Use a heading such as "Verify your installation" or "Verify successful configuration". Whenever possible, it is useful to add verification steps at the end of a procedural topic. For example, if the procedural was about installing a product, use this section to tell them how they can verify that the install was successful.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/developer-docs/docs/templates/reference.tmpl.md
================================================================================

---
title: "Markdown template: reference"
---

Write a few sentences introducing the feature/component/technology, and state that this page contains reference materials.

:::info Optionally add a title here
If needed, use this syntax to add a info, warning or danger box to the document.
:::

## Head 2

After a brief description of this section, list the reference values.

Consider using a table if that is cleaner looking.

### Head 3 (optional, if needed)

After a brief description of this section, list the reference values.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/developer-docs/docs/templates/reference.md
================================================================================

---
title: "Reference topic"
---

:::info How to use this template
Start with the markdown version of the template, either by copying the [`reference.tmpl.md`](https://github.com/goauthentik/authentik/tree/main/website/docs/developer-docs/docs/templates) file from our GitHub repo or downloading the template file using the following command:

```shell
wget https://raw.githubusercontent.com/goauthentik/authentik/main/website/docs/developer-docs/docs/templates/reference.tmpl.md
```

Edit your markdown file as you work, reading this page for the descriptions of each section. You can build out a "stub file" with just headers, then gradually add content to each section. Use screenshots sparingly, only for complex UIs where it is difficult to describe a UI element with words. Refer to our [Style Guide](../style-guide.mdx) for writing tips and authentik-specific rules.
:::

Create a title that specifies the component you are documenting. For example, "Group attributes".

Provide a sentence or two about the topic.

Reference documentation provides details, values, syntax, etc., about specific programming elements.

The most common type of reference documentation is for REST APIs; the request syntax, a successful response, any parameters such as query, header, or request body parameters, and possible http status codes.

Other types of reference content include lists of functions, parameters, object properties, event actions, and attributes.

## Head 2

Use a title that is descriptive, such as "User object attributes" or "Expression policy functions".

Use tables, bullet lists, Head3s... whatever you need to clearly present the values.

Be sure to use a sentence after every heading, to explain what the section is about, how the values are used, etc.

### Head 3 (optional, if needed)

Add a sentence explaining the following grouping.

### Head 3 (optional, if needed)

Add a sentence explaining the following grouping.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/developer-docs/docs/theming/index.mdx
================================================================================

---
title: Documentation Theming
sidebar_label: Theming
---

    PaletteGroup,
    ColorGroup,
} from "@goauthentik/docusaurus-theme/components/infima/Swatch/index.tsx";
    DispositionDangerColorEntries,
    DispositionInfoColorEntries,
    DispositionSuccessColorEntries,
    DispositionWarningColorEntries,
    InfimaColorsMap,
    UtilityColorEntries,
} from "@goauthentik/docusaurus-theme/components/infima/constants.ts";

:::info Advanced

This section is intended for developers of authentik's documentation site. If you are looking to customize the theming of your own authentik instance, please refer to the [branding](../../../sys-mgmt/brands/index.md) documentation.

:::

The authentik documentation site is built using Meta's [Docusaurus](https://docusaurus.io/), which uses their internal [Infima CSS framework](https://infima.dev/) for its styling and theming capabilities. Infima's own documentation is limited, possibly due to it's internal nature and Docusaurus being the primary consumer. This document aims to provide an overview of how theming is handled in the authentik documentation site, and how you can customize it.

## Infima Color Palette

With the exception of a few customizations, our color palette is managed through Infima's theming system.

### Primary


### Secondary


### Success


### Info


### Warning


### Danger


## Utility & UI Colors


## Dispositions

### Info


### Success


### Warning


### Danger




================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/user/invitations.md
================================================================================

---
title: Invitations
description: "Learn how to create an invitation URL for new users to enroll."
toc_max_heading_level: 4
---

Invitations are another way to create a user, by inviting someone to join your authentik instance as a new user. With invitations, you can either email an enrollment invitation URL to one or more specific recipients with pre-defined credentials, or you can email a URL to users, who can then log in and define their own credentials.

You can configure invitations either by:

- using [pre-built blueprints](#use-pre-built-blueprints-to-configure-invitations) (recommended for quick setup).
- [manually creating flows and stages](#manual-setup-without-blueprints) (for custom configurations).

:::info
You can also create a [policy](../../../customize/policies/) to see if the invitation was ever used.
:::

## Use pre-built blueprints to configure invitations

The fastest way to configure invitations in authentik is to use our pre-defined blueprints that have the necessary flows, stages, and prompts already included.

### Step 1. Download a blueprint

We have two pre-defined blueprints, the`Example - Invitation-based Enrollment` blueprint and the `Example - Enrollment (2 Stage)`blueprint.

- #### Option 1: Download the `Example - Invitation-based Enrollment` blueprint (Recommended)

    This blueprint provides several examples of how to configure different invitation features and serves as a helpful starting point:
    - Separate flows for external and internal users
    - An example of [automatic group assignment](#automatic-group-assignment) (creates an example group called `engineering-team`)
    - [User path organization](#user-paths)
    - Five example invitations demonstrating different use cases

    Download the `Example - Invitation-based Enrollment` blueprint by running this command:

    ```shell
    wget https://goauthentik.io/blueprints/example/flows-invitation-enrollment.yaml
    ```

    Alternatively, use this [link](/blueprints/example/flows-invitation-enrollment.yaml) to view and save the file.

- #### Option 2: Download the `Example - Enrollment (2 Stage)` blueprint

    For a simpler invitation flow that doesn't include separate flows for internal/external user types, [automatic group assignment](#automatic-group-assignment), and [set user paths](#user-paths), download the `Example - Enrollment (2 Stage)` blueprint by running this command:

    ```shell
    wget https://goauthentik.io/blueprints/example/flows-enrollment-2-stage.yaml
    ```

    Alternatively, use this [link](/blueprints/example/flows-enrollment-2-stage.yaml) to view and save the file.

### Step 2. Import the blueprint file

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Flows** and click **Import**.
3. Click **Choose file**, select the blueprint file that you downloaded, and then click **Import**.

### Step 3. Create the invitation object

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Invitations** and click **Create**.

    The Create Invitation box appears.

![Create an invitation modal](./create_invite.png)

Configure the following settings:

- **Name**: provide a name for your invitation object.
- **Expires**: select a date for when you want the invitation to expire.
- **Flow**: In the drop-down menu, select the enrollment flow to use (`invitation-enrollment-flow-external`, `invitation-enrollment-flow-internal`, `invitation-enrollment-flow-internal-engineering`, or ` default-enrollment-flow` depending on which blueprint you used).
- **Custom attributes**: (_optional_) Enter JSON or YAML to pre-fill user information. This data is merged with the user's input during enrollment.


    :::info
    The field keys (e.g., `email`, `name`) must match the field keys configured in your flow's [prompt stage](../../add-secure-apps/flows-stages/stages/prompt/index.md).
    :::

    - **Single use**: Specify whether the invitation should expire after a single use.
        - Enable for invitations sent to specific individuals.
        - Disable for invitations shared with multiple people (e.g., department onboarding links).

3. Click **Save**.

### Step 4. Share the invitation

On the **Invitations** page, click the chevron beside your new invitation to expand the details. The **Link to use the invitation** displays with the URL.

You can share the invitation in two ways:

#### Option 1: Copy the link manually

Copy the URL and send it in an email to the people you want to invite to enroll.

The invitation link format is:

```
https://authentik.company/if/flow/<flow-slug>/?itoken=<invitation-uuid>
```

#### Option 2: Send an invitation email directly from authentik

Follow the steps below to send invitation emails directly from authentik:

1. On the **Invitations** page, click the chevron beside your invitation to expand the details.
2. Click **Send via Email** and configure the following settings:
    - **To**: Enter the email addresses of the recipients. You can enter multiple addresses, one per line, or separated by commas or semicolons. Each recipient will receive a separate email with the invitation link.
    - **CC**: (_optional_) Enter the email addresses to carbon copy.
    - **BCC**: (_optional_) Enter the email addresses to blind carbon copy.
    - **Template**: Select the email template to use. The default `Invitation` template is recommended.
3. Click **Send**.

The emails are queued and sent asynchronously by the background worker. Each recipient receives an email containing the invitation link.

:::note Email configuration required
To use this feature, you must have email configured in authentik, refer to the [Email configuration](../../install-config/email.mdx) documentation for details.
:::

## Manual setup (without blueprints)

If you prefer to create your invitation flow manually instead of using a blueprint, follow these steps:

### Step 1: Create an Invitation stage

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Stages** and click **Create**.
3. Select **Invitation Stage** from the stage type list.
4. Configure the stage:
    - **Name**: Provide a descriptive name (e.g., `enrollment-invitation-stage`)
    - **Continue flow without invitation**:
        - Set to `false` if you want to require a valid invitation token (recommended for invitation-only flows).
        - Set to `true` if you want to allow both invited and non-invited users to use the same enrollment flow.

5. Click **Create**.

:::info
The **Continue flow without invitation** setting determines whether users can proceed through the flow without a valid invitation token. When set to `false`, only users with valid invitation links can complete enrollment.
:::

### Step 2: Create or modify an Enrollment flow

1. Navigate to **Flows and Stages** > **Flows**.
2. Either create a new flow or edit an existing enrollment flow:
    - **Name**: Provide a descriptive name.
    - **Title**: Enter the title shown to users during enrollment.
    - **Slug**: Enter a unique identifier (e.g., `invitation-enrollment`).
    - **Designation**: Must be set to **Enrollment**.
    - **Authentication**: Set to **Require unauthenticated** (users shouldn't be logged in to enroll).

### Step 3: Bind the Invitation stage to the flow

1. In your enrollment flow, go to the **Stage Bindings** tab.
2. Click **Bind Stage** and select your invitation stage.
3. Configure the binding:
    - **Order**: Set to a low number (e.g., `5` or `10`) so it evaluates early in the flow.
    - **Evaluate on plan**: Enable this option so the invitation is validated when the flow starts.
    - **Re-evaluate policies**: Enable this to ensure policies are checked.

4. Add other necessary stages to your flow (in order):
    - **Prompt Stage** for collecting credentials (username, password)
    - **Prompt Stage** for collecting user details (name, email)
    - **User Write Stage** to create the user account
    - **User Login Stage** to log the user in after enrollment

### Step 4: Create invitations

Now you can create invitations that reference your custom flow. Follow the steps in [Create the invitation object](#step-3-create-the-invitation-object) above.

## Advanced features

### Automatic group assignment

To automatically add users to a group when they enroll via invitation, you need to configure the enrollment flow's User Write Stage:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Stages**.
3. Create or edit a **User Write Stage** used by your enrollment flow.
4. Set **Create users group** to your desired group.
5. All users enrolling through that flow will automatically be added to the selected group.

:::info
Groups cannot be set directly in invitation custom attributes because they require database relationships. They must be configured at the flow/stage level.
:::

### User paths

[User paths](user_ref.mdx#path) organize users in a directory structure (e.g., `users/external`, `users/internal/engineering`). To configure user paths:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Stages**.
3. Create or edit a **User Write Stage** used by your enrollment flow.
4. Set **User path template** to your desired path.
5. All users enrolling through that flow will be created under that path.

### Expression policies with invitations

You can use [expression policies](../../../customize/policies/expression/) to make decisions based on invitation data:

```python
# Check if user was invited
return context.get('invitation_in_effect', False)

# Access invitation data
invitation = context.get('invitation')
if invitation:
    return invitation.fixed_data.get('department') == 'Engineering'

# Access pre-filled prompt data
prompt_data = context.get('prompt_data', {})
return prompt_data.get('email', '').endswith('@example.com')
```

## Troubleshooting

### "Permission denied" error for external users

**Problem**: External user sees "Interface can only be accessed by internal users" after enrollment.

**Solution**: Configure a Default Application in your brand settings (System → Brands) so external users have somewhere to go after login.

### Invitation not working

Possible causes:

- Invitation has expired (check the expiration date)
- Single-use invitation has already been used
- Flow slug doesn't match the invitation's configured flow
- Invitation stage is not bound to the flow

### Pre-filled Data Not Appearing

Possible causes:

- Field keys in custom attributes don't match your prompt field keys
- Prompt fields are marked as `placeholder_expression: true`
- Invitation stage is not evaluated before prompt stages in the flow

:::info Invitation links validity
Be aware that when an authentik administrator or any other user creates an invitation link, that link remains valid even if the administrator is deactivated or has permissions revoked. However, if the user who created the link is deleted and removed from the authentik system, the link is also deleted.
:::



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/user/password_reset_on_login.mdx
================================================================================

---
title: Force password reset on next login
sidebar_label: Password reset on login
---

You can require users to reset their password on their next login, using expression policies, custom stages, and a custom user attribute. This guide explains how to configure this with the `default-authentication-flow`; however, the same steps apply to any authentication flow.

Configuring forced password reset on next login involves the following steps:

    1. Creating two expression policies.
    2. Creating and binding two stages to the active authentication flow.
    3. Binding the expression policies to the stages.
    4. Setting a custom user attribute which triggers the password prompt.

## Create expression policies

You'll need to create two expression policies; one that checks the value of a custom user attribute on the user account attempting to log in, and another that resets the value of the custom user attribute.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies** and click **Create** to set up the first policy.
3. Select **Expression Policy** as the policy type, click **Next**, and configure the following settings:
    - **Name**: Provide a descriptive name for the policy (e.g. `reset_password_check`).
    - **Expression**:

        ```python
        # Check if the "reset_password" attribute set to true for the pending user
        if request.context["pending_user"].attributes.get("reset_password") == True:
            return True

        return False
        ```

4. Click **Finish** to save the first policy, then repeat the steps to create the second policy using the following settings:
    - **Name**: Provide a descriptive name for the policy (e.g. `reset_password_update`).
    - **Expression**:

        ```python
        # Check if the "reset_password" attribute is set to true for the pending user
        if request.context["pending_user"].attributes.get("reset_password") == True:
            # Reset the "reset_password" attribute to false to prevent forcing a password reset on next login
            request.context["pending_user"].attributes["reset_password"] = False
            return True

        return False
        ```

5. Click **Finish**.

## Create stages

You'll need to create two stages; a _Prompt stage_ to prompt the user to enter a new password, and a _User Write stage_ to update the user's account with the new password. Both stages will need to be bound to the active authentication flow, typically the `default-authentication-flow`.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Flows** and click on the name of the active authentication flow, typically the `default-authentication-flow`.
3. Select the **Stage Bindings** tab and click **Create and bind stage**.
4. Select **Prompt Stage** as the stage type, click **Next**, and configure the following settings for the stage:
    - **Name**: Provide a descriptive name for the stage (e.g. `Force Password Reset Prompt Stage`).
    - Under **Fields**:
        - Click the `x` icon between **Available Fields** and **Selected Fields** to clear the selections.
        - Select `default-password-change-field-password` and `default-password-change-field-password-repeat`.
    - Under **Validation Policies**:
        - Click the `x` icon between **Available Policies** and **Selected Policies** to clear the selections.
        - _(Optional but recommended)_ Select `default-password-change-policy`.

:::tip
Optionally, you can create and add a text field to the prompt stage to inform users that they are required to reset their password. For more details on configuring this, refer to the [Prompt Stage documentation](../../add-secure-apps/flows-stages/stages/prompt/index.md).
:::

5. Click **Next** to create the stage and then configure the following settings for the binding:
    - **Order**: `25` or any number higher than the `default-authentication-password` stage order and lower than the `default-authentication-mfa-validation` stage order.
    - Leave the other settings as their default values.

6. Click **Finish** to create the binding and repeat the process for the second stage using the following settings:
    - **Stage type**: Select **User Write Stage** as the type.
    - **Name**: Provide a descriptive name for the stage (e.g. `Force Password Reset User Write Stage`).
    - Leave the other settings as their default values.

7. Click **Next** to create the stage and then configure the following settings for the binding:
    - **Order**: `26` or any number higher than the `Force Password Reset Prompt Stage` stage order and lower than the `default-authentication-mfa-validation` stage order.
    - Leave the other settings as their default values.

8. Click **Finish** to create the binding.

## Bind policies to stages

You will need to bind the previously created policies to the newly created stages. Specifically:

    - The `reset_password_check` policy needs to be bound to the `Force Password Reset Prompt Stage`.
    - The `reset_password_update` policy needs to be bound to the `Force Password Reset User Write Stage`.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Flows** and click on the name of the active authentication flow, typically `default-authentication-flow`.
3. Select the **Stage Bindings** tab and click the arrow next to the newly created `Force Password Reset Prompt Stage` to expand it.
4. Click **Bind existing Policy / Group / User**.
5. Set **Policy** to `reset_password_check` and click **Create**.
6. Click the arrow next to the newly created `Force Password Reset User Write Stage` to expand it.
7. Click **Bind existing Policy / Group / User**.
8. Set **Policy** to `reset_password_update` and click **Create**.

## Set custom user attribute

To require a user to reset their password on next login, you will need to set a custom user attribute on their account.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Users** and click the **Edit** icon of the user in question.
3. Add the following values to the user's attribute field:
    ```python
    reset_password: True
    ```
4. Click **Update**.

The next time the user logs in, they will be required to reset their password, and the `reset_password` attribute on their account will be set to `False`.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/user/index.mdx
================================================================================

---
title: About users
---


In authentik you can create and manage users with fine-tuned access control, session and event details, group membership, role assignment, super-user rights, impersonation, and password management and recovery.

To learn more about Enterprise licenses with internal and external users, refer to our [Enterprise documentation](../../enterprise/manage-enterprise.mdx#about-users-and-licenses).

To learn more about working with users in authentik, refer to the following topics:




================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/user/user_ref.mdx
================================================================================

---
title: User properties and attributes
---

## Object properties

The User object has the following properties:

- `username`: User's username.
- `email`: User's email.
- `uid`: User's unique ID. Read-only.
- `name`: User's display name.
- `is_staff`: Boolean field defining if user is staff.
- `is_active`: Boolean field defining if user is active.
- `date_joined`: Date user joined/was created. Read-only.
- `password_change_date`: Date password was last changed. Read-only.
- `path`: User's path, see [Path](#path)
- `attributes`: Dynamic attributes, see [Attributes](#attributes)
- `group_attributes()`: Merged attributes of all groups the user is a member of and the user's own attributes. Read-only.
- `groups`: This is a queryset of all the user's direct groups.
- `all_groups()`: This is a queryset of all the user's direct and indirect groups.

:::info Clarifying direct vs indirect group membership
A user is a member of a group (direct member). If that group in turn has a parent group, then the user is an indirect member of that parent group.
:::

## Examples

These are examples of how User objects can be used within Policies and Property Mappings.

### List a user's group memberships

Use the following example to list all groups that a user object is a direct member of:

```python
for group in user.groups.all():
    yield group.name
```

### List a user's group memberships and filter based on group name

Use the following example to list groups that a user object is a direct member of, filtered based on group name:

```python
user.groups.filter(name__startswith='test')
```

### List a user's group memberships including parent groups

Use the following example to list all groups that a user object is a direct and indirect member of:

```python
groups = [group.name for group in request.user.all_groups()]
```

:::info
For Django field lookups, see the [Django documentation](https://docs.djangoproject.com/en/stable/ref/models/querysets/#id4).
:::

## Path

Paths can be used to organize users into folders depending on which source created them or organizational structure. Paths may not start or end with a slash, but they can contain any other character as path segments. Paths are currently used purely for organization; this does not affect permissions, group memberships, or anything else.

## Attributes

### `goauthentik.io/user/can-change-username`

Optional flag, when set to false prevents the user from changing their own username.

### `goauthentik.io/user/can-change-name`

Optional flag, when set to false prevents the user from changing their own name.

### `goauthentik.io/user/can-change-email`

Optional flag, when set to false prevents the user from changing their own email address.

### `goauthentik.io/user/token-expires`:

Optional flag, when set to false, Tokens created by the user will not expire.

Only applies when the token creation is triggered by the user with this attribute set. Additionally, the flag does not apply to superusers.

### `goauthentik.io/user/token-maximum-lifetime`:

Optional flag, when set, defines the maximum lifetime of user-created tokens. Defaults to the system setting if not set.

Only applies when `goauthentik.io/user/token-expires` set to true.

Format is string of format `days=10;hours=1;minute=3;seconds=5`.

### `goauthentik.io/user/debug`:

See [Troubleshooting access problems](../../troubleshooting/access.md), when set, the user gets a more detailed explanation of access decisions.

### `additionalHeaders`:

:::info
This field is only used by the Proxy Provider.
:::

Some applications can be configured to create new users using header information forwarded from authentik. You can forward additional header information by adding each header
underneath `additionalHeaders`:

#### Example

```yaml
additionalHeaders:
    REMOTE-USER: joe.smith
    REMOTE-EMAIL: joe@jsmith.com
    REMOTE-NAME: Joseph
```

These headers will now be passed to the application when the user logs in. Most applications will need to be configured to accept these headers. Some examples of applications that can accept additional headers from an authentik Proxy Provider are [Grafana](https://grafana.com/docs/grafana/latest/auth/auth-proxy/) and [Tandoor Recipes](https://docs.tandoor.dev/features/authentication/).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/user/user_basic_operations.md
================================================================================

---
title: Manage users
---

The following topics are for the basic management of users: how to create, modify, delete or deactivate users, and using a recovery email.

[Policies](../../customize/policies/index.md) can be used to further manage how users are authenticated. For example, by default authentik does not require email addresses be unique, but you can use a policy to [enforce unique email addresses](../../customize/policies/expression/unique_email.md).

## Create a user

> If you want to automate user creation, you can do that either by [invitations](./invitations.md), [`user_write` stage](../../add-secure-apps/flows-stages/stages/user_write.md), or [using the API](/api/reference/core-users-create).

1. In the Admin interface of your authentik instance, select **Directory** > **Users** in the left side menu.
2. In the **User folders** area, select the folder where you want to create a user.
3. Click **Create** (for a default user).
4. Fill in the required fields:

- **Username**: This value must be unique across your user folders.
- **Path**: The path where the user will be created. It will be automatically populated with the folder you selected in the previous step.

5. Fill the **_optional_** fields if needed:

- **Name**: The display name of the user.
- **Email**: The email address of the user. Email addresses are used in [email stages](../../add-secure-apps/flows-stages/stages/email/index.mdx) and to receive [notifications](../../sys-mgmt/events/notifications.md), if configured.
- **Is active**: Define if the newly created user account is active. Selected by default.
- **Attributes**: Custom attributes definition for the user, in YAML or JSON format. These attributes can be used to enforce additional prompts on authentication stages or define conditions to enforce specific policies if the current implementation does not fit your use case. The value is an empty dictionary by default.

6. Click **Create**

You should see a confirmation pop-up on the top-right of the screen that the user has been created, and see the new user in the user list. You can directly click the username if you want to [modify your user](./user_basic_operations.md#modify-a-user).

:::info
To create a super-user, you need to add the user to a group that has super-user permissions. For more information, refer to [Create a Group](../groups/manage_groups.mdx#create-a-group).
:::

## Advanced queries for users:ak-enterprise {#advanced-queries}

You can create advanced queries to locate specific users within the list shown under **Directory** > **Users** in the Admin interface. Use the auto-complete in the **Search** field or enter your own queries to return results with greater specificity.

- **Field**: `username`, `path`, `name`, `email`, `path`, `is_active`, `type`, `attributes`

- **Operators**: `=`, `!=`, `~`, `!~`, `startswith`, `not startswith`, `endswith`, `not endswith`, `in`, `not in`

- **Values**: `True`, `False`, `None`, and more

- **Example queries**:
    - search user by status: `is_active = False`
    - search user by username: `username = "bob"`
    - search user by email address: `email = "bob@authentik.company"`
    - search user by attribute: `attribute.my_custom_attribute = "foo"`

:::info

1. To dismiss the drop-down menu option, click **ESC**.
2. If the list of operators does not appear in a drop-down menu you will need to manually enter it.
   :::

## View user details

In the **Directory** > **Users** menu of the Admin interface, you can browse all the users in your authentik instance.

To view details about a specific user:

1. In the list of all users, click on the name of the user you want to check.

    This takes you to the **Overview** tab, with basic information about the user and quick access to perform basic actions on the user.

2. To see further details, click any of the other tabs:
    - **Session** shows the active sessions established by the user. If there is any need, you can clean up the connected devices for a user by selecting the device(s) and then clicking **Delete**. This forces the user to authenticate again on the deleted devices.
    - **Groups** allows you to manage the group membership of the user. You can find more details on [groups](../groups/index.mdx).
    - **User events** displays all the events generated by the user during a session, such as login, logout, application authorisation, password reset, user info update, etc.
    - **Explicit consent** lists all the permissions the user has given explicitly to an application. Entries will only appear if the user is validating an [explicit consent flow in an OAuth2 provider](../../add-secure-apps/providers/oauth2/index.mdx). If you want to delete the explicit consent (because the application is requiring new permissions, or the user has explicitly asked to reset his consent on third-party apps), select the applications and click **Delete**. The user will be asked to again give explicit consent to share information with the application.
    - **OAuth Refresh Tokens** lists all the OAuth tokens currently distributed. You can remove the tokens by selecting the applications and then clicking **Delete**.
    - **MFA Authenticators** shows all the authenticators that the user has registered to their profile. You can remove the tokens if the user has lost their authenticator and wants to enroll a new one.

## Modify a user

After the creation of the user, you can edit any parameter defined during the creation.

To modify a user object, go to **Directory** > **Users**, and click the edit icon beside the name. You can also go into [user details](#view-user-details), and click **Edit**.

## Manage user permissions

You cannot directly grant a user any permissions. Instead, either assign the user to a role with the appropriate permissions, or add a user to a group that has the appropriate permissions (via the group's role/roles).

On the flipside, to grant permissions on a user object to a role, review ["Manage permissions"](../access-control/manage_permissions.md#assign-or-remove-permissions-for-a-specific-role).

## Add a user to a group

1. To add a user to a group, navigate to **Directory** > **Users** to display all users.
2. Click the name of the user to display the full user details page.
3. Click the **Groups** tab, and then click either **Add to existing group** (or **Add new group** first).

## Add a user to a role

1. To add a user to a role, navigate to **Directory > Users** to display all users.
2. Click the name of the user to display the full user details page.
3. Click the **Roles** tab, and then click either **Add to existing role** (or **Add new role** first).

:::info
Users also inherit roles from the groups they belong to. The **Roles** tab has two sub-tabs: **Assigned Roles** shows roles directly assigned to the user, while **All Roles** shows all roles including those inherited from groups. Inherited roles are marked with an "Inherited" label.
:::

## Bind a user to an application

These bindings control which users can access an application, and whether or not the application is visible in the user's **My applications** page. If no bindings for an application are defined, this means that all users and groups can access the application.

For instructions refer to [Manage applications](../../add-secure-apps/applications/manage_apps.mdx#bind-a-user-or-group-to-an-application).

## User credentials recovery

If a user has lost their credentials and needs to recover their account, there are two available options:

1. Create a recovery link and send it to the user
2. Have authentik send the user a recovery email

Both options require you to configure a recovery flow and set it as the **Default recovery flow** for the active brand.

### Configure a recovery flow

To get started, you can [import](../../add-secure-apps/flows-stages/flow/index.md#import-or-export-a-flow) this example flow: [Recovery with email verification flow](../../add-secure-apps/flows-stages/flow/examples/flows.md#recovery-with-email-verification)

Then, set this as the default recovery flow for the active brand:

1. In the Admin interface, navigate to **System** > **Brands**, and select the active brand.
2. Under **Default flows**, set **Recovery flow** to the imported recovery flow: `default-recovery-flow`.
3. Click **Update**.

Now that you've configured a recovery flow, you can select one of the following options:

### 1. Create a recovery link

:::info Email stage not required
The example recovery flow includes an email stage. However, if you're manually sending the recovery link to the user, this email stage is not required and can be removed.
:::

1. In the Admin interface, navigate to **Directory** > **Users** to display all users.
2. Click the name of the user to display the full User details page.
3. To generate a recovery link, which you can then send to the user, click **Create recovery link**.

A pop-up will appear on your browser with the link for you to copy and to send to the user.

### 2. Email a recovery link

:::info Email stage required
This option is only available if the default recovery flow has an [Email Stage](../../add-secure-apps/flows-stages/stages/email/index.mdx) bound to it. The example recovery flow includes an email stage.
:::

You can send a link with the URL for the user to reset their password via Email. This option will only work if you have [configured email](../../install-config/email.mdx) and set an email address for the user.

1. In the Admin interface, navigate to **Directory** > **Users** to display all users.
2. Click the name of the user to display the full User details page.
3. To send the email to the user, click **Email recovery link**.

If the user does not receive the email, check if the mail server parameters [are properly configured](../../troubleshooting/emails.md).

## Reset the password for the user

As an Admin, you can simply reset the password for the user.

1. In the Admin interface, navigate to **Directory** > **Users** to display all users.
2. Either click the name of the user to display the full User details page, or click the chevron beside their name to expand the options.
3. To reset the user's password, click **Reset password**, and then define the new value.

## Deactivate or Delete user

### To deactivate a user:

1. Go into the user list or detail, and click **Deactivate**.
2. Review the changes and click **Update**.

The active sessions are revoked and the authentication of the user blocked. You can reactivate the account by following the same procedure.

### To delete a user:

:::caution
This deletion is not reversible, so be sure you do not need to recover any identity data of the user.
You may instead deactivate the account to preserve identity data.
:::

1. Go into the user list and select one (or multiple users) to delete and click **Delete** on the top-right of the page.
2. Review the changes and click **Delete**.

The user list refreshes and no longer displays the removed users.

## Impersonate a user

With authentik, an Admin can impersonate a user, meaning that the Admin temporarily assumes the identity of the user.

1. In the Admin interface, navigate to **Directory** > **Users** to display all users.
2. Click the name of the user to display the full User details page.
3. On the Overview tab, beneath **User Details**, in the **Actions** area, click **Impersonate**.
4. At the prompt, provide a reason why you are impersonating this user, and then click **Impersonate**.

:::info
An Admin can globally enable or disable impersonation in the [System Settings](../../sys-mgmt/settings.md#impersonation). By default, this option is set to true, meaning all users can be impersonated.

An Admin can also configure whether inputting a reason for impersonation is required in the [System Settings](../../sys-mgmt/settings.md#require-reason-for-impersonation).
:::

## Export users :ak-enterprise

You can export your authentik instance's user data to a CSV file. To generate a data export, follow these steps:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Users** and click **Export**.
3. Set a [search query](#advanced-queries) as well as the ordering for the data export.
4. Click **Export** above the event list.
5. Confirm the export parameters in the confirmation dialog.
6. The export is processed in the background. When it's ready, you will receive a notification in the Admin interface's notification area.
7. In the notification, click **Download**.

To review, download, or delete past data exports, navigate to **Events** > **Data Exports** in the Admin interface.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/access-control/permissions.md
================================================================================

---
title: "About permissions"
description: "Learn about global and object permissions in authentik."
---

Permissions are the central, lowest-level components in all access control systems. They are assigned (or removed) to define exactly WHO can do WHAT to WHICH part of the overall software system.

:::info
Note that global and object permissions only apply to objects within authentik, and not to who can access certain applications (which are access-controlled using [policies](../../customize/policies/index.md)).
:::

For instructions to add, remove, and manage permissions, refer to [Manage Permissions](./manage_permissions.md).

## Fundamentals of authentik permissions

A [role](../roles/index.md) is a collection of permissions. A user or a group can be assigned to any number of roles. A user has a certain permission if they have a role that also has that permission, or if they are part of a group (either directly or indirectly) that has a role which has that permission.

- Example 1 (no group): Judith has the role "RADIUS", which has every permission for RADIUS providers and property mappings. With this role, Judith has permission to add/view/change/delete RADIUS providers or RADIUS property mappings.
- Example 2 (direct group): Marie is part of the group "Auditors". That group has the role "Event Log manager", which in turn has the permissions "Can view Event", "Can change Event", and "Can delete Event". Thus, Marie has permissions to view, change, or delete Events.
- Example 3 (indirect group): Elaine is part of the group "Accounting", which has a parent group "Back office", which has a parent group "Employees". The group "Employees" has the role "Read-only", which has view permissions on all object types. So Elaine has the permission to view any object in authentik through indirect membership of the "Employees" group.

:::info
From 2025.12, authentik's access control is fully role-based. Before 2025.12, Admins could assign permissions to individual [users](../user/index.mdx). To mimic this behavior of "User permissions", an Admin can assign a user to a role that has the required permissions.
:::

There are two main types of permissions in authentik:

- [**Global permissions**](#global-permissions)
- [**Object permissions**](#object-permissions)

Additionally, authentik employs _initial permissions_ to streamline the process of granting object-level permissions when an object (user or role) is created. When an Admin implements initial permissions, this feature automatically adds permissions for newly created objects to the role (and thus users with that role) that created them. For more details, refer to [Initial permissions](./initial_permissions.mdx).

### Global permissions

Global permissions define coarse-grained access control. For example, a role with a global permission of "Can change Flow" can change any [flow](../../add-secure-apps/flows-stages/flow/index.md). Some permissions only make sense as global permissions, e.g. the permission to add a specific object type or whether a user [`Can access admin interface`](./manage_permissions.md#assign-can-access-admin-interface-permissions).

### Object permissions

An object permission grants permission (via a role) on a single, specific object (e.g. a [user](../user/index.mdx), a [group](../groups/index.mdx), a [role](../roles/index.md), a [flow](../../add-secure-apps/flows-stages/flow/index.md), etc.) instead of all objects of a specific type.

For example, a role with the object permission to change only the Default Authentication flow will not be able to change any other flow.

## Viewing permissions

Many objects in authentik's Admin interface have a **Permissions** tab, where you can check which roles have rights on that particular object. Those permissions describe what those roles can do _to_ the object detailed on the page.

For example, the screenshot below shows the **Permissions** tab for the user named Peter, listing what actions the listed roles can perform on the user object "Peter".

![](./user-page.png)

You can see in the **Permissions on this object** table that the Admin role and one other role (Read-only) have permissions on Peter (that is, on the user object named Peter). The Admin role has all object permissions on this object, while the Read-only role has only the view permission.

Hover over a checkmark to see whether that permission is granted by a global permission or an object permission.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/access-control/manage_permissions.md
================================================================================

---
title: "Manage permissions"
description: "Learn how to use global and object permissions in authentik."
---

For instructions on viewing and managing permissions, see the following topics. To learn more about the concepts and fundamentals of authentik permissions, refer to [About Permissions](./permissions.md).

To learn about using Initial Permissions, a pre-defined set of permissions, refer to our [documentation](./initial_permissions.mdx).

## View permissions

You can view all permissions that are assigned to a user, group, role, flow, stage, or other objects.

### View permissions assigned for a specific role

To view permissions assigned for a specific role:

1. Go to the Admin interface and navigate to **Directory > Roles**
2. Select a specific role by clicking on the name (this opens the details page).
3. Click the **Permissions** tab at the top of the page
4. Select the **Assigned global permissions** sub-tab to see global permissions and the **Assigned object permissions** sub-tab to see the object permissions.

### View permissions on objects with a detail page

Here we'll use flows as an example for objects with a detail page.

1. Go to the Admin interface and navigate to **Flows and Stages > Flows**.
2. Click the name of the flow (this opens the details page).
3. View the assigned permissions by clicking the **Permissions** tab at the top of the page.
4. (Optionally) Hover over any checkmark to see whether that permission is granted by a global permission or an object permission.

### View permissions for objects without a detail page

Here we'll use stages as an example for objects without a detail page.

1. Go to the Admin interface and navigate to **Flows and Stages > Stages**.
2. On the row for the specific stage whose permissions you want to view, click the **lock icon**.
3. View the assigned permissions on the **Update Permissions** window
4. (Optionally) Hover over any checkmark to see whether that permission is granted by a global permission or an object permission.

## Manage permissions

You can assign or remove permissions to a user, role, group, flow, stage, or other objects.

### Assign or remove permissions for a specific role

To assign or remove _object_ permissions for a specific role:

1. Go to the Admin interface and navigate to **Directory > Roles**.
2. Select a specific role by clicking on the role's name.
3. Click the **Permissions** tab at the top of the page, then click the **Permissions on this object** tab
4. To assign permissions that another _role_ has on this specific role:
    1. Click **Assign Object Permission**.
    2. In the **Role** drop-down, select the role object.
    3. Use the toggles to set which permissions on that selected role object you want to grant to the specific role.
    4. Click **Assign** to save your settings and close the box.
5. To remove permissions that another _role_ has on this specific role:
    1. Select the role you'd like to remove object permissions from.
    2. Click **Delete Object Permission**.

To assign or remove _global_ permissions for a role:

1. Go to the Admin interface and navigate to **Directory > Roles**.
2. Select a specific role by clicking on the role's name.
3. Click the **Permissions** tab at the top of the page.
4. Click **Assigned Global Permissions** to the left.
5. To assign permissions that another _role_ has on this specific role: 2. In the **Assign permissions** area, click **Assign Permission**. 3. In the **Assign permission to role** box, click the plus sign (**+**) and then click the checkbox beside each permission that you want to assign to the user. 4. Click **Add**, and then click **Assign** to save your changes and close the box.
6. To remove permissions that another _role_ has on this specific role:
    1. Select the permission(s) you'd like to remove.
    2. Click **Delete Object Permission**.

### Assign `Can access admin interface` permissions

You can use a role to grant regular users, who are not superusers nor Admins, the right to view the Admin interface. This can be useful in scenarios where you have a team who needs to be able to create certain objects (flows, other users, etc) but who should not have _full_ access to the Admin interface.

To assign the `Can access Admin interface` permission to a role:

1. Go to the Admin interface and navigate to **Directory > Role**.
2. Select a specific role by clicking on the role's name.
3. Click the **Permissions** tab at the top of the page.
4. Click **Assigned Global Permissions** to the left.
5. In the **Assigned global permissions** area, click **Assign Permission**.
6. In the **Assign permission to role** box, click the plus sign (**+**), enter `admin` in the Search field and click the search icon.
7. Select the returned permission, click **Add**, and then click **Assign** to save your changes and close the box.

Be aware that any rights beyond viewing the Admin interface will need to be assigned as well; for example, if you want a non-administrator user to be able to create flows in the Admin interface, you need to grant those global permissions to add flows.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/access-control/initial_permissions.mdx
================================================================================

---
title: "Initial permissions"
description: "Set permissions for object creation."
authentik_version: "2025.4.0"
authentik_preview: true
---

Initial permissions automatically assigns [object-level permissions](./permissions.md#object-permissions) between a newly created object and its creator.

The purpose of initial permissions is to assign a specific role a set of pre-selected permissions that are required for users of that role to accomplish their tasks.

An authentik administrator creates an initial permissions object (a set of selected permissions) and then associates it with a role - when an object is created by a user of that role, the specified permissions are granted for that role on that object.

## Common use cases

Imagine you have a new team tasked with creating [flows](../../add-secure-apps/flows-stages/flow/index.md) and [stages](../../add-secure-apps/flows-stages/stages/index.md). These team members need the ability to view and manage all the flow and stage objects created by other team members. However, they should not have permissions to perform any other actions within the Admin interface.

In the example use case above, the specific objects that the users create and manage could be any object. For example, you might have a team responsible for creating new users and managing those user objects, but any other user object.

## High-level workflow

The fundamental steps to implement initial permissions are as follows:

1. Create a role. Initial permissions will be assigned whenever a user with this role creates a new object.
2. Create a group, and assign the new role to it, and add any members that you want to use the initial permissions set. You can also create new users later, and add them to the group.
3. Create an initial permissions object, and add all needed permissions to it.
4. Optionally, create additional users and add them to the group to which the role is assigned.

Because the new initial permissions object is coupled with the role (and that role is assigned to a group), the initial permissions object is applied automatically to any new objects (users or flows or any object) that the member user creates.

:::info
Typically, initial permissions are assigned to non-super-user, non-administrator roles. In this scenario, the administrator needs to verify that the user has the `Can access Admin interface` permission (which allows the user to access the Admin interface). For details, see Step 5 below.

Be aware that any rights beyond viewing the Admin interface will need to be assigned as well; for example, if you want a non-administrator user to be able to create flows in the Admin interface, you need to grant those global permissions to add flows.
:::

## Create and implement initial permissions

To create a new set of initial permissions and apply them to a role, follow these steps:

1. Log in to authentik as an administrator and open the authentik Admin interface.

2. [Create a new role](../roles/manage_roles.md): navigate to **Directory** > **Roles** and click **Create**.

3. [Create a new group](../groups/manage_groups.mdx): navigate to **Directory** > **Groups** and click **Create**. After creating the group:
    - [assign the new role to the group](../groups/manage_groups.mdx#assign-a-role-to-a-group)
    - [add any members](../user/user_basic_operations.md#add-a-user-to-a-group) that require the initial permissions. You can add already existing users, or [create new users](../user/user_basic_operations.md#create-a-user).

4. Create an initial permissions object: navigate to **Directory** > **Initial Permissions** and click **Create**. Configure the following settings:
    - **Name**: Provide a descriptive name for the new initial permissions object.

    - **Role**: Select the role to which you want to apply initial permissions. When a member of a group with this assigned role creates an object, initial permissions will be applied for that role to that object.

    - **Permissions**: select all permissions to add to the initial permissions object.

5. To ensure that the role to which you assign the initial permissions _also_ has access to the Admin interface, check to see if the users also need [the global permission `Can access admin interface`](./manage_permissions.md#assign-can-access-admin-interface-permissions). Furthermore, verify that the user(s) has the global permissions to add specific objects.

6. Optionally, create new users and add them to the group. Each new user added to the group will automatically have the set of permissions included within the initial permissions object.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/access-control/index.mdx
================================================================================

---
title: About access control
---


To comply with important regulations such as PCI-DSS, HIPAA, SOC 2, and GDPR, it's necessary to have the ability to control which users have access to specific areas of the system, what [permissions](./permissions.md) they have globally and on certain objects, and a way to monitor [events](../../sys-mgmt/events/index.md) related to user activity.

In authentik, we provide role-based access control (RBAC), an industry standard for managing access control. By carefully designing roles with appropriate permissions, and then assigning those roles to groups, RBAC provides a fine-tuned approach to controlling user access.

RBAC is a way of ensuring the well-known [principle of least privilege](https://en.wikipedia.org/wiki/Principle_of_least_privilege) whereby "every module (such as a process, a user, or a program, depending on the subject) must be able to access only the information and resources that are necessary for its legitimate purpose."

To learn more about access control with authentik, refer to these topics:




================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/index.md
================================================================================

---
title: Sources
---

Sources allow you to connect authentik to an external user directory. Sources can also be used with social login providers such as Facebook, Twitter, or GitHub.

## Find your source

Sources are in the following general categories:

- **Protocols** ([Kerberos](./protocols/kerberos/index.md), [LDAP](./protocols/ldap/index.md), [OAuth](./protocols/oauth/index.mdx), [SAML](./protocols/saml/index.md), and [SCIM](./protocols/scim/index.md))
- [**Property mappings**](./property-mappings/index.md) or how to import data from a source
- **Directory synchronization** (Active Directory, FreeIPA)
- **Social logins** (Apple, Discord, Twitch, Twitter, and many others)

For instructions to add a specific source, refer to the documentation links in the left navigation pane.

## Add sources to default login page

To have sources show on the default login screen you will need to add them to the flow. The process below assumes that you have not created or renamed the default stages and flows.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Flows**.
3. Click the **default-authentication-flow**.
4. Click the **Stage Bindings** tab.
5. Click **Edit Stage** on the **default-authentication-identification** stage.
6. Under **Source settings**, add sources to **Selected sources** to have them displayed on the authentik login page.

## Bind a policy to a source

You can bind a policy to a source to control whether or not the users from the source can access an application.

For instructions, refer to [Bind a policy to a source](../../customize/policies/working_with_policies.md#bind-a-policy-to-a-source).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/roles/manage_roles.md
================================================================================

---
title: "Manage roles"
description: "Learn how to work with roles and permissions in authentik."
---

Roles are a collection of permissions, which can then be assigned, en masse, to a user or a group. Using roles is a way to quickly grant permissions; by adding a user to a group with the appropriate assigned roles, any user in that group then inherits all of those permissions that are assigned to the role.

:::info
Roles are intended to be assigned to groups, not to individual users. However, in some cases it's practical to assign a role straight to a user, so authentik implements that functionality.
:::

## Create a role

To create a new role, follow these steps:

1. In the Admin interface, navigate to **Directory > Roles**.
2. Click **Create**, enter the name of the role, and then click **Create** in the box.
3. Next, [assign permissions for the role](../access-control/manage_permissions.md#assign-or-remove-permissions-for-a-specific-role).

## Modify a role

To modify a role, follow these steps:

- To edit the name of the role, click the Edit icon beside the role's name.

- To modify the permissions that are assigned for the role, click the role's name to go to the role's detail page. There you can add or remove permissions. For more information, refer to ["Assign or remove permissions for a specific role"](../access-control/manage_permissions.md#assign-or-remove-permissions-for-a-specific-role).

## Delete a role

To delete a role, follow these steps:

1. In the Admin interface, navigate to **Directory > Roles**.
2. Select the checkbox beside the name of the role that you want to delete.
3. Click **Delete**.

## Assign a role to a group

1. To assign the role to a group, navigate to **Directory > Groups**.
2. Click the name of the group to which you want to add a role.
3. On the group's detail page, on the Overview tab, click **Edit** in the **Group Info** area.
4. On the **Update Group** box, in the **Roles** field, select the roles you want to assign to the group from the list of **Available Roles** in the left box (you can select multiple roles at once by holding the Shift key while selecting the roles), and then click the appropriate arrow icon to move them into the **Selected Roles** box.
5. Click **Update** to add the role(s) and close the box.

## Assign a role to a user

See [add user to a role](../user/user_basic_operations.md#add-a-user-to-a-role).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/roles/index.md
================================================================================

---
title: About roles
---


Roles are a way to simplify the assignment of permissions. Roles are also the backbone of role-based access control (RBAC), an industry standard for managing [access control](../access-control/index.mdx). In authentik, RBAC is how you manage access to system components and specific objects such as flows, stages, users, etc.

Think of roles as a collection of permissions. A role, along with its "bucket" of assigned permissions, can then be assigned to a user, or it can be assigned to a group (which means that every user who is a part of that group will inherit all of the permissions in that role's "bucket").

Roles are also inherited through group hierarchy. When a role is assigned to a parent group, all child groups automatically inherit that role. This means users in any descendant group will have the permissions from roles assigned to any of their ancestor groups.

For example, let's take a look at the following scenario:

> You need to add 5 new users, all new hires, to authentik, your identity management system. These users will be the first team members on the brand new Security team, so they will need some high-level permissions, with object permissions to create and remove other users, revoke permissions, and send recovery emails. They will also need [global permissions](../access-control/permissions.md#fundamentals-of-authentik-permissions) to control access to flows and stages.

The easiest workflow for setting up these new users involves [creating a role](./manage_roles.md#create-a-role) specifically for their type of work, and then [assigning that role to a group](./manage_roles.md#assign-a-role-to-a-group) to which all of the users belong.

## Viewing roles for users and groups

You can view the roles assigned to a user or group through their detail pages in the Admin interface.

### User roles

To view roles for a user:

1. Navigate to **Directory > Users** and click on a user's name.
2. Click the **Roles** tab.
3. The tab has two sub-tabs:
    - **Assigned Roles**: Shows roles directly assigned to this user.
    - **All Roles**: Shows all roles the user has, including roles inherited from groups they belong to. Inherited roles are marked with an "Inherited" label.

### Group roles

To view roles for a group:

1. Navigate to **Directory > Groups** and click on a group's name.
2. Click the **Roles** tab.
3. The tab has two sub-tabs:
    - **Assigned Roles**: Shows roles directly assigned to this group.
    - **All Roles**: Shows all roles the group has, including roles inherited from parent groups. Inherited roles are marked with an "Inherited" label.

To learn more about working with roles in authentik, refer to the following topics:




================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/property-mappings/expressions.md
================================================================================

---
title: Sources expression property mappings
---

The property mapping should return a value that is expected by the source. Returning `None` is always accepted and would simply skip the mapping for which `None` was returned.

## Variables

- Arbitrary arguments given by the source (this is documented by the source).
- `properties`: A Python dictionary containing the result of the previously run property mappings, plus the initial data computed by the source.
- `request`: The current request. This may be `None` if there is no contextual request. See ([Django documentation](https://docs.djangoproject.com/en/3.0/ref/request-response/#httprequest-objects))



## Available Functions





================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/property-mappings/index.md
================================================================================

---
title: Source property mappings
---

Source property mappings allow you to modify or gather extra information from sources.

This page is an overview of how property mappings work. For information about specific protocol, please refer to each protocol page:

- [Kerberos](../protocols/kerberos/#kerberos-source-property-mappings)
- [LDAP](../protocols/ldap/index.md#ldap-source-property-mappings)
- [OAuth](../protocols/oauth/index.mdx#oauth-source-property-mappings)
- [SAML](../protocols/saml/index.md#saml-source-property-mappings)
- [SCIM](../protocols/scim/index.md#scim-source-property-mappings)

## Create a custom source property mapping

If the default source mappings are not enough, or if you need to get additional data from the source, you can create your own custom source property mappings.

Here are the steps:

1. In authentik, open the Admin interface, and then navigate to **Customization > Property Mappings**.
2. Click **Create**, select the property mapping type for your source, and then click **Next**.
3. Type a unique and meaningful **Name**, such as `ldap-displayName-mapping:name`.
4. In the **Expression** field enter Python expressions to retrieve the value from the source. See [Expression Semantics](#expression-semantics) below for details.
5. In the source configuration, select the newly created property mapping as a **User property mapping** if it applies to users, or **Group property mapping** if it applies to groups.

## How it works

### Expression semantics

Each source provides the Python expression with additional data. You can import parts of that data into authentik users and groups. Assuming the source provides us with a `data` Python dictionary, you can write the following:

```python
return {
    "name": data.get("displayName"),
}
```

You can see that the expression returns a Python dictionary. The dictionary keys must match [User properties](../../user/user_ref.mdx#object-properties) or [Group properties](../../groups/group_ref.md#object-properties). Note that for users, `groups` and `group_attributes` cannot be set.

See each source documentation for a reference of the available data. See the authentik [expressions documentation](./expressions.md) for available data and functions.

Note that the [`list_flatten`](./expressions.md#list_flattenvalue-listany--any---optionalany) method is applied for all top-level properties, but not for attributes:

```python
return {
    "username": data.get("username"), # list_flatten is automatically applied to top-level attributes
    "attributes": {
        "phone": list_flatten(data.get("phoneNumber")), # but not for attributes!
    },
}
```

### Object construction process

A user or group object is constructed as follows:

1.  The source provides initial properties based on commonly used data.
2.  Each property mapping associated with the source is run and results are merged into the previous properties.
    - If a property mapping throws an error, the process is aborted. If that happens inside a synchronization process, the object is skipped. If it happens during an enrollment or authentication flow, the flow is cancelled.
    - If a property mapping sets one attribute to `None`, that attribute is then discarded.
3.  If the `username` field is not set for user objects, or the `name` field is not set for group objects, the process is aborted.
4.  The object is created or updated. The `attributes` property is merged with existing data if the object already exists.

### Group synchronization

LDAP and SCIM sources have built-in mechanisms to get groups. This section does not apply to them.

You can write a custom property mapping to set the user's groups:

```python
return {
    "groups": data.get("groups", []),
}
```

The `groups` attribute is a special attribute that must contain group identifiers. By default, those identifiers are also used as the group name by default, those identifiers are also used as the group name. Each of those identifiers is then given to group property mappings as the `group_id` variable, if extra processing needs to happen.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/social-logins/index.mdx
================================================================================

---
title: Federated Identity Providers
sidebar_label: Identity Providers
tags: [saml, oauth]
---

Configuring authentik with a federated identity provider allows users to authenticate with their existing credentials, such as social logins or enterprise identity providers.

Typically, identity providers use protocols such as [OAuth 2.0](https://en.wikipedia.org/wiki/OAuth) or [Security Assertion Markup Language](https://en.wikipedia.org/wiki/Security_Assertion_Markup_Language) (<abbr>SAML</abbr>). These protocols allow authentik to act as a Service Provider (<abbr>SP</abbr>), delegating the authentication process to the Identity Provider (<abbr>IdP</abbr>). The choice of protocol depends on the provider and the level of integration desired.

## IdP Initiated Single Sign-On

In this scenario, a user is logged in to the IdP and attempts to access a resource on a remote SP server. In this example, the IdP would be Google, Facebook, or another social login provider. The SP would be authentik, acting as a service provider.

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant IdP as Identity Provider
    participant SP as authentik
    participant Browser

    User->>IdP: Log in
    User->>SP: Access resource
    SP->>IdP: Request SAML assertion
    IdP->>IdP: Authenticate user
    IdP->>SP: Return SAML assertion
    SP->>Browser: Redirect to resource
```

In short, the user logs in to the IdP, requests access to a resource on the SP, and is redirected to the SP with a SAML assertion. The SP validates the assertion and establishes a session for the user.

## SP Initiated Single Sign-On

In this scenario, a user attempts to access a protected resource directly on an SP website without being logged in. The user does not have an account on the SP site, but does have a federated account managed by a third-party IdP. The SP sends an authentication request to the IdP. Both the request and the returned SAML assertion are sent through the user's browser via HTTP POST.

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant IdP as Identity Provider
    participant SP as authentik
    participant Browser

    User->>SP: Access resource
    SP->>IdP: Request SAML assertion
    IdP->>IdP: Authenticate user
    IdP->>SP: Return SAML assertion
    SP->>Browser: Redirect to resource
```

In short, the user requests access to a resource on the SP, the SP requests a SAML assertion from the IdP, the IdP authenticates the user and returns a SAML assertion, and the SP establishes a session for the user.

## Configuring authentik

While we provide detailed guides for popular services like Google, GitHub, and Azure AD, you can configure any standards-compliant provider using the same basic process.

authentik supports most identity providers that implement standard OAuth 2.0 or SAML 2.0 protocols. While each provider may have its own administrative interface, the core information needed is consistent, typically OAuth client credentials or SAML metadata.

Our provider-specific guides walk you through any unique steps needed for each service.

## See also

- [Google Identity Providers](./google/index.mdx)
- [Application Providers](./../../../add-secure-apps/providers/index.mdx)

## External references

- [Federated Identity](https://en.wikipedia.org/wiki/Federated_identity)
- [Social Login](https://en.wikipedia.org/wiki/Social_login)
- [OAuth](https://en.wikipedia.org/wiki/OAuth)
- [SAML](https://en.wikipedia.org/wiki/Security_Assertion_Markup_Language)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/directory-sync/active-directory/index.md
================================================================================

---
title: Active Directory
support_level: community
---

## Preparation

The following placeholders are used in this guide:

- `ad.company` is the name of the Active Directory domain.
- `authentik.company` is the FQDN of the authentik install.

## Active Directory configuration

To support the integration of Active Directory with authentik, you need to create a service account in Active Directory.

1. Open **Active Directory Users and Computers** on a domain controller or computer with **Active Directory Remote Server Administration Tools** installed.
2. Navigate to an Organizational Unit, right-click it, and select **New** > **User**.
3. Create a service account, matching your naming scheme, for example:

    ![](./01_user_create.png)

4. Set the password for the service account. Ensure that the **Reset user password and force password change at next logon** option is not checked.

    Either one of the following commands can be used to generate the password:

    ```sh
    pwgen 64 1
    ```

    ```sh
    openssl rand 36 | base64 -w 0
    ```

5. Open the **Delegation of Control Wizard** by right-clicking the domain Active Directory Users and Computers, and selecting **All Tasks**.
6. Select the authentik service account that you've just created.
7. Grant these additional permissions (only required when _User password writeback_ is enabled on the LDAP source in authentik, and dependent on your AD Domain)

    ![](./02_delegate.png)

:::info Limiting service account permissions
Optionally, if you don't want authentik to be able to view and sync objects within certain Organizational Units, you can limit the service account's permissions:

1. Right click the Organizational Unit in question and navigate to **Properties** > **Security**.
2. Select the authentik service account that you created.
3. Under the **Deny** column, check **Read**.
4. Click **Apply**.

You can repeat this process for other OUs and objects within Active Directory.
:::

## authentik Setup

To support the integration of authentik with Active Directory, you will need to create a new LDAP Source in authentik.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation & Social login**.
3. Click **Create** and select **LDAP Source** as the type.
4. Provide a name, slug, and the following required configurations:

    Under **Connection Settings**:
    - **Server URI**: `ldap://ad.company`

    :::info
    For authentik to be able to write passwords back to Active Directory, make sure to use `ldaps://` as a prefix. You can verify that LDAPS is working by opening the `ldp.exe` tool on a domain controller and attempting a connection to the server via port 636. If a connection can be established, LDAPS is functioning as expected. More information can be found in the [Microsoft LDAPS documentation](https://learn.microsoft.com/en-us/troubleshoot/windows-server/active-directory/ldap-over-ssl-connection-issues).

    Multiple servers can be specified by separating URIs with a comma (e.g. `ldap://dc1.ad.company,ldap://dc2.ad.company`). If a DNS entry with multiple records is used, authentik will select a random entry when first connecting.
    :::
    - **Bind CN**: `<service account>@ad.company`
    - **Bind Password**: the password of the service account created in the previous section.
    - **Base DN**: the base DN which you want authentik to sync.

    Under **LDAP Attribute Mapping**:
    - **User Property Mappings**: select all Mappings which start with "authentik default LDAP" and "authentik default Active Directory"
    - **Group Property Mappings**: select "authentik default LDAP Mapping: Name"

    Under **Additional Settings** _(optional)_ configurations that may need to be adjusted based on the setup of your domain:
    - **Group**: if enabled, all synchronized groups will be given this group as a parent.
    - **Addition User/Group DN**: additional DN which is _prepended_ to your Base DN configured above, to limit the scope of synchronization for Users and Groups.
    - **User object filter**: which objects should be considered users (e.g. `(objectClass=user)`). For Active Directory set it to `(&(objectClass=user)(!(objectClass=computer)))` to exclude Computer accounts.
    - **Group object filter**: which objects should be considered groups (e.g `(objectClass=group)`).
    - **Lookup using a user attribute**: acquire group membership from a User object attribute (`memberOf`) instead of a Group attribute (`member`). This works with directories and nested groups memberships (Active Directory, RedHat IDM/FreeIPA), using `memberOf:1.2.840.113556.1.4.1941:` as the group membership field.
    - **Group membership field**: the user object attribute or the group object attribute that determines the group membership of a user (e.g. `member`). If **Lookup using a user attribute** is set, this should be a user object attribute, otherwise a group object attribute.
    - **User membership attribute**: ensure that this is set to `distinguishedName`.
    - **Object uniqueness field**: a user attribute that contains a unique identifier (e.g. `objectSid`).

    :::info

5. Click **Finish** to save the LDAP Source. An LDAP synchronization will begin in the background. Once completed, you can view the summary by navigating to **Dashboards** > **System Tasks**:

    ![](./03_additional_perms.png)

6. To finalise the Active Directory setup, you need to enable the backend "authentik LDAP" in the Password Stage.

    ![](./11_ak_stage.png)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/directory-sync/freeipa/index.md
================================================================================

---
title: FreeIPA
support_level: community
---

## Preparation

The following placeholders are used in this guide:

- `svc_authentik` is the name of the bind account.
- `freeipa.company` is the Name of the domain.
- `ipa1.freeipa.company` is the Name of the FreeIPA server.

## FreeIPA Setup

1. Log in to FreeIPA.

2. Create a user in FreeIPA, matching your naming scheme. Provide a strong password, example generation methods: `pwgen 64 1` or `openssl rand 36 | base64 -w 0`. After you are done click **Add and Edit**.

    ![](./user_create.png)

3. In the user management screen, select the Roles tab.

    ![](./user_roles.png)

4. Add a role that has privileges to change user passwords, the default `User Administrators` role is sufficient. This is needed to support password resets from within authentik.

    ![](./add_user_role.png)

5. By default, if an administrator account resets a user's password in FreeIPA the user's password expires after the first use and must be reset again. This is a security feature to ensure password complexity and history policies are enforced. To bypass this feature for a more seamless experience, you can make the following modification on each of your FreeIPA servers:

    ```
    $ ldapmodify -x -D "cn=Directory Manager" -W -h ipa1.freeipa.company -p 389

    dn: cn=ipa_pwd_extop,cn=plugins,cn=config
    changetype: modify
    add: passSyncManagersDNs
    passSyncManagersDNs: uid=svc_authentik,cn=users,cn=accounts,dc=freeipa,dc=company
    ```

:::info
Additional info: [22.1.2. Enabling Password Reset Without Prompting for a Password Change at the Next Login](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/linux_domain_identity_authentication_and_policy_guide/user-authentication#user-passwords-no-expiry)
:::

## authentik Setup

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues.

See the [LDAP Source documentation](../../protocols/ldap) for more information on these settings.
:::

To create a new LDAP Source in authentik:

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social Login**, click **Create**, select **LDAP Source**, and click **Next**.
3. Configure the following settings:
    - **Name**: Provide a descriptive name for the LDAP source.
    - **Slug**: Provide a slug for the LDAP source.
    - **Update internal password on login**: Enable this if you want users to still be able to log in when FreeIPA is unavailable.
    - **Delete not found object**: Enable to delete users from authentik when they are deleted in FreeIPA.

    - Under **Connection settings**:
        - **Server URI**: `ldaps://ipa1.freeipa.company`
          :::tip
          You can specify multiple server URIs separated by commas (e.g. `ldap://ipa1.freeipa.company,ldap://ipa2.freeipa.company`); if using a DNS record with multiple entries, authentik will pick one at random on first connection.
          :::
        - **Enable StartTLS**: Enable for `ldap://` protocol, disable for `ldaps://`.
        - **TLS Verification Certificate**: Optionally select the certificate used to validate the remote certificate.
        - **Bind CN**: `uid=svc_authentik,cn=users,cn=accounts,dc=freeipa,dc=company`
        - **Bind Password**: The password for the above user account.
        - **Base DN**: `dc=freeipa,dc=company`

    - Under **LDAP Attribute mapping**:
        - **User Property Mappings**: Select all Mappings whose names begin with `authentik default LDAP` and `authentik default OpenLDAP`. Deselect any other Mappings that are selected by default.
        - **Group property mappings**: Select `authentik default OpenLDAP Mapping: cn`

    - Under **Additional settings**:
        - **Parent Group**: If selected, all synchronized groups will be given this authentik group as a parent.
        - **User Path**: The path that users will be saved under in authentik.
        - **Addition User/Group DN**: `cn=users,cn=accounts`
        - **Addition Group DN**: `cn=groups,cn=accounts`
        - **User object filter**: `(objectClass=person)`
        - **Group object filter**: `(objectClass=groupofnames)`
        - **Group membership field**: `memberOf`
        - **User membership attribute**: `distinguishedName`
        - **Lookup using user attribute**: Enabled.
        - **Object uniqueness field**: `ipaUniqueID`

    :::caution
    FreeIPA groups can contain nested groups. The `memberOf` user attribute lists all group memberships, direct and indirect.

    If you want to sync only direct group memberships, use the following settings:
    - **Group membership field**: `member`
    - **User membership attribute**: `distinguishedName`
    - **Lookup using user attribute**: Disabled.
      :::

4. Click **Finish**.

### Manual synchronization

After saving the source, start a synchronization by opening the source, going to the **Sync** tab, and clicking **Run sync again**.

Finally, confirm that the **User database + LDAP password** backend is selected in **Flows and Stages** > **Stages** > **Password Stage**.

![](./password_stage.png)

### Blueprints

You can also configure the LDAP source with a blueprint:

:::note
You must set the username (dn) and password in the environment variables `FREEIPA_DN` and `FREEIPA_PASSWORD`.
:::

```yaml
# yaml-language-server: $schema=https://goauthentik.io/blueprints/schema.json
version: 1
metadata:
    name: FreeIPA LDAP Source
    labels:
        blueprints.goauthentik.io/description: "LDAP Source configuration for FreeIPA"
entries:
    - model: authentik_sources_ldap.ldapsource
      identifiers:
          slug: ldap-source-freeipa
      attrs:
          enabled: true
          base_dn: dc=freeipa,dc=company
          additional_user_dn: cn=users,cn=accounts
          additional_group_dn: cn=groups,cn=accounts
          bind_cn: !Env FREEIPA_DN
          bind_password: !Env FREEIPA_PASSWORD
          delete_not_found_objects: true
          group_membership_field: memberOf
          group_object_filter: (objectClass=groupofnames)
          lookup_groups_from_user: true
          object_uniqueness_field: ipaUniqueID
          server_uri: ldaps://ipa1.freeipa.company,ldaps://ipa2.freeipa.company
          sni: true
          sync_groups: true
          sync_users: true
          sync_users_password: true
          user_membership_attribute: distinguishedName
          user_object_filter: (objectClass=person)
          user_property_mappings:
              - !Find [
                    authentik_sources_ldap.ldapsourcepropertymapping,
                    [managed, goauthentik.io/sources/ldap/openldap-cn],
                ]
              - !Find [
                    authentik_sources_ldap.ldapsourcepropertymapping,
                    [managed, goauthentik.io/sources/ldap/openldap-uid],
                ]
              - !Find [
                    authentik_sources_ldap.ldapsourcepropertymapping,
                    [managed, goauthentik.io/sources/ldap/default-mail],
                ]
              - !Find [
                    authentik_sources_ldap.ldapsourcepropertymapping,
                    [managed, goauthentik.io/sources/ldap/default-dn-path],
                ]
              - !Find [
                    authentik_sources_ldap.ldapsourcepropertymapping,
                    [managed, goauthentik.io/sources/ldap/default-name],
                ]
          group_property_mappings:
              - !Find [
                    authentik_sources_ldap.ldapsourcepropertymapping,
                    [managed, goauthentik.io/sources/ldap/openldap-cn],
                ]
```

:::note
If using LDAP, prepend the server URI with `ldap://` and include `start_tls: true`.
:::



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/social-logins/shibboleth/index.md
================================================================================

---
title: Shibboleth
tags:
    - source
    - shibboleth
    - saml
---

Allows users to authenticate using their [Shibboleth](https://www.shibboleth.net/about-us/the-shibboleth-project/) credentials by configuring Shibboleth as a federated identity provider via SAML.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `shibboleth.company` is the FQDN of the Shibboleth IdP installation.
- `shibboleth-slug` is the slug you will assign to the SAML source in authentik (e.g., `shibboleth`).

## authentik configuration

To integrate Shibboleth with authentik you will need to create a SAML source in authentik.

### Create a SAML source in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login** and click **Create**.
3. Select **SAML Source** and configure the following settings:
    - Set **Name** to `Shibboleth`.
    - Set **Slug** to `shibboleth` (this sets the slug used in Shibboleth's metadata url).
    - Set **SSO URL** to `https://shibboleth.company/idp/profile/SAML2/Redirect/SSO`.
    - Set **Binding Type** to `Redirect`.
    - Set **Issuer** to `https://authentik.company/source/saml/<shibboleth-slug>/metadata/`.
    - Set **NameID Policy** to `Transient`.
      :::warning NameID Policy
      Shibboleth supports the `Transient` NameID by default. You will need to reconfigure Shibboleth to use other NameIDs.
      :::
    - Set **Signing Keypair** to an authentik certificate (e.g., the default `authentik Self-signed Certificate`).
    - Set **Encryption Certificate** to an authentik certificate (e.g., the default `authentik Self-signed Certificate`).
4. Click **Finish**.

:::info Display new source on login screen
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source).
:::

## Shibboleth configuration

To integrate Shibboleth with authentik you will need to add authentik as a service provider in your Shibboleth IdP.

### Add authentik as a Service Provider

1. Edit `/opt/shibboleth-idp/conf/metadata-providers.xml` on the Shibboleth IdP server.
2. Add the following `MetadataProvider` element before the final closing tag of the existing `MetadataProvider` block:

```xml


================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/social-logins/apple/index.md
================================================================================

---
title: Apple
tags:
    - source
    - apple
---

Allows users to authenticate using their Apple ID credentials by configuring Apple as a federated identity provider via OAuth2.

## Preparation

The following placeholders are used in this guide:

Apple mandates the use of a [registered top-level domain](https://en.wikipedia.org/wiki/List_of_Internet_top-level_domains), therefore this source will not work with `.local` and other non-public TLDs.

## Apple configuration

To integrate Apple with authentik, you will need to register two identifiers and a key in the Apple Developer Portal.

### Registering identifiers

1. Log in to the [Apple Developer Portal](https://developer.apple.com/account/), and navigate to **Account** > **Certificates, IDs & Profiles**, then click **Identifiers** in the sidebar.
2. Register a new identifier with the type of **App IDs**, and the subtype **App**.
3. Choose a name that users will recognize for the **Description** field (e.g. `authentik`).
4. For your **Bundle ID**, use the reverse of your authentik domain, for example: `company.authentik`.
5. Scroll down the list of capabilities, and check the box next to **Sign In with Apple**.
6. At the top, click **Continue** and **Register**.

![](./app_id.png)

7. Register another new identifier with the type of **Services IDs**.
8. Again, choose the same name as above for your **Description** field.
9. Use the same identifier as above, but add a suffix like `signin` or `oauth`, as identifiers are unique.
10. At the top, click **Continue** and **Register**.

![](./service_id.png)

### Configuring identifier

11. Once back at the overview list, click on the just-created identifier.
12. Enable the checkbox next to **Sign In with Apple**, and click **Configure**
13. Under **Domains and Subdomains**, enter `authentik.company`.
14. Under **Return URLs**, enter `https://authentik.company/source/oauth/callback/apple/`.

![](./app_service_config.png)

### Registering a key

15. Click **Keys** in the sidebar, then register a new key with any name, and select **Sign in with Apple**.
16. Click **Configure**, then select the App ID that you created.
17. At the top, click **Save**, **Continue** and **Register**.
18. Download the Key file and note the **Key ID**.

![](./key.png)

19. Take note of the **Team ID** visible at the top of the page.

## authentik configuration

To support the integration of Apple with authentik, you need to create an Apple OAuth source in authentik.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, then configure the following settings:
    - **Select type**: select **Apple OAuth Source**.
    - **Create Apple OAuth Source**: provide a name, a slug which must match the slug used in the Apple `Return URL`, and the following required configurations:
        - Under **Protocol Settings**:
            - **Consumer key**: The identifier from step 9, then `;`, then your **Team ID** from step 19, then `;`, then the **Key ID** from step 18. (e.g. `company.authentik;JQNH45HN7V;XFBNJ82BV6`).
            - **Consumer secret**: Paste the contents of the keyfile you've downloaded.
            - **Scopes** _(optional)_: define any further access scopes.

3. Click **Save**.

:::info Display new source on login screen
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source).
:::

## Source property mappings

Source property mappings allow you to modify or gather extra information from sources. See the [overview](../../property-mappings/index.md) for more information.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/social-logins/github/index.mdx
================================================================================

---
title: GitHub
tags:
    - source
    - github
---

Allows users to authenticate using their GitHub credentials by configuring GitHub as a federated identity provider via OAuth2.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `www.my.company` is the Homepage URL for your site

## GitHub configuration

To integrate GitHub with authentik, you need to create an OAuth application in GitHub Developer Settings.

1. Log in to GitHub and open the [Developer Settings](https://github.com/settings/developers) menu.
2. Create an OAuth app by clicking on the **Register a new application** button and set the following values:
    - **Application Name**: `authentik`
    - **Homepage URL**: `www.my.company`
    - **Authorization callback URL**: `https://authentik.company/source/oauth/callback/github`

3. Click **Register Application**
4. Click **Generate a new client secret** and take note of the **Client Secret** and **Client ID**. These values will be required in the next section.

## authentik configuration

To support the integration of GitHub with authentik, you need to create a GitHub OAuth source in authentik.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **GitHub OAuth Source** as the source type.
    - **Create GitHub OAuth Source**: provide a name, a slug which must match the slug used in the GitHub `Authorization callback URL` field (e.g. `github`), and set the following required configurations:
        - **Protocol settings**
            - **Consumer Key**: `<client_ID>`
            - **Consumer Secret**: `<client_secret>`
            - **Scopes** _(optional)_: define any further access scopes.
3. Click **Finish** to save your settings.

:::info Display new source on login screen
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source/).
:::

## Optional additional configuration

### Checking for membership of a GitHub Organization

:::info
Ensure that the GitHub OAuth source in **Federation & Social login** has the additional `read:org` scope added under **Protocol settings** > **Scopes**.
:::

To check if the user is a member of an organization, you can use the following policy on your flows.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies**.
3. Click **Create**, select **Expression Policy** and then **Next**.
4. Provide a name for the policy and set the following expression:

```python
from authentik.sources.oauth.models import OAuthSource

# Set this value
accepted_org = "your_organization"

# Ensure flow is only run during OAuth logins via GitHub
if not isinstance(context['source'], OAuthSource) or context["source"].provider_type != "github":
    return True

# Get the user-source connection object from the context, and get the access token
connection = context["goauthentik.io/sources/connection"]
access_token = connection.access_token

# We also access the user info authentik already retrieved, to get the correct username
github_username = context["oauth_userinfo"]

# GitHub does not include organizations in the userinfo endpoint, so we have to call another URL
orgs_response = requests.get(
    "https://api.github.com/user/orgs",
    auth=(github_username["login"], access_token),
    headers={
        "accept": "application/vnd.github.v3+json"
    }
)
orgs_response.raise_for_status()
orgs = orgs_response.json()

# `orgs` will be formatted like this
# [
#     {
#         "login": "goauthentik",
#         [...]
#     }
# ]
user_matched = any(org['login'] == accepted_org for org in orgs)
if not user_matched:
    ak_message(f"User is not member of {accepted_org}.")
return user_matched
```

5. Click **Finish**. You can now bind this policy to the chosen enrollment and/or authentication flow of the GitHub OAuth source.
6. Navigate to **Flows and Stages** > **Flows** and click the name of the flow in question.
7. Open the **Policy/Group/User Bindings** tab and click **Bind existing Policy/Group/User**.
8. Select the policy that you previously created and click **Create**.
9. Optionally, repeat the process for any other flows that you want the policy applied to.

If a user is not a member of the chosen organization, they will see this message:

![](./github_org_membership.png)

## Source property mappings

Source property mappings allow you to modify or gather extra information from sources. See the [overview](../../property-mappings/index.md) for more information.

## Resources



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/social-logins/keycloak/index.md
================================================================================

---
title: Keycloak
tags:
    - source
    - keycloak
    - saml
---

Allows users to authenticate using their Keycloak credentials by configuring Keycloak as a federated identity provider via SAML.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `keycloak.company` is the FQDN of the Keycloak installation.
- `keycloak-slug` is the slug you will assign to the SAML source in authentik (e.g., `keycloak`).

## Export certificates

Before configuring either service, you need to export the signing certificates from both Keycloak and authentik. Each service needs the other's public certificate to verify signatures and handle SAML encryption.

### Export the Keycloak signing certificate

1. Log in to Keycloak as an administrator.
2. Navigate to **Realm settings** > **Keys**.
3. Find the RSA key with **Use** set to `SIG`.
4. Click **Certificate** to copy the certificate value.
5. Save the certificate in the following format:

```
-----BEGIN CERTIFICATE-----


================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/social-logins/plex/index.md
================================================================================

---
title: Plex
tags:
    - source
    - plex
---

Allows users to authenticate using their Plex credentials by configuring Plex as a federated identity provider via OAuth2.

## Preparation

None

## authentik configuration

To support the integration of Plex with authentik, you need to create a Plex source in authentik.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **Plex Source** as the source type.
    - **Create Plex Source**: provide a name, a slug, and set the following required configurations:
        - **Protocol settings**
            - **Client ID**: Set a unique Client ID or leave the generated ID
                - Click **Load Servers** to log in to Plex and pick the authorized Plex servers for "allowed users".
                - Decide if _anyone_ with a Plex account can authenticate or only friends you share access with.
3. Click **Finish** to save your settings.

:::info
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source/).
:::

## Source property mappings

Source property mappings allow you to modify or gather extra information from sources. See the [overview](../../property-mappings/index.md) for more information.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/social-logins/twitter/index.md
================================================================================

---
title: X (Twitter)
tags:
    - source
    - x
    - twitter
---

Allows users to authenticate using their X credentials by configuring X as a federated identity provider via OAuth2.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

## X configuration

To integrate X with authentik you will need to create an OAuth application in the X Developer Portal.

1. Log in to the [X Developer Portal](https://developer.twitter.com/).
2. Navigate to **Projects & Apps** > **Overview**.
3. Click the **App Settings** icon (cogwheel) next to the Project App that you want to use. For information on creating a new Project App, refer to the [X Developer Documentation](https://docs.x.com/fundamentals/developer-apps#app-management).
4. Under **User authentication settings**, click **Set up** and set the following required fields:
    - **App permissions**: `Read`
    - **Type of App**: `Web App, Automated App or Bot`
    - **Callback URI / Redirect URL**: `https://authentik.company/source/oauth/callback/x/`
    - **Website URL**: `https://authentik.company`

5. Click **Save**.
6. Take note of the **Client ID** and **Client Secret**. These values will be required in the next section.
7. Click **Done**.

## authentik configuration

To support the integration of X with authentik, you need to create a Twitter OAuth source in authentik.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **Twitter OAuth Source** as the source type.
    - **Create OAuth Source**: provide a name, a slug which must match the slug used in the X `Callback URI / Redirect URL` field (e.g. `x`), and set the following required configurations:
        - **Protocol settings**
            - **Consumer Key**: Enter the Client ID from the X Developer Portal.
            - **Consumer Secret**: Enter the Client Secret from the X Developer Portal.
            - **Scopes** _(optional)_: define any further access scopes.
3. Click **Finish**.

:::info
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source/).
:::

## Resources

- [X Developer Portal Documentation](https://docs.x.com/fundamentals/developer-portal)
- [X Developer Documentation - App Management](https://docs.x.com/fundamentals/developer-apps#app-management)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/social-logins/facebook/index.md
================================================================================

---
title: Facebook
tags:
    - source
    - facebook
    - meta
---

Allows users to authenticate using their Facebook credentials by configuring Facebook as a federated identity provider via OAuth2.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

## Facebook configuration

To integrate Facebook with authentik you will need to create an OAuth application in the Meta for Developers Dashboard.

1. Log in to the [Meta for Developers Dashboard](https://developers.facebook.com/) with your Facebook account.
2. After logging in, [register as a developer](https://developers.facebook.com/async/registration). Refer to the [Facebook development documentation](https://developers.facebook.com/docs/development) for more information.

After registering, you need to create an application so that Facebook generates a unique ID for authentik.

3. On the [Meta for Developers Dashboard](https://developers.facebook.com/) click **Create**.
4. Follow the prompts to create the application.

After creating the application you need to customize its login settings.

5. On the [Meta for Developers Dashboard](https://developers.facebook.com/) click **Use Cases** in the left navigation pane.
6. Under **Authentication and account creation** click **Customize** and then **Go to settings**.
7. Set the **Valid OAuth redirect URIs** field to `https://authentik.company/source/oauth/callback/facebook/` and then click **Save**.
8. Navigate to the **Use cases** > **Customize** page.
9. Under **Permissions** click **Add** for the **email** permission.

Next, you need to obtain the **App ID** and **App Secret** for the Facebook app. These will be required when creating the source in authentik.

10. Go back to the Dashboard, and in the bottom left of the navigation pane, click **App settings** > **Basic**.
11. Take note of the **App ID** and the **App secret** values.

Finally, you need to publish the Facebook app.

12. Go back to the Dashboard, and on the **Create and publish this app** page, follow the prompts to complete the process.

## authentik configuration

To support the integration of Facebook with authentik, you need to create a Facebook OAuth source in authentik.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **Facebook OAuth Source** as the source type.
    - **Create Facebook OAuth Source**: provide a name, a slug which must match the slug used in the Facebook `Valid OAuth redirect URIs` field (e.g. `facebook`), and the following required configurations:
        - **Protocol settings**
            - **Consumer Key**: enter the **App ID** from Facebook.
            - **Consumer Secret**: enter the **App Secret** from Facebook.
            - **Scopes** _(optional)_: define any further access scopes.
3. Click **Finish** to save your settings.

:::info Display new source on login screen
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source/).
:::

## Source property mappings

Source property mappings allow you to modify or gather extra information from sources. See the [overview](../../property-mappings/index.md) for more information.

## Resources

- [Meta for Developers Documentation - Facebook Login Overview](https://developers.facebook.com/docs/facebook-login/overview)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/social-logins/google/index.mdx
================================================================================

---
title: Google Identity Providers
sidebar_label: Google
tags:
    - source
    - google
    - saml
    - oidc
    - google workspace
    - google cloud
---

There are several ways that Google services can be integrated with authentik to allow for authentication with Google user credentials.

:::info authentik as a third-party IdP
authentik can also be configured to authenticate users to Google services.

For more information, see the [Google Workspace Integration](/integrations/services/google/) guide.
:::

## Google Cloud (OAuth)

Google Cloud Identity Platform provides OAuth 2.0 as a federated identity provider. This configuration guide shows how to set up OAuth 2.0 as the authentication method between Google and authentik.

[Configure Google Cloud with authentik](./cloud/index.md)

## Google Workspace (SAML)

Google Workspace (formerly G Suite) allows users to authenticate to applications using their company email addresses. This configuration guide shows how to set up Security Assertion Markup Language (SAML) as the authentication method between Google Workspace and authentik.

[Configure Google Workspace with authentik](./workspace/index.md)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/social-logins/wechat/index.md
================================================================================

---
title: WeChat
tags:
    - source
    - wechat
---

Allows users to authenticate using their WeChat credentials by configuring WeChat as a federated identity provider via OAuth2.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

## WeChat configuration

To integrate WeChat with authentik you will need to register a "Website Application" (网站应用) on the [WeChat Open Platform](https://open.weixin.qq.com/).

1. Register for a developer account on the [WeChat Open Platform](https://open.weixin.qq.com/).
2. Navigate to the **Management Center** (管理中心) > **Website Application** (网站应用) and click **Create Website Application** (创建网站应用).
3. Submit the application for review.
4. Once approved, you will obtain an **AppID** and **AppSecret**.
5. In the WeChat application settings, configure the **Authorized Callback Domain** (授权回调域) to match your authentik domain (e.g. `authentik.company`).

:::info
This integration uses the WeChat "Website Application" login flow (QR Code login). When users access the login page on a desktop device (Windows/Mac) with the WeChat client installed, they may see a "Fast Login" prompt.
:::

## authentik configuration

To support the integration of WeChat with authentik, you need to create a WeChat OAuth source in authentik.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **WeChat OAuth Source** as the source type.
    - **Create OAuth Source**: provide a name, a slug (e.g. `wechat`), and set the following required configurations:
        - **Protocol settings**
            - **Consumer Key**: Enter the **AppID** from the WeChat Open Platform.
            - **Consumer Secret**: Enter the **AppSecret** from the WeChat Open Platform.
            - **Scopes**: define any further access scopes.
3. Click **Finish**.

:::info Display new source on login screen
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source/).
:::

## Source property mappings

Source property mappings allow you to modify or gather extra information from sources. See the [overview](../../property-mappings/index.md) for more information.

The following data is retrieved from WeChat and mapped to the user's attributes in authentik:

| WeChat Field            | authentik Attribute     | Description                     |
| :---------------------- | :---------------------- | :------------------------------ |
| `unionid` (or `openid`) | `username`              | Used as the primary identifier. |
| `nickname`              | `name`                  | The user's display name.        |
| `headimgurl`            | `attributes.headimgurl` | URL to the user's avatar.       |
| `sex`                   | `attributes.sex`        | Gender (1=Male, 2=Female).      |
| `city`                  | `attributes.city`       | User's city.                    |
| `province`              | `attributes.province`   | User's province.                |
| `country`               | `attributes.country`    | User's country.                 |

### User Matching

WeChat users are identified by their `unionid` (if available) or `openid`.

- **UnionID**: Unique across multiple applications under the same developer account. authentik prioritizes this as the username.
- **OpenID**: Unique to the specific application. Used as a fallback if `unionid` is not returned.

:::info
WeChat does not provide the user's email address via the API.
:::

## Resources

- [WeChat Open Platform](https://open.weixin.qq.com/)
- [WeChat Login document](https://developers.weixin.qq.com/doc/oplatform/Website_App/WeChat_Login/Wechat_Login.html)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/social-logins/discord/index.md
================================================================================

---
title: Discord
tags:
    - source
    - discord
---

Allows users to authenticate using their Discord credentials by configuring Discord as a federated identity provider via OAuth2.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

## Discord configuration

To integrate Discord with authentik you will need to create an OAuth application in the Discord Developer Portal.

1. Log in to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Navigate to **Applications** and click **New Application**.
3. Provide a name for the application, accept the terms, and then click **Create**.
4. Select **OAuth2** in the sidebar.
5. Under **Client Secret**, click **Reset Secret** and follow the steps.
6. Take note of the **Client ID** and **Client Secret**. They will be required in the next section.
7. Click **Add Redirect** and enter `https://authentik.company/source/oauth/callback/discord/`.

## authentik configuration

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **Discord OAuth Source** as the source type.
    - **Create Discord OAuth Source**: provide a name, a slug which must match the slug used in the Discord `Redirect URI` (e.g. `discord`), and the following required configurations:
        - Under **Protocol Settings**:
            - **Consumer key**: set the Client ID from Discord.
            - **Consumer secret**: set the Client Secret from Discord.
            - **Scopes** _(optional)_: if you need authentik to sync guild membership information from Discord, add the `guilds guilds.members.read` scope.

3. Click **Save**.

:::info Display new source on login screen
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source).
:::

## Optional additional configuration

### Syncing Discord roles and avatars to authentik

The following property mapping allows you to synchronize roles from a Discord guild to roles in authentik.

Whenever a user enrolls in authentik via a Discord source, this property mapping will check the user's Discord roles and update the user's authentik groups accordingly.

:::info Group Attribute
Any authentik group that you want to sync with a Discord role needs to have a `discord_role_id` attribute set with the ID of the Discord role.
Example: `discord_role_id: "<ROLE ID>"`

This group attribute can be set via **Directory** > **Groups** > **Your_Group** > **Attributes**.
:::

:::info Required OAuth Scopes
Ensure that the Discord OAuth source in **Federation & Social login** has the additional `guilds guilds.members.read` scopes added under **Protocol settings** > **Scopes**.
:::

:::info Avatar Setting
In order to use the created avatar attribute in authentik you will need to set the [authentik avatar configuration](../../../../sys-mgmt/settings.md#avatars).
:::

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings**.
3. Click **Create**, select **OAuth Source Property Mapping** and then **Next**.
4. Provide a name for the mapping and set the following expression:

```python
from authentik.core.models import Group

# To get the guild ID number for the parameters, open Discord, go to Settings > Advanced and enable developer mode.
# Right-click on the server/guild title and select "Copy ID" to get the guild ID.

#Set these values
ACCEPTED_GUILD_ID = "123456789123456789" # Discord server id to fetch roles from
AVATAR_SIZE = "64" # Valid avatar size values: 16,32,64,128,256,512,1024.
# Larger values than 64 may cause HTTP error 431 on applications/providers
# due to headers being too large.

# Generate avatar URL and base64 avatar image
avatar_url = None
avatar_base64 = None

if info.get("avatar"):
    avatar_url = (f"https://cdn.discordapp.com/avatars/{info.get('id')}/"
                  f"{info.get('avatar')}.png?size={AVATAR_SIZE}")
    try:
        response = client.do_request("GET", avatar_url)
        encoded_image = base64.b64encode(response.content).decode('utf-8')
        avatar_base64 = f"data:image/png;base64,{encoded_image}"
    except:
        avatar_base64 = None

# Get guild membership
guild_url = f"https://discord.com/api/v10/users/@me/guilds/{ACCEPTED_GUILD_ID}/member"
guild_response = client.do_request("GET", guild_url, token=token)
guild_data = guild_response.json()

# Get matching groups
user_groups = Group.objects.filter(attributes__discord_role_id__in=guild_data["roles"])

# Return user data
return {
    "name": info.get("global_name"),
    "attributes.discord": {
        "id": info.get("id"),
        "username": info.get("username"),
        "discriminator": info.get("discriminator"),
        "email": info.get("email"),
        "avatar": info.get("avatar"),
        "avatar_url": avatar_url
    },
    "groups": [group.name for group in user_groups],
    "attributes.avatar": avatar_base64
}
```

5. Click **Finish**.
6. Navigate to **Directory** > **Federation and Social login** and click the **Edit** icon next to your Discord OAuth Source.
7. Under **OAuth Attribute mapping** add the newly created property mapping to **Selected User Property Mappings**.
8. Click **Update**.

### Checking Discord Guild membership

:::info
Ensure that the Discord OAuth source in **Federation & Social login** has the additional `guilds guilds.members.read` scopes added under **Protocol settings** > **Scopes**.
:::

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies**.
3. Click **Create**, select **Expression Policy** and then **Next**.
4. Provide a name for the policy and set the following expression:

```python
from authentik.sources.oauth.models import OAuthSource

# To get the guild ID number for the parameters, open Discord, go to Settings > Advanced and enable developer mode.
# Right-click on the server/guild title and select "Copy ID" to get the guild ID.

# Set these values
ACCEPTED_GUILD_ID = "123456789123456789"
GUILD_NAME_STRING = "The desired server/guild name in the error message."

# The following sections should not need to be edited
# Ensure flow is only run during OAuth logins via Discord
if not isinstance(context['source'], OAuthSource) or context['source'].provider_type != "discord":
    return True

# Get the user-source connection object from the context, and get the access token
connection = context.get("goauthentik.io/sources/connection")
if not connection:
  return False
access_token = connection.access_token

guilds = requests.get(
    "https://discord.com/api/users/@me/guilds",
    headers= {
        "Authorization": f"Bearer {access_token}",
    }
).json()

user_matched = any(ACCEPTED_GUILD_ID == g["id"] for g in guilds)
if not user_matched:
    ak_message(f"User is not a member of {GUILD_NAME_STRING}.")
return user_matched
```

5. Click **Finish**. You can now bind this policy to the chosen enrollment and/or authentication flow of the Discord OAuth source.
6. Navigate to **Flows and Stages** > **Flows** and click the name of the flow in question.
7. Open the **Policy/Group/User Bindings** tab and click **Bind existing Policy/Group/User**.
8. Select the policy that you previously created and click **Create**.
9. Optionally, repeat the process for any other flows that you want the policy applied to.

### Checking Discord Guild role membership

:::info
Ensure that the Discord OAuth source in **Federation & Social login** has the additional `guilds guilds.members.read` scopes added under **Protocol settings** > **Scopes**.
:::

To check if the user is a member of a Discord Guild role, you can use the following policy on your flows:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies**.
3. Click **Create**, select **Expression Policy** and then **Next**.
4. Provide a name for the policy and set the following expression:

```python
from authentik.sources.oauth.models import OAuthSource

# To get the guild ID number for the parameters, open Discord, go to Settings > Advanced and enable developer mode.
# Right-click on the server/guild title and select "Copy ID" to get the guild ID.
# Right-click on the server/guild title and select server settings > roles, right click on the role and click "Copy ID" to get the role ID.

#Set these values
ACCEPTED_GUILD_ID = "123456789123456789"
GUILD_NAME_STRING = "The desired server/guild name in the error message."
ACCEPTED_ROLE_ID = "123456789123456789"
ROLE_NAME_STRING = "The desired role name in the error message."

GUILD_API_URL = f"https://discord.com/api/users/@me/guilds/{ACCEPTED_GUILD_ID}/member"

# The following sections should not need to be edited
# Ensure flow is only run during OAuth logins via Discord
if not isinstance(context['source'], OAuthSource) or context['source'].provider_type != "discord":
    return True

# Get the user-source connection object from the context, and get the access token
connection = context.get("goauthentik.io/sources/connection")
if not connection:
  return False
access_token = connection.access_token

guild_member_object = requests.get(
    GUILD_API_URL,
    headers= {
        "Authorization": f"Bearer {access_token}",
    }
).json()

# The response for JSON errors is held within guild_member_object['code']
# See: https://discord.com/developers/docs/topics/opcodes-and-status-codes#json
# If the user isn't in the queried guild, it gives the somewhat misleading code = 10004.
if "code" in guild_member_object:
    if guild_member_object['code'] == 10004:
        ak_message(f"User is not a member of {GUILD_NAME_STRING}.")
    else:
        ak_create_event("discord_error", source=context['source'], code=guild_member_object['code'])
        ak_message("Discord API error, try again later.")
    # Policy does not match if there is any error.
    return False

user_matched = any(ACCEPTED_ROLE_ID == g for g in guild_member_object["roles"])
if not user_matched:
    ak_message(f"User is not a member of the {ROLE_NAME_STRING} role in {GUILD_NAME_STRING}.")
return user_matched
```

5. Click **Finish**. You can now bind this policy to the chosen enrollment and/or authentication flow of the Discord OAuth source.
6. Navigate to **Flows and Stages** > **Flows** and click the name of the flow in question.
7. Open the **Policy/Group/User Bindings** tab and click **Bind existing Policy/Group/User**.
8. Select the policy that you previously created and click **Create**.
9. Optionally, repeat the process for any other flows that you want the policy applied to.

## Resources

- [Discord Developer Documentation](https://discord.com/developers/docs/intro)
- [Discord Developer Documentation - OAuth2](https://discord.com/developers/docs/topics/oauth2#oauth2)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/social-logins/mailcow/index.md
================================================================================

---
title: Mailcow
tags:
    - source
    - mailcow
---

Allows users to authenticate using their Mailcow credentials by configuring Mailcow as a federated identity provider via OAuth2.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `mailcow.company` is the FQDN of the Mailcow installation.

## Mailcow configuration

To integrate Mailcow with authentik you will need to create an OAuth application in Mailcow.

1. Log in to Mailcow as an administrator
2. Navigate to **System** > **Configuration**, and then **Access** > **OAuth2 Apps**.
3. Click **Add OAuth2 client** and provide the **Redirect URI**: `https://authentik.company/source/oauth/callback/mailcow/`
4. Take note of the **Client ID** and **Client Secret**. These values will be required in the next section.

## authentik configuration

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **OAuth Source** as the source type.
    - **Create OAuth Source**: provide a name, a slug which must match the slug used in the Mailcow `Redirect URI` field (e.g. `mailcow`), and set the following required configurations:
        - **Protocol settings**
            - **Consumer Key**: `<client_ID>`
            - **Consumer Secret**: `<client_secret>`
            - **Scopes** _(optional)_: define any further access scopes.
        - **URL Settings**
            - **Authorization URL**: `https://mailcow.company/oauth/authorize`
            - **Access token URL**: `https://mailcow.company/oauth/token`
            - **Profile URL**: `https://mailcow.company/oauth/profile`
3. Click **Finish** to save your settings.

:::info
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source/).
:::

## Source property mappings

Source property mappings allow you to modify or gather extra information from sources. See the [overview](../../property-mappings/index.md) for more information.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/social-logins/entra-id/index.mdx
================================================================================

---
title: Entra ID
tags:
    - source
    - entra
    - azure
    - scim
    - oauth
---

There are several ways that Entra ID can be integrated with authentik to allow for user and group provisioning and authentication with Entra ID user credentials.

## OAuth

The [Entra ID OAuth](./oauth/index.mdx) guide explains how to set up Entra ID as a federated OAuth identity provider for authentik.

This enables users to sign in to authentik using their Entra ID credentials. User accounts are created in authentik upon first login and updated on each subsequent login.

Alternatively, Entra ID authentication can be embedded into a flow via a [Source stage](../../../../../add-secure-apps/flows-stages/stages/source).

## SCIM

The [Entra ID SCIM](./scim/index.mdx) guide explains how you can provision users and groups from Entra ID into authentik via the SCIM protocol.

Optionally, both the OAuth and SCIM integrations can be used in conjunction so that users and groups are provisioned before a user signs in using their Entra ID credentials. This is the recommended setup for organizations with large numbers of users and groups.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/social-logins/okta/index.md
================================================================================

---
title: Okta
description: "Integrate Okta as a source in authentik"
tags: [source, okta]
---

Allows users to authenticate using their Okta credentials by configuring Okta as a federated identity provider via OAuth2.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `company.okta.com` is the FQDN of your Okta tenant.

## Okta configuration

To integrate Okta with authentik you will need to create an App Integration in the Okta Admin Console.

1. Log in to the Okta Admin Console as an administrator.
2. Navigate to **Applications** > **Applications** > **Add App Integration**.
3. Select **OIDC - OpenID Connect**, set **Application Type** to **Web Application**, and then click **Next**.
4. Configure the following required settings:
    - **App Integration Name**: `authentik`
    - **Sign-in redirect URIs**: `https://authentik.company/source/oauth/callback/<source_slug>/`
    - Under **Assignments**, select how you'd like to control access to authentik. **Allow everyone in your organization to access** or select a group to limit access.
5. Click **Save**.
6. Under **Client Credentials**, take note of the **Client ID**. This value will be required in the next section.
7. Under **CLIENT SECRETS**, click the **Copy to clipboard** next to the secret and take note of the value, it will also be required in the next section.

## authentik configuration

To support the integration of Okta with authentik, you need to create an Okta OAuth source in authentik.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **Okta OAuth Source** as the source type.
    - **Create Okta OAuth Source**: provide a name, a slug which must match the slug used in the Okta Sign-in redirect URI field (e.g. `okta`), and the following required settings:
        - Under **Protocol settings**:
            - **Consumer key**: paste the **Client ID** from Okta
            - **Consumer secret**: paste the **Secret** from Okta
        - Under **URL settings**:
            - **Authorization URL**: `https://company.okta.com/oauth2/v1/authorize`
            - **Access Token URL**: `https://company.okta.com/oauth2/v1/token`
            - **Profile URL**: `https://company.okta.com/oauth2/v1/userinfo`
            - **OIDC Well-known URL**: `https://company.okta.com/.well-known/openid-configuration`
            - **OIDC JWKS URL**: `https://company.okta.com/oauth2/v1/keys`

3. Click **Finish** to save your settings.

:::info Display new source on login screen
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source/).
:::

## Source property mappings

Source property mappings allow you to modify or gather extra information from sources. See the [overview](../../property-mappings/index.md) for more information.

## Resources

- [Okta Developer Documentation - Create an app integration](https://developer.okta.com/docs/guides/create-an-app-integration/openidconnect/main/)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/social-logins/telegram/index.md
================================================================================

---
title: Telegram
support_level: community
---

Configuring Telegram as a source allows users to authenticate within authentik using their Telegram account credentials.

## Preparation

Using Telegram as a source requires that your authentik instance is served from a domain.

## Telegram configuration

To use Telegram as a source, you first need to register a Telegram bot:

1. Start a chat with `@BotFather` on Telegram.
2. Use the `/newbot` command to create a new bot. Define a name and username for your new bot (e.g., `authentik_bot`).
3. BotFather will provide you with a token for the new bot. Take note of the username and token because they will be required when setting up the source in authentik.
4. Link the bot to your authentik domain name using the `/setdomain` command.

:::note
The domain name set in Telegram must **exactly** match the FQDN of the authentik installation.
:::

Now that the bot is configured you can proceed to creating a source in authentik.

## authentik configuration

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **Telegram** as the source type.
    - **Create Telegram Source**: provide a name, a slug, and the following required configurations:
        - **Bot username**: The username of your Telegram bot (e.g., `authentik_bot`).
        - **Bot token**: The token of your Telegram bot.
        - **Request access to send messages from your bot**: enable this to allow your bot to send messages to authentik users utilizing the Telegram source for authentication.

3. Click **Save**.

:::note
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

## Telegram source property mappings

[Property mappings](../../property-mappings/index.md) can be used to map Telegram user properties to authentik user properties.

### Expression data

Telegram user data is accessible to Telegram source property mappings as a dictionary named `info`.
The dictionary contains the following fields:

- `id` - Telegram user ID
- `username` - Username of the user. Might not be present.
- `first_name` - First name of the user. Might not be present.
- `last_name` - Last name of the user. Might not be present.
- `photo_url` - URL of the user's profile photo. Might not be present.

## Resources

- [Telegram Documentation - BotFather](https://core.telegram.org/bots/features#botfather)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/social-logins/twitch/index.md
================================================================================

---
title: Twitch
tags:
    - source
    - twitch
---

Allows users to authenticate using their Twitch credentials by configuring Twitch as a federated identity provider via OAuth2.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

## Twitch configuration

To integrate Twitch with authentik you will need to create an OAuth application in the Twitch Developers Console.

1. Log in to the [Twitch Developers Console](https://dev.twitch.tv/console).
2. Next to **Applications** click **Register Your Application** and set the following fields:
    - **Name**: `authentik`
    - **OAuth Redirect URLs**: `https://authentik.company/source/oauth/callback/twitch`
    - **Category**: select a category for your application

3. Click **Create** to finish the registration of your application.
4. Next to your newly created application, click **Manage**.
5. Generate a secret by clicking **New Secret**.
6. Take note of the **Client ID** and **Client Secret**. This value will be required in the next section.
7. Click **Save**.

## authentik configuration

To support the integration of Twitch with authentik, you need to create an Twitch OAuth source in authentik.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **Twitch OAuth Source** as the source type.
    - **Create OAuth Source**: provide a name, a slug which must match the slug used in the Twitch `OAuth Redirect URLs` field (e.g. `twitch`), and set the following required configurations:
        - **Protocol settings**
            - **Consumer Key**: `<client_ID>`
            - **Consumer Secret**: `<client_secret>`
            - **Scopes** _(optional)_: define any further access scopes.
3. Click **Finish** to save your settings.

:::info
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source/).
:::

## Source property mappings

Source property mappings allow you to modify or gather extra information from sources. See the [overview](../../property-mappings/index.md) for more information.

## Resources

- [Twitch Developer Documentation](https://dev.twitch.tv/docs)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/social-logins/google/cloud/index.md
================================================================================

---
title: Google Cloud (with OAuth)
sidebar_label: Google Cloud (OAuth)
tags:
    - source
    - google
    - google cloud
    - oauth
---

Allows users to authenticate using their Google credentials by configuring Google Cloud as a federated identity provider via OAuth 2.0.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

## Google configuration

To integrate Google with authentik, you need to create a new project and OAuth credentials in the Google Developer Console.

1. Log in to the [Google Developer Console](https://console.developers.google.com/).
2. Click on **GLogin** in the top left and then **New Project**.

![](./googledeveloper1.png)

3. Set the following values:
    - **Project Name**: Provide a name
    - **Organization**: Leave as default if unsure
    - **Location**: Leave as default if unsure

4. Click **Create**.
5. Select your project from the drop-down at the top.
6. Click the **Credentials** menu icon on the left which looks like a key.

![](./googledeveloper2.png)

7. On the right side, click on **Configure Consent Screen**.

![](./googledeveloper3.png)

8. Set the following required fields:
    - **User Type**: If you do not have a Google Workspace account, choose _External_. If you do have a Google Workspace account and want to limit access to users inside your organization, choose _Internal_.
    - **App Name**: `authentik`
    - **User Support Email**: Must have a value
    - **Authorized Domains**: authentik.company
    - **Developer Contact Info**: Must have a value
9. Click **Save and Continue**.
10. If you have special scopes configured for Google, enter them on this screen. If not, click **Save and Continue**.
11. If you want to create test users, enter them here. If not, click **Save and Continue**.
12. From the **Summary** page, click the **Credentials** menu icon on the left (the icon looks like a key).
13. Click **Create Credentials** on the top of the screen and select **OAuth Client ID**.
14. Set the following required fields:
    - **Application Type**: `Web Application`
    - **Name**: Provide a name
    - **Authorized redirect URIs**: `https://authentik.company/source/oauth/callback/google/`

![](./googledeveloper4.png)

15. Click **Create**.
16. Take note of the **Client ID** and **Client Secret**. These values will be required in the next section.

## authentik configuration

To support the integration of Google with authentik, you need to create a Google OAuth source in authentik.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **Google OAuth Source** as the source type.
    - **Create Google OAuth Source**: provide a name, a slug that must match the slug used in the Google `Authorized redirect URI` field (e.g. `google`), and set the following required configurations:
        - **Protocol settings**
            - **Consumer Key**: `<client_ID>`
            - **Consumer Secret**: `<client_secret>`
            - **Scopes** _(optional)_: define any additional access scopes.
3. Click **Finish** to save your settings.

:::info Display new source on login screen
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source/).
:::

## Optional additional configuration

### Username mapping

Google does not support usernames as a distinct field, so authentik prompts the user for a username when they first enroll through a Google source. To change this behavior and automatically use the email address as the username, create an expression policy to set the username to the email address and bind it to the enrollment flow.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies**.
3. Click **Create**, select **Expression Policy** and then **Next**.
4. Provide a name for the policy and set the following expression:

```python
email = request.context["prompt_data"]["email"]
# Direct set username to email

request.context["prompt_data"]["username"] = email
# Set username to email without domain
# request.context["prompt_data"]["username"] = email.split("@")[0]
return False
```

5. Click **Finish**. You can now bind this policy to the chosen enrollment flow of the Google OAuth source.
6. Navigate to **Flows and Stages** > **Flows** and click the name of the flow in question.
7. Open the **Stage Bindings** tab, expand the policies bound to the first stage and click **Bind existing Policy/Group/User**.
8. Select the policy that you previously created and click **Create**.

:::note
If using the default enrollment flow the policy should be bound to the **default-source-enrollment-prompt** stage. Ensure that the policy comes before **default-source-enrollment-if-username**.
:::

Afterward, any new logins will automatically use the user's Google email address as their username. This can be combined with disallowing users from changing their usernames; see [Configuration](../../../../../sys-mgmt/settings.md#allow-users-to-change-username).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/social-logins/google/workspace/index.md
================================================================================

---
title: Google Workspace (with SAML)
sidebar_label: Google Workspace (SAML)
tags:
    - source
    - google
    - google workspace
    - saml
---

Allows users to authenticate using their Google Workspace credentials by configuring Google Workspace as a federated identity provider via SAML.

## What is Google Workspace?

Google Workspace (formerly G Suite) is a collection of cloud-computing, productivity, and collaboration tools, software, and products developed and marketed by Google.

Organizations using Google Workspace allow their users to authenticate to applications using their company email addresses. This guide shows how to set up Security Assertion Markup Language (SAML) as the authentication method between Google Workspace and authentik.

## SAML Authentication Flow

This sequence diagram shows a high-level flow between user, authentik, Google Workspace, and the target application.

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant authentik
    participant Google
    participant App

    User->>App: User navigates to app...
    App-->>authentik: ← Redirected to authentik
    Note over authentik: User chooses "Google Workspace"
    authentik-->>Google: Redirect to Google →
    Note over Google: Authenticate with email and password
    Google-->>authentik: ← Redirect to authentik
    authentik-->>App: Redirect to app →
```

In short, the user navigates to the application, is redirected to authentik, chooses Google Workspace as the authentication method, authenticates with Google, and is redirected back to the application.

The key characteristic of this IdP-to-IdP flow is that authentik acts as an intermediary identity provider, brokering trust between your application and Google Workspace.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `google-slug` is the slug you will assign to the SAML source in authentik (e.g., `google`).

## Google Workspace configuration

### Create a SAML application

1. Log in to the [Google Workspace Admin Console](https://admin.google.com/) as a super-admin.
2. Navigate to **Apps** > **Web and mobile apps**.
3. Expand the **Add app** dropdown and select **Add custom SAML app**.
4. Configure the following settings:
    - Set **Name** to `authentik`.
    - Set **Description** to `Single Sign-On for authentik`.
5. Click **Continue**.
6. Under **Option 2**, click **Download Certificate** to download the signing certificate.
7. Take note of the **SSO URL**. This will be required when configuring authentik.

:::info Entity ID
authentik is acting as both a Service Provider (SP) to Google and an Identity Provider (IdP) to your applications. Since we only need the SP configuration, you can ignore the Entity ID provided by Google.
:::

8. Click **Continue** to proceed to the Service Provider configuration.

### Configure Service Provider details

1. Configure the following settings:
    - Set **ACS URL** to `https://authentik.company/source/saml/<google-slug>/acs/`.
    - Set **Entity ID** to `https://authentik.company/source/saml/<google-slug>/metadata/`.
    - Set **Start URL** to `https://authentik.company`.
    - Set **Name ID format** to `EMAIL`.
    - Set **Name ID** to `Basic Information > Primary Email`.
2. Click **Continue**.

### Configure attribute mapping

1. Click **Add Mapping** and configure the following settings:
    - Set **Google Directory attribute** to `Basic Information > Primary Email`.
    - Set **App attribute** to `email`.
2. Click **Finish**.

### Enable the application

1. Navigate to **Apps** > **Web and mobile apps** and click the SAML app you created.
2. Click **User access**.
3. Turn the application **ON** for everyone or for specific organizational units.
4. Click **Save**.

## authentik configuration

### Upload the Google Workspace certificate to authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **System** > **Certificates** and click **Import**.
3. Give it a name like `Google Workspace Signing Certificate`.
4. Paste the Google Workspace certificate you exported earlier into the **Certificate** field.
5. Click **Create**.

### Create a SAML source in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login** and click **Create**.
3. Select **SAML Source** and configure the following settings:
    - Set **Name** to `Google Workspace`.
    - Set **Slug** to `google` (must match the slug used in Google Workspace ACS URL).
    - Set **SSO URL** to the SSO URL from Google Workspace.
    - Set **Issuer** to `https://authentik.company/source/saml/<google-slug>/metadata/`.
    - Set **Verification Certificate** to the Google Workspace certificate you uploaded earlier.
      :::warning Disable Verify Assertion Signature
      If you do not disable the following option, your integration with Google Workspace will not work.
      :::
    - Disable **Verify Assertion Signature**.
    - Enable **Verify Response Signature**.
    - Enable **Allow IdP-initiated Login**.
    - Set **NameID Policy** to `Email address`.
4. Click **Finish**.

:::info Display new source on login screen
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source).
:::

## Troubleshooting

- **`403 app_not_configured_for_user`**: Ensure the Entity ID matches between Google Workspace and authentik. The Entity ID must be identical in both configurations.
- **`403 app_not_enabled_for_user`**: Enable the application for your organization in the Google Workspace Admin Console under **Apps** > **Web and mobile apps**.

## Resources

- [Google Workspace Admin Help — Set up your own custom SAML app](https://support.google.com/a/answer/6087519)
- [Google Workspace Admin Help — SAML app error messages](https://support.google.com/a/answer/6301076)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/social-logins/entra-id/scim/index.mdx
================================================================================

---
title: Entra ID SCIM user and group provisioning
sidebar_label: Entra ID SCIM
description: Provisioning users and groups from Entra ID to authentik via the SCIM protocol
toc_max_heading_level: 4
tags:
    - source
    - entra
    - azure
    - scim
---

This guide explains how to provision users and groups from Entra ID to authentik by configuring Entra ID as a SCIM source.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

## authentik configuration

To integrate authentik with Entra ID via SCIM, you need to create a SCIM source in authentik.

### Create SCIM source

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **SCIM Source**.
    - **Create SCIM Source**: provide a name and a slug.
    - All other configurations are optional.
3. Click **Finish**.
4. On the **Federation and Social login** page, click on the name of the newly created SCIM source.
5. Take note of the **SCIM Base URL**. This value will be required in the next section.
6. Under **Token**, click **Click to copy token** and securely store the value. This value will also be required in the next section.

:::warning Copying the token
If authentik has the required browser permissions, the token will be copied to your clipboard after you click the **Click to copy token** button. However, some browsers do not allow this. In those cases, a notification will appear in the bottom-right corner with the token, and you will need to copy it manually.
:::

:::warning Entra ID SCIM requirements
Microsoft requires that the authentik SCIM endpoint be accessible via TLS 1.2. If enforcing TLS 1.3, you may run into issues. For more information, refer to the [Microsoft SCIM endpoint documentation](https://learn.microsoft.com/en-us/entra/identity/app-provisioning/use-scim-to-provision-users-and-groups#security-requirements).

You can use the [Microsoft SCIM Validator](https://scimvalidator.microsoft.com/) to test your authentik SCIM endpoint.
:::

## Entra ID configuration

### Create a custom enterprise application

1. Log in to [Entra ID](https://entra.microsoft.com) using a [global administrator](https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference#global-administrator) account.
2. Navigate to **Enterprise apps**, click **Create your own application**, and configure the following fields:
    - **Name**: provide a name for the application (e.g. `authentik-scim`).
    - Select `Integrate any other application you don't find in the gallery (Non-gallery)`.
3. Click **Create**.

### Configure provisioning

4. Navigate to **Provisioning**, click **New Configuration**, and configure the following fields:
    - **Tenant URL**: Set to the **SCIM Base URL** from authentik (e.g. `https://authentik.company/source/scim/entra-scim/v2`).
    - **Secret Token**: Set to the **Token** from authentik.
5. Click **Test connection** to validate that Entra ID can communicate with authentik.
6. If the connection is successful, click **Create** and **Save**. If the connection fails, ensure that your authentik **SCIM Base URL** is accessible from the internet.
7. In the left sidebar, under **Manage**, click **Provisioning**.

There are three options for determining which users and groups are provisioned to authentik:

- Set Entra ID to sync all users and groups.
- Set Entra ID to sync all users and groups with scopes that limit which users and groups are synced.
- Set Entra ID to sync only assigned users and groups. Group assignment is only available to Microsoft Entra Suite, Microsoft Entra ID Governance, and Microsoft Entra ID P2 customers.

#### Sync all users and groups

1. On the **Provisioning** page, expand the **Settings** section, and set **Scope** to `Sync all users and groups`.
2. Toggle **Provisioning status** to `On`.
3. At the top of the page, click **Save**.
4. Track provisioning progress via the **Overview** page.

#### Sync all users and groups with scopes

1. On the **Provisioning** page, expand the **Settings** section, and set **Scope** to `Sync all users and groups`.
2. At the top of the page, click **Save**.
3. Expand the **Mappings** section and then click **Provision Microsoft Entra ID Users**.
4. Under **Source Object Scope**, click **All records**.
5. Click **Add new filter group**, design the filters that you want applied to synced users and click **Apply**.
6. Optionally, configure **Target object actions** and modify the **Attribute Mappings**.
7. At the top of the page, click **Save**.
8. On the **Provisioning** page, expand the **Mappings** section and then click **Provision Microsoft Entra ID Groups** and repeat steps 4-7.
9. Back on the **Provisioning** page, toggle **Provisioning status** to `On`.
10. At the top of the page, click **Save**.
11. Track provisioning progress via the **Overview** page.

#### Sync only assigned users and groups

1. On the **Provisioning** page, expand the **Settings** section, and set **Scope** to `Sync only assigned users and groups`.
2. At the top of the page, click **Save**.
3. Under **Manage**, click **Users and groups** and then click **Add user/group**.
4. Select the users and groups that you want synced to authentik.
5. Click **Assign**.
6. On the **Provisioning** page, toggle **Provisioning status** to `On`.
7. At the top of the page, click **Save**.
8. Track provisioning progress via the **Overview** page.

:::note Group assignment
Group assignment is only available for Microsoft Entra Suite, Microsoft Entra ID Governance and Microsoft Entra ID P2 subscribers.
:::

## Confirm provisioning in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login** and click on the name of the SCIM source.
3. Open the **Provisioned Users** and **Provisioned Groups** tabs to confirm whether the correct users and groups have been provisioned from Entra ID.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/protocols/scim/index.md
================================================================================

---
title: SCIM Source
---

The SCIM source allows other applications to directly create users and groups within authentik. SCIM provides a predefined schema for users and groups, along with a RESTful API, to enable automatic user provisioning and deprovisioning. SCIM is supported by applications such as Microsoft Entra ID, Google Workspace, and Okta.

The base SCIM URL is in the format of `https://authentik.company/source/scim/<source-slug>/v2`. Authentication is done via Bearer tokens that are generated by authentik. When an SCIM source is created, a service account is created and a matching token is provided.

## First steps

To set up an SCIM source, log in to authentik as an administrator. Navigate to **Directory->Federation & Social login**, and click on **Create**. Select the **SCIM Source** type, and give the source a name.

After the source is created, click on the name of the source in the list, and you will see the **SCIM Base URL** which is used by the SCIM client. Use the **Click to copy token** button to copy the token which is used by the client to authenticate SCIM requests.

## Supported Options & Resource types

### `/v2/Users`

Endpoint to list, create, update and delete users.

### `/v2/Groups`

Endpoint to list, create, update and delete groups.

There are also `/v2/ServiceProviderConfig` and `/v2/ResourceTypes`, which are used by SCIM-enabled applications to find out which features authentik supports.

## SCIM source property mappings

See the [overview](../../property-mappings/index.md) for information on how property mappings work.

### Expression data

Each top-level SCIM attribute is available as a variable in the expression. For example, given a SCIM request with the payload of



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/protocols/kerberos/browser.md
================================================================================

---
title: Browser configuration for SPNEGO
---

You might need to configure your web browser to allow SPNEGO. Following are the instructions for major browsers.

## Firefox

1.  In the address bar of Firefox, type `about:config` to display the list of current configuration options.
2.  In the **Filter** field, type `negotiate` to restrict the list of options.
3.  Double-click the `network.negotiate-auth.trusted-uris` entry to display the **Enter string value** dialog box.
4.  Enter the name of the domain against which you want to authenticate. For example, `.example.com`.

On Windows environments, to automate the deployment of this configuration use a [Group policy](https://support.mozilla.org/en-US/kb/customizing-firefox-using-group-policy-windows). On Linux or macOS systems, use [policies.json](https://support.mozilla.org/en-US/kb/customizing-firefox-using-policiesjson).

## Chrome

This section applies only for Chrome users on macOS and Linux machines. For Windows, see the instructions below.

1. Make sure you have the necessary directory created by running: `mkdir -p /etc/opt/chrome/policies/managed/`
2. Create a new `/etc/opt/chrome/policies/managed/mydomain.json` file with write privileges limited to the system administrator or root, and include the following line: `{ "AuthServerWhitelist": "*.example.com" }`.

**Note**: if using Chromium, use `/etc/chromium/policies/managed/` instead of `/etc/opt/chrome/policies/managed/`.

To automate the deployment of this configuration use a [Group policy](https://support.google.com/chrome/a/answer/187202).

## Windows / Internet Explorer

Log in to the Windows machine using an account of your Kerberos realm (or administrative domain).

Open Internet Explorer, click **Tools** and then click **Internet Options**. You can also find **Internet Options** using the system search.

1. Click the **Security** tab.
2. Click **Local intranet**.
3. Click **Sites**.
4. Click **Advanced**.
5. Add your domain to the list.
6. Click the **Security tab**.
7. Click **Local intranet**.
8. Click **Custom Level**.
9. Select **Automatic login only in Intranet zone**.

To automate the deployment of this configuration use a [Group policy](https://learn.microsoft.com/en-us/previous-versions/troubleshoot/browsers/administration/how-to-configure-group-policy-preference-settings).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/users-sources/sources/protocols/kerberos/index.md
================================================================================

---
title: Kerberos
authentik_preview: true
authentik_version: "2024.10"
---

This source allows users to enroll themselves with an existing Kerberos identity.

## Preparation

The following placeholders are used in this guide:

- `REALM.COMPANY` is the Kerberos realm.
- `authentik.company` is the FQDN of the authentik install.

Examples are shown for an MIT Krb5 KDC system; you might need to adapt them for your Kerberos installation.

There are three ways to use the Kerberos source:

- As a password backend, where users can log in to authentik with their Kerberos password.
- As a directory source, where users are synced from the KDC.
- With SPNEGO, where users can log in to authentik with their [browser](./browser.md) and their Kerberos credentials.

You can choose to use one or more of those methods.

## Common settings

In the authentik Admin interface, under **Directory** > **Federation and Social login**, create a new source of type Kerberos with these settings:

- Name: a value of your choosing. This name is shown to users if you use the SPNEGO login method.
- Slug: `kerberos`
- Realm: `REALM.COMPANY`
- Kerberos 5 configuration: If you need to override the default Kerberos configuration, you can do it here. See [man krb5.conf(5)](https://web.mit.edu/kerberos/krb5-latest/doc/admin/conf_files/krb5_conf.html) for the expected format.
- User matching mode: define how Kerberos users get matched to authentik users.
- Group matching mode: define how Kerberos groups (specified via property mappings) get matched to authentik groups.
- User property mappings and group property mappings: see [Source property mappings](../../property-mappings/index.md) and the section below for details.

## Password backend

No extra configuration is required. Simply select the Kerberos backend in the password stage of your flow.

Note that this only works on users that have been linked to this source, i.e. they must have been created via sync or via SPNEGO.

## Sync

The sync process uses the [Kerberos V5 administration system](https://web.mit.edu/kerberos/krb5-latest/doc/admin/database.html) to list users. Your KDC must support it to sync users with this source.

You need to create both a principal (a unique identity that represents a user or service in a Kerberos network) for authentik and a keytab file:

```bash
$ kadmin
> add_principal authentik/admin@REALM.COMPANY
> ktadd -k /tmp/authentik.keytab authentik/admin@REALM.COMPANY
> exit
$ cat /tmp/authentik.keytab | base64
$ rm /tmp/authentik.keytab
```

In authentik, configure these extra options:

- Sync users: enable it
- Sync principal: `authentik/admin@REALM.COMPANY`
- Sync keytab: the base64-encoded keytab created above.

If you do not wish to use a keytab, you can also configure authentik to authenticate using a password or an existing credentials cache.

## SPNEGO

You need to create both a principal (a unique identity that represents a user or service in a Kerberos network) for authentik and a keytab file:

```bash
$ kadmin
> add_principal HTTP/authentik.company@REALM.COMPANY
> ktadd -k /tmp/authentik.keytab HTTP/authentik.company@REALM.COMPANY
> exit
$ cat /tmp/authentik.keytab | base64
$ rm /tmp/authentik.keytab
```

In authentik, configure these extra options:

- SPNEGO keytab: the base64-encoded keytab created above.

If you do not wish to use a keytab, you can also configure authentik to use an existing credentials cache.

You can also override the SPNEGO server name if needed.

You might need to configure your web browser to allow SPNEGO. Check out [our documentation](./browser.md) on how to do so. You can now log in to authentik using SPNEGO.

### Custom server name

If your authentik instance is accessed from multiple domains, you might want to force the use of a specific server name. You can do so with the **Custom server name** option. The value must be in the form of `HTTP@authentik.company`.

If not specified, the server name defaults to trying out all entries in the keytab/credentials cache until a valid server name is found.

## Extra settings

There are some extra settings you can configure:

- Update internal password on login: when a user logs in to authentik using the Kerberos source as a password backend, their internal authentik password will be updated to match the one from Kerberos.
- Use password writeback: when a user changes their password in authentik, their Kerberos password is automatically updated to match the one from authentik. This is only available if synchronization is configured.

## Kerberos source property mappings

See the [overview](../../property-mappings/index.md) for information on how property mappings work with external sources.

By default, authentik ships with [pre-configured mappings](#built-in-property-mappings) for the most common Kerberos setups. These mappings can be found on the Kerberos Source Configuration page in the Admin interface.

### Built-in property mappings

Kerberos property mappings are used when you define a Kerberos source. These mappings define which Kerberos property maps to which authentik property. By default, the following mappings are created:

- authentik default Kerberos User Mapping: Add realm as group
  The realm of the user will be added as a group for that user.
- authentik default Kerberos User Mapping: Ignore other realms
  Realms other than the one configured on the source are ignored, and logging in is not allowed.
- authentik default Kerberos User Mapping: Ignore system principals
  System principals such as `K/M` or `kadmin/admin` are ignored.
- authentik default Kerberos User Mapping: Multipart principals as service accounts
  Multipart principals (for example: `HTTP/authentik.company`) have their user type set to **service account**.

These property mappings are configured with the most common Kerberos setups.

### Expression data

The following variable is available to Kerberos source property mappings:

- `principal`: a Python string containing the Kerberos principal. For example `alice@REALM.COMPANY` or `HTTP/authentik.company@REALM.COMPANY`.

When the property mapping is invoked from a SPNEGO context, the following variable is also available:

- `spnego_info`: a Python dictionary with the following keys:
    - `initiator_name`: the name of the initiator of the GSSAPI security context
    - `target_name`: the name of the target of the GSSAPI security context
    - `mech`: the GSSAPI mechanism used. Should always be Kerberos
    - `actual_flags`: the flags set on the GSSAPI security context

When the property mapping is invoked from a synchronization context, the following variable is also available:

- `principal_obj`: a [`Principal`](https://kadmin-rs.readthedocs.io/latest/kadmin.html#kadmin.Principal) object retrieved from the KAdmin API

### Additional expression semantics

If you need to skip synchronization for a specific object, you can raise the `SkipObject` exception. To do so, create or modify a Kerberos property mapping to use an expression to define the object to skip.

**Example:**

```python
localpart, realm = principal.rsplit("@", 1)
if localpart == "username":
    raise SkipObject
```

## Troubleshooting

You can start authentik with the `KRB5_TRACE=/dev/stderr` environment variable for Kerberos to print errors in the logs.

Reverse proxy caching can break the Kerberos authentication flow because, during negotiation, the server sends a second `401 Unauthorized` response containing the `WWW-Authenticate` header that the client needs to continue the handshake; if the reverse proxy caches that `401` instead of forwarding it to authentik, the authentication process fails, so response caching should be disabled on any reverse proxy routes involved in Kerberos authentication.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/security-hardening.md
================================================================================

---
title: Hardening authentik
---

While authentik is secure out of the box, you can take steps to further increase the security of an authentik instance. As everyone knows, there is a consequential tradeoff between security and convenience. All of these hardening practices have an impact on the user experience and should only be applied knowing this tradeoff.

### Password policy

authentik's default Password policy complies with the [NIST SP 800-63 Digital Identity Guidelines](https://pages.nist.gov/800-63-4/sp800-63b.html#password).

However, for further hardening compliant to the NIST Guidelines, consider

- setting the length of the password to a minimum of 15 characters, and
- enabling the "Check haveibeenpwned.com" blocklist comparison (note that this cannot be used on Air-gapped instances)

For further options, see [Password policy](../customize/policies/index.md#password-policy).

### Expressions

[Expressions](../customize/policies/expression.mdx) allow super-users and other highly privileged users to create custom logic within authentik to modify its behaviour. Editing/creating these expressions is, by default, limited to super-users and any related events are fully logged.

However, for further hardening, it is possible to prevent any user (even super-users) from using expressions to create or edit any objects. To do so, configure your deployment to block API requests to these endpoints:

- `/api/v3/policies/expression*`
- `/api/v3/propertymappings*`
- `/api/v3/managed/blueprints*`

With these restrictions in place, expressions can only be edited using [Blueprints on the file system](../customize/blueprints/index.mdx#as-a-local-file). Take care to restrict access to the file system itself.

### Blueprints

Blueprints allow for templating and managing the authentik configuration as code. Just like expressions, they can only be created/edited by super-users or users with specific permissions assigned to them. However, because they interact with the authentik API on a lower level, they can create other objects.

To prevent any user from creating/editing blueprints, block API requests to this endpoint:

- `/api/v3/managed/blueprints*`

With these restrictions in place, Blueprints can only be edited via [the file system](../customize/blueprints/index.mdx#as-a-local-file).

### CAPTCHA Stage

The CAPTCHA stage allows for additional verification of a user while authenticating or authorizing an application. Because the CAPTCHA stage supports multiple different CAPTCHA providers, such as Google’s reCAPTCHA and Cloudflare’s Turnstile, the URL for the JavaScript snippet can be modified. Depending on the threat model, this could be exploited by a malicious internal actor.

To prevent any user from creating/editing CAPTCHA stages block API requests to these endpoints:

- `/api/v3/stages/captcha*`
- `/api/v3/managed/blueprints*`

With these restrictions in place, CAPTCHA stages can only be edited using [Blueprints on the file system](../customize/blueprints/index.mdx#as-a-local-file).

### Content Security Policy (CSP)

:::caution
Setting up CSP incorrectly might result in the client not loading necessary third-party code.
:::

:::caution
In some cases, a CSP header will already be set by authentik (for example, in [user uploaded content](https://github.com/goauthentik/authentik/pull/12092/)). Do not overwrite an already existing header as doing so might result in vulnerabilities. Instead, add a new CSP header.
:::

Content Security Policy (CSP) is a security standard that mitigates the risk of content injection vulnerabilities. authentik doesn't currently support CSP natively, so setting it up depends on your installation. We recommend using a [reverse proxy](../install-config/reverse-proxy.md) to set a CSP header.

authentik requires at least the following allowed locations:

```
default-src 'self';
img-src https: data:;
object-src 'none';
style-src 'self' 'unsafe-inline';    # Required due to Lit/ShadowDOM
script-src 'self' 'unsafe-inline';   # Required for generated scripts
```

Your use case might require more allowed locations for various directives, for example:

- when using a CAPTCHA service
- when using Sentry
- when using any custom JavaScript in a prompt stage
- when using Spotlight Sidecar for development
- when using images hosted via HTTP



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/audits-and-certs/2025-09-includesec.md
================================================================================

# 2025-09 IncludeSec pentest

In September of 2025, we had a pentest conducted by [Include Security](https://includesecurity.com). This resulted in a number of code improvements to our application, however did not result in any assigned CVEs.

> IncludeSec performed a security assessment of Authentik Security's Web Apps, APIs, Deployment Config, Servers, & ETL. The assessment team performed a 8 day effort spanning from September 4 through September 15, 2025, using a Standard Grey Box assessment methodology.

View the full report of our original [test](https://goauthentik.io/resources/includesec-Q3-2025-Multi-Report.pdf) and the [retest results](https://goauthentik.io/resources/includesec-Q3-2025-Multi-Remediation-Report.pdf), completed in January/February 2026.

## Summary of findings

Below is a table summarizing the findings from the report, along with IncludeSec's risk labeling and our contextual categorization of these risks. As IncludeSec states, "It is common and encouraged that all clients recategorize findings based on their internal business risk tolerances."

| Finding | IncludeSec Risk | Status           | authentik Risk Categorization |
| ------- | --------------- | ---------------- | ----------------------------- |
| H1      | High            | Risk Accepted    | Expected behavior             |
| H2      | High            | Closed           | Low                           |
| H3      | High            | Risk Accepted    | Expected behavior             |
| M1      | Medium          | Fixed in 2025.12 | Low                           |
| M2      | Medium          | Closed           | Low                           |
| L1      | Low             | Closed           | Low                           |
| L2      | Low             | Closed           | Low                           |
| L3      | Low             | Closed           | None (not exploitable)        |
| L4      | Low             | Closed           | Low                           |

During the time of this test, we also separately addressed a number of community-reported CVEs as reported in our security pages.

## Responses to specific findings

This is the complete list of findings from the audit, with information about how we addressed each.

### H1: Blueprint Import Allows Arbitrary Modification of Application Objects (Internal: None)

_Issue:_ This is intended functionality. This behavior reflects the privileged design of blueprint imports. It is 'exploitable' when importing blueprints from untrusted sources without reviewing the blueprint beforehand. Flow imports are technically blueprint imports, which by design can be used to create any object within authentik.

_Improvement:_ We added a [warning banner](https://github.com/goauthentik/authentik/pull/19288) with 2025.12 to flow imports.

### H2: TOTP Brute-Force Vulnerability (Internal: Low) - Closed

_Issue:_ TOTP could in theory be brute-forced for login given knowledge of a target user's password, enough time, and no WAF/altering on high amounts of requests.

_Improvement:_ We added stricter rate limiting to the infrastructure used for testing.

In addition to using authentik's built-in methods to reduce the ability for attackers to brute-force credentials, we also recommend that customers use a WAF.

### H3: Arbitrary Python Code execution (Internal: None)

_Issue:_ The authentik application allowed execution of arbitrary Python code with the same privileges as the application's system user. This behavior extended to prompt stages.

_Response:_ By design, prompt inputs can be configured to have placeholder values based on Python expressions, inheriting the behavior from expression policies. Our [hardening docs](https://docs.goauthentik.io/security/security-hardening/) already cover this topic.

### M1: Anti-Brute Force Mechanisms Bypassed via Race conditions

_Issue:_ The anti-brute force mechanism could be bypassed by triggering a race condition using the `default-authentication-flow`, given enough time and no WAF/other filtering in place.

_Improvement:_ In 2025.12, we [replaced](https://github.com/goauthentik/authentik/pull/18643) session-based login attempt retries to rely instead on the reputation scores.

Once again, in addition to using authentik's built-in methods to reduce the ability for attackers to brute-force credentials, we recommend that customers use a WAF.

### M2: Password Hashes Disclosed via Application Launch URL (Internal: Low) - Closed

_Issue:_ authentik disclosed salted user password hashes to a privileged user when accessing a specially crafted launch URL for a custom Application.

_Fix:_ We [improved](https://github.com/goauthentik/authentik/pull/18076) the Application launch URL format.

### L1: FROM Tags in Dockerfiles Enable Supply-Chain Takeover (Internal: Low) - Closed

_Issue:_ Our container build process used Dockerfiles containing unpinned tags, allowing a possible supply chain attack from an attacker with control of the referenced repository who could repoint the tag to a different image.

_Fix:_ We [updated](https://github.com/goauthentik/authentik/pull/17795) to use image digests for Dockerfile `FROM` calls.

### L2: User Accounts Enumerable

_Issue:_ In the small test environment, the application's response time varied based on whether the supplied account was associated with a valid user, allowing potential account enumeration.

In real-world production environments with typical network latency and reverse proxies, the timing variance would likely be obscured.

_Improvement:_ We [replaced](https://github.com/goauthentik/authentik/pull/18883) a randomized call to `sleep` with `make_password`, which better emulates checking the password of a user.

### L3: [Server] Shell Command Execution Did Not Use Absolute Path (Internal: Low) - Closed

_Issue:_ authentik called OpenSSL based on its binary name without specifying an absolute path, which could lead to path hijacking.

_Fix:_ We [updated](https://github.com/goauthentik/authentik/pull/17856) the OpenSSL call to use the absolute binary path.

### L4: [Server] [Proxy] Potential Slowloris DoS (Internal: Low) - Closed

_Issue:_ The test infrastructure's HTTP server had been instantiated without setting ReadHeaderTimeout, ReadTimeout, WriteTimeout, IdleTimeout, or limiting header sizes, leaving it susceptible to Slowloris-style denial of service attacks.

_Fix:_ We [added](https://github.com/goauthentik/authentik/pull/17858) default HTTP server timeouts. We recommend that admins use a load-balancer/reverse proxy in front of authentik in production, which would have different timeout settings.

### I1: [Server] [RADIUS] RADIUS Message-Authenticator Validation

_Issue:_ RADIUS Message-Authenticator validation logic appeared to be inverted, causing valid packets to be rejected and weakening the integrity check.

RADIUS Message-Authenticator validation is the process of verifying the integrity and authenticity of a RADIUS packet using the Message-Authenticator attribute.

Although the issue is currently theoretical, correctly authenticated RADIUS messages may be rejected, causing authentication failures and a potential denial-of-service.

_Improvement:_ This was initially [fixed](https://github.com/goauthentik/authentik/pull/17855) but later reverted; we're testing our RADIUS implementation with different clients to resolve the underlying bug that required the fix to be reverted.

## Conclusion

We encourage an open and ongoing communication with our users and community. For more information abut our security stance, read our [Security Policy](https://docs.goauthentik.io/security/policy), [Hardening authentik](https://docs.goauthentik.io/security/security-hardening/), and our other security-related documentation. If you have any questions or feedback you can reach us on [GitHub](https://github.com/goauthentik/authentik/), [Discord](https://discord.com/invite/jg33eMhnj6), or via [email](mailto:hello@goauthentik.io). Please follow our [security policy](https://docs.goauthentik.io/security/policy/#reporting-a-vulnerability) for reporting any security concerns or vulnerabilities.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/audits-and-certs/2024-11-cobalt.md
================================================================================

# 2024-11 Cobalt pentest

We are committed to engaging in regular pentesting and security audits of authentik. Defining and adhering to a cadence of external testing ensures a stronger probability that our code base, our features, and our architecture is as secure and non-exploitable as possible.

In August-September of 2024, we had a pentest conducted by [Cobalt](https://www.cobalt.io). This document covers the findings of the audit, how we addressed the noted issues, and the subsequent [re-testing](https://goauthentik.io/resources/fullReport_authentik-cobalt-test-instance-august-2024-pt26135.pdf) by Cobalt to confirm that all issues were resolved.

Cobalt described their process for testing:

> This pentest was a manual assessment of the security of the application’s functionality, business logic, and vulnerabilities, such as those cataloged in the Open Web Application Security Project OWASP) Top 10. The assessment also included a review of security controls and requirements listed in the OWASP Application Security Verification Standard (ASVS).

## Summary of findings

Overall, we are pleased with the report's findings and grateful for the opportunity to improve in every area we can.

> Cobalt reported "The pentesters found that the Authentik Security team implemented robust and up-to-date security practices throughout the application."

In total, there were 5 low-level and one info-level vulnerabilities reported. By early November 2024, all 6 vulnerabilities were addressed and released in the [2024.10.4 patch release](https://docs.goauthentik.io/docs/releases/2024.10#fixed-in-2024103).

## Responses to specific findings

From the audit, this is the complete list of findings, with information about how we addressed each.

### HTML Injection

**Issue**: A vulnerability existed through user-supplied names in our Flow diagrams, where the application did not properly sanitize or escape HTML input when parsing user-entered names. As a result, an attacker could inject arbitrary HTML or JavaScript code into the application, potentially leading to manipulation of the web page or execution of malicious scripts in the context of the user's session. (This action could only be performed by an authenticated admin user, and thus had little practical value as an attack vector.)

**Fix**: We added strict [DOMpurify](https://github.com/cure53/DOMPurify) configurations for any user-defined names in our diagrams. For details, refer to [Pull Request #11783](https://github.com/goauthentik/authentik/pull/11783).

### SVG images for icons possible XSS vulnerability

**Issue**: The pentesters discovered that the application was susceptible to insecure file upload and stored Cross-Site Scripting (XSS) vulnerabilities by uploading crafted SVG files that were used as application icons. (This action could only be performed by an authenticated admin user, and thus had little practical value as an attack vector.)

**Fix**: The fix was to add a CSP header to files that are stored in the `/media` directory of the installation. For details, refer to [Pull Request #12092](https://github.com/goauthentik/authentik/pull/12092).

### Vulnerability through footer links on website

**Issue**: It was found that the application was vulnerable to stored XSS through footer links. The footer section of the application accepted and displayed user-provided links without proper sanitization. This could allow an attacker to inject malicious scripts into these links, which would then stored and executed when other users access the footer links, leading to potential script execution in the context of the victim's session. (This action could only be performed by an authenticated admin user, and thus had little practical value as an attack vector.)

**Fix**: Again, as with the diagram issue above, we added strict [DOMpurify](https://github.com/cure53/DOMPurify) configurations. For more details, refer to [Pull Request #11773](https://github.com/goauthentik/authentik/pull/11773).

### Password policy weakness

**Issue**: It was determined that the password policy in place on the testing environment was weak, allowing users to create passwords that lacked complexity and were easily guessable. This made the application more susceptible to brute-force and dictionary attacks.

**Fix**: This was not a vulnerability in authentik, but rather a poor configuration of our provided test environment. Rather than simply improve our test instance’s configuration once, to make this issue easier to avoid for all our users and customers, we added a strong default password policy that applies to all new instances. (As always, admins can still configure their own custom policies.) For more details, refer to [Pull Request #11793](https://github.com/goauthentik/authentik/pull/11793).

### Lack of a CSP header

The absence of Content Security Policy (CSP) headers means that the application may lack a mechanism to restrict sources of content and scripts, which can potentially expose it to XSS attacks and other forms of content injection.

**Fix**: We added CSP headers to control the sources of content and scripts that the application can load for our provided test instance. Again, this is not a direct vulnerability in authentik itself. Given the variety of architectures in which authentik is deployed, adding our own CSP headers would be more likely to break functionality than to provide improved security.

### API endpoints strengthened

**Issue**: Finally, the only informational level finding was the potential for the unauthenticated download of private key and certificate values via a direct URL. (Guessing the URL required the knowledge of the UUID of an object.) We had already fixed this issue in 2024.8.0, but the instance tested against was the immediately preceding version.

**Fix**: For more details, refer to [CVE-2024-42490](https://docs.goauthentik.io/docs/security/cves/CVE-2024-42490).

## Retest results

The subsequent retest conducted by Cobalt deemed all issues resolved. See page 17 of the [report](https://goauthentik.io/resources/fullReport_authentik-cobalt-test-instance-august-2024-pt26135.pdf) for the mitigation status ("fixed") for each of the issues discovered in September.

We are pleased to share this pentest and the final results of the retest. We encourage an open and ongoing communication with our users and community. For more information abut our security stance, read our [Security Policy](https://docs.goauthentik.io/docs/security/policy), [Hardening authentik](https://docs.goauthentik.io/docs/security/security-hardening), and our other [security-related documentation](https://docs.goauthentik.io/docs/security). If you have any questions or feedback you can reach us on [GitHub](https://github.com/goauthentik/authentik), [Discord](https://discord.com/channels/809154715984199690/809154716507963434), or via email to [hello@goauthentik.io](mailto:hello@goauthentik.io).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/audits-and-certs/2023-06-cure53.md
================================================================================

# 2023-06 Cure53 Code audit

In May/June of 2023, we had a pentest conducted by [Cure53](https://cure53.de). The following security updates, 2023.4.2 and 2023.5.3 were released as a response to the found issues.

From the [complete report](https://cure53.de/pentest-report_authentik.pdf), these are the points we're addressing with this update:

### ATH-01-001: Path traversal on blueprints allows arbitrary file-read (Medium)

This had accidentally been patched by a previous commit already; and was also only possible for users with superuser permissions.

### ATH-01-003: CSS injection via faulty string replacement in Mermaid (Low)

This is an unrelated issue that was found with a third-party dependency ([Mermaid](https://mermaid.js.org/)), fixed with https://github.com/mermaid-js/mermaid/releases/tag/v10.2.2

Additionally we've also taken steps to further mitigate possible issues that could be caused in this way.

### ATH-01-008: User-passwords disclosed to third-party service (High)

In certain circumstances, using the Enter key to submit some forms instead of clicking submit would cause the frontend to change the URL instead of calling the API, which could lead to sensitive data being disclosed.

### ATH-01-009: Lack of CSRF protection in impersonate feature (Low)

Previous the URL to start an impersonation was a simple GET URL request, which was susceptible to CSRF. This has been changed to an API Post request.

### ATH-01-010: Web authentication bypass via key confusion (High)

When using WebAuthn to authenticate, the owner of the WebAuthn device wasn't checked. However to exploit this, an attacker would need to be able to already intercept HTTP traffic and read the data.

### ATH-01-014: Authentication challenges abused by foreign flow (Medium)

Previously it was possible to use an MFA authenticator class that wasn't allowed in a flow, if another flow existed that allowed this class. The patch changes data to be isolated per flow to prevent this issue.

### ATH-01-004: Information disclosure on system endpoint (Info)

The `/api/v3/admin/system/` (only accessible to superusers) endpoint returns a large amount of system info (mostly used for debugging), like the HTTP headers sent to the server. It also included all environment variables set for authentik. The environment variables have been removed.

### ATH-01-005: Timing-unsafe comparison in API authentication (Info)

In the API authentication that is used by the embedded outpost (API authentication via Secret key), a timing-unsafe comparison was used.

### ATH-01-012: Unintended diagram created due to unescaped quotes (Info)

Related to ATH-01-003, it was possible to insert unintended diagrams into generated diagrams.

## Additional info

In addition to the points above, several of the findings are classified as intended features (such as the expression policies). However, we have published additional [hardening documentation](../security-hardening.md) to provide guidance for further measures that can be taken to limit any possible risks associated with these features.

### ATH-01-002: Stored XSS in help text of prompt module (Medium)

Prompt help texts can use HTML to add markup, which also includes the option to include JavaScript. This is only possible to configure for superusers. To mitigate the risk of a rogue superuser creating a stage with a malicious script, requests to the `/api/v3/stages/captcha*` and `/api/v3/managed/blueprints*` endpoints can be blocked. With these restrictions in place, Captcha stages can only be edited using Blueprints on the file system. It is also recommended to use the RBAC system to restrict which users can edit these objects.

### ATH-01-006: Arbitrary code execution via expressions (Critical)

This is the intended function of expression policies/property mappings, which also requires superuser permissions to edit. To mitigate the risk of a rogue superuser creating a malicious expression, requests to the `/api/v3/policies/expression*`, `/api/v3/propertymappings*`, and ` /api/v3/managed/blueprints*` endpoints can be blocked. With these restrictions in place, expression can only be edited using Blueprints on the file system. It is also recommended to use the RBAC system to restrict which users can edit these objects.

### ATH-01-007: SSRF via blueprints feature for fetching manifests (Medium)

Superusers can fetch blueprints via OCI registries, which could be potentially used for server-side request forgery. To mitigate the risk of a rogue superuser sending malicious requests, requests to the `/api/v3/managed/blueprints*` endpoint can be blocked. With these restrictions in
place, blueprints can only be edited using YAML files on the file system. It is also recommended to use the RBAC system to restrict which users can edit these objects.

### ATH-01-013: XSS via CAPTCHA JavaScript URL (Medium)

Similar to ATH-01-002, any arbitrary JavaScript can be loaded using the Captcha stage. This is also limited to superusers. In order to prevent potential exploitation, it is recommended to limit the setting to allow-listed JavaScript URLs only.

### ATH-01-011: Weak default configs in logout/change password flows (Info)

The default logout flow does not do any additional validation and logs the user out with a single GET request. The default password-change flow does not verify the users current password, nor does it show the current users info.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2024-52287.md
================================================================================

# CVE-2024-52287

_Reported by [@matt1097](https://github.com/matt1097)_

## Insufficient validation of OAuth scopes for client_credentials and device_code grants

### Summary

When using the `client_credentials` or `device_code` OAuth grants, it was possible for an attacker to get a token from authentik with scopes that haven't been configured in authentik.

### Details

With the `device_code` grant, it was possible to have a user authorize a set of permitted scopes, and then acquire a token with a different set of scopes, including scopes not configured. This token could potentially be used to send requests to another system which trusts tokens signed by authentik and execute malicious actions on behalf of the user.

With the `client_credentials` grant, because there is no user authorization process, authentik would not validate the scopes requested for the token, allowing tokens to be issued with scopes not configured in authentik. These could similarly be used to execute malicious actions in other systems.

There is no workaround for this issue; however this issue could only be exploited if an attacker possesses a valid set of OAuth2 `client_id` and `client_secret` credentials, and has the knowledge of another system that trusts tokens issued by authentik and what scopes it checks for.

### Patches

authentik 2024.8.5 and 2024.10.3 fix this issue.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2025-53942.md
================================================================================

# CVE-2025-53942

_Reported by [@pascalwei](https://github.com/pascalwei)_

## Insufficient check for account active status when authenticating with OAuth/SAML Sources

### Summary

Deactivated users that had either enrolled via OAuth/SAML or had their account connected to an OAuth/SAML account can still partially access authentik even if their account is deactivated. They end up in a half-authenticated state where they cannot access the API but crucially they can authorize applications if they know the URL of the application.

### Patches

authentik 2025.4.4 and 2025.6.4 fix this issue.

### Workarounds

Adding an expression policy to the user login stage on the respective authentication flow with the expression of

```py
return request.context["pending_user"].is_active
```

This expression will only activate the user login stage when the user is active.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2024-38371.md
================================================================================

# CVE-2024-38371

_Reported by Stefan Zwanenburg_

## Insufficient access control for OAuth2 Device Code flow

### Impact

Due to a bug, access restrictions assigned to an application were not checked when using the OAuth2 Device code flow. This could potentially allow users without the correct authorization to get OAuth tokens for an application, and access the application.

### Patches

authentik 2024.6.0, 2024.4.3 and 2024.2.4 fix this issue, for other versions the workaround can be used.

### Workarounds

As authentik flows are still used as part of the OAuth2 Device code flow, it is possible to add access control to the configured flows.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2022-46145.md
================================================================================

# CVE-2022-46145

_Reported by [@sdimovv](https://github.com/sdimovv)_

## Unauthorized user creation and potential account takeover

### Impact

With the default flows, unauthenticated users can create new accounts in authentik. If a flow exists that allows for email-verified password recovery, this can be used to overwrite the email address of admin accounts and take over their accounts

### Patches

authentik 2022.11.2 and 2022.10.2 fix this issue, for other versions the workaround can be used.

### Workarounds

A policy can be created and bound to the `default-user-settings-flow` flow with the following contents

```python
return request.user.is_authenticated
```



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2023-39522.md
================================================================================

# CVE-2023-39522

_Reported by [@markrassamni](https://github.com/markrassamni)_

## Username enumeration attack

### Summary

Using a recovery flow with an identification stage an attacker is able to determine if a username exists.

### Patches

authentik 2023.5.6 and 2023.6.2 fix this issue.

### Impact

Only setups configured with a recovery flow are impacted by this.

### Details

An attacker can easily enumerate and check users' existence using the recovery flow, as a clear message is shown when a user doesn't exist. Depending on configuration this can either be done by username, email, or both.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2024-52307.md
================================================================================

# CVE-2024-52307

_Reported by [@mgerstner](https://github.com/mgerstner)_

## Timing attack due to a lack of constant time comparison for metrics view

### Summary

Due to the usage of a non-constant time comparison for the `/-/metrics/` endpoint it was possible to brute-force the `SECRET_KEY`, which is used to authenticate the endpoint. The `/-/metrics/` endpoint returns Prometheus metrics and is not intended to be accessed directly, as the Go proxy running in the authentik server container fetches data from this endpoint and serves it on a separate port (9300 by default), which can be scraped by Prometheus without being exposed publicly.

### Patches

authentik 2024.8.5 and 2024.10.3 fix this issue, for other versions the workaround below can be used.

### Impact

With enough attempts the `SECRET_KEY` of the authentik installation can be brute-forced, which can be used to sign new or modify existing cookies.

### Workarounds

Since the `/-/metrics/` endpoint is not intended to be accessed publicly, requests to the endpoint can be blocked by the reverse proxy/load balancer used in conjunction with authentik.

For example for nginx:

```
location /-/metrics/ {
    deny all;
    return 404;
}
```

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2024-37905.md
================================================================================

# CVE-2024-37905

_Reported by [@m2a2](https://github.com/m2a2)_

## Improper Authorization for Token modification

### Summary

Due to insufficient permission checks it was possible for any authenticated user to elevate their permissions to a superuser by creating an API token and changing the user the token belonged to.

### Patches

authentik 2024.6.0, 2024.4.3 and 2024.2.4 fix this issue, for other versions the workaround can be used.

### Details

By setting a token's user ID to the ID of a higher privileged user, the token will inherit the higher privileged access to the API. This can be used to change the password of the affected user or to modify the authentik configuration in a potentially malicious way.

### Workarounds

As a workaround it is possible to block any requests to `/api/v3/core/tokens*` at the reverse-proxy/load-balancer level. Doing so prevents this issue from being exploited.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2026-25748.md
================================================================================

# CVE-2026-25748

_Reported by [@imlonghao](https://github.com/imlonghao)_

## Forward authentication bypass with malformed session cookie on Traefik and Caddy

### Summary

With a malformed cookie it was possible to bypass authentication when using forward authentication in the authentik **Proxy Provider** when used in conjunction with Traefik or Caddy as reverse proxy. When a malicious cookie was used, none of the authentik-specific `X-Authentik-*` headers were set which depending on application can grant access to an attacker.

### Patches

authentik 2025.10.4 and 2025.12.4 fix this issue.

### Impact

Depending on the behavior of applications (based on if they require an `X-Authentik` header being present) behind the Proxy Provider, attackers are potentially able to gain full access to the application.

### Workarounds

There are no workarounds. If an upgrade is not possible, it is recommended to deactivate the reverse proxy entries for any applications using forward authentication until authentik can be upgraded.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2023-26481.md
================================================================================

# CVE-2023-26481

_Reported by [@fuomag9](https://github.com/fuomag9)_

## Insufficient user check in FlowTokens by Email stage

### Summary

Due to an insufficient access check, a recovery flow link that is created by an admin (or sent via email by an admin) can be used to set the password for any arbitrary user.

### Patches

authentik 2022.12.3, 2023.1.3, 2023.2.3 fix this issue.

### Impact

This attack is only possible if a recovery flow exists, which has both an Identification and an Email stage bound to it. If the flow has policies on the identification stage to skip it when the flow is restored (by checking `request.context['is_restored']`), the flow is not affected by this. With this flow in place, an administrator must create a recovery Link or send a recovery URL to the attacker, who can, due to the improper validation of the token create, set the password for any account.

### Workaround

It is recommended to upgrade to the patched version of authentik. Regardless, for custom recovery flows it is recommended to add a policy that checks if the flow is restored, and skips the identification stage.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2025-52553.md
================================================================================

# CVE-2025-52553

_Reported by [SPIEGEL-Verlag](https://gruppe.spiegel.de)_

## Insufficient Session verification for Remote Access Control endpoint access

### Summary

After authorizing access to a RAC endpoint, authentik creates a token which is used for a single connection and is sent to the client in the URL. This token is intended to only be valid for the session of the user who authorized the connection, however this check is currently missing.

### Patches

authentik 2025.4.3 and 2025.6.3 fix this issue.

### Impact

When for example using RAC during a screenshare, a malicious user could access the same session by copying the URL from the shown browser.

### Workarounds

As a workaround it is recommended to decrease the duration a token is valid for (in the RAC Provider settings, set **Connection expiry** to `minutes=5` for example). We also recommend enabling the option **Delete authorization on disconnect**.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2024-42490.md
================================================================================

# CVE-2024-42490

_Reported by [@m2a2](https://github.com/m2a2)_

## Insufficient Authorization for several API endpoints

### Summary

Several API endpoints can be accessed by users without correct authentication/authorization.

The main API endpoints affected by this:

- `/api/v3/crypto/certificatekeypairs/<uuid>/view_certificate/`
- `/api/v3/crypto/certificatekeypairs/<uuid>/view_private_key/`
- `/api/v3/.../used_by/`

Note that all of the affected API endpoints require the knowledge of the ID of an object, which especially for certificates is not accessible to an unprivileged user. Additionally the IDs for most objects are UUIDv4, meaning they are not easily guessable/enumerable.

### Patches

authentik 2024.4.4, 2024.6.4 and 2024.8.0 fix this issue.

### Workarounds

Access to the API endpoints can be blocked at a Reverse-proxy/Load balancer level to prevent this issue from being exploited.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2024-52289.md
================================================================================

# CVE-2024-52289

_Reported by [@PontusHanssen](https://github.com/PontusHanssen)_

## Insecure default configuration for OAuth2 Redirect URIs

### Summary

Redirect URIs in the OAuth2 provider in authentik are checked by RegEx comparison.
When no Redirect URIs are configured in a provider, authentik will automatically use the first `redirect_uri` value received as an allowed redirect URI, without escaping characters that have a special meaning in RegEx. Similarly, the documentation did not take this into consideration either.

Given a provider with the Redirect URIs set to `https://foo.example.com`, an attacker can register a domain `fooaexample.com`, and it will correctly pass validation.

### Patches

authentik 2024.8.5 and 2024.10.3 fix this issue.

The patched versions remedy this issue by changing the format that the Redirect URIs are saved in, allowing for the explicit configuration if the URL should be checked strictly or as a RegEx. This means that these patches include a backwards-incompatible database change and API change.

Manual action _is required_ if any provider is intended to use RegEx for Redirect URIs because the migration will set the comparison type to strict for every Redirect URI.

### Workarounds

When configuring OAuth2 providers, make sure to escape any wildcard characters that are not intended to function as a wildcard, for example replace `.` with `\.`.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2025-64708.md
================================================================================

# CVE-2025-64708

_Reported by [@melizeche](https://github.com/melizeche)_

## Invitation expiry is delayed by at least 5 minutes

### Summary

In previous authentik versions, invitations were considered valid regardless if they are expired or not, thus relying on background tasks to clean up expired ones. In a normal scenario this can take up to 5 minutes because the cleanup of expired objects is scheduled to run every 5 minutes. However, with a large amount of tasks in the backlog, this might take longer.

### Patches

authentik 2025.8.5 and 2025.10.2 fix this issue; for other versions the workaround below can be used.

### Workarounds

You can create a policy that explicitly checks whether the invitation is still valid, and then bind it to the invitation stage on your invitation flow, and deny access if the invitation is not valid.

```python
return not context['flow_plan'].context['invitation'].is_expired
```

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2025-64521.md
================================================================================

# CVE-2025-64521

## Deactivated service account can authenticate to OAuth

### Summary

When authenticating with `client_id` and `client_secret` to an OAuth provider, authentik creates a service account for the provider. In previous authentik versions, authentication for this account was possible even when the account was deactivated. Other permissions are correctly applied and federation with other providers still take assigned policies correctly into account.

### Patches

authentik 2025.8.5 and 2025.10.2 fix this issue, for other versions the workaround below can be used.

### Workarounds

You can add a policy to your application that explicitly checks if the service account is still valid, and deny access if not.

```python
return request.user.is_active
```

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2023-36456.md
================================================================================

# CVE-2023-36456

_Reported by [@thijsa](https://github.com/thijsa)_

## Lack of Proxy IP headers validation

### Summary

authentik does not verify the source of the X-Forwarded-For and X-Real-IP headers, both in the Python code and the go code.

### Impact

Only authentik setups that are directly accessible by users without a reverse proxy are susceptible to this. Possible spoofing of IP addresses in logs, downstream applications proxied by (built in) outpost, IP bypassing in custom flows if used.

### Details

This poses a possible security risk when you have flows or policies that check the user's IP address, e.g. when you want to ignore the user's 2 factor authentication when the user is connected to the company network.

Another security risk is that the IP addresses in the logfiles and user sessions is not reliable anymore, anybody can spoof this address and you cannot verify that the user has logged in from the IP address that is in their account's log.

And the third risk is that this header is passed on to the proxied application behind an outpost. The application may do any kind of verification, logging, blocking or rate limiting based on the IP address, and this IP address can be overridden by anybody that want to.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2024-23647.md
================================================================================

# CVE-2024-23647

_Reported by [@pieterphilippaerts](https://github.com/pieterphilippaerts)_

## PKCE downgrade attack in authentik

## Summary

PKCE is a very important countermeasure in OAuth2, both for public and confidential clients. It protects against CSRF attacks and code injection attacks. Because of this bug, an attacker can circumvent the protection PKCE offers.

## Patches

authentik 2023.8.7 and 2023.10.7 fix this issue.

## Details

There is a bug in our implementation of PKCE that allows an attacker to circumvent the protection that PKCE offers. PKCE adds the `code_challenge` parameter to the authorization request and adds the `code_verifier` parameter to the token request. We recently fixed a downgrade attack (in v2023.8.5 and 2023.10.4) where if the attacker removed the `code_verifier` parameter in the token request, authentik would allow the request to pass, thus circumventing PKCE’s protection. However, in the latest version of the software, another downgrade scenario is still possible: if the attacker removes the `code_challenge` parameter from the authorization request, authentik will also not do the PKCE check.

Note that this type of downgrade enables an attacker to perform a code injection attack, even if the OAuth client is using PKCE (which is supposed to protect against code injection attacks). To start the attack, the attacker must initiate the authorization process without that `code_challenge` parameter in the authorization request. But this is easy to do (just use a phishing site or email to trick the user into clicking on a link that the attacker controls – the authorization link without that `code_challenge` parameter).

The OAuth BCP (https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics) explicitly mentions this particular attack in section 2.1.1: “Authorization servers MUST mitigate PKCE Downgrade Attacks by ensuring that a token request containing a code_verifier parameter is accepted only if a code_challenge parameter was present in the authorization request, see Section 4.8.2 for details.”

## For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2024-47070.md
================================================================================

# CVE-2024-47070

_Reported by [@efpi-bot](https://github.com/efpi-bot) from [LogicalTrust](https://logicaltrust.net/en/)_

## Password authentication bypass via X-Forwarded-For HTTP header

### Summary

The vulnerability allows bypassing policies by adding X-Forwarded-For header with unparsable IP address, e.g. "a". This results in a possibility to authenticate/authorize to any account with known login or email address.

Since the default authentication flow uses a policy to enable the password stage only when there is no password stage selected on the Identification stage, this vulnerability can be used to skip this policy and continue without the password stage.

### Am I affected

This can be exploited for the following configurations:

- An attacker can access authentik without a reverse proxy (and `AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS` is not configured properly)
- The reverse proxy configuration does not correctly overwrite X-Forwarded-For
- Policies (User and group bindings do _not_ apply) are bound to authentication/authorization flows

### Patches

authentik 2024.6.5 and 2024.8.3 fix this issue.

### Workarounds

Ensure the X-Forwarded-For header is always set by the reverse proxy, and is always set to a correct IP.

In addition you can manually change the _Failure result_ option on policy bindings to _Pass_, which will prevent any stages from being skipped if a malicious request is received.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2024-47077.md
================================================================================

# CVE-2024-47077

_Reported by [@quentinmit](https://github.com/quentinmit)_

## Insufficient cross-provider token validation during introspection

### Summary

Access tokens issued to one application can be stolen by that application and used to impersonate the user against any other proxy provider. Also, a user can steal an access token they were legitimately issued for one application and use it to access another application that they aren't allowed to access.

### Details

The proxy provider uses `/application/o/introspect/` to validate bearer tokens provided in the `Authorization` header:

The implementation of this endpoint separately validates the `client_id` and `client_secret` (which are that of the proxy provider) and the `token` without validating that they correspond to the same provider.

### Patches

authentik 2024.6.5 and 2024.8.3 fix this issue.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2024-21637.md
================================================================================

# CVE-2024-21637

_Reported by [@lauritzh](https://github.com/lauritzh)_

## XSS in Authentik via JavaScript-URI as Redirect URI and form_post Response Mode

### Summary

Given an OAuth2 provider configured with allowed redirect URIs set to `*` or `.*`, an attacker can send an OAuth Authorization request using `response_mode=form_post` and setting `redirect_uri` to a malicious URI, to capture authentik's session token.

### Patches

authentik 2023.8.6 and 2023.10.6 fix this issue.

### Impact

The impact depends on the attack scenario. In the following I will describe the two scenario that were identified for Authentik.

#### Redirect URI Misconfiguration

While advising that this may cause security issues, Authentik generally allows wildcards as Redirect URI. Therefore, using a wildcard-only effectively allowing arbitrary URLS is possible misconfiguration that may be present in real-world instances.

In such cases, unauthenticated and unprivileged attackers can perform the above described actions.

### User with (only) App Administration Permissions

A more likely scenario is an administrative user (e.g. a normal developer) having only permissions to manage applications.

This relatively user could use the described attacks to perform a privilege escalation.

### Workaround

It is recommended to upgrade to the patched version of authentik. If not possible, ensure that OAuth2 providers do not use a wildcard (`*` or `.*`) value as allowed redirect URI setting. (This is _not_ exploitable if part of the redirect URI has a wildcard, for example `https://foo-.*\.bar\.com`)

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2022-46172.md
================================================================================

# CVE-2022-46172

_Reported by [@DreamingRaven](https://github.com/DreamingRaven)_

## Existing Authenticated Users can Create Arbitrary Accounts

### Summary

Any authenticated user can create an arbitrary number of accounts through the default flows. This would circumvent any policy in a situation where it is undesirable for users to create new accounts by themselves. This may also have carry over consequences to other applications being how these new basic accounts would exist throughout the SSO infrastructure. By default the newly created accounts cannot be logged into as no password reset exists by default. However password resets are likely to be enabled by most installations.

### Patches

authentik 2022.11.4, 2022.10.4 and 2022.12.0 fix this issue.

### Impact

This vulnerability could make it much easier for name and email collisions to occur, making it harder for user to log in. This also makes it more difficult for admins to properly administer users since more and more confusing users will exist. This paired with password reset flows if enabled would mean a circumvention of on-boarding policies. Say for instance a company wanted to invite a limited number of beta testers, those beta testers would be able to create an arbitrary number of accounts themselves.

### Details

This vulnerability has already been submitted over email, this security advisory serves as formalization towards broader information dissemination. This vulnerability pertains to the user context used in the default-user-settings-flow. /api/v3/flows/instances/default-user-settings-flow/execute/

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2022-23555.md
================================================================================

# CVE-2022-23555

_Reported by [@fuomag9](https://github.com/fuomag9)_

## Token reuse in invitation URLs leads to access control bypass via the use of a different enrollment flow

### Summary

Token reuse in invitation URLs leads to access control bypass via the use of a different enrollment flow than in the one provided.

### Patches

authentik 2022.11.4, 2022.10.4 and 2022.12.0 fix this issue, for other versions the workaround can be used.

### Impact

Only configurations using both invitations and have multiple enrollment flows with invitation stages that grant different permissions are affected. The default configuration is not vulnerable, and neither are configurations with a single enrollment flow.

### Details

The vulnerability allows an attacker that knows different invitation flows names (e.g. `enrollment-invitation-test` and `enrollment-invitation-admin`) via either different invite links or via brute forcing to signup via a single invitation url for any valid invite link received (it can even be a url for a third flow as long as it's a valid invite) as the token used in the `Invitations` section of the Admin interface does NOT change when a different `enrollment flow` is selected via the interface and it is NOT bound to the selected flow, so it will be valid for any flow when used.

### Workarounds

As a workaround, fixed data can be added to invitations which can be checked in the flow to deny requests. Alternatively, an identifier with high entropy (like a UUID) can be used as flow slug, mitigating the attack vector by exponentially decreasing the possibility of discovering other flows.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2025-29928.md
================================================================================

# CVE-2025-29928

## Deletion of sessions did not revoke sessions when using database session storage

### ADDENDUM May 30, 2025

As of version 2025.4, the option to store sessions in cache has been removed; sessions are now exclusively stored in the database. See our [2025.4 release notes](../../releases/2025/v2025.4.md#sessions-are-now-stored-in-the-database) for more information.

### Summary

When authentik was configured to use the database for session storage (which is a non-default setting), deleting sessions via the Web Interface or the API would not revoke the session and the session holder would continue to have access to authentik.

This also affects automatic session deletion when a user is set to inactive or a user is deleted.

The session backend was configured via the `AUTHENTIK_SESSION_STORAGE` setting, which was removed in version 2025.4.

### Patches

authentik 2025.2.3 and 2024.12.4 fix this issue.

### Workarounds

Switching to the cache-based session storage until the authentik instance can be upgraded is recommended. This will however also delete all existing sessions and users will have to re-authenticate.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2023-48228.md
================================================================================

# CVE-2023-48228

_Reported by [@Sapd](https://github.com/Sapd)_

## OAuth2: Insufficient PKCE check

### Summary

When initializing a OAuth2 flow with a `code_challenge` and `code_method` (thus requesting PKCE), the SSO provider (authentik) **must** check if there is a matching **and** existing `code_verifier` during the token step.

authentik checks if the contents of code*verifier is matching \*\*\_ONLY*\*\* when it is provided. When it is left out completely, authentik simply accepts the token request without it; even when the flow was started with a `code_challenge`.

### Patches

authentik 2023.8.5 and 2023.10.4 fix this issue.

### Details

The `code_verifier` is only checked when the user provides it. Note that in line 209 there is a check if the code_parameter is left out. But there is no check if the PKCE parameter simply was omitted WHEN the request was started with a `code_challenge_method`.

This oversight likely did not stem from a coding error but from a misinterpretation of the RFC, where the backward compatibility section may be somewhat confusing.
https://datatracker.ietf.org/doc/html/rfc7636#section-4.5
RFC7636 explicitly says in Section 4.5:

> The "code_challenge_method" is bound to the Authorization Code when
> the Authorization Code is issued. That is the method that the token
> endpoint MUST use to verify the "code_verifier".

Section 5, Compatibility

> Server implementations of this specification MAY accept OAuth2.0
> clients that do not implement this extension. If the "code_verifier"
> is not received from the client in the Authorization Request, servers
> supporting backwards compatibility revert to the OAuth 2.0 [[RFC6749](https://datatracker.ietf.org/doc/html/rfc6749)]
> protocol without this extension.

Section 5, Compatibility, allows server implementations of this specification to accept OAuth 2.0 clients that do not implement this extension. However, if a `code_verifier` is not received from the client in the Authorization Request, servers that support backward compatibility should revert to the standard OAuth 2.0 protocol sans this extension (including all steps).

It should be noted that this does not mean that the `code_verifier` check can be disregarded at any point if the initial request included `code_challenge` or `code_challenge_method`. Since Authentik supports PKCE, it **MUST** verify the code_verifier as described in Section 4.5 **AND** fail if it was not provided.

Ofc verification can be skipped if the original authorization request did not invoke PKCE (no `code_challenge_method` and no `code_challenge`).

Failure to check the `code_verifier` renders the PKCE flow ineffective. This vulnerability particularly endangers public or hybrid clients, as their `code` is deemed non-confidential.

While not explicitly stated in the standard, it is generally recommended that OAuth2 flows accepting public clients should enforce PKCE - at least when redirecting to a non HTTPS URL (like http or an app link).

### Impact

The vulnerability poses a high risk to both public and hybrid clients.
When for example a mobile app implements oauth2, a malicious app can simply also register the same in-app-link (e.g. `mycoolapp://oauth2`) for the redirect callback URL, possibly receiving `code` during callback. With PKCE working, a malicious app would still receive a `code` but the `code` would not work without the correct unhashed code-challenge.
This is especially problematic, because authentik claims to support PKCE, and a developer can expect that the proper checks are in place. Note that app-links cannot be protected by HTTPS or similar mechanisms.

Note also that this vulnerability poses a threat to confidential clients. Many confidential clients act as a proxy for OAuth2 API requests, typically from mobile apps or single-page applications. These proxies relay `code_challenge`, `code_challenge_method` (in auth request, which most libraries force and provide on default settings) and `code_verifier` in the token request unchanged and supplement the CLIENT_SECRET which only the relay knows. The relay can but does not have to check for an existing `code_verifier` as the standard does not define that PKCE can be ignored on confidential clients during the token request when the client requested PKCE during the authorization request.

An attacker could potentially gain full access to the application. If the code grants access to an admin account, the confidentiality, integrity, and availability of that application are compromised.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2023-46249.md
================================================================================

# CVE-2023-46249

_Reported by [@devSparkle](https://github.com/devSparkle)_

## Potential Installation takeover when default admin user is deleted

### Summary

In the affected versions, when the default admin user has been deleted, it is potentially possible for an attacker to set the password of the default admin user without any authentication.

### Patches

authentik 2023.8.4 and 2023.10.2 fix this issue, for other versions the workaround can be used.

### Impact

authentik uses a blueprint to create the default admin user, which can also optionally set the default admin users' password from an environment variable. When the user is deleted, the `initial-setup` flow used to configure authentik after the first installation becomes available again.

### Workarounds

Ensure the default admin user (Username `akadmin`) exists and has a password set. It is recommended to use a very strong password for this user, and store it in a secure location like a password manager. It is also possible to deactivate the user to prevent any logins as akadmin.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2026-25922.md
================================================================================

# CVE-2026-25922

_Reported by [@odgrso](https://github.com/odgrso)_

## Signature Verification bypass in SAML Source Assertion

### Summary

When using a SAML Source that has the option **Verify Assertion Signature** under **Verification Certificate** enabled and not **Verify Response Signature**, or does not have the **Encryption Certificate** setting under **Advanced Protocol settings** configured, it was possible for an attacker to inject a malicious assertion before the signed assertion that authentik would use instead.

### Patches

authentik 2025.8.6, 2025.10.4 and 2025.12.4 fix this issue, for other versions the workaround below can be used.

### Impact

Depending on configuration of the source it is possible to authenticate as any existing user.

### Workarounds

Configure the SAML Source to enable **Verify Response Signature** or the **Encryption Certificate** if possible.

If this isn't possible, add this property mapping expression on the SAML source to detect duplicate assertions:

```python
assertions = root.findall("{urn:oasis:names:tc:SAML:2.0:assertion}Assertion")
if len(assertions) > 1:
  raise ValueError("Multiple assertions found")
return {}
```

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/security/cves/CVE-2026-25227.md
================================================================================

# CVE-2026-25227

_Reported by [@rahulgovind](https://github.com/rahulgovind)_

## Authenticated Remote Code Execution via Policy/Property Mapping test endpoint

### Summary

When using delegated permissions, a User that has the permission **Can view \* Property Mapping** or **Can view Expression Policy** is able to execute arbitrary code within the authentik server container through the `test` endpoint, which is intended to preview how a property mapping/policy works.

### Patches

authentik 2025.8.6, 2025.10.4 and 2025.12.4 fix this issue; for other versions the workaround below can be used.

### Impact

Users with the view permissions specified above are able to execute arbitrary code that has access to the entire authentik database as well as any environment variables, allowing the user to escalate their permissions and fully take over an instance.

### Workarounds

If an upgrade is not possible, it is strongly recommended to un-assign the **Can view \* Property Mapping** and **Can view Expression Policy** permissions from any user that should not have administrative privileges, and treat them equal to the edit equivalent permissions.

It is also possible to block requests to the test endpoint, which have the following URLs:

(:uuid is a placeholder for any UUID.)

```
POST /api/v3/propertymappings/all/:uuid/test/
POST /api/v3/policies/all/:uuid/test/
```

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/expressions/_functions.mdx
================================================================================

### `regex_match(value: Any, regex: str) -> bool`

Check if `value` matches Regular Expression `regex`.

Example:

```python
return regex_match(request.user.username, '.*admin.*')
```

### `regex_replace(value: Any, regex: str, repl: str) -> str`

Replace anything matching `regex` within `value` with `repl` and return it.

Example:

```python
user_email_local = regex_replace(request.user.email, '(.+)@.+', '')
```

### `list_flatten(value: list[Any] | Any) -> Optional[Any]`

Flatten a list by either returning its first element, None if the list is empty, or the passed in object if it's not a list.

Example:

```python
user = list_flatten(["foo"])
# user = "foo"
```

### `ak_call_policy(name: str, **kwargs) -> PolicyResult`

Call another policy with the name _name_. The current request is passed to the policy. Keyword arguments
can be used to modify the request's context.

Example:

```python
result = ak_call_policy("test-policy")
# result is a PolicyResult object, so you can access `.passing` and `.messages`.
# Starting with authentik 2023.4, you can also access `.raw_result`, which is the raw value returned from the called policy
# `result.passing` will always be a boolean if the policy is passing or not.
return result.passing

result = ak_call_policy("test-policy-2", foo="bar")
# Inside the `test-policy-2` you can then use `request.context["foo"]`
return result.passing
```

### `ak_is_group_member(user: User, **group_filters) -> bool`

Check if `user` is member of a group matching `**group_filters`.

Example:

```python
return ak_is_group_member(request.user, name="test_group")
```

### `ak_user_by(**filters) -> Optional[User]`

Fetch a user matching `**filters`.

Returns `None` if no user was found; otherwise, returns the [User](../users-sources/user/index.mdx) object.

Example:

```python
# Find user by username
other_user = ak_user_by(username="other_user")

# Find user by custom attribute
other_user = ak_user_by(attributes__<custom_attribute_name>="<value>")
```

### `ak_user_has_authenticator(user: User, device_type: Optional[str] = None) -> bool`

Check if a user has any authenticator devices. Only fully validated devices are counted.

Optionally, you can filter by a specific device type. The following options are valid:

- `totp`
- `duo`
- `static`
- `webauthn`

Example:

```python
return ak_user_has_authenticator(request.user)
```

### `ak_create_event(action: str, **kwargs) -> None`

Create a new event with the action set to `action`. Any additional keyword parameters will be saved in the event context. Additionally, `context` will be set to the context in which this function is called.

Before saving, any data structures which are not representable in JSON are flattened, and credentials are removed.

The event is saved automatically.

Example:

```python
ak_create_event("my_custom_event", foo=request.user)
```

### `ak_create_jwt(user: User, provider: OAuth2Provider | str, scopes: list[str], validity = "seconds=60") -> str | None`:ak-version[2025.2]

:::info Requires HTTP Request
This function will only work when there is an HTTP request in the current context.
:::

Create a new JWT signed by the given `provider` for `user`.

The `provider` parameter can either be an instance of `OAuth2Provider` or the name of a provider instance as a string. Scopes are an array of all scopes that the JWT should have.

The JWT is valid for 60 seconds by default, and this can be customized using the `validity` parameter. The syntax of the parameter is `hours=1,minutes=2,seconds=3`. The following keys are allowed:

    - Microseconds
    - Milliseconds
    - Seconds
    - Minutes
    - Hours
    - Days
    - Weeks

    All values accept floating-point values.

Example:

```python
jwt = ak_create_jwt(request.user, "my-oauth2-provider-name", ["openid", "profile", "email"])
```

### `ak_create_jwt_raw(provider: OAuth2Provider | str, validity = "seconds=60", **kwargs) -> str | None`:ak-version[2025.12]

Similar to [`ak_create_jwt`](#ak_create_jwtuser-user-provider-oauth2provider--str-scopes-liststr-validity--seconds60---str--none), however this function does _not_ require an HTTP request and allows for setting custom claims via `**kwargs`.

The `provider` parameter can either be an instance of `OAuth2Provider` or the name of a provider instance as a string. Scopes are an array of all scopes that the JWT should have.

The JWT is valid for 60 seconds by default, and this can be customized using the `validity` parameter. The syntax of the parameter is `hours=1,minutes=2,seconds=3`. The following keys are allowed:

    - Microseconds
    - Milliseconds
    - Seconds
    - Minutes
    - Hours
    - Days
    - Weeks

    All values accept floating-point values.

Example:

```python
jwt = ak_create_jwt_raw("my-oauth2-provider-name", my_claim="my_value")
```

### `ak_send_email(address: str | list[str], subject: str, body: str = None, stage: EmailStage = None, template: str = None, context: dict = None, cc: str | list[str] = None, bcc: str | list[str] = None) -> bool`:ak-version[2025.10]

Send an email using authentik's email system.

The `address` parameter specifies the recipient email address(es). It can be:

- A single email address as a string: `"user@example.com"`
- A list of email addresses: `["user1@example.com", "user2@example.com"]`

:::info
When using multiple recipients in the `address` or `cc` fields, all email addresses will be visible to all recipients. Use `bcc` to send to multiple recipients without revealing addresses to each other.
:::

The `subject` parameter sets the email subject line.

You must provide either `body` (for plain text/HTML content) or `template` (for template rendering), but not both.

The `stage` parameter can be an `EmailStage` instance for custom email settings. If `None`, global email settings are used.

The `template` parameter specifies a template name to render. When using templates, you can pass additional context variables via the `context` parameter.

The `cc` parameter specifies email address(es) to carbon copy. Same format as `address`.

The `bcc` parameter specifies email address(es) to blind carbon copy. Same format as `address`. Recipients in `bcc` will not be visible to other recipients.

If the email is queued successfully, the function returns `True`; otherwise, it returns `False`.

Examples:

```python
# Send email with plain body to single recipient
ak_send_email("user@example.com", "Welcome!", body="Welcome to our platform!")

# Send email to multiple recipients
ak_send_email(
    ["user1@example.com", "user2@example.com", "admin@example.com"],
    "System Maintenance",
    body="Scheduled maintenance will occur tonight."
)

# Send email using a template
ak_send_email("user@example.com", "Password Reset", template="email/password_reset.html")

# Send email with custom context for template to multiple recipients
ak_send_email(
    ["user@example.com", "admin@example.com"],
    "Account Update",
    template="email/event_notification.html",
    context={
        "title": "Profile Updated",
        "body": "Your account profile has been successfully updated.",
        "key_value": {"Updated Field": "Email Address", "Date": "2025-01-01"}
    }
)

# Send email with custom email stage
ak_send_email("admin@example.com", "Report", body="Daily report", stage=my_custom_stage)

# Send email with CC
ak_send_email(
    "user@example.com",
    "Important Update",
    body="Please review this update.",
    cc="manager@example.com"
)

# Send email with multiple CC and BCC recipients
ak_send_email(
    "user@example.com",
    "Confidential Report",
    body="Attached is the quarterly report.",
    cc=["manager@example.com", "lead@example.com"],
    bcc=["audit@example.com", "compliance@example.com"]
)
```

## Comparing IP Addresses

To compare IP addresses or check if an IP address is within a given subnet, you can use the functions `ip_address('192.0.2.1')` and `ip_network('192.0.2.0/24')`. With these objects you can do [arithmetic operations](https://docs.python.org/3/library/ipaddress.html#operators).

You can also check if an IP Address is within a subnet by writing the following:

```python
ip_address('192.0.2.1') in ip_network('192.0.2.0/24')
# evaluates to True
```

## DNS resolution and reverse DNS lookups

To resolve a hostname to a list of IP addresses, use the functions `resolve_dns(hostname)` and `resolve_dns(hostname, ip_version)`.

```python
resolve_dns("google.com")  # returns a list of all IPv4 and IPv6 addresses
resolve_dns("google.com", 4)  # returns a list of only IPv4 addresses
resolve_dns("google.com", 6)  # returns a list of only IPv6 addresses
```

You can also perform reverse DNS lookups.

:::note
Reverse DNS lookups may not return the expected host if the IP address is part of a shared hosting environment.
See: https://stackoverflow.com/a/19867936
:::

To perform a reverse DNS lookup use `reverse_dns("192.0.2.0")`. If no DNS records are found the original IP address is returned.

:::info
DNS resolving results are cached in memory. The last 32 unique queries are cached for up to 3 minutes.
:::



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/expressions/_objects.md
================================================================================

- `ak_logger`: structlog BoundLogger. See [structlog documentation](https://www.structlog.org/en/stable/api.html#structlog.BoundLogger)

    Example:

    ```python
    ak_logger.debug("This is a test message")
    ak_logger.warning("This will be logged with a warning level")
    ak_logger.info("Passing structured data", request=request)
    ```

- `requests`: requests Session object. See [requests documentation](https://requests.readthedocs.io/en/master/user/advanced/)



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/expressions/_user.md
================================================================================

- `user`: The current user. This may be `None` if there is no contextual user. See [User](../users-sources/user/user_ref.mdx#object-properties).

Example:

```python
return {
  "custom_attribute": request.user.attributes.get("custom_attribute", "default"),
}
```



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/install-config/automated-install.mdx
================================================================================

---
title: Automated install
---

To install authentik automatically (skipping the Out-of-box experience), you can use the following environment variables on the worker container:

:::info
These can't be defined using the file-based syntax (`file://`), so you can't pass them in as secrets in a Docker Compose installation.
:::

### `AUTHENTIK_BOOTSTRAP_PASSWORD`

Configure the default password for the `akadmin` user. Only read on the first startup. Can be used for any flow executor.

### `AUTHENTIK_BOOTSTRAP_TOKEN`

Create a token for the default `akadmin` user. Only read on the first startup. The string you specify for this variable is the token key you can use to authenticate yourself to the API.

### `AUTHENTIK_BOOTSTRAP_EMAIL`

Set the email address for the default `akadmin` user.

## Kubernetes

In the Helm values, set the `akadmin` user password and token:

```yaml
authentik:
    bootstrap_token: test
    bootstrap_password: test
```

To store the password and token in a secret, use:

```yaml
global:
    envFrom:
        - secretRef:
              name: _some-secret_
```

where _some-secret_ contains the environment variables as in the documentation above.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/install-config/high-availability.mdx
================================================================================

---
title: High availability
---

High availability refers to system design that minimizes downtime even in the event of failures or disruptions.

authentik supports high availability in several ways:

- Multiple instances of the server and worker can be run in parallel, allowing for redundancy.
- The authentik database is PostgreSQL, which has extensive support for different [highly available setups](https://www.postgresql.org/docs/current/high-availability.html).
- Both authentik and PostgreSQL support active-passive deployments.

## Parallel server and worker instances

authentik server and worker instances are stateless. All session state and configuration data is stored in the database. This statelessness makes it easy to horizontally scale authentik deployments by adding more server and worker instances, ensuring resilience and fault tolerance.

If a server or worker instance goes offline, another instance can continue to serve traffic. If these instances are distributed among multiple hosts, it can provide even higher levels of resilience and fault tolerance.

## PostgreSQL high availability

PostgreSQL provides high availability through _replication_ and _clustering_.

Refer to the [PostgreSQL High Availability, Load Balancing, and Replication documentation](https://www.postgresql.org/docs/current/high-availability.html) for more details.

authentik also has built-in support for [PostgreSQL Read Replicas](../configuration/#read-replicas) and using [PostgreSQL Connection Poolers](../configuration/#using-a-postgresql-connection-pooler) like PgBouncer or PgPool.

## Active-passive authentik deployment

In an active-passive deployment, one authentik instance actively serves all requests while the other is on standby, prepared to assume control in the event of a failure.

The components of an active-passive authentik deployment include:

- **Active Instance**: Handles all user authentication requests, API calls, and background tasks. It is fully operational and serves live traffic.
- **Passive Instance**: Runs as a hot/warm standby. Does not handle incoming traffic or processing. Does not actively write to the database.
- **Shared Database**: Both instances connect to the same PostgreSQL database which ensures data consistency. Because authentik is stateless, there are no data conflicts.
- **Load Balancer**: A load balancer monitors the active instance's health. Upon detecting failure, it promotes the passive instance to active by redirecting all traffic to it. This failover can be triggered automatically or manually, depending on your failover strategy. When the original active authentik instance is restored, it can either remain passive or be promoted back to active (failback).

For more information on monitoring the health of an authentik instance, refer to the [Monitoring documentation](../sys-mgmt/ops/monitoring.md).

The following diagram shows a typical active-passive configuration:

```mermaid
graph TD
    subgraph authentikInstances["authentik instances"]
        A[Active authentik instance]@{stroke: #fd4b2d}
        P[Passive authentik instance]@{stroke: #fd4b2d}
    end

    U[Users]@{ shape: processes}
    L[Load Balancer]
    PG[(PostgreSQL Cluster)]

    U <-->|Traffic| L

    L <-->|Traffic + Health monitoring| A
    L ---|Health monitoring| P

    A <-->|Database traffic - Read and Write| PG
    P ---|Database traffic - Read only| PG

    style A stroke: #fd4b2d,stroke-width:2px
    style P stroke: #fd4b2d,stroke-width:2px
    style authentikInstances stroke:#fd4b2d,stroke-width:2px
```

This setup provides several advantages:

- **Resilient hosting options**: The ability to host each authentik deployment in separate environments. Different hardware, datacenters, or providers can be utilized for each deployment to increase resiliency and fault tolerance.
- **Continuity of service**: During maintenance windows, continuity of service can be assured by switching between active and passive instances.
- **Automatic failover**: A load balancer allows for automatic failover based on health monitoring, rather than waiting for administrators to detect an issue and manually failover.
- **Possibility of blue-green deployment**: The use of a load balancer also allows for blue-green methodology, assuming that appropriate changes are made to the database.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/install-config/air-gapped.mdx
================================================================================

---
title: Air-gapped environments
---


## Outbound connections

By default, authentik creates outbound connections to the following URLs:

- https://version.goauthentik.io: Periodic update check
- https://goauthentik.io: Anonymous analytics on startup
- https://secure.gravatar.com: Avatars for users
- https://authentik.error-reporting.a7k.io: Error reporting
- https://tile.openstreetmap.org: Map tiles for event logs :ak-enterprise :ak-version[2025.8]

## Configuration

To disable these outbound connections, adjust the following settings:


Additionally, adjust the following [System settings](../sys-mgmt/settings.md):

- **Avatars**: By default this setting connects to [Gravatar](https://secure.gravatar.com/). To avoid outgoing connections, set this to a combination of other options, such as `initials`.

## Required resources

### Container images

authentik deployments require access to the following container images. In an air-gapped environment, this can be achieved by mirroring the images to an internal registry, or using other methods appropriate for your environment.

#### Main image

- `ghcr.io/goauthentik/server` or `authentik/server`

#### Outpost images

- `ghcr.io/goauthentik/ldap` or `authentik/ldap`
- `ghcr.io/goauthentik/proxy` or `authentik/proxy`
- `ghcr.io/goauthentik/rac` or `authentik/rac`
- `ghcr.io/goauthentik/radius` or `authentik/radius`

#### Supporting services

- PostgreSQL

### Helm repositories

For Helm deployments, ensure access to the following repository. In an air-gapped environment, this can be achieved by mirroring the chart to an internal registry, or using other methods appropriate for your environment.

- https://charts.goauthentik.io

## Network requirements

### Required ports

- **9000/9443**: Default authentik server ports for HTTP/HTTPS access.
- **80/443**: For reverse proxy setups (if using a load balancer or ingress controller).
- **SMTP ports**: Connectivity to your configured SMTP server (typically 25, 465, or 587).
- **S3/object storage**: If configured, connectivity to your S3-compatible storage.

### Outpost-specific ports

Each outpost container, in order to communicate with authentik, requires access to the authentik server via whichever protocol is specified in the URL set in the `AUTHENTIK_HOST` environment variable (preferably HTTPS).

The outpost containers also need certain ports exposed:

- **LDAP Outpost**: Ports 389/636 (LDAP/LDAPS) exposed to ports 3389/6636 of the container.
- **Proxy Outpost**: Ports 9000/9443 (HTTP/HTTPS) exposed to ports 9000/9443 of the container.
- **RAC Outpost**: Exposed ports not required.
- **RADIUS Outpost**: Port 1812 (RADIUS Authentication) exposed to port 1812/udp of the container.

For more detailed information about outpost configuration in air-gapped environments, see the [Outposts documentation](../add-secure-apps/outposts/index.mdx).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/install-config/index.mdx
================================================================================

---
title: Installation and Configuration
---

Everything you need to get authentik up and running!

The installation process for our free open source version and our [Enterprise](../enterprise/index.md) version are exactly the same. For information about obtaining an Enterprise license, refer to [License management](../enterprise/manage-enterprise.mdx#license-management) documentation.

For information about upgrading to a new version, refer to the <b>Upgrade</b> section in the relevant [Release Notes](../releases) and to our [Upgrade authentik](./upgrade.mdx) documentation.





================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/install-config/beta.mdx
================================================================================

---
title: Beta and release candidate versions
---


You can test upcoming authentik versions before they are released as stable. There are two types of pre-release versions available:

- **Release Candidates (RC)**: Near-final versions that are feature-complete and undergoing final testing before a stable release. RCs are more stable than Beta versions and are recommended for testing in staging environments.
- **Beta versions**: Early builds that include new, or experimental features and may introduce bugs or breaking changes.

It is recommended to upgrade your installation to the latest stable release before switching from stable to an RC or Beta version.

:::warning
Downgrading from RC or Beta versions is not supported. It is recommended to take a backup before upgrading, or test these versions on a separate installation. Upgrading from RC or Beta versions to the next stable release generally works, but is not officially supported.
:::

## Release Candidate (RC) versions

Release candidates are available for testing before major version releases. To use an RC version, you need to specify the exact RC tag (e.g., `2025.10.0-rc3`).



## Beta versions

Beta versions provide early access to major new features that are still in active development.






:::info
If you are upgrading from an older Beta release to the most recent Beta release, you might need to run `kubectl rollout restart deployment`, because Helm needs to recreate the pods in order to pick up the new image (the tag doesn't change).
:::

## Verifying the installation

To verify whether the upgrade was successful, go to your Admin panel and navigate to the Overview dashboard. There, you can check the version number to ensure that you are using the RC or Beta version you intended.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/install-config/upgrade.mdx
================================================================================

---
title: Upgrade authentik
---

Upgrading to the latest version of authentik, whether a new major release or a patch, involves running a few commands to pull down the latest images and then restarting the servers and databases.

## Important considerations

:::danger
authentik does not support downgrading. Make sure to back up your database in case you need to revert an upgrade.
:::

**Preview the release notes**: Be sure to carefully read the [Release Notes](../../releases/) for the specific version to which you plan to upgrade. The release might have special requirements or actions, or contain breaking changes.

**Database backup**: Before upgrading, make a backup of your PostgreSQL database. You can create a backup by dumping your existing database. For detailed instructions, refer to the relevant guide for your deployment method ([Docker Compose](../troubleshooting/postgres/upgrade_docker.md) or [Kubernetes](../troubleshooting/postgres/upgrade_kubernetes.md)).

**Upgrade sequence**: Upgrades must follow the sequence of major releases; **do not skip** directly from an older major version to the most recent version.

Always upgrade to the latest minor version (`.x`) within each `major.minor` version before upgrading to the next major version. For example, if you're currently running `2025.2.1`, upgrade in the following order:

1. Upgrade to the latest `2025.2.x`.
2. Then to the latest `2025.4.x`.
3. Finally to the latest `2025.6.x`.

**Outposts**: The version of the authentik server and all authentik outposts must match. Ensure that all [outposts are upgraded](../add-secure-apps/outposts/upgrading.md) at the same time as the core authentik instance.

## Upgrade authentik



## Upgrade any outposts

Be sure to also [upgrade any outposts](../add-secure-apps/outposts/upgrading.md) when you upgrade your authentik instance.

## Verify your upgrade

You can view the current version of your authentik instance by logging in to the Admin interface, and then navigating to **Dashboards > Overview**.

![](./version1.png)

## Troubleshooting your upgrade

If you run the upgrade commands but your version on the Dashboard doesn't change, follow these steps:

1. Look at the server logs and search for an entry of `migration inconsistency`.
2. If you see this entry, revert to your database backup.
3. Now, upgrade to each subsequent higher version. That is, upgrade in sequence, do not skip directly to the most recent version.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/install-config/reverse-proxy.md
================================================================================

---
title: Reverse proxy
---

:::info
Since authentik uses WebSockets to communicate with Outposts, it does not support HTTP/1.0 reverse proxies. The HTTP/1.0 specification does not officially support WebSockets or protocol upgrades, though some clients may allow it.
:::

If you want to access authentik behind a reverse proxy, there are a few headers that must be passed upstream:

- `X-Forwarded-Proto`: Tells authentik and Proxy Providers if they are being served over an HTTPS connection.
- `X-Forwarded-For`: Without this, authentik will not know the IP addresses of clients.
- `Host`: Required for various security checks, WebSocket handshake, and Outpost and Proxy Provider communication.
- `Connection: Upgrade` and `Upgrade: WebSocket`: Required to upgrade protocols for requests to the WebSocket endpoints under HTTP/1.1.

It is also recommended to use a [modern TLS configuration](https://ssl-config.mozilla.org/) and disable SSL/TLS protocols older than TLS 1.3.

If your reverse proxy isn't accessing authentik from a private IP address, [trusted proxy CIDRs configuration](./configuration/configuration.mdx#listen-settings) needs to be set on the authentik server to allow client IP address detection.

The following nginx configuration can be used as a starting point for your own configuration.

```
# Upstream where your authentik server is hosted.
upstream authentik {
    server <hostname of your authentik server>:9443;
    # Improve performance by keeping some connections alive.
    keepalive 10;
}

# Upgrade WebSocket if requested, otherwise use keepalive
map $http_upgrade $connection_upgrade_keepalive {
    default upgrade;
    ''      '';
}

server {
    # HTTP server config
    listen 80;
    listen [::]:80;
    server_name sso.domain.tld;
    # 301 redirect to HTTPS
    return 301 https://$host$request_uri;
}
server {
    # HTTPS server config
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name sso.domain.tld;

    # TLS certificates
    ssl_certificate /etc/letsencrypt/live/domain.tld/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/domain.tld/privkey.pem;
    add_header Strict-Transport-Security "max-age=63072000" always;

    # Proxy site
    # Location can be set to a subpath if desired, see documentation linked below:
    # https://docs.goauthentik.io/docs/install-config/configuration/#authentik_web__path
    location / {
        proxy_pass https://authentik;
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade_keepalive;
    }
}
```



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/install-config/email.mdx
================================================================================

---
title: Email
---


This page covers both configuring authentik to send emails and testing that email delivery is working.

authentik can be configured with global email settings used to notify administrators about alerts, configuration issues, and new releases. They can also be used alongside [notification rules](../sys-mgmt/events/notifications.md) to send emails based on any event that occurs within authentik.

authentik also provides [Email stages](../../add-secure-apps/flows-stages/stages/email/), which are used to send emails to users for actions such as account recovery and verification. Email stages can be configured to use the global email settings or their own specific email settings.

:::warning
Some hosting providers block outgoing SMTP ports, in which case you will need to host an SMTP relay on a different port with a different provider.
:::

## Global email settings


## Testing email configuration

To test whether the global email settings are configured correctly, you can use the following command on your authentik server:

```shell
ak test_email <to_address>
```

To test the email settings of a specific email stage, you can optionally provide the `-S` parameter:

```shell
ak test_email <to_address> [-S <stage_name>]
```


## Google Workspace SMTP relay configuration

To send email through Google SMTP servers, the easiest and most reliable method is often to use [Google's SMTP relay service](https://support.google.com/a/answer/2956491). Google provides detailed guidance in their documentation: [Send email from a printer, scanner, or app](https://support.google.com/a/answer/176600?hl=en).

First, confirm the outbound IP address that authentik uses to send emails. [Follow Google's documentation](https://support.google.com/a/answer/2956491) to add the IP address or addresses to the **SMTP relay service** options in your workspace's Gmail settings.

    - Set **Allowed Senders** to `Only addresses in my domains`.
    - Set **Authentication** to `Only accept mail from the specified IP addresses`.
    - Do not set **Require SMTP Authentication**.
    - Select **Require TLS encryption**.


## SMTP server with TLS verification

If you're configuring authentik to send email via an SMTP server with TLS enabled, you must mount the certificate used for authentication in your authentik worker and server containers:




================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/install-config/install/kubernetes.md
================================================================================

---
title: Kubernetes installation
---

You can install authentik to run on Kubernetes using a Helm chart.

:::info
You can also [view a video walk-through](https://www.youtube.com/watch?v=O1qUbrk4Yc8) of the installation process on Kubernetes (with bonus details about email configuration and other important options).
:::

## Requirements

- Kubernetes
- Helm

## Video

View our video about installing authentik on Kubernetes.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/install-config/install/aws.md
================================================================================

---
title: AWS installation
---

You can install authentik to run on AWS with a CloudFormation template.

### Prerequisites

- An AWS account.
- An [AWS Certificate Manager](https://aws.amazon.com/certificate-manager/) certificate. Take note of the ARN of the certificate.

### Installation

Log in to your AWS account and create a CloudFormation stack [with our template](https://console.aws.amazon.com/cloudformation/home#/stacks/create/review?stackName=authentik&templateURL=https://authentik-cloudformation-templates.s3.amazonaws.com/authentik.ecs.latest.yaml).

Under the **Certificate ARN** input, enter the previously created certificate ARN. You can also configure other settings if needed. You can follow the prompts to create the stack.

This stack will create the following resources:

- AWS SSM secrets for the PostgreSQL user and the authentik secret key
- A VPC for all other resources
- A RDS PostgreSQL Multi-AZ cluster
- An ECS cluster with two tasks:
    - One for the authentik server
    - One for the authentik worker
- An ALB (Application Load Balancer) pointing to the authentik server ECS task with the configured certificate
- An EFS filesystem mounted on both ECS tasks for file storage

The stack will output the endpoint of the ALB to which you can point your DNS records.

## Access authentik from AWS CloudFormation

To launch authentik, in your browser go to:

`http://<domain_you_configured>/if/flow/initial-setup/`

:::info Initial setup in browser
You will get a `Not Found` error if initial setup URL doesn't include the trailing forward slash `/`. Also verify that the authentik server, worker, and PostgreSQL database are running and healthy. Review additional tips in our [troubleshooting docs](../../troubleshooting/login.md#cant-access-initial-setup-flow-during-installation-steps).
:::

### Further customization

If you require further customization, we recommend you install authentik via [Docker Compose](./docker-compose.mdx) or [Kubernetes](./kubernetes.md).



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/install-config/install/docker-compose.mdx
================================================================================

---
title: Docker Compose installation
---

This installation method is for test setups and small-scale production setups.

## Requirements

- A host with at least 2 CPU cores and 2 GB of RAM
- Podman or Docker Compose (Compose v2, see [instructions for upgrade](https://docs.docker.com/compose/migrate/))

## Video

View our video about installing authentik on Docker.


## Generate PostgreSQL password and secret key

If this is a fresh authentik installation, you need to generate a PostgreSQL password and a secret key. Use a secure password generator of your choice such as `pwgen`, or you can use `openssl` as below.

Run the following commands to generate a PostgreSQL password and secret key and write them to your `.env` file:

{/* prettier-ignore */}
```shell
echo "PG_PASS=$(openssl rand -base64 36 | tr -d '\n')" >> .env
echo "AUTHENTIK_SECRET_KEY=$(openssl rand -base64 60 | tr -d '\n')" >> .env
```

:::info
Because of a PostgreSQL limitation, only passwords up to 99 chars are supported. See: https://www.postgresql.org/message-id/09512C4F-8CB9-4021-B455-EF4C4F0D55A0@amazon.com
:::

To enable error reporting, run the following command:

```shell
echo "AUTHENTIK_ERROR_REPORTING__ENABLED=true" >> .env
```

For an explanation about what each service in the Docker Compose file does, see [Architecture](../../core/architecture.md).

## Configure custom ports

By default, authentik listens internally on port 9000 for HTTP and 9443 for HTTPS. To use different exposed ports such as 80 and 443, you can set the following variables in `.env`:

```shell
COMPOSE_PORT_HTTP=80
COMPOSE_PORT_HTTPS=443
```

See [Configuration](../configuration/configuration.mdx) to change the internal ports. Be sure to run `docker compose up -d` to rebuild with the new port numbers.

## Docker socket

By default, the authentik Docker Compose file mounts the Docker socket to the authentik worker container:

```yaml
- /var/run/docker.sock:/var/run/docker.sock
```

This is used for [automatic deployment and management of authentik Outposts](../../add-secure-apps/outposts/integrations/docker.md).

Mounting the Docker socket to a container comes with some inherent security risks. To reduce these risks, you can use a [Docker Socket Proxy](../../add-secure-apps/outposts/integrations/docker.md#docker-socket-proxy) as an additional layer of protection.

Alternatively, you can remove this mount and instead [manually deploy and manage outposts](../../add-secure-apps/outposts/manual-deploy-docker-compose.md).

## Email configuration (optional but recommended)

It is also recommended to configure global email settings. These are used by authentik to notify administrators about alerts, configuration issues and new releases. They can also be used by [Email stages](../../add-secure-apps/flows-stages/stages/email/index.mdx) to send verification/recovery emails.

For more information, refer to our [Email configuration](../email.mdx) documentation.

## Install and start authentik

:::warning
All internal operations use UTC. Times displayed in the UI are automatically localized for the user. Do not update or mount `/etc/timezone` or `/etc/localtime` in the authentik containers; it will cause problems with OAuth and SAML authentication, as seen this [GitHub issue](https://github.com/goauthentik/authentik/issues/3005).
:::

After you have downloaded the `docker-compose.yml` file, generated a password and a secret key, and optionally configured your global email, run these commands to retrieve and install the current version of authentik:

```shell
docker compose pull
docker compose up -d
```

The `compose.yml` file statically references the latest version available at the time of downloading the compose file. Each time you upgrade to a newer version of authentik, you download a new `compose.yml` file, which points to the latest available version. For more information, refer to the **Upgrading** section in the [Release Notes](../../../releases/).

## Access authentik

To start the initial setup, navigate to `http://<your server's IP or hostname>:9000/if/flow/initial-setup/`.

:::info Initial setup in browser
You will get a `Not Found` error if initial setup URL doesn't include the trailing forward slash `/`. Also verify that the authentik server, worker, and PostgreSQL database are running and healthy. Review additional tips in our [troubleshooting docs](../../troubleshooting/login.md#cant-access-initial-setup-flow-during-installation-steps).
:::

You are then prompted to set a password for the `akadmin` user (the default user).

## First steps in authentik





================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/install-config/first-steps/index.mdx
================================================================================

---
title: First steps
---


After you have installed and started authentik, you are now ready to add your first application and provider, add some users, and get started with using authentik as your Identity provider.

```mermaid
architecture-beta

    group first

    service install(mdi:application-cog-outline)[Install authentik] in first
    service acl(mdi:account-key-outline)[Access authentik] in first
    service apps(mdi:plus-box-multiple-outline)[Add an app and provider] in first
    service users(mdi:account-multiple-plus)[Create a new user] in first
    service further(mdi:cog-clockwise)[Further customization] in first

    install:R --> L:acl
    acl:R --> L:apps
    apps:R --> L:users
    users:R --> L:further

```

## Where are we now, and what's next?

The following tutorial assumes that you have already:

1. Installed authentik on either [Docker Compose](../../install-config/install/docker-compose.mdx#install-and-start-authentik), [Kubernetes](../../install-config/install/kubernetes.md#install-authentik-helm-chart), or [AWS CloudFormation](../../install-config/install/aws.md) and confirmed that the server, worker, and the PostgreSQL database are started and running.

2. Opened authentik in your browser to the `initial-setup` flow and added credentials for a default Admin account. ([Docker](../../install-config/install/docker-compose.mdx#access-authentik), [Kubernetes](../../install-config/install/kubernetes.md#access-authentik)), or [AWS CloudFormation](../../install-config/install/aws.md#access-authentik-from-aws-cloudformation).

:::info Initial setup in browser
You will get a `Not Found` error if the initial setup URL doesn't include the forward slash `/` at the very end of the URL. Also verify that the authentik server, worker, and PostgreSQL database are running and healthy. Review additional tips in our [troubleshooting docs](../../troubleshooting/login.md#cant-access-initial-setup-flow-during-installation-steps).
:::

Other optional pre-installation configurations that you might have already completed include:

- [Configured your global email address](../email/#global-email-settings).
- [Configured your PostgreSQL settings](../configuration/configuration.mdx#postgresql-settings) (read-replica, connections, etc.).
- Configured a [reverse proxy](../reverse-proxy.md).
- Configured your [media storage settings](../../install-config/configuration/configuration.mdx#media-storage-settings) or optionally [AWS S3 file storage](../../sys-mgmt/ops/storage-s3.md).
- Added additional [custom configurations environment variables](../configuration/#set-your-environment-variables).
- [Verified](../configuration/#verify-your-configuration-settings) your configuration settings.

## Install your first application and provider

Now that you have your authentik instance installed and configured with the required settings, you can add your first [application](../../../core/glossary/?application) and [provider](../../../core/glossary/?provider). After that, we'll walk through how to add your first user.

:::tip Security Best Practice

In a production environment, best practice is to first [create a group](../../users-sources/groups/manage_groups.mdx#create-a-group), then [create the user(s)](../../users-sources/user/user_basic_operations.md#create-a-user), and then add the application. Then you can configure the application to have a [binding](../../add-secure-apps/bindings-overview/work-with-bindings.md#) to a specific group or user. The binding controls the access to the application (whether or not it is displayed on a user's My Applications page).

:::

authentik supports integration with any application; refer to our [Integrations documentation](https://integrations.goauthentik.io) to view integrations guides for over 180 of the most common ones.

**In this guide we'll be setting up Grafana as an example application.**


### 1. Log in to authentik as an administrator and open the authentik Admin interface.

    **A.** In the Admin interface, navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair.

:::tip About application and provider pairs
Every application that you add to authentik requires a provider, which is used to configure the specific protocol between the application and authentik, for example OAuth2/OIDC, SAML, LDAP, or others.
:::

**B.** Provide the details for the application (Grafana) and provider (OAuth2/OIDC).

- **Configure the Application**:
    - **Name**: provide a descriptive name (such as Grafana).
        - **Group**: select an optional group for the application; groups are used to visually separate applications. For example, you can choose to group applications that you use for coding from those you use for internal communication.
    - **Policy engine mode**: select **Any** for this tutorial; the mode determines how strictly policies are adhered to.
        - <strong className="tip">TIP</strong>: in authentik,
          [policies](../../customize/policies/working_with_policies.md) are used in authentik to
          fine-tune access to applications, flows, stages and many other authentik components. It is
          not required to use a policy at all, though. The _policy engine mode_ setting of **Any**
          means that as long as a single policy passes (or if there are no policies bound to the
          application), then access to the application is granted. The mode **ALL** means that every
          one of any policies bound to the application must pass in order for a user to have access
          to the application.
    - **UI Settings**: optional UI settings that are displayed about the application, including the launch URL, and three settings to display extra information about the application on the **My Applications** page: an optional icon, the publisher of the application, and a brief description.

- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.

- **Configure the Provider**:
    - **Name**: Provide a name (or accept the auto-provided name).
    - **Authorization flow**: Select the default `implicit` authorization flow to use for this provider.
        - <strong className="tip">TIP</strong>: The authorization
          [flow](../../add-secure-apps/flows-stages/flow/index.md) is where the various steps, or
          [_stages_](../../add-secure-apps/flows-stages/stages/index.md) of authorization are
          defined and executed. The defined set of stages construct the workflows of authentication,
          authorization, etc.
    - **Protocol settings** provide the following required configurations:
        - Note the **Client ID**, **Client Secret**, and **Slug** values because they will be required later when you configure Grafana to use authentik.
        - Set a `Strict` redirect URI to `https://grafana.company/login/generic_oauth`.
            - <strong className="tip">TIP</strong>: The Redirect URI is where the application will
              go as soon as authentik's authorization flow is successfully completed.
    - **Logout URI**: set to `https://grafana.company/logout`.
    - **Logout Method**: set to `Front-channel`.
        - <strong className="tip">TIP</strong>: With OAuth2, front-channel logout is considered the
          default because most applications (including Grafana) do not support back-channel logout.
    - **Signing key**: select any available signing key.
        - <strong className="tip">TIP</strong>: authentik generates a key that you can use, called
          the `authentik Self-signed Certificate`, if you do not have a specific signing key for an
          application.

- **Configure Bindings** _(optional)_: for this tutorial, skip this step because you do not yet have a user. Later, after you create your first user, you can [create a binding](../../add-secure-apps/bindings-overview/work-with-bindings.md) to manage the display and access to applications on a user's **My applications** page.
    - <strong className="tip">TIP</strong>: By creating a binding between an application and a
      specific user, you are ensuring that the application is accessible only to that user and any
      other users or groups for whom you created a binding. Learn more about how bindings are used
      in authentik in our [Bindings overview](../../add-secure-apps/bindings-overview/index.md).

    For any fields not mentioned above, you can leave the default value.

**C.** Click **Submit** to save the new application and provider.

### 2. Configure Grafana to use authentik as its IdP

For some applications, you log in to the application and configure settings there; with Grafana you simply edit your Grafana Docker Compose file. Here you add basic configuration settings as well as the **Client ID**, **Client Secret**, and the **Slug** values that you obtained when you configured the application and provider in authentik in Step 1 above.

**A.** In the Grafana Docker Compose file, set the following environment variables:

:::tip Tips
These values are for a [Grafana instance running in Docker](https://grafana.com/docs/grafana/latest/setup-grafana/configure-docker/); for standalone or Helm Chart instances refer to our [Grafana integration guide](https://integrations.goauthentik.io/monitoring/grafana/).

Note that `authentik.company` is a placeholder that we use in our example settings; replace this with the domain that authentik is running on in your environment.
:::

```
environment:
    GF_AUTH_GENERIC_OAUTH_ENABLED: "true"
    GF_AUTH_GENERIC_OAUTH_NAME: "authentik"
    GF_AUTH_GENERIC_OAUTH_CLIENT_ID: "<Client ID from above>"
    GF_AUTH_GENERIC_OAUTH_CLIENT_SECRET: "<Client Secret from above>"
    GF_AUTH_GENERIC_OAUTH_SCOPES: "openid profile email"
    GF_AUTH_GENERIC_OAUTH_AUTH_URL: "https://authentik.company/application/o/authorize/"
    GF_AUTH_GENERIC_OAUTH_TOKEN_URL: "https://authentik.company/application/o/token/"
    GF_AUTH_GENERIC_OAUTH_API_URL: "https://authentik.company/application/o/userinfo/"
    GF_AUTH_SIGNOUT_REDIRECT_URL: "https://authentik.company/application/o/<application_slug>/end-session/"
    # Optionally enable auto-login (bypasses Grafana login screen)
    GF_AUTH_OAUTH_AUTO_LOGIN: "true"
    # Optionally map user groups to Grafana roles
    GF_AUTH_GENERIC_OAUTH_ROLE_ATTRIBUTE_PATH: "contains(groups[*], 'Grafana Admins') && 'Admin' || contains(groups[*], 'Grafana Editors') && 'Editor' || 'Viewer'"
    # Required if Grafana is running behind a reverse proxy
    GF_SERVER_ROOT_URL: "https://grafana.company"
```

**B.** Save your Grafana Docker Compose file, and then launch the stack and access Grafana via your browser at the configured URL.

**C.** To confirm that authentik is properly configured with the new application, log out of Grafana and then log back in using the **Sign in with authentik** button. You should be redirected to authentik to provide credentials.

## Add your first user

Now that you can access the authentik Admin interface, and you have added an application and provider, let's add a new user.

### 1. Log in to authentik as an administrator and open the authentik Admin interface.

    **A.** Navigate to **Directory > Users**, and click **New User**.

    **B.** Fill in the **_required_** fields:

    - **Username**: This value must be unique across all users.
    - <strong className="tip">TIP</strong>: With OAuth2, front-channel logout is considered the default because most applications
          (including Grafana) do not support back-channel logout.
    - **Path**: The path where the user will be created. By default the new user is created in the `users` directory, but you can change that later by editing the user.
        - <strong className="tip">TIP</strong>: Paths are basically directories that are used to organize your users (for example HR vs Sales, etc.). Paths do not impact access; they are purely organizational. Note that the top-level **users** directory displays all users in that directory and all sub-directories.

    For information about the **_optional_** fields below, refer to our [documentation on managing users](../../users-sources/user/user_basic_operations.md#create-a-user).

    - **Name**: The display name of the user.
    - **Email**: The email address of the user. This is required for many integrations.
    - **Is active**: Define the newly created user account as active.
    - **Attributes**: You can leave this empty for this tutorial. This field can be used to store custom attributes for the user, in YAML or JSON format. These attributes can then be used within property mappings and policies.

    **C.** Click **Create**.

### 2. Verify that the new user was created

- Look for the new user in the list on the **Directory** > **Users** page.

## What's next?

Now that you have added your first application, and a new user, here are some typical next steps:

- Assign your new user to appropriate [groups](../../users-sources/user/user_basic_operations.md#add-a-user-to-a-group) and [roles](../../users-sources/user/user_basic_operations.md#add-a-user-to-a-role).
- Configure federated or external [sources](../../users-sources/sources/index.md) (an existing source of user credentials and other user data).
- Set up MFA
- Define [property mappings](../../add-secure-apps/providers/property-mappings/index.md).
- Create a [custom flow](../../add-secure-apps/flows-stages/flow/index.md#).
- Install an [Enterprise license](../../enterprise/manage-enterprise.mdx#purchase-a-license)
- [Create a policy](../../customize/policies/index.md) to control access, force MFA use, etc..

## Things to know and troubleshooting tips

Review the following information to learn more about the basics of setting up authentik and for troubleshooting tips.

### Modifying the Docker Compose file

Especially when you are just starting out with authentik, we recommend that you use the default `docker-compose.yml` file that comes with the download, instead of trying to write the file from scratch. After you have successfully installed, configured, and accessed authentik, you can edit the file to do more advanced configurations, as documented in the [Configuration section](../../install-config/configuration/configuration.mdx).

### Reverse proxy

Typically authentik is set up with a reverse proxy in front of it. If you already have a reverse proxy that you are using to handle your incoming network traffic, you can simply use that same reverse proxy for authentik, by adding a few configuration values. For more details see the [Reverse proxy guide](../reverse-proxy.md).

### The `latest` tag is deprecated

The `:latest` tag has been deprecated and will never be updated from the 2025.2 release.
Instead, use a specific version tag for authentik instances' container images, such as `:2025.12`.

### Using bindings to allow or restrict access to applications

Note that if you do not define any [bindings](../../add-secure-apps/bindings-overview/index.md), then all users have access to the application. To control access, you can [create a binding](../../add-secure-apps/bindings-overview/work-with-bindings.md). For more information about user access, refer to our documentation about [authorization](../../add-secure-apps/applications/manage_apps.mdx#policy-driven-authorization) and [hiding an application](../../add-secure-apps/applications/manage_apps.mdx#hide-applications).

### Upgrades

When you are ready to upgrade to the latest version, be sure to read our [Upgrade documentation](../upgrade.mdx) and refer to the [Release Notes](../../releases/) for the specific version.



================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/install-config/first-steps/_blurb_first_steps.mdx
================================================================================

You are now ready to add your first application and its provider. Then you'll want to add a new user.

To view a typical workflow for adding applications and users, with helpful context and explanations for each step, refer to the [First Steps](./index.mdx) tutorial.




================================================================================
SOURCE: src/extraction/local-docs/authentik/website/docs/install-config/configuration/configuration.mdx
================================================================================

---
title: Configuration
---

This page details all the authentik configuration options that you can set via environment variables.

## About authentik configurations

:::info
The double-underscores are intentional, as all these settings are translated to YAML internally, and a double-underscore indicates the next level (a subsetting).
:::

All of these variables can be set to values, but you can also use a URI-like format to load values from other places:

- `env://<name>` Loads the value from the environment variable `<name>`. Fallback can be optionally set like `env://<name>?<default>`
- `file://<name>` Loads the value from the file `<name>`. Fallback can be optionally set like `file://<name>?<default>`

## Set your environment variables




## Verify your configuration settings

To check if your config has been applied correctly, you can run the following command to output the full config:



## PostgreSQL Settings

authentik requires a PostgreSQL database to store its configuration and data. Below are the settings to configure the database connection.

### Connection settings

- `AUTHENTIK_POSTGRESQL__HOST`: Hostname or IP address of your PostgreSQL server.
- `AUTHENTIK_POSTGRESQL__PORT`: Port on which PostgreSQL is listening. Defaults to the standard PostgreSQL port `5432`.
- `AUTHENTIK_POSTGRESQL__USER`: Username that authentik will use to authenticate with PostgreSQL.
- `AUTHENTIK_POSTGRESQL__PASSWORD`: Password for PostgreSQL authentication. If not set, it defaults to the value of the `POSTGRES_PASSWORD` environment variable (this fallback is specific to the default Docker Compose setup).
- `AUTHENTIK_POSTGRESQL__NAME`: The name of the database for authentik to use.

:::info Hot-reloading
The `AUTHENTIK_POSTGRESQL__HOST`, `AUTHENTIK_POSTGRESQL__PORT`, `AUTHENTIK_POSTGRESQL__USER`, and `AUTHENTIK_POSTGRESQL__PASSWORD` settings support hot-reloading and can be changed without restarting authentik. However, adding or removing read replicas requires a restart.
:::

### SSL/TLS settings

Configure SSL/TLS to secure the connection to your PostgreSQL server.

- `AUTHENTIK_POSTGRESQL__SSLMODE`: Controls the SSL verification mode. Defaults to `verify-ca`.
    - `disable`: No SSL is used.
    - `allow`: Use SSL if available, but don't perform verification.
    - `prefer`: Attempt an SSL connection first, fall back to non-SSL if it fails.
    - `require`: Require an SSL connection, but without certificate verification.
    - `verify-ca`: Require SSL and verify that the server certificate is signed by a trusted CA.
    - `verify-full`: Require SSL, verify the CA, and verify that the server hostname matches the certificate.

- `AUTHENTIK_POSTGRESQL__SSLROOTCERT`: Path to the CA certificate file for verifying the server's certificate. Required for `verify-ca` and `verify-full` modes.

- `AUTHENTIK_POSTGRESQL__SSLCERT`: Path to the client SSL certificate file. Required if the PostgreSQL server is configured for mutual TLS and requires client certificates.

- `AUTHENTIK_POSTGRESQL__SSLKEY`: Path to the private key for the client certificate (`SSLCERT`).

For more details, see [Django's PostgreSQL documentation](https://docs.djangoproject.com/en/stable/ref/databases/#postgresql-connection-settings) or the [PostgreSQL documentation](https://www.postgresql.org/docs/current/libpq-ssl.html#LIBPQ-SSL-PROTECTION).

### Connection management

These settings control connection persistence and behavior, which is particularly important when using a connection pooler like PgBouncer.

- `AUTHENTIK_POSTGRESQL__CONN_MAX_AGE`: The maximum age of a database connection in seconds.
    - `0` (default): Connections are closed after each request.
    - greater than `0`: Enables persistent connections, with the value defining the maximum lifetime.
    - `None`: Unlimited persistence. Use with caution, especially with connection poolers.
      See [Django's documentation on persistent connections](https://docs.djangoproject.com/en/stable/ref/databases/#persistent-connections) for more details.

- `AUTHENTIK_POSTGRESQL__CONN_HEALTH_CHECKS`: Enables health checks on persistent connections before reuse. Defaults to `false`. This helps prevent errors from stale connections that may have been terminated by the database or a pooler. See [Django's documentation](https://docs.djangoproject.com/en/stable/ref/settings/#conn-health-checks) for details.

- `AUTHENTIK_POSTGRESQL__DISABLE_SERVER_SIDE_CURSORS`: Disables server-side cursors. Defaults to `false`. Server-side cursors can improve performance for large result sets but are incompatible with connection poolers in transaction pooling mode (like PgBouncer). **Set this to `true` if you use a transaction-based pooler or encounter cursor-related errors.** See [Django's documentation](https://docs.djangoproject.com/en/stable/ref/databases/#transaction-pooling-and-server-side-cursors) for more details.

### Advanced Settings

- `AUTHENTIK_POSTGRESQL__DEFAULT_SCHEMA`

    The name of the database schema for authentik to use. Defaults to `public`.

    This can only be set before authentik is started for the first time. If you specify a custom schema, it must already exist in the database, and the user that authentik connects with must have permissions to access it. The `search_path` for the database user must also be configured to include this schema.

- `AUTHENTIK_POSTGRESQL__CONN_OPTIONS`

    Arbitrary `libpq` parameter keywords for the database connection. A list of parameter keywords can be found [in the PostgreSQL documentation](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-PARAMKEYWORDS).
    - Parameters passed with this setting will override those passed with other settings.
    - These parameters are not applied to read replicas.
    - Parameter keywords should be formatted as a base64-encoded JSON dictionary.

### Read Replicas

You can configure additional read replica databases to distribute database load and improve performance. When read replicas are configured, authentik automatically routes query operations between the primary database (for writes) and read replica databases (for queries). By default, the primary database won't be used for queries when read replicas are available. If you want the primary database to also handle queries, add it as a read replica.

To configure authentik to use read replicas, add the settings below to your [configuration file](./configuration.mdx#set-your-environment-variables). If you have multiple read replicas, add settings for each one by using a unique index starting from `0` (e.g., `0`, `1`, `2`, etc.).

The same PostgreSQL settings as described above are used for each read replica. For example, for the first read replica (index `0`):

- `AUTHENTIK_POSTGRESQL__READ_REPLICAS__0__HOST`
- `AUTHENTIK_POSTGRESQL__READ_REPLICAS__0__NAME`
- `AUTHENTIK_POSTGRESQL__READ_REPLICAS__0__USER`
- `AUTHENTIK_POSTGRESQL__READ_REPLICAS__0__PORT`
- `AUTHENTIK_POSTGRESQL__READ_REPLICAS__0__PASSWORD`
- `AUTHENTIK_POSTGRESQL__READ_REPLICAS__0__SSLMODE`
- `AUTHENTIK_POSTGRESQL__READ_REPLICAS__0__SSLROOTCERT`
- `AUTHENTIK_POSTGRESQL__READ_REPLICAS__0__SSLCERT`
- `AUTHENTIK_POSTGRESQL__READ_REPLICAS__0__SSLKEY`
- `AUTHENTIK_POSTGRESQL__READ_REPLICAS__0__CONN_MAX_AGE`
- `AUTHENTIK_POSTGRESQL__READ_REPLICAS__0__CONN_HEALTH_CHECKS`
- `AUTHENTIK_POSTGRESQL__READ_REPLICAS__0__DISABLE_SERVER_SIDE_CURSORS`
- `AUTHENTIK_POSTGRESQL__READ_REPLICAS__0__CONN_OPTIONS`

Additionally, you can set arbitrary connection parameters on all read replicas with:

- `AUTHENTIK_POSTGRESQL__REPLICA_CONN_OPTIONS`

    Arbitrary `libpq` parameter keywords for all read replicas database connections. A list of options can be found [in the PostgreSQL documentation](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-PARAMKEYWORDS).
    - Parameters passed with this setting will override those passed with other settings.
    - Parameter keywords should be formatted as a base64-encoded JSON dictionary.

### Using a PostgreSQL Connection Pooler

When your PostgreSQL databases are running behind a connection pooler (like PgBouncer or PgPool), you need to adjust several settings to ensure compatibility:

- `AUTHENTIK_POSTGRESQL__CONN_MAX_AGE`:

    A connection pooler running in session pool mode (which is the default for PgBouncer) can be incompatible with unlimited persistent connections (`null` setting). When the connection from the pooler to the database is dropped, the pooler will wait for the client to disconnect before releasing the connection. However, this will _never_ happen as authentik keeps the connection indefinitely.

    To address this incompatibility, either configure the connection pooler to run in transaction pool mode or set this value lower than any timeout that might cause the connection to be dropped (down to `0` to disable persistent connections).

- `AUTHENTIK_POSTGRESQL__DISABLE_SERVER_SIDE_CURSORS`:

    When using a connection pooler in transaction pool mode (e.g., PgPool, or PgBouncer in transaction or statement pool mode), you must set this option to `true`. This is required because server-side cursors maintain state across multiple queries, which is incompatible with transaction-based pooling where connections may change between queries.

### Deprecated Settings

- `AUTHENTIK_POSTGRESQL__USE_PGBOUNCER`: Adjusts the database configuration to support connections to a PgBouncer connection pooler. This setting is deprecated and will be removed in a future version. Instead, use the configuration described in the [Using a PostgreSQL Connection Pooler](#using-a-postgresql-connection-pooler) section.
- `AUTHENTIK_POSTGRESQL__USE_PGPOOL`: Adjusts the database configuration to support connections to a Pgpool connection pooler. This setting is deprecated and will be removed in a future version. Instead, use the configuration described in the [Using a PostgreSQL Connection Pooler](#using-a-postgresql-connection-pooler) section.

## Cache Settings

- `AUTHENTIK_CACHE__TIMEOUT`: Timeout for cached data until it expires in seconds, defaults to 300
- `AUTHENTIK_CACHE__TIMEOUT_FLOWS`: Timeout for cached flow plans until they expire in seconds, defaults to 300
- `AUTHENTIK_CACHE__TIMEOUT_POLICIES`: Timeout for cached policies until they expire in seconds, defaults to 300

## Worker settings

##### `AUTHENTIK_WORKER__PROCESSES`

Configure how many worker processes should be started for Dramatiq to use. In environments where scaling with multiple replicas of the authentik worker is not possible, this number can be increased to handle higher loads.

Defaults to 1. In environments where scaling with multiple replicas of the authentik worker is not possible, this number can be increased to handle higher loads.

##### `AUTHENTIK_WORKER__THREADS`

Configure how many Dramatiq threads are started per worker. In environments where scaling with multiple replicas of the authentik worker is not possible, this number can be increased to handle higher loads.

Defaults to 2. A value below 2 threads is not recommended, unless you have multiple worker replicas.

##### `AUTHENTIK_WORKER__CONSUMER_LISTEN_TIMEOUT`

Configure how long a worker waits for a PostgreSQL `LISTEN` notification.

Defaults to `seconds=30`.

##### `AUTHENTIK_WORKER__TASK_MAX_RETRIES`

Configure how many times a failing task will be retried before abandoning.

Defaults to 5.

##### `AUTHENTIK_WORKER__TASK_DEFAULT_TIME_LIMIT`

Configure the default duration a task can run for before it is aborted. Some tasks will override this setting based on other settings, such as LDAP source synchronization tasks.

Defaults to `minutes=10`.

##### `AUTHENTIK_WORKER__TASK_PURGE_INTERVAL`

Configure the interval at which old tasks are cleaned up.

Defaults to `days=1`.

##### `AUTHENTIK_WORKER__TASK_EXPIRATION`

Configure how long tasks are kept in the database before they are deleted.

Defaults to `days=30`.

##### `AUTHENTIK_WORKER__SCHEDULER_INTERVAL`

Configure how often the task scheduler runs.

Defaults to `seconds=60`.

## Listen Settings

##### `AUTHENTIK_LISTEN__HTTP`

List of comma-separated `address:port` values for HTTP.

Applies to the Server, the Worker, and Proxy outposts.

Defaults to `[::]:9000`.

##### `AUTHENTIK_LISTEN__HTTPS`

List of comma-separated `address:port` values for HTTPS.

Applies to the Server and Proxy outposts.

Defaults to `[::]:9443`.

##### `AUTHENTIK_LISTEN__LDAP`

List of comma-separated `address:port` values for LDAP.

Applies to LDAP outposts.

Defaults to `[::]:3389`.

##### `AUTHENTIK_LISTEN__LDAPS`

List of comma-separated `address:port` values for LDAPS.

Applies to LDAP outposts.

Defaults to `[::]:6636`.

##### `AUTHENTIK_LISTEN__METRICS`

List of comma-separated `address:port` values for Prometheus metrics.

Applies to all.

Defaults to `[::]:9300`.

##### `AUTHENTIK_LISTEN__DEBUG`

Listening address:port for Go Debugging metrics.

Applies to all, except the worker.

Defaults to `0.0.0.0:9900`.

##### `AUTHENTIK_LISTEN__DEBUG_PY`

Listening address:port for Python debugging server, see [Debugging](../../developer-docs/setup/debugging.md).

Applies to the Server and the Worker.

Defaults to `0.0.0.0:9901`.

##### `AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS`

List of comma-separated CIDRs that proxy headers should be accepted from.

Applies to the Server.

Requests directly coming from one an address within a CIDR specified here are able to set proxy headers, such as `X-Forwarded-For`. Requests coming from other addresses will not be able to set these headers.

Defaults to `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `fe80::/10`, `::1/128`.

## Storage settings

These settings affect where files are stored. By default, they are stored on disk in the `/data` directory of the authentik container. S3 storage is also supported.

#### `AUTHENTIK_STORAGE__BACKEND`

This parameter defines where to store files. Valid values are `file` and `s3`. For `file` storage, files are stored in a `/data` directory in the container. For `s3`, see below.

Defaults to `file`.

### File storage backend settings

#### `AUTHENTIK_STORAGE__FILE__PATH`

Where to store files on disk.

Defaults to `/data`.

#### `AUTHENTIK_STORAGE__FILE__URL_EXPIRY`

How long generated URLs for file access are valid for.

Defaults to `minutes=15`.

### S3 storage backend settings

For more information on S3 storage, see [S3 storage setup](../../sys-mgmt/ops/storage-s3.md).

#### `AUTHENTIK_STORAGE__S3__REGION`

S3 region where the bucket has been created. May be omitted depending on which S3 provider you use.

Defaults to not set.

#### `AUTHENTIK_STORAGE__S3__ENDPOINT`

Endpoint to use to talk to the S3 storage provider. Overrides the previous region and use_ssl settings.

Must be a valid URL in the form of `https://s3.provider`.

Defaults to not set.

#### `AUTHENTIK_STORAGE__S3__USE_SSL`

Whether to use HTTPS when talking to the S3 storage providers.

Defaults to `true`.

#### `AUTHENTIK_STORAGE__S3__ADDRESSING_STYLE`

Configure the addressing style used to address a bucket.

Valid values are `auto` and `path`.

Defaults to `auto`.

#### `AUTHENTIK_STORAGE__S3__SIGNATURE_VERSION`

Configure the signing method used for S3 requests.

Defaults to `s3v4`.

Set to `s3` for legacy S3-compatible providers that do not support signature v4.

#### `AUTHENTIK_STORAGE__S3__SESSION_PROFILE`

Profile to use when using AWS SDK authentication.

Supports hot-reloading.

Defaults to not set.

#### `AUTHENTIK_STORAGE__S3__ACCESS_KEY`

Access key to authenticate to S3. May be omitted if using AWS SDK authentication.

Supports hot-reloading.

Defaults to not set.

#### `AUTHENTIK_STORAGE__S3__SECRET_KEY`

Secret key to authenticate to S3. May be omitted if using AWS SDK authentication.

Supports hot-reloading.

Defaults to not set.

#### `AUTHENTIK_STORAGE__S3__SECURITY_TOKEN`

Security token to authenticate to S3. May be omitted.

Supports hot-reloading.

Defaults to not set.

#### `AUTHENTIK_STORAGE__S3__BUCKET_NAME`

Name of the bucket to use to store files.

#### `AUTHENTIK_STORAGE__S3__CUSTOM_DOMAIN`

Domain to use to create URLs for users. Mainly useful for non-AWS providers.

May include a port. Must include the bucket.

Example: `s3.company:8080/authentik-data`.

Defaults to not set.

#### `AUTHENTIK_STORAGE__S3__SECURE_URLS`

Whether URLs created use HTTPS or HTTP.

Defaults to `true`.

#### `AUTHENTIK_STORAGE__S3__URL_EXPIRY`

How long generated URLs for file access are valid for.

Defaults to `minutes=15`.

### Media storage settings

These settings affect where media files are stored. Those files include applications and sources icons.

#### `AUTHENTIK_STORAGE__MEDIA__BACKEND`

Overrides [`AUTHENTIK_STORAGE__BACKEND`](#authentik_storage__backend)

#### `AUTHENTIK_STORAGE__MEDIA__FILE__[...]`

Overrides [`AUTHENTIK_STORAGE__FILE__[...]`](#file-storage-backend-settings) settings.

#### `AUTHENTIK_STORAGE__MEDIA__S3__[...]`

Overrides [`AUTHENTIK_STORAGE__S3__[...]`](#s3-storage-backend-settings) settings.

These settings affect where media files are stored. Those files include applications and sources icons. By default, they use the same storage settings as the main storage configuration. S3 storage is also supported.

### Reports storage settings

These settings affect where CSV reports are stored.

#### `AUTHENTIK_STORAGE__REPORTS__BACKEND`

Overrides [`AUTHENTIK_STORAGE__BACKEND`](#authentik_storage__backend)

#### `AUTHENTIK_STORAGE__REPORTS__FILE__[...]`

Overrides [`AUTHENTIK_STORAGE__FILE__[...]`](#file-storage-backend-settings) settings.

#### `AUTHENTIK_STORAGE__REPORTS__S3__[...]`

Overrides [`AUTHENTIK_STORAGE__S3__[...]`](#s3-storage-backend-settings) settings.

## authentik Settings

### `AUTHENTIK_SECRET_KEY`

Secret key used for cookie signing. Changing this will invalidate active sessions.

:::caution
Prior to 2023.6.0 the secret key was also used for unique user IDs. When running a pre-2023.6.0 version of authentik the key should _not_ be changed after the first install.
:::

### `AUTHENTIK_LOG_LEVEL`

Log level for the server and worker containers. Possible values: `debug`, `info`, `warning`, `error`.

Starting with 2021.12.3, you can also set the log level to `trace`. This has no effect on the core authentik server, but shows additional messages for the embedded outpost.

:::danger
Setting the log level to `trace` will include sensitive details in logs, so it shouldn't be used in most cases.

Logs generated with `trace` should be treated with care as they can give others access to your instance, and can potentially include things like session cookies to authentik **and other pages**.
:::

Defaults to `info`.

### `AUTHENTIK_COOKIE_DOMAIN`

Which domain the session cookie should be set to. By default, the cookie is set to the domain authentik is accessed under.

### `AUTHENTIK_EVENTS__CONTEXT_PROCESSORS__GEOIP`

Path to the GeoIP City database. Defaults to `/geoip/GeoLite2-City.mmdb`. If the file is not found, authentik will skip GeoIP support.

### `AUTHENTIK_EVENTS__CONTEXT_PROCESSORS__ASN`

Path to the GeoIP ASN database. Defaults to `/geoip/GeoLite2-ASN.mmdb`. If the file is not found, authentik will skip GeoIP support.

### `AUTHENTIK_DISABLE_UPDATE_CHECK`

Disable the inbuilt update-checker. Defaults to `false`.

### `AUTHENTIK_ERROR_REPORTING`

- `AUTHENTIK_ERROR_REPORTING__ENABLED`

    Enable error reporting. Defaults to `false`.

    Error reports are sent to https://sentry.io and are used for debugging and general feedback. Anonymous performance data is also sent.

- `AUTHENTIK_ERROR_REPORTING__SENTRY_DSN`

    Sets the DSN for the Sentry API endpoint.

    When error reporting is enabled, the default Sentry DSN will allow the authentik developers to receive error reports and anonymous performance data, which is used for general feedback about authentik, and in some cases, may be used for debugging purposes.

    Users can create their own hosted Sentry account (or self-host Sentry) and opt to collect this data themselves.

- `AUTHENTIK_ERROR_REPORTING__ENVIRONMENT`

    The environment tag associated with all data sent to Sentry. Defaults to `customer`.

    When error reporting has been enabled to aid in debugging issues, this should be set to a unique value, such as an email address.

- `AUTHENTIK_ERROR_REPORTING__SEND_PII`

    Whether or not to send personal data, like usernames. Defaults to `false`.

- `AUTHENTIK_ERROR_REPORTING__EXTRA_ARGS`

    Base64-encoded sentry_init arguments. See [Sentry's documentation](https://docs.sentry.io/platforms/python/configuration/options/) for available options.

### `AUTHENTIK_EMAIL`

- `AUTHENTIK_EMAIL__HOST`

    Default: `localhost`

- `AUTHENTIK_EMAIL__PORT`

    Default: `25`

- `AUTHENTIK_EMAIL__USERNAME`

    Default: `` (Don't add quotation marks)

- `AUTHENTIK_EMAIL__PASSWORD`

    Default: `` (Don't add quotation marks)

- `AUTHENTIK_EMAIL__USE_TLS`

    Default: `false`

- `AUTHENTIK_EMAIL__USE_SSL`

    Default: `false`

- `AUTHENTIK_EMAIL__TIMEOUT`

    Default: `10`

- `AUTHENTIK_EMAIL__FROM`

    Default: `authentik@localhost`

    Email address authentik will send from, should have a correct @domain

    To change the sender's display name, use a format like `Name <account@domain>`.

### `AUTHENTIK_OUTPOSTS`

- `AUTHENTIK_OUTPOSTS__CONTAINER_IMAGE_BASE`

    Placeholders:
    - `%(type)s`: Outpost type; proxy, ldap, etc
    - `%(version)s`: Current version; 2021.4.1
    - `%(build_hash)s`: Build hash if you're running a beta version

    Placeholder for outpost docker images. Default: `ghcr.io/goauthentik/%(type)s:%(version)s`.

- `AUTHENTIK_OUTPOSTS__DISCOVER`

    Configure the automatic discovery of integrations. Defaults to `true`.

    By default, the following is discovered:
    - Kubernetes in-cluster config
    - Kubeconfig
    - Existence of a docker socket

### `AUTHENTIK_LDAP__TASK_TIMEOUT_HOURS`

Timeout in hours for LDAP synchronization tasks.

Defaults to `2`.

### `AUTHENTIK_LDAP__PAGE_SIZE`

Page size for LDAP synchronization. Controls the number of objects created in a single task.

Defaults to `50`.

### `AUTHENTIK_LDAP__TLS__CIPHERS`

Allows configuration of TLS Ciphers for LDAP connections used by LDAP sources. Setting applies to all sources.

Defaults to `null`.

### `AUTHENTIK_REPUTATION__EXPIRY`

Configure how long reputation scores should be saved for in seconds.

Defaults to `86400`.

### `AUTHENTIK_SESSION_STORAGE`

:::info Deprecated
This setting is removed as of version 2025.4. Sessions are now exclusively stored in the database. See our [2025.4 release notes](../../releases/2025.4#sessions-are-now-stored-in-the-database) for more information.
:::

If you are running a version earlier than 2025.4, you can configure if the sessions are stored in the cache or the database. Defaults to `cache`. Allowed values are `cache` and `db`. Note that changing this value will invalidate all previous sessions.

### `AUTHENTIK_SESSIONS__UNAUTHENTICATED_AGE`:ak-version[2025.4]

Configure how long unauthenticated sessions last for. Does not impact how long authenticated sessions are valid for. See the [user login stage](../../add-secure-apps/flows-stages/stages/user_login/index.md) for session validity.

Defaults to `days=1`.

### `AUTHENTIK_WEB__WORKERS`

Configure how many gunicorn worker processes should be started (see https://docs.gunicorn.org/en/stable/design.html).

Defaults to 2. A value below 2 workers is not recommended. In environments where scaling with multiple replicas of the authentik server is not possible, this number can be increased to handle higher loads.

### `AUTHENTIK_WEB__THREADS`

Configure how many gunicorn threads a worker processes should have (see https://docs.gunicorn.org/en/stable/design.html).

Defaults to 4.

### `AUTHENTIK_WEB__MAX_REQUESTS`

The maximum number of requests a worker will process before restarting. If this is set to zero then the automatic worker restarts are disabled (see https://gunicorn.org/reference/settings/#max_requests).

Defaults to 1000.

### `AUTHENTIK_WEB__MAX_REQUESTS_JITTER`

The maximum jitter to add to the `AUTHENTIK_WEB__MAX_REQUESTS` setting (see https://gunicorn.org/reference/settings/#max_requests_jitter).

Defaults to 50.

### `AUTHENTIK_WEB__PATH`

Configure the path under which authentik is served. For example to access authentik under `https://my.domain/authentik/`, set this to `/authentik/`. Value _must_ contain both a leading and trailing slash.

Defaults to `/`.

### `AUTHENTIK_WEB__TIMEOUT_HTTP`

Configure the timeouts for the web HTTP/HTTPS Server. Accepts duration in the format of "300ms", "-1.5h" or "2h45m". Valid time units are "ns", "us" (or "µs"), "ms", "s", "m", "h".

- `AUTHENTIK_WEB__TIMEOUT_HTTP_READ_HEADER`

Defaults to `5s`

- `AUTHENTIK_WEB__TIMEOUT_HTTP_READ`

Defaults to `30s`

- `AUTHENTIK_WEB__TIMEOUT_HTTP_WRITE`

Defaults to `60s`

- `AUTHENTIK_WEB__TIMEOUT_HTTP_IDLE`

Defaults to `120s`

## Advanced settings

##### `AUTHENTIK_SKIP_MIGRATIONS`

Whether to skip running migrations on starting authentik. This is destined to advanced setups and not recommended in normal use.

Defaults to `false`.

## System settings

Additional [system settings](../../sys-mgmt/settings.md) are configurable using the Admin interface, under **System** > **Settings** or using the API.

## Custom python settings

To modify additional settings further than the options above allow, you can create a custom Python file and mount it to `/data/user_settings.py`. This file will be loaded on startup by both the server and the worker. All default settings are [here](https://github.com/goauthentik/authentik/blob/main/authentik/root/settings.py)

:::caution
Using these custom settings is not supported and can prevent your authentik instance from starting. Use with caution.
:::
