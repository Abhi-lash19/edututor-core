# src/edututor/llm/mock.py
from __future__ import annotations

import re
from typing import Dict, List

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
    """
    Normalize intent names to an UPPERCASE single-token form,
    e.g. "explain code" -> "EXPLAIN_CODE".
    """
    return raw.strip().upper().replace(" ", "_")


def chat_completion(messages: List[Dict[str, str]], *, temperature: float = 0.2) -> str:
    """
    Deterministic mock for local tests.

    Behavior:
    - Finds the last user message's content and tries to detect an explicit
      `INTENT: <name>` tag (case-insensitive). If found, returns the canned
      response for that intent.
    - If no explicit intent tag is present, falls back to keyword heuristics:
      - "error", "traceback", etc. -> error reply
      - otherwise -> concept-style reply

    This function is intentionally simple and deterministic for reproducible tests.
    """
    last_user = ""
    for m in reversed(messages):
        # defensive: messages are expected to be dicts with 'role' and 'content'
        if not isinstance(m, dict):
            continue
        role = m.get("role", "")
        if role == "user":
            last_user = (m.get("content", "") or "").strip()
            break

    if not last_user:
        # nothing from user -> concept fallback
        return _CONCEPT_REPLY

    # Look for explicit "INTENT: ..." tag anywhere in the user's content.
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
        # unknown explicit intent -> fall back to concept
        return _CONCEPT_REPLY

    # No explicit tag — use simple keyword heuristics on the user content:
    user_lower = last_user.lower()
    if any(k in user_lower for k in ("error", "exception", "traceback", "segmentation fault")):
        return _ERROR_REPLY

    # Default fallback: concept-style reply
    return _CONCEPT_REPLY
