"""Test eval mode definitions and CLI integration."""
from src.eval_modes import EVAL_MODES, ALL_ABLATION_MODES, EvalMode


def test_all_modes_defined():
    for name in ALL_ABLATION_MODES:
        assert name in EVAL_MODES
        mode = EVAL_MODES[name]
        assert isinstance(mode, EvalMode)


def test_full_mode():
    m = EVAL_MODES["full"]
    assert m.generation_mode == "attack"
    assert m.use_invariants is True
    assert m.use_examples is True
    assert "oracle" in m.verdict_paths
    assert m.enable_mutation_sweep is True


def test_blind_mode():
    m = EVAL_MODES["blind"]
    assert m.generation_mode == "coverage"
    assert m.use_invariants is False
    assert m.use_examples is False
    assert m.verdict_paths == ["oracle"]
    assert m.enable_mutation_sweep is False


def test_verdict_compare_runs_all_three():
    m = EVAL_MODES["verdict_compare"]
    assert "oracle" in m.verdict_paths
    assert "oracle_guided" in m.verdict_paths
    assert "plain_llm" in m.verdict_paths


def test_no_examples_mode():
    m = EVAL_MODES["no_examples"]
    assert m.use_invariants is True
    assert m.use_examples is False


def test_blind_vs_oracle_differ_on_invariants():
    blind = EVAL_MODES["blind"]
    oracle = EVAL_MODES["oracle_gen"]
    assert blind.use_invariants is False
    assert oracle.use_invariants is True


def test_eval_mode_to_dict():
    m = EVAL_MODES["full"]
    d = m.to_dict()
    assert d["name"] == "full"
    assert d["generation_mode"] == "attack"
    assert d["enable_mutation_sweep"] is True


def test_all_special_mode_is_none():
    assert EVAL_MODES["all"] is None


def test_all_ablation_modes_order():
    assert ALL_ABLATION_MODES == ["full", "blind", "oracle_gen", "verdict_compare", "no_examples"]


def test_all_ablation_includes_full():
    assert "full" in ALL_ABLATION_MODES


def test_oracle_gen_mode():
    m = EVAL_MODES["oracle_gen"]
    assert m.generation_mode == "attack"
    assert m.use_invariants is True
    assert m.use_examples is True
    assert m.enable_mutation_sweep is False
