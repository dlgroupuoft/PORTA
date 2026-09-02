#!/usr/bin/env python3
"""Aggregator for the 9 manual_triage_2026/*.py files.

Axis: confidence thresholds (HIGH, HIGH+MEDIUM, ALL). The LLM's verdict_type
(VIOLATION/UNEXPECTED) is NOT used as an analysis axis — Full also counts
UNEXPECTED as findings, so the fair comparison is by confidence only.

Produces:
  - manual_triage_2026/aggregate_results.json (structured)
  - manual_triage_2026/aggregate_results.md (human-readable tables)

Usage:
    cd /home/ubuntu/broker/fuzzer/results/ablation/analysis
    python3 aggregate_triage.py
"""
from __future__ import annotations

import importlib.util
import json
import statistics
from collections import Counter
from pathlib import Path

TRIAGE_DIR = Path(__file__).parent / "manual_triage_2026"
OUT_JSON = TRIAGE_DIR / "aggregate_results.json"
OUT_MD = TRIAGE_DIR / "aggregate_results.md"

VARIANTS = {
    "no_context": ["no_context_r1", "no_context_r2", "no_context_r3"],
    "profile": ["profile_r1", "profile_r2", "profile_r3"],
    "invariant": ["invariant_r1", "invariant_r2", "invariant_r3"],
}

CONF_RANK = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}

# FP-reason normalization (keeps the per_ablation docs' buckets consistent).
#   fabricated     = description is a concrete attack narrative not in the 33
#   hedged         = speculative language or LLM declined to commit; ≠ concrete claim
#   setup-artifact = test-infra failure mistaken for security behavior
#   wrong-classif  = concrete violation on the wrong invariant axis
FP_MAP = {
    "speculative": "hedged",
    "unexpected-not-violation": "hedged",
    "not-in-33": "fabricated",
    "setup-failure": "setup-artifact",
    "wrong-classification": "wrong-classif",
}


def load_triage(run: str) -> dict:
    spec = importlib.util.spec_from_file_location(run, TRIAGE_DIR / f"{run}_triage.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.TRIAGE


def fp_bucket(v: dict) -> str:
    return FP_MAP.get(v["reason"], v["reason"])


def stats_at_threshold(triage: dict, thresh: str) -> dict:
    t_rank = CONF_RANK[thresh]
    at = [v for v in triage.values() if CONF_RANK.get(v["conf"], 0) >= t_rank]
    total = len(at)
    tp_list = [v for v in at if v["label"] == "TP"]
    fp_list = [v for v in at if v["label"] == "FP"]
    fp_buckets = Counter(fp_bucket(v) for v in fp_list)
    flaws = {v["reason"] for v in tp_list}
    return {
        "total": total,
        "tp": len(tp_list),
        "fp": len(fp_list),
        "precision": len(tp_list) / total if total else 0.0,
        "fp_buckets": dict(fp_buckets),
        "flaws": sorted(flaws),
        "flaws_count": len(flaws),
    }


def ms(xs):
    return f"{statistics.mean(xs):.1f}±{statistics.stdev(xs):.1f}"


def pms(xs):
    return f"{statistics.mean(xs) * 100:.1f}%±{statistics.stdev(xs) * 100:.1f}%"


def main():
    all_results: dict = {}

    for variant, runs in VARIANTS.items():
        all_results[variant] = {"per_run": {}, "thresholds": {}}
        triage_by_run = {r: load_triage(r) for r in runs}

        for r, t in triage_by_run.items():
            all_results[variant]["per_run"][r] = {
                "HIGH": stats_at_threshold(t, "HIGH"),
                "MEDIUM": stats_at_threshold(t, "MEDIUM"),
                "LOW": stats_at_threshold(t, "LOW"),
            }

        for thresh in ("HIGH", "MEDIUM", "LOW"):
            per_run_stats = [all_results[variant]["per_run"][r][thresh] for r in runs]
            totals = [s["total"] for s in per_run_stats]
            tps = [s["tp"] for s in per_run_stats]
            fps = [s["fp"] for s in per_run_stats]
            precs = [s["precision"] for s in per_run_stats]
            union_flaws = set()
            for s in per_run_stats:
                union_flaws.update(s["flaws"])
            agg_buckets = Counter()
            for s in per_run_stats:
                agg_buckets.update(s["fp_buckets"])
            all_results[variant]["thresholds"][thresh] = {
                "findings_per_run": totals,
                "findings_mean_std": ms(totals),
                "tp_per_run": tps,
                "tp_mean_std": ms(tps),
                "fp_per_run": fps,
                "fp_mean_std": ms(fps),
                "precision_per_run": precs,
                "precision_mean_std": pms(precs),
                "union_flaws": sorted(union_flaws),
                "union_flaws_count": len(union_flaws),
                "fp_buckets_total": dict(agg_buckets),
            }

    OUT_JSON.write_text(json.dumps(all_results, indent=2, default=str))

    # ───────────── Markdown ─────────────
    lines: list[str] = ["# Manual Triage 2026 — Aggregate Results\n"]
    lines.append(
        "Aggregated from 9 agent-generated triage files in `manual_triage_2026/`. "
        "Each variant × run file contains per-finding TP/FP labels.\n"
    )
    lines.append(
        "Axis = **confidence threshold** (HIGH / HIGH+MEDIUM / ALL). Full "
        "counts all confidence levels as findings, so ALL is the apples-to-apples "
        "comparison. HIGH-only is the most favorable reading for each LLM-judge "
        "variant.\n"
    )

    lines.append("## Per-run counts (ALL threshold = all findings)\n")
    lines.append("| Variant | Run | Findings | TP | FP | Precision | Flaws/run |")
    lines.append("|---|---|---|---|---|---|---|")
    for variant, runs in VARIANTS.items():
        for r in runs:
            s = all_results[variant]["per_run"][r]["LOW"]
            lines.append(
                f"| {variant} | {r} | {s['total']} | {s['tp']} | {s['fp']} | "
                f"{s['precision']*100:.1f}% | {s['flaws_count']} |"
            )

    for thresh_label, thresh in [
        ("HIGH only", "HIGH"),
        ("HIGH + MEDIUM", "MEDIUM"),
        ("ALL (HIGH + MEDIUM + LOW)", "LOW"),
    ]:
        lines.append(f"\n## {thresh_label} threshold\n")
        lines.append("| Variant | Findings/run | TP/run | FP/run | Precision | Flaws (union) |")
        lines.append("|---|---|---|---|---|---|")
        for variant in VARIANTS:
            a = all_results[variant]["thresholds"][thresh]
            lines.append(
                f"| {variant} | {a['findings_mean_std']} | {a['tp_mean_std']} | "
                f"{a['fp_mean_std']} | {a['precision_mean_std']} | {a['union_flaws_count']}/33 |"
            )

    lines.append(
        "\n## FP root-cause breakdown (ALL threshold, 3-run totals)\n"
    )
    lines.append(
        "Each FP is categorized by the quality of the finding description, "
        "independent of the LLM's verdict field:\n\n"
        "- **fabricated** — concrete description of an attack/behavior that "
        "does not match any of the 33 flaws (made-up or out-of-scope).\n"
        "- **hedged** — speculative language (suggests/may/appears/...) or "
        "declines to commit to a specific violation.\n"
        "- **setup-artifact** — test-infrastructure failure mistaken for a "
        "security behavior.\n"
        "- **wrong-classif** — concrete violation labeled under the wrong "
        "invariant axis.\n"
    )
    lines.append("| Variant | fabricated | hedged | setup-artifact | wrong-classif | Total FP |")
    lines.append("|---|---|---|---|---|---|")
    for variant in VARIANTS:
        a = all_results[variant]["thresholds"]["LOW"]
        b = a["fp_buckets_total"]
        total_fp = sum(b.values())
        lines.append(
            f"| {variant} | {b.get('fabricated', 0)} | {b.get('hedged', 0)} | "
            f"{b.get('setup-artifact', 0)} | {b.get('wrong-classif', 0)} | {total_fp} |"
        )

    lines.append("\n## FP root-cause breakdown at HIGH confidence (3-run totals)\n")
    lines.append(
        "HIGH-confidence FPs reveal the LLM's judgment-quality floor — it "
        "selected these itself as high-confidence.\n"
    )
    lines.append("| Variant | fabricated | hedged | setup-artifact | wrong-classif | Total FP @ HIGH |")
    lines.append("|---|---|---|---|---|---|")
    for variant in VARIANTS:
        a = all_results[variant]["thresholds"]["HIGH"]
        b = a["fp_buckets_total"]
        total_fp = sum(b.values())
        lines.append(
            f"| {variant} | {b.get('fabricated', 0)} | {b.get('hedged', 0)} | "
            f"{b.get('setup-artifact', 0)} | {b.get('wrong-classif', 0)} | {total_fp} |"
        )

    lines.append("\n## Flaws recovered by variant (union across 3 runs, ALL threshold)\n")
    for variant in VARIANTS:
        flaws = all_results[variant]["thresholds"]["LOW"]["union_flaws"]
        lines.append(f"- **{variant}** ({len(flaws)}/33): {', '.join(flaws)}")

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    print()
    print("Summary at ALL threshold:")
    for variant in VARIANTS:
        a = all_results[variant]["thresholds"]["LOW"]
        print(
            f"  {variant}: findings={a['findings_mean_std']} tp={a['tp_mean_std']} "
            f"prec={a['precision_mean_std']} flaws={a['union_flaws_count']}/33"
        )


if __name__ == "__main__":
    main()
