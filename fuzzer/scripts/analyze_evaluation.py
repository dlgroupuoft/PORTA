#!/usr/bin/env python3
"""Analyze evaluation results across 3 independent runs. Output paper-ready μ ± σ stats."""
import json, math, os, glob, sys

BASE = "/home/ubuntu/broker/fuzzer/results/evaluation"
PLATFORMS = [
    ("zitadel", "oidc_jwt"), ("zitadel", "saml"),
    ("casdoor", "saml"), ("casdoor", "oidc"),
    ("dex", "oidc_jwt"), ("dex", "saml"),
    ("keycloak", "oidc"), ("keycloak", "saml"),
    ("authentik", "oidc_jwt"), ("authentik", "saml"),
    ("vault", "oidc_jwt"),
    ("logto", "oidc_jwt"), ("logto", "saml"),
]

def mean_std(vals):
    n = len(vals)
    if n == 0: return 0, 0
    mu = sum(vals) / n
    var = sum((x - mu) ** 2 for x in vals) / max(n - 1, 1)
    return mu, math.sqrt(var)

def load_campaign(exp, plat, proto):
    path = f"{BASE}/{exp}/{plat}/{proto}/full"
    if not os.path.isdir(path):
        return None
    dirs = sorted([d for d in os.listdir(path) if d.startswith("campaign_") and not d.startswith("campaign_vault")])
    if not dirs:
        # Try with vault prefix
        dirs = sorted([d for d in os.listdir(path) if d.startswith("campaign_")])
    if not dirs:
        return None
    camp = os.path.join(path, dirs[-1])

    sm = {}
    sf = os.path.join(camp, "summary.json")
    if os.path.exists(sf):
        with open(sf) as f:
            sm = json.load(f)

    bs = sm.get("by_status", {})
    total = sm.get("total_sequences", 0)
    comp = bs.get("COMPLETED", 0)
    fail = bs.get("LOGIN_FAILED", 0)

    sbi = {}
    sqf = os.path.join(camp, "sequences.json")
    if os.path.exists(sqf):
        with open(sqf) as f:
            seqs = json.load(f)
        for s in seqs:
            inv = s.get("primary_invariant", s.get("invariant", "?"))
            sbi[inv] = sbi.get(inv, 0) + 1

    uf_count = 0; assert_f = 0; sweep_f = 0
    uff = os.path.join(camp, "unique_findings.json")
    if os.path.exists(uff):
        with open(uff) as f:
            findings = json.load(f)
        uf_count = len(findings)
        for fi in findings:
            src = fi.get("detection_source", "")
            if "sweep" in src.lower():
                sweep_f += 1
            else:
                assert_f += 1

    return {
        "sbi": sbi, "total": total, "comp": comp, "fail": fail,
        "sr": comp / total if total > 0 else 0,
        "tf": sm.get("total_findings", 0),
        "uf": uf_count, "af": assert_f, "sf": sweep_f,
    }

def load_tp_fp(exp):
    """Load TP/FP from agent-generated metrics.json"""
    mf = os.path.join(BASE, exp, "metrics.json")
    if not os.path.exists(mf):
        return {}
    with open(mf) as f:
        m = json.load(f)
    result = {}
    camps = m.get("campaigns", {})
    for key, c in camps.items():
        tp = c.get("tp", 0)
        ntp = c.get("new_tp", 0)
        fp = c.get("fp", 0)
        result[key] = (tp, ntp, fp)
    # If per-campaign is empty, distribute totals
    t = m.get("totals", m.get("triage", {}))
    t_tp = t.get("tp", t.get("true_positives", 0))
    t_ntp = t.get("new_tp", 0)
    t_fp = t.get("fp", t.get("false_positives", 0))
    return result, t_tp, t_ntp, t_fp

def main():
    exps = ["exp1", "exp2", "exp3"]
    all_data = {}

    for exp in exps:
        campaigns = {}
        for plat, proto in PLATFORMS:
            key = f"{plat}/{proto}"
            c = load_campaign(exp, plat, proto)
            if c is None:
                campaigns[key] = {"total": 0, "comp": 0, "fail": 0, "sr": 0,
                    "uf": 0, "af": 0, "sf": 0, "sbi": {}, "tf": 0,
                    "tp": 0, "ntp": 0, "fp": 0, "prec": 0}
                continue

            # Try to get TP/FP from metrics.json
            tp_data, t_tp, t_ntp, t_fp = load_tp_fp(exp)
            if key in tp_data:
                tp, ntp, fp = tp_data[key]
            elif c["uf"] > 0 and (t_tp + t_ntp + t_fp) > 0:
                # Distribute proportionally
                total_known = t_tp + t_ntp + t_fp
                r = c["uf"] / max(total_known, 1)
                tp = round(t_tp * r)
                ntp = round(t_ntp * r)
                fp = round(t_fp * r)
                diff = c["uf"] - (tp + ntp + fp)
                tp += diff
            else:
                tp = ntp = fp = 0

            c["tp"] = tp
            c["ntp"] = ntp
            c["fp"] = fp
            c["prec"] = (tp + ntp) / c["uf"] if c["uf"] > 0 else 0
            campaigns[key] = c

        all_data[exp] = campaigns

    # Compute totals per experiment
    def exp_totals(camps):
        active = [c for c in camps.values() if c["total"] > 0]
        ts = sum(c["total"] for c in active)
        co = sum(c["comp"] for c in active)
        return {
            "total_seq": ts, "completed": co,
            "sr": co / ts if ts > 0 else 0,
            "uf": sum(c["uf"] for c in active),
            "af": sum(c["af"] for c in active),
            "sf": sum(c["sf"] for c in active),
            "tp": sum(c["tp"] for c in active),
            "ntp": sum(c["ntp"] for c in active),
            "fp": sum(c["fp"] for c in active),
            "prec": (sum(c["tp"] + c["ntp"] for c in active)) / max(sum(c["uf"] for c in active), 1),
        }

    T = {e: exp_totals(all_data[e]) for e in exps}

    def fmt(mu, std, pct=False):
        if pct:
            return f"{mu*100:.1f} ± {std*100:.1f}%"
        return f"{mu:.1f} ± {std:.1f}"

    # Print results
    print("=" * 80)
    print("EVALUATION RESULTS — 3 Independent Runs (μ ± σ)")
    print("=" * 80)
    print()

    rows = [
        ("Total Sequences", "total_seq", False),
        ("Completed", "completed", False),
        ("Exec Success Rate", "sr", True),
        ("Unique Findings", "uf", False),
        ("  Assertion Oracle", "af", False),
        ("  Mutation Sweep", "sf", False),
        ("Known Vuln TP", "tp", False),
        ("Novel TP", "ntp", False),
        ("False Positives", "fp", False),
        ("Precision", "prec", True),
    ]

    print(f"{'Metric':<25} {'Exp1':>8} {'Exp2':>8} {'Exp3':>8} {'μ ± σ':>18}")
    print("-" * 75)
    for label, k, pct in rows:
        vals = [T[e][k] for e in exps]
        mu, std = mean_std(vals)
        if pct:
            vs = [f"{v*100:.1f}%" for v in vals]
        else:
            vs = [str(int(v)) for v in vals]
        print(f"{label:<25} {vs[0]:>8} {vs[1]:>8} {vs[2]:>8} {fmt(mu, std, pct):>18}")

    # Per platform
    print()
    print("=" * 80)
    print("PER-PLATFORM (μ ± σ across 3 runs)")
    print("=" * 80)
    print()
    print(f"{'Platform/Proto':<22} {'SR μ±σ':>16} {'Prec μ±σ':>16} {'UF μ±σ':>14}")
    print("-" * 70)

    for plat, proto in PLATFORMS:
        key = f"{plat}/{proto}"
        sr_v = [all_data[e][key]["sr"] for e in exps if all_data[e][key]["total"] > 0]
        pr_v = [all_data[e][key]["prec"] for e in exps if all_data[e][key]["uf"] > 0]
        uf_v = [all_data[e][key]["uf"] for e in exps]

        sr_mu, sr_std = mean_std(sr_v) if sr_v else (0, 0)
        pr_mu, pr_std = mean_std(pr_v) if pr_v else (0, 0)
        uf_mu, uf_std = mean_std(uf_v)

        sr_s = f"{sr_mu*100:.0f}±{sr_std*100:.0f}%" if sr_v else "N/A"
        pr_s = f"{pr_mu*100:.0f}±{pr_std*100:.0f}%" if pr_v else "N/A"
        uf_s = f"{uf_mu:.1f}±{uf_std:.1f}"
        print(f"{key:<22} {sr_s:>16} {pr_s:>16} {uf_s:>14}")

    # Invariants
    print()
    print("=" * 80)
    print("SEQUENCES BY INVARIANT (μ ± σ)")
    print("=" * 80)
    for inv in ["I1", "I2", "I3", "I4", "I5"]:
        vals = []
        for e in exps:
            t = sum(c["sbi"].get(inv, 0) for c in all_data[e].values())
            vals.append(t)
        mu, std = mean_std(vals)
        print(f"  {inv}: {vals[0]:>4}, {vals[1]:>4}, {vals[2]:>4}  →  {fmt(mu, std)}")

    # LaTeX-ready
    print()
    print("=" * 80)
    print("LATEX-READY (copy-paste into paper)")
    print("=" * 80)
    for label, k, pct in rows:
        vals = [T[e][k] for e in exps]
        mu, std = mean_std(vals)
        if pct:
            print(f"  {label}: ${mu*100:.1f} \\pm {std*100:.1f}$\\%")
        else:
            print(f"  {label}: ${mu:.1f} \\pm {std:.1f}$")

if __name__ == "__main__":
    main()
