from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class RefusalTemplate:
    title: str
    body_lines: List[str]


REFUSAL = RefusalTemplate(
    title="I can’t write code for you — let’s learn it instead",
    body_lines=[
        "EduTutor is designed to build your understanding, not deliver finished code.",
        "Here’s how we can proceed:",
        "1) Clarify the goal (what should the program do, with what inputs/outputs?).",
        "2) Identify the core building blocks (data structures, loops/recursion, invariants).",
        "3) Sketch the algorithm in plain language or pseudocode.",
        "4) Translate each step into *your own* code — I’ll explain each step conceptually.",
    ],
)

SOCRATIC_QUESTIONS = [
    "What inputs and outputs should the program handle?",
    "If you had to do this by hand, step-by-step, what would you do first?",
    "Which data structure best fits this task (list, dict/map, set, queue, stack, tree)? Why?",
    "What’s the smallest sub-problem you can solve first?",
    "How will you verify correctness (invariants, test cases)?",
]

# Response scaffolds (not code) for allowed intents:
CONCEPT_SCAFFOLD = (
    "Here’s the idea in plain words, then an analogy, and then a quick mental model.\n"
    "• Definition: {definition}\n"
    "• Analogy: {analogy}\n"
    "• Mental model: {mental_model}\n"
    "Check yourself: {check_question}"
)

ERROR_EXPLANATION_SCAFFOLD = (
    "Meaning of this error: {meaning}\n"
    "Why it likely happens: {causes}\n"
    "How you can debug it: {debug_steps}\n"
    "What to inspect next: {inspect}"
)

EXPLAIN_CODE_SCAFFOLD = (
    "Let’s walk through your code conceptually — not editing it — to understand how it works.\n"
    "High-level intent: {intent}\n"
    "Key moving parts: {parts}\n"
    "Flow summary: {flow}\n"
    "Complexity intuition: {complexity}\n"
    "Edge cases to test: {edges}"
)
