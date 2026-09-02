"""LLM client wrapper using OpenAI SDK."""

import json
import logging
import re
import time

import openai

logger = logging.getLogger(__name__)


class LLMClient:
    """Thin wrapper around OpenAI API for structured JSON extraction."""

    def __init__(self, model: str = "gpt-5.2", temperature: float = 0.01):
        self.model = model
        self.temperature = temperature
        self._client = openai.OpenAI()
        self.stats = {
            "requests": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "errors": 0,
        }

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        """Call LLM, parse JSON from response. Returns {} on failure.

        gpt-5.2 parameters:
          - 400,000 token context window
          - 128,000 max output tokens
          - reasoning token support (tracked via usage.completion_tokens_details)
        """
        self.stats["requests"] += 1
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                max_completion_tokens=32768,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            usage = response.usage
            if usage:
                self.stats["input_tokens"] += usage.prompt_tokens
                self.stats["output_tokens"] += usage.completion_tokens
                # Track reasoning tokens separately if present
                details = getattr(usage, "completion_tokens_details", None)
                if details:
                    reasoning = getattr(details, "reasoning_tokens", 0) or 0
                    self.stats.setdefault("reasoning_tokens", 0)
                    self.stats["reasoning_tokens"] += reasoning

            text = response.choices[0].message.content or ""
            return self._parse_json(text)

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"LLM call failed: {e}")
            return {}

    def _parse_json(self, text: str) -> dict:
        """Extract JSON from LLM response, handling markdown code fences."""
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            text = match.group(1)
        text = text.strip()

        brace = text.find("{")
        if brace > 0:
            text = text[brace:]

        # Try strict parse first
        try:
            result = json.loads(text)
            # Handle double-encoded JSON (LLM returns a JSON string of JSON)
            if isinstance(result, str):
                try:
                    return json.loads(result)
                except (json.JSONDecodeError, TypeError):
                    pass
            return result
        except json.JSONDecodeError:
            pass

        # Try lenient parse (allows control chars in strings)
        try:
            return json.loads(text, strict=False)
        except json.JSONDecodeError:
            pass

        # Clean common LLM JSON artifacts and retry
        cleaned = text
        # Remove single-line comments (// ...)
        cleaned = re.sub(r'//[^\n]*', '', cleaned)
        # Remove trailing commas before } or ]
        cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
        # Truncate to last complete } or ]
        last_brace = max(cleaned.rfind('}'), cleaned.rfind(']'))
        if last_brace >= 0:
            cleaned = cleaned[:last_brace + 1]
        try:
            return json.loads(cleaned, strict=False)
        except json.JSONDecodeError as e2:
            logger.error(f"JSON parse failed: {e2}\nText (first 500): {text[:500]}")
            return {}
