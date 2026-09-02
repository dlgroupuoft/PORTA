"""Safe assertion evaluator for oracle checks.

Supported grammar:
    assertion  := comparison (("AND" | "OR") comparison)*
    comparison := operand operator operand
               | operand "is" "None"
               | operand "is" "not" "None"
    operand    := variable | literal
    operator   := "==" | "!=" | "in" | "not in" | "contains" | ">" | "<" | ">=" | "<="
"""
from __future__ import annotations

import logging
import operator
import re
from typing import Any

logger = logging.getLogger(__name__)


class AssertionEvalError(Exception):
    pass


class AssertionEngine:
    """Safe assertion evaluator for oracle checks."""

    OPERATORS = {
        "==": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
    }

    @staticmethod
    def _normalize_template_syntax(assertion: str) -> str:
        """Normalize LLM-generated template/dot syntax to plain variable names.

        Handles two patterns:
        1. ``{{var_name.field}}`` → ``var_name_field`` (template wrappers)
        2. ``var_name.field`` → ``var_name_field`` (plain dot notation in
           variable-like tokens, not inside string literals)
        """
        def _replace_template(m: re.Match) -> str:
            inner = m.group(1).strip()
            return inner.replace(".", "_")

        # Step 1: handle {{...}} wrappers
        assertion = re.sub(r"\{\{\s*([^}]+?)\s*\}\}", _replace_template, assertion)

        # Step 2: convert plain dot-notation variables (word.word patterns)
        # but NOT inside quoted strings. Split on quoted segments first.
        parts = re.split(r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')', assertion)
        def _replace_dots(m: re.Match) -> str:
            return m.group(0).replace(".", "_")
        for i, part in enumerate(parts):
            # Odd indices are quoted strings — skip them
            if i % 2 == 0:
                parts[i] = re.sub(
                    r'\b([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)+)\b',
                    _replace_dots,
                    part,
                )
        assertion = "".join(parts)

        return assertion

    def evaluate(self, assertion: str, captures: dict) -> tuple[bool, str]:
        """Evaluate an assertion against captured values.

        Returns:
            (result: bool, explanation: str)
        Raises:
            AssertionEvalError if the assertion is malformed or variables missing.
        """
        assertion = assertion.strip()
        # Normalize LLM-generated template syntax: {{var.field}} → var_field
        assertion = self._normalize_template_syntax(assertion)
        logger.debug(f"Evaluating assertion: {assertion!r}")

        # Split on top-level AND / OR
        parts, ops = self._split_logical(assertion)

        if not parts:
            raise AssertionEvalError(f"Empty assertion: {assertion!r}")

        results = []
        explanations = []
        for part in parts:
            result, expl = self._evaluate_comparison(part.strip(), captures)
            results.append(result)
            explanations.append(expl)

        if not ops:
            return results[0], explanations[0]

        # Fold AND/OR left-to-right
        final = results[0]
        final_expl = explanations[0]
        for i, op in enumerate(ops):
            rhs = results[i + 1]
            rhs_expl = explanations[i + 1]
            if op == "AND":
                final = final and rhs
            else:  # OR
                final = final or rhs
            final_expl = f"({final_expl}) {op} ({rhs_expl})"

        logger.debug(f"Assertion result: {final}, explanation: {final_expl}")
        return final, final_expl

    def _split_logical(self, assertion: str) -> tuple[list[str], list[str]]:
        """Split assertion on AND/OR/&&/||, respecting quoted strings."""
        # Tokenize preserving quoted strings and symbolic operators
        token_pattern = re.compile(
            r'"[^"]*"|\'[^\']*\'|&&|\|\||\bAND\b|\bOR\b|[^\s]+'
        )
        tokens = token_pattern.findall(assertion)

        parts = []
        ops = []
        current = []
        for tok in tokens:
            if tok in ("AND", "&&"):
                parts.append(" ".join(current))
                ops.append("AND")
                current = []
            elif tok in ("OR", "||"):
                parts.append(" ".join(current))
                ops.append("OR")
                current = []
            else:
                current.append(tok)
        if current:
            parts.append(" ".join(current))

        return parts, ops

    def _evaluate_comparison(self, expr: str, captures: dict) -> tuple[bool, str]:
        """Evaluate a single comparison expression."""

        # "X is not None"
        m = re.match(r'^(.+?)\s+is\s+not\s+None\s*$', expr)
        if m:
            val = self._resolve_operand(m.group(1).strip(), captures)
            result = val is not None
            expl = f"{m.group(1).strip()}={val!r} is not None → {result}"
            return result, expl

        # "X is None" — also treat empty collections ([], {}, "") as None-equivalent
        # in security assertion context, "no data" = "absent"
        m = re.match(r'^(.+?)\s+is\s+None\s*$', expr)
        if m:
            val = self._resolve_operand(m.group(1).strip(), captures)
            result = val is None or val == [] or val == {} or val == ""
            expl = f"{m.group(1).strip()}={val!r} is None → {result}"
            return result, expl

        # "X not in Y"
        m = re.match(r'^(.+?)\s+not\s+in\s+(.+)$', expr)
        if m:
            left_tok, right_tok = m.group(1).strip(), m.group(2).strip()
            left = self._resolve_operand(left_tok, captures)
            right = self._resolve_operand(right_tok, captures)
            right_is_var = not right_tok.startswith(("'", '"')) and not right_tok.replace(".", "", 1).lstrip("-").isdigit() and right_tok not in ("True", "False", "None", "true", "false", "null", "none")
            if right is None and right_is_var:
                return False, f"{left!r} not in {right!r} → False (variable captured as None — verify event returned no data)"
            result = left not in right if right is not None else False
            expl = f"{left!r} not in {right!r} → {result}"
            return result, expl

        # "X contains Y" (X is a list/string, Y is the element)
        m = re.match(r'^(.+?)\s+contains\s+(.+)$', expr)
        if m:
            left_tok, right_tok = m.group(1).strip(), m.group(2).strip()
            left = self._resolve_operand(left_tok, captures)
            right = self._resolve_operand(right_tok, captures)
            left_is_var_c = not left_tok.startswith(("'", '"')) and not left_tok.replace(".", "", 1).lstrip("-").isdigit() and left_tok not in ("True", "False", "None", "true", "false", "null", "none")
            if left is None and left_is_var_c:
                return False, f"{left!r} contains {right!r} → False (variable captured as None — verify event returned no data)"
            result = right in left if left is not None else False
            expl = f"{left!r} contains {right!r} → {result}"
            return result, expl

        # "X in Y"
        m = re.match(r'^(.+?)\s+in\s+(.+)$', expr)
        if m:
            left_tok, right_tok = m.group(1).strip(), m.group(2).strip()
            left = self._resolve_operand(left_tok, captures)
            right = self._resolve_operand(right_tok, captures)
            right_is_var_in = not right_tok.startswith(("'", '"')) and not right_tok.replace(".", "", 1).lstrip("-").isdigit() and right_tok not in ("True", "False", "None", "true", "false", "null", "none")
            if right is None and right_is_var_in:
                return False, f"{left!r} in {right!r} → False (variable captured as None — verify event returned no data)"
            result = left in right if right is not None else False
            expl = f"{left!r} in {right!r} → {result}"
            return result, expl

        # Standard comparison operators (try longest first to avoid partial matches)
        for op_str in (">=", "<=", "==", "!=", ">", "<"):
            # Split on operator, not inside quotes
            pattern = re.compile(
                r'^(.+?)\s*' + re.escape(op_str) + r'\s*(.+)$'
            )
            m = pattern.match(expr)
            if m:
                left_tok = m.group(1).strip()
                right_tok = m.group(2).strip()
                left = self._resolve_operand(left_tok, captures)
                right = self._resolve_operand(right_tok, captures)

                # Guard: if both operands resolved to None (unset captures),
                # the comparison is meaningless — likely a failed event.
                # Treat as False to avoid false BY_DESIGN verdicts.
                left_is_var = left_tok not in ("None", "True", "False", "none", "true", "false", "null") and not left_tok.startswith(("'", '"'))
                right_is_literal = right_tok.startswith(("'", '"')) or right_tok.replace(".", "", 1).lstrip("-").isdigit() or right_tok in ("True", "False", "None", "true", "false", "null", "none")
                # Only flag as infrastructure failure when the assertion is NOT
                # explicitly comparing against None/null (e.g. "x == null" is
                # a legitimate check, but "x == 403" with x=None is not).
                right_is_none_literal = right_tok in ("None", "null", "none")
                if left is None and left_is_var and not right_is_none_literal:
                    if left_tok not in captures:
                        expl = f"{left_tok}={left!r} {op_str} {right!r} → False (variable not captured — event likely failed)"
                    else:
                        expl = f"{left_tok}={left!r} {op_str} {right!r} → False (variable captured as None — verify event returned no data)"
                    return False, expl

                op_fn = self.OPERATORS[op_str]
                try:
                    result = op_fn(left, right)
                except TypeError as e:
                    raise AssertionEvalError(
                        f"Cannot compare {left!r} {op_str} {right!r}: {e}"
                    )
                expl = f"{left_tok}={left!r} {op_str} {right!r} → {result}"
                return result, expl

        raise AssertionEvalError(f"Cannot parse comparison: {expr!r}")

    def _resolve_operand(self, token: str, captures: dict) -> Any:
        """Resolve a token to its value.

        - Quoted string → the string content
        - Number → int or float
        - True/False/None → Python literals
        - dot-path: "user_a_meta.username" → captures["user_a_meta"]["username"]
        - Otherwise: look up in captures
        """
        # Quoted string
        if (token.startswith('"') and token.endswith('"')) or \
           (token.startswith("'") and token.endswith("'")):
            return token[1:-1]

        # Python literals (also accept JSON-style true/false/null)
        if token in ("True", "true"):
            return True
        if token in ("False", "false"):
            return False
        if token in ("None", "null", "none"):
            return None

        # Numeric
        try:
            if "." in token:
                return float(token)
            return int(token)
        except ValueError:
            pass

        # Variable (possibly dot-path)
        if "." in token:
            parts = token.split(".", 1)
            base = parts[0]
            rest = parts[1]
            base_val = self._lookup_capture(base, captures)
            if base_val is None:
                logger.debug(f"Variable {base!r} not in captures")
                return None
            return self._extract_dot_path(base_val, rest)

        return self._lookup_capture(token, captures)

    def _lookup_capture(self, token: str, captures: dict) -> Any:
        """Look up a capture variable, with generic alias resolution.

        If ``token`` is not directly in captures, search for a key of the form
        ``{single_word}_{token}`` — handling the common case where the executor
        stores captures with an auth-as-derived prefix (e.g. ``user_u2_entity_id``)
        while the oracle assertion uses the shorter form (``u2_entity_id``).
        """
        if token in captures:
            return captures[token]

        # Alias resolution: find keys ending in _{token} whose prefix is a
        # single identifier component (no underscores) to avoid false matches.
        suffix = f"_{token}"
        candidates = [
            k for k in captures
            if k.endswith(suffix) and "_" not in k[: -len(suffix)]
        ]
        if candidates:
            resolved_key = candidates[0]
            if len(candidates) > 1:
                logger.debug(
                    f"Variable {token!r} has multiple alias candidates {candidates!r}, using {resolved_key!r}"
                )
            else:
                logger.debug(f"Variable {token!r} resolved via alias {resolved_key!r}")
            return captures[resolved_key]

        logger.debug(f"Variable {token!r} not found in captures (keys: {list(captures.keys())})")
        return None

    def _extract_dot_path(self, obj: Any, path: str) -> Any:
        """Navigate a dot-separated path into nested dicts/lists."""
        current = obj
        for part in path.split("."):
            if current is None:
                return None
            m = re.match(r'^(\w+)\[(\d+)\]$', part)
            if m:
                key, idx = m.group(1), int(m.group(2))
                current = current.get(key, []) if isinstance(current, dict) else None
                if isinstance(current, list) and idx < len(current):
                    current = current[idx]
                else:
                    return None
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current
