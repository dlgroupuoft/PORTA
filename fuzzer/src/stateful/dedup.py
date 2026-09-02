"""Deduplication of generated sequences."""
import hashlib


def structural_hash(seq) -> str:
    """Hash based on event type sequence + invariant."""
    key = "|".join([e.event_type for e in seq.events]) + "|" + seq.primary_invariant
    return hashlib.md5(key.encode()).hexdigest()


def param_hash(seq) -> str:
    """Hash based on event types + key parameter names (not values)."""
    parts = []
    for e in seq.events:
        param_keys = sorted(e.params.keys())
        parts.append(f"{e.event_type}:{','.join(param_keys)}")
    key = "|".join(parts) + "|" + seq.primary_invariant
    return hashlib.md5(key.encode()).hexdigest()


def deduplicate(sequences: list) -> list:
    """Remove duplicate sequences using structural and param hashing.

    Guarantees that each invariant retains at least one representative
    sequence even if its structural/param hash collides with an earlier
    invariant's sequence (which should not happen when primary_invariant
    is set correctly, but guards against LLM misclassification).
    """
    seen_structural = set()
    seen_param = set()
    unique = []
    # Track which invariants have at least one representative
    invariants_seen = set()

    for seq in sequences:
        sh = structural_hash(seq)
        ph = param_hash(seq)
        inv = getattr(seq, 'primary_invariant', '') or ''

        if sh in seen_structural:
            # Still allow if this invariant has zero representatives
            if inv and inv not in invariants_seen:
                pass  # fall through to add
            else:
                continue
        if ph in seen_param:
            if inv and inv not in invariants_seen:
                pass  # fall through to add
            else:
                continue

        seen_structural.add(sh)
        seen_param.add(ph)
        unique.append(seq)
        if inv:
            invariants_seen.add(inv)

    return unique
