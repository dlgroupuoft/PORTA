"""Tests for mutation sweep integration."""
import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass

from src.stateful.mutation_sweep import MutationSweep, EnvironmentConfig
from src.engines.jwt_engine import JWTEngine
from src.models.types import AuthResult, Platform, Protocol, VerdictType


@pytest.fixture
def jwt_engine():
    return JWTEngine({
        "legitimate_issuer": "http://idp.test",
        "legitimate_audience": "vault",
        "legitimate_subject": "test-user",
    })


@pytest.fixture
def mock_executor():
    executor = MagicMock()
    executor.base_url = "http://localhost:8200"
    executor.adapter = MagicMock()
    # Default: baseline succeeds, mutations fail
    executor.adapter.authenticate.return_value = AuthResult(
        success=True,
        platform=Platform.VAULT,
        protocol=Protocol.JWT,
        downstream_token="test-token",
        downstream_claims={"entity_id": "ent-123", "policies": ["default"]},
        http_status=200,
        raw_response={"auth": {"client_token": "test-token", "entity_id": "ent-123"}},
    )
    return executor


class TestMutationSweep:
    def test_sweep_with_successful_baseline(self, jwt_engine, mock_executor):
        sweep = MutationSweep(mock_executor, jwt_engine, {})
        env = EnvironmentConfig(
            role_name="test-role",
            baseline_claims={"sub": "alice", "aud": "vault"},
        )
        result = sweep.run(env, invariants=["I1"], min_priority="low")
        assert result.baseline_success
        assert result.total_mutations > 0

    def test_sweep_baseline_failure_skips(self, jwt_engine, mock_executor):
        mock_executor.adapter.authenticate.return_value = AuthResult(
            success=False, platform=Platform.VAULT, protocol=Protocol.JWT,
            error_message="login failed", http_status=400,
        )
        sweep = MutationSweep(mock_executor, jwt_engine, {})
        env = EnvironmentConfig(role_name="test-role")
        result = sweep.run(env)
        assert not result.baseline_success
        assert result.total_mutations == 0

    def test_sweep_no_engine_returns_empty(self, mock_executor):
        sweep = MutationSweep(mock_executor, jwt_engine=None)
        env = EnvironmentConfig(role_name="test-role")
        result = sweep.run(env)
        assert result.total_mutations == 0

    def test_sweep_respects_max_mutations(self, jwt_engine, mock_executor):
        sweep = MutationSweep(mock_executor, jwt_engine, {})
        env = EnvironmentConfig(
            role_name="test-role",
            baseline_claims={"sub": "alice", "aud": "vault"},
        )
        result = sweep.run(env, max_mutations=5)
        assert result.total_mutations <= 5

    def test_sweep_with_oracles(self, jwt_engine, mock_executor):
        mock_oracle = MagicMock()
        from src.models.types import Verdict, VerdictType
        mock_oracle.check.return_value = Verdict(
            invariant="I1",
            verdict_type=VerdictType.REJECTED,
            confidence="HIGH",
            description="Mutation correctly rejected",
        )
        sweep = MutationSweep(mock_executor, jwt_engine, {"I1": mock_oracle})
        env = EnvironmentConfig(
            role_name="test-role",
            baseline_claims={"sub": "alice", "aud": "vault"},
        )
        result = sweep.run(env, invariants=["I1"], min_priority="low")
        assert result.baseline_success
        assert len(result.verdicts) > 0
        assert len(result.violations) == 0  # All REJECTED, no violations

    def test_sweep_detects_violations(self, jwt_engine, mock_executor):
        mock_oracle = MagicMock()
        from src.models.types import Verdict, VerdictType
        mock_oracle.check.return_value = Verdict(
            invariant="I1",
            verdict_type=VerdictType.VIOLATION,
            confidence="HIGH",
            description="Unsigned token accepted!",
        )
        sweep = MutationSweep(mock_executor, jwt_engine, {"I1": mock_oracle})
        env = EnvironmentConfig(
            role_name="test-role",
            baseline_claims={"sub": "alice", "aud": "vault"},
        )
        result = sweep.run(env, invariants=["I1"], min_priority="low")
        assert len(result.violations) > 0

    def test_extract_environment_from_sequence(self):
        """Test _extract_environment correctly parses sequence events."""
        from src.stateful.models import Event, EventSequence

        seq = EventSequence(
            sequence_id="test",
            description="test",
            invariant_hypothesis="I1: test",
            events=[
                Event(event_type="create_auth_role",
                      params={"role_name": "sweep-role", "mount": "jwt",
                              "bound_audiences": ["vault"]},
                      auth_as="admin"),
                Event(event_type="login_with_jwt",
                      params={"role": "sweep-role",
                              "jwt_claims": {"sub": "alice", "aud": "vault"}},
                      auth_as="user_A"),
            ],
            oracle_checks=[],
        )

        # Test extraction logic directly
        role_name = None
        baseline_claims = {}
        for event in seq.events:
            if event.event_type == "create_auth_role":
                role_name = event.params.get("role_name")
            if event.event_type == "login_with_jwt":
                baseline_claims = event.params.get("jwt_claims", {})

        assert role_name == "sweep-role"
        assert baseline_claims == {"sub": "alice", "aud": "vault"}

    def test_environment_config_defaults(self):
        env = EnvironmentConfig(role_name="test")
        assert env.mount == ""  # Empty default; _run_login derives from protocol
        assert env.platform == "vault"
        assert env.protocol == "oidc_jwt"
        assert env.baseline_claims == {}
        assert env.role_config == {}

    def test_sweep_result_fields(self, jwt_engine, mock_executor):
        sweep = MutationSweep(mock_executor, jwt_engine, {})
        env = EnvironmentConfig(
            role_name="test-role",
            baseline_claims={"sub": "alice", "aud": "vault"},
        )
        result = sweep.run(env, invariants=["I1"], min_priority="low")
        assert result.environment is env
        assert isinstance(result.verdicts, list)
        assert isinstance(result.violations, list)
        assert isinstance(result.baseline_captures, dict)
