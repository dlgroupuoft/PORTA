#!/usr/bin/env python3
"""Run large-scale Casdoor campaign."""
import os, sys, json, logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.WARNING, format='%(name)s %(levelname)s: %(message)s')
logging.getLogger('src.stateful.sequence_executor').setLevel(logging.ERROR)

from src.config import CampaignConfig
from src.stateful.campaign_runner import StatefulCampaignRunner

config = CampaignConfig(
    platform='casdoor',
    protocol='oidc_jwt',
    profile_path='src/profiles/casdoor.json',
    llm_model='gpt-5.2',
    output_dir='results/casdoor_large2_20260316',
    invariant_focus=['I1', 'I3', 'I4', 'I5'],
    num_sequences=40,
)

runner = StatefulCampaignRunner(config=config)
results = runner.run(
    invariants=['I1', 'I3', 'I4', 'I5'],
    sequences_per_invariant=10,
    generation_batch_size=5,
)
