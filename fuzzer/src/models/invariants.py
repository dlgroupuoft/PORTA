"""Canonical invariant definitions for the VALENCE fuzzing framework.

This is the single source of truth for invariant IDs and descriptions.
All modules that need invariant metadata should import from here.
"""

INVARIANT_DEFINITIONS = {
    "I1": (
        "Proof Integrity: The broker must ensure authenticity checks are applied "
        "to the exact semantic proof under the intended verification policy. "
        "Oracle: SemanticContent(Verify(proof)) ≡ SemanticContent(Consume(proof))"
    ),
    "I2": (
        "Freshness & Anti-Replay: Credential artifacts must not be reusable beyond "
        "their intended lifetime. One-time artifacts must not be accepted more than once. "
        "Oracle: Accept(artifact_id, t) AND Δ > TTL → NOT Accept(artifact_id, t+Δ)"
    ),
    "I3": (
        "Flow Coherence: Multi-step authentication must be atomic, order-preserving, "
        "and bound to the correct session/client. No step skipping or cross-session splicing. "
        "Oracle: ValidAuth(trace) ⇒ trace ∈ L(FSM_protocol)"
    ),
    "I4": (
        "Principal Binding: Security-distinct upstream principals must not collapse "
        "into the same downstream subject. The broker must preserve identity boundaries. "
        "Oracle: SecurityDistinct(p1, p2) ⇒ Map(p1) ≠ Map(p2)"
    ),
    "I5": (
        "Authorization Binding: Effective permissions must not exceed "
        "UpstreamIntent(auth_context) ∩ BrokerPolicy(config). "
        "Oracle: EffectivePerms(session) ⊆ UpstreamIntent ∩ BrokerPolicy"
    ),
}
