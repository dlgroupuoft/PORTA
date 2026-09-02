"""Vault platform adapter — raw HTTP API."""

from __future__ import annotations

import logging
from datetime import datetime

import requests

from src.adapters.base import BrokerAdapter
from src.models.types import AuthResult, Credential, Platform, Protocol

log = logging.getLogger(__name__)


class VaultAdapter(BrokerAdapter):
    """Adapter for HashiCorp Vault using its HTTP API directly."""

    def __init__(self, *args, config: dict | None = None, **kwargs):
        # Accept VaultAdapter(config) or VaultAdapter(Platform.VAULT, config)
        if args and isinstance(args[-1], dict):
            config = args[-1]
        config = config or kwargs or {}
        super().__init__(Platform.VAULT, config)
        self.base_url = config.get("base_url", "http://localhost:8200")
        self.admin_token = config.get("admin_token", "root")
        self.jwt_mount = config.get("auth_mount_path", "jwt")
        self.session = requests.Session()
        self.session.headers.update({"X-Vault-Token": self.admin_token})

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def setup(self) -> None:
        if not self.health_check():
            raise ConnectionError(f"Vault is not reachable at {self.base_url}")
        log.info("Vault adapter connected to %s", self.base_url)

    def health_check(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/v1/sys/health", timeout=5)
            return r.status_code in (200, 429, 472, 473)
        except requests.RequestException:
            return False

    # ------------------------------------------------------------------
    # Auth method configuration
    # ------------------------------------------------------------------

    def configure_auth_method(self, protocol: Protocol, auth_config: dict) -> None:
        if protocol == Protocol.JWT:
            self._configure_jwt(auth_config)
        elif protocol == Protocol.OAUTH2_CODE:
            self._configure_oidc(auth_config)
        elif protocol == Protocol.LDAP:
            self._configure_ldap(auth_config)
        else:
            raise ValueError(f"Vault does not support protocol {protocol}")

    def _enable_auth(self, path: str, auth_type: str) -> None:
        """Enable an auth method, ignoring 'already enabled' errors."""
        r = self.session.post(
            f"{self.base_url}/v1/sys/auth/{path}",
            json={"type": auth_type},
        )
        if r.status_code not in (200, 204):
            if "already in use" not in r.text:
                r.raise_for_status()

    # --- JWT ---

    def _configure_jwt(self, cfg: dict) -> None:
        self._enable_auth("jwt", "jwt")

        config_payload: dict = {}
        for key in ("oidc_discovery_url", "jwks_url", "jwt_validation_pubkeys",
                     "bound_issuer"):
            if key in cfg:
                config_payload[key] = cfg[key]
        if config_payload:
            self.session.post(
                f"{self.base_url}/v1/auth/jwt/config",
                json=config_payload,
            ).raise_for_status()

        role_name = cfg.get("role_name", "test-role")
        role_payload = {
            "role_type": "jwt",
            "bound_audiences": cfg.get("bound_audiences", []),
            "user_claim": cfg.get("user_claim", "sub"),
            "groups_claim": cfg.get("groups_claim", ""),
            "token_policies": cfg.get("token_policies", ["default"]),
            "token_ttl": cfg.get("token_ttl", "1h"),
        }
        if "bound_claims" in cfg:
            role_payload["bound_claims"] = cfg["bound_claims"]
        self.session.post(
            f"{self.base_url}/v1/auth/jwt/role/{role_name}",
            json=role_payload,
        ).raise_for_status()

    # --- OIDC ---

    def _configure_oidc(self, cfg: dict) -> None:
        self._enable_auth("oidc", "oidc")

        self.session.post(
            f"{self.base_url}/v1/auth/oidc/config",
            json={
                "oidc_discovery_url": cfg["oidc_discovery_url"],
                "oidc_client_id": cfg["oidc_client_id"],
                "oidc_client_secret": cfg["oidc_client_secret"],
                "default_role": cfg.get("default_role", "test-role"),
            },
        ).raise_for_status()

        role_name = cfg.get("role_name", "test-role")
        self.session.post(
            f"{self.base_url}/v1/auth/oidc/role/{role_name}",
            json={
                "bound_audiences": cfg.get("bound_audiences", []),
                "allowed_redirect_uris": cfg.get("allowed_redirect_uris", []),
                "user_claim": cfg.get("user_claim", "sub"),
                "groups_claim": cfg.get("groups_claim", ""),
                "token_policies": cfg.get("token_policies", ["default"]),
            },
        ).raise_for_status()

    # --- LDAP ---

    def _configure_ldap(self, cfg: dict) -> None:
        self._enable_auth("ldap", "ldap")

        self.session.post(
            f"{self.base_url}/v1/auth/ldap/config",
            json={
                "url": cfg["url"],
                "userdn": cfg.get("userdn", ""),
                "groupdn": cfg.get("groupdn", ""),
                "binddn": cfg.get("binddn", ""),
                "bindpass": cfg.get("bindpass", ""),
                "userattr": cfg.get("userattr", "cn"),
            },
        ).raise_for_status()

        for group, policies in cfg.get("groups", {}).items():
            self.session.post(
                f"{self.base_url}/v1/auth/ldap/groups/{group}",
                json={"policies": policies},
            ).raise_for_status()

    # ------------------------------------------------------------------
    # Authenticate
    # ------------------------------------------------------------------

    def authenticate(self, credential: Credential) -> AuthResult:
        if credential.protocol == Protocol.JWT:
            return self._auth_jwt(credential)
        if credential.protocol == Protocol.OAUTH2_CODE:
            return self._auth_oidc(credential)
        if credential.protocol == Protocol.LDAP:
            return self._auth_ldap(credential)
        return AuthResult(
            success=False,
            platform=Platform.VAULT,
            protocol=credential.protocol,
            error_message=f"Unsupported protocol: {credential.protocol}",
        )

    def _auth_jwt(self, cred: Credential) -> AuthResult:
        role = cred.metadata.get("role", self.config.get("role_name", "test-role"))
        mount = cred.metadata.get("mount", self.jwt_mount)
        r = self.session.post(
            f"{self.base_url}/v1/auth/{mount}/login",
            json={"role": role, "jwt": cred.raw_token},
        )
        return self._parse_auth_response(r, cred)

    def _auth_oidc(self, cred: Credential) -> AuthResult:
        # For fuzzing we hit the callback directly
        r = self.session.post(
            f"{self.base_url}/v1/auth/oidc/oidc/callback",
            json={
                "state": cred.metadata.get("state", ""),
                "code": cred.metadata.get("code", ""),
                "nonce": cred.metadata.get("nonce", ""),
            },
        )
        return self._parse_auth_response(r, cred)

    def _auth_ldap(self, cred: Credential) -> AuthResult:
        username = cred.metadata.get("username", "")
        r = self.session.post(
            f"{self.base_url}/v1/auth/ldap/login/{username}",
            json={"password": cred.raw_token},
        )
        return self._parse_auth_response(r, cred)

    def _parse_auth_response(self, r: requests.Response, cred: Credential) -> AuthResult:
        try:
            body = r.json()
        except ValueError:
            body = {}

        if r.status_code == 200 and body.get("auth"):
            auth_data = body["auth"]
            return AuthResult(
                success=True,
                platform=Platform.VAULT,
                protocol=cred.protocol,
                upstream_credential=cred.to_dict(),
                downstream_token=auth_data.get("client_token", ""),
                downstream_claims={
                    "policies": auth_data.get("policies", []),
                    "metadata": auth_data.get("metadata", {}),
                    "accessor": auth_data.get("accessor", ""),
                    "entity_id": auth_data.get("entity_id", ""),
                },
                http_status=r.status_code,
                raw_response=body,
            )

        errors = body.get("errors", [])
        return AuthResult(
            success=False,
            platform=Platform.VAULT,
            protocol=cred.protocol,
            upstream_credential=cred.to_dict(),
            error_message="; ".join(errors) if errors else r.text,
            http_status=r.status_code,
            raw_response=body,
        )

    # ------------------------------------------------------------------
    # Token metadata
    # ------------------------------------------------------------------

    def get_token_metadata(self, token: str) -> dict:
        r = self.session.post(
            f"{self.base_url}/v1/auth/token/lookup",
            json={"token": token},
        )
        if r.status_code == 200:
            return r.json().get("data", {})
        return {"error": r.text, "status": r.status_code}

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def reset_state(self) -> None:
        self.session.post(
            f"{self.base_url}/v1/sys/leases/revoke-prefix/auth/",
        )

    def get_server_logs(self, since: datetime) -> list[str]:
        try:
            import docker as docker_lib
            client = docker_lib.from_env()
            for c in client.containers.list():
                if "vault" in c.name.lower():
                    return c.logs(since=since).decode(errors="replace").splitlines()
        except Exception:
            pass
        return []

    # ------------------------------------------------------------------
    # Supported protocols
    # ------------------------------------------------------------------

    @property
    def supported_protocols(self) -> list[Protocol]:
        return [Protocol.JWT, Protocol.OAUTH2_CODE, Protocol.LDAP]
