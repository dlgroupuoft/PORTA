"""Integration tests for stateful fuzzing campaign.

Run against a live Vault instance:
    docker compose -f docker-compose.vault-stateful.yml up -d
    pytest tests/test_stateful_campaign.py -m integration -v
"""
import pytest
import requests

from src.stateful.models import Event, EventSequence, OracleCheck
from src.stateful.sequence_executor import SequenceExecutor
from src.stateful.assertion_engine import AssertionEngine

VAULT_URL = "http://localhost:8200"
ADMIN_TOKEN = "root"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def vault_available():
    """Skip all integration tests if Vault is not running."""
    try:
        r = requests.get(f"{VAULT_URL}/v1/sys/health", timeout=3)
        if r.status_code not in (200, 429, 472, 473):
            pytest.skip("Vault not healthy")
    except requests.RequestException:
        pytest.skip("Vault not reachable")


@pytest.fixture(scope="module")
def jwt_factory(vault_available):
    """Create a JWTFactory and configure Vault to accept its tokens."""
    from src.utils.jwt_factory import JWTFactory
    from src.utils.crypto import generate_rsa_key_pair
    from cryptography.hazmat.primitives import serialization

    private_key, public_key = generate_rsa_key_pair()
    factory = JWTFactory(default_signing_key=private_key)

    public_pem = public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    headers = {"X-Vault-Token": ADMIN_TOKEN}

    # Enable JWT auth mount
    requests.post(f"{VAULT_URL}/v1/sys/auth/jwt",
                  headers=headers, json={"type": "jwt"})

    # Configure static public key
    r = requests.post(
        f"{VAULT_URL}/v1/auth/jwt/config",
        headers=headers,
        json={"jwt_validation_pubkeys": [public_pem]},
    )
    assert r.status_code in (200, 204), f"JWT config failed: {r.text}"

    # Enable KV v2 at /secret
    requests.post(f"{VAULT_URL}/v1/sys/mounts/secret",
                  headers=headers,
                  json={"type": "kv", "options": {"version": "2"}})

    return factory


@pytest.fixture
def executor(jwt_factory):
    from src.adapters.vault_adapter import VaultAdapter
    from src.models.platform_profile import PlatformProfile
    adapter = VaultAdapter({
        "base_url": VAULT_URL,
        "admin_token": ADMIN_TOKEN,
        "auth_mount_path": "jwt",
    })
    profile = PlatformProfile.from_json("src/profiles/vault.json")
    return SequenceExecutor(
        vault_adapter=adapter,
        jwt_factory=jwt_factory,
        admin_token=ADMIN_TOKEN,
        profile=profile,
        protocol="oidc_jwt",
    )


# ---------------------------------------------------------------------------
# Unit tests for AssertionEngine (no Vault needed)
# ---------------------------------------------------------------------------

class TestAssertionEngine:
    def setup_method(self):
        self.engine = AssertionEngine()

    def test_eq_true(self):
        result, _ = self.engine.evaluate("x == y", {"x": "abc", "y": "abc"})
        assert result is True

    def test_eq_false(self):
        result, _ = self.engine.evaluate("x == y", {"x": "abc", "y": "def"})
        assert result is False

    def test_neq(self):
        result, _ = self.engine.evaluate("x != y", {"x": "abc", "y": "def"})
        assert result is True

    def test_is_none(self):
        result, _ = self.engine.evaluate("x is None", {"x": None})
        assert result is True

    def test_is_not_none(self):
        result, _ = self.engine.evaluate("x is not None", {"x": "value"})
        assert result is True

    def test_in_list(self):
        result, _ = self.engine.evaluate('"admin-policy" in policies', {"policies": ["default", "admin-policy"]})
        assert result is True

    def test_not_in_list(self):
        result, _ = self.engine.evaluate('"admin-policy" not in policies', {"policies": ["default"]})
        assert result is True

    def test_eq_false_literal(self):
        result, _ = self.engine.evaluate("login_success == False", {"login_success": False})
        assert result is True

    def test_numeric_comparison(self):
        result, _ = self.engine.evaluate("status == 403", {"status": 403})
        assert result is True

    def test_and(self):
        result, _ = self.engine.evaluate("x == 1 AND y == 2", {"x": 1, "y": 2})
        assert result is True

    def test_or(self):
        result, _ = self.engine.evaluate("x == 1 OR y == 3", {"x": 1, "y": 2})
        assert result is True

    def test_dot_path(self):
        result, _ = self.engine.evaluate(
            'meta.username == "alice"',
            {"meta": {"username": "alice"}}
        )
        assert result is True

    def test_json_bool_true(self):
        result, _ = self.engine.evaluate("x == true", {"x": True})
        assert result is True

    def test_json_bool_false(self):
        result, _ = self.engine.evaluate("x == false", {"x": False})
        assert result is True

    def test_json_null(self):
        result, _ = self.engine.evaluate("x == null", {"x": None})
        assert result is True

    def test_json_bool_in_complex(self):
        result, _ = self.engine.evaluate(
            "active == true AND scope != null",
            {"active": True, "scope": "openid"}
        )
        assert result is True


# ---------------------------------------------------------------------------
# Integration Test 1: Hardcoded sequence (no LLM)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_hardcoded_sequence(executor):
    """Execute the example_i4_entity_collision sequence against live Vault.

    This verifies the executor works without LLM involvement.
    Expected: two different sub values create two different entities.
    """
    seq = EventSequence(
        sequence_id="test_i4_entity_collision",
        description="Two users with different sub values should map to different entities",
        invariant_hypothesis="I4: SecurityDistinct(p1, p2) => Map(p1) != Map(p2)",
        primary_invariant="I4",
        cve_analog="CVE-2021-41802",
        events=[
            Event(
                event_type="create_auth_role",
                params={
                    "role_name": "collision-test-role",
                    "user_claim": "sub",
                    "bound_audiences": ["vault"],
                    "token_policies": ["default"],
                },
                auth_as="admin",
            ),
            Event(
                event_type="login_with_jwt",
                params={
                    "role": "collision-test-role",
                    "jwt_claims": {"sub": "alice@corp.com", "aud": "vault"},
                },
                auth_as="user_A",
                captures={
                    "user_a_token": "auth.client_token",
                    "user_a_entity": "auth.entity_id",
                },
            ),
            Event(
                event_type="login_with_jwt",
                params={
                    "role": "collision-test-role",
                    "jwt_claims": {"sub": "alice@corp.com ", "aud": "vault"},
                },
                auth_as="user_B",
                captures={
                    "user_b_token": "auth.client_token",
                    "user_b_entity": "auth.entity_id",
                },
            ),
            Event(
                event_type="verify_token_self",
                params={},
                auth_as="session_user_A",
                captures={
                    "user_a_policies": "data.policies",
                },
            ),
            Event(
                event_type="verify_token_self",
                params={},
                auth_as="session_user_B",
                captures={
                    "user_b_policies": "data.policies",
                },
            ),
        ],
        oracle_checks=[
            OracleCheck(
                check_id="i4_entity_distinct",
                invariant="I4",
                assertion="user_a_entity != user_b_entity",
                violation_description=(
                    "Two users with different sub values (trailing space) "
                    "collapsed to same Vault entity — principal binding violation"
                ),
                cve_analog="CVE-2021-41802",
            ),
        ],
    )

    result = executor.execute(seq)

    assert result.status == "COMPLETED", f"Sequence failed with status: {result.status}"
    assert len(result.verdicts) >= 1

    for v in result.verdicts:
        print(f"\nVerdict: {v.verdict_type.value} — {v.description[:120]}")
    print(f"Captured state: {result.captured_state}")

    # The assertion oracle verdict should be BY_DESIGN or UNEXPECTED
    assertion_verdicts = [v for v in result.verdicts if "[AutoVerify]" not in v.description]
    assert len(assertion_verdicts) >= 1
    assert assertion_verdicts[0].verdict_type.value in ("BY_DESIGN", "UNEXPECTED", "ERROR")

    # Verify both users successfully logged in
    assert result.captured_state.get("user_A_login_success") is True, \
        "user_A login should succeed"
    assert result.captured_state.get("user_B_login_success") is True, \
        "user_B login should succeed"


# ---------------------------------------------------------------------------
# Integration Test 2: One LLM-generated sequence
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.llm
def test_llm_single_sequence(executor):
    """Generate one sequence via LLM and execute against live Vault.

    Requires OPENAI_API_KEY environment variable.
    """
    import os
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    from src.llm.client import LLMClient
    from src.stateful.sequence_generator import SequenceGenerator

    llm = LLMClient(model=os.getenv("VALENCE_LLM_MODEL", "gpt-5.2"))
    generator = SequenceGenerator(llm)

    sequences = generator.generate(invariant_focus="I4", num_sequences=1)
    assert len(sequences) >= 1, "LLM should generate at least 1 valid sequence"

    seq = sequences[0]
    print(f"\nLLM generated: {seq.sequence_id} — {seq.description}")
    print(f"Events: {[e.event_type for e in seq.events]}")

    result = executor.execute(seq)
    print(f"Status: {result.status}")
    for v in result.verdicts:
        print(f"  [{v.invariant}] {v.verdict_type.value}: {v.description[:100]}")

    # Just verify it ran without crashing
    assert result.status in ("COMPLETED", "SETUP_FAILED")
