from __future__ import annotations

import pytest

from edututor.core.classifiers import Intent, classify_intent


@pytest.mark.parametrize(
    "prompt",
    [
        "write the code for quicksort",
        "can you implement a binary search function",
        "please give me the complete solution",
        "generate code for a stack class",
        "can you paste the full program",
    ],
)
def test_disallowed_requests(prompt: str) -> None:
    ci = classify_intent(prompt)
    assert ci.intent == Intent.DISALLOWED


@pytest.mark.parametrize(
    "prompt",
    [
        "explain recursion in simple words",
        "what is a hash table and how does it work",
        "teach me object oriented programming",
    ],
)
def test_concept_requests(prompt: str) -> None:
    ci = classify_intent(prompt)
    assert ci.intent in (Intent.CONCEPT, Intent.UNKNOWN)


@pytest.mark.parametrize(
    "prompt",
    [
        "what does this traceback mean",
        "i got a segmentation fault, why",
        "explain this error message",
    ],
)
def test_error_requests(prompt: str) -> None:
    ci = classify_intent(prompt)
    assert ci.intent == Intent.ERROR


@pytest.mark.parametrize(
    "prompt",
    [
        "explain my function step by step",
        "walk me through this code",
        "what does this snippet do",
    ],
)
def test_explain_code_requests(prompt: str) -> None:
    ci = classify_intent(prompt)
    assert ci.intent == Intent.EXPLAIN_CODE
