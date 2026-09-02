"""Tests for PlatformVerifier. No Docker, no LLM, no platform dependency."""
import pytest
from src.stateful.models import UniversalLoginContext
from src.stateful.platform_verifier import PlatformVerifier
from src.models.types import VerdictType


def _ctx(**kwargs) -> UniversalLoginContext:
    defaults = dict(
        login_type="password",
        sent_identity="alice",
        granted_identity="alice",
        login_success=True,
        http_status=200,
        granted_identity_id="uid-123",
        granted_permissions=["user-role"],
        configured_permissions=["user-role"],
    )
    defaults.update(kwargs)
    return UniversalLoginContext(**defaults)


@pytest.fixture
def verifier():
    return PlatformVerifier()


def test_clean_login_no_verdicts(verifier):
    assert verifier.verify_login(_ctx()) == []

def test_case_divergence(verifier):
    verdicts = verifier.verify_login(_ctx(sent_identity="Alice", granted_identity="alice"))
    assert any("case" in v.description.lower() for v in verdicts)
    assert all(v.verdict_type == VerdictType.UNEXPECTED for v in verdicts)

def test_whitespace_divergence(verifier):
    verdicts = verifier.verify_login(_ctx(sent_identity="alice", granted_identity="alice "))
    assert any("whitespace" in v.description.lower() for v in verdicts)

def test_complete_mismatch(verifier):
    verdicts = verifier.verify_login(_ctx(sent_identity="alice", granted_identity="bob"))
    assert any(v.verdict_type == VerdictType.VIOLATION for v in verdicts)

def test_empty_identity_accepted(verifier):
    verdicts = verifier.verify_login(_ctx(sent_identity="", granted_identity="alice"))
    assert any("empty" in v.description.lower() for v in verdicts)

def test_permission_escalation(verifier):
    verdicts = verifier.verify_login(_ctx(
        configured_permissions=["user-role"],
        granted_permissions=["user-role", "admin-role"],
    ))
    assert any("escalation" in v.description.lower() for v in verdicts)

def test_no_escalation_when_equal(verifier):
    verdicts = verifier.verify_login(_ctx(
        configured_permissions=["user-role", "admin-role"],
        granted_permissions=["user-role", "admin-role"],
    ))
    escalation = [v for v in verdicts if "escalation" in v.description.lower()]
    assert escalation == []

def test_audience_bypass(verifier):
    verdicts = verifier.verify_login(_ctx(
        sent_audience="wrong-service",
        configured_constraints={"bound_audiences": ["correct-service"]},
    ))
    assert any(v.verdict_type == VerdictType.VIOLATION for v in verdicts)

def test_identity_collision_cross_user(verifier):
    ctx_a = _ctx(sent_identity="alice", granted_identity_id="same-id", auth_as="user_A")
    ctx_b = _ctx(sent_identity="bob", granted_identity_id="same-id", auth_as="user_B")
    verdicts = verifier.verify_cross_user([ctx_a, ctx_b])
    assert any("collision" in v.description.lower() for v in verdicts)

def test_permission_divergence(verifier):
    ctx_a = _ctx(granted_identity_id="id-1", granted_permissions=["read"], auth_as="user_A")
    ctx_b = _ctx(granted_identity_id="id-1", granted_permissions=["admin"], auth_as="user_B")
    verdicts = verifier.verify_cross_user([ctx_a, ctx_b])
    assert any("divergence" in v.description.lower() for v in verdicts)

def test_failed_login_no_verdicts(verifier):
    assert verifier.verify_login(_ctx(login_success=False)) == []


def test_universal_context_from_captures():
    """Verify that abstract suffix names align between writer and reader."""
    from src.stateful.sequence_executor import SequenceExecutor
    from src.models.platform_profile import PlatformProfile

    profile = PlatformProfile.from_json("src/profiles/keycloak.json")
    executor = SequenceExecutor(profile=profile, protocol="oidc_jwt")

    # Simulate what _captures_from_profile + response extraction would produce
    executor.captures = {
        "user_A_entity_id": "uid-abc-123",
        "user_A_display_name": "alice",
        "user_A_policies": ["user-role", "default-roles-valence"],
        "user_A_groups": ["/developers"],
        "user_A_email": "alice@test.local",
        "user_A_login_success": True,
        "user_A_login_status": 200,
    }

    # Create minimal events
    from src.stateful.models import Event, EventResult
    login_event = Event(
        event_type="login_with_password",
        params={"username": "alice", "password": "pass", "client_id": "test"},
        auth_as="user_A",
    )
    login_result = EventResult(event=login_event, success=True, http_status=200)

    contexts = executor._build_universal_contexts([login_event], [login_result])

    assert len(contexts) == 1
    ctx = contexts[0]
    assert ctx.login_type == "password"
    assert ctx.sent_identity == "alice"
    assert ctx.granted_identity == "alice", \
        f"Expected 'alice', got '{ctx.granted_identity}' — capture suffix mismatch?"
    assert ctx.granted_identity_id == "uid-abc-123", \
        f"Expected 'uid-abc-123', got '{ctx.granted_identity_id}' — capture suffix mismatch?"
    assert "user-role" in ctx.granted_permissions, \
        f"Expected user-role in permissions, got {ctx.granted_permissions}"
    assert "/developers" in ctx.granted_groups

    # Now run PlatformVerifier on it
    pv = PlatformVerifier(profile=profile)
    verdicts = pv.verify_login(ctx)
    # Clean login — should have 0 or only informational verdicts
    violations = [v for v in verdicts if v.verdict_type == VerdictType.VIOLATION]
    assert violations == [], f"Clean login should not have violations: {violations}"


def test_universal_context_escalation_detected():
    """Verify PlatformVerifier catches escalation from universal context."""
    from src.stateful.sequence_executor import SequenceExecutor
    from src.models.platform_profile import PlatformProfile

    profile = PlatformProfile.from_json("src/profiles/keycloak.json")
    executor = SequenceExecutor(profile=profile, protocol="oidc_jwt")

    executor.captures = {
        "user_A_entity_id": "uid-abc",
        "user_A_display_name": "alice",
        "user_A_policies": ["user-role", "admin-role", "default-roles-valence"],
        "user_A_email": "alice@test.local",
        "user_A_login_success": True,
    }

    from src.stateful.models import Event, EventResult
    # Setup events: only assigned user-role
    setup_event = Event(event_type="create_policy", params={"role_name": "user-role"}, auth_as="admin")
    assign_event = Event(event_type="assign_user_role", params={"role_name": "user-role"}, auth_as="admin")
    login_event = Event(
        event_type="login_with_password",
        params={"username": "alice", "password": "pass"},
        auth_as="user_A",
    )
    login_result = EventResult(event=login_event, success=True, http_status=200)

    contexts = executor._build_universal_contexts(
        [setup_event, assign_event, login_event],
        [EventResult(event=setup_event), EventResult(event=assign_event), login_result],
    )

    assert len(contexts) == 1
    ctx = contexts[0]
    assert ctx.configured_permissions == ["user-role"]  # Only the assigned role

    pv = PlatformVerifier(profile=profile)
    verdicts = pv.verify_login(ctx)
    escalation = [v for v in verdicts if "escalation" in v.description.lower()]
    assert escalation, f"Expected escalation verdict for admin-role, got {[v.description for v in verdicts]}"
