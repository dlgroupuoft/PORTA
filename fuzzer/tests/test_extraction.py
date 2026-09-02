"""Tests for the API spec extraction pipeline."""
import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# ── Adjust to project root ───────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent


# ── Profile / spec fixtures (use existing hand-written files) ────────────────

class TestVaultProfileLoads:
    def test_vault_profile_loads(self):
        """Hand-written vault profile loads without error."""
        from src.models.platform_profile import PlatformProfile
        profile = PlatformProfile.from_json("src/profiles/vault.json")
        assert profile.name == "vault"

    def test_vault_essential_ops(self):
        """Essential operations exist in the vault profile."""
        from src.models.platform_profile import PlatformProfile
        profile = PlatformProfile.from_json("src/profiles/vault.json")
        jwt_ops = profile.api_mapping.get("oidc_jwt", {})
        assert "login_with_jwt" in jwt_ops, "login_with_jwt missing"
        assert "create_auth_role" in jwt_ops, "create_auth_role missing"
        assert "verify_granted_identity" in jwt_ops, "verify_granted_identity missing"

    def test_vault_login_has_session_token(self):
        """login_with_jwt has session_token in response_map."""
        from src.models.platform_profile import PlatformProfile
        profile = PlatformProfile.from_json("src/profiles/vault.json")
        login_ep = profile.api_mapping["oidc_jwt"]["login_with_jwt"]
        assert login_ep.response_map, "login_with_jwt.response_map is empty"
        assert "session_token" in login_ep.response_map, \
            f"session_token missing from {login_ep.response_map}"

    def test_vault_verify_has_identity_id(self):
        """verify_granted_identity has identity_id in response_map."""
        from src.models.platform_profile import PlatformProfile
        profile = PlatformProfile.from_json("src/profiles/vault.json")
        verify_ep = profile.api_mapping["oidc_jwt"]["verify_granted_identity"]
        assert "identity_id" in verify_ep.response_map, \
            f"identity_id missing from {verify_ep.response_map}"

    def test_vault_known_behaviors_have_conditions(self):
        """All known_behaviors have non-empty id, invariants, and conditions."""
        from src.models.platform_profile import PlatformProfile
        profile = PlatformProfile.from_json("src/profiles/vault.json")
        for kb in profile.known_behaviors:
            assert kb.id, f"known_behavior missing id: {kb}"
            assert kb.invariants, f"known_behavior '{kb.id}' missing invariants"
            assert kb.conditions, f"known_behavior '{kb.id}' missing conditions"

    def test_vault_api_constraints_non_empty(self):
        """Vault profile has api_constraints."""
        from src.models.platform_profile import PlatformProfile
        profile = PlatformProfile.from_json("src/profiles/vault.json")
        assert profile.api_constraints, "api_constraints is empty"


class TestVaultVerificationSpec:
    def test_vault_verification_spec_exists(self):
        """vault_api_spec.json exists."""
        assert Path("src/llm/platform_apis/vault_api_spec.json").exists()

    def test_vault_verification_spec_complete(self):
        """Verification spec has all 5 categories."""
        with open("src/llm/platform_apis/vault_api_spec.json") as f:
            spec = json.load(f)
        for cat in ["identity_lookup", "permission_check", "access_test",
                    "session_token_inspect", "admin_audit"]:
            assert cat in spec["verification_apis"], f"Missing category: {cat}"
            assert len(spec["verification_apis"][cat]) >= 1, \
                f"Category '{cat}' is empty"


class TestValidateProfile:
    def test_validate_vault_passes(self):
        """Full validation passes for existing vault profile."""
        from src.extraction.validate_specs import validate_profile
        errors = validate_profile("vault", "oidc_jwt")
        assert errors == [], f"Validation errors: {errors}"

    def test_validate_missing_platform_fatal(self, tmp_path):
        """Missing profile returns FATAL error."""
        from src.extraction.validate_specs import validate_profile
        errors = validate_profile(
            "vault", "oidc_jwt",
            profile_path=str(tmp_path / "nonexistent.json"),
        )
        assert any("FATAL" in e for e in errors)

    def test_validate_missing_login_op(self, tmp_path):
        """Profile without login_with_jwt reports error."""
        from src.extraction.validate_specs import validate_profile
        # Create a minimal profile without login_with_jwt
        profile = {
            "name": "vault",
            "base_url": "http://localhost:8200",
            "admin_auth": {"header": "X-Vault-Token", "value": "root"},
            "supported_protocols": ["oidc_jwt"],
            "api_mapping": {"oidc_jwt": {
                "create_auth_role": {
                    "method": "POST", "path": "/v1/auth/{mount}/role/{role_name}",
                    "body_map": {}, "response_map": {}, "auth": "admin"
                },
                "verify_granted_identity": {
                    "method": "GET", "path": "/v1/auth/token/lookup-self",
                    "body_map": {}, "response_map": {"identity_id": "data.entity_id"},
                    "auth": "session"
                },
            }},
            "known_behaviors": [],
            "verification_fields": {},
            "api_constraints": ["At least one constraint"],
        }
        profile_path = tmp_path / "vault.json"
        profile_path.write_text(json.dumps(profile))
        spec = {
            "platform": "vault",
            "verification_apis": {
                "identity_lookup": [{"name": "x"}],
                "permission_check": [{"name": "y"}],
                "access_test": [],
                "session_token_inspect": [{"name": "z"}],
                "admin_audit": [],
            }
        }
        spec_path = tmp_path / "vault_api_spec.json"
        spec_path.write_text(json.dumps(spec))

        errors = validate_profile(
            "vault", "oidc_jwt",
            profile_path=str(profile_path),
            spec_path=str(spec_path),
        )
        assert any("login_with_jwt" in e for e in errors)

    def test_validate_login_missing_session_token(self, tmp_path):
        """Login op without session_token in response_map reports error."""
        from src.extraction.validate_specs import validate_profile
        profile = {
            "name": "vault",
            "base_url": "http://localhost:8200",
            "admin_auth": {"header": "X-Vault-Token", "value": "root"},
            "supported_protocols": ["oidc_jwt"],
            "api_mapping": {"oidc_jwt": {
                "login_with_jwt": {
                    "method": "POST", "path": "/v1/auth/{mount}/login",
                    "body_map": {}, "response_map": {},  # ← no session_token
                    "auth": "none"
                },
                "create_auth_role": {
                    "method": "POST", "path": "/v1/auth/{mount}/role/{role_name}",
                    "body_map": {}, "response_map": {}, "auth": "admin"
                },
                "verify_granted_identity": {
                    "method": "GET", "path": "/v1/auth/token/lookup-self",
                    "body_map": {}, "response_map": {"identity_id": "data.entity_id"},
                    "auth": "session"
                },
            }},
            "known_behaviors": [],
            "verification_fields": {},
            "api_constraints": ["constraint"],
        }
        profile_path = tmp_path / "vault.json"
        profile_path.write_text(json.dumps(profile))
        spec = {
            "platform": "vault",
            "verification_apis": {
                "identity_lookup": [{"name": "x"}],
                "permission_check": [{"name": "y"}],
                "access_test": [],
                "session_token_inspect": [{"name": "z"}],
                "admin_audit": [],
            }
        }
        spec_path = tmp_path / "vault_api_spec.json"
        spec_path.write_text(json.dumps(spec))

        errors = validate_profile(
            "vault", "oidc_jwt",
            profile_path=str(profile_path),
            spec_path=str(spec_path),
        )
        assert any("session_token" in e for e in errors)


class TestFetchDocs:
    def test_clean_mdx_strips_jsx(self):
        """clean_mdx strips import/export and JSX tags."""
        from src.extraction.fetch_docs import clean_mdx
        content = """import Something from '@site/thing'
export const Foo = 'bar'
<Tab label="x">
  some content inside
</Tab>

## Real Content

This is regular markdown.
"""
        result = clean_mdx(content)
        assert "import " not in result
        assert "export " not in result
        assert "## Real Content" in result
        assert "regular markdown" in result

    def test_clean_html_strips_tags(self):
        """clean_html removes HTML tags, keeps text."""
        from src.extraction.fetch_docs import clean_html
        html = "<html><body><h1>Title</h1><p>Content here</p></body></html>"
        result = clean_html(html)
        assert "Title" in result
        assert "Content here" in result
        assert "<html>" not in result
        assert "<h1>" not in result

    def test_clean_mdx_keeps_markdown_headers(self):
        """clean_mdx preserves markdown headers and code blocks."""
        from src.extraction.fetch_docs import clean_mdx
        content = """## API Reference

### POST /auth/jwt/login

```json
{"role": "test"}
```
"""
        result = clean_mdx(content)
        assert "## API Reference" in result
        assert "POST /auth/jwt/login" in result

    def test_platform_doc_sources_vault_has_entries(self):
        """PLATFORM_DOC_SOURCES has Vault config defined."""
        from src.extraction.fetch_docs import PLATFORM_DOC_SOURCES
        assert "vault" in PLATFORM_DOC_SOURCES
        assert "oidc_jwt" in PLATFORM_DOC_SOURCES["vault"]
        config = PLATFORM_DOC_SOURCES["vault"]["oidc_jwt"]
        assert len(config.get("github_repos", [])) >= 1
        assert len(config["github_repos"][0]["paths"]) >= 3

    def test_cache_freshness_check(self, tmp_path):
        """Cache freshness check works correctly."""
        from src.extraction.fetch_docs import _is_cache_fresh
        # Non-existent file → not fresh
        assert not _is_cache_fresh(tmp_path / "nonexistent.txt")
        # Just-created file → fresh
        f = tmp_path / "test.txt"
        f.write_text("content")
        assert _is_cache_fresh(f, max_age=3600)
        # Old file → not fresh
        assert not _is_cache_fresh(f, max_age=0)


class TestExtractSpecs:
    def test_split_and_save_creates_files(self, tmp_path):
        """split_and_save produces all expected output files."""
        from src.extraction.extract_specs import split_and_save

        llm_output = {
            "input_operations": [
                {
                    "operation_name": "login_with_jwt",
                    "category": "AUTH_LOGIN",
                    "method": "POST",
                    "path": "/v1/auth/{mount}/login",
                    "path_params": ["mount"],
                    "body_map": {"jwt_token": "jwt", "role_name": "role"},
                    "response_map": {
                        "session_token": "auth.client_token",
                        "identity_id": "auth.entity_id",
                    },
                    "auth": "none",
                    "description": "Authenticate with JWT",
                    "invariant_relevance": ["I1", "I4"],
                    "dependencies": [],
                    "access_control_params": [],
                },
                {
                    "operation_name": "create_auth_role",
                    "category": "AUTH_CONFIG",
                    "method": "POST",
                    "path": "/v1/auth/{mount}/role/{role_name}",
                    "path_params": ["mount", "role_name"],
                    "body_map": {"identity_claim": "user_claim"},
                    "response_map": {},
                    "auth": "admin",
                    "description": "Create a JWT auth role",
                    "invariant_relevance": ["I4", "I5"],
                    "dependencies": ["login_with_jwt"],
                    "access_control_params": ["identity_claim"],
                },
            ],
            "verification_operations": [
                {
                    "name": "lookup_self",
                    "category": "IDENTITY_LOOKUP",
                    "description": "Look up current token",
                    "method": "GET",
                    "path": "/v1/auth/token/lookup-self",
                    "auth": "session",
                    "response_fields": {"data.entity_id": "The entity ID"},
                    "invariant_relevance": ["I4"],
                },
            ],
            "api_constraints": [
                "Every JWT role needs at least one bound constraint",
            ],
            "access_control_params": [
                {
                    "operation": "create_auth_role",
                    "param": "audience_restriction",
                    "platform_param": "bound_audiences",
                    "values_least_to_most_restricted": [[], ["vault"]],
                    "description": "Controls which audiences are accepted",
                }
            ],
            "known_behaviors": [
                {
                    "id": "vault_test_behavior",
                    "description": "Test behavior",
                    "invariants": ["I4"],
                    "conditions": {"mismatch_type": "case"},
                    "source": "test",
                    "note": "test note",
                }
            ],
        }

        profile_path = str(tmp_path / "vault.json")
        spec_path = str(tmp_path / "vault_api_spec.json")

        # Override analysis dir to tmp_path
        import src.extraction.extract_specs as es
        orig_mkdir = Path.mkdir

        result = split_and_save(
            llm_output, "vault", "oidc_jwt",
            model_name="test-model",
            profile_path=profile_path,
            spec_path=spec_path,
        )

        # Profile should exist and be valid JSON
        with open(profile_path) as f:
            profile = json.load(f)
        assert profile["name"] == "vault"
        assert "oidc_jwt" in profile["api_mapping"]
        assert "login_with_jwt" in profile["api_mapping"]["oidc_jwt"]
        assert "create_auth_role" in profile["api_mapping"]["oidc_jwt"]

        # session_token preserved in response_map
        login_op = profile["api_mapping"]["oidc_jwt"]["login_with_jwt"]
        assert login_op["response_map"]["session_token"] == "auth.client_token"

        # api_spec should exist
        with open(spec_path) as f:
            spec = json.load(f)
        assert spec["platform"] == "vault"
        assert len(spec["verification_apis"]["identity_lookup"]) == 1
        assert spec["extraction_model"] == "test-model"

        # known_behaviors merged
        assert any(kb["id"] == "vault_test_behavior" for kb in profile["known_behaviors"])

        # dependencies saved to analysis dir
        dep_path = Path("src/extraction/analysis/vault_oidc_jwt_dependencies.json")
        assert dep_path.exists()
        with open(dep_path) as f:
            deps = json.load(f)
        assert "create_auth_role" in deps

    def test_split_and_save_merges_existing_profile(self, tmp_path):
        """split_and_save merges into existing profile without overwriting other protocols."""
        from src.extraction.extract_specs import split_and_save

        # Create an existing profile with ldap protocol
        existing_profile = {
            "name": "vault",
            "base_url": "http://localhost:8200",
            "admin_auth": {"header": "X-Vault-Token", "value": "root"},
            "supported_protocols": ["ldap"],
            "api_mapping": {
                "ldap": {"ldap_login": {"method": "POST", "path": "/v1/auth/ldap/login/{username}", "body_map": {}, "response_map": {"session_token": "auth.client_token"}, "auth": "none"}}
            },
            "known_behaviors": [],
            "verification_fields": {},
            "api_constraints": ["existing constraint"],
        }
        profile_path = tmp_path / "vault.json"
        profile_path.write_text(json.dumps(existing_profile))
        spec_path = tmp_path / "vault_api_spec.json"

        llm_output = {
            "input_operations": [
                {
                    "operation_name": "login_with_jwt",
                    "method": "POST", "path": "/v1/auth/{mount}/login",
                    "body_map": {}, "response_map": {"session_token": "auth.client_token"},
                    "auth": "none", "dependencies": [],
                }
            ],
            "verification_operations": [],
            "api_constraints": ["new constraint"],
            "access_control_params": [],
            "known_behaviors": [],
        }

        split_and_save(
            llm_output, "vault", "oidc_jwt",
            profile_path=str(profile_path),
            spec_path=str(spec_path),
        )

        with open(profile_path) as f:
            merged = json.load(f)

        # Both protocols present
        assert "ldap" in merged["api_mapping"]
        assert "oidc_jwt" in merged["api_mapping"]
        # Both protocols in supported_protocols
        assert "ldap" in merged["supported_protocols"]
        assert "oidc_jwt" in merged["supported_protocols"]
        # Constraints merged (deduplicated)
        assert "existing constraint" in merged["api_constraints"]
        assert "new constraint" in merged["api_constraints"]

    def test_build_user_prompt_includes_platform(self):
        """build_user_prompt includes platform name and protocol in output."""
        from src.extraction.extract_specs import build_user_prompt
        prompt = build_user_prompt("vault", "oidc_jwt", "## Some docs\n\ncontent here")
        assert "vault" in prompt
        assert "oidc_jwt" in prompt
        assert "input_operations" in prompt
        assert "verification_operations" in prompt
        assert "known_behaviors" in prompt

    def test_system_prompt_includes_invariants(self):
        """SYSTEM_PROMPT mentions all 5 invariants."""
        from src.extraction.extract_specs import SYSTEM_PROMPT
        for inv in ["I1", "I2", "I3", "I4", "I5"]:
            assert inv in SYSTEM_PROMPT


class TestFetchDocsOpenAPI:
    def test_clean_openapi_json_filters_paths(self):
        """clean_openapi_json keeps only security-relevant paths."""
        from src.extraction.fetch_docs import clean_openapi_json
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/auth/token": {"get": {}},
                "/realms/{realm}/clients": {"get": {}},
                "/health/ready": {"get": {}},          # should be filtered
                "/metrics": {"get": {}},               # should be filtered
            }
        }
        result = json.loads(clean_openapi_json(json.dumps(spec)))
        assert "/auth/token" in result["paths"]
        assert "/realms/{realm}/clients" in result["paths"]
        # /health and /metrics don't match any security prefix → filtered out
        assert "/health/ready" not in result["paths"]
        assert "/metrics" not in result["paths"]


class TestGitHubDiscovery:
    @pytest.mark.skipif(
        not os.environ.get("GITHUB_TOKEN"),
        reason="GITHUB_TOKEN not set — skip API test"
    )
    def test_list_github_directory_vault(self):
        """Can discover Vault API doc files via GitHub API."""
        from src.extraction.fetch_docs import list_github_directory
        files = list_github_directory(
            "hashicorp/web-unified-docs",
            "content/vault/v1.21.x/content/api-docs/auth",
            "main",
            [".mdx"],
        )
        assert len(files) >= 5
        filenames = [f["path"].split("/")[-1] for f in files]
        assert any("jwt" in name for name in filenames)

    def test_matches_extensions(self):
        from src.extraction.fetch_docs import _matches_extensions
        assert _matches_extensions("test.mdx", [".mdx", ".md"])
        assert _matches_extensions("test.md", [".mdx", ".md"])
        assert not _matches_extensions("test.go", [".mdx", ".md"])
        assert _matches_extensions("test.go", None)  # None = accept all


class TestCleaners:
    def test_clean_go_source(self):
        from src.extraction.fetch_docs import clean_go_source
        go_code = '''package server

import "net/http"

// HandleLogin processes JWT login requests
func (s *Server) HandleLogin(w http.ResponseWriter, r *http.Request) {
    token := r.Header.Get("Authorization")
    if token == "" {
        http.Error(w, "missing token", http.StatusUnauthorized)
        return
    }
    // validate token...
}

type Config struct {
    Issuer string
    ClientID string
}
'''
        result = clean_go_source(go_code)
        assert "func" in result
        assert "HandleLogin" in result
        assert "type Config" in result
        assert "http.Error" not in result  # Implementation detail stripped

    def test_clean_asciidoc(self):
        from src.extraction.fetch_docs import clean_asciidoc
        content = """ifdef::env-github[]
:icons:: font
endif::[]

= Server Administration Guide

This is the main content.

include::topics/overview.adoc[]
"""
        result = clean_asciidoc(content)
        assert "ifdef" not in result
        assert "endif" not in result
        assert "include::" not in result
        assert ":icons::" not in result
        assert "Server Administration Guide" in result
        assert "main content" in result

    def test_auto_clean_dispatches(self):
        from src.extraction.fetch_docs import auto_clean
        # MDX path should use clean_mdx
        result = auto_clean("import X\n## Title\ncontent", "docs/page.mdx")
        assert "import" not in result
        assert "## Title" in result

        # Go path should use clean_go_source
        result = auto_clean("package main\nfunc Foo() {}\nbar := 1", "server/main.go")
        assert "func Foo" in result
        assert "package main" in result


class TestCompareWithReference:
    def test_compare_identical(self, tmp_path):
        """Identical profiles produce no diffs."""
        from src.extraction.validate_specs import compare_with_reference
        profile = {
            "api_mapping": {"oidc_jwt": {
                "login_with_jwt": {"method": "POST", "path": "/v1/auth/{mount}/login"},
                "create_auth_role": {"method": "POST", "path": "/v1/auth/{mount}/role/{name}"},
            }}
        }
        extracted = tmp_path / "extracted.json"
        reference = tmp_path / "reference.json"
        extracted.write_text(json.dumps(profile))
        reference.write_text(json.dumps(profile))

        diffs = compare_with_reference("vault", "oidc_jwt",
                                       str(extracted), str(reference))
        assert diffs == []

    def test_compare_missing_ops(self, tmp_path):
        """Missing operations are reported."""
        from src.extraction.validate_specs import compare_with_reference
        extracted = {
            "api_mapping": {"oidc_jwt": {
                "login_with_jwt": {"method": "POST", "path": "/login"},
            }}
        }
        reference = {
            "api_mapping": {"oidc_jwt": {
                "login_with_jwt": {"method": "POST", "path": "/login"},
                "create_auth_role": {"method": "POST", "path": "/role"},
            }}
        }
        ext_path = tmp_path / "extracted.json"
        ref_path = tmp_path / "reference.json"
        ext_path.write_text(json.dumps(extracted))
        ref_path.write_text(json.dumps(reference))

        diffs = compare_with_reference("vault", "oidc_jwt",
                                       str(ext_path), str(ref_path))
        assert any("MISSING" in d for d in diffs)
        assert any("create_auth_role" in d for d in diffs)


@pytest.mark.integration
@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="needs OPENAI_API_KEY")
@pytest.mark.skipif(not os.environ.get("GITHUB_TOKEN"), reason="needs GITHUB_TOKEN")
def test_full_vault_extraction_pipeline():
    """Run the complete extraction pipeline for Vault and validate output."""
    from src.extraction.fetch_docs import fetch_platform_docs
    from src.extraction.extract_specs import extract_platform_specs
    from src.extraction.validate_specs import validate_profile

    # Step 1: Fetch
    result = fetch_platform_docs("vault", "oidc_jwt")
    assert result["total_files"] >= 10

    # Step 2: Extract (this calls LLM)
    extract_result = extract_platform_specs("vault", "oidc_jwt")
    assert extract_result["ops_extracted"] >= 10

    # Step 3: Validate
    errors = validate_profile("vault", "oidc_jwt")
    fatal = [e for e in errors if e.startswith("FATAL")]
    assert not fatal, f"Fatal validation errors: {fatal}"
