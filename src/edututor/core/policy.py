from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from . import templates
from .classifiers import ClassifiedIntent, Intent

SYSTEM_PROMPT = """You are EduTutor, a strict but helpful computer science tutor.
Your mission is to foster deep understanding, not to provide finished solutions or code.

ALWAYS FOLLOW THESE RULES:
1) Never write new code, never complete code, never paste full solutions.
2) You may explain *concepts*, *error messages*, and *user-provided code* step-by-step.
3) Prefer the Socratic method: ask 1–2 guiding questions that lead the learner forward.
4) Speak concisely. Use plain language and simple examples. Avoid jargon unless you explain it.
5) If the user asks for code/solutions, politely refuse and redirect to understanding.

Output format:
- Short paragraphs or bullet points.
- For concept questions: definition → analogy → mental model → 1 check question.
- For error questions: meaning → likely causes → how to debug → what to inspect next.
- For code explanation: intent → key parts → flow → complexity intuition → edge cases.

Do not include code blocks or complete functions in your answers.
"""


@dataclass(frozen=True)
class TutorDecision:
    allowed: bool
    reason: str
    # Which scaffold to use; empty if refusal/unknown
    scaffold: str = ""
    # Optionally include a few Socratic questions
    questions: Tuple[str, ...] = ()


def decide_response(ci: ClassifiedIntent) -> TutorDecision:
    if ci.intent == Intent.DISALLOWED:
        return TutorDecision(
            allowed=False,
            reason=ci.reason,
        )

    if ci.intent == Intent.CONCEPT:
        return TutorDecision(
            allowed=True,
            reason=ci.reason,
            scaffold=templates.CONCEPT_SCAFFOLD,
            questions=tuple(templates.SOCRATIC_QUESTIONS[:2]),
        )

    if ci.intent == Intent.ERROR:
        return TutorDecision(
            allowed=True,
            reason=ci.reason,
            scaffold=templates.ERROR_EXPLANATION_SCAFFOLD,
            questions=tuple(templates.SOCRATIC_QUESTIONS[:2]),
        )

    if ci.intent == Intent.EXPLAIN_CODE:
        return TutorDecision(
            allowed=True,
            reason=ci.reason,
            scaffold=templates.EXPLAIN_CODE_SCAFFOLD,
            questions=tuple(templates.SOCRATIC_QUESTIONS[:2]),
        )

    # Unknown → treat as concept guidance prompt
    return TutorDecision(
        allowed=True,
        reason="Defaulted to concept-style guidance",
        scaffold=templates.CONCEPT_SCAFFOLD,
        questions=tuple(templates.SOCRATIC_QUESTIONS[:2]),
    )
