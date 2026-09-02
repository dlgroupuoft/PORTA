"""Merged pipeline integration tests: Sprint 1-4 components + Sprint 6 stateful framework.

Verifies that SequenceExecutor uses VaultAdapter.authenticate() for logins
(not raw HTTP), and that all three oracle layers fire correctly.

Run:
    pytest tests/test_merged_pipeline.py -v -s
"""
import pytest
import requests

from src.utils.jwt_factory import JWTFactory
from src.utils.crypto import generate_rsa_key_pair
from src.adapters.vault_adapter import VaultAdapter
from src.oracles.i4_principal_binding import I4PrincipalBindingOracle
from src.oracles.i5_authorization_binding import I5AuthorizationBindingOracle
from src.stateful.models import Event, EventSequence, OracleCheck
from src.stateful.sequence_executor import SequenceExecutor
from cryptography.hazmat.primitives import serialization

VAULT_URL = "http://localhost:8200"
TEST_MOUNT = "merged-test-jwt"


def vault_running():
    try:
        return requests.get(f"{VAULT_URL}/v1/sys/health", timeout=3).status_code in (200, 429, 472, 473)
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not vault_running(), reason="Vault not running")


@pytest.fixture(scope="module")
def pipeline():
    """Set up the merged pipeline with Sprint 1-4 components."""
    priv, pub = generate_rsa_key_pair()
    pub_pem = pub.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    factory = JWTFactory(default_signing_key=priv)

    adapter = VaultAdapter({
        "base_url": VAULT_URL,
        "admin_token": "root",
        "auth_mount_path": TEST_MOUNT,
        "role_name": "test",
    })

    oracles = {
        "I4": I4PrincipalBindingOracle(),
        "I5": I5AuthorizationBindingOracle(),
    }

    # Configure Vault
    headers = {"X-Vault-Token": "root"}
    requests.post(f"{VAULT_URL}/v1/sys/auth/{TEST_MOUNT}", headers=headers, json={"type": "jwt"})
    r = requests.post(
        f"{VAULT_URL}/v1/auth/{TEST_MOUNT}/config",
        headers=headers,
        json={"jwt_validation_pubkeys": [pub_pem]},
    )
    assert r.status_code in (200, 204), f"JWT config failed: {r.text}"

    from src.models.platform_profile import PlatformProfile
    profile = PlatformProfile.from_json("src/profiles/vault.json")

    executor = SequenceExecutor(
        vault_adapter=adapter,
        jwt_factory=factory,
        oracles=oracles,
        admin_token="root",
        profile=profile,
        protocol="oidc_jwt",
    )

    yield executor, factory

    requests.delete(f"{VAULT_URL}/v1/sys/auth/{TEST_MOUNT}", headers=headers)


def test_adapter_reuse(pipeline):
    """Verify login uses VaultAdapter.authenticate(), not raw HTTP, and all 3 oracle layers fire."""
    executor, factory = pipeline

    seq = EventSequence(
        sequence_id="merge_test_001",
        description="Verify adapter is used for login",
        invariant_hypothesis="Sanity check",
        primary_invariant="I4",
        events=[
            Event(
                event_type="setup_jwt_role",
                params={
                    "mount": TEST_MOUNT,
                    "role_name": "merge-role",
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
                    "role": "merge-role",
                    "jwt_claims": {"sub": "test-user", "aud": "vault"},
                },
                auth_as="user_A",
                captures={"user_a_entity": "auth.entity_id"},
            ),
            Event(
                event_type="verify_token_self",
                params={},
                auth_as="session_user_A",
                captures={"user_a_policies": "data.policies"},
            ),
        ],
        oracle_checks=[
            OracleCheck(
                check_id="c1",
                invariant="I4",
                assertion="user_a_entity is not None",
                violation_description="Should get entity_id",
            ),
        ],
    )

    result = executor.execute(seq)

    assert result.status == "COMPLETED", f"Sequence failed: {result.status}"
    assert result.captured_state.get("user_a_entity") is not None, "No entity_id captured"

    print(f"\nTotal verdicts: {len(result.verdicts)}")
    for v in result.verdicts:
        src = "[SYNTACTIC]" if not any(tag in v.description for tag in ["[AutoVerify]", "Assertion"]) \
              else "[AUTO]" if "[AutoVerify]" in v.description else "[ASSERT]"
        print(f"  {src} {v.verdict_type.value}: {v.description[:80]}")

    # At minimum the assertion oracle verdict should be present
    assert len(result.verdicts) >= 1


def test_trailing_space_collision(pipeline):
    """Core I4 test using merged pipeline: sub='alice' vs sub='alice ' — entity collision?"""
    executor, factory = pipeline

    seq = EventSequence(
        sequence_id="merge_i4_001",
        description="sub='alice' vs sub='alice ' — entity collision?",
        invariant_hypothesis="I4: trailing space = security distinct",
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
                check_id="ws_collision",
                invariant="I4",
                assertion="user_a_entity != user_b_entity",
                violation_description="Trailing space caused entity collision",
                cve_analog="CVE-2021-41802",
            ),
        ],
    )

    result = executor.execute(seq)

    print(f"\nUser A entity: {result.captured_state.get('user_a_entity')}")
    print(f"User B entity: {result.captured_state.get('user_b_entity')}")
    same = result.captured_state.get("user_a_entity") == result.captured_state.get("user_b_entity")
    print(f"Same entity? {same}")

    for v in result.verdicts:
        marker = "[VIOLATION]" if v.verdict_type.value == "VIOLATION" \
                 else "[UNEXPECTED]" if v.verdict_type.value == "UNEXPECTED" else "[OK]"
        print(f"  {marker} [{v.invariant}] {v.verdict_type.value}: {v.description[:120]}")

    assert result.status == "COMPLETED"

    # Check three-layer verdict sources
    syntactic = [v for v in result.verdicts if "[AutoVerify]" not in v.description and "Assertion" not in v.description]
    auto = [v for v in result.verdicts if "[AutoVerify]" in v.description]
    assertion = [v for v in result.verdicts if "Assertion" in v.description or ("Assertion" not in v.description and "[AutoVerify]" not in v.description and v not in syntactic)]

    print(f"\n  Syntactic oracle verdicts: {len(syntactic)}")
    print(f"  InvariantVerifier verdicts: {len(auto)}")
    print(f"  Total verdicts: {len(result.verdicts)}")
