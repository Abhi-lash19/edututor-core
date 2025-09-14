# src/edututor/core/orchestrator.py
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

from edututor.llm import make_provider
from edututor.persistence.store import ConversationStore

from . import sanitizer, templates
from .classifiers import ClassifiedIntent, Intent, classify_intent
from .policy import decide_response

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorResult:
    text: str
    intent: Optional[Intent] = None


class Orchestrator:
    def __init__(self, provider: Any | None = None, store: ConversationStore | None = None) -> None:
        self.provider = provider or make_provider()
        self.store = store or ConversationStore()

    def handle_user_message(
        self,
        text: str,
        *,
        user_hint: Optional[Intent] = None,
    ) -> OrchestratorResult:
        ci: ClassifiedIntent = classify_intent(text, user_hint=user_hint)
        decision: Any = decide_response(ci)

        if getattr(decision, "is_disallowed", False):
            # use templates.disallowed_message() if present, otherwise fallback
            disallowed_fn = getattr(templates, "disallowed_message", None)
            out = (
                disallowed_fn()
                if callable(disallowed_fn)
                else ("I'm sorry, I can't help with that.")
            )
            try:
                self.store.save_conversation(
                    user_text=text,
                    intent=ci.intent.name if hasattr(ci.intent, "name") else str(ci.intent),
                    provider=type(self.provider).__name__,
                    llm_raw={},
                    sanitized_text=out,
                    metadata={"decision": "disallowed"},
                )
            except Exception:
                logger.exception("failed to save disallowed conversation (continuing)")

            return OrchestratorResult(text=out, intent=ci.intent)

        # build prompt using templates.scaffold_for(ci) if available; otherwise fallback
        scaffold_fn = getattr(templates, "scaffold_for", None)
        prompt = scaffold_fn(ci) if callable(scaffold_fn) else text

        llm_resp = self.provider.send(prompt=prompt, intent=ci.intent)

        # defensive: providers that return plain strings
        llm_text = getattr(llm_resp, "text", None) or (
            llm_resp if isinstance(llm_resp, str) else ""
        )
        llm_raw = getattr(llm_resp, "raw", {}) or {}

        sanitized = sanitizer.sanitize(llm_text)

        if not sanitized.strip():
            fallback_fn = getattr(templates, "fallback_message", None)
            sanitized = (
                fallback_fn()
                if callable(fallback_fn)
                else ("Sorry — I couldn't produce a helpful answer. Try rephrasing?")
            )

        try:
            self.store.save_conversation(
                user_text=text,
                intent=ci.intent.name if hasattr(ci.intent, "name") else str(ci.intent),
                provider=type(self.provider).__name__,
                llm_raw=llm_raw,
                sanitized_text=sanitized,
                metadata={
                    "decision": decision.name if hasattr(decision, "name") else str(decision)
                },
            )
        except Exception:
            logger.exception("failed to save conversation (continuing)")

        return OrchestratorResult(text=sanitized, intent=ci.intent)
