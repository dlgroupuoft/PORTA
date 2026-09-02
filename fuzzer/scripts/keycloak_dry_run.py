#!/usr/bin/env python3
"""Dry-run: generate Keycloak sequences and inspect them."""
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models.platform_profile import PlatformProfile
from src.stateful.sequence_generator import SequenceGenerator
from src.llm.client import LLMClient

profile = PlatformProfile.from_json("src/profiles/keycloak.json")
llm = LLMClient(model="gpt-5.2", temperature=0.3)
gen = SequenceGenerator(llm, profile=profile)

# Generate 2 sequences for I4
sequences = gen.generate(
    invariant_focus="I4",
    num_sequences=2,
    protocol="oidc_jwt",
)

print(f"Generated {len(sequences)} sequences")
for seq in sequences:
    print(f"\n{'='*60}")
    print(f"ID: {seq.sequence_id}")
    print(f"Description: {seq.description}")
    print(f"Events:")
    for e in seq.events:
        print(f"  {e.event_type} (auth_as={e.auth_as})")
        if e.event_type.startswith("login_"):
            print(f"    params: {json.dumps(e.params, indent=6)[:300]}")
    print(f"Oracle checks: {len(seq.oracle_checks)}")

    # KEY CHECK: login events should NOT have jwt_claims for Keycloak
    for e in seq.events:
        if e.event_type.startswith("login_") and "jwt_claims" in e.params:
            print(f"  WARNING: {e.event_type} has jwt_claims -- should use username/password!")
        if e.event_type == "login_with_password":
            if "username" in e.params and "password" in e.params:
                print(f"  CORRECT: login_with_password has username/password")
