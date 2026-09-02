"""One-command extraction pipeline.

Usage:
    # Full pipeline: fetch -> extract -> validate
    python -m src.extraction.run_pipeline --platform vault --protocol oidc_jwt

    # With comparison to existing hand-written profile
    python -m src.extraction.run_pipeline --platform vault --protocol oidc_jwt --compare-reference

    # Just see what would be fetched
    python -m src.extraction.run_pipeline --platform vault --protocol oidc_jwt --list-only

    # Regenerate from scratch (delete existing profile first)
    python -m src.extraction.run_pipeline --platform vault --protocol oidc_jwt --regenerate
"""
import argparse
import logging
import os
import shutil

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="VALENCE API Spec Extraction Pipeline")
    parser.add_argument("--platform", required=True)
    parser.add_argument("--protocol", default="oidc_jwt")
    parser.add_argument("--model", default="gpt-5.2-2025-12-11")
    parser.add_argument("--force-fetch", action="store_true", help="Re-download docs")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts, don't call LLM")
    parser.add_argument("--list-only", action="store_true", help="List discoverable doc files")
    parser.add_argument("--regenerate", action="store_true",
                        help="Start fresh (delete existing profile)")
    parser.add_argument("--no-merge", action="store_true",
                        help="Write raw LLM output to a timestamped file instead of merging "
                             "into the main profile (useful for quality comparison)")
    parser.add_argument("--validate", action="store_true",
                        help="After extraction, probe the running platform to validate "
                             "endpoints and remove fields that cause 400 errors")
    parser.add_argument("--tag", default=None,
                        help="Tag to include in profile filename (e.g., 'evaluation-exp1')")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    print(f"\n{'='*60}")
    print(f"VALENCE Extraction Pipeline: {args.platform}/{args.protocol}")
    print(f"{'='*60}\n")

    if args.list_only:
        from src.extraction.fetch_docs import (
            PLATFORM_DOC_SOURCES, list_github_directory,
        )
        config = PLATFORM_DOC_SOURCES.get(args.platform, {}).get(args.protocol, {})
        for repo_config in config.get("github_repos", []):
            for dir_path in repo_config["paths"]:
                files = list_github_directory(
                    repo_config["repo"], dir_path,
                    repo_config.get("branch", "main"),
                    repo_config.get("extensions"),
                    os.environ.get("GITHUB_TOKEN")
                )
                for f in files:
                    print(f"  {f['path']} ({f['size']} bytes)")
        return

    # Step 1: Fetch docs
    print("[Step 1/3] Fetching documentation...")
    from src.extraction.fetch_docs import fetch_platform_docs
    fetch_result = fetch_platform_docs(
        args.platform, args.protocol, force=args.force_fetch
    )
    print(f"  Fetched {fetch_result['total_files']} files "
          f"({fetch_result['approx_tokens']:,} tokens)")

    if args.dry_run:
        print("\n[Step 2/3] DRY RUN — printing prompts...")
    else:
        print("\n[Step 2/3] Extracting API specs via LLM...")

    # Step 2: Extract
    if args.regenerate:
        profile_path = f"src/profiles/{args.platform}.json"
        if os.path.exists(profile_path):
            backup = f"{profile_path}.bak"
            shutil.copy2(profile_path, backup)
            os.remove(profile_path)
            print(f"  Backed up and removed existing profile: {profile_path}")

    from src.extraction.extract_specs import extract_platform_specs
    extract_result = extract_platform_specs(
        args.platform, args.protocol, model=args.model, dry_run=args.dry_run,
        no_merge=args.no_merge, tag=args.tag,
    )

    if args.dry_run:
        print("\nDry run complete. Review prompts above, then run without --dry-run.")
        return

    print(f"  Operations extracted: {extract_result.get('ops_extracted', '?')}")

    profile_out = extract_result.get("profile_path", f"src/profiles/{args.platform}.json")

    # Step 3 (optional): Validate extracted profile against running platform
    if args.validate and os.path.exists(profile_out):
        print("\n[Step 3/3] Validating profile against running platform...")
        from src.extraction.validate_profile import validate_and_fix_profile
        fixes = validate_and_fix_profile(profile_out, args.protocol)
        if fixes:
            print(f"  Fixed {len(fixes)} field issues:")
            for fix in fixes:
                print(f"    - {fix}")
        else:
            print("  All fields validated OK")

    print(f"\n{'='*60}")
    print(f"Pipeline complete. Profile: {profile_out}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
