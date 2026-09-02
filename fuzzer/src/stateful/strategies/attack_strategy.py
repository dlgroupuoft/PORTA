"""Attack-mode generation strategy for event sequence generation."""
import logging

from src.stateful.generation_strategy import GenerationStrategy, GenerationConfig, INVARIANT_DEFINITIONS
from src.stateful.models import EventSequence
from src.stateful.sequence_quality import SequenceQualityReport

logger = logging.getLogger(__name__)


class AttackStrategy(GenerationStrategy):
    """Generate targeted attack sequences guided by I1-I5 invariants.

    Uses invariant definitions and attack patterns to craft sequences
    that specifically test for vulnerability classes.
    oracle_checks MUST contain concrete assertions.
    """

    def __init__(self, llm_client, profile, prompt_builder):
        self.llm = llm_client
        self.profile = profile
        self.prompt_builder = prompt_builder
        self.last_quality = SequenceQualityReport()

    @property
    def strategy_name(self) -> str:
        return "attack"

    def build_mode_instruction(self, config: GenerationConfig) -> str:
        """Attack-specific instructions.

        Key difference from coverage: uses invariant definitions,
        references known CVE patterns, requires oracle_checks.
        """
        invariant_def = INVARIANT_DEFINITIONS.get(config.invariant_focus, "")

        # I4 baseline guidance: prompt the LLM to include a diversity baseline
        # check as the first oracle_check in I4 sequences. If the mechanism
        # cannot distinguish two known-different users, subsequent I4 assertions
        # are meaningless.
        i4_baseline = ""
        if config.invariant_focus == "I4":
            i4_baseline = """
## IMPORTANT — I4 Diversity Baseline
For I4 (Principal Binding) sequences, include a BASELINE oracle_check as the FIRST check:
  check_id: "i4_diversity_baseline"
  assertion: "user_A_entity_id != user_B_entity_id"
  violation_description: "Baseline failed: mechanism cannot distinguish principals"
This baseline verifies that two known-different users actually get different identities.
If this baseline check fails, all subsequent I4 assertions are inconclusive
(the mechanism itself cannot distinguish principals, so identity collision tests
are not meaningful).
"""

        return f"""
## Generation Mode: ATTACK
Generate targeted attack sequences based on known vulnerability patterns.

Target Invariant: {config.invariant_focus}
Definition: {invariant_def}

Each sequence should:
1. Test a SPECIFIC invariant violation hypothesis
2. Include concrete oracle_checks with parseable assertions
3. Reference a CVE analog if one exists (or 'none' if novel)
4. Set primary_invariant to "{config.invariant_focus}"

Attack design principles:
- Create a scenario where the invariant SHOULD hold
- Then perform an action that COULD violate the invariant
- Include verify events that collect evidence of whether it was violated
- Write assertions that check the violation condition

oracle_checks MUST NOT be empty. Every sequence MUST have at least
one assertion that checks for the invariant violation.
{i4_baseline}"""

    def generate(self, config: GenerationConfig) -> list[EventSequence]:
        """Generate attack sequences and tag them with strategy metadata."""
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
            f"[AttackStrategy] Generating {config.num_sequences} sequences "
            f"for {config.invariant_focus} (use_examples={config.use_examples})"
        )
        raw = self.llm.generate_json(system_prompt, user_prompt)
        sequences = self._parse_sequences(raw, protocol=self.prompt_builder.protocol)

        for seq in sequences:
            seq.metadata["generation_strategy"] = "attack"
            seq.metadata["used_examples"] = config.use_examples
            seq.metadata["num_examples"] = config.max_examples
            seq.metadata["invariant_focus"] = config.invariant_focus
            # Force primary_invariant to match the generation target.
            # The LLM sometimes sets this incorrectly or leaves it empty,
            # which causes dedup to merge sequences across invariants.
            if config.invariant_focus and (
                not seq.primary_invariant or seq.primary_invariant != config.invariant_focus
            ):
                seq.primary_invariant = config.invariant_focus

        logger.info(f"[AttackStrategy] Produced {len(sequences)} valid sequences")
        return sequences
