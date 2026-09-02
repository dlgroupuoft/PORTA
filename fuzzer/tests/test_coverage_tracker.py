"""Tests for CoverageTracker."""
import pytest

from src.stateful.coverage_tracker import CoverageTracker
from src.stateful.models import Event, EventSequence, OracleCheck


def _make_seq(seq_id="s1", description="Test", primary_invariant="I4",
              events=None, oracle_checks=None):
    if events is None:
        events = [
            Event(event_type="login_jwt", params={}, auth_as="user_A"),
            Event(event_type="verify_token_self", params={}, auth_as="session_user_A"),
        ]
    if oracle_checks is None:
        oracle_checks = [
            OracleCheck(check_id="c1", invariant=primary_invariant,
                        assertion="x != y", violation_description="test"),
        ]
    return EventSequence(
        sequence_id=seq_id,
        description=description,
        invariant_hypothesis=f"{primary_invariant}: test",
        events=events,
        oracle_checks=oracle_checks,
        primary_invariant=primary_invariant,
    )


class TestCoverageTracker:
    def test_empty_tracker(self):
        tracker = CoverageTracker()
        assert tracker.coverage_ratio() == 0.0
        assert len(tracker.uncovered_cells()) > 0

    def test_record_sequence(self):
        tracker = CoverageTracker()
        seq = _make_seq(description="Two users collision same entity")
        tracker.record_sequence(seq)
        assert tracker.coverage_ratio() > 0.0
        assert len(tracker.covered) > 0

    def test_coverage_increases(self):
        tracker = CoverageTracker()
        seq1 = _make_seq(description="Cross user collision same entity",
                         primary_invariant="I4")
        tracker.record_sequence(seq1)
        r1 = tracker.coverage_ratio()

        seq2 = _make_seq(seq_id="s2", description="Empty audience bypass",
                         primary_invariant="I5")
        tracker.record_sequence(seq2)
        r2 = tracker.coverage_ratio()
        assert r2 >= r1

    def test_suggest_focus(self):
        tracker = CoverageTracker()
        suggestion = tracker.suggest_focus()
        assert "focus_invariant" in suggestion
        assert "uncovered_count" in suggestion
        assert "total_coverage" in suggestion

    def test_full_coverage_message(self):
        tracker = CoverageTracker()
        # Manually fill all cells
        for inv in tracker.DIMENSIONS["invariant"]:
            for p in tracker.DIMENSIONS["attack_pattern"]:
                for c in tracker.DIMENSIONS["user_config"]:
                    for t in tracker.DIMENSIONS["temporal"]:
                        tracker.covered.add((inv, p, c, t))
        assert tracker.coverage_ratio() == 1.0
        suggestion = tracker.suggest_focus()
        assert suggestion["message"] == "Full coverage achieved"

    def test_infer_cross_user(self):
        tracker = CoverageTracker()
        seq = _make_seq(
            description="Two users different sub",
            events=[
                Event(event_type="login_jwt", params={}, auth_as="user_A"),
                Event(event_type="login_jwt", params={}, auth_as="user_B"),
                Event(event_type="verify_token_self", params={}, auth_as="session_user_A"),
            ],
        )
        configs = tracker._infer_user_config(seq)
        assert "cross_user" in configs

    def test_infer_temporal_revoke(self):
        tracker = CoverageTracker()
        seq = _make_seq(
            description="Login then revoke",
            events=[
                Event(event_type="login_jwt", params={}, auth_as="user_A"),
                Event(event_type="revoke_session", params={}, auth_as="admin"),
                Event(event_type="verify_token_self", params={}, auth_as="session_user_A"),
            ],
        )
        temporals = tracker._infer_temporal(seq)
        assert "post_revoke" in temporals

    def test_infer_temporal_modify(self):
        tracker = CoverageTracker()
        seq = _make_seq(description="Login then tighten role and re-auth")
        temporals = tracker._infer_temporal(seq)
        assert "mid_session_change" in temporals

    def test_get_gap_descriptions(self):
        tracker = CoverageTracker()
        gaps = tracker.get_gap_descriptions(limit=5)
        assert len(gaps) == 5
        assert " × " in gaps[0]

    def test_dimensions_complete(self):
        assert "invariant" in CoverageTracker.DIMENSIONS
        assert "attack_pattern" in CoverageTracker.DIMENSIONS
        assert "user_config" in CoverageTracker.DIMENSIONS
        assert "temporal" in CoverageTracker.DIMENSIONS

    def test_total_cells(self):
        total = 1
        for dim in CoverageTracker.DIMENSIONS.values():
            total *= len(dim)
        # 5 * 10 * 4 * 3 = 600
        assert total == 600
