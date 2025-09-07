from __future__ import annotations

from typing import Dict, List


def chat_completion(messages: List[Dict[str, str]], *, temperature: float = 0.2) -> str:
    """
    Deterministic mock for local tests. It looks for an INTENT tag in the last
    user message to decide which canned reply to return.

    Recognized intents: INTENT: CONCEPT, INTENT: ERROR, INTENT: EXPLAIN_CODE
    Fallback: concept-style reply.
    """
    user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "").lower()

    # prefer intent tag if present
    if user_msg.startswith("intent: error") or "intent: error" in user_msg:
        return (
            "Meaning: This error indicates something went wrong at runtime.\n"
            "Likely causes: A bad reference or invalid input.\n"
            "Debug steps: Reproduce with a minimal example and inspect variables.\n"
            "Inspect next: The line mentioned in the error and inputs feeding it."
        )

    if user_msg.startswith("intent: explain_code") or "intent: explain_code" in user_msg:
        return (
            "Intent: Understand the code’s purpose.\n"
            "Key parts: Data flow and control flow.\n"
            "Flow: Input → transform → output.\n"
            "Complexity: Consider time and space.\n"
            "Edges: Empty inputs and extreme values."
        )

    # INTENT: CONCEPT or fallback
    return (
        "Definition: A high-level idea.\n"
        "Analogy: Like organizing items on shelves.\n"
        "Mental model: Break big problems into smaller ones.\n"
        "Check: Can you describe it in one sentence?"
    )
