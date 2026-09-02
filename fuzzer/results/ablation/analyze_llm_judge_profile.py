#!/usr/bin/env python3
"""Analyze LLM-Judge-with-Profile ablation results.

Reads findings from llm_judge_profile_r1, r2, r3 and classifies each as
TP or FP against the 33 ground-truth findings from the paper.

Produces:
  - Per-confidence-threshold results (HIGH only, HIGH+MEDIUM, all)
  - Per-run and aggregate precision
  - Which of the 33 findings each threshold recovers
  - Comparison with original llm_judge (no profile) results
"""
import json
import glob
import os
import re
from collections import defaultdict
from pathlib import Path

FUZZER = Path(__file__).parent.parent.parent
ABLATION_DIR = FUZZER / "results" / "ablation"
OUTPUT_DIR = ABLATION_DIR / "analysis"
OUTPUT_DIR.mkdir(exist_ok=True)

# Ground truth: 33 findings mapped by platform+invariant+description keywords
GROUND_TRUTH = {
    # Specification violations (15)
    "ZT-1": {"platform": "zitadel", "inv": "I5", "keywords": ["aud", "audience", "jwt"], "proto": "oidc"},
    "ZT-2": {"platform": "zitadel", "inv": "I5", "keywords": ["audience", "saml", "audiencerestriction"], "proto": "saml"},
    "CD-1": {"platform": "casdoor", "inv": "I2", "keywords": ["replay", "assertion"], "proto": "saml"},
    "CD-2": {"platform": "casdoor", "inv": "I2", "keywords": ["notonorafter", "expir", "time", "temporal"], "proto": "saml"},
    "CD-3": {"platform": "casdoor", "inv": "I5", "keywords": ["audience", "audiencerestriction"], "proto": "saml"},
    "CD-4": {"platform": "casdoor", "inv": "I5", "keywords": ["token exchange", "cross-org", "cross-tenant", "organization"], "proto": "oidc"},
    "CD-6": {"platform": "casdoor", "inv": "I1", "keywords": ["cert", "certificate", "trust anchor", "saml"], "proto": "saml"},
    "CD-7": {"platform": "casdoor", "inv": "I3", "keywords": ["mfa", "multi-factor", "bypass", "federation"], "proto": "saml"},
    "DX-2": {"platform": "dex", "inv": "I2", "keywords": ["replay", "assertion"], "proto": "saml"},
    "KC-3": {"platform": "keycloak", "inv": "I2", "keywords": ["onetimeuse", "replay", "assertion"], "proto": "saml"},
    "AK-1": {"platform": "authentik", "inv": "I2", "keywords": ["notonorafter", "expir", "time", "temporal", "replay"], "proto": "saml"},
    "AK-3": {"platform": "authentik", "inv": "I1", "keywords": ["issuer", "iss", "verify_iss"], "proto": "oidc"},
    "AK-5": {"platform": "authentik", "inv": "I5", "keywords": ["audience", "conditions", "saml"], "proto": "saml"},
    "AK-6": {"platform": "authentik", "inv": "I2", "keywords": ["exp", "jwt", "temporal", "expir", "client assertion"], "proto": "oidc"},
    "LG-1": {"platform": "logto", "inv": "I2", "keywords": ["nonce", "bypass", "oidc"], "proto": "oidc"},
    # Under-specified flaws (18)
    "ZT-3": {"platform": "zitadel", "inv": "I2", "keywords": ["exp", "iat", "temporal", "expir", "freshness"], "proto": "oidc"},
    "CD-5": {"platform": "casdoor", "inv": "I2", "keywords": ["revok", "token exchange", "revocation"], "proto": "oidc"},
    "CD-8": {"platform": "casdoor", "inv": "I3", "keywords": ["unsolicited", "flow", "idp-initiated"], "proto": "saml"},
    "CD-9": {"platform": "casdoor", "inv": "I4", "keywords": ["email", "identity", "collision", "confusion", "binding"], "proto": "saml"},
    "DX-1": {"platform": "dex", "inv": "I5", "keywords": ["conditions", "audience", "optional"], "proto": "saml"},
    "DX-3": {"platform": "dex", "inv": "I2", "keywords": ["notonorafter", "expir", "time", "conditions"], "proto": "saml"},
    "DX-4": {"platform": "dex", "inv": "I3", "keywords": ["non-atomic", "connector", "stale", "config", "lifecycle"], "proto": "saml"},
    "DX-5": {"platform": "dex", "inv": "I3", "keywords": ["unsolicited", "inresponseto", "flow"], "proto": "saml"},
    "KC-1": {"platform": "keycloak", "inv": "I1", "keywords": ["alg=none", "alg", "request object", "unsigned"], "proto": "oidc"},
    "KC-4": {"platform": "keycloak", "inv": "I5", "keywords": ["conditions", "missing", "null", "absent"], "proto": "saml"},
    "KC-5": {"platform": "keycloak", "inv": "I5", "keywords": ["audience", "wrong", "saml"], "proto": "saml"},
    "KC-6": {"platform": "keycloak", "inv": "I3", "keywords": ["non-atomic", "config", "stale"], "proto": "saml"},
    "AK-7": {"platform": "authentik", "inv": "I3", "keywords": ["stale", "non-atomic", "config", "jwks"], "proto": "saml"},
    "VT-5/6": {"platform": "vault", "inv": "I4", "keywords": ["collision", "case", "email", "identity", "alias"], "proto": "oidc"},
    "LG-2": {"platform": "logto", "inv": "I4", "keywords": ["email", "auto-link", "linking", "unverified"], "proto": "oidc"},
    "LG-3": {"platform": "logto", "inv": "I5", "keywords": ["conditions", "saml", "missing", "absent"], "proto": "saml"},
    "LG-5": {"platform": "logto", "inv": "I3", "keywords": ["mfa", "bypass", "saml", "federation"], "proto": "saml"},
    "LG-6": {"platform": "logto", "inv": "I4", "keywords": ["collision", "case", "unicode", "whitespace", "identity"], "proto": "oidc"},
}

# Speculative language patterns (FP filter from original analysis)
SPECULATIVE_RE = re.compile(
    r'\bsuggests?\b|\bmay\b|\bappears?\b|\bcannot confirm\b|\bambiguous\b|'
    r'\bpotentially\b|\bunclear\b|\bmight\b|\bcould indicate\b|\bpossible\b',
    re.IGNORECASE
)

# Setup failure patterns
SETUP_FAIL_RE = re.compile(
    r'no session token|409 already exists|invalid_client|setup fail|'
    r'control.*fail|baseline.*fail|401 unauthorized|404 not found',
    re.IGNORECASE
)


def load_findings(run_name: str) -> list[dict]:
    """Load all unique findings from a run."""
    pattern = str(ABLATION_DIR / run_name / "**" / "unique_findings.json")
    files = sorted(glob.glob(pattern, recursive=True))
    all_findings = []
    for f in files:
        # Extract platform and protocol from path
        parts = Path(f).relative_to(ABLATION_DIR / run_name).parts
        platform = parts[0] if len(parts) > 0 else "?"
        protocol = parts[1] if len(parts) > 1 else "?"

        findings = json.load(open(f))
        for finding in findings:
            finding["_platform"] = platform
            finding["_protocol"] = protocol
            finding["_run"] = run_name
            all_findings.append(finding)
    return all_findings


def match_finding_to_ground_truth(finding: dict) -> str | None:
    """Try to match a finding to one of the 33 ground-truth flaws.
    Returns the flaw ID (e.g., 'ZT-1') or None."""
    platform = finding.get("_platform", "").lower()
    desc = finding.get("description", "").lower()
    seq_desc = finding.get("sequence_description", "").lower()
    inv = finding.get("invariant", "")
    full_text = f"{desc} {seq_desc}"

    best_match = None
    best_score = 0

    for flaw_id, gt in GROUND_TRUTH.items():
        if gt["platform"] != platform:
            continue

        score = 0
        # Invariant match
        if inv == gt["inv"]:
            score += 2

        # Keyword matches
        for kw in gt["keywords"]:
            if kw.lower() in full_text:
                score += 1

        if score > best_score and score >= 3:  # At least invariant match + 1 keyword
            best_score = score
            best_match = flaw_id

    return best_match


def is_speculative(finding: dict) -> bool:
    desc = finding.get("description", "")
    return bool(SPECULATIVE_RE.search(desc))


def is_setup_failure(finding: dict) -> bool:
    desc = finding.get("description", "")
    return bool(SETUP_FAIL_RE.search(desc))


def classify_at_threshold(findings: list[dict], min_confidence: str) -> dict:
    """Classify findings at a given confidence threshold.

    min_confidence: 'HIGH' = only HIGH, 'MEDIUM' = HIGH+MEDIUM, 'LOW' = all
    """
    conf_levels = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    threshold = conf_levels.get(min_confidence, 0)

    filtered = []
    for f in findings:
        conf = f.get("confidence", "LOW").upper()
        if conf_levels.get(conf, 0) >= threshold:
            filtered.append(f)

    tp_findings = []
    fp_findings = []
    matched_flaws = set()

    for f in filtered:
        verdict = f.get("verdict_type", f.get("verdict", "")).upper()

        # Must be VIOLATION (not UNEXPECTED)
        if verdict != "VIOLATION":
            fp_findings.append(f)
            continue

        # Filter speculative language
        if is_speculative(f):
            fp_findings.append(f)
            continue

        # Filter setup failures
        if is_setup_failure(f):
            fp_findings.append(f)
            continue

        # Try to match against ground truth
        match = match_finding_to_ground_truth(f)
        if match:
            tp_findings.append(f)
            matched_flaws.add(match)
        else:
            fp_findings.append(f)

    total = len(filtered)
    tp = len(tp_findings)
    fp = len(fp_findings)
    precision = tp / total if total > 0 else 0.0

    return {
        "threshold": min_confidence,
        "total_before_filter": len(findings),
        "total_at_threshold": total,
        "tp": tp,
        "fp": fp,
        "precision": precision,
        "matched_flaws": sorted(matched_flaws),
        "matched_count": len(matched_flaws),
    }


def analyze_run(run_name: str) -> dict:
    """Analyze a single run."""
    findings = load_findings(run_name)

    results = {"run": run_name, "total_findings": len(findings)}

    for threshold in ["HIGH", "MEDIUM", "LOW"]:
        results[threshold] = classify_at_threshold(findings, threshold)

    # Per-platform breakdown at MEDIUM threshold
    by_platform = defaultdict(list)
    for f in findings:
        by_platform[f["_platform"]].append(f)

    platform_results = {}
    for plat, pfindings in sorted(by_platform.items()):
        platform_results[plat] = classify_at_threshold(pfindings, "MEDIUM")
    results["by_platform"] = platform_results

    return results


def main():
    runs = ["llm_judge_profile_r1", "llm_judge_profile_r2", "llm_judge_profile_r3"]
    available_runs = [r for r in runs if (ABLATION_DIR / r).exists()]

    if not available_runs:
        print("No completed runs found yet.")
        return

    print(f"Analyzing {len(available_runs)} runs: {available_runs}")

    all_results = []
    all_matched_by_threshold = {"HIGH": set(), "MEDIUM": set(), "LOW": set()}

    for run_name in available_runs:
        print(f"\n{'='*60}")
        print(f"Run: {run_name}")
        print(f"{'='*60}")

        result = analyze_run(run_name)
        all_results.append(result)

        for threshold in ["HIGH", "MEDIUM", "LOW"]:
            r = result[threshold]
            all_matched_by_threshold[threshold].update(r["matched_flaws"])
            print(f"\n  [{threshold}] Total={r['total_at_threshold']}, "
                  f"TP={r['tp']}, FP={r['fp']}, "
                  f"Precision={r['precision']:.1%}, "
                  f"Flaws={r['matched_count']}/33")

    # Aggregate across runs
    print(f"\n{'='*60}")
    print("AGGREGATE (union across runs)")
    print(f"{'='*60}")

    aggregate = {}
    for threshold in ["HIGH", "MEDIUM", "LOW"]:
        runs_data = [r[threshold] for r in all_results]
        n = len(runs_data)

        avg_total = sum(r["total_at_threshold"] for r in runs_data) / n
        avg_tp = sum(r["tp"] for r in runs_data) / n
        avg_fp = sum(r["fp"] for r in runs_data) / n
        avg_precision = sum(r["precision"] for r in runs_data) / n
        union_flaws = sorted(all_matched_by_threshold[threshold])

        import statistics
        std_tp = statistics.stdev([r["tp"] for r in runs_data]) if n > 1 else 0
        std_total = statistics.stdev([r["total_at_threshold"] for r in runs_data]) if n > 1 else 0
        std_precision = statistics.stdev([r["precision"] for r in runs_data]) if n > 1 else 0

        aggregate[threshold] = {
            "avg_findings": f"{avg_total:.1f} +/- {std_total:.1f}",
            "avg_tp": f"{avg_tp:.1f} +/- {std_tp:.1f}",
            "avg_fp": f"{avg_fp:.1f}",
            "avg_precision": f"{avg_precision:.1%} +/- {std_precision:.1%}",
            "union_flaws": union_flaws,
            "union_count": f"{len(union_flaws)}/33",
            "per_run_tp": [r["tp"] for r in runs_data],
            "per_run_total": [r["total_at_threshold"] for r in runs_data],
            "per_run_precision": [f"{r['precision']:.1%}" for r in runs_data],
        }

        print(f"\n  [{threshold}] "
              f"Findings/run={avg_total:.1f}+/-{std_total:.1f}, "
              f"TP/run={avg_tp:.1f}+/-{std_tp:.1f}, "
              f"Precision={avg_precision:.1%}+/-{std_precision:.1%}, "
              f"Union flaws={len(union_flaws)}/33")
        print(f"    Flaws found: {', '.join(union_flaws)}")

        # Show which of the 33 are NOT found
        all_ids = set(GROUND_TRUTH.keys())
        missed = sorted(all_ids - set(union_flaws))
        print(f"    Missed ({len(missed)}): {', '.join(missed)}")

    # Comparison with original llm_judge
    print(f"\n{'='*60}")
    print("COMPARISON: llm_judge (no profile) vs llm_judge_profile")
    print(f"{'='*60}")
    print(f"  Original llm_judge: 245.3+/-22.7 findings/run, 19.7+/-4.7 TP, 8.1% precision, 13/33 flaws")
    med = aggregate.get("MEDIUM", {})
    print(f"  With profile (MEDIUM): {med.get('avg_findings','?')} findings/run, "
          f"{med.get('avg_tp','?')} TP, {med.get('avg_precision','?')} precision, "
          f"{med.get('union_count','?')} flaws")

    # Save results
    output = {
        "runs_analyzed": available_runs,
        "per_run": all_results,
        "aggregate": aggregate,
        "ground_truth_ids": sorted(GROUND_TRUTH.keys()),
    }

    out_path = OUTPUT_DIR / "llm_judge_profile_analysis.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nResults saved to {out_path}")

    # Also write a markdown summary
    md_path = OUTPUT_DIR / "LLM_judge_profile_TP_FP.md"
    with open(md_path, "w") as f:
        f.write("# LLM-as-Judge WITH Profile — TP/FP Analysis\n\n")
        f.write("## Configuration\n")
        f.write("- **eval-mode**: `llm_judge_profile`\n")
        f.write("- **Generation**: Full pipeline (invariants + examples)\n")
        f.write("- **Verdict**: LLM judge with sanitized platform profile context\n")
        f.write("- **Profile content**: API endpoints + constraints (invariant refs stripped)\n")
        f.write(f"- **Runs analyzed**: {len(available_runs)}\n\n")

        f.write("## Aggregate Results\n\n")
        f.write("| Threshold | Findings/run | TP/run | Precision | Flaws (union) |\n")
        f.write("|-----------|:---:|:---:|:---:|:---:|\n")
        for threshold in ["HIGH", "MEDIUM", "LOW"]:
            a = aggregate[threshold]
            f.write(f"| {threshold} | {a['avg_findings']} | {a['avg_tp']} | "
                    f"{a['avg_precision']} | {a['union_count']} |\n")

        f.write("\n## Per-Run Breakdown (MEDIUM threshold)\n\n")
        f.write("| Metric | Run 1 | Run 2 | Run 3 |\n")
        f.write("|--------|:---:|:---:|:---:|\n")
        med = aggregate["MEDIUM"]
        for metric, key in [("Findings", "per_run_total"), ("TP", "per_run_tp"), ("Precision", "per_run_precision")]:
            vals = med.get(key, [])
            row = " | ".join(str(v) for v in vals)
            f.write(f"| {metric} | {row} |\n")

        f.write(f"\n## Flaws Found (MEDIUM threshold, union of {len(available_runs)} runs)\n\n")
        med_flaws = aggregate["MEDIUM"]["union_flaws"]
        f.write(f"**{len(med_flaws)}/33 found:**\n\n")
        for fid in med_flaws:
            gt = GROUND_TRUTH[fid]
            f.write(f"- {fid}: {gt['platform']} {gt['inv']}\n")

        missed = sorted(set(GROUND_TRUTH.keys()) - set(med_flaws))
        f.write(f"\n**{len(missed)}/33 missed:**\n\n")
        for fid in missed:
            gt = GROUND_TRUTH[fid]
            f.write(f"- {fid}: {gt['platform']} {gt['inv']}\n")

        f.write("\n## Comparison with Original LLM-Judge (no profile)\n\n")
        f.write("| Metric | No Profile | With Profile (MEDIUM) |\n")
        f.write("|--------|:---:|:---:|\n")
        f.write(f"| Findings/run | 245.3 +/- 22.7 | {med.get('avg_findings','?')} |\n")
        f.write(f"| TP/run | 19.7 +/- 4.7 | {med.get('avg_tp','?')} |\n")
        f.write(f"| Precision | 8.1% | {med.get('avg_precision','?')} |\n")
        f.write(f"| Flaws found | 13/33 | {med.get('union_count','?')} |\n")

    print(f"Markdown saved to {md_path}")


if __name__ == "__main__":
    main()
