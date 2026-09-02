"""Unit tests for InvariantVerifier. No Docker, no LLM required."""
import pytest

from src.stateful.models import LoginContext
from src.stateful.invariant_verifier import InvariantVerifier
from src.models.types import VerdictType


def _clean_ctx(**kwargs) -> LoginContext:
    """Build a minimal clean LoginContext with sensible defaults."""
    defaults = dict(
        jwt_claims={"sub": "alice", "aud": "vault-prod"},
        role_name="test-role",
        role_config={
            "user_claim": "sub",
            "bound_audiences": ["vault-prod"],
            "token_policies": ["readonly"],
            "bound_claims": {},
        },
        login_success=True,
        http_status=200,
        granted_entity_id="ent-abc",
        granted_policies=["readonly", "default"],
        granted_metadata={"username": "alice"},
        entity_aliases=[{"name": "alice"}],
        entity_name="alice",
        entity_policies=[],
        identity_policies=[],
        group_ids=[],
        token_lookup={},
        auth_as="user_A",
    )
    defaults.update(kwargs)
    return LoginContext(**defaults)


@pytest.fixture
def verifier():
    return InvariantVerifier()


# ---------------------------------------------------------------------------
# 1. Clean login → no verdicts
# ---------------------------------------------------------------------------

def test_correct_login_produces_no_verdicts(verifier):
    ctx = _clean_ctx()
    verdicts = verifier.verify_login(ctx)
    assert verdicts == [], f"Expected no verdicts but got: {verdicts}"


# ---------------------------------------------------------------------------
# 2. Whitespace divergence
# ---------------------------------------------------------------------------

def test_whitespace_divergence_detected(verifier):
    ctx = _clean_ctx(
        jwt_claims={"sub": "alice", "aud": "vault-prod"},
        entity_aliases=[{"name": "alice "}],  # trailing space
    )
    verdicts = verifier.verify_login(ctx)
    assert any("whitespace" in v.description.lower() for v in verdicts), \
        f"Expected whitespace verdict, got: {[v.description for v in verdicts]}"
    assert all(v.verdict_type == VerdictType.UNEXPECTED for v in verdicts
               if "whitespace" in v.description.lower())


# ---------------------------------------------------------------------------
# 3. Case divergence
# ---------------------------------------------------------------------------

def test_case_divergence_detected(verifier):
    ctx = _clean_ctx(
        jwt_claims={"sub": "Alice", "aud": "vault-prod"},
        entity_aliases=[{"name": "alice"}],
        granted_metadata={"username": "Alice"},
    )
    verdicts = verifier.verify_login(ctx)
    assert any("case" in v.description.lower() for v in verdicts), \
        f"Expected case divergence verdict, got: {[v.description for v in verdicts]}"


# ---------------------------------------------------------------------------
# 4. Type coercion detected
# ---------------------------------------------------------------------------

def test_type_coercion_detected(verifier):
    ctx = _clean_ctx(
        jwt_claims={"sub": 12345, "aud": "vault-prod"},  # int sub
        entity_aliases=[{"name": "12345"}],              # stored as string
        granted_metadata={"username": "12345"},
    )
    verdicts = verifier.verify_login(ctx)
    assert any(
        v.evidence.get("mismatch_type") == "type_coercion"
        for v in verdicts
    ), f"Expected type_coercion in evidence, got: {[v.evidence for v in verdicts]}"


# ---------------------------------------------------------------------------
# 5. Empty sub accepted
# ---------------------------------------------------------------------------

def test_empty_sub_detected(verifier):
    ctx = _clean_ctx(
        jwt_claims={"sub": "", "aud": "vault-prod"},
        entity_aliases=[{"name": ""}],
        granted_metadata={"username": ""},
    )
    verdicts = verifier.verify_login(ctx)
    assert any("empty" in v.description.lower() for v in verdicts), \
        f"Expected empty-identity verdict, got: {[v.description for v in verdicts]}"


# ---------------------------------------------------------------------------
# 6. Audience bypass → VIOLATION
# ---------------------------------------------------------------------------

def test_audience_bypass_violation(verifier):
    ctx = _clean_ctx(
        jwt_claims={"sub": "alice", "aud": "wrong-service"},
        role_config={
            "user_claim": "sub",
            "bound_audiences": ["vault-prod"],
            "token_policies": ["readonly"],
            "bound_claims": {},
        },
    )
    verdicts = verifier.verify_login(ctx)
    violations = [v for v in verdicts if v.verdict_type == VerdictType.VIOLATION]
    assert any("audience" in v.description.lower() for v in violations), \
        f"Expected audience VIOLATION, got: {[v.description for v in verdicts]}"


# ---------------------------------------------------------------------------
# 7. No audience binding → UNEXPECTED
# ---------------------------------------------------------------------------

def test_no_audience_binding_unexpected(verifier):
    ctx = _clean_ctx(
        jwt_claims={"sub": "alice", "aud": "anything"},
        role_config={
            "user_claim": "sub",
            "bound_audiences": [],
            "token_policies": ["readonly"],
            "bound_claims": {},
        },
    )
    verdicts = verifier.verify_login(ctx)
    unexpected = [v for v in verdicts if v.verdict_type == VerdictType.UNEXPECTED]
    assert any("audience" in v.description.lower() for v in unexpected), \
        f"Expected no-audience-binding UNEXPECTED, got: {[v.description for v in verdicts]}"


# ---------------------------------------------------------------------------
# 8. Policy escalation
# ---------------------------------------------------------------------------

def test_policy_escalation(verifier):
    ctx = _clean_ctx(
        role_config={
            "user_claim": "sub",
            "bound_audiences": ["vault-prod"],
            "token_policies": ["readonly"],
            "bound_claims": {},
        },
        granted_policies=["readonly", "default", "admin"],  # extra "admin"
        identity_policies=[],
    )
    verdicts = verifier.verify_login(ctx)
    escalation = [
        v for v in verdicts
        if v.evidence.get("mismatch_type") == "policy_escalation"
    ]
    assert escalation, f"Expected policy_escalation verdict, got: {[v.description for v in verdicts]}"
    unexpected_policies = escalation[0].evidence.get("unexpected_policies", [])
    assert "admin" in unexpected_policies, \
        f"Expected 'admin' in unexpected_policies, got: {unexpected_policies}"


# ---------------------------------------------------------------------------
# 9. Entity collision across users
# ---------------------------------------------------------------------------

def test_entity_collision_cross_user(verifier):
    ctx_a = _clean_ctx(
        jwt_claims={"sub": "alice", "aud": "vault-prod"},
        granted_entity_id="ent-1",
        auth_as="user_A",
    )
    ctx_b = _clean_ctx(
        jwt_claims={"sub": "bob", "aud": "vault-prod"},
        granted_entity_id="ent-1",  # same entity!
        auth_as="user_B",
    )
    verdicts = verifier.verify_cross_user([ctx_a, ctx_b])
    assert any("collision" in v.description.lower() for v in verdicts), \
        f"Expected collision verdict, got: {[v.description for v in verdicts]}"


# ---------------------------------------------------------------------------
# 10. Collision with policy divergence → two verdicts
# ---------------------------------------------------------------------------

def test_collision_with_policy_divergence(verifier):
    ctx_a = _clean_ctx(
        jwt_claims={"sub": "alice", "aud": "vault-prod"},
        granted_entity_id="ent-1",
        granted_policies=["readonly", "default"],
        auth_as="user_A",
    )
    ctx_b = _clean_ctx(
        jwt_claims={"sub": "bob", "aud": "vault-prod"},
        granted_entity_id="ent-1",
        granted_policies=["admin", "default"],  # different policies
        auth_as="user_B",
    )
    verdicts = verifier.verify_cross_user([ctx_a, ctx_b])
    collision_verdicts = [v for v in verdicts if "collision" in v.description.lower()]
    divergence_verdicts = [v for v in verdicts if "divergence" in v.description.lower()]
    assert collision_verdicts, "Expected collision verdict"
    assert divergence_verdicts, "Expected policy divergence verdict"


# ---------------------------------------------------------------------------
# 11. bound_claims bypass → VIOLATION
# ---------------------------------------------------------------------------

def test_bound_claims_bypass(verifier):
    ctx = _clean_ctx(
        jwt_claims={"sub": "alice", "aud": "vault-prod", "department": "marketing"},
        role_config={
            "user_claim": "sub",
            "bound_audiences": ["vault-prod"],
            "token_policies": ["readonly"],
            "bound_claims": {"department": ["engineering"]},
        },
    )
    verdicts = verifier.verify_login(ctx)
    violations = [v for v in verdicts if v.verdict_type == VerdictType.VIOLATION]
    assert any("bound_claims" in v.description.lower() for v in violations), \
        f"Expected bound_claims VIOLATION, got: {[v.description for v in verdicts]}"


# ---------------------------------------------------------------------------
# 12. Identity policies without groups (orphan) → UNEXPECTED
# ---------------------------------------------------------------------------

def test_identity_policy_without_groups(verifier):
    ctx = _clean_ctx(
        identity_policies=["mystery-policy"],
        group_ids=[],
        entity_policies=[],
    )
    verdicts = verifier.verify_login(ctx)
    orphan = [
        v for v in verdicts
        if v.evidence.get("mismatch_type") == "orphan_identity_policies"
    ]
    assert orphan, \
        f"Expected orphan_identity_policies verdict, got: {[v.description for v in verdicts]}"
    assert all(v.verdict_type == VerdictType.UNEXPECTED for v in orphan)
