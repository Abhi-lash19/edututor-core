# src/edututor/llm/__init__.py
from __future__ import annotations

import os

from .base import BaseLLM
from .mock import MockLLM


def make_provider() -> BaseLLM:
    """Factory to choose the LLM provider from environment config.

    Defaults to the MockLLM for local dev and CI.
    """
    provider = os.getenv("LLM_PROVIDER", "mock").lower()
    if provider in ("openai", "openai_api"):
        # import lazily to keep startup cheap in CI when mock is used
        from .openai_provider import OpenAIProvider  # type: ignore

        return OpenAIProvider.from_env()
    return MockLLM()
