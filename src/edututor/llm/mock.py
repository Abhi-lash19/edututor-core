# src/edututor/llm/mock.py
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, cast

# Try to import BaseLLM and LLMResponse for typing; fall back cleanly at runtime.
if TYPE_CHECKING:
    # Only used by static type checker
    from edututor.llm.base import BaseLLM, LLMResponse  # type: ignore
else:
    try:
        from edututor.llm.base import BaseLLM, LLMResponse  # type: ignore
    except Exception:
        # runtime fallback so tests / usage still run if base isn't importable here
        BaseLLM = object  # type: ignore
        LLMResponse = None  # type: ignore


@dataclass
class MockResponse:
    """
    Simple response object that mirrors what a real LLM wrapper might return.
    - text: human-readable reply
    - raw: optional structured data to inspect (like a provider-specific payload)
    """

    text: str
    raw: Optional[Dict[str, Any]] = None


def _prompt_to_text(prompt: Any) -> str:
    """
    Normalize possible prompt shapes into a single string:
    - list of message dicts -> join their 'content' fields
    - dict -> use its 'content' if present, else str(dict)
    - str -> return as-is
    - otherwise -> str(prompt)
    """
    if prompt is None:
        return ""
    if isinstance(prompt, list):
        parts = []
        for part in prompt:
            if isinstance(part, dict):
                parts.append(str(part.get("content", "")))
            else:
                parts.append(str(part))
        return " ".join(p for p in parts if p)
    if isinstance(prompt, dict):
        return str(prompt.get("content", prompt))
    return str(prompt)


def _extract_explicit_intent(text: str) -> Optional[str]:
    """
    Look for explicit intent markers inside the text like:
      INTENT: ERROR
      intent=explain_code
    Returns the intent token (lowercased) if found.
    """
    if not text:
        return None
    m = re.search(
        r"intent\s*[:=]\s*([a-zA-Z0-9_\-]+)",
        text,
        flags=re.IGNORECASE,
    )
    if m:
        return m.group(1).strip().lower()
    return None


def _decide_response(prompt: Any, intent: Optional[Any] = None) -> Tuple[str, Dict[str, Any]]:
    """
    Internal helper: decide which canned response to return based on prompt and intent.
    Returns (text, raw_dict).
    """
    text_prompt = _prompt_to_text(prompt)
    low = (text_prompt or "").lower()

    # If the prompt itself contains an explicit intent directive, prefer that
    explicit = _extract_explicit_intent(text_prompt)
    if explicit:
        intent = explicit

    # If an explicit/parsed intent is provided, handle it first.
    if intent:
        it = str(intent).lower()
        # explicit error intent -> must include "Meaning: This error"
        if it == "error" or "error" in it:
            return (
                "Meaning: This error indicates an exception was raised while "
                "executing the code. Suggested steps: check the stack trace, "
                "inspect the line and variables mentioned, and add logging or "
                "a breakpoint to reproduce and fix the root cause.",
                {"intent": "error"},
            )
        # explicit explain_code intent
        if it in ("explain_code", "explaincode", "explain-code") or (
            "explain" in it and "code" in it
        ):
            return (
                "Key parts:\n- What the code does\n- Important functions\n"
                "- Edge cases and complexity\n",
                {"intent": "explain_code"},
            )

    # Keyword-based heuristics (fallbacks)
    if "traceback" in low or "exception" in low or "nullpointerexception" in low:
        # phrase includes "Meaning: This error" to satisfy tests that check for it.
        return (
            "Meaning: This error indicates an exception. Check the stack trace "
            "and the lines referenced to diagnose.",
            {"fallback": "error"},
        )

    if "explain code" in low or "explain_code" in low or ("explain" in low and "code" in low):
        return (
            "Key parts:\n- This function does X\n- Key variables are A, B\n"
            "- Consider edge cases and performance\n",
            {"fallback": "explain_code"},
        )

    # Updated recursion response to match test expectation substring
    if "recursion" in low or "what is recursion" in low or "tell me about recursion" in low:
        return (
            "Definition: A high-level idea: Recursion is when a function calls "
            "itself. Typical parts include a base case, a recursive case, and "
            "ensuring progress toward the base case.",
            {"concept": "recursion"},
        )

    # Generic default response
    return (
        "I'm not sure how to help with that exact input — can you provide more details?",
        {"fallback": "unknown"},
    )


def chat_completion(prompt: Any, intent: Optional[Any] = None) -> str:
    """
    Public mock function used by tests.
    Accepts:
      - a list of message dicts (e.g. [{'role':'user','content':'...'}, ...])
      - a dict with 'content'
      - a plain string
    Returns the response text (string).
    """
    text, raw = _decide_response(prompt, intent=intent)
    return text


class MockLLM(BaseLLM):  # type: ignore[misc]
    """
    Simple mock LLM provider class.

    Usage:
        provider = MockLLM()
        resp = provider.send(prompt="explain this code: ...")
        print(resp.text)
    """

    def send(self, *, prompt: str, intent: Any, max_tokens: Optional[int] = None) -> "LLMResponse":  # type: ignore[name-defined]
        """
        Return a response compatible with the project's LLMResponse type.
        We construct a MockResponse and cast it to LLMResponse so static typing
        accepts MockLLM as a BaseLLM implementation.
        """
        text, raw = _decide_response(prompt, intent=intent)
        # If LLMResponse is available and is a class, you may want to build it.
        # For compatibility we return a MockResponse cast to LLMResponse.
        return cast("LLMResponse", MockResponse(text=text, raw=raw))


# Public API
__all__ = ["MockResponse", "chat_completion", "MockLLM"]
