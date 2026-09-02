"""Plain LLM-as-judge verdict path.

Sends the sequence description, event outcomes, and captured state to an LLM
and asks it to judge whether the behavior indicates a security vulnerability.
No assertion oracle, no deterministic checks, no invariant taxonomy — pure LLM judgment.

Optionally includes sanitized platform profile information (API endpoints and
operational constraints) so the LLM has platform context for its judgment.
All invariant references (I1-I5, invariant names) are stripped from the profile
to prevent information leakage from the taxonomy.
"""
import json
import logging
import re
from typing import Any

from src.llm.client import LLMClient
from src.models.types import Verdict, VerdictType

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a security analyst reviewing the execution results of an automated \
test sequence against an identity broker platform (SSO / OIDC / SAML).

Your task: determine whether the observed behavior indicates a security \
vulnerability. You will be given:
1. The test sequence description and events
2. The HTTP status codes and outcomes of each event
3. All captured runtime values (login identities, entity IDs, etc.)

For each potential vulnerability you find, provide:
- verdict: "VIOLATION" (clear security issue) or "UNEXPECTED" (suspicious)
- confidence: "HIGH", "MEDIUM", or "LOW"
- description: one-line explanation of the vulnerability
- evidence: key captured values that support the judgment

If the behavior is normal/expected, return an empty findings list.

Respond in JSON:
{
  "findings": [
    {
      "verdict": "VIOLATION",
      "confidence": "HIGH",
      "description": "...",
      "evidence_keys": ["key1", "key2"]
    }
  ]
}
"""

# Regex to strip invariant references from profile text
_INVARIANT_RE = re.compile(
    r'\bI[1-5]\b|'
    r'\binvariant[s]?\b|'
    r'\bproof.integrity\b|'
    r'\btemporal.validity\b|'
    r'\bflow.coherence\b|'
    r'\bprincipal.binding\b|'
    r'\bauthorization.scope\b',
    re.IGNORECASE,
)


def _sanitize_profile(profile) -> str:
    """Extract API mapping and constraints from profile, stripping invariant refs."""
    if profile is None:
        return ""

    sanitized = {}

    # Include platform name and base URL
    sanitized["name"] = getattr(profile, "name", "unknown")
    sanitized["base_url"] = getattr(profile, "base_url", "")

    # Include API mapping (endpoint info: operation -> method + path)
    api_mapping = getattr(profile, "api_mapping", {})
    if api_mapping:
        sanitized["api_endpoints"] = {}
        for proto, endpoints in api_mapping.items():
            sanitized["api_endpoints"][proto] = {}
            for op_name, ep in endpoints.items():
                method = getattr(ep, "method", "")
                path = getattr(ep, "path", "")
                sanitized["api_endpoints"][proto][op_name] = {
                    "method": method, "path": path,
                }

    # Include api_constraints but strip invariant references
    constraints = getattr(profile, "api_constraints", [])
    if constraints:
        clean = []
        for c in constraints:
            text = c if isinstance(c, str) else str(c)
            text = _INVARIANT_RE.sub("", text)
            if text.strip():
                clean.append(text)
        if clean:
            sanitized["api_constraints"] = clean

    text = json.dumps(sanitized, indent=2)
    # Final pass: strip any remaining invariant references
    text = _INVARIANT_RE.sub("", text)
    return text


class PlainLLMVerifier:
    """LLM-as-judge: sends execution results to LLM for vulnerability judgment."""

    def __init__(self, llm_model: str = None, profile=None,
                 include_invariants: bool = False, **kwargs):
        model = llm_model or "gpt-5.2"
        self.llm = LLMClient(model=model, temperature=0.01)
        self._profile_text = _sanitize_profile(profile)
        self._invariant_text = ""
        if include_invariants:
            from src.models.invariants import INVARIANT_DEFINITIONS
            self._invariant_text = "\n".join(
                f"  {k}: {v}" for k, v in INVARIANT_DEFINITIONS.items()
            )

    def verify(self, sequence, execution_result) -> list[Verdict]:
        """Ask LLM to judge whether execution results indicate a vulnerability."""
        user_prompt = self._build_prompt(sequence, execution_result)

        try:
            response = self.llm.generate_json(SYSTEM_PROMPT, user_prompt)
        except Exception as e:
            logger.error(f"PlainLLMVerifier LLM call failed: {e}")
            return []

        if not response or "findings" not in response:
            return []

        verdicts = []
        for f in response.get("findings", []):
            verdict_str = f.get("verdict", "UNEXPECTED")
            try:
                vtype = VerdictType(verdict_str)
            except ValueError:
                vtype = VerdictType.UNEXPECTED

            confidence = f.get("confidence", "MEDIUM")
            description = f.get("description", "")
            evidence_keys = f.get("evidence_keys", [])

            captured = getattr(execution_result, "captured_state", {})
            evidence = {
                k: captured.get(k) for k in evidence_keys if k in captured
            }
            evidence["llm_judge_description"] = description

            v = Verdict(
                invariant="",  # LLM judge does not classify by invariant
                verdict_type=vtype,
                confidence=confidence,
                description=f"[LLM-Judge] {description}",
                evidence=evidence,
            )
            v.detection_source = "plain_llm"
            verdicts.append(v)

        logger.info(
            f"PlainLLMVerifier: {len(verdicts)} finding(s) from LLM judge"
        )
        return verdicts

    def _build_prompt(self, sequence, execution_result) -> str:
        """Build user prompt from sequence + execution results."""
        parts = []

        # Invariant definitions (if enabled)
        if self._invariant_text:
            parts.append("## Security Invariants")
            parts.append("Use these invariant definitions to guide your analysis:")
            parts.append(self._invariant_text)
            parts.append("")

        # Platform profile context (if available)
        if self._profile_text:
            parts.append("## Platform Profile")
            parts.append(self._profile_text)
            parts.append("")

        # Sequence info
        parts.append(f"## Test Sequence: {sequence.sequence_id}")
        parts.append(f"Description: {sequence.description}")
        parts.append("")

        # Events and outcomes
        parts.append("## Events and Outcomes")
        event_results = getattr(execution_result, "event_results", [])
        for i, er in enumerate(event_results):
            evt = er.event
            parts.append(
                f"  [{i+1}] {evt.event_type} (auth_as={evt.auth_as}) "
                f"→ HTTP {er.http_status}, success={er.success}"
            )
            if er.error:
                parts.append(f"      error: {er.error[:200]}")
            if er.captured_values:
                for k, v in er.captured_values.items():
                    val_str = str(v)[:100]
                    parts.append(f"      captured: {k} = {val_str}")
        parts.append("")

        # Captured state (all variables)
        parts.append("## Captured State")
        captured = getattr(execution_result, "captured_state", {})
        for k, v in sorted(captured.items()):
            val_str = json.dumps(v) if isinstance(v, (dict, list)) else str(v)
            if len(val_str) > 200:
                val_str = val_str[:200] + "..."
            parts.append(f"  {k} = {val_str}")
        parts.append("")

        # Execution status
        parts.append(f"## Execution Status: {execution_result.status}")

        return "\n".join(parts)
