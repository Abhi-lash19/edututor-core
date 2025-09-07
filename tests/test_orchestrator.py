from __future__ import annotations

from edututor.core.orchestrator import Orchestrator


def test_orchestrator_refuses_disallowed() -> None:
    o = Orchestrator()
    res = o.handle_user_message("please write the code for mergesort")
    assert res.allowed is False
    assert "I can’t provide code" in res.content


def test_orchestrator_concept_allowed() -> None:
    o = Orchestrator()
    res = o.handle_user_message("explain recursion conceptually")
    assert res.allowed is True
    assert "Definition" in res.content or "definition" in res.content.lower()


def test_orchestrator_error_allowed() -> None:
    o = Orchestrator()
    res = o.handle_user_message("why am i getting this error")
    assert res.allowed is True
    assert "Debug" in res.content or "debug" in res.content.lower()
