#!/usr/bin/env python3
"""Wipe all VALENCE test residuals from Vault before a new campaign run.

Deletes:
  - All JWT auth mounts except the base 'jwt/' (mounts with type=jwt)
  - All policies except 'root' and 'default'
  - All identity entities
  - All identity groups
  - All KV v2 secrets under secret/data/ (lists then deletes metadata)

Usage:
  python3 scripts/cleanup_vault.py [--url http://localhost:8200] [--token root] [--dry-run]
"""

import argparse
import sys
import requests


def cleanup(base_url: str, token: str, dry_run: bool):
    h = {"X-Vault-Token": token, "Content-Type": "application/json"}
    deleted = {"mounts": 0, "policies": 0, "entities": 0, "groups": 0, "secrets": 0}

    def delete(path, label):
        if dry_run:
            print(f"  [DRY-RUN] DELETE {path}")
            return True
        r = requests.delete(f"{base_url}{path}", headers=h, timeout=10)
        if r.status_code in (200, 204):
            return True
        print(f"  WARN: DELETE {path} → {r.status_code}")
        return False

    # ── 1. JWT auth mounts ────────────────────────────────────────────────────
    print("── JWT auth mounts ──")
    r = requests.get(f"{base_url}/v1/sys/auth", headers=h, timeout=10)
    mounts = r.json().get("data", r.json())
    for mount, info in mounts.items():
        if info.get("type") == "jwt":
            print(f"  Deleting auth mount: {mount}")
            if delete(f"/v1/sys/auth/{mount.rstrip('/')}", "mount"):
                deleted["mounts"] += 1

    # ── 2. Policies ───────────────────────────────────────────────────────────
    print("\n── Policies ──")
    r = requests.get(f"{base_url}/v1/sys/policies/acl?list=true", headers=h, timeout=10)
    policies = r.json().get("data", {}).get("keys", [])
    KEEP = {"root", "default"}
    for pol in policies:
        if pol in KEEP:
            continue
        print(f"  Deleting policy: {pol}")
        if delete(f"/v1/sys/policies/acl/{pol}", "policy"):
            deleted["policies"] += 1

    # ── 3. Identity entities ──────────────────────────────────────────────────
    print("\n── Identity entities ──")
    r = requests.get(f"{base_url}/v1/identity/entity/id?list=true", headers=h, timeout=10)
    entity_ids = r.json().get("data", {}).get("keys", [])
    for eid in entity_ids:
        print(f"  Deleting entity: {eid}")
        if delete(f"/v1/identity/entity/id/{eid}", "entity"):
            deleted["entities"] += 1

    # ── 4. Identity groups ────────────────────────────────────────────────────
    print("\n── Identity groups ──")
    r = requests.get(f"{base_url}/v1/identity/group/id?list=true", headers=h, timeout=10)
    group_ids = r.json().get("data", {}).get("keys", [])
    for gid in group_ids:
        print(f"  Deleting group: {gid}")
        if delete(f"/v1/identity/group/id/{gid}", "group"):
            deleted["groups"] += 1

    # ── 5. KV secrets under secret/ ──────────────────────────────────────────
    print("\n── KV secrets ──")

    def delete_kv_tree(prefix: str):
        r = requests.get(
            f"{base_url}/v1/secret/metadata/{prefix}?list=true",
            headers=h, timeout=10
        )
        if r.status_code == 404:
            return
        keys = r.json().get("data", {}).get("keys", [])
        for key in keys:
            full = prefix + key
            if key.endswith("/"):
                delete_kv_tree(full)
            else:
                print(f"  Deleting secret: {full}")
                if delete(f"/v1/secret/metadata/{full}", "secret"):
                    deleted["secrets"] += 1

    delete_kv_tree("")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'[DRY-RUN] ' if dry_run else ''}Cleanup complete:")
    for k, v in deleted.items():
        print(f"  {k}: {v} deleted")


def main():
    parser = argparse.ArgumentParser(description="Clean up VALENCE Vault test residuals")
    parser.add_argument("--url", default="http://localhost:8200")
    parser.add_argument("--token", default="root")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be deleted without deleting")
    args = parser.parse_args()

    # Quick health check
    try:
        r = requests.get(f"{args.url}/v1/sys/health", timeout=5)
        if not r.json().get("initialized"):
            print("Vault is not initialized. Aborting.")
            sys.exit(1)
    except Exception as e:
        print(f"Cannot reach Vault at {args.url}: {e}")
        sys.exit(1)

    print(f"Cleaning Vault at {args.url} (dry_run={args.dry_run})\n")
    cleanup(args.url, args.token, args.dry_run)


if __name__ == "__main__":
    main()
