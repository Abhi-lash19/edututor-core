# tests/test_classifiers_extra.py
from edututor.core.classifiers import Intent, classify_intent


def test_hint_respected():
    ci = classify_intent("some question", user_hint=Intent.CONCEPT)
    assert ci.intent == Intent.CONCEPT


def test_code_indicators_detected():
    ci = classify_intent("can you walk me through this function?")
    assert ci.intent == Intent.EXPLAIN_CODE
