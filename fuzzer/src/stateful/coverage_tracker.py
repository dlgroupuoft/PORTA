"""Track which areas of the test space have been explored."""
import logging

logger = logging.getLogger(__name__)


class CoverageTracker:
    """Multi-dimensional test coverage tracking.

    Dimensions:
      - invariant: I1, I2, I3, I4, I5
      - attack_pattern: cross_user_collision, type_confusion, ...
      - user_config: single_user, cross_user, cross_role, cross_mount
      - temporal: static, mid_session_change, post_revoke
    """

    DIMENSIONS = {
        "invariant": ["I1", "I2", "I3", "I4", "I5"],
        "attack_pattern": [
            "cross_user_collision", "type_confusion", "empty_config_bypass",
            "audience_bypass", "claim_binding_bypass", "group_escalation",
            "replay", "flow_splice", "signature_manipulation", "trust_anchor",
        ],
        "user_config": ["single_user", "cross_user", "cross_role", "cross_mount"],
        "temporal": ["static", "mid_session_change", "post_revoke"],
    }

    def __init__(self):
        self.covered = set()

    def record_sequence(self, seq):
        """Analyze a sequence and mark which cells it covers."""
        inv = seq.primary_invariant or "I4"
        patterns = self._infer_attack_patterns(seq)
        configs = self._infer_user_config(seq)
        temporals = self._infer_temporal(seq)
        for p in patterns:
            for c in configs:
                for t in temporals:
                    self.covered.add((inv, p, c, t))

    def coverage_ratio(self) -> float:
        total = 1
        for dim in self.DIMENSIONS.values():
            total *= len(dim)
        return len(self.covered) / total if total > 0 else 0.0

    def uncovered_cells(self) -> list[tuple]:
        all_cells = set()
        for inv in self.DIMENSIONS["invariant"]:
            for p in self.DIMENSIONS["attack_pattern"]:
                for c in self.DIMENSIONS["user_config"]:
                    for t in self.DIMENSIONS["temporal"]:
                        all_cells.add((inv, p, c, t))
        return sorted(all_cells - self.covered)

    def suggest_focus(self) -> dict:
        """Suggest which invariant x pattern to explore next."""
        uncovered = self.uncovered_cells()
        by_inv = {}
        for cell in uncovered:
            by_inv.setdefault(cell[0], []).append(cell)
        if not by_inv:
            return {"message": "Full coverage achieved"}
        focus_inv = max(by_inv, key=lambda k: len(by_inv[k]))
        return {
            "focus_invariant": focus_inv,
            "uncovered_count": {k: len(v) for k, v in by_inv.items()},
            "total_coverage": f"{self.coverage_ratio():.1%}",
            "suggested_patterns": list(set(c[1] for c in by_inv[focus_inv][:5])),
        }

    def get_gap_descriptions(self, limit: int = 10) -> list[str]:
        """Get human-readable descriptions of uncovered cells for LLM prompts."""
        gaps = self.uncovered_cells()[:limit]
        return [
            f"{inv} × {pattern} × {config} × {temporal}"
            for inv, pattern, config, temporal in gaps
        ]

    def _infer_attack_patterns(self, seq) -> list[str]:
        """Heuristic inference from sequence description and events."""
        desc = (seq.description + " " + seq.invariant_hypothesis).lower()
        patterns = []

        pattern_keywords = {
            "cross_user_collision": ["collision", "same entity", "same identity", "different sub"],
            "type_confusion": ["type", "string vs", "array vs", "coercion", "confusion"],
            "empty_config_bypass": ["empty", "missing", "no constraints", "skip"],
            "audience_bypass": ["audience", "aud", "bound_audiences"],
            "claim_binding_bypass": ["bound_claims", "claim constraint"],
            "group_escalation": ["group", "escalat", "privilege"],
            "replay": ["replay", "reuse", "same token", "jti"],
            "flow_splice": ["redirect", "state", "pkce", "code injection"],
            "signature_manipulation": ["sign", "alg", "key", "kid", "none"],
            "trust_anchor": ["issuer", "jwks", "trust", "anchor"],
        }

        for pattern, keywords in pattern_keywords.items():
            if any(kw in desc for kw in keywords):
                patterns.append(pattern)

        return patterns or ["empty_config_bypass"]

    def _infer_user_config(self, seq) -> list[str]:
        """Infer user configuration from events."""
        login_events = [e for e in seq.events if e.event_type in ("login_jwt", "login_with_jwt")]
        auth_users = set(e.auth_as for e in login_events)

        if len(auth_users) >= 2:
            return ["cross_user"]

        # Check for role/mount diversity
        roles = set()
        mounts = set()
        for e in login_events:
            if "role" in e.params:
                roles.add(e.params["role"])
            if "mount" in e.params:
                mounts.add(e.params["mount"])

        if len(mounts) >= 2:
            return ["cross_mount"]
        if len(roles) >= 2:
            return ["cross_role"]

        return ["single_user"]

    def _infer_temporal(self, seq) -> list[str]:
        """Infer temporal pattern from events."""
        event_types = [e.event_type for e in seq.events]
        desc = seq.description.lower()

        if any("revoke" in et for et in event_types) or "revoke" in desc:
            return ["post_revoke"]
        if any("modify" in et for et in event_types) or "tighten" in desc or "change" in desc:
            return ["mid_session_change"]
        return ["static"]
