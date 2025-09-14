# tests/test_persistence.py
from __future__ import annotations

import json

from edututor.persistence.store import ConversationStore


def test_save_and_fetch_roundtrip(tmp_path) -> None:
    db_file = tmp_path / "test.db"
    store = ConversationStore(db_path=str(db_file))

    row_id = store.save_conversation(
        user_text="Explain recursion",
        intent="CONCEPT",
        provider="MockLLM",
        llm_raw={"mock_intent": "CONCEPT"},
        sanitized_text="High-level hint about recursion",
        metadata={"exam_mode": False},
    )

    assert isinstance(row_id, int) and row_id > 0

    fetched = store.fetch_by_id(row_id)
    assert fetched is not None
    assert fetched.user_text == "Explain recursion"
    assert fetched.intent == "CONCEPT"
    assert fetched.provider == "MockLLM"
    assert fetched.sanitized_text == "High-level hint about recursion"
    assert fetched.llm_raw == {"mock_intent": "CONCEPT"}

    exported = store.export_json(limit=1)
    parsed = json.loads(exported)
    assert isinstance(parsed, list) and parsed[0]["user_text"] == "Explain recursion"
