from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class Intent(Enum):
    """High-level user intent categories the app understands."""

    CONCEPT = auto()  # "Explain recursion"
    ERROR = auto()  # "What does this traceback mean?"
    EXPLAIN_CODE = auto()  # "Explain my quicksort function"
    DISALLOWED = auto()  # "Write/implement the code for X"
    UNKNOWN = auto()


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
# we try to detect that as EXPLAIN_CODE.
_EXPLAIN_RE = re.compile(r"(?i)\b(explain|walk\ me\ through|annotate|what\ does\ this)\b")

_ERROR_RE = re.compile(
    r"(?i)\b(error|exception|traceback|stack\ trace|segmentation\ fault|undefined\ reference)\b"
)

_CONCEPT_RE = re.compile(r"(?i)\b(explain|what\ is|how\ does|teach|overview|concept|intuition)\b")


@dataclass(frozen=True)
class ClassifiedIntent:
    intent: Intent
    reason: str
    # optional explicit kind hint chosen by the user via UI (concept/error/explain)
    user_hint: Optional[Intent] = None


def classify_intent(text: str, *, user_hint: Optional[Intent] = None) -> ClassifiedIntent:
    """
    Cheap-and-cheerful heuristic classifier.

    Rules:
      - Disallowed patterns (requests for solutions/code) are checked first.
      - If user explicitly hints via UI, respect that (unless disallowed).
      - Then check error patterns.
      - Then check for explicit code-related explain (EXPLAIN_CODE) *if* the text
        mentions code artifacts like "function", "snippet", "this code", "my method".
      - Then treat general "explain X" or "what is X" as CONCEPT.
      - Fallback: UNKNOWN.
    """
    t = text.strip()

    if _DISALLOWED_RE.search(t):
        return ClassifiedIntent(
            Intent.DISALLOWED,
            "Matched disallowed request for code/solution",
            user_hint,
        )

    # If user hinted explicitly in the UI, respect that when plausible.
    if user_hint in (Intent.CONCEPT, Intent.ERROR, Intent.EXPLAIN_CODE):
        # Double-check we aren't obviously disallowed.
        if _DISALLOWED_RE.search(t):
            return ClassifiedIntent(
                Intent.DISALLOWED, "Hinted intent but disallowed content", user_hint
            )
        return ClassifiedIntent(user_hint, f"User hinted {user_hint.name}", user_hint)

    # Heuristics without hint (order matters):
    # 1) Error patterns (clear runtime/debugging intent)
    if _ERROR_RE.search(t):
        return ClassifiedIntent(Intent.ERROR, "Matched error-related phrasing", user_hint)

    # 2) Code-indicator patterns: if the user uses words that imply they are referring
    #    to code/implementation, treat as EXPLAIN_CODE. This avoids misclassifying
    #    "explain my function step by step" as a generic concept question.
    code_indicators = re.compile(
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

    # parenthesize to make precedence explicit:
    if code_indicators.search(t) or (_EXPLAIN_RE.search(t) and code_indicators.search(t)):
        return ClassifiedIntent(
            Intent.EXPLAIN_CODE,
            "Matched explain-code phrasing / code indicators",
            user_hint,
        )

    # 3) Concept patterns (e.g., "explain recursion", "what is a hash table")
    if _CONCEPT_RE.search(t):
        return ClassifiedIntent(Intent.CONCEPT, "Matched concept phrasing", user_hint)

    # 4) Generic explain patterns fallback to EXPLAIN_CODE when they mention "this" along
    #    with code indicators. Otherwise treat as a generic explain/code explanation.
    if _EXPLAIN_RE.search(t):
        # if text contains words like 'this' and 'code' then it's code explain; else treat
        # as explain-code by default
        return ClassifiedIntent(Intent.EXPLAIN_CODE, "Matched explain-style phrasing", user_hint)

    return ClassifiedIntent(Intent.UNKNOWN, "No pattern matched", user_hint)
