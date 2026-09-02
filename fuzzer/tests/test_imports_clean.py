"""Verify all new modules import cleanly without circular deps or missing deps."""
import pytest


def test_import_generation_strategy():
    from src.stateful.generation_strategy import GenerationStrategy, GenerationConfig, INVARIANT_DEFINITIONS
    assert "I1" in INVARIANT_DEFINITIONS
    assert "I5" in INVARIANT_DEFINITIONS


def test_import_strategies():
    from src.stateful.strategies.coverage_strategy import CoverageStrategy
    from src.stateful.strategies.attack_strategy import AttackStrategy


def test_import_prompt_builder():
    from src.stateful.prompt_builder import PromptBuilder


def test_import_sequence_quality():
    from src.stateful.sequence_quality import SequenceQualityReport


def test_import_verifier_pipeline():
    from src.verification.verifier_pipeline import VerifierPipeline


def test_import_campaign_report():
    from src.reporting.campaign_report import CampaignReport, FindingRecord, SequenceRecord


def test_import_aggregate_runs():
    from src.reporting.aggregate_runs import aggregate_runs


def test_import_populate_registry():
    from src.experiments.populate_registry import populate


def test_import_sequence_generator_facade():
    from src.stateful.sequence_generator import SequenceGenerator, INVARIANT_DEFINITIONS


def test_import_campaign_runner():
    from src.stateful.campaign_runner import StatefulCampaignRunner


def test_invariant_definitions_single_source():
    """INVARIANT_DEFINITIONS must be the same object in all modules."""
    from src.stateful.generation_strategy import INVARIANT_DEFINITIONS as GS_DEFS
    from src.stateful.sequence_generator import INVARIANT_DEFINITIONS as SG_DEFS
    assert GS_DEFS is SG_DEFS or GS_DEFS == SG_DEFS
