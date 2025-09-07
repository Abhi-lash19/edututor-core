# tests/test_mock.py
from edututor.llm.mock import chat_completion


def _mk_messages(user_text: str):
    return [
        {"role": "system", "content": "SYSTEM PROMPT"},
        {"role": "user", "content": user_text},
    ]


def test_mock_explicit_intent_error():
    msgs = _mk_messages("INTENT: ERROR\nplease help")
    out = chat_completion(msgs)
    assert "Meaning: This error" in out


def test_mock_explicit_intent_explain_code_variants():
    msgs1 = _mk_messages("intent: explain_code\nsome code")
    msgs2 = _mk_messages("INTENT: explain code\nsome code")
    assert "Key parts" in chat_completion(msgs1)
    assert "Key parts" in chat_completion(msgs2)


def test_mock_keyword_fallback_error():
    msgs = _mk_messages("i got a traceback: NullPointerException")
    out = chat_completion(msgs)
    assert "Meaning: This error" in out


def test_mock_concept_fallback():
    msgs = _mk_messages("tell me about recursion")
    out = chat_completion(msgs)
    assert "Definition: A high-level idea" in out
