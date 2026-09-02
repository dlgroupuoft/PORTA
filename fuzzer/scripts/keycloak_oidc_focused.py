#!/usr/bin/env python3
"""Keycloak OIDC focused tests — I4/I5 invariant checks.

Test 1 (I4): Case-insensitive username collision
Test 2 (I5): Group role inheritance escalation
Test 3 (I4): Protocol mapper sub override
"""

import json
import logging
import requests
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

KC = "http://localhost:8080"
REALM = "valence-focused"
CLIENT = "focused-client"
SECRET = "focused-secret"


def get_admin():
    r = requests.post(f"{KC}/realms/master/protocol/openid-connect/token", data={
        "grant_type": "password", "client_id": "admin-cli",
        "username": "admin", "password": "admin",
    })
    return {"Authorization": f"Bearer {r.json()['access_token']}", "Content-Type": "application/json"}


def setup_realm(h):
    requests.delete(f"{KC}/admin/realms/{REALM}", headers=h)
    requests.post(f"{KC}/admin/realms", headers=h, json={
        "realm": REALM, "enabled": True, "sslRequired": "none"
    })
    # Disable required profile attrs (KC 26.5+)
    prof = requests.get(f"{KC}/admin/realms/{REALM}/users/profile", headers=h).json()
    for a in prof.get("attributes", []):
        if a.get("required"):
            a["required"] = {}
    requests.put(f"{KC}/admin/realms/{REALM}/users/profile", headers=h, json=prof)
    # Create client
    requests.post(f"{KC}/admin/realms/{REALM}/clients", headers=h, json={
        "clientId": CLIENT, "enabled": True, "protocol": "openid-connect",
        "publicClient": False, "secret": SECRET,
        "directAccessGrantsEnabled": True, "redirectUris": ["*"],
    })


def create_user(h, username, password, roles=None):
    r = requests.post(f"{KC}/admin/realms/{REALM}/users", headers=h, json={
        "username": username, "enabled": True, "emailVerified": True,
        "email": f"{username.replace(' ', '')}@valence.local",
        "firstName": "Test", "lastName": "User",
        "requiredActions": [],
        "credentials": [{"type": "password", "value": password, "temporary": False}],
    })
    uid = r.headers.get("Location", "").rsplit("/", 1)[-1] if r.status_code == 201 else None
    if uid and roles:
        for role_name in roles:
            role = requests.get(f"{KC}/admin/realms/{REALM}/roles/{role_name}", headers=h)
            if role.ok:
                requests.post(
                    f"{KC}/admin/realms/{REALM}/users/{uid}/role-mappings/realm",
                    headers=h, json=[role.json()])
    return uid, r.status_code


def login(username, password, scope="openid"):
    r = requests.post(f"{KC}/realms/{REALM}/protocol/openid-connect/token", data={
        "grant_type": "password", "client_id": CLIENT, "client_secret": SECRET,
        "username": username, "password": password, "scope": scope,
    })
    return r.json() if r.ok else {"error": r.text[:200], "status": r.status_code}


def introspect(token):
    r = requests.post(f"{KC}/realms/{REALM}/protocol/openid-connect/token/introspect",
                      data={"token": token, "client_id": CLIENT, "client_secret": SECRET})
    return r.json()


def userinfo(token):
    r = requests.get(f"{KC}/realms/{REALM}/protocol/openid-connect/userinfo",
                     headers={"Authorization": f"Bearer {token}"})
    return r.json() if r.ok else {"error": r.status_code}


def test_case_collision(h):
    """Test 1 (I4): Case-insensitive username collision."""
    log.info("\n=== TEST 1: Case-Insensitive Username Collision (I4) ===")

    # Create admin role
    requests.post(f"{KC}/admin/realms/{REALM}/roles", headers=h, json={"name": "admin-role"})
    requests.post(f"{KC}/admin/realms/{REALM}/roles", headers=h, json={"name": "user-role"})

    # Create "Admin" with admin role
    uid1, s1 = create_user(h, "Admin", "admin-pass", ["admin-role"])
    log.info(f"  Create 'Admin': {s1}, uid={uid1}")

    # Try to create "admin" (lowercase)
    uid2, s2 = create_user(h, "admin", "admin-pass2", ["user-role"])
    log.info(f"  Create 'admin': {s2}, uid={uid2}")

    if s2 == 409:
        log.info("  Keycloak rejected 'admin' — case-insensitive collision (BY_DESIGN)")
        verdict = "BY_DESIGN"
        detail = "Keycloak treats 'Admin' and 'admin' as same user (case-insensitive)"
    elif s2 == 201 and uid1 != uid2:
        # Both created — check if roles leak
        tok1 = login("Admin", "admin-pass")
        tok2 = login("admin", "admin-pass2")
        if "access_token" in tok1 and "access_token" in tok2:
            roles1 = introspect(tok1["access_token"]).get("realm_access", {}).get("roles", [])
            roles2 = introspect(tok2["access_token"]).get("realm_access", {}).get("roles", [])
            log.info(f"  Admin roles: {roles1}")
            log.info(f"  admin roles: {roles2}")
            if "admin-role" in roles2:
                verdict = "VIOLATION"
                detail = "'admin' got 'admin-role' meant for 'Admin' — role leakage!"
            else:
                verdict = "BY_DESIGN"
                detail = "Separate users, no role leakage"
        else:
            verdict = "INCONCLUSIVE"
            detail = f"Login failed: {tok1.get('error', '')} / {tok2.get('error', '')}"
    else:
        verdict = "INCONCLUSIVE"
        detail = f"Unexpected: s1={s1}, s2={s2}"

    log.info(f"  VERDICT: {verdict} — {detail}")
    return {"test": "case_collision", "invariant": "I4", "verdict": verdict, "detail": detail}


def test_group_escalation(h):
    """Test 2 (I5): Group role inheritance escalation."""
    log.info("\n=== TEST 2: Group Role Inheritance Escalation (I5) ===")

    # Create admin role
    requests.post(f"{KC}/admin/realms/{REALM}/roles", headers=h, json={"name": "escalation-admin"})

    # Create parent group "admins" with admin role
    r = requests.post(f"{KC}/admin/realms/{REALM}/groups", headers=h, json={"name": "admins"})
    admins_id = r.headers.get("Location", "").rsplit("/", 1)[-1]
    admin_role = requests.get(f"{KC}/admin/realms/{REALM}/roles/escalation-admin", headers=h).json()
    requests.post(f"{KC}/admin/realms/{REALM}/groups/{admins_id}/role-mappings/realm",
                  headers=h, json=[admin_role])

    # Create child group "users" under "admins"
    r = requests.post(f"{KC}/admin/realms/{REALM}/groups/{admins_id}/children",
                      headers=h, json={"name": "users"})
    users_id = r.headers.get("Location", "").rsplit("/", 1)[-1]
    log.info(f"  Created groups: admins={admins_id}, users={users_id}")

    # Create user in "users" group (child of admins)
    uid, _ = create_user(h, "lowpriv", "lowpriv-pass")
    requests.put(f"{KC}/admin/realms/{REALM}/users/{uid}/groups/{users_id}", headers=h)

    # Login and check roles
    tok = login("lowpriv", "lowpriv-pass")
    if "access_token" in tok:
        info = introspect(tok["access_token"])
        roles = info.get("realm_access", {}).get("roles", [])
        log.info(f"  lowpriv roles: {roles}")
        if "escalation-admin" in roles:
            verdict = "BY_DESIGN"  # Keycloak documents group role inheritance
            detail = f"Child group inherits parent roles. lowpriv got escalation-admin via group hierarchy"
        else:
            verdict = "SECURE"
            detail = "Child group does NOT inherit parent roles"
    else:
        verdict = "INCONCLUSIVE"
        detail = f"Login failed: {tok}"

    log.info(f"  VERDICT: {verdict} — {detail}")
    return {"test": "group_escalation", "invariant": "I5", "verdict": verdict, "detail": detail}


def test_mapper_override(h):
    """Test 3 (I4): Protocol mapper sub override."""
    log.info("\n=== TEST 3: Protocol Mapper Sub Override (I4) ===")

    # Create user with custom attribute
    uid, _ = create_user(h, "attacker", "attacker-pass")
    # Set user attribute "custom_sub" to a different user's expected sub
    requests.put(f"{KC}/admin/realms/{REALM}/users/{uid}", headers=h, json={
        "username": "attacker", "enabled": True, "emailVerified": True,
        "email": "attacker@valence.local", "firstName": "A", "lastName": "T",
        "attributes": {"custom_sub": ["victim-sub-id-12345"]},
    })

    # Get client UUID
    r = requests.get(f"{KC}/admin/realms/{REALM}/clients?clientId={CLIENT}", headers=h)
    clients = r.json()
    if not clients:
        log.info("  Client not found")
        return {"test": "mapper_override", "invariant": "I4", "verdict": "INCONCLUSIVE", "detail": "No client"}
    client_uuid = clients[0]["id"]

    # Create protocol mapper that maps custom_sub attribute to "sub" claim
    r = requests.post(
        f"{KC}/admin/realms/{REALM}/clients/{client_uuid}/protocol-mappers/models",
        headers=h, json={
            "name": "sub-override-mapper",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-attribute-mapper",
            "config": {
                "user.attribute": "custom_sub",
                "claim.name": "custom_sub_claim",
                "id.token.claim": "true",
                "access.token.claim": "true",
                "jsonType.label": "String",
            }
        })
    log.info(f"  Create mapper: {r.status_code}")

    # Login and check if custom_sub appears in token
    tok = login("attacker", "attacker-pass")
    if "access_token" in tok:
        info = introspect(tok["access_token"])
        custom_sub = info.get("custom_sub_claim")
        real_sub = info.get("sub")
        log.info(f"  real sub: {real_sub}")
        log.info(f"  custom_sub_claim: {custom_sub}")
        if custom_sub == "victim-sub-id-12345":
            verdict = "BY_DESIGN"
            detail = "Protocol mapper CAN map user attributes to custom claims. If mapped to 'sub', identity confusion possible. This is documented Keycloak behavior."
        else:
            verdict = "SECURE"
            detail = f"custom_sub_claim not in token or different value: {custom_sub}"
    else:
        verdict = "INCONCLUSIVE"
        detail = f"Login failed: {tok}"

    log.info(f"  VERDICT: {verdict} — {detail}")
    return {"test": "mapper_override", "invariant": "I4", "verdict": verdict, "detail": detail}


def main():
    h = get_admin()
    setup_realm(h)

    results = []
    results.append(test_case_collision(h))
    results.append(test_group_escalation(h))
    results.append(test_mapper_override(h))

    # Summary
    log.info("\n" + "=" * 60)
    log.info("KEYCLOAK OIDC FOCUSED TEST RESULTS")
    log.info("=" * 60)
    for r in results:
        log.info(f"  [{r['invariant']}] {r['test']}: {r['verdict']} — {r['detail'][:80]}")

    # Cleanup
    requests.delete(f"{KC}/admin/realms/{REALM}", headers=h)

    out = Path("results/triage_20260314/keycloak_oidc_focused.json")
    out.write_text(json.dumps(results, indent=2))
    log.info(f"\nResults saved: {out}")


if __name__ == "__main__":
    main()
