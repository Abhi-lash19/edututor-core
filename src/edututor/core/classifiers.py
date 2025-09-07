# src/edututor/core/classifiers.py
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


# ---------------------------------------------------------------------
# Intent enum + result dataclass
# ---------------------------------------------------------------------
class Intent(Enum):
    """High-level user intent categories the app understands."""

    CONCEPT = auto()  # "Explain recursion"
    ERROR = auto()  # "What does this traceback mean?"
    EXPLAIN_CODE = auto()  # "Explain my quicksort function"
    DISALLOWED = auto()  # "Write/implement the code for X"
    UNKNOWN = auto()


@dataclass(frozen=True)
class ClassifiedIntent:
    intent: Intent
    reason: str
    # optional explicit kind hint chosen by the user via UI (concept/error/explain)
    user_hint: Optional[Intent] = None


# ---------------------------------------------------------------------
# Compiled regexes (module-level; compile once)
# ---------------------------------------------------------------------
# Common phrasing we want to refuse (asks for code/solutions).
# Broad but tuned to minimize false positives.
_DISALLOWED_RE = re.compile(
    r"""
    (?ix)                  # case-insensitive, verbose
    \b(
        write|implement|code|solve|complete|fill\ in|finish|
        generate|produce|give|provide|paste|spit\ out|send\ me
    )\b
    [^.\n\r]{0,50}          # up to 50 chars of gap
    \b(
        code|function|class|program|solution|implementation|script|method
    )s?\b
    |
    \b(share|post)\b[^.\n\r]{0,30}\b(code|full\ solution|entire)\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

# If the user supplies their own code and wants an explanation,
# detect that as EXPLAIN_CODE.
_EXPLAIN_RE = re.compile(
    r"(?ix)\b(explain|walk\ me\ through|annotate|what\ does\ this|what\ does\ this\ code)\b"
)

_ERROR_RE = re.compile(
    r"(?ix)\b(error|exception|traceback|stack\ trace|segmentation\ fault|undefined\ reference)\b"
)

_CONCEPT_RE = re.compile(r"(?ix)\b(explain|what\ is|how\ does|teach|overview|concept|intuition)\b")

# Code indicators: words that strongly imply "this is code / implementation"
_CODE_INDICATORS_RE = re.compile(
    r"""
    (?ix)
    \b(
        function |
        method |
        snippet |
        this\ code |
        this\ function |
        my\ function |
        my\ method |
        class |
        module
    )\b
    """,
    re.VERBOSE,
)


# ---------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------
def classify_intent(text: str, *, user_hint: Optional[Intent] = None) -> ClassifiedIntent:
    """
    Heuristic classifier for user intent.

    Rules (priority order):
      1. Explicit disallowed requests (requests for code/solutions) => DISALLOWED.
      2. If user_hint is provided and plausible, respect it (unless disallowed).
      3. Error-related language => ERROR.
      4. Presence of code indicators (and/or explain phrasing) => EXPLAIN_CODE.
      5. Concept-like phrasing => CONCEPT.
      6. Generic explain phrasing => EXPLAIN_CODE (conservative).
      7. Fallback => UNKNOWN.
    """
    if text is None:
        text = ""
    t = text.strip()
    if not t:
        return ClassifiedIntent(Intent.UNKNOWN, "Empty or whitespace-only input", user_hint)

    # 1) Disallowed patterns -> immediate refusal
    if _DISALLOWED_RE.search(t):
        return ClassifiedIntent(
            Intent.DISALLOWED,
            "Matched disallowed request for code/solution",
            user_hint,
        )

    # 2) Respect explicit UI hint when plausible
    if user_hint in (Intent.CONCEPT, Intent.ERROR, Intent.EXPLAIN_CODE):
        # If text is obviously disallowed, refuse regardless of hint
        if _DISALLOWED_RE.search(t):
            return ClassifiedIntent(
                Intent.DISALLOWED, "Hinted intent but disallowed content", user_hint
            )
        return ClassifiedIntent(user_hint, f"User hinted {user_hint.name}", user_hint)

    # 3) Error-related phrasing
    if _ERROR_RE.search(t):
        return ClassifiedIntent(Intent.ERROR, "Matched error-related phrasing", user_hint)

    # 4) Code indicators: prefer EXPLAIN_CODE when code-related words present.
    #    Also treat "explain" + code indicators as EXPLAIN_CODE.
    has_code_indicators = bool(_CODE_INDICATORS_RE.search(t))
    if has_code_indicators or (_EXPLAIN_RE.search(t) and has_code_indicators):
        return ClassifiedIntent(
            Intent.EXPLAIN_CODE,
            "Matched explain-code phrasing / code indicators",
            user_hint,
        )

    # 5) Concept wording
    if _CONCEPT_RE.search(t):
        return ClassifiedIntent(Intent.CONCEPT, "Matched concept phrasing", user_hint)

    # 6) Generic explain-style phrasing -> default to EXPLAIN_CODE (conservative)
    if _EXPLAIN_RE.search(t):
        return ClassifiedIntent(Intent.EXPLAIN_CODE, "Matched explain-style phrasing", user_hint)

    # 7) Fallback
    return ClassifiedIntent(Intent.UNKNOWN, "No pattern matched", user_hint)
