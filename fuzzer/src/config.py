"""Campaign configuration with CLI and env var support."""
from dataclasses import dataclass, field
from datetime import datetime
import os


@dataclass
class CampaignConfig:
    # Platform
    platform: str = "vault"
    protocol: str = "oidc_jwt"
    profile_path: str = "src/profiles/vault.json"

    # API Specs
    input_api_spec_path: str = ""   # Future: platform input API spec
    verification_api_spec_path: str = "src/llm/platform_apis/vault_api_spec.json"

    # Verification
    verification_paths: list[str] = field(default_factory=lambda: ["oracle"])

    # LLM
    llm_model: str = field(default_factory=lambda: os.getenv("VALENCE_LLM_MODEL", "gpt-5.2"))
    llm_temperature: float = 0.01  # near-deterministic generation

    # Generation
    invariant_focus: list[str] = field(default_factory=lambda: ["I4", "I5"])
    num_sequences: int = 10

    # Output
    output_dir: str = "results"
    timestamp: str = ""  # Auto-generated if empty

    # Docker
    docker_compose_file: str = ""

    # Mutation sweep
    enable_mutation_sweep: bool = False
    sweep_min_priority: str = "high"

    # Dry run mode
    dry_run: bool = False

    # Pre-campaign cleanup: delete leftover test resources before generating sequences
    pre_campaign_cleanup: bool = True

    # Example ablation control
    use_examples: bool = True
    max_examples: int = -1  # -1 = all available

    # Generation mode: "attack" (G_oracle) or "coverage" (G_blind)
    generation_mode: str = "attack"
    # Whether to include I1-I5 invariant definitions in the system prompt
    use_invariants: bool = True

    # Replay mode: skip generation and execute sequences from this file
    replay_path: str = ""  # Path to sequences.json from a previous campaign run

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
