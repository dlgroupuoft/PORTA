"""Evaluation mode definitions for paper experiments.

Each mode is a named configuration that sets:
- generation_mode: 'coverage' (G_blind) or 'attack' (G_oracle)
- use_examples: bool
- verdict_paths: list of verdict paths to run
- enable_mutation_sweep: bool
- description: human-readable label for reports
"""
from dataclasses import dataclass, field


@dataclass
class EvalMode:
    name: str
    description: str
    generation_mode: str         # "coverage" or "attack"
    use_invariants: bool         # Whether I1-I5 definitions are in the prompt
    use_examples: bool           # Whether few-shot examples are in the prompt
    verdict_paths: list[str]     # Which verdict paths to run
    enable_mutation_sweep: bool  # Whether to run credential mutations after sequences
    include_invariants_in_judge: bool = False  # Whether to pass I1-I5 to LLM judge

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


# --- Named modes ---

EVAL_MODES = {
    # === Primary mode: the full system ===
    "full": EvalMode(
        name="full",
        description="Full system: oracle-guided generation + rule verdict + mutation sweep",
        generation_mode="attack",
        use_invariants=True,
        use_examples=True,
        verdict_paths=["oracle"],
        enable_mutation_sweep=True,
    ),

    # === RQ1: Generation ablation ===
    "blind": EvalMode(
        name="blind",
        description="Blind generation (no I1-I5, no attack examples) + rule verdict",
        generation_mode="coverage",
        use_invariants=False,     # Coverage mode already excludes I1-I5 from prompt
        use_examples=False,       # Examples contain I1-I5 references → must disable for clean baseline
        verdict_paths=["oracle"],
        enable_mutation_sweep=False,
    ),
    "oracle_gen": EvalMode(
        name="oracle_gen",
        description="Oracle-guided generation + rule verdict (no mutation sweep)",
        generation_mode="attack",
        use_invariants=True,
        use_examples=True,
        verdict_paths=["oracle"],
        enable_mutation_sweep=False,
    ),

    # === RQ2: Verdict ablation ===
    "verdict_compare": EvalMode(
        name="verdict_compare",
        description="Oracle-guided generation + ALL three verdict paths for comparison",
        generation_mode="attack",
        use_invariants=True,
        use_examples=True,
        verdict_paths=["oracle", "oracle_guided", "plain_llm"],
        enable_mutation_sweep=False,
    ),

    # === RQ3: Example ablation ===
    "no_examples": EvalMode(
        name="no_examples",
        description="Oracle-guided generation WITHOUT examples + rule verdict",
        generation_mode="attack",
        use_invariants=True,
        use_examples=False,
        verdict_paths=["oracle"],
        enable_mutation_sweep=False,
    ),

    # === RQ4: LLM-as-judge ablation ===
    "llm_judge": EvalMode(
        name="llm_judge",
        description="Full generation (invariants + examples) + LLM-as-judge verdict (no assertion oracle)",
        generation_mode="attack",
        use_invariants=True,
        use_examples=True,
        verdict_paths=["plain_llm"],
        enable_mutation_sweep=False,
    ),

    # === RQ4b: LLM-as-judge with profile context ===
    "llm_judge_profile": EvalMode(
        name="llm_judge_profile",
        description="Full generation (invariants + examples) + LLM-as-judge with sanitized profile context (no assertion oracle)",
        generation_mode="attack",
        use_invariants=True,
        use_examples=True,
        verdict_paths=["plain_llm"],
        enable_mutation_sweep=False,
    ),

    # === RQ4c: LLM-as-judge with invariant definitions ===
    "llm_judge_invariant": EvalMode(
        name="llm_judge_invariant",
        description="Full generation + LLM-as-judge with I1-I5 invariant definitions and profile context",
        generation_mode="attack",
        use_invariants=True,
        use_examples=True,
        verdict_paths=["plain_llm"],
        enable_mutation_sweep=False,
        include_invariants_in_judge=True,
    ),

    # === Utility: all conditions in one run ===
    "all": None,  # Special: runs blind + oracle_gen + verdict_compare + no_examples
}

# The "all" mode runs these in sequence:
ALL_ABLATION_MODES = ["full", "blind", "oracle_gen", "verdict_compare", "no_examples"]
