# src/edututor/core/orchestrator.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from edututor.llm import make_provider
from edututor.llm.base import BaseLLM, LLMResponse

from . import sanitizer
from .classifiers import ClassifiedIntent, Intent, classify_intent
from .policy import decide_response


@dataclass(frozen=True)
class OrchestratorResult:
    """Result returned to callers and tests (keeps compatibility with tests)."""

    allowed: bool
    reason: str
    content: str
    intent: Optional[Intent] = None


class Orchestrator:
    """
    Orchestrator glue: classify -> policy -> LLM provider -> sanitize -> return.
    The `provider` can be injected for tests; by default we use make_provider().
    """

    def __init__(self, provider: BaseLLM | None = None) -> None:
        # allow dependency injection for tests; default factory uses env
        self.provider: BaseLLM = provider or make_provider()

    def handle_user_message(
        self, text: str, *, user_hint: Optional[Intent] = None
    ) -> OrchestratorResult:
        ci: ClassifiedIntent = classify_intent(text, user_hint=user_hint)
        decision = decide_response(ci)

        # Policy-level disallow -> return a templated refusal (no LLM call)
        if not getattr(decision, "allowed", True):
            # Build a refusal response using templates (format to plain text).
            lines = [
                "I can’t provide code or full solutions.",
                "Reason: " + decision.reason,
                "",
                "Let’s proceed by understanding the problem instead:",
            ]
            # short Socratic nudge:
            lines.extend(f"- {q}" for q in (getattr(decision, "questions", ()) or ()))
            content = "\n".join(lines)

            result = OrchestratorResult(
                allowed=False,
                reason=decision.reason,
                content=content,
                intent=ci.intent,
            )
            return result

        # Allowed -> craft a structured prompt for the model using the scaffold
        scaffold = getattr(decision, "scaffold", "")
        prompt = scaffold or ""

        # Ask the provider for a response
        llm_resp: LLMResponse = self.provider.send(prompt=prompt, intent=ci.intent)
        sanitized = sanitizer.sanitize(llm_resp.text or "")

        if not sanitized.strip():
            sanitized = "[content removed: empty after sanitization]"

        result = OrchestratorResult(
            allowed=True,
            reason=decision.reason,
            content=sanitized,
            intent=ci.intent,
        )
        return result
