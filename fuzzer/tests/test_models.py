"""Tests for data model serialization round-trips."""

from datetime import datetime, timezone

from src.models.types import (
    AuthResult,
    CampaignResult,
    Confidence,
    Credential,
    Invariant,
    MutationRecord,
    Platform,
    Protocol,
    Verdict,
    VerdictType,
)


class TestCredential:
    def test_round_trip(self):
        c = Credential(
            protocol=Protocol.JWT,
            raw_token="eyJ...",
            headers={"alg": "RS256"},
            claims={"sub": "alice"},
            metadata={"role": "test"},
        )
        d = c.to_dict()
        c2 = Credential.from_dict(d)
        assert c2.protocol == Protocol.JWT
        assert c2.raw_token == "eyJ..."
        assert c2.claims["sub"] == "alice"

    def test_protocol_serializes_as_string(self):
        c = Credential(protocol=Protocol.SAML)
        d = c.to_dict()
        assert d["protocol"] == "saml"


class TestAuthResult:
    def test_round_trip(self):
        now = datetime.now(timezone.utc)
        ar = AuthResult(
            success=True,
            platform=Platform.VAULT,
            protocol=Protocol.JWT,
            downstream_token="tok123",
            timestamp=now,
        )
        d = ar.to_dict()
        assert d["platform"] == "vault"
        assert d["protocol"] == "jwt"
        assert isinstance(d["timestamp"], str)

        ar2 = AuthResult.from_dict(d)
        assert ar2.success is True
        assert ar2.platform == Platform.VAULT
        assert ar2.downstream_token == "tok123"

    def test_error_result(self):
        ar = AuthResult(
            success=False,
            platform=Platform.KEYCLOAK,
            protocol=Protocol.OAUTH2_CODE,
            error_message="invalid_grant",
            http_status=400,
        )
        d = ar.to_dict()
        ar2 = AuthResult.from_dict(d)
        assert ar2.success is False
        assert ar2.error_message == "invalid_grant"


class TestVerdict:
    def test_round_trip(self):
        v = Verdict(
            invariant=Invariant.I1_PROOF_INTEGRITY.value,
            verdict_type=VerdictType.VIOLATION,
            confidence="HIGH",
            description="alg=none accepted",
            evidence={"detail": "unsigned token"},
        )
        d = v.to_dict()
        assert d["invariant"] == "I1"
        assert d["confidence"] == "HIGH"
        assert d["verdict_type"] == "VIOLATION"

        v2 = Verdict.from_dict(d)
        assert v2.invariant == "I1"
        assert v2.verdict_type == VerdictType.VIOLATION


class TestMutationRecord:
    def test_round_trip(self):
        m = MutationRecord(
            mutation_type="claim_tamper",
            target_field="sub",
            original_value="alice",
            mutated_value="admin",
            description="Changed subject claim",
        )
        d = m.to_dict()
        m2 = MutationRecord.from_dict(d)
        assert m2.mutation_type == "claim_tamper"
        assert m2.original_value == "alice"
        assert m2.mutated_value == "admin"


class TestCampaignResult:
    def test_round_trip(self):
        cr = CampaignResult(
            campaign_id="test-001",
            platform=Platform.DEX,
            protocol=Protocol.SAML,
            total_tests=50,
        )
        d = cr.to_dict()
        assert d["platform"] == "dex"

        cr2 = CampaignResult.from_dict(d)
        assert cr2.campaign_id == "test-001"
        assert cr2.platform == Platform.DEX
        assert cr2.total_tests == 50

    def test_datetime_serialization(self):
        now = datetime.now(timezone.utc)
        cr = CampaignResult(
            platform=Platform.VAULT,
            protocol=Protocol.JWT,
            start_time=now,
            end_time=now,
        )
        d = cr.to_dict()
        cr2 = CampaignResult.from_dict(d)
        assert isinstance(cr2.start_time, datetime)
        assert isinstance(cr2.end_time, datetime)
