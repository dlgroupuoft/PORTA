"""Pre-campaign platform initialization.

Handles platform-specific setup that must run before test sequences execute:
- Cookie-based admin session establishment
- Test org/app/provider provisioning (Casdoor)
- Realm creation (Keycloak)
- Future platforms: project/app setup, connector registration, etc.

The initializer is driven by two sources:
1. profile.init_hooks (explicit, config-driven — preferred for new platforms)
2. Hardcoded fallbacks (backward compat for existing Casdoor/KC profiles)
"""
import logging
import uuid
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class PlatformInitializer:
    """Pre-campaign setup per platform.  Called once before sequences run."""

    def __init__(self, profile, base_url: str, session: requests.Session = None,
                 protocol: str = "oidc_jwt"):
        self.profile = profile
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.protocol = protocol
        self._admin_session_established = False
        self._test_org_ensured = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ensure_admin_session(self, force: bool = False):
        """Establish admin session for cookie-auth platforms.

        Uses profile.cookie_login config when available, falls back to
        hardcoded Casdoor defaults for backward compatibility.
        """
        if self._admin_session_established and not force:
            # Verify the session is still valid
            try:
                check = self.session.get(f"{self.base_url}/api/get-account", timeout=5)
                cd = check.json()
                if cd.get("status") == "ok" and isinstance(cd.get("data"), dict):
                    return  # Session still valid
                logger.info("    COOKIE-AUTH: admin session expired, re-establishing")
                self._admin_session_established = False
            except Exception:
                self._admin_session_established = False

        if not (self.profile
                and getattr(self.profile, 'session_auth_method', 'bearer') == 'cookie'):
            return

        # Determine login endpoint
        login_ep = self.profile.get_endpoint("oidc_jwt", "login_with_password")
        if not login_ep:
            login_ep = self.profile.get_endpoint(self.protocol, "login_with_password")
        if not login_ep:
            return

        # Use profile.cookie_login config if present, else Casdoor defaults
        cookie_cfg = getattr(self.profile, 'cookie_login', {}) or {}
        login_path = cookie_cfg.get("path") or login_ep.path
        body = cookie_cfg.get("body") or {
            "type": "login",
            "application": "app-built-in",
            "organization": "built-in",
            "username": "admin",
            "password": "123",
        }

        try:
            url = f"{self.base_url}{login_path}"
            resp = self.session.post(url, json=body, timeout=15)
            if resp.ok:
                data = resp.json()
                success_check = cookie_cfg.get("success_check", "status == ok")
                if success_check == "status == ok":
                    ok = data.get("status") == "ok"
                else:
                    ok = resp.ok
                if ok:
                    self._admin_session_established = True
                    logger.info(
                        f"    COOKIE-AUTH: admin session established for "
                        f"{self.profile.name}"
                    )
                    self.run_init_hooks()
                else:
                    logger.warning(
                        f"    COOKIE-AUTH: admin login returned: "
                        f"{data.get('msg', '')}"
                    )
        except Exception as e:
            logger.error(f"    COOKIE-AUTH: failed to establish admin session: {e}")

    def run_init_hooks(self):
        """Execute init_hooks from profile, then hardcoded fallbacks."""
        init_hooks = getattr(self.profile, 'init_hooks', []) or []

        if init_hooks:
            for hook in init_hooks:
                hook_type = hook.get("type", "")
                try:
                    if hook_type == "ensure_org":
                        self._ensure_org(hook)
                    elif hook_type == "ensure_app":
                        self._ensure_app(hook)
                    elif hook_type == "ensure_saml_provider":
                        self._ensure_saml_provider_hook(hook)
                    elif hook_type == "ensure_realm":
                        self._ensure_realm(hook)
                    else:
                        logger.warning(f"    INIT: unknown hook type '{hook_type}'")
                except Exception as e:
                    logger.error(f"    INIT: hook '{hook_type}' failed: {e}")
        else:
            # Backward compat: run hardcoded Casdoor init when no hooks configured
            if (self.profile
                    and getattr(self.profile, 'session_auth_method', 'bearer') == 'cookie'):
                self._ensure_test_org_compat()

    # ------------------------------------------------------------------
    # Config-driven init hooks (for new platforms)
    # ------------------------------------------------------------------

    def _ensure_org(self, hook: dict):
        """Create an organization if it doesn't exist."""
        name = hook.get("name", "test-org")
        owner = hook.get("owner", "admin")
        r = self.session.get(
            f"{self.base_url}/api/get-organization",
            params={"id": f"{owner}/{name}"}, timeout=10,
        )
        if r.ok and r.json().get("data"):
            return
        org = {"owner": owner, "name": name}
        org.update({k: v for k, v in hook.items() if k not in ("type", "owner", "name")})
        self.session.post(
            f"{self.base_url}/api/add-organization", json=org, timeout=15,
        )
        logger.info(f"    INIT: created org '{name}'")

    def _ensure_app(self, hook: dict):
        """Create an application if it doesn't exist."""
        name = hook.get("name", "app-test")
        owner = hook.get("owner", "admin")
        r = self.session.get(
            f"{self.base_url}/api/get-application",
            params={"id": f"{owner}/{name}"}, timeout=10,
        )
        if r.ok and r.json().get("data"):
            return
        app = {"owner": owner, "name": name}
        app.update({k: v for k, v in hook.items() if k not in ("type",)})
        self.session.post(
            f"{self.base_url}/api/add-application", json=app, timeout=15,
        )
        logger.info(f"    INIT: created app '{name}'")

    def _ensure_saml_provider_hook(self, hook: dict):
        """Create a SAML provider and link to apps."""
        name = hook.get("name", "provider-saml-test")
        owner = hook.get("owner", "admin")
        r = self.session.get(
            f"{self.base_url}/api/get-provider",
            params={"id": f"{owner}/{name}"}, timeout=10,
        )
        if not (r.ok and r.json().get("data")):
            provider = {"owner": owner, "name": name}
            provider.update({k: v for k, v in hook.items()
                             if k not in ("type", "link_to_apps")})
            self.session.post(
                f"{self.base_url}/api/add-provider", json=provider, timeout=15,
            )
            logger.info(f"    INIT: created SAML provider '{name}'")

        for app_name in hook.get("link_to_apps", []):
            self._link_provider_to_app(name, app_name)

    def _ensure_realm(self, hook: dict):
        """Create a Keycloak realm if it doesn't exist (placeholder)."""
        # Keycloak realm creation is handled by existing setup events.
        # This hook is for future use when we want pre-campaign realm setup.
        logger.info(f"    INIT: ensure_realm hook (no-op for now)")

    def _link_provider_to_app(self, provider_name: str, app_name: str):
        """Link a provider to an application."""
        try:
            ar = self.session.get(
                f"{self.base_url}/api/get-application",
                params={"id": f"admin/{app_name}"}, timeout=10,
            )
            if ar.ok and ar.json().get("data"):
                app_data = ar.json()["data"]
                existing = [p.get("name") for p in (app_data.get("providers") or [])]
                if provider_name not in existing:
                    providers = app_data.get("providers") or []
                    providers.append({
                        "name": provider_name,
                        "canSignUp": True, "canSignIn": True, "canUnlink": True,
                    })
                    app_data["providers"] = providers
                    self.session.post(
                        f"{self.base_url}/api/update-application",
                        params={"id": f"admin/{app_name}"},
                        json=app_data, timeout=15,
                    )
                    logger.info(f"    INIT: linked provider '{provider_name}' to '{app_name}'")
        except Exception as e:
            logger.warning(f"    INIT: link provider to app failed: {e}")

    # ------------------------------------------------------------------
    # Backward-compatible hardcoded init (Casdoor)
    # ------------------------------------------------------------------

    def _ensure_test_org_compat(self):
        """Hardcoded Casdoor test-org + app-test + SAML provider setup.

        This is the backward-compat path for existing Casdoor profiles
        that don't have init_hooks configured.
        """
        if self._test_org_ensured:
            return
        try:
            r = self.session.get(
                f"{self.base_url}/api/get-organization",
                params={"id": "admin/test-org"}, timeout=10,
            )
            if r.ok and r.json().get("data"):
                # Org exists — still ensure SAML provider linked + grantTypes intact
                # (LLM update_application events may have cleared providers/grantTypes)
                self._ensure_saml_provider_compat()
                self._ensure_app_test_grants()
                self._test_org_ensured = True
                return

            # Create test-org
            org = {
                "owner": "admin", "name": "test-org",
                "displayName": "VALENCE Test Organization",
                "websiteUrl": "http://test-org.example.com",
                "passwordType": "bcrypt",
                "passwordOptions": ["AtLeast6"],
                "countryCodes": ["US"], "languages": ["en"],
            }
            self.session.post(
                f"{self.base_url}/api/add-organization", json=org, timeout=15,
            )

            # Create app-test for test-org
            app = {
                "owner": "admin", "name": "app-test",
                "displayName": "VALENCE Test Application",
                "organization": "test-org",
                "clientId": "valence_" + uuid.uuid4().hex[:16],
                "clientSecret": "valence_secret_" + uuid.uuid4().hex[:16],
                "redirectUris": ["http://localhost:8000/callback"],
                "grantTypes": ["authorization_code", "password", "urn:ietf:params:oauth:grant-type:token-exchange"],
                "tokenFormat": "JWT", "expireInHours": 168,
                "cert": "cert-built-in", "enablePassword": True,
                "enableSignUp": True, "providers": [],
                "signinMethods": [
                    {"name": "Password", "displayName": "Password", "rule": "All"},
                ],
                "signupItems": [
                    {"name": "ID", "visible": False, "required": True, "rule": "Random"},
                    {"name": "Username", "visible": True, "required": True, "rule": "None"},
                    {"name": "Password", "visible": True, "required": True, "rule": "None"},
                    {"name": "Email", "visible": True, "required": False, "rule": "None"},
                ],
            }
            self.session.post(
                f"{self.base_url}/api/add-application", json=app, timeout=15,
            )

            # Ensure SAML provider
            self._ensure_saml_provider_compat()

            self._test_org_ensured = True
            logger.info("    COOKIE-AUTH: test-org and app-test created for Casdoor")
        except Exception as e:
            logger.error(f"    COOKIE-AUTH: failed to ensure test-org: {e}")

    def _ensure_saml_provider_compat(self):
        """Hardcoded Casdoor SAML provider setup (backward compat).

        Always re-links provider to apps because LLM-generated
        update_application events may overwrite the providers list.
        """
        try:
            r = self.session.get(
                f"{self.base_url}/api/get-provider",
                params={"id": "admin/provider-saml-test"}, timeout=10,
            )
            provider = r.json().get("data") if r.ok else None

            _CANONICAL_ISSUER = "http://fake-idp.valence.local"
            _CANONICAL_SSO = "http://fake-idp.valence.local/saml/sso"
            if not provider:
                provider = {
                    "owner": "admin", "name": "provider-saml-test",
                    "displayName": "Test SAML IdP", "category": "SAML",
                    "type": "Custom",
                    "endpoint": _CANONICAL_SSO,
                    "issuerUrl": _CANONICAL_ISSUER,
                    "userMapping": {
                        "id": "NameID", "username": "username",
                        "email": "email", "displayName": "displayName",
                    },
                }
                self.session.post(
                    f"{self.base_url}/api/add-provider",
                    json=provider, timeout=15,
                )
                logger.info("    SAML: created provider-saml-test")
            elif provider.get("issuerUrl") != _CANONICAL_ISSUER:
                # Update existing provider to canonical issuer
                provider["issuerUrl"] = _CANONICAL_ISSUER
                provider["endpoint"] = _CANONICAL_SSO
                self.session.post(
                    f"{self.base_url}/api/update-provider",
                    params={"id": "admin/provider-saml-test"},
                    json=provider, timeout=15,
                )
                logger.info(f"    SAML: updated provider-saml-test issuer to {_CANONICAL_ISSUER}")

            # Always re-link (not just on creation) because LLM update_application
            # events can overwrite the providers list to empty.
            for app_name in ["app-built-in", "app-test"]:
                self._link_provider_to_app("provider-saml-test", app_name)
        except Exception as e:
            logger.warning(f"    SAML: provider setup failed: {e}")

    def _ensure_app_test_grants(self):
        """Ensure app-test has password + token-exchange grant types.

        LLM-generated update_application events frequently clear grantTypes.
        """
        try:
            r = self.session.get(
                f"{self.base_url}/api/get-application",
                params={"id": "admin/app-test"}, timeout=10,
            )
            if not r.ok:
                return
            app = r.json().get("data")
            if not app or not isinstance(app, dict):
                return
            required = {"authorization_code", "password",
                        "urn:ietf:params:oauth:grant-type:token-exchange"}
            current = set(app.get("grantTypes") or [])
            if not required.issubset(current):
                app["grantTypes"] = list(required | current)
                app["enablePassword"] = True
                self.session.post(
                    f"{self.base_url}/api/update-application",
                    params={"id": "admin/app-test"},
                    json=app, timeout=15,
                )
                logger.info("    INIT: restored app-test grantTypes")
        except Exception as e:
            logger.warning(f"    INIT: app-test grant check failed: {e}")
