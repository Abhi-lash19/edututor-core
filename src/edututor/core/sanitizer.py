# src/edututor/core/sanitizer.py
from __future__ import annotations

import re
from typing import List

# Fenced code block: ```...```
_FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
# Inline backticks: `...`
_INLINE_CODE_RE = re.compile(r"`[^`]+`")

# heuristics to detect code-like content
_CODE_LIKE_PATTERNS = [
    re.compile(r"^\s*def\s+\w+\(", re.MULTILINE),
    re.compile(r"^\s*class\s+\w+\s*:", re.MULTILINE),
    re.compile(r"\bfor\s+\w+\s+in\s+", re.IGNORECASE),
    re.compile(r"\bwhile\s+.*:\b", re.IGNORECASE),
    re.compile(r"\breturn\b", re.IGNORECASE),
]


def strip_code_blocks(text: str) -> str:
    """
    Remove fenced code blocks and inline backtick sections from model output.
    Uses the same placeholders expected by tests.
    """
    text = _FENCED_CODE_RE.sub("[code omitted — EduTutor does not provide code]", text)
    text = _INLINE_CODE_RE.sub("[code omitted]", text)
    return text


def strip_inline_code(text: str) -> str:
    """Replace inline backtick-delimited sections with a short placeholder."""
    return _INLINE_CODE_RE.sub("[code omitted]", text)


def detect_code_like(text: str) -> bool:
    """
    Heuristic detection for code-like content.
    """
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return False

    punct_chars = "{};()<>:=[]"
    punct_count = sum(1 for ln in lines if re.search(f"[{re.escape(punct_chars)}]", ln))
    punctuation_ratio = punct_count / len(lines)
    if punctuation_ratio > 0.35:
        return True

    for pat in _CODE_LIKE_PATTERNS:
        if pat.search(text):
            return True

    return False


def sanitize(text: str) -> str:
    """
    Sanitize LLM output so UI never receives raw code.

    Steps:
      1. Replace fenced code blocks with a descriptive placeholder.
      2. Replace inline backtick sections.
      3. If the result still looks code-like, drop suspicious lines.
    """
    t = strip_code_blocks(text)
    t = strip_inline_code(t)

    if detect_code_like(t):
        safe_lines: List[str] = []
        for ln in t.splitlines():
            ln_stripped = ln.strip()
            if not ln_stripped:
                continue
            if len(ln_stripped) > 300:
                continue
            # drop lines that contain code punctuation or keywords
            if re.search(r"[{};()<>=\[\]]", ln_stripped):
                continue
            if re.search(r"\b(return|yield|import|from|def|class)\b", ln_stripped, re.IGNORECASE):
                continue
            safe_lines.append(ln_stripped)
        t = "\n".join(safe_lines).strip()
        if not t:
            t = "[content removed: code-like output]"

    return t.strip()
