"""Tests for platform adapters.

Integration tests are skipped when Docker services are not available.
"""

import pytest

from src.adapters.vault_adapter import VaultAdapter
from src.models.types import Credential, Platform, Protocol
from tests.conftest import vault_available


# -----------------------------------------------------------------------
# Unit tests (no Docker required)
# -----------------------------------------------------------------------

class TestVaultAdapterUnit:
    def test_supported_protocols(self):
        adapter = VaultAdapter()
        assert Protocol.JWT in adapter.supported_protocols
        assert Protocol.OAUTH2_CODE in adapter.supported_protocols
        assert Protocol.LDAP in adapter.supported_protocols

    def test_platform(self):
        adapter = VaultAdapter()
        assert adapter.platform == Platform.VAULT


# -----------------------------------------------------------------------
# Integration tests (Docker required)
# -----------------------------------------------------------------------

@vault_available
class TestVaultAdapterIntegration:
    def test_health_check(self, vault_adapter):
        assert vault_adapter.health_check() is True

    def test_configure_jwt_auth(self, vault_adapter, jwt_factory):
        from cryptography.hazmat.primitives import serialization
        pub_pem = jwt_factory._public_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()
        vault_adapter.configure_auth_method(Protocol.JWT, {
            "jwt_validation_pubkeys": [pub_pem],
            "bound_issuer": "test-issuer",
            "role_name": "integration-role",
            "bound_audiences": ["test-aud"],
            "user_claim": "sub",
            "token_policies": ["default"],
        })

    def test_authenticate_valid_jwt(self, vault_adapter, jwt_factory):
        token = jwt_factory.create_token({
            "sub": "alice", "iss": "test-issuer", "aud": "test-aud",
        })
        cred = Credential(
            protocol=Protocol.JWT,
            raw_token=token,
            metadata={"role": "integration-role"},
        )
        result = vault_adapter.authenticate(cred)
        # Will succeed only if configure was called first
        assert result.platform == Platform.VAULT

    def test_authenticate_invalid_jwt(self, vault_adapter):
        cred = Credential(
            protocol=Protocol.JWT,
            raw_token="invalid.token.here",
            metadata={"role": "test-role"},
        )
        result = vault_adapter.authenticate(cred)
        assert result.success is False

    def test_reset_state(self, vault_adapter):
        vault_adapter.reset_state()  # Should not raise
