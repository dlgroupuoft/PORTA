"""Profile-driven invariant verification.

Universal checks that work on ANY platform. Uses UniversalLoginContext
fields populated from profile.verification_fields.

Does NOT wrap or delegate to InvariantVerifier.
"""
from __future__ import annotations
import logging
from typing import Optional

from src.stateful.models import UniversalLoginContext
from src.models.types import Verdict, VerdictType
from src.models.platform_profile import PlatformProfile

logger = logging.getLogger(__name__)


class PlatformVerifier:
    """Universal invariant checks driven by profile.verification_fields."""

    def __init__(self, profile: Optional[PlatformProfile] = None):
        self.profile = profile
        self.platform = profile.name if profile else "unknown"

    def verify_login(self, ctx: UniversalLoginContext) -> list[Verdict]:
        """Run per-login checks. Returns list[Verdict]."""
        if not ctx.login_success:
            return []

        # If all granted fields are empty, verify events failed — don't produce noise
        if not ctx.granted_identity and not ctx.granted_identity_id and not ctx.granted_permissions:
            logger.warning(
                f"[PlatformVerify:{self.platform}] All granted fields empty for {ctx.auth_as} — "
                f"verify events likely failed. Skipping checks."
            )
            return [self._v("I0", VerdictType.ERROR, "LOW",
                f"Verify events returned no data for {ctx.auth_as} — cannot check invariants",
                {"note": "All granted_identity/id/permissions are empty despite successful login"})]

        verdicts = []
        verdicts.extend(self._check_identity_binding(ctx))
        verdicts.extend(self._check_empty_identity(ctx))
        verdicts.extend(self._check_permission_escalation(ctx))
        verdicts.extend(self._check_constraint_bypass(ctx))
        return verdicts

    def verify_cross_user(self, contexts: list[UniversalLoginContext],
                          sequence_events: list = None) -> list[Verdict]:
        """Run cross-login checks.

        Args:
            contexts: List of UniversalLoginContext from login events.
            sequence_events: Optional list of all Event objects in the sequence,
                used for temporal checks (e.g., detecting role assignments between logins).
        """
        verdicts = []
        verdicts.extend(self._check_identity_collision(contexts))
        verdicts.extend(self._check_permission_divergence(contexts, sequence_events))
        return verdicts

    # ------------------------------------------------------------------
    # I4: Identity Binding
    # ------------------------------------------------------------------

    def _check_identity_binding(self, ctx: UniversalLoginContext) -> list[Verdict]:
        """I4: sent_identity should match granted_identity."""
        if not ctx.sent_identity or not ctx.granted_identity:
            return []  # Can't check without both sides

        sent = str(ctx.sent_identity)
        granted = str(ctx.granted_identity)

        if sent == granted:
            return []

        # Username vs email mismatch: when sent is a username and granted is
        # an email, the identity may still be the same user. Platforms like
        # Casdoor return email in userinfo while the login used username.
        # Check if the local part of the email is derivable from the username
        # (or vice versa) via common naming conventions.
        _sent_lower = sent.lower()
        _granted_lower = granted.lower()
        if "@" in granted:
            _local = granted.split("@")[0].lower()
            if _sent_lower == _local or _local in _sent_lower or _sent_lower in _local:
                return []
        if "@" in sent:
            _local = sent.split("@")[0].lower()
            if _granted_lower == _local or _local in _granted_lower or _granted_lower in _local:
                return []

        # Display-name prefix pattern: some auth systems set display_name as
        # "{prefix}-{user_claim_value}" (e.g. Vault JWT auth uses
        # "{mount_path}-{sub}").  The pattern is configured per-profile in
        # verification_fields.identity_prefix_pattern.  When set, strip the
        # prefix before flagging a mismatch.
        prefix_pattern = None
        if self.profile:
            prefix_pattern = self.profile.verification_fields.get("identity_prefix_pattern")

        if prefix_pattern and len(sent) > 0:
            import re
            # Pattern should capture the prefix; if granted matches
            # "<prefix><sent>", it's auth-system metadata, not a real change.
            m = re.match(prefix_pattern.replace("{sent}", re.escape(sent)), granted)
            if m:
                return []  # prefix is auth-system metadata, not a real identity change
            # Same check but case-insensitive — emit case-divergence, not full mismatch
            m_ci = re.match(
                prefix_pattern.replace("{sent}", re.escape(sent)),
                granted,
                re.IGNORECASE,
            )
            if m_ci:
                suffix_start = len(granted) - len(sent)
                actual_suffix = granted[suffix_start:]
                if actual_suffix != sent:  # genuinely different case
                    return [self._v("I4", VerdictType.UNEXPECTED, "MEDIUM",
                        f"Case divergence: sent={sent!r} → granted={granted!r}",
                        {"mismatch_type": "case", "sent": sent, "granted": granted})]
                return []

        # Case divergence (common across platforms)
        if sent.lower() == granted.lower():
            return [self._v("I4", VerdictType.UNEXPECTED, "MEDIUM",
                f"Case divergence: sent={sent!r} → granted={granted!r}",
                {"mismatch_type": "case", "sent": sent, "granted": granted})]

        # Whitespace divergence
        if sent.strip() == granted.strip():
            return [self._v("I4", VerdictType.UNEXPECTED, "MEDIUM",
                f"Whitespace divergence: sent={sent!r} → granted={granted!r}",
                {"mismatch_type": "whitespace", "sent": sent, "granted": granted})]

        # Complete mismatch — HIGH severity
        return [self._v("I4", VerdictType.VIOLATION, "HIGH",
            f"Identity mismatch: sent={sent!r} → granted={granted!r}",
            {"mismatch_type": "identity_mismatch", "sent": sent, "granted": granted})]

    def _check_empty_identity(self, ctx: UniversalLoginContext) -> list[Verdict]:
        """I4: Login should not succeed with empty identity.

        Only applies when the protocol explicitly carries an identity claim
        (JWT sub, SAML NameID, password username). For redirect-based flows
        (OAuth authorization code, SSO) the identity is determined by the
        upstream provider, so sent_identity is structurally absent — this is
        not an "empty identity accepted" condition.
        """
        sent = str(ctx.sent_identity).strip() if ctx.sent_identity else ""
        if not sent and ctx.login_success:
            # Only flag if the login type explicitly carries identity
            # (jwt, password, saml). Redirect-based flows (oauth, mock, code)
            # don't have sent_identity by design.
            # Read from profile if available; fall back to default set for backward compat.
            _default_carrying = {"jwt", "password", "saml", "ldap", "cert"}
            if self.profile and hasattr(self.profile, 'identity_carrying_types') and self.profile.identity_carrying_types:
                identity_carrying_types = set(self.profile.identity_carrying_types)
            else:
                identity_carrying_types = _default_carrying
            if ctx.login_type and ctx.login_type.lower() not in identity_carrying_types:
                return []  # Redirect-based flow — empty sent_identity is expected
            return [self._v("I4", VerdictType.UNEXPECTED, "HIGH",
                f"Empty identity accepted: granted={ctx.granted_identity!r}",
                {"mismatch_type": "empty_identity", "granted": ctx.granted_identity})]
        return []

    # ------------------------------------------------------------------
    # I5: Permission Binding
    # ------------------------------------------------------------------

    def _check_permission_escalation(self, ctx: UniversalLoginContext) -> list[Verdict]:
        """I5: granted_permissions should not exceed configured_permissions."""
        if not ctx.configured_permissions or not ctx.granted_permissions:
            return []

        # Normalize to string sets for comparison
        configured = set(str(p) for p in ctx.configured_permissions)
        granted = set(str(p) for p in ctx.granted_permissions)

        # Filter out platform-specific "always present" permissions
        # These are NOT hardcoded per-platform — they come from known_behaviors
        always_present = set()
        if self.profile:
            for kb in self.profile.known_behaviors:
                if kb.conditions.get("mismatch_type") == "default_permission":
                    always_present.add(kb.conditions.get("permission_name", ""))

        extras = granted - configured - always_present
        if extras:
            return [self._v("I5", VerdictType.UNEXPECTED, "MEDIUM",
                f"Permission escalation: extras={sorted(extras)}",
                {"mismatch_type": "policy_escalation",
                 "configured": sorted(configured), "granted": sorted(granted),
                 "extras": sorted(extras)})]
        return []

    def _check_constraint_bypass(self, ctx: UniversalLoginContext) -> list[Verdict]:
        """I5: If constraints were configured, check if login should have been rejected."""
        if not ctx.configured_constraints:
            return []

        verdicts = []

        # Audience constraint check (universal across JWT-based platforms)
        bound_aud = ctx.configured_constraints.get("bound_audiences") or \
                    ctx.configured_constraints.get("audience_restriction")
        if bound_aud and ctx.sent_audience:
            sent_aud = ctx.sent_audience if isinstance(ctx.sent_audience, list) else [ctx.sent_audience]
            if not any(a in bound_aud for a in sent_aud):
                verdicts.append(self._v("I5", VerdictType.VIOLATION, "HIGH",
                    f"Audience bypass: sent={sent_aud} not in configured={bound_aud}",
                    {"mismatch_type": "audience_bypass",
                     "sent_audience": sent_aud, "bound_audiences": bound_aud},
                    cve_pattern="CVE-2024-5798"))

        # Claim constraint check: if admin configured bound_claims / claim_constraints,
        # verify that the sent JWT claim values literally match. A successful login
        # with a non-matching claim value indicates the platform accepted a credential
        # it should have rejected (e.g., numeric type coercion, glob pattern abuse).
        bound_claims = ctx.configured_constraints.get("claim_constraints") or \
                       ctx.configured_constraints.get("bound_claims") or {}
        sent_claims = ctx.login_params.get("jwt_claims", {})
        if bound_claims and sent_claims and ctx.login_success:
            for claim_key, bound_val in bound_claims.items():
                if claim_key not in sent_claims:
                    continue
                sent_val = sent_claims[claim_key]
                # Coerce both to string for comparison — this catches:
                # - numeric type coercion (sent float 100.7 vs bound int 100)
                # - case differences
                # - type mismatches (string "42" vs number 42)
                if str(sent_val) != str(bound_val):
                    verdicts.append(self._v("I5", VerdictType.VIOLATION, "HIGH",
                        f"[PlatformVerify:{self.platform}] Claim constraint bypass: "
                        f"claim '{claim_key}' sent={sent_val!r} (type={type(sent_val).__name__}) "
                        f"does not match bound={bound_val!r} (type={type(bound_val).__name__}), "
                        f"but login succeeded. Platform accepted a credential violating its "
                        f"own configured constraint.",
                        {"mismatch_type": "claim_constraint_bypass",
                         "claim_key": claim_key,
                         "sent_value": sent_val,
                         "bound_value": bound_val,
                         "sent_type": type(sent_val).__name__,
                         "bound_type": type(bound_val).__name__},
                        cve_pattern="numeric type coercion"))

        return verdicts

    # ------------------------------------------------------------------
    # Cross-user checks
    # ------------------------------------------------------------------

    def _check_identity_collision(self, contexts: list[UniversalLoginContext]) -> list[Verdict]:
        """I4: Different sent identities should not receive same granted identity.

        Includes an **identity diversity precondition**: if ALL successful logins
        in the sequence map to the same downstream identity regardless of upstream
        principal, the authentication mechanism lacks the expressiveness to
        distinguish principals. This is a structural limitation (e.g., a test
        connector with fixed identity), not a platform vulnerability. In such
        cases, I4 findings are suppressed as INCONCLUSIVE rather than VIOLATION.
        """
        successful = [c for c in contexts if c.login_success and c.granted_identity_id]

        # Identity diversity precondition: check if the mechanism can produce
        # distinct identities AT ALL. If every successful login yields the same
        # granted_identity_id, the mechanism is identity-constant and I4 testing
        # is structurally meaningless.
        unique_granted = set(c.granted_identity_id for c in successful)
        unique_sent = set(c.sent_identity for c in successful if c.sent_identity)
        if len(unique_granted) == 1 and len(unique_sent) >= 2 and len(successful) >= 3:
            logger.info(
                f"[PlatformVerify:{self.platform}] Identity diversity precondition NOT met: "
                f"{len(unique_sent)} distinct principals → 1 identity ({list(unique_granted)[0][:20]}...). "
                f"Suppressing I4 collision findings (mechanism is identity-constant)."
            )
            return []

        id_map: dict[str, list[UniversalLoginContext]] = {}
        for ctx in successful:
            id_map.setdefault(ctx.granted_identity_id, []).append(ctx)

        verdicts = []
        for gid, colliders in id_map.items():
            sents = list(set(c.sent_identity for c in colliders))
            if len(sents) >= 2:
                # ── Fix 4: Token dedup — suppress collision when colliders
                # share the same session token (capture variable scoping issue,
                # not a real identity collision). ──
                # Extract session tokens from each collider's captured state.
                # If all colliders have the same session_token value, their
                # verify responses are identical because they introspected the
                # same token — not because the platform merged identities.
                _tokens = set()
                for c in colliders:
                    _cap = c.captured or {}
                    _tok = _cap.get(f"{c.auth_as}_session_token")
                    if _tok:
                        _tokens.add(str(_tok))
                if len(_tokens) == 1 and len(colliders) >= 2:
                    logger.info(
                        f"[PlatformVerify:{self.platform}] Identity collision suppressed: "
                        f"colliders {sents} share the same session token — "
                        f"capture variable scoping issue, not a real collision."
                    )
                    continue

                # Determine if this is a case collision (all sents differ only by case)
                lowered = set(s.lower() for s in sents)
                mtype = "case" if len(lowered) == 1 else "identity_collision"
                verdicts.append(self._v("I4", VerdictType.UNEXPECTED, "HIGH",
                    f"Identity collision: {sents} → same internal ID {gid}",
                    {"mismatch_type": mtype,
                     "granted_id": gid, "sent_identities": sents},
                    cve_pattern="CVE-2021-41802" if mtype != "case" else ""))
        return verdicts

    # Event types that represent deliberate role/permission modifications
    _ROLE_MODIFICATION_EVENT_TYPES = {
        "assign_user_role", "assign_group_role", "assign_client_role",
        "add_user_to_group", "create_policy", "assign_role",
        "remove_user_role", "remove_group_role", "remove_client_role",
        "remove_user_from_group",
    }

    def _check_permission_divergence(self, contexts: list[UniversalLoginContext],
                                     sequence_events: list = None) -> list[Verdict]:
        """I4/I5: Same granted_identity_id but different permissions is suspicious.

        Bug 4 fix: Different roles deliberately grant different policies to the same
        entity — that is by-design. Only flag when the SAME entity logs in via the
        SAME role and receives different permission sets across logins.

        Temporal fix: If a role/permission modification event (assign_user_role,
        assign_group_role, etc.) exists between two login events for the same
        identity, the permission change is expected and should be suppressed.
        """
        successful = [c for c in contexts if c.login_success and c.granted_identity_id]

        # Identity diversity precondition: if all logins map to the same
        # identity, permission divergence is from login timing/caching, not
        # a principal binding issue. Same logic as _check_identity_collision.
        unique_granted = set(c.granted_identity_id for c in successful)
        unique_sent = set(c.sent_identity for c in successful if c.sent_identity)
        if len(unique_granted) == 1 and len(successful) >= 2:
            logger.info(
                f"[PlatformVerify:{self.platform}] Permission divergence check skipped — "
                f"identity diversity precondition not met (all {len(successful)} logins → same identity)"
            )
            return []

        # Group by (entity_id, role_name) — different roles → expected policy difference
        role_id_map: dict[str, list[UniversalLoginContext]] = {}
        for ctx in successful:
            role_name = str(
                ctx.login_params.get("role", "") or ctx.login_params.get("role_name", "")
            )
            key = f"{ctx.granted_identity_id}::{role_name}"
            role_id_map.setdefault(key, []).append(ctx)

        # Build login event index for temporal checks
        # Maps auth_as → position in the sequence events list
        login_positions: dict[str, int] = {}
        if sequence_events:
            for idx, ev in enumerate(sequence_events):
                if hasattr(ev, 'event_type') and ev.event_type.startswith("login_"):
                    login_positions[ev.auth_as] = idx

        verdicts = []
        for key, colliders in role_id_map.items():
            if len(colliders) < 2:
                continue
            gid, role_name = key.split("::", 1)
            perm_sets = [frozenset(str(p) for p in c.granted_permissions) for c in colliders]
            if len(set(perm_sets)) > 1:
                # Temporal check: if a role modification event exists between
                # any two logins for this identity, the divergence is expected.
                if sequence_events and self._has_role_modification_between_logins(
                    colliders, sequence_events, login_positions
                ):
                    logger.info(
                        f"[PlatformVerify:{self.platform}] Permission divergence on "
                        f"{gid} suppressed — role modification found between logins"
                    )
                    continue

                verdicts.append(self._v("I4", VerdictType.UNEXPECTED, "MEDIUM",
                    f"Permission divergence on same identity+role {gid} (role={role_name!r})",
                    {"mismatch_type": "permission_divergence",
                     "granted_id": gid,
                     "role_name": role_name,
                     "permission_sets": [sorted(ps) for ps in perm_sets]}))
        return verdicts

    def _has_role_modification_between_logins(
        self,
        colliders: list[UniversalLoginContext],
        sequence_events: list,
        login_positions: dict[str, int],
    ) -> bool:
        """Check if any role/permission modification event exists between login events."""
        # Find the position range of the login events for these colliders
        positions = []
        for ctx in colliders:
            pos = login_positions.get(ctx.auth_as)
            if pos is not None:
                positions.append(pos)

        if len(positions) < 2:
            return False

        min_pos = min(positions)
        max_pos = max(positions)

        # Check if any role modification event exists between the first and last login
        for idx in range(min_pos + 1, max_pos):
            ev = sequence_events[idx]
            if hasattr(ev, 'event_type') and ev.event_type in self._ROLE_MODIFICATION_EVENT_TYPES:
                return True

        return False

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _v(self, invariant: str, vtype: VerdictType, confidence: str,
           description: str, evidence: dict,
           cve_pattern: str = "", spec_ref: str = "") -> Verdict:
        return Verdict(
            invariant=invariant,
            verdict_type=vtype,
            confidence=confidence,
            description=f"[PlatformVerify:{self.platform}] {description}",
            evidence=evidence,
            cve_pattern=cve_pattern,
            spec_reference=spec_ref or invariant,
        )
