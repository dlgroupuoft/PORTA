"""Validate extracted specs are compatible with VALENCE components.

Usage:
    python -m src.extraction.validate_specs --platform vault --protocol oidc_jwt
    python -m src.extraction.validate_specs --platform vault --protocol oidc_jwt --strict
"""
import json
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Operations that MUST be present for the fuzzer to work
ESSENTIAL_OPS = {
    "login_with_jwt": "AUTH_LOGIN — needed for JWT testing",
    "create_auth_role": "AUTH_CONFIG — needed for role setup",
    "verify_granted_identity": "IDENTITY_LOOKUP — needed for oracle",
}

# Verification categories that must have at least one endpoint
REQUIRED_VERIFICATION_CATEGORIES = [
    "identity_lookup",
    "permission_check",
    "session_token_inspect",
]


def validate_profile(platform: str, protocol: str,
                     profile_path: Optional[str] = None,
                     spec_path: Optional[str] = None,
                     strict: bool = False) -> list[str]:
    """Validate profile.json and api_spec.json for a platform/protocol.

    Args:
        platform: e.g. "vault"
        protocol: e.g. "oidc_jwt"
        profile_path: Override path to profile JSON
        spec_path: Override path to api_spec JSON
        strict: If True, also check PROTOCOL_OPERATIONS cross-reference

    Returns:
        List of validation error strings. Empty list = all checks passed.
    """
    errors = []
    profile_path = profile_path or f"src/profiles/{platform}.json"
    spec_path = spec_path or f"src/llm/platform_apis/{platform}_api_spec.json"

    # ── 1. Load profile ──────────────────────────────────────────────────────
    from src.models.platform_profile import PlatformProfile
    try:
        profile = PlatformProfile.from_json(profile_path)
    except FileNotFoundError:
        return [f"FATAL: Profile not found: {profile_path}"]
    except Exception as e:
        return [f"FATAL: Cannot load profile: {e}"]

    # ── 2. Protocol exists ───────────────────────────────────────────────────
    if protocol not in profile.api_mapping:
        errors.append(f"Protocol '{protocol}' not in api_mapping")
        return errors  # Nothing else to check without the protocol

    ops = profile.api_mapping[protocol]

    # ── 3. Essential operations exist ────────────────────────────────────────
    for op_name, desc in ESSENTIAL_OPS.items():
        if op_name not in ops:
            errors.append(f"Missing essential operation: {op_name} ({desc})")

    # ── 4. Per-operation checks ───────────────────────────────────────────────
    for op_name, ep in ops.items():
        path = getattr(ep, "path", "") or ""
        method = getattr(ep, "method", "") or ""
        auth = getattr(ep, "auth", "") or ""
        body_map = getattr(ep, "body_map", {}) or {}
        response_map = getattr(ep, "response_map", {}) or {}

        # Must have method and path
        if not method:
            errors.append(f"{op_name}: missing 'method'")
        if not path:
            errors.append(f"{op_name}: missing 'path'")
        if not auth:
            errors.append(f"{op_name}: missing 'auth'")

        # path_params declared in profile should match placeholders in path
        path_placeholders = set(re.findall(r'\{(\w+)\}', path))
        declared = set(getattr(ep, "path_params", []) or [])
        if declared and path_placeholders:
            undeclared = path_placeholders - declared
            if undeclared:
                errors.append(
                    f"{op_name}: path has placeholder(s) {undeclared} "
                    f"not declared in path_params"
                )

        # Login ops must have session_token in response_map
        if op_name.startswith("login_"):
            if not response_map or "session_token" not in response_map:
                errors.append(
                    f"{op_name}: missing 'session_token' in response_map "
                    f"(needed to store the session token after login)"
                )

        # verify_granted_identity must have identity_id in response_map
        if op_name == "verify_granted_identity":
            if not response_map or "identity_id" not in response_map:
                errors.append(
                    f"{op_name}: missing 'identity_id' in response_map "
                    f"(needed by InvariantVerifier)"
                )

        # response_map values should look like JSON dot-paths
        for abstract_key, json_path in response_map.items():
            if not isinstance(json_path, str) or not json_path:
                errors.append(
                    f"{op_name}.response_map['{abstract_key}']: "
                    f"invalid JSON path '{json_path}'"
                )

    # ── 5. known_behaviors validation ────────────────────────────────────────
    for kb in profile.known_behaviors:
        kb_id = getattr(kb, "id", "") or ""
        if not kb_id:
            errors.append("known_behavior missing 'id'")
        if not getattr(kb, "invariants", []):
            errors.append(f"known_behavior '{kb_id}': missing 'invariants'")
        if not getattr(kb, "conditions", {}):
            errors.append(f"known_behavior '{kb_id}': missing 'conditions' (needed for auto-matching)")

    # ── 6. api_constraints non-empty ─────────────────────────────────────────
    if not profile.api_constraints:
        errors.append(
            "api_constraints is empty — missing platform rules may cause test setup failures"
        )

    # ── 7. Verification spec ─────────────────────────────────────────────────
    try:
        with open(spec_path) as f:
            spec = json.load(f)
    except FileNotFoundError:
        errors.append(f"Missing verification spec: {spec_path}")
        return errors
    except Exception as e:
        errors.append(f"Cannot load verification spec: {e}")
        return errors

    apis = spec.get("verification_apis", {})
    for category in REQUIRED_VERIFICATION_CATEGORIES:
        if not apis.get(category):
            errors.append(f"Verification spec missing or empty category: {category}")

    # ── 8. Cross-reference: PROTOCOL_OPERATIONS coverage (strict mode) ───────
    if strict:
        from src.stateful.protocol_operations import PROTOCOL_OPERATIONS
        profile_op_names = set(ops.keys())
        for abstract_op in PROTOCOL_OPERATIONS:
            if abstract_op not in profile_op_names:
                errors.append(
                    f"[STRICT] PROTOCOL_OPERATIONS.{abstract_op} not in "
                    f"profile.api_mapping.{protocol}"
                )

    return errors


def print_report(platform: str, protocol: str, errors: list[str]) -> bool:
    """Print validation report. Returns True if all checks passed."""
    print(f"\n{'='*60}")
    print(f"Validation: {platform}/{protocol}")
    print(f"{'='*60}")
    if not errors:
        print("✅ All checks passed")
        return True
    else:
        print(f"❌ {len(errors)} error(s) found:")
        for e in errors:
            print(f"  • {e}")
        return False


def compare_with_reference(platform: str, protocol: str,
                            extracted_path: str, reference_path: str) -> list[str]:
    """Compare auto-extracted profile with hand-written reference.
    Reports missing operations, extra operations, and field differences.
    """
    with open(extracted_path) as f:
        extracted = json.load(f)
    with open(reference_path) as f:
        reference = json.load(f)

    diffs = []

    ext_ops = set(extracted.get("api_mapping", {}).get(protocol, {}).keys())
    ref_ops = set(reference.get("api_mapping", {}).get(protocol, {}).keys())

    missing = ref_ops - ext_ops
    extra = ext_ops - ref_ops

    if missing:
        diffs.append(f"MISSING operations (in reference but not extracted): {sorted(missing)}")
    if extra:
        diffs.append(f"EXTRA operations (extracted but not in reference): {sorted(extra)}")

    # Check common operations for field differences
    for op_name in ext_ops & ref_ops:
        ext_op = extracted["api_mapping"][protocol][op_name]
        ref_op = reference["api_mapping"][protocol][op_name]

        if ext_op.get("method") != ref_op.get("method"):
            diffs.append(f"{op_name}: method differs (extracted={ext_op.get('method')}, reference={ref_op.get('method')})")
        if ext_op.get("path") != ref_op.get("path"):
            diffs.append(f"{op_name}: path differs (extracted={ext_op.get('path')}, reference={ref_op.get('path')})")

    return diffs


def diff_against_handwritten(platform: str, protocol: str) -> dict:
    """Compare auto-extracted profile against the hand-written one.

    Loads the full_extraction.json if available, prints a diff summary.
    Returns dict with coverage metrics.
    """
    debug_path = Path(f"src/extraction/analysis/{platform}_{protocol}_full_extraction.json")
    if not debug_path.exists():
        return {"error": f"No extraction found at {debug_path}"}

    with open(debug_path) as f:
        extracted = json.load(f)

    # Load the current profile for comparison
    try:
        with open(f"src/profiles/{platform}.json") as f:
            current = json.load(f)
    except FileNotFoundError:
        return {"error": "No profile found to compare against"}

    current_ops = set(current.get("api_mapping", {}).get(protocol, {}).keys())
    extracted_ops = {
        op.get("operation_name")
        for op in extracted.get("input_operations", [])
        if op.get("operation_name")
    }

    in_extracted_not_current = extracted_ops - current_ops
    in_current_not_extracted = current_ops - extracted_ops

    result = {
        "current_ops": sorted(current_ops),
        "extracted_ops": sorted(extracted_ops),
        "new_in_extracted": sorted(in_extracted_not_current),
        "missing_from_extracted": sorted(in_current_not_extracted),
        "coverage": len(extracted_ops & current_ops) / max(len(current_ops), 1),
    }

    print(f"\n--- Diff: auto-extracted vs hand-written ({platform}/{protocol}) ---")
    print(f"Hand-written ops : {len(current_ops)}")
    print(f"Auto-extracted ops: {len(extracted_ops)}")
    if in_extracted_not_current:
        print(f"New in extracted (not in hand-written): {sorted(in_extracted_not_current)}")
    if in_current_not_extracted:
        print(f"Missing from extracted (in hand-written): {sorted(in_current_not_extracted)}")
    print(f"Coverage: {result['coverage']:.1%}")

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Validate extracted specs against VALENCE component expectations"
    )
    parser.add_argument("--platform", required=True,
                        choices=["vault", "keycloak", "dex", "casdoor"],
                        help="Platform to validate")
    parser.add_argument("--protocol", default="oidc_jwt",
                        help="Protocol variant (default: oidc_jwt)")
    parser.add_argument("--strict", action="store_true",
                        help="Also check PROTOCOL_OPERATIONS cross-reference")
    parser.add_argument("--diff", action="store_true",
                        help="Diff auto-extracted vs hand-written profile")
    parser.add_argument("--profile", default=None,
                        help="Override path to profile JSON")
    parser.add_argument("--spec", default=None,
                        help="Override path to api_spec JSON")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    errors = validate_profile(
        args.platform, args.protocol,
        profile_path=args.profile,
        spec_path=args.spec,
        strict=args.strict,
    )
    passed = print_report(args.platform, args.protocol, errors)

    if args.diff:
        diff_against_handwritten(args.platform, args.protocol)

    import sys
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
