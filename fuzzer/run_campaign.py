"""VALENCE Campaign Runner CLI."""
import argparse
import json
import os
import sys
import time
import logging
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="VALENCE Stateful Fuzzing Campaign")

    # Platform
    parser.add_argument("--platform", default="vault", choices=["vault", "keycloak", "dex"])
    parser.add_argument("--protocol", default="oidc_jwt", choices=["oidc_jwt", "saml", "ldap"])
    parser.add_argument("--profile", default=None, help="Path to platform profile JSON")

    # API Specs
    parser.add_argument("--input-api-spec", default="", help="Path to input API spec")
    parser.add_argument("--verification-api-spec", default="", help="Path to verification API spec")

    # Verification
    parser.add_argument("--verify-path", nargs="+", default=["oracle"],
                        choices=["oracle", "prediction", "both"],
                        help="Verification path(s) to use")

    # LLM
    parser.add_argument("--llm-model", default=None, help="LLM model (default: gpt-5.2)")

    # Generation
    parser.add_argument("--invariants", nargs="+", default=["I4", "I5"],
                        help="Invariants to focus on")
    parser.add_argument("--num-sequences", type=int, default=10)

    # Output
    parser.add_argument("--output-dir", default="results")

    # Control
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate config and print plan without executing")

    args = parser.parse_args()

    from src.config import CampaignConfig

    # Build config
    profile_path = args.profile or f"src/profiles/{args.platform}.json"
    verification_paths = ["oracle", "prediction"] if "both" in args.verify_path else args.verify_path

    config = CampaignConfig(
        platform=args.platform,
        protocol=args.protocol,
        profile_path=profile_path,
        verification_api_spec_path=args.verification_api_spec or
            f"src/llm/platform_apis/{args.platform}_api_spec.json",
        input_api_spec_path=args.input_api_spec,
        verification_paths=verification_paths,
        llm_model=args.llm_model or os.getenv("VALENCE_LLM_MODEL", "gpt-5.2"),
        invariant_focus=args.invariants,
        num_sequences=args.num_sequences,
        output_dir=args.output_dir,
        dry_run=args.dry_run,
    )

    # Load and validate profile
    from src.models.platform_profile import PlatformProfile
    profile = PlatformProfile.from_json(config.profile_path)

    print(f"\n{'='*60}")
    print(f"VALENCE v2 Campaign")
    print(f"{'='*60}")
    print(f"Platform:     {profile.name}")
    print(f"Protocol:     {config.protocol}")
    print(f"Profile:      {config.profile_path}")
    print(f"Invariants:   {config.invariant_focus}")
    print(f"Sequences:    {config.num_sequences}")
    print(f"Verify paths: {config.verification_paths}")
    print(f"LLM model:    {config.llm_model}")
    print(f"Output:       {config.output_dir}")
    print(f"{'='*60}")

    if config.dry_run:
        print("\n[DRY RUN] Configuration validated successfully.")
        print(f"  Profile: {profile.name} ({len(profile.api_mapping.get(config.protocol, {}))} API mappings)")
        print(f"  Known behaviors: {len(profile.known_behaviors)} rules")
        print(f"  Constraints: {len(profile.api_constraints)} rules")
        print(f"  Verification fields: {list(profile.verification_fields.keys())}")
        return

    # Full campaign execution
    from src.stateful.campaign_runner import StatefulCampaignRunner

    runner = StatefulCampaignRunner(
        vault_url=profile.base_url,
        admin_token=profile.admin_auth.get("value", "root"),
        llm_model=config.llm_model,
    )

    report = runner.run(
        invariants=config.invariant_focus,
        sequences_per_invariant=max(1, config.num_sequences // len(config.invariant_focus)),
    )

    # Print summary
    print(f"\n{'='*60}")
    print(f"Campaign complete: {report['summary']['total_sequences']} sequences")
    print(f"Findings: {report['summary']['findings']}")
    output_dir = Path(config.output_dir) / f"campaign_{profile.name}_{config.timestamp}"
    print(f"Results: {output_dir}")


if __name__ == "__main__":
    main()
