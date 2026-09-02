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