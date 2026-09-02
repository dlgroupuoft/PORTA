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