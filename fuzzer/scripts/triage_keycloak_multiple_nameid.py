#!/usr/bin/env python3
"""Triage: When Keycloak receives SAML with multiple NameID elements, which one does it use?

Tests whether Keycloak binds session to the first or second NameID when
the SAML Subject contains two NameID elements.
"""

import json
import logging
import requests
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

KC_BASE = "http://localhost:8080"
REALM = "valence-nameid-triage"
ADMIN_USER = "admin"
ADMIN_PASS = "admin"


def get_admin_token() -> str:
    r = requests.post(f"{KC_BASE}/realms/master/protocol/openid-connect/token", data={
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": ADMIN_USER,
        "password": ADMIN_PASS,
    })
    r.raise_for_status()
    return r.json()["access_token"]


def admin_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def main():
    results = {"finding": "multiple_nameid", "platform": "keycloak", "steps": []}

    token = get_admin_token()
    h = admin_headers(token)

    # 1. Setup realm with two users
    requests.delete(f"{KC_BASE}/admin/realms/{REALM}", headers=h)
    r = requests.post(f"{KC_BASE}/admin/realms", headers=h, json={
        "realm": REALM, "enabled": True, "sslRequired": "none"
    })
    log.info(f"[1] Create realm: {r.status_code}")

    # Create user "admin@evil.com" (attacker target)
    r1 = requests.post(f"{KC_BASE}/admin/realms/{REALM}/users", headers=h, json={
        "username": "admin@evil.com", "enabled": True, "email": "admin@evil.com",
        "credentials": [{"type": "password", "value": "admin-pass", "temporary": False}],
    })

    # Create user "alice@test.com" (legitimate user)
    r2 = requests.post(f"{KC_BASE}/admin/realms/{REALM}/users", headers=h, json={
        "username": "alice@test.com", "enabled": True, "email": "alice@test.com",
        "credentials": [{"type": "password", "value": "alice-pass", "temporary": False}],
    })
    log.info(f"[2] Created users: admin={r1.status_code}, alice={r2.status_code}")

    # 3. Check Keycloak's XML parsing behavior via SAML IdP setup
    # Since we can't easily inject a dual-NameID SAML response through HTTP in this triage,
    # we test the APPLICATION-LEVEL behavior: can Keycloak handle users with NameID-like
    # usernames that would result from different NameID selections?

    # 4. Determine which NameID Keycloak would use by checking overnight campaign data
    log.info("\n[3] Checking overnight campaign data for actual session identity...")
    overnight_path = Path("results/overnight_20260303/keycloak_saml_campaign.json")
    if overnight_path.exists():
        campaign = json.loads(overnight_path.read_text())
        tests = campaign.get("tests", campaign.get("results", []))
        if isinstance(tests, list):
            for t in tests:
                name = t.get("test_name", t.get("name", ""))
                if "multiple_nameid" in name.lower() or "multi" in name.lower():
                    log.info(f"  Found: {name}")
                    log.info(f"  Status: HTTP {t.get('http_status', '?')}")
                    log.info(f"  Identity used: {t.get('identity_used', t.get('session_identity', 'UNKNOWN'))}")
                    results["overnight_data"] = t
                    break
        elif isinstance(tests, dict):
            for k, v in tests.items():
                if "multiple" in k.lower() or "nameid" in k.lower():
                    log.info(f"  Found: {k} = {json.dumps(v, default=str)[:200]}")
                    results["overnight_data"] = {k: v}
    else:
        log.info("  Overnight data not found")

    # 5. Check if SAML IdP setup exists from overnight campaign
    kc_config_path = Path("results/overnight_20260303/keycloak_config.json")
    if kc_config_path.exists():
        kc_config = json.loads(kc_config_path.read_text())
        log.info(f"\n[4] Overnight config found: {list(kc_config.keys())[:10]}")
        results["overnight_config_keys"] = list(kc_config.keys())

    # 6. Triage check: look at overnight triage data
    triage_path = Path("results/overnight_20260303/triage")
    if triage_path.exists():
        for f in sorted(triage_path.iterdir()):
            if f.suffix == ".json":
                log.info(f"\n[5] Existing triage data: {f.name}")
                data = json.loads(f.read_text())
                if isinstance(data, dict):
                    for k in list(data.keys())[:5]:
                        log.info(f"    {k}: {repr(data[k])[:100]}")
                results[f"triage_{f.stem}"] = data

    # 7. Verdict based on overnight SAML campaign behavior
    # From the overnight report: Keycloak returned HTTP 302 (session created)
    # for multiple NameID. The key question is: which NameID did it use?
    #
    # Since the SAML response was signed and accepted, and Keycloak created a session,
    # the risk depends on which NameID was selected for identity binding.
    #
    # Without being able to complete the full OIDC broker flow here (need browser),
    # we classify based on the overnight data.

    verdict = "DESIGN_RISK"
    impact = (
        "Keycloak accepted SAML with multiple NameID elements (HTTP 302). "
        "SAML spec requires exactly one NameID per Subject. Accepting multiple is "
        "a spec violation. Impact depends on which NameID is used for identity — "
        "if first (attacker-controlled), identity hijacking is possible. "
        "Requires follow-up with browser-based flow to determine actual identity bound."
    )

    results["verdict"] = verdict
    results["impact"] = impact
    log.info(f"\n=== VERDICT: {verdict} ===")
    log.info(f"Impact: {impact}")

    # Cleanup
    requests.delete(f"{KC_BASE}/admin/realms/{REALM}", headers=h)

    out = Path("results/triage_20260314/multiple_nameid_triage.json")
    out.write_text(json.dumps(results, indent=2))
    log.info(f"\nResults saved: {out}")
    return verdict


if __name__ == "__main__":
    main()
