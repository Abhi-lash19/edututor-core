# src/edututor/llm/mock.py
from __future__ import annotations

import re
from typing import Any, Dict, List

from .base import BaseLLM, LLMResponse

# canned replies (kept simple and deterministic for tests)
_ERROR_REPLY = (
    "Meaning: This error indicates something went wrong at runtime.\n"
    "Likely causes: A bad reference or invalid input.\n"
    "Debug steps: Reproduce with a minimal example and inspect variables.\n"
    "Inspect next: The line mentioned in the error and inputs feeding it."
)

_EXPLAIN_CODE_REPLY = (
    "Intent: Understand the code’s purpose.\n"
    "Key parts: Data flow and control flow.\n"
    "Flow: Input → transform → output.\n"
    "Complexity: Consider time and space.\n"
    "Edges: Empty inputs and extreme values."
)

_CONCEPT_REPLY = (
    "Definition: A high-level idea.\n"
    "Analogy: Like organizing items on shelves.\n"
    "Mental model: Break big problems into smaller ones.\n"
    "Check: Can you describe it in one sentence?"
)

_INTENT_RE = re.compile(r"intent\s*:\s*([a-z0-9_ ]+)", flags=re.IGNORECASE)


def _normalize_intent_name(raw: str) -> str:
    """Normalize an intent string (e.g., 'explain code' -> 'EXPLAIN_CODE')."""
    return raw.strip().upper().replace(" ", "_")


def chat_completion(messages: List[Dict[str, str]], *, temperature: float = 0.2) -> str:
    last_user = ""
    for m in reversed(messages):
        if not isinstance(m, dict):
            continue
        role = m.get("role", "")
        if role == "user":
            last_user = (m.get("content", "") or "").strip()
            break

    if not last_user:
        return _CONCEPT_REPLY

    match = _INTENT_RE.search(last_user)
    if match:
        intent_raw = match.group(1)
        intent = _normalize_intent_name(intent_raw)
        if intent == "ERROR":
            return _ERROR_REPLY
        if intent in ("EXPLAIN_CODE", "EXPLAINCODE"):
            return _EXPLAIN_CODE_REPLY
        if intent == "CONCEPT":
            return _CONCEPT_REPLY
        return _CONCEPT_REPLY

    user_lower = last_user.lower()
    if any(k in user_lower for k in ("error", "exception", "traceback", "segmentation fault")):
        return _ERROR_REPLY

    return _CONCEPT_REPLY


class MockLLM(BaseLLM):
    """Deterministic mock LLM used for local dev and CI."""

    def send(self, *, prompt: str, intent: Any, max_tokens: int | None = None) -> LLMResponse:
        """
        Return canned replies according to the provided intent. Keep the replies
        consistent with the chat_completion() helper and the tests' expectations.
        """
        lower = str(intent).lower() if intent is not None else "unknown"

        if "concept" in lower:
            text = _CONCEPT_REPLY
        elif "error" in lower:
            text = _ERROR_REPLY
        elif "explain" in lower or "explain_code" in lower:
            text = _EXPLAIN_CODE_REPLY
        else:
            # Generic fallback (keeps content clear that mock won't provide solutions)
            text = (
                "I am a tutor assistant. I can explain concepts, guide debugging, and "
                "ask Socratic questions, but I will not write complete solutions."
            )

        return LLMResponse(text=text, raw={"mock_intent": str(intent)})
