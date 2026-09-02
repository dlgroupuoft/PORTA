"""One-time script to populate CVE test registry from classification CSV.

Reads `identity_broker_logic_vulnerability_classification_v5.csv` and creates
initial `src/experiments/cve_tests.json` entries for all CVEs where
Reproducible == "Yes".  Docker image tags are set to FIXME placeholders —
fill them in manually before running experiments.

Usage:
    python -m src.experiments.populate_registry
    python -m src.experiments.populate_registry \\
        --csv path/to/classification.csv \\
        --output src/experiments/cve_tests.json
"""

import argparse
import csv
import json
import os
import sys


# Normalise platform name strings coming from the CSV to canonical short IDs.
# Entries are matched case-insensitively; the first prefix that matches wins.
_PLATFORM_MAP: dict[str, str] = {
    "keycloak":           "keycloak",
    "hashicorp vault":    "vault",
    "vault enterprise":   "vault",
    "vault":              "vault",
    "dex":                "dex",
    "teleport":           "teleport",
    "ory hydra":          "hydra",
    "ory fosite":         "hydra",   # Fosite is the library Hydra builds on
    "ory kratos":         "kratos",
    "conjur":             "conjur",
    "keystone":           "keystone",
    "openstack keystone": "keystone",
    "shibboleth":         "shibboleth",
    "opensaml":           "opensaml",
    "casdoor":            "casdoor",
}


def _normalize_platform(raw: str) -> str:
    """Return canonical platform ID for *raw* (case-insensitive prefix match)."""
    low = raw.strip().lower()
    for key, canonical in _PLATFORM_MAP.items():
        if low == key or low.startswith(key):
            return canonical
    # Fall back: lower-case, replace spaces with underscores
    return low.replace(" ", "_")


def _reproducible(value: str) -> bool:
    """Return True only for cells whose first word is 'yes' (case-insensitive)."""
    return value.strip().lower().startswith("yes")


def populate(
    csv_path: str = "identity_broker_logic_vulnerability_classification_v5.csv",
    output_path: str = "src/experiments/cve_tests.json",
) -> list[dict]:
    """Read the CSV and write cve_tests.json.  Returns the list of cases written."""
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    cases: list[dict] = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not _reproducible(row.get("Reproducible", "")):
                continue

            cve_id   = row.get("CVE ID", "").strip()
            platform = _normalize_platform(row.get("Platform", ""))
            invariant = row.get("Primary Invariant", "").strip()

            # Normalise invariant: keep only the prefix up to the first space
            # e.g. "I1 Proof Integrity" -> "I1"
            invariant_id = invariant.split()[0] if invariant else invariant

            subtype = row.get("Subtype", "").strip()

            cases.append({
                "cve_id":          cve_id,
                "platform":        platform,
                "invariant":       invariant_id,
                "subtype":         subtype,
                "description":     row.get("Vulnerability Pattern (Short)", "").strip(),
                "vulnerable_image": f"FIXME:{platform}-vulnerable",
                "patched_image":    f"FIXME:{platform}-patched",
                "docker_compose_override": "",
                "profile_path":    f"src/profiles/{platform}.json",
                "attack_sequence_path": "",
                "vulnerable_expected": "VIOLATION",
                "patched_expected":    "NO_VIOLATION",
            })

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"cases": cases}, f, indent=2)

    print(f"Wrote {len(cases)} reproducible CVE test cases → {output_path}")
    for c in cases:
        print(f"  {c['cve_id']:20s}  platform={c['platform']:12s}  invariant={c['invariant']}")

    return cases


def main():
    parser = argparse.ArgumentParser(
        description="Populate CVE test registry from classification CSV"
    )
    parser.add_argument(
        "--csv",
        default="identity_broker_logic_vulnerability_classification_v5.csv",
        help="Path to the classification CSV (default: current directory)",
    )
    parser.add_argument(
        "--output",
        default="src/experiments/cve_tests.json",
        help="Destination JSON path (default: src/experiments/cve_tests.json)",
    )
    args = parser.parse_args()
    populate(csv_path=args.csv, output_path=args.output)


if __name__ == "__main__":
    main()
