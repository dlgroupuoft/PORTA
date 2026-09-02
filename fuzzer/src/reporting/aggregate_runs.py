"""Aggregate results across multiple campaign runs for statistical reporting.

Usage:
    python -m src.reporting.aggregate_runs \
        --runs results/campaign_run1 results/campaign_run2 results/campaign_run3 \
        --output results/aggregated_report.json
"""

import argparse
import json
import os
import statistics
from pathlib import Path


def aggregate_runs(run_dirs: list[str]) -> dict:
    """Aggregate summary statistics across multiple runs.

    For each scalar metric, compute mean, std, min, max across runs.
    Also computes cross-run unique findings (deduplicated across ALL runs).
    """
    summaries = []
    for run_dir in run_dirs:
        summary_path = os.path.join(run_dir, "summary.json")
        if os.path.exists(summary_path):
            with open(summary_path) as f:
                summaries.append(json.load(f))

    if not summaries:
        return {"error": "No summaries found", "num_runs": 0}

    result: dict = {
        "num_runs": len(summaries),
        "metrics": {},
    }

    # Aggregate scalar metrics
    scalar_keys = [
        "total_sequences", "total_findings", "unique_findings", "duplicate_count"
    ]
    for key in scalar_keys:
        values = [s.get(key, 0) for s in summaries]
        result["metrics"][key] = {
            "mean": statistics.mean(values),
            "std": statistics.stdev(values) if len(values) > 1 else 0.0,
            "min": min(values),
            "max": max(values),
            "values": values,
        }

    # Aggregate findings by generation strategy
    for strategy in ["coverage", "attack"]:
        key = f"findings_{strategy}"
        values = [
            s.get("findings_by_strategy", {}).get(strategy, 0)
            for s in summaries
        ]
        result["metrics"][key] = {
            "mean": statistics.mean(values),
            "std": statistics.stdev(values) if len(values) > 1 else 0.0,
            "values": values,
        }

    # Aggregate findings by verdict path
    for path in ["oracle", "oracle_guided", "plain_llm", "assertion"]:
        key = f"findings_{path}"
        values = [
            s.get("findings_by_verdict_path", {}).get(path, 0)
            for s in summaries
        ]
        result["metrics"][key] = {
            "mean": statistics.mean(values),
            "std": statistics.stdev(values) if len(values) > 1 else 0.0,
            "values": values,
        }

    # Aggregate execution rates
    for strategy in ["coverage", "attack"]:
        key = f"exec_rate_{strategy}"
        values = [
            s.get("execution_rate", {}).get(strategy, 0.0)
            for s in summaries
        ]
        if any(v > 0 for v in values):
            result["metrics"][key] = {
                "mean": statistics.mean(values),
                "std": statistics.stdev(values) if len(values) > 1 else 0.0,
                "values": values,
            }

    # Aggregate event success rates
    for strategy in ["coverage", "attack"]:
        key = f"event_success_rate_{strategy}"
        values = [
            s.get("event_success_rates", {}).get(strategy, 0.0)
            for s in summaries
        ]
        if any(v > 0 for v in values):
            result["metrics"][key] = {
                "mean": statistics.mean(values),
                "std": statistics.stdev(values) if len(values) > 1 else 0.0,
                "values": values,
            }

    # Cross-run unique findings (deduplicated across ALL runs)
    all_findings = []
    for run_dir in run_dirs:
        findings_path = os.path.join(run_dir, "findings.json")
        if os.path.exists(findings_path):
            with open(findings_path) as f:
                all_findings.extend(json.load(f))

    seen_keys: set[str] = set()
    unique_cross_run = []
    for f in all_findings:
        # Dedup key mirrors FindingRecord.dedup_key() logic
        invariant = f.get("invariant", "")
        generation_strategy = f.get("generation_strategy", "")
        verdict_path = f.get("verdict_path", "")
        description = f.get("description", "")
        import hashlib
        desc_hash = hashlib.md5(description.lower().encode()).hexdigest()[:8]
        key = f"{invariant}:{generation_strategy}:{verdict_path}:{desc_hash}"
        if key not in seen_keys:
            seen_keys.add(key)
            unique_cross_run.append(f)

    result["cross_run_unique_findings"] = len(unique_cross_run)
    result["cross_run_total_findings"] = len(all_findings)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate VALENCE campaign results across multiple runs."
    )
    parser.add_argument(
        "--runs", nargs="+", required=True,
        help="Paths to campaign result directories (each must contain summary.json)"
    )
    parser.add_argument(
        "--output", default="results/aggregated_report.json",
        help="Output path for aggregated JSON report"
    )
    args = parser.parse_args()

    report = aggregate_runs(args.runs)

    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Aggregated {report['num_runs']} runs → {args.output}")
    for key, val in report.get("metrics", {}).items():
        mean = val.get("mean", 0)
        std = val.get("std", 0)
        print(f"  {key}: {mean:.2f} ± {std:.2f}")


if __name__ == "__main__":
    main()
