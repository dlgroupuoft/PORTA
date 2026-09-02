#!/usr/bin/env python3
"""
Extract a comprehensive report from a VALENCE fuzzer round's results.

Usage:
    python3 scripts/extract_round_report.py <round_results_dir> [--output report.json]

Example:
    python3 scripts/extract_round_report.py results/round1
    python3 scripts/extract_round_report.py results/round1 --output results/round1_report.json
"""

import argparse
import glob
import json
import os
import sys
from pathlib import Path


def find_campaign_dir(experiment_dir: str) -> str | None:
    """Find the campaign directory containing summary.json inside an experiment dir."""
    matches = glob.glob(os.path.join(experiment_dir, "**/summary.json"), recursive=True)
    for m in matches:
        parent = os.path.dirname(m)
        # The campaign dir is the one with summary.json + sequences.json
        if os.path.exists(os.path.join(parent, "sequences.json")):
            return parent
    return None


def load_json(path: str):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def extract_experiment(exp_dir: str) -> dict:
    """Extract all data from a single experiment directory."""
    exp_name = os.path.basename(exp_dir)
    campaign_dir = find_campaign_dir(exp_dir)

    result = {
        "experiment": exp_name,
        "campaign_dir": campaign_dir,
        "has_data": campaign_dir is not None,
    }

    if not campaign_dir:
        result["error"] = "No campaign directory with summary.json found"
        return result

    # --- Summary ---
    summary = load_json(os.path.join(campaign_dir, "summary.json"))
    if summary:
        result["total_sequences_generated"] = summary.get("sequence_quality", {}).get("total_generated", summary.get("total_sequences", 0))
        result["total_sequences"] = summary.get("total_sequences", 0)

        by_status = summary.get("by_status", {})
        result["by_status"] = by_status
        completed = by_status.get("COMPLETED", 0)
        login_failed = by_status.get("LOGIN_FAILED", 0)
        total = result["total_sequences"]
        result["execution_success_count"] = completed
        result["execution_success_rate"] = round(completed / total, 4) if total else 0
        result["execution_rate_incl_login_fail"] = round((completed + login_failed) / total, 4) if total else 0

        # By invariant
        result["sequences_by_invariant"] = summary.get("by_invariant", {})

        # Sequence quality funnel
        sq = summary.get("sequence_quality", {})
        if sq:
            result["sequence_quality"] = {
                "generated": sq.get("total_generated", 0),
                "parseable": sq.get("level0_parseable", 0),
                "valid_structure": sq.get("level1_valid_structure", 0),
                "executable": sq.get("level2_executable", 0),
                "meaningful": sq.get("level3_meaningful", 0),
                "found_finding": sq.get("level4_finding", 0),
            }
            rates = sq.get("rates", {})
            if rates:
                result["sequence_quality"]["rates"] = {
                    "parse_rate": rates.get("parse_rate"),
                    "validity_rate": rates.get("validity_rate"),
                    "execution_rate": rates.get("execution_rate"),
                    "meaningful_rate": rates.get("meaningful_rate"),
                    "finding_rate": rates.get("finding_rate"),
                }

        # Findings summary
        result["total_findings"] = summary.get("total_findings", 0)
        result["unique_findings_count"] = summary.get("unique_findings", 0)
        result["duplicate_count"] = summary.get("duplicate_count", 0)
        result["findings_by_invariant"] = summary.get("findings_by_invariant", {})
        result["findings_by_confidence"] = summary.get("findings_by_confidence", {})
        result["findings_by_strategy"] = summary.get("findings_by_strategy", {})

        # Execution / event rates
        result["execution_rate_by_strategy"] = summary.get("execution_rate", {})
        result["event_success_rates"] = summary.get("event_success_rates", {})

    # --- Sequences ---
    sequences = load_json(os.path.join(campaign_dir, "sequences.json"))
    if sequences:
        seq_list = []
        for seq in sequences:
            seq_list.append({
                "sequence_id": seq.get("sequence_id"),
                "description": seq.get("description", ""),
                "primary_invariant": seq.get("primary_invariant"),
                "generation_strategy": seq.get("generation_strategy"),
                "status": seq.get("status"),
                "events_total": seq.get("events_total", 0),
                "events_succeeded": seq.get("events_succeeded", 0),
                "events_failed": seq.get("events_failed", 0),
                "used_examples": seq.get("used_examples"),
            })
        result["sequences"] = seq_list

        # Per-invariant execution breakdown
        inv_exec = {}
        for seq in sequences:
            inv = seq.get("primary_invariant", "unknown")
            if inv not in inv_exec:
                inv_exec[inv] = {"total": 0, "completed": 0, "login_failed": 0, "other": 0}
            inv_exec[inv]["total"] += 1
            status = seq.get("status", "UNKNOWN")
            if status == "COMPLETED":
                inv_exec[inv]["completed"] += 1
            elif status == "LOGIN_FAILED":
                inv_exec[inv]["login_failed"] += 1
            else:
                inv_exec[inv]["other"] += 1
        result["execution_by_invariant"] = inv_exec

    # --- Unique Findings ---
    unique_findings = load_json(os.path.join(campaign_dir, "unique_findings.json"))
    if unique_findings:
        findings_detail = []
        for f in unique_findings:
            findings_detail.append({
                "finding_id": f.get("finding_id"),
                "sequence_id": f.get("sequence_id"),
                "sequence_description": f.get("sequence_description", ""),
                "invariant": f.get("invariant"),
                "verdict_type": f.get("verdict_type"),
                "confidence": f.get("confidence"),
                "description": f.get("description"),
                "cve_analog": f.get("cve_analog"),
                "generation_strategy": f.get("generation_strategy"),
                "verdict_path": f.get("verdict_path"),
                "evidence": f.get("evidence"),
            })
        result["unique_findings"] = findings_detail

    # --- All Findings (for mapping findings back to sequences) ---
    all_findings = load_json(os.path.join(campaign_dir, "findings.json"))
    if all_findings:
        # Build mapping: sequence_id -> list of finding_ids
        seq_to_findings = {}
        for f in all_findings:
            sid = f.get("sequence_id", "")
            fid = f.get("finding_id", "")
            if sid not in seq_to_findings:
                seq_to_findings[sid] = []
            seq_to_findings[sid].append({
                "finding_id": fid,
                "invariant": f.get("invariant"),
                "verdict_type": f.get("verdict_type"),
                "confidence": f.get("confidence"),
                "verdict_path": f.get("verdict_path"),
            })
        result["findings_by_sequence"] = seq_to_findings

    return result


def build_overview(experiments: list[dict]) -> dict:
    """Build a cross-experiment overview table."""
    overview = []
    for exp in experiments:
        row = {
            "experiment": exp["experiment"],
            "total_sequences": exp.get("total_sequences", 0),
            "completed": exp.get("execution_success_count", 0),
            "exec_rate": exp.get("execution_success_rate", 0),
            "total_findings": exp.get("total_findings", 0),
            "unique_findings": exp.get("unique_findings_count", 0),
        }
        # Count by verdict type from unique findings
        verdict_counts = {}
        for f in exp.get("unique_findings", []):
            vt = f.get("verdict_type", "UNKNOWN")
            verdict_counts[vt] = verdict_counts.get(vt, 0) + 1
        row["unique_by_verdict"] = verdict_counts

        # Count by invariant from unique findings
        inv_counts = {}
        for f in exp.get("unique_findings", []):
            inv = f.get("invariant", "UNKNOWN")
            inv_counts[inv] = inv_counts.get(inv, 0) + 1
        row["unique_by_invariant"] = inv_counts

        overview.append(row)
    return overview


def format_text_report(report: dict) -> str:
    """Format the report as a human-readable text summary."""
    lines = []
    lines.append("=" * 80)
    lines.append(f"VALENCE Round Report — {report['round_dir']}")
    lines.append(f"Experiments found: {report['total_experiments']}")
    lines.append("=" * 80)

    # Overview table
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    header = f"{'Experiment':<45} {'Seq':>4} {'Done':>4} {'Exec%':>6} {'Finds':>5} {'Uniq':>4}"
    lines.append(header)
    lines.append("-" * len(header))
    for row in report["overview"]:
        exec_pct = f"{row['exec_rate']*100:.0f}%" if row['exec_rate'] else "0%"
        lines.append(
            f"{row['experiment']:<45} {row['total_sequences']:>4} {row['completed']:>4} "
            f"{exec_pct:>6} {row['total_findings']:>5} {row['unique_findings']:>4}"
        )

    # Unique findings summary per verdict type across all experiments
    lines.append("")
    lines.append("## All Unique Findings by Verdict Type")
    lines.append("")
    all_verdicts = {}
    for exp in report["experiments"]:
        for f in exp.get("unique_findings", []):
            vt = f.get("verdict_type", "UNKNOWN")
            all_verdicts[vt] = all_verdicts.get(vt, 0) + 1
    for vt, count in sorted(all_verdicts.items()):
        lines.append(f"  {vt}: {count}")

    # Per-experiment detail
    for exp in report["experiments"]:
        lines.append("")
        lines.append("=" * 80)
        lines.append(f"### {exp['experiment']}")
        lines.append("=" * 80)

        if not exp.get("has_data"):
            lines.append("  NO DATA — campaign not found")
            continue

        lines.append(f"  Sequences generated: {exp.get('total_sequences_generated', '?')}")
        lines.append(f"  Sequences executed:  {exp.get('total_sequences', 0)}")
        lines.append(f"  Completed:           {exp.get('execution_success_count', 0)}")
        lines.append(f"  Execution rate:      {exp.get('execution_success_rate', 0)*100:.1f}%")
        lines.append(f"  Status breakdown:    {json.dumps(exp.get('by_status', {}))}")

        # Quality funnel
        sq = exp.get("sequence_quality")
        if sq:
            lines.append("")
            lines.append("  Sequence Quality Funnel:")
            lines.append(f"    Generated → Parseable → Valid → Executable → Meaningful → Finding")
            lines.append(
                f"    {sq.get('generated',0):>9} → {sq.get('parseable',0):>9} → "
                f"{sq.get('valid_structure',0):>5} → {sq.get('executable',0):>10} → "
                f"{sq.get('meaningful',0):>10} → {sq.get('found_finding',0):>7}"
            )
            rates = sq.get("rates", {})
            if rates:
                lines.append(
                    f"    Rates: parse={rates.get('parse_rate','?'):.0%}  "
                    f"valid={rates.get('validity_rate','?'):.0%}  "
                    f"exec={rates.get('execution_rate','?'):.0%}  "
                    f"meaningful={rates.get('meaningful_rate','?'):.0%}  "
                    f"finding={rates.get('finding_rate','?'):.0%}"
                )

        # Per-invariant execution
        inv_exec = exp.get("execution_by_invariant", {})
        if inv_exec:
            lines.append("")
            lines.append("  Execution by Invariant:")
            for inv in sorted(inv_exec.keys()):
                s = inv_exec[inv]
                rate = f"{s['completed']/s['total']*100:.0f}%" if s["total"] else "N/A"
                lines.append(f"    {inv}: {s['completed']}/{s['total']} completed ({rate})")

        # Findings
        lines.append(f"")
        lines.append(f"  Total findings:  {exp.get('total_findings', 0)}")
        lines.append(f"  Unique findings: {exp.get('unique_findings_count', 0)}")
        lines.append(f"  Duplicates:      {exp.get('duplicate_count', 0)}")

        if exp.get("unique_findings"):
            lines.append("")
            lines.append("  Unique Findings Detail:")
            for i, f in enumerate(exp["unique_findings"], 1):
                lines.append(f"")
                lines.append(f"    [{i}] {f.get('finding_id', '?')}")
                lines.append(f"        Invariant:   {f.get('invariant')}")
                lines.append(f"        Verdict:     {f.get('verdict_type')} ({f.get('confidence')})")
                lines.append(f"        Strategy:    {f.get('generation_strategy')} / {f.get('verdict_path')}")
                lines.append(f"        Sequence:    {f.get('sequence_id')}")
                lines.append(f"        CVE analog:  {f.get('cve_analog', 'none')}")
                desc = f.get('description', '')
                # Wrap long descriptions
                if len(desc) > 100:
                    lines.append(f"        Description: {desc[:100]}")
                    for chunk_start in range(100, len(desc), 100):
                        lines.append(f"                     {desc[chunk_start:chunk_start+100]}")
                else:
                    lines.append(f"        Description: {desc}")
                evidence = f.get("evidence", {})
                if evidence:
                    lines.append(f"        Evidence:    {json.dumps(evidence, ensure_ascii=False)}")

        # Findings-to-sequence mapping
        f_by_seq = exp.get("findings_by_sequence", {})
        if f_by_seq:
            lines.append("")
            lines.append("  Findings per Sequence:")
            for sid, flist in sorted(f_by_seq.items()):
                finding_strs = [
                    f"{fi['finding_id'][:8]}({fi.get('invariant','?')}/{fi.get('verdict_type','?')}/{fi.get('confidence','?')})"
                    for fi in flist
                ]
                lines.append(f"    {sid}: {', '.join(finding_strs)}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Extract VALENCE round results into a report")
    parser.add_argument("round_dir", help="Path to the round results directory (e.g. results/round1)")
    parser.add_argument("--output", "-o", help="Output file path (default: <round_dir>/round_report.json)")
    parser.add_argument("--text", "-t", action="store_true", help="Also output a human-readable .txt report")
    args = parser.parse_args()

    round_dir = os.path.abspath(args.round_dir)
    if not os.path.isdir(round_dir):
        print(f"ERROR: {round_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    # Find all experiment directories (directories only, skip .log files)
    exp_dirs = sorted([
        os.path.join(round_dir, d)
        for d in os.listdir(round_dir)
        if os.path.isdir(os.path.join(round_dir, d))
    ])

    if not exp_dirs:
        print(f"ERROR: No experiment directories found in {round_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(exp_dirs)} experiments in {round_dir}")

    experiments = []
    for exp_dir in exp_dirs:
        print(f"  Extracting: {os.path.basename(exp_dir)} ...", end=" ", flush=True)
        exp_data = extract_experiment(exp_dir)
        experiments.append(exp_data)
        uf = exp_data.get("unique_findings_count", 0)
        ts = exp_data.get("total_sequences", 0)
        print(f"{ts} seq, {uf} unique findings")

    overview = build_overview(experiments)

    report = {
        "round_dir": round_dir,
        "total_experiments": len(experiments),
        "overview": overview,
        "experiments": experiments,
    }

    # Output JSON
    output_path = args.output or os.path.join(round_dir, "round_report.json")
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nJSON report written to: {output_path}")

    # Output text
    if args.text or not args.output:
        text_report = format_text_report(report)
        text_path = output_path.replace(".json", ".txt")
        with open(text_path, "w") as f:
            f.write(text_report)
        print(f"Text report written to: {text_path}")

    # Print overview to stdout
    print("\n" + "=" * 70)
    print("OVERVIEW")
    print("=" * 70)
    print(f"{'Experiment':<45} {'Seq':>4} {'Done':>4} {'Exec%':>6} {'Finds':>5} {'Uniq':>4}")
    print("-" * 70)
    for row in overview:
        exec_pct = f"{row['exec_rate']*100:.0f}%" if row['exec_rate'] else "0%"
        print(
            f"{row['experiment']:<45} {row['total_sequences']:>4} {row['completed']:>4} "
            f"{exec_pct:>6} {row['total_findings']:>5} {row['unique_findings']:>4}"
        )


if __name__ == "__main__":
    main()
