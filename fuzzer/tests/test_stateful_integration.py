"""Integration test: run hardcoded sequences against live Vault.

No LLM required. Uses a dedicated 'stateful-test-jwt' auth mount so it
doesn't interfere with other tests.

Run:
    pytest tests/test_stateful_integration.py -v -s
"""
import os
import pytest
import requests

from src.stateful.models import Event, EventSequence, OracleCheck
from src.stateful.sequence_executor import SequenceExecutor

VAULT_URL = os.getenv("VAULT_URL", "http://localhost:8200")
ADMIN_TOKEN = "root"
TEST_MOUNT = "stateful-test-jwt"


def vault_is_running() -> bool:
    try:
        r = requests.get(f"{VAULT_URL}/v1/sys/health", timeout=3)
        return r.status_code in (200, 429, 472, 473)
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not vault_is_running(), reason="Vault not running"
)


# ---------------------------------------------------------------------------
# Module-scoped fixture: configure Vault once for all tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def executor():
    """Create SequenceExecutor with real JWTFactory, configure Vault."""
    from src.utils.jwt_factory import JWTFactory
    from src.utils.crypto import generate_rsa_key_pair
    from cryptography.hazmat.primitives import serialization

    # Generate test RSA key pair
    private_key, public_key = generate_rsa_key_pair()
    factory = JWTFactory(default_signing_key=private_key)

    public_pem = public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    headers = {"X-Vault-Token": ADMIN_TOKEN, "Content-Type": "application/json"}

    # Enable dedicated JWT auth mount (ignore if already exists)
    requests.post(
        f"{VAULT_URL}/v1/sys/auth/{TEST_MOUNT}",
        headers=headers,
        json={"type": "jwt"},
    )

    # Configure with our test public key
    r = requests.post(
        f"{VAULT_URL}/v1/auth/{TEST_MOUNT}/config",
        headers=headers,
        json={"jwt_validation_pubkeys": [public_pem]},
    )
    assert r.status_code in (200, 204), f"JWT config failed: {r.text}"

    from src.adapters.vault_adapter import VaultAdapter
    from src.models.platform_profile import PlatformProfile
    adapter = VaultAdapter({
        "base_url": VAULT_URL,
        "admin_token": ADMIN_TOKEN,
        "auth_mount_path": TEST_MOUNT,
    })
    profile = PlatformProfile.from_json("src/profiles/vault.json")
    ex = SequenceExecutor(
        vault_adapter=adapter,
        jwt_factory=factory,
        admin_token=ADMIN_TOKEN,
        profile=profile,
        protocol="oidc_jwt",
    )

    yield ex

    # Cleanup: disable the test auth mount
    requests.delete(
        f"{VAULT_URL}/v1/sys/auth/{TEST_MOUNT}",
        headers={"X-Vault-Token": ADMIN_TOKEN},
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestBasicSequenceExecution:

    def test_single_login_and_verify(self, executor):
        """最简单的测试：create role → login → verify token。"""
        seq = EventSequence(
            sequence_id="test_basic_001",
            description="Basic login and token verification",
            invariant_hypothesis="Sanity check: correct login should work",
            primary_invariant="I4",
            events=[
                Event(
                    event_type="setup_jwt_role",
                    params={
                        "mount": TEST_MOUNT,
                        "role_name": "basic-test",
                        "user_claim": "sub",
                        "bound_audiences": ["vault"],
                        "token_policies": ["default"],
                    },
                    auth_as="admin",
                ),
                Event(
                    event_type="login_jwt",
                    params={
                        "mount": TEST_MOUNT,
                        "role": "basic-test",
                        "jwt_claims": {"sub": "test-user", "aud": "vault"},
                    },
                    auth_as="user_A",
                    captures={
                        "user_a_token": "auth.client_token",
                        "user_a_entity": "auth.entity_id",
                        "user_a_policies": "auth.policies",
                    },
                ),
                Event(
                    event_type="verify_token_self",
                    params={},
                    auth_as="session_user_A",
                    captures={
                        "user_a_display_name": "data.display_name",
                        "user_a_token_policies": "data.policies",
                        "user_a_identity_policies": "data.identity_policies",
                        "user_a_verified_entity_id": "data.entity_id",
                    },
                ),
            ],
            oracle_checks=[
                OracleCheck(
                    check_id="basic_login",
                    invariant="I4",
                    assertion="user_a_entity is not None",
                    violation_description="Login should produce a non-null entity_id",
                ),
            ],
        )

        result = executor.execute(seq)

        print(f"\nStatus: {result.status}")
        print(f"Captures: {result.captured_state}")
        for v in result.verdicts:
            print(f"Verdict: [{v.invariant}] {v.verdict_type.value}: {v.description[:100]}")

        assert result.status == "COMPLETED", f"Sequence failed: {result.status}"
        assert result.captured_state.get("user_a_entity") is not None, \
            "No entity_id captured from login"

        # InvariantVerifier should produce 0 VIOLATION/UNEXPECTED for a clean login
        auto_verdicts = [v for v in result.verdicts if "[AutoVerify]" in v.description]
        unexpected = [v for v in auto_verdicts
                      if v.verdict_type.value in ("VIOLATION", "UNEXPECTED")]
        assert len(unexpected) == 0, \
            f"Clean login should have 0 auto findings: {[v.description for v in unexpected]}"

    def test_two_users_different_entity(self, executor):
        """两个不同 sub 的用户应该得到不同的 entity。"""
        seq = EventSequence(
            sequence_id="test_i4_001",
            description="Two users with different sub should get different entities",
            invariant_hypothesis="I4: SecurityDistinct(p1,p2) => Map(p1) != Map(p2)",
            primary_invariant="I4",
            events=[
                Event(
                    event_type="setup_jwt_role",
                    params={
                        "mount": TEST_MOUNT,
                        "role_name": "i4-test",
                        "user_claim": "sub",
                        "bound_audiences": ["vault"],
                        "token_policies": ["default"],
                    },
                    auth_as="admin",
                ),
                Event(
                    event_type="login_jwt",
                    params={
                        "mount": TEST_MOUNT,
                        "role": "i4-test",
                        "jwt_claims": {"sub": "alice@corp.com", "aud": "vault"},
                    },
                    auth_as="user_A",
                    captures={
                        "user_a_entity": "auth.entity_id",
                        "user_a_policies": "auth.policies",
                    },
                ),
                Event(
                    event_type="login_jwt",
                    params={
                        "mount": TEST_MOUNT,
                        "role": "i4-test",
                        "jwt_claims": {"sub": "bob@corp.com", "aud": "vault"},
                    },
                    auth_as="user_B",
                    captures={
                        "user_b_entity": "auth.entity_id",
                        "user_b_policies": "auth.policies",
                    },
                ),
                Event(
                    event_type="verify_token_self",
                    params={},
                    auth_as="session_user_A",
                    captures={"user_a_identity_policies": "data.identity_policies"},
                ),
                Event(
                    event_type="verify_token_self",
                    params={},
                    auth_as="session_user_B",
                    captures={"user_b_identity_policies": "data.identity_policies"},
                ),
                Event(
                    event_type="verify_entity",
                    params={"entity_id": "{{user_a_entity}}"},
                    auth_as="admin",
                    captures={
                        "user_a_entity_name": "data.name",
                        "user_a_entity_aliases": "data.aliases",
                    },
                ),
                Event(
                    event_type="verify_entity",
                    params={"entity_id": "{{user_b_entity}}"},
                    auth_as="admin",
                    captures={
                        "user_b_entity_name": "data.name",
                        "user_b_entity_aliases": "data.aliases",
                    },
                ),
            ],
            oracle_checks=[
                OracleCheck(
                    check_id="entity_distinct",
                    invariant="I4",
                    assertion="user_a_entity != user_b_entity",
                    violation_description="Different sub values should map to different entities",
                    cve_analog="CVE-2021-41802",
                ),
            ],
        )

        result = executor.execute(seq)

        print(f"\nStatus: {result.status}")
        print(f"User A entity: {result.captured_state.get('user_a_entity')}")
        print(f"User A aliases: {result.captured_state.get('user_a_entity_aliases')}")
        print(f"User B entity: {result.captured_state.get('user_b_entity')}")
        print(f"User B aliases: {result.captured_state.get('user_b_entity_aliases')}")
        for v in result.verdicts:
            print(f"Verdict: [{v.invariant}] {v.verdict_type.value}: {v.description[:120]}")

        assert result.status == "COMPLETED"
        assert result.captured_state.get("user_a_entity") != result.captured_state.get("user_b_entity"), \
            "alice and bob must have different entities"

    def test_trailing_space_entity_collision(self, executor):
        """核心 I4 测试：sub='alice' vs sub='alice ' — 是否碰撞到同一 entity？"""
        seq = EventSequence(
            sequence_id="test_i4_whitespace_001",
            description="Trailing space in sub — entity collision test",
            invariant_hypothesis="I4: 'alice' and 'alice ' are SecurityDistinct",
            primary_invariant="I4",
            events=[
                Event(
                    event_type="setup_jwt_role",
                    params={
                        "mount": TEST_MOUNT,
                        "role_name": "ws-test",
                        "user_claim": "sub",
                        "bound_audiences": ["vault"],
                        "token_policies": ["default"],
                    },
                    auth_as="admin",
                ),
                Event(
                    event_type="login_jwt",
                    params={
                        "mount": TEST_MOUNT,
                        "role": "ws-test",
                        "jwt_claims": {"sub": "alice", "aud": "vault"},
                    },
                    auth_as="user_A",
                    captures={"user_a_entity": "auth.entity_id"},
                ),
                Event(
                    event_type="login_jwt",
                    params={
                        "mount": TEST_MOUNT,
                        "role": "ws-test",
                        "jwt_claims": {"sub": "alice ", "aud": "vault"},  # trailing space
                    },
                    auth_as="user_B",
                    captures={"user_b_entity": "auth.entity_id"},
                ),
                Event(
                    event_type="verify_entity",
                    params={"entity_id": "{{user_a_entity}}"},
                    auth_as="admin",
                    captures={
                        "user_a_entity_aliases": "data.aliases",
                        "user_a_entity_name": "data.name",
                    },
                ),
                Event(
                    event_type="verify_entity",
                    params={"entity_id": "{{user_b_entity}}"},
                    auth_as="admin",
                    captures={
                        "user_b_entity_aliases": "data.aliases",
                        "user_b_entity_name": "data.name",
                    },
                ),
            ],
            oracle_checks=[
                OracleCheck(
                    check_id="whitespace_collision",
                    invariant="I4",
                    assertion="user_a_entity != user_b_entity",
                    violation_description="Trailing space in sub caused entity collision",
                    cve_analog="CVE-2021-41802",
                ),
            ],
        )

        result = executor.execute(seq)

        print(f"\nStatus: {result.status}")
        print(f"User A entity: {result.captured_state.get('user_a_entity')}")
        print(f"User B entity: {result.captured_state.get('user_b_entity')}")
        print(f"User A aliases: {result.captured_state.get('user_a_entity_aliases')}")
        print(f"User B aliases: {result.captured_state.get('user_b_entity_aliases')}")
        for v in result.verdicts:
            marker = "[VIOLATION]" if v.verdict_type.value == "VIOLATION" \
                else "[UNEXPECTED]" if v.verdict_type.value == "UNEXPECTED" else "[OK]"
            print(f"{marker} [{v.invariant}] {v.verdict_type.value}: {v.description[:150]}")

        assert result.status == "COMPLETED"

        # Observe without forcing pass/fail — this is a real finding test
        if result.captured_state.get("user_a_entity") == result.captured_state.get("user_b_entity"):
            print("\n*** FINDING: sub='alice' and sub='alice ' mapped to SAME entity! ***")
            print("    This may be CVE-worthy: trailing space not treated as security-distinct.")

    def test_empty_bound_audiences(self, executor):
        """I5 测试：bound_audiences=[] 是否接受任意 audience 的 JWT？"""
        seq = EventSequence(
            sequence_id="test_i5_aud_001",
            description="Empty bound_audiences — should it accept any audience?",
            invariant_hypothesis="I5: empty bound_audiences should deny, not allow-all",
            primary_invariant="I5",
            events=[
                Event(
                    event_type="setup_jwt_role",
                    params={
                        "mount": TEST_MOUNT,
                        "role_name": "aud-empty-test",
                        "user_claim": "sub",
                        "bound_audiences": [],  # EMPTY — CVE-2024-7594 pattern
                        "token_policies": ["default"],
                    },
                    auth_as="admin",
                ),
                Event(
                    event_type="login_jwt",
                    params={
                        "mount": TEST_MOUNT,
                        "role": "aud-empty-test",
                        "jwt_claims": {"sub": "attacker", "aud": "completely-wrong-service"},
                    },
                    auth_as="attacker",
                    captures={
                        "attacker_token": "auth.client_token",
                        "attacker_entity": "auth.entity_id",
                    },
                    expected_outcome="any",
                ),
            ],
            oracle_checks=[
                OracleCheck(
                    check_id="empty_aud_deny",
                    invariant="I5",
                    assertion="attacker_login_success == False",
                    violation_description=(
                        "Empty bound_audiences accepted login with arbitrary audience — "
                        "allow-all semantics (CVE-2024-7594 pattern)"
                    ),
                    cve_analog="CVE-2024-7594",
                ),
            ],
        )

        result = executor.execute(seq)

        print(f"\nStatus: {result.status}")
        login_success = result.captured_state.get("attacker_login_success", "UNKNOWN")
        print(f"Attacker login success: {login_success}")
        for v in result.verdicts:
            marker = "[VIOLATION]" if v.verdict_type.value == "VIOLATION" \
                else "[UNEXPECTED]" if v.verdict_type.value == "UNEXPECTED" else "[OK]"
            print(f"{marker} [{v.invariant}] {v.verdict_type.value}: {v.description[:150]}")

        assert result.status in ("COMPLETED", "SETUP_FAILED")
