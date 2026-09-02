"""Tests for CampaignReport, FindingRecord, SequenceRecord, and aggregate_runs."""

import json
import os
import tempfile

import pytest

from src.reporting.campaign_report import CampaignReport, FindingRecord, SequenceRecord
from src.reporting.aggregate_runs import aggregate_runs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_finding(
    sequence_id="seq-001",
    generation_strategy="coverage",
    verdict_path="oracle",
    invariant="I4",
    identified_invariant="I4",
    verdict_type="VIOLATION",
    confidence="HIGH",
    description="Principal binding violated: entity aliasing allowed",
    cve_analog="CVE-2023-0001",
) -> FindingRecord:
    finding_id = f"{sequence_id}:{verdict_path}:{invariant}"
    return FindingRecord(
        finding_id=finding_id,
        sequence_id=sequence_id,
        sequence_description="Test sequence description",
        generation_strategy=generation_strategy,
        verdict_path=verdict_path,
        invariant=invariant,
        identified_invariant=identified_invariant,
        verdict_type=verdict_type,
        confidence=confidence,
        description=description,
        cve_analog=cve_analog,
        evidence={"key": "value"},
    )


def _make_sequence(
    sequence_id="seq-001",
    generation_strategy="coverage",
    status="COMPLETED",
    primary_invariant="I4",
    events_total=3,
    events_succeeded=3,
) -> SequenceRecord:
    return SequenceRecord(
        sequence_id=sequence_id,
        description="Test scenario description",
        generation_strategy=generation_strategy,
        primary_invariant=primary_invariant,
        invariant_hypothesis=f"{primary_invariant}: hypothesis text",
        cve_analog="CVE-2023-0001",
        status=status,
        events_total=events_total,
        events_succeeded=events_succeeded,
        events_failed=events_total - events_succeeded,
        used_examples=True,
        num_examples=2,
        events=[{"event_type": "login_with_jwt", "params": {}, "auth_as": "admin",
                 "expected_outcome": "success", "captures": {}, "phase": "login"}],
        oracle_checks=[{"check_id": "c1", "invariant": primary_invariant,
                        "assertion": "a == b", "violation_description": "desc", "cve_analog": ""}],
        sequence_metadata={"generation_strategy": generation_strategy},
        captured_state={"token": "abc123"},
    )


def _make_full_report() -> CampaignReport:
    report = CampaignReport(
        campaign_id="test-20240101",
        timestamp="2024-01-01T00:00:00+00:00",
        platform="vault",
        base_url="http://localhost:8200",
        llm_model="gpt-5.2",
        invariants_tested=["I4", "I5"],
    )

    # Two coverage sequences, one attack sequence
    report.add_sequence(_make_sequence("s1", "coverage", "COMPLETED", "I4", 3, 3))
    report.add_sequence(_make_sequence("s2", "coverage", "SETUP_FAILED", "I5", 2, 0))
    report.add_sequence(_make_sequence("s3", "attack", "COMPLETED", "I4", 4, 4))

    # Findings from different paths and strategies
    report.add_finding(_make_finding("s1", "coverage", "oracle", "I4"))
    report.add_finding(_make_finding("s1", "coverage", "oracle_guided", "I4",
                                     description="Oracle guided: same root cause"))
    report.add_finding(_make_finding("s3", "attack", "plain_llm", "I4",
                                     description="Plain LLM finding: different invariant"))

    return report


# ---------------------------------------------------------------------------
# FindingRecord tests
# ---------------------------------------------------------------------------

class TestFindingRecord:
    def test_dedup_key_same_description_same_key(self):
        f1 = _make_finding(sequence_id="s1", description="exact same text")
        f2 = _make_finding(sequence_id="s2", description="exact same text")
        assert f1.dedup_key() == f2.dedup_key()

    def test_dedup_key_different_description_different_key(self):
        f1 = _make_finding(description="violation A — entity alias")
        f2 = _make_finding(description="violation B — token replay")
        assert f1.dedup_key() != f2.dedup_key()

    def test_dedup_key_different_identified_invariant_different_key(self):
        # dedup_key uses identified_invariant (the actual violation) not sequence invariant
        f1 = _make_finding(identified_invariant="I4", description="same text")
        f2 = _make_finding(identified_invariant="I5", description="same text")
        assert f1.dedup_key() != f2.dedup_key()

    def test_dedup_key_strategy_does_not_differentiate(self):
        # Same root cause (same description + invariant) from different strategies
        # is intentionally deduped together — root cause is strategy-agnostic
        f1 = _make_finding(generation_strategy="coverage", description="same text")
        f2 = _make_finding(generation_strategy="attack", description="same text")
        assert f1.dedup_key() == f2.dedup_key()

    def test_dedup_key_case_insensitive(self):
        f1 = _make_finding(description="Principal Binding Violated")
        f2 = _make_finding(description="principal binding violated")
        assert f1.dedup_key() == f2.dedup_key()

    def test_to_dict_roundtrip(self):
        f = _make_finding()
        d = f.to_dict()
        assert d["finding_id"] == f.finding_id
        assert d["generation_strategy"] == "coverage"
        assert d["verdict_path"] == "oracle"
        assert d["invariant"] == "I4"
        assert d["verdict_type"] == "VIOLATION"
        assert d["triage_result"] == ""


# ---------------------------------------------------------------------------
# SequenceRecord tests
# ---------------------------------------------------------------------------

class TestSequenceRecord:
    def test_to_dict_includes_all_fields(self):
        s = _make_sequence()
        d = s.to_dict()
        assert d["sequence_id"] == "seq-001"
        assert d["generation_strategy"] == "coverage"
        assert d["status"] == "COMPLETED"
        assert d["events_total"] == 3
        assert d["events_succeeded"] == 3
        assert d["events_failed"] == 0
        assert len(d["events"]) == 1
        assert len(d["oracle_checks"]) == 1
        assert d["sequence_metadata"]["generation_strategy"] == "coverage"

    def test_captured_state_truncated_to_200(self):
        s = _make_sequence()
        s.captured_state = {"long_key": "x" * 500}
        d = s.to_dict()
        assert len(d["captured_state"]["long_key"]) == 200


# ---------------------------------------------------------------------------
# CampaignReport — finalize() tests
# ---------------------------------------------------------------------------

class TestCampaignReportFinalize:
    def setup_method(self):
        self.report = _make_full_report()
        self.report.finalize()
        self.summary = self.report.summary

    def test_total_sequences(self):
        assert self.summary["total_sequences"] == 3

    def test_by_strategy_counts(self):
        assert self.summary["by_strategy"]["coverage"] == 2
        assert self.summary["by_strategy"]["attack"] == 1

    def test_by_status_counts(self):
        assert self.summary["by_status"]["COMPLETED"] == 2
        assert self.summary["by_status"]["SETUP_FAILED"] == 1

    def test_total_findings(self):
        assert self.summary["total_findings"] == 3

    def test_findings_by_strategy(self):
        assert self.summary["findings_by_strategy"]["coverage"] == 2
        assert self.summary["findings_by_strategy"]["attack"] == 1

    def test_findings_by_verdict_path(self):
        by_path = self.summary["findings_by_verdict_path"]
        assert by_path.get("oracle", 0) == 1
        assert by_path.get("oracle_guided", 0) == 1
        assert by_path.get("plain_llm", 0) == 1

    def test_findings_by_invariant(self):
        assert self.summary["findings_by_invariant"]["I4"] == 3

    def test_execution_rate(self):
        rates = self.summary["execution_rate"]
        assert rates["coverage"] == pytest.approx(0.5)  # 1/2 completed
        assert rates["attack"] == pytest.approx(1.0)    # 1/1 completed

    def test_event_success_rates(self):
        rates = self.summary["event_success_rates"]
        # coverage: s1 has 3/3, s2 has 0/2 → 3/5 = 0.6
        assert rates["coverage"] == pytest.approx(0.6)
        # attack: s3 has 4/4 → 1.0
        assert rates["attack"] == pytest.approx(1.0)

    def test_cross_tabulation(self):
        tab = self.summary["cross_tab"]
        assert tab.get("coverage:oracle", 0) == 1
        assert tab.get("coverage:oracle_guided", 0) == 1
        assert tab.get("attack:plain_llm", 0) == 1

    def test_unique_findings_dedup(self):
        # Two findings with same description (oracle vs oracle_guided) → 2 unique
        # because verdict_path differs in dedup_key
        # All three have different descriptions or different strategies, so expect 3
        assert self.summary["unique_findings"] == 3
        assert self.summary["duplicate_count"] == 0

    def test_dedup_removes_true_duplicates(self):
        r = CampaignReport(campaign_id="x", timestamp="", platform="vault",
                           base_url="", llm_model="gpt-5.2")
        r.add_finding(_make_finding("s1", "coverage", "oracle", "I4",
                                    description="exact same text"))
        r.add_finding(_make_finding("s2", "coverage", "oracle", "I4",
                                    description="exact same text"))
        r.finalize()
        assert r.summary["unique_findings"] == 1
        assert r.summary["duplicate_count"] == 1


# ---------------------------------------------------------------------------
# CampaignReport — save() directory structure tests
# ---------------------------------------------------------------------------

class TestCampaignReportSave:
    def test_save_creates_expected_structure(self):
        report = _make_full_report()
        report.finalize()

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_dir = report.save(tmpdir)

            assert os.path.isdir(campaign_dir)
            assert os.path.isfile(os.path.join(campaign_dir, "summary.json"))
            assert os.path.isfile(os.path.join(campaign_dir, "sequences.json"))
            assert os.path.isfile(os.path.join(campaign_dir, "findings.json"))
            assert os.path.isfile(os.path.join(campaign_dir, "unique_findings.json"))

            # Strategy subdirectories
            for strategy in ["coverage", "attack"]:
                strat_dir = os.path.join(campaign_dir, strategy)
                assert os.path.isdir(strat_dir), f"Missing directory: {strategy}/"
                assert os.path.isfile(os.path.join(strat_dir, "sequences.json"))
                assert os.path.isfile(os.path.join(strat_dir, "findings.json"))

    def test_save_coverage_sequences_only_coverage(self):
        report = _make_full_report()
        report.finalize()

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_dir = report.save(tmpdir)
            with open(os.path.join(campaign_dir, "coverage", "sequences.json")) as f:
                cov_seqs = json.load(f)
            assert all(s["generation_strategy"] == "coverage" for s in cov_seqs)
            assert len(cov_seqs) == 2

    def test_save_attack_sequences_only_attack(self):
        report = _make_full_report()
        report.finalize()

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_dir = report.save(tmpdir)
            with open(os.path.join(campaign_dir, "attack", "sequences.json")) as f:
                atk_seqs = json.load(f)
            assert all(s["generation_strategy"] == "attack" for s in atk_seqs)
            assert len(atk_seqs) == 1

    def test_save_verdict_path_split_files(self):
        report = _make_full_report()
        report.finalize()

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_dir = report.save(tmpdir)
            # oracle finding should be in coverage/findings_oracle.json
            oracle_path = os.path.join(campaign_dir, "coverage", "findings_oracle.json")
            assert os.path.isfile(oracle_path)
            with open(oracle_path) as f:
                oracle_findings = json.load(f)
            assert all(f["verdict_path"] == "oracle" for f in oracle_findings)

            # oracle_guided finding
            og_path = os.path.join(campaign_dir, "coverage", "findings_oracle_guided.json")
            assert os.path.isfile(og_path)

    def test_save_unique_findings_deduplicated(self):
        report = CampaignReport(campaign_id="dup-test", timestamp="", platform="vault",
                                base_url="", llm_model="gpt-5.2")
        report.add_sequence(_make_sequence("s1"))
        report.add_finding(_make_finding("s1", description="dup description"))
        report.add_finding(_make_finding("s1", description="dup description"))
        report.add_finding(_make_finding("s1", description="unique description"))
        report.finalize()

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_dir = report.save(tmpdir)
            with open(os.path.join(campaign_dir, "unique_findings.json")) as f:
                unique = json.load(f)
            assert len(unique) == 2  # "dup description" deduped to 1 + "unique description"

    def test_save_summary_json_valid(self):
        report = _make_full_report()
        report.finalize()

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_dir = report.save(tmpdir)
            with open(os.path.join(campaign_dir, "summary.json")) as f:
                summary = json.load(f)
            assert summary["total_sequences"] == 3
            assert summary["total_findings"] == 3

    def test_save_sequences_json_has_replay_fields(self):
        """sequences.json must have oracle_checks and events for replay."""
        report = _make_full_report()
        report.finalize()

        with tempfile.TemporaryDirectory() as tmpdir:
            campaign_dir = report.save(tmpdir)
            with open(os.path.join(campaign_dir, "sequences.json")) as f:
                seqs = json.load(f)
            for s in seqs:
                assert "events" in s
                assert "oracle_checks" in s
                assert "sequence_metadata" in s


# ---------------------------------------------------------------------------
# aggregate_runs tests
# ---------------------------------------------------------------------------

def _write_mock_campaign(tmpdir: str, campaign_id: str, summary: dict,
                          findings: list | None = None) -> str:
    """Write a mock campaign directory with summary.json and findings.json."""
    campaign_dir = os.path.join(tmpdir, campaign_id)
    os.makedirs(campaign_dir, exist_ok=True)
    with open(os.path.join(campaign_dir, "summary.json"), "w") as f:
        json.dump(summary, f)
    if findings is not None:
        with open(os.path.join(campaign_dir, "findings.json"), "w") as f:
            json.dump(findings, f)
    return campaign_dir


class TestAggregateRuns:
    def test_no_summaries_returns_error(self):
        result = aggregate_runs(["/nonexistent/path1", "/nonexistent/path2"])
        assert "error" in result

    def test_scalar_mean_and_std(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            d1 = _write_mock_campaign(tmpdir, "run1", {
                "total_sequences": 10, "total_findings": 4,
                "unique_findings": 3, "duplicate_count": 1,
                "findings_by_strategy": {}, "findings_by_verdict_path": {},
                "execution_rate": {}, "event_success_rates": {},
            })
            d2 = _write_mock_campaign(tmpdir, "run2", {
                "total_sequences": 10, "total_findings": 6,
                "unique_findings": 5, "duplicate_count": 1,
                "findings_by_strategy": {}, "findings_by_verdict_path": {},
                "execution_rate": {}, "event_success_rates": {},
            })

            result = aggregate_runs([d1, d2])

        assert result["num_runs"] == 2
        metrics = result["metrics"]
        assert metrics["total_findings"]["mean"] == pytest.approx(5.0)
        # statistics.stdev([4, 6]) is sample std = sqrt(2) ≈ 1.414
        import math
        assert metrics["total_findings"]["std"] == pytest.approx(math.sqrt(2), rel=0.01)
        assert metrics["total_findings"]["min"] == 4
        assert metrics["total_findings"]["max"] == 6
        assert metrics["total_findings"]["values"] == [4, 6]

    def test_single_run_std_is_zero(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            d1 = _write_mock_campaign(tmpdir, "run1", {
                "total_sequences": 5, "total_findings": 2,
                "unique_findings": 2, "duplicate_count": 0,
                "findings_by_strategy": {}, "findings_by_verdict_path": {},
                "execution_rate": {}, "event_success_rates": {},
            })
            result = aggregate_runs([d1])

        assert result["metrics"]["total_findings"]["std"] == 0.0

    def test_findings_by_strategy_aggregated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            d1 = _write_mock_campaign(tmpdir, "r1", {
                "total_sequences": 5, "total_findings": 3,
                "unique_findings": 3, "duplicate_count": 0,
                "findings_by_strategy": {"coverage": 2, "attack": 1},
                "findings_by_verdict_path": {}, "execution_rate": {},
                "event_success_rates": {},
            })
            d2 = _write_mock_campaign(tmpdir, "r2", {
                "total_sequences": 5, "total_findings": 5,
                "unique_findings": 5, "duplicate_count": 0,
                "findings_by_strategy": {"coverage": 3, "attack": 2},
                "findings_by_verdict_path": {}, "execution_rate": {},
                "event_success_rates": {},
            })
            result = aggregate_runs([d1, d2])

        assert result["metrics"]["findings_coverage"]["mean"] == pytest.approx(2.5)
        assert result["metrics"]["findings_attack"]["mean"] == pytest.approx(1.5)

    def test_cross_run_unique_findings(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmpdir:
            # Same finding repeated across runs → dedup to 1
            same_finding = {
                "invariant": "I4", "generation_strategy": "coverage",
                "verdict_path": "oracle",
                "description": "Entity aliasing violation",
            }
            unique_finding = {
                "invariant": "I5", "generation_strategy": "attack",
                "verdict_path": "oracle",
                "description": "Authorization bypass",
            }
            d1 = _write_mock_campaign(tmpdir, "r1",
                {"total_sequences": 1, "total_findings": 1, "unique_findings": 1,
                 "duplicate_count": 0, "findings_by_strategy": {},
                 "findings_by_verdict_path": {}, "execution_rate": {},
                 "event_success_rates": {}},
                findings=[same_finding])
            d2 = _write_mock_campaign(tmpdir, "r2",
                {"total_sequences": 1, "total_findings": 2, "unique_findings": 2,
                 "duplicate_count": 0, "findings_by_strategy": {},
                 "findings_by_verdict_path": {}, "execution_rate": {},
                 "event_success_rates": {}},
                findings=[same_finding, unique_finding])

            result = aggregate_runs([d1, d2])

        assert result["cross_run_total_findings"] == 3
        assert result["cross_run_unique_findings"] == 2  # same_finding deduped, unique_finding kept

    def test_execution_rate_aggregated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            d1 = _write_mock_campaign(tmpdir, "r1", {
                "total_sequences": 4, "total_findings": 0, "unique_findings": 0,
                "duplicate_count": 0, "findings_by_strategy": {},
                "findings_by_verdict_path": {},
                "execution_rate": {"coverage": 0.8, "attack": 1.0},
                "event_success_rates": {},
            })
            d2 = _write_mock_campaign(tmpdir, "r2", {
                "total_sequences": 4, "total_findings": 0, "unique_findings": 0,
                "duplicate_count": 0, "findings_by_strategy": {},
                "findings_by_verdict_path": {},
                "execution_rate": {"coverage": 0.6, "attack": 0.8},
                "event_success_rates": {},
            })
            result = aggregate_runs([d1, d2])

        assert result["metrics"]["exec_rate_coverage"]["mean"] == pytest.approx(0.7)
        assert result["metrics"]["exec_rate_attack"]["mean"] == pytest.approx(0.9)
