#!/usr/bin/env python3
"""Count findings and unique_findings across exp1/exp2/exp3 campaign dirs."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
EXPS = ["exp1", "exp2", "exp3"]


def count_json_list(path: Path) -> int:
    if not path.is_file():
        return 0
    with path.open() as f:
        data = json.load(f)
    return len(data) if isinstance(data, list) else 0


def main() -> None:
    grand_findings = 0
    grand_unique = 0
    print(f"{'exp':<5} {'platform':<10} {'protocol':<10} {'findings':>10} {'unique':>8}")
    print("-" * 48)
    for exp in EXPS:
        exp_dir = ROOT / exp
        if not exp_dir.is_dir():
            continue
        exp_findings = 0
        exp_unique = 0
        for platform_dir in sorted(p for p in exp_dir.iterdir() if p.is_dir() and p.name != "logs"):
            for protocol_dir in sorted(p for p in platform_dir.iterdir() if p.is_dir()):
                full_dir = protocol_dir / "full"
                if not full_dir.is_dir():
                    continue
                for campaign_dir in sorted(full_dir.iterdir()):
                    if not campaign_dir.is_dir() or not campaign_dir.name.startswith("campaign_"):
                        continue
                    if campaign_dir.name.startswith("campaign_vault_"):
                        continue
                    f_count = count_json_list(campaign_dir / "findings.json")
                    u_count = count_json_list(campaign_dir / "unique_findings.json")
                    exp_findings += f_count
                    exp_unique += u_count
                    print(f"{exp:<5} {platform_dir.name:<10} {protocol_dir.name:<10} {f_count:>10} {u_count:>8}")
        print(f"{exp:<5} {'SUBTOTAL':<21} {exp_findings:>10} {exp_unique:>8}")
        print("-" * 48)
        grand_findings += exp_findings
        grand_unique += exp_unique
    print(f"{'TOTAL':<27} {grand_findings:>10} {grand_unique:>8}")


if __name__ == "__main__":
    main()
