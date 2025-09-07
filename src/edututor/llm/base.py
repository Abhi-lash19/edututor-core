# src/edututor/llm/base.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


@dataclass(frozen=True)
class LLMResponse:
    """
    Uniform response object for LLM providers.

    `text` is the sanitized plain string the orchestrator will receive.
    `raw` is the original provider payload (for diagnostics only).
    """

    text: str
    raw: Dict[str, Any]


class BaseLLM(Protocol):
    """
    Protocol interface for pluggable LLM providers.
    """

    def send(
        self, *, prompt: str, intent: Any, max_tokens: Optional[int] = None
    ) -> LLMResponse: ...
