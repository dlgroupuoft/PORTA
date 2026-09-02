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
