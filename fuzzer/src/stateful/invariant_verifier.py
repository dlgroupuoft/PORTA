# DEAD CODE — kept temporarily until we verify safe to delete after tests pass.
"""Deterministic invariant verification layer for stateful fuzzing.

Runs automatically after every login event. Compares what JWT claims were SENT
with what Vault GRANTED, checking against formal invariants I1-I5.
No LLM involved — pure comparison logic.
"""
from __future__ import annotations

import logging
from typing import Any

from src.stateful.models import LoginContext
from src.models.types import Verdict, VerdictType

logger = logging.getLogger(__name__)


class InvariantVerifier:
    """Deterministic checker for JWT→Vault invariants.

    Every public method returns list[Verdict]. Empty list means no findings.
    All verdict descriptions are prefixed with [AutoVerify].
    """

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def verify_login(self, ctx: LoginContext) -> list[Verdict]:
        """Run per-login checks (I4 + I5 + I2)."""
        verdicts: list[Verdict] = []

        if not ctx.login_success:
            return verdicts  # Nothing to check for failed logins

        verdicts.extend(self._check_sub_alias_binding(ctx))
        verdicts.extend(self._check_empty_sub(ctx))
        verdicts.extend(self._check_metadata_username(ctx))
        verdicts.extend(self._check_policy_escalation(ctx))
        verdicts.extend(self._check_identity_policy_source(ctx))
        verdicts.extend(self._check_audience_bypass(ctx))
        verdicts.extend(self._check_no_audience_binding(ctx))
        verdicts.extend(self._check_bound_claims_bypass(ctx))
        verdicts.extend(self._check_num_uses(ctx))

        return verdicts

    def verify_cross_user(self, contexts: list[LoginContext]) -> list[Verdict]:
        """Run cross-login checks (I4 entity collision)."""
        verdicts: list[Verdict] = []

        # Only consider successful logins with an entity_id
        successful = [c for c in contexts if c.login_success and c.granted_entity_id]

        # Group by entity_id
        entity_map: dict[str, list[LoginContext]] = {}
        for ctx in successful:
            entity_map.setdefault(ctx.granted_entity_id, []).append(ctx)

        for entity_id, colliders in entity_map.items():
            if len(colliders) < 2:
                continue

            # Find distinct sub values
            subs = [self._get_sub(c) for c in colliders]
            if len(set(subs)) < 2:
                continue  # Same sub — not a collision

            # Collision detected
            verdicts.append(Verdict(
                invariant="I4",
                verdict_type=VerdictType.UNEXPECTED,
                confidence="HIGH",
                description=(
                    f"[AutoVerify] Entity collision: different principals share entity_id={entity_id}. "
                    f"Principals: {subs}"
                ),
                evidence={
                    "mismatch_type": "entity_collision",
                    "entity_id": entity_id,
                    "principals": subs,
                    "auth_as_list": [c.auth_as for c in colliders],
                },
                spec_reference="I4",
                cve_pattern="CVE-2021-41802",
                requires_manual_review=True,
            ))

            # Check if they also got different policies (escalation via merge)
            policy_sets = [frozenset(c.granted_policies) for c in colliders]
            if len(set(policy_sets)) > 1:
                verdicts.append(Verdict(
                    invariant="I4",
                    verdict_type=VerdictType.UNEXPECTED,
                    confidence="HIGH",
                    description=(
                        f"[AutoVerify] Policy divergence across colliding principals on entity_id={entity_id}. "
                        f"Principals {subs} received different policy sets."
                    ),
                    evidence={
                        "mismatch_type": "collision_policy_divergence",
                        "entity_id": entity_id,
                        "principals": subs,
                        "policy_sets": [list(ps) for ps in policy_sets],
                    },
                    spec_reference="I4",
                    cve_pattern="CVE-2021-41802",
                    requires_manual_review=True,
                ))

        return verdicts

    # -----------------------------------------------------------------------
    # Per-login checks
    # -----------------------------------------------------------------------

    def _check_sub_alias_binding(self, ctx: LoginContext) -> list[Verdict]:
        """I4: JWT user_claim value must exactly match entity alias name."""
        verdicts: list[Verdict] = []
        user_claim_field = ctx.role_config.get("user_claim", "sub")
        sent_identity = ctx.jwt_claims.get(user_claim_field)

        if sent_identity is None:
            return verdicts

        for alias in ctx.entity_aliases:
            alias_name = alias.get("name", "") if isinstance(alias, dict) else str(alias)

            # Type coercion: sent non-string but str() matches alias — check FIRST
            # before the string-based exact match swallows it
            if not isinstance(sent_identity, str) and str(sent_identity) == alias_name:
                verdicts.append(self._make_verdict(
                    invariant="I4",
                    verdict_type=VerdictType.UNEXPECTED,
                    description=(
                        f"[AutoVerify] Type coercion in identity binding: "
                        f"JWT {user_claim_field}={sent_identity!r} ({type(sent_identity).__name__}) "
                        f"coerced to string alias_name={alias_name!r}"
                    ),
                    evidence={
                        "mismatch_type": "type_coercion",
                        "sent": sent_identity,
                        "sent_type": type(sent_identity).__name__,
                        "alias_name": alias_name,
                        "user_claim_field": user_claim_field,
                    },
                    cve_pattern="CVE-2024-5798",
                ))
                continue

            # Exact match (string) — OK
            if alias_name == str(sent_identity):
                continue

            # Whitespace divergence
            if alias_name.strip() == str(sent_identity).strip() and alias_name != str(sent_identity):
                verdicts.append(self._make_verdict(
                    invariant="I4",
                    verdict_type=VerdictType.UNEXPECTED,
                    description=(
                        f"[AutoVerify] Whitespace divergence in identity binding: "
                        f"JWT {user_claim_field}={sent_identity!r} but alias_name={alias_name!r}"
                    ),
                    evidence={
                        "mismatch_type": "whitespace_divergence",
                        "sent": str(sent_identity),
                        "alias_name": alias_name,
                        "user_claim_field": user_claim_field,
                    },
                    cve_pattern="CVE-2021-41802",
                ))

            # Case divergence
            elif alias_name.lower() == str(sent_identity).lower() and alias_name != str(sent_identity):
                verdicts.append(self._make_verdict(
                    invariant="I4",
                    verdict_type=VerdictType.UNEXPECTED,
                    description=(
                        f"[AutoVerify] Case divergence in identity binding: "
                        f"JWT {user_claim_field}={sent_identity!r} but alias_name={alias_name!r}"
                    ),
                    evidence={
                        "mismatch_type": "case_divergence",
                        "sent": str(sent_identity),
                        "alias_name": alias_name,
                        "user_claim_field": user_claim_field,
                    },
                    cve_pattern="CVE-2024-5798",
                ))

            # Complete mismatch
            elif alias_name and str(sent_identity) not in alias_name:
                verdicts.append(self._make_verdict(
                    invariant="I4",
                    verdict_type=VerdictType.UNEXPECTED,
                    description=(
                        f"[AutoVerify] Complete mismatch in identity binding: "
                        f"JWT {user_claim_field}={sent_identity!r} but alias_name={alias_name!r}"
                    ),
                    evidence={
                        "mismatch_type": "complete_mismatch",
                        "sent": str(sent_identity),
                        "alias_name": alias_name,
                        "user_claim_field": user_claim_field,
                    },
                    cve_pattern="CVE-2021-41802",
                ))

        return verdicts

    def _check_empty_sub(self, ctx: LoginContext) -> list[Verdict]:
        """I4: Empty or None sub should not result in successful login."""
        user_claim_field = ctx.role_config.get("user_claim", "sub")
        sub = ctx.jwt_claims.get(user_claim_field)

        if sub is None or str(sub).strip() == "":
            return [self._make_verdict(
                invariant="I4",
                verdict_type=VerdictType.UNEXPECTED,
                description=(
                    f"[AutoVerify] Empty identity accepted: JWT {user_claim_field}={sub!r} "
                    f"resulted in successful login (entity_id={ctx.granted_entity_id!r})"
                ),
                evidence={
                    "mismatch_type": "empty_identity",
                    "user_claim_field": user_claim_field,
                    "sub_value": sub,
                    "granted_entity_id": ctx.granted_entity_id,
                },
                cve_pattern="CVE-2021-41802",
            )]
        return []

    def _check_metadata_username(self, ctx: LoginContext) -> list[Verdict]:
        """I4: auth.metadata.username should match JWT user_claim value."""
        user_claim_field = ctx.role_config.get("user_claim", "sub")
        sent_identity = ctx.jwt_claims.get(user_claim_field)
        if sent_identity is None:
            return []

        # granted_metadata comes from auth.metadata on the login response
        username_in_meta = ctx.granted_metadata.get("username")
        if username_in_meta is None:
            return []

        if str(username_in_meta) != str(sent_identity):
            return [self._make_verdict(
                invariant="I4",
                verdict_type=VerdictType.UNEXPECTED,
                description=(
                    f"[AutoVerify] Metadata username divergence: "
                    f"JWT {user_claim_field}={sent_identity!r} but auth.metadata.username={username_in_meta!r}"
                ),
                evidence={
                    "mismatch_type": "metadata_username_divergence",
                    "sent": str(sent_identity),
                    "metadata_username": str(username_in_meta),
                    "user_claim_field": user_claim_field,
                },
            )]
        return []

    def _check_policy_escalation(self, ctx: LoginContext) -> list[Verdict]:
        """I5: Granted policies (minus identity_policies) must not exceed role's token_policies."""
        role_token_policies = set(ctx.role_config.get("token_policies", []))
        role_token_policies.add("default")  # Vault always adds default

        # identity_policies come from entity/group membership, not the role
        identity_policy_set = set(ctx.identity_policies or [])
        expected = role_token_policies | identity_policy_set

        granted_set = set(ctx.granted_policies or [])
        unexpected_extras = granted_set - expected

        if unexpected_extras:
            return [self._make_verdict(
                invariant="I5",
                verdict_type=VerdictType.UNEXPECTED,
                description=(
                    f"[AutoVerify] Policy escalation detected: granted policies contain extras "
                    f"beyond role config. Unexpected: {sorted(unexpected_extras)}"
                ),
                evidence={
                    "mismatch_type": "policy_escalation",
                    "role_token_policies": sorted(role_token_policies),
                    "identity_policies": sorted(identity_policy_set),
                    "granted_policies": sorted(granted_set),
                    "unexpected_policies": sorted(unexpected_extras),
                },
                cve_pattern="CVE-2024-7594",
            )]
        return []

    def _check_identity_policy_source(self, ctx: LoginContext) -> list[Verdict]:
        """I5: Identity policies without group membership is suspicious."""
        identity_policies = ctx.identity_policies or []
        group_ids = ctx.group_ids or []
        entity_policies = ctx.entity_policies or []

        # Identity policies can come from groups OR directly from entity policies
        if identity_policies and not group_ids and not entity_policies:
            return [self._make_verdict(
                invariant="I5",
                verdict_type=VerdictType.UNEXPECTED,
                description=(
                    f"[AutoVerify] Orphan identity policies: token has identity_policies={identity_policies} "
                    f"but entity has no group_ids and no entity_policies — unexpected policy source"
                ),
                evidence={
                    "mismatch_type": "orphan_identity_policies",
                    "identity_policies": identity_policies,
                    "group_ids": group_ids,
                    "entity_policies": entity_policies,
                },
            )]
        return []

    def _check_audience_bypass(self, ctx: LoginContext) -> list[Verdict]:
        """I5: If bound_audiences is set, JWT aud must match — or it's a bypass."""
        bound_audiences = ctx.role_config.get("bound_audiences", [])
        if not bound_audiences:
            return []

        jwt_aud = ctx.jwt_claims.get("aud")
        if jwt_aud is None:
            return []

        # aud can be a string or list
        if isinstance(jwt_aud, str):
            jwt_aud_list = [jwt_aud]
        else:
            jwt_aud_list = list(jwt_aud)

        # Any intersection = satisfied
        if any(a in bound_audiences for a in jwt_aud_list):
            return []

        return [self._make_verdict(
            invariant="I5",
            verdict_type=VerdictType.VIOLATION,
            description=(
                f"[AutoVerify] Audience bypass: login succeeded but JWT aud={jwt_aud!r} "
                f"does not match bound_audiences={bound_audiences!r}"
            ),
            evidence={
                "mismatch_type": "audience_bypass",
                "jwt_aud": jwt_aud,
                "bound_audiences": bound_audiences,
            },
            cve_pattern="CVE-2024-7594",
        )]

    def _check_no_audience_binding(self, ctx: LoginContext) -> list[Verdict]:
        """I5: Missing bound_audiences is a security gap (UNEXPECTED, not VIOLATION)."""
        bound_audiences = ctx.role_config.get("bound_audiences", [])
        if not bound_audiences:
            return [self._make_verdict(
                invariant="I5",
                verdict_type=VerdictType.UNEXPECTED,
                description=(
                    f"[AutoVerify] No audience binding: role has empty bound_audiences — "
                    f"any JWT aud value will be accepted"
                ),
                evidence={
                    "mismatch_type": "no_audience_binding",
                    "bound_audiences": bound_audiences,
                    "jwt_aud": ctx.jwt_claims.get("aud"),
                },
            )]
        return []

    def _check_bound_claims_bypass(self, ctx: LoginContext) -> list[Verdict]:
        """I5: Each key in bound_claims must match JWT claim — else it's a bypass."""
        bound_claims = ctx.role_config.get("bound_claims", {})
        if not bound_claims:
            return []

        verdicts: list[Verdict] = []
        for claim_key, expected_values in bound_claims.items():
            jwt_value = ctx.jwt_claims.get(claim_key)
            # expected_values can be a string or list of strings
            if isinstance(expected_values, str):
                expected_list = [expected_values]
            else:
                expected_list = list(expected_values)

            if jwt_value is None or str(jwt_value) not in [str(e) for e in expected_list]:
                verdicts.append(self._make_verdict(
                    invariant="I5",
                    verdict_type=VerdictType.VIOLATION,
                    description=(
                        f"[AutoVerify] bound_claims bypass: login succeeded but JWT {claim_key}={jwt_value!r} "
                        f"does not satisfy bound_claims requirement {expected_list!r}"
                    ),
                    evidence={
                        "mismatch_type": "bound_claims_bypass",
                        "claim_key": claim_key,
                        "jwt_value": jwt_value,
                        "expected_values": expected_list,
                    },
                    cve_pattern="CVE-2024-7594",
                ))

        return verdicts

    def _check_num_uses(self, ctx: LoginContext) -> list[Verdict]:
        """I2: token_num_uses in role should match token's actual num_uses."""
        role_num_uses = ctx.role_config.get("token_num_uses", 0)
        if not role_num_uses:
            return []

        token_num_uses = ctx.token_lookup.get("num_uses")
        if token_num_uses is None:
            return []

        # The token-lookup API call itself consumes one use, so the observed
        # num_uses is typically (role_num_uses - 1).  Only flag when the
        # discrepancy is larger than that single-call offset.
        expected_after_lookup = int(role_num_uses) - 1
        if int(token_num_uses) not in (int(role_num_uses), expected_after_lookup):
            return [self._make_verdict(
                invariant="I2",
                verdict_type=VerdictType.UNEXPECTED,
                description=(
                    f"[AutoVerify] num_uses mismatch: role specifies token_num_uses={role_num_uses} "
                    f"but token has num_uses={token_num_uses} (expected {role_num_uses} or {expected_after_lookup})"
                ),
                evidence={
                    "mismatch_type": "num_uses_mismatch",
                    "role_token_num_uses": role_num_uses,
                    "token_num_uses": token_num_uses,
                },
            )]
        return []

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _get_sub(self, ctx: LoginContext) -> Any:
        user_claim_field = ctx.role_config.get("user_claim", "sub")
        return ctx.jwt_claims.get(user_claim_field)

    def _make_verdict(
        self,
        invariant: str,
        verdict_type: VerdictType,
        description: str,
        evidence: dict,
        cve_pattern: str = "",
    ) -> Verdict:
        return Verdict(
            invariant=invariant,
            verdict_type=verdict_type,
            confidence="HIGH" if verdict_type == VerdictType.VIOLATION else "MEDIUM",
            description=description,
            evidence=evidence,
            spec_reference=invariant,
            cve_pattern=cve_pattern,
            requires_manual_review=True,
        )
