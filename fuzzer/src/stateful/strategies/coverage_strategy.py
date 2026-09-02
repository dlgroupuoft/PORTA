"""Coverage-mode generation strategy for event sequence generation."""
import logging

from src.stateful.generation_strategy import GenerationStrategy, GenerationConfig
from src.stateful.models import EventSequence
from src.stateful.sequence_quality import SequenceQualityReport

logger = logging.getLogger(__name__)


class CoverageStrategy(GenerationStrategy):
    """Generate diverse operation sequences for coverage testing.

    Does NOT use invariant knowledge to guide generation.
    oracle_checks array is ALWAYS empty [].
    Verification is handled externally by PlatformVerifier or LLM verdict.
    """

    def __init__(self, llm_client, profile, prompt_builder):
        self.llm = llm_client
        self.profile = profile
        self.prompt_builder = prompt_builder
        self.last_quality = SequenceQualityReport()

    @property
    def strategy_name(self) -> str:
        return "coverage"

    def build_mode_instruction(self, config: GenerationConfig) -> str:
        """Coverage-specific instructions.

        Key difference from attack: NO invariant-specific attack patterns.
        Instructions focus on operation diversity, not vulnerability testing.
        """
        return """
## Generation Mode: COVERAGE
Generate diverse operation sequences that exercise different API combinations.
Your goal is NOT to craft specific attacks. Instead:
1. Use a VARIETY of setup operations (create different resource types, configurations)
2. Login as different identities with different credentials
3. Use ALL available verify operations to capture the platform's response
4. Verification will be handled automatically — you do NOT need oracle_checks

Think about functional coverage:
- What happens with 2 users with similar names and login as each?
- What happens with roles via groups vs direct assignment?
- What happens with different scope/audience configurations?
- What happens if I login, change config, then verify again?

oracle_checks array MUST be EMPTY [].
Do NOT include any invariant-specific attack reasoning.
"""

    def generate(self, config: GenerationConfig) -> list[EventSequence]:
        """Generate coverage sequences and tag them with strategy metadata."""
        self.last_quality = SequenceQualityReport()
        system_prompt = self.prompt_builder.build_system_prompt(
            use_examples=config.use_examples,
            max_examples=config.max_examples,
            use_invariants=config.use_invariants,
        )
        mode_instruction = self.build_mode_instruction(config)
        user_prompt = self.prompt_builder.build_user_prompt(
            mode_instruction=mode_instruction,
            config=config,
        )

        logger.info(
            f"[CoverageStrategy] Generating {config.num_sequences} sequences "
            f"for {config.invariant_focus} (use_examples={config.use_examples})"
        )
        raw = self.llm.generate_json(system_prompt, user_prompt)
        sequences = self._parse_sequences(raw, protocol=self.prompt_builder.protocol)

        for seq in sequences:
            seq.metadata["generation_strategy"] = "coverage"
            seq.metadata["used_examples"] = config.use_examples
            seq.metadata["num_examples"] = config.max_examples
            # Force primary_invariant to match the generation target.
            if config.invariant_focus and (
                not seq.primary_invariant or seq.primary_invariant != config.invariant_focus
            ):
                seq.primary_invariant = config.invariant_focus

        logger.info(f"[CoverageStrategy] Produced {len(sequences)} valid sequences")
        return sequences
