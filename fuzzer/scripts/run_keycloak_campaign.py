#!/usr/bin/env python3
"""Run Keycloak I4/I5 campaign."""
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
    output_dir="results/keycloak_oidc_20260315",
    invariant_focus=["I4", "I5"],
    num_sequences=3,
)
runner = StatefulCampaignRunner(config=config)
results = runner.run(
    invariants=["I4", "I5"],
    sequences_per_invariant=3,
    generation_batch_size=2,
)

print(f"\nSequences: {results.get('total_sequences', '?')}")
print(f"Findings: {results.get('total_findings', '?')}")
