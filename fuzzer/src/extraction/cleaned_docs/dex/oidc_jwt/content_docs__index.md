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
