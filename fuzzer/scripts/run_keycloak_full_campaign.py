#!/usr/bin/env python3
"""Full-scale Keycloak campaign: ROPC + UMA, all testable invariants."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.stateful.campaign_runner import StatefulCampaignRunner
from src.config import CampaignConfig

config = CampaignConfig(
    platform="keycloak",
    protocol="oidc_jwt",
    profile_path="src/profiles/keycloak.json",
    llm_model="gpt-5.2",
    output_dir="results/keycloak_full_scale_20260316",
    invariant_focus=["I2", "I3", "I4", "I5"],
    num_sequences=12,
)
runner = StatefulCampaignRunner(config=config)

# Scale up: 12 sequences per invariant x 4 invariants = 48 sequences
# Mix: 60% coverage + 40% attack
# Invariants: I2 (replay), I3 (flow), I4 (binding), I5 (authz)
# I1 skipped for now — needs SAML mutations, separate campaign
results = runner.run(
    invariants=["I2", "I3", "I4", "I5"],
    sequences_per_invariant=12,
    generation_batch_size=4,  # 4 sequences per LLM call
)

print(f"\n{'='*60}")
print(f"CAMPAIGN COMPLETE")
print(f"  Sequences: {results.get('total_sequences', '?')}")
print(f"  Completed: {results.get('completed', '?')}")
print(f"  PlatformVerifier findings: {results.get('pv_findings', '?')}")
print(f"  AssertionEngine findings: {results.get('ae_findings', '?')}")
print(f"  INCONCLUSIVE: {results.get('inconclusive', '?')}")
