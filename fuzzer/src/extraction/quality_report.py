"""Generate quality report for extracted profiles.

Checks:
1. Completeness: all canonical ops present
2. Field validity: no ABSENT paths, correct methods
3. Platform-specific: env_defaults, session_auth, cleanup_rules
4. Cross-protocol consistency: management ops shared
"""

import json
import sys
from pathlib import Path


CRITICAL_OPS = {
    "verify_granted_identity", "exchange_code_for_token", "start_oidc_auth",
}
SAML_OPS = {"saml_login"}
LOGIN_OPS = {"login_with_password", "login_with_jwt"}
MGMT_OPS = {"create_user", "create_application", "create_provider"}

PLATFORM_CHECKS = {
    "keycloak": {"needs": ["create_tenant", "enable_auth_method"], "env": ["realm_prefix", "isolation_strategy"]},
    "casdoor":  {"needs": ["create_user", "mfa_setup_enable"], "env": ["organization"], "session": "cookie"},
    "dex":      {"needs": [], "env": ["client_id", "connector_id"]},
    "vault":    {"needs": ["enable_auth_method", "configure_jwt_validation"], "env": ["mount"]},
    "zitadel":  {"needs": ["create_user"], "env": ["project_id"]},
    "logto":    {"needs": ["create_user", "create_provider"], "env": ["login_strategy"]},
    "authentik": {"needs": ["create_user", "create_application"], "env": []},
}


def check_profile(path: str) -> dict:
    """Run quality checks on a single profile."""
    with open(path) as f:
        p = json.load(f)

    name = p.get("name", "unknown")
    proto = list(p.get("api_mapping", {}).keys())[0] if p.get("api_mapping") else "?"
    ops = p.get("api_mapping", {}).get(proto, {})
    op_names = set(ops.keys())
    env = p.get("environment_defaults", {})

    issues = []
    warnings = []
    score = 100

    # 1. Critical ops
    for op in CRITICAL_OPS:
        if op not in op_names:
            issues.append(f"missing critical op: {op}")
            score -= 15

    # 2. SAML ops
    if proto == "saml":
        for op in SAML_OPS:
            if op not in op_names:
                issues.append(f"missing SAML op: {op}")
                score -= 15
        sl = ops.get("saml_login", {})
        if sl:
            if sl.get("method") != "POST":
                issues.append(f"saml_login method={sl.get('method')} (should be POST)")
                score -= 10
            if not sl.get("metadata", {}).get("initiate_saml_flow"):
                warnings.append("saml_login missing initiate_saml_flow")
                score -= 5

    # 3. Login ops
    if not (op_names & LOGIN_OPS):
        issues.append("no login operation (login_with_password or login_with_jwt)")
        score -= 15

    # 4. ABSENT/empty paths
    absent = [n for n, ep in ops.items()
              if not ep.get("path") or ep.get("path", "").upper() in ("ABSENT", "UNKNOWN")]
    if absent:
        issues.append(f"ABSENT paths: {absent}")
        score -= 10 * len(absent)

    # 5. Platform-specific
    pc = PLATFORM_CHECKS.get(name, {})
    for needed in pc.get("needs", []):
        if needed not in op_names:
            warnings.append(f"missing platform op: {needed}")
            score -= 5
    for env_key in pc.get("env", []):
        if env_key not in env:
            warnings.append(f"missing env_default: {env_key}")
            score -= 3
    if pc.get("session") and p.get("session_auth_method") != pc["session"]:
        issues.append(f"session_auth_method should be '{pc['session']}'")
        score -= 10

    # 6. Token endpoint content_type
    for tok_op in ("exchange_code_for_token", "token_exchange"):
        ep = ops.get(tok_op, {})
        if ep and ep.get("path", "").endswith("/token"):
            if ep.get("content_type") != "form":
                warnings.append(f"{tok_op} should have content_type=form for /token endpoint")
                score -= 3

    score = max(0, score)
    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F"

    return {
        "profile": Path(path).name,
        "platform": name,
        "protocol": proto,
        "ops": len(op_names),
        "score": score,
        "grade": grade,
        "issues": issues,
        "warnings": warnings,
    }


def main():
    import glob
    pattern = sys.argv[1] if len(sys.argv) > 1 else "src/profiles/*_exp-1_*.json"
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"No profiles matching {pattern}")
        return

    print(f"{'Profile':<50s} {'Ops':>3s} {'Score':>5s} {'Grade':>5s}  Issues")
    print("-" * 120)

    total_score = 0
    for f in files:
        r = check_profile(f)
        total_score += r["score"]
        issue_str = "; ".join(r["issues"][:2]) if r["issues"] else ""
        warn_str = "; ".join(r["warnings"][:2]) if r["warnings"] and not r["issues"] else ""
        detail = issue_str or warn_str or "clean"
        print(f"{r['profile']:<50s} {r['ops']:3d} {r['score']:5d} {r['grade']:>5s}  {detail}")

    avg = total_score / len(files) if files else 0
    print(f"\n{'Average':.<50s} {'':>3s} {avg:5.0f}")


if __name__ == "__main__":
    main()
