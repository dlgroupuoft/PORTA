#!/usr/bin/env python3
"""Generate per-ablation TP/FP markdown from manual_triage_2026/*.py.

Framing (per project convention): axes are confidence thresholds (HIGH,
HIGH+MEDIUM, ALL) — NOT LLM verdict_type (VIOLATION/UNEXPECTED). The Full
system also counts UNEXPECTED findings, so the apples-to-apples comparison is
by confidence only. The interesting question is why even HIGH-confidence
LLM-judge output has 2.5–5x worse precision than Full.

Writes three files under per_ablation/:
  - llm_judge_no_context.md
  - llm_judge_profile.md
  - llm_judge_invariant.md

Re-run whenever the triage dicts change.
"""
from __future__ import annotations
import importlib.util
import statistics
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).parent
TRIAGE_DIR = HERE / "manual_triage_2026"
OUT_DIR = HERE / "per_ablation"
OUT_DIR.mkdir(exist_ok=True)

CONF_RANK = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
ALL_FLAW_IDS = {
    "ZT-1", "ZT-2", "ZT-3", "CD-1", "CD-2", "CD-3", "CD-4", "CD-5",
    "CD-6", "CD-7", "CD-8", "CD-9", "DX-1", "DX-2", "DX-3", "DX-4",
    "DX-5", "KC-1", "KC-3", "KC-4", "KC-5", "KC-6", "AK-1", "AK-3",
    "AK-5", "AK-6", "AK-7", "LG-1", "LG-2", "LG-3", "LG-5", "LG-6",
    "VT-5/6",
}

VARIANTS = {
    "no_context": {
        "title": "LLM-Judge (no context)",
        "eval_mode": "llm_judge",
        "description": (
            "Pure LLM-as-judge with only the captured HTTP trace. No platform "
            "profile, no invariant taxonomy in the judge prompt. Generation "
            "pipeline matches Full (invariant + examples)."
        ),
        "runs": ["no_context_r1", "no_context_r2", "no_context_r3"],
        "run_dirs": ["llm_judge", "llm_judge_r2", "llm_judge_r3"],
    },
    "profile": {
        "title": "LLM-Judge + profile",
        "eval_mode": "llm_judge_profile",
        "description": (
            "LLM-as-judge with the sanitized platform profile (API endpoints, "
            "constraints; invariant references stripped) added to the judge "
            "prompt. Generation pipeline matches Full."
        ),
        "runs": ["profile_r1", "profile_r2", "profile_r3"],
        "run_dirs": [
            "llm_judge_profile_r1",
            "llm_judge_profile_r2",
            "llm_judge_profile_r3",
        ],
    },
    "invariant": {
        "title": "LLM-Judge + invariant",
        "eval_mode": "llm_judge_invariant",
        "description": (
            "LLM-as-judge with the I1–I5 invariant definitions added to the "
            "judge prompt. Generation pipeline matches Full."
        ),
        "runs": ["invariant_r1", "invariant_r2", "invariant_r3"],
        "run_dirs": [
            "llm_judge_invariant_r1",
            "llm_judge_invariant_r2",
            "llm_judge_invariant_r3",
        ],
    },
}


# FP-reason normalization: collapse agent-specific labels into 3 buckets.
# `hedged` = description is speculative, inconclusive, or LLM declined to
#            commit to a concrete security claim (merges `speculative` and
#            `unexpected-not-violation` — both are "LLM output lacks a
#            confident, concrete violation claim").
# `fabricated` = concrete description of an attack/behavior that doesn't
#                map to any of the 33 ground-truth flaws (`not-in-33`).
# `setup-artifact` = description is about control/baseline infrastructure
#                     failure rather than a security behavior (`setup-failure`).
# `wrong-classif` = LLM wrote a violation against the wrong invariant axis
#                   (rare; kept separate for visibility).
FP_REASON_MAP = {
    "speculative": "hedged",
    "unexpected-not-violation": "hedged",
    "not-in-33": "fabricated",
    "setup-failure": "setup-artifact",
    "wrong-classification": "wrong-classif",
}


def load_triage(run: str) -> dict:
    path = TRIAGE_DIR / f"{run}_triage.py"
    spec = importlib.util.spec_from_file_location(run, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.TRIAGE


def fp_bucket(v: dict) -> str:
    """Normalize FP reason to one of {hedged, fabricated, setup-artifact, wrong-classif}."""
    return FP_REASON_MAP.get(v["reason"], v["reason"])


def at_threshold(triage: dict, thresh: str):
    t = CONF_RANK[thresh]
    return [v for v in triage.values() if CONF_RANK.get(v["conf"], 0) >= t]


def stats(findings: list) -> dict:
    total = len(findings)
    tp = [v for v in findings if v["label"] == "TP"]
    fp = [v for v in findings if v["label"] == "FP"]
    fp_buckets = Counter(fp_bucket(v) for v in fp)
    flaws = {v["reason"] for v in tp}
    return {
        "total": total,
        "tp": len(tp),
        "fp": len(fp),
        "precision": len(tp) / total if total else 0.0,
        "fp_buckets": dict(fp_buckets),
        "flaws": sorted(flaws),
    }


def ms(xs: list[float]) -> str:
    return f"{statistics.mean(xs):.1f}±{statistics.stdev(xs):.1f}"


def pms(xs: list[float]) -> str:
    return f"{statistics.mean(xs) * 100:.1f}%±{statistics.stdev(xs) * 100:.1f}%"


def format_variant(variant_key: str) -> str:
    v = VARIANTS[variant_key]
    triages = {r: load_triage(r) for r in v["runs"]}

    # Per-run × per-threshold stats
    per_run: dict[str, dict[str, dict]] = {}
    for r in v["runs"]:
        per_run[r] = {th: stats(at_threshold(triages[r], th)) for th in ("HIGH", "MEDIUM", "LOW")}

    lines: list[str] = []
    lines.append(f"# {v['title']} — TP/FP Analysis\n")
    lines.append(f"- **eval-mode**: `{v['eval_mode']}`")
    lines.append(f"- **Generation pipeline**: invariant + CVE examples (identical to Full)")
    lines.append(f"- **Verdict layer**: single LLM call (gpt-5.2, temperature 0.01)")
    lines.append(f"- **Runs analyzed**: 3 — `{', '.join(v['run_dirs'])}`")
    lines.append(f"- **Triage**: per-finding manual triage (2026-04-16), see [../manual_triage_2026/](../manual_triage_2026/)\n")
    lines.append(v["description"] + "\n")

    # Per-run table, columns grouped by confidence threshold
    lines.append("## Per-run results by confidence threshold\n")
    lines.append(
        "Findings are filtered by the confidence field the LLM attached to each "
        "finding. *ALL* = all findings (same denominator as Full). *HIGH+MED* = "
        "exclude findings the LLM itself flagged as low-confidence. *HIGH* = "
        "only findings the LLM marked high-confidence (the most favorable "
        "reading for the LLM-judge).\n"
    )
    lines.append(
        "| Run | Findings@HIGH | TP@HIGH | Prec@HIGH | Findings@HIGH+MED | TP@HIGH+MED | Prec@HIGH+MED | Findings@ALL | TP@ALL | Prec@ALL |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in v["runs"]:
        h = per_run[r]["HIGH"]
        hm = per_run[r]["MEDIUM"]
        al = per_run[r]["LOW"]
        lines.append(
            f"| {r} | {h['total']} | {h['tp']} | {h['precision']*100:.1f}% "
            f"| {hm['total']} | {hm['tp']} | {hm['precision']*100:.1f}% "
            f"| {al['total']} | {al['tp']} | {al['precision']*100:.1f}% |"
        )

    def agg(th, key):
        return [per_run[r][th][key] for r in v["runs"]]

    lines.append(
        f"| **mean±std** | **{ms(agg('HIGH','total'))}** | **{ms(agg('HIGH','tp'))}** | **{pms(agg('HIGH','precision'))}** "
        f"| **{ms(agg('MEDIUM','total'))}** | **{ms(agg('MEDIUM','tp'))}** | **{pms(agg('MEDIUM','precision'))}** "
        f"| **{ms(agg('LOW','total'))}** | **{ms(agg('LOW','tp'))}** | **{pms(agg('LOW','precision'))}** |\n"
    )

    # Flaws
    union_high = set()
    union_med = set()
    union_low = set()
    for r in v["runs"]:
        union_high.update(per_run[r]["HIGH"]["flaws"])
        union_med.update(per_run[r]["MEDIUM"]["flaws"])
        union_low.update(per_run[r]["LOW"]["flaws"])

    lines.append("## Flaws recovered (union of 3 runs)\n")
    lines.append("| Threshold | Distinct flaws | IDs |")
    lines.append("|---|---|---|")
    lines.append(f"| HIGH      | {len(union_high)}/33 | {', '.join(sorted(union_high))} |")
    lines.append(f"| HIGH+MED  | {len(union_med)}/33 | {', '.join(sorted(union_med))} |")
    lines.append(f"| ALL       | {len(union_low)}/33 | {', '.join(sorted(union_low))} |\n")
    missed = sorted(ALL_FLAW_IDS - union_low)
    lines.append(f"**Never found across any run/threshold** ({len(missed)}/33): {', '.join(missed)}\n")

    # FP root-cause breakdown at each threshold (NO verdict_type axis)
    lines.append("## FP root-cause breakdown\n")
    lines.append(
        "Each FP is categorized by the *quality of the finding description*, "
        "independent of the LLM's verdict field. Categories:\n\n"
        "- **`fabricated`** — description commits to a concrete attack/behavior that does not match any of the 33 ground-truth flaws (either a made-up attack narrative or a real-but-out-of-scope platform behavior)\n"
        "- **`hedged`** — description uses speculative language (*suggests*, *may*, *appears*, *cannot confirm*) or declines to commit to a specific violation claim; the output is not a concrete assertion a reviewer can evaluate\n"
        "- **`setup-artifact`** — description is about control/baseline test-infrastructure failure (missing session token, `invalid_client`, 409 already-exists, etc.) rather than a security behavior\n"
        "- **`wrong-classif`** — concrete violation but labeled with the wrong invariant axis\n"
    )
    lines.append("| Threshold | fabricated | hedged | setup-artifact | wrong-classif | Total FP |")
    lines.append("|---|---|---|---|---|---|")
    for th, label in [("HIGH", "HIGH"), ("MEDIUM", "HIGH+MED"), ("LOW", "ALL")]:
        agg_b = Counter()
        for r in v["runs"]:
            for k, c in per_run[r][th]["fp_buckets"].items():
                agg_b[k] += c
        total_fp = sum(agg_b.values())
        lines.append(
            f"| {label} | {agg_b.get('fabricated', 0)} | {agg_b.get('hedged', 0)} | "
            f"{agg_b.get('setup-artifact', 0)} | {agg_b.get('wrong-classif', 0)} | {total_fp} |"
        )
    lines.append("")

    # Per-platform breakdown at HIGH threshold
    lines.append("## Per platform × protocol (HIGH threshold, 3-run aggregate)\n")
    pp_agg = defaultdict(lambda: {"total": 0, "tp": 0})
    for r in v["runs"]:
        for key, v_ in triages[r].items():
            if CONF_RANK.get(v_["conf"], 0) < CONF_RANK["HIGH"]:
                continue
            plat, proto, _ = key
            pp_agg[(plat, proto)]["total"] += 1
            if v_["label"] == "TP":
                pp_agg[(plat, proto)]["tp"] += 1
    lines.append("| platform / protocol | Findings | TP | FP | Precision |")
    lines.append("|---|---|---|---|---|")
    for (plat, proto), a in sorted(
        pp_agg.items(),
        key=lambda x: (x[1]["tp"] / x[1]["total"]) if x[1]["total"] else 0,
        reverse=True,
    ):
        t, tp_ = a["total"], a["tp"]
        p = tp_ / t * 100 if t else 0.0
        lines.append(f"| {plat} / {proto} | {t} | {tp_} | {t - tp_} | {p:.1f}% |")

    # HIGH-confidence FP examples by bucket
    lines.append("\n## Example FPs at HIGH confidence\n")
    lines.append(
        "These are findings the LLM itself marked HIGH-confidence yet are still false positives. "
        "They illustrate the judgment-quality floor: extra prompt context does not fix this class of error.\n"
    )
    for r in v["runs"]:
        high_fps = [
            (key, val) for key, val in triages[r].items()
            if val["label"] == "FP" and val["conf"] == "HIGH"
        ]
        if not high_fps:
            continue
        by_bucket: dict[str, list] = defaultdict(list)
        for key, val in high_fps:
            by_bucket[fp_bucket(val)].append((key, val))

        lines.append(f"\n### {r}\n")
        for bucket in ("fabricated", "hedged", "setup-artifact", "wrong-classif"):
            items = by_bucket.get(bucket, [])[:2]
            if not items:
                continue
            lines.append(f"**`{bucket}`** ({len(by_bucket[bucket])} total at HIGH, 2 shown):")
            for key, v_ in items:
                plat, proto, idx = key
                snippet = v_["desc_snippet"][:170]
                lines.append(
                    f"- `{plat}/{proto}` #{idx} (inv={v_['invariant']}): {snippet}"
                )
            lines.append("")

    lines.append("## Reproducibility\n")
    lines.append("- **Raw findings**: `FINDINGS_ROOT` in each triage file — one campaign per platform × protocol per run.")
    lines.append("- **Per-finding labels**: [`../manual_triage_2026/`](../manual_triage_2026/) (9 Python files, one per variant × run).")
    lines.append("- **Aggregator**: [`../aggregate_triage.py`](../aggregate_triage.py) regenerates aggregate_results from the triage files.")
    lines.append(
        f"- **Re-run raw campaigns**: see [`../README.md`](../README.md) §3 "
        f"(`bash scripts/run_ablation_{v['eval_mode']}.sh`)."
    )
    lines.append("- **Regenerate this doc**: `python3 ../scripts_gen_per_ablation.py`.")
    return "\n".join(lines) + "\n"


def main():
    for variant in VARIANTS:
        md = format_variant(variant)
        out = OUT_DIR / f"llm_judge_{variant}.md"
        out.write_text(md)
        print(f"Wrote {out}")


if __name__ == "__main__":
    main()
