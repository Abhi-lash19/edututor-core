from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from ..llm import mock as mock_llm
from .classifiers import ClassifiedIntent, Intent, classify_intent
from .policy import SYSTEM_PROMPT, TutorDecision, decide_response
from .sanitizer import strip_code_blocks


@dataclass
class OrchestratorResult:
    allowed: bool
    reason: str
    content: str


class Orchestrator:
    """
    Minimal orchestrator for MVP Day-1/2:
    - classify
    - decide via policy
    - call mock LLM if allowed
    - sanitize response
    """

    def __init__(self) -> None:
        pass

    def handle_user_message(
        self,
        text: str,
        *,
        user_hint: Optional[Intent] = None,
    ) -> OrchestratorResult:
        ci: ClassifiedIntent = classify_intent(text, user_hint=user_hint)
        decision: TutorDecision = decide_response(ci)

        if not decision.allowed:
            # Build a refusal response using templates.
            lines = [
                "I can’t provide code or full solutions.",
                "Reason: " + decision.reason,
                "",
                "Let’s proceed by understanding the problem instead:",
            ]
            # short Socratic nudge:
            lines.extend(f"- {q}" for q in decision.questions)
            content = "\n".join(lines)
            return OrchestratorResult(False, decision.reason, content)

        # Allowed → craft a structured prompt for the model.
        # IMPORTANT: include an explicit intent tag so downstream LLM adapters
        # (and our mock) can deterministically return the right style.
        # e.g., "INTENT: CONCEPT\nUser question: explain recursion"
        intent_tag = ci.intent.name  # CONCEPT / ERROR / EXPLAIN_CODE / UNKNOWN
        user_msg = f"INTENT: {intent_tag}\n\nUser: {text}"

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        raw = mock_llm.chat_completion(messages)
        safe = strip_code_blocks(raw)
        return OrchestratorResult(True, decision.reason, safe)


def test_strip_code_blocks_removes_fenced_and_inline():
    s = "Here is code:\n```py\nprint('hi')\n```\nAnd inline `x = 1` end."
    out = strip_code_blocks(s)
    assert "[code omitted" in out
    assert "[code omitted]" in out
