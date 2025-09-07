from __future__ import annotations

import re


_FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`]+`")


def strip_code_blocks(text: str) -> str:
    """
    Remove fenced code blocks and inline backtick sections from model output.
    We do NOT remove short identifiers inside normal text; this targets code-like output.
    """
    text = _FENCED_CODE_RE.sub("[code omitted — EduTutor does not provide code]", text)
    text = _INLINE_CODE_RE.sub("[code omitted]", text)
    return text
