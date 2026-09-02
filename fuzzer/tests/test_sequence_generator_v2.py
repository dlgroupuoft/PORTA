"""Tests for protocol-abstracted SequenceGenerator (v2)."""
import pytest
from unittest.mock import MagicMock, patch

from src.models.platform_profile import PlatformProfile
from src.stateful.sequence_generator import SequenceGenerator, INVARIANT_DEFINITIONS
from src.stateful.protocol_operations import PROTOCOL_OPERATIONS, CROSS_PLATFORM_ATTACK_PATTERNS
from src.stateful.models import Event, EventSequence, OracleCheck


class TestProtocolOperations:
    def test_operations_defined(self):
        assert "login_with_jwt" in PROTOCOL_OPERATIONS
        assert "enable_auth_method" in PROTOCOL_OPERATIONS
        assert "verify_granted_identity" in PROTOCOL_OPERATIONS
        assert len(PROTOCOL_OPERATIONS) >= 15

    def test_attack_patterns_per_invariant(self):
        for inv in ["I1", "I2", "I3", "I4", "I5"]:
            assert inv in CROSS_PLATFORM_ATTACK_PATTERNS
            assert len(CROSS_PLATFORM_ATTACK_PATTERNS[inv]) >= 1


class TestSequenceGeneratorV2:
    @pytest.fixture
    def vault_profile(self):
        return PlatformProfile.from_json("src/profiles/vault.json")

    @pytest.fixture
    def mock_llm(self):
        return MagicMock()

    def test_init_with_profile(self, mock_llm, vault_profile):
        gen = SequenceGenerator(mock_llm, profile=vault_profile)
        assert gen.profile is not None
        assert gen.profile.name == "vault"

    def test_init_legacy_mode(self, mock_llm):
        gen = SequenceGenerator(mock_llm)
        assert gen.profile is None

    def test_build_system_prompt_v2(self, mock_llm, vault_profile):
        gen = SequenceGenerator(mock_llm, profile=vault_profile)
        prompt = gen._build_system_prompt_v2("oidc_jwt")
        assert "vault" in prompt
        assert "oidc_jwt" in prompt
        assert "Available Operations" in prompt
        assert "login_with_jwt" in prompt
        assert "Platform-Specific Constraints" in prompt
        assert "bound_claims" in prompt

    def test_build_system_prompt_legacy(self, mock_llm):
        gen = SequenceGenerator(mock_llm)
        prompt = gen._build_system_prompt()
        assert "HashiCorp Vault" in prompt
        assert "Available Event Types" in prompt

    def test_validate_profile_mode(self, mock_llm, vault_profile):
        gen = SequenceGenerator(mock_llm, profile=vault_profile)
        seq = EventSequence(
            sequence_id="test_1",
            description="Test",
            invariant_hypothesis="I4",
            events=[
                Event(event_type="create_auth_role", params={}, auth_as="admin"),
                Event(event_type="login_with_jwt", params={}, auth_as="user_A"),
                Event(event_type="verify_granted_identity", params={}, auth_as="session_user_A"),
            ],
            oracle_checks=[
                OracleCheck(
                    check_id="c1", invariant="I4",
                    assertion="x != y", violation_description="test",
                )
            ],
            primary_invariant="I4",
        )
        assert gen._validate_sequence(seq) is True

    def test_validate_profile_mode_unknown_op_filtered(self, mock_llm, vault_profile):
        """Unknown ops are filtered out — sequence is salvaged if login+verify remain."""
        gen = SequenceGenerator(mock_llm, profile=vault_profile)
        seq = EventSequence(
            sequence_id="test_2",
            description="Test",
            invariant_hypothesis="I4",
            events=[
                Event(event_type="completely_unknown_op", params={}, auth_as="admin"),
                Event(event_type="login_with_jwt", params={}, auth_as="user_A"),
                Event(event_type="verify_granted_identity", params={}, auth_as="session_user_A"),
            ],
            oracle_checks=[
                OracleCheck(check_id="c1", invariant="I4", assertion="x != y", violation_description="test")
            ],
            primary_invariant="I4",
        )
        assert gen._validate_sequence(seq) is True
        assert len(seq.events) == 2  # unknown op filtered

    def test_validate_profile_mode_all_unknown_ops_rejected(self, mock_llm, vault_profile):
        """When filtering removes login/verify, sequence is rejected."""
        gen = SequenceGenerator(mock_llm, profile=vault_profile)
        seq = EventSequence(
            sequence_id="test_2b",
            description="Test",
            invariant_hypothesis="I4",
            events=[
                Event(event_type="fake_login", params={}, auth_as="admin"),
                Event(event_type="fake_verify", params={}, auth_as="session_user_A"),
            ],
            oracle_checks=[
                OracleCheck(check_id="c1", invariant="I4", assertion="x != y", violation_description="test")
            ],
            primary_invariant="I4",
        )
        assert gen._validate_sequence(seq) is False

    def test_validate_legacy_mode(self, mock_llm):
        gen = SequenceGenerator(mock_llm)
        seq = EventSequence(
            sequence_id="test_3",
            description="Test",
            invariant_hypothesis="I4",
            events=[
                Event(event_type="setup_jwt_role", params={}, auth_as="admin"),
                Event(event_type="login_jwt", params={}, auth_as="user_A"),
                Event(event_type="verify_token_self", params={}, auth_as="session_user_A"),
            ],
            oracle_checks=[
                OracleCheck(check_id="c1", invariant="I4", assertion="x != y", violation_description="test")
            ],
            primary_invariant="I4",
        )
        assert gen._validate_sequence(seq) is True

    def test_generate_uses_profile_prompt(self, mock_llm, vault_profile):
        """When profile is set, generate() should use v2 prompt."""
        mock_llm.generate_json.return_value = {"sequences": []}
        gen = SequenceGenerator(mock_llm, profile=vault_profile)
        gen.generate(invariant_focus="I4", num_sequences=1)
        # Check that the system prompt was called
        call_args = mock_llm.generate_json.call_args
        system_prompt = call_args[0][0]
        assert "vault" in system_prompt
        assert "Available Operations" in system_prompt

    def test_generate_legacy_prompt(self, mock_llm):
        """Without profile, generate() should use legacy prompt."""
        mock_llm.generate_json.return_value = {"sequences": []}
        gen = SequenceGenerator(mock_llm)
        gen.generate(invariant_focus="I4", num_sequences=1)
        call_args = mock_llm.generate_json.call_args
        system_prompt = call_args[0][0]
        assert "HashiCorp Vault" in system_prompt

    def test_parse_sequence(self, mock_llm, vault_profile):
        gen = SequenceGenerator(mock_llm, profile=vault_profile)
        data = {
            "id": "seq_test",
            "description": "A test",
            "invariant_hypothesis": "I4: test",
            "primary_invariant": "I4",
            "cve_analog": "none",
            "events": [
                {"event_type": "login_with_jwt", "params": {"role": "test"}, "auth_as": "user_A"},
            ],
            "oracle_checks": [
                {"check_id": "c1", "invariant": "I4", "assertion": "x == y", "violation_description": "test"},
            ],
        }
        seq = gen._parse_sequence(data)
        assert seq.sequence_id == "seq_test"
        assert len(seq.events) == 1
        assert seq.events[0].event_type == "login_with_jwt"

    def test_validate_login_with_password(self, mock_llm):
        """login_with_password should be accepted on platforms that have it in their profile."""
        kc_profile = PlatformProfile.from_json("src/profiles/keycloak.json")
        gen = SequenceGenerator(mock_llm, profile=kc_profile)
        seq = EventSequence(
            sequence_id="test_kc_login",
            description="Test Keycloak password login",
            invariant_hypothesis="I4",
            events=[
                Event(event_type="create_user", params={}, auth_as="admin"),
                Event(event_type="login_with_password", params={
                    "username": "alice", "password": "pass", "client_id": "test",
                    "grant_type": "password",
                }, auth_as="user_A"),
                Event(event_type="verify_granted_identity", params={}, auth_as="session_user_A"),
            ],
            oracle_checks=[
                OracleCheck(check_id="c1", invariant="I4", assertion="x != y", violation_description="test")
            ],
            primary_invariant="I4",
        )
        # login_with_password is in Keycloak's profile api_mapping
        assert gen._validate_sequence(seq, protocol="oidc_jwt") is True

    def test_coverage_gaps_in_user_prompt(self, mock_llm, vault_profile):
        mock_llm.generate_json.return_value = {"sequences": []}
        gen = SequenceGenerator(mock_llm, profile=vault_profile)
        gen.generate(
            invariant_focus="I4", num_sequences=1,
            coverage_gaps=["I4 × cross_user_collision × single_user × static"]
        )
        call_args = mock_llm.generate_json.call_args
        user_prompt = call_args[0][1]
        assert "UNCOVERED TEST SPACE" in user_prompt
        assert "cross_user_collision" in user_prompt
