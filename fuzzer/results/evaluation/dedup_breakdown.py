#!/usr/bin/env python3
"""Break down dedup by branch: mutation_sweep vs sequence-level oracle."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
EXPS = ["exp1", "exp2", "exp3"]


def classify(f: dict) -> str:
    """Return 'sweep' or 'seq' — mirrors FindingRecord.dedup_key()."""
    source = (f.get("evidence") or {}).get("source", "")
    if source == "mutation_sweep" or f.get("verdict_path") == "mutation_sweep":
        return "sweep"
    return "seq"


def dedup_key(f: dict) -> str:
    """Replicate FindingRecord.dedup_key() from campaign_report.py."""
    if classify(f) == "sweep":
        mutation_name = (f.get("evidence") or {}).get("mutation_name", "unknown")
        if mutation_name.startswith("i4_bound_claims_glob"):
            mutation_name = "i4_bound_claims_glob"
        return f"sweep:{f.get('identified_invariant','')}:{mutation_name}"
    else:
        core = f"seq:{f.get('identified_invariant','')}:{f.get('verdict_path','')}"
        desc_hash = hashlib.md5(f.get("description", "").lower().encode()).hexdigest()[:8]
        return f"{core}:{desc_hash}"


def dedup_firstwin(findings: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for f in findings:
        k = dedup_key(f)
        if k in seen:
            continue
        seen.add(k)
        out.append(f)
    return out


def iter_campaign_findings(exp: Path):
    for platform in sorted(p for p in exp.iterdir() if p.is_dir() and p.name != "logs"):
        for protocol in sorted(p for p in platform.iterdir() if p.is_dir()):
            full = protocol / "full"
            if not full.is_dir():
                continue
            for camp in sorted(full.iterdir()):
                if not camp.is_dir() or not camp.name.startswith("campaign_") or camp.name.startswith("campaign_vault_"):
                    continue
                fpath = camp / "findings.json"
                if not fpath.is_file():
                    continue
                with fpath.open() as fh:
                    yield platform.name, protocol.name, json.load(fh)


def main() -> None:
    grand = {
        "sweep": {"raw": 0, "unique": 0},
        "seq":   {"raw": 0, "unique": 0},
    }
    print(f"{'exp':<5} {'branch':<6} {'raw':>6} {'unique':>7} {'removed':>8}")
    print("-" * 38)
    for exp in EXPS:
        exp_dir = ROOT / exp
        if not exp_dir.is_dir():
            continue
        by_branch = {"sweep": [], "seq": []}
        for _, _, findings in iter_campaign_findings(exp_dir):
            # Dedup is applied per-campaign (matches real unique_findings.json).
            # We classify raw findings and re-run the same first-win dedup within
            # each campaign, then sum across campaigns.
            by_camp_branch = {"sweep": [], "seq": []}
            for f in findings:
                by_camp_branch[classify(f)].append(f)
            # Per-campaign dedup (cross-branch keys don't collide by construction).
            for br in ("sweep", "seq"):
                by_branch[br].append((by_camp_branch[br], dedup_firstwin(by_camp_branch[br])))
        for br in ("sweep", "seq"):
            raw = sum(len(r) for r, _ in by_branch[br])
            uniq = sum(len(u) for _, u in by_branch[br])
            print(f"{exp:<5} {br:<6} {raw:>6} {uniq:>7} {raw-uniq:>8}")
            grand[br]["raw"] += raw
            grand[br]["unique"] += uniq
        print("-" * 38)

    print("=== TOTAL ===")
    tot_raw = tot_uniq = 0
    for br in ("sweep", "seq"):
        r, u = grand[br]["raw"], grand[br]["unique"]
        tot_raw += r
        tot_uniq += u
        pct = (r - u) / r * 100 if r else 0.0
        print(f"  {br:<6} raw={r:>4}  unique={u:>4}  removed={r-u:>4}  ({pct:.1f}%)")
    print(f"  {'ALL':<6} raw={tot_raw:>4}  unique={tot_uniq:>4}  removed={tot_raw-tot_uniq:>4}")


if __name__ == "__main__":
    main()
