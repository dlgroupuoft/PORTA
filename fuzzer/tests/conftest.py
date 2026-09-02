"""Shared fixtures for VALENCE tests."""

import pytest

from src.utils.jwt_factory import JWTFactory
from src.utils.saml_factory import SAMLFactory
from src.adapters.vault_adapter import VaultAdapter


@pytest.fixture
def jwt_factory():
    return JWTFactory()


@pytest.fixture
def saml_factory():
    return SAMLFactory()


def _service_available(url: str) -> bool:
    import requests
    try:
        r = requests.get(url, timeout=3)
        return r.status_code < 500
    except Exception:
        return False


@pytest.fixture
def vault_adapter():
    adapter = VaultAdapter({"base_url": "http://localhost:8200", "admin_token": "root"})
    return adapter



@pytest.fixture
def mock_idp_url():
    return "http://localhost:9090"


# Markers for integration tests that need Docker services
vault_available = pytest.mark.skipif(
    not _service_available("http://localhost:8200/v1/sys/health"),
    reason="Vault not running",
)

keycloak_available = pytest.mark.skipif(
    not (_service_available("http://localhost:8080/health/ready")
         or _service_available("http://localhost:8080/realms/master/.well-known/openid-configuration")),
    reason="Keycloak not running",
)

dex_available = pytest.mark.skipif(
    not _service_available("http://localhost:5556/dex/healthz"),
    reason="Dex not running",
)
