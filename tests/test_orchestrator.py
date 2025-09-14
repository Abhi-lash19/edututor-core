# tests/test_orchestrator.py
from edututor.core.orchestrator import Orchestrator, OrchestratorResult


class DummyResp:
    def __init__(self, text, raw=None):
        self.text = text
        self.raw = raw or {}


class DummyProvider:
    def __init__(self, resp_text="ok"):
        self._resp_text = resp_text

    def send(self, prompt, intent):
        return DummyResp(self._resp_text, raw={"mock": True})


class DummyStore:
    def __init__(self):
        self.rows = []

    def save_conversation(self, **kwargs):
        # return fake id
        self.rows.append(kwargs)
        return len(self.rows)


def test_orchestrator_basic(monkeypatch):
    provider = DummyProvider("Hello student")
    store = DummyStore()
    o = Orchestrator(provider=provider, store=store)
    res = o.handle_user_message("Explain recursion", user_hint=None)
    assert isinstance(res, OrchestratorResult)
    # ensure we got a non-empty sanitized text back
    assert res.text
    # saved to store
    assert len(store.rows) == 1
    saved = store.rows[0]
    assert saved["user_text"] == "Explain recursion"
