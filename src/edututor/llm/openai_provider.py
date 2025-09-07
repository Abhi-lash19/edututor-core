# src/edututor/llm/openai_provider.py
from __future__ import annotations

import logging
import os
import random
import time
from typing import Any, Dict, Optional

import requests

from .base import BaseLLM, LLMResponse

LOG = logging.getLogger(__name__)


class OpenAIProvider(BaseLLM):
    def __init__(
        self,
        api_key: str,
        api_base: str,
        model: str,
        timeout_seconds: int = 20,
        max_retries: int = 3,
        max_tokens: int = 512,
    ) -> None:
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_tokens = max_tokens

    @classmethod
    def from_env(cls) -> "OpenAIProvider":
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            api_base=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            timeout_seconds=int(os.getenv("OPENAI_TIMEOUT_SECONDS", "20")),
            max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "3")),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "512")),
        )

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _payload(self, prompt: str, intent: Any, max_tokens: Optional[int]) -> Dict[str, Any]:
        system_msg = (
            "You are a strict pedagogical tutor. "
            "INTENT: " + str(intent) + ". You must not provide full code or exact solutions. "
            "Provide conceptual explanations, hints, and Socratic prompts only."
        )
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": 0.2,
        }

    def send(self, *, prompt: str, intent: Any, max_tokens: Optional[int] = None) -> LLMResponse:
        url = f"{self.api_base}/chat/completions"
        payload = self._payload(prompt, intent, max_tokens)

        attempt = 0
        while True:
            attempt += 1
            try:
                LOG.debug("OpenAIProvider POST %s attempt=%d", url, attempt)
                resp = requests.post(
                    url,
                    headers=self._headers(),
                    json=payload,
                    timeout=self.timeout_seconds,
                )
                if resp.status_code == 200:
                    body = resp.json()
                    text = ""
                    if isinstance(body, dict):
                        choices = body.get("choices") or []
                        if choices and choices[0].get("message"):
                            text = choices[0]["message"].get("content", "")
                    return LLMResponse(text=str(text).strip(), raw=body)

                # Retry on rate limit / server errors
                if resp.status_code in {429, 500, 502, 503, 504} and attempt <= self.max_retries:
                    wait = (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                    LOG.warning(
                        "OpenAI transient error status=%d; retrying in %.2fs (attempt=%d)",
                        resp.status_code,
                        wait,
                        attempt,
                    )
                    time.sleep(wait)
                    continue

                resp.raise_for_status()

            except requests.RequestException as exc:
                if attempt <= self.max_retries:
                    wait = (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                    LOG.warning(
                        "OpenAI request exception %s. Retrying in %.2fs (attempt=%d)",
                        exc,
                        wait,
                        attempt,
                    )
                    time.sleep(wait)
                    continue
                LOG.exception("OpenAIProvider failed after %d attempts", attempt)
                raise
