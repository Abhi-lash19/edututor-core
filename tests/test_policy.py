from __future__ import annotations

from edututor.core.classifiers import Intent, ClassifiedIntent
from edututor.core.policy import decide_response


def _mk(intent: Intent, reason: str = "t") -> ClassifiedIntent:
    return ClassifiedIntent(intent=intent, reason=reason, user_hint=None)


def test_policy_refuses_disallowed() -> None:
    decision = decide_response(_mk(Intent.DISALLOWED))
    assert decision.allowed is False
    assert "t" in decision.reason


def test_policy_concept_allows_with_scaffold() -> None:
    decision = decide_response(_mk(Intent.CONCEPT))
    assert decision.allowed is True
    assert "Definition" in decision.scaffold or "definition" in decision.scaffold.lower()


def test_policy_error_allows_with_scaffold() -> None:
    decision = decide_response(_mk(Intent.ERROR))
    assert decision.allowed is True
    assert "debug" in decision.scaffold.lower()


def test_policy_explain_code_allows_with_scaffold() -> None:
    decision = decide_response(_mk(Intent.EXPLAIN_CODE))
    assert decision.allowed is True
    assert "walk through" in decision.scaffold.lower() or "walk" in decision.scaffold.lower()
