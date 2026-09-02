"""Tests for PlatformProfile data model."""
import json
import tempfile
from pathlib import Path

import pytest

from src.models.platform_profile import APIEndpoint, KnownBehaviorRule, PlatformProfile


class TestAPIEndpoint:
    def test_defaults(self):
        ep = APIEndpoint(method="GET", path="/test")
        assert ep.body_map == {}
        assert ep.response_map == {}
        assert ep.auth == "admin"
        assert ep.headers_map == {}

    def test_full_construction(self):
        ep = APIEndpoint(
            method="POST",
            path="/v1/auth/{mount}/login",
            body_map={"role": "role", "token": "jwt"},
            response_map={"session_token": "auth.client_token"},
            auth="none",
        )
        assert ep.method == "POST"
        assert ep.body_map["role"] == "role"


class TestKnownBehaviorRule:
    def test_defaults(self):
        rule = KnownBehaviorRule(
            id="test_rule",
            description="A test rule",
            invariants=["I4"],
            conditions={"field": "value"},
        )
        assert rule.action == "downgrade_to_informational"
        assert rule.source == ""
        assert rule.note == ""


class TestPlatformProfile:
    def test_from_vault_json(self):
        profile = PlatformProfile.from_json("src/profiles/vault.json")
        assert profile.name == "vault"
        assert profile.base_url == "http://localhost:8200"
        assert "oidc_jwt" in profile.supported_protocols
        assert len(profile.known_behaviors) == 7
        assert len(profile.api_constraints) == 12

    def test_from_keycloak_json(self):
        profile = PlatformProfile.from_json("src/profiles/keycloak.json")
        assert profile.name == "keycloak"
        assert "oidc_jwt" in profile.supported_protocols
        assert "saml" in profile.supported_protocols

    def test_get_endpoint_exists(self):
        profile = PlatformProfile.from_json("src/profiles/vault.json")
        ep = profile.get_endpoint("oidc_jwt", "login_with_jwt")
        assert ep is not None
        assert ep.method == "POST"
        assert ep.path == "/v1/auth/{mount}/login"
        assert ep.auth == "none"

    def test_get_endpoint_missing(self):
        profile = PlatformProfile.from_json("src/profiles/vault.json")
        ep = profile.get_endpoint("oidc_jwt", "nonexistent_op")
        assert ep is None

    def test_get_endpoint_missing_protocol(self):
        profile = PlatformProfile.from_json("src/profiles/vault.json")
        ep = profile.get_endpoint("saml", "login_with_jwt")
        assert ep is None

    def test_api_mapping_parsed(self):
        profile = PlatformProfile.from_json("src/profiles/vault.json")
        jwt_ops = profile.api_mapping.get("oidc_jwt", {})
        assert len(jwt_ops) > 10
        for name, ep in jwt_ops.items():
            assert isinstance(ep, APIEndpoint)

    def test_known_behaviors_parsed(self):
        profile = PlatformProfile.from_json("src/profiles/vault.json")
        rule = profile.known_behaviors[0]
        assert isinstance(rule, KnownBehaviorRule)
        assert rule.id == "vault_empty_bound_claims"
        assert "I5" in rule.invariants

    def test_get_constraints_text(self):
        profile = PlatformProfile.from_json("src/profiles/vault.json")
        text = profile.get_constraints_text()
        assert "bound_claims" in text
        assert text.startswith("- ")

    def test_get_constraints_text_empty(self):
        profile = PlatformProfile(
            name="empty",
            base_url="http://localhost",
            admin_auth={},
            supported_protocols=[],
        )
        assert profile.get_constraints_text() == ""

    def test_from_json_roundtrip(self):
        """Load vault.json, verify all endpoints have valid fields."""
        profile = PlatformProfile.from_json("src/profiles/vault.json")
        login_ep = profile.get_endpoint("oidc_jwt", "login_with_jwt")
        assert "role" in login_ep.body_map
        assert "session_token" in login_ep.response_map

    def test_from_json_custom(self):
        """Test loading from a custom JSON."""
        data = {
            "name": "test-platform",
            "base_url": "http://localhost:9999",
            "admin_auth": {"header": "Auth", "value": "token"},
            "supported_protocols": ["oidc_jwt"],
            "api_mapping": {
                "oidc_jwt": {
                    "login": {
                        "method": "POST",
                        "path": "/login",
                        "body_map": {"user": "username"},
                    }
                }
            },
            "known_behaviors": [
                {
                    "id": "test_rule",
                    "description": "Test",
                    "invariants": ["I1"],
                    "conditions": {"x": "y"},
                }
            ],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            profile = PlatformProfile.from_json(f.name)

        assert profile.name == "test-platform"
        assert len(profile.known_behaviors) == 1
        ep = profile.get_endpoint("oidc_jwt", "login")
        assert ep.method == "POST"

    def test_verification_fields(self):
        profile = PlatformProfile.from_json("src/profiles/vault.json")
        assert profile.verification_fields["identity_field"] == "entity_id"
        assert "policies_field" in profile.verification_fields
