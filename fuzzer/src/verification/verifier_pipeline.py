"""Configurable verification pipeline that runs oracle and/or LLM verification."""
import logging

from src.verification.path_b_oracle import OracleVerifier

logger = logging.getLogger(__name__)


class VerifierPipeline:
    """Orchestrates one or more verification paths."""

    def __init__(self, config: dict):
        self.config = config
        self.paths = config.get("paths", ["oracle"])

        kbf = config.get("known_behavior_filter")

        self.oracle_verifier = (
            OracleVerifier(known_behavior_filter=kbf)
            if "oracle" in self.paths else None
        )

        self.plain_llm_verifier = None
        if "plain_llm" in self.paths:
            from src.verification.plain_llm_verifier import PlainLLMVerifier
            llm_model = config.get("llm_model")
            profile = config.get("profile")
            include_invariants = config.get("include_invariants_in_judge", False)
            self.plain_llm_verifier = PlainLLMVerifier(
                llm_model=llm_model, profile=profile,
                include_invariants=include_invariants,
            )

    def verify(self, sequence, execution_result) -> dict:
        """Run configured verification paths and return results."""
        results = {"sequence_id": sequence.sequence_id, "verdicts": {}}

        if self.oracle_verifier:
            results["verdicts"]["oracle"] = self.oracle_verifier.verify(
                sequence, execution_result
            )

        if self.plain_llm_verifier:
            results["verdicts"]["plain_llm"] = self.plain_llm_verifier.verify(
                sequence, execution_result
            )

        return results
