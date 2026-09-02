#!/usr/bin/env python3
"""Triage: Does Keycloak strip XML comments from NameID before creating identity?

Tests whether SAML NameID with embedded XML comments (e.g., adm<!--x-->in@evil.com)
produces an identity collision with the clean version (admin@evil.com).
"""

import json
import logging
import requests
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

KC_BASE = "http://localhost:8080"
REALM = "valence-saml-triage"
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
    results = {"finding": "comment_injection_nameid", "platform": "keycloak", "steps": []}

    # 1. Get admin token
    token = get_admin_token()
    h = admin_headers(token)
    log.info("[1] Got admin token")

    # 2. Delete + create triage realm
    requests.delete(f"{KC_BASE}/admin/realms/{REALM}", headers=h)
    r = requests.post(f"{KC_BASE}/admin/realms", headers=h, json={
        "realm": REALM, "enabled": True, "sslRequired": "none"
    })
    log.info(f"[2] Create realm: {r.status_code}")
    results["steps"].append({"step": "create_realm", "status": r.status_code})

    # 3. Create a real user "admin@evil.com"
    r = requests.post(f"{KC_BASE}/admin/realms/{REALM}/users", headers=h, json={
        "username": "admin@evil.com",
        "enabled": True,
        "email": "admin@evil.com",
        "emailVerified": True,
        "credentials": [{"type": "password", "value": "admin-pass", "temporary": False}],
    })
    log.info(f"[3] Create real user 'admin@evil.com': {r.status_code}")
    results["steps"].append({"step": "create_real_user", "status": r.status_code})

    # 4. Try to create user with comment-injected name
    comment_name = "adm<!--x-->in@evil.com"
    r = requests.post(f"{KC_BASE}/admin/realms/{REALM}/users", headers=h, json={
        "username": comment_name,
        "enabled": True,
        "email": comment_name,
        "credentials": [{"type": "password", "value": "injected-pass", "temporary": False}],
    })
    log.info(f"[4] Create comment-injected user '{comment_name}': {r.status_code}")
    results["steps"].append({
        "step": "create_comment_user",
        "username": comment_name,
        "status": r.status_code,
        "response": r.text[:500] if r.status_code != 201 else "created"
    })

    # 5. Check: does Keycloak treat these as same user? (case-insensitive + comment strip?)
    r = requests.get(f"{KC_BASE}/admin/realms/{REALM}/users?search=admin", headers=h)
    users = r.json()
    log.info(f"[5] Users matching 'admin': {len(users)}")
    for u in users:
        log.info(f"    username={u['username']}, id={u['id']}, email={u.get('email')}")
    results["steps"].append({
        "step": "search_users",
        "count": len(users),
        "users": [{"username": u["username"], "id": u["id"]} for u in users]
    })

    # 6. Try ROPC login with both identities (if both created)
    for username, password in [("admin@evil.com", "admin-pass"), (comment_name, "injected-pass")]:
        # Create a client for ROPC
        requests.post(f"{KC_BASE}/admin/realms/{REALM}/clients", headers=h, json={
            "clientId": "triage-client", "enabled": True, "protocol": "openid-connect",
            "publicClient": True, "directAccessGrantsEnabled": True,
        })
        r = requests.post(f"{KC_BASE}/realms/{REALM}/protocol/openid-connect/token", data={
            "grant_type": "password", "client_id": "triage-client",
            "username": username, "password": password,
        })
        if r.status_code == 200:
            token_data = r.json()
            access_token = token_data["access_token"]
            # Get userinfo
            ui = requests.get(
                f"{KC_BASE}/realms/{REALM}/protocol/openid-connect/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            ).json()
            log.info(f"[6] Login as '{username}': sub={ui.get('sub')}, "
                     f"preferred_username={ui.get('preferred_username')}")
            results["steps"].append({
                "step": f"login_{username}",
                "success": True,
                "sub": ui.get("sub"),
                "preferred_username": ui.get("preferred_username"),
            })
        else:
            log.info(f"[6] Login as '{username}': FAILED ({r.status_code})")
            results["steps"].append({
                "step": f"login_{username}",
                "success": False,
                "status": r.status_code,
            })

    # 7. Determine verdict
    user_count = len(users)
    if user_count == 1:
        verdict = "CONFIRMED_BUG"
        impact = "Comment stripped — identity collision. adm<!--x-->in@evil.com collapsed to admin@evil.com"
    elif user_count == 2:
        # Check if usernames are different
        usernames = [u["username"] for u in users]
        if comment_name in usernames:
            verdict = "FALSE_POSITIVE"
            impact = "Comment preserved as literal — no identity collision"
        else:
            verdict = "DESIGN_RISK"
            impact = f"Unexpected user mapping: {usernames}"
    elif user_count == 0:
        verdict = "INCONCLUSIVE"
        impact = "No users found — setup issue"
    else:
        verdict = "DESIGN_RISK"
        impact = f"Unexpected: {user_count} users matching 'admin'"

    results["verdict"] = verdict
    results["impact"] = impact
    log.info(f"\n=== VERDICT: {verdict} ===")
    log.info(f"Impact: {impact}")

    # Cleanup
    requests.delete(f"{KC_BASE}/admin/realms/{REALM}", headers=h)

    # Save results
    out = Path("results/triage_20260314/comment_injection_triage.json")
    out.write_text(json.dumps(results, indent=2))
    log.info(f"\nResults saved: {out}")
    return verdict


if __name__ == "__main__":
    verdict = main()
    sys.exit(0 if verdict != "CONFIRMED_BUG" else 1)
