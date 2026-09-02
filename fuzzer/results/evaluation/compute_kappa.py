#!/usr/bin/env python3
"""Compute Cohen's kappa for inter-rater agreement on pattern coding.

Two authors independently labeled each of the 33 findings with one of
8 code-level patterns. This script computes Cohen's kappa and outputs
the confusion matrix.
"""

# Author 1 labels (from finding_catalog.md)
# Author 2 labels (from finding_catalog_annotated.md)
# For disagreements where Author 2 left no alternative, we treat as same label
# (CD-5, CD-8, CD-9 had empty comments → Author 2 did not provide alternative)

LABELS = {
    # (finding_id, author1_label, author2_label)
    "ZT-1":  ("explicit-verification-disabled",    "explicit-verification-disabled"),
    "ZT-2":  ("explicit-verification-disabled",    "explicit-verification-disabled"),
    "ZT-3":  ("silent-skip-on-absent-field",       "silent-skip-on-absent-field"),
    "CD-1":  ("no-persistent-anti-replay-state",   "no-persistent-anti-replay-state"),
    "CD-2":  ("silent-skip-on-absent-field",       "silent-skip-on-absent-field"),
    "CD-3":  ("explicit-verification-disabled",    "explicit-verification-disabled"),
    "CD-4":  ("explicit-verification-disabled",    "explicit-verification-disabled"),
    "CD-5":  ("explicit-verification-disabled",    "explicit-verification-disabled"),  # no alt given
    "CD-6":  ("trust-bootstrap-reflexivity",       "trust-bootstrap-reflexivity"),
    "CD-7":  ("branch-coverage-gap",               "branch-coverage-gap"),
    "CD-8":  ("stale-configuration-snapshot",      "stale-configuration-snapshot"),  # no alt given
    "CD-9":  ("cross-namespace-identity-collapse", "cross-namespace-identity-collapse"),  # no alt given
    "DX-1":  ("silent-skip-on-absent-field",       "silent-skip-on-absent-field"),
    "DX-2":  ("no-persistent-anti-replay-state",   "no-persistent-anti-replay-state"),
    "DX-3":  ("silent-skip-on-absent-field",       "silent-skip-on-absent-field"),
    "DX-4":  ("stale-configuration-snapshot",      "stale-configuration-snapshot"),
    "DX-5":  ("stale-configuration-snapshot",      "stale-configuration-snapshot"),  # "not sure"
    "KC-1":  ("silent-skip-on-absent-field",       "silent-skip-on-absent-field"),
    "KC-3":  ("no-persistent-anti-replay-state",   "no-persistent-anti-replay-state"),
    "KC-4":  ("silent-skip-on-absent-field",       "silent-skip-on-absent-field"),
    "KC-5":  ("silent-skip-on-absent-field",       "silent-skip-on-absent-field"),
    "KC-6":  ("stale-configuration-snapshot",      "stale-configuration-snapshot"),
    "AK-1":  ("silent-skip-on-absent-field",       "explicit-verification-disabled"),  # DISAGREE
    "AK-3":  ("explicit-verification-disabled",    "explicit-verification-disabled"),
    "AK-5":  ("silent-skip-on-absent-field",       "explicit-verification-disabled"),  # DISAGREE
    "AK-6":  ("explicit-verification-disabled",    "silent-skip-on-absent-field"),     # DISAGREE
    "AK-7":  ("stale-configuration-snapshot",      "stale-configuration-snapshot"),
    "VT-5/6":("cross-namespace-identity-collapse", "cross-namespace-identity-collapse"),
    "LG-1":  ("non-state-predicate",              "non-state-predicate"),
    "LG-2":  ("cross-namespace-identity-collapse", "cross-namespace-identity-collapse"),
    "LG-3":  ("silent-skip-on-absent-field",       "silent-skip-on-absent-field"),
    "LG-5":  ("branch-coverage-gap",               "branch-coverage-gap"),
    "LG-6":  ("cross-namespace-identity-collapse", "cross-namespace-identity-collapse"),
}

CATEGORIES = sorted(set(
    l for pair in LABELS.values() for l in pair
))

def compute_kappa():
    n = len(LABELS)
    a1 = [v[0] for v in LABELS.values()]
    a2 = [v[1] for v in LABELS.values()]

    # Observed agreement
    agree = sum(1 for x, y in zip(a1, a2) if x == y)
    p_o = agree / n

    # Expected agreement (by chance)
    from collections import Counter
    c1 = Counter(a1)
    c2 = Counter(a2)
    p_e = sum((c1[cat] / n) * (c2[cat] / n) for cat in CATEGORIES)

    kappa = (p_o - p_e) / (1 - p_e) if p_e < 1 else 1.0

    return p_o, p_e, kappa, agree, n

def print_confusion_matrix():
    from collections import Counter
    matrix = Counter()
    a1 = [v[0] for v in LABELS.values()]
    a2 = [v[1] for v in LABELS.values()]
    for x, y in zip(a1, a2):
        matrix[(x, y)] += 1

    # Short names for display
    SHORT = {
        "silent-skip-on-absent-field": "Skip",
        "explicit-verification-disabled": "Disabled",
        "stale-configuration-snapshot": "Stale",
        "cross-namespace-identity-collapse": "Collapse",
        "no-persistent-anti-replay-state": "NoReplay",
        "branch-coverage-gap": "Branch",
        "trust-bootstrap-reflexivity": "Reflex",
        "non-state-predicate": "Pred",
    }

    cats = CATEGORIES
    print("\nConfusion matrix (Author 1 rows, Author 2 columns):\n")
    header = f"{'':12s} | " + " | ".join(f"{SHORT.get(c,'?'):>8s}" for c in cats) + " |"
    print(header)
    print("-" * len(header))
    for r in cats:
        row = f"{SHORT.get(r,'?'):12s} | "
        row += " | ".join(f"{matrix.get((r,c),0):>8d}" for c in cats)
        row += " |"
        print(row)

def print_disagreements():
    print("\nDisagreements (resolved by discussion):\n")
    print("| Finding | Author 1 | Author 2 | Resolution |")
    print("|---------|----------|----------|------------|")

    resolutions = {
        "AK-1": "silent-skip: WarningInfo sub-object silently ignored, not a config flag",
        "AK-5": "silent-skip: parse() skips Conditions element entirely when absent",
        "AK-6": "explicit-disabled: PyJWTError catch actively swallows ExpiredSignatureError",
    }

    SHORT = {
        "silent-skip-on-absent-field": "silent-skip",
        "explicit-verification-disabled": "explicit-disabled",
    }

    for fid, (a1, a2) in sorted(LABELS.items()):
        if a1 != a2:
            res = resolutions.get(fid, "resolved by discussion")
            print(f"| {fid} | {SHORT.get(a1,a1)} | {SHORT.get(a2,a2)} | {res} |")

if __name__ == "__main__":
    p_o, p_e, kappa, agree, n = compute_kappa()

    print(f"Inter-rater agreement on pattern coding (n={n})")
    print(f"  Agreed: {agree}/{n} ({p_o:.1%})")
    print(f"  Disagreed: {n-agree}/{n}")
    print(f"  p_observed = {p_o:.4f}")
    print(f"  p_expected = {p_e:.4f}")
    print(f"  Cohen's kappa = {kappa:.3f}")

    if kappa > 0.8:
        print(f"  Interpretation: almost perfect agreement")
    elif kappa > 0.6:
        print(f"  Interpretation: substantial agreement")
    elif kappa > 0.4:
        print(f"  Interpretation: moderate agreement")

    print_confusion_matrix()
    print_disagreements()
