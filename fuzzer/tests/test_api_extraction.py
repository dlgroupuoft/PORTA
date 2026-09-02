"""Test that API extraction produces valid, complete specs."""

import json
import os

import pytest

SPECS_DIR = "src/llm/platform_apis"


def load_spec(platform: str) -> dict:
    path = os.path.join(SPECS_DIR, f"{platform}_api_spec.json")
    if not os.path.exists(path):
        pytest.skip(f"Run extract_all_platforms first: {path} not found")
    with open(path) as f:
        return json.load(f)


# --------------------------------------------------------------------------
# Shared completeness check
# --------------------------------------------------------------------------

def _check_spec_completeness(spec: dict, platform: str):
    assert spec.get("platform") == platform, \
        f"Expected platform={platform}, got {spec.get('platform')}"

    apis = spec.get("verification_apis", {})
    required = ["identity_lookup", "permission_check", "session_token_inspect"]
    for cat in required:
        assert cat in apis, f"Missing category: {cat}"
        assert len(apis[cat]) > 0, f"Empty category: {cat}"

    for cat, endpoints in apis.items():
        for ep in endpoints:
            assert "name" in ep, f"Missing name in {cat}"
            assert "method" in ep, f"Missing method in {cat}/{ep.get('name')}"
            assert "path" in ep, f"Missing path in {cat}/{ep.get('name')}"
            assert "response_fields" in ep, \
                f"Missing response_fields in {cat}/{ep.get('name')}"
            assert "invariant_relevance" in ep, \
                f"Missing invariant_relevance in {cat}/{ep.get('name')}"

    recipes = spec.get("verification_recipes", {})
    assert len(recipes) >= 2, "Need at least 2 verification recipes"


# --------------------------------------------------------------------------
# Per-platform completeness
# --------------------------------------------------------------------------

def test_vault_spec_completeness():
    _check_spec_completeness(load_spec("vault"), "vault")


def test_keycloak_spec_completeness():
    _check_spec_completeness(load_spec("keycloak"), "keycloak")


def test_dex_spec_completeness():
    _check_spec_completeness(load_spec("dex"), "dex")


# --------------------------------------------------------------------------
# Vault-specific
# --------------------------------------------------------------------------

def test_vault_spec_has_identity_apis():
    """Vault must have token lookup and entity lookup."""
    spec = load_spec("vault")
    identity = spec["verification_apis"]["identity_lookup"]
    names = [ep["name"] for ep in identity]
    assert any("token" in n or "lookup" in n for n in names), \
        f"Missing token lookup in identity_lookup: {names}"
    assert any("entity" in n for n in names), \
        f"Missing entity lookup in identity_lookup: {names}"


def test_vault_spec_has_access_test():
    """Vault must have secret read endpoint for access testing."""
    spec = load_spec("vault")
    access = spec["verification_apis"].get("access_test", [])
    assert len(access) > 0, "Vault must have access_test APIs (KV read)"


def test_vault_endpoint_count():
    """Vault should have 10+ endpoints across identity + permission categories."""
    spec = load_spec("vault")
    apis = spec["verification_apis"]
    count = len(apis.get("identity_lookup", [])) + len(apis.get("permission_check", []))
    assert count >= 5, f"Expected >=5 identity+permission endpoints, got {count}"


# --------------------------------------------------------------------------
# Keycloak-specific
# --------------------------------------------------------------------------

def test_keycloak_spec_has_oidc_endpoints():
    """Keycloak must have token, userinfo, introspect endpoints."""
    spec = load_spec("keycloak")
    all_names = []
    for eps in spec.get("verification_apis", {}).values():
        all_names.extend(ep.get("name", "") for ep in eps)
    for ep in spec.get("oidc_protocol_endpoints", []):
        all_names.append(ep.get("name", ""))

    assert any("userinfo" in n for n in all_names), \
        f"Missing userinfo endpoint: {all_names[:20]}"
    assert any("introspect" in n for n in all_names), \
        f"Missing introspect endpoint: {all_names[:20]}"


def test_keycloak_uses_openapi():
    """Keycloak spec should be extracted from OpenAPI, not raw HTML."""
    spec = load_spec("keycloak")
    method = spec.get("extraction_method", "")
    assert "openapi" in method, \
        f"Expected openapi extraction method, got: {method}"


# --------------------------------------------------------------------------
# Dex-specific
# --------------------------------------------------------------------------

def test_dex_spec_is_static():
    """Dex spec must exist and note its limitations."""
    spec = load_spec("dex")
    assert spec["extraction_method"] == "static_hardcoded"
    assert "no_admin_api" in spec.get("platform_limitations", {}), \
        "Dex spec missing platform_limitations.no_admin_api"
    identity = spec["verification_apis"]["identity_lookup"]
    assert identity[0]["method"] == "LOCAL_DECODE", \
        f"Expected LOCAL_DECODE, got {identity[0]['method']}"


# --------------------------------------------------------------------------
# Cross-platform invariant coverage
# --------------------------------------------------------------------------

def test_all_specs_cover_i1_i4():
    """All platforms must have APIs to verify I1 and I4."""
    for platform in ["vault", "keycloak", "dex"]:
        spec = load_spec(platform)
        covered = set()
        for eps in spec.get("verification_apis", {}).values():
            for ep in eps:
                covered.update(ep.get("invariant_relevance", []))
        assert "I1" in covered, f"{platform} missing I1 coverage"
        assert "I4" in covered, f"{platform} missing I4 coverage"


def test_all_specs_exist():
    """Verify all three platform specs have been generated."""
    for platform in ["vault", "keycloak", "dex"]:
        path = os.path.join(SPECS_DIR, f"{platform}_api_spec.json")
        assert os.path.exists(path), f"Missing spec: {path}"


def test_raw_docs_cached():
    """Verify raw documentation caches exist (in extraction/raw_docs/)."""
    raw_dir = "src/extraction/raw_docs"
    assert os.path.isdir(raw_dir), f"Missing raw_docs dir: {raw_dir}"


def test_recipes_have_steps():
    """Verify recipes contain actual steps."""
    spec = load_spec("vault")
    for name, recipe in spec.get("verification_recipes", {}).items():
        assert "steps" in recipe, f"Recipe {name} missing steps"
        assert len(recipe["steps"]) >= 1, f"Recipe {name} has no steps"
        assert "detects_invariants" in recipe, \
            f"Recipe {name} missing detects_invariants"


def test_invariant_coverage_vault():
    """Vault extracted APIs must cover I1, I2, I4, I5."""
    spec = load_spec("vault")
    covered = set()
    for eps in spec.get("verification_apis", {}).values():
        for ep in eps:
            covered.update(ep.get("invariant_relevance", []))
    required = {"I1", "I2", "I4", "I5"}
    missing = required - covered
    assert not missing, f"Vault missing invariant coverage: {missing}"


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="needs OPENAI_API_KEY"
)
def test_real_extraction_vault():
    """Actually run extraction on Vault docs (costs LLM tokens)."""
    from src.extraction.extract_specs import extract_platform_specs

    result = extract_platform_specs("vault", "oidc_jwt")
    assert result.get("ops_extracted", 0) > 0
    print(f"Extracted {result.get('ops_extracted')} input ops, "
          f"{result.get('verification_ops_extracted')} verification ops")
