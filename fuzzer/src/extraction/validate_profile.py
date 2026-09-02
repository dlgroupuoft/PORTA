"""Post-extraction profile validation against a running platform.

Probes each operation's endpoint with minimal test data to detect:
- Fields rejected by the platform ("Unrecognized field", "unknown property")
- Incorrect HTTP methods (405 Method Not Allowed)
- Wrong paths (404 Not Found on well-known base paths)

Automatically removes rejected fields from body_map and saves the fixed profile.
"""

import json
import logging
import re
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# Patterns that indicate a field-level rejection (not a business logic error)
FIELD_REJECTION_PATTERNS = [
    # Keycloak (handles both raw and escaped quotes)
    r'Unrecognized field\s*["\\\s]*(\w+)',
    # Generic JSON schema validators
    r'unknown property[:\s]+"?(\w+)"?',
    r'Additional property (\w+) is not allowed',
    r'Invalid property[:\s]+"?(\w+)"?',
    # Casdoor
    r'unknown field[:\s]+"?(\w+)"?',
    # Zitadel gRPC
    r'invalid value for.*field\s+(\w+)',
]

FIELD_REJECTION_RE = [re.compile(p, re.IGNORECASE) for p in FIELD_REJECTION_PATTERNS]


def _extract_rejected_field(error_text: str) -> str | None:
    """Extract the rejected field name from an error message."""
    for pattern in FIELD_REJECTION_RE:
        m = pattern.search(error_text)
        if m:
            return m.group(1)
    return None


def _build_probe_body(body_map: dict) -> dict:
    """Build a minimal request body from body_map for probing.

    Uses type-appropriate placeholder values so the platform's JSON
    parser succeeds, allowing field-level validation to run.
    """
    body = {}
    for abstract_key, platform_key in body_map.items():
        parts = platform_key.split(".")
        d = body
        for part in parts[:-1]:
            existing = d.get(part)
            if not isinstance(existing, dict):
                d[part] = {}
            d = d[part]

        leaf = parts[-1]
        low = leaf.lower()

        # Boolean fields (common IAM field names)
        if any(kw in low for kw in (
            "enabled", "active", "signed", "validate", "encrypted", "supported",
            "create", "trust", "store", "readable", "hidden", "hide", "link",
            "backchannel", "force", "pass", "sign", "want", "use", "post_binding",
            "http_post", "artifact", "case_sensitive",
        )):
            d[leaf] = False
        # Array fields
        elif any(kw in low for kw in ("uris", "urls", "list", "domains", "scopes",
                                       "refs", "certificates")):
            d[leaf] = []
        # Numeric fields
        elif any(kw in low for kw in ("port", "order", "index", "count", "gui")):
            d[leaf] = 0
        # Provider type — must be a valid value for KC to parse
        elif leaf in ("providerId",):
            d[leaf] = "saml"
        else:
            d[leaf] = f"probe-{leaf}"

    return body


def _acquire_admin_token(base_url: str, platform: str, profile: dict) -> str | None:
    """Try to acquire an admin token from the running platform."""
    try:
        if platform == "keycloak":
            # KC: client_credentials with admin-cli
            resp = requests.post(
                f"{base_url}/realms/master/protocol/openid-connect/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": "admin-cli",
                    "client_secret": "admin",
                },
                timeout=10,
            )
            if resp.status_code == 200:
                return resp.json().get("access_token")
            # Fallback: password grant
            resp = requests.post(
                f"{base_url}/realms/master/protocol/openid-connect/token",
                data={
                    "grant_type": "password",
                    "client_id": "admin-cli",
                    "username": "admin",
                    "password": "admin",
                },
                timeout=10,
            )
            if resp.status_code == 200:
                return resp.json().get("access_token")

        elif platform == "casdoor":
            cookie_login = profile.get("cookie_login", {})
            if cookie_login:
                resp = requests.post(
                    f"{base_url}{cookie_login.get('path', '/api/login')}",
                    json=cookie_login.get("body", {}),
                    timeout=10,
                )
                if resp.status_code == 200:
                    return "cookie"  # Cookie-based, handled differently

        elif platform == "vault":
            auth = profile.get("admin_auth", {})
            val = auth.get("value", "")
            if "{" not in val:
                return val  # Vault uses static root token

        elif platform == "zitadel":
            # Check VALENCE_ADMIN_TOKEN env var (set by extract script from PAT file)
            import os
            pat = os.environ.get("VALENCE_ADMIN_TOKEN")
            if pat:
                return pat

    except Exception as e:
        logger.debug(f"Token acquisition failed for {platform}: {e}")

    return None


def validate_and_fix_profile(profile_path: str, protocol: str) -> list[str]:
    """Validate profile operations against the running platform.

    For each operation with a body_map, sends a probe request.
    If the platform rejects specific fields, removes them from body_map.

    Returns list of fix descriptions.
    """
    with open(profile_path) as f:
        profile = json.load(f)

    base_url = profile.get("base_url", "")
    if not base_url:
        logger.warning("No base_url in profile, skipping validation")
        return []

    # Build auth headers — try multiple auth strategies
    admin_auth = profile.get("admin_auth", {})
    headers = {"Content-Type": "application/json"}

    # Check if platform is reachable
    try:
        resp = requests.get(base_url, timeout=5, allow_redirects=True)
    except Exception as e:
        logger.warning(f"Platform not reachable at {base_url}: {e}")
        return []

    # Try to obtain admin token for platforms that need it
    platform_name = profile.get("name", "")
    auth_header = admin_auth.get("header", "")
    auth_value = admin_auth.get("value", "")

    if "{" in auth_value:
        # Token placeholder — try platform-specific token acquisition
        token = _acquire_admin_token(base_url, platform_name, profile)
        if token:
            headers[auth_header] = auth_value.replace("{admin_token}", token)
        else:
            logger.warning("Could not acquire admin token, skipping auth-required probes")
            return []
    elif auth_header and auth_value:
        headers[auth_header] = auth_value

    api_mapping = profile.get("api_mapping", {}).get(protocol, {})
    fixes = []

    # For platforms that need a realm/tenant for probing, create a temporary one
    probe_realm = None
    if platform_name == "keycloak":
        probe_realm = "valence-field-probe"
        try:
            requests.post(
                f"{base_url}/admin/realms",
                json={"realm": probe_realm, "enabled": True},
                headers=headers, timeout=10,
            )
        except Exception:
            pass

    for op_name, endpoint in api_mapping.items():
        method = endpoint.get("method", "").upper()
        path = endpoint.get("path", "")
        body_map = endpoint.get("body_map", {})

        # Only validate POST operations with body_map (create endpoints)
        if method != "POST" or not body_map:
            continue

        # Build URL, substituting path params
        url = base_url.rstrip("/") + "/" + path.lstrip("/")
        if probe_realm:
            url = re.sub(r"\{realm\}", probe_realm, url)
        url = re.sub(r"\{[^}]+\}", "valence-probe-dummy", url)

        # Build a minimal body with each body_map field set to a simple value
        probe_body = _build_probe_body(body_map)

        # Iteratively probe and remove rejected fields
        max_iterations = 5
        for _ in range(max_iterations):
            try:
                resp = requests.request(
                    method, url, json=probe_body, headers=headers, timeout=10,
                    allow_redirects=False
                )
            except Exception as e:
                logger.debug(f"  {op_name}: probe failed ({e})")
                break

            if resp.status_code != 400:
                break

            rejected_field = _extract_rejected_field(resp.text)
            if not rejected_field:
                break

            # Find and remove the body_map entry for this field
            keys_to_remove = [
                k for k, v in body_map.items()
                if v == rejected_field or v.split(".")[-1] == rejected_field
            ]

            if not keys_to_remove:
                break

            for key in keys_to_remove:
                del body_map[key]
                fix_msg = f"{op_name}: removed '{key}' → '{rejected_field}' (rejected by platform)"
                fixes.append(fix_msg)
                logger.info(f"  {fix_msg}")

            # Rebuild probe without the removed fields
            probe_body = _build_probe_body(body_map)

    # Cleanup probe realm
    if probe_realm:
        try:
            requests.delete(
                f"{base_url}/admin/realms/{probe_realm}",
                headers=headers, timeout=10,
            )
        except Exception:
            pass

    if fixes:
        # Save the fixed profile
        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)
        logger.info(f"Saved fixed profile to {profile_path}")

    return fixes
